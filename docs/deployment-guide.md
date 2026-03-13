# AI Agents Sandbox Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Go 1.19+
- Node.js 16+
- Docker (optional for containerized deployment)
- AWS CLI (for Bedrock integration)
- Temporal Cloud or local Temporal server

### Local Development Setup

#### 1. Clone and Setup
```bash
git clone https://github.com/lloydchang/ai-agents-sandbox.git
cd ai-agents-sandbox
```

#### 2. Backend Setup
```bash
cd backend
go mod tidy
go run verification_server.go
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### 4. Access Services
- Backend API: http://localhost:8081
- Frontend: http://localhost:3000
- WebSocket: ws://localhost:8081/ws
- Health Check: http://localhost:8081/health

## 🐳 Docker Deployment

### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8081:8081"
    environment:
      - TEMPORAL_HOST=temporal:7233
      - AWS_REGION=us-west-2
    depends_on:
      - temporal
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  temporal:
    image: temporalio/auto-setup:latest
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - DB_USER=temporal
      - DB_PASSWORD=temporal
    depends_on:
      - postgres

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
      - POSTGRES_DB=temporal
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Deploy with Docker
```bash
docker-compose up -d
```

## ☁️ Cloud Deployment

### AWS ECS Deployment

#### 1. Build and Push Images
```bash
# Backend
docker build -t ai-agents-backend ./backend
docker tag ai-agents-backend:latest your-account.dkr.ecr.region.amazonaws.com/ai-agents-backend:latest
docker push your-account.dkr.ecr.region.amazonaws.com/ai-agents-backend:latest

