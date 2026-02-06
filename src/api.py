from flask import Flask, jsonify
from database import get_connection
from flask import send_from_directory

app = Flask(__name__)


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

if __name__ == "__main__":
    app.run(port=5000, debug=True)

