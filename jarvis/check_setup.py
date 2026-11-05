"""Checks that this PC is ready for the project.

Run from the project folder:  python -m jarvis.check_setup
"""
import platform
import sys

import cv2
import numpy as np
import psutil
import sounddevice as sd

from jarvis.config import cpu_threads, load_config
from jarvis.latency import LatencyLog


def title(text):
    print(f"\n=== {text} ===")


def check_system(cfg):
    title("System")
    print(f"Python    : {sys.version.split()[0]}")
    print(f"OS        : {platform.system()} {platform.release()}")
    print(f"CPU cores : {psutil.cpu_count(logical=True)} (logical)")
    ram = psutil.virtual_memory()
    print(f"RAM       : {ram.total / 1e9:.1f} GB total, {ram.available / 1e9:.1f} GB free")
    print(f"CPU threads the assistant will use: {cpu_threads(cfg)}")


def check_audio_devices():
    title("Audio devices")
    mic = sd.query_devices(kind="input")
    speaker = sd.query_devices(kind="output")
    print(f"Default microphone: {mic['name']}")
    print(f"Default speaker   : {speaker['name']}")


def check_speaker(cfg):
    title("Speaker test")
    sr = cfg["audio"]["sample_rate"]
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    beep = (0.3 * np.sin(2 * np.pi * 660 * t)).astype("float32")
    print("Playing a short beep...")
    sd.play(beep, sr, device=cfg["audio"]["output_device"])
    sd.wait()
    print("Did you hear it? If not, check your volume and default speaker.")


def check_mic(cfg):
    title("Microphone test")
    sr = cfg["audio"]["sample_rate"]
    print("Say something for 3 seconds, starting now...")
    audio = sd.rec(
        int(3 * sr),
        samplerate=sr,
        channels=1,
        dtype="float32",
        device=cfg["audio"]["input_device"],
    )
    sd.wait()
    level = float(np.abs(audio).max())
    print(f"Loudest level heard: {level:.3f}")
    if level < 0.01:
        print("PROBLEM: almost no sound. Check that the mic is on and not muted.")
    else:
        print("OK: the microphone is picking up sound.")


def check_webcam(log):
    title("Webcam test")
    with log.measure("webcam open"):
        cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("FAILED: could not open the webcam. Close other apps using it and retry.")
        return
    ok, frame = cam.read()
    cam.release()
    if ok:
        height, width = frame.shape[:2]
        print(f"OK: got a frame of {width}x{height}")
    else:
        print("FAILED: the webcam opened but gave no picture.")


def run(name, func, *args):
    """Runs one check. If it crashes, we show the error and continue."""
    try:
        func(*args)
    except Exception as error:
        print(f"FAILED ({name}): {error}")


def main():
    cfg = load_config()
    log = LatencyLog()
    run("system", check_system, cfg)
    run("audio devices", check_audio_devices)
    run("speaker", check_speaker, cfg)
    run("microphone", check_mic, cfg)
    run("webcam", check_webcam, log)
    log.summary()
    print("\nSetup check finished.")


if __name__ == "__main__":
    main()