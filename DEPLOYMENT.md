# Deployment Guide

Guide for deploying the distributed search engine to production.

## Prerequisites

- Cloud hosting account (AWS, Google Cloud, Azure, etc.)
- Docker registry (Docker Hub, AWS ECR, etc.)
- Kubernetes cluster (optional, for advanced scaling)
- Domain name and SSL certificate

## Quick Docker Deployment

### Deploy to a Single Server

```bash
# 1. Install Docker and Docker Compose on server
ssh user@server.com

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 2. Clone repository
git clone <repo-url>
cd search-engine

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with production settings

# 4. Build and run
docker-compose up -d

# 5. Enable auto-restart
docker-compose up -d --restart=always
```

## Deployment to AWS EC2

### 1. Create EC2 Instance

```bash
# Create t3.medium instance (2 vCPU, 4GB RAM minimum)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key \
  --security-groups web \
  --region us-east-1
```

### 2. Configure Instance

```bash
# Connect to instance
ssh -i your-key.pem ec2-user@your-instance

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and start
git clone <repo-url>
cd search-engine
docker-compose up -d
```

### 3. Setup Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo yum install -y nginx

# Create config
sudo tee /etc/nginx/conf.d/search-engine.conf > /dev/null <<EOF
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    location / {
        # Next.js frontend
        proxy_pass http://localhost:3000;
    }
}
EOF

sudo systemctl start nginx
```

## Kubernetes Deployment

### Create Deployment Files

**backend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-engine-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: search-engine-backend
  template:
    metadata:
      labels:
        app: search-engine-backend
    spec:
      containers:
      - name: backend
        image: your-registry/search-engine-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: ELASTICSEARCH_URL
          value: "http://elasticsearch-service:9200"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: search-engine-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to Kubernetes

```bash
# Build and push image
docker build -t your-registry/search-engine-backend:latest backend/
docker push your-registry/search-engine-backend:latest

# Apply manifests
kubectl apply -f backend-deployment.yaml
kubectl apply -f redis-statefulset.yaml
kubectl apply -f elasticsearch-statefulset.yaml

# Check status
kubectl get pods
kubectl get svc
```

## Elasticsearch in Production

### Configure for Production

```yaml
# docker-compose.yml changes for Elasticsearch
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.type=multi-node  # For cluster mode
    - "ES_JAVA_OPTS=-Xms2g -Xmx2g"  # Increase heap
    - xpack.security.enabled=true
    - ELASTIC_PASSWORD=your-secure-password
  volumes:
    - elasticsearch_data:/usr/share/elasticsearch/data
  ulimits:
    memlock:
      soft: -1
      hard: -1
```

### Backup Elasticsearch

```bash
# Create snapshot repository
curl -X PUT "localhost:9200/_snapshot/my_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/mnt/backups/my_backup"
  }
}'

# Take snapshot
curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_1"

# Restore from snapshot
curl -X POST "localhost:9200/_snapshot/my_backup/snapshot_1/_restore"
```

## Redis in Production

### Configure Persistence

```bash
# docker-compose.yml Redis settings
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --appendfsync everysec
  volumes:
    - redis_data:/data  # Persistent volume
```

### Monitor Memory

```bash
# Check Redis memory usage
redis-cli INFO memory

# Set max memory policy
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## SSL/TLS Configuration

### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Update Nginx config
sudo tee /etc/nginx/conf.d/search-engine.conf > /dev/null <<EOF
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Location configs...
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
EOF

sudo systemctl reload nginx

# Auto-renew
sudo systemctl enable certbot.timer
```

## Monitoring and Logging

### Setup Logging

```bash
# Docker logging with json-file driver
docker run --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 ...

# View logs
docker logs -f container-name

# Setup centralized logging (ELK Stack)
docker-compose up -d filebeat elasticsearch kibana
```

### Setup Monitoring

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['localhost:9200']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
```

### Health Checks

```bash
# Add health check to docker-compose
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

## Performance Tuning

### Elasticsearch Optimization

```bash
# Adjust refresh interval for better indexing performance
curl -X PUT "localhost:9200/web_pages/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s"
  }
}'
```

### Redis Optimization

```bash
# Tune Redis config
redis-cli CONFIG SET timeout 300
redis-cli CONFIG SET tcp-backlog 511
```

### API Optimization

```python
# Add caching to FastAPI
from fastapi_cache2 import FastAPICache2
from fastapi_cache2.backends.redis import RedisBackend
from redis import asyncio as aioredis

redis = await aioredis.from_url("redis://localhost")
FastAPICache2.init(RedisBackend(redis), prefix="search-cache")

@app.get("/search", response_cache_times_in_seconds=300)
async def search(...):
    ...
```

## Scaling Strategy

### Horizontal Scaling

```bash
# Scale backend service
docker-compose scale backend=5

# Or in Kubernetes
kubectl scale deployment search-engine-backend --replicas=5
```

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 10000 -c 100 http://localhost:8000/
```

## Backup Strategy

### Daily Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/search-engine"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup Elasticsearch
curl -X POST "localhost:9200/_snapshot/backups/snapshot_$DATE"

# Backup Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3
aws s3 sync $BACKUP_DIR s3://my-backup-bucket/
```

### Schedule with cron

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

## Disaster Recovery

### Restore from Backup

```bash
# 1. Restore Elasticsearch
curl -X POST "localhost:9200/_snapshot/backups/snapshot_20240315_020000/_restore"

# 2. Restore Redis
redis-cli SHUTDOWN
cp /backups/redis_20240315_020000.rdb /var/lib/redis/dump.rdb
redis-server

# 3. Verify data
curl localhost:9200/_cat/indices
redis-cli DBSIZE
```

## Security Checklist

- [ ] Enable authentication on Elasticsearch
- [ ] Enable password on Redis
- [ ] Setup SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Use security groups/network policies
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Rate limiting on APIs
- [ ] CORS configuration
- [ ] Input validation/sanitization

## Cost Estimation (AWS)

- EC2 t3.medium: ~$30/month
- Elasticsearch: ~$0.50/hour = ~$360/month
- Data transfer: ~$0.12/GB
- S3 backups: ~$0.023/GB/month

**Total estimated: $400-500/month for production setup**

## Support and Resources

- Docker Compose docs: https://docs.docker.com/compose/
- Elasticsearch docs: https://www.elastic.co/guide/en/elasticsearch/reference/
- FastAPI docs: https://fastapi.tiangolo.com/
- Kubernetes docs: https://kubernetes.io/docs/
