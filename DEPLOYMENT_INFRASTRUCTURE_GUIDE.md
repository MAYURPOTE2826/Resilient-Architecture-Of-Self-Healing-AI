# 🚀 DEPLOYMENT INFRASTRUCTURE GUIDE — Step-by-Step

**Self-Healing Infrastructure Platform**  
**Date:** 2026-06-16  
**Status:** Ready for Deployment

---

## PART 1: WHAT YOU NEED (Infrastructure Requirements)

### Option A: Docker Compose (Recommended for Quick Start)
**Best For:** Development, testing, small production deployments (single server)

**What You Need:**
```
1. Server (Linux/Mac/Windows):
   - CPU: 4+ cores
   - RAM: 8+ GB
   - Disk: 50+ GB SSD
   - OS: Ubuntu 20.04+, CentOS 7+, or Docker Desktop on Mac/Windows

2. Docker:
   - Docker Engine 20.10+
   - Docker Compose 2.0+

3. Network:
   - Internet connectivity
   - Ports accessible: 5000 (app), 5432 (db), 6379 (redis), 
     9090 (prometheus), 3000 (grafana), 3100 (loki)

4. Optional:
   - SSL certificate (for HTTPS)
   - Domain name
```

### Option B: Kubernetes (Recommended for Production)
**Best For:** Production, high availability, multi-region scaling

**What You Need:**
```
1. Kubernetes Cluster:
   - 3+ worker nodes (minimum)
   - 8+ GB RAM per node
   - 50+ GB disk per node
   - Kubernetes 1.24+

2. Container Registry:
   - Docker Hub (free tier)
   - Docker Registry (self-hosted)
   - ECR (AWS)
   - GCR (Google Cloud)
   - ACR (Azure)

3. Ingress Controller:
   - NGINX Ingress
   - AWS Application Load Balancer
   - Azure Application Gateway

4. Storage:
   - PersistentVolume for databases
   - Database backup storage

5. Monitoring:
   - Prometheus (metrics)
   - Grafana (dashboards)
   - Loki (logs)
```

### Option C: Cloud Platforms (Easiest for Beginners)
**Best For:** Managed services, minimal infrastructure management

**Choice 1: AWS (Amazon Web Services)**
```
Required:
- EC2 instances (app servers)
- RDS (managed PostgreSQL)
- ElastiCache (managed Redis)
- Application Load Balancer (ALB)
- CloudWatch (monitoring)
- S3 (backups)
Cost: $500-1000/month
```

**Choice 2: Google Cloud Platform (GCP)**
```
Required:
- Cloud Run (container hosting)
- Cloud SQL (managed PostgreSQL)
- Cloud Memorystore (managed Redis)
- Cloud Load Balancing
- Cloud Monitoring
- Cloud Storage (backups)
Cost: $400-800/month
```

**Choice 3: Microsoft Azure**
```
Required:
- App Service (app hosting)
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Application Gateway (load balancer)
- Azure Monitor (monitoring)
- Blob Storage (backups)
Cost: $600-1200/month
```

**Choice 4: DigitalOcean (Budget-Friendly)**
```
Required:
- Droplets (virtual machines)
- Managed Database (PostgreSQL)
- Managed Redis
- Load Balancer
- Spaces (object storage/backups)
Cost: $100-300/month
```

---

## PART 2: DEPLOYMENT OPTION COMPARISON

| Feature | Docker Compose | Kubernetes | AWS | GCP | Azure | DigitalOcean |
|---------|---|---|---|---|---|---|
| **Setup Time** | 30 min | 2 hours | 1 hour | 1 hour | 1 hour | 45 min |
| **Cost/Month** | $50-100 | $100-300 | $500-1000 | $400-800 | $600-1200 | $100-300 |
| **Scalability** | Manual | Automatic | Automatic | Automatic | Automatic | Manual |
| **HA/Redundancy** | Single server | Multi-node | Built-in | Built-in | Built-in | Needs setup |
| **Ease of Use** | Very Easy | Medium | Hard | Medium | Hard | Easy |
| **Best For** | Dev/Test | Production | Enterprise | Enterprise | Enterprise | Startup |

---

