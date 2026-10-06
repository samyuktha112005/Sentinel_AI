from ultralytics import YOLO
from config import MODEL_PATH, CONFIDENCE_THRESHOLD


model = YOLO(MODEL_PATH)


def detect_objects(frame):
    results = model(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )

    return results[0]


def get_detections(frame):
    result = detect_objects(frame)
    detections = []

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])
        class_name = result.names[class_id]

        detections.append({
            "class": class_name,
            "confidence": confidence,
            "bbox": (x1, y1, x2, y2)
        })

    return detections