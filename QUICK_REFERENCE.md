# Quick Reference Card

## 🚀 Getting Started

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Train models
cd src && python train.py && cd ..

# Run application
docker-compose up -d
# OR
python src/api.py
```

## 📊 Access Points

| Service | URL | Credentials | Purpose |
|---------|-----|-----------|---------|
| Flask API | http://localhost:5000 | None | System status, events, metrics |
| Prometheus | http://localhost:9090 | None | Metrics database |
| Grafana | http://localhost:3000 | admin/admin | Dashboards visualization |

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest src/ -v

# With coverage
pytest src/ --cov=src --cov-report=html

# Specific test
pytest src/test_anomaly_detector.py -v

# Run with markers
pytest src/ -m unit -v
```

## 📡 API Endpoints

### Status & Health
```bash
GET /api/status          # Health check
GET /health              # Docker health probe
GET /api/state           # Current system state
```

### Data & Metrics
```bash
GET /api/events          # Event history
GET /api/events?limit=50 # Last 50 events
GET /api/stats           # Statistics
GET /metrics             # Prometheus metrics
```

### Information
```bash
GET /api/version         # App version info
GET /api/config          # Configuration (non-sensitive)
```

## 🔍 Monitoring

### Prometheus Queries
```promql
anomalies_total          # Total anomalies detected
healings_total           # Total healing actions
system_state             # Current state (0,1,2,3)
```

### View Logs
```bash
tail -f src/logs/system.log     # Live logs
grep ERROR src/logs/system.log  # Errors only
```

### Database Queries
```bash
# Event count
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"

# Last 10 events
sqlite3 self_healing.db "SELECT * FROM events ORDER BY id DESC LIMIT 10;"

# Events by type
sqlite3 self_healing.db "SELECT event_type, COUNT(*) FROM events GROUP BY event_type;"

# High confidence anomalies
sqlite3 self_healing.db "SELECT * FROM events WHERE event_type='ANOMALY' AND confidence > 0.8;"
```

## 🔧 Configuration

### Key Settings

**ML Detection** (src/api.py or src/main.py):
```python
WINDOW_SIZE = 5              # Sliding window samples
MIN_ANOMALIES = 3            # Trigger healing after N
CONFIDENCE_THRESHOLD = 0.6   # Z-score threshold
MAX_CONSECUTIVE_ERRORS = 10  # Circuit breaker
```

**Anomaly Threshold** (src/anomaly_detector.py):
```python
ZSCORE_THRESHOLD = 2.5       # Standard deviations
```

**Database** (src/database.py):
```python
_MAX_EVENTS = 10_000         # Prune at this size
```

**Logging** (src/logger.py):
```python
maxBytes = 10 * 1024 * 1024  # 10 MB rotation
backupCount = 5              # Keep 5 files
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Artifact not found` | `cd src && python train.py && cd ..` |
| `Database locked` | `rm -f self_healing.db-shm self_healing.db-wal` |
| `Port in use` | `lsof -i :5000` → kill process or change port |
| `Email not sending` | Check `.env` SMTP credentials, use Google App Password |
| `No metrics` | `curl http://localhost:5000/metrics` to test |
| `Rate limited (429)` | Wait 1 minute or add API key |

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| README.md | Feature overview & quick start | Everyone |
| API_DOCUMENTATION.md | API endpoint reference | Developers |
| DEPLOYMENT_GUIDE.md | How to deploy | DevOps |
| TROUBLESHOOTING_GUIDE.md | Fix common issues | Operations |
| ARCHITECTURE_DECISIONS.md | Design rationale | Architects |
| PRODUCTION_ASSESSMENT.md | Readiness analysis | Management |
| IMPROVEMENTS_SUMMARY.md | Changes summary | Teams |

## 🔐 Security

### Before Production:
- [ ] Add API authentication (JWT/API keys)
- [ ] Enable HTTPS/TLS
- [ ] Add input validation
- [ ] Configure rate limiting per user
- [ ] Set up secrets management

### Already Implemented:
- ✅ Non-root Docker user
- ✅ Security headers
- ✅ Rate limiting (60 req/min)
- ✅ SSL for SMTP
- ✅ Rotating logs
- ✅ Environment variables for secrets

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Restart app
docker-compose restart app

