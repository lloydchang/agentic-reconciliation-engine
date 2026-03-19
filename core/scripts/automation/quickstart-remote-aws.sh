#!/bin/bash
# Agentic Reconciliation Engine - Quick Start for Remote AWS Production
# Repository setup and initial onboarding for AWS EKS production deployments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
RESET='\033[0m'

# Script information
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Source the deploy_ai_agent_skills function
if [[ -f "$SCRIPT_DIR/deploy_ai_agent_skills.sh" ]]; then
    source "$SCRIPT_DIR/deploy_ai_agent_skills.sh"
else
    echo "Warning: deploy_ai_agent_skills.sh not found"
fi

# Global counters for validation
ERRORS=0
WARNINGS=0

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Validation functions from prerequisites.sh
pass() { echo -e "  ${GREEN}✓${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}!${RESET} $*"; WARNINGS=$((WARNINGS + 1)); }
info() { echo -e "  ${CYAN}→${RESET} $*"; }

# Environment-specific validation for Remote AWS
run_aws_production_validation() {
    ERRORS=0
    WARNINGS=0

    echo ""
    echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}║  agentic-reconciliation-engine — AWS Production Validation ║${RESET}"
    echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # 1. AWS prerequisites
    echo -e "${BOLD}[1/8] Checking AWS prerequisites${RESET}"

    # Check AWS CLI
    if command -v aws &>/dev/null; then
        local aws_version=$(aws --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        pass "AWS CLI available (${aws_version})"
    else
        fail "AWS CLI not found (required for AWS operations)"
    fi

    # Check kubectl
    if command -v kubectl &>/dev/null; then
        local kube_version=$(kubectl version --client --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        pass "kubectl available (${kube_version})"
    else
        fail "kubectl not found (required for EKS)"
    fi

    # Check AWS authentication
    if aws sts get-caller-identity &>/dev/null; then
        local account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
        local user=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null | awk -F'/' '{print $NF}')
        pass "AWS authenticated - Account: ${account}, User: ${user}"
    else
        fail "AWS authentication failed - run: aws configure"
    fi

    # Check if EKS cluster exists
    local cluster_name=${EKS_CLUSTER_NAME:-agentic-cluster}
    if aws eks describe-cluster --name "$cluster_name" --region "$AWS_DEFAULT_REGION" &>/dev/null; then
        pass "EKS cluster '$cluster_name' exists"
    else
        warn "EKS cluster '$cluster_name' not found - will be created"
    fi

    echo ""

    # 2. Standard CLI tools
    echo -e "${BOLD}[2/8] Checking required CLI tools${RESET}"

    check_tool() {
        local tool=$1 min_version=$2 version_flag="${3:---version}"
        if command -v "$tool" &>/dev/null; then
            local ver=""
            if "$tool" $version_flag >/dev/null 2>&1; then
                ver=$("$tool" $version_flag 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
            fi
            pass "${tool} ${ver}"
        else
            fail "${tool} not found (required)"
        fi
    }

    check_tool_optional() {
        local tool=$1
        if command -v "$tool" &>/dev/null; then
            pass "${tool} available"
        else
            warn "${tool} not found (optional — some skills will have limited functionality)"
        fi
    }

    # Required for AWS
    check_tool "helm"       "3.12"
    check_tool "terraform"  "1.6"
    check_tool "jq"         "1.6"
    check_tool "yq"         "4.0"

    # Optional but recommended
    check_tool_optional "eksctl"
    check_tool_optional "kubectx"
    check_tool_optional "kubens"
    check_tool_optional "aws-iam-authenticator"

    echo ""

    # 3. AWS region and environment
    echo -e "${BOLD}[3/8] Checking AWS region and environment${RESET}"

    # Check AWS region
    local region=${AWS_DEFAULT_REGION:-$(aws configure get region)}
    if [[ -n "$region" ]]; then
        pass "AWS region: ${region}"

        # Check region availability
        if aws ec2 describe-regions --region-names "$region" &>/dev/null; then
            pass "Region ${region} is available"
        else
            warn "Region ${region} may not be available"
        fi
    else
        fail "AWS region not set - run: aws configure"
    fi

    # Check required environment variables
    check_env_var() {
        local var=$1 required=${2:-true}
        if [[ -n "${!var:-}" ]]; then
            pass "${var} set"
        elif [[ "$required" == "true" ]]; then
            fail "${var} not set (required)"
        else
            warn "${var} not set (optional)"
        fi
    }

    check_env_var "AWS_DEFAULT_REGION" "true"
    check_env_var "EKS_CLUSTER_NAME" "false"
    check_env_var "VPC_ID" "false"
    check_env_var "SUBNET_IDS" "false"

    echo ""

    # 4. AWS resource availability
    echo -e "${BOLD}[4/8] Checking AWS resource availability${RESET}"

    # Check VPC quota
    local vpc_count=$(aws ec2 describe-vpcs --query 'length(Vpcs)' --output text 2>/dev/null || echo "unknown")
    if [[ "$vpc_count" != "unknown" && $vpc_count -lt 4 ]]; then
        pass "VPC usage: ${vpc_count}/5 (sufficient)"
    else
        warn "High VPC usage: ${vpc_count}/5 - may hit limits"
    fi

    # Check EKS cluster quota
    local eks_count=$(aws eks list-clusters --query 'length(clusters)' --output text 2>/dev/null || echo "unknown")
    if [[ "$eks_count" != "unknown" && $eks_count -lt 95 ]]; then
        pass "EKS clusters: ${eks_count}/100 (sufficient)"
    else
        warn "High EKS cluster usage: ${eks_count}/100"
    fi

    echo ""

    # 5. Network and security
    echo -e "${BOLD}[5/8] Checking network and security${RESET}"

    # Check if VPC exists
    if [[ -n "${VPC_ID:-}" ]]; then
        if aws ec2 describe-vpcs --vpc-ids "$VPC_ID" &>/dev/null; then
            pass "VPC ${VPC_ID} exists"
        else
            fail "VPC ${VPC_ID} not found"
        fi
    else
        info "VPC_ID not set - will create new VPC"
    fi

    # Check subnets
    if [[ -n "${SUBNET_IDS:-}" ]]; then
        local subnet_count=$(echo "$SUBNET_IDS" | tr ',' '\n' | wc -l)
        if [[ $subnet_count -ge 2 ]]; then
            pass "${subnet_count} subnets configured"
        else
            warn "Only ${subnet_count} subnet(s) configured - recommend at least 2"
        fi
    else
        info "SUBNET_IDS not set - will create subnets"
    fi

    echo ""

    # 6. Kubernetes context
    echo -e "${BOLD}[6/8] Checking Kubernetes context${RESET}"

    if kubectl cluster-info &>/dev/null; then
        local context=$(kubectl config current-context 2>/dev/null)
        if [[ "$context" == *"$cluster_name"* ]]; then
            pass "kubectl context set to EKS cluster: ${context}"
        else
            warn "kubectl context (${context}) does not match expected cluster (${cluster_name})"
        fi
    else
        info "kubectl not connected to cluster - will connect after EKS creation"
    fi

    echo ""

    # 7. Cost and resource estimation
    echo -e "${BOLD}[7/8] Estimating costs and resources${RESET}"

    # Rough cost estimation for EKS
    info "Estimated monthly costs for EKS cluster:"
    info "  - EKS control plane: ~$70/month"
    info "  - 3 t3.medium nodes: ~$120/month"
    info "  - EBS storage: ~$10/month"
    info "  - Data transfer: Variable"
    info "  Total estimate: ~$200+/month"

    echo ""

    # 8. Final confirmation
    echo -e "${BOLD}[8/8] Deployment confirmation${RESET}"

    local cluster_name=${EKS_CLUSTER_NAME:-agentic-cluster}
    local region=${AWS_DEFAULT_REGION:-$(aws configure get region)}

    echo -e "${YELLOW}This will deploy to AWS region: ${region}${NC}"
    echo -e "${YELLOW}EKS cluster name: ${cluster_name}${NC}"
    echo -e "${YELLOW}Estimated monthly cost: ~$200+${NC}"
    echo ""

    # Summary
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
    if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}  ✓ AWS production validation PASSED — ready for deployment${RESET}"
    elif [[ $ERRORS -eq 0 ]]; then
        echo -e "${YELLOW}${BOLD}  ⚠ AWS production validation PASSED with ${WARNINGS} warning(s)${RESET}"
        echo -e "${YELLOW}  Review warnings above before proceeding with deployment.${RESET}"
    else
        echo -e "${RED}${BOLD}  ✗ AWS production validation FAILED — ${ERRORS} error(s), ${WARNINGS} warning(s)${RESET}"
        echo -e "${RED}  Fix the errors above before proceeding.${RESET}"
        echo ""
        echo -e "  ${CYAN}Quick fixes:${RESET}"
        echo -e "    aws configure                          # Configure AWS credentials"
        echo -e "    export AWS_DEFAULT_REGION=us-east-1    # Set AWS region"
        echo -e "    export EKS_CLUSTER_NAME=my-cluster      # Set cluster name"
    fi
    echo -e "${BOLD}══════════════════════════════════════════════════════════════${RESET}"
    echo ""

    return $ERRORS
}

