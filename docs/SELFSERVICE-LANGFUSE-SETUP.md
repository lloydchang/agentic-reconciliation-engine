# Fully Autonomous Self-Hosted Langfuse Setup

## Overview

This guide covers the **completely automated, autonomous setup** of self-hosted Langfuse for the GitOps Infra Control Plane. **No manual configuration required** - everything including API key generation, secret creation, and application configuration is fully automated.

🚀 **Key Features:**
- ✅ **Zero Manual Setup** - Everything automated
- ✅ **Auto-Generated API Keys** - No manual key creation
- ✅ **Automatic Kubernetes Secrets** - Pre-configured
- ✅ **Self-Hosted Only** - No cloud dependencies
- ✅ **Complete Observability Stack** - Ready to use

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
                                              │   ClickHouse    │
                                              │     MinIO       │
                                              └─────────────────┘
```

## 🚀 One-Command Fully Automated Setup

### Complete Autonomous Deployment

**Run this single command for everything:**

```bash
# Fully automated setup - no manual steps required
./core/automation/scripts/langfuse-auto-setup-complete.sh
```

**This single command automatically:**
- ✅ Deploys complete Langfuse stack (PostgreSQL, Redis, ClickHouse, MinIO, Langfuse)
- ✅ Generates secure API keys automatically
- ✅ Creates Kubernetes secrets with generated keys
- ✅ Configures all applications for self-hosted Langfuse
- ✅ Sets up port-forward for dashboard access
- ✅ Verifies end-to-end connectivity

**No manual intervention required - completely autonomous!**

## 🤖 What Gets Automated

### Fully Autonomous Components

**🔐 API Key Generation (Automatic)**
- Generates cryptographically secure API keys
- Creates unique project ID
- No manual UI interaction required
- Keys stored securely in Kubernetes secrets

**🚀 Complete Stack Deployment (Automatic)**
- PostgreSQL database with automatic schema
- Redis cache for session management
- ClickHouse for analytics (Langfuse v3 requirement)
- MinIO object storage for traces
- Langfuse server with all dependencies

**⚙️ Kubernetes Configuration (Automatic)**
- Creates `observability` namespace
- Generates `langfuse-secrets` secret with API keys
- Creates `langfuse-config` ConfigMap with endpoints
- Configures all environment variables

**🔗 Application Integration (Automatic)**
- Sets up OTLP endpoint for self-hosted Langfuse
- Configures service names and sampling
- Enables tracing for all components
- No code changes required

### Generated Credentials (Auto-Created)

The automation generates these automatically:

```bash
# Example auto-generated keys (different each run)
Public Key:  pk-lf-400fa063d6299b80450ff9d8d912a7db
Secret Key:  sk-lf-eb7aeee5b802e359d236ce85ff547dfb47f4fa9f7a43b3377f7455e5e954207e
Project ID:  proj_d1ddb68df4c87727
```

**These are automatically stored in:**
```bash
kubectl get secret langfuse-secrets -n observability
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
