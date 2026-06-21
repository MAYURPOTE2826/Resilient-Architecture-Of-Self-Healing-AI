import hmac
import ipaddress
import threading
import time
from collections import deque
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    Response,
    request,
    send_from_directory
)

from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST
)

from database import (
    get_connection,
    get_db_session,
    init_db,
    DB_URL,
    Event
)

from metrics_collector import collect_metrics
from anomaly_detector import detect_anomaly
from fault_classifier import classify_fault

from healing_engine import (
    heal,
    save_event
)

from system_state import SystemState
from logger import logger
import psutil

from prometheus_exporter import (
    anomalies_total,
    healings_total,
    system_state as prom_state,
    start_exporter
)

from config import settings
from auth import require_jwt, require_role, create_access_token, create_refresh_token
from middleware import init_security, require_json_body, limiter
from error_handler import init_error_handlers
from health_checks import get_health_checker
from shutdown_manager import setup_signal_handlers, register_shutdown_handler
from token_manager import revoke_token
from security_utils import RequestContextManager

from werkzeug.middleware.proxy_fix import ProxyFix

# ==========================================
# Flask App
# ==========================================

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize Security (CORS, Headers, Limiter)
init_security(app, settings)

# Initialize Error Handlers
init_error_handlers(app)

# Initialize OpenTelemetry
from middleware import init_tracing
init_tracing(app)

# Initialize Signal Handlers for Graceful Shutdown
setup_signal_handlers()
register_shutdown_handler(lambda: init_db(), "database_init")


@app.route("/api/auth/login", methods=["POST"])
@require_json_body
def login():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    # Constant-time comparison to prevent timing attacks
    # Credentials are loaded from settings/environment variables
    valid_user = hmac.compare_digest(
        str(username), str(settings.ADMIN_USERNAME)
    )
    valid_pass = hmac.compare_digest(
        str(password), str(settings.ADMIN_PASSWORD)
    )

    if valid_user and valid_pass:
        access_token = create_access_token(identity=username, role="admin")
        refresh_token = create_refresh_token(identity=username)
        logger.info("User login successful", username=username)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60
        }), 200

    logger.warning("Failed login attempt", username=username, remote_addr=request.remote_addr)
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/auth/refresh", methods=["POST"])
@require_json_body
def refresh_token_endpoint():
    """Exchange a valid refresh token for a new access token."""
    data = request.get_json()
    token = data.get("refresh_token", "")

    if not token:
        return jsonify({"error": "refresh_token is required"}), 400

    from auth import decode_token
    payload = decode_token(token)

    if "error" in payload:
        return jsonify({"error": payload["error"]}), 401

    if payload.get("type") != "refresh":
        return jsonify({"error": "Invalid token type — must be a refresh token"}), 401

    identity = payload.get("sub")
    new_access = create_access_token(identity=identity, role="admin")
    logger.info("Access token refreshed", username=identity)
    return jsonify({
        "access_token": new_access,
        "token_type": "Bearer",
        "expires_in": settings.JWT_ACCESS_EXPIRE_MINUTES * 60
    }), 200


@app.route("/api/auth/logout", methods=["POST"])
@require_jwt
def logout():
    """Logout and revoke access token."""
    token = getattr(request, 'token', None)
    user = getattr(request, 'user', None)
    
    if token:
        revoke_token(token, reason="logout")
    
    if user:
        logger.info("User logged out", username=user.get("sub"))
    
    return jsonify({"message": "Logged out successfully"}), 200


# ==========================================
# Health Checks - Kubernetes/Container Probes
# ==========================================

@app.route("/health", methods=["GET"])
def health():
    """
    Detailed health check endpoint.
    Returns comprehensive health status of all components.
    """
    checker = get_health_checker()
    status = checker.get_health()
    
    # Return 503 if unhealthy, 200 otherwise
    status_code = 200 if status["status"] == "healthy" else (503 if status["status"] == "unhealthy" else 200)
    
    return jsonify(status), status_code


@app.route("/live", methods=["GET"])
def live():
    """
    Liveness probe endpoint.
    Returns whether the service process is alive.
    Used by container orchestrators to restart dead processes.
    """
    checker = get_health_checker()
    status = checker.get_liveness()
    
    # Return 200 if alive, 503 if not
    status_code = 200 if status["alive"] else 503
    
    return jsonify(status), status_code


@app.route("/ready", methods=["GET"])
def ready():
    """
    Readiness probe endpoint.
    Returns whether the service is ready to accept requests.
    Used by load balancers to route traffic.
    """
    checker = get_health_checker()
    status = checker.get_readiness()
    
    # Return 200 if ready, 503 if not
    status_code = 200 if status["ready"] else 503
    
    return jsonify(status), status_code


