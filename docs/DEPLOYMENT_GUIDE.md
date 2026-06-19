# Deployment Guide — Self-Healing Engine

**Document Version:** 2.0  
**Date:** 2026-06-16  
**Environment:** Production  

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourorg/self-healing-engine.git
cd self-healing-engine

# 2. Copy environment template
cp .env.example .env

# 3. Generate secure secrets
python -c "import secrets; print(secrets.token_hex(32))"  # For SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"  # For JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"  # For ADMIN_API_KEY

# 4. Edit .env with your values
nano .env

# 5. Start stack
docker compose -f docker-compose.prod.yml up -d

# 6. Verify health
curl http://localhost:5000/health
```

---

## Prerequisites

- Docker & Docker Compose (or Kubernetes)
- PostgreSQL 14+ (or use managed RDS)
- Redis 7+ (for session/cache)
- 4GB RAM minimum
- 10GB disk space
- Network connectivity for monitoring

---

## Pre-Deployment Checklist

### Infrastructure

- [ ] Load balancer configured
- [ ] TLS certificates installed
- [ ] Firewall rules created
- [ ] Database provisioned and tested
- [ ] Redis cluster provisioned
- [ ] Monitoring stack deployed (Prometheus/Grafana)
- [ ] Log aggregation configured (ELK/Loki)

### Secrets Management

- [ ] Generate strong `SECRET_KEY` (64+ hex chars)
- [ ] Generate strong `JWT_SECRET` (64+ hex chars)
- [ ] Generate strong `ADMIN_API_KEY` (32+ bytes)
- [ ] Generate strong `ADMIN_PASSWORD` (12+ chars, mixed case, numbers, symbols)
- [ ] Store in secret vault (HashiCorp Vault, AWS Secrets Manager, etc.)
- [ ] Configure secret rotation policy
- [ ] Backup encryption keys securely

### Testing

- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration tests passing
- [ ] Security tests passing
- [ ] Performance baseline established
- [ ] Load testing completed
- [ ] Chaos engineering tests completed

### Documentation

- [ ] Security guide reviewed
- [ ] Runbook created
- [ ] Incident response plan updated
- [ ] Architecture documented
- [ ] API documentation generated

---

## Deployment Methods

### 1. Docker Compose (Single Server)

Best for: Development, staging, small production deployments

```bash
# Build image
docker compose -f docker-compose.prod.yml build

# Deploy
docker compose -f docker-compose.prod.yml up -d

# Monitor
docker compose -f docker-compose.prod.yml logs -f app

# Scale
docker compose -f docker-compose.prod.yml up -d --scale app=3

# Graceful shutdown
docker compose -f docker-compose.prod.yml down
```

### 2. Kubernetes (Enterprise)

Best for: High availability, multi-region, autoscaling

```bash
# Deploy
kubectl apply -f kubernetes/

# Verify
kubectl get pods -n self-healing

# Scale
kubectl scale deployment app -n self-healing --replicas=3

# Monitor
kubectl port-forward -n self-healing svc/grafana 3000:3000

# Upgrade
kubectl set image deployment/app -n self-healing app=app:v2

# Rollback
kubectl rollout undo deployment/app -n self-healing
```

### 3. CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -f Dockerfile.prod -t app:${{ github.ref_name }} .
      
      - name: Push to registry
        run: docker push app:${{ github.ref_name }}
      
      - name: Deploy to production
        run: kubectl set image deployment/app app=app:${{ github.ref_name }}
```

---

## Configuration

### Environment Variables

```bash
# Application
APP_ENV=production              # development|staging|production
DEBUG=false
HOST=0.0.0.0
PORT=5000

# Security (REQUIRED - generate with secrets module)
SECRET_KEY=<64+ hex chars>
JWT_SECRET=<64+ hex chars>
ADMIN_API_KEY=<32+ base64>
ADMIN_PASSWORD=<strong password>
ADMIN_USERNAME=admin

# Database
DATABASE_URL=postgres://user:pass@host:5432/db
DATA_DIR=/app/data

# CORS
CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318

# SMTP (optional)
SENDER_EMAIL=noreply@example.com
SENDER_PASSWORD=<app-specific password>
ADMIN_EMAIL=admin@example.com
```

### Database Migrations

```bash
# Run migrations
docker exec self_healing_engine alembic upgrade head

# Create new migration
docker exec self_healing_engine alembic revision -m "Add user table"

# Rollback
docker exec self_healing_engine alembic downgrade -1
```

---

## Health Checks

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /live
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2

startupProbe:
  httpGet:
    path: /startup
    port: 5000
  failureThreshold: 30
  periodSeconds: 10
```

### Manual Health Checks

```bash
# Detailed health
curl http://localhost:5000/health

# Liveness
curl http://localhost:5000/live

# Readiness
curl http://localhost:5000/ready

# Startup
curl http://localhost:5000/startup
```

---

## Monitoring

### Prometheus Scraping

```yaml
scrape_configs:
  - job_name: 'self-healing-engine'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Key Metrics

- `requests_total` - Total API requests
- `request_duration_seconds` - Request latency
- `anomalies_total` - Total anomalies detected
- `healings_total` - Total healing operations
- `system_state` - Current system state

### Grafana Dashboards

