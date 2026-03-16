# Overlays System

This directory contains overlay extensions for the GitOps Infrastructure Control Plane. Overlays allow forks and contributors to customize and extend the platform while maintaining upstream compatibility.

## Quick Start

### Create a New Overlay

```bash
# Create a skill overlay
mkdir -p overlays/.agents/my-skill
cp overlays/templates/skill-overlay/kustomization.yaml overlays/.agents/my-skill/

# Create a dashboard overlay
mkdir -p overlays/agents/dashboard/my-theme
cp overlays/templates/dashboard-overlay/kustomization.yaml overlays/agents/dashboard/my-theme/

# Create an infrastructure overlay
mkdir -p overlays/control-plane/flux/my-config
cp overlays/templates/infra-overlay/kustomization.yaml overlays/control-plane/flux/my-config/
```

### Apply an Overlay

```bash
# Build and apply a single overlay
kustomize build overlays/.agents/ai-agent-debugger/enhanced | kubectl apply -f -

# Build composed overlays
kustomize build overlays/composed/enterprise-suite | kubectl apply -f -
```

## Directory Structure

```
overlays/
├── .agents/                # Skill overlays
│   └── ai-agent-debugger/
│       ├── enhanced/       # ML-enhanced debugging
│       └── enterprise/     # Enterprise features
├── agents/                 # Dashboard overlays
│   └── dashboard/
│       ├── themes/         # Visual themes
│       └── widgets/        # Custom widgets
├── control-plane/          # Infrastructure overlays
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

### Skill Overlays (`.agents/`)
Extend AI agent capabilities while maintaining agentskills.io compliance.

### Dashboard Overlays (`agents/dashboard/`)
Customize the React frontend experience with themes, widgets, and integrations.

### Infrastructure Overlays (`control-plane/`)
Extend Kubernetes infrastructure and GitOps components.

### Composed Overlays (`composed/`)
Combine multiple overlays into complete solutions.

## Development Guidelines

### 1. Use Templates
Start with templates from `overlays/templates/` for consistency.

### 2. Reference Base Components
Always reference base components using relative paths:
```yaml
resources:
  - ../../../../.agents/base-skill
```

### 3. Maintain Compatibility
Ensure overlays work with multiple base versions using version constraints.

### 4. Document Overlays
Include README.md and metadata for each overlay.

## Validation

```bash
# Validate overlay structure
python scripts/validate-overlays.py overlays/

# Test overlay composition
kustomize build overlays/.agents/my-overlay
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