# Hook support
run_hooks() {
    local hook_name="$1"
    local hook_file="core/hooks/${hook_name}.sh"

    if [[ -f "$hook_file" ]]; then
        print_info "Running $hook_name hook..."
        if bash "$hook_file"; then
            print_success "$hook_name hook completed"
        else
            print_error "$hook_name hook failed"
            return 1
        fi
    else
        print_info "No $hook_name hook found - skipping"
    fi
}

# Create EKS cluster
create_eks_cluster() {
    print_header "Creating EKS Cluster"

    local cluster_name=${EKS_CLUSTER_NAME:-agentic-cluster}
    local region=${AWS_DEFAULT_REGION}

    if aws eks describe-cluster --name "$cluster_name" --region "$region" &>/dev/null; then
        print_info "EKS cluster '$cluster_name' already exists"
        return 0
    fi

    print_info "Creating EKS cluster '$cluster_name' in region '$region'..."

    # Use eksctl to create cluster (more reliable than raw CloudFormation)
    if command -v eksctl &>/dev/null; then
        print_info "Using eksctl to create EKS cluster..."

        # Create cluster configuration
        cat > /tmp/eks-cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: ${cluster_name}
  region: ${region}
  version: "1.28"

vpc:
  clusterEndpoints:
    publicAccess: true
    privateAccess: true

managedNodeGroups:
  - name: agentic-nodes
    instanceType: t3.medium
    minSize: 2
    maxSize: 5
    desiredCapacity: 3
    volumeSize: 20
    ssh:
      allow: false
    iam:
      withAddonPolicies:
        imageBuilder: true
        autoScaler: true
        externalDNS: true
        certManager: true
        appMesh: true
        appMeshPreview: true
        xRay: true
        cloudWatch: true

addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest

iam:
  withOIDC: true
EOF

        if eksctl create cluster -f /tmp/eks-cluster-config.yaml; then
            print_success "EKS cluster '$cluster_name' created successfully"
            rm -f /tmp/eks-cluster-config.yaml
        else
            print_error "Failed to create EKS cluster with eksctl"
            rm -f /tmp/eks-cluster-config.yaml
            return 1
        fi
    else
        print_warning "eksctl not found - attempting manual CloudFormation deployment..."
        print_info "This method is more complex and may fail. Consider installing eksctl."

        # Fallback to manual CloudFormation (more complex)
        print_error "Manual CloudFormation deployment not implemented in this script"
        print_info "Please install eksctl: brew install eksctl"
        return 1
    fi

    # Update kubeconfig
    print_info "Updating kubeconfig..."
    aws eks update-kubeconfig --name "$cluster_name" --region "$region"

    print_success "EKS cluster setup complete"
}

