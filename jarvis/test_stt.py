"""Tests the ears.  Run:  python -m jarvis.test_stt   (Ctrl+C to stop)"""
import time

import numpy as np
import psutil

from jarvis.config import load_config
from jarvis.latency import LatencyLog
from jarvis.mic import Microphone
from jarvis.stt import load_stt


def main():
    cfg = load_config()
    level = cfg["stt"]["speech_level"]
    log = LatencyLog()

    print("Loading speech recognition (the first run downloads a model)...")
    with log.measure("load speech model"):
        stt = load_stt(cfg)

    process = psutil.Process()
    print(f"Memory used by this program: {process.memory_info().rss / 1e6:.0f} MB")

    state = {"last_loud": time.perf_counter()}

    def on_partial(text):
        print(f"\r  hearing: {text:<90}", end="", flush=True)

    def on_final(text):
        if not text.strip():
            return
        wait_ms = max(0, (time.perf_counter() - state["last_loud"]) * 1000)
        cpu = process.cpu_percent() / psutil.cpu_count()
        print(f"\r  YOU SAID: {text:<90}")
        print(f"  (text ready {wait_ms:.0f} ms after you stopped talking, CPU {cpu:.0f}%)\n")

    mic = Microphone(cfg)
    stt.start(on_partial, on_final)
    process.cpu_percent()  # start measuring CPU
    mic.start()
    print("\nListening. Speak normally. Press Ctrl+C to stop.\n")

    try:
        while True:
            chunk = mic.chunks.get()
            print(f"\rrms: {float(np.sqrt(np.mean(chunk ** 2))):.4f}", end="", flush=True)
            if float(np.sqrt(np.mean(chunk ** 2))) > level:
                state["last_loud"] = time.perf_counter()
            stt.feed(chunk)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        mic.stop()
        stt.stop()


if __name__ == "__main__":
    main()