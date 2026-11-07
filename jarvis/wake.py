"""Wake word detection with openWakeWord ("hey jarvis")."""
import numpy as np
from openwakeword.model import Model

FRAME = 1280  # 80 ms of audio at 16 kHz


class WakeWord:
    def __init__(self, cfg):
        name = cfg["wake"]["model"]
        try:
            self.model = Model(wakeword_models=[name], inference_framework="onnx")
        except Exception as error:
            raise RuntimeError(
                f"Could not load the wake word model '{name}': {error}\n"
                "Did you run the one-time download from Step 1?"
            ) from error
        self.buffer = np.zeros(0, dtype=np.int16)

    def score(self, audio):
        """audio = float32 microphone samples (-1 to 1).

        Returns the highest wake word score (0 to 1) heard in this chunk.
        """
        pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
        self.buffer = np.concatenate([self.buffer, pcm])
        best = 0.0
        while len(self.buffer) >= FRAME:
            frame = self.buffer[:FRAME]
            self.buffer = self.buffer[FRAME:]
            scores = self.model.predict(frame)
            if scores:
                best = max(best, float(max(scores.values())))
        return best

    def reset(self):
        """Forget recent audio, so one wake word does not trigger twice."""
        self.buffer = np.zeros(0, dtype=np.int16)
        if hasattr(self.model, "reset"):
            self.model.reset()