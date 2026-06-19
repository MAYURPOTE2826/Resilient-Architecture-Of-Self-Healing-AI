# ⚡ QUICK DEPLOYMENT COMMANDS — Copy & Paste Ready

**Self-Healing Infrastructure Platform**  
**Ready to Deploy** ✅

---

## 🚀 FASTEST WAY TO DEPLOY (10 Minutes)

### On Linux/Mac:

```bash
# 1. Prerequisites check
docker --version
docker-compose --version
git --version

# 2. Clone and enter directory
git clone https://github.com/your-org/self-healing-engine.git
cd self-healing-engine

# 3. Setup environment
cp .env.example .env
# Edit .env with your secret keys:
# SECRET_KEY=<run: openssl rand -hex 32>
# JWT_SECRET=<run: openssl rand -hex 32>

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 5. Wait for startup
sleep 15

# 6. Check status
docker-compose ps

# 7. Verify health
curl http://localhost:5000/health | jq '.'

# DONE! Access at:
# App: http://localhost:5000
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## 🔑 GENERATE SECURE SECRETS (One-liner)

```bash
# Generate 64-character hex string
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📋 ENVIRONMENT FILE TEMPLATE

```bash
# Create .env file
cat > .env << 'EOF'
# Flask
FLASK_APP=src/api.py
FLASK_ENV=production
DEBUG=False

# Security (GENERATE NEW!)
SECRET_KEY=<paste-64-hex-here>
JWT_SECRET=<paste-64-hex-here>

# Database
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/self_healing

# Redis
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# App
APP_ENV=production
WORKERS=4
TIMEOUT=120
EOF
```

---

## ✅ HEALTH CHECK COMMANDS

```bash
# 1. Check if service alive
curl http://localhost:5000/live

# 2. Full health check
curl http://localhost:5000/health | jq '.'

# 3. Check readiness
curl http://localhost:5000/ready | jq '.'

# 4. Check specific dependency
curl http://localhost:5000/health | jq '.database'

# 5. Monitor real-time
watch -n 5 'curl -s http://localhost:5000/health | jq "."'
```

---

## 📊 LOGS & MONITORING

```bash
# Follow app logs
docker logs -f app

# Follow all services
docker-compose logs -f

# View specific service
docker-compose logs -f postgres

# Last 100 lines
docker logs app | tail -100

# Search for errors
docker logs app | grep -i error

# Show container stats
docker stats --no-stream
```

---

## 🔄 START/STOP/RESTART

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose restart app

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# View status
docker-compose ps

# Pull latest images
docker-compose pull

# Remove everything (careful!)
docker-compose -f docker-compose.prod.yml down -v
```

---

## 💾 DATABASE OPERATIONS

```bash
# Connect to database
docker exec -it postgres psql -U postgres self_healing

# Backup database
docker exec postgres pg_dump -U postgres self_healing > backup-$(date +%Y%m%d).sql

# Backup with compression
docker exec postgres pg_dump -U postgres self_healing | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore database
docker exec -i postgres psql -U postgres self_healing < backup-20260616.sql

# Check database size
docker exec postgres psql -U postgres self_healing -c "SELECT pg_size_pretty(pg_database_size('self_healing'));"

# List all tables
docker exec postgres psql -U postgres self_healing -c "\dt"

# Row count
docker exec postgres psql -U postgres self_healing -c "SELECT count(*) FROM events;"

# Vacuum and analyze
docker exec postgres psql -U postgres self_healing -c "VACUUM ANALYZE;"
```

---

## 🔐 SECURITY & SECRETS

```bash
# View current secrets
grep -E "SECRET_KEY|JWT_SECRET|PASSWORD" .env

# Rotate secrets (generate new ones)
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env.new
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env.new

# Export for use in commands
export SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET=$(openssl rand -hex 32)

# Verify no secrets in logs
docker logs app | grep -i "password\|secret\|token" || echo "✓ No secrets in logs"

# Check image for secrets
docker run --rm your-registry/app:latest grep -r "password" . || echo "✓ No hardcoded secrets"
```

---

## 🧪 API TESTING

```bash
# Test health endpoint
curl -X GET http://localhost:5000/health

# Test status endpoint
curl -X GET http://localhost:5000/api/status

# Test authentication
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Extract token and use it
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | jq -r '.token')

# Use token
curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN"

# Test file upload
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt"

# Test with verbose output
curl -v http://localhost:5000/health

# Test with timing
curl -w "\nTime: %{time_total}s\n" http://localhost:5000/health
```

---

## 📈 METRICS & MONITORING

```bash
# Get Prometheus metrics
curl http://localhost:9090/metrics

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=up'

# Get specific metric
curl 'http://localhost:9090/api/v1/query?query=http_requests_total'

# Query with time range
curl 'http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[5m])&start=1686000000&end=1686003600&step=60'

# List all metrics
curl 'http://localhost:9090/api/v1/label/__name__/values'

# Get Loki logs
curl -s 'http://localhost:3100/api/prom/query' -d 'query={job="app"}'

# Access Grafana API
curl -X GET http://localhost:3000/api/health
```

---

## 🐳 DOCKER COMMANDS

```bash
# Build image
docker build -f Dockerfile.prod -t app:v1 .

