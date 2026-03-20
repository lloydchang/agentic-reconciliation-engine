# Portal - Deployment Guide

This guide covers all deployment options for the Portal, from local development to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Bare Metal/VM Deployment](#bare-metalvm-deployment)
5. [Production Considerations](#production-considerations)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Node.js**: v16+ (v18+ recommended)
- **Docker**: v20.10+ (for containerized deployment)
- **Kubernetes**: v1.24+ (for K8s deployment)
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: 10GB free space

### Dependencies

```bash
# Install Node.js dependencies
npm install axios express cors helmet compression

# For Docker deployments
docker --version
docker-compose --version

# For Kubernetes deployments
kubectl version --client
helm version
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
PORT=5001
DASHBOARD_PORT=8081
API_BASE_URL=http://localhost:5001/api

# External Service URLs (optional - defaults to mock data)
ARGOCD_URL=http://localhost:8080
LANGFUSE_URL=http://localhost:3000
PROMETHEUS_URL=http://localhost:9090
ELASTICSEARCH_URL=http://localhost:9200

# Authentication (for production)
ARGOCD_TOKEN=your-argocd-token
LANGFUSE_SECRET_KEY=your-langfuse-secret
LANGFUSE_PUBLIC_KEY=your-langfuse-public
ELASTICSEARCH_API_KEY=your-es-api-key
```

## Docker Compose Deployment

### Quick Start

```bash
# Clone the repository
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Start all services
docker-compose -f docker-compose-portal.yaml up -d

# Check status
docker-compose -f docker-compose-portal.yaml ps

# View logs
docker-compose -f docker-compose-portal.yaml logs -f ai-infrastructure-portal
```

### Services Included

- **ai-infrastructure-portal**: Main API and dashboard (ports 5001, 8081)
- **temporal**: Workflow orchestration (port 7233)
- **temporal-ui**: Web UI for Temporal (port 8080)
- **postgres**: Database for Temporal (port 5432)
- **redis**: Caching layer (port 6379)
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Metrics visualization (port 3000)

### Scaling

```bash
# Scale the API service
docker-compose -f docker-compose-portal.yaml up -d --scale ai-infrastructure-portal=3

# Update configuration
docker-compose -f docker-compose-portal.yaml up -d --no-deps ai-infrastructure-portal
```

### Backup and Restore

```bash
# Backup data volumes
docker run --rm -v agentic-portal_postgres:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore data volumes
docker run --rm -v agentic-portal_postgres:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/postgres-backup.tar.gz"
```

## Kubernetes Deployment

### Using Helm

```bash
# Add the repository
helm repo add agentic-portal https://charts.agentic-portal.io
helm repo update

# Install with default values
helm install ai-portal agentic-portal/agentic-portal

# Install with custom values
helm install ai-portal agentic-portal/agentic-portal -f values.yaml
```

### Manual Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace ai-infrastructure

# Deploy services
kubectl apply -f dashboard/overlay/dashboard-backend-k8s-real.yaml
kubectl apply -f dashboard/overlay/dashboard-backend-code.yaml

# Check deployment
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure

# View logs
kubectl logs -n ai-infrastructure deployment/ai-infrastructure-portal
```

### Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-portal-ingress
  namespace: ai-infrastructure
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: portal.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-infrastructure-portal
            port:
              number: 8081
  - host: api.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: ai-infrastructure-portal
            port:
              number: 5001
```

### High Availability Setup

```bash
# Deploy multiple replicas
kubectl scale deployment ai-infrastructure-portal --replicas=3 -n ai-infrastructure

# Configure horizontal pod autoscaling
kubectl autoscale deployment ai-infrastructure-portal --cpu-percent=70 --min=2 --max=10 -n ai-infrastructure
```

## Bare Metal/VM Deployment

### Manual Installation

```bash
# Install Node.js (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 for process management
sudo npm install -g pm2

# Clone and setup
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Install dependencies
npm install

# Configure environment
cp .env.template .env
# Edit .env with your settings

# Start services with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Systemd Service

Create `/etc/systemd/system/ai-portal.service`:

```ini
[Unit]
Description=Portal
After=network.target

[Service]
Type=simple
User=portal
WorkingDirectory=/opt/ai-portal
ExecStart=/usr/bin/node real-data-api.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-portal
sudo systemctl start ai-portal
sudo systemctl status ai-portal
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name portal.yourdomain.com;

    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:5001/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Production Considerations

### Security

```bash
# Generate SSL certificates
certbot --nginx -d portal.yourdomain.com -d api.yourdomain.com

# Configure firewall
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Secure environment variables
# Use Docker secrets or Kubernetes secrets for sensitive data
```

### Monitoring

```bash
# Install monitoring stack
docker-compose -f docker-compose-monitoring.yaml up -d

# Configure alerts
# Edit prometheus/alert_rules.yml
# Configure Grafana dashboards
```

### Backup Strategy

```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U temporal temporal > backup_$DATE.sql
gzip backup_$DATE.sql

# Schedule with cron
# 0 2 * * * /path/to/backup-script.sh
```

### Performance Tuning

```javascript
// In real-data-api.js, adjust settings:
const server = express();
server.set('trust proxy', 1);
server.use(compression());
server.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));
```

## Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Check what's using ports
sudo lsof -i :5001
sudo lsof -i :8081

# Kill process or change ports in .env
```

**Memory issues:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Or reduce cache sizes in application config
```

**Database connection failures:**
```bash
# Test database connectivity
docker exec -it postgres pg_isready -h localhost

# Check connection string in .env
# Verify database is running
```

**Service startup failures:**
```bash
# Check logs
docker-compose logs ai-infrastructure-portal

# Validate configuration
node -c real-data-api.js
node -c real-dashboard-server.js
```

### Health Checks

```bash
# API health check
curl http://localhost:5001/api/health

# Dashboard health check
curl http://localhost:8081/health

# Service connectivity test
curl http://localhost:5001/api/services
```

### Logs and Debugging

```bash
# Application logs
docker-compose logs -f ai-infrastructure-portal

# System logs
journalctl -u ai-portal -f

# Enable debug mode
export DEBUG=ai-portal:*
npm start
```

---

For additional support, check the [API Documentation](./API_REFERENCE.md) or create an issue on GitHub.
