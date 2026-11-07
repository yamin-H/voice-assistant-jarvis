"""Plays speech. Sentence 1 plays while sentence 2 is still being made."""
import queue
import threading
import time
import numpy as np
from jarvis.ui_server import hub
import sounddevice as sd

SLICE_SECONDS = 0.05  # audio is written in tiny slices so we can stop quickly


class Speaker:
    def __init__(self, cfg, tts):
        self.tts = tts
        self.device = cfg["audio"]["output_device"]
        self._stop = threading.Event()

    def stop(self):
        """Stops speaking right now."""
        self._stop.set()

    def say(self, text):
        """Speaks the text. Returns milliseconds until the first sound played."""
        return self.say_stream([text])

    def say_stream(self, pieces):
        """Speaks pieces of text as they arrive (they can come slowly, e.g. from the brain).

        Returns milliseconds until the first sound played.
        """
        self._stop.clear()
        stop = self._stop
        audio_queue = queue.Queue(maxsize=8)
        done = object()  # a marker meaning "no more audio"

        def put(item):
            """Adds to the queue, but gives up if we were told to stop."""
            while not stop.is_set():
                try:
                    audio_queue.put(item, timeout=0.05)
                    return True
                except queue.Full:
                    pass
            return False

        def producer():
            try:
                for piece in pieces:
                    if stop.is_set():
                        return
                    for chunk in self.tts.stream(piece):
                        if not put(chunk):
                            return
            finally:
                put(done)

        start = time.perf_counter()
        threading.Thread(target=producer, daemon=True).start()
        slice_size = int(self.tts.sample_rate * SLICE_SECONDS)

        first_sound_ms = None
        with sd.OutputStream(
            samplerate=self.tts.sample_rate,
            channels=1,
            dtype="float32",
            device=self.device,
        ) as stream:
            while not stop.is_set():
                try:
                    chunk = audio_queue.get(timeout=0.05)
                except queue.Empty:
                    continue
                if chunk is done:
                    break
                if first_sound_ms is None:
                    first_sound_ms = (time.perf_counter() - start) * 1000
                    hub.emit("state", state="speaking")
                for i in range(0, len(chunk), slice_size):
                    if stop.is_set():
                        break
                    part = chunk[i:i + slice_size]
                    hub.emit("level", source="voice", value=float(np.sqrt(np.mean(part ** 2))))
                    stream.write(part.reshape(-1, 1))
            if stop.is_set():
                stream.abort()
        hub.emit("level", source="voice", value=0.0)
        return first_sound_ms