# Deploy AWS Load Balancer Controller
deploy_aws_load_balancer_controller() {
    print_header "Deploying AWS Load Balancer Controller"

    if kubectl get deployment aws-load-balancer-controller -n kube-system &>/dev/null; then
        print_info "AWS Load Balancer Controller already deployed"
        return 0
    fi

    print_info "Deploying AWS Load Balancer Controller..."

    # Create IAM policy for ALB controller
    cat > /tmp/alb-iam-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:CreateServiceLinkedRole"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeAccountAttributes",
                "ec2:DescribeAddresses",
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeInternetGateways",
                "ec2:DescribeVpcs",
                "ec2:DescribeVpcPeeringConnections",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeInstances",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeTags",
                "ec2:GetCoipPoolUsage",
                "ec2:DescribeCoipPools",
                "elasticloadbalancing:*",
                "ec2:CreateSecurityGroup",
                "ec2:DeleteSecurityGroup",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupIngress",
                "ec2:CreateTags",
                "ec2:DeleteTags"
            ],
            "Resource": "*"
        }
    ]
}
EOF

    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=${AWS_DEFAULT_REGION}
    local policy_name="AWSLoadBalancerControllerIAMPolicy"

    # Create IAM policy
    aws iam create-policy --policy-name "$policy_name" --policy-document file:///tmp/alb-iam-policy.json || true

    # Create IAM service account
    eksctl create iamserviceaccount \
        --cluster="$cluster_name" \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name "AmazonEKSLoadBalancerControllerRole" \
        --attach-policy-arn="arn:aws:iam::${account_id}:policy/${policy_name}" \
        --approve

    # Deploy ALB controller
    kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
    kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

    helm repo add eks https://aws.github.io/eks-charts
    helm repo update

    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="$cluster_name" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller

    # Wait for deployment
    kubectl wait --for=condition=available --timeout=300s deployment/aws-load-balancer-controller -n kube-system

    rm -f /tmp/alb-iam-policy.json
    print_success "AWS Load Balancer Controller deployed"
}