## PART 3: STEP-BY-STEP DEPLOYMENT (Docker Compose)

### Recommended: Start with Docker Compose for Testing

#### Step 1: Prepare Your Server (30 minutes)

**On Linux (Ubuntu 20.04+):**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
sudo apt install docker.io -y
sudo usermod -aG docker $USER
newgrp docker

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Verify installation
docker --version
docker-compose --version
```

**On macOS:**

```bash
# 1. Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# 2. Launch Docker Desktop from Applications

# 3. Verify
docker --version
docker-compose --version
```

**On Windows:**

```bash
# 1. Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# 2. Run installer and complete setup

# 3. Enable WSL 2 (Windows Subsystem for Linux 2)
# Settings → Resources → WSL Integration → Enable

# 4. Restart and verify
docker --version
docker-compose --version
```

---

#### Step 2: Get the Application Code (15 minutes)

```bash
# Option A: Clone from Git
git clone https://github.com/your-org/self-healing-engine.git
cd self-healing-engine

# Option B: Download as ZIP
# Download from GitHub → Code → Download ZIP
# Extract: unzip self-healing-engine-main.zip
# Navigate: cd self-healing-engine-main
```

---

#### Step 3: Configure Environment Variables (15 minutes)

```bash
# 1. Navigate to project root
cd /path/to/self-healing-engine

# 2. Create .env file
cp .env.example .env

# 3. Edit .env with your values
nano .env  # or use your preferred editor

# Required variables to configure:
```

**.env File Content (Example):**

```bash
# Flask Configuration
FLASK_APP=src/api.py
FLASK_ENV=production
DEBUG=False

# Security (GENERATE NEW SECRETS!)
SECRET_KEY=<generate-64-char-hex-string>
JWT_SECRET=<generate-64-char-hex-string>

# Database
DATABASE_URL=postgresql://postgres:your_secure_password@postgres:5432/self_healing

# Redis
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO

# CORS (change example.com to your domain)
CORS_ORIGINS=http://localhost:3000,http://example.com,https://example.com

# Application
APP_ENV=production
WORKERS=4
TIMEOUT=120
```

**To Generate Secure Secrets:**

```bash
# Linux/Mac:
openssl rand -hex 32

# Python:
python -c "import secrets; print(secrets.token_hex(32))"

# Windows PowerShell:
[Convert]::ToHexString((1..32 | ForEach-Object { Get-Random -Max 256 }))
```

---

#### Step 4: Build and Start Services (30 minutes)

```bash
# 1. Build Docker image
docker-compose -f docker-compose.prod.yml build

# Expected output:
# Building app... [==>] 
# Successfully built 7a8b9c0d1e2f

# 2. Start all services
docker-compose -f docker-compose.prod.yml up -d

# Expected output:
# Creating postgres ... done
# Creating redis ... done
# Creating app ... done
# Creating prometheus ... done
# Creating grafana ... done
# Creating loki ... done

# 3. Wait for services to start
sleep 10

# 4. Check status
docker-compose ps

# Expected: All services should be "Up"
```

---

#### Step 5: Verify Deployment (15 minutes)

```bash
# 1. Check health endpoint
curl -s http://localhost:5000/health | jq '.'

# Expected output:
# {
#   "status": "healthy",
#   "timestamp": "2026-06-16T13:45:00Z",
#   "database": "connected",
#   "memory": "45%",
#   "disk": "62%"
# }

# 2. Check API is responding
curl -s http://localhost:5000/api/status | jq '.'

# 3. Check logs
docker logs app

# Expected: No ERROR messages

# 4. Access Grafana dashboard
open http://localhost:3000
# Username: admin
# Password: admin (change after first login)

# 5. Access Prometheus metrics
open http://localhost:9090

# 6. View logs in Grafana Loki
open http://localhost:3100
```

---

#### Step 6: Configure Initial Secrets & Users (20 minutes)

```bash
# 1. Access application container
docker exec -it app bash

# 2. Generate initial admin user
python -c "
from src.security_utils import PasswordManager
password = 'ChangeMe@1234567890'
hashed = PasswordManager.hash_password(password)
print(f'Admin password hash: {hashed}')
"

