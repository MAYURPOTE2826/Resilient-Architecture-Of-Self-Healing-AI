with open('api.py', 'r') as f:
    content = f.read()

health_endpoints = """
# ==========================================
# Reliability / Health Probes
# ==========================================

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/live")
def live():
    return jsonify({"status": "alive"}), 200

@app.route("/ready")
def ready():
    try:
        conn = get_connection()
        conn.close()
        return jsonify({"status": "ready", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "not_ready", "error": str(e)}), 503
"""

content = content.replace('# ==========================================\n# Process Monitoring API', health_endpoints + '\n# ==========================================\n# Process Monitoring API')

with open('api.py', 'w') as f:
    f.write(content)
