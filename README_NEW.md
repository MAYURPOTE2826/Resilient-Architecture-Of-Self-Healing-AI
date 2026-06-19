# Resilient Architecture for Self-Healing System using Machine Learning

A production-ready, AI-powered self-healing system that detects infrastructure anomalies and automatically triggers remediation actions with minimal human intervention.

## 🎯 Features

- **Intelligent Anomaly Detection** - Uses Isolation Forest + Z-score analysis for real-time anomaly detection
- **Automated Fault Classification** - Random Forest classifier identifies root causes (High CPU, Memory, Disk I/O, Latency)
- **Self-Healing Actions** - Automatic service recovery with healing cooldown to prevent storms
- **Real-time Monitoring** - Prometheus metrics export with Grafana dashboards
- **Production-Grade Resilience** - Circuit breakers, rate limiting, health checks, graceful degradation
- **Comprehensive Logging** - Structured logging with rotating files and full event audit trail
- **Email Notifications** - Real-time alerts on anomalies and healing actions (configurable)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Metrics Collection Layer                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ metrics_collector.py - CPU, Memory, Disk I/O, Latency│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Machine Learning Analysis Layer                 │
│  ┌───────────────────────┬─────────────────────────────┐    │
│  │ anomaly_detector.py   │ fault_classifier.py         │    │
│  │ (Z-score + IF)        │ (Random Forest)             │    │
│  └───────────────────────┴─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Response & Healing Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ healing_engine.py - Execute recovery, Log events     │   │
│  │ alert_service.py - Send notifications               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│            Observability & Persistence Layer                 │
│  ┌─────────────────┬──────────────┬──────────────────────┐  │
│  │ prometheus      │ grafana      │ sqlite database      │  │
│  │ (metrics)       │ (dashboards) │ (event audit trail)  │  │
│  └─────────────────┴──────────────┴──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
self-healing-ai/
├── src/                          # Application source code
│   ├── api.py                   # Flask API server (port 5000)
│   ├── main.py                  # Standalone ML engine
│   ├── metrics_collector.py      # System metrics collection
│   ├── anomaly_detector.py       # Anomaly detection logic
│   ├── fault_classifier.py       # Fault type classification
│   ├── healing_engine.py         # Automated recovery actions
│   ├── alert_service.py          # Email notifications
│   ├── system_state.py           # State machine (NORMAL, DEGRADED, HEALING, RECOVERED)
│   ├── database.py               # SQLite operations & WAL mode
│   ├── logger.py                 # Rotating file logging
│   ├── prometheus_exporter.py    # Prometheus metrics endpoint
│   ├── model_store.py            # ML artifact management
│   ├── train.py                  # Model training script
│   ├── Dockerfile                # Container image definition
│   ├── requirements.txt           # Python dependencies
│   ├── conftest.py               # Pytest fixtures
│   ├── test_*.py                 # Unit tests
│   └── logs/                     # Rotating log files
│
├── Data/                         # Training datasets
│   └── raw_dataset/              # System metrics time series
│
├── frontend/                     # UI components (future)
├── grafana/                      # Grafana dashboard provisioning
│   └── provisioning/
│       ├── dashboards/           # Dashboard JSON files
│       └── datasources/          # Prometheus datasource config
│
├── docker-compose.yml            # Multi-service orchestration
├── prometheus.yml                # Prometheus scrape configuration
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development/testing dependencies
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional)
- Linux/macOS (Windows support via WSL2 or Git Bash)

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/username/self-healing-ai.git
cd self-healing-ai
```

**2. Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your SMTP credentials (Gmail recommended)
# SENDER_EMAIL=your_email@gmail.com
# SENDER_PASSWORD=your_app_specific_password  # Use Google App Password, not main password
# ADMIN_EMAIL=admin@your_domain.com
```

**5. Train ML models:**
```bash
cd src
python train.py
```

