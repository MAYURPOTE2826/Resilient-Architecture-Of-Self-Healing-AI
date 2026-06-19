# Operations Runbook — Self-Healing Engine

**Version:** 1.0  
**Date:** 2026-06-16  
**Audience:** Operations Team, SREs, On-Call  
**Classification:** Internal - Confidential  

---

## Quick Reference

### Critical Contacts
- **On-Call Duty:** [Phone/Pager]
- **Incident Commander:** incident@example.com
- **Security Lead:** security@example.com
- **Database Admin:** dba@example.com

### Common Commands

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f app

# Check health
curl -s http://localhost:5000/health | jq

# Restart service
docker compose -f docker-compose.prod.yml restart app

# Graceful shutdown
docker compose -f docker-compose.prod.yml down

# Scale horizontally
docker compose -f docker-compose.prod.yml up -d --scale app=3
```

---

## Section 1: Normal Operations

### 1.1 Daily Checks

**Morning Checklist (9:00 AM)**

```bash
# 1. Verify service is running
curl -s http://localhost:5000/live | jq '.alive'

# 2. Check error rate (last hour)
curl -s http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[1h]) | jq

# 3. Verify database connection
psql $DATABASE_URL -c "SELECT 1" && echo "Database OK"

# 4. Check disk space
df -h | grep -E "root|home"

# 5. Check memory usage
free -h

