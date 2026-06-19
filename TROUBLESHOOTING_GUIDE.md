# Troubleshooting Guide

## Common Issues & Solutions

### Application Won't Start

#### Error: `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

---

#### Error: `RuntimeError: Artifact file not found. Run training first.`

**Solution:**
```bash
# Train ML models (generates artifacts.joblib)
cd src
python train.py

# Verify artifact was created
ls -lah artifacts.joblib

# Restart application
cd ..
python src/api.py
```

---

#### Error: `sqlite3.OperationalError: database is locked`

**Why it happens**: 
- Multiple processes accessing database simultaneously
- Stale WAL checkpoint files

**Solution:**
```bash
# Stop all processes accessing the database
docker-compose down
# or kill all Python processes

# Remove WAL files (if stuck)
rm -f self_healing.db-shm self_healing.db-wal

# Restart application
docker-compose up -d
```

---

### API Issues

#### No Response from `/api/status`

**Diagnosis:**
```bash
# Check if Flask is running
curl -v http://localhost:5000/api/status

# Check if port is in use
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Check logs
tail -f src/logs/system.log
```

**Solution:**
```bash
# Restart Flask application
docker-compose restart app
# or
python src/api.py
```

---

#### 429 Too Many Requests

**Why it happens**: Rate limit exceeded (60 requests/minute)

**Temporary solution:**
```bash
# Wait for rate limit window to reset
# Or retry from different IP
curl -H "X-Forwarded-For: 192.168.1.1" http://localhost:5000/api/status
```

**Permanent solution**: 
- Add API authentication (see Security section)
- Whitelist trusted IPs
- Implement per-user rate limiting

---

#### Empty `/api/events` response

**Why it happens**: No events have been logged yet

**Solution:**
```bash
# Check system state
curl http://localhost:5000/api/state

# Run stress test to generate events
cd src && python stress_test.py

# Verify events were created
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"
```

---

### Database Issues

#### Cannot query events table

```bash
# Check if table exists
sqlite3 self_healing.db ".tables"

# Check table structure
sqlite3 self_healing.db ".schema events"

# Verify data
sqlite3 self_healing.db "SELECT COUNT(*) FROM events;"
```

**Solution if table missing:**
```bash
# Reinitialize database
python -c "from database import init_db; init_db()"

# Verify
sqlite3 self_healing.db ".tables"
```

---

#### Database file keeps growing

**Why it happens**: WAL checkpoint not occurring, or events not pruning

**Solution:**
```bash
# Force WAL checkpoint
sqlite3 self_healing.db "PRAGMA wal_checkpoint(RESTART);"

# Check file size
ls -lh self_healing.db*

# Manually trigger pruning
python -c "from database import prune_events; prune_events()"

# Verify size
ls -lh self_healing.db*
```

---

### Email Alerts Not Working

#### Test SMTP connection:
```bash
python -c "
import smtplib, ssl
context = ssl.create_default_context()
with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
    server.starttls(context=context)
    server.login('your@gmail.com', 'your_app_password')
    print('✓ SMTP connection successful')
"
```

#### Gmail-specific issues:

1. **Error: "invalid SMTP credentials"**
   - Verify .env has correct credentials: `cat .env | grep SENDER`
   - Check Gmail app-specific password (not main password)
   - Ensure 2FA is enabled on Gmail account
   - Create new app password: https://myaccount.google.com/apppasswords

2. **Error: "SMTP connection timed out"**
   - Check firewall blocking port 587
   - Try alternative SMTP provider
   - Verify network connectivity: `curl -I https://smtp.gmail.com:587`

3. **Alerts sent but never received**
   - Check spam/promotions folder
   - Verify recipient email in .env: `cat .env | grep ADMIN_EMAIL`
   - Check email logs: `grep -i "alert\|email" src/logs/system.log`

#### Disable alerts temporarily:
```bash
# Leave SENDER_PASSWORD empty in .env
SENDER_PASSWORD=

# Restart app
docker-compose restart app
```

---

### Metrics & Monitoring Issues

#### Prometheus not scraping metrics

**Diagnosis:**
```bash
# Check if app is exporting metrics
curl http://localhost:5000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq .

# Check prometheus.yml syntax
promtool check config prometheus.yml
```

**Solution:**
```bash
# Verify prometheus.yml points to correct target
cat prometheus.yml

# Restart Prometheus
docker-compose restart prometheus

# Wait for scrape (default: 5 seconds)
sleep 10

# Check metrics in Prometheus UI
# http://localhost:9090/graph?query=anomalies_total
```

---

#### Grafana dashboards empty

