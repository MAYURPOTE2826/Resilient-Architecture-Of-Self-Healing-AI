# Disaster Recovery Plan — Self-Healing Engine

**Version:** 1.0  
**Classification:** Internal - Confidential  
**Last Updated:** 2026-06-16  
**Next Review:** 2026-06-30

---

## Executive Summary

This Disaster Recovery Plan (DRP) defines procedures for recovering from service outages, data loss, or infrastructure failures. The plan supports Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) required for production systems.

### Key Metrics

| Metric | Target | Implementation |
|--------|--------|-----------------|
| **RTO (Recovery Time Objective)** | < 1 hour | Redundant infrastructure, automated failover |
| **RPO (Recovery Point Objective)** | < 15 minutes | Continuous replication, hourly backups |
| **MTTR (Mean Time To Restore)** | < 30 minutes | Documented procedures, test drills quarterly |
| **Availability SLA** | 99.95% | Multi-zone deployment, redundancy |

---

## Section 1: Failure Categories & Responses

### 1.1 Single Instance Failure

**Failure Mode:** One application pod/container crashes

**Recovery:** < 5 minutes

```bash
# Detection (automated)
# Kubernetes/Docker Compose detects crash
# Automatic restart triggered

# If automatic restart fails:
# 1. Identify failed instance
docker ps -a | grep app

# 2. Get logs
docker logs <container_id> | tail -50

# 3. Restart container
docker restart <container_id>

# 4. Monitor recovery
docker logs -f <container_id>

# 5. If repeated failures, escalate to Level 2
```

**Prevention:**
- Configure restart policies: `restart_policy: always`
- Set memory limits to prevent OOMKill
- Implement resource requests/limits

---

### 1.2 Database Failure

**Failure Mode:** Database instance becomes unavailable

**Recovery:** < 15 minutes

#### Scenario A: Database Process Crashed

```bash
# 1. Verify database is down
psql $DATABASE_URL -c "SELECT 1" 2>&1
# Output: "Connection refused"

# 2. Check database container
docker ps | grep postgres

# 3. Check logs
docker logs postgres | tail -100

# 4. Restart database
docker restart postgres

# 5. Wait for startup (~30 seconds)
docker logs postgres | grep "ready to accept"

# 6. Verify connectivity
psql $DATABASE_URL -c "SELECT version();"

# 7. Check data integrity
psql $DATABASE_URL -c "SELECT count(*) FROM events;"

# 8. Monitor for errors
docker logs -f postgres
```

#### Scenario B: Disk Corruption

```bash
# 1. Stop application to prevent further corruption
docker compose stop app

# 2. Stop database
docker stop postgres

# 3. Restore from backup (see Section 3)
pg_restore /backups/latest.dump -d self_healing

# 4. Verify restored data
psql $DATABASE_URL -c "SELECT count(*) FROM events;"

# 5. Resume application
docker compose up -d app

# 6. Monitor closely for 24 hours
```

#### Scenario C: Replication Lag

```bash
# 1. Check replication status
psql $DATABASE_URL -c "SELECT slot_name, restart_lsn, confirmed_flush_lsn FROM pg_replication_slots;"

# 2. If lag > 10MB, increase wal_keep_size
# In postgresql.conf:
wal_keep_size = 1GB

# 3. Reload configuration
docker exec postgres pg_ctl reload

# 4. Monitor lag
watch -n 5 "psql $DATABASE_URL -c \"SELECT slot_name, confirmed_flush_lsn FROM pg_replication_slots;\""
```

---

### 1.3 Storage/Disk Failure

**Failure Mode:** Disk fills up or becomes corrupted

**Recovery:** < 30 minutes

```bash
# 1. Immediate mitigation
# - Stop accepting writes
docker compose stop app

# 2. Identify issue
df -h /
du -sh /* | sort -rh

# 3. If disk full (< 1GB free):
# a) Archive and remove old logs
tar -czf logs-archive-$(date +%Y%m%d).tar.gz logs/
rm logs/*.log

# b) Clean temporary files
rm -rf /tmp/*
docker system prune -f

# c) Resize volume
# - If cloud: increase volume size
# - If on-prem: add new disk

# 4. If corruption detected:
# - Mount read-only
# - Run fsck (offline)
# - Restore from backup

# 5. Resume service
docker compose up -d app

# 6. Monitor disk usage
watch -n 60 "df -h /"
```

