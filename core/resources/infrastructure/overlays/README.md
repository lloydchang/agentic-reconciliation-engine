# Overlays System

This directory contains overlay extensions for the GitOps Infrastructure Control Plane. Overlays allow forks and contributors to customize and extend the platform while maintaining upstream compatibility.

## Quick Start

### Create a New Overlay

```bash
# Create a skill overlay
mkdir -p core/deployment/overlays/core/ai/skills/my-skill
cp core/deployment/overlays/templates/skill-overlay/kustomization.yaml core/deployment/overlays/core/ai/skills/my-skill/

# Create a dashboard overlay
mkdir -p core/deployment/overlays/core/ai/runtime/dashboard/my-theme
cp core/deployment/overlays/templates/dashboard-overlay/kustomization.yaml core/deployment/overlays/core/ai/runtime/dashboard/my-theme/

# Create an infrastructure overlay
mkdir -p core/deployment/overlays/core/operators/flux/my-config
cp core/deployment/overlays/templates/infra-overlay/kustomization.yaml core/deployment/overlays/core/operators/flux/my-config/
```

### Apply an Overlay

```bash
# Build and apply a single overlay
kustomize build core/deployment/overlays/core/ai/skills/ai-agent-debugger/enhanced | kubectl apply -f -

# Build composed overlays
kustomize build core/deployment/overlays/composed/enterprise-suite | kubectl apply -f -
```

## Directory Structure

```
core/deployment/overlays/
├── core/ai/skills/                # Skill overlays
│   └── ai-agent-debugger/
│       ├── enhanced/       # ML-enhanced debugging
│       └── enterprise/     # Enterprise features
├── core/ai/runtime/                 # Dashboard overlays
│   └── dashboard/
│       ├── themes/         # Visual themes
│       └── widgets/        # Custom widgets
├── core/operators/          # Infrastructure overlays
│   └── flux/
│       └── enhanced-monitoring/
├── composed/               # Cross-component compositions
│   └── enterprise-suite/
├── registry/               # Overlay catalog
│   ├── catalog.yaml
│   └── schema.yaml
└── templates/              # Development templates
    ├── skill-overlay/
    ├── dashboard-overlay/
    └── infra-overlay/
```

## Overlay Types

### Skill Overlays (`core/ai/skills/`)
Extend AI agent capabilities while maintaining agentskills.io compliance.

### Dashboard Overlays (`core/ai/runtime/dashboard/`)
Customize the React frontend experience with themes, widgets, and integrations.

### Infrastructure Overlays (`core/operators/`)
Extend Kubernetes infrastructure and GitOps components.

### Composed Overlays (`composed/`)
Combine multiple overlays into complete solutions.

## Development Guidelines

### 1. Use Templates
Start with templates from `core/deployment/overlays/templates/` for consistency.

### 2. Reference Base Components
Always reference base components using relative paths:
```yaml
resources:
  - ../../../../core/ai/skills/base-skill
```

### 3. Maintain Compatibility
Ensure overlays work with multiple base versions using version constraints.

### 4. Document Overlays
Include README.md and metadata for each overlay.

## Validation

```bash
# Validate overlay structure
python core/core/automation/ci-cd/scripts/validate-overlays.py core/deployment/overlays/

# Test overlay composition
kustomize build core/deployment/overlays/core/ai/skills/my-overlay
```

## Community

- **Contribution Guidelines**: See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Issue Reporting**: Use GitHub Issues
- **Discussions**: Use GitHub Discussions for questions

## Documentation

- [Overlays Architecture](../docs/OVERLAYS-ARCHITECTURE.md)
- [Implementation Planning](../docs/OVERLAYS-PLANNING.md)
- [Agent Skills Specification](https://agentskills.io/specification)

## Support

For overlay-specific questions:
1. Check existing overlays for examples
2. Review templates and documentation
3. Open an issue with the `overlay` label
4. Join community discussions
