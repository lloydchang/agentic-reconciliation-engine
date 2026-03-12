#!/bin/bash

# Hub-Spoke Cluster Architecture Validation Script
# This script validates the complete hub-spoke GitOps architecture

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HUB_NAMESPACE="flux-system"
SPOKE_NAMESPACE="default"
VALIDATION_TIMEOUT="300s"

echo -e "${BLUE}🏗️  Hub-Spoke Architecture Validation${NC}"
echo "======================================"

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Check Flux is installed
if ! kubectl get fluxinstance -n $HUB_NAMESPACE &> /dev/null; then
    echo -e "${RED}❌ Flux is not installed in hub cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites validated${NC}"

# Validate Hub Cluster Components
echo -e "${YELLOW}🧠 Validating Hub Cluster Components...${NC}"

# Check Flux controllers
echo -e "${BLUE}  📊 Checking Flux Controllers...${NC}"
flux_controllers=("source-controller" "kustomize-controller" "helm-controller" "notification-controller" "image-reflector-controller" "image-automation-controller")

for controller in "${flux_controllers[@]}"; do
    if kubectl get deployment $controller -n $HUB_NAMESPACE &> /dev/null; then
        replicas=$(kubectl get deployment $controller -n $HUB_NAMESPACE -o jsonpath='{.status.readyReplicas}')
        if [[ $replicas -gt 0 ]]; then
            echo -e "${GREEN}    ✅ $controller ($replicas replicas)${NC}"
        else
            echo -e "${RED}    ❌ $controller (0 ready replicas)${NC}"
        fi
    else
        echo -e "${RED}    ❌ $controller not found${NC}"
    fi
done

# Check cloud controllers
echo -e "${BLUE}  ☁️  Checking Cloud Controllers...${NC}"

# AWS ACK controllers
aws_controllers=("eks-controller" "ec2-controller" "iam-controller")
for controller in "${aws_controllers[@]}"; do
    if kubectl get deployment $controller -n $HUB_NAMESPACE &> /dev/null; then
        replicas=$(kubectl get deployment $controller -n $HUB_NAMESPACE -o jsonpath='{.status.readyReplicas}')
        if [[ $replicas -gt 0 ]]; then
            echo -e "${GREEN}    ✅ AWS ACK $controller${NC}"
        else
            echo -e "${YELLOW}    ⚠️  AWS ACK $controller (not ready)${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  AWS ACK $controller not found${NC}"
    fi
done

# Azure ASO controllers
azure_controllers=("aks-controller" "network-controller" "resource-controller")
for controller in "${azure_controllers[@]}"; do
    if kubectl get deployment $controller -n $HUB_NAMESPACE &> /dev/null; then
        replicas=$(kubectl get deployment $controller -n $HUB_NAMESPACE -o jsonpath='{.status.readyReplicas}')
        if [[ $replicas -gt 0 ]]; then
            echo -e "${GREEN}    ✅ Azure ASO $controller${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Azure ASO $controller (not ready)${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  Azure ASO $controller not found${NC}"
    fi
done

# GCP KCC controllers
gcp_controllers=("gke-controller" "compute-controller" "iam-controller")
for controller in "${gcp_controllers[@]}"; do
    if kubectl get deployment $controller -n $HUB_NAMESPACE &> /dev/null; then
        replicas=$(kubectl get deployment $controller -n $HUB_NAMESPACE -o jsonpath='{.status.readyReplicas}')
        if [[ $replicas -gt 0 ]]; then
            echo -e "${GREEN}    ✅ GCP KCC $controller${NC}"
        else
            echo -e "${YELLOW}    ⚠️  GCP KCC $controller (not ready)${NC}"
        fi
    else
        echo -e "${YELLOW}    ⚠️  GCP KCC $controller not found${NC}"
    fi
done

# Validate Git Sources
echo -e "${YELLOW}📚 Validating Git Sources...${NC}"

