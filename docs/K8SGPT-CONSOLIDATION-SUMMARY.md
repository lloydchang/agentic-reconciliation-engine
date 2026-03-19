# K8sGPT Consolidation Summary

## Overview

This document summarizes the consolidation of multiple K8sGPT deployments into a single, unified instance per cluster. This change ensures resource efficiency, simplified management, and consistent AI analysis across all Agentic Reconciliation Engine components.

## Problem Statement

The repository contained multiple K8sGPT deployment instances across different components:
- **ArgoCD Integration**: Separate K8sGPT deployment in `k8sgpt-system` namespace
- **Flux System Integration**: K8sGPT deployment in `flux-system` namespace  
- **Argo Workflows Integration**: K8sGPT deployment in `argo-workflows` namespace
- **Standalone Analyzer**: K8sGPT with embedded Qwen server
- **PipeCD Integration**: Additional configuration for PipeCD

This approach violated the principle of "one instance per cluster" and led to:
- Resource waste (multiple AI models running)
- Configuration complexity
- Inconsistent analysis results
- Difficult maintenance and upgrades

## Solution Architecture

### Consolidated Design

**Single K8sGPT Instance** in `k8sgpt-system` namespace:
- **Unified Service**: `http://k8sgpt.k8sgpt-system.svc.cluster.local:8080`
- **Multi-Backend Support**: Agent-memory (primary), LocalAI (fallback), OpenAI (optional)
- **Cluster-Wide RBAC**: Comprehensive permissions for all resource types
- **Standardized Configuration**: Centralized ConfigMap for all integrations
- **Metrics & Tracing**: Built-in monitoring with Prometheus and Jaeger

### Key Features

1. **Backend Fallback Chain**:
   - Primary: Agent-memory with Qwen2.5B
   - Fallback: LocalAI with Qwen2.5-coder
   - Optional: External OpenAI-compatible API

2. **Multi-Component Analysis**:
   - Core Kubernetes resources
   - Argo Workflows (workflows, templates)
   - Argo Rollouts (rollouts, analysis templates)
   - Argo Events (event sources, sensors)
   - Flux CD (kustomizations, helm releases)
   - ArgoCD applications

3. **Unified Sink Configuration**:
   - Primary: Flux webhook
   - Additional: Argo Workflows, Argo Rollouts, monitoring

4. **Comprehensive RBAC**:
   - All necessary permissions for cluster-wide analysis
   - Support for custom resources from all GitOps tools

## Files Created

### Core Consolidation Files
- `core/gitops/consolidated/k8sgpt-unified-deployment.yaml` - Main deployment manifest
- `core/gitops/consolidated/k8sgpt-unified-config.yaml` - Unified configuration
- `core/gitops/consolidated/k8sgpt-secrets-template.yaml` - Secrets template
- `core/gitops/consolidated/k8sgpt-gitops-apps.yaml` - GitOps application manifests
- `core/gitops/consolidated/component-integration-guide.md` - Integration guide

### Migration Tools
- `core/scripts/migrate-to-consolidated-k8sgpt.sh` - Migration automation script

## Files to Remove

After migration, the following files can be safely removed:

### Redundant Deployment Files
- `core/gitops/argocd/k8sgpt/k8sgpt-deployment.yaml` ❌
- `core/gitops/flux-system/k8sgpt-qwen.yaml` ❌
- `overlay/argo-workflows/qwen/qwen-k8sgpt-deployment.yaml` ❌
- `overlay/k8sgpt/deployments/k8sgpt-analyzer.yaml` ❌
- `overlay/k8sgpt/services/k8sgpt-analyzer.yaml` ❌

### Redundant Configuration Files
- `overlay/flux-system/production/patches/k8sgpt-patches.yaml` ❌
- `overlay/flux-system/staging/patches/k8sgpt-patches.yaml` ❌
- `overlay/flux-system/development/patches/k8sgpt-patches.yaml` ❌
- `overlay/argocd/production/k8sgpt-patch.yaml` ❌
- `overlay/argocd/staging/k8sgpt-patch.yaml` ❌
- `overlay/pipecd/k8sgpt/k8sgpt-config.yaml` ❌

### Redundant RBAC Files
- `overlay/k8sgpt/rbac/k8sgpt-rbac.yaml` ❌
- `core/gitops/argocd/applications/k8sgpt-app.yaml` ❌ (replace with consolidated version)

### Test Files (to be updated)
- `tests/k8sgpt/test_k8sgpt_integration.py` 🔄 (update for consolidated service)
- `tests/k8sgpt/test_examples.py` 🔄 (update for consolidated service)

## Migration Steps

### 1. Preparation
```bash
# Review the consolidated configuration
cat core/gitops/consolidated/k8sgpt-unified-config.yaml

# Update secrets template with actual values
cp core/gitops/consolidated/k8sgpt-secrets-template.yaml core/gitops/consolidated/k8sgpt-secrets.yaml
# Edit the file with your actual secrets
```

