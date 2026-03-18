#!/bin/bash

# Setup GCP GKE Hub Cluster for GitOps Control Plane
# This script creates a GKE cluster that serves as the hub for multi-cloud GitOps
#
# Tooling Choice Summary:
# - Uses Google Cloud CLI (gcloud) (industry-standard for GKE) instead of Terraform Blueprints for cluster bootstrap
# - Reference: https://docs.cloud.google.com/kubernetes-engine/docs/how-to/creating-a-zonal-cluster
# - Aligns with GitOps migration strategy: imperative setup for initial infrastructure,
#   then Flux + KCC for declarative management of workloads and cross-cloud resources
# - Avoids IaC lock-in during transition period, enables gradual migration from legacy IaC
CLUSTER_NAME="${CLUSTER_NAME:-gitops-hub-gke}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-us-central1-c}"
NODE_COUNT="${NODE_COUNT:-3}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-medium}"

echo "🚀 Setting up GCP GKE Hub Cluster: $CLUSTER_NAME"
echo "📍 Project: $PROJECT_ID"
echo "📍 Region: $REGION"
echo "🖥️  Nodes: $NODE_COUNT x $MACHINE_TYPE"

# Check prerequisites
command -v gcloud >/dev/null 2>&1 || { echo "❌ Google Cloud SDK not installed"; exit 1; }

# Authenticate if needed
echo "🔐 Ensuring authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" || {
    echo "Please run: gcloud auth login"
    exit 1
}

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable container.googleapis.com
gcloud services enable iamcredentials.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

# Create GKE cluster
echo "📦 Creating GKE cluster..."
gcloud container clusters create "$CLUSTER_NAME" \
  --region "$REGION" \
  --num-nodes "$NODE_COUNT" \
  --machine-type "$MACHINE_TYPE" \
  --workload-pool="$PROJECT_ID.svc.id.goog" \
  --enable-identity-service \
  --labels environment=gitops-hub,purpose=multi-cloud-control-plane

# Get cluster credentials
echo "🔑 Getting cluster credentials..."
gcloud container clusters get-credentials "$CLUSTER_NAME" --region "$REGION"

# Create service account for KCC
echo "🔐 Creating service account for KCC controllers..."
SA_NAME="gitops-kcc-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create "$SA_NAME" \
  --display-name "GitOps KCC Service Account" \
  --description "Service account for Kubernetes Config Connector"

# Grant necessary permissions
echo "📋 Granting permissions to service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:$SA_EMAIL" \
  --role "roles/editor"

# Create workload identity binding
echo "🔗 Creating workload identity binding..."
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role "roles/iam.workloadIdentityUser" \
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[cnrm-system/cnrm-controller-manager]"

# Verify cluster
echo "✅ Verifying cluster..."
kubectl get nodes
kubectl get pods -A | head -10

echo ""
echo "🎉 GCP GKE Hub Cluster '$CLUSTER_NAME' is ready!"
echo ""
echo "Next steps:"
echo "1. Run core/automation/scripts/deploy-gitops-infrastructure.sh to install Flux and controllers"
echo "2. Configure spoke clusters (EKS, AKS) to connect to this hub"
echo "3. Deploy multi-cloud workloads via GitOps DAG"
echo ""
echo "Cluster details:"
echo "- Name: $CLUSTER_NAME"
echo "- Project: $PROJECT_ID"
echo "- Region: $REGION"
echo "- API Server: $(kubectl cluster-info | grep 'Kubernetes control plane' | awk '{print $7}')"
echo ""
echo "Service Account: $SA_EMAIL"