---

### 1.4 Network Partition

**Failure Mode:** Service can't communicate with dependencies

**Recovery:** < 5 minutes (automatic)

```bash
# Detection (automatic)
# Liveness/readiness checks fail

# Resolution (automatic)
# Traffic routed to healthy instance
# Partition heals, service recovers

# Manual verification:
# 1. Check network connectivity
docker exec app ping -c 5 postgres

# 2. Check DNS resolution
docker exec app getent hosts postgres

# 3. Restart networking
# On Docker:
docker network disconnect app-network app
docker network connect app-network app

# On Kubernetes:
kubectl rollout restart deployment/app
```

---

### 1.5 Region/Zone Failure

**Failure Mode:** Entire availability zone goes down

**Recovery:** < 60 minutes

**Architecture Requirement:** Multi-zone deployment

```bash
# 1. Automatic failover
# - DNS updated to healthy region
# - Traffic routed to secondary region
# - Within 30 seconds

# 2. Manual verification
# Check secondary region health
curl -s https://us-west-1.example.com/health | jq '.status'

# 3. Restore application state
# - Promote read replica to primary
# - Restore from replicated backup

# 4. Verify data consistency
psql $DATABASE_URL -c "SELECT count(*) FROM events;"
psql $STANDBY_DATABASE_URL -c "SELECT count(*) FROM events;"

# 5. Monitor for 24 hours
docker logs -f app | grep -E "error|exception|warning"

# 6. Plan return to failed zone
# - Replace infrastructure
# - Restore replication
# - Sync data
# - Switch traffic back
```

---

## Section 2: Backup Strategy

### 2.1 Backup Types

**Full Backup (Daily, 2:00 AM UTC)**
```bash
pg_dump -F c self_healing > backup-full-$(date +%Y%m%d).dump
gzip backup-full-*.dump
```

**Incremental Backup (Hourly)**
```bash
# PostgreSQL WAL archiving
# Configured in postgresql.conf:
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
```

**Transaction Log Backup**
```bash
# Enables PITR (Point-in-Time Recovery)
# Stored for 7 days
```

### 2.2 Backup Storage

**Primary Backups:**
- Location: `/backups/` on primary server
- Retention: 30 days
- Verification: Hourly

**Off-site Backups:**
- Location: S3 / Cloud Storage
- Retention: 90 days
- Replication: Real-time
- Encryption: AES-256

**Compliance Backups:**
- Location: Immutable storage
- Retention: 1 year
- For: Audit, legal hold

### 2.3 Backup Verification

```bash
# Daily backup test (automated)
1. Restore backup to test database
2. Run data integrity checks
3. Verify row counts match production
4. Test query performance
5. Alert if any check fails

# Monthly backup drill (manual)
1. Restore latest backup to staging
2. Run full integration tests
3. Simulate production traffic
4. Verify application works
5. Document restoration time
```

---

## Section 3: Recovery Procedures

### 3.1 Recovery from Recent Backup (< 24 hours)

**Time to Recovery: 15-30 minutes**

```bash
# 1. Stop application
docker compose stop app

# 2. Create backup of corrupted database (for forensics)
pg_dump self_healing > corrupted-backup-$(date +%Y%m%d_%H%M%S).dump

# 3. List available backups
ls -lh /backups/ | head -10

# 4. Select backup (usually latest)
BACKUP_FILE="/backups/backup-full-$(date -d yesterday +%Y%m%d).dump"

# 5. Drop current database
psql -U postgres -c "DROP DATABASE IF EXISTS self_healing;"

# 6. Create empty database
psql -U postgres -c "CREATE DATABASE self_healing;"

# 7. Restore from backup
pg_restore -d self_healing $BACKUP_FILE

# 8. Verify restore
psql self_healing -c "SELECT count(*) as event_count FROM events;"

# 9. Run post-recovery checks
psql self_healing -c "VACUUM ANALYZE;"
psql self_healing -c "REINDEX DATABASE self_healing;"

# 10. Restart application
docker compose up -d app

# 11. Verify application health
curl -s http://localhost:5000/health | jq '.status'

# 12. Monitor for issues
docker logs -f app
```

