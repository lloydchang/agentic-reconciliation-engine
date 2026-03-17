# Complete Automated Langfuse Setup Process

## Overview

This document captures the complete end-to-end automated setup process for self-hosted Langfuse, including all steps, configurations, and verification procedures.

## 🚀 One-Command Complete Setup

### Primary Automation Script

```bash
# Run this single command for complete autonomous setup
./core/automation/scripts/langfuse-auto-setup-complete.sh
```

### What This Script Does Automatically

1. **Deploys Complete Stack**
   - PostgreSQL database
   - Redis cache
   - ClickHouse analytics (Langfuse v3 requirement)
   - MinIO object storage
   - Langfuse server

2. **Generates API Keys**
   - Creates cryptographically secure keys
   - No manual UI interaction required
   - Stores in Kubernetes secrets

3. **Configures Applications**
   - Sets up OTLP endpoints
   - Configures environment variables
   - Enables tracing for all components

4. **Sets Up Access**
   - Configures port-forwarding
   - Opens browser dashboard
   - Verifies connectivity

## 📋 Step-by-Step Process

### Step 1: Stack Deployment

The automation deploys these components automatically:

```yaml
# PostgreSQL
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: langfuse
spec:
  # ... database configuration
  env:
  - name: POSTGRES_DB
    value: "langfuse"
  - name: POSTGRES_USER
    value: "postgres"
  - name: POSTGRES_PASSWORD
    value: "postgres"

# Redis
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: langfuse
spec:
  # ... cache configuration

# ClickHouse (Critical for Langfuse v3)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clickhouse
  namespace: langfuse
spec:
  # ... analytics configuration
  env:
  - name: CLICKHOUSE_DB
    value: "langfuse"

# MinIO
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: langfuse
spec:
  # ... object storage configuration

# Langfuse Server
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langfuse-server
  namespace: langfuse
spec:
  # ... main application configuration
  env:
  - name: DATABASE_URL
    value: "postgresql://postgres:postgres@postgres:5432/langfuse"
  - name: REDIS_URL
    value: "redis://redis:6379"
  - name: CLICKHOUSE_URL
    value: "clickhouse://clickhouse:9000/langfuse"
```

### Step 2: Service Configuration

Fixed service configurations with proper port names:

```yaml
# ClickHouse Service (Fixed)
apiVersion: v1
kind: Service
metadata:
  name: clickhouse
  namespace: langfuse
spec:
  selector:
    app: clickhouse
  ports:
  - port: 9000
    targetPort: 9000
    name: clickhouse-http
  - port: 8123
    targetPort: 8123
    name: clickhouse-native
  type: ClusterIP

# Langfuse Service
apiVersion: v1
kind: Service
metadata:
  name: langfuse-server
  namespace: langfuse
spec:
  selector:
    app: langfuse
  ports:
  - port: 3000
    targetPort: 3000
  type: ClusterIP
```

### Step 3: API Key Generation

Automatic generation of secure credentials:

```bash
# Auto-generated keys (example)
PUBLIC_KEY="pk-lf-400fa063d6299b80450ff9d8d912a7db"
SECRET_KEY="sk-lf-eb7aeee5b802e359d236ce85ff547dfb47f4fa9f7a43b3377f7455e5e954207e"
PROJECT_ID="proj_d1ddb68df4c87727"
```

### Step 4: Kubernetes Secrets Creation

Automatic secret creation in `observability` namespace:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-secrets
  namespace: observability
data:
  public-key: cGstbGYtNDAwZmEwNjNkNjI5OWI4MDQ1MGZmOWQ4ZDkxMmE3ZGI=
  secret-key: c2stbGYtZWI3YWVlZTViODAyZTM1OWQyMzZjZTg1ZmY1NDdkZmI0N2Y0ZmE5ZjdhNDNiMzM3N2Y3NDU1ZTVlOTU0MjA3ZQ==
  project-id: cHJval9kMWRkYjY4ZGY0Yzg3NzI3
type: Opaque
```

### Step 5: Application Configuration

Automatic ConfigMap creation for self-hosted endpoints:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: langfuse-config
  namespace: observability
data:
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://langfuse-server.langfuse.svc.cluster.local:3000/api/public/otel"
  LANGFUSE_HOST: "http://langfuse-server.langfuse.svc.cluster.local:3000"
  OTEL_SERVICE_NAME: "gitops-temporal-worker"
  OTEL_TRACES_ENABLED: "true"
  OTEL_TRACES_SAMPLER: "traceidratio"
  OTEL_TRACES_SAMPLER_ARG: "0.1"
  ENVIRONMENT: "development"
```

### Step 6: Access Setup

Automatic port-forward and browser access:

```bash
# Port-forward automatically started
kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse &

# Browser automatically opened
open http://localhost:3010
```

## 🔍 Verification Process

### Health Checks