# Stop all
docker-compose down

# Clean up
docker-compose down -v  # Remove volumes too
```

## ☸️ Kubernetes Commands

```bash
# Check pods
kubectl get pods -n self-healing

# View logs
kubectl logs -f <pod-name> -n self-healing

# Port-forward
kubectl port-forward svc/self-healing-app 5000:5000 -n self-healing

# Check events
kubectl get events -n self-healing

# Describe pod
kubectl describe pod <pod-name> -n self-healing

# Scale
kubectl scale deployment/self-healing-app --replicas=3 -n self-healing
```

## 💾 Backup & Recovery

```bash
# Backup database
cp self_healing.db self_healing.db.backup

# Backup models
cp artifacts.joblib artifacts.joblib.backup

# Restore
cp self_healing.db.backup self_healing.db

# Verify
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"
```

## 🔄 Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and test
pytest src/ -v --cov=src

# Format code (if using black)
black src/

# Lint (if using flake8)
flake8 src/

# Commit
git add .
git commit -m "feat: description of changes"

# Push and create PR
git push origin feature/my-feature
```

## 📊 Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Metrics collection | ~50ms | psutil calls |
| Anomaly detection | ~5ms | Z-score calculation |
| Fault classification | ~10ms | Random Forest |
| Database insert | ~20ms | SQLite WAL |
| API response | <100ms | Average latency |
| Full cycle | ~5s | Configured |
| Memory footprint | ~150MB | ML models + Python |
| CPU (idle) | <1% | Minimal baseline |

## 🎯 Key Files to Know

```
src/
├── api.py                    # Flask application (main entry)
├── main.py                   # Standalone engine
├── anomaly_detector.py       # ML anomaly detection
├── fault_classifier.py       # ML fault classification
├── healing_engine.py         # Recovery actions
├── metrics_collector.py       # System metrics
├── database.py               # SQLite operations
├── alert_service.py          # Email notifications
├── logger.py                 # Logging setup
├── prometheus_exporter.py    # Metrics export
├── test_*.py                 # Unit tests (31 tests)
└── logs/                     # Rotating log files

Root/
├── README.md                 # Main documentation
├── API_DOCUMENTATION.md      # API reference
├── DEPLOYMENT_GUIDE.md       # Deployment steps
├── TROUBLESHOOTING_GUIDE.md  # Fix issues
├── ARCHITECTURE_DECISIONS.md # Design decisions
├── docker-compose.yml        # Multi-service orchestration
├── prometheus.yml            # Metrics scrape config
├── pytest.ini               # Test configuration
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── artifacts.joblib         # ML models (generated)
```

## 🚦 State Machine

```
NORMAL (baseline operation)
   ↓ (MIN_ANOMALIES detected in WINDOW_SIZE)
DEGRADED (anomaly confirmed)
   ↓ (trigger healing)
HEALING (recovery in progress)
   ↓ (cooldown 60s, metrics normalize)
RECOVERED (successfully recovered)
   ↓ (return to baseline)
NORMAL
```

## 📞 Getting Help

1. **Check logs**: `tail -f src/logs/system.log`
2. **Read guide**: `cat TROUBLESHOOTING_GUIDE.md | grep ERROR_MESSAGE`
3. **Test health**: `curl http://localhost:5000/api/status`
4. **Check database**: `sqlite3 self_healing.db ".tables"`
5. **Review API**: `curl -s http://localhost:5000/api/version | jq .`

## 🎓 Learning Path

1. **Start here**: README.md (5 min)
2. **Understand API**: API_DOCUMENTATION.md (10 min)
3. **Run tests**: `pytest src/ -v` (5 min)
4. **Read architecture**: ARCHITECTURE_DECISIONS.md (15 min)
5. **Deploy**: DEPLOYMENT_GUIDE.md (20 min)
6. **Troubleshoot**: TROUBLESHOOTING_GUIDE.md (reference)

---

**Last Updated**: 2026-04-23  
**Version**: 1.0.0  
**Status**: Production-ready documentation complete