@app.route("/startup", methods=["GET"])
def startup():
    """
    Startup probe endpoint.
    Returns whether the service has completed startup initialization.
    """
    checker = get_health_checker()
    status = checker.get_readiness()
    
    status_code = 200 if status["ready"] else 503
    return jsonify(status), status_code



# ==========================================
# Shared State
# ==========================================

_state_lock = threading.Lock()

_current_state: SystemState = SystemState.NORMAL

_latest_metrics: dict = {}

_latest_fault: str = "NONE"

_healing_active = False


# ==========================================
# Thread Safe State Functions
# ==========================================

def _set_state(state: SystemState):

    global _current_state

    with _state_lock:

        _current_state = state

    prom_state.set(state.value)


def _get_state():

    with _state_lock:

        return _current_state


def _set_latest_metrics(metrics: dict):

    global _latest_metrics

    with _state_lock:

        _latest_metrics = metrics


def _get_latest_metrics():

    with _state_lock:

        return _latest_metrics.copy()


def _set_latest_fault(fault: str):

    global _latest_fault

    with _state_lock:

        _latest_fault = fault


def _get_latest_fault():

    with _state_lock:

        return _latest_fault


def _set_healing_status(status: bool):

    global _healing_active

    with _state_lock:

        _healing_active = status


def _get_healing_status():

    with _state_lock:

        return _healing_active


# ==========================================
# ML ENGINE CONFIG
# ==========================================

WINDOW_SIZE = 5

MIN_ANOMALIES = 3

CONFIDENCE_THRESHOLD = 0.60

MAX_CONSECUTIVE_ERRORS = 10


# ==========================================
# ML ENGINE
# ==========================================

def start_ml_engine():

    history = deque(maxlen=WINDOW_SIZE)
    history_metrics = deque(maxlen=WINDOW_SIZE)

    consecutive_errors = 0

    last_fault_type = "UNKNOWN"

    logger.info("ML Engine Started")

    while True:

        try:

            # ==================================
            # Collect Metrics
            # ==================================

            metrics = collect_metrics()

            _set_latest_metrics(metrics)
            history_metrics.append(metrics)

            logger.info(f"Metrics: {metrics}")

            # ==================================
            # Predictive Healing
            # ==================================
            cpu_history = [m.get("cpu", 0) for m in history_metrics]
            if len(cpu_history) >= 4:
                last_4 = cpu_history[-4:]
                if all(last_4[i] < last_4[i+1] for i in range(3)) and last_4[-1] >= 80:
                    logger.warning("Predictive Analytics: CPU strictly increasing and >80%. Triggering Preventive Recovery.")
                    
                    _set_state(SystemState.DEGRADED)
                    time.sleep(1)
                    
                    _set_state(SystemState.HEALING)
                    _set_healing_status(True)
                    
                    last_fault_type = "CPU_OVERLOAD"
                    _set_latest_fault(last_fault_type)
                    
                    heal(last_fault_type, 1.0)
                    healings_total.inc()
                    time.sleep(2)
                    
                    _set_state(SystemState.RECOVERED)
                    save_event("PREVENTIVE_RECOVERY", last_fault_type, 1.0)
                    time.sleep(1)
                    
                    _set_state(SystemState.NORMAL)
                    _set_healing_status(False)
                    
                    history.clear()
                    history_metrics.clear()
                    continue

            # ==================================
            # Detect Anomaly
            # ==================================

            anomaly = detect_anomaly(metrics)

            consecutive_errors = 0

            # ==================================
            # Anomaly Handling
            # ==================================

            if (
                anomaly["status"] == "ANOMALY"
                and anomaly["confidence"] > CONFIDENCE_THRESHOLD
            ):

                last_fault_type = classify_fault(metrics)

                _set_latest_fault(last_fault_type)

                logger.warning(
                    f"Anomaly Detected | "
                    f"Fault={last_fault_type} | "
                    f"Confidence={anomaly['confidence']}"
                )

                save_event(
                    event_type="ANOMALY",
                    fault_type=last_fault_type,
                    confidence=anomaly["confidence"]
                )

                anomalies_total.inc()

                history.append(1)

            else:

                history.append(0)

            # ==================================
            # Trigger Healing
            # ==================================

            if sum(history) >= MIN_ANOMALIES:

                logger.warning(
                    "Multiple anomalies detected. "
                    "Starting healing workflow."
                )

                _set_state(SystemState.DEGRADED)

                time.sleep(1)

                _set_state(SystemState.HEALING)

                _set_healing_status(True)

                heal(
                    last_fault_type,
                    anomaly["confidence"]
                )

                healings_total.inc()

                time.sleep(2)

                _set_state(SystemState.RECOVERED)

                save_event(
                    event_type="RECOVERED",
                    fault_type=last_fault_type,
                    confidence=anomaly["confidence"]
                )

                time.sleep(1)

                _set_state(SystemState.NORMAL)

                _set_healing_status(False)

                history.clear()

                logger.info("Healing workflow completed")

        except (KeyboardInterrupt, SystemExit):

            raise

        except Exception as e:

            consecutive_errors += 1

            logger.error(
                f"ML Engine Error "
                f"({consecutive_errors}/"
                f"{MAX_CONSECUTIVE_ERRORS}): {e}"
            )

            _set_state(SystemState.NORMAL)

            history.clear()

            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:

                logger.critical(
                    "Too many ML engine failures. "
                    "Stopping engine."
                )

                break

        time.sleep(5)


