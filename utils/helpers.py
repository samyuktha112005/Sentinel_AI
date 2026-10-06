from datetime import datetime
from pathlib import Path
import cv2


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_folder(folder_path):
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def save_evidence(frame, folder_path, filename):
    ensure_folder(folder_path)

    file_path = Path(folder_path) / filename
    cv2.imwrite(str(file_path), frame)

    return str(file_path)