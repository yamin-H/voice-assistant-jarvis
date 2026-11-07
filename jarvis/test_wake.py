"""Tests the wake word.  Run:  python -m jarvis.test_wake   (Ctrl+C to stop)"""
import time

from jarvis.config import load_config
from jarvis.mic import Microphone
from jarvis.wake import WakeWord


def main():
    cfg = load_config()
    threshold = cfg["wake"]["threshold"]
    wake = WakeWord(cfg)
    mic = Microphone(cfg)
    mic.start()

    print(f"Say 'Hey Jarvis'. It triggers at a score of {threshold}. Ctrl+C to stop.\n")
    last_trigger = 0.0
    peak = 0.0
    try:
        while True:
            chunk = mic.chunks.get()
            score = wake.score(chunk)
            peak = max(score, peak * 0.9)  # the bar falls slowly so you can see it
            bar = "#" * int(peak * 40)
            print(f"\r  score {peak:4.2f} {bar:<40}", end="", flush=True)
            if score >= threshold and time.perf_counter() - last_trigger > 1.5:
                last_trigger = time.perf_counter()
                print(f"\n  >>> WAKE WORD DETECTED (score {score:.2f})")
                wake.reset()
                peak = 0.0
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mic.stop()


if __name__ == "__main__":
    main()