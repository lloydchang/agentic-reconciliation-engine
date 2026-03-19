# Overlay Architecture

## Overview

The Overlays Architecture provides a layered system for extending and customizing the GitOps Infrastructure Control Plane while maintaining compatibility with upstream updates. This architecture enables forks to add custom functionality, themes, integrations, and entirely new components without modifying the base repository.

## Architecture Principles

### 1. **Layer Separation**
- **Base Layer**: Core components (immutable, upstream-controlled)
- **Overlay Layer**: Extensions and customizations (fork-specific)
- **Composition Layer**: Combined deployments (Kustomize-based)

### 2. **Mirror Structure**
Overlays mirror the base directory structure for intuitive mapping:

```
Base Components                    Overlay Extensions
core/ai/skills/debug/    →  overlay/ai/skills/debug/
core/ai/runtime/dashboard/               →  overlay/ai/runtime/dashboard/
core/operators/flux/             →  overlay/operators/control-plane/flux/
```

### 3. **Composition Over Modification**
Instead of modifying base files, overlays compose new configurations using:
- Kustomize patches and merges
- ConfigMap and Secret generation
- Resource augmentation and replacement

## Directory Structure

```
agentic-reconciliation-engine/
├── core/                           # Base components (upstream)
│   ├── ai/skills/                  # Base skills
│   ├── ai/runtime/                 # Base dashboard
│   ├── operators/                  # Base infrastructure
│   ├── automation/                  # Base automation
│   ├── config/                      # Base configuration
│   ├── deployment/                  # Base deployment
│   ├── governance/                  # Base governance
│   ├── resources/                   # Base resources
│   └── workspace/                   # Base workspace
├── overlay/                        # Overlay extensions (fork-specific)
│   ├── ai/skills/                   # Skill overlays
│   │   ├── debug/
│   │   │   ├── enhanced/            # ML-enhanced debugging
│   │   │   ├── enterprise/          # Enterprise features
│   │   │   └── custom/              # Custom implementations
│   │   └── new-skills/              # Entirely new skills
│   ├── ai/runtime/                 # Dashboard overlays
│   │   └── dashboard/
│   │       ├── themes/              # Visual themes
│   │       ├── widgets/             # Custom widgets
│   │       └── integrations/        # External integrations
│   ├── operators/                   # Infrastructure overlays
│   │   ├── control-plane/
│   │   │   ├── flux/                # Flux customizations
│   │   │   ├── monitoring/          # Monitoring extensions
│   │   │   └── new-controllers/     # New infrastructure
│   │   └── crossplane/              # Crossplane overlays
│   ├── automation/                  # Automation overlays
│   │   ├── ci-cd/                   # CI/CD overlays
│   │   ├── scripts/                 # Script overlays
│   │   └── testing/                 # Testing overlays
│   ├── config/                      # Configuration overlays
│   │   ├── kind/                    # Kind cluster overlays
│   │   ├── kubeconfigs/             # Kubeconfig overlays
│   │   └── sops/                    # SOPS overlays
│   ├── deployment/                  # Deployment overlays
│   │   ├── overlays/                # Environment-specific overlays
│   │   └── templates/               # Deployment templates
│   ├── governance/                  # Governance overlays
│   │   ├── policies/                # Policy overlays
│   │   └── scripts/                 # Governance scripts
│   ├── resources/                   # Resource overlays
│   │   ├── infrastructure/          # Infrastructure resources
│   │   ├── applications/            # Application resources
│   │   └── monitoring/              # Monitoring resources
│   ├── workspace/                   # Workspace overlays
│   │   ├── workspace/               # Workspace configurations
│   │   └── templates/               # Workspace templates
│   ├── editions/                    # Edition collections
│   │   ├── enterprise/              # Enterprise edition
│   │   ├── opensource/              # Open source edition
│   │   └── languages/               # Language-specific
│   │       ├── csharp/
│   │       ├── go/
│   │       ├── java/
│   │       ├── python/
│   │       ├── rust/
│   │       └── typescript/
│   ├── examples/                    # Complete examples
│   │   ├── complete-hub-spoke/
│   │   ├── complete-hub-spoke-consensus/
│   │   ├── complete-hub-spoke-kagent/
│   │   ├── complete-hub-spoke-temporal/
│   │   └── template-multi-cloud/
│   └── registry/                    # Overlay catalog and discovery
│       ├── catalog.yaml             # Available overlays
│       └── templates/               # Overlay templates
└── docs/                           # Documentation
    ├── OVERLAY-ARCHITECTURE.md
    └── OVERLAY-PLANNING.md
```

