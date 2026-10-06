from database import get_connection


def get_all_events():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, event_type, severity, timestamp, evidence_path
        FROM events
        ORDER BY id DESC
    """)

    events = cursor.fetchall()
    conn.close()

    return events