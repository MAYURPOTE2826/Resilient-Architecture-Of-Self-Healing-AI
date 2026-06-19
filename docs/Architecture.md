# Architecture & Documentation

## Overview
This document covers the refactored, enterprise-grade architecture for the Self-Healing ML Engine.

## Components
1. **API Layer (Flask/Waitress)**: Serves all routes. Hardened with JWT, RBAC, Pydantic configuration, and rate limiting.
2. **Security Middleware**: CORS, HSTS, X-Frame-Options configured via `middleware.security`.
3. **Tracing & Logging**: OpenTelemetry injects Trace IDs, exported via OTLP. Structlog formats JSON logs.
4. **Database (SQLAlchemy + Alembic)**: Connection pooling via `QueuePool` (Postgres) or `SingletonThreadPool` (SQLite). Managed with Alembic for schema evolution.
5. **Machine Learning Engine**: Continuously monitors the system in the background. Now decoupled with Tenacity retries.

## Deployment (Docker)
- `Dockerfile.prod`: Multi-stage build for minimal size, runs as a non-root user.
- `docker-compose.prod.yml`: Deploys the App, Prometheus, Grafana, Loki, and Promtail.
