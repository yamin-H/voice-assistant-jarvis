"""Microphone input. Puts 100 ms chunks of audio into a queue."""
import queue

import sounddevice as sd


class Microphone:
    def __init__(self, cfg):
        self.sample_rate = cfg["audio"]["sample_rate"]
        self.device = cfg["audio"]["input_device"]
        self.chunks = queue.Queue()
        self._stream = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[mic warning] {status}")
        self.chunks.put(indata[:, 0].copy())

    def start(self):
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=int(self.sample_rate * 0.1),
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None