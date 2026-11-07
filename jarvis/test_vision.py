"""Tests the eyes: live webcam with boxes.

Run:  python -m jarvis.test_vision
In the window: press q to quit, d to print what Jarvis would say.
"""
import time

import cv2

from jarvis.config import load_config
from jarvis.vision import Vision
from jarvis.vision.describe import describe

MAX_FPS = 5  # we cap the speed so your PC stays smooth


def main():
    cfg = load_config()
    print("Loading detector and opening camera...")
    vision = Vision(cfg)
    print(f"Detector ready: {vision.detector.info}")
    vision.start()
    print("A window will open. Press q in the window to quit, d to print what I see.\n")

    try:
        while True:
            loop_start = time.perf_counter()
            frame = vision.camera.latest()
            if frame is None:
                continue

            t0 = time.perf_counter()
            detections = vision.detector.detect(frame)
            ms = (time.perf_counter() - t0) * 1000

            for d in detections:
                x1, y1, x2, y2 = (int(v) for v in d.box)
                color = (0, 200, 0) if d.conf >= vision.sure else (0, 165, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{d.label} {d.conf:.2f}", (x1, max(15, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.putText(frame, f"detector: {ms:.0f} ms per picture", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            cv2.imshow("Jarvis eyes", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("d"):
                print(f"  ({ms:.0f} ms) " + describe(detections, vision.sure))

            spare = 1.0 / MAX_FPS - (time.perf_counter() - loop_start)
            if spare > 0:
                time.sleep(spare)
    finally:
        vision.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()