# 3. Create admin user in database
docker exec -it postgres psql -U postgres self_healing << EOF
INSERT INTO users (id, username, email, password_hash, role) VALUES
('admin-001', 'admin', 'admin@example.com', '<hashed_password>', 'admin');
EOF

# 4. Generate API keys for integrations
curl -X POST http://localhost:5000/api/admin/api-keys \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "monitoring-key", "description": "For Grafana integration"}'

# 5. Verify database populated
docker exec -it postgres psql -U postgres self_healing << EOF
SELECT * FROM users;
SELECT * FROM api_keys;
EOF
```

---

#### Step 7: Test Critical Flows (20 minutes)

```bash
# 1. Test Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "ChangeMe@1234567890"
  }' | jq '.token'

# Expected: JWT token returned

# 2. Test API with token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "ChangeMe@1234567890"
  }' | jq -r '.token')

curl -X GET http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Test anomaly detection
curl -X POST http://localhost:5000/api/anomalies/detect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "cpu_usage",
    "values": [10, 12, 11, 9, 85, 88]
  }' | jq '.'

# 4. Test backup
docker exec postgres pg_dump -U postgres self_healing > backup-test-$(date +%Y%m%d).sql

# 5. Verify backup
ls -lh backup-test-*.sql

# Expected: File should exist and be > 1MB
```

---

#### Step 8: Configure Monitoring Alerts (20 minutes)

```bash
# 1. Access Prometheus
open http://localhost:9090

# 2. Go to Alerts section
# Alerts → Add New Alert

# Configure alerts:
# - High error rate: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
# - High latency: histogram_quantile(0.99, http_request_duration_seconds) > 0.5
# - Database down: up{job="postgres"} == 0
# - Memory usage: container_memory_usage_bytes / 1024 / 1024 / 1024 > 6
# - Disk usage: 100 - (node_filesystem_free_bytes / node_filesystem_size_bytes * 100) > 85

# 2. Configure Grafana notifications
open http://localhost:3000
# Settings → Notification channels → New Channel
# Type: Webhook / Email / Slack
# Configure your preferred alert destination
```

---

#### Step 9: Set Up Automated Backup (15 minutes)

```bash
# 1. Create backup directory
mkdir -p /backups
chmod 755 /backups

# 2. Create backup script
cat > /backups/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup-$TIMESTAMP.sql.gz"

# Backup database
docker exec postgres pg_dump -U postgres self_healing | gzip > $BACKUP_FILE

# Keep only last 30 backups
cd $BACKUP_DIR
ls -t backup-*.sql.gz | tail -n +31 | xargs rm -f

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "✅ Backup successful: $BACKUP_FILE"
else
    echo "❌ Backup failed"
    exit 1
fi
EOF

# 3. Make script executable
chmod +x /backups/backup.sh

# 4. Schedule backup with cron (every hour)
crontab -e
# Add this line:
# 0 * * * * /backups/backup.sh >> /backups/backup.log 2>&1

# 5. Verify cron job
crontab -l

# 6. Test backup manually
/backups/backup.sh
ls -lh /backups/backup-*.sql.gz
```

---

#### Step 10: Production Hardening (15 minutes)

```bash
# 1. Change default passwords
docker exec postgres psql -U postgres << EOF
ALTER USER postgres WITH PASSWORD 'new_secure_password';
EOF

# Update in .env:
# DATABASE_URL=postgresql://postgres:new_secure_password@postgres:5432/self_healing

# 2. Enable TLS (HTTPS)
# Obtain SSL certificate (e.g., Let's Encrypt)
# Copy certificates to: /path/to/certs/

# 3. Configure reverse proxy (NGINX)
cat > /etc/nginx/sites-available/default << 'EOF'
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
EOF

# Restart NGINX
sudo systemctl restart nginx

# 4. Enable firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 5. Set up log rotation
cat > /etc/logrotate.d/app << 'EOF'
/var/log/app/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
}
EOF
```

---

## PART 4: DEPLOYMENT FOR PRODUCTION (Kubernetes)

### If You Need High Availability & Scalability

#### Step 1: Prepare Kubernetes Cluster

```bash
# Option A: Use managed Kubernetes
# - AWS EKS
# - Google GKE
# - Azure AKS
# - DigitalOcean Kubernetes

