# Unified Crossplane Multi-Cloud Architecture

A single Crossplane instance with smart provider selection, proper team isolation, and advanced multi-cloud capabilities.

## 🎯 Overview

This implementation provides:
- **Single Control Plane** - One place to manage, upgrade, and debug
- **Smart Provider Selection** - Intelligent cost and performance optimization
- **Team-Based Isolation** - Proper separation through ProviderConfig and RBAC
- **Cross-Cloud Capabilities** - Failover, optimization, and resource placement
- **GitOps Integration** - Single source of truth deployment
- **Comprehensive Monitoring** - Full observability and alerting

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Unified Crossplane Control Plane              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Smart Provider Selection Engine             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │ │
│  │  │ AWS Provider │ │Azure Provider│ │ GCP Provider │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │        Composite Resource Definitions          │ │ │
│  │  │    • Smart Multi-Cloud Compute                 │ │ │
│  │  │    • Cost-Optimized Storage                    │ │ │
│  │  │    • Cross-Cloud Failover                     │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │           Team-Based Isolation                 │ │ │
│  │  │    • ProviderConfig per Team                   │ │ │
│  │  │    • RBAC Controls                             │ │ │
│  │  │    • Namespace Separation                      │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Team A      │ │ Team B      │ │ Crossplane  │
│ Resources   │ │ Resources   │ │ System      │
│             │ │             │ │             │
│ • Compute    │ │ • Compute    │ │ • Providers │
│ • Storage    │ │ • Storage    │ │ • XRDs      │
│ • Networks   │ │ • Networks   │ │ • Monitoring│
└─────────────┘ └─────────────┘ └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Cloud provider credentials (AWS, Azure, GCP)
- Python 3.8+ (for orchestrator)
- Helm 3.x (recommended)

### 1. Deploy Unified Crossplane

```bash
# Clone the repository
git clone https://github.com/agentic-reconciliation-engine/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Deploy the unified architecture
./scripts/deploy-unified-crossplane.sh deploy
```

### 2. Verify Deployment

```bash
# Check Crossplane status
./scripts/deploy-unified-crossplane.sh verify

# Test the orchestrator
./scripts/deploy-unified-crossplane.sh test
```

### 3. Create Your First Resource

```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XCompute
metadata:
  name: my-smart-compute
  namespace: team-a
spec:
  provider: auto  # Let Crossplane select optimal provider
  region: us-west-2
  instanceType: medium
  image: ubuntu-20.04
  providerSelector:
    costOptimal: true
    performanceOptimal: true
  autoScaling:
    enabled: true
    minInstances: 2
    maxInstances: 5
```

```bash
kubectl apply -f my-smart-compute.yaml
```

## 📋 Features

### Smart Provider Selection

The unified orchestrator automatically selects the optimal provider based on:

- **Cost Optimization** - Chooses lowest-cost provider
- **Performance Optimization** - Prioritizes high-performance providers
- **Compliance Requirements** - Ensures regulatory compliance
- **Resource Type** - Provider strengths for different resources

```python
# Example: Create cost-optimized compute
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action create \
  --type compute \
  --name web-server \
  --cost-optimal \
  --failover
```

### Team-Based Isolation

**Namespace Separation:**
- `team-a` - Team A resources and credentials
- `team-b` - Team B resources and credentials
- `crossplane-system` - Control plane components

**ProviderConfig Isolation:**
```yaml
# Team A AWS configuration
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: aws-team-a
  namespace: team-a
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: team-a
      name: aws-team-a-credentials
```

**RBAC Controls:**
```yaml
# Team A can only manage their resources
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: crossplane-operator
  namespace: team-a
rules:
- apiGroups: ["multicloud.example.com"]
  resources: ["xnetworks", "xcomputes", "xstorages"]
  verbs: ["create", "get", "list", "watch", "update", "patch", "delete"]
```

### Cross-Cloud Capabilities

**Failover Configuration:**
```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XCompute
metadata:
  name: ha-compute-cluster
spec:
  provider: aws
  failoverConfig:
    enabled: true
    backupProvider: gcp
    healthCheckInterval: 15
```

**Cost Optimization:**
```yaml
apiVersion: multicloud.example.com/v1alpha1
kind: XStorage
metadata:
  name: cost-effective-storage
spec:
  provider: auto
  providerSelector:
    costOptimal: true
  crossCloudReplication:
    enabled: true
    targetProviders: [aws, azure]
    replicationInterval: 24h
```

## 🛠️ Components

### Core Files

| Component | Path | Description |
|-----------|------|-------------|
| **Unified Orchestrator** | `core/scripts/automation/unified_crossplane_orchestrator.py` | Smart provider selection and optimization |
| **Multi-Cloud Orchestrator** | `.agents/orchestrate-automation/scripts/multi_cloud_orchestrator.py` | Updated for unified Crossplane |
| **Temporal Workflow** | `overlay/ai/skills/complete-hub-spoke-temporal/workflows/unified-multi-cloud-scatter-gather.go` | Multi-cloud operations workflow |
| **Deployment Script** | `scripts/deploy-unified-crossplane.sh` | Automated deployment and management |

### Crossplane Configuration

