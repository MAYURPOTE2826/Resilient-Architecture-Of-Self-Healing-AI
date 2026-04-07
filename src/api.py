import ipaddress
import threading
import time
from collections import deque

from flask import Flask, jsonify, Response, request, send_from_directory

from database import get_connection, init_db
from metrics_collector import collect_metrics
from anomaly_detector import detect_anomaly
from fault_classifier import classify_fault
from healing_engine import heal, save_event
from system_state import SystemState
from logger import logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_exporter import anomalies_total, healings_total, system_state as prom_state, start_exporter

app = Flask(__name__)

# ── Rate limiting ──────────────────────────────────────────────────────────────
limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])

# ── Security headers on every response ────────────────────────────────────────
@app.after_request
def _set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )
    return response


# ===============================
# SHARED STATE (thread-safe)
# ===============================

_state_lock = threading.Lock()
_current_state: SystemState = SystemState.NORMAL


def _set_state(s: SystemState) -> None:
    global _current_state
    with _state_lock:
        _current_state = s
    prom_state.set(s.value)


def _get_state() -> SystemState:
    with _state_lock:
        return _current_state


# ===============================
# ML ENGINE BACKGROUND THREAD
# ===============================

WINDOW_SIZE = 5
MIN_ANOMALIES = 3
CONFIDENCE_THRESHOLD = 0.6      # Z-score: 2.5σ → 0.625 confidence
MAX_CONSECUTIVE_ERRORS = 10     # circuit breaker threshold


def start_ml_engine() -> None:
    history = deque(maxlen=WINDOW_SIZE)
    consecutive_errors = 0
    last_fault_type = "unknown"   # always tracks the most recent classified fault

    while True:
        try:
            metrics = collect_metrics()
            logger.info(f"Metrics: {metrics}")

            anomaly = detect_anomaly(metrics)
            consecutive_errors = 0   # reset circuit breaker on success

            if anomaly["status"] == "ANOMALY" and anomaly["confidence"] > CONFIDENCE_THRESHOLD:
                last_fault_type = classify_fault(metrics)
                save_event(
                    event_type=anomaly["status"],
                    fault_type=last_fault_type,
                    confidence=anomaly["confidence"],
                )
                anomalies_total.inc()
                history.append(1)
            else:
                history.append(0)

            if sum(history) >= MIN_ANOMALIES:
                _set_state(SystemState.DEGRADED)
                time.sleep(2)

                _set_state(SystemState.HEALING)
                heal(last_fault_type, anomaly["confidence"])
                healings_total.inc()
                time.sleep(2)

                _set_state(SystemState.RECOVERED)
                history.clear()
                time.sleep(1)

                _set_state(SystemState.NORMAL)

        except (KeyboardInterrupt, SystemExit):
            raise   # never swallow shutdown signals

        except Exception as e:
            consecutive_errors += 1
            logger.error(
                f"ML engine error ({consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}): {e}"
            )
            _set_state(SystemState.NORMAL)
            history.clear()

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.critical(
                    "ML engine: too many consecutive errors — stopping engine to prevent runaway loop"
                )
                break   # exit the loop; daemon thread ends cleanly

        time.sleep(5)


# ===============================
# HELPERS
# ===============================

def _is_internal_ip(ip: str) -> bool:
    """Allow localhost and RFC-1918 private ranges only."""
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_loopback or addr.is_private
    except ValueError:
        return False


# ===============================
# ROUTES
# ===============================

@app.route("/")
def ui():
    return send_from_directory("../frontend", "index.html")


@app.route("/api/events")
@limiter.limit("30 per minute")
def get_events():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM events ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify([
        {
            "id":         r[0],
            "event_type": r[1],
            "fault_type": r[2],
            "confidence": r[3],
            "timestamp":  r[4],
        }
        for r in rows
    ])


@app.route("/api/status")
@limiter.limit("30 per minute")
def status():
    return jsonify({
        "system":    _get_state().name,
        "ml_engine": "ACTIVE",
    })


@app.route("/metrics")
def metrics():
    if not _is_internal_ip(request.remote_addr):
        return Response("Forbidden", status=403)
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ===============================
# STARTUP HELPERS
# ===============================

def _init_counters_from_db() -> None:
    """Restore Prometheus counters from DB so Grafana shows history after restart."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM events WHERE event_type = 'ANOMALY'")
        anomaly_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events WHERE event_type = 'HEALING'")
        healing_count = cur.fetchone()[0]
    finally:
        conn.close()

    if anomaly_count > 0:
        anomalies_total.inc(anomaly_count)
    if healing_count > 0:
        healings_total.inc(healing_count)
    logger.info(f"Counters restored from DB: anomalies={anomaly_count}, healings={healing_count}")


# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    init_db()
    _init_counters_from_db()
    start_exporter(port=8000)
    threading.Thread(target=start_ml_engine, daemon=True).start()

    logger.info("Self-Healing AI System started on http://0.0.0.0:5000")

    try:
        from waitress import serve
        logger.info("Serving with waitress (production WSGI server)")
        serve(app, host="0.0.0.0", port=5000, threads=4)
    except ImportError:
        logger.warning("waitress not installed — falling back to Flask dev server. Run: pip install waitress")
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
