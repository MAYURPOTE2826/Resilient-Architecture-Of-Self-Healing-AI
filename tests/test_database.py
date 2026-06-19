"""
Unit tests for the database module.
"""
import pytest
from sqlalchemy.orm import Session


class TestGetDbSession:
    def test_returns_session_instance(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()
        session = database.get_db_session()
        assert isinstance(session, Session)
        session.close()

    def test_session_can_query_events(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()
        session = database.get_db_session()
        events = session.query(database.Event).all()
        assert isinstance(events, list)
        session.close()


class TestInitDb:
    def test_creates_events_table(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()
        session = database.get_db_session()
        # Should not raise
        _ = session.query(database.Event).count()
        session.close()


class TestGetConnection:
    def test_returns_non_none_connection(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()
        conn = database.get_connection()
        assert conn is not None
        conn.close()


class TestPruneEvents:
    def test_prunes_excess_events(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()

        session = database.get_db_session()
        database._MAX_EVENTS = 5  # Lower the limit for this test
        for i in range(10):
            session.add(database.Event(event_type="TEST", fault_type="CPU", confidence=0.9))
        session.commit()

        assert session.query(database.Event).count() == 10
        database.prune_events()
        assert session.query(database.Event).count() == 5
        session.close()

    def test_prune_no_op_when_below_limit(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database
        importlib.reload(database)
        database.init_db()

        session = database.get_db_session()
        session.add(database.Event(event_type="TEST", fault_type="CPU", confidence=0.9))
        session.commit()
        count_before = session.query(database.Event).count()
        database.prune_events()
        count_after = session.query(database.Event).count()
        assert count_before == count_after
        session.close()
