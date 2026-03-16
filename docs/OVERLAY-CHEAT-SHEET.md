# Overlay Cheat Sheet

Quick reference for common overlay operations and commands.

## Table of Contents

1. [Quick Start](#quick-start)
2. [CLI Commands](#cli-commands)
3. [Registry Commands](#registry-commands)
4. [Validation Commands](#validation-commands)
5. [Testing Commands](#testing-commands)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)
8. [File Templates](#file-templates)

## Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/gitops-infra-control-plane/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# Setup tools
chmod +x scripts/*.py
export PATH="$PWD/scripts:$PATH"

# Verify installation
python scripts/overlay-cli.py list
```

### Create First Overlay
```bash
# Create skill overlay
python scripts/overlay-cli.py create my-skill skills base-skill --template skill-overlay

# Test overlay
cd overlays/.agents/my-skill
python scripts/validate-overlays.py .
python scripts/test-overlays.py .

# Build and apply
python scripts/overlay-cli.py build . --output my-skill.yaml
python scripts/overlay-cli.py apply . --dry-run
```

## CLI Commands

### List Overlays
```bash
# List all overlays
python scripts/overlay-cli.py list

# List by category
python scripts/overlay-cli.py list --category skills
python scripts/overlay-cli.py list --category dashboard
python scripts/overlay-cli.py list --category infrastructure
python scripts/overlay-cli.py list --category composed

# Different output formats
python scripts/overlay-cli.py list --format table
python scripts/overlay-cli.py list --format json
python scripts/overlay-cli.py list --format yaml
```

### Create Overlays
```bash
# Skill overlay
python scripts/overlay-cli.py create my-skill skills base-skill --template skill-overlay

# Dashboard theme
python scripts/overlay-cli.py create dark-theme dashboard themes --template dashboard-overlay

# Infrastructure overlay
python scripts/overlay-cli.py create enhanced-infra infrastructure flux --template infra-overlay

# Composed overlay
python scripts/overlay-cli.py create my-bundle composed ""
```

### Validate Overlays
```bash
# Validate specific overlay
python scripts/overlay-cli.py validate overlays/.agents/my-skill

# Validate all overlays
python scripts/overlay-cli.py validate overlays/

# Verbose validation
python scripts/validate-overlays.py overlays/.agents/my-skill --verbose
```

### Test Overlays
```bash
# Test specific overlay
python scripts/overlay-cli.py test overlays/.agents/my-skill

# Test all overlays
python scripts/overlay-cli.py test overlays/

# Verbose testing
python scripts/test-overlays.py overlays/.agents/my-skill --verbose
```

### Build Overlays
```bash
# Build overlay
python scripts/overlay-cli.py build overlays/.agents/my-skill

# Save to file
python scripts/overlay-cli.py build overlays/.agents/my-skill --output my-skill.yaml

# Build composed overlay
python scripts/overlay-cli.py build overlays/composed/my-bundle
```

### Apply Overlays
```bash
# Apply overlay (dry run)
python scripts/overlay-cli.py apply overlays/.agents/my-skill --dry-run

# Apply to cluster
python scripts/overlay-cli.py apply overlays/.agents/my-skill

# Apply composed overlay
python scripts/overlay-cli.py apply overlays/composed/my-bundle
```

### Search Overlays
```bash
# Search by name or description
python scripts/overlay-cli.py search "debugging"
python scripts/overlay-cli.py search "ml"
python scripts/overlay-cli.py search "monitoring"

# Search by tags
python scripts/overlay-cli.py search "enhanced" --tags machine-learning
python scripts/overlay-cli.py search "security" --tags compliance audit

# Search with filters
python scripts/overlay-cli.py search "enterprise" --category composed
```

### Update Catalog
```bash
# Update overlay catalog
python scripts/overlay-cli.py update-catalog
```

## Registry Commands

### Initialize Registry
```bash
# Create new registry
python scripts/overlay-registry.py init

# Custom registry location
python scripts/overlay-registry.py init --registry-dir /path/to/registry
```

### Register Overlays
```bash
# Register overlay
python scripts/overlay-registry.py register overlays/.agents/my-skill

# Register with custom metadata
python scripts/overlay-registry.py register overlays/.agents/my-skill --metadata custom-metadata.yaml
```

### Search Registry
```bash
# Search overlays
python scripts/overlay-registry.py search "debugging"

# Filter by category
python scripts/overlay-registry.py search "enhanced" --category skills

# Filter by risk level
python scripts/overlay-registry.py search "enterprise" --risk-level medium
```

### List Overlays
```bash
# List all overlays
python scripts/overlay-registry.py list

# Filter by category
python scripts/overlay-registry.py list --category skills

# Sort by version
python scripts/overlay-registry.py list --sort version
```

### Get Overlay Details
```bash
# Get overlay metadata
python scripts/overlay-registry.py get my-skill
python scripts/overlay-registry.py get debug-enhanced
```

### Validate Registry
```bash
# Validate registry integrity
python scripts/overlay-registry.py validate
```

### Export/Import Registry
```bash
# Export registry
python scripts/overlay-registry.py export registry-backup.yaml
python scripts/overlay-registry.py export registry-backup.json --format json

# Import registry (merge)
python scripts/overlay-registry.py import registry-backup.yaml

# Import registry (replace)
python scripts/overlay-registry.py import registry-backup.yaml --replace
```

## Validation Commands

### Basic Validation
```bash
# Validate single overlay
python scripts/validate-overlays.py overlays/.agents/my-skill

# Validate all overlays
python scripts/validate-overlays.py overlays/

# Verbose output
python scripts/validate-overlays.py overlays/ --verbose
```

### Generate Reports
```bash
# Generate validation report
python scripts/validate-overlays.py overlays/ --report validation-report.json

# Generate HTML report
python scripts/validate-overlays.py overlays/ --report validation-report.html
```

### Schema Validation
```bash
# Validate against schema only
python scripts/validate-overlays.py overlays/.agents/my-skill --schema-only

# Validate agentskills.io compliance only
python scripts/validate-overlays.py overlays/.agents/my-skill --agentskills-only
```

## Testing Commands

### Basic Testing
```bash
# Test single overlay
python scripts/test-overlays.py overlays/.agents/my-skill

# Test all overlays
python scripts/test-overlays.py overlays/

# Verbose output
python scripts/test-overlays.py overlays/ --verbose
```

### Specific Test Types
```bash
# Test structure only
python scripts/test-overlays.py overlays/.agents/my-skill --test-structure

# Test composition only
python scripts/test-overlays.py overlays/.agents/my-skill --test-composition

# Test dependencies only
python scripts/test-overlays.py overlays/.agents/my-skill --test-dependencies
```

### Test Reports
```bash
# Generate test report
python scripts/test-overlays.py overlays/ --report test-report.json

# Generate coverage report
python scripts/test-overlays.py overlays/ --coverage
```

## Common Patterns

### Skill Overlay Structure
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-skill-enhanced
  namespace: flux-system
resources:
  - ../../../../.agents/base-skill
patchesStrategicMerge:
  - patches/enhanced-features.yaml
configMapGenerator:
  - name: my-skill-config
    literals:
      - OVERLAY_ENABLED=true
      - ENHANCED_FEATURES=true
```

### Dashboard Theme Structure
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: dark-theme
  namespace: flux-system
resources:
  - ../../../../../agents/dashboard
patchesStrategicMerge:
  - patches/theme-patches.yaml
configMapGenerator:
  - name: dark-theme-config
    files:
      - theme/dark.css
      - theme/dark.json
```

### Composed Overlay Structure
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: enterprise-bundle
  namespace: flux-system
resources:
  - ../../../../control-plane
  - ../.agents/skill-enhanced
  - ../agents/dashboard/theme-dark
  - ../control-plane/monitoring-enhanced
```

### Resource Patch Pattern
```yaml
# patches/enhanced-features.yaml
---
# Enhanced ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: enhanced-config
data:
  enhanced_features.yaml: |
    enabled: true
    features:
      - feature1
      - feature2

---
# Enhanced Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: base-deployment
spec:
  template:
    spec:
      containers:
      - name: container
        env:
        - name: ENHANCED_FEATURES
          value: "true"
```

### JSON6902 Patch Pattern
```yaml
# kustomization.yaml
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: my-deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: NEW_VAR
          value: "value"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "512Mi"
```

## Troubleshooting

### Common Issues
```bash
# Check overlay structure
ls -la overlays/.agents/my-skill/

# Validate YAML syntax
yamllint overlays/.agents/my-skill/*.yaml

# Check resource paths
find overlays/.agents/my-skill -name "*.yaml"

# Test kustomize build
kustomize build overlays/.agents/my-skill --enable-alpha-plugins

# Check dependencies
python scripts/test-overlays.py overlays/.agents/my-skill --test-dependencies
```

### Debug Commands
```bash
# Verbose validation
python scripts/validate-overlays.py overlays/.agents/my-skill --verbose

# Debug build
kustomize build overlays/.agents/my-skill --enable-alpha-plugins --v 6

# Check cluster state
kubectl get all -n flux-system
kubectl describe deployment my-skill -n flux-system

# Check logs
kubectl logs -n flux-system deployment/my-skill
```

### Recovery Commands
```bash
# Reset overlay state
git checkout overlays/.agents/my-skill/kustomization.yaml

# Remove overlay
rm -rf overlays/.agents/my-skill

# Re-create from template
python scripts/overlay-cli.py create my-skill skills base-skill --template skill-overlay
```

## File Templates

### overlay-metadata.yaml Template
```yaml
---
name: overlay-name
version: "1.0.0"
description: "Brief description of overlay"
category: skills|dashboard|infrastructure|composed
base_path: "path/to/base/component"
license: "AGPLv3"
risk_level: low|medium|high
autonomy: fully_auto|conditional|requires_pr

maintainer:
  name: "Your Name"
  email: "your.email@example.com"
  organization: "Your Organization"

tags:
  - relevant-tag
  - another-tag

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"

dependencies:
  - name: "dependency-name"
    version: ">=1.0.0"
    optional: false

examples:
  - name: "Example usage"
    description: "Description of example"
    command: "command to run"
    expected_output: "Expected result"

resources:
  cpu: "100m"
  memory: "256Mi"

human_gate:
  required: false
  description: "Human approval requirements"
```

### kustomization.yaml Template
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: overlay-name
  namespace: flux-system
  annotations:
    overlay.name: "overlay-name"
    overlay.version: "1.0.0"
    overlay.category: "skills"

resources:
  # Reference to base component
  - ../../../../path/to/base/component

# Patches to modify or extend base functionality
patchesStrategicMerge:
  - patches/enhanced-features.yaml
  - patches/config-patches.yaml

# Additional configurations
configMapGenerator:
  - name: overlay-name-config
    literals:
      - OVERLAY_ENABLED=true
      - OVERLAY_VERSION="1.0.0"

# Secret generation for sensitive data
secretGenerator:
  - name: overlay-name-secrets
    envs:
      - .env.secret

# Common labels for overlay resources
commonLabels:
  overlay: "overlay-name"
  overlay-type: "skills"
  managed-by: "kustomize"

# Namespace configuration
namespace: flux-system

# Images for overlay (if custom containers needed)
images:
  - name: python
    newTag: "3.11-slim"
```

### README.md Template
```markdown
# Overlay Name

Brief description of what this overlay does.

## Overview
Detailed description of overlay functionality.

## Prerequisites
List any prerequisites or dependencies.

## Installation
How to install and use the overlay.

## Configuration
Configuration options and their meanings.

## Examples
Usage examples and commands.

## Troubleshooting
Common issues and solutions.

## Support
How to get help and report issues.
```

## Quick Reference

### One-Liners
```bash
# List all overlays
python scripts/overlay-cli.py list

# Create new overlay
python scripts/overlay-cli.py create my-overlay skills base-skill --template skill-overlay

# Validate overlay
python scripts/validate-overlays.py overlays/.agents/my-overlay

# Test overlay
python scripts/test-overlays.py overlays/.agents/my-overlay

# Build overlay
python scripts/overlay-cli.py build overlays/.agents/my-overlay --output overlay.yaml

# Apply overlay
python scripts/overlay-cli.py apply overlays/.agents/my-overlay --dry-run

# Search overlays
python scripts/overlay-cli.py search "keyword"

# Update catalog
python scripts/overlay-registry.py update-catalog
```

### Common Commands
```bash
# Development workflow
python scripts/overlay-cli.py create my-overlay skills base-skill --template skill-overlay
cd overlays/.agents/my-overlay
# ... make changes ...
python scripts/validate-overlays.py .
python scripts/test-overlays.py .
python scripts/overlay-registry.py register .

# Production deployment
python scripts/validate-overlays.py overlays/.agents/my-overlay
python scripts/test-overlays.py overlays/.agents/my-overlay
python scripts/overlay-cli.py build overlays/.agents/my-overlay --output production.yaml
kubectl apply -f production.yaml

# Troubleshooting
python scripts/validate-overlays.py overlays/.agents/my-overlay --verbose
python scripts/test-overlays.py overlays/.agents/my-overlay --verbose
kustomize build overlays/.agents/my-overlay --enable-alpha-plugins
```

---

## Need More Help?

- **[User Guide](OVERLAY-USER-GUIDE.md)**: Complete documentation
- **[Developer Guide](OVERLAY-DEVELOPER-GUIDE.md)**: Development guidelines
- **[FAQ](OVERLAY-FAQ.md)**: Frequently asked questions
- **[Examples](OVERLAY-EXAMPLES.md)**: Real-world examples

---

*Last updated: March 2026*
