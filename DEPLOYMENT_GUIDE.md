# Deployment Guide

## Prerequisites

- Docker 20.10+ and Docker Compose 1.29+
- 2+ CPU cores, 2GB RAM minimum
- Port availability: 5000 (app), 9090 (Prometheus), 3000 (Grafana)
- Linux/macOS or Windows with WSL2
- SMTP access (Gmail or other) for email alerts (optional)

## Deployment Options

### Option 1: Docker Compose (Recommended for Quick Start)

**Best for:** Development, testing, small deployments (single host)

#### 1. Prepare environment
```bash
git clone <repository>
cd self-healing-ai
cp .env.example .env
# Edit .env with your SMTP credentials
nano .env
```

#### 2. Build and start services
```bash
docker-compose up -d
```

This starts three services:
- **app** (Flask): http://localhost:5000
- **prometheus**: http://localhost:9090
- **grafana**: http://localhost:3000 (default: admin/admin)

#### 3. Verify deployment
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f app

# Test health endpoint
curl http://localhost:5000/api/status
```

#### 4. Training ML models
```bash
# Inside app container
docker-compose exec app python train.py

# Or from host
cd src && python train.py
```

#### 5. Stop services
```bash
docker-compose down
```

---

### Option 2: Kubernetes (Production)

**Best for:** Scalable, resilient production deployments

#### 1. Create namespace
```bash
kubectl create namespace self-healing
```

#### 2. Create ConfigMap for configuration
```bash
kubectl create configmap self-healing-config \
  --from-file=prometheus.yml=prometheus.yml \
  -n self-healing
```

#### 3. Create Secret for credentials
```bash
kubectl create secret generic self-healing-secrets \
  --from-literal=sender_email=your@gmail.com \
  --from-literal=sender_password=your_app_password \
  --from-literal=admin_email=admin@example.com \
  -n self-healing
```

#### 4. Apply Kubernetes manifests
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/app-deployment.yaml
kubectl apply -f k8s/prometheus-deployment.yaml
kubectl apply -f k8s/grafana-deployment.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml
```

#### 5. Verify deployment
```bash
# Check pod status
kubectl get pods -n self-healing

# View logs
kubectl logs -f deployment/self-healing-app -n self-healing

# Port-forward for local access
kubectl port-forward -n self-healing svc/self-healing-app 5000:5000
```

#### 6. Scale the application
```bash
kubectl scale deployment/self-healing-app --replicas=3 -n self-healing
```

---

### Option 3: Manual Installation (Development Only)

**Best for:** Development and debugging

#### 1. Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure environment
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

#### 3. Train models
```bash
cd src
python train.py
```

#### 4. Run application
```bash
# Terminal 1: Flask API
cd src && python api.py

# Terminal 2: Prometheus (separate installation required)
/path/to/prometheus --config.file=../prometheus.yml

# Terminal 3: Grafana (separate installation required)
grafana-server
```

---

## Configuration

### Environment Variables

Create `.env` file from template:
```bash
cp .env.example .env
```

**Configuration:**
```env
# Email notifications (optional, leave empty to disable)
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
ADMIN_EMAIL=admin@your_domain.com

# Data storage
DATA_DIR=/app/data
```

**For Gmail:**
1. Enable 2-Factor Authentication on your Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the generated password (16 characters with spaces removed)

### Application Configuration

Edit in code before deployment:

**File: `src/api.py` or `src/main.py`**
```python
WINDOW_SIZE = 5              # Sliding window for anomaly detection
MIN_ANOMALIES = 3           # Trigger healing after N anomalies in window
CONFIDENCE_THRESHOLD = 0.6  # Z-score confidence (0.6 = 2.5σ)
MAX_CONSECUTIVE_ERRORS = 10 # Circuit breaker threshold
```

**File: `src/anomaly_detector.py`**
```python
ZSCORE_THRESHOLD = 2.5      # Standard deviations threshold (~99.4% confidence)
```

**File: `src/database.py`**
```python
_MAX_EVENTS = 10_000        # Prune database when exceeded
```

**File: `src/logger.py`**
```python
maxBytes=10 * 1024 * 1024   # 10 MB log rotation
backupCount=5                # Keep 5 backup logs
```

---

## Pre-Deployment Checklist

- [ ] Environment variables configured (.env created)
- [ ] ML models trained (artifacts.joblib exists)
- [ ] Docker images built and tested
- [ ] Database backups configured
- [ ] SMTP credentials validated
- [ ] Resource limits set (CPU, memory)
- [ ] Health checks configured
- [ ] Monitoring/alerting enabled
- [ ] SSL/TLS certificates prepared
- [ ] Network policies defined

---

## Monitoring Post-Deployment

