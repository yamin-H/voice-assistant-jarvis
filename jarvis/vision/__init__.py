"""Eyes: camera + object detector."""
from jarvis.vision.camera import Camera
from jarvis.vision.detector import YoloDetector


class Vision:
    def __init__(self, cfg):
        self.camera = Camera(cfg)
        self.detector = YoloDetector(cfg)
        self.sure = cfg["vision"]["sure_confidence"]

    def start(self):
        self.camera.start()

    def stop(self):
        self.camera.stop()

    def look(self):
        """Detects objects in the newest camera picture."""
        frame = self.camera.latest()
        if frame is None:
            raise RuntimeError("no camera picture yet")
        return self.detector.detect(frame)