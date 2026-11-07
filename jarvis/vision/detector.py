"""Object detection with YOLO26 (ONNX). Runs on the CPU. Knows 80 common object types."""
from dataclasses import dataclass

import cv2
import numpy as np
import onnxruntime as ort

from jarvis.config import ROOT

COCO_NAMES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
    "toothbrush",
]


@dataclass
class Detection:
    label: str
    conf: float
    box: tuple  # (x1, y1, x2, y2) in pixels of the camera picture


class YoloDetector:
    def __init__(self, cfg):
        settings = cfg["vision"]
        path = ROOT / cfg["paths"]["models_dir"] / "yolo" / settings["model_file"]
        if not path.exists():
            raise FileNotFoundError(f"Detector file not found: {path}")

        options = ort.SessionOptions()
        options.intra_op_num_threads = settings["threads"]
        self.session = ort.InferenceSession(
            str(path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        model_input = self.session.get_inputs()[0]
        model_output = self.session.get_outputs()[0]
        self.input_name = model_input.name
        self.size = model_input.shape[2] if isinstance(model_input.shape[2], int) else 640
        self.dtype = np.float16 if "float16" in model_input.type else np.float32
        self.min_conf = settings["confidence"]
        self.info = f"input {model_input.shape}, output {model_output.shape}"

        # Warm-up: the first run is slower, so we do one now.
        blank = np.zeros((1, 3, self.size, self.size), dtype=self.dtype)
        self.session.run(None, {self.input_name: blank})

    def detect(self, frame):
        """frame = a BGR picture from OpenCV. Returns a list of Detection, best first."""
        height, width = frame.shape[:2]

        # Resize to fit the square input, keeping the shape (grey bars fill the rest).
        scale = min(self.size / width, self.size / height)
        new_w, new_h = round(width * scale), round(height * scale)
        pad_x, pad_y = (self.size - new_w) // 2, (self.size - new_h) // 2
        canvas = np.full((self.size, self.size, 3), 114, dtype=np.uint8)
        canvas[pad_y:pad_y + new_h, pad_x:pad_x + new_w] = cv2.resize(frame, (new_w, new_h))

        blob = canvas[:, :, ::-1].transpose(2, 0, 1)  # BGR -> RGB, then channels first
        blob = np.ascontiguousarray(blob, dtype=np.float32)[None] / 255.0
        output = self.session.run(None, {self.input_name: blob.astype(self.dtype)})[0]

        return self._read_output(output, scale, pad_x, pad_y, width, height)

    def _read_output(self, output, scale, pad_x, pad_y, width, height):
        out = np.squeeze(output, axis=0) if output.ndim == 3 else output

        if out.shape[-1] == 6:
            # Ready-made format: up to 300 rows of [x1, y1, x2, y2, confidence, class]
            keep = out[:, 4] >= self.min_conf
            boxes, conf, cls = out[keep, :4], out[keep, 4], out[keep, 5].astype(int)
        else:
            # Classic format: (4 + 80) values for each of 8400 spots. Needs NMS.
            preds = out.T if out.shape[0] < out.shape[1] else out
            scores = preds[:, 4:]
            cls, conf = scores.argmax(axis=1), scores.max(axis=1)
            keep = conf >= self.min_conf
            preds, conf, cls = preds[keep], conf[keep], cls[keep]
            cx, cy, w, h = preds[:, 0], preds[:, 1], preds[:, 2], preds[:, 3]
            boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)
            if len(boxes):
                xywh = [[float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])]
                        for b in boxes]
                picked = cv2.dnn.NMSBoxes(xywh, conf.astype(float).tolist(), self.min_conf, 0.5)
                picked = np.array(picked).flatten().astype(int)
                boxes, conf, cls = boxes[picked], conf[picked], cls[picked]

        detections = []
        for (x1, y1, x2, y2), score, k in zip(boxes, conf, cls):
            box = (
                float(np.clip((x1 - pad_x) / scale, 0, width)),
                float(np.clip((y1 - pad_y) / scale, 0, height)),
                float(np.clip((x2 - pad_x) / scale, 0, width)),
                float(np.clip((y2 - pad_y) / scale, 0, height)),
            )
            label = COCO_NAMES[k] if 0 <= k < len(COCO_NAMES) else f"object {k}"
            detections.append(Detection(label, float(score), box))
        detections.sort(key=lambda d: d.conf, reverse=True)
        return detections