# 6. Review logs for errors
docker logs app | tail -100 | grep -i error
```

**Expected Results:**
- ✅ Liveness check returns `"alive": true`
- ✅ Error rate < 0.1%
- ✅ Database connection succeeds
- ✅ Disk available > 20%
- ✅ Memory used < 80%
- ✅ No error logs

### 1.2 Weekly Maintenance

**Every Monday 2:00 AM**

1. **Database Maintenance**
   ```bash
   # Vacuum database
   docker exec postgres vacuumdb -U user -d self_healing
   
   # Analyze tables
   docker exec postgres analyzedb -U user -d self_healing
   ```

2. **Log Rotation**
   ```bash
   # Archive logs
   tar -czf logs-$(date +%Y%m%d).tar.gz logs/
   rm logs/*.log
   ```

3. **Backup Verification**
   ```bash
   # Verify last backup
   ls -lh /backups/ | head -3
   
   # Test restore (to staging)
   pg_restore /backups/latest.dump -d test_self_healing
   ```

4. **Security Audit**
   ```bash
   # Check failed authentication attempts
   docker logs app | grep "Failed login" | wc -l
   
   # Check token revocations
   docker logs app | grep "Token revoked" | wc -l
   ```

---

## Section 2: Troubleshooting

### 2.1 Service Won't Start

**Symptom:** `docker compose up` fails immediately

**Diagnosis:**

```bash
# 1. Check configuration
env | grep -E "SECRET_KEY|JWT_SECRET|ADMIN"

# 2. Validate configuration
docker run --rm -e APP_ENV=production app python -c "from config import settings; print('OK')"

# 3. Check logs
docker compose logs app | tail -50
```

**Common Causes & Fixes:**

| Cause | Error | Fix |
|-------|-------|-----|
| Missing SECRET_KEY | "SECRET_KEY must be set" | Generate and set SECRET_KEY |
| Weak JWT_SECRET | "JWT_SECRET must be at least 32" | Use 64-char hex string |
| Database unavailable | "Connection refused" | Check database is running |
| Port already in use | "Address already in use" | `lsof -i :5000` and kill process |
| Permission denied | "Permission denied" | `sudo chown app:app /app` |

**Resolution:**

```bash
# 1. Fix the issue
# 2. Restart service
docker compose down
docker compose up -d

# 3. Verify
curl -s http://localhost:5000/health | jq '.status'

# 4. Monitor
docker compose logs -f app
```

### 2.2 High CPU Usage

**Symptom:** CPU usage consistently > 80%

**Diagnosis:**

```bash
# 1. Identify top processes
top -b -n 1 | head -15

# 2. Check Flask app threads
docker exec app ps -eLo pid,tid,cmd | grep python

# 3. Check database queries
psql $DATABASE_URL -c "SELECT pid, usename, query FROM pg_stat_activity WHERE state='active';"

# 4. Check Prometheus queries
curl -s http://localhost:9090/api/v1/query?query=up | jq
```

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Slow query | Kill query: `pg_terminate_backend(pid)` or optimize index |
| Memory leak | Restart app: `docker compose restart app` |
| Too many connections | Reduce pool size or scale database |
| Heavy ML computation | Throttle: `CONFIDENCE_THRESHOLD = 0.8` |
| Memory pressure | Increase available memory or scale horizontally |

### 2.3 High Memory Usage

**Symptom:** Memory usage > 90% or service getting OOMKilled

**Diagnosis:**

```bash
# 1. Check memory usage
docker stats --no-stream

# 2. Check process memory
docker exec app ps aux | grep -E "VSZ|RSS"

# 3. Check memory leaks
docker exec app python -c "import psutil; print(psutil.Process().memory_info())"

# 4. Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solution:**

```bash
# Option 1: Restart (if acceptable downtime)
docker compose restart app

# Option 2: Graceful restart
# Stops accepting new requests, waits for in-flight to complete
docker kill -s SIGTERM $(docker ps -q -f name=app)

# Option 3: Scale horizontally (if running single instance)
docker compose up -d --scale app=2

# Option 4: Increase memory limits
# Edit docker-compose.yml limits, then:
docker compose up -d --force-recreate
```

### 2.4 Database Connection Errors

**Symptom:** "Connection refused" or "Connection timeout"

**Diagnosis:**

```bash
# 1. Check database is running
docker compose ps postgres

# 2. Verify connectivity
docker exec app psql $DATABASE_URL -c "SELECT 1"

# 3. Check connection count
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"

# 4. Check connection pool
docker logs app | grep -i "pool\|connection"
```

**Solutions:**

| Issue | Fix |
|-------|-----|
| Database stopped | `docker compose up -d postgres` |
| Network disconnected | Check Docker network: `docker network ls` |
| Pool exhausted | Increase `pool_size` or scale app |
| Connection timeout | Increase timeout: `pool_timeout=60` |
| Stale connection | Enable `pool_recycle=1800` |

### 2.5 High Error Rate

**Symptom:** Error rate > 1% or increasing errors in logs

**Diagnosis:**

```bash
# 1. Check error rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | jq

# 2. Check error logs
docker logs app | grep ERROR | tail -20

# 3. Check specific errors
docker logs app | grep -E "500|503|502" | tail -10

# 4. Check dependencies
for dep in postgres loki prometheus; do
  docker compose ps $dep
done
```

**Common Errors & Fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| 502 Bad Gateway | App crashed | Restart: `docker compose restart app` |
| 503 Service Unavailable | Health check failing | Check `/health` endpoint |
| 500 Internal Error | Exception in code | Check logs for stack trace |
| 429 Too Many Requests | Rate limited | Client needs backoff logic |
| 401 Unauthorized | Invalid token | Verify JWT or API key |

---

## Section 3: Emergency Procedures

### 3.1 Service Down (Emergency)

**SLA:** Restore to health within 5 minutes

**Steps:**

```bash
# 1. Immediate assessment (30 seconds)
curl -s http://localhost:5000/live

# 2. Check basic health (1 min)
docker compose ps
docker compose logs app | tail -50

# 3. Immediate restart (1 min)
docker compose restart app

# 4. Verify recovery (1 min)
for i in {1..30}; do
  curl -s http://localhost:5000/health | jq '.status'
  sleep 1
done

# 5. If still down, escalate to Level 2
```

**Escalation Paths:**

If service doesn't come back:
1. Notify incident commander
2. Check database connectivity
3. Check memory/CPU/disk
4. Review recent deployments
5. Consider rollback

### 3.2 Database Down (Emergency)

**SLA:** Restore within 10 minutes

**Steps:**

```bash
# 1. Check database status
docker compose ps postgres
docker logs postgres | tail -50

# 2. Try to connect
psql $DATABASE_URL -c "SELECT 1" 2>&1

# 3. If stopped, restart
docker compose restart postgres

# 4. Wait for startup (30-60 seconds)
docker logs postgres | grep "ready to accept"

# 5. Verify connection
psql $DATABASE_URL -c "SELECT 1"

# 6. If corruption suspected, restore from backup
# See: Backup Recovery below
```

### 3.3 Disk Space Critical (Emergency)

**Symptom:** Disk usage > 95% or health check failing

**Steps:**

```bash
# 1. Identify large files
du -sh /* | sort -rh | head -10

# 2. Check logs directory
du -sh /app/logs
ls -lhS /app/logs | head -10

# 3. Archive old logs
tar -czf logs-archive-$(date +%Y%m%d).tar.gz /app/logs/*.log.* 
rm /app/logs/*.log.*

# 4. Check database size
du -sh /var/lib/postgresql/

# 5. Purge old data (if needed)
# DELETE FROM events WHERE timestamp < NOW() - INTERVAL '90 days';

# 6. Verify disk space
df -h /

# SLA: < 85% within 15 minutes
```

### 3.4 Security Incident (Emergency)

**Steps:**

```bash
# 1. Immediate containment
# - Revoke all tokens
# - Rotate all API keys
# - Enable extra logging
docker exec app python -c "from token_manager import get_blacklist; get_blacklist().clear()"

# 2. Gather evidence
docker logs app > /tmp/incident-logs-$(date +%Y%m%d_%H%M%S).txt
docker exec app tail -1000 logs/system.log > /tmp/incident-app.log

# 3. Notify security team
# email security@example.com with:
# - Time of detection
# - Nature of incident
# - Evidence collected
# - Actions taken

# 4. Monitor closely
docker logs -f app | grep -E "security|auth|error"

# 5. Implement fixes
# - Patch vulnerability
# - Deploy fixed code
# - Re-enable normal operations

# 6. Conduct post-incident
# - Full forensics
# - Root cause analysis
# - Implement preventive measures
```

---

## Section 4: Deployment & Upgrades

### 4.1 Rolling Deployment

**Zero-downtime deployment strategy**

```bash
# 1. Build new image
docker build -f Dockerfile.prod -t app:v2 .

# 2. Start new instance (blue)
docker compose up -d app

# 3. Verify health of new instance
curl -s http://localhost:5000/health | jq '.status'

# 4. Switch traffic (green → blue)
docker compose stop app_v1 || true

# 5. Verify traffic on new instance
curl -s http://localhost:5000/status | jq

# 6. Monitor for issues (5-15 minutes)
docker compose logs -f app

# 7. Cleanup old instance
docker compose rm app_v1 || true
```

### 4.2 Rollback Procedure

**If deployment fails, rollback to previous version**

```bash
# 1. Detect failure
# - Error rate spikes
# - Health checks fail
# - Performance degrades

# 2. Immediately stop new version
docker compose stop app

# 3. Start previous version
docker compose up -d app_v1

# 4. Verify recovery (< 2 minutes)
for i in {1..20}; do
  status=$(curl -s http://localhost:5000/health | jq '.status')
  echo "$i: $status"
  [ "$status" = "healthy" ] && break
  sleep 3
done

# 5. Investigate failure
# - Review code changes
# - Check logs
# - Identify bug

# 6. Fix and re-deploy
# When ready, re-run deployment
```

---

## Section 5: Backup & Recovery

### 5.1 Create Manual Backup

```bash
# 1. Backup database
pg_dump -U postgres self_healing > backup-$(date +%Y%m%d-%H%M%S).sql

# 2. Compress
gzip backup-*.sql

# 3. Verify backup
zcat backup-*.sql.gz | head -20

# 4. Copy to safe location
scp backup-*.sql.gz backup-server:/backups/

# 5. Verify remote copy
ssh backup-server ls -lh /backups/backup-*.sql.gz | head -3
```

### 5.2 Restore from Backup

```bash
# 1. Verify backup file
ls -lh backup-*.sql.gz

# 2. Stop application
docker compose stop app

# 3. Drop current database
psql -U postgres -c "DROP DATABASE IF EXISTS self_healing;"

# 4. Create fresh database
psql -U postgres -c "CREATE DATABASE self_healing;"

# 5. Restore from backup
gunzip < backup-YYYYMMDD-HHMMSS.sql.gz | psql -U postgres self_healing

# 6. Verify restore
psql -U postgres self_healing -c "SELECT count(*) FROM events;"

# 7. Start application
docker compose up -d app

# 8. Verify recovery
curl -s http://localhost:5000/health | jq '.status'
```

---

## Section 6: Monitoring & Alerting

### 6.1 Key Metrics to Monitor

**Real-time Monitoring (check every hour):**

```bash
# 1. Error rate
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | jq '.data.result[].value[1]'

# 2. Response time (p99)
curl -s 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.99,http_request_duration_seconds)' | jq

# 3. Database connection pool
curl -s 'http://localhost:9090/api/v1/query?query=db_pool_checked_out_connections' | jq

# 4. System resources
docker stats --no-stream

# 5. Anomaly detection rate
curl -s 'http://localhost:9090/api/v1/query?query=increase(anomalies_total[1h])' | jq

# 6. Healing success rate
curl -s 'http://localhost:9090/api/v1/query?query=increase(healings_successful[1h])' | jq
```

### 6.2 Alert Response

**Critical Alerts:**

| Alert | Threshold | Action |
|-------|-----------|--------|
| Error Rate High | > 1% | Check logs, investigate root cause |
| Latency High | p99 > 500ms | Check database, run slow query log |
| Memory High | > 90% | Restart or scale |
| Disk Full | > 95% | Archive logs, cleanup |
| Database Down | Not responding | Restart database |
| Service Down | Health check failing | Check app logs, restart |

---

## Section 7: Performance Optimization

### 7.1 Database Query Optimization

```bash
# 1. Find slow queries
psql $DATABASE_URL -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"

# 2. Check missing indexes
psql $DATABASE_URL -c "SELECT schemaname, tablename FROM pg_stat_user_tables WHERE idx_scan = 0;"

# 3. Create indexes for missing scans
psql $DATABASE_URL -c "CREATE INDEX idx_events_timestamp ON events(timestamp);"

# 4. Analyze query plan
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM events WHERE timestamp > NOW() - INTERVAL '1 day';"

# 5. Vacuum database
psql $DATABASE_URL -c "VACUUM ANALYZE events;"
```

### 7.2 Application Performance Tuning

```python
# In config/settings.py:
# - Increase pool_size if connection pool exhausted
# - Reduce MIN_ANOMALIES if detection is slow
# - Adjust WINDOW_SIZE for memory usage
# - Enable caching for ML models

# Check current settings:
docker exec app python -c "from config import settings; print(settings.dict())"
```

---

## Section 8: Disaster Recovery

### 8.1 Complete System Restoration

**Time to Recovery: < 1 hour**

```bash
# 1. Provision new infrastructure
# - New server with Docker
# - New database instance
# - New Redis cache

# 2. Restore database from backup
psql -U postgres -d self_healing < backup-latest.sql

# 3. Deploy application
docker compose -f docker-compose.prod.yml up -d

# 4. Restore configuration
# - Copy .env file
# - Copy ML model artifacts

# 5. Verify all systems
curl -s http://localhost:5000/health | jq

# 6. Monitor for 24 hours
docker logs -f app
```

### 8.2 Multi-Region Failover

If primary region fails:

```bash
# 1. Detect failure (automated)
# - Health checks fail in primary
# - Failover automation triggers

# 2. DNS failover (managed by Route53/Cloudflare)
# - Automatic within 30 seconds

# 3. Secondary region activation
# - Restore from replicated backup
# - Promote read replica to primary

# 4. Verify secondary region health
curl -s https://backup.example.com/health | jq '.status'

# 5. Monitor for issues
# 6. Plan return to primary
```

---

## Appendix A: Command Reference

### Essential Commands

```bash
# Status & Health
docker compose ps                                    # List services
docker compose logs app                             # View logs
curl http://localhost:5000/health                   # Health check
docker stats                                        # Resource usage

# Operations
docker compose up -d                                # Start
docker compose down                                 # Stop
docker compose restart app                          # Restart
docker compose scale app=3                          # Scale

# Debugging
docker exec app bash                                # Shell access
docker exec app tail -f logs/system.log             # Follow logs
docker exec app ps aux                              # Process list
docker exec app python -c "code"                    # Run Python

# Database
psql $DATABASE_URL -c "SELECT ..."                 # Query database
pg_dump $DATABASE_URL > backup.sql                 # Backup
pg_restore < backup.sql                            # Restore

# Monitoring
docker logs -f app                                  # Follow app logs
docker compose logs -f postgres                    # Follow DB logs
curl http://localhost:9090/metrics                 # Prometheus metrics
```

---

**Last Updated:** 2026-06-16  
**Next Review:** 2026-06-30  
**Owner:** Operations Lead  
**Reviewers:** SRE Team

---

*This runbook is a living document. Update it regularly as procedures change.*
