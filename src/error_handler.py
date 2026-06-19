"""
Error Handling Middleware
Implements comprehensive error handling and error response formatting.
"""

from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException
from datetime import datetime
from functools import wraps
from typing import Tuple, Optional
import traceback
import sys
from logger import logger
from security_utils import RequestContextManager


class APIError(Exception):
    """Base API error class."""

    def __init__(
        self,
        error: str,
        detail: Optional[str] = None,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        headers: Optional[dict] = None
    ):
        """Initialize API error."""
        super().__init__(error)
        self.error = error
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.headers = headers or {}


class ValidationError(APIError):
    """Validation error."""
    def __init__(self, detail: str, errors: list = None):
        super().__init__(
            error="Validation failed",
            detail=detail,
            code="VALIDATION_ERROR",
            status_code=422
        )
        self.errors = errors or []


class AuthenticationError(APIError):
    """Authentication error."""
    def __init__(self, detail: str = None):
        super().__init__(
            error="Authentication failed",
            detail=detail or "Invalid credentials",
            code="AUTH_ERROR",
            status_code=401
        )


class AuthorizationError(APIError):
    """Authorization error."""
    def __init__(self, detail: str = None):
        super().__init__(
            error="Authorization failed",
            detail=detail or "Insufficient permissions",
            code="AUTHZ_ERROR",
            status_code=403
        )


class NotFoundError(APIError):
    """Not found error."""
    def __init__(self, resource: str, detail: str = None):
        super().__init__(
            error=f"{resource} not found",
            detail=detail,
            code="NOT_FOUND",
            status_code=404
        )


class ConflictError(APIError):
    """Conflict error."""
    def __init__(self, detail: str):
        super().__init__(
            error="Resource conflict",
            detail=detail,
            code="CONFLICT",
            status_code=409
        )


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__(
            error="Rate limit exceeded",
            detail="Too many requests",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
        if retry_after:
            self.headers["Retry-After"] = str(retry_after)


class ServiceUnavailableError(APIError):
    """Service unavailable error."""
    def __init__(self, detail: str = None):
        super().__init__(
            error="Service temporarily unavailable",
            detail=detail,
            code="SERVICE_UNAVAILABLE",
            status_code=503
        )


def init_error_handlers(app: Flask):
    """
    Initialize error handlers for Flask app.
    
    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request_hook():
        """Hook before each request."""
        g.request_id = RequestContextManager.generate_request_id()
        g.trace_id = RequestContextManager.generate_trace_id()
        g.correlation_id = request.headers.get("X-Correlation-ID", RequestContextManager.generate_correlation_id())
        g.start_time = datetime.utcnow()

    @app.after_request
    def after_request_hook(response):
        """Hook after each request."""
        request_id = getattr(g, 'request_id', 'unknown')
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = getattr(g, 'trace_id', 'unknown')
        response.headers["X-Correlation-ID"] = getattr(g, 'correlation_id', 'unknown')
        return response

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle APIError exceptions."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        response = {
            "error": error.error,
            "code": error.code,
            "detail": error.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        # Log the error
        logger.warning(
            "API error",
            error=error.error,
            code=error.code,
            status_code=error.status_code,
            request_id=request_id,
            path=request.path
        )

        return jsonify(response), error.status_code, error.headers

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """Handle validation errors."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        response = {
            "error": error.error,
            "code": error.code,
            "detail": error.detail,
            "errors": error.errors,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        logger.warning(
            "Validation error",
            code=error.code,
            request_id=request_id,
            path=request.path
        )

        return jsonify(response), error.status_code, error.headers

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        response = {
            "error": "Not found",
            "code": "NOT_FOUND",
            "detail": "The requested resource does not exist",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "path": request.path
        }

        return jsonify(response), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 errors."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        response = {
            "error": "Method not allowed",
            "code": "METHOD_NOT_ALLOWED",
            "detail": f"The {request.method} method is not allowed for this resource",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        return jsonify(response), 405

    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 errors."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        response = {
            "error": "Bad request",
            "code": "BAD_REQUEST",
            "detail": str(error.description) if hasattr(error, 'description') else "Invalid request",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        return jsonify(response), 400

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        """Handle generic exceptions."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        # Log full traceback
        logger.error(
            "Unhandled exception",
            request_id=request_id,
            path=request.path,
            error=str(error),
            exception_type=type(error).__name__,
            traceback=traceback.format_exc()
        )

        # Don't expose internal details in production
        from config import settings
        if settings.APP_ENV == "production":
            error_message = "An internal server error occurred"
        else:
            error_message = str(error)

        response = {
            "error": "Internal server error",
            "code": "INTERNAL_SERVER_ERROR",
            "detail": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        return jsonify(response), 500


def validate_request(schema_class):
    """
    Decorator to validate request using Pydantic schema.
    
    Args:
        schema_class: Pydantic model class for validation
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                if request.method in ["POST", "PUT", "PATCH"]:
                    data = request.get_json() or {}
                    validated_data = schema_class(**data)
                    # Store validated data in kwargs
                    kwargs['validated_data'] = validated_data
                
                return f(*args, **kwargs)
            except Exception as e:
                error_detail = str(e)
                errors = []
                
                # Extract validation errors if available
                if hasattr(e, 'errors'):
                    errors = e.errors()
                
                raise ValidationError(detail=error_detail, errors=errors)
        
        return decorated
    return decorator


def require_content_type(content_types: list):
    """
    Decorator to validate Content-Type header.
    
    Args:
        content_types: List of allowed content types
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.method in ["POST", "PUT", "PATCH"]:
                if not request.content_type or not any(
                    ct in request.content_type for ct in content_types
                ):
                    raise APIError(
                        error="Unsupported Media Type",
                        detail=f"Content-Type must be one of: {', '.join(content_types)}",
                        code="UNSUPPORTED_MEDIA_TYPE",
                        status_code=415
                    )
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def log_request_response(f):
    """Decorator to log request and response."""
    @wraps(f)
    def decorated(*args, **kwargs):
        request_id = getattr(g, 'request_id', 'unknown')
        
        logger.info(
            "Request",
            request_id=request_id,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr
        )
        
        try:
            response = f(*args, **kwargs)
            
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = 200
            
            duration = (datetime.utcnow() - getattr(g, 'start_time', datetime.utcnow())).total_seconds()
            
            logger.info(
                "Response",
                request_id=request_id,
                status_code=status_code,
                duration_seconds=duration
            )
            
            return response
        except Exception as e:
            duration = (datetime.utcnow() - getattr(g, 'start_time', datetime.utcnow())).total_seconds()
            logger.error(
                "Request error",
                request_id=request_id,
                duration_seconds=duration,
                error=str(e)
            )
            raise
    
    return decorated
