# Langfuse Secrets Deployment Fix

## Issue Summary

**Problem**: Failed to deploy Langfuse secrets to control-plane namespace

**Date**: March 18, 2026  
**Status**: ✅ Resolved  
**Impact**: High - Blocked Langfuse observability integration

---

## Root Cause Analysis

### Primary Issue
1. **Missing Namespace**: The `control-plane` namespace did not exist in the cluster
2. **Wrong Target Namespace**: Secret was configured for non-existent `control-plane` namespace instead of existing `ai-infrastructure` namespace
3. **Cluster Connectivity**: kubectl commands were experiencing timeouts during troubleshooting

### Investigation Findings

#### Namespace Status
```bash
# Command that revealed the issue
kubectl get namespace control-plane
# Error: Error from server (NotFound): namespaces "control-plane" not found

# Actual existing namespaces
kubectl get namespaces | grep -E "(control|langfuse|ai)"
# Output:
# ai-infrastructure    Active   18h
# langfuse             Active   18h
```

#### Secret Configuration Analysis
Two secret files existed with different namespace targets:

1. **`core/config/langfuse-secret.yaml`** - Target: `control-plane` (non-existent)
2. **`core/config/langfuse-secret-$TOPDIR.yaml`** - Target: `ai-infrastructure` (exists)

---

## Solution Applied

### Fix Implementation
Updated the namespace in the primary secret configuration file:

**File**: `$TOPDIR/core/config/langfuse-secret.yaml`

**Change Made**:
```yaml
# Before (incorrect)
metadata:
  name: langfuse-secrets
  namespace: control-plane  # Matches temporal deployment namespace

# After (correct)
metadata:
  name: langfuse-secrets
  namespace: ai-infrastructure  # Matches existing namespace
```

### Additional Improvements
The fix also included proper base64 placeholder values for better documentation:

```yaml
data:
  public-key: eW91ci1iYXNlNjQtZW5jb2RlZC1wdWJsaWMta2V5  # placeholder: "your-base64-encoded-public-key"
  secret-key: eW91ci1iYXNlNjQtZW5jb2RlZC1zZWNyZXQta2V5  # placeholder: "your-base64-encoded-secret-key"
  otlp-headers: QXV0aG9yaXphdGlvbj1CZWFyZXIgeW91ci1zZWNyZXQta2V5  # placeholder: "Authorization=Bearer your-secret-key"
```

---

## Deployment Steps

### 1. Apply the Fixed Secret
```bash
kubectl apply -f core/config/langfuse-secret.yaml
```

### 2. Replace Placeholder Values
Before deployment, replace the placeholder values with your actual Langfuse credentials:

```bash
# Encode your actual values
echo -n 'your-public-key' | base64
echo -n 'your-secret-key' | base64
echo -n 'Authorization=Bearer your-secret-key' | base64

# Update the secret file with the encoded values
```

### 3. Verify Deployment
```bash
# Check secret exists
kubectl get secret langfuse-secrets -n ai-infrastructure

# Verify secret data
kubectl get secret langfuse-secrets -n ai-infrastructure -o yaml
```

---

## Verification Commands

### Pre-Deployment Checks
```bash
# Verify target namespace exists
kubectl get namespace ai-infrastructure

# Check for existing secrets
kubectl get secrets -n ai-infrastructure | grep langfuse

# Validate secret configuration
kubectl apply -f core/config/langfuse-secret.yaml --dry-run=client
```

### Post-Deployment Verification
```bash
# Confirm secret creation
kubectl get secret langfuse-secrets -n ai-infrastructure

# Check secret details
kubectl describe secret langfuse-secrets -n ai-infrastructure

# Verify data encoding (optional)
kubectl get secret langfuse-secrets -n ai-infrastructure -o jsonpath='{.data.public-key}' | base64 --decode
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Namespace Not Found
**Error**: `Error from server (NotFound): namespaces "control-plane" not found`

**Solution**: Use the existing `ai-infrastructure` namespace instead
```bash
# Check available namespaces
kubectl get namespaces

