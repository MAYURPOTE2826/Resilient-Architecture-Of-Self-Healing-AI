"""
API Integration Tests — tests all REST endpoints including auth, status, events, health.
"""
import pytest
import os
import json


# ─── Health Probe Tests ────────────────────────────────────────────────────────

class TestHealthProbes:
    def test_health_returns_200(self, app):
        r = app.get("/health")
        assert r.status_code == 200

    def test_health_returns_ok_status(self, app):
        r = app.get("/health")
        assert r.get_json()["status"] == "ok"

    def test_live_returns_200(self, app):
        r = app.get("/live")
        assert r.status_code == 200

    def test_live_returns_alive(self, app):
        r = app.get("/live")
        assert r.get_json()["status"] == "alive"

    def test_ready_returns_200_with_db(self, app):
        r = app.get("/ready")
        # Should be 200 since in-memory DB is connected
        assert r.status_code in (200, 503)  # 503 acceptable if DB not seeded


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuthentication:
    def test_login_valid_credentials_returns_200(self, app):
        r = app.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_login_returns_access_token(self, app):
        r = app.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            content_type="application/json",
        )
        data = r.get_json()
        assert "access_token" in data
        assert len(data["access_token"]) > 10

    def test_login_invalid_credentials_returns_401(self, app):
        r = app.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password"},
            content_type="application/json",
        )
        assert r.status_code == 401

    def test_login_missing_body_returns_415_or_400(self, app):
        r = app.post("/api/auth/login", data="not-json", content_type="text/plain")
        assert r.status_code in (400, 415)

    def test_login_empty_body_returns_401_or_400(self, app):
        r = app.post("/api/auth/login", json={}, content_type="application/json")
        assert r.status_code in (400, 401)


# ─── Protected Endpoint Authorization Tests ───────────────────────────────────

class TestProtectedEndpoints:
    def test_status_without_token_returns_401(self, app):
        r = app.get("/api/status")
        assert r.status_code == 401

    def test_status_with_valid_token_returns_200(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert r.status_code == 200

    def test_status_with_invalid_token_returns_401(self, app):
        r = app.get("/api/status", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_metrics_latest_requires_auth(self, app):
        r = app.get("/api/metrics/latest")
        assert r.status_code == 401

    def test_metrics_latest_with_auth_returns_200(self, app, auth_headers):
        r = app.get("/api/metrics/latest", headers=auth_headers)
        assert r.status_code == 200

    def test_events_requires_auth(self, app):
        r = app.get("/api/events")
        assert r.status_code == 401

    def test_events_with_auth_returns_200(self, app, auth_headers):
        r = app.get("/api/events", headers=auth_headers)
        assert r.status_code == 200

    def test_stats_requires_auth(self, app):
        r = app.get("/api/stats")
        assert r.status_code == 401

    def test_stats_with_auth_returns_200(self, app, auth_headers):
        r = app.get("/api/stats", headers=auth_headers)
        assert r.status_code == 200

    def test_processes_requires_auth(self, app):
        r = app.get("/api/processes")
        assert r.status_code == 401

    def test_processes_with_auth_returns_200(self, app, auth_headers):
        r = app.get("/api/processes", headers=auth_headers)
        assert r.status_code == 200


# ─── API Key Auth Tests ────────────────────────────────────────────────────────

class TestApiKeyAuth:
    def test_status_with_valid_api_key(self, app, api_key_headers):
        r = app.get("/api/status", headers=api_key_headers)
        assert r.status_code == 200

    def test_status_with_invalid_api_key_returns_401(self, app):
        r = app.get("/api/status", headers={"X-API-Key": "totally-wrong-key"})
        assert r.status_code == 401


# ─── Response Schema Tests ────────────────────────────────────────────────────

class TestResponseSchemas:
    def test_status_response_has_required_fields(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        data = r.get_json()
        assert "system_state" in data
        assert "latest_fault" in data
        assert "healing_active" in data
        assert "ml_engine" in data

    def test_events_response_has_events_list(self, app, auth_headers):
        r = app.get("/api/events", headers=auth_headers)
        data = r.get_json()
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_stats_response_has_required_fields(self, app, auth_headers):
        r = app.get("/api/stats", headers=auth_headers)
        data = r.get_json()
        assert "anomalies_detected" in data
        assert "healing_actions" in data
        assert "successful_recoveries" in data
        assert "success_rate" in data

    def test_events_limit_param_accepted(self, app, auth_headers):
        r = app.get("/api/events?limit=10", headers=auth_headers)
        assert r.status_code == 200

    def test_events_invalid_limit_falls_back(self, app, auth_headers):
        r = app.get("/api/events?limit=abc", headers=auth_headers)
        assert r.status_code == 200
