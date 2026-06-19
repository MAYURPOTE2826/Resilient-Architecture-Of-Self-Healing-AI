# 📋 DEPLOYMENT STEP-BY-STEP CHECKLIST

**Self-Healing Infrastructure Platform**  
**Print This Page & Check Off as You Go**  
**Estimated Time: 3-4 Hours**

---

## 📅 PHASE 1: PREPARATION (30 minutes)

### Step 1A: Install Docker

**On Ubuntu/Debian:**
```bash
[ ] sudo apt update && sudo apt upgrade -y
[ ] sudo apt install docker.io -y
[ ] sudo usermod -aG docker $USER
[ ] newgrp docker
[ ] docker --version
```

**On macOS:**
```bash
[ ] Download Docker Desktop from docker.com
[ ] Run installer
[ ] Launch Docker Desktop
[ ] docker --version
```

**On Windows:**
```bash
[ ] Download Docker Desktop for Windows
[ ] Run installer
[ ] Enable WSL 2
[ ] docker --version
```

### Step 1B: Install Docker Compose

**All Platforms:**
```bash
[ ] sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
[ ] sudo chmod +x /usr/local/bin/docker-compose
[ ] docker-compose --version
```

### Step 1C: Install Git

**Ubuntu/Debian:**
```bash
[ ] sudo apt install git -y
[ ] git --version
```

**macOS:**
```bash
[ ] brew install git
[ ] git --version
```

**Windows:**
```bash
[ ] Download from git-scm.com
[ ] Run installer
[ ] git --version
```

---

## 📥 PHASE 2: GET THE CODE (15 minutes)

### Step 2A: Clone Repository

```bash
[ ] git clone https://github.com/your-org/self-healing-engine.git
[ ] cd self-healing-engine
[ ] ls -la  # Verify files present
[ ] ls -la docker-compose.prod.yml
```

### Step 2B: Verify Project Structure

```bash
[ ] Check src/ folder exists
[ ] Check tests/ folder exists
[ ] Check docs/ folder exists
[ ] Check requirements.txt exists
[ ] Check Dockerfile.prod exists
[ ] Check docker-compose.prod.yml exists
```

---

## 🔧 PHASE 3: CONFIGURATION (15 minutes)

### Step 3A: Create Environment File

```bash
[ ] cp .env.example .env
[ ] ls -la .env
```

### Step 3B: Generate Secrets

```bash
# Generate SECRET_KEY
[ ] openssl rand -hex 32
    # Copy output to .env SECRET_KEY=<value>

# Generate JWT_SECRET
[ ] openssl rand -hex 32
    # Copy output to .env JWT_SECRET=<value>
```

### Step 3C: Edit .env File

```bash
[ ] nano .env  (or your preferred editor)

# Verify these are set:
[ ] FLASK_ENV=production
[ ] SECRET_KEY=<64-char hex>
[ ] JWT_SECRET=<64-char hex>
[ ] DATABASE_URL=postgresql://postgres:your_password@postgres:5432/self_healing
[ ] LOG_LEVEL=INFO
[ ] CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

[ ] Save file (Ctrl+O, Enter, Ctrl+X for nano)
```

### Step 3D: Verify Configuration

```bash
[ ] grep "SECRET_KEY=" .env | head -1
[ ] grep "JWT_SECRET=" .env | head -1
[ ] grep "DATABASE_URL=" .env | head -1
[ ] wc -l .env  # Should have 15+ lines
```

---

## 🔨 PHASE 4: BUILD (30 minutes)

### Step 4A: Build Docker Images

```bash
[ ] docker-compose -f docker-compose.prod.yml build
[ ] Wait for completion (5-10 minutes)
[ ] Check for "Successfully built" message
```

### Step 4B: Verify Image Creation

```bash
[ ] docker images | grep app
[ ] docker images | grep postgres
[ ] docker images | grep redis
[ ] docker images | grep prometheus
[ ] docker images | grep grafana
```

