"""Piper text-to-speech. Fast, runs on the CPU."""
import numpy as np
from piper import PiperVoice

from jarvis.config import ROOT


class PiperTTS:
    def __init__(self, cfg):
        voice_name = cfg["tts"]["piper"]["voice"]
        model_path = ROOT / cfg["paths"]["models_dir"] / "piper" / f"{voice_name}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Voice file not found: {model_path}\n"
                f"Download it with: python -m piper.download_voices {voice_name} --data-dir models\\piper"
            )
        self.voice = PiperVoice.load(str(model_path))
        self.sample_rate = self.voice.config.sample_rate

        # Warm-up: the very first synthesis is slower, so we do one now.
        for _ in self.voice.synthesize("Hello."):
            pass

    def stream(self, text):
        """Yields the speech piece by piece (one piece per sentence)."""
        for chunk in self.voice.synthesize(text):
            pcm = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            yield pcm.astype(np.float32) / 32768.0