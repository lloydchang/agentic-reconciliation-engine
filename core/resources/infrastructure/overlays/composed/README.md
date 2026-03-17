# Composed Overlays

This directory contains composed overlays that combine multiple individual overlays into complete solutions.

## Available Composed Overlays

### Enterprise Suite
- **Path**: `enterprise-suite/`
- **Description**: Complete enterprise solution with enhanced debugging, dark theme, and monitoring
- **Risk Level**: Medium
- **Autonomy**: Conditional
- **Use Case**: Production enterprise deployments

### Enterprise Variant (Migrated)
- **Path**: `enterprise-variant/`
- **Description**: Enterprise variant migrated from `variants/enterprise/` with enhanced Flux, controllers, monitoring, security, and backup
- **Risk Level**: Medium
- **Autonomy**: Conditional
- **Use Case**: Enterprise-grade infrastructure

### Open Source Variant (Migrated)
- **Path**: `opensource-variant/`
- **Description**: Open source variant migrated from `variants/opensource/` with core Flux, controllers, and community monitoring
- **Risk Level**: Low
- **Autonomy**: Fully Auto
- **Use Case**: Community and open source deployments

### Community Bundle
- **Path**: `community-bundle/`
- **Description**: Community-curated bundle of popular overlays including enhanced debugging, dark theme, cost calculator, and multi-cloud provisioning
- **Risk Level**: Low
- **Autonomy**: Fully Auto
- **Use Case**: Community-driven deployments

## Usage

### Deploy a Composed Overlay
```bash
# Deploy enterprise suite
kustomize build core/deployment/overlays/composed/enterprise-suite | kubectl apply -f -

# Deploy enterprise variant
kustomize build core/deployment/overlays/composed/enterprise-variant | kubectl apply -f -

# Deploy open source variant
kustomize build core/deployment/overlays/composed/opensource-variant | kubectl apply -f -

# Deploy community bundle
kustomize build core/deployment/overlays/composed/community-bundle | kubectl apply -f -
```

### Test Before Deployment
```bash
# Dry run to test composition
kustomize build core/deployment/overlays/composed/enterprise-suite | kubectl apply --dry-run=client -f -

# Validate composition
python core/core/automation/ci-cd/scripts/validate-overlays.py core/deployment/overlays/composed/enterprise-suite

# Test composition
python core/core/automation/ci-cd/scripts/test-overlays.py core/deployment/overlays/composed/enterprise-suite
```

## Migration from Variants

The following variants have been migrated to composed overlays:

### From `variants/enterprise/` → `core/deployment/overlays/composed/enterprise-variant/`
- All enterprise features preserved
- Enhanced with overlay system capabilities
- Better dependency management
- Improved testing and validation

### From `variants/opensource/` → `core/deployment/overlays/composed/opensource-variant/`
- All open source features preserved
- Enhanced with overlay system capabilities
- Community-focused configuration
- Simplified deployment process

## Creating New Composed Overlays

1. **Create Directory Structure**:
   ```bash
   mkdir -p core/deployment/overlays/composed/my-composed-overlay
   ```

2. **Create Kustomization**:
   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   metadata:
     name: my-composed-overlay
   resources:
     # Base components
     - ../../../control-plane
     - ../../../.agents
     - ../../../agents
     # Individual overlays
     - ../core/ai/skills/my-skill-overlay
     - ../core/ai/runtime/dashboard/my-theme
   ```

3. **Add Metadata**:
   ```yaml
   ---
   name: my-composed-overlay
   version: "1.0.0"
   description: "My custom composed overlay"
   category: composed
   ```

4. **Test and Validate**:
   ```bash
   python core/core/automation/ci-cd/scripts/validate-overlays.py core/deployment/overlays/composed/my-composed-overlay
   python core/core/automation/ci-cd/scripts/test-overlays.py core/deployment/overlays/composed/my-composed-overlay
   ```

## Best Practices

### 1. Dependency Management
- List all overlay dependencies in metadata
- Use version constraints for compatibility
- Test dependency resolution

### 2. Resource Planning
- Consider combined resource requirements
- Set appropriate limits for composed overlays
- Monitor resource usage

### 3. Testing
- Test individual overlays first
- Test composition scenarios
- Validate with dry-run deployments

### 4. Documentation
- Document included overlays
- Provide usage examples
- Include migration guides

## Troubleshooting

### Common Issues

1. **Resource Conflicts**:
   - Check for duplicate resource names
   - Use proper namespacing
   - Validate resource uniqueness

2. **Dependency Resolution**:
   - Verify all dependencies exist
   - Check version compatibility
   - Test dependency order

3. **Build Failures**:
   - Check YAML syntax
   - Validate resource paths
   - Test individual overlays

### Debug Commands

```bash
# Validate composed overlay
python core/core/automation/ci-cd/scripts/validate-overlays.py core/deployment/overlays/composed/my-overlay

# Test composition
python core/core/automation/ci-cd/scripts/test-overlays.py core/deployment/overlays/composed/my-overlay

# Check build output
kustomize build core/deployment/overlays/composed/my-overlay

# Dry run deployment
kustomize build core/deployment/overlays/composed/my-overlay | kubectl apply --dry-run=client -f -
```

## Support

For composed overlay issues:
1. Check individual overlay documentation
2. Review composition examples
3. Use validation and testing tools
4. Open an issue with the `composed-overlay` label