---

## 🚀 PHASE 5: DEPLOYMENT (30 minutes)

### Step 5A: Start Services

```bash
[ ] docker-compose -f docker-compose.prod.yml up -d
[ ] Wait 10-15 seconds for startup
```

### Step 5B: Verify Services Running

```bash
[ ] docker-compose ps
   # Verify ALL services show "Up"
   [ ] app
   [ ] postgres
   [ ] redis
   [ ] prometheus
   [ ] grafana
   [ ] loki
```

### Step 5C: Check Container Logs

```bash
[ ] docker logs app | head -20
    # Look for: "WARNING in app running on..."
    # Should NOT see: "ERROR" or "CRITICAL"

[ ] docker logs postgres | grep "ready to accept"
    # Should show: "PostgreSQL X.X is now accepting connections"

[ ] docker logs redis
    # Should show: "Ready to accept connections"
```

---

## ✅ PHASE 6: VERIFICATION (20 minutes)

### Step 6A: Health Checks

```bash
[ ] curl -s http://localhost:5000/health | jq '.'
    # Expected: status = "healthy"

[ ] curl -s http://localhost:5000/live | jq '.'
    # Expected: alive = true

[ ] curl -s http://localhost:5000/ready | jq '.'
    # Expected: ready = true

[ ] curl -s http://localhost:5000/startup | jq '.'
    # Expected: Contains configuration info
```

### Step 6B: API Testing

```bash
[ ] curl http://localhost:5000/api/status | jq '.'
    # Expected: JSON response

[ ] curl -X GET http://localhost:5000/api/admin/health -H "Accept: application/json"
    # Expected: 401 or 403 (no auth)
```

### Step 6C: Database Connectivity

```bash
[ ] docker exec -it postgres psql -U postgres self_healing -c "SELECT 1;"
    # Expected: "(1 row)"

[ ] docker exec -it postgres psql -U postgres self_healing -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
    # Expected: Shows table count
```

### Step 6D: Backup System

```bash
[ ] mkdir -p /backups
[ ] docker exec postgres pg_dump -U postgres self_healing | gzip > /backups/backup-$(date +%Y%m%d).sql.gz
[ ] ls -lh /backups/backup-*.sql.gz
    # Expected: File > 1MB
```

---

## 📊 PHASE 7: MONITORING SETUP (20 minutes)

### Step 7A: Access Grafana

```bash
[ ] open http://localhost:3000
    # Or: http://your-ip:3000

[ ] Login:
    [ ] Username: admin
    [ ] Password: admin

[ ] Change password:
    [ ] Click Profile → Change Password
    [ ] Save new password
```

### Step 7B: Configure Prometheus Data Source

```bash
[ ] Configuration → Data Sources
[ ] Add new data source
[ ] Select: Prometheus
[ ] URL: http://prometheus:9090
[ ] Click Save
```

### Step 7C: Configure Loki Data Source

```bash
[ ] Configuration → Data Sources
[ ] Add new data source
[ ] Select: Loki
[ ] URL: http://loki:3100
[ ] Click Save
```

### Step 7D: Add Dashboard

```bash
[ ] Click "+" → Import
[ ] Paste: 1860 (Node Exporter Full)
[ ] Select Prometheus data source
[ ] Click Import
```

### Step 7E: View Logs

```bash
[ ] Explore → Loki
[ ] Run query: {job="app"}
[ ] View recent logs
[ ] Verify entries from last 15 minutes
```

---

## 🔐 PHASE 8: SECURITY & USERS (20 minutes)

### Step 8A: Create Admin User

```bash
[ ] docker exec -it postgres psql -U postgres self_healing

# At psql prompt:
[ ] SELECT version();
    # Verify PostgreSQL is working

[ ] INSERT INTO users (username, email, password_hash, role) VALUES 
    ('admin', 'admin@example.com', 'bcrypt_hash_here', 'admin');
    # Note: Use proper bcrypt hash

[ ] SELECT count(*) FROM users;
    # Expected: 1 (one user)

[ ] \q  # Exit psql
```

