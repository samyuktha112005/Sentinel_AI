import math
import time

from config import RESTRICTED_ZONE, LOITERING_TIME


tracked_persons = {}
tracked_objects = {}

VEHICLE_CLASSES = {
    "car",
    "motorcycle",
    "bus",
    "truck",
    "bicycle",
}

BAG_CLASSES = {
    "backpack",
    "handbag",
    "suitcase",
}

BASE_WIDTH = 1920
BASE_HEIGHT = 1080


def get_center(bbox):
    x1, y1, x2, y2 = bbox

    return (
        (x1 + x2) // 2,
        (y1 + y2) // 2
    )


def distance(point1, point2):
    return math.sqrt(
        (point1[0] - point2[0]) ** 2
        + (point1[1] - point2[1]) ** 2
    )


def get_scaled_zone(frame_width, frame_height):
    scale_x = frame_width / BASE_WIDTH
    scale_y = frame_height / BASE_HEIGHT

    return [
        (
            int(x * scale_x),
            int(y * scale_y)
        )
        for x, y in RESTRICTED_ZONE
    ]


def is_inside_restricted_zone(
    bbox,
    frame_width,
    frame_height
):
    center_x, center_y = get_center(bbox)

    zone = get_scaled_zone(
        frame_width,
        frame_height
    )

    zone_x = [point[0] for point in zone]
    zone_y = [point[1] for point in zone]

    return (
        min(zone_x) <= center_x <= max(zone_x)
        and
        min(zone_y) <= center_y <= max(zone_y)
    )


def make_track_key(class_name, center):
    x, y = center

    return (
        f"{class_name}_"
        f"{x // 60}_"
        f"{y // 60}"
    )


def cleanup_old_tracks(current_time):
    # Keep a person/object long enough for loitering
    # detection to complete.
    track_timeout = max(
        LOITERING_TIME * 2,
        30
    )

    for key in list(tracked_persons.keys()):

        if (
            current_time
            - tracked_persons[key]["last_seen"]
            > track_timeout
        ):
            del tracked_persons[key]

    for key in list(tracked_objects.keys()):

        if (
            current_time
            - tracked_objects[key]["last_seen"]
            > track_timeout
        ):
            del tracked_objects[key]


def update_person_tracking(
    center,
    current_time
):
    track_key = make_track_key(
        "person",
        center
    )

    if track_key not in tracked_persons:

        tracked_persons[track_key] = {
            "position": center,
            "start_time": current_time,
            "last_seen": current_time
        }

        return False

    person = tracked_persons[track_key]

    movement = distance(
        person["position"],
        center
    )

    person["last_seen"] = current_time

    # Person is staying roughly in the same area
    if movement < 30:

        elapsed = (
            current_time
            - person["start_time"]
        )

        if elapsed >= LOITERING_TIME:
            return True

    else:

        # Person moved significantly,
        # so restart the loitering timer.
        person["position"] = center
        person["start_time"] = current_time

    return False


def detect_events(
    detections,
    frame_width,
    frame_height
):
    current_time = time.time()

    cleanup_old_tracks(
        current_time
    )

    person_count = 0
    vehicle_count = 0
    bag_count = 0

    restricted_zone_event = False
    loitering_event = False
    unattended_object_event = False

    person_positions = []

    # ---------------------------------------------------------
    # PERSON AND VEHICLE DETECTION
    # ---------------------------------------------------------

    for detection in detections:

        class_name = detection["class"]
        bbox = detection["bbox"]

        center = get_center(bbox)

        if class_name == "person":

            person_count += 1

            person_positions.append(
                center
            )

            # Loitering detection
            if update_person_tracking(
                center,
                current_time
            ):
                loitering_event = True

            # Restricted zone detection
            if is_inside_restricted_zone(
                bbox,
                frame_width,
                frame_height
            ):
                restricted_zone_event = True

        elif class_name in VEHICLE_CLASSES:

            vehicle_count += 1

            # Vehicle inside restricted zone
            if is_inside_restricted_zone(
                bbox,
                frame_width,
                frame_height
            ):
                restricted_zone_event = True

    # ---------------------------------------------------------
    # UNATTENDED BAG DETECTION
    # ---------------------------------------------------------

    for detection in detections:

        class_name = detection["class"]
        bbox = detection["bbox"]

        if class_name not in BAG_CLASSES:
            continue

        bag_count += 1

        center = get_center(bbox)

        track_key = make_track_key(
            class_name,
            center
        )

        if track_key not in tracked_objects:

            tracked_objects[track_key] = {
                "position": center,
                "start_time": current_time,
                "last_seen": current_time
            }

            continue

        obj = tracked_objects[track_key]

        movement = distance(
            obj["position"],
            center
        )

        obj["last_seen"] = current_time

        if movement < 20:

            elapsed = (
                current_time
                - obj["start_time"]
            )

            person_nearby = False

            for person_position in person_positions:

                if distance(
                    center,
                    person_position
                ) < 120:

                    person_nearby = True
                    break

            if (
                elapsed >= LOITERING_TIME
                and not person_nearby
            ):
                unattended_object_event = True

        else:

            obj["position"] = center
            obj["start_time"] = current_time

    # ---------------------------------------------------------
    # EVENT PRIORITY
    # ---------------------------------------------------------

    if restricted_zone_event:

        event_type = "Restricted Zone Entry"
        severity = "CRITICAL"

    elif unattended_object_event:

        event_type = "Unattended Object Detected"
        severity = "CRITICAL"

    elif loitering_event:

        event_type = "Loitering Detected"
        severity = "CRITICAL"

    elif person_count > 0:

        event_type = "Person Detected"
        severity = "WARNING"

    elif vehicle_count > 0:

        event_type = "Vehicle Detected"
        severity = "WARNING"

    else:

        event_type = "No Threat"
        severity = "NORMAL"

    return {
        "event_type": event_type,
        "severity": severity,
        "person_count": person_count,
        "vehicle_count": vehicle_count,
        "bag_count": bag_count,
        "restricted_zone": restricted_zone_event,
        "loitering": loitering_event,
        "unattended_object": unattended_object_event
    }