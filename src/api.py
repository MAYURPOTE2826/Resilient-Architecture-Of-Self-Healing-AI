import threading
import time
from collections import deque



from flask import Flask, jsonify, Response, send_from_directory
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from database import get_connection
from metrics_collector import collect_metrics
from anomaly_detector import detect_anomaly
from fault_classifier import classify_fault
from healing_engine import heal
from system_state import SystemState
from logger import logger
from prometheus_exporter import anomalies_total, healings_total, system_state

app = Flask(__name__)

# ===============================
# ML ENGINE BACKGROUND THREAD
# ===============================

WINDOW_SIZE = 5
MIN_ANOMALIES = 3
CONFIDENCE_THRESHOLD = 0.01

def start_ml_engine():
    history = deque(maxlen=WINDOW_SIZE)
    state = SystemState.NORMAL

    while True:
        try:
            metrics = collect_metrics()
            logger.info(f"Metrics: {metrics}")

            anomaly = detect_anomaly(metrics)

            if anomaly["status"] == "ANOMALY" and anomaly["confidence"] > CONFIDENCE_THRESHOLD:
                anomalies_total.inc()
                history.append(1)
            else:
                history.append(0)

            system_state.set(state.value)

            if sum(history) >= MIN_ANOMALIES:
                state = SystemState.DEGRADED
                system_state.set(state.value)

                fault = classify_fault(metrics)

                state = SystemState.HEALING
                system_state.set(state.value)

                heal(fault, anomaly["confidence"])
                healings_total.inc()

                state = SystemState.RECOVERED
                system_state.set(state.value)

                history.clear()

        except Exception as e:
            logger.error(f"System crashed: {e}")

        time.sleep(5)


# ===============================
# FRONTEND ROUTES
# ===============================

@app.route("/")
def ui():
    return send_from_directory("../frontend", "index.html")

@app.route("/api/events")
def get_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()

    events = []
    for r in rows:
        events.append({
            "id": r[0],
            "event_type": r[1],
            "fault_type": r[2],
            "confidence": r[3],
            "timestamp": r[4]
        })

    return jsonify(events)

@app.route("/api/status")
def status():
    return jsonify({
        "system": "RUNNING",
        "ml_engine": "ACTIVE"
    })

# ===============================
# PROMETHEUS METRICS ROUTE
# ===============================

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    threading.Thread(target=start_ml_engine, daemon=True).start()
    
    print("\n🚀 Self-Healing AI System Started")
    print("🌐 Open your browser and go to:")
    print("👉 http://127.0.0.1:5000\n")

    app.run(host="127.0.0.1", port=5000)
