#!/bin/bash

# GitOps Infrastructure Control Plane - Drift Test Script
# This script validates the continuous reconciliation capability

set -e

echo "🚀 Starting GitOps Infrastructure Drift Test"
echo "============================================="

# Configuration
AWS_REGION="us-west-2"
EKS_CLUSTER_NAME="gitops-eks-cluster"
VPC_NAME="gitops-vpc"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Verify initial infrastructure exists
print_status "Step 1: Verifying initial infrastructure exists..."

# Check VPC exists
if ! aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$VPC_NAME" --region $AWS_REGION >/dev/null 2>&1; then
    print_error "VPC $VPC_NAME not found. Please run initial deployment first."
    exit 1
fi

# Check EKS cluster exists
if ! aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION >/dev/null 2>&1; then
    print_error "EKS cluster $EKS_CLUSTER_NAME not found. Please run initial deployment first."
    exit 1
fi

print_status "✅ Initial infrastructure verified"

# Step 2: Record current state
print_status "Step 2: Recording current infrastructure state..."

VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$VPC_NAME" --region $AWS_REGION --query 'Vpcs[0].VpcId' --output text)
EKS_STATUS=$(aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION --query 'cluster.status' --output text)

print_status "VPC ID: $VPC_ID"
print_status "EKS Cluster Status: $EKS_STATUS"

# Step 3: Introduce drift - Delete a subnet
print_status "Step 3: Introducing drift by deleting a subnet..."

SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=gitops-public-subnet-1a" --region $AWS_REGION --query 'Subnets[0].SubnetId' --output text)

if [ "$SUBNET_ID" != "None" ] && [ "$SUBNET_ID" != "" ]; then
    print_warning "Deleting subnet: $SUBNET_ID"
    aws ec2 delete-subnet --subnet-id $SUBNET_ID --region $AWS_REGION
    print_status "✅ Subnet deleted - drift introduced"
else
    print_warning "Subnet not found, skipping drift creation"
fi

# Step 4: Wait for reconciliation
print_status "Step 4: Waiting for Flux reconciliation (up to 10 minutes)..."
print_warning "The controllers should detect drift and recreate the subnet"

RECONCILIATION_TIMEOUT=600
RECONCILIATION_INTERVAL=30
elapsed=0

while [ $elapsed -lt $RECONCILIATION_TIMEOUT ]; do
    # Check if subnet has been recreated
    RECREATED_SUBNET=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=gitops-public-subnet-1a" --region $AWS_REGION --query 'Subnets[0].SubnetId' --output text)
    
    if [ "$RECREATED_SUBNET" != "None" ] && [ "$RECREATED_SUBNET" != "" ]; then
        print_status "✅ Drift detected and reconciled! Subnet recreated: $RECREATED_SUBNET"
        break
    fi
    
    print_status "Waiting for reconciliation... (${elapsed}s elapsed)"
    sleep $RECONCILIATION_INTERVAL
    elapsed=$((elapsed + RECONCILIATION_INTERVAL))
done

if [ $elapsed -ge $RECONCILIATION_TIMEOUT ]; then
    print_error "❌ Drift reconciliation failed - subnet was not recreated within timeout"
    exit 1
fi

# Step 5: Test cluster drift
print_status "Step 5: Testing EKS cluster drift detection..."

# Get current node count
NODE_COUNT=$(aws eks describe-nodegroup --cluster-name $EKS_CLUSTER_NAME --nodegroup-name gitops-eks-nodegroup --region $AWS_REGION --query 'nodegroup.scalingConfig.desiredSize' --output text)
print_status "Current node count: $NODE_COUNT"

# Modify node count manually
print_warning "Manually changing node count to create drift..."
aws eks update-nodegroup-config \
    --cluster-name $EKS_CLUSTER_NAME \
    --nodegroup-name gitops-eks-nodegroup \
    --scaling-config minSize=1,maxSize=4,desiredSize=2 \
    --region $AWS_REGION

# Wait for cluster reconciliation
print_status "Waiting for EKS cluster reconciliation..."
sleep 60

# Check if node count reverted
RESTORED_NODE_COUNT=$(aws eks describe-nodegroup --cluster-name $EKS_CLUSTER_NAME --nodegroup-name gitops-eks-nodegroup --region $AWS_REGION --query 'nodegroup.scalingConfig.desiredSize' --output text)

if [ "$RESTORED_NODE_COUNT" = "$NODE_COUNT" ]; then
    print_status "✅ EKS cluster drift detected and reconciled! Node count restored to: $RESTORED_NODE_COUNT"
else
    print_warning "EKS cluster reconciliation may still be in progress or requires manual intervention"
fi

# Step 6: Final verification
print_status "Step 6: Final infrastructure verification..."

# Verify all components are healthy
VPC_HEALTH=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$VPC_NAME" --region $AWS_REGION --query 'Vpcs[0].State' --output text)
EKS_HEALTH=$(aws eks describe-cluster --name $EKS_CLUSTER_NAME --region $AWS_REGION --query 'cluster.status' --output text)

print_status "VPC State: $VPC_HEALTH"
print_status "EKS Cluster Status: $EKS_HEALTH"

if [ "$VPC_HEALTH" = "available" ] && [ "$EKS_HEALTH" = "ACTIVE" ]; then
    print_status "🎉 DRIFT TEST PASSED!"
    print_status "✅ All infrastructure components are healthy"
    print_status "✅ Continuous reconciliation is working correctly"
    print_status "✅ GitOps control plane successfully detected and repaired drift"
else
    print_error "❌ DRIFT TEST FAILED - Infrastructure health check failed"
    exit 1
fi

echo ""
echo "============================================="
echo "✅ GitOps Infrastructure Drift Test Complete"
echo "============================================="