### Step 8B: Test Login

```bash
[ ] curl -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"testpass"}'
    # Should return JWT token
```

### Step 8C: Create API Key

```bash
[ ] TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"testpass"}' | jq -r '.token')

[ ] curl -X POST http://localhost:5000/api/admin/api-keys \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"test-key"}'
    # Should return API key
```

---

## 🧪 PHASE 9: FUNCTIONALITY TESTS (15 minutes)

### Step 9A: Test Core Features

```bash
[ ] Test health endpoints
    [ ] /health → 200 OK
    [ ] /live → 200 OK
    [ ] /ready → 200 OK
    [ ] /startup → 200 OK

[ ] Test authentication
    [ ] POST /api/auth/login → Returns token
    [ ] GET /api/admin/users with token → Returns users
    [ ] GET /api/admin/users without token → 401

[ ] Test data endpoints
    [ ] POST /api/data → Stores data
    [ ] GET /api/data → Retrieves data
    [ ] PUT /api/data/{id} → Updates data
    [ ] DELETE /api/data/{id} → Deletes data
```

### Step 9B: Test Error Handling

```bash
[ ] Send invalid data
    [ ] POST /api/data with invalid JSON → 400
    [ ] GET /api/nonexistent → 404
    [ ] Verify error response doesn't leak internal details

[ ] Test rate limiting
    [ ] Send 100 requests in quick succession
    [ ] Should get some 429 responses
```

### Step 9C: Test Logging

```bash
[ ] Make a request
[ ] Check logs
    [ ] docker logs app | tail -10
    [ ] Verify JSON format
    [ ] Verify request is logged
    [ ] Verify no sensitive data
```

---

## 💾 PHASE 10: BACKUP & RECOVERY (15 minutes)

### Step 10A: Create Backup

```bash
[ ] mkdir -p /backups
[ ] docker exec postgres pg_dump -U postgres self_healing | gzip > /backups/backup-manual-$(date +%Y%m%d-%H%M%S).sql.gz
[ ] ls -lh /backups/
    # Verify file exists and is > 1MB
```

### Step 10B: Verify Backup Content

```bash
[ ] gunzip -c /backups/backup-manual-*.sql.gz | head -20
    # Should show SQL statements
```

### Step 10C: Test Restore (Optional)

```bash
[ ] docker exec postgres createdb test_restore
[ ] gunzip -c /backups/backup-manual-*.sql.gz | docker exec -i postgres psql -U postgres test_restore
[ ] docker exec postgres psql -U postgres test_restore -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"
    # Should show some tables
```

### Step 10D: Schedule Backup

```bash
[ ] crontab -e
[ ] Add: 0 * * * * /backups/backup.sh >> /backups/backup.log 2>&1
    # Backs up every hour
[ ] crontab -l
    # Verify entry added
```

---

## 📈 PHASE 11: MONITORING & ALERTS (15 minutes)

### Step 11A: Create Alert Rules

```bash
[ ] In Prometheus (http://localhost:9090):
    [ ] Alerts → Add Alert Rule
    [ ] High error rate: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    [ ] High latency: histogram_quantile(0.99, http_request_duration_seconds) > 0.5
    [ ] Service down: up{job="app"} == 0
```

### Step 11B: Setup Notifications

```bash
[ ] In Grafana (http://localhost:3000):
    [ ] Settings → Notification channels
    [ ] Add notification channel (email/webhook/slack)
    [ ] Test notification
    [ ] Create alert policy with notification
```

### Step 11C: Monitor Dashboard

```bash
[ ] View Grafana dashboards
[ ] Check all metrics are flowing
[ ] Verify graphs show data
[ ] Check for any warning icons
```

---

## 🎯 PHASE 12: FINAL VERIFICATION (10 minutes)

### Step 12A: System Status Check

