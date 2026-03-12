# Variant Swapping Guide

## Overview

The GitOps Infrastructure Control Plane supports three main variants that can be swapped based on organizational needs and requirements. Each variant maintains the same DAG structure while providing different levels of functionality and complexity.

## Variant Types

### 1. Open Source Variant
**Label:** `variant: opensource`

**Characteristics:**
- Basic Flux controllers and core GitOps functionality
- Community-supported tools and integrations
- Standard monitoring (Prometheus/Grafana)
- Minimal overhead and complexity
- Ideal for: Small teams, learning environments, proof-of-concepts

**Components:**
```yaml
# Core infrastructure
- flux-system
- network-infra
- cluster-infra
- workload-infra (basic)
- monitoring (basic)
```

**Configuration:**
```yaml
configMapGenerator:
- name: variant-config
  literals:
  - DEPLOYMENT_SIZE=small
  - AI_INTEGRATION=false
  - MONITORING_LEVEL=basic
  - SECURITY_LEVEL=standard
```

### 2. Small Business Variant
**Label:** `variant: small-business`

**Characteristics:**
- Enhanced monitoring and observability
- Backup and disaster recovery solutions
- Security scanning and compliance tools
- Cost optimization features
- Multi-cloud support (basic)
- Ideal for: Growing companies, production workloads

**Components:**
```yaml
# Core infrastructure + enhancements
- flux-system
- network-infra
- cluster-infra
- workload-infra (enhanced)
- monitoring (advanced)
- backup-solutions
- security-scanning
- cost-optimization
```

**Configuration:**
```yaml
configMapGenerator:
- name: variant-config
  literals:
  - DEPLOYMENT_SIZE=medium
  - AI_INTEGRATION=false
  - MONITORING_LEVEL=advanced
  - SECURITY_LEVEL=enhanced
  - BACKUP_ENABLED=true
  - COST_OPTIMIZATION=true
```

### 3. Enterprise Variant
**Label:** `variant: enterprise`

**Characteristics:**
- Full AI integration and orchestration
- Advanced security and compliance
- Multi-cloud controllers (ACK/ASO/KCC)
- Consensus-based agent swarms
- High availability and disaster recovery
- Advanced observability and analytics
- Ideal for: Large enterprises, mission-critical workloads

**Components:**
```yaml
# Complete enterprise stack
- flux-system
- network-infra
- cluster-infra
- workload-infra (complete)
- monitoring (enterprise)
- ai-gateway
- ai-cronjobs
- consensus-agents
- multi-cloud-controllers
- advanced-security
- compliance-tools
```

**Configuration:**
```yaml
configMapGenerator:
- name: variant-config
  literals:
  - DEPLOYMENT_SIZE=large
  - AI_INTEGRATION=true
  - MONITORING_LEVEL=enterprise
  - SECURITY_LEVEL=enterprise
  - BACKUP_ENABLED=true
  - MULTI_CLOUD=true
  - CONSENSUS_ORCHESTRATION=true
```

## Swapping Between Variants

### Method 1: Label-Based Selection

Update the variant label in your kustomization.yaml:

```yaml
labels:
  - pairs:
      variant: enterprise  # Change from opensource/small-business/enterprise
```

### Method 2: Resource Inclusion/Exclusion

Comment/uncomment resources based on variant needs:

```yaml
resources:
  # Core resources (all variants)
  - ../../control-plane/
  
  # Small Business+ resources
  # - backup-solutions/
  # - security-scanning/
  
  # Enterprise only resources
  # - ai-gateway/
  # - consensus-agents/
```

### Method 3: ConfigMap Configuration

Update variant configuration:

```yaml
configMapGenerator:
- name: variant-config
  literals:
  - VARIANT=enterprise  # opensource, small-business, enterprise
  - AI_INTEGRATION=true
  - MULTI_CLOUD=true
```

## Variant Dependency Management

All variants maintain the same core DAG structure:

```
flux-system [ROOT]
    ↓ dependsOn
network-infra [ROOT]
    ↓ dependsOn
cluster-infra
    ↓ dependsOn
workload-infra
    ↓ dependsOn
variant-specific-components
```

### Variant-Specific Dependencies

**Open Source:**
- Basic monitoring depends on: workload-infra
- Standard networking depends on: network-infra

**Small Business:**
- Enhanced monitoring depends on: workload-infra
- Backup solutions depends on: cluster-infra
- Security scanning depends on: workload-infra

**Enterprise:**
- AI gateway depends on: workload-infra
- Consensus agents depends on: ai-gateway
- Multi-cloud controllers depends on: cluster-infra

## Migration Paths

### Open Source → Small Business
1. Update variant label to `small-business`
2. Enable enhanced monitoring
3. Add backup solutions
4. Configure security scanning
5. Update monitoring dashboards

### Small Business → Enterprise
1. Update variant label to `enterprise`
2. Enable AI integration
3. Add consensus orchestration
4. Deploy multi-cloud controllers
5. Configure advanced security

### Enterprise → Small Business (Downgrade)
1. Disable AI components first
2. Remove consensus agents
3. Scale down monitoring
4. Update variant label
5. Verify core functionality

## Best Practices

1. **Test in staging**: Always test variant changes in non-production environments
2. **Gradual migration**: Use phased approach when upgrading variants
3. **Backup configuration**: Export working configurations before changes
4. **Monitor dependencies**: Ensure all dependencies are properly configured
5. **Document customizations**: Keep track of variant-specific customizations

## Validation

Use the DAG validation script to ensure proper dependencies:

```bash
./scripts/generate-dag-visualization.sh | grep -A 20 "Validation"
```

Check variant-specific labels:

```bash
kubectl get kustomizations -l variant=enterprise
```

Verify component health:

```bash
kubectl get kustomizations -o wide | grep -E "(variant|dependsOn)"
```
