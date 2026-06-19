"""
Security Tests
Comprehensive tests for authentication, authorization, and security features.
"""

import pytest
from datetime import datetime, timedelta
import jwt
import json
from unittest.mock import Mock, patch, MagicMock

# Import the security modules
from security_utils import (
    PasswordManager,
    APIKeyGenerator,
    InputValidator,
    RequestContextManager,
    SecurityHeaders,
    IPValidator
)
from token_manager import TokenBlacklist, APIKeyStore, is_token_blacklisted, revoke_token
from health_checks import HealthChecker
from schemas import LoginRequest, TokenResponse


class TestPasswordManager:
    """Test password hashing and verification."""

    def test_hash_password_creates_valid_hash(self):
        """Test password hashing."""
        password = "SecurePassword123!"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert '$2a$' in hashed or '$2b$' in hashed

    def test_verify_password_succeeds_with_correct_password(self):
        """Test password verification succeeds."""
        password = "SecurePassword123!"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed)

    def test_verify_password_fails_with_wrong_password(self):
        """Test password verification fails with wrong password."""
        password = "SecurePassword123!"
        hashed = PasswordManager.hash_password(password)
        
        assert not PasswordManager.verify_password("WrongPassword", hashed)

    def test_needs_rehash_detects_outdated_hash(self):
        """Test rehash detection."""
        password = "SecurePassword123!"
        hashed = PasswordManager.hash_password(password)
        
        # Current hash should not need rehashing
        assert not PasswordManager.needs_rehash(hashed)


class TestAPIKeyGenerator:
    """Test API key generation and validation."""

    def test_generate_creates_valid_key(self):
        """Test API key generation."""
        key = APIKeyGenerator.generate()
        
        assert key.startswith("sk_")
        assert len(key) > 35

    def test_hash_key_creates_consistent_hash(self):
        """Test API key hashing."""
        key = "sk_test_key_12345"
        hash1 = APIKeyGenerator.hash_key(key)
        hash2 = APIKeyGenerator.hash_key(key)
        
        assert hash1 == hash2
        assert hash1 != key

    def test_validate_key_format_accepts_valid_key(self):
        """Test API key format validation."""
        key = APIKeyGenerator.generate()
        
        assert APIKeyGenerator.validate_key_format(key)

    def test_validate_key_format_rejects_invalid_key(self):
        """Test API key format validation rejects invalid keys."""
        assert not APIKeyGenerator.validate_key_format("invalid_key")
        assert not APIKeyGenerator.validate_key_format("sk_short")
        assert not APIKeyGenerator.validate_key_format(None)


class TestInputValidator:
    """Test input validation."""

    def test_validate_email_accepts_valid_email(self):
        """Test valid email validation."""
        assert InputValidator.validate_email("test@example.com")
        assert InputValidator.validate_email("user.name+tag@example.co.uk")

    def test_validate_email_rejects_invalid_email(self):
        """Test invalid email validation."""
        assert not InputValidator.validate_email("invalid_email")
        assert not InputValidator.validate_email("@example.com")
        assert not InputValidator.validate_email("test@")

    def test_validate_username_accepts_valid_username(self):
        """Test valid username validation."""
        assert InputValidator.validate_username("valid_user")
        assert InputValidator.validate_username("user123")
        assert InputValidator.validate_username("u")

    def test_validate_username_rejects_invalid_username(self):
        """Test invalid username validation."""
        assert not InputValidator.validate_username("  ")  # Too short
        assert not InputValidator.validate_username("a" * 100)  # Too long
        assert not InputValidator.validate_username("user@invalid")  # Invalid chars

    def test_validate_password_strength_accepts_strong_password(self):
        """Test strong password validation."""
        valid, msg = InputValidator.validate_password_strength("SecurePass123!@")
        assert valid
        assert msg is None

    def test_validate_password_strength_rejects_weak_password(self):
        """Test weak password validation."""
        valid, msg = InputValidator.validate_password_strength("weak")
        assert not valid
        assert msg is not None

    def test_sanitize_string_removes_null_bytes(self):
        """Test string sanitization."""
        dirty = "valid\x00string"
        clean = InputValidator.sanitize_string(dirty)
        assert "\x00" not in clean

    def test_sanitize_html_removes_scripts(self):
        """Test HTML sanitization."""
        html = "<div><script>alert('xss')</script>Content</div>"
        clean = InputValidator.sanitize_html(html)
        assert "<script>" not in clean


class TestRequestContextManager:
    """Test request context management."""

    def test_generate_request_id_creates_unique_ids(self):
        """Test request ID generation."""
        id1 = RequestContextManager.generate_request_id()
        id2 = RequestContextManager.generate_request_id()
        
        assert id1.startswith("req_")
        assert id2.startswith("req_")
        assert id1 != id2

    def test_generate_trace_id_creates_valid_id(self):
        """Test trace ID generation."""
        trace_id = RequestContextManager.generate_trace_id()
        
        assert trace_id.startswith("trace_")
        assert len(trace_id) > 6

    def test_generate_correlation_id_creates_valid_id(self):
        """Test correlation ID generation."""
        corr_id = RequestContextManager.generate_correlation_id()
        
        assert corr_id.startswith("corr_")
        assert len(corr_id) > 5


