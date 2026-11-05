"""Tests the voice.

Run one of these:
  python -m jarvis.test_tts                  (uses config.yaml)
  python -m jarvis.test_tts piper
  python -m jarvis.test_tts kokoro
  python -m jarvis.test_tts kokoro af_bella  (kokoro with a chosen voice)
"""
import sys
import time

import psutil

from jarvis.audio import Speaker
from jarvis.config import load_config
from jarvis.latency import LatencyLog
from jarvis.tts import load_tts

LONG_TEXT = (
    "Hello, I am your assistant. I can talk to you, look through the camera, "
    "and help you with small tasks. How can I help you today?"
)


def speed_test(tts, text):
    """Makes the speech without playing it, to measure raw speed."""
    start = time.perf_counter()
    total_samples = 0
    for chunk in tts.stream(text):
        total_samples += len(chunk)
    took = time.perf_counter() - start
    audio_seconds = total_samples / tts.sample_rate
    print(f"  Made {audio_seconds:.1f}s of speech in {took:.2f}s")
    print(f"  That is {audio_seconds / took:.1f}x faster than real time")
    print("  (above 2x is comfortable, below 1x will stutter)")


def main():
    cfg = load_config()
    if len(sys.argv) > 1:
        cfg["tts"]["engine"] = sys.argv[1]
    if len(sys.argv) > 2:
        cfg["tts"]["kokoro"]["voice"] = sys.argv[2]

    engine = cfg["tts"]["engine"]
    print(f"Engine: {engine}")
    if engine == "kokoro":
        print(f"Voice : {cfg['tts']['kokoro']['voice']}")

    log = LatencyLog()
    with log.measure("load voice"):
        tts = load_tts(cfg)
    speaker = Speaker(cfg, tts)

    memory = psutil.Process().memory_info().rss / 1e6
    print(f"Memory used by this program: {memory:.0f} MB")

    print("\n--- Speed test ---")
    speed_test(tts, LONG_TEXT)

    print("\n--- Listen ---")
    first = speaker.say(LONG_TEXT)
    print(f"  Time until first sound: {first:.0f} ms")

    print("\n--- Your turn ---")
    print("Type a sentence and press Enter. Type q to quit.")
    while True:
        text = input("You: ").strip()
        if text.lower() in ("q", "quit", ""):
            break
        first = speaker.say(text)
        print(f"  (first sound after {first:.0f} ms)")


if __name__ == "__main__":
    main()