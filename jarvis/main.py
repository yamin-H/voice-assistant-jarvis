"""Jarvis-lite main loop: hear -> understand -> speak.

Run:  python -m jarvis.main
"""
import queue
import threading
import time

import numpy as np

from jarvis.audio import Speaker
from jarvis.config import load_config
from jarvis.mic import Microphone
from jarvis.router import Reply, Router
from jarvis.stt import load_stt
from jarvis.tts import load_tts

# Seconds of silence after speaking, so the mic does not hear the end of our own voice.
ECHO_TAIL = 0.6


class Jarvis:
    def __init__(self, cfg):
        self.level = cfg["stt"]["speech_level"]

        print("Loading voice...")
        self.tts = load_tts(cfg)
        self.speaker = Speaker(cfg, self.tts)
        print("Loading ears...")
        self.stt = load_stt(cfg)
        self.router = Router(cfg)
        self.mic = Microphone(cfg)

        self.heard = queue.Queue()        # finished sentences waiting to be handled
        self.speaking = threading.Event()  # set while Jarvis is talking
        self.quiet_until = 0.0
        self.last_loud = time.perf_counter()
        self.running = True

    # --- called by the speech recognizer ---
    def _on_partial(self, text):
        print(f"\r  hearing: {text:<90}", end="", flush=True)

    def _on_final(self, text):
        if text.strip():
            self.heard.put((text.strip(), time.perf_counter()))

    # --- handle one sentence ---
    def _handle(self, text, text_ready_at):
        print(f"\r  YOU:     {text:<90}")
        listen_ms = max(0, (text_ready_at - self.last_loud) * 1000)

        start = time.perf_counter()
        reply = self.router.route(text)
        if reply is None:
            reply = Reply("Sorry, I can't do that yet.")
        route_ms = (time.perf_counter() - start) * 1000

        # Speak first (in the background), then do the action.
        self.speaking.set()
        threading.Thread(
            target=self._speak, args=(reply, listen_ms, route_ms), daemon=True
        ).start()
        if reply.action:
            try:
                reply.action()
            except Exception as error:
                print(f"  [action failed] {error}")

    def _speak(self, reply, listen_ms, route_ms):
        try:
            print(f"  JARVIS:  {reply.text}")
            voice_ms = self.speaker.say(reply.text) or 0
            total = listen_ms + route_ms + voice_ms
            print(
                f"  (stopped talking -> first sound: {total:.0f} ms = "
                f"hearing {listen_ms:.0f} + routing {route_ms:.0f} + voice {voice_ms:.0f})\n"
            )
        finally:
            self.quiet_until = time.perf_counter() + ECHO_TAIL
            self.speaking.clear()
            if reply.quit:
                self.running = False

    # --- main loop ---
    def run(self):
        self.stt.start(self._on_partial, self._on_final)
        self.mic.start()
        print("\nReady! Try: 'what time is it', 'open YouTube', 'search for python tutorials'.")
        print("Say 'goodbye' or press Ctrl+C to quit.\n")

        try:
            while self.running:
                try:
                    chunk = self.mic.chunks.get(timeout=0.1)
                except queue.Empty:
                    chunk = None

                if chunk is not None:
                    if self.speaking.is_set() or time.perf_counter() < self.quiet_until:
                        chunk = np.zeros_like(chunk)  # deaf while talking
                    elif float(np.sqrt(np.mean(chunk ** 2))) > self.level:
                        self.last_loud = time.perf_counter()
                    self.stt.feed(chunk)

                if not self.speaking.is_set():
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


def main():
    Jarvis(load_config()).run()


if __name__ == "__main__":
    main()