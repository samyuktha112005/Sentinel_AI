import event_detector


def test_restricted_zone():
    event_detector.tracked_persons.clear()
    event_detector.tracked_objects.clear()

    detections = [
        {
            "class": "person",
            "confidence": 0.95,
            "bbox": (900, 450, 1000, 650)
        }
    ]

    result = event_detector.detect_events(
        detections,
        1920,
        1080
    )

    assert result["event_type"] == "Restricted Zone Entry"
    assert result["severity"] == "CRITICAL"

    print("✅ Restricted Zone Test: PASSED")


def test_loitering():
    event_detector.tracked_persons.clear()
    event_detector.tracked_objects.clear()

    detections = [
        {
            "class": "person",
            "confidence": 0.95,
            "bbox": (20, 20, 70, 70)
        }
    ]

    event_detector.detect_events(
        detections,
        1920,
        1080
    )

    for track in event_detector.tracked_persons.values():
        track["start_time"] -= 20

    result = event_detector.detect_events(
        detections,
        1920,
        1080
    )

    assert result["event_type"] == "Loitering Detected"
    assert result["severity"] == "CRITICAL"

    print("✅ Loitering Test: PASSED")


def test_unattended_object():
    event_detector.tracked_persons.clear()
    event_detector.tracked_objects.clear()

    detections = [
        {
            "class": "backpack",
            "confidence": 0.95,
            "bbox": (1800, 200, 1850, 250)
        }
    ]

    event_detector.detect_events(
        detections,
        1920,
        1080
    )

    for track in event_detector.tracked_objects.values():
        track["start_time"] -= 20

    result = event_detector.detect_events(
        detections,
        1920,
        1080
    )

    assert result["event_type"] == "Unattended Object Detected"
    assert result["severity"] == "CRITICAL"

    print("✅ Unattended Object Test: PASSED")


if __name__ == "__main__":
    test_restricted_zone()
    test_loitering()
    test_unattended_object()

    print("\n🎉 ALL SAFETY EVENT TESTS PASSED!")