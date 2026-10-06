import cv2


def read_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError("Unable to open video")

    while True:
        success, frame = cap.read()

        if not success:
            break

        yield frame

    cap.release()