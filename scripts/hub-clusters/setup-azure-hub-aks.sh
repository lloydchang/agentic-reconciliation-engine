#!/bin/bash

# Setup Azure AKS Hub Cluster for GitOps Control Plane
# This script creates an AKS cluster that serves as the hub for multi-cloud GitOps

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

# Check prerequisites
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI not installed"; exit 1; }

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
echo "1. Run bootstrap.sh to install Flux and controllers"
echo "2. Configure spoke clusters (EKS, GKE) to connect to this hub"
echo "3. Deploy multi-cloud workloads via GitOps DAG"
echo ""
echo "Cluster details:"
echo "- Name: $CLUSTER_NAME"
echo "- Resource Group: $RESOURCE_GROUP"
echo "- Location: $LOCATION"
echo "- API Server: $(kubectl cluster-info | grep 'Kubernetes control plane' | awk '{print $7}')"