# Check GitRepository
if kubectl get gitrepository gitops-infra-control-plane -n $HUB_NAMESPACE &> /dev/null; then
    git_status=$(kubectl get gitrepository gitops-infra-control-plane -n $HUB_NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
    if [[ $git_status == "True" ]]; then
        echo -e "${GREEN}  ✅ GitRepository gitops-infra-control-plane${NC}"
        last_sync=$(kubectl get gitrepository gitops-infra-control-plane -n $HUB_NAMESPACE -o jsonpath='{.status.lastHandledReconcileAt}')
        echo -e "${BLUE}    🔄 Last sync: $last_sync${NC}"
    else
        echo -e "${RED}  ❌ GitRepository gitops-infra-control-plane (not ready)${NC}"
    fi
else
    echo -e "${RED}  ❌ GitRepository gitops-infra-control-plane not found${NC}"
fi

# Validate Kustomizations
echo -e "${YELLOW}🔧 Validating Kustomizations...${NC}"

kustomizations=("network-infrastructure" "cluster-infrastructure" "workload-infrastructure")

for kustomization in "${kustomizations[@]}"; do
    if kubectl get kustomization $kustomization -n $HUB_NAMESPACE &> /dev/null; then
        kust_status=$(kubectl get kustomization $kustomization -n $HUB_NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        if [[ $kust_status == "True" ]]; then
            echo -e "${GREEN}  ✅ Kustomization $kustomization${NC}"
            
            # Check dependsOn relationships
            depends_on=$(kubectl get kustomization $kustomization -n $HUB_NAMESPACE -o jsonpath='{.spec.dependsOn[*].name}' 2>/dev/null || echo "")
            if [[ -n "$depends_on" ]]; then
                echo -e "${BLUE}    🔗 Depends on: $depends_on${NC}"
            fi
        else
            echo -e "${RED}  ❌ Kustomization $kustomization (not ready)${NC}"
            # Show error message
            error_msg=$(kubectl get kustomization $kustomization -n $HUB_NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}' 2>/dev/null || echo "Unknown error")
            echo -e "${RED}    Error: $error_msg${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️  Kustomization $kustomization not found${NC}"
    fi
done

# Validate Dependency Chains
echo -e "${YELLOW}🔗 Validating Dependency Chains...${NC}"

# Check if dependsOn is properly configured
network_deps=$(kubectl get kustomization cluster-infrastructure -n $HUB_NAMESPACE -o jsonpath='{.spec.dependsOn[*].name}' 2>/dev/null || echo "")
cluster_deps=$(kubectl get kustomization workload-infrastructure -n $HUB_NAMESPACE -o jsonpath='{.spec.dependsOn[*].name}' 2>/dev/null || echo "")

if [[ "$network_deps" == *"network-infrastructure"* ]]; then
    echo -e "${GREEN}  ✅ Cluster infrastructure depends on network infrastructure${NC}"
else
    echo -e "${RED}  ❌ Cluster infrastructure missing dependency on network infrastructure${NC}"
fi

if [[ "$cluster_deps" == *"cluster-infrastructure"* ]]; then
    echo -e "${GREEN}  ✅ Workload infrastructure depends on cluster infrastructure${NC}"
else
    echo -e "${RED}  ❌ Workload infrastructure missing dependency on cluster infrastructure${NC}"
fi

# Validate Namespace Separation
echo -e "${YELLOW}🏷️  Validating Namespace Separation...${NC}"

# Check hub namespace
if kubectl get namespace $HUB_NAMESPACE &> /dev/null; then
    echo -e "${GREEN}  ✅ Hub namespace: $HUB_NAMESPACE${NC}"
    
    # Check for Flux resources in hub namespace
    flux_resources=$(kubectl get all -n $HUB_NAMESPACE --no-headers | wc -l)
    echo -e "${BLUE}    📊 Resources in hub namespace: $flux_resources${NC}"
else
    echo -e "${RED}  ❌ Hub namespace: $HUB_NAMESPACE not found${NC}"
fi

# Check spoke namespace
if kubectl get namespace $SPOKE_NAMESPACE &> /dev/null; then
    echo -e "${GREEN}  ✅ Spoke namespace: $SPOKE_NAMESPACE${NC}"
    
    # Check for application resources in spoke namespace
    app_resources=$(kubectl get all -n $SPOKE_NAMESPACE --no-headers | wc -l)
    echo -e "${BLUE}    📊 Resources in spoke namespace: $app_resources${NC}"
else
    echo -e "${RED}  ❌ Spoke namespace: $SPOKE_NAMESPACE not found${NC}"
fi

# Validate ResourceSets
echo -e "${YELLOW}📦 Validating ResourceSets...${NC}"

if kubectl get resourceset infrastructure -n $HUB_NAMESPACE &> /dev/null; then
    echo -e "${GREEN}  ✅ ResourceSet infrastructure${NC}"
    
    # Check ResourceSet resources
    rs_resources=$(kubectl get resourceset infrastructure -n $HUB_NAMESPACE -o jsonpath='{.spec.resources[*].name}')
    echo -e "${BLUE}    📋 Resources: $rs_resources${NC}"
else
    echo -e "${YELLOW}  ⚠️  ResourceSet infrastructure not found${NC}"
fi

# Validate Flux Status Page
echo -e "${YELLOW}🖥️  Validating Flux Status Page...${NC}"

if kubectl get svc flux-operator -n $HUB_NAMESPACE &> /dev/null; then
    echo -e "${GREEN}  ✅ Flux Status Page service${NC}"
    
    # Test local access
    kubectl port-forward -n $HUB_NAMESPACE svc/flux-operator 9080:9080 &
    PF_PID=$!
    
    sleep 3
    
    if curl -s http://localhost:9080/health > /dev/null 2>&1; then
        echo -e "${GREEN}    ✅ Flux Status Page accessible${NC}"
    else
        echo -e "${YELLOW}    ⚠️  Flux Status Page not yet ready${NC}"
    fi
    
    kill $PF_PID 2>/dev/null || true
else
    echo -e "${YELLOW}  ⚠️  Flux Status Page service not found${NC}"
fi

# Validate MCP Server
echo -e "${YELLOW}🤖 Validating MCP Server...${NC}"

if command -v flux-operator-mcp &> /dev/null; then
    echo -e "${GREEN}  ✅ MCP Server CLI installed${NC}"
    
    # Test MCP server
    if flux-operator-mcp list_flux_instances --dry-run &> /dev/null; then
        echo -e "${GREEN}    ✅ MCP Server functional${NC}"
    else
        echo -e "${YELLOW}    ⚠️  MCP Server not configured${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  MCP Server CLI not installed${NC}"
fi

# Validate Security Configuration
echo -e "${YELLOW}🔒 Validating Security Configuration...${NC}"

# Check RBAC
if kubectl get clusterrole flux-ui-admin &> /dev/null; then
    echo -e "${GREEN}  ✅ RBAC roles configured${NC}"
else
    echo -e "${YELLOW}  ⚠️  RBAC roles not found${NC}"
fi

# Check NetworkPolicies
if kubectl get networkpolicy -n $HUB_NAMESPACE | grep -q "flux-ui-netpol"; then
    echo -e "${GREEN}  ✅ Network policies configured${NC}"
else
    echo -e "${YELLOW}  ⚠️  Network policies not found${NC}"
fi

# Check Secrets
secrets=("flux-ui-oidc" "sops-keys" "grafana-credentials")
for secret in "${secrets[@]}"; do
    if kubectl get secret $secret -n $HUB_NAMESPACE &> /dev/null; then
        echo -e "${GREEN}    ✅ Secret: $secret${NC}"
    else
        echo -e "${YELLOW}    ⚠️  Secret: $secret not found${NC}"
    fi
done

# Validate Monitoring
echo -e "${YELLOW}📊 Validating Monitoring...${NC}"

# Check Prometheus
if kubectl get deployment prometheus-server -n monitoring &> /dev/null; then
    replicas=$(kubectl get deployment prometheus-server -n monitoring -o jsonpath='{.status.readyReplicas}')
    if [[ $replicas -gt 0 ]]; then
        echo -e "${GREEN}  ✅ Prometheus ($replicas replicas)${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Prometheus not ready${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Prometheus not found${NC}"
fi

# Check Grafana
if kubectl get deployment grafana -n monitoring &> /dev/null; then
    replicas=$(kubectl get deployment grafana -n monitoring -o jsonpath='{.status.readyReplicas}')
    if [[ $replicas -gt 0 ]]; then
        echo -e "${GREEN}  ✅ Grafana ($replicas replicas)${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Grafana not ready${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠️  Grafana not found${NC}"
fi

# Check ServiceMonitors
if kubectl get servicemonitor -n monitoring | grep -q "flux"; then
    echo -e "${GREEN}  ✅ Flux ServiceMonitors configured${NC}"
else
    echo -e "${YELLOW}  ⚠️  Flux ServiceMonitors not found${NC}"
fi

# Generate Validation Report
echo -e "${YELLOW}📋 Generating Validation Report...${NC}"

# Count ready components
ready_controllers=0
total_controllers=${#flux_controllers[@]}
for controller in "${flux_controllers[@]}"; do
    if kubectl get deployment $controller -n $HUB_NAMESPACE &> /dev/null; then
        replicas=$(kubectl get deployment $controller -n $HUB_NAMESPACE -o jsonpath='{.status.readyReplicas}')
        if [[ $replicas -gt 0 ]]; then
            ((ready_controllers++))
        fi
    fi
done

ready_kustomizations=0
total_kustomizations=${#kustomizations[@]}
for kustomization in "${kustomizations[@]}"; do
    if kubectl get kustomization $kustomization -n $HUB_NAMESPACE &> /dev/null; then
        kust_status=$(kubectl get kustomization $kustomization -n $HUB_NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}')
        if [[ $kust_status == "True" ]]; then
            ((ready_kustomizations++))
        fi
    fi
done

# Calculate overall health
controller_health=$((ready_controllers * 100 / total_controllers))
kustomization_health=$((ready_kustomizations * 100 / total_kustomizations))

echo -e "${BLUE}📊 Validation Summary:${NC}"
echo -e "  Flux Controllers: $ready_controllers/$total_controllers ($controller_health%)"
echo -e "  Kustomizations: $ready_kustomizations/$total_kustomizations ($kustomization_health%)"

# Overall status
if [[ $controller_health -ge 80 && $kustomization_health -ge 80 ]]; then
    echo -e "${GREEN}🎉 Hub-Spoke Architecture: HEALTHY${NC}"
    echo -e "${GREEN}✅ Ready for production deployment${NC}"
else
    echo -e "${YELLOW}⚠️  Hub-Spoke Architecture: NEEDS ATTENTION${NC}"
    echo -e "${YELLOW}📝 Review failed components before production${NC}"
fi

# Recommendations
echo -e "${YELLOW}💡 Recommendations:${NC}"

if [[ $controller_health -lt 100 ]]; then
    echo -e "  🔧 Check Flux controller logs for failures"
    echo -e "  🔧 Verify cloud provider credentials"
fi

if [[ $kustomization_health -lt 100 ]]; then
    echo -e "  🔧 Review Kustomization error messages"
    echo -e "  🔧 Verify dependsOn relationships"
fi

if [[ ! -f "flux-operator-mcp" ]]; then
    echo -e "  🔧 Install MCP Server for AI integration"
fi

echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "  1. Configure cloud provider credentials"
echo "  2. Deploy spoke clusters"
echo "  3. Set up application workloads"
echo "  4. Configure monitoring alerts"
echo "  5. Test disaster recovery procedures"

echo -e "${GREEN}✅ Hub-Spoke Architecture Validation Complete!${NC}"
