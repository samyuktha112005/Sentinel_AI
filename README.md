# Sentinel AI

## Intelligent Safety Event Detection System

Sentinel AI is an AI-powered surveillance system that analyzes video footage and detects safety-related events using computer vision.

### Features

- Person detection
- Vehicle detection
- Restricted-zone entry detection
- Loitering detection
- Unattended-object detection
- Normal, Warning, and Critical event classification
- Evidence-frame saving
- SQLite event logging
- Event history
- Safety dashboard
- Processed-video output
- Gradio web interface

### Technology Stack

- Python
- YOLO
- OpenCV
- Gradio
- SQLite

### How It Works

Surveillance Video → YOLO Detection → Event Detection → Severity Classification → SQLite → Evidence & Dashboard

## How to Run

### 1. Activate the virtual environment

```bash
venv\Scripts\activate
```

### 2. Install the required libraries

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

### 4. Open the application

Open the local URL shown in the terminal.

Usually:

```text
http://127.0.0.1:7860
```

If port 7860 is already in use, Gradio may automatically start on another port such as:

```text
http://127.0.0.1:7861
```

### Safety Event Classification

**NORMAL**
- No safety threat detected

**WARNING**
- Person detected
- Vehicle detected

**CRITICAL**
- Restricted Zone Entry
- Loitering Detected
- Unattended Object Detected

### Testing

The project includes automated tests for the main safety-event detection features.

Run:

```bash
python test_event_detection.py
```

Expected result:

```text
Restricted Zone Test: PASSED
Loitering Test: PASSED
Unattended Object Test: PASSED

ALL SAFETY EVENT TESTS PASSED!
```