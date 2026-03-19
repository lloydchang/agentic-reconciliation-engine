# Quickstart Script Fixes Summary

## Overview

This document documents all fixes applied to resolve issues encountered when running the Agentic Reconciliation Engine quickstart script (`./core/scripts/automation/quickstart.sh`).

## Issues Identified and Fixed

### 1. Langfuse Secrets Base64 Encoding Errors

**Problem**: Invalid base64 encoded values in Langfuse secret files causing deployment failures.

**Error Message**:
```
Error from server (BadRequest): error when creating "core/config/langfuse-secret.yaml": Secret in version "v1" cannot be handled as a Secret: illegal base64 data at input byte 0
```

**Root Cause**: The base64 strings contained invalid characters that weren't properly encoded.

**Files Fixed**:
- `core/config/langfuse-secret.yaml`
- `core/config/langfuse-secret-$TOPDIR.yaml`

**Fix Applied**:
```yaml
data:
  # Replace with base64 encoded actual values from your Langfuse account
  # To encode: echo -n 'your-value' | base64
  public-key: cGxhY2Vob2xkZXItcHVibGljLWtleQ==  # placeholder: "placeholder-public-key"
  secret-key: cGxhY2Vob2xkZXItc2VjcmV0LWtleQ==  # placeholder: "placeholder-secret-key"
  otlp-headers: QXV0aG9yaXphdGlvbj1CZWFyZXIgcGxhY2Vob2xkZXItc2VjcmV0LWtleQ==  # placeholder: "Authorization=Bearer placeholder-secret-key"
```

**Verification**: The new base64 values are properly encoded and can be decoded correctly:
```bash
echo "cGxhY2Vob2xkZXItcHVibGljLWtleQ==" | base64 -d  # Outputs: placeholder-public-key
```

---

### 2. Monitoring Namespace Missing Error

**Problem**: Monitoring resources were trying to deploy to a non-existent `monitoring` namespace.

**Error Message**:
```
Error from server (NotFound): error when creating "core/resources/infrastructure/monitoring": namespaces "monitoring" not found
```

**Root Cause**: The monitoring kustomization referenced a namespace but didn't include the namespace resource itself.

**Files Fixed**:
- `core/resources/infrastructure/monitoring/namespace.yaml` (created)
- `core/resources/infrastructure/monitoring/kustomization.yaml` (updated)

**Fix Applied**:

1. **Created namespace resource** (`namespace.yaml`):
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
  labels:
    app.kubernetes.io/name: monitoring
    app.kubernetes.io/part-of: agentic-reconciliation-engine
    app.kubernetes.io/managed-by: flux
```

2. **Updated kustomization** to include namespace:
```yaml
resources:
  # Namespace
  - namespace.yaml
  
  # Core monitoring components
  - flux-health.yaml
  - honeycomb.yaml
  - loki.yaml
  - promtail.yaml
  - langfuse-dashboard.yaml
  
  # eBPF observability
  - pixie.yaml
```

---

### 3. Agent Dashboard YAML Parsing Error

**Problem**: Large HTML content embedded in YAML heredoc caused parsing failures.

**Error Message**:
```
error: error parsing STDIN: error converting YAML to JSON: yaml: line 9: could not find expected ':'
```

**Root Cause**: Complex HTML content with special characters in the ConfigMap caused YAML parsing issues when embedded in shell heredoc.

**Files Fixed**:
- `core/resources/infrastructure/dashboard/agent-dashboard-configmap.yaml` (created)
- `core/scripts/automation/deploy-ai-agents-ecosystem.sh` (modified)

**Fix Applied**:

1. **Created external ConfigMap file** with properly formatted HTML content
2. **Modified deployment script** to use external file instead of embedded content:
```bash
# Deploy dashboard ConfigMap from external file
log_info "Deploying dashboard ConfigMap..."
$KUBECTL_CMD apply -f core/resources/infrastructure/dashboard/agent-dashboard-configmap.yaml
```

**Benefits**:
- Eliminates YAML parsing issues
- Better maintainability
- Cleaner script structure
- Easier to update HTML content

---

### 4. Auto-Configure-Langfuse Script Resource Finding Issue

**Problem**: Script was looking for pods with incorrect labels, causing resource discovery failures.

**Error Message**:
```
error: no matching resources found
⚠️  Automated setup failed, but secrets deployed
```

**Root Cause**: The script used `app=langfuse-server` label selector, but the actual deployment uses `app=langfuse`.

**Files Fixed**:
- `core/scripts/automation/auto-configure-langfuse.sh`

**Fix Applied**:

Updated pod label selectors from `app=langfuse-server` to `app=langfuse`:

```bash
# Before
kubectl wait --for=condition=ready pod -l app=langfuse-server -n langfuse --timeout=300s
kubectl get pod -l app=langfuse-server -n langfuse --no-headers