# Deploy AI agents dashboard function (same as base)
deploy_ai_agents_dashboard() {
    print_header "Deploying AI Agents Dashboard"

    # Check if the ecosystem deployment script exists
    local ecosystem_script="$SCRIPT_DIR/deploy-ai-agents-ecosystem.sh"

    if [[ ! -f "$ecosystem_script" ]]; then
        print_warning "AI agents ecosystem script not found at $ecosystem_script"
        print_info "You can manually run: ./core/automation/scripts/deploy-ai-agents-ecosystem.sh"
        return 0
    fi

    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_warning "Kubernetes cluster not accessible - skipping dashboard deployment"
        print_info "To deploy dashboard later: QUICKSTART_DEPLOY_DASHBOARD=true ./core/scripts/automation/quickstart-remote-aws.sh"
        return 0
    fi

    print_info "Deploying AI agents ecosystem with dashboard..."

    # Run the ecosystem deployment script
    if bash "$ecosystem_script"; then
        print_success "AI agents dashboard deployed successfully!"
        echo ""
        echo -e "${GREEN}🎉 Your AI Agents Dashboard is now running!${NC}"
        echo -e "${YELLOW}📊 Access it via AWS Load Balancer (check kubectl get svc -n ai-infrastructure)${NC}"
        echo ""

        # Start all required port-forwards in background
        start_all_port_forwards

        echo ""
        echo "🌐 All Services Access:"
        echo "  🚪 Infrastructure Portal:  http://localhost:9000"
        echo "  🤖 AI Dashboard:        http://localhost:8080"
        echo "  📊 Dashboard API:        http://localhost:5000"
        echo "  ⏰ Temporal UI:          http://localhost:7233"
        echo "  🔍 Langfuse Observability: http://localhost:3000"
        echo "  📈 Comprehensive API:   http://localhost:5001"
        echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
        echo "  🧠 Memory Service:       http://localhost:8081"
        echo ""
        echo "💡 Management:"
        echo "  📝 View logs: tail -f /tmp/quickstart-port-forwards/*.log"
        echo "  🧹 Clean up: ./core/scripts/automation/quickstart-remote-aws.sh --cleanup"
        echo "  🔄 Restart: ./core/scripts/automation/quickstart-remote-aws.sh --start-pf"
        echo ""
        echo "Dashboard features:"
        echo "  ✅ Real-time AI agents monitoring"
        echo "  ✅ 91 operational skills visualization"
        echo "  ✅ Performance metrics and charts"
        echo "  ✅ Activity feed and system controls"
        echo "  ✅ Temporal workflow orchestration UI"
        echo "  ✅ Comprehensive analytics dashboard"
    else
        print_error "Failed to deploy AI agents dashboard"
        print_info "Check the logs above for errors and try running the script manually"
        return 1
    fi
}