### 3.2 Point-in-Time Recovery (PITR)

**For recovering to specific point in time**

```bash
# 1. Stop application
docker compose stop app

# 2. Get latest full backup
BACKUP_FILE=$(ls -t /backups/backup-full-*.dump | head -1)

# 3. Get backup timestamp
BACKUP_TIME=$(stat -c %y $BACKUP_FILE | awk '{print $1 " " $2}')

# 4. List available WAL files (transaction logs)
ls -lh /archive/ | grep wal

# 5. Restore to point in time
# Example: restore to 2 hours ago
psql self_healing -c "
  SELECT now() - INTERVAL '2 hours' as recovery_target_time
"

# 6. Perform recovery
# - Restore full backup
# - Replay WAL files up to recovery_target_time
# - Use: recovery_target_timeline and recovery_target_xid

# 7. Detailed steps:
# a) Stop database
docker stop postgres

# b) Clear data directory
rm -rf /var/lib/postgresql/data/*

# c) Restore base backup
pg_restore $BACKUP_FILE -d self_healing

# d) Create recovery configuration
cat > /var/lib/postgresql/data/recovery.conf << EOF
restore_command = 'cp /archive/%f %p'
recovery_target_timeline = latest
recovery_target_time = '2026-06-16 14:30:00 UTC'
recovery_target_inclusive = true
EOF

# e) Start database (will recover)
docker start postgres

# f) Monitor recovery
docker logs postgres | grep -i recovery

# g) Verify data
psql self_healing -c "SELECT max(created_at) FROM events;"
```

### 3.3 Disaster Recovery Drill

**Quarterly full DR test**

```bash
# 1. Schedule maintenance window (2 hours)
# 2. Notify stakeholders
# 3. Start drill timer

# 4. Scenario: Complete data center failure
# Simulate by:
# - Stopping production database
# - Stopping production app
# - Using standby infrastructure

# 5. Execute recovery
# - Start from backup on secondary infrastructure
# - Run complete restore procedure
# - Verify all data restored
# - Run integration tests

# 6. Measure:
# - Time to restore database
# - Time to restore application
# - Time to pass health checks
# - Data loss (if any)

# 7. Document:
# - What worked
# - What broke
# - Issues encountered
# - Fixes needed

# 8. Improvement plan:
# - Update procedures based on findings
# - Invest in tooling/automation
# - Schedule next drill (3 months)

# Example drill timeline:
14:00 - Drill starts
14:05 - Production stopped
14:10 - Begin recovery procedures
14:15 - Database restore starts
14:30 - Database restore completes
14:35 - Application deployed
14:40 - Health checks pass
14:45 - Integration tests run
14:55 - Drill complete
15:00 - Post-incident review
```

---

## Section 4: Data Protection

### 4.1 Data Encryption

**In Transit:**
```bash
# All connections use TLS 1.3
# Certificates automatically rotated
# HSTS headers enforced

# Verify TLS:
openssl s_client -connect api.example.com:443
```

**At Rest:**
```bash
# Database files encrypted with:
# - dm-crypt (Linux)
# - BitLocker (Windows)
# - EBS encryption (AWS)

# Backups encrypted with AES-256-CBC
openssl enc -aes-256-cbc -in backup.sql -out backup.sql.enc
```

### 4.2 Data Retention

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Transaction Logs | 7 days | Quick recovery |
| Full Backups | 30 days | Compliance |
| Compliance Backups | 1 year | Legal holds |
| Audit Logs | 2 years | Security |
| Event Data | 1 year | Analytics |

### 4.3 PII Protection

```bash
# Automatic PII redaction in logs:
- Passwords: [REDACTED]
- API keys: [REDACTED]
- Tokens: [REDACTED]
- IP addresses: [REDACTED]
- Email addresses: [REDACTED]

# Backup encryption for PII safety
# Restore access restricted to DBA team
```