# Option B: Self-hosted (advanced)
# - kubeadm
# - kops
# - Kubespray

# For this guide, assume you have a cluster running

# Verify kubectl access
kubectl cluster-info
kubectl get nodes
```

#### Step 2: Create Kubernetes Manifests

```bash
# Create deployment directory
mkdir -p k8s/
cd k8s/

# Create namespace
cat > namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: production
EOF

# Create ConfigMap for environment variables
cat > configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  FLASK_ENV: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  CORS_ORIGINS: "https://example.com"
EOF

# Create Secret for sensitive data
cat > secret.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  SECRET_KEY: "<your-secret-key-here>"
  JWT_SECRET: "<your-jwt-secret-here>"
  DATABASE_URL: "postgresql://postgres:password@postgres:5432/self_healing"
  REDIS_URL: "redis://redis:6379/0"
EOF

# Create app deployment
cat > deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
      - name: app
        image: your-registry/app:v1.0.0
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
EOF

# Create service
cat > service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: app
  namespace: production
spec:
  selector:
    app: app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
EOF

# Create ingress
cat > ingress.yaml << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: production
spec:
  ingressClassName: nginx
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app
            port:
              number: 80
  tls:
  - hosts:
    - example.com
    secretName: tls-secret
EOF
```

#### Step 3: Deploy to Kubernetes

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Create secrets
kubectl apply -f secret.yaml

# 3. Create configmap
kubectl apply -f configmap.yaml

# 4. Deploy application
kubectl apply -f deployment.yaml

# 5. Create service
kubectl apply -f service.yaml

# 6. Create ingress
kubectl apply -f ingress.yaml

# 7. Verify deployment
kubectl get pods -n production
kubectl get svc -n production
kubectl get ingress -n production

# 8. Check pod logs
kubectl logs -n production -l app=app -f

# 9. Get LoadBalancer IP
kubectl get svc app -n production
# Copy the EXTERNAL-IP address
```

---

## PART 5: CLOUD DEPLOYMENT (AWS Example)

### Deploy to AWS (Most Popular)

#### Step 1: Create AWS Account & Set Up CLI

```bash
# 1. Create AWS account: https://aws.amazon.com

# 2. Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 3. Configure credentials
aws configure
# Enter: AWS Access Key, Secret Access Key, Region (e.g., us-east-1), Output (json)

# 4. Verify
aws sts get-caller-identity
```

#### Step 2: Create Database (RDS)

```bash
# 1. Create PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier self-healing-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --storage-type gp2 \
  --publicly-accessible false \
  --no-multi-az \
  --region us-east-1

# 2. Get database endpoint
aws rds describe-db-instances \
  --db-instance-identifier self-healing-db \
  --query 'DBInstances[0].Endpoint'
```

#### Step 3: Deploy to EC2

```bash
# 1. Create key pair
aws ec2 create-key-pair --key-name app-key --region us-east-1 > app-key.pem
chmod 400 app-key.pem

# 2. Create security group
aws ec2 create-security-group \
  --group-name app-sg \
  --description "Security group for app" \
  --region us-east-1

# 3. Open ports
aws ec2 authorize-security-group-ingress \
  --group-name app-sg \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name app-sg \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name app-sg \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# 4. Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t3.medium \
  --key-name app-key \
  --security-groups app-sg \
  --region us-east-1

# 5. Get public IP
aws ec2 describe-instances \
  --filters "Name=key-name,Values=app-key" \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# 6. Connect to instance
ssh -i app-key.pem ec2-user@<public-ip>

# 7. Install Docker (on instance)
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# 8. Deploy app (on instance)
git clone https://github.com/your-org/self-healing-engine.git
cd self-healing-engine
nano .env  # Configure with RDS endpoint
docker-compose -f docker-compose.prod.yml up -d
```

---

## PART 6: POST-DEPLOYMENT VERIFICATION

### Final Verification Checklist

