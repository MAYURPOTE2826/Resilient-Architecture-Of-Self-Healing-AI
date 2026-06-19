"""
Audit Logging Middleware
Logs all security-relevant events for compliance and forensics.
"""

from flask import Flask, request, g
from datetime import datetime
from typing import Dict, Optional, Any
import json
from functools import wraps
from logger import logger


class AuditLogger:
    """Audit logging for security events."""

    # Severity levels
    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"
    SEVERITY_CRITICAL = "CRITICAL"

    # Event types
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTHZ_FAILURE = "authz.failure"
    TOKEN_CREATED = "token.created"
    TOKEN_REVOKED = "token.revoked"
    TOKEN_EXPIRED = "token.expired"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    API_KEY_ROTATED = "api_key.rotated"
    CONFIG_CHANGED = "config.changed"
    USER_CREATED = "user.created"
    USER_DELETED = "user.deleted"
    USER_MODIFIED = "user.modified"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    DATA_EXPORTED = "data.exported"
    DATA_DELETED = "data.deleted"
    SECURITY_ALERT = "security.alert"

    @staticmethod
    def log_event(
        event_type: str,
        severity: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., auth.success)
            severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
            user_id: User identifier
            resource: Resource type (e.g., 'user', 'api_key')
            resource_id: Resource identifier
            action: Action performed
            result: Result of action (success, failure)
            reason: Reason for action/failure
            details: Additional context
            status_code: HTTP status code
        """
        request_id = getattr(g, 'request_id', 'unknown')
        trace_id = getattr(g, 'trace_id', 'unknown')
        
        audit_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "request_id": request_id,
            "trace_id": trace_id,
            "user_id": user_id or "anonymous",
            "resource": resource,
            "resource_id": resource_id,
            "action": action,
            "result": result,
            "ip_address": request.remote_addr if request else None,
            "user_agent": request.user_agent.string if request else None,
            "http_method": request.method if request else None,
            "http_path": request.path if request else None,
            "status_code": status_code,
            "reason": reason,
            "details": details or {}
        }
        
        # Log at appropriate level
        log_func = {
            AuditLogger.SEVERITY_INFO: logger.info,
            AuditLogger.SEVERITY_WARNING: logger.warning,
            AuditLogger.SEVERITY_ERROR: logger.error,
            AuditLogger.SEVERITY_CRITICAL: logger.critical
        }.get(severity, logger.info)
        
        log_func("Audit event", audit_event=json.dumps(audit_event))


def audit_login(f):
    """Decorator to audit login attempts."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = None
        try:
            response = f(*args, **kwargs)
            
            # Extract user info from request
            data = request.get_json() or {}
            user_id = data.get("username")
            
            # Determine if login was successful
            if isinstance(response, tuple) and len(response) > 1:
                status_code = response[1]
            else:
                status_code = 200
            
            if status_code == 200:
                AuditLogger.log_event(
                    event_type=AuditLogger.AUTH_SUCCESS,
                    severity=AuditLogger.SEVERITY_INFO,
                    user_id=user_id,
                    action="login",
                    status_code=status_code
                )
            else:
                AuditLogger.log_event(
                    event_type=AuditLogger.AUTH_FAILURE,
                    severity=AuditLogger.SEVERITY_WARNING,
                    user_id=user_id,
                    action="login",
                    result="failure",
                    reason="Invalid credentials",
                    status_code=status_code
                )
            
            return response
        except Exception as e:
            AuditLogger.log_event(
                event_type=AuditLogger.AUTH_FAILURE,
                severity=AuditLogger.SEVERITY_ERROR,
                user_id=user_id,
                action="login",
                result="error",
                reason=str(e)
            )
            raise
    
    return decorated


def audit_token_revocation(f):
    """Decorator to audit token revocation."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = getattr(request, 'user', None)
            user_id = user.get("sub") if user else "unknown"
            
            response = f(*args, **kwargs)
            
            AuditLogger.log_event(
                event_type=AuditLogger.TOKEN_REVOKED,
                severity=AuditLogger.SEVERITY_INFO,
                user_id=user_id,
                resource="token",
                action="revoke",
                reason="user_logout"
            )
            
            return response
        except Exception as e:
            logger.error("Token revocation audit failed", error=str(e))
            raise
    
    return decorated


def audit_api_key_operation(operation_type: str):
    """
    Decorator factory for API key operations.
    
    Args:
        operation_type: Type of operation (create, revoke, rotate)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                user = getattr(request, 'user', None)
                user_id = user.get("sub") if user else "unknown"
                
                response = f(*args, **kwargs)
                
                AuditLogger.log_event(
                    event_type=f"api_key.{operation_type}",
                    severity=AuditLogger.SEVERITY_INFO,
                    user_id=user_id,
                    resource="api_key",
                    action=operation_type
                )
                
                return response
            except Exception as e:
                logger.error(f"API key {operation_type} audit failed", error=str(e))
                raise
        
        return decorated
    return decorator


def audit_security_event(event_type: str, severity: str):
    """
    Decorator factory for security events.
    
    Args:
        event_type: Type of security event
        severity: Severity level
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                user = getattr(request, 'user', None)
                user_id = user.get("sub") if user else "unknown"
                
                response = f(*args, **kwargs)
                
                AuditLogger.log_event(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    action="security_check"
                )
                
                return response
            except Exception as e:
                AuditLogger.log_event(
                    event_type=event_type,
                    severity=severity,
                    user_id="unknown",
                    action="security_check",
                    result="error",
                    reason=str(e)
                )
                raise
        
        return decorated
    return decorator


def init_audit_logging(app: Flask):
    """Initialize audit logging for Flask app."""
    
    @app.before_request
    def audit_request_start():
        """Log request start for audit trail."""
        # Note: Don't log every request for performance
        # Only log sensitive endpoints
        sensitive_paths = ['/api/auth/', '/api/admin/', '/api/config/']
        
        for path in sensitive_paths:
            if request.path.startswith(path):
                logger.info(
                    "Sensitive endpoint accessed",
                    method=request.method,
                    path=request.path,
                    ip=request.remote_addr
                )
                break

    @app.after_request
    def audit_request_end(response):
        """Log request end for audit trail."""
        # Log failed auth attempts at sensitive endpoints
        if request.path.startswith('/api/auth/login') and response.status_code != 200:
            data = request.get_json() or {}
            AuditLogger.log_event(
                event_type=AuditLogger.AUTH_FAILURE,
                severity=AuditLogger.SEVERITY_WARNING,
                user_id=data.get("username"),
                action="login_attempt",
                result="failure",
                status_code=response.status_code
            )
        
        return response


# Singleton instance
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the audit logger instance."""
    return _audit_logger


def log_audit_event(*args, **kwargs):
    """Log an audit event."""
    AuditLogger.log_event(*args, **kwargs)
