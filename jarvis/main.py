"""Jarvis-lite main loop: sleep -> wake word -> listen -> think -> speak.

Run:  python -m jarvis.main
"""
import queue
import threading
import time

import numpy as np
from jarvis import sounds
from jarvis.agent import VoiceAgent
from jarvis.audio import Speaker
from jarvis.brain import load_brain
from jarvis.brain.chunker import speakable_pieces
from jarvis.config import load_config, validate_env, migrate_legacy_data
from jarvis.logger import setup_logging, get_logger
from jarvis.mic import Microphone
from jarvis.reply import Reply
from jarvis.router import Router
from jarvis.scheduler import SCHEDULER, spoken
from jarvis.skills.control import CANCEL
from jarvis.stt import load_stt
from jarvis.tts import load_tts
from jarvis.vision import Vision
from jarvis.wake import WakeWord
from jarvis.ui_server import hub, start_ui_server

log = get_logger("main")

ECHO_TAIL = 0.6      # seconds of deafness after Jarvis stops talking
WAKE_COOLDOWN = 1.5  # ignore a second wake word right after one

SLEEPING = "sleeping"    # waiting for the wake word
LISTENING = "listening"  # waiting for you to speak
BUSY = "busy"            # thinking, speaking or doing something


class Jarvis:
    def __init__(self, cfg):
        wake_cfg = cfg["wake"]
        self.use_wake = wake_cfg["enabled"]
        self.wake_threshold = wake_cfg["threshold"]
        self.wake_threshold_busy = wake_cfg["threshold_while_busy"]
        self.listen_seconds = wake_cfg["listen_seconds"]
        self.follow_up_seconds = wake_cfg["follow_up_seconds"]
        self.level = cfg["stt"]["speech_level"]
        self.output_device = cfg["audio"]["output_device"]
        self._last_level = 0.0

        print("Loading voice...")
        self.tts = load_tts(cfg)
        self.speaker = Speaker(cfg, self.tts)
        print("Loading ears...")
        self.stt = load_stt(cfg)
        self.mic = Microphone(cfg)
        self.wake = WakeWord(cfg) if self.use_wake else None

        self.vision = None
        if cfg["vision"]["enabled"]:
            print("Starting camera and vision...")
            try:
                self.vision = Vision(cfg)
                self.vision.start()
            except Exception as error:
                log.warning("Vision not available: %s", error, exc_info=True)
                print(f"  Vision not available: {error}")
                self.vision = None

        print("Loading brain (the first time can take a while)...")
        self.brain = load_brain(cfg)
        try:
            self.brain.warm_up()
        except Exception as error:
            log.warning("Brain warmup error: %s", error, exc_info=True)
            print(f"  Brain not available: {error}")
            print("  Jarvis will still work for simple commands.")
            self.brain = None

        self.router = Router(cfg, self.vision, self.brain)

        self.voice_agent = None

        if cfg["agent"].get("voice_enabled", False):
            try:
                # Share the Router's Context so window and app states are unified!
                self.voice_agent = VoiceAgent(cfg, ctx=self.router.ctx)
                print("Agent voice mode is enabled.")
            except Exception as error:
                log.error("Agent mode init error: %s", error, exc_info=True)
                print(f"  Agent voice mode is unavailable: {error}")

        self.heard = queue.Queue()          # finished sentences waiting to be handled
        self.announcements = queue.Queue()  # timers and reminders waiting to be spoken
        self.state = SLEEPING if self.use_wake else LISTENING
        self.awake_until = 0.0
        self.quiet_until = 0.0
        self.last_wake = 0.0
        self.last_loud = time.perf_counter()
        self.running = True

    # --- state (every change is broadcast to the UI) ---
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        hub.emit("state", state="thinking" if value == BUSY else value)

    # --- called by the speech recognizer ---
    def _on_partial(self, text):
        if self.state != LISTENING:
            return
        if text.strip():
            # You are talking: keep the listening window open.
            self.awake_until = max(self.awake_until, time.perf_counter() + 6)
            hub.emit("transcript", kind="partial", text=text)
        print(f"\r  hearing: {text:<90}", end="", flush=True)

    def _on_final(self, text):
        if self.state != LISTENING:
            return
        if sum(c.isalnum() for c in text) < 2:
            return  # just noise
        hub.emit("transcript", kind="final", text=text.strip())
        self.heard.put((text.strip(), time.perf_counter()))

    # --- state changes ---
    def _wake_up(self):
        now = time.perf_counter()
        if now - self.last_wake < WAKE_COOLDOWN:
            return
        self.last_wake = now

        if self.state == BUSY:
            print("\n  [interrupted]")
            CANCEL.set()          # stops typing and running steps
            self.speaker.stop()   # stops talking

        self.state = LISTENING
        self.awake_until = now + self.listen_seconds
        self.quiet_until = now + 0.45  # so we do not hear our own chime
        while not self.heard.empty():
            self.heard.get_nowait()
        sounds.play(sounds.WAKE, self.output_device)
        print("\n  [listening...]")
        self.wake.reset()

    def _go_to_sleep(self):
        self.state = SLEEPING
        sounds.play(sounds.SLEEP, self.output_device)
        print("\r  [sleeping. Say 'Hey Jarvis' to wake me]" + " " * 60 + "\n")
        self.wake.reset()

    def _finish_speaking(self, quit_after):
        now = time.perf_counter()
        self.quiet_until = now + ECHO_TAIL
        if self.state == BUSY:  # not interrupted, so keep listening for a follow-up
            self.state = LISTENING
            self.awake_until = now + self.follow_up_seconds
        if quit_after:
            self.running = False

    # --- timers and reminders that go off by themselves ---
    def _can_announce(self, now):
        if self.state == SLEEPING:
            return True
        # Do not talk over you: only when you have been quiet for a moment.
        return self.state == LISTENING and now - self.last_loud > 2.0 and self.heard.empty()

    def _announce(self, item):
        self.state = BUSY
        threading.Thread(target=self._say_announcement, args=(item,), daemon=True).start()

    def _say_announcement(self, item):
        try:
            text = spoken(item)
            print(f"\n  [{item['kind']} went off] JARVIS: {text}\n")
            sounds.play(sounds.ALARM, self.output_device, wait=True)
            if self.state == BUSY:  # nobody interrupted the beeps
                self.speaker.say(text)
        finally:
            now = time.perf_counter()
            self.quiet_until = now + ECHO_TAIL
            if self.state == BUSY:
                # Stay awake for a few seconds, so you can say "snooze" or "thanks".
                self.state = LISTENING
                self.awake_until = now + self.follow_up_seconds

    # --- agent ---
    def _run_voice_agent(self, text, listen_ms, route_ms):
        """Run agent planning/actions off the microphone loop thread."""
        try:
            response = self.voice_agent.handle(text, CANCEL)

            # The wake word may have interrupted us while the model was planning.
            if self.state != BUSY or CANCEL.is_set():
                return

            print(f"  JARVIS:  {response}")
            hub.emit("reply", text=response)
            voice_ms = self.speaker.say(response) or 0

            total = listen_ms + route_ms + voice_ms
            print(
                f"  (agent response -> first sound: {total:.0f} ms = "
                f"hearing {listen_ms:.0f} + routing {route_ms:.0f} "
                f"+ planning and voice {voice_ms:.0f})\n"
            )
        except Exception as error:
            log.error("Voice agent execution error: %s", error, exc_info=True)
            print(f"  [voice agent error] {error}")
            if self.state == BUSY and not CANCEL.is_set():
                self.speaker.say("Sorry, something went wrong with that request.")
        finally:
            if self.state == BUSY:
                self._finish_speaking(False)

    # --- handle one sentence ---
    def _handle(self, text, text_ready_at):
        print(f"\r  YOU:     {text:<90}")
        listen_ms = max(0, (text_ready_at - self.last_loud) * 1000)

        self.state = BUSY
        CANCEL.clear()

        # A pending agent confirmation owns the next short spoken answer.
        if self.voice_agent and self.voice_agent.awaiting_confirmation:
            threading.Thread(
                target=self._run_voice_agent,
                args=(text, listen_ms, 0),
                daemon=True,
            ).start()
            return

        start = time.perf_counter()
        reply = self.router.route(text)
        route_ms = (time.perf_counter() - start) * 1000

        # Stable existing skills stay the fast path.
        if reply is not None:
            threading.Thread(
                target=self._speak,
                args=(reply, listen_ms, route_ms),
                daemon=True,
            ).start()
            return

        # Natural-language requests that do not match a legacy command go to
        # the restricted agent before falling back to ordinary conversation.
        if self.voice_agent is not None:
            threading.Thread(
                target=self._run_voice_agent,
                args=(text, listen_ms, route_ms),
                daemon=True,
            ).start()
            return

        if self.brain is not None:
            threading.Thread(
                target=self._chat,
                args=(text, listen_ms, route_ms),
                daemon=True,
            ).start()
            return

        threading.Thread(
            target=self._speak,
            args=(Reply("Sorry, I can't do that yet."), listen_ms, route_ms),
            daemon=True,
        )

    @staticmethod
    def _run_action(action, result):
        try:
            message = action()
            if isinstance(message, str) and message:
                result["message"] = message
        except Exception as error:
            log.error("Action failure: %s", error, exc_info=True)
            print(f"  [action failed] {error}")
            result["message"] = "Sorry, something went wrong."

    def _speak(self, reply, listen_ms, route_ms):
        result = {}
        worker = None
        try:
            if reply.action:
                # The action runs in the background while Jarvis talks.
                CANCEL.clear()
                worker = threading.Thread(
                    target=self._run_action, args=(reply.action, result), daemon=True
                )
                worker.start()

            print(f"  JARVIS:  {reply.text}")
            hub.emit("reply", text=reply.text)
            voice_ms = self.speaker.say(reply.text) or 0
            total = listen_ms + route_ms + voice_ms
            print(
                f"  (stopped talking -> first sound: {total:.0f} ms = "
                f"hearing {listen_ms:.0f} + routing {route_ms:.0f} + voice {voice_ms:.0f})\n"
            )

            if worker:
                worker.join()
                message = result.get("message")
                if message and not CANCEL.is_set():
                    print(f"  JARVIS:  {message}\n")
                    hub.emit("reply", text=message)
                    self.speaker.say(message)
        finally:
            self._finish_speaking(reply.quit)

    def _chat(self, text, listen_ms, route_ms):
        try:
            print("  JARVIS:  ", end="", flush=True)

            def pieces():
                for piece in speakable_pieces(self.brain.stream(text)):
                    print(piece + " ", end="", flush=True)
                    hub.emit("reply_chunk", text=piece)
                    yield piece

            first_sound = self.speaker.say_stream(pieces()) or 0
            print()
            total = listen_ms + route_ms + first_sound
            brain_ms = self.brain.first_token_ms or 0
            print(
                f"  (stopped talking -> first sound: {total:.0f} ms = hearing {listen_ms:.0f} "
                f"+ routing {route_ms:.0f} + brain and voice {first_sound:.0f}; "
                f"the brain's first word took {brain_ms:.0f} ms)\n"
            )
        finally:
            self._finish_speaking(False)

    # --- main loop ---
    def run(self):
        self.stt.start(self._on_partial, self._on_final)
        self.mic.start()
        if self.use_wake:
            print("\nReady! Say 'Hey Jarvis' (wait for the chime), then ask something.")
        else:
            print("\nReady! Wake word is off, so I am always listening.")
        print("Say 'goodbye' or press Ctrl+C to quit.\n")

        try:
            while self.running:
                try:
                    chunk = self.mic.chunks.get(timeout=0.1)
                except queue.Empty:
                    chunk = None
                now = time.perf_counter()

                if chunk is not None:
                    rms = float(np.sqrt(np.mean(chunk ** 2)))
                    if self.state == LISTENING and now - self._last_level > 0.033:
                        self._last_level = now
                        hub.emit("level", source="mic", value=rms)

                    # 1) Wake word: runs while sleeping, and while busy (to allow interrupts).
                    if self.use_wake and self.state in (SLEEPING, BUSY):
                        limit = (
                            self.wake_threshold_busy
                            if self.state == BUSY
                            else self.wake_threshold
                        )
                        if self.wake.score(chunk) >= limit:
                            self._wake_up()
                            continue

                    # 2) Speech recognition: only while listening.
                    if self.state == LISTENING and now >= self.quiet_until:
                        if rms > self.level:
                            self.last_loud = now
                        self.stt.feed(chunk)

                # Listening window ran out: go back to sleep.
                if self.use_wake and self.state == LISTENING and now > self.awake_until:
                    self._go_to_sleep()

                # A timer, alarm or reminder went off.
                for item in SCHEDULER.pop_due():
                    self.announcements.put(item)
                if not self.announcements.empty() and self._can_announce(now):
                    self._announce(self.announcements.get_nowait())
                    continue

                # A finished sentence is waiting.
                if self.state == LISTENING:
                    try:
                        text, ready_at = self.heard.get_nowait()
                    except queue.Empty:
                        continue
                    self._handle(text, ready_at)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.mic.stop()
            self.stt.stop()
            if self.vision:
                self.vision.stop()


def main():
    cfg = load_config()
    validate_env(cfg)
    migrate_legacy_data()
    setup_logging(cfg)
    start_ui_server()
    Jarvis(cfg).run()


if __name__ == "__main__":
    main()