```bash
All Services Running:
[ ] docker-compose ps → All "Up"

Health Checks Passing:
[ ] curl http://localhost:5000/health → "healthy"
[ ] All dependency checks green

Database:
[ ] Data persisting across requests
[ ] Backup created automatically
[ ] Can query data

Logging:
[ ] All requests logged
[ ] No errors in logs
[ ] JSON format verified

Monitoring:
[ ] Grafana dashboard visible
[ ] Prometheus collecting metrics
[ ] Loki aggregating logs

Security:
[ ] No hardcoded secrets in logs
[ ] Password hashed in database
[ ] API keys generated
[ ] CORS configured
```

### Step 12B: Documentation Check

```bash
[ ] Have DEPLOYMENT_GUIDE.md open
[ ] Have OPERATIONS_RUNBOOK.md saved
[ ] Have emergency contacts listed
[ ] Have runbook procedures printed (optional)
```

### Step 12C: Readiness Confirmation

```bash
✅ Infrastructure Ready
   [ ] Docker running
   [ ] All containers healthy
   [ ] Volumes mounted
   [ ] Networks configured

✅ Application Ready
   [ ] Code deployed
   [ ] Configuration loaded
   [ ] Tests passing
   [ ] Monitoring active

✅ Operations Ready
   [ ] Team trained
   [ ] Procedures documented
   [ ] Backup working
   [ ] Alerts configured

✅ Security Ready
   [ ] Authentication working
   [ ] Authorization enforced
   [ ] Secrets secured
   [ ] Audit logging enabled

✅ DEPLOYMENT COMPLETE ✅
```

---

## 📞 POST-DEPLOYMENT

### Immediate (30 minutes after deployment)

```bash
[ ] Monitor system closely
[ ] Watch for errors in logs
[ ] Monitor resource usage (docker stats)
[ ] Verify all health checks green
[ ] Confirm backup ran
```

### First Day (24 hours)

```bash
[ ] Monitor system continuously
[ ] Check for anomalies
[ ] Test all user workflows
[ ] Verify dashboard accuracy
[ ] Confirm alerts work correctly
```

### First Week

```bash
[ ] Run full test suite
[ ] Test disaster recovery
[ ] Review logs for issues
[ ] Optimize performance if needed
[ ] Document any issues
```

---

## 🆘 QUICK TROUBLESHOOTING

**Service won't start:**
```bash
[ ] docker-compose logs app
    # Read error message
[ ] Fix issue
[ ] docker-compose restart app
```

**Port already in use:**
```bash
[ ] lsof -i :5000
    # Find PID
[ ] kill -9 <PID>
    # Kill process
```

**Database connection error:**
```bash
[ ] docker-compose ps postgres
    # Check if running
[ ] docker logs postgres
    # Check postgres logs
[ ] docker-compose restart postgres
```

**Disk space issue:**
```bash
[ ] df -h
[ ] du -sh /backups/
[ ] docker system prune -a
    # Clean up old images
```

---

## 📊 SUCCESS CRITERIA

```
CHECKLIST ITEMS:  [ ] / [ ]

If ALL items checked ✅:
✅ DEPLOYMENT SUCCESSFUL
✅ SYSTEM PRODUCTION READY
✅ READY FOR TRAFFIC

If ANY item unchecked ❌:
❌ RESOLVE ISSUE
❌ RETRY STEP
❌ CONTACT SUPPORT (see OPERATIONS_RUNBOOK.md)
```

---

**Print this page and check off items as you go!**

**Time to completion: 3-4 hours**

**Questions?** → See [DEPLOYMENT_INFRASTRUCTURE_GUIDE.md](DEPLOYMENT_INFRASTRUCTURE_GUIDE.md)

**Stuck?** → See [docs/OPERATIONS_RUNBOOK.md](docs/OPERATIONS_RUNBOOK.md)

---

**Status: ✅ READY TO DEPLOY**

*Good luck! You've got this! 🚀*