# Start all required port-forwards in background (same as base)
start_all_port_forwards() {
    print_info "Starting background port-forwards for all services..."

    # Create log directory
    mkdir -p /tmp/quickstart-port-forwards

    local started_count=0
    local failed_count=0

    # AI Infrastructure Services
    local services=(
        "ai-infrastructure:ai-infrastructure-portal:80:9000"
        "ai-infrastructure:agent-dashboard-service:80:8080"
        "ai-infrastructure:dashboard-api-service:5000:5000"
        "ai-infrastructure:temporal-server-service:7233:7233"
        "ai-infrastructure:comprehensive-dashboard-api:5000:5001"
        "ai-infrastructure:comprehensive-dashboard-frontend:80:8082"
        "ai-infrastructure:agent-memory-service:8080:8081"

        # Langfuse Services
        "langfuse:langfuse-server:3000:3000"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r namespace service_name target_port local_port <<< "$service_config"
        local log_file="/tmp/quickstart-port-forwards/${namespace}-${service_name}.log"
        local service_key="${namespace}-${service_name}"

        # Check if port-forward already running
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            print_info "Port-forward already running: ${service_name} -> ${local_port}"
            ((started_count++))
            continue
        fi

        # Start port-forward in background
        print_info "Starting: ${service_name} -> localhost:${local_port}"
        nohup kubectl port-forward -n "${namespace}" svc/"${service_name}" "${local_port}:${target_port}" > "${log_file}" 2>&1 &

        # Wait a moment and check if it started successfully
        sleep 2
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            print_success "✅ ${service_name} -> localhost:${local_port}"
            ((started_count++))
        else
            print_warning "❌ Failed to start: ${service_name} -> localhost:${local_port}"
            ((failed_count++))
        fi
    done

    # Summary
    echo ""
    print_success "Port-forward summary:"
    echo "  ✅ Started: ${started_count} services"
    if [[ $failed_count -gt 0 ]]; then
        echo "  ❌ Failed: ${failed_count} services"
    fi
    echo ""
    echo -e "${GREEN}🌐 Access URLs:${NC}"
    echo "  🚪 Infrastructure Portal:  http://localhost:9000"
    echo "  🤖 AI Dashboard:        http://localhost:8080"
    echo "  📊 Dashboard API:        http://localhost:5000"
    echo "  ⏰ Temporal UI:          http://localhost:7233"
    echo "  🔍 Langfuse Observability: http://localhost:3000"
    echo "  📈 Comprehensive API:   http://localhost:5001"
    echo "  🖥️  Comprehensive Frontend: http://localhost:8082"
    echo "  🧠 Memory Service:       http://localhost:8081"
    echo ""
    echo -e "${YELLOW}📝 Logs: tail -f /tmp/quickstart-port-forwards/*.log${NC}"
}

# Enhanced cleanup function for AWS
cleanup_aws() {
    print_header "Cleaning up AWS environment"

    # Stop all port-forwards
    cleanup_port_forwards

    local cluster_name=${EKS_CLUSTER_NAME:-agentic-cluster}
    local region=${AWS_DEFAULT_REGION}

    # Ask for confirmation before destroying cluster
    echo -e "${RED}⚠️  This will destroy the EKS cluster and all associated resources!${NC}"
    echo -e "${RED}Cluster: ${cluster_name}${NC}"
    echo -e "${RED}Region: ${region}${NC}"
    echo -e "${YELLOW}This action cannot be undone. Are you sure? (yes/NO)${NC}"
    read -r response

    if [[ "$response" != "yes" ]]; then
        print_info "Cleanup cancelled by user"
        return 0
    fi

    # Delete EKS cluster
    if aws eks describe-cluster --name "$cluster_name" --region "$region" &>/dev/null; then
        print_info "Deleting EKS cluster '$cluster_name'..."

        if command -v eksctl &>/dev/null; then
            if eksctl delete cluster --name "$cluster_name" --region "$region"; then
                print_success "EKS cluster deleted successfully"
            else
                print_error "Failed to delete EKS cluster"
            fi
        else
            print_warning "eksctl not found - manual cleanup required"
            print_info "Run: aws eks delete-cluster --name $cluster_name --region $region"
        fi
    else
        print_info "EKS cluster '$cluster_name' not found"
    fi

    # Clean up CloudFormation stacks
    print_info "Checking for CloudFormation stacks..."
    local stacks=$(aws cloudformation list-stacks --region "$region" --query 'StackSummaries[?StackName!=`null`]|[?contains(StackName, `eksctl-`) || contains(StackName, `agentic`)]|[].StackName' --output text 2>/dev/null || echo "")

    if [[ -n "$stacks" ]]; then
        print_info "Found CloudFormation stacks to clean up: $stacks"
        for stack in $stacks; do
            echo -e "${YELLOW}Delete stack '$stack'? (y/N)${NC}"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                aws cloudformation delete-stack --stack-name "$stack" --region "$region"
                print_info "Deletion initiated for stack '$stack'"
            fi
        done
    fi

    print_success "AWS environment cleanup completed"
}

# Main function for AWS production quickstart
main() {
    print_header "Agentic Reconciliation Engine - AWS Production Quick Start"

    echo -e "${BLUE}Welcome to Agentic Reconciliation Engine - AWS Production Deployment!${NC}"
    echo ""
    echo -e "${YELLOW}This will deploy a complete production environment on AWS EKS.${NC}"
    echo -e "${RED}⚠️  This will create billable AWS resources!${NC}"
    echo ""

    # Check if we're in the right directory
    if [[ ! -f "$REPO_ROOT/README.md" ]]; then
        print_error "Not in repository root. Please run from repository root."
        exit 1
    fi

    # Run AWS production-specific validation
    print_info "Running AWS production prerequisites validation..."
    if ! run_aws_production_validation; then
        print_error "AWS production validation failed. Please fix errors above and retry."
        exit 1
    fi

    # If there are warnings, prompt user to continue
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s). Continue with AWS deployment? (Y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Nn]$ ]]; then
            print_info "AWS deployment cancelled by user."
            exit 0
        fi
    fi

    # Final cost confirmation
    echo -e "${RED}⚠️  DEPLOYMENT COST WARNING${NC}"
    echo -e "${YELLOW}This deployment will create billable AWS resources with estimated monthly costs of ~$200+${NC}"
    echo -e "${YELLOW}Resources include: EKS cluster, EC2 instances, EBS storage, load balancers${NC}"
    echo -e "${YELLOW}Do you want to proceed with deployment? (yes/NO)${NC}"
    read -r response
    if [[ "$response" != "yes" ]]; then
        print_info "AWS deployment cancelled by user."
        exit 0
    fi

    # Run pre-quickstart hook
    run_hooks "pre-quickstart" || return 1

    # Setup basic configuration
    print_info "Setting up AWS production environment..."

    # Create basic directories if they don't exist
    mkdir -p logs/
    mkdir -p tmp/

    # Make scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;
    find "$SCRIPT_DIR" -name "*.py" -exec chmod +x {} \;

    print_success "AWS production environment ready"

    # Create EKS cluster
    create_eks_cluster || return 1

    # Deploy AWS Load Balancer Controller
    deploy_aws_load_balancer_controller || return 1

    # Run post-quickstart hook
    run_hooks "post-quickstart" || return 1

    # Deploy AI agents dashboard
    deploy_ai_agents_dashboard || return 1

    # Deploy AI Agent Skills and MCP servers
    deploy_ai_agent_skills || return 1

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Access your AI agents dashboard via AWS Load Balancer"
    echo "2. Check service endpoints: kubectl get svc -n ai-infrastructure"
    echo "3. Configure DNS for LoadBalancer services if needed"
    echo "4. Configure Claude Desktop with AI Agent Skills (auto-configured)"
    echo "5. Use consolidated K8sGPT: http://k8sgpt.k8sgpt-system.svc.cluster.local:8080"
    echo "6. Monitor AWS costs in AWS Cost Explorer"
    echo "7. View port-forward logs: tail -f /tmp/quickstart-port-forwards/*.log"
    echo "8. Clean up environment: ./core/scripts/automation/quickstart-remote-aws.sh --cleanup"
    echo ""
    echo -e "${GREEN}🚀 AWS production environment is ready!${NC}"
    echo -e "${YELLOW}🧠 AI agents are fully operational!${NC}"
    echo -e "${BLUE}☁️  AWS EKS cluster is running in ${AWS_DEFAULT_REGION}!${NC}"
    echo ""
    echo -e "${RED}💰 Remember to monitor your AWS costs!${NC}"
}