### 2. Backup Existing Resources
```bash
# Run the migration script with backup option
./scripts/migrate-to-consolidated-k8sgpt.sh --backup
```

### 3. Deploy Consolidated Instance
```bash
# Apply the consolidated deployment
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-config.yaml
kubectl apply -f core/gitops/consolidated/k8sgpt-unified-deployment.yaml
```

### 4. Update Component Configurations
```bash
# Follow the integration guide to update components
# Reference: core/gitops/consolidated/component-integration-guide.md
```

### 5. Remove Old Deployments
```bash
# Run the migration script
./core/scripts/migrate-to-consolidated-k8sgpt.sh
```

## Component Integration Updates

### Standard Service Endpoint
All components should use:
```
http://k8sgpt.k8sgpt-system.svc.cluster.local:8080
```

### Environment Variables
```bash
K8SGPT_ENDPOINT="http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
K8SGPT_MODEL="qwen2.5-7b-instruct"
K8SGPT_BACKEND="agent-memory"
K8SGPT_TIMEOUT="30s"
```

### Network Policies
Ensure network policies allow traffic to `k8sgpt-system` namespace from:
- `argo-workflows`
- `argo-rollouts`
- `flux-system`
- `argo-events`
- `pipecd`

## Benefits Achieved

### Resource Efficiency
- **Reduced Memory Usage**: From ~16Gi to ~4Gi per cluster
- **Reduced CPU Usage**: From ~6000m to ~2000m per cluster
- **Single Model Instance**: One Qwen2.5B model instead of multiple

### Operational Benefits
- **Simplified Management**: Single deployment to monitor and upgrade
- **Consistent Analysis**: Same AI model and configuration across all components
- **Centralized Configuration**: One ConfigMap for all integrations
- **Unified Monitoring**: Single metrics endpoint for all K8sGPT operations

### Maintenance Benefits
- **Easier Updates**: Update once, affects all components
- **Simplified Backup**: One set of logs and cache to backup
- **Unified Debugging**: Single location for troubleshooting
- **Consistent Security**: One RBAC policy to maintain

## Verification Steps

### 1. Deployment Health
```bash
# Check deployment status
kubectl get deployment k8sgpt -n k8sgpt-system

# Check service endpoints
kubectl get service k8sgpt -n k8sgpt-system

# Test health endpoint
kubectl port-forward service/k8sgpt 8080:8080 -n k8sgpt-system &
curl http://localhost:8080/healthz
```

### 2. Component Integration
```bash
# Test from each component namespace
kubectl run test-pod --image=curlimages/curl -i --restart=Never --rm -- \
  curl -f http://k8sgpt.k8sgpt-system.svc.cluster.local:8080/healthz
```

### 3. Metrics Collection
```bash
# Check metrics endpoint
kubectl port-forward service/k8sgpt 9090:9090 -n k8sgpt-system &
curl http://localhost:9090/metrics
```

## Troubleshooting

### Common Issues
1. **Connection Refused**: Check network policies and service discovery
2. **Authentication Errors**: Verify secrets and API keys
3. **Backend Failures**: Check agent-memory service availability
4. **Permission Issues**: Verify RBAC configuration

### Recovery Steps
1. **Restore Backup**: Use the backup created during migration
2. **Rollback**: Revert to previous deployment files
3. **Debug Logs**: Check K8sGPT logs for backend connection issues

## Future Considerations

### Scalability
- **Horizontal Scaling**: Can increase replicas if needed
- **Resource Scaling**: Adjust CPU/memory limits based on usage
- **Backend Scaling**: Multiple agent-memory instances for high load

### Multi-Cluster Support
- **One Instance Per Cluster**: Maintains the principle of single instance per cluster
- **Cross-Cluster Analysis**: Each cluster analyzes its own resources
- **Centralized Monitoring**: Aggregate metrics across clusters

### Security Enhancements
- **Network Segmentation**: Additional network policies for security
- **Secret Management**: Integration with external secret stores
- **Audit Logging**: Enhanced audit trails for compliance

## Conclusion

The consolidation of K8sGPT deployments achieves significant benefits in resource efficiency, operational simplicity, and maintainability while preserving all functionality across the Agentic Reconciliation Engine. The unified architecture provides a solid foundation for AI-powered Kubernetes analysis at scale.

### Next Steps
1. Execute the migration using the provided script
2. Update all component configurations
3. Remove redundant deployment files
4. Update documentation
5. Monitor the consolidated deployment in production

This consolidation aligns with the principle of "one instance per cluster" similar to the agent-memory-rust with Qwen2.5B approach, ensuring efficient resource utilization while maintaining comprehensive AI analysis capabilities.