# Frontend  
docker build -t ai-agents-frontend ./frontend
docker tag ai-agents-frontend:latest your-account.dkr.ecr.region.amazonaws.com/ai-agents-frontend:latest
docker push your-account.dkr.ecr.region.amazonaws.com/ai-agents-frontend:latest
```

#### 2. ECS Task Definition
```json
{
  "family": "ai-agents-sandbox",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ai-agents-backend:latest",
      "portMappings": [
        {
          "containerPort": 8081,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "TEMPORAL_HOST",
          "value": "temporal.namespace.id.tmprl.cloud:7233"
        },
        {
          "name": "AWS_REGION", 
          "value": "us-west-2"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-agents-sandbox",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Kubernetes Deployment

#### 1. Namespace and ConfigMaps
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-agents-sandbox

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-agents-config
  namespace: ai-agents-sandbox
data:
  TEMPORAL_HOST: "temporal.namespace.id.tmprl.cloud:7233"
  AWS_REGION: "us-west-2"
  LOG_LEVEL: "info"
```

#### 2. Backend Deployment
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agents-backend
  namespace: ai-agents-sandbox
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agents-backend
  template:
    metadata:
      labels:
        app: ai-agents-backend
    spec:
      containers:
      - name: backend
        image: your-account.dkr.ecr.region.amazonaws.com/ai-agents-backend:latest
        ports:
        - containerPort: 8081
        envFrom:
        - configMapRef:
            name: ai-agents-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ai-agents-backend-service
  namespace: ai-agents-sandbox
spec:
  selector:
    app: ai-agents-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8081
  type: LoadBalancer
```

#### 3. Frontend Deployment
```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agents-frontend
  namespace: ai-agents-sandbox
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-agents-frontend
  template:
    metadata:
      labels:
        app: ai-agents-frontend
    spec:
      containers:
      - name: frontend
        image: your-account.dkr.ecr.region.amazonaws.com/ai-agents-frontend:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: ai-agents-frontend-service
  namespace: ai-agents-sandbox
spec:
  selector:
    app: ai-agents-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
```

#### 4. Ingress Configuration
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-ingress
  namespace: ai-agents-sandbox
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - ai-agents.yourdomain.com
    secretName: ai-agents-tls
  rules:
  - host: ai-agents.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: ai-agents-backend-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-agents-frontend-service
            port:
              number: 80
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend Configuration
TEMPORAL_HOST=temporal.namespace.id.tmprl.cloud:7233
TEMPORAL_NAMESPACE=default
AWS_REGION=us-west-2
LOG_LEVEL=info
PORT=8081

# Frontend Configuration  
REACT_APP_API_BASE_URL=http://localhost:8081
REACT_APP_WS_URL=ws://localhost:8081/ws
```

### AWS Configuration
```bash
# Configure AWS credentials for Bedrock
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter us-west-2 as default region

# Verify Bedrock access
aws bedrock list-foundation-models --region us-west-2
```

### Temporal Configuration
```bash
# For Temporal Cloud
export TEMPORAL_HOST="temporal.namespace.id.tmprl.cloud:7233"
export TEMPORAL_NAMESPACE="default"

# For local Temporal
docker run --rm -it \
  -p 7233:7233 \
  -p 8233:8233 \
  temporalio/auto-setup:latest
```

## 🔍 Monitoring & Observability

### Prometheus Metrics
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-agents-backend'
    static_configs:
      - targets: ['backend:8081']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'temporal'
    static_configs:
      - targets: ['temporal:9090']
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "AI Agents Sandbox",
    "panels": [
      {
        "title": "Workflow Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(workflow_executions_total[5m])",
            "legendFormat": "{{workflow_type}}"
          }
        ]
      },
      {
        "title": "Active WebSocket Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "websocket_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "AI Model Request Latency",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ai_model_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation
```yaml
# logging/fluentd.yml
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match ai-agents.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name ai-agents
  type_name _doc
</match>
```

## 🔒 Security Configuration

### Authentication
```go
// middleware/auth.go
func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        
        // Validate JWT token
        claims, err := validateToken(token)
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }
        
        // Add user context to request
        ctx := context.WithValue(r.Context(), "user", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### Rate Limiting
```go
// middleware/ratelimit.go
func rateLimitMiddleware() func(http.Handler) http.Handler {
    limiter := rate.NewLimiter(rate.Limit(100), 200)
    
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if !limiter.Allow() {
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}
```

### Network Policies (Kubernetes)
```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-agents-network-policy
  namespace: ai-agents-sandbox
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

## 🚀 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy AI Agents Sandbox

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-go@v3
      with:
        go-version: '1.19'
    - uses: actions/setup-node@v3
      with:
        node-version: '16'
    
    - name: Run backend tests
      run: |
        cd backend
        go test ./...
    
    - name: Run frontend tests
      run: |
        cd frontend
        npm test

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Build and push Docker images
      run: |
        # Build backend
        docker build -t ai-agents-backend ./backend
        docker tag ai-agents-backend:latest ${{ secrets.ECR_REGISTRY }}/ai-agents-backend:latest
        docker push ${{ secrets.ECR_REGISTRY }}/ai-agents-backend:latest
        
        # Build frontend
        docker build -t ai-agents-frontend ./frontend  
        docker tag ai-agents-frontend:latest ${{ secrets.ECR_REGISTRY }}/ai-agents-frontend:latest
        docker push ${{ secrets.ECR_REGISTRY }}/ai-agents-frontend:latest
    
    - name: Deploy to Kubernetes
      run: |
        aws eks update-kubeconfig --name ${{ secrets.EKS_CLUSTER_NAME }}
        kubectl apply -f k8s/
```

## 📊 Performance Tuning

### Backend Optimization
```go
// config/performance.go
func setupPerformanceConfig() {
    // Database connection pool
    db.SetMaxOpenConns(100)
    db.SetMaxIdleConns(10)
    db.SetConnMaxLifetime(time.Hour)
    
    // HTTP server timeouts
    server := &http.Server{
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }
    
    // Enable GZIP compression
    handler := gziphandler.GzipHandler(mux.NewRouter())
}
```

### Frontend Optimization
```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
  plugins: [
    new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 8192,
      minRatio: 0.8,
    }),
  ],
};
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Temporal Connection Issues
```bash
# Check Temporal status
curl http://localhost:8233/api/v1/namespaces/default

# Verify network connectivity
telnet temporal.namespace.id.tmprl.cloud 7233
```

#### 2. AWS Bedrock Access Issues
```bash
# Check Bedrock model access
aws bedrock get-foundation-model --model-id anthropic.claude-3-sonnet-20240229-v1:0 --region us-west-2

# Verify IAM permissions
aws iam get-user
```

#### 3. WebSocket Connection Issues
```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:8081/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

#### 4. Memory Issues
```bash
# Monitor memory usage
docker stats

# Increase memory limits
docker run --memory="2g" ai-agents-backend
```

### Health Checks
```bash
# Backend health
curl http://localhost:8081/health

# Frontend health
curl http://localhost:3000

# WebSocket health
wscat -c ws://localhost:8081/ws
```

## 📚 Additional Resources

### Documentation
- [API Reference](./api-reference.md)
- [Workflow Guide](./workflow-guide.md)
- [Troubleshooting Guide](./troubleshooting.md)

### Support
- GitHub Issues: [Create Issue](https://github.com/lloydchang/ai-agents-sandbox/issues)
- Community Forum: [Discussions](https://github.com/lloydchang/ai-agents-sandbox/discussions)
- Email Support: support@ai-agents-sandbox.com

### Training
- [Getting Started Tutorial](./tutorials/getting-started.md)
- [Advanced Configuration](./tutorials/advanced-config.md)
- [Best Practices Guide](./tutorials/best-practices.md)

---

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup strategy in place

### Deployment
- [ ] Infrastructure provisioned
- [ ] Secrets configured
- [ ] Services deployed
- [ ] Health checks passing
- [ ] Monitoring configured

### Post-Deployment
- [ ] Smoke tests executed
- [ ] Load testing performed
- [ ] Monitoring alerts configured
- [ ] Rollback plan tested
- [ ] Team training completed

---

**Ready for production deployment! 🚀**
