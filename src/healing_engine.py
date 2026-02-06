import time
from alert_service import send_alert
from database import get_connection
from datetime import datetime

LAST_HEAL_TIME = 0
COOLDOWN = 60  # seconds

def heal(fault_type, confidence):
    global LAST_HEAL_TIME
    now = time.time()

    if now - LAST_HEAL_TIME < COOLDOWN:
        print("⏳ Healing skipped due to cooldown")
        return

    # === Healing Action ===
    print(f"🔄 System healing triggered for fault: {fault_type}")

    # === Send Email Alert ===
    subject = "🚨 Self-Healing System Alert"
    message = f"""
Self-Healing Action Triggered

Fault Detected : {fault_type}
Confidence     : {confidence}
Action Taken   : System Recovery
Time           : {time.ctime()}
"""

    send_alert(subject, message)

    # === Save event to DB ===
    save_event("HEALING", fault_type, confidence)

    LAST_HEAL_TIME = now


def save_event(event_type, fault_type, confidence):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO events (event_type, fault_type, confidence, timestamp)
    VALUES (?, ?, ?, ?)
    """, (event_type, fault_type, confidence, datetime.now()))

    conn.commit()
    conn.close()
