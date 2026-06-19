import re

with open('api.py', 'r') as f:
    content = f.read()

# Add get_db_session and Event to imports
content = content.replace(
    'from database import (\n    get_connection,\n    init_db,\n    DB_URL\n)',
    'from database import (\n    get_connection,\n    get_db_session,\n    init_db,\n    DB_URL,\n    Event\n)'
)

# Replace get_events
pattern_events = r'def get_events\(\):.*?return jsonify\(\{.*?\"events\": \[.*?for r in rows\s*\]\s*\}\)'
replacement_events = '''def get_events():

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

    return jsonify({"events": events})'''
content = re.sub(pattern_events, replacement_events, content, flags=re.DOTALL)

# Replace stats
pattern_stats = r'def stats\(\):.*?return jsonify\(\{.*?\"success_rate\": success_rate\s*\}\)'
replacement_stats = '''def stats():

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
    })'''
content = re.sub(pattern_stats, replacement_stats, content, flags=re.DOTALL)

with open('api.py', 'w') as f:
    f.write(content)
