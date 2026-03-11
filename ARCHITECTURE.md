# GitOps Infrastructure Control Plane - Architecture

This document provides detailed architectural information about the GitOps Infrastructure Control Plane implementation.

## Overview

The GitOps Infrastructure Control Plane implements a zero-Terraform, multi-cloud infrastructure management system using native Kubernetes controllers and GitOps principles. The system treats infrastructure as a living, self-healing process rather than a one-time deployment.

## Core Components

### 1. Hub Cluster (Control Plane)

The central hub that orchestrates all infrastructure across multiple cloud providers.

**Components:**
- **Flux CD**: GitOps operator for continuous reconciliation
- **AWS ACK Controllers**: Native AWS resource management
- **Azure ASO Controllers**: Native Azure resource management  
- **GCP KCC Controllers**: Native Google Cloud resource management

**Responsibilities:**
- Monitor Git repository for infrastructure changes
- Reconcile cloud resources to match Git state
- Detect and repair configuration drift
- Orchestrate resource dependencies

### 2. Spoke Clusters

Kubernetes clusters provisioned and managed by the Hub Cluster.

**Characteristics:**
- Provisioned via native cloud controllers (EKS/AKS/GKE)
- Independent operation if Hub Cluster is lost:
- Can be re-bootstrapped to point back to Git
- Run application workloads and monitoring

### 3. Git Repository (Source of Truth)

The single source of truth for all infrastructure configuration.

**Structure:**
```
gitops-infra-control-plane/
├── control-plane/          # Controllers and Flux configuration
│   ├── flux/              # Flux GitOps setup
│   ├── controllers/       # Cloud provider controllers
│   └── identity/          # Workload identity configuration
└── infrastructure/        # Infrastructure resources
    └── tenants/
        ├── 1-network/     # Network resources (VPCs, subnets)
        ├── 2-clusters/    # Kubernetes clusters
        └── 3-workloads/   # Applications and services
```

## Cloud Provider Integration

### AWS (Amazon Web Services)

**Controller**: AWS Controllers for Kubernetes (ACK)
**Services**: EKS, EC2, VPC, IAM
**Authentication**: IAM Roles for Service Accounts (IRSA)

**Key Features:**
- Native CRDs for AWS resources
- Continuous reconciliation
- Event-driven updates
- No custom abstractions

### Azure (Microsoft Azure)

**Controller**: Azure Service Operator (ASO)
**Services**: AKS, Virtual Networks, Resource Groups
**Authentication**: Azure Workload Identity

**Key Features:**
- Direct Azure API integration
- ARM template compatibility
- Resource group management
- Managed identity support

### Google Cloud Platform

**Controller**: Kubernetes Config Connector (KCC)
**Services**: GKE, Compute Networks, Resource Manager
**Authentication**: Google Workload Identity

**Key Features:**
- Cloud Resource Manager integration
- Service directory management
- IAM policy management
- Project-level organization

## Dependency Management

### Flux Dependency DAG

The system uses Flux's `dependsOn` feature to create a Directed Acyclic Graph (DAG) for infrastructure dependencies:

```
1-network/ (VPCs, Subnets)
    ↓ dependsOn
2-clusters/ (EKS, AKS, GKE)
    ↓ dependsOn  
3-workloads/ (Applications, Monitoring)
```

**Benefits:**
- Explicit resource ordering
- Parallel execution where possible
- Failure isolation
- Clear dependency visualization

### Resource References

Infrastructure resources reference each other using native Kubernetes object references:

```yaml
# Example: EKS cluster referencing subnets
spec:
  resourcesVPCConfig:
    subnetRefs:
      - name: gitops-public-subnet-1a
      - name: gitops-public-subnet-1b
```

## Continuous Reconciliation

### Drift Detection

The system continuously monitors for configuration drift:

1. **Controller Polling**: Each controller periodically checks cloud resource state
2. **Event-Driven Updates**: Cloud provider events trigger immediate reconciliation
3. **Git State Comparison**: Desired state from Git is compared with actual cloud state

