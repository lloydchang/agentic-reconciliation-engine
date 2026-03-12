# Strategic Architecture Context

**Strategic Architecture: Flux + Temporal + Consensus Hybrid Approach**

This file documents dependency management within the Flux declarative layer of our hybrid architecture.

**North Star Vision**: Provide an implementation for autonomous, self-organizing infrastructure management.

**Current Status**: Implementing DAG-based dependency management for infrastructure orchestration.

**Strategic Plan**: See [docs/STRATEGIC-ARCHITECTURE.md](docs/STRATEGIC-ARCHITECTURE.md) for comprehensive roadmap.

---

# GitOps Infrastructure Control Plane - DAG Architecture

## Overview

This document outlines the Directed Acyclic Graph (DAG) architecture of the GitOps Infrastructure Control Plane, leveraging Flux's `dependsOn` feature for explicit dependency management.

## Core DAG Structure

### Level 0: Foundation Layer
```
flux-system (GitRepository)
└── flux-system (Kustomization)
```

### Level 1: Control Plane Core
```
flux-system
├── infrastructure-controllers
└── monitoring-alerts
```

### Level 2: Multi-Cloud Infrastructure
```
infrastructure-controllers
├── aws-network
├── azure-network
└── gcp-network
```

### Level 3: Compute Infrastructure
```
aws-network → aws-clusters
azure-network → azure-clusters
gcp-network → gcp-clusters
```

### Level 4: Workloads & Services
```
aws-clusters → aws-workloads
azure-clusters → azure-workloads
gcp-clusters → gcp-workloads
```

### Level 5: Enhanced Services
```
aws-clusters → aws-certificate-authority
azure-clusters → azure-entra-id-workload
gcp-clusters → gcp-auth-workload
gcp-clusters → gcp-vertex-ai-gemini
```

## Modular Component Architecture

### Core Modules

#### 1. Control Plane Module (`control-plane/`)
- **Purpose**: Base GitOps controllers and monitoring
- **Dependencies**: None (foundation layer)
- **Contains**: Flux, Kustomize controllers, monitoring stack
- **Swappable Components**:
  - Open-source: Basic Flux + Prometheus
  - Enterprise: Enhanced Flux + Grafana Enterprise + Honeycomb

#### 2. Infrastructure Module (`infrastructure/tenants/`)
- **Purpose**: Multi-cloud infrastructure deployment
- **Dependencies**: control-plane
- **Contains**: Network, compute, and workload resources
- **Swappable Components**:
  - Network: AWS VPC, Azure VNet, GCP VPC
  - Compute: AWS EKS, Azure AKS, GCP GKE
  - Workloads: Standard, AI-enhanced, Edge computing

#### 3. AI/ML Integration Module (`examples/*/`)
- **Purpose**: AI/ML workload orchestration
- **Dependencies**: infrastructure
- **Contains**: Agent workflows, consensus layers, AI gateways
- **Swappable Components**:
  - AI Framework: TensorFlow, PyTorch, ONNX Runtime
  - Orchestration: Kagent, Consensus-based, Standard K8s Jobs
  - Language Ecosystem: Python, Go, Rust, TypeScript, C#, Java

## Dependency Management Patterns

### 1. Sequential Dependencies
```yaml
dependsOn:
- name: network-infra
```

### 2. Multiple Dependencies
```yaml
dependsOn:
- name: infrastructure-controllers
- name: flux-system
```

### 3. Cross-Cloud Dependencies
```yaml
dependsOn:
- name: gcp-clusters
- name: azure-entra-workload  # GCP auth via Azure AD
```

## Variant Swapping Architecture

### Open Source vs Enterprise

#### Open Source Stack
```yaml
resources:
- control-plane/flux/gotk-components.yaml
- control-plane/monitoring/prometheus.yaml
- infrastructure/tenants/
```