## Overlay Types

### 1. **Skill Overlays** (`overlay/ai/skills/`)
Extend AI agent capabilities while maintaining agentskills.io compliance.

**Examples:**
- Enhanced debugging with ML correlation
- Multi-cloud provisioning extensions
- Custom optimization algorithms
- Industry-specific compliance checks

**Structure:**
```
overlay/ai/skills/debug/enhanced/
├── kustomization.yaml          # Overlay composition
├── SKILL.md                   # Extended skill definition
├── core/automation/ci-cd/scripts/
│   ├── main.py               # Enhanced main script
│   ├── ml_correlation.py     # New ML capabilities
│   └── enhanced_handler.py   # Extended handlers
└── config/
    └── enhanced-config.yaml   # Additional configuration
```

### 2. **Dashboard Overlays** (`overlay/ai/runtime/dashboard/`)
Customize the React frontend experience.

**Examples:**
- Dark mode and custom themes
- Organization-specific widgets
- External service integrations
- Custom navigation and layouts

**Structure:**
```
overlay/ai/runtime/dashboard/themes/dark-mode/
├── kustomization.yaml          # Theme composition
├── config/
│   └── theme-config.yaml      # Theme configuration
├── assets/
│   ├── dark-theme.css         # Custom styles
│   └── custom-logo.svg        # Branding assets
└── patches/
    └── deployment-patch.yaml  # Deployment modifications
```

### 3. **Infrastructure Overlays** (`overlay/operators/`)
Extend Kubernetes infrastructure and GitOps components.

**Examples:**
- Enhanced monitoring with custom metrics
- Additional cloud provider integrations
- Security hardening configurations
- Custom controllers and operators

**Structure:**
```
overlay/operators/control-plane/flux/enhanced-monitoring/
├── kustomization.yaml          # Infrastructure composition
├── config/
│   └── monitoring-config.yaml  # Monitoring configuration
├── controllers/
│   └── custom-metrics.yaml     # Custom metric definitions
└── patches/
    └── flux-patch.yaml         # Flux modifications
```

### 4. **Composed Overlays** (`overlay/examples/`)
Combine multiple overlays into complete solutions.

**Examples:**
- Enterprise suite (security + compliance + monitoring)
- Community bundle (popular features)
- Industry-specific solutions

**Structure:**
```
overlay/examples/enterprise-suite/
├── kustomization.yaml          # Master composition
├── components/                 # Component references
│   ├── skills.yaml            # Skill overlay references
│   ├── dashboard.yaml         # Dashboard overlay references
│   └── infrastructure.yaml    # Infrastructure overlay references
└── config/
    └── enterprise-config.yaml  # Enterprise configuration
```

## Composition Patterns

### 1. **Kustomize-Based Composition**
```yaml
# overlay/ai/skills/debug/enhanced/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: debug-enhanced
resources:
  - ../../../../core/ai/skills/debug  # Base reference
patchesStrategicMerge:
  - enhanced-features.yaml                 # Feature patches
configMapGenerator:
  - name: enhanced-debugger-config
    literals:
      - ML_CORRELATION=true
      - ADVANCED_ANALYSIS=true
```

### 2. **Cross-Component Composition**
```yaml
# overlay/examples/enterprise-suite/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: enterprise-suite
resources:
  # Base components
  - ../../.agents
  - ../../agents
  - ../../control-plane
  # Overlay components
  - ../ai/skills/debug/enterprise
  - ../ai/runtime/dashboard/themes/corporate
  - ../operators/control-plane/flux/enhanced-monitoring
```

### 3. **Layer Composition**
```yaml
# overlay/registry/catalog.yaml
apiVersion: v1
kind: OverlayRegistry
metadata:
  name: overlay-catalog
overlays:
  - category: skills
    base_path: "core/ai/skills/debug"
    overlays:
      - name: enhanced
        path: "overlay/ai/skills/debug/enhanced"
        description: "ML-enhanced debugging capabilities"
        dependencies:
          - scikit-learn>=1.0.0
          - pandas>=1.3.0
        compatibility:
          - base: ">=1.0.0"
          - agentskills.io: ">=1.0"
```

