"""
Tests for the auth module — JWT creation, decoding, and RBAC decorators.
"""
import pytest
import datetime


class TestJwtCreation:
    def test_create_access_token_returns_string(self):
        from auth.jwt_auth import create_access_token
        token = create_access_token("user1", "admin")
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_access_token_contains_correct_claims(self):
        from auth.jwt_auth import create_access_token, decode_token
        token = create_access_token("testuser", "admin")
        payload = decode_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_create_refresh_token_returns_string(self):
        from auth.jwt_auth import create_refresh_token
        token = create_refresh_token("user1")
        assert isinstance(token, str)

    def test_create_refresh_token_type_is_refresh(self):
        from auth.jwt_auth import create_refresh_token, decode_token
        token = create_refresh_token("user1")
        payload = decode_token(token)
        assert payload["type"] == "refresh"


class TestJwtDecoding:
    def test_decode_valid_token_returns_payload(self):
        from auth.jwt_auth import create_access_token, decode_token
        token = create_access_token("alice", "user")
        payload = decode_token(token)
        assert "sub" in payload
        assert payload["sub"] == "alice"

    def test_decode_invalid_token_returns_error(self):
        from auth.jwt_auth import decode_token
        result = decode_token("totally.invalid.token")
        assert "error" in result

    def test_decode_expired_token_returns_error(self):
        import jwt
        from config import settings
        from auth.jwt_auth import decode_token
        payload = {
            "sub": "user",
            "role": "admin",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            "iat": datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            "type": "access",
        }
        expired = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        result = decode_token(expired)
        assert "error" in result
        assert "expired" in result["error"].lower()

    def test_decode_tampered_token_returns_error(self):
        from auth.jwt_auth import create_access_token, decode_token
        token = create_access_token("user", "admin")
        tampered = token + "corruption"
        result = decode_token(tampered)
        assert "error" in result


class TestConfigSettings:
    def test_settings_loaded_successfully(self):
        from config import settings
        assert settings.APP_NAME is not None
        assert settings.JWT_SECRET is not None

    def test_jwt_secret_is_set(self):
        from config import settings
        assert len(settings.JWT_SECRET) >= 16

    def test_admin_api_key_is_set(self):
        from config import settings
        assert settings.ADMIN_API_KEY is not None
        assert len(settings.ADMIN_API_KEY) > 5

    def test_cors_origin_list_returns_list(self):
        from config import settings
        origins = settings.cors_origin_list
        assert isinstance(origins, list)
        assert len(origins) >= 1
