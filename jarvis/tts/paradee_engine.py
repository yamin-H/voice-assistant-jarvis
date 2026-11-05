"""Paradee text-to-speech. A tiny voice distilled from Kokoro (af_heart). Very fast."""
import numpy as np
from paradee import SAMPLE_RATE, Paradee

from jarvis.tts.text import split_for_speech


class ParadeeTTS:
    def __init__(self, cfg):
        self.tts = Paradee()
        self.sample_rate = SAMPLE_RATE

        # Warm-up: the first synthesis is slower, so we do one now.
        self.tts("Hello.")

    def stream(self, text):
        """Yields speech piece by piece (short pieces, so sound starts fast)."""
        for piece in split_for_speech(text):
            audio = np.asarray(self.tts(piece), dtype=np.float32).squeeze()
            yield audio