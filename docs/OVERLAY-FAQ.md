# Overlay FAQ

Frequently asked questions about the GitOps Infrastructure Control Plane Overlay System.

## Table of Contents

1. [General Questions](#general-questions)
2. [Getting Started](#getting-started)
3. [Overlay Development](#overlay-development)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Topics](#advanced-topics)
6. [Community](#community)

## General Questions

### Q: What are overlays?

**A**: Overlays are modular extensions that customize and enhance the base GitOps Infrastructure Control Plane without modifying the core components. They follow a layered architecture where overlays sit on top of immutable base components, providing customization, new features, and integrations.

### Q: Why use overlays instead of modifying the base?

**A**: Overlays provide several advantages:
- **Upstream Compatibility**: Easy to merge upstream updates
- **Modularity**: Separate concerns and features
- **Reusability**: Share overlays across environments
- **Testing**: Test overlays independently
- **Rollback**: Easy to disable or remove overlays

### Q: What types of overlays are available?

**A**: Four main types:
- **Skill Overlays**: Extend AI agent capabilities
- **Dashboard Overlays**: Customize UI/UX and add widgets
- **Infrastructure Overlays**: Enhance infrastructure components
- **Composed Overlays**: Combine multiple overlays into complete solutions

### Q: How do overlays relate to Kustomize?

**A**: Overlays use Kustomize as the underlying composition engine. Kustomize handles the actual resource generation, while overlays provide the structure, metadata, and tooling around it.

### Q: Can I use multiple overlays together?

**A**: Yes! That's the power of the overlay system. You can combine multiple overlays using composed overlays, and the system handles dependency resolution and conflict detection.

## Getting Started

### Q: What are the prerequisites?

**A**: You need:
- Kubernetes 1.20 or higher
- Kustomize 4.0 or higher
- kubectl configured for your cluster
- Python 3.8 or higher
- Git for version control

### Q: How do I install the overlay tools?

**A**: 
```bash
# Clone the repository
git clone https://github.com/gitops-infra-control-plane/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# Make CLI tools executable
chmod +x scripts/*.py

# Add to PATH (optional)
export PATH="$PWD/scripts:$PATH"

# Verify installation
python scripts/overlay-cli.py list
```

### Q: How do I see what overlays are available?

**A**: 
```bash
# List all overlays
python scripts/overlay-cli.py list

# List by category
python scripts/overlay-cli.py list --category skills

# Search overlays
python scripts/overlay-cli.py search "debugging"

# Get detailed information
python scripts/overlay-registry.py get overlay-name
```

### Q: How do I use an existing overlay?

**A**: 
```bash
# Validate overlay
python scripts/overlay-cli.py validate overlays/.agents/debug/enhanced

# Build overlay
python scripts/overlay-cli.py build overlays/.agents/debug/enhanced --output enhanced.yaml

# Apply overlay (dry run)
python scripts/overlay-cli.py apply overlays/.agents/debug/enhanced --dry-run

# Apply to cluster
python scripts/overlay-cli.py apply overlays/.agents/debug/enhanced
```

### Q: How do I create my first overlay?

**A**: 
```bash
# Create from template
python scripts/overlay-cli.py create my-skill skills base-skill --template skill-overlay

# Customize the overlay
cd overlays/.agents/my-skill
# Edit files as needed

# Test your overlay
python scripts/validate-overlays.py .
python scripts/test-overlays.py .
```

## Overlay Development

### Q: What files do I need for an overlay?

**A**: Minimum required files:
- `kustomization.yaml`: Kustomize configuration
- `overlay-metadata.yaml`: Overlay metadata

Optional files:
- [README.md](README.md): Documentation
- `patches/`: Resource patches
- `config/`: Configuration files
- `assets/`: Static assets

### Q: How do I structure an overlay?

**A**: Follow this structure:
```
overlay-name/
├── kustomization.yaml          # Required
├── overlay-metadata.yaml       # Required
├── README.md                   # Optional
├── patches/                    # Optional
│   ├── enhanced-features.yaml
│   └── config-patches.yaml
├── config/                     # Optional
│   ├── config.json
│   └── settings.yaml
└── assets/                     # Optional
    ├── themes.css
    └── images/
```

### Q: How do I update overlay metadata?

**A**: Edit the `overlay-metadata.yaml` file:
```yaml
---
name: my-overlay
version: "1.0.0"
description: "My custom overlay"
category: skills
base_path: ".agents/base-skill"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto

maintainer:
  name: "Your Name"
  email: "your.email@example.com"

tags:
  - skills
  - custom
  - my-overlay

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"
```

### Q: How do I add patches to an overlay?

**A**: Create patch files and reference them in `kustomization.yaml`:
```yaml
# kustomization.yaml
patchesStrategicMerge:
  - patches/enhanced-features.yaml
  - patches/config-patches.yaml
```

```yaml
# patches/enhanced-features.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: enhanced-config
data:
  feature_x: "enabled"
  setting_y: "production"
```

### Q: How do I handle dependencies between overlays?

**A**: Specify dependencies in metadata:
```yaml
dependencies:
  - name: "base-skill"
    version: ">=1.0.0"
    optional: false
  - name: "enhanced-monitoring"
    version: ">=2.0.0"
    optional: true
```

### Q: How do I version my overlay?

**A**: Use semantic versioning in `overlay-metadata.yaml`:
```yaml
version: "1.2.3"
```

Update version when:
- **Major (X.0.0)**: Breaking changes
- **Minor (X.Y.0)**: New features, backward compatible
- **Patch (X.Y.Z)**: Bug fixes, backward compatible

### Q: How do I test my overlay?

**A**: 
```bash
# Validate structure and metadata
python scripts/validate-overlays.py overlays/.agents/my-overlay

# Test functionality
python scripts/test-overlays.py overlays/.agents/my-overlay

# Build to verify
python scripts/overlay-cli.py build overlays/.agents/my-overlay

# Test composition
python scripts/test-overlays.py overlays/composed/my-bundle
```

### Q: How do I register my overlay in the catalog?

**A**: 
```bash
# Register overlay
python scripts/overlay-registry.py register overlays/.agents/my-overlay

# Update catalog
python scripts/overlay-registry.py update-catalog

# Verify registration
python scripts/overlay-registry.py get my-overlay
```

## Troubleshooting

### Q: Validation failed with "Missing required file"

**A**: Ensure you have the required files:
```bash
# Check required files
ls -la overlays/.agents/my-overlay/

# Missing files? Create them:
touch overlays/.agents/my-overlay/kustomization.yaml
touch overlays/.agents/my-overlay/overlay-metadata.yaml

# Use template for correct structure
python scripts/overlay-cli.py create my-overlay skills base-skill --template skill-overlay
```

### Q: Build failed with "Resource not found"

**A**: Check resource paths in `kustomization.yaml`:
```bash
# Check current directory
pwd

# Verify relative paths
find overlays/.agents/my-overlay -name "*.yaml"

# Test paths
kustomize build overlays/.agents/my-overlay --enable-alpha-plugins

# Fix paths in kustomization.yaml
# Use ../../../../.agents/base-skill for skill overlays
```

### Q: YAML syntax errors

**A**: Validate YAML syntax:
```bash
# Check YAML syntax
yamllint overlays/.agents/my-overlay/*.yaml

# Fix common issues:
# - Use 2 spaces for indentation
# - Use kebab-case for names
# - Quote strings with special characters
```

### Q: Overlay conflicts with another overlay

**A**: Check for conflicts:
```bash
# Test composition
python scripts/test-overlays.py overlays/composed/my-bundle

# Look for resource name conflicts
grep -r "name:" overlays/.agents/my-overlay/

# Use unique names or different namespaces
```

### Q: Deployment failed with permission errors

**A**: Check permissions:
```bash
# Check RBAC permissions
kubectl auth can-i create deployment --namespace=flux-system
kubectl auth can-i create configmap --namespace=flux-system

# Check service account
kubectl get serviceaccount -n flux-system
kubectl describe serviceaccount default -n flux-system
```

### Q: Overlay changes not reflected in deployment

**A**: Check for caching and sync issues:
```bash
# Check Flux sync status
flux get kustomizations -n flux-system
flux reconcile kustomization overlay-name -n flux-system

# Force rebuild
kustomize build overlays/.agents/my-overlay | kubectl apply -f -

# Check for stuck resources
kubectl get all -n flux-system
```

### Q: Memory or CPU issues

**A**: Check resource requirements:
```bash
# Check current usage
kubectl top pods -n flux-system
kubectl describe deployment overlay-name -n flux-system

# Add resource limits
# In kustomization.yaml, add patchesJson6902 for resources
```

## Advanced Topics

### Q: How do I create a composed overlay?

**A**: 
```bash
# Create composed overlay
python scripts/overlay-cli.py create my-bundle composed ""

# Edit kustomization.yaml to include other overlays
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-bundle
resources:
  - ../../../../control-plane
  - ../.agents/skill-enhanced
  - ../agents/dashboard/theme-dark
  - ../control-plane/monitoring-enhanced
```

### Q: How do I handle environment-specific configurations?

**A**: Use environment-specific configurations:
```yaml
# Use configurations
configurations:
  - configs/production/
  - configs/staging/
  - configs/development/

# Or use components
components:
  - ../../environments/${ENVIRONMENT}/
```

### Q: How do I implement conditional features?

**A**: Use ConfigMaps and environment variables:
```yaml
configMapGenerator:
  - name: feature-config
    literals:
      - FEATURE_X_ENABLED=${FEATURE_X_ENABLED:-false}
      - DEBUG_MODE=${DEBUG_MODE:-false}

# In your patches, reference these values
```

### Q: How do I integrate with CI/CD?

**A**: Use the provided GitHub Actions workflow:
```yaml
# .github/workflows/overlay-validation.yml
# Automatically validates and tests overlays on PR
# Includes security scanning and integration testing
```

### Q: How do I implement multi-region support?

**A**: Use region-specific configurations:
```yaml
# Region-specific configurations
configurations:
  - configs/us-east-1/
  - configs/us-west-2/
  - configs/eu-west-1/

# Region-specific patches
patchesStrategicMerge:
  - patches/us-east-1.yaml
  - patches/us-west-2.yaml
```

### Q: How do I implement security policies?

**A**: Add security-focused overlays:
```yaml
# Security overlay example
resources:
  - security-policies/
  - network-policies/
  - rbac/
  - pod-security-policies/

# Security context patches
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/securityContext
        value:
          runAsNonRoot: true
          fsGroup: 2000
```

### Q: How do I implement monitoring and observability?

**A**: Add monitoring overlays:
```yaml
# Monitoring overlay example
resources:
  - prometheus/
  - grafana/
  - alertmanager/
  - servicemonitors/

# Add monitoring sidecar
patchesStrategicMerge:
  - patches/monitoring-sidecar.yaml
```

### Q: How do I implement backup and disaster recovery?

**A**: Add backup overlays:
```yaml
# Backup overlay example
resources:
  - backup/velero/
  - backup/schedules/
  - backup/restores/

# Backup configuration
configMapGenerator:
  - name: backup-config
    literals:
      - BACKUP_SCHEDULE="0 2 * * *"
      - RETENTION_PERIOD="30d"
      - STORAGE_LOCATION="s3://backups"
```

## Community

### Q: How can I contribute to the overlay system?

**A**: There are many ways to contribute:
- **Create overlays**: Develop new overlays for the community
- **Improve documentation**: Enhance guides and examples
- **Report bugs**: Submit issues with detailed information
- **Review PRs**: Help review and improve contributions
- **Answer questions**: Help others in discussions

### Q: How do I report a bug?

**A**: 
1. **Check existing issues**: Search for similar problems
2. **Create new issue**: Use the bug report template
3. **Provide details**: Include logs, configuration, and steps to reproduce
4. **Be patient**: Maintainers will review and respond

### Q: How do I request a feature?

**A**: 
1. **Check roadmap**: Review planned features
2. **Search discussions**: Look for existing discussions
3. **Create feature request**: Use the feature request template
4. **Provide details**: Include use case and requirements
5. **Consider contributing**: Offer to implement the feature

### Q: How do I get help?

**A**: 
- **GitHub Discussions**: Ask questions in the community
- **Discord Server**: Join for real-time help
- **Documentation**: Check the comprehensive guides
- **Examples**: Review the examples repository
- **Office Hours**: Attend community office hours

### Q: How do I stay updated?

**A**: 
- **Star the repository**: Follow updates on GitHub
- **Subscribe to newsletter**: Get monthly community updates
- **Join discussions**: Participate in community conversations
- **Attend events**: Join community calls and workshops
- **Follow on social media**: Stay connected on Twitter and LinkedIn

### Q: What are the community guidelines?

**A**: 
- **Be respectful**: Treat everyone with respect
- **Be constructive**: Focus on solutions and improvements
- **Be inclusive**: Welcome participants from all backgrounds
- **Be helpful**: Offer assistance when you can
- **Follow code of conduct**: Adhere to community standards

---

## Still Have Questions?

If you don't find your answer here, check out:

- **[User Guide](OVERLAY-USER-GUIDE.md)**: Comprehensive user documentation
- **[Developer Guide](OVERLAY-DEVELOPER-GUIDE.md)**: Development guidelines
- **[Community Guide](OVERLAY-COMMUNITY-GUIDE.md)**: Community resources
- **[Examples](OVERLAY-EXAMPLES.md)**: Real-world examples

Or reach out through our [community channels](https://github.com/gitops-infra-control-plane/discussions).

---

*Last updated: March 2026*