# ==========================================
# Internal Metrics Protection
# ==========================================

def _is_internal_ip(ip: str):

    try:

        addr = ipaddress.ip_address(ip)

        return (
            addr.is_loopback
            or addr.is_private
        )

    except ValueError:

        return False


# ==========================================
# FRONTEND ROUTES
# ==========================================

@app.route("/")
def ui():

    return send_from_directory(
        "../frontend",
        "index.html"
    )


@app.route("/<path:filename>")
def static_files(filename):

    return send_from_directory(
        "../frontend",
        filename
    )


# ==========================================
# API ROUTES
# ==========================================

@app.route("/api/status")
@limiter.limit("120 per minute")
def status():

    return jsonify({

        "system_state": _get_state().name,

        "latest_fault": _get_latest_fault(),

        "healing_active": _get_healing_status(),

        "ml_engine": "ACTIVE"
    })


@app.route("/api/metrics/latest")
@limiter.limit("120 per minute")
def latest_metrics():

    return jsonify(
        _get_latest_metrics()
    )


@app.route("/api/events")
@limiter.limit("120 per minute")
def get_events():

    try:
        limit = int(request.args.get("limit", 50))
        if not 1 <= limit <= 1000:
            limit = 50
    except ValueError:
        limit = 50

    session = get_db_session()
    try:
        rows = session.query(Event).order_by(Event.id.desc()).limit(limit).all()
        events = [
            {
                "id": r.id,
                "event_type": r.event_type,
                "fault_type": r.fault_type,
                "confidence": r.confidence,
                "timestamp": r.timestamp,
            }
            for r in rows
        ]
    finally:
        session.close()

    return jsonify({"events": events})





# ==========================================
# Process Monitoring API
# ==========================================

from cachetools import cached, TTLCache
_process_cache = TTLCache(maxsize=1, ttl=2)

@app.route("/api/processes")
@limiter.limit("120 per minute")
def processes():
    return jsonify(_fetch_processes_cached())

@cached(_process_cache)
def _fetch_processes_cached():
    process_list = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            process_list.append(proc.info)
        # Sort by CPU descending
        process_list.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
    except Exception as e:
        logger.error(f"Failed to fetch processes: {e}")
    return process_list[:50]

# ==========================================
# Recovery Statistics API
# ==========================================

@app.route("/api/stats")
@limiter.limit("120 per minute")
def stats():

    session = get_db_session()
    try:
        anomalies = session.query(Event).filter(Event.event_type == 'ANOMALY').count()
        healings = session.query(Event).filter(Event.event_type == 'HEALING').count()
        recovered = session.query(Event).filter(Event.event_type == 'RECOVERED').count()
    finally:
        session.close()

    success_rate = 0
    if healings > 0:
        success_rate = round((recovered / healings) * 100, 2)

    return jsonify({
        "anomalies_detected": anomalies,
        "healing_actions": healings,
        "successful_recoveries": recovered,
        "success_rate": success_rate
    })


# ==========================================
# Prometheus Metrics
# ==========================================

@app.route("/metrics")
def metrics():

    if not _is_internal_ip(
        request.remote_addr
    ):

        return Response(
            "Forbidden",
            status=403
        )

    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


# ==========================================
# Startup Helpers
# ==========================================

def initialize_system():

    logger.info(
        "Initializing Self-Healing System"
    )

    init_db()

    start_exporter()

    ml_thread = threading.Thread(
        target=start_ml_engine,
        daemon=True
    )

    ml_thread.start()

    logger.info(
        "ML Engine Background Thread Started"
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    import os
    initialize_system()

    # Use Waitress for production WSGI serving instead of Flask's built-in dev server
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Production WSGI Server (Waitress) on port {port}...")
    serve(app, host="0.0.0.0", port=port, threads=6)