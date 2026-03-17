#!/bin/bash

# Setup Azure AKS Hub Cluster for GitOps Control Plane
# This script creates an AKS cluster that serves as the hub for multi-cloud GitOps
#
# INDUSTRY STANDARD: Uses Azure CLI (az aks) - Microsoft's official command-line tool for AKS
# Reference: https://learn.microsoft.com/en-us/cli/azure/aks
# Azure CLI is the standard and most widely adopted tool for AKS cluster management
#
# Tooling Choice Summary:
# - Uses Azure CLI (az aks) (industry-standard for AKS) instead of Bicep for cluster bootstrap
# - Reference: https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-deploy-cli
# - Aligns with GitOps migration strategy: imperative setup for initial infrastructure,
#   then Flux + ASO for declarative management of workloads and cross-cloud resources
# - Avoids IaC lock-in during transition period, enables gradual migration from legacy IaC

set -euo pipefail

# Configuration
CLUSTER_NAME="${CLUSTER_NAME:-gitops-hub-aks}"
RESOURCE_GROUP="${RESOURCE_GROUP:-gitops-hub-rg}"
LOCATION="${LOCATION:-eastus}"
NODE_COUNT="${NODE_COUNT:-3}"
VM_SIZE="${VM_SIZE:-Standard_B2s}"

echo "🚀 Setting up Azure AKS Hub Cluster: $CLUSTER_NAME"
echo "📍 Location: $LOCATION"
echo "🖥️  Nodes: $NODE_COUNT x $VM_SIZE"

# Using Azure CLI (az), the industry-standard command-line interface for managing Azure resources and AKS clusters.
# Azure CLI provides comprehensive support for AKS operations and integrates seamlessly with Azure services.

# Login to Azure (interactive)
echo "🔐 Please login to Azure..."
az login --use-device-code

# Set subscription if provided
if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
    az account set --subscription "$AZURE_SUBSCRIPTION_ID"
fi

# Create resource group
echo "📦 Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags Environment=gitops-hub Purpose=multi-cloud-control-plane

# Create AKS cluster
echo "📦 Creating AKS cluster..."
az aks create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CLUSTER_NAME" \
  --node-count "$NODE_COUNT" \
  --node-vm-size "$VM_SIZE" \
  --enable-managed-identity \
  --enable-oidc-issuer \
  --enable-workload-identity \
  --generate-ssh-keys \
  --tags Environment=gitops-hub Purpose=multi-cloud-control-plane

# Get cluster credentials
echo "🔑 Getting cluster credentials..."
az aks get-credentials \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CLUSTER_NAME" \
  --overwrite-existing

# Create Azure AD application for ASO
echo "🔐 Creating Azure AD application for ASO controllers..."
APP_NAME="gitops-aso-app"
az ad app create --display-name "$APP_NAME" --query appId -o tsv

# Create service principal
SP_NAME="gitops-aso-sp"
az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role Contributor \
  --scopes "/subscriptions/$(az account show --query id -o tsv)" \
  --query "{clientId:appId,clientSecret:password,tenantId:tenant}"

# Enable Azure Workload Identity
echo "🔄 Enabling Azure Workload Identity..."
az aks update \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CLUSTER_NAME" \
  --enable-workload-identity

# Verify cluster
echo "✅ Verifying cluster..."
kubectl get nodes
kubectl get pods -A | head -10

echo ""
echo "🎉 Azure AKS Hub Cluster '$CLUSTER_NAME' is ready!"
echo ""
echo "Next steps:"
echo "1. Run core/core/automation/ci-cd/scripts/deploy-gitops-infrastructure.sh to install Flux and controllers"
echo "2. Configure spoke clusters (EKS, GKE) to connect to this hub"
echo "3. Deploy multi-cloud workloads via GitOps DAG"
echo ""
echo "Cluster details:"
echo "- Name: $CLUSTER_NAME"
echo "- Resource Group: $RESOURCE_GROUP"
echo "- Location: $LOCATION"
echo "- API Server: $(kubectl cluster-info | grep 'Kubernetes control plane' | awk '{print $7}')"
