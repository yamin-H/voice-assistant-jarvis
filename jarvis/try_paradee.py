"""Quick test of Paradee. Run:  python jarvis\\try_paradee.py"""
import time

import numpy as np
import sounddevice as sd
from paradee import SAMPLE_RATE, Paradee

TEXT = (
    "Hello, I am your assistant. I can talk to you, look through the camera, "
    "and help you with small tasks. How can I help you today?"
)

print("Loading Paradee...")
start = time.perf_counter()
tts = Paradee()
print(f"Load time: {(time.perf_counter() - start) * 1000:.0f} ms")

tts("Hello.")  # warm-up

start = time.perf_counter()
audio = np.asarray(tts(TEXT), dtype=np.float32).squeeze()
took = time.perf_counter() - start
seconds = len(audio) / SAMPLE_RATE
print(f"Made {seconds:.1f}s of speech in {took:.2f}s")
print(f"That is {seconds / took:.1f}x faster than real time")

print("Playing...")
sd.play(audio, SAMPLE_RATE)
sd.wait()

while True:
    text = input("You (q to quit): ").strip()
    if text.lower() in ("q", ""):
        break
    start = time.perf_counter()
    audio = np.asarray(tts(text), dtype=np.float32).squeeze()
    print(f"  made in {(time.perf_counter() - start) * 1000:.0f} ms")
    sd.play(audio, SAMPLE_RATE)
    sd.wait()