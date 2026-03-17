# Strategic Architecture Context

**Strategic Architecture: Flux + Temporal + Consensus Hybrid Approach**

This file provides setup instructions for the complete infrastructure control plane deployment.

**North Star Vision**: Establish a reference implementation for autonomous, self-organizing infrastructure management.

**Current Status**: Documenting deployment procedures for production environments.

**Strategic Plan**: See [docs/STRATEGIC-ARCHITECTURE.md](docs/STRATEGIC-ARCHITECTURE.md) for comprehensive roadmap.

---

# GitOps Infra Control Plane - Setup Guide

This guide provides step-by-step instructions to set up the complete GitOps Infra Control Plane.

## Prerequisites

### Required Tools

- `kubectl` v1.28+
- `flux` CLI v2.2+
- AWS CLI v2.0+
- Azure CLI v2.0+
- Google Cloud CLI v400.0+
- `git` v2.30+

### Cloud Provider Accounts

- AWS account with EKS, EC2, VPC, IAM permissions
- Azure subscription with AKS, VNet permissions  
- Google Cloud project with GKE, Compute Network permissions

### Hub Cluster

- Kubernetes cluster (EKS/AKS/GKE) to serve as the control plane
- Cluster admin access

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/lloydchang/gitops-infra-control-plane.git
cd gitops-infra-control-plane
```

### 2. Install Flux on Hub Cluster

```bash
flux bootstrap git \
  --url=ssh://git@github.com/lloydchang/gitops-infra-control-plane \
  --branch=main \
  --path=core/operators/flux \
  --private-key-file=~/.ssh/id_rsa
```

### 3. Configure Cloud Provider Identities

#### AWS - IAM Roles for Service Accounts (IRSA)

```bash
# Replace ACCOUNT_ID, REGION, CLUSTER_ID with your values
export AWS_ACCOUNT_ID="123456789012"
export AWS_REGION="us-west-2"
export EKS_CLUSTER_NAME="gitops-management-cluster"

# Get OIDC provider
OIDC_PROVIDER=$(aws eks describe-cluster --name $EKS_CLUSTER_NAME --query "cluster.identity.oidc.issuer" --output text | sed -e "s/^https:\/\///")

# Create IAM roles for Crossplane and CAPI controllers (IRSA)
# See core/operators/identity/irsa-setup.yaml for detailed configuration
```

#### Azure - Workload Identity

```bash
# Set Azure subscription and resource group
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="gitops-rg"

# Create managed identity for Crossplane and CAPZ controllers
# See core/operators/identity/azure-workload-identity.yaml
```

#### Google Cloud - Workload Identity

```bash
# Set project ID
export GCP_PROJECT_ID="your-project-id"

# Configure workload identity for Crossplane and CAPG controllers
# See core/operators/identity/gcp-workload-identity.yaml
```

### 4. Update Configuration Files

Replace placeholder values in the following files:

- `core/operators/identity/irsa-setup.yaml` - Update `ACCOUNT_ID`, `REGION`, `CLUSTER_ID`
- `core/operators/identity/azure-workload-identity.yaml` - Update `SUBSCRIPTION_ID`, `RESOURCE_GROUP`
- `core/operators/identity/gcp-workload-identity.yaml` - Update `PROJECT_ID`
- `core/operators/capi/infrastructure-providers.yaml` - Update workload identity annotations
- `core/operators/capi/clusterclass-aws.yaml` - Update `region`, `sshKeyName`
- `core/operators/capi/clusterclass-azure.yaml` - Update `subscriptionID`, `resourceGroup`
- `core/operators/capi/clusterclass-gcp.yaml` - Update `project`, `region`
See [docs/operator-inputs.md](docs/operator-inputs.md) for a consolidated checklist.
See [docs/EXECUTION-CHECKLIST.md](docs/EXECUTION-CHECKLIST.md) for the apply/validation sequence.

### 5. Commit and Push

```bash
git add .
git commit -m "Initial GitOps infrastructure setup"
git push origin main
```

### 6. Verify Deployment

```bash
# Check Flux status
flux get kustomizations

# Check controller pods
kubectl get pods -n crossplane-system
kubectl get pods -n capi-system

# Check infrastructure resources
kubectl get managed -A
kubectl get clusters -A
```

## Detailed Configuration

### Crossplane Providers

Crossplane providers manage cloud resources behind XRDs:

- AWS: `provider-aws`
- Azure: `provider-azure`
- GCP: `provider-gcp`

### Cluster API Providers

CAPI providers manage spoke cluster lifecycle:

- AWS: CAPA
- Azure: CAPZ
- GCP: CAPG

## Infrastructure Resources

### Network Layer (1-network/)

- XNetwork claims mapped to provider resources by Crossplane

### Cluster Layer (2-clusters/)

- **AWS**: EKS Cluster, Node Groups, IAM Roles
- **Azure**: AKS Cluster, Managed Identities, Agent Pools
- **GCP**: GKE Cluster, Node Pools, Service Accounts

### Workload Layer (3-workloads/)

- Sample applications (Nginx, Redis)
- Monitoring stack (Prometheus, Grafana)
- Ingress configuration

## Validation

### Run Drift Test

```bash
# Execute the drift test to validate continuous reconciliation
./core/automation/testing/drift-test.sh
```

### Manual Verification

```bash
# Check resource status
kubectl get vpc -n flux-system
kubectl get cluster -n flux-system

# Test drift by manually modifying resources
aws ec2 delete-subnet --subnet-id <subnet-id>

# Watch reconciliation
kubectl logs -n ack-system deployment/ack-ec2-controller -f
```

## Troubleshooting

### Common Issues

1. **Controllers not starting**
   - Check IAM permissions and service account annotations
   - Verify cloud provider credentials
   - Review controller logs

2. **Resources not provisioning**
   - Check Flux reconciliation status
   - Verify CRD installation
   - Review resource specifications

3. **Drift not detected**
   - Ensure controllers are running
   - Check cloud provider API access
   - Verify resource references

### Debug Commands

```bash
# Flux status
flux get kustomizations --watch

# Controller logs
kubectl logs -n ack-system deployment/ack-eks-controller
kubectl logs -n azureserviceoperator-system deployment/azureserviceoperator-controller-manager
kubectl logs -n cnrm-system deployment/cnrm-controller-manager

# Resource status
kubectl describe vpc gitops-vpc -n flux-system
kubectl describe cluster gitops-eks-cluster -n flux-system
```

## Security Considerations

- **No Static Secrets**: All authentication uses workload identity
- **Principle of Least Privilege**: Service accounts have minimal required permissions
- **Git as Source of Truth**: All infrastructure state is version controlled
- **Continuous Reconciliation**: Drift is automatically detected and repaired

## Next Steps

1. Customize infrastructure resources for your requirements
2. Add additional cloud services and controllers
3. Implement monitoring and alerting
4. Set up GitOps workflows for application deployment
5. Configure backup and disaster recovery

## Support

For issues and questions:

- Check the [implementation plan](./implementation_plan.md)
- Review the drift test documentation in [core/automation/testing/README.md](core/automation/testing/README.md)
- Examine controller logs and Flux status
- Verify cloud provider permissions and configurations