**Why it happens**: Prometheus hasn't scraped metrics yet, or datasource misconfigured

**Solution:**
1. Wait 30+ seconds for Prometheus to scrape
2. Verify datasource:
   - Login to Grafana (admin/admin)
   - Configuration → Data Sources
   - Click "Prometheus"
   - URL should be: `http://prometheus:9090`
   - Test connection

3. Reload dashboard:
   - Go to dashboard
   - Press F5 to reload
   - Adjust time range to last hour

---

### Performance Issues

#### High CPU usage (>90%)

**Diagnosis:**
```bash
# Check top processes
top -p $(pgrep -f "python api.py")

# Check app logs for errors
tail -50 src/logs/system.log | grep -i error

# Check stress test is not running
ps aux | grep stress_test
```

**Solution:**
```bash
# Stop stress test if running
pkill -f stress_test.py

# Increase confidence threshold (fewer false positives)
# Edit src/api.py:
# CONFIDENCE_THRESHOLD = 0.7  # instead of 0.6

# Restart
docker-compose restart app
```

---

#### Slow API response times (>1 second)

**Diagnosis:**
```bash
# Profile an API call
time curl http://localhost:5000/api/events

# Check database query performance
sqlite3 self_healing.db "EXPLAIN QUERY PLAN SELECT * FROM events LIMIT 100;"

# Check system resources
free -h
df -h
```

**Solution:**
```bash
# Analyze and rebuild database
sqlite3 self_healing.db "ANALYZE; PRAGMA optimize;"

# Increase database page cache
sqlite3 self_healing.db "PRAGMA cache_size = -64000;"  # 64 MB

# Restart
docker-compose restart app
```

---

### Docker Issues

#### Container exits immediately

```bash
# Check exit code
docker-compose ps app

# View full logs
docker-compose logs app --tail=100

# Try running interactively
docker-compose run --rm app python api.py
```

---

#### Port already in use

```bash
# Find process using port
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows

# Or use different port
docker-compose override add:
environment:
  - FLASK_PORT=5001
```

---

### Kubernetes Issues

#### Pod stuck in CrashLoopBackOff

```bash
# Check pod logs
kubectl logs <pod-name> -n self-healing

# Check pod events
kubectl describe pod <pod-name> -n self-healing

# Check resource constraints
kubectl get resourcequota -n self-healing
```

---

#### Service not accessible

```bash
# Check service
kubectl get svc -n self-healing

# Port-forward for testing
kubectl port-forward svc/self-healing-app 5000:5000 -n self-healing

# Check endpoints
kubectl get endpoints -n self-healing
```

---

## Diagnostic Commands

### Quick Health Check
```bash
#!/bin/bash
echo "=== Health Check ==="
echo "Flask status:"
curl -s http://localhost:5000/api/status | jq .

echo -e "\nSystem state:"
curl -s http://localhost:5000/api/state | jq .

echo -e "\nPrometheus targets:"
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .job, state: .health}'

echo -e "\nDatabase:"
sqlite3 self_healing.db "SELECT 'Total events:', COUNT(*) FROM events UNION ALL SELECT 'DB size (MB):', ROUND(page_count * page_size / 1024 / 1024, 2) FROM pragma_page_count(), pragma_page_size();"

echo -e "\nApplication logs (last 10 errors):"
grep -i error src/logs/system.log | tail -10

echo -e "\n=== End Health Check ==="
```

---

## Getting Help

### Before contacting support, collect:
1. Full error message and stack trace
2. Relevant logs (last 50 lines): `tail -50 src/logs/system.log`
3. System info:
   ```bash
   docker-compose ps
   docker stats
   curl -s http://localhost:5000/api/version | jq .
   ```
4. Configuration (sanitized): `cat .env | grep -v PASSWORD`
5. Reproduction steps

### Where to report issues:
- **GitHub Issues**: Feature requests, bugs
- **Email**: security@example.com (security issues only)
- **Slack**: #self-healing-support channel

---

## Quick Reference

| Issue | Check | Fix |
|-------|-------|-----|
| App won't start | `ps aux \| grep python` | `pip install -r requirements.txt` |
| No metrics | `curl localhost:5000/metrics` | Restart Flask: `docker-compose restart app` |
| Alerts failing | `.env` has credentials | Verify app password for Gmail |
| DB locked | `lsof -i :5000` | Remove .db-shm/.db-wal files |
| Slow API | `EXPLAIN QUERY PLAN` | `sqlite3 db "PRAGMA optimize;"` |
| High CPU | Check logs for errors | Increase confidence threshold |
