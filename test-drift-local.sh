#!/bin/bash
# Local drift test using LocalStack and manual reconciliation simulation

set -euxo pipefail

# Configuration
AWS_REGION="us-west-2"
VPC_NAME="main-vpc"
SUBNET_NAME="main-subnet"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Setup AWS CLI for LocalStack
setup_localstack() {
    print_status "Setting up LocalStack connection..."
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=$AWS_REGION
    export AWS_ENDPOINT_URL=http://localhost:4566
    
    # Start port-forwarding to LocalStack
    print_status "Starting port-forward to LocalStack..."
    kubectl port-forward -n localstack svc/localstack 4566:4566 >/dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    sleep 3
    
    # Test connection
    if aws --endpoint-url=$AWS_ENDPOINT_URL ec2 describe-regions >/dev/null 2>&1; then
        print_status "✅ LocalStack connection successful"
    else
        print_error "❌ Cannot connect to LocalStack"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        exit 1
    fi
}

# Create test infrastructure
create_infrastructure() {
    print_status "Creating test infrastructure..."
    
    # Create VPC
    VPC_ID=$(aws --endpoint-url=$AWS_ENDPOINT_URL ec2 create-vpc \
        --cidr-block 10.0.0.0/16 \
        --query 'Vpc.VpcId' --output text)
    
    print_status "✅ Created VPC: $VPC_ID"
    
    # Create subnet
    SUBNET_ID=$(aws --endpoint-url=$AWS_ENDPOINT_URL ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --query 'Subnet.SubnetId' --output text)
    
    print_status "✅ Created Subnet: $SUBNET_ID"
    
    echo $VPC_ID > /tmp/vpc_id.txt
    echo $SUBNET_ID > /tmp/subnet_id.txt
}

# Test drift detection and manual reconciliation
test_drift() {
    print_status "Testing drift detection and reconciliation..."
    
    VPC_ID=$(cat /tmp/vpc_id.txt)
    SUBNET_ID=$(cat /tmp/subnet_id.txt)
    
    # Verify infrastructure exists
    if aws --endpoint-url=$AWS_ENDPOINT_URL ec2 describe-vpcs --vpc-ids $VPC_ID >/dev/null 2>&1; then
        print_status "✅ VPC exists"
    else
        print_error "❌ VPC not found"
        return 1
    fi
    
    if aws --endpoint-url=$AWS_ENDPOINT_URL ec2 describe-subnets --subnet-ids $SUBNET_ID >/dev/null 2>&1; then
        print_status "✅ Subnet exists"
    else
        print_error "❌ Subnet not found"
        return 1
    fi
    
    # Introduce drift - delete subnet
    print_status "🔄 Introducing drift - deleting subnet..."
    aws --endpoint-url=$AWS_ENDPOINT_URL ec2 delete-subnet --subnet-id $SUBNET_ID
    print_status "✅ Subnet deleted - drift introduced"
    
    # Verify subnet is gone
    if ! aws --endpoint-url=$AWS_ENDPOINT_URL ec2 describe-subnets --subnet-ids $SUBNET_ID >/dev/null 2>&1; then
        print_status "✅ Drift confirmed - subnet no longer exists"
    else
        print_error "❌ Subnet still exists - drift test failed"
        return 1
    fi
    
    # Simulate GitOps reconciliation - recreate subnet
    print_status "🔄 Simulating GitOps reconciliation - recreating subnet..."
    NEW_SUBNET_ID=$(aws --endpoint-url=$AWS_ENDPOINT_URL ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --query 'Subnet.SubnetId' --output text)
    
    print_status "✅ Subnet recreated: $NEW_SUBNET_ID"
    
    # Verify reconciliation
    if aws --endpoint-url=$AWS_ENDPOINT_URL ec2 describe-subnets --subnet-ids $NEW_SUBNET_ID >/dev/null 2>&1; then
        print_status "✅ Drift reconciliation successful!"
        return 0
    else
        print_error "❌ Reconciliation failed"
        return 1
    fi
}

# Main execution
echo "🚀 Local Drift Test with LocalStack"
echo "===================================="

setup_localstack
create_infrastructure
test_drift

echo ""
echo "🎉 Local drift test completed successfully!"
echo "✅ Infrastructure created"
echo "✅ Drift introduced"
echo "✅ Reconciliation simulated"
echo "✅ Infrastructure restored"
