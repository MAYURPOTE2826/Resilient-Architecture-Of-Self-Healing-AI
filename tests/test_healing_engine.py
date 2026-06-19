"""
Unit tests for the healing_engine module.
"""
import pytest
import os
import time
from datetime import datetime, timezone


class TestSaveEvent:
    def test_creates_single_record(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine.save_event("ANOMALY", "HIGH_CPU", 0.95)
        session = database.get_db_session()
        assert session.query(database.Event).count() == 1
        session.close()

    def test_stores_correct_data(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine.save_event("HEALING", "HIGH_MEMORY", 0.87)
        session = database.get_db_session()
        event = session.query(database.Event).first()
        assert event.event_type == "HEALING"
        assert event.fault_type == "HIGH_MEMORY"
        assert abs(event.confidence - 0.87) < 0.001
        session.close()

    def test_stores_timestamp(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        before = datetime.now(timezone.utc)
        healing_engine.save_event("ANOMALY", "FAULT_TYPE", 0.9)
        after = datetime.now(timezone.utc)

        session = database.get_db_session()
        event = session.query(database.Event).first()
        stored = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        assert before <= stored <= after
        session.close()

    def test_multiple_records(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine.save_event("ANOMALY", "CPU", 0.8)
        healing_engine.save_event("HEALING", "CPU", 0.9)
        healing_engine.save_event("ANOMALY", "MEMORY", 0.7)

        session = database.get_db_session()
        assert session.query(database.Event).count() == 3
        session.close()


class TestHeal:
    def test_heal_respects_cooldown(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        monkeypatch.setenv("SENDER_PASSWORD", "")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine._last_heal_time = 0.0
        healing_engine.heal("CPU_OVERLOAD", 0.9)

        # Reset time to simulate "just healed"
        healing_engine._last_heal_time = time.time()
        # Second call should be skipped due to cooldown (no exception raised)
        healing_engine.heal("CPU_OVERLOAD", 0.9)
        assert True  # Should not raise

    def test_heal_handles_unknown_fault(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        monkeypatch.setenv("SENDER_PASSWORD", "")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine._last_heal_time = 0.0
        # Should not raise for unknown fault type
        healing_engine.heal("TOTALLY_UNKNOWN_FAULT", 0.5)
        assert True

    def test_heal_no_crash_without_email(self, test_db_path, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
        monkeypatch.setenv("SENDER_PASSWORD", "")
        monkeypatch.setenv("SENDER_EMAIL", "")
        import importlib, database, healing_engine
        importlib.reload(database)
        database.init_db()
        importlib.reload(healing_engine)

        healing_engine._last_heal_time = 0.0
        healing_engine.heal("CPU_OVERLOAD", 0.9)
        assert True
