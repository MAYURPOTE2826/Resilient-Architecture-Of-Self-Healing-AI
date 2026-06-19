import datetime
import jwt
from functools import wraps
from flask import request, jsonify
from config import settings
from security_utils import PasswordManager
from token_manager import is_token_blacklisted, revoke_token
from logger import logger

def create_access_token(identity: str, role: str = "user") -> str:
    payload = {
        "sub": identity,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        "iat": datetime.datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def create_refresh_token(identity: str) -> str:
    payload = {
        "sub": identity,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.JWT_REFRESH_EXPIRE_MINUTES),
        "iat": datetime.datetime.utcnow(),
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            return {"error": "Token has been revoked"}
        
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

def require_jwt(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow API Key as alternative to JWT for automated systems
        api_key = request.headers.get(settings.API_KEY_HEADER)
        if api_key and api_key == settings.ADMIN_API_KEY:
            request.user = {"sub": "system", "role": "admin"}
            request.token = None
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header", remote_addr=request.remote_addr)
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        payload = decode_token(token)

        if "error" in payload:
            logger.warning("Token decode error", error=payload["error"], remote_addr=request.remote_addr)
            return jsonify({"error": payload["error"]}), 401

        if payload.get("type") != "access":
            logger.warning("Invalid token type", token_type=payload.get("type"), remote_addr=request.remote_addr)
            return jsonify({"error": "Invalid token type"}), 401

        request.user = payload
        request.token = token
        return f(*args, **kwargs)
    return decorated

def require_role(role: str):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(request, "user", None)
            if not user or (user.get("role") != role and user.get("role") != "admin"):
                logger.warning("Insufficient permissions", required_role=role, user_role=user.get("role") if user else None, remote_addr=request.remote_addr)
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return PasswordManager.hash_password(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    return PasswordManager.verify_password(password, hashed)

