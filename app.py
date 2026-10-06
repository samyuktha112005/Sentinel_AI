import os
from datetime import datetime

import cv2
import gradio as gr
import numpy as np

from config import EVIDENCE_FOLDER, RESTRICTED_ZONE
from database import create_table, get_connection, log_event
from detector import get_detections
from event_detector import detect_events, tracked_persons


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

create_table()


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE event_type = 'Person Detected'
    """)
    person_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE event_type = 'Vehicle Detected'
    """)
    vehicle_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
        WHERE severity = 'CRITICAL'
    """)
    critical_events = cursor.fetchone()[0]

    conn.close()

    return (
        total_events,
        person_events,
        vehicle_events,
        critical_events
    )


# ---------------------------------------------------------
# EVENT HISTORY
# ---------------------------------------------------------

def get_event_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            event_type,
            severity,
            timestamp,
            evidence_path
        FROM events
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# ---------------------------------------------------------
# RESTRICTED ZONE DRAWING
# ---------------------------------------------------------

def draw_restricted_zone(
    frame,
    frame_width,
    frame_height
):
    base_width = 1920
    base_height = 1080

    scale_x = frame_width / base_width
    scale_y = frame_height / base_height

    points = np.array([
        (
            int(x * scale_x),
            int(y * scale_y)
        )
        for x, y in RESTRICTED_ZONE
    ], dtype=np.int32)

    overlay = frame.copy()

    # Transparent red restricted area
    cv2.fillPoly(
        overlay,
        [points],
        (0, 0, 255)
    )

    frame = cv2.addWeighted(
        overlay,
        0.15,
        frame,
        0.85,
        0
    )

    # Restricted-zone boundary
    cv2.polylines(
        frame,
        [points],
        True,
        (0, 0, 255),
        4
    )

    # Label
    label_x = int(points[0][0])
    label_y = max(
        int(points[0][1]) - 15,
        30
    )

    cv2.putText(
        frame,
        "RESTRICTED ZONE",
        (label_x, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    return frame


# ---------------------------------------------------------
# VIDEO PROCESSING
# ---------------------------------------------------------

def process_video(video_path):

    if not video_path:
        return (
            None,
            [],
            0,
            0,
            0,
            0
        )

    # Reset person tracking for a new video
    tracked_persons.clear()

    os.makedirs(
        EVIDENCE_FOLDER,
        exist_ok=True
    )

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(
            "Unable to open the selected video."
        )

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 25

    output_path = "sentinel_output.mp4"

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height)
    )

    current_events = []

    frame_number = 0
    last_event = None

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame_number += 1

        # ---------------------------------------------
        # Draw restricted zone
        # ---------------------------------------------

        frame = draw_restricted_zone(
            frame,
            width,
            height
        )

        # ---------------------------------------------
        # YOLO detection
        # ---------------------------------------------

        detections = get_detections(
            frame
        )

        # ---------------------------------------------
        # Safety event detection
        # ---------------------------------------------

        event = detect_events(
            detections,
            width,
            height
        )

        event_type = event["event_type"]
        severity = event["severity"]

        # ---------------------------------------------
        # Draw detected objects
        # ---------------------------------------------

        for detection in detections:

            x1, y1, x2, y2 = detection["bbox"]

            class_name = detection["class"]

            confidence = detection["confidence"]

            # Bounding box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Object label
            label = (
                f"{class_name} "
                f"{confidence:.2f}"
            )

            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(y1 - 10, 20)
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # ---------------------------------------------
        # Display event information
        # ---------------------------------------------

        cv2.putText(
            frame,
            f"Event: {event_type}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            f"Severity: {severity}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        # ---------------------------------------------
        # Display counts
        # ---------------------------------------------

        cv2.putText(
            frame,
            f"People: {event['person_count']}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Vehicles: {event['vehicle_count']}",
            (20, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Bags: {event['bag_count']}",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # ---------------------------------------------
        # Save important events
        # ---------------------------------------------

        if (
            event_type != "No Threat"
            and event_type != last_event
        ):

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            evidence_name = (
                f"event_{frame_number}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            )

            evidence_path = os.path.join(
                EVIDENCE_FOLDER,
                evidence_name
            )

            # Save evidence frame
            cv2.imwrite(
                evidence_path,
                frame
            )

            # Store event in SQLite
            log_event(
                event_type,
                severity,
                timestamp,
                evidence_path
            )

            # Show event in current-video table
            current_events.append([
                event_type,
                severity,
                timestamp,
                evidence_path
            ])

            last_event = event_type

        # ---------------------------------------------
        # Write processed frame
        # ---------------------------------------------

        writer.write(frame)

    cap.release()
    writer.release()

    # ---------------------------------------------
    # Updated dashboard numbers
    # ---------------------------------------------

    (
        total_events,
        person_events,
        vehicle_events,
        critical_events
    ) = get_dashboard_stats()

    return (
        output_path,
        current_events,
        total_events,
        person_events,
        vehicle_events,
        critical_events
    )


# ---------------------------------------------------------
# GRADIO APPLICATION
# ---------------------------------------------------------

with gr.Blocks(
    title="Sentinel AI"
) as app:

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    gr.Markdown(
        """
        # 🛡️ Sentinel AI

        ## Intelligent Safety Event Detection System

        **AI-powered surveillance analysis using YOLO,
        OpenCV, SQLite and Gradio.**
        """
    )

    # -----------------------------------------------------
    # DASHBOARD
    # -----------------------------------------------------

    gr.Markdown(
        """
        ## 📊 Safety Dashboard

        Real-time summary of recorded safety events.
        """
    )

    with gr.Row():

        total_events = gr.Number(
            label="Total Events",
            value=0,
            interactive=False
        )

        person_events = gr.Number(
            label="Person Events",
            value=0,
            interactive=False
        )

        vehicle_events = gr.Number(
            label="Vehicle Events",
            value=0,
            interactive=False
        )

        critical_events = gr.Number(
            label="Critical Events",
            value=0,
            interactive=False
        )

    refresh_dashboard = gr.Button(
        "🔄 Refresh Dashboard"
    )

    refresh_dashboard.click(
        fn=get_dashboard_stats,
        inputs=None,
        outputs=[
            total_events,
            person_events,
            vehicle_events,
            critical_events
        ]
    )

    # -----------------------------------------------------
    # VIDEO ANALYSIS
    # -----------------------------------------------------

    gr.Markdown(
        """
        ## 🎥 Video Analysis
        """
    )

    video_input = gr.Video(
        label="Upload Surveillance Video"
    )

    process_button = gr.Button(
        "🔍 Analyze Video",
        variant="primary"
    )

    video_output = gr.Video(
        label="Processed Video"
    )

    current_events = gr.Dataframe(
        headers=[
            "Event",
            "Severity",
            "Timestamp",
            "Evidence"
        ],
        label="Events From Current Video"
    )

    process_button.click(
        fn=process_video,
        inputs=video_input,
        outputs=[
            video_output,
            current_events,
            total_events,
            person_events,
            vehicle_events,
            critical_events
        ]
    )

    # -----------------------------------------------------
    # EVENT HISTORY
    # -----------------------------------------------------

    gr.Markdown(
        """
        ## 📋 Event History

        Previously recorded safety events stored in SQLite.
        """
    )

    history_button = gr.Button(
        "🔄 Refresh Event History"
    )

    history_output = gr.Dataframe(
        headers=[
            "ID",
            "Event",
            "Severity",
            "Timestamp",
            "Evidence"
        ],
        label="All Recorded Events"
    )

    history_button.click(
        fn=get_event_history,
        inputs=None,
        outputs=history_output
    )


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

app.launch()