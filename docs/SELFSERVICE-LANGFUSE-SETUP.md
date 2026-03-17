# Self-Hosted Langfuse Setup Guide

## Overview

This guide covers the complete setup and configuration of self-hosted Langfuse for the GitOps Infra Control Plane. We use Langfuse for observability across our Temporal workflows, AI agents, and system components.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Backend API    │    │ Temporal Worker │
│  (localhost:3000)│───▶│ (localhost:8081)│───▶│  (Traced)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │  Self-Hosted   │
                                              │    Langfuse     │
                                              │ (localhost:3010)│
                                              └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │     Redis       │
                                              │     MinIO       │
                                              └─────────────────┘
```

## Quick Start

### 1. Deploy Self-Hosted Langfuse

```bash
# Deploy Langfuse with all dependencies
./core/automation/scripts/deploy-langfuse-selfhosted.sh
```

### 2. Access Langfuse Dashboard

```bash
# Port-forward Langfuse UI
kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse

# Open browser
open http://localhost:3010
```

### 3. Default Credentials

- **Email**: `admin@example.com`
- **Password**: `password`

⚠️ **Important**: Change credentials after first login!

## Complete Setup Process

### Prerequisites

- Kubernetes cluster (local or remote)
- kubectl configured
- Helm (optional, for advanced setups)

### Step 1: Deploy Langfuse Stack

The deployment script creates:
- **Langfuse Server**: Main application (port 3000)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache (port 6379)
- **MinIO**: Object storage (ports 9000, 9001)

```bash
# Run the deployment script
./core/automation/scripts/deploy-langfuse-selfhosted.sh

# Verify deployment
kubectl get pods -n langfuse
```

Expected output:
```
NAME                               READY   STATUS    RESTARTS   AGE
langfuse-server-xxxxxxxx-xxxx        1/1     Running   0          2m
postgres-xxxxxxxx-xxxx              1/1     Running   0          2m
redis-xxxxxxxx-xxxx                 1/1     Running   0          2m
minio-xxxxxxxx-xxxx                1/1     Running   0          2m
```

### Step 2: Configure API Keys

1. **Access Langfuse UI**:
   ```bash
   kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse
   # Open http://localhost:3010
   ```

2. **Create Account**:
   - Login with default credentials
   - Create your own account
   - Generate API keys in Settings > API Keys

3. **Update Kubernetes Secrets**:
   ```bash
   # Create/update secrets with your API keys
   kubectl create secret generic langfuse-secrets \
     --from-literal=public-key="pk-lf-your-public-key" \
     --from-literal=secret-key="sk-lf-your-secret-key" \
     --namespace=observability \
     --dry-run=client -o yaml | kubectl apply -f -
   ```

### Step 3: Configure Applications

Update your applications to use the self-hosted Langfuse endpoint:

```yaml
# Environment variables for all traced applications
env:
- name: LANGFUSE_PUBLIC_KEY
  valueFrom:
    secretKeyRef:
      name: langfuse-secrets
      key: public-key
- name: LANGFUSE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: langfuse-secrets
      key: secret-key
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/otel"
- name: OTEL_SERVICE_NAME
  value: "gitops-temporal-worker"
```

## Access Methods

### Option 1: Port Forward (Recommended for Development)

```bash
# Langfuse UI
kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse
# Open: http://localhost:3010

# MinIO Console (optional)
kubectl port-forward svc/minio 9001:9001 -n langfuse
# Open: http://localhost:9001
```

### Option 2: NodePort (For Cluster Access)

```bash
# Patch service for NodePort access
kubectl patch svc langfuse-server -n langfuse -p '{"spec":{"type":"NodePort","ports":[{"port":3000,"nodePort":30101}]}'

# Access via NodeIP:Port
kubectl get nodes -o wide
# Open: http://<NODE_IP>:30101
```

### Option 3: Ingress (For Production)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: langfuse-ingress
  namespace: langfuse
spec:
  rules:
  - host: langfuse.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: langfuse-server
            port:
              number: 3000
```

## Configuration Details

### Database Configuration

```yaml
# PostgreSQL (default)
DATABASE_URL: "postgresql://postgres:postgres@postgres:5432/langfuse"

# Redis (default)
REDIS_URL: "redis://redis:6379"

# MinIO S3 (default)
S3_ACCESS_KEY_ID: "minioadmin"
S3_SECRET_ACCESS_KEY: "minioadmin"
S3_ENDPOINT: "http://minio:9000"
S3_BUCKET_NAME: "langfuse"
```

### Security Configuration

```yaml
# Authentication
NEXTAUTH_SECRET: "your-secret-key-here"
NEXTAUTH_URL: "http://localhost:3010"

# Environment
ENVIRONMENT: "production"  # or "development"
```

