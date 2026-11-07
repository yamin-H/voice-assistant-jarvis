"""Webcam capture. Keeps only the newest picture, so there is never a delay or backlog."""
import threading
import time

import cv2


class Camera:
    def __init__(self, cfg):
        settings = cfg["vision"]
        self.index = settings["camera_index"]
        self.width = settings["width"]
        self.height = settings["height"]
        self._cap = None
        self._frame = None
        self._count = 0
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        self._cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            raise RuntimeError("Could not open the webcam. Is another app using it?")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

        # Wait for a few pictures: the first ones are often dark while the camera adjusts.
        deadline = time.time() + 5
        while self._count < 8 and time.time() < deadline:
            time.sleep(0.05)
        if self._count == 0:
            raise RuntimeError("The webcam opened but gave no pictures.")

    def _loop(self):
        while self._running:
            cap = self._cap
            if cap is None:
                break
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            with self._lock:
                self._frame = frame
                self._count += 1

    def latest(self):
        """Returns a copy of the newest picture (or None if there is none yet)."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def stop(self):
        self._running = False
        time.sleep(0.1)
        if self._cap is not None:
            self._cap.release()
            self._cap = None