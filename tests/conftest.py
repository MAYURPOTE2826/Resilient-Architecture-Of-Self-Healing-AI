"""
Root conftest for all tests.
Configures sys.path, env vars, and shared fixtures.
"""
import os
import sys
import sqlite3
import pytest

# ─── Path Setup ────────────────────────────────────────────────────────────────
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))

# ─── Environment Setup (before any module import) ──────────────────────────────
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-at-least-32-chars!!")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-api-key-for-ci-testing")
os.environ.setdefault("DATA_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "data")))
os.environ.setdefault("SENDER_EMAIL", "test@example.com")
os.environ.setdefault("SENDER_PASSWORD", "")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")


# ─── Shared Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_db_path(tmp_path):
    """Provide a fresh temporary SQLite database path per test."""
    return str(tmp_path / "test.db")


@pytest.fixture(scope="function")
def test_db(test_db_path):
    """Create a temporary SQLite DB with the events schema."""
    conn = sqlite3.connect(test_db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            fault_type TEXT,
            confidence REAL,
            timestamp  TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp DESC)
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def sample_metrics():
    """Normal system metrics."""
    return {
        "cpu_usage":    45.2,
        "memory_usage": 62.1,
        "latency":      25.5,
        "disk_io":      1.23,
    }


@pytest.fixture(scope="function")
def anomaly_metrics():
    """Metrics that should trigger anomaly detection."""
    return {
        "cpu_usage":    95.0,
        "memory_usage": 88.5,
        "latency":      150.0,
        "disk_io":      50.0,
    }


@pytest.fixture(scope="function")
def mock_artifact_path(tmp_path, monkeypatch):
    """Create a minimal artifacts.joblib for anomaly-detector tests."""
    import joblib
    artifacts = {
        "stats": {
            "cpu_usage":    (50.0, 10.0),
            "memory_usage": (60.0, 15.0),
            "latency":      (30.0,  8.0),
            "disk_io":      (5.0,   2.0),
        }
    }
    artifact_file = tmp_path / "artifacts.joblib"
    joblib.dump(artifacts, artifact_file)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return str(artifact_file)


@pytest.fixture(scope="function")
def app(monkeypatch, tmp_path):
    """Create a Flask test client with an isolated in-memory DB."""
    db_url = f"sqlite:///{tmp_path / 'test_api.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    # Import after env is patched
    import importlib
    import database
    importlib.reload(database)
    database.init_db()

    import api as api_module
    api_module.app.config["TESTING"] = True
    api_module.app.config["WTF_CSRF_ENABLED"] = False
    with api_module.app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def auth_headers(app):
    """Return JWT bearer token headers for admin user."""
    response = app.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        content_type="application/json",
    )
    data = response.get_json()
    token = data.get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def api_key_headers():
    """Return X-API-Key headers for system-level access."""
    return {"X-API-Key": os.environ["ADMIN_API_KEY"]}
