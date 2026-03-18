# Agent Dashboard Deployment Guide

## Overview

This guide documents the complete deployment process for the AI Agent Dashboard, including troubleshooting steps, fixes applied, and best practices for deploying the dashboard in a Kubernetes GitOps environment.

## Prerequisites

- Kubernetes cluster (Kind/Docker Desktop for local development)
- kubectl configured and connected to cluster
- Docker installed and running
- Go 1.24+ (for building the dashboard)
- Node.js 18+ (for frontend build)
- Access to the gitops-infra-control-plane repository

## Architecture

The AI Agent Dashboard consists of:
- **Backend**: Go-based API server with Temporal integration
- **Frontend**: React-based web interface with voice chat capabilities
- **Database**: PostgreSQL for persistent storage
- **Deployment**: Kubernetes with GitOps manifests

## Deployment Process

### 1. Initial Deployment Attempt

```bash
# Apply the dashboard deployment
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/dashboard-deployment.yaml
```

### 2. Common Issues and Fixes

#### Issue 1: YAML Parsing Error
**Error**: `error converting YAML to JSON: yaml: line 9: could not find expected ':'`

**Solution**: Use kustomize to build and apply resources:
```bash
kustomize build core/ai/runtime/dashboard/deployment/kubernetes | kubectl apply -f -
```

#### Issue 2: ErrImagePull - Missing Docker Image
**Error**: `Failed to pull image "ai-agents/dashboard:latest"`

**Root Cause**: The Docker image didn't exist and needed to be built from source.

**Solution**: Build the dashboard image:
```bash
cd core/ai/runtime/dashboard
docker build -t ai-agents/dashboard:latest .
```

#### Issue 3: Go Version Mismatch
**Error**: `go: go.mod requires go >= 1.24.0 (running go 1.21.13)`

**Solution**: Update Dockerfile Go version:
```dockerfile
FROM golang:1.24-alpine AS backend-builder
```

#### Issue 4: npm Package Lock Sync Error
**Error**: `npm ci can only install packages when your package.json and package-lock.json are in sync`

**Solution**: Replace `npm ci` with `npm install` in Dockerfile:
```dockerfile
RUN npm install --only=production
```

#### Issue 5: TypeScript Compilation Errors
**Error**: `TS2304: Cannot find name 'SpeechRecognition'`

**Solution**: Add proper type declarations for Web Speech API:
```typescript
// Type declaration for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: any) => void) | null;
  onerror: ((event: any) => void) | null;
  onend: ((event: any) => void) | null;
}
```

#### Issue 6: Image Pull Policy for Local Clusters
**Error**: Pods trying to pull from Docker Hub instead of using local image

**Solution**: Add `imagePullPolicy: Never` to deployment:
```yaml
containers:
- name: dashboard
  image: ai-agents/dashboard:latest
  imagePullPolicy: Never
```

#### Issue 7: Missing Secrets
**Error**: `Error: secret "db-secret" not found` and `Error: secret "argocd-secret" not found`

**Solution**: Create required secrets:
```bash
# Database secret
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"

# ArgoCD secret
kubectl create secret generic argocd-secret -n ai-infrastructure \
  --from-literal=password="admin"
```

#### Issue 8: Database Connection and Migration
**Error**: `pq: password authentication failed` and `pq: type "datetime" does not exist`

**Solution**: 
1. Use correct PostgreSQL credentials (postgres/postgres)
2. Create separate database for dashboard:
```bash
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -c "CREATE DATABASE dashboard;"
```

### 3. Complete Deployment Commands

```bash
# 1. Build the dashboard image
cd core/ai/runtime/dashboard
docker build -t ai-agents/dashboard:latest .

# 2. Load image into Kind cluster (if using Kind)
kind load docker-image ai-agents/dashboard:latest --name gitops-hub

# 3. Create required secrets
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"
kubectl create secret generic argocd-secret -n ai-infrastructure \
  --from-literal=password="admin"

# 4. Apply deployment
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/dashboard-deployment.yaml

# 5. Check pod status
kubectl get pods -n ai-infrastructure -l app=ai-agents-dashboard
```

## Configuration

### Environment Variables

The dashboard uses the following environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `TEMPORAL_ADDRESS` | Temporal server address | `temporal-frontend.ai-infrastructure.svc.cluster.local:7233` |
| `MEMORY_AGENT_URL` | Memory agent service URL | `http://agent-memory-service:8080` |
| `RAG_ENABLED` | Enable RAG features | `true` |
| `RAG_MODEL` | RAG model provider | `ollama` |
| `RAG_EMBEDDING_MODEL` | Embedding model | `nomic-embed-text` |
| `RAG_CHAT_MODEL` | Chat model | `llama3.1:8b` |
| `ARGOCD_ENABLED` | Enable ArgoCD integration | `true` |
| `ARGOCD_URL` | ArgoCD server URL | `http://argocd-server.argocd.svc.cluster.local:8080` |
| `ARGOCD_USERNAME` | ArgoCD username | `admin` |
| `VOICE_ENABLED` | Enable voice chat | `true` |
| `SPEECH_TO_TEXT_PROVIDER` | STT provider | `browser` |
| `TEXT_TO_SPEECH_PROVIDER` | TTS provider | `browser` |