**6. Run the application:**
```bash
# Option A: Standalone mode
python main.py

# Option B: Flask API + Web interface
python api.py
```

### Docker Deployment

**Build and run with Docker Compose:**
```bash
docker-compose up -d
```

This starts:
- Flask API: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## 📊 API Endpoints

### Status & Health
- `GET /api/status` - System health check
- `GET /health` - Docker health check

### Metrics & Events
- `GET /api/metrics` - Get Prometheus metrics in text format
- `GET /api/events` - Retrieve event history
- `GET /api/events?limit=100` - Get last N events
- `GET /api/state` - Current system state (NORMAL, DEGRADED, HEALING, RECOVERED)

### System Information
- `GET /api/version` - Application version
- `GET /` - Serve frontend (static HTML)

## 🧪 Testing

### Run all tests:
```bash
pip install -r requirements-dev.txt
pytest src/ -v
```

### Run with coverage report:
```bash
pytest src/ --cov=src --cov-report=html
# View report in htmlcov/index.html
```

### Run specific test file:
```bash
pytest src/test_anomaly_detector.py -v
```

### Run with markers:
```bash
pytest src/ -m unit -v          # Only unit tests
pytest src/ -m integration -v   # Only integration tests
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATA_DIR` | Directory for ML artifacts and database | `./` | No |
| `SENDER_EMAIL` | Gmail address for alerts | "" | No* |
| `SENDER_PASSWORD` | Gmail app-specific password | "" | No* |
| `ADMIN_EMAIL` | Recipient email for alerts | "" | No* |

*Required only if you want email notifications enabled.

### Algorithm Tuning

Edit `src/api.py` or `src/main.py` to adjust:

```python
WINDOW_SIZE = 5                 # Anomaly detection window (samples)
MIN_ANOMALIES = 3              # Trigger healing after N anomalies
CONFIDENCE_THRESHOLD = 0.6     # Z-score confidence threshold
MAX_CONSECUTIVE_ERRORS = 10    # Circuit breaker threshold
```

For anomaly detection, in `src/anomaly_detector.py`:
```python
ZSCORE_THRESHOLD = 2.5         # 2.5 sigma = ~99.4% confidence
```

## 📈 Monitoring

### Grafana Dashboards

Access at http://localhost:3000:

1. **Self-Healing System Dashboard** - Real-time state, anomaly count, healing actions
2. **Metrics Dashboard** - CPU, Memory, Disk I/O, Latency trends
3. **Events Dashboard** - Event timeline and fault types

### Prometheus Metrics

Available at http://localhost:9090/graph:

- `anomalies_total` - Cumulative anomalies detected
- `healings_total` - Cumulative healing actions triggered
- `system_state` - Current system state (0=NORMAL, 1=DEGRADED, 2=HEALING, 3=RECOVERED)

### Application Logs

Logs are written to `src/logs/system.log` with rotation:
- Max file size: 10 MB
- Max backups: 5 files
- Format: `[timestamp] | [level] | [message]`

View logs:
```bash
tail -f src/logs/system.log
```

## 🧬 Machine Learning Models

### Anomaly Detection

**Algorithm**: Isolation Forest + Z-score
- **Purpose**: Detect when system metrics deviate from baseline
- **Baseline**: Calculated during training phase (mean, std dev per metric)
- **Threshold**: 2.5 sigma (99.4% confidence, allows ~0.6% false positives)

### Fault Classification

**Algorithm**: Random Forest Classifier
- **Purpose**: Identify root cause (CPU, Memory, Disk I/O, Latency issues)
- **Training Data**: Labeled time series with known fault types
- **Output**: Primary fault type with confidence scores

### Model Training

```bash
cd src
python train.py --data Data/raw_dataset/
```

This generates `artifacts.joblib` containing:
- Isolation Forest model
- Random Forest classifier
- Baseline statistics for each metric

### Model Artifacts

- **File**: `artifacts.joblib`
- **Validation**: SHA256 hash verification on load
- **Storage**: Copied to container at `/app/data/artifacts.joblib`

