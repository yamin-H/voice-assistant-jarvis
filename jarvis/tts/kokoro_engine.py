"""Kokoro text-to-speech. More natural than Piper, but heavier."""
import numpy as np
from kokoro_onnx import Kokoro

from jarvis.config import ROOT
from jarvis.tts.text import split_for_speech


class KokoroTTS:
    def __init__(self, cfg):
        settings = cfg["tts"]["kokoro"]
        folder = ROOT / cfg["paths"]["models_dir"] / "kokoro"
        model_path = folder / settings["model_file"]
        voices_path = folder / "voices-v1.0.bin"
        for path in (model_path, voices_path):
            if not path.exists():
                raise FileNotFoundError(f"Missing file: {path}")

        self.kokoro = Kokoro(str(model_path), str(voices_path))
        self.voice = settings["voice"]
        self.speed = settings["speed"]

        # Warm-up: the first synthesis is slower. This also tells us the sample rate.
        _, self.sample_rate = self.kokoro.create(
            "Hello.", voice=self.voice, speed=self.speed, lang="en-us"
        )

    def stream(self, text):
        """Yields speech piece by piece (short pieces, so sound starts fast)."""
        for piece in split_for_speech(text):
            audio, _ = self.kokoro.create(
                piece, voice=self.voice, speed=self.speed, lang="en-us"
            )
            yield audio.astype(np.float32)