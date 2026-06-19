from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

def init_security(app: Flask, settings):
    # Setup CORS
    CORS(app, resources={
        r"/*": {
            "origins": settings.cors_origin_list,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Authorization", "Content-Type", settings.API_KEY_HEADER]
        }
    })

    # Setup Limiter
    limiter.init_app(app)

    # Security Headers
    @app.after_request
    def set_security_headers(response):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline';"
        )
        return response

def require_json_body(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ["POST", "PUT", "PATCH"]:
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 415
        return f(*args, **kwargs)
    return decorated
