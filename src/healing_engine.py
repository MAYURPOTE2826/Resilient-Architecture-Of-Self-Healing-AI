import threading
import time
from datetime import datetime, timezone

from alert_service import send_alert
from database import get_connection, prune_events
from logger import logger

_heal_lock = threading.Lock()
_last_heal_time: float = 0.0
_COOLDOWN = 60  # seconds — prevent rapid re-healing storms


def heal(fault_type: str, confidence: float) -> None:
    global _last_heal_time
    now = time.time()

    with _heal_lock:
        if now - _last_heal_time < _COOLDOWN:
            logger.warning("Healing skipped due to cooldown")
            return
        _last_heal_time = now

    logger.info(f"System healing triggered for fault: {fault_type}")

    subject = "Self-Healing System Alert"
    message = f"""
Self-Healing Action Triggered

Fault Detected : {fault_type}
Confidence     : {confidence:.4f}
Action Taken   : System Recovery
Time           : {time.ctime()}
"""
    send_alert(subject, message)
    save_event("HEALING", fault_type, confidence)


def save_event(event_type: str, fault_type: str, confidence: float) -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO events (event_type, fault_type, confidence, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (event_type, fault_type, confidence, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to save event to database: {e}")
    finally:
        conn.close()

    prune_events()   # keep DB from growing unbounded