Default dashboards available:

- **System Overview** - CPU, memory, disk, network
- **API Performance** - Requests, latency, errors
- **Healing Operations** - Detections, healings, success rate
- **Security** - Auth attempts, token operations, errors

---

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker compose -f docker-compose.prod.yml up -d --scale app=3

# Kubernetes
kubectl scale deployment app --replicas=3

# Load Balancer Configuration
# Round-robin across all instances
# Session affinity (if needed)
# Health check: GET /live
```

### Vertical Scaling

```yaml
# Docker Compose
resources:
  limits:
    cpus: '4.0'
    memory: 4G
  reservations:
    cpus: '2.0'
    memory: 2G

# Kubernetes
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Database Scaling

- Use read replicas for queries
- Implement connection pooling
- Archive old event data
- Use partitioning for large tables

---

## Upgrades & Rollbacks

### Blue-Green Deployment

```bash
# 1. Deploy new version (blue)
kubectl apply -f deployment-v2.yaml

# 2. Verify health
kubectl get pods
curl http://v2-service/health

# 3. Switch traffic (green → blue)
kubectl patch service app -p '{"spec":{"selector":{"version":"v2"}}}'

# 4. Monitor
kubectl logs -f deployment/app

# 5. Rollback if needed
kubectl patch service app -p '{"spec":{"selector":{"version":"v1"}}}'

# 6. Cleanup old version
kubectl delete deployment app-v1
```

### Canary Deployment

```bash
# Deploy new version to 10% of traffic
kubectl set image deployment/app app=app:v2 --record
kubectl patch deployment app -p '{"spec":{"replicas":1}}'

# Monitor metrics
# If healthy, gradually increase traffic
# If issues, rollback immediately
```

### Rollback Procedure

```bash
# Automatic rollback
kubectl rollout undo deployment/app

# Check rollout history
kubectl rollout history deployment/app

# Rollback to specific revision
kubectl rollout undo deployment/app --to-revision=2
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Automated daily backups (scheduled)
0 2 * * * pg_dump DATABASE_URL > /backups/db-$(date +%Y%m%d).sql

# Manual backup
pg_dump DATABASE_URL | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Restore from backup
gunzip < backup-20260616.sql.gz | psql DATABASE_URL
```

### RTO/RPO Targets

- **RTO** (Recovery Time Objective): < 1 hour
- **RPO** (Recovery Point Objective): < 15 minutes

### Disaster Recovery Plan

1. **Detection**: Automated alerts detect issues
2. **Assessment**: On-call team assesses scope
3. **Decision**: Trigger failover if needed
4. **Execution**: Restore from backup/failover
5. **Verification**: Verify system integrity
6. **Communication**: Notify stakeholders

---

## Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check logs
docker compose logs app

# Verify configuration
docker exec app env | grep -E "SECRET_KEY|JWT_SECRET"

# Check database connection
docker exec app python -c "from database import engine; engine.connect()"
```

**High memory usage**
```bash
# Check process memory
docker stats

# Check for memory leaks
docker exec app ps aux | grep python

# Restart service gracefully
docker compose restart app
```

**Database connection errors**
```bash
# Verify database is accessible
docker exec app psql $DATABASE_URL -c "SELECT 1"

# Check connection pool
docker exec app ps aux | grep psql

# Review database logs
docker logs postgres
```

**API endpoints returning 503**
```bash
# Check health endpoint
curl http://localhost:5000/health

# Check dependencies
docker compose ps

# Check logs for errors
docker compose logs -f app

# Manually verify dependencies
docker exec app python -c "from database import engine; engine.connect()"
```

---

## Maintenance Windows

### Planned Maintenance

```bash
# 1. Notify users
# 2. Set maintenance window
# 3. Stop new requests
# 4. Wait for in-flight requests to complete
# 5. Perform maintenance
# 6. Restart service
# 7. Verify health
# 8. Resume traffic
# 9. Notify users of completion
```

### Zero-Downtime Deployments

```bash
# Blue-green deployment
# Rolling update with health checks
# Canary deployment with traffic shifting
# Feature flags for gradual rollouts
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_fault_type ON events(fault_type);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM events WHERE timestamp > now() - INTERVAL '1 day';

-- Vacuum
VACUUM ANALYZE;
```

### Application Tuning

```python
# Connection pooling
pool_size=20
max_overflow=10
pool_recycle=1800

# Query caching
# Request compression
# Response streaming for large payloads
```

### Infrastructure Tuning

```bash
# OS-level tuning
sysctl -w net.core.somaxconn=4096
sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Container limits
# Network optimization
# Storage optimization
```

---

## Success Criteria

✅ All health checks passing
✅ No error logs in last 5 minutes
✅ API response time < 200ms (p99)
✅ Uptime > 99.9%
✅ No security alerts
✅ Database connection stable
✅ Memory usage < 80%
✅ CPU usage < 70%

---

## Support & Escalation

**L1 Support**: Monitoring alerts, basic troubleshooting
**L2 Support**: Application debugging, performance tuning
**L3 Support**: Architecture changes, major incidents
**On-Call**: Available 24/7 for critical incidents

---

**Last Updated:** 2026-06-16  
**Next Review:** 2026-09-16  
**Deployment Lead:** [Contact Information]
