"""
Token Revocation & Blacklist Management
Implements JWT token blacklist for logout functionality and token revocation.
"""

import time
from typing import Set, Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import threading
from logger import logger


class TokenBlacklist:
    """
    In-memory token blacklist for revoked/expired tokens.
    In production, use Redis for distributed cache.
    """

    def __init__(self, cleanup_interval: int = 3600):
        """
        Initialize token blacklist.
        
        Args:
            cleanup_interval: Seconds between cleanup cycles
        """
        self._blacklist: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def revoke_token(self, token: str, reason: str = "logout", expires_at: Optional[datetime] = None):
        """
        Revoke a token by adding it to the blacklist.
        
        Args:
            token: JWT token to revoke
            reason: Reason for revocation (logout, security, password_change, etc.)
            expires_at: When the token would naturally expire
        """
        with self._lock:
            self._blacklist[token] = {
                "revoked_at": datetime.utcnow(),
                "reason": reason,
                "expires_at": expires_at or datetime.utcnow() + timedelta(days=7)
            }
            logger.info("Token revoked", reason=reason, token_hash=hash(token))
            self._cleanup_if_needed()

    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted."""
        with self._lock:
            if token not in self._blacklist:
                return False
            
            entry = self._blacklist[token]
            if datetime.utcnow() > entry["expires_at"]:
                # Token expired from blacklist, remove it
                del self._blacklist[token]
                return False
            
            return True

    def get_revocation_reason(self, token: str) -> Optional[str]:
        """Get the reason a token was revoked."""
        with self._lock:
            if token in self._blacklist:
                entry = self._blacklist[token]
                if datetime.utcnow() <= entry["expires_at"]:
                    return entry["reason"]
                else:
                    del self._blacklist[token]
        return None

    def _cleanup_if_needed(self):
        """Periodically clean up expired entries."""
        if time.time() - self._last_cleanup > self.cleanup_interval:
            self._cleanup()

    def _cleanup(self):
        """Remove expired tokens from blacklist."""
        with self._lock:
            now = datetime.utcnow()
            expired = [token for token, entry in self._blacklist.items()
                      if now > entry["expires_at"]]
            
            for token in expired:
                del self._blacklist[token]
            
            self._last_cleanup = time.time()
            
            if expired:
                logger.info("Cleaned up expired tokens", count=len(expired))

    def clear(self):
        """Clear all blacklisted tokens (use with caution)."""
        with self._lock:
            self._blacklist.clear()
            logger.warning("Token blacklist cleared")

    def stats(self) -> Dict:
        """Get blacklist statistics."""
        with self._lock:
            return {
                "total_revoked": len(self._blacklist),
                "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat()
            }


# Global token blacklist instance
_blacklist = TokenBlacklist()


def get_blacklist() -> TokenBlacklist:
    """Get the global token blacklist instance."""
    return _blacklist


def revoke_token(token: str, reason: str = "logout", expires_at: Optional[datetime] = None):
    """Revoke a token."""
    _blacklist.revoke_token(token, reason, expires_at)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    return _blacklist.is_blacklisted(token)


def get_blacklist_stats() -> Dict:
    """Get blacklist statistics."""
    return _blacklist.stats()


class APIKeyStore:
    """
    Secure API key storage with rotation support.
    Stores hashed API keys (never store plaintext).
    """

    def __init__(self):
        """Initialize API key store."""
        self._keys: Dict[str, Dict] = {}
        self._lock = threading.RLock()

    def create_key(self, key_id: str, key_hash: str, expires_at: Optional[datetime] = None):
        """
        Store a hashed API key.
        
        Args:
            key_id: Unique key identifier
            key_hash: Hash of the API key (use bcrypt for storage)
            expires_at: When the key expires
        """
        with self._lock:
            self._keys[key_id] = {
                "key_hash": key_hash,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "is_active": True,
                "last_used": None,
                "use_count": 0
            }
            logger.info("API key created", key_id=key_id)

    def verify_key(self, key_id: str, key_hash: str) -> bool:
        """
        Verify an API key.
        
        Args:
            key_id: Key identifier
            key_hash: Hash to verify against
            
        Returns:
            True if key is valid and active
        """
        with self._lock:
            if key_id not in self._keys:
                return False
            
            entry = self._keys[key_id]
            
            # Check if key is active
            if not entry["is_active"]:
                return False
            
            # Check if key has expired
            if entry["expires_at"] and datetime.utcnow() > entry["expires_at"]:
                entry["is_active"] = False
                logger.warning("API key expired", key_id=key_id)
                return False
            
            # Verify hash (in real implementation, use bcrypt.checkpw)
            # For now, simple equality check
            if entry["key_hash"] != key_hash:
                return False
            
            # Update usage stats
            entry["last_used"] = datetime.utcnow()
            entry["use_count"] += 1
            
            return True

    def revoke_key(self, key_id: str, reason: str = "revoked"):
        """Revoke an API key."""
        with self._lock:
            if key_id in self._keys:
                self._keys[key_id]["is_active"] = False
                self._keys[key_id]["revoked_at"] = datetime.utcnow()
                self._keys[key_id]["revoke_reason"] = reason
                logger.info("API key revoked", key_id=key_id, reason=reason)

    def rotate_key(self, old_key_id: str, new_key_id: str, new_key_hash: str) -> bool:
        """
        Rotate an API key.
        
        Args:
            old_key_id: Current key identifier
            new_key_id: New key identifier
            new_key_hash: Hash of new key
            
        Returns:
            True if rotation successful
        """
        with self._lock:
            if old_key_id not in self._keys:
                return False
            
            old_entry = self._keys[old_key_id]
            
            # Create new key
            self._keys[new_key_id] = {
                "key_hash": new_key_hash,
                "created_at": datetime.utcnow(),
                "expires_at": old_entry["expires_at"],
                "is_active": True,
                "last_used": None,
                "use_count": 0
            }
            
            # Mark old key as rotated (keep for reference)
            old_entry["rotated_to"] = new_key_id
            old_entry["is_active"] = False
            
            logger.info("API key rotated", old_key_id=old_key_id, new_key_id=new_key_id)
            return True

    def get_key_info(self, key_id: str) -> Optional[Dict]:
        """Get key information (without exposing hash)."""
        with self._lock:
            if key_id not in self._keys:
                return None
            
            entry = self._keys[key_id]
            return {
                "key_id": key_id,
                "created_at": entry["created_at"],
                "expires_at": entry["expires_at"],
                "is_active": entry["is_active"],
                "last_used": entry["last_used"],
                "use_count": entry["use_count"]
            }


# Global API key store
_api_key_store = APIKeyStore()


def get_api_key_store() -> APIKeyStore:
    """Get the global API key store."""
    return _api_key_store
