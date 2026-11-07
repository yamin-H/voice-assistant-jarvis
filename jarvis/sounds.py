"""Small sound effects, made in code (no files needed)."""
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 24000


def _tone(freq, seconds, volume=0.25):
    t = np.linspace(0, seconds, int(SAMPLE_RATE * seconds), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    fade = np.minimum(1.0, np.minimum(t, seconds - t) / 0.01)  # 10 ms fade in and out
    return (volume * wave * fade).astype(np.float32)


def _silence(seconds):
    return np.zeros(int(SAMPLE_RATE * seconds), dtype=np.float32)


WAKE = np.concatenate([_tone(660, 0.08), _tone(880, 0.12)])   # going up = "I'm listening"
SLEEP = np.concatenate([_tone(660, 0.08), _tone(440, 0.12)])  # going down = "going to sleep"

_BEEPS = np.concatenate([_tone(880, 0.12), _silence(0.08), _tone(880, 0.12), _silence(0.08), _tone(1100, 0.22)])
ALARM = np.concatenate([_BEEPS, _silence(0.3), _BEEPS])       # timers, alarms and reminders


def play(sound, device=None, wait=False):
    """Plays a sound. By default it does not wait for it to finish."""
    sd.play(sound, SAMPLE_RATE, device=device)
    if wait:
        sd.wait()