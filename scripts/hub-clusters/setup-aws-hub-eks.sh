#!/bin/bash

# Setup AWS EKS Hub Cluster for GitOps Control Plane
# This script creates an EKS cluster that serves as the hub for multi-cloud GitOps

set -euo pipefail

# Configuration
CLUSTER_NAME="${CLUSTER_NAME:-gitops-hub-eks}"
REGION="${AWS_REGION:-us-east-1}"
NODE_COUNT="${NODE_COUNT:-3}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"

echo "🚀 Setting up AWS EKS Hub Cluster: $CLUSTER_NAME"
echo "📍 Region: $REGION"
echo "🖥️  Nodes: $NODE_COUNT x $INSTANCE_TYPE"

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not installed"; exit 1; }
command -v eksctl >/dev/null 2>&1 || { echo "❌ eksctl not installed"; exit 1; }

# Create EKS cluster
echo "📦 Creating EKS cluster..."
eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$REGION" \
  --nodegroup-name "gitops-nodes" \
  --node-type "$INSTANCE_TYPE" \
  --nodes "$NODE_COUNT" \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed \
  --with-oidc \
  --ssh-access \
  --ssh-public-key "$(ssh-keygen -y -f ~/.ssh/id_rsa)" \
  --tags "Environment=gitops-hub,Purpose=multi-cloud-control-plane"

# Enable IAM roles for service accounts (IRSA)
echo "🔐 Enabling IAM Roles for Service Accounts..."
eksctl utils associate-iam-oidc-provider --region "$REGION" --cluster "$CLUSTER_NAME" --approve

# Create IAM policy for ACK controllers
echo "📋 Creating IAM policy for ACK controllers..."
cat > ack-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "eks:*",
                "iam:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF

aws iam create-policy \
  --policy-name GitOpsACKPolicy \
  --policy-document file://ack-policy.json \
  --region "$REGION" || echo "Policy may already exist"

# Get cluster info
echo "🔍 Getting cluster information..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Verify cluster
echo "✅ Verifying cluster..."
kubectl get nodes
kubectl get pods -A | head -10

echo ""
echo "🎉 AWS EKS Hub Cluster '$CLUSTER_NAME' is ready!"
echo ""
echo "Next steps:"
echo "1. Run scripts/bootstrap.sh to install Flux and controllers"
echo "2. Configure spoke clusters (AKS, GKE) to connect to this hub"
echo "3. Deploy multi-cloud workloads via GitOps DAG"
echo ""
echo "Cluster details:"
echo "- Name: $CLUSTER_NAME"
echo "- Region: $REGION"
echo "- API Server: $(kubectl cluster-info | grep 'Kubernetes control plane' | awk '{print $7}')"