# Enhanced cleanup function (same as base)
cleanup_port_forwards() {
    print_info "Cleaning up all background port-forwards..."

    local services=(
        "ai-infrastructure-portal:9000"
        "agent-dashboard-service:8080"
        "dashboard-api-service:5000"
        "temporal-server-service:7233"
        "comprehensive-dashboard-api:5001"
        "comprehensive-dashboard-frontend:8082"
        "langfuse-server:3000"
        "agent-memory-service:8081"
    )

    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port <<< "$service_config"

        # Kill the port-forward process
        if pgrep -f "port-forward.*${service_name}.*${local_port}" > /dev/null; then
            pkill -f "port-forward.*${service_name}.*${local_port}"
            print_success "Stopped ${service_name} port-forward (port ${local_port})"
        fi
    done

    # Clean up log directory
    if [[ -d /tmp/quickstart-port-forwards ]]; then
        rm -rf /tmp/quickstart-port-forwards
        print_info "Cleaned up port-forward logs"
    fi

    # Clean up old individual log files
    for service_config in "${services[@]}"; do
        IFS=':' read -r service_name local_port <<< "$service_config"
        local log_file="/tmp/${service_name}-port-forward.log"
        if [[ -f "$log_file" ]]; then
            rm -f "$log_file"
        fi
    done

    print_success "All port-forwards cleaned up"
}