| Component | Path | Description |
|-----------|------|-------------|
| **Provider Installation** | `overlay/crossplane/unified/crossplane-install.yaml` | All cloud providers |
| **Provider Isolation** | `overlay/crossplane/unified/provider-configs-isolated.yaml` | Team-specific configs |
| **RBAC Setup** | `overlay/crossplane/unified/rbac.yaml` | Access control |
| **Composite Resources** | `overlay/crossplane/unified/composite-resources-unified.yaml` | XRDs with smart selection |
| **Compositions** | `overlay/crossplane/unified/compositions/` | Smart resource templates |

### Monitoring & GitOps

| Component | Path | Description |
|-----------|------|-------------|
| **Monitoring** | `overlay/crossplane/unified/monitoring/unified-monitoring.yaml` | Prometheus + Grafana |
| **GitOps** | `overlay/crossplane/unified/gitops/unified-gitops.yaml` | Flux configuration |
| **Examples** | `overlay/crossplane/unified/examples/` | Sample resources |

## 📊 Monitoring

### Key Metrics

- **Provider Health Scores** - Overall health per provider
- **Resource Distribution** - Cross-cloud resource allocation
- **Cost Optimization** - Percentage of cost-optimized resources
- **Failover Status** - Health of failover configurations
- **Reconciliation Performance** - Duration and error rates

### Grafana Dashboard

Access the unified dashboard at `http://grafana/d/crossplane-unified` after deployment.

### Alerts

Automated alerts for:
- Provider health degradation
- Resource reconciliation failures
- High error rates
- Cost optimization opportunities

## 🔧 Operations

### Using the Unified Orchestrator

```bash
# Create smart resource
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action create \
  --type compute \
  --name app-server \
  --cost-optimal

# Analyze cost optimization
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action analyze \
  --namespace team-a

# Get optimization recommendations
python3 core/scripts/automation/unified_crossplane_orchestrator.py \
  --action optimize
```

### Using kubectl

```bash
# List all resources
kubectl get xnetworks,xcomputes,xstorages --all-namespaces

# Check resource status
kubectl describe xcompute smart-compute-cluster -n team-a

# Check provider health
kubectl get providers -n crossplane-system
```

### Using GitOps

```bash
# Apply changes through Git
git add .
git commit -m "Add new compute resource"
git push

# Flux will automatically apply changes
```

## 🧪 Testing

### Unit Tests

```bash
# Test orchestrator functionality
python3 core/scripts/automation/unified_crossplane_orchestrator.py --action status

# Test multi-cloud orchestration
python3 .agents/orchestrate-automation/scripts/multi_cloud_orchestrator.py --strategy parallel
```

### Integration Tests

```bash
# Verify deployment
./scripts/deploy-unified-crossplane.sh verify

# Test resource creation
kubectl apply -f overlay/crossplane/unified/examples/unified-sample-resources.yaml

# Monitor resource status
watch kubectl get xnetworks,xcomputes,xstorages --all-namespaces
```

## 🔄 Migration from Terraform

### 1. Backup Existing Infrastructure

```bash
python3 core/scripts/automation/crossplane_migration_utils.py --action backup
```

### 2. Create Migration Plan

```bash
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action plan \
  --state-file core/infrastructure/terraform/terraform.tfstate
```

### 3. Execute Migration

```bash
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action migrate \
  --state-file core/infrastructure/terraform/terraform.tfstate \
  --namespace team-a
```

### 4. Validate Migration

```bash
python3 core/scripts/automation/crossplane_migration_utils.py \
  --action validate \
  --namespace team-a
```

## 🛡️ Security

### Provider Credentials

- Store in team-specific namespaces
- Use Kubernetes secrets with encryption
- Rotate credentials regularly
- Apply least privilege access

### Network Security

- Use network policies for isolation
- Enable private endpoints where possible
- Monitor cross-cloud network traffic

### Compliance

- Enable audit logging for all operations
- Tag resources with compliance metadata
- Regular security scans and assessments

## 🚨 Troubleshooting

### Common Issues

1. **Provider Installation Fails**
```bash
kubectl get providers -n crossplane-system
kubectl describe provider aws-team-a -n team-a
```

2. **Resource Creation Stuck**
```bash
kubectl describe xcompute smart-compute-cluster -n team-a
kubectl logs -n crossplane-system deployment/crossplane | grep smart-compute-cluster
```

3. **Provider Configuration Issues**
```bash
kubectl get secrets -n team-a
kubectl get providerconfig aws-team-a -n team-a -o yaml
```

### Debug Commands

```bash
# Check Crossplane pods
kubectl get pods -n crossplane-system

# View resource events
kubectl get events --field-selector involvedObject.kind=XCompute

# Validate compositions
kubectl get compositions
kubectl describe composition smart-multi-cloud-compute
```

## 📚 Documentation

- [Implementation Guide](docs/unified-crossplane-implementation-guide.md)
- [Migration Plan](docs/single-crossplane-instance-migration-plan.md)
- [API Documentation](docs/api/unified-crossplane-api.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the AGPLv3 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an issue for bugs or feature requests
- Check the troubleshooting section for common issues
- Join our community discussions

---

**Note:** This unified approach provides operational simplicity while maintaining proper isolation and enabling advanced multi-cloud capabilities. Start single, split later if you hit real limits!