class TestTokenBlacklist:
    """Test token blacklist functionality."""

    def test_revoke_token_adds_to_blacklist(self):
        """Test token revocation."""
        blacklist = TokenBlacklist()
        token = "test_token_123"
        
        blacklist.revoke_token(token)
        assert blacklist.is_blacklisted(token)

    def test_is_blacklisted_returns_false_for_valid_token(self):
        """Test non-blacklisted token."""
        blacklist = TokenBlacklist()
        
        assert not blacklist.is_blacklisted("valid_token")

    def test_get_revocation_reason_returns_reason(self):
        """Test revocation reason retrieval."""
        blacklist = TokenBlacklist()
        token = "test_token"
        reason = "user_logout"
        
        blacklist.revoke_token(token, reason=reason)
        assert blacklist.get_revocation_reason(token) == reason

    def test_cleanup_removes_expired_tokens(self):
        """Test token cleanup."""
        blacklist = TokenBlacklist(cleanup_interval=0)
        token = "test_token"
        
        # Revoke with immediate expiration
        blacklist.revoke_token(token, expires_at=datetime.utcnow() - timedelta(seconds=1))
        
        # Trigger cleanup
        blacklist._cleanup()
        
        # Token should no longer be blacklisted
        assert not blacklist.is_blacklisted(token)


class TestAPIKeyStore:
    """Test API key storage."""

    def test_create_key_stores_key(self):
        """Test key creation."""
        store = APIKeyStore()
        key_id = "key_1"
        key_hash = "hash_value"
        
        store.create_key(key_id, key_hash)
        
        info = store.get_key_info(key_id)
        assert info is not None
        assert info["key_id"] == key_id
        assert info["is_active"]

    def test_verify_key_succeeds_with_valid_key(self):
        """Test key verification."""
        store = APIKeyStore()
        key_id = "key_1"
        key_hash = "hash_value"
        
        store.create_key(key_id, key_hash)
        assert store.verify_key(key_id, key_hash)

    def test_verify_key_fails_with_invalid_hash(self):
        """Test key verification with invalid hash."""
        store = APIKeyStore()
        key_id = "key_1"
        key_hash = "hash_value"
        
        store.create_key(key_id, key_hash)
        assert not store.verify_key(key_id, "wrong_hash")

    def test_revoke_key_deactivates_key(self):
        """Test key revocation."""
        store = APIKeyStore()
        key_id = "key_1"
        key_hash = "hash_value"
        
        store.create_key(key_id, key_hash)
        store.revoke_key(key_id)
        
        assert not store.verify_key(key_id, key_hash)

    def test_rotate_key_creates_new_key(self):
        """Test key rotation."""
        store = APIKeyStore()
        old_key_id = "key_1"
        new_key_id = "key_2"
        old_hash = "old_hash"
        new_hash = "new_hash"
        
        store.create_key(old_key_id, old_hash)
        assert store.rotate_key(old_key_id, new_key_id, new_hash)
        
        # New key should work
        assert store.verify_key(new_key_id, new_hash)
        
        # Old key should not work
        assert not store.verify_key(old_key_id, old_hash)


class TestIPValidator:
    """Test IP address validation."""

    def test_is_valid_ip_accepts_ipv4(self):
        """Test IPv4 validation."""
        assert IPValidator.is_valid_ip("192.168.1.1")
        assert IPValidator.is_valid_ip("10.0.0.1")

    def test_is_valid_ip_rejects_invalid_ip(self):
        """Test invalid IP validation."""
        assert not IPValidator.is_valid_ip("256.256.256.256")
        assert not IPValidator.is_valid_ip("not_an_ip")

    def test_is_private_ip_detects_private_ranges(self):
        """Test private IP detection."""
        assert IPValidator.is_private_ip("192.168.1.1")
        assert IPValidator.is_private_ip("10.0.0.1")
        assert IPValidator.is_private_ip("172.16.0.1")

    def test_is_private_ip_rejects_public_ip(self):
        """Test public IP is not private."""
        assert not IPValidator.is_private_ip("8.8.8.8")

    def test_is_loopback_detects_localhost(self):
        """Test loopback detection."""
        assert IPValidator.is_loopback("127.0.0.1")


class TestSecurityHeaders:
    """Test security headers."""

    def test_get_headers_includes_required_headers(self):
        """Test security headers."""
        headers = SecurityHeaders.get_headers()
        
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "Referrer-Policy" in headers

    def test_get_headers_includes_hsts_when_requested(self):
        """Test HSTS header inclusion."""
        headers = SecurityHeaders.get_headers(include_hsts=True)
        
        assert "Strict-Transport-Security" in headers


class TestHealthChecker:
    """Test health checking."""

    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.cpu_percent')
    def test_health_check_returns_status(self, mock_cpu, mock_disk, mock_memory):
        """Test health check."""
        mock_cpu.return_value = 50.0
        mock_disk.return_value = MagicMock(free=1000000000)
        mock_memory.return_value = MagicMock(percent=50.0)
        
        checker = HealthChecker()
        health = checker.get_health()
        
        assert "status" in health
        assert "components" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

    def test_readiness_check_returns_ready_status(self):
        """Test readiness check."""
        checker = HealthChecker()
        ready = checker.get_readiness()
        
        assert "ready" in ready
        assert isinstance(ready["ready"], bool)

    def test_liveness_check_returns_alive_status(self):
        """Test liveness check."""
        checker = HealthChecker()
        alive = checker.get_liveness()
        
        assert "alive" in alive
        assert isinstance(alive["alive"], bool)


# Pydantic Schema Tests
class TestSchemas:
    """Test Pydantic schemas."""

    def test_login_request_validates_username(self):
        """Test login request schema."""
        data = {"username": "admin", "password": "SecurePass123!"}
        req = LoginRequest(**data)
        
        assert req.username == "admin"

    def test_login_request_rejects_empty_username(self):
        """Test login request rejects empty username."""
        with pytest.raises(Exception):
            LoginRequest(username="", password="SecurePass123!")

    def test_login_request_rejects_weak_password(self):
        """Test login request rejects weak password."""
        with pytest.raises(Exception):
            LoginRequest(username="admin", password="weak")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
