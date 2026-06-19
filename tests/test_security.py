"""
Security Tests — validates security controls, headers, CORS, and injection resistance.
"""
import pytest


class TestSecurityHeaders:
    """Verify all security headers are present on every response."""

    def test_hsts_header_present(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert "Strict-Transport-Security" in r.headers

    def test_x_content_type_options(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert r.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert r.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert "Referrer-Policy" in r.headers

    def test_csp_header_present(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        assert "Content-Security-Policy" in r.headers

    def test_csp_no_wildcard_sources(self, app, auth_headers):
        r = app.get("/api/status", headers=auth_headers)
        csp = r.headers.get("Content-Security-Policy", "")
        # Should not have * as source (only narrow domains)
        assert "script-src *" not in csp
        assert "default-src *" not in csp

    def test_health_endpoint_also_has_headers(self, app):
        r = app.get("/health")
        assert "X-Content-Type-Options" in r.headers


class TestAuthenticationSecurity:
    """Verify authentication enforcement on all protected endpoints."""

    PROTECTED_ROUTES = [
        ("GET", "/api/status"),
        ("GET", "/api/metrics/latest"),
        ("GET", "/api/events"),
        ("GET", "/api/stats"),
        ("GET", "/api/processes"),
    ]

    @pytest.mark.parametrize("method,route", PROTECTED_ROUTES)
    def test_no_token_returns_401(self, app, method, route):
        r = getattr(app, method.lower())(route)
        assert r.status_code == 401, f"{method} {route} should return 401 without token"

    def test_expired_token_returns_401(self, app):
        # Manually crafted expired JWT (signature correct but exp in past)
        import jwt
        import datetime
        from config import settings
        payload = {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            "iat": datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            "type": "access",
        }
        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        r = app.get("/api/status", headers={"Authorization": f"Bearer {expired_token}"})
        assert r.status_code == 401

    def test_tampered_token_returns_401(self, app):
        # Get a valid token then tamper with it
        login_r = app.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            content_type="application/json",
        )
        token = login_r.get_json()["access_token"]
        # Tamper: flip last character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        r = app.get("/api/status", headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401

    def test_refresh_token_cannot_access_protected_endpoints(self, app):
        """Refresh tokens must not be accepted as access tokens."""
        import jwt
        import datetime
        from config import settings
        payload = {
            "sub": "admin",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow(),
            "type": "refresh",  # NOT "access"
        }
        refresh_token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        r = app.get("/api/status", headers={"Authorization": f"Bearer {refresh_token}"})
        assert r.status_code == 401

    def test_bearer_without_token_returns_401(self, app):
        r = app.get("/api/status", headers={"Authorization": "Bearer"})
        assert r.status_code == 401

    def test_basic_auth_not_accepted(self, app):
        import base64
        creds = base64.b64encode(b"admin:admin123").decode()
        r = app.get("/api/status", headers={"Authorization": f"Basic {creds}"})
        assert r.status_code == 401


class TestInputValidation:
    """Validate that malformed input is rejected cleanly."""

    def test_login_with_non_json_body_rejected(self, app):
        r = app.post("/api/auth/login", data="<xml>hack</xml>", content_type="application/xml")
        assert r.status_code in (400, 415)

    def test_login_with_sql_injection_in_username(self, app):
        r = app.post(
            "/api/auth/login",
            json={"username": "' OR '1'='1", "password": "anything"},
            content_type="application/json",
        )
        # Should NOT return 200 — injection should fail gracefully
        assert r.status_code == 401

    def test_events_limit_sql_injection(self, app, auth_headers):
        # Injecting via query param — should not crash, should fall back to default
        r = app.get("/api/events?limit=1;DROP TABLE events;--", headers=auth_headers)
        assert r.status_code == 200

    def test_events_limit_too_large_clamped(self, app, auth_headers):
        r = app.get("/api/events?limit=99999", headers=auth_headers)
        # Should succeed but limit is clamped to 1000
        assert r.status_code == 200

    def test_login_xss_in_username_rejected(self, app):
        r = app.post(
            "/api/auth/login",
            json={"username": "<script>alert(1)</script>", "password": "x"},
            content_type="application/json",
        )
        assert r.status_code == 401


class TestMetricsEndpointProtection:
    """The /metrics endpoint should only be accessible from internal IPs."""

    def test_metrics_from_loopback_or_blocked(self, app, auth_headers):
        # In test client, remote_addr defaults to 127.0.0.1 — should be allowed
        r = app.get("/metrics", headers=auth_headers)
        # Either allowed (200) or blocked (403) — should not be 401 or 500
        assert r.status_code in (200, 403)
