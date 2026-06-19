import re

with open('api.py', 'r') as f:
    content = f.read()

# Replace block from import os down to the end of security headers
pattern = r'import os.*?return response'
replacement = """from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST
)

from database import (
    get_connection,
    init_db,
    DB_URL
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
from auth import require_jwt, require_role, create_access_token
from middleware import init_security, require_json_body, limiter

# ==========================================
# Flask App
# ==========================================

app = Flask(__name__)

# Initialize Security (CORS, Headers, Limiter)
init_security(app, settings)

@app.route("/api/auth/login", methods=["POST"])
@require_json_body
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    # TODO: Connect to DB users in later phase
    if username == "admin" and password == "admin123":
        access_token = create_access_token(identity=username, role="admin")
        return jsonify({"access_token": access_token}), 200
        
    return jsonify({"error": "Invalid credentials"}), 401"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Replace @auth.login_required with @require_jwt
content = content.replace('@auth.login_required', '@require_jwt')

with open('api.py', 'w') as f:
    f.write(content)
