# Network Connectivity and Installation Troubleshooting Documentation

## Overview

This document covers the comprehensive network connectivity diagnostic and enhanced installation scripts developed to resolve Helm/kubectl timeout issues in the GitOps infrastructure control plane.

## Files Created/Modified

### 1. Network Connectivity Diagnostic Script
**File**: `core/scripts/automation/network-connectivity-diagnostic.sh`

**Purpose**: Comprehensive network connectivity testing for Kubernetes clusters

**Features**:
- DNS resolution testing using nslookup
- CoreDNS pod health checking
- Node resource utilization monitoring
- Network policy detection
- Helm repository connectivity testing
- Required port accessibility checks (53, 443, 6443, 10250)
- Connectivity pod status verification (konnectivity, tunnelfront, aks-link)

**Usage**:
```bash
./core/scripts/automation/network-connectivity-diagnostic.sh
```

**Key Functions**:
- `print_status()`: Color-coded status output
- DNS testing via dedicated test pod
- Port connectivity verification
- Resource usage analysis
- Automated recommendations based on findings

### 2. Enhanced Crossplane Installation Script
**File**: `core/scripts/automation/install-crossplane.sh` (Modified)

**Purpose**: Crossplane installation with intelligent failure diagnosis

**Key Enhancements**:
- **Smart Error Handling**: Each operation wrapped with proper error checking
- **Exit Code Analysis**: Distinguishes between different failure types:
  - Code 125: Timeout/resource exhaustion
  - Code 1: Command execution/permission failures
  - Code 2: Invalid arguments/misconfiguration
  - Code 130: Script interruption
  - Code 255: Signal termination
- **Automatic Diagnostics**: Runs network connectivity script on failure
- **Operation-Specific Troubleshooting**: Targeted advice for different failure modes

**New Functions**:
- `diagnose_installation_failure()`: Comprehensive failure analysis and recommendations
- Enhanced error handling in `install_crossplane()`, `verify_installation()`
- Global error trap with `set -Eeo pipefail` and `trap`

### 3. kubectl Version Fix Script
**File**: `core/scripts/automation/fix-kubectl-version.sh`

**Purpose**: Resolve kubectl version skew issues between client and server

**Features**:
- Current version checking (client and server)
- Automatic kubectl update via Homebrew
- Connectivity testing for hub and bootstrap clusters
- Version skew detection and resolution

**Usage**:
```bash
./core/scripts/automation/fix-kubectl-version.sh
```

## Root Cause Analysis

### Network Connectivity Issues Identified

1. **DNS Resolution Problems**
   - CoreDNS pod failures
   - DNS configuration issues
   - Network policy blocking DNS traffic

2. **Helm Repository Connectivity**
   - Timeout accessing charts.crossplane.io
   - Proxy configuration issues
   - Firewall blocking HTTPS (port 443)

3. **Cluster Communication**
   - API server connectivity problems (port 6443)
   - Node-to-control plane communication failures
   - Connectivity pod issues (konnectivity-agent)

4. **Resource Constraints**
   - Overloaded nodes affecting connectivity
   - Insufficient CPU/memory for pod startup
   - Network bandwidth limitations

### Non-Network Issues Addressed

1. **Permission Problems**
   - RBAC configuration issues
   - Namespace creation permissions
   - Service account permissions

2. **Resource Exhaustion**
   - Node capacity limits
   - Memory pressure
   - CPU throttling

3. **Configuration Errors**
   - Invalid Helm values
   - Incorrect namespace settings
   - Version incompatibilities

## Troubleshooting Workflow

### Automated Diagnosis
When installation fails, the enhanced script automatically:

1. **Captures Failure Context**
   - Operation being performed
   - Exit code returned
   - Error messages

2. **Runs Network Diagnostics**
   - Executes `network-connectivity-diagnostic.sh`
   - Captures comprehensive system state

3. **Analyzes Failure Pattern**
   - Maps exit code to likely causes
   - Provides targeted troubleshooting steps

4. **Offers Actionable Solutions**
   - Specific commands for further investigation
   - Common fixes based on failure type
   - Prevention recommendations

### Manual Troubleshooting Commands

**Network Testing**:
```bash
# Test DNS resolution
kubectl exec -i -t dnsutils -- nslookup kubernetes.default

# Check required ports
nc -zv <cluster-api-server> 6443
nc -zv 8.8.8.8 53

# Test Helm connectivity
helm repo update
curl -I https://charts.crossplane.io/stable
```

**Resource Analysis**:
```bash
# Check node utilization
kubectl top nodes
kubectl top pods --all-namespaces

# Check pod status
kubectl get pods -n crossplane-system
kubectl describe pods -n crossplane-system
```

**Permission Verification**:
```bash
# Check RBAC permissions
kubectl auth can-i create namespace
kubectl auth can-i create deployment --namespace=crossplane-system
```

## Common Solutions

### 1. Network Issues
```bash
# Set proxy variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Restart CoreDNS
kubectl rollout restart deployment/coredns -n kube-system

# Clear Helm cache
helm repo rm crossplane
helm repo add crossplane https://charts.crossplane.io/stable
```

### 2. Resource Issues
```bash
# Check cluster capacity
kubectl describe nodes

# Scale down resource-intensive workloads
kubectl scale deployment --replicas=0 <deployment-name>
```

### 3. Version Issues
```bash
# Update kubectl
brew install kubernetes-cli
brew link --overwrite kubernetes-cli

# Check version compatibility
kubectl version
```

## Integration with GitOps Workflow

### Pre-Deployment Validation
- Run network diagnostics before major deployments
- Verify kubectl version compatibility
- Check cluster resource availability

### During Deployment
- Enhanced installation scripts provide real-time feedback
- Automatic failure diagnosis reduces troubleshooting time
- Targeted error messages guide resolution

### Post-Deployment Verification
- Comprehensive installation verification
- Health checks for all components
- Performance baseline establishment

## Future Enhancements

### Planned Improvements
1. **Automated Remediation**: Self-healing for common issues
2. **Performance Monitoring**: Continuous network health tracking
3. **Integration Testing**: Automated validation before deployments
4. **Multi-Cluster Support**: Extended diagnostics for hub-spoke topology

### Monitoring Integration
- Prometheus metrics for network health
- Grafana dashboards for connectivity trends
- Alert rules for common failure patterns

## Best Practices

### Prevention
1. **Regular Health Checks**: Run diagnostics periodically
2. **Version Management**: Keep kubectl and cluster versions compatible
3. **Resource Planning**: Monitor cluster capacity utilization
4. **Network Documentation**: Maintain network topology and firewall rules

### Response
1. **Structured Troubleshooting**: Follow the automated workflow
2. **Comprehensive Logging**: Capture all diagnostic output
3. **Incremental Fixes**: Apply one change at a time
4. **Validation**: Verify fixes with diagnostic script

## Conclusion

The enhanced diagnostic and installation capabilities provide a robust foundation for maintaining network connectivity and resolving installation issues in the GitOps infrastructure control plane. By combining automated diagnostics with intelligent failure analysis, the system reduces troubleshooting time and improves reliability of Crossplane and other component deployments.

The approach moves beyond generic timeout assumptions to provide specific, actionable solutions for a wide range of potential issues, ensuring that both network and non-network problems are properly identified and resolved.
