import sqlite3

DB_PATH = "database/sentinel.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            severity TEXT,
            timestamp TEXT,
            evidence_path TEXT
        )
    """)

    conn.commit()
    conn.close()


def log_event(event_type, severity, timestamp, evidence_path):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (event_type, severity, timestamp, evidence_path)
        VALUES (?, ?, ?, ?)
    """, (event_type, severity, timestamp, evidence_path))

    conn.commit()
    conn.close()
    