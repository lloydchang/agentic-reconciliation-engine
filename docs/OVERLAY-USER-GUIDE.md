# Overlay User Guide

Welcome to the comprehensive user guide for the Agentic Reconciliation Engine Overlay System. This guide will help you understand, create, and manage overlays effectively.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding Overlays](#understanding-overlays)
3. [Quick Start](#quick-start)
4. [Creating Overlays](#creating-overlays)
5. [Managing Overlays](#managing-overlays)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Topics](#advanced-topics)

## Getting Started

### Prerequisites

Before you begin working with overlays, ensure you have:

- **Kubernetes**: Version 1.20 or higher
- **Kustomize**: Version 4.0 or higher
- **kubectl**: Configured for your target cluster
- **Python**: Version 3.8 or higher
- **Git**: For version control

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/lloydchang/agentic-reconciliation-engine/core/operators/agentic-reconciliation-engine.git
   cd agentic-reconciliation-engine
   ```

2. **Set Up Tools**:
   ```bash
   # Make CLI tools executable
   chmod +x core/scripts/automation/*.py
   
   # Add to PATH (optional)
   export PATH="$PWD/scripts:$PATH"
   ```

3. **Verify Installation**:
   ```bash
   # Test CLI tool
   python core/scripts/automation/overlay-cli.py list
   
   # Test validation
   python core/scripts/automation/validate-overlays.py core/deployment/overlays/ --verbose
   ```

## Understanding Overlays

### What are Overlays?

Overlays are modular extensions that customize and enhance the base Agentic Reconciliation Engine without modifying the core components. They follow a layered architecture where:

- **Base Layer**: Immutable core components
- **Overlay Layer**: Customizable extensions
- **Composition Layer**: Multiple overlays combined

### Overlay Types

#### 1. Skill Overlays
Extend AI agent capabilities with new skills and enhanced functionality.

**Location**: `core/deployment/overlays/core/ai/skills/`

**Example**: Enhanced debugging with ML correlation analysis

#### 2. Dashboard Overlays
Customize the user interface with themes, widgets, and visual enhancements.

**Location**: `core/deployment/overlays/core/ai/runtime/dashboard/`

**Example**: Dark theme, cost calculator widget

#### 3. Infrastructure Overlays
Enhance infrastructure components with additional features and integrations.

**Location**: `core/deployment/overlays/core/operators/`

**Example**: Enhanced monitoring, security policies

#### 4. Composed Overlays
Combine multiple overlays into complete solutions.

**Location**: `core/deployment/overlays/composed/`

**Example**: Enterprise suite, community bundle

### Overlay Structure

Each overlay follows a consistent structure:

```
overlay-name/
├── kustomization.yaml          # Kustomize configuration
├── overlay-metadata.yaml       # Overlay metadata
├── README.md                   # Documentation (optional)
├── patches/                    # Resource patches
│   ├── enhanced-features.yaml
│   └── config-patches.yaml
├── config/                     # Configuration files
│   ├── config.json
│   └── settings.yaml
└── assets/                     # Static assets
    ├── themes.css
    └── images/
```

## Quick Start

### 1. Explore Available Overlays

```bash
# List all overlays
python core/scripts/automation/overlay-cli.py list

# List by category
python core/scripts/automation/overlay-cli.py list --category skills

# Search overlays
python core/scripts/automation/overlay-cli.py search "debugging"
```

### 2. Use an Existing Overlay

```bash
# Validate overlay
python core/scripts/automation/overlay-cli.py validate core/deployment/overlays/core/ai/skills/debug/enhanced

# Build overlay
python core/scripts/automation/overlay-cli.py build core/deployment/overlays/core/ai/skills/debug/enhanced --output enhanced.yaml

# Apply overlay (dry run)
python core/scripts/automation/overlay-cli.py apply core/deployment/overlays/core/ai/skills/debug/enhanced --dry-run

# Apply overlay to cluster
python core/scripts/automation/overlay-cli.py apply core/deployment/overlays/core/ai/skills/debug/enhanced
```

### 3. Use a Composed Overlay

```bash
# Deploy enterprise suite
kustomize build core/deployment/overlays/composed/enterprise-suite | kubectl apply -f -

# Deploy community bundle
kustomize build core/deployment/overlays/composed/community-bundle | kubectl apply -f -
```

## Creating Overlays

### 1. Create from Template

The easiest way to create an overlay is using the provided templates:

```bash
# Create skill overlay
python core/scripts/automation/overlay-cli.py create my-skill skills debug --template skill-overlay

# Create dashboard theme
python core/scripts/automation/overlay-cli.py create dark-theme dashboard themes --template dashboard-overlay

# Create infrastructure overlay
python core/scripts/automation/overlay-cli.py create enhanced-infra infrastructure flux --template infra-overlay
```

### 2. Manual Overlay Creation

If you prefer to create an overlay manually:

#### Step 1: Create Directory Structure

```bash
mkdir -p core/deployment/overlays/core/ai/skills/my-skill/{patches,config,assets}
```

#### Step 2: Create Kustomization

```yaml
# core/deployment/overlays/core/ai/skills/my-skill/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-skill
  namespace: flux-system
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/enhanced-features.yaml
configMapGenerator:
  - name: my-skill-config
    literals:
      - OVERLAY_ENABLED=true
```

#### Step 3: Create Metadata

```yaml
# core/deployment/overlays/core/ai/skills/my-skill/overlay-metadata.yaml
---
name: my-skill
version: "1.0.0"
description: "My custom skill overlay"
category: skills
base_path: "core/ai/skills/debug"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto
maintainer:
  name: "Your Name"
  email: "your.email@example.com"
tags:
  - skills
  - custom
  - my-skill
```

#### Step 4: Add Patches

```yaml
# core/deployment/overlays/core/ai/skills/my-skill/patches/enhanced-features.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-skill-enhanced-config
data:
  enhanced_features.yaml: |
    # Your enhanced configuration
    enabled: true
    features:
      - feature1
      - feature2
```

### 3. Validate Your Overlay

```bash
# Validate structure and metadata
python core/scripts/automation/validate-overlays.py core/deployment/overlays/core/ai/skills/my-skill

# Test functionality
python core/scripts/automation/test-overlays.py core/deployment/overlays/core/ai/skills/my-skill

# Build to verify
python core/scripts/automation/overlay-cli.py build core/deployment/overlays/core/ai/skills/my-skill
```

## Managing Overlays

### 1. Registry Management

The overlay registry provides discovery and catalog management:

```bash
# Initialize registry
python core/scripts/automation/overlay-registry.py init

# Register your overlay
python core/scripts/automation/overlay-registry.py register core/deployment/overlays/core/ai/skills/my-skill

# Search registry
python core/scripts/automation/overlay-registry.py search "my-skill"

# List all overlays
python core/scripts/automation/overlay-registry.py list
```

### 2. Version Management

Overlays use semantic versioning:

```yaml
# overlay-metadata.yaml
version: "1.0.0"
```

Version update process:
1. Update version in metadata
2. Test changes
3. Update registry
4. Tag release

```bash
# Update version
sed -i 's/version: "1.0.0"/version: "1.1.0"/' overlay-metadata.yaml

# Test changes
python core/scripts/automation/test-overlays.py core/deployment/overlays/core/ai/skills/my-skill

# Update registry
python core/scripts/automation/overlay-registry.py register core/deployment/overlays/core/ai/skills/my-skill

# Tag release
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

### 3. Dependency Management

Overlays can depend on other overlays:

```yaml
# overlay-metadata.yaml
dependencies:
  - name: "base-skill"
    version: ">=1.0.0"
    optional: false
  - name: "enhanced-monitoring"
    version: ">=2.0.0"
    optional: true
```

### 4. Composition

Create composed overlays to combine multiple overlays:

```yaml
# core/deployment/overlays/composed/my-bundle/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-bundle
resources:
  - ../../../../control-plane
  - ../core/ai/skills/my-skill
  - ../core/ai/runtime/dashboard/my-theme
  - ../core/operators/my-enhancement
```

## Best Practices

### 1. Development Workflow

#### Before You Start
- Understand the base components you're extending
- Review existing overlays for patterns
- Plan your overlay structure

#### During Development
- Use templates for consistency
- Validate frequently
- Test incrementally
- Document as you go

#### Before Release
- Run full validation suite
- Test in multiple environments
- Update documentation
- Register in catalog

### 2. Naming Conventions

#### Overlay Names
- Use lowercase letters and hyphens
- Be descriptive but concise
- Include category prefix if helpful

```
Good: debug-enhanced
Good: dashboard-dark-theme
Good: infrastructure-monitoring-enhanced

Bad: MyOverlay
Bad: overlay_v2
Bad: temp-fix
```

#### File Names
- Use kebab-case for files
- Be descriptive of content
- Follow existing patterns

### 3. Metadata Standards

#### Required Fields
```yaml
name: "overlay-name"
version: "1.0.0"
description: "Clear, concise description"
category: "skills|dashboard|infrastructure|composed"
license: "AGPLv3|MIT|Apache-2.0"
risk_level: "low|medium|high"
autonomy: "fully_auto|conditional|requires_pr"
```

#### Recommended Fields
```yaml
maintainer:
  name: "Your Name"
  email: "your.email@example.com"
  organization: "Your Organization"
tags:
  - relevant-tag
  - another-tag
compatibility:
  min_base: "main"
  kubernetes: ">=1.20"
```

### 4. Security Considerations

#### Risk Assessment
- **Low**: Read-only operations, no resource changes
- **Medium**: Resource modifications, limited scope
- **High**: Critical infrastructure changes, broad impact

#### Autonomy Levels
- **fully_auto**: No human approval required
- **conditional**: Approval required for production
- **requires_pr**: Always requires approval

#### Security Best Practices
- Validate all inputs
- Use least privilege principle
- Audit all changes
- Monitor resource usage

### 5. Testing Strategy

#### Unit Testing
- Validate YAML syntax
- Check metadata compliance
- Test individual components

#### Integration Testing
- Test overlay composition
- Validate resource generation
- Check cluster compatibility

#### End-to-End Testing
- Deploy in test environment
- Verify functionality
- Monitor resource usage

```bash
# Run comprehensive tests
python core/scripts/automation/test-overlays.py core/deployment/overlays/core/ai/skills/my-skill --verbose

# Test composition
python core/scripts/automation/test-overlays.py core/deployment/overlays/composed/my-bundle

# Integration test
kustomize build core/deployment/overlays/core/ai/skills/my-skill | kubectl apply --dry-run=client -f -
```

## Troubleshooting

### Common Issues

#### 1. Validation Failures

**Problem**: Overlay validation fails
```bash
❌ ERRORS (2):
  - Missing required file: overlay-metadata.yaml
  - Invalid YAML in kustomization.yaml
```

**Solution**:
```bash
# Check required files
ls -la core/deployment/overlays/core/ai/skills/my-skill/

# Validate YAML syntax
yamllint core/deployment/overlays/core/ai/skills/my-skill/*.yaml

# Use template for correct structure
python core/scripts/automation/overlay-cli.py create my-skill skills debug --template skill-overlay
```

#### 2. Build Failures

**Problem**: Kustomize build fails
```bash
Error: accumulating resources: couldn't make target for path
```

**Solution**:
```bash
# Check resource paths
find core/deployment/overlays/core/ai/skills/my-skill -name "*.yaml"

# Validate relative paths
kustomize build core/deployment/overlays/core/ai/skills/my-skill --enable-alpha-plugins

# Fix resource references
# Update kustomization.yaml with correct paths
```

#### 3. Dependency Issues

**Problem**: Overlay dependencies not resolved
```bash
❌ ERRORS (1):
  - Dependency not found: required-skill
```

**Solution**:
```bash
# Check available overlays
python core/scripts/automation/overlay-registry.py list

# Verify dependency names
python core/scripts/automation/overlay-registry.py get required-skill

# Update dependency version
# Edit overlay-metadata.yaml with correct dependency
```

#### 4. Composition Conflicts

**Problem**: Multiple overlays conflict
```bash
Error: resource name already used
```

**Solution**:
```bash
# Check for conflicts
python core/scripts/automation/test-overlays.py core/deployment/overlays/composed/my-bundle

# Use namespacing
# Add unique prefixes or use different namespaces

# Resolve conflicts
# Modify overlays to use different resource names
```

### Debug Commands

#### 1. Validation Debugging
```bash
# Verbose validation
python core/ooretomation/ci/ci-cd/scripts-cd/scripts/validate-overlays.py core/deployment/overlays/core/ai/skills/my-skill --verbose

# Check specific overlay
python core/ooretomation/ci/ci-cd/scripts-cd/scripts/validate-overlays.py core/deployment/overlays/core/ai/skills/my-skill --report debug-report.json
```

#### 2. Build Debugging
```bash
# Debug kustomize build
kustomize build core/deployment/overlays/core/ai/skills/my-skill --enable-alpha-plugins

# Check resources
kustomize build core/deployment/overlays/core/ai/skills/my-skill | grep "kind:"
```

#### 3. Cluster Debugging
```bash
# Dry run application
kustomize build core/deployment/overlays/core/ai/skills/my-skill | kubectl apply --dry-run=client -f -

# Check cluster state
kubectl get all -n flux-system
kubectl describe deployment my-skill -n flux-system
```

### Getting Help

1. **Documentation**: Check this guide and tooling documentation
2. **Examples**: Review existing overlays in the repository
3. **Templates**: Use provided templates as starting points
4. **Community**: Open an issue with detailed information
5. **Validation**: Use validation tools for specific error messages

## Advanced Topics

### 1. Custom Overlay Types

While the system supports four main overlay types, you can create custom patterns:

```yaml
# Custom overlay type example
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: custom-integration
  annotations:
    overlay.type: "custom"
    overlay.integration: "external-system"
resources:
  - base-components
  - custom-resources
patchesStrategicMerge:
  - integration-patches.yaml
```

### 2. Multi-Cluster Overlays

Deploy overlays across multiple clusters:

```yaml
# Multi-cluster configuration
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-cluster-overlay
resources:
  - base-resources
patchesStrategicMerge:
  - cluster-specific/
configurations:
  - cluster-configs/
```

### 3. Dynamic Configuration

Use ConfigMaps and Secrets for dynamic configuration:

```yaml
# Dynamic configuration
configMapGenerator:
  - name: dynamic-config
    envs:
      - .env.config
    literals:
      - FEATURE_ENABLED=true
      - LOG_LEVEL=info
secretGenerator:
  - name: dynamic-secrets
    envs:
      - .env.secrets
```

### 4. Performance Optimization

Optimize overlay performance:

```yaml
# Resource optimization
commonLabels:
  app.kubernetes.io/name: my-overlay
  app.kubernetes.io/version: "1.0.0"
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "100m"
            memory: "128Mi"
```

### 5. Monitoring and Observability

Add monitoring to overlays:

```yaml
# Monitoring configuration
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-overlay-monitor
spec:
  selector:
    matchLabels:
      overlay: my-overlay
  endpoints:
  - port: metrics
    interval: 30s
```

### 6. Security Enhancements

Add security features to overlays:

```yaml
# Security policies
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: my-overlay-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
```

## Next Steps

Now that you understand overlays, you can:

1. **Explore Examples**: Review existing overlays in the repository
2. **Create Your Own**: Use templates to create custom overlays
3. **Join Community**: Contribute overlays and improvements
4. **Advanced Topics**: Explore complex compositions and integrations
5. **Stay Updated**: Follow the project for new features and updates

## Resources

- [Architecture Documentation](OVERLAY-ARCHITECTURE.md)
- [Planning Document](OVERLAY-PLANNING.md)
- [Tooling Guide](OVERLAY-TOOLING.md)
- [GitHub Repository](https://github.com/agentic-reconciliation-engine)
- [Community Forum](https://github.com/lloydchang/agentic-reconciliation-engine/core/operators/discussions)
- [Issue Tracker](https://github.com/lloydchang/agentic-reconciliation-engine/core/operators/issues)

---

Happy overlay building! 🚀
