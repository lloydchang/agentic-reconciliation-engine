# Dashboard Troubleshooting Guide

## Quick Reference

This guide provides quick solutions for common dashboard deployment issues.

## Error Solutions

### 1. YAML Parsing Error
**Problem**: `error converting YAML to JSON: yaml: line 9: could not find expected ':'`

**Solution**:
```bash
kustomize build core/ai/runtime/dashboard/deployment/kubernetes | kubectl apply -f -
```

### 2. Image Pull Error
**Problem**: `Failed to pull image "ai-agents/dashboard:latest"`

**Solution**:
```bash
# Build image
cd core/ai/runtime/dashboard
docker build -t ai-agents/dashboard:latest .

# Load into Kind cluster
kind load docker-image ai-agents/dashboard:latest --name gitops-hub

# Update deployment with imagePullPolicy: Never
```

### 3. Go Version Mismatch
**Problem**: `go: go.mod requires go >= 1.24.0 (running go 1.21.13)`

**Solution**: Update Dockerfile:
```dockerfile
FROM golang:1.24-alpine AS backend-builder
```

### 4. npm Package Lock Error
**Problem**: `npm ci can only install packages when your package.json and package-lock.json are in sync`

**Solution**: Replace in Dockerfile:
```dockerfile
RUN npm install --only=production
```

### 5. TypeScript SpeechRecognition Error
**Problem**: `TS2304: Cannot find name 'SpeechRecognition'`

**Solution**: Add type declarations to VoiceChat.tsx:
```typescript
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}
```

### 6. Database Connection Error
**Problem**: `dial tcp: lookup postgres on 10.96.0.10:53: no such host`

**Solution**: Update DATABASE_URL secret:
```bash
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"
```

### 7. Database Migration Error
**Problem**: `pq: type "datetime" does not exist`

**Solution**: Create separate database:
```bash
kubectl exec -n langfuse postgres-6dd595ffbb-6h4lb -- psql -U postgres -c "CREATE DATABASE dashboard;"
```

### 8. Missing Secrets
**Problem**: `Error: secret "db-secret" not found` or `Error: secret "argocd-secret" not found`

**Solution**:
```bash
# Create both secrets
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"
kubectl create secret generic argocd-secret -n ai-infrastructure \
  --from-literal=password="admin"
```

## Diagnostic Commands

### Check Pod Status
```bash
kubectl get pods -n ai-infrastructure -l app=ai-agents-dashboard
```

### Check Pod Logs
```bash
kubectl logs -n ai-infrastructure -l app=ai-agents-dashboard
```

### Check Events
```bash
kubectl describe pod -n ai-infrastructure -l app=ai-agents-dashboard
```

### Check Services
```bash
kubectl get svc -n ai-infrastructure | grep dashboard
```

### Check Secrets
```bash
kubectl get secrets -n ai-infrastructure | grep -E "(db|argocd)"
```

## Common Pod States

| State | Meaning | Action |
|-------|---------|--------|
| `ErrImagePull` | Can't pull image | Build/load image, check imagePullPolicy |
| `ImagePullBackOff` | Pull failed, retrying | Fix image reference or policy |
| `CrashLoopBackOff` | App crashing | Check logs for errors |
| `CreateContainerConfigError` | Missing config/secrets | Create required secrets |
| `Pending` | Scheduling issue | Check resources, node availability |

## Reset Commands

### Delete and Recreate
```bash
# Delete deployment
kubectl delete deployment -n ai-infrastructure ai-agents-dashboard

# Delete secrets
kubectl delete secret -n ai-infrastructure db-secret argocd-secret

# Recreate everything
kubectl create secret generic db-secret -n ai-infrastructure \
  --from-literal=url="postgresql://postgres:postgres@postgres.langfuse.svc.cluster.local:5432/dashboard?sslmode=disable"
kubectl create secret generic argocd-secret -n ai-infrastructure \
  --from-literal=password="admin"
kubectl apply -f core/ai/runtime/dashboard/deployment/kubernetes/dashboard-deployment.yaml
```

### Force Restart
```bash
kubectl delete pods -n ai-infrastructure -l app=ai-agents-dashboard
```

## Access Dashboard

```bash
# Port forward
nohup kubectl port-forward -n ai-infrastructure svc/ai-agents-dashboard 8081:8081 &

# Access at http://localhost:8081
```

---

**Quick Tip**: Most issues are related to missing secrets or incorrect image configuration. Start by checking these two things first.