### Docker Compose
```bash
# View real-time logs
docker-compose logs -f app

# Check resource usage
docker stats

# View metrics
docker-compose exec app curl http://localhost:8000/metrics
```

### Kubernetes
```bash
# Check pod status
kubectl get pods -n self-healing

# View logs
kubectl logs -f <pod-name> -n self-healing

# Monitor resource usage
kubectl top nodes
kubectl top pods -n self-healing

# Get events
kubectl get events -n self-healing
```

### Application Metrics
```bash
# Access Prometheus
http://localhost:9090

# Access Grafana
http://localhost:3000

# View application logs
tail -f src/logs/system.log
```

---

## Troubleshooting Deployment

### Container fails to start
```bash
# Check logs
docker-compose logs app

# Verify environment variables
docker-compose config | grep -A5 "app:"

# Test image locally
docker run --rm -it -v $(pwd)/.env:/app/.env self-healing-ai-app bash
```

### Permission denied errors
```bash
# Fix file permissions
chmod 644 .env
chmod 755 src/

# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

### Database locked error
```bash
# Remove WAL checkpoint files
rm -f self_healing.db-shm self_healing.db-wal

# Verify database
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"
```

### Prometheus not scraping
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq .

# Verify app metrics endpoint
curl http://localhost:5000/metrics

# Check prometheus.yml syntax
promtool check config prometheus.yml
```

### Email alerts not working
```bash
# Test SMTP connection
python -c "
import smtplib
import ssl
context = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
    server.starttls(context=context)
    server.login('your_email@gmail.com', 'your_app_password')
    print('SMTP connection successful!')
"

# Check .env file
cat .env | grep SENDER
```

---

## Production Hardening Checklist

### Security
- [ ] API authentication enabled (JWT/API keys)
- [ ] HTTPS/TLS configured
- [ ] Secrets in environment variables (not files)
- [ ] Network policies restrict traffic
- [ ] Database encryption enabled
- [ ] Backups encrypted
- [ ] Security scanning enabled (container images, dependencies)

### Reliability
- [ ] Health checks configured
- [ ] Auto-restart policies enabled
- [ ] Resource limits set
- [ ] Horizontal scaling configured
- [ ] Database backups automated daily
- [ ] Disaster recovery tested
- [ ] Graceful shutdown implemented

### Observability
- [ ] Structured logging enabled
- [ ] Distributed tracing configured
- [ ] Metrics exported to central system
- [ ] Alerts configured (Slack, PagerDuty, email)
- [ ] SLOs/SLIs defined
- [ ] Runbooks created for common issues

### Compliance
- [ ] Audit logging enabled
- [ ] Data retention policies implemented
- [ ] Compliance requirements documented
- [ ] Security assessment completed
- [ ] Incident response plan created

---

## Backup & Recovery

### Database Backups

**Daily backup script:**
```bash
#!/bin/bash
BACKUP_DIR="/backups/self-healing"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp self_healing.db $BACKUP_DIR/self_healing_db_$TIMESTAMP.db

# Backup artifacts
cp artifacts.joblib $BACKUP_DIR/artifacts_$TIMESTAMP.joblib

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

**Kubernetes cronjob:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: self-healing-ai-app:latest
            command: ["/app/backup.sh"]
          restartPolicy: OnFailure
```

### Restore from Backup
```bash
# Restore database
cp /backups/self-healing/self_healing_db_20260423.db ./self_healing.db

# Verify restore
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"

# Restart service
docker-compose restart app
```

---

## Updating the Application

### Zero-Downtime Deployment (Kubernetes)

```bash
# Update image
kubectl set image deployment/self-healing-app \
  app=self-healing-ai-app:2.0.0 \
  -n self-healing

# Monitor rollout
kubectl rollout status deployment/self-healing-app -n self-healing

# Rollback if needed
kubectl rollout undo deployment/self-healing-app -n self-healing
```

### Docker Compose Update

```bash
# Pull latest image
docker-compose pull

# Rebuild if necessary
docker-compose build --no-cache

# Restart with zero downtime using rolling updates
docker-compose up -d --no-deps --build app
```

---

## Performance Tuning

### Docker Resource Limits
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Kubernetes Resource Requests/Limits
```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi
```

### Database Optimization
```python
# Connection pooling (future enhancement)
# Increase checkpoint frequency
PRAGMA wal_autocheckpoint = 1000;

# Optimize query performance
ANALYZE;
```

---

## Support & Documentation

- **Logs**: Check `src/logs/system.log`
- **API Documentation**: See `API_DOCUMENTATION.md`
- **Troubleshooting**: See `TROUBLESHOOTING.md`
- **Security**: See `SECURITY.md`