```bash
# 1. Health Check
echo "✓ Health endpoint:"
curl -s http://localhost:5000/health | jq '.status'

# 2. Database Connected
echo "✓ Database:"
curl -s http://localhost:5000/health | jq '.database'

# 3. Logs Flowing
echo "✓ Application logs:"
docker logs app | tail -5

# 4. Metrics Exporting
echo "✓ Prometheus metrics:"
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result | length'

# 5. Dashboards Visible
echo "✓ Grafana dashboard:"
curl -s http://localhost:3000/api/health | jq '.database'

# 6. No Errors
echo "✓ Error logs:"
docker logs app | grep -i error || echo "No errors found ✓"

# 7. Backup Running
echo "✓ Backup file:"
ls -lh /backups/backup-*.sql.gz | tail -1

# 8. API Responding
echo "✓ API endpoint:"
curl -s http://localhost:5000/api/status | jq '.'
```

---

## PART 7: TROUBLESHOOTING

### Common Issues & Solutions

#### Issue 1: Ports Already in Use

```bash
# Problem: docker-compose fails with "port 5000 already in use"

# Solution:
# Find what's using the port
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use different port - edit docker-compose.prod.yml:
# ports:
#   - "8000:5000"
```

#### Issue 2: Database Connection Failed

```bash
# Problem: App can't connect to database

# Solution:
# Check database is running
docker-compose ps postgres

# Check database is responsive
docker exec postgres psql -U postgres -c "SELECT 1"

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Verify credentials match
```

#### Issue 3: High Memory Usage

```bash
# Problem: Container using too much memory

# Solution:
# Check current usage
docker stats app

# Limit memory in docker-compose.prod.yml:
# services:
#   app:
#     mem_limit: 1g

# Restart container
docker-compose restart app
```

#### Issue 4: Services Won't Start

```bash
# Problem: docker-compose up fails

# Solution:
# Check all required variables in .env
docker-compose config

# Check logs for errors
docker-compose logs app

# Rebuild image
docker-compose build --no-cache

# Start with verbose output
docker-compose up --verbose
```

---

## PART 8: MAINTENANCE & MONITORING

### Daily Tasks

```bash
# 1. Check system health
curl http://localhost:5000/health | jq '.'

# 2. View error logs
docker logs app | grep -i error

# 3. Check backup completed
ls -lh /backups/backup-*.sql.gz | head -1

# 4. Monitor resource usage
docker stats --no-stream

# 5. Review alerts in Grafana
open http://localhost:3000
```

### Weekly Tasks

```bash
# 1. Test backup restore (to staging)
pg_restore /backups/backup-latest.sql -d test_self_healing

# 2. Run security scan
docker run --rm -v $(pwd):/src aquasec/trivy image your-registry/app:latest

# 3. Review logs for anomalies
docker logs app | tail -100 | grep -i warn

# 4. Check disk space
df -h /
du -sh /backups/

# 5. Update dependencies
docker-compose pull
docker-compose build --no-cache
```

---

## SUMMARY

### Deployment Timeline

| Step | Duration | Task |
|------|----------|------|
| 1 | 30 min | Install Docker & Docker Compose |
| 2 | 15 min | Get application code |
| 3 | 15 min | Configure .env file |
| 4 | 30 min | Build and start services |
| 5 | 15 min | Verify deployment |
| 6 | 20 min | Create initial users |
| 7 | 20 min | Test critical flows |
| 8 | 20 min | Configure monitoring alerts |
| 9 | 15 min | Set up automated backups |
| 10 | 15 min | Production hardening |
| **Total** | **3-4 hours** | **Production Ready** |

---

### Quick Start (TL;DR)

```bash
# 1. Install Docker
# (See Part 3, Step 1)

# 2. Clone repo
git clone https://github.com/your-org/self-healing-engine.git

# 3. Configure
cp .env.example .env
nano .env  # Update secrets

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
curl http://localhost:5000/health | jq '.status'

# Done! Access:
# App: http://localhost:5000
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

---

**Ready to deploy?** Start with **Step 1** above! 🚀

For detailed guides:
- **Docker Compose:** See Part 3
- **Kubernetes:** See Part 4
- **AWS:** See Part 5
- **Troubleshooting:** See Part 7
