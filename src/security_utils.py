"""
Security Utilities
Implements secure password handling, input sanitization, and security best practices.
"""

import bcrypt
import secrets
import hashlib
import uuid
from typing import Tuple, Optional
import re
from logger import logger


class PasswordManager:
    """Secure password hashing and verification."""

    # Bcrypt work factor (computational cost)
    ROUNDS = 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password (includes salt)
        """
        if not isinstance(password, bytes):
            password = password.encode('utf-8')
        
        hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=PasswordManager.ROUNDS))
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password to verify against
            
        Returns:
            True if password matches
        """
        try:
            if not isinstance(password, bytes):
                password = password.encode('utf-8')
            if not isinstance(hashed, bytes):
                hashed = hashed.encode('utf-8')
            
            result = bcrypt.checkpw(password, hashed)
            return result
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False

    @staticmethod
    def needs_rehash(hashed: str) -> bool:
        """
        Check if a password hash needs rehashing (bcrypt rounds increased).
        
        Args:
            hashed: Current password hash
            
        Returns:
            True if should be rehashed
        """
        try:
            # Extract work factor from hash
            if not isinstance(hashed, bytes):
                hashed = hashed.encode('utf-8')
            
            # Bcrypt format: $2a$10$... (10 is the cost)
            # If cost is less than current ROUNDS, needs rehashing
            cost = int(hashed.decode('utf-8').split('$')[2])
            return cost < PasswordManager.ROUNDS
        except Exception:
            return True


class APIKeyGenerator:
    """Generate and manage secure API keys."""

    KEY_LENGTH = 32  # 256 bits = 32 bytes
    PREFIX = "sk_"  # API key prefix for identification

    @staticmethod
    def generate() -> str:
        """
        Generate a new secure API key.
        
        Returns:
            Base64-encoded API key
        """
        random_bytes = secrets.token_urlsafe(APIKeyGenerator.KEY_LENGTH)
        return f"{APIKeyGenerator.PREFIX}{random_bytes}"

    @staticmethod
    def hash_key(api_key: str) -> str:
        """
        Hash an API key for storage.
        
        Args:
            api_key: Plain API key
            
        Returns:
            SHA-256 hash of API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def validate_key_format(api_key: str) -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid format
        """
        if not isinstance(api_key, str):
            return False
        
        if not api_key.startswith(APIKeyGenerator.PREFIX):
            return False
        
        # Should be sk_ + 43 url-safe base64 chars (approx)
        if len(api_key) < 50:
            return False
        
        return True


class InputValidator:
    """Validate and sanitize user inputs."""

    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        re.IGNORECASE
    )
    
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
    
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)*[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    @staticmethod
    def validate_email(email: str, max_length: int = 254) -> bool:
        """Validate email format."""
        if not email or len(email) > max_length:
            return False
        return bool(InputValidator.EMAIL_PATTERN.match(email))

    @staticmethod
    def validate_username(username: str, min_length: int = 3, max_length: int = 32) -> bool:
        """Validate username."""
        if not username or len(username) < min_length or len(username) > max_length:
            return False
        return bool(InputValidator.ALPHANUMERIC_PATTERN.match(username))

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if len(password) > 128:
            return False, "Password must be less than 128 characters"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        complexity = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity < 3:
            return False, "Password must contain uppercase, lowercase, numbers, and special characters"
        
        return True, None

    @staticmethod
    def validate_url(url: str, max_length: int = 2048) -> bool:
        """Validate URL format."""
        if not url or len(url) > max_length:
            return False
        return bool(InputValidator.URL_PATTERN.match(url))

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, allow_special: bool = False) -> str:
        """
        Sanitize string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_special: Whether to allow special characters
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return ""
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        if not allow_special:
            # Remove control characters
            value = ''.join(c for c in value if ord(c) >= 32 or c in '\n\r\t')
        
        return value.strip()

    @staticmethod
    def sanitize_html(html: str) -> str:
        """
        Sanitize HTML input (basic XSS prevention).
        Note: For production, use bleach library.
        """
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'on\w+\s*=',  # Event handlers
            r'javascript:',
        ]
        
        result = html
        for pattern in dangerous_patterns:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)
        
        return result


class RequestContextManager:
    """Manage request context and correlation IDs."""

    @staticmethod
    def generate_request_id() -> str:
        """Generate a unique request ID."""
        return f"req_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_trace_id() -> str:
        """Generate a unique trace ID for distributed tracing."""
        return f"trace_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a correlation ID for request grouping."""
        return f"corr_{uuid.uuid4().hex[:12]}"


class SecurityHeaders:
    """Security headers for HTTP responses."""

    HEADERS = {
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Clickjacking prevention
        "X-Frame-Options": "DENY",
        
        # XSS protection
        "X-XSS-Protection": "1; mode=block",
        
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Permissions policy (formerly Feature Policy)
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        
        # HSTS (only in production HTTPS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        
        # Prevent caching of sensitive data
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    @staticmethod
    def get_headers(include_hsts: bool = False) -> dict:
        """
        Get security headers.
        
        Args:
            include_hsts: Whether to include HSTS header (only for HTTPS)
            
        Returns:
            Dictionary of security headers
        """
        headers = SecurityHeaders.HEADERS.copy()
        
        if not include_hsts:
            headers.pop("Strict-Transport-Security", None)
        
        return headers


class IPValidator:
    """Validate IP addresses."""

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Check if IP is valid IPv4 or IPv6."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP is in private range."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private
        except ValueError:
            return False

    @staticmethod
    def is_loopback(ip: str) -> bool:
        """Check if IP is loopback."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_loopback
        except ValueError:
            return False
