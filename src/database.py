import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
DB_PATH = os.path.join(DATA_DIR, "self_healing.db")

_MAX_EVENTS = 10_000   # cap table size — oldest rows pruned when exceeded


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    # WAL mode: concurrent readers don't block the writer (essential for Flask + ML thread)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        fault_type TEXT,
        confidence REAL,
        timestamp TEXT
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)
    """)

    conn.commit()
    conn.close()


def prune_events() -> None:
    """Delete oldest rows so the table never exceeds _MAX_EVENTS entries."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM events")
        count = cur.fetchone()[0]
        if count > _MAX_EVENTS:
            excess = count - _MAX_EVENTS
            cur.execute(
                "DELETE FROM events WHERE id IN "
                "(SELECT id FROM events ORDER BY id ASC LIMIT ?)",
                (excess,),
            )
            conn.commit()
    finally:
        conn.close()
