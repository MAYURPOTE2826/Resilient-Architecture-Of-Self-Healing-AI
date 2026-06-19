"""
Pytest configuration and shared fixtures for test suite.
"""
import os
import sys
import pytest
import sqlite3
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set test environment variables
os.environ["DATA_DIR"] = "/tmp/test_data"
os.environ["SENDER_EMAIL"] = "test@example.com"
os.environ["SENDER_PASSWORD"] = "test_pass"
os.environ["ADMIN_EMAIL"] = "admin@example.com"


@pytest.fixture
def test_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def test_db(test_db_path):
    """Create an in-memory test database with schema."""
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Create events table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        fault_type TEXT,
        confidence REAL,
        timestamp TEXT
    )
    """)
    
    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)
    """)
    
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def sample_metrics():
    """Provide sample system metrics for testing."""
    return {
        "cpu_usage": 45.2,
        "memory_usage": 62.1,
        "latency": 25.5,
        "disk_io": 1.23
    }


@pytest.fixture
def anomaly_metrics():
    """Provide metrics that should trigger anomaly detection."""
    return {
        "cpu_usage": 95.0,  # Very high
        "memory_usage": 88.5,  # High
        "latency": 150.0,  # Very high
        "disk_io": 50.0  # Very high
    }
