#!/bin/bash

# Dependency DAG Validation Test
# Validates that all infrastructure resources have proper dependsOn annotations

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[DEPS-TEST]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DEPS-TEST]${NC} $1"
}

print_error() {
    echo -e "${RED}[DEPS-TEST]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Test AWS network dependencies
test_aws_network_deps() {
    print_header "Testing AWS Network Dependencies"
    
    local aws_network_dir="infrastructure/tenants/1-network"
    local errors=0
    
    # Check VPC has order 1
    if grep -q "dependsOn.fluxcd.io/order: \"1\"" "$aws_network_dir/aws-vpc.yaml"; then
        print_status "✅ AWS VPC has correct order (1)"
    else
        print_error "❌ AWS VPC missing order annotation"
        ((errors++))
    fi
    
    # Check InternetGateway depends on VPC
    if grep -q "dependsOn.fluxcd.io/vpc: \"gitops-vpc\"" "$aws_network_dir/aws-vpc.yaml"; then
        print_status "✅ AWS InternetGateway depends on VPC"
    else
        print_error "❌ AWS InternetGateway missing VPC dependency"
        ((errors++))
    fi
    
    # Check Subnets depend on VPC
    if grep -q "dependsOn.fluxcd.io/vpc: \"gitops-vpc\"" "$aws_network_dir/aws-subnets.yaml"; then
        print_status "✅ AWS Subnets depend on VPC"
    else
        print_error "❌ AWS Subnets missing VPC dependency"
        ((errors++))
    fi
    
    # Check RouteTable depends on VPC and IGW
    if grep -q "dependsOn.fluxcd.io/vpc: \"gitops-vpc\"" "$aws_network_dir/aws-subnets.yaml" && \
       grep -q "dependsOn.fluxcd.io/igw: \"gitops-igw\"" "$aws_network_dir/aws-subnets.yaml"; then
        print_status "✅ AWS RouteTable depends on VPC and IGW"
    else
        print_error "❌ AWS RouteTable missing dependencies"
        ((errors++))
    fi
    
    # Check RouteTableAssociations depend on RouteTable and Subnets
    if grep -q "dependsOn.fluxcd.io/route-table: \"gitops-public-rt\"" "$aws_network_dir/aws-subnets.yaml"; then
        print_status "✅ AWS RouteTableAssociations depend on RouteTable"
    else
        print_error "❌ AWS RouteTableAssociations missing dependencies"
        ((errors++))
    fi
    
    return $errors
}

# Test AWS cluster dependencies
test_aws_cluster_deps() {
    print_header "Testing AWS Cluster Dependencies"
    
    local aws_cluster_dir="infrastructure/tenants/2-clusters"
    local errors=0
    
    # Check IAM Role has order 1
    if grep -q "dependsOn.fluxcd.io/order: \"1\"" "$aws_cluster_dir/aws-eks-cluster.yaml"; then
        print_status "✅ AWS IAM Role has correct order (1)"
    else
        print_error "❌ AWS IAM Role missing order annotation"
        ((errors++))
    fi
    
    # Check IAM Policy depends on Role
    if grep -q "dependsOn.fluxcd.io/role: \"eks-cluster-role\"" "$aws_cluster_dir/aws-eks-cluster.yaml"; then
        print_status "✅ AWS IAM Policy depends on Role"
    else
        print_error "❌ AWS IAM Policy missing Role dependency"
        ((errors++))
    fi
    
    # Check RolePolicyAttachment depends on Role and Policy
    if grep -q "dependsOn.fluxcd.io/role: \"eks-cluster-role\"" "$aws_cluster_dir/aws-eks-cluster.yaml" && \
       grep -q "dependsOn.fluxcd.io/policy: \"eks-cluster-policy\"" "$aws_cluster_dir/aws-eks-cluster.yaml"; then
        print_status "✅ AWS RolePolicyAttachment depends on Role and Policy"
    else
        print_error "❌ AWS RolePolicyAttachment missing dependencies"
        ((errors++))
    fi
    
    # Check EKS Cluster depends on IAM Role and Subnets
    if grep -q "dependsOn.fluxcd.io/iam-role: \"eks-cluster-role\"" "$aws_cluster_dir/aws-eks-cluster.yaml" && \
       grep -q "dependsOn.fluxcd.io/vpc: \"gitops-vpc\"" "$aws_cluster_dir/aws-eks-cluster.yaml"; then
        print_status "✅ AWS EKS Cluster depends on IAM Role and VPC"
    else
        print_error "❌ AWS EKS Cluster missing dependencies"
        ((errors++))
    fi
    
    # Check EKS Nodegroup depends on Cluster
    if grep -q "dependsOn.fluxcd.io/cluster: \"gitops-eks-cluster\"" "$aws_cluster_dir/aws-eks-cluster.yaml"; then
        print_status "✅ AWS EKS Nodegroup depends on Cluster"
    else
        print_error "❌ AWS EKS Nodegroup missing Cluster dependency"
        ((errors++))
    fi
    
    return $errors
}

# Test Azure dependencies
test_azure_deps() {
    print_header "Testing Azure Dependencies"
    
    local azure_network_dir="infrastructure/tenants/1-network"
    local azure_cluster_dir="infrastructure/tenants/2-clusters"
    local errors=0
    
    # Check ResourceGroup has order 1
    if grep -q "dependsOn.fluxcd.io/order: \"1\"" "$azure_network_dir/azure-vnet.yaml"; then
        print_status "✅ Azure ResourceGroup has correct order (1)"
    else
        print_error "❌ Azure ResourceGroup missing order annotation"
        ((errors++))
    fi
    
    # Check VirtualNetwork depends on ResourceGroup
    if grep -q "dependsOn.fluxcd.io/resource-group: \"gitops-resource-group\"" "$azure_network_dir/azure-vnet.yaml"; then
        print_status "✅ Azure VirtualNetwork depends on ResourceGroup"
    else
        print_error "❌ Azure VirtualNetwork missing ResourceGroup dependency"
        ((errors++))
    fi
    
    # Check ManagedIdentity depends on ResourceGroup
    if grep -q "dependsOn.fluxcd.io/resource-group: \"gitops-resource-group\"" "$azure_cluster_dir/azure-aks-cluster.yaml"; then
        print_status "✅ Azure ManagedIdentity depends on ResourceGroup"
    else
        print_error "❌ Azure ManagedIdentity missing ResourceGroup dependency"
        ((errors++))
    fi
    
    # Check AKS Cluster depends on ResourceGroup, Identity, and VNet
    if grep -q "dependsOn.fluxcd.io/resource-group: \"gitops-resource-group\"" "$azure_cluster_dir/azure-aks-cluster.yaml" && \
       grep -q "dependsOn.fluxcd.io/identity: \"gitops-aks-identity\"" "$azure_cluster_dir/azure-aks-cluster.yaml" && \
       grep -q "dependsOn.fluxcd.io/vnet: \"gitops-vnet\"" "$azure_cluster_dir/azure-aks-cluster.yaml"; then
        print_status "✅ Azure AKS Cluster depends on ResourceGroup, Identity, and VNet"
    else
        print_error "❌ Azure AKS Cluster missing dependencies"
        ((errors++))
    fi
    
    return $errors
}

# Test GCP dependencies
test_gcp_deps() {
    print_header "Testing GCP Dependencies"
    
    local gcp_network_dir="infrastructure/tenants/1-network"
    local gcp_cluster_dir="infrastructure/tenants/2-clusters"
    local errors=0
    
    # Check ComputeNetwork has order 1
    if grep -q "dependsOn.fluxcd.io/order: \"1\"" "$gcp_network_dir/gcp-network.yaml"; then
        print_status "✅ GCP ComputeNetwork has correct order (1)"
    else
        print_error "❌ GCP ComputeNetwork missing order annotation"
        ((errors++))
    fi
    
    # Check ComputeSubnets depend on Network
    if grep -q "dependsOn.fluxcd.io/network: \"gitops-network\"" "$gcp_network_dir/gcp-network.yaml"; then
        print_status "✅ GCP ComputeSubnets depend on Network"
    else
        print_error "❌ GCP ComputeSubnets missing Network dependency"
        ((errors++))
    fi
    
    # Check IAMServiceAccount has order 1
    if grep -q "dependsOn.fluxcd.io/order: \"1\"" "$gcp_cluster_dir/gcp-gke-cluster.yaml"; then
        print_status "✅ GCP IAMServiceAccount has correct order (1)"
    else
        print_error "❌ GCP IAMServiceAccount missing order annotation"
        ((errors++))
    fi
    
    # Check GKE Cluster depends on ServiceAccount and Network
    if grep -q "dependsOn.fluxcd.io/service-account: \"gke-node-sa\"" "$gcp_cluster_dir/gcp-gke-cluster.yaml" && \
       grep -q "dependsOn.fluxcd.io/network: \"gitops-network\"" "$gcp_cluster_dir/gcp-gke-cluster.yaml"; then
        print_status "✅ GCP GKE Cluster depends on ServiceAccount and Network"
    else
        print_error "❌ GCP GKE Cluster missing dependencies"
        ((errors++))
    fi
    
    # Check GKE NodePool depends on Cluster
    if grep -q "dependsOn.fluxcd.io/cluster: \"gitops-gke-cluster\"" "$gcp_cluster_dir/gcp-gke-cluster.yaml"; then
        print_status "✅ GCP GKE NodePool depends on Cluster"
    else
        print_error "❌ GCP GKE NodePool missing Cluster dependency"
        ((errors++))
    fi
    
    return $errors
}

# Test Flux Kustomization dependencies
test_flux_kustomization_deps() {
    print_header "Testing Flux Kustomization Dependencies"
    
    local flux_dir="control-plane/flux"
    local errors=0
    
    # Check network-infra has no dependencies (first)
    if ! awk '/name: network-infra/,/^---/' "$flux_dir/gotk-sync.yaml" | grep -q "dependsOn:"; then
        print_status "✅ network-infra has no dependencies (first in chain)"
    else
        print_error "❌ network-infra should not have dependencies"
        ((errors++))
    fi
    
    # Check cluster-infra depends on network-infra
    if grep -A 10 "name: cluster-infra" "$flux_dir/gotk-sync.yaml" | grep -q "dependsOn:" && \
       grep -A 10 "name: cluster-infra" "$flux_dir/gotk-sync.yaml" | grep -q "network-infra"; then
        print_status "✅ cluster-infra depends on network-infra"
    else
        print_error "❌ cluster-infra missing network-infra dependency"
        ((errors++))
    fi
    
    # Check workload-infra depends on cluster-infra
    if grep -A 10 "name: workload-infra" "$flux_dir/gotk-sync.yaml" | grep -q "dependsOn:" && \
       grep -A 10 "name: workload-infra" "$flux_dir/gotk-sync.yaml" | grep -q "cluster-infra"; then
        print_status "✅ workload-infra depends on cluster-infra"
    else
        print_error "❌ workload-infra missing cluster-infra dependency"
        ((errors++))
    fi
    
    # Check karmada-infra depends on workload-infra
    if grep -A 10 "name: karmada-infra" "$flux_dir/gotk-sync.yaml" | grep -q "dependsOn:" && \
       grep -A 10 "name: karmada-infra" "$flux_dir/gotk-sync.yaml" | grep -q "workload-infra"; then
        print_status "✅ karmada-infra depends on workload-infra"
    else
        print_error "❌ karmada-infra missing workload-infra dependency"
        ((errors++))
    fi
    
    return $errors
}

# Generate dependency DAG visualization
generate_dependency_dag() {
    print_header "Generating Dependency DAG Visualization"
    
    local dag_file="dependency-dag.md"
    
    cat > "$dag_file" << 'EOF'
# Infrastructure Dependency DAG

## Kustomization Level Dependencies
```
network-infra (1-network/)
    ↓ dependsOn
cluster-infra (2-clusters/)
    ↓ dependsOn
workload-infra (3-workloads/)
    ↓ dependsOn
karmada-infra (karmada/)
```

## Resource Level Dependencies

### AWS Dependencies
```
VPC (gitops-vpc) [order: 1]
    ↓ dependsOn
InternetGateway (gitops-igw) [order: 2]
    ↓ dependsOn
Subnets (gitops-*-subnet) [order: 3]
    ↓ dependsOn
RouteTable (gitops-public-rt) [order: 4]
    ↓ dependsOn
RouteTableAssociations (gitops-public-rta-*) [order: 5]

IAM Role (eks-cluster-role) [order: 1]
    ↓ dependsOn
IAM Policy (eks-cluster-policy) [order: 2]
    ↓ dependsOn
RolePolicyAttachment (eks-cluster-service-policy) [order: 3]
    ↓ dependsOn
EKS Cluster (gitops-eks-cluster) [order: 4]
    ↓ dependsOn
EKS Nodegroup (gitops-eks-nodegroup) [order: 5]
```

### Azure Dependencies
```
ResourceGroup (gitops-resource-group) [order: 1]
    ↓ dependsOn
VirtualNetwork (gitops-vnet) [order: 2]
    ↓ dependsOn
UserAssignedIdentity (gitops-aks-identity) [order: 1]
    ↓ dependsOn
AKS Cluster (gitops-aks-cluster) [order: 2]
```

### GCP Dependencies
```
ComputeNetwork (gitops-network) [order: 1]
    ↓ dependsOn
ComputeSubnets (gitops-subnet-*) [order: 2]
    ↓ dependsOn
IAMServiceAccount (gke-node-sa) [order: 1]
    ↓ dependsOn
GKE Cluster (gitops-gke-cluster) [order: 2]
    ↓ dependsOn
GKE NodePool (gitops-gke-nodepool) [order: 3]
```

## Benefits
- ✅ Explicit resource ordering
- ✅ Parallel execution where possible
- ✅ Failure isolation
- ✅ Clear dependency visualization
- ✅ Reliable infrastructure deployment
EOF
    
    print_status "✅ Dependency DAG visualization generated: $dag_file"
}

# Main execution
main() {
    print_header "Dependency DAG Validation Test"
    
    local total_errors=0
    
    # Run all dependency tests
    test_aws_network_deps
    ((total_errors += $?))
    
    test_aws_cluster_deps
    ((total_errors += $?))
    
    test_azure_deps
    ((total_errors += $?))
    
    test_gcp_deps
    ((total_errors += $?))
    
    test_flux_kustomization_deps
    ((total_errors += $?))
    
    # Generate DAG visualization
    generate_dependency_dag
    
    # Summary
    print_header "Dependency Validation Summary"
    
    if [ $total_errors -eq 0 ]; then
        print_status "🎉 All dependency tests passed!"
        print_status "✅ Infrastructure DAG is properly configured"
        print_status "✅ All resources have correct dependsOn annotations"
        echo ""
        print_status "📊 Generated dependency-dag.md for visualization"
        exit 0
    else
        print_error "❌ $total_errors dependency validation errors found"
        print_warning "⚠️  Please fix missing or incorrect dependsOn annotations"
        exit 1
    fi
}

# Run main function
main "$@"