---

## Section 5: Communication Plan

### 5.1 Incident Declaration

**When to declare incident:**
- Service degradation > 5 minutes
- Data loss > 1 hour
- Security breach suspected

**Declaration process:**
```bash
# 1. Create incident ticket (auto or manual)
# 2. Notify incident commander
# 3. Open incident channel (Slack #incidents)
# 4. Post initial assessment

# Template:
# - Severity (P1/P2/P3)
# - Services affected
# - Estimated time to resolution
# - Temporary mitigation measures
# - Full recovery plan

# Example:
# P1: API service degraded
# - Root cause: Database connection pool exhausted
# - Mitigation: Restarted database
# - ETA recovery: 15 minutes
# - Full fix: Increase pool size in config
```

### 5.2 Stakeholder Notifications

**P1 (Critical):**
- Notify within 5 minutes
- Update every 5 minutes
- Channels: Email, SMS, Slack, PagerDuty

**P2 (Major):**
- Notify within 15 minutes
- Update every 15 minutes
- Channels: Email, Slack

**P3 (Minor):**
- Update end of day
- Channels: Email

### 5.3 Post-Incident Review

**Within 24 hours of resolution:**

```markdown
# Post-Incident Review Template

## Incident Details
- **ID**: INC-2026-0001
- **Severity**: P1
- **Duration**: 45 minutes
- **Impact**: 1,250 affected users

## Timeline
14:30 UTC - Alert triggered (error rate > 1%)
14:32 UTC - On-call engineer investigates
14:35 UTC - Root cause identified: DB connection exhaustion
14:40 UTC - Mitigation deployed: Increased pool size
14:45 UTC - Service recovered
14:50 UTC - Verified no data loss
15:15 UTC - Post-incident review begins

## Root Cause
- Heavy ML processing jobs not throttled
- Database connection pool size insufficient
- No proactive alerting on pool usage

## Immediate Actions (24 hours)
1. Increased connection pool size to 50
2. Added alerts for pool usage > 80%
3. Throttled ML processing during peak hours

## Follow-up Actions (1 week)
1. Implement auto-scaling for connection pool
2. Code review for all database access
3. Load test with 2x peak traffic

## Preventive Measures (ongoing)
1. Monthly capacity planning reviews
2. Quarterly load testing
3. Training on database best practices
```

---

## Section 6: Testing & Validation

### 6.1 Recovery Testing Checklist

**Monthly Validation:**

```bash
# Database Recovery
[ ] Backup file exists and is recent (< 24 hours)
[ ] Backup file can be opened: tar -tzf backup-*.tar.gz
[ ] Test restore to staging environment
[ ] Verify row counts match production
[ ] Run sample queries successfully
[ ] Performance is acceptable

# Application Recovery
[ ] Build application image from current code
[ ] Deploy to staging environment
[ ] All tests pass: pytest tests/ -v
[ ] Health checks return 200 OK
[ ] Can connect to database
[ ] API endpoints respond correctly

# Failover Testing
[ ] DNS failover works
[ ] Secondary region responds
[ ] Data is consistent between regions
[ ] No data loss during failover
[ ] Failback works correctly

# Security Validation
[ ] TLS certificates valid
[ ] No hardcoded secrets in deployment
[ ] API keys rotated recently
[ ] Database credentials encrypted
[ ] Audit logs contain proper entries
```

### 6.2 Disaster Recovery Drill Schedule

| Quarter | Focus | Duration | Participants |
|---------|-------|----------|--------------|
| Q1 | Database recovery | 2 hours | DBA, On-call |
| Q2 | Application recovery | 2 hours | DevOps, SRE |
| Q3 | Multi-region failover | 3 hours | Eng, Ops, Prod |
| Q4 | Full DR test | 4 hours | All teams |

---

## Section 7: Runbooks by Scenario

### 7.1 Quick Recovery Checklist

**Scenario: Application is down**