## 🔄 Healing Actions

When anomalies are detected and classified, the system:

1. **Detection Phase** (5 second cycle)
   - Collect metrics
   - Detect anomalies (Z-score > 2.5σ)
   - Classify fault type

2. **Validation Phase** (sliding window)
   - Require MIN_ANOMALIES in WINDOW_SIZE
   - Prevent noise-driven false positives

3. **Healing Phase**
   - Log event to database
   - Send admin email alert
   - Execute recovery action (service restart)
   - Update Prometheus metrics

4. **Recovery Phase**
   - Monitor for stabilization
   - Return to NORMAL state
   - 60-second cooldown before next healing (prevent storms)

## 🚨 Stress Testing

Generate a controlled CPU spike to trigger anomaly detection:

```bash
cd src
python stress_test.py
```

Watch the system state progression:
1. NORMAL → baseline metrics
2. DEGRADED → anomaly detected
3. HEALING → recovery action triggered
4. RECOVERED → system stabilized
5. NORMAL → return to baseline

View in Grafana at http://localhost:3000 or Flask API at http://localhost:5000/api/state

## 🔐 Security Features

- ✅ Non-root Docker user
- ✅ Security headers (X-Content-Type-Options, X-Frame-Options, CSP)
- ✅ Rate limiting (60 requests/minute)
- ✅ SSL/TLS for email (certificate verification)
- ✅ Environment-based secrets (no hardcoded credentials)
- ✅ SQLite WAL mode (safe concurrent access)
- ✅ Input validation on all API endpoints
- ✅ Rotating log files (prevent disk exhaustion)

## 🐛 Troubleshooting

### Artifact file not found
```
RuntimeError: Artifact file not found. Run training first.
```
**Solution**: Run `python src/train.py` to generate ML models.

### Email alerts not sending
```
Alert failed: invalid SMTP credentials
```
**Solution**:
1. Verify .env file exists with valid credentials
2. Use Gmail app-specific password (not main password)
3. Enable "Less secure apps" if not using app password
4. Check `src/logs/system.log` for SMTP errors

### Prometheus not scraping
```
No metrics loading in Prometheus dashboard
```
**Solution**:
1. Verify Flask app is running: `curl http://localhost:5000/metrics`
2. Check `prometheus.yml` has correct target: `localhost:5000`
3. Restart Prometheus: `docker-compose restart prometheus`

### Database locked error
```
sqlite3.OperationalError: database is locked
```
**Solution**: WAL mode is enabled (see `database.py`). This is normal and rare. If persistent:
1. Stop all processes accessing the database
2. Delete `self_healing.db-shm` and `self_healing.db-wal` files
3. Restart the application

## 📊 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Metrics Collection | ~50ms | psutil calls |
| Anomaly Detection | ~5ms | Z-score calculation |
| Fault Classification | ~10ms | Random Forest inference |
| Database Insert | ~20ms | SQLite with WAL |
| Email Send | ~2sec | Async background thread |
| Full Cycle Time | ~5sec | Configured in main loop |
| Memory Footprint | ~150 MB | ML models + base Python |
| CPU Usage (idle) | <1% | Minimal CPU when normal |

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributing

Contributions welcome! Please:
1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests: `pytest src/ --cov=src`
3. Follow PEP 8: Run `black src/ && flake8 src/`
4. Submit pull request with description

## 📞 Support

- **Issues**: Create a GitHub issue with reproduction steps
- **Questions**: Open a discussion thread
- **Security**: Email security@example.com (do not use GitHub issues)

## 🔄 Release History

- **v1.0.0** (2026-04-23) - Initial release
  - Anomaly detection with Isolation Forest
  - Fault classification with Random Forest
  - Email alerting
  - Prometheus/Grafana integration
  - Docker deployment ready

---

**Built with ❤️ for reliable infrastructure**
