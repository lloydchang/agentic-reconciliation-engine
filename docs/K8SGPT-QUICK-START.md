# K8sGPT Consolidation - Quick Start Guide

## 🚀 Quick Deployment

Ready to deploy the consolidated K8sGPT to your test cluster? Follow these steps:

### 1️⃣ Prerequisites
```bash
# Ensure kubectl is configured
kubectl cluster-info

# Check cluster resources (need 4Gi memory, 2000m CPU)
kubectl top nodes
```

### 2️⃣ One-Command Deployment
```bash
# One-command deployment and validation
./core/scripts/deploy-consolidated-k8sgpt.sh full
```

### 3️⃣ Verify Success
```bash
# Check deployment status
kubectl get deployment k8sgpt -n k8sgpt-system

# Test service connectivity
kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system &
curl -f http://localhost:8080/healthz
```

## 📋 Available Commands

```bash
# Deploy only
./core/scripts/deploy-consolidated-k8sgpt.sh deploy

# Validate existing deployment
./core/scripts/deploy-consolidated-k8sgpt.sh validate

# Test connectivity only
./core/scripts/deploy-consolidated-k8sgpt.sh test

# Clean up old deployments
./core/scripts/deploy-consolidated-k8sgpt.sh cleanup

# Generate deployment report
./core/scripts/deploy-consolidated-k8sgpt.sh report

# Full deployment and validation
./core/scripts/deploy-consolidated-k8sgpt.sh full

# Dry run (show commands without executing)
./core/scripts/deploy-consolidated-k8sgpt.sh --dry-run full

# Custom namespace
./core/scripts/deploy-consolidated-k8sgpt.sh --namespace my-k8sgpt deploy

# Verbose output
./core/scripts/deploy-consolidated-k8sgpt.sh --verbose full
```

## 🔧 Manual Steps (Optional)

If you prefer manual deployment:

```bash
# 1. Create namespace
kubectl create namespace k8sgpt-system

# 2. Configure secrets
cp core/gitops/consolidated/k8sgpt-secrets-template.yaml core/gitops/consolidated/k8sgpt-secrets.yaml
# Edit the secrets file with your actual values

# 3. Apply configurations
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-config.yaml
kubectl apply -f core/gitops/consolidated/k8sgpt-secrets.yaml
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-deployment.yaml

# 4. Wait for rollout
kubectl rollout status deployment/k8sgpt -n k8sgpt-system
```

## 🎯 Service Endpoints

Once deployed, K8sGPT will be available at:

- **HTTP API**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:8080`
- **Health Check**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz`
- **Metrics**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:9090/metrics`
- **Analysis**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/analyze`

## 📊 Component Integration

All GitOps components should use this unified service endpoint:

```bash
# Argo Workflows
K8SGPT_ENDPOINT="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"

# Flux CD
K8SGPT_API_BASE="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"

# Argo Rollouts
K8SGPT_SERVICE_URL="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
```

## ✅ Validation Checklist

After deployment, verify:

- [ ] K8sGPT pod is running and healthy
- [ ] Service is accessible from all component namespaces
- [ ] Health endpoint returns 200 OK
- [ ] Metrics endpoint is working
- [ ] Resource usage is within limits (4Gi memory, 2 CPU)
- [ ] All component integrations are working

## 🚨 Troubleshooting

```bash
# Check logs
kubectl logs -n k8sgpt-system deployment/k8sgpt

# Check events
kubectl get events -n k8sgpt-system --sort-by='.lastTimestamp'

# Debug connectivity
kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system
curl -v http://localhost:8080/healthz

# Check resource usage
kubectl top pod -n k8sgpt-system -l app.kubernetes.io/name=k8sgpt
```

## 📚 Additional Resources

- **Complete Guide**: `docs/K8SGPT-DEPLOYMENT-VALIDATION-GUIDE.md`
- **Migration Script**: `core/scripts/migrate-to-consolidated-k8sgpt.sh`
- **Integration Guide**: `core/gitops/consolidated/component-integration-guide.md`
- **Architecture Summary**: `docs/K8SGPT-CONSOLIDATION-SUMMARY.md`

## 🎉 Success!

When you see:
- ✅ Deployment is healthy
- ✅ All component integrations working  
- ✅ Resource usage optimized (75% reduction!)
- ✅ Single service endpoint for all GitOps components

Your K8sGPT consolidation is complete and ready for production!
