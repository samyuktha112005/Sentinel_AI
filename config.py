# YOLO model
MODEL_PATH = "yolo11n.pt"

# Project folders
VIDEO_FOLDER = "videos"
EVIDENCE_FOLDER = "evidence"

# Detection confidence
CONFIDENCE_THRESHOLD = 0.5

# Time required to classify someone as loitering
LOITERING_TIME = 10

# Restricted area coordinates
# Format: (x, y)

RESTRICTED_ZONE = [
    (200, 100),
    (1700, 100),
    (1700, 950),
    (200, 950)
]