```bash
# Check all pods
kubectl get pods -n langfuse

# Expected output:
NAME                               READY   STATUS    RESTARTS   AGE
langfuse-server-xxxxxxxx-xxxx     1/1     Running   0          5m
postgres-xxxxxxxx-xxxx             1/1     Running   0          5m
redis-xxxxxxxx-xxxx                1/1     Running   0          5m
clickhouse-xxxxxxxx-xxxx           1/1     Running   0          5m
minio-xxxxxxxx-xxxx               1/1     Running   0          5m
```

### Secret Verification

```bash
# Verify secrets exist
kubectl get secret langfuse-secrets -n observability

# Decode and verify keys
kubectl get secret langfuse-secrets -n observability -o jsonpath='{.data.public-key}' | base64 -d
kubectl get secret langfuse-secrets -n observability -o jsonpath='{.data.secret-key}' | base64 -d
```

### ConfigMap Verification

```bash
# Verify configuration
kubectl get configmap langfuse-config -n observability -o yaml
```

### Dashboard Access

```bash
# Test dashboard accessibility
curl -s http://localhost:3010/api/health

# Expected output: {"status":"healthy"}
```

## 🛠️ Troubleshooting Common Issues

### Issue 1: ClickHouse Service Error

**Problem:** `The Service "clickhouse" is invalid: spec.ports[0].name: Required value`

**Solution:** Ensure proper port names in service definition:

```yaml
ports:
- port: 9000
  targetPort: 9000
  name: clickhouse-http  # Required!
- port: 8123
  targetPort: 8123
  name: clickhouse-native  # Required!
```

### Issue 2: Langfuse Pod Crashing

**Problem:** `ERROR: CLICKHOUSE_URL is not configured`

**Solution:** Ensure ClickHouse URL is properly set in Langfuse deployment:

```yaml
env:
- name: CLICKHOUSE_URL
  value: "clickhouse://clickhouse:9000/langfuse"
```

### Issue 3: Port Forward Not Working

**Problem:** Connection refused errors

**Solution:** Wait for pods to be ready, then restart port-forward:

```bash
# Wait for pods
kubectl wait --for=condition=ready pod -l app=langfuse -n langfuse --timeout=300s

# Kill existing port-forward
pkill -f "kubectl.*port-forward.*3010"

# Start new port-forward
kubectl port-forward svc/langfuse-server 3010:3000 -n langfuse &
```

## 📊 Monitoring and Maintenance

### Resource Monitoring

```bash
# Monitor resource usage
kubectl top pods -n langfuse

# Check storage
kubectl get pv,pvc -n langfuse
```

### Log Monitoring

```bash
# Langfuse logs
kubectl logs -n langfuse deployment/langfuse-server -f

# Database logs
kubectl logs -n langfuse deployment/postgres -f

# ClickHouse logs
kubectl logs -n langfuse deployment/clickhouse -f
```

### Backup Procedures

```bash
# Database backup
kubectl exec -n langfuse deployment/postgres -- pg_dump -U postgres langfuse > backup-$(date +%Y%m%d).sql

# MinIO backup
kubectl exec -n langfuse deployment/minio -- mc alias set local http://localhost:9000 minioadmin minioadmin
kubectl exec -n langfuse deployment/minio -- mc mirror local/langfuse ./backup-$(date +%Y%m%d)
```

## 🔄 Reset and Rebuild

### Complete Reset

```bash
# Delete everything
kubectl delete namespace langfuse
kubectl delete namespace observability

# Rebuild from scratch
./core/automation/scripts/langfuse-auto-setup-complete.sh
```

### Partial Reset

```bash
# Just restart Langfuse
kubectl rollout restart deployment/langfuse-server -n langfuse

# Regenerate keys
./core/automation/scripts/setup-langfuse-keys-automated.sh
```

## 🎯 Success Criteria

### Setup Complete When:

1. ✅ All 5 pods are running (langfuse-server, postgres, redis, clickhouse, minio)
2. ✅ Dashboard accessible at http://localhost:3010
3. ✅ API keys generated and stored in secrets
4. ✅ ConfigMap created with proper endpoints
5. ✅ Port-forward working
6. ✅ Health checks passing

### Tracing Working When:

1. ✅ Applications can connect to OTLP endpoint
2. ✅ Traces appear in Langfuse dashboard
3. ✅ Service names correctly identified
4. ✅ Span attributes properly set

## 📚 Additional Resources

### Related Documentation

- `docs/SELFSERVICE-LANGFUSE-SETUP.md` - User-facing setup guide
- `core/automation/scripts/langfuse-auto-setup-complete.sh` - Main automation script
- `core/automation/scripts/setup-langfuse-keys-automated.sh` - API key automation
- `core/automation/scripts/setup-langfuse-playwright.ts` - UI automation backup

### Integration Points

- Temporal workers automatically configured
- Backend API automatically traced
- Agent skills automatically monitored
- Dashboard automatically populated

---

**Result:** Complete autonomous Langfuse setup with zero manual intervention required.
