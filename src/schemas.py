"""
Pydantic models for request/response validation.
Implements comprehensive input validation across all endpoints.
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# ========== Authentication & Authorization ==========

class LoginRequest(BaseModel):
    """Validated login request."""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, dots, underscores, and hyphens')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class RefreshTokenRequest(BaseModel):
    """Validated refresh token request."""
    refresh_token: str = Field(..., min_length=10, max_length=10000)


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int


class RevokeTokenRequest(BaseModel):
    """Request to revoke a token."""
    token: str = Field(..., min_length=10, max_length=10000)
    revoke_type: Optional[str] = Field("access", pattern="^(access|refresh)$")


class APIKeyRequest(BaseModel):
    """Request to create/rotate API key."""
    name: str = Field(..., min_length=1, max_length=255)
    expires_in_days: Optional[int] = Field(90, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response."""
    key_id: str
    key_secret: str  # Only shown once
    name: str
    created_at: datetime
    expires_at: datetime


# ========== Health & Status ==========

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime
    components: Dict[str, str]
    service: str = "self-healing-engine"
    version: str


class ReadyResponse(BaseModel):
    """Readiness probe response."""
    ready: bool
    dependencies: Dict[str, bool]


class LiveResponse(BaseModel):
    """Liveness probe response."""
    alive: bool
    uptime_seconds: float


# ========== Metrics & Status ==========

class MetricsQueryRequest(BaseModel):
    """Validated metrics query."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metric_types: Optional[List[str]] = Field(None, max_items=10)
    limit: Optional[int] = Field(1000, ge=1, le=10000)


class MetricsResponse(BaseModel):
    """Metrics response."""
    timestamp: datetime
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    disk_percent: float = Field(..., ge=0, le=100)
    network_latency_ms: Optional[float] = None


class SystemStatusResponse(BaseModel):
    """System status."""
    state: str
    metrics: MetricsResponse
    last_healing: Optional[datetime] = None
    anomaly_count: int = 0
    healing_count: int = 0


# ========== Anomaly & Recovery ==========

class AnomalyResponse(BaseModel):
    """Anomaly detection response."""
    status: str = Field(..., pattern="^(NORMAL|ANOMALY)$")
    confidence: float = Field(..., ge=0, le=1)
    anomaly_type: Optional[str] = None
    timestamp: datetime


class FaultResponse(BaseModel):
    """Fault classification response."""
    fault_type: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    recommended_action: str
    timestamp: datetime


class HealingEventResponse(BaseModel):
    """Healing event log entry."""
    event_id: str
    event_type: str
    fault_type: str
    confidence: float
    action_taken: str
    result: str
    timestamp: datetime
    duration_ms: int


class HealingEventListResponse(BaseModel):
    """List of healing events."""
    events: List[HealingEventResponse]
    total_count: int
    page: int
    page_size: int


# ========== Configuration & Preferences ==========

class SettingsUpdateRequest(BaseModel):
    """Request to update system settings."""
    confidence_threshold: Optional[float] = Field(None, ge=0, le=1)
    window_size: Optional[int] = Field(None, ge=1, le=60)
    min_anomalies: Optional[int] = Field(None, ge=1, le=20)
    enable_auto_healing: Optional[bool] = None


class AlertingConfigRequest(BaseModel):
    """Alerting configuration."""
    email_recipients: Optional[List[str]] = Field(None, max_items=10)
    alert_on_anomaly: Optional[bool] = None
    alert_on_healing: Optional[bool] = None
    alert_on_failure: Optional[bool] = None
    webhook_url: Optional[str] = Field(None, max_length=2000)


# ========== Admin Operations ==========

class AuditLogEntry(BaseModel):
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    resource_id: str
    changes: Dict[str, Any]
    ip_address: str
    result: str = Field(..., pattern="^(success|failure)$")


class AuditLogQuery(BaseModel):
    """Query audit logs."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[str] = None
    action_filter: Optional[str] = None
    limit: Optional[int] = Field(1000, ge=1, le=10000)


class SystemConfigResponse(BaseModel):
    """System configuration (filtered for security)."""
    app_env: str
    app_version: str
    log_level: str
    enable_auth: bool
    enable_rate_limiting: bool


# ========== Error Responses ==========

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: str = Field(..., pattern="^[A-Z_]+$")
    timestamp: datetime
    request_id: str
    path: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "Validation error"
    detail: str
    errors: List[Dict[str, Any]]
    request_id: str
    timestamp: datetime


# ========== Page Response Wrapper ==========

class PagedResponse(BaseModel):
    """Generic paginated response wrapper."""
    data: List[Any]
    total_count: int
    page: int = 1
    page_size: int
    total_pages: int


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
