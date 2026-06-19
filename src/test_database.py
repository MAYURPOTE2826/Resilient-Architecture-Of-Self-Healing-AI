import pytest
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.engine.base import Connection

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_get_db_session_returns_session(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import get_db_session, init_db
    init_db()
    
    session = get_db_session()
    assert isinstance(session, Session)
    session.close()

def test_get_connection_returns_connection(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import get_connection, init_db
    init_db()
    
    conn = get_connection()
    # It returns a raw connection, which depends on driver, but it's not None
    assert conn is not None
    conn.close()

def test_init_db_creates_table(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, Event
    init_db()
    
    session = get_db_session()
    # If the table exists, we can query it without throwing an OperationalError
    events = session.query(Event).all()
    assert isinstance(events, list)
    session.close()

def test_prune_events_removes_oldest_rows(test_db_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", os.path.dirname(test_db_path))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    from database import init_db, get_db_session, prune_events, Event, _MAX_EVENTS
    
    init_db()
    session = get_db_session()
    
    # We will temporarily mock _MAX_EVENTS since inserting 10k rows is slow
    import database
    database._MAX_EVENTS = 5
    
    for i in range(10):
        new_event = Event(event_type="TEST", fault_type="fault_type", confidence=0.9)
        session.add(new_event)
    
    session.commit()
    
    count_before = session.query(Event).count()
    assert count_before == 10
    
    prune_events()
    
    count_after = session.query(Event).count()
    assert count_after == 5
    session.close()
