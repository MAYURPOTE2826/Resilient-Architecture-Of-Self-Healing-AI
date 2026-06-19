import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyHttpUrl, validator

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Self-Healing-Engine"
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    HOST: str = "0.0.0.0"
    PORT: int = 5000

    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", description="Must be set in production")
    JWT_SECRET: str = Field(..., env="JWT_SECRET", description="Used for encoding JWT tokens")
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_MINUTES: int = 60 * 24 * 7
    API_KEY_HEADER: str = "X-API-Key"
    ADMIN_API_KEY: str = Field(..., env="ADMIN_API_KEY")

    # Admin UI Credentials (for the /api/auth/login endpoint)
    ADMIN_USERNAME: str = Field("admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field("admin123", env="ADMIN_PASSWORD")
    
    # CORS
    CORS_ORIGINS: str = Field("http://localhost:5000,http://127.0.0.1:5000", env="CORS_ORIGINS")

    # Database
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
    DATA_DIR: str = Field(..., env="DATA_DIR")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

def get_settings() -> Settings:
    # Ensure DATA_DIR defaults correctly if not set
    if "DATA_DIR" not in os.environ:
        os.environ["DATA_DIR"] = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Generate random secrets for dev if not set to prevent startup crash, but fail in prod
    if os.environ.get("APP_ENV", "development") != "production":
        os.environ.setdefault("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
        os.environ.setdefault("JWT_SECRET", "dev-jwt-secret-do-not-use-in-prod")
        os.environ.setdefault("ADMIN_API_KEY", "dev-admin-api-key")

    try:
        s = Settings()
    except Exception as e:
        import sys
        print(f"Configuration Validation Error: {e}")
        sys.exit(1)

    # Production hardening: fail if default/weak credentials are in use
    if s.APP_ENV == "production":
        _WEAK_DEFAULTS = {"admin123", "password", "admin", "secret", "changeme"}
        if s.ADMIN_PASSWORD in _WEAK_DEFAULTS:
            import sys
            print("FATAL: ADMIN_PASSWORD must not be a default/weak value in production.")
            sys.exit(1)
        if len(s.JWT_SECRET) < 32:
            import sys
            print("FATAL: JWT_SECRET must be at least 32 characters in production.")
            sys.exit(1)
        if len(s.SECRET_KEY) < 32:
            import sys
            print("FATAL: SECRET_KEY must be at least 32 characters in production.")
            sys.exit(1)

    return s


settings = get_settings()