# Help function
show_help() {
    echo "Agentic Reconciliation Engine - AWS Production Quick Start"
    echo ""
    echo "USAGE: $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help         Show this help message"
    echo "  --validate         Run AWS production validation only"
    echo "  --cleanup          Clean up AWS EKS cluster and resources"
    echo "  --start-pf         Start all port-forwards (if not already running)"
    echo "  --create-cluster   Create EKS cluster only"
    echo "  --deploy-alb       Deploy AWS Load Balancer Controller only"
    echo ""
    echo "DESCRIPTION:"
    echo "  Sets up a complete production environment on AWS EKS."
    echo "  This includes EKS cluster creation, AWS Load Balancer Controller,"
    echo "  comprehensive prerequisites validation, and deployment of AI agents dashboard."
    echo ""
    echo "  ⚠️  This creates billable AWS resources! Monitor costs carefully."
    echo ""
    echo "EXAMPLES:"
    echo "  $0                        # Complete AWS production setup"
    echo "  $0 --validate            # Validate AWS prerequisites only"
    echo "  $0 --cleanup             # Clean up AWS environment (destructive!)"
    echo "  $0 --create-cluster      # Create EKS cluster only"
    echo ""
    echo "AWS REQUIREMENTS:"
    echo "  - AWS CLI configured with appropriate permissions"
    echo "  - eksctl installed (recommended)"
    echo "  - Sufficient AWS quota for EKS, EC2, ELB"
    echo "  - Budget for ~$200+/month in costs"
    echo ""
    echo "REQUIRED PERMISSIONS:"
    echo "  - eks:* (EKS operations)"
    echo "  - ec2:* (VPC, subnets, security groups)"
    echo "  - iam:* (IAM roles and policies)"
    echo "  - elasticloadbalancing:* (Load balancers)"
    echo ""
    echo "SERVICES ACCESS:"
    echo "  🚪 Infrastructure Portal:  AWS Load Balancer"
    echo "  🤖 AI Dashboard:        AWS Load Balancer"
    echo "  📊 Dashboard API:        AWS Load Balancer"
    echo "  ⏰ Temporal UI:          AWS Load Balancer"
    echo "  🔍 Langfuse Observability: AWS Load Balancer"
    echo "  📈 Comprehensive API:   AWS Load Balancer"
    echo "  🖥️  Comprehensive Frontend: AWS Load Balancer"
    echo "  🧠 Memory Service:       AWS Load Balancer"
    echo ""
    echo "COST ESTIMATION:"
    echo "  - EKS control plane: ~$70/month"
    echo "  - 3 t3.medium nodes: ~$120/month"
    echo "  - Load balancers: ~$20/month"
    echo "  - EBS storage: ~$10/month"
    echo "  - Total: ~$220/month (varies by region and usage)"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --validate)
        run_aws_production_validation
        exit $?
        ;;
    --cleanup)
        cleanup_aws
        exit 0
        ;;
    --start-pf)
        start_all_port_forwards
        exit 0
        ;;
    --create-cluster)
        create_eks_cluster
        exit $?
        ;;
    --deploy-alb)
        deploy_aws_load_balancer_controller
        exit $?
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