# After  
kubectl wait --for=condition=ready pod -l app=langfuse -n langfuse --timeout=300s
kubectl get pod -l app=langfuse -n langfuse --no-headers
```

**Verification**: Confirmed the actual Langfuse deployment uses `app: langfuse` labels by checking the deployment manifest.

---

## Testing and Verification

### Quickstart Script Test
After applying all fixes, the quickstart script should run successfully:

```bash
./core/scripts/automation/quickstart.sh
```

Expected behavior:
- ✅ Langfuse secrets deploy without base64 errors
- ✅ Monitoring namespace created successfully
- ✅ Agent dashboard deploys without YAML parsing errors
- ✅ Auto-configure Langfuse script finds resources correctly

### Individual Component Testing

1. **Langfuse Secrets**:
```bash
kubectl apply -f core/config/langfuse-secret.yaml
kubectl apply -f core/config/langfuse-secret-$TOPDIR.yaml
```

2. **Monitoring Infrastructure**:
```bash
kubectl apply -k core/resources/infrastructure/monitoring
```

3. **Agent Dashboard**:
```bash
./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

4. **Langfuse Auto-Configuration**:
```bash
./core/scripts/automation/auto-configure-langfuse.sh
```

---

## Root Cause Analysis

### Common Patterns

1. **Configuration Issues**: Most problems stemmed from incorrect configuration values or missing resources
2. **Label Mismatches**: Resource discovery failures due to inconsistent labeling
3. **YAML Complexity**: Large embedded content causing parsing issues
4. **Missing Dependencies**: Resources referencing non-existent namespaces or dependencies

### Prevention Strategies

1. **Configuration Validation**: Validate base64 encoding and YAML syntax before deployment
2. **Label Consistency**: Ensure consistent labeling across deployments and scripts
3. **Resource Organization**: Use external files for complex content instead of embedded YAML
4. **Dependency Management**: Create required namespaces and dependencies before deploying resources

---

## Files Modified Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `core/config/langfuse-secret.yaml` | Fixed | Corrected base64 encoding |
| `core/config/langfuse-secret-$TOPDIR.yaml` | Fixed | Corrected base64 encoding |
| `core/resources/infrastructure/monitoring/namespace.yaml` | Created | Added monitoring namespace |
| `core/resources/infrastructure/monitoring/kustomization.yaml` | Updated | Added namespace to resources |
| `core/resources/infrastructure/dashboard/agent-dashboard-configmap.yaml` | Created | External dashboard ConfigMap |
| `core/scripts/automation/deploy-ai-agents-ecosystem.sh` | Modified | Use external ConfigMap |
| `core/scripts/automation/auto-configure-langfuse.sh` | Fixed | Corrected pod label selectors |

---

## Future Improvements

### Short-term
1. Add configuration validation to quickstart script
2. Implement pre-flight checks for namespace existence
3. Add YAML syntax validation for embedded content

### Long-term
1. Migrate to Helm charts for better dependency management
2. Implement GitOps-based deployment with proper resource ordering
3. Add comprehensive health checks and rollback capabilities

---

## Troubleshooting Guide

### If Issues Persist

1. **Check Resource Status**:
```bash
kubectl get all -n ai-infrastructure
kubectl get all -n monitoring
kubectl get all -n langfuse
```

2. **Check Pod Logs**:
```bash
kubectl logs -n ai-infrastructure deployment/agent-dashboard
kubectl logs -n monitoring -l app.kubernetes.io/name=monitoring
```

3. **Verify Configuration**:
```bash
kubectl get secrets -n ai-infrastructure | grep langfuse
kubectl get configmaps -n ai-infrastructure | grep dashboard
```

4. **Manual Recovery**:
```bash
# Delete and recreate problematic resources
kubectl delete secret langfuse-secrets -n ai-infrastructure
kubectl apply -f core/config/langfuse-secret.yaml
```

---

## Related Documentation

- [Agent Dashboard Guide](AGENT-DASHBOARD-GUIDE.md)
- [Langfuse Integration Guide](LANGFUSE-INTEGRATION.md)
- [Monitoring Setup Guide](MONITORING-SETUP.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**Last Updated**: 2025-03-18  
**Author**: Cascade AI Assistant  
**Version**: 1.0
