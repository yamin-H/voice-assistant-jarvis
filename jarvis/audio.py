"""Plays speech. Sentence 1 plays while sentence 2 is still being made."""
import queue
import threading
import time

import sounddevice as sd


class Speaker:
    def __init__(self, cfg, tts):
        self.tts = tts
        self.device = cfg["audio"]["output_device"]

    def say(self, text):
        """Speaks the text. Returns milliseconds until the first sound played."""
        audio_queue = queue.Queue(maxsize=8)
        done = object()  # a marker meaning "no more audio"

        def producer():
            try:
                for chunk in self.tts.stream(text):
                    audio_queue.put(chunk)
            finally:
                audio_queue.put(done)

        start = time.perf_counter()
        threading.Thread(target=producer, daemon=True).start()

        first_sound_ms = None
        with sd.OutputStream(
            samplerate=self.tts.sample_rate,
            channels=1,
            dtype="float32",
            device=self.device,
        ) as stream:
            while True:
                chunk = audio_queue.get()
                if chunk is done:
                    break
                if first_sound_ms is None:
                    first_sound_ms = (time.perf_counter() - start) * 1000
                stream.write(chunk.reshape(-1, 1))
        return first_sound_ms