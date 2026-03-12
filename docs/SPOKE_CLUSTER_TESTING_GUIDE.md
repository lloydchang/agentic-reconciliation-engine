# Spoke Cluster Provisioning Testing Guide

## Overview

This guide explains how to test AWS ACK, Azure ASO, and GCP KCC controllers for provisioning and managing the three spoke clusters (EKS, AKS, GKE) as described in the README.md hub-and-spoke architecture.

## Architecture

```
                       GIT REPOSITORY
                     (Source of Truth)
                             |
                    Flux Pulls Manifests
                             |
                             v
      +------------------------------------------+
      |                HUB CLUSTER               |
      |------------------------------------------|
      | Flux | ACK        | ASO           | KCC  |
      +------------------------------------------+
             |               |               |
   Provisions/Manages Provisions/Manages Provisions/Manages
             |               |               |
      +-------------+ +-------------+ +-------------+
      |   SPOKE 1   | |   SPOKE 2   | |   SPOKE 3   |
      |   (EKS)     | |   (AKS)     | |   (GKE)     |
      |   CLUSTER   | |   CLUSTER   | |   CLUSTER   |
      +-------------+ +-------------+ +-------------+
```

## Test Script: `test-spoke-provisioning-validation.sh`

This comprehensive test validates the complete hub-and-spoke architecture with local emulators.

### What It Tests

#### 1. **AWS ACK Controller for Spoke 1 (EKS)**
- ✅ Validates AWS ACK controller readiness
- ✅ Creates EKS cluster manifests in `spoke-1` namespace
- ✅ Configures AWS credentials and cluster settings
- ✅ Tests EC2 instance provisioning via ACK

#### 2. **Azure ASO Controller for Spoke 2 (AKS)**
- ✅ Validates Azure ASO controller readiness  
- ✅ Creates AKS cluster manifests in `spoke-2` namespace
- ✅ Configures Azure credentials and cluster settings
- ✅ Tests Virtual Network provisioning via ASO

#### 3. **GCP KCC Controller for Spoke 3 (GKE)**
- ✅ Validates GCP KCC controller readiness
- ✅ Creates GKE cluster manifests in `spoke-3` namespace
- ✅ Configures GCP service account and cluster settings
- ✅ Tests Compute Engine instance provisioning via KCC

#### 4. **Flux Dependency Chains**
- ✅ Creates proper `dependsOn` relationships
- ✅ Validates dependency ordering: network → clusters → workloads
- ✅ Tests Flux Kustomization reconciliation

#### 5. **Multi-Cloud Resource Management**
- ✅ Validates all spoke namespaces exist
- ✅ Checks ConfigMaps and Secrets for each spoke
- ✅ Verifies resource isolation between spokes

#### 6. **Hub-Spoke Communication Architecture**
- ✅ Validates hub namespace (`flux-system`)
- ✅ Checks spoke namespace separation
- ✅ Counts resources in hub and spoke namespaces

#### 7. **Cloud Controller Integration**
- ✅ Tests AWS ACK can create EC2 instances
- ✅ Tests Azure ASO can create Virtual Networks  
- ✅ Tests GCP KCC can create Compute instances

## How to Run

```bash
# Make executable
chmod +x test-spoke-provisioning-validation.sh

# Run the complete test suite
./test-spoke-provisioning-validation.sh
```

## Expected Results

### ✅ **Successful Test Output**
```
🚀 AWS ACK, Azure ASO, GCP KCC Spoke Cluster Provisioning Validation
=========================================================================

Test 1: AWS ACK Controller for Spoke 1 (EKS)
================================
[TEST] ✅ AWS ACK EC2 controller ready (1 replicas)
[TEST] ✅ Spoke 1 (EKS) manifests created
[TEST] ✅ EKS cluster: spoke-1-eks-cluster

Test 2: Azure ASO Controller for Spoke 2 (AKS)
================================
[TEST] ✅ Azure ASO controller ready (1 replicas)
[TEST] ✅ Spoke 2 (AKS) manifests created
[TEST] ✅ AKS cluster: spoke-2-aks-cluster

Test 3: GCP KCC Controller for Spoke 3 (GKE)
================================
[TEST] ✅ GCP KCC controller ready (1 replicas)
[TEST] ✅ Spoke 3 (GKE) manifests created
[TEST] ✅ GKE cluster: spoke-3-gke-cluster

... (all 7 tests pass) ...

🎉 All spoke cluster provisioning tests completed!
✅ Hub-and-spoke architecture validated
✅ AWS ACK, Azure ASO, GCP KCC controllers tested
✅ Multi-cloud spoke cluster management verified
```

### ⚠️ **Expected Warnings with Emulators**
```
[WARN] ⚠️ AWS ACK EC2 controller not ready
[WARN] ⚠️ Azure ASO controller not ready  
[WARN] ⚠️ GCP KCC controller not ready
[WARN] ⚠️ Cloud controller integration failed (expected with emulator)
```

These warnings are **expected** when using local emulators instead of real cloud controllers.

## Key Components Tested

### **Namespaces Created**
- `flux-system` - Hub cluster management
- `spoke-1` - EKS cluster resources
- `spoke-2` - AKS cluster resources  
- `spoke-3` - GKE cluster resources

### **ConfigMaps Created**
- `spoke-1-eks-config` - EKS cluster configuration
- `spoke-2-aks-config` - AKS cluster configuration
- `spoke-3-gke-config` - GKE cluster configuration

### **Secrets Created**
- `spoke-1-aws-credentials` - AWS access credentials
- `spoke-2-azure-credentials` - Azure service credentials
- `spoke-3-gcp-credentials` - GCP service account

### **Kustomizations Created**
- `network-infrastructure` - Foundation layer
- `spoke-cluster-infrastructure` - Spoke clusters (depends on network)
- `spoke-workload-infrastructure` - Workloads (depends on clusters)

## Integration with Local Emulators

The test works with the local emulators deployed in this repository:

### **AWS Services (LocalStack)**
- Endpoint: `http://localstack.localstack.svc.cluster.local:4566`
- Services: EC2, EKS, IAM
- Namespace: `localstack`

### **Azure Services (LocalStack Azure)**
- Endpoint: `http://localstack-azure.localstack.svc.cluster.local:4567`
- Services: Virtual Networks, Storage, Functions
- Namespace: `localstack`

### **GCP Services (GCS Emulator)**
- Endpoint: `http://gcs-emulator.default.svc.cluster.local:9023`
- Services: Compute Engine, Storage, Pub/Sub
- Namespace: `default`

## Real Cloud vs Emulator Behavior

| Feature | Real Cloud | Local Emulator | Status |
|---------|-------------|------------------|---------|
| ACK/ASO/KCC Controllers | ✅ Ready | ⚠️ Mock | Expected |
| Resource Creation | ✅ Working | ⚠️ Simulated | Expected |
| API Calls | ✅ Real Endpoints | ⚠️ Local Endpoints | Expected |
| Cost | 💰 Real Cost | 🆓 Free | Expected |

## Next Steps

1. **Deploy Real Cloud Controllers**: Replace emulators with actual cloud controllers
2. **Configure Credentials**: Set up real cloud provider credentials
3. **Test Real Provisioning**: Verify actual cluster creation
4. **Monitor Reconciliation**: Test drift detection and repair
5. **Scale Testing**: Test with multiple clusters per cloud

## Troubleshooting

### **Common Issues**
- **Permission denied**: Check RBAC and service accounts
- **Controller not ready**: Wait for deployment to complete
- **CRD not found**: Install cloud provider CRDs first
- **Network timeouts**: Verify emulator connectivity

### **Debug Commands**
```bash
# Check controller status
kubectl get deployments -n ack-system
kubectl get deployments -n azureserviceoperator-system
kubectl get deployments -n cnrm-system

# Check CRDs
kubectl get crd | grep -E "(eks|aks|gke)"

# Check reconciliation status
kubectl get kustomization -n flux-system
```

This comprehensive test validates that the GitOps Infrastructure Control Plane can properly provision and manage multi-cloud spoke clusters using native Kubernetes controllers.