## Implementation Guidelines

### 1. **Base Component References**
Always reference base components using relative paths:
```yaml
resources:
  - ../../../../core/ai/skills/base-skill    # Correct
  # NOT: absolute paths or copied files
```

### 2. **Schema Compatibility**
Maintain compatibility with base schemas:
```yaml
# Extend, don't replace base schemas
input_schema:
  allOf:
    - $ref: "../../base-schema.yaml"
    - type: object
      properties:
        enhanced_feature:
          type: boolean
          default: true
```

### 3. **Version Management**
Track overlay versions and compatibility:
```yaml
metadata:
  name: enhanced-debugger
  version: "2.0.0"
  base_version: "1.0.0"
  compatibility:
    min_base: "1.0.0"
    max_base: "1.9.9"
```

## Fork Management

### 1. **Fork Structure**
```bash
my-fork/
├── core/                           # Base (upstream, read-only)
│   ├── ai/skills/
│   ├── ai/runtime/
│   ├── operators/
│   ├── automation/
│   ├── config/
│   ├── deployment/
│   ├── governance/
│   ├── resources/
│   └── workspace/
├── overlay/                        # Customizations (active)
│   ├── ai/skills/
│   │   └── debug/
│   │       └── my-org-enhancements/
│   ├── ai/runtime/
│   │   └── dashboard/
│   │       └── my-org-theme/
│   └── operators/
│       └── control-plane/
│           └── flux/
│               └── my-org-config/
└── README.md                       # Document overlay strategy
```

### 2. **Update Workflow**
```bash
# Update base components
git remote add upstream https://github.com/original/repo.git
git fetch upstream
git merge upstream/main

# Resolve any overlay conflicts
cd overlay/ai/skills/debug/my-enhancements/
# Update overlay compatibility if needed

# Test composition
kustomize build overlay/examples/my-org-suite/
```

### 3. **Distribution**
Forks can share overlays through:
- Git submodules
- Overlay registries
- Package managers (Helm charts, Kustomize packages)
- Container images

## Benefits

### 1. **Upstream Compatibility**
- Base components remain untouched
- Easy to merge upstream updates
- Clear separation of customizations

### 2. **Community Ecosystem**
- Share overlays with other forks
- Build on community contributions
- Collaborative development

### 3. **Maintainability**
- Organized structure
- Clear ownership
- Version tracking

### 4. **Flexibility**
- Customize any component
- Combine multiple overlays
- Create complete solutions

## Best Practices

### 1. **Naming Conventions**
- Use descriptive names: `enhanced-debugger`, `dark-theme`
- Include category prefixes: `skill-`, `dashboard-`, `infra-`
- Version overlays: `v1.0.0`, `v2.0.0`

### 2. **Documentation**
- Document overlay purpose and usage
- Include compatibility information
- Provide examples and templates

### 3. **Testing**
- Test overlays with multiple base versions
- Validate schema compatibility
- Test composition scenarios

### 4. **Security**
- Validate overlay security
- Check for malicious code
- Maintain compliance requirements

## Migration Path

### 1. **Phase 1: Foundation**
- Create overlays directory structure
- Implement overlay templates
- Document overlay patterns

### 2. **Phase 2: Migration**
- Migrate existing variants to overlays
- Convert custom components to overlays
- Update documentation

### 3. **Phase 3: Ecosystem**
- Build overlay registry
- Implement overlay distribution
- Foster community contributions

## Conclusion

The Overlays Architecture provides a powerful, flexible system for extending the GitOps Infrastructure Control Plane while maintaining upstream compatibility. This approach enables forks to customize every aspect of the system - from AI skills to dashboard themes to infrastructure components - while preserving the ability to merge upstream improvements and participate in the community ecosystem.

The mirror structure ensures intuitive mapping between base and overlay components, while Kustomize-based composition provides robust, declarative overlay application. This architecture scales from simple customizations to complex enterprise solutions, making it suitable for individual developers, organizations, and the broader community.