## Tracing Configuration

### OpenTelemetry Setup

Your applications should be configured with:

```go
// Go example
endpoint := "http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/otel"
exporter, err := otlptracegrpc.New(ctx,
    otlptracegrpc.WithEndpoint(endpoint),
    otlptracegrpc.WithHeaders(map[string]string{
        "Authorization": "Bearer " + os.Getenv("LANGFUSE_SECRET_KEY"),
    }),
)
```

### Service Names

Use consistent service naming:
- `gitops-temporal-worker` - Temporal workers
- `ai-agents-backend` - Backend API
- `cost-optimizer` - Cost optimization agent
- `security-scanner` - Security scanning agent

## Viewing Traces

### Access Dashboard

```bash
# Start port forward
kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse &

# Open browser
open http://localhost:3010
```

### Navigate Traces

1. **Login** to Langfuse UI
2. **Go to Traces** tab
3. **Filter by service**:
   - `gitops-temporal-worker`
   - `ai-agents-backend`
4. **Time range**: Select appropriate range
5. **Trace details**: Click on any trace to see spans

### Expected Trace Structure

```
ExecuteWorkflow (API)
├── WorkflowName (e.g., CostOptimizationWorkflow)
    ├── Activity: CostAnalysis
    ├── Activity: ResourceOptimization
    └── Activity: GenerateRecommendations
```

## Troubleshooting

### Common Issues

#### 1. Langfuse UI Not Accessible

```bash
# Check pod status
kubectl get pods -n langfuse

# Check logs
kubectl logs -n langfuse deployment/langfuse-server

# Check service
kubectl get svc -n langfuse
```

#### 2. No Traces Appearing

```bash
# Check application logs
kubectl logs -n observability deployment/temporal-worker | grep -i "trace\|otel\|langfuse"

# Verify OTLP connectivity
curl -H "Authorization: Bearer $LANGFUSE_SECRET_KEY" \
     http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/health

# Check environment variables
kubectl exec -it deployment/temporal-worker -n observability -- env | grep LANGFUSE
```

#### 3. Database Issues

```bash
# Check PostgreSQL
kubectl logs -n langfuse deployment/postgres

# Connect to database
kubectl exec -it -n langfuse deployment/postgres -- psql -U postgres -d langfuse

# Check tables
\dt
```

### Reset Langfuse

```bash
# Delete and redeploy
kubectl delete namespace langfuse
./core/automation/scripts/deploy-langfuse-selfhosted.sh
```

## Monitoring Langfuse

### Health Checks

```bash
# Langfuse health
curl http://localhost:3010/api/health

# Database health
kubectl exec -n langfuse deployment/postgres -- pg_isready

# Redis health
kubectl exec -n langfuse deployment/redis -- redis-cli ping
```

### Resource Usage

```bash
# Monitor resources
kubectl top pods -n langfuse

# Check storage
kubectl get pv,pvc -n langfuse
```

## Production Considerations

### Persistence

For production, replace `emptyDir` with persistent volumes:

```yaml
volumes:
- name: postgres-storage
  persistentVolumeClaim:
    claimName: postgres-pvc
```

### Security

1. **Change default passwords**
2. **Use TLS certificates**
3. **Network policies**
4. **RBAC restrictions**

### Backup

```bash
# Backup database
kubectl exec -n langfuse deployment/postgres -- pg_dump -U postgres langfuse > backup.sql

# Backup MinIO
kubectl exec -n langfuse deployment/minio -- mc alias set local http://localhost:9000 minioadmin minioadmin
kubectl exec -n langfuse deployment/minio -- mc mirror local/langfuse ./backup
```

## Integration Points

### Temporal Worker Integration

Your Temporal workers are already configured with:
- Tracing interceptor
- OpenTelemetry exporter
- Proper span attributes

### Backend API Integration

The backend API includes:
- Workflow execution tracing
- Error tracking
- Performance metrics

### Agent Skills Integration

Individual agent skills can add custom tracing:

```go
tracer := otel.Tracer("skill-name")
ctx, span := tracer.Start(ctx, "skill-execution")
defer span.End()
```

## Next Steps

1. **Deploy Langfuse** using the script
2. **Create account** and generate API keys
3. **Update secrets** in your cluster
4. **Restart applications** to pick up new configuration
5. **Verify traces** appear in dashboard
6. **Set up monitoring** for Langfuse itself

## Support

- **Langfuse Documentation**: https://langfuse.com/docs
- **Troubleshooting**: Check logs and health endpoints
- **Issues**: Create GitHub issues in the repository

---

**Note**: This setup uses port 3010 for Langfuse to avoid conflicts with the frontend on port 3000.