### Services

The dashboard exposes the following services:

| Service | Port | Description |
|---------|------|-------------|
| `ai-agents-dashboard` | 8081 | Main dashboard API and UI |

## Accessing the Dashboard

### Port Forwarding

```bash
# Forward dashboard port to localhost
nohup kubectl port-forward -n ai-infrastructure svc/ai-agents-dashboard 8081:8081 &

# Access at http://localhost:8081
```

### Ingress (Optional)

Configure ingress to expose the dashboard externally:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-agents-dashboard-ingress
  namespace: ai-infrastructure
spec:
  rules:
  - host: dashboard.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-agents-dashboard
            port:
              number: 8081
```

## Troubleshooting

### Pod Status Issues

| Status | Cause | Solution |
|--------|-------|----------|
| `ErrImagePull` | Image not found | Build and load image into cluster |
| `ImagePullBackOff` | Wrong registry/policy | Use `imagePullPolicy: Never` for local images |
| `CrashLoopBackOff` | Application error | Check logs for database/connection issues |
| `CreateContainerConfigError` | Missing secrets | Create required secrets |

### Common Log Errors

#### Database Connection Failed
```
FATAL Failed to connect to database {"error": "failed to ping database: dial tcp: lookup postgres on 10.96.0.10:53: no such host"}
```
**Solution**: Update DATABASE_URL with correct service name and namespace.

#### Migration Failed
```
FATAL Failed to run migrations {"error": "migration failed: pq: type \"datetime\" does not exist"}
```
**Solution**: Create separate database and check migration compatibility.

### Health Checks

The dashboard includes health checks:
- **Liveness Probe**: `/health` after 30s initial delay
- **Readiness Probe**: `/health` after 5s initial delay

## Development

### Local Development

```bash
# Backend development
cd core/ai/runtime/dashboard
go run ./cmd/server

# Frontend development
cd core/ai/runtime/dashboard/frontend
npm start
```

### Building

```bash
# Build Docker image
docker build -t ai-agents/dashboard:latest .

# Build with custom tag
docker build -t ai-agents/dashboard:v1.0.0 .
```

### Testing

```bash
# Run backend tests
cd core/ai/runtime/dashboard
go test ./...

# Run frontend tests
cd core/ai/runtime/dashboard/frontend
npm test
```

## Security Considerations

1. **Secrets Management**: Use Kubernetes secrets for sensitive data
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Implement proper role-based access control
4. **TLS**: Enable TLS for external communications
5. **Image Security**: Use signed images and vulnerability scanning

## Monitoring and Observability

### Metrics

The dashboard exposes Prometheus metrics at `/metrics`:
- HTTP request metrics
- Database connection metrics
- Temporal workflow metrics
- Custom business metrics

### Logging

Structured JSON logging with correlation IDs:
- Request/response logging
- Error tracking
- Performance metrics
- Audit trails

### Alerts

Configure alerts for:
- High error rates
- Database connection failures
- Pod restarts
- Resource exhaustion

## GitOps Integration

### Flux/ArgoCD

The deployment is GitOps-ready:
- Manifests stored in version control
- Automated synchronization
- Rollback capabilities
- Progressive delivery support

### Deployment Pipeline

```yaml
# Example ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ai-agents-dashboard
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/gitops-infra-control-plane
    targetRevision: main
    path: core/ai/runtime/dashboard/deployment/kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: ai-infrastructure
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Backup and Recovery

### Database Backup

```bash
# Backup dashboard database
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- \
  pg_dump -U postgres dashboard > dashboard-backup.sql

# Restore database
kubectl exec -i -n langfuse postgres-6dd595ffbb-6h4lb -- \
  psql -U postgres dashboard < dashboard-backup.sql
```

### Configuration Backup

```bash
# Export secrets and config
kubectl get secret db-secret -n ai-infrastructure -o yaml > db-secret.yaml
kubectl get deployment ai-agents-dashboard -n ai-infrastructure -o yaml > deployment.yaml
```

## Performance Tuning

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Database Optimization

- Connection pooling
- Query optimization
- Index tuning
- Regular maintenance

## Scaling

### Horizontal Scaling

```yaml
# Increase replicas
spec:
  replicas: 5
```

### Vertical Scaling

```yaml
# Increase resource limits
resources:
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-03-18 | Initial deployment with fixes for TypeScript, image building, and database connectivity |

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## Support

For issues and questions:
1. Check this documentation
2. Review pod logs
3. Check GitHub issues
4. Contact the maintainers

---

**Last Updated**: 2026-03-18
**Version**: 1.0.0
**Maintainer**: AI Infrastructure Team