### Automatic Repair

When drift is detected:
1. Controllers identify the discrepancy
2. Cloud API calls are made to correct the state
3. Resources are reconciled to match Git manifests
4. Status is updated in Kubernetes

### Benefits

- **Self-Healing**: Infrastructure automatically repairs itself
- **Consistency**: Cloud state always matches Git state
- **Compliance**: Changes are tracked and auditable
- **Reliability**: Manual changes are automatically reverted

## Security Model

### Zero Static Secrets

The system eliminates static secrets through workload identity:

- **AWS IRSA**: IAM roles mapped to Kubernetes service accounts
- **Azure Workload Identity**: Azure AD integration with Kubernetes
- **GCP Workload Identity**: Google Service Account mapping

### Principle of Least Privilege

Each controller has minimal required permissions:
- Network controllers manage network resources only
- Cluster controllers manage compute resources only
- IAM controllers manage identity resources only

### Git as Security Boundary

- All changes go through Git pull requests
- Audit trail of all infrastructure modifications
- Role-based access control through Git permissions
- Immutable history of infrastructure changes

## Scalability Considerations

### Controller Isolation

Each cloud provider runs in separate namespaces:
- `ack-system` for AWS controllers
- `azureserviceoperator-system` for Azure controllers
- `cnrm-system` for Google Cloud controllers

### Resource Isolation

Infrastructure is organized by tenants and environments:
- Separate namespaces for different teams
- Resource quotas per namespace
- Network isolation at cloud level

### Performance Optimization

- **Parallel Reconciliation**: Independent resources reconcile simultaneously
- **Event-Driven Updates**: Only changed resources trigger reconciliation
- **Caching**: Controllers cache resource state for efficiency
- **Batching**: Multiple changes are batched for API efficiency

## Disaster Recovery

### Hub Cluster Failure

If the Hub Cluster is lost:
1. Spoke Clusters continue operating independently
2. Infrastructure state remains in cloud providers
3. New Hub Cluster can be bootstrapped
4. Git repository contains all required state

### Git Repository Failure

The Git repository is the single source of truth:
- Multiple backups and replicas
- Distributed version control
- Can be restored from any clone
- Complete history of all changes

### Cloud Provider Outages

Multi-cloud strategy provides resilience:
- Independent cloud provider operations
- Cross-cloud failover capabilities
- Regional distribution of resources
- Local controller instances

## Monitoring and Observability

### Controller Health

- Controller pod health monitoring
- Reconciliation metrics and success rates
- Error tracking and alerting
- Performance monitoring

### Infrastructure State

- Resource status aggregation
- Drift detection metrics
- Compliance reporting
- Cost monitoring

### GitOps Pipeline

- Flux reconciliation status
- Git commit and deployment tracking
- Dependency chain visualization
- Rollback capabilities

## Future Extensibility

### Additional Cloud Providers

The architecture supports adding new cloud providers:
- Implement controller interface
- Add cloud-specific authentication
- Create resource CRDs
- Integrate with dependency DAG

### Advanced Features

- Multi-region deployments
- Blue-green infrastructure updates
- Canary infrastructure changes
- Automated testing and validation

### Integration Points

- CI/CD pipeline integration
- External monitoring systems
- Cost management tools
- Compliance automation

## Compliance and Governance

### Change Management

- All changes through Git pull requests
- Automated testing before deployment
- Approval workflows for critical changes
- Rollback capabilities for failed changes

### Audit Trail

- Complete Git history of infrastructure changes
- Controller reconciliation logs
- Cloud provider API audit logs
- Resource state change tracking

### Policy Enforcement

- Resource naming conventions
- Tag requirements for all resources
- Security group and network policies
- Cost allocation and budgeting

This architecture provides a robust, scalable, and secure foundation for managing multi-cloud infrastructure through GitOps principles while maintaining the agility and reliability required for modern cloud-native operations.