```bash
1. [ ] Check if service responds: curl http://localhost:5000/health
2. [ ] Check if running: docker ps | grep app
3. [ ] Restart if stopped: docker compose up -d app
4. [ ] Check logs for errors: docker logs app | tail -50
5. [ ] Check dependencies:
     [ ] Database: psql $DATABASE_URL -c "SELECT 1"
     [ ] Redis: redis-cli ping
     [ ] Network: docker network ls
6. [ ] Restart if needed: docker compose restart app
7. [ ] Monitor: docker logs -f app
8. [ ] If still down, escalate to Level 2
```

**Scenario: Data loss/corruption**

```bash
1. [ ] Stop application: docker compose stop app
2. [ ] Backup corrupted data: pg_dump ... > corrupted.sql
3. [ ] Identify restore point:
     [ ] Check backup timestamps: ls -lh /backups/
     [ ] Determine RPO: last backup time
     [ ] Calculate data loss: current time - backup time
4. [ ] Perform restore:
     [ ] Drop database: psql ... DROP DATABASE
     [ ] Restore backup: pg_restore ...
     [ ] Verify data: SELECT COUNT(*) FROM events
5. [ ] Resume application: docker compose up -d app
6. [ ] Monitor: docker logs -f app
7. [ ] Notify stakeholders of data loss
```

**Scenario: Security breach**

```bash
1. [ ] IMMEDIATELY stop application
2. [ ] Isolate compromised instance
3. [ ] Collect forensic data:
     [ ] Full disk image
     [ ] Process dumps
     [ ] Memory dump
     [ ] Logs (all logs)
4. [ ] Revoke all credentials
5. [ ] Restore from verified backup
6. [ ] Redeploy application from scratch
7. [ ] Change all secrets
8. [ ] Notify security team
9. [ ] Run full security audit
```

---

## Section 8: Contact Information

### 8.1 Escalation Matrix

**Level 1: On-Call SRE**
- Response time: < 5 minutes
- Authority: Start triage, basic troubleshooting

**Level 2: SRE Lead**
- Response time: < 15 minutes
- Authority: Full access, make decisions

**Level 3: Incident Commander**
- Response time: < 30 minutes
- Authority: Escalate, coordinate teams

**Level 4: CTO**
- Response time: < 1 hour
- Authority: Business decisions, customer communication

### 8.2 Contact Methods

```
On-Call SRE:
- Slack: #incidents
- PagerDuty: [INTEGRATION_ID]
- Phone: [PHONE_NUMBER]

Database Admin:
- Slack: @dba-team
- Email: dba@example.com

Security Lead:
- Slack: @security
- Email: security@example.com
```

---

## Appendix A: Recovery Time Goals

### RTO by Component

| Component | RTO | Method |
|-----------|-----|--------|
| Application | < 5 min | Container restart |
| Database | < 15 min | Backup restore |
| Cache | < 1 min | Auto-recovery |
| DNS | < 1 min | DNS failover |
| Full system | < 1 hour | Multi-region failover |

### RPO by Component

| Component | RPO | Backup Frequency |
|-----------|-----|------------------|
| Database | < 15 min | Hourly + replication |
| Transaction logs | < 1 min | Continuous |
| Application config | < 1 hour | Version control |
| Machine images | < 1 day | Automated |

---

## Appendix B: Templates

### B.1 Incident Log Template

```
Time: [TIMESTAMP]
Severity: [P1/P2/P3]
Component: [APP/DB/NETWORK/etc]
Status: [INVESTIGATING/MITIGATING/RESOLVED]
Summary: [1-line description]
Details: [What happened and why]
Actions: [What was done to fix]
Follow-up: [Next steps]
```

### B.2 Change Log (for recovery)

```
Date: 2026-06-16
Changed by: [NAME]
Change: [WHAT CHANGED]
Reason: [WHY]
Rollback: [HOW TO REVERT]
Risk: [LOW/MEDIUM/HIGH]
Tested: [YES/NO]
```

---

**Approved by:** Operations Lead, CTO  
**Last Tested:** 2026-06-16  
**Next Test:** 2026-09-16  

*This plan should be reviewed and updated quarterly. All staff must complete DR training annually.*