# Scan image for vulnerabilities
trivy image app:v1 --severity HIGH,CRITICAL

# Push to registry
docker tag app:v1 your-registry/app:v1
docker push your-registry/app:v1

# List images
docker images | grep app

# Remove old images
docker image prune -a --filter "until=72h"

# View image layers
docker history app:v1

# Inspect image
docker inspect app:v1

# Save image for backup
docker save app:v1 | gzip > app-v1.tar.gz

# Load image from backup
docker load < app-v1.tar.gz
```

---

## 🛠️ TROUBLESHOOTING COMMANDS

```bash
# Check port usage
lsof -i :5000

# Kill process using port
kill -9 <PID>

# Check disk space
df -h

# Check memory usage
free -h

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Container logs with timestamps
docker logs --timestamps app

# Resource usage
docker stats app --no-stream

# Network connectivity
docker exec app ping -c 5 postgres

# DNS resolution
docker exec app getent hosts postgres

# Environment variables
docker exec app env | grep -E "SECRET|DATABASE|CORS"

# File system inside container
docker exec app ls -la /app

# Check container IP
docker inspect app | grep IPAddress

# Restart in foreground (for debugging)
docker-compose run -it app bash
```

---

## 🚨 EMERGENCY COMMANDS

```bash
# Stop everything immediately
docker-compose down

# Kill and remove all containers
docker-compose -f docker-compose.prod.yml down -v

# Force restart
docker-compose -f docker-compose.prod.yml restart -t 0

# Access container shell
docker exec -it app bash

# Execute command in container
docker exec app python -c "print('Hello')"

# Copy file from container
docker cp app:/app/data.json ./data.json

# Copy file to container
docker cp ./backup.sql postgres:/backup.sql

# View resource limits
docker inspect app | grep -A 10 Resources

# Change memory limit (with restart)
docker update --memory 2g app && docker-compose restart app
```

---

## 📦 DEPLOYMENT CHECKLIST

```bash
# Run this before deploying

#!/bin/bash
echo "🔍 Pre-deployment checks..."

# 1. Check Docker
docker --version || exit 1
echo "✓ Docker installed"

# 2. Check Docker Compose
docker-compose --version || exit 1
echo "✓ Docker Compose installed"

# 3. Check .env
test -f .env || { echo "✗ .env file missing"; exit 1; }
echo "✓ .env exists"

# 4. Check secrets
grep "SECRET_KEY=" .env | grep -v "^#" || { echo "✗ SECRET_KEY not set"; exit 1; }
echo "✓ SECRET_KEY set"

grep "JWT_SECRET=" .env | grep -v "^#" || { echo "✗ JWT_SECRET not set"; exit 1; }
echo "✓ JWT_SECRET set"

# 5. Check ports available
! netstat -tuln 2>/dev/null | grep :5000 || { echo "✗ Port 5000 in use"; exit 1; }
echo "✓ Port 5000 available"

# 6. Check Docker images
docker-compose -f docker-compose.prod.yml config > /dev/null || exit 1
echo "✓ Docker Compose config valid"

echo ""
echo "✅ All pre-deployment checks passed!"
echo "Ready to run: docker-compose -f docker-compose.prod.yml up -d"
```

Save as `pre-deploy-check.sh` and run: `chmod +x pre-deploy-check.sh && ./pre-deploy-check.sh`

---

## 📝 COMPLETE DEPLOYMENT SCRIPT

```bash
#!/bin/bash
# Complete deployment script

set -e  # Exit on error

echo "🚀 Starting deployment..."

# 1. Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose not installed"; exit 1; }

# 2. Check configuration
echo "Checking configuration..."
test -f .env || { echo ".env file missing"; exit 1; }

# 3. Stop old containers
echo "Stopping old containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# 4. Pull latest images
echo "Pulling latest images..."
docker-compose pull

# 5. Build images
echo "Building images..."
docker-compose -f docker-compose.prod.yml build

# 6. Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# 7. Wait for startup
echo "Waiting for services to start..."
sleep 15

# 8. Verify deployment
echo "Verifying deployment..."
HEALTH=$(curl -s http://localhost:5000/health | jq '.status' | tr -d '"')
if [ "$HEALTH" = "healthy" ]; then
    echo "✅ Deployment successful!"
    echo "App: http://localhost:5000"
    echo "Grafana: http://localhost:3000"
    echo "Prometheus: http://localhost:9090"
else
    echo "❌ Deployment failed. Checking logs..."
    docker-compose logs
    exit 1
fi
```

Save as `deploy.sh` and run: `chmod +x deploy.sh && ./deploy.sh`

---

## 🔗 USEFUL LINKS

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| App | http://localhost:5000 | N/A (API) |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | N/A (no auth) |
| Loki | http://localhost:3100 | N/A (no auth) |
| Redis | localhost:6379 | none |
| PostgreSQL | localhost:5432 | postgres / (see .env) |

---

**Copy any command and run it! ✨**

For detailed explanations, see: **[DEPLOYMENT_INFRASTRUCTURE_GUIDE.md](DEPLOYMENT_INFRASTRUCTURE_GUIDE.md)**
