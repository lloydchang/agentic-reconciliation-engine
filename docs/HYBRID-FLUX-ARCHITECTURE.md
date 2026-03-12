# Hybrid Flux Architecture Documentation

## Overview

This GitOps Infrastructure Control Plane now implements a **Hybrid Flux Architecture** that combines the reliability of standard Flux CD with the enhanced features of Flux Operator.

## Architecture

### 🚀 Core Flux CD (Critical Path)
- **Purpose**: Handles all critical GitOps operations
- **Components**: source-controller, kustomize-controller, helm-controller
- **Reliability**: Battle-tested CNCF project
- **Failure Impact**: CRITICAL - system stops working

### 🛠️ Flux Operator (Optional Add-on)
- **Purpose**: Provides enterprise-grade enhancements
- **Features**: Web UI, MCP Server, multi-tenancy
- **Reliability**: Nice-to-have, non-critical
- **Failure Impact**: OPTIONAL - core GitOps continues working

## Directory Structure

```
infrastructure/
├── flux/
│   ├── core/                    # Critical Flux CD components
│   │   ├── kustomization.yaml
│   │   ├── controllers.yaml
│   │   └── git-repository.yaml
│   └── operator/                # Optional Flux Operator
│       ├── kustomization.yaml
│       ├── flux-instance.yaml
│       ├── rbac.yaml
│       └── namespace.yaml
├── monitoring/
│   └── flux-health.yaml         # Health checks and incident response
└── clusters/
    └── hub/
        └── flux-system/
            └── hub-flux-system.yaml  # Hub cluster kustomizations
```

## Deployment

### Quick Start
```bash
# Deploy hybrid architecture
./scripts/deploy-hybrid-flux.sh

# Check status
kubectl get pods -n flux-system      # Core Flux (critical)
kubectl get pods -n flux-operator-system  # Operator (optional)
```

### Manual Steps
```bash
# 1. Bootstrap Core Flux CD
flux bootstrap git \
  --url=https://github.com/lloydchang/gitops-infra-control-plane \
  --path=infrastructure/flux/core \
  --components=source-controller,kustomize-controller,helm-controller

# 2. Deploy Flux Operator (optional)
kubectl apply -f infrastructure/flux/operator/

# 3. Deploy hub kustomizations
kubectl apply -f infrastructure/flux/hub-flux-system.yaml
```

## Configuration

### Core Flux Configuration
- **Interval**: 5 minutes for fast reconciliation
- **Path**: `./infrastructure/flux/core`
- **Wait**: Yes - critical for validation
- **Timeout**: 5 minutes

### Operator Configuration
- **Interval**: 30 minutes (slower, non-critical)
- **Path**: `./infrastructure/flux/operator`
- **Wait**: No - optional, don't block
- **Timeout**: 10 minutes
- **Depends On**: flux-core (requires core to be healthy first)

## Access & Monitoring

### Web UI (Operator)
```bash
# Port forward to access dashboards
kubectl port-forward svc/flux-operator 9080:9080
# Open http://localhost:9080
```

### MCP Server (Operator)
```bash
# Check MCP server status
flux-operator-mcp status

# Configure AI assistant with MCP
# See docs/FLUX-MCP-SERVER.md
```

### Health Monitoring
```bash
# Core Flux health (critical)
kubectl wait --for=condition=available --timeout=60s \
  deployment/source-controller -n flux-system

# Operator health (optional)
kubectl get pods -n flux-operator-system || echo "Operator not running (optional)"
```

## Incident Response

### Priority 1: Core Flux Issues
**Symptoms**: GitOps deployments failing, core pods crashed

**Actions**:
1. Check core controllers: `kubectl get pods -n flux-system`
2. Check reconciliation: `flux get kustomizations -n flux-system`
3. Force re-bootstrap: `flux bootstrap git --force`
4. Restart controllers: `kubectl rollout restart deployment/source-controller -n flux-system`

### Priority 2: Operator Issues
**Symptoms**: Web UI down, MCP server not responding

**Actions**:
1. Check operator: `kubectl get pods -n flux-operator-system`
2. Restart operator: `kubectl rollout restart deployment/flux-operator -n flux-operator-system`
3. Disable features: `kubectl patch fluxinstance flux-operator --type='merge' -p='{"spec":{"webUI":{"enabled":false}}}'`

## Benefits

### ✅ Reliability First
- Core GitOps never fails due to operator issues
- Minimal dependencies in critical path
- Battle-tested CNCF components

### ✅ Enhanced Experience
- Web UI provides great visibility when available
- MCP Server enables AI-assisted operations
- Enterprise features when needed

### ✅ Operational Flexibility
- Can disable operator features during incidents
- Operator failure doesn't affect core deployments
- Gradual adoption of enterprise features

## Best Practices

1. **Monitor Core Flux**: Set up alerts for core controller health
2. **Operator as Enhancement**: Treat operator as value-add, not requirement
3. **Graceful Degradation**: System works perfectly without operator
4. **Regular Testing**: Test operator failure scenarios
5. **Documentation**: Keep incident response procedures updated

This hybrid architecture provides **bulletproof GitOps reliability** with **enterprise-grade enhancements**! 🎯