#### Enterprise Stack
```yaml
resources:
- control-plane/flux/enhanced-flux-controllers.yaml
- control-plane/monitoring/grafana-enterprise.yaml
- control-plane/monitoring/honeycomb.yaml
- infrastructure/tenants/
```

### Language Ecosystem Variants

#### Python/ML Stack
```yaml
configMapGenerator:
- name: python-config
  literals:
  - RUNTIME=python3.11
  - PACKAGE_MANAGER=uv
  - ML_FRAMEWORK=torch
```

#### Go/Cloud Native Stack
```yaml
configMapGenerator:
- name: go-config
  literals:
  - RUNTIME=go1.21
  - BUILD_TOOL=go
  - FRAMEWORK=kubernetes-operator
```

#### Rust/Performance Stack
```yaml
configMapGenerator:
- name: rust-config
  literals:
  - RUNTIME=rust1.75
  - BUILD_TOOL=cargo
  - FRAMEWORK=wasmcloud
```

## DAG Visualization Tools

### 1. Dependency Graph Generator
Location: `control-plane/monitoring/dependency-graph.yaml`

Features:
- Real-time dependency visualization
- Health status integration
- Deployment pipeline tracking

### 2. Status Dashboard
Location: `control-plane/monitoring/dependency-status-dashboard.yaml`

Features:
- Component health monitoring
- Dependency chain validation
- Failure impact analysis

## Modular Deployment Patterns

### 1. Hub-Spoke Architecture
```
Hub Cluster (control-plane)
├── Spoke AWS Cluster
├── Spoke Azure Cluster
└── Spoke GCP Cluster
```

### 2. Consensus-Based Orchestration
```
Consensus Layer
├── Agent Swarm (Python)
├── Agent Swarm (Go)
├── Agent Swarm (Rust)
└── Agent Swarm (TypeScript)
```

### 3. AI-Enhanced Workflows
```
AI Gateway
├── Claude Integration
├── OpenAI Integration
└── Local LLM Integration
```

## Best Practices

### 1. Dependency Declaration
- Always use explicit `dependsOn` declarations
- Avoid relying on manifest order
- Use descriptive names for dependencies

### 2. Modularity
- Keep components loosely coupled
- Use clear interfaces between modules
- Enable hot-swapping of variants

### 3. Testing
- Test dependency chains in isolation
- Validate DAG acyclicity
- Test variant swapping scenarios

### 4. Monitoring
- Monitor dependency health
- Track deployment failures
- Alert on circular dependencies

## Implementation Examples

### Adding a New Cloud Provider
1. Create network resource: `newcloud-network.yaml`
2. Create cluster resource with dependency: `newcloud-clusters.yaml`
3. Create workload resource with dependency: `newcloud-workloads.yaml`
4. Update main kustomization to include new resources

### Swapping AI Framework
1. Update `configMapGenerator` with new framework
2. Modify agent deployment specifications
3. Update dependency chains if needed
4. Test with new framework

### Adding Language Support
1. Create language-specific runtime config
2. Add language-specific agent templates
3. Update consensus layer for new language
4. Add monitoring for language-specific metrics

## Troubleshooting

### Common Issues
1. **Circular Dependencies**: Check for dependency loops
2. **Missing Dependencies**: Verify all `dependsOn` references exist
3. **Deployment Order**: Ensure proper dependency sequencing
4. **Variant Conflicts**: Check for incompatible component combinations

### Debugging Tools
- `flux get kustomizations` - View dependency status
- `flux reconcile` - Trigger manual reconciliation
- Dependency graph visualization - See current DAG state
- Status dashboard - Monitor component health

## Future Enhancements

### 1. Dynamic Dependency Resolution
- Runtime dependency calculation
- Conditional dependencies based on configuration
- Smart dependency optimization

### 2. Advanced Variant Management
- Semantic versioning for variants
- Compatibility matrix validation
- Automatic variant selection

### 3. Enhanced Monitoring
- Predictive failure analysis
- Performance impact assessment
- Cost optimization recommendations