# Update secret configuration to use ai-infrastructure
```

#### 2. Secret Already Exists
**Error**: `Error from server (AlreadyExists): secrets "langfuse-secrets" already exists`

**Solution**: Delete and recreate, or patch the existing secret
```bash
# Option 1: Delete and recreate
kubectl delete secret langfuse-secrets -n ai-infrastructure
kubectl apply -f core/config/langfuse-secret.yaml

# Option 2: Patch existing secret
kubectl patch secret langfuse-secrets -n ai-infrastructure -p='<patch-data>'
```

#### 3. Invalid Base64 Encoding
**Error**: `Secret "langfuse-secrets" is invalid`

**Solution**: Ensure all secret data is properly base64 encoded
```bash
# Test your encoding
echo -n 'test-value' | base64
# Should output: dGVzdC12YWx1ZQ==
```

#### 4. kubectl Connection Issues
**Error**: Command timeouts or connection refused

**Solution**: Check cluster connectivity
```bash
# Verify cluster connection
kubectl cluster-info

# Check current context
kubectl config current-context

# Test with simple command
kubectl get pods
```

---

## Architecture Context

### Namespace Strategy
The repository uses a unified namespace approach:

- **`ai-infrastructure`**: Primary namespace for AI/ML workloads
- **`langfuse`**: Dedicated namespace for Langfuse observability stack
- **`control-plane`**: Not currently implemented (planned future)

### Secret Management Pattern
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <service>-secrets
  namespace: <target-namespace>
type: Opaque
data:
  <key1>: <base64-encoded-value1>
  <key2>: <base64-encoded-value2>
```

---

## Related Files

### Configuration Files
- `core/config/langfuse-secret.yaml` - Main secret configuration (fixed)
- `core/config/langfuse-secret-$TOPDIR.yaml` - Alternative configuration

### Documentation
- `docs/COMPREHENSIVE-LANGFUSE-TEMPORAL-INTEGRATION-GUIDE.md`
- `docs/LANGFUSE-AUTOMATED-SETUP-PROCESS.md`
- `docs/SELFSERVICE-LANGFUSE-SETUP.md`

### Automation Scripts
- `core/automation/scripts/setup-langfuse-keys-automated.sh`
- `core/automation/scripts/deploy-langfuse-selfhosted.sh`
- `core/automation/scripts/debug-langfuse.sh`

---

## Prevention Measures

### 1. Namespace Validation
Add namespace existence checks to deployment scripts:
```bash
#!/bin/bash
NAMESPACE="ai-infrastructure"
if ! kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
    echo "Namespace $NAMESPACE does not exist"
    exit 1
fi
```

### 2. Configuration Validation
Validate secret configurations before deployment:
```bash
#!/bin/bash
# Validate YAML syntax
kubectl apply -f secret.yaml --dry-run=client

# Validate namespace exists
kubectl get namespace $(yq eval '.metadata.namespace' secret.yaml)
```

### 3. Automated Testing
Include integration tests for secret deployments:
```bash
#!/bin/bash
# Test secret creation and retrieval
kubectl apply -f test-secret.yaml
if kubectl get secret test-secret -n ai-infrastructure >/dev/null 2>&1; then
    echo "Secret deployment successful"
    kubectl delete secret test-secret -n ai-infrastructure
else
    echo "Secret deployment failed"
    exit 1
fi
```

---

## Monitoring and Maintenance

### Health Checks
Regularly verify secret availability:
```bash
# Weekly health check
kubectl get secret langfuse-secrets -n ai-infrastructure || echo "ALERT: Langfuse secrets missing"
```

### Rotation Procedures
Plan for secret key rotation:
1. Generate new keys in Langfuse
2. Encode new values with base64
3. Update secret configuration
4. Apply changes
5. Verify connectivity
6. Delete old keys (after verification)

---

## Summary

The Langfuse secrets deployment issue was resolved by updating the target namespace from the non-existent `control-plane` namespace to the existing `ai-infrastructure` namespace. This fix ensures proper integration with the current cluster architecture and enables Langfuse observability functionality.

**Key Takeaways**:
1. Always verify target namespaces exist before deployment
2. Use existing namespace architecture rather than creating new ones unnecessarily
3. Include proper validation in deployment automation
4. Document namespace strategy for team alignment

---

**Tags**: langfuse, secrets, deployment, namespace, kubernetes, troubleshooting, fix-documentation
