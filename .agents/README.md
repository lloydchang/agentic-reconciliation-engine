# Multi-Cloud Agent Skills

This directory contains agent skills following the [Agent Skills Specification](https://agentskills.io/specification) with Python-first architecture and PEP 723 dependency management.

## 🏗️ Architecture Overview

```
.agents/
├── shared/                    # Shared models and utilities
│   └── models.py             # Pydantic models for type safety
├── infrastructure-provisioning/  # Infrastructure provisioning skill
│   ├── SKILL.md              # Skill definition (agentskills.io compliant)
│   └── scripts/
│       ├── main.py          # CLI entry point with PEP 723 deps
│       ├── multi_cloud_orchestrator.py  # Core orchestration logic
│       └── infrastructure_provisioning_handler.py  # Provider handlers
├── cluster-health-check/     # Cluster health monitoring skill
│   ├── SKILL.md              # Skill definition
│   └── scripts/
│       ├── main.py          # CLI entry point with PEP 723 deps
│       ├── multi_cloud_orchestrator.py  # Health check orchestration
│       └── cluster_health_check_handler.py  # Health check handlers
├── resource-optimizer/        # Resource optimization skill
│   ├── SKILL.md              # Skill definition
│   └── scripts/              # Implementation scripts
└── examples/                  # Example configurations
    └── config.json           # Multi-cloud configuration example
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Cloud provider CLI tools and credentials
- `uv` or `pipx` for dependency management (recommended)

### Installation

```bash
# Install uv for modern Python dependency management
pip install uv

# Or use pipx for isolated script execution
pip install pipx
```

### Usage Examples

#### Infrastructure Provisioning

```bash
# Provision an EC2 instance
cd .agents/infrastructure-provisioning/scripts
python main.py provision \
  --type ec2 \
  --name my-web-server \
  --provider aws \
  --region us-west-2 \
  --tags "environment=production,team=backend" \
  --config ../../examples/config.json

# Check resource status
python main.py status my-web-server --provider aws --verbose
```

#### Cluster Health Check

```bash
# Perform comprehensive health check
cd .agents/cluster-health-check/scripts
python main.py check my-k8s-cluster \
  --provider aws \
  --checks "node,pod,network,storage" \
  --severity warning \
  --verbose

# Continuous monitoring
python main.py monitor my-k8s-cluster --interval 60 --provider aws
```

### PEP 723 Dependency Management

Each script includes inline dependencies following PEP 723:

```python
# /// script
# dependencies = [
#   "boto3>=1.26.0",
#   "azure-mgmt-compute>=29.0.0",
#   "google-cloud-compute>=1.8.0",
#   "kubernetes>=25.0.0",
#   "pydantic>=1.10.0",
#   "requests>=2.28.0"
# ]
# ///
```

Run with automatic dependency installation:

```bash
# Using uv
uv run script.py --help

# Using pipx
pipx run --spec=. script.py --help

# Or install dependencies manually
pip install -r requirements.txt
python script.py --help
```

## 📋 Available Skills

### Infrastructure Provisioning

**Purpose**: Multi-cloud infrastructure provisioning with automation and best practices

**Risk Level**: Medium  
**Autonomy**: Conditional (requires approval for production)

**Features**:
- ✅ Multi-cloud support (AWS, Azure, GCP, On-prem)
- ✅ Automated resource provisioning
- ✅ Cost estimation and tagging
- ✅ Compliance and governance
- ✅ Rollback capabilities

**Usage**:
```bash
python main.py provision --type ec2 --name my-instance --provider aws
```

### Cluster Health Check

**Purpose**: Comprehensive cluster health monitoring across multi-cloud environments

**Risk Level**: Low  
**Autonomy**: Fully automated

**Features**:
- ✅ Multi-cluster health monitoring
- ✅ Real-time health scores
- ✅ Issue detection and recommendations
- ✅ Continuous monitoring mode
- ✅ Prometheus integration

**Usage**:
```bash
python main.py check my-cluster --provider aws --checks "node,pod,network"
```

### Resource Optimizer

**Purpose**: Cost and performance optimization for cloud resources

**Risk Level**: Low  
**Autonomy**: Conditional

**Features**:
- ✅ Cost analysis and recommendations
- ✅ Resource right-sizing suggestions
- ✅ Performance optimization
- ✅ Savings tracking
- ✅ Automated optimization

## 🛡️ Type Safety with Pydantic

All skills use shared Pydantic models for type safety:

```python
from models import InfrastructureRequest, CloudProvider, OperationType

request = InfrastructureRequest(
    operation=OperationType.PROVISION,
    target_resource="my-instance",
    cloud_provider=CloudProvider.AWS,
    environment=Environment.PRODUCTION,
    dry_run=True
)
```

### Available Models

- `BaseAgentRequest` - Base request model
- `InfrastructureRequest` - Infrastructure provisioning requests
- `HealthCheckRequest` - Health check requests
- `OptimizationRequest` - Resource optimization requests
- `OrchestrationTask` - Orchestration task definition
- `SkillMetadata` - Execution metadata and human gates

## 🔧 Configuration

### Multi-Cloud Configuration

See `examples/config.json` for a complete configuration example:

```json
{
  "providers": {
    "aws": {
      "enabled": true,
      "region": "us-west-2",
      "credentials": {
        "profile": "default"
      }
    }
  },
  "orchestration": {
    "max_workers": 10,
    "timeout_minutes": 30
  }
}
```

### Environment Variables

```bash
export AWS_PROFILE=default
export AZURE_SUBSCRIPTION_ID=your-subscription-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export KUBECONFIG=/path/to/kubeconfig
```

## 🧪 Testing

Each skill includes comprehensive test suites:

```bash
# Infrastructure provisioning tests
cd .agents/infrastructure-provisioning/scripts
python test_multi_cloud_orchestrator_simple.py

# Cluster health check tests
cd .agents/cluster-health-check/scripts
python test_cluster_health_orchestrator.py
```

## 🔄 Orchestration Strategies

All orchestrators support multiple deployment strategies:

- **Sequential**: Execute tasks one by one with dependencies
- **Parallel**: Execute all tasks simultaneously
- **Rolling**: Staggered deployment with health checks
- **Blue-Green**: Parallel deployment with traffic switching

## 📊 Monitoring and Observability

### Metrics and Logging

- Structured logging with JSON output
- Prometheus metrics integration
- Grafana dashboards
- Audit trails for compliance

### Health Status

- Real-time health scores (0-100)
- Issue detection and classification
- Automated recommendations
- Rollback capabilities

## 🛡️ Security and Compliance

### Human Gates

Production operations require human approval:

```python
metadata = SkillMetadata(
    risk_level=RiskLevel.MEDIUM,
    autonomy=AutonomyLevel.CONDITIONAL,
    human_gate=HumanGateConfig(
        required=True,
        approvers=["admin@company.com"],
        timeout_minutes=60
    )
)
```

### Compliance Features

- SOC2, GDPR, HIPAA compliance support
- Required tagging enforcement
- Audit logging
- Role-based access control

## 🚀 Deployment

### GitOps Integration

Skills integrate with GitOps workflows:

```yaml
# .github/workflows/agent-skill.yml
name: Agent Skill Execution
on:
  workflow_dispatch:
    inputs:
      skill:
        required: true
        type: choice
        options: [infrastructure-provisioning, cluster-health-check, resource-optimizer]
```

### Container Deployment

```dockerfile
FROM python:3.11-slim
COPY .agents/infrastructure-provisioning /app
WORKDIR /app
RUN pip install uv
CMD ["uv", "run", "python", "main.py", "--help"]
```

## 🤝 Contributing

### Adding New Skills

1. Create skill directory: `.agents/new-skill/`
2. Add `SKILL.md` following agentskills.io specification
3. Implement scripts with PEP 723 dependencies
4. Add comprehensive tests
5. Update documentation

### Skill Template

Use `.agents/SKILL_TEMPLATE.md` as a starting point for new skills.

## 📚 Documentation

- [Agent Skills Specification](https://agentskills.io/specification)
- [Python Rationale](../docs/AGENT-SKILLS-PYTHON-RATIONALE.md)
- [AI Inference Language Choice](../docs/AI-INFERENCE-LANGUAGE-CHOICE.md)
- [GitOps Control Plane](../AGENTS.md)

## 📞 Support

For issues and questions:

1. Check existing [GitHub Issues](../../issues)
2. Review skill documentation
3. Run test suites for debugging
4. Check logs with `--verbose` flag

---

**Built with ❤️ following the Agent Skills Specification and Python-first architecture principles.**
