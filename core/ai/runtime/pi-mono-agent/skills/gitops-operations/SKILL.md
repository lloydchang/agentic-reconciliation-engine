---
name: gitops-operations
description: >
  GitOps operations skill for pi-mono containerized agent. Use when asked to deploy,
  manage, or troubleshoot GitOps workflows, Kubernetes manifests, or infrastructure
  changes. Integrates with the GitOps Control Plane for safe, auditable deployments.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: gitops
  human_gate: PR approval required for production changes
---

# GitOps Operations Skill

Use this skill when the user asks about:
- Deploying infrastructure changes
- Managing Kubernetes manifests
- GitOps workflow operations
- Cluster management
- Security and compliance checks

## Prerequisites

- GitOps Control Plane access
- kubectl configured
- Repository write access

## GitOps Deployment Steps

### 1. Analyze Request
```bash
# Understand what needs to be deployed
read /workspace/gitops-infra-control-plane/README.md
```

### 2. Check Current State
```bash
# Check current cluster state
kubectl get pods -A
kubectl get deployments -A
git status
```

### 3. Validate Changes
```bash
# Validate manifests
kubectl apply --dry-run=client -f manifests/
helm template ./charts/ | kubectl apply --dry-run=client -f -
```

### 4. Create Pull Request
```bash
# Create feature branch
git checkout -b feature/infrastructure-update
git add .
git commit -m "Infrastructure update: [description]"
git push origin feature/infrastructure-update

# Create PR (via gh CLI)
gh pr create --title "Infrastructure Update" --body "Changes: [description]"
```

### 5. Monitor Deployment
```bash
# Monitor after merge
kubectl get pods -w
kubectl logs -f deployment/name
```

## Security Checklist

Before any deployment:
- [ ] Review manifests for security issues
- [ ] Check resource limits
- [ ] Validate network policies
- [ ] Ensure secrets are properly managed
- [ ] Verify RBAC permissions

## Troubleshooting

### Common Issues

**Pod Not Starting:**
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Deployment Stuck:**
```bash
kubectl rollout status deployment/<name>
kubectl rollout undo deployment/<name>
```

**Resource Issues:**
```bash
kubectl top nodes
kubectl top pods
kubectl describe node <node-name>
```

## Integration with Memory Agent

```bash
# Query memory agent for similar past operations
curl -X POST "$MEMORY_AGENT_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "previous deployment issues", "limit": 5}'
```

## Examples

### Deploy New Service
```bash
# User: "Deploy the new payment service to staging"

# 1. Check manifests
ls /workspace/gitops-infra-control-plane/gitops/staging/payment-service/

# 2. Validate
kubectl apply --dry-run=client -f gitops/staging/payment-service/

# 3. Deploy via GitOps
git add gitops/staging/payment-service/
git commit -m "Add payment service to staging"
git push origin main

# 4. Monitor
kubectl get pods -n staging -l app=payment-service
```

### Rollback Deployment
```bash
# User: "Rollback the payment service deployment"

# 1. Check previous revisions
kubectl rollout history deployment/payment-service -n staging

# 2. Rollback
kubectl rollout undo deployment/payment-service -n staging

# 3. Verify
kubectl get pods -n staging -l app=payment-service
```

## Cost Optimization

When making changes:
- Review resource requests/limits
- Check for unused resources
- Consider spot instances for dev/test
- Monitor cost impact

## Monitoring

Set up alerts for:
- Deployment failures
- High resource usage
- Security violations
- Cost anomalies

## References

- GitOps Control Plane documentation
- Kubernetes best practices
- Security guidelines
- Cost optimization strategies
