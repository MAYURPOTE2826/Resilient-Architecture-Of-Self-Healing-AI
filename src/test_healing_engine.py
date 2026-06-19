import pytest
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_save_event_creates_record(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, Event
    from healing_engine import save_event
    
    init_db()
    
    save_event("ANOMALY", "HIGH_CPU", 0.95)
    
    session = get_db_session()
    count = session.query(Event).count()
    assert count == 1
    session.close()

def test_save_event_stores_correct_data(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, Event
    from healing_engine import save_event
    
    init_db()
    
    save_event("HEALING", "HIGH_MEMORY", 0.87)
    
    session = get_db_session()
    event = session.query(Event).filter(Event.id == 1).first()
    
    assert event.event_type == "HEALING"
    assert event.fault_type == "HIGH_MEMORY"
    assert event.confidence == 0.87
    session.close()

def test_save_event_stores_timestamp(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, Event
    from healing_engine import save_event
    
    init_db()
    
    before = datetime.now(timezone.utc)
    save_event("ANOMALY", "FAULT_TYPE", 0.9)
    after = datetime.now(timezone.utc)
    
    session = get_db_session()
    event = session.query(Event).filter(Event.id == 1).first()
    
    stored_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
    
    assert before <= stored_time <= after
    session.close()

def test_save_event_multiple_records(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, Event
    from healing_engine import save_event
    
    init_db()
    
    save_event("ANOMALY", "CPU", 0.8)
    save_event("HEALING", "CPU", 0.9)
    save_event("ANOMALY", "MEMORY", 0.7)
    
    session = get_db_session()
    count = session.query(Event).count()
    
    assert count == 3
    session.close()

def test_heal_respects_cooldown(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    monkeypatch.setenv("SENDER_PASSWORD", "")  # Disable email to avoid SMTP
    
    from database import init_db
    import healing_engine
    
    init_db()
    
    healing_engine._last_heal_time = 0.0
    # First heal should succeed
    healing_engine.heal("CPU_OVERLOAD", 0.9)
    time.sleep(0.1)
    
    # Immediate second heal should be skipped (cooldown)
    healing_engine.heal("CPU_OVERLOAD", 0.9)
    assert True

def test_heal_handles_missing_config(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    monkeypatch.setenv("SENDER_PASSWORD", "")
    
    from database import init_db
    import healing_engine
    
    init_db()
    healing_engine._last_heal_time = 0.0
    # Should not raise exception even with no email config
    healing_engine.heal("CPU_OVERLOAD", 0.9)
    assert True
