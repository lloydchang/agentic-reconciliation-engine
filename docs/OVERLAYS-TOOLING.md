# Overlays Tooling Guide

This document describes the comprehensive tooling ecosystem for managing overlays in the GitOps Infrastructure Control Plane.

## Overview

The overlays system includes a complete set of tools for:

- **CLI Management**: Command-line interface for overlay operations
- **Registry Management**: Metadata catalog and discovery system
- **Validation & Testing**: Quality assurance frameworks
- **CI/CD Integration**: Automated validation and testing
- **WebMCP Interface**: Model Context Protocol for integration

## CLI Tool (`overlay-cli.py`)

The overlay CLI provides comprehensive command-line management of overlays.

### Installation

```bash
# Make executable
chmod +x scripts/overlay-cli.py

# Add to PATH (optional)
export PATH="$PWD/scripts:$PATH"
```

### Commands

#### List Overlays

```bash
# List all overlays
python scripts/overlay-cli.py list

# Filter by category
python scripts/overlay-cli.py list --category skills

# Different output formats
python scripts/overlay-cli.py list --format json
python scripts/overlay-cli.py list --format yaml
```

#### Create Overlay

```bash
# Create new skill overlay
python scripts/overlay-cli.py create my-skill skills ai-agent-debugger --template skill-overlay

# Create dashboard theme
python scripts/overlay-cli.py.py create dark-theme dashboard themes --template dashboard-overlay

# Create infrastructure overlay
python scripts/overlay-cli.py create enhanced-infra infrastructure flux --template infra-overlay

# Create composed overlay
python scripts/overlay-cli.py create enterprise-bundle composed ""
```

#### Validate Overlay

```bash
# Validate specific overlay
python scripts/overlay-cli.py validate overlays/.agents/ai-agent-debugger/enhanced

# Validate all overlays in directory
python scripts/overlay-cli.py validate overlays/
```

#### Test Overlay

```bash
# Test overlay functionality
python scripts/overlay-cli.py test overlays/.agents/ai-agent-debugger/enhanced

# Test composition
python scripts/overlay-cli.py test overlays/composed/community-bundle
```

#### Build Overlay

```bash
# Build overlay manifest
python scripts/overlay-cli.py build overlays/.agents/ai-agent-debugger/enhanced

# Save to file
python scripts/overlay-cli.py build overlays/.agents/ai-agent-debugger/enhanced --output enhanced.yaml
```

#### Apply Overlay

```bash
# Apply overlay to cluster
python scripts/overlay-cli.py apply overlays/.agents/ai-agent-debugger/enhanced

# Dry run
python scripts/overlay-cli.py apply overlays/.agents/ai-agent-debugger/enhanced --dry-run
```

#### Search Overlays

```bash
# Search by name or description
python scripts/overlay-cli.py search "debugging"

# Search by tags
python scripts/overlay-cli.py search "ml" --tags machine-learning debugging

# Search with filters
python scripts/overlay-cli.py search "enhanced" --category skills
```

#### Update Catalog

```bash
# Update overlay catalog
python scripts/overlay-cli.py update-catalog
```

## Registry Tool (`overlay-registry.py`)

The registry tool manages overlay metadata, discovery, and distribution.

### Commands

#### Initialize Registry

```bash
# Create new registry
python scripts/overlay-registry.py init

# Custom registry location
python scripts/overlay-registry.py init --registry-dir /path/to/registry
```

#### Register Overlay

```bash
# Register overlay from directory
python scripts/overlay-registry.py register overlays/.agents/ai-agent-debugger/enhanced

# Register with custom metadata
python scripts/overlay-registry.py register overlays/my-overlay --metadata custom-metadata.yaml
```

#### Search Registry

```bash
# Search overlays
python scripts/overlay-registry.py search "debugging"

# Filter by category
python scripts/overlay-registry.py search "enhanced" --category skills

# Filter by risk level
python scripts/overlay-registry.py search "enterprise" --risk-level medium
```

#### List Overlays

```bash
# List all overlays
python scripts/overlay-registry.py list

# Filter by category
python scripts/overlay-registry.py list --category skills

# Sort by version
python scripts/overlay-registry.py list --sort version
```

#### Get Overlay Details

```bash
# Get overlay metadata
python scripts/overlay-registry.py get ai-agent-debugger-enhanced
```

#### Validate Registry

```bash
# Validate registry integrity
python scripts/registry.py validate
```

#### Export/Import Registry

```bash
# Export registry
python scripts/overlay-registry.py export registry-backup.yaml

# Export as JSON
python scripts/overlay-registry.py export registry-backup.json --format json

# Import registry (merge)
python scripts/overlay-registry.py import registry-backup.yaml

# Import registry (replace)
python scripts/overlay-registry.py import registry-backup.yaml --replace
```

## Validation Framework (`validate-overlays.py`)

The validation framework ensures overlay quality and compliance.

### Validation Checks

1. **Structure Validation**
   - Required files presence
   - YAML syntax validation
   - Directory structure compliance

2. **Metadata Validation**
   - Schema compliance
   - Required fields validation
   - Version format validation
   - agentskills.io compliance

3. **Resource Validation**
   - Kustomize build validation
   - Resource path validation
   - Dependency resolution

### Usage

```bash
# Validate single overlay
python scripts/validate-overlays.py overlays/.agents/ai-agent-debugger/enhanced

# Validate all overlays
python scripts/validate-overlays.py overlays/

# Verbose output
python scripts/validate-overlays.py overlays/ --verbose

# Generate report
python scripts/validate-overlays.py overlays/ --report validation-report.json
```

### Validation Report

The validation tool generates detailed reports including:

```json
{
  "summary": {
    "total_overlays": 12,
    "passed": 10,
    "failed": 2,
    "warnings": 5
  },
  "results": [
    {
      "overlay": "ai-agent-debugger-enhanced",
      "status": "PASS",
      "checks": {
        "structure": "PASS",
        "metadata": "PASS",
        "kustomization": "PASS"
      }
    }
  ]
}
```

## Testing Framework (`test-overlays.py`)

The testing framework provides comprehensive overlay testing.

### Test Categories

1. **Structure Tests**
   - Directory structure validation
   - File presence checks
   - YAML syntax validation

2. **Build Tests**
   - Kustomize build validation
   - Resource generation testing
   - Output validation

3. **Composition Tests**
   - Multiple overlay composition
   - Dependency resolution
   - Conflict detection

4. **Integration Tests**
   - Kubernetes dry-run validation
   - Resource application testing
   - End-to-end scenarios

### Usage

```bash
# Test single overlay
python scripts/test-overlays.py overlays/.agents/ai-agent-debugger/enhanced

# Test all overlays
python scripts/test-overlays.py overlays/

# Verbose output
python scripts/test-overlays.py overlays/ --verbose

# Generate test report
python scripts/test-overlays.py overlays/ --report test-report.json
```

### Test Results

```json
{
  "summary": {
    "total_tests": 45,
    "passed": 42,
    "failed": 3,
    "success_rate": "93.3%"
  },
  "test_results": [
    {
      "overlay": "ai-agent-debugger-enhanced",
      "tests": {
        "structure": "PASS",
        "build": "PASS",
        "composition": "PASS",
        "integration": "PASS"
      }
    }
  ]
}
```

## CI/CD Integration

The overlays system includes comprehensive CI/CD integration through GitHub Actions.

### Workflow Features

1. **Automated Validation**
   - Structure validation on every push
   - Metadata schema validation
   - Kustomize build testing

2. **Automated Testing**
   - Comprehensive overlay testing
   - Composition testing
   - Integration testing

3. **Security Scanning**
   - Trivy vulnerability scanning
   - Security policy validation
   - SARIF report generation

4. **Registry Updates**
   - Automatic catalog updates
   - Index generation
   - Metadata synchronization

### Workflow Triggers

```yaml
# Automatic triggers
on:
  push:
    paths:
      - 'overlays/**'
      - 'scripts/validate-overlays.py'
  pull_request:
    paths:
      - 'overlays/**'

# Manual triggers
on:
  workflow_dispatch:
    inputs:
      overlay_path:
        description: 'Specific overlay to validate'
        test_only:
          description: 'Run tests only'
```

### Workflow Jobs

1. **validate-overlays**: Structure and metadata validation
2. **test-overlays**: Comprehensive overlay testing
3. **build-overlays**: Kustomize build and validation
4. **security-scan**: Vulnerability scanning
5. **registry-update**: Catalog maintenance
6. **integration-test**: End-to-end testing

## WebMCP Interface

The WebMCP interface provides Model Context Protocol integration for overlay management.

### MCP Methods

```json
{
  "methods": {
    "overlays/list": "List available overlays",
    "overlays/create": "Create new overlay",
    "overlays/validate": "Validate overlay",
    "overlays/test": "Test overlay",
    "overlays/build": "Build overlay manifest",
    "overlays/apply": "Apply overlay to cluster",
    "overlays/search": "Search overlays",
    "overlays/get_metadata": "Get overlay metadata"
  }
}
```

### MCP Usage

```python
# Start MCP server
python scripts/overlay-webmcp.py --port 8080

# Make MCP request
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "overlays/list",
    "params": {"category": "skills"}
  }'
```

### MCP Response

```json
{
  "result": [
    {
      "name": "ai-agent-debugger-enhanced",
      "category": "skills",
      "version": "2.0.0",
      "description": "ML-enhanced debugging skill"
    }
  ],
  "warnings": []
}
```

## Integration Examples

### GitOps Integration

```bash
# Validate before commit
pre-commit:
  - python scripts/validate-overlays.py overlays/

# Test in CI pipeline
ci:
  - python scripts/test-overlays.py overlays/
  - python scripts/overlay-cli.py build overlays/community-bundle
```

### IDE Integration

```bash
# VS Code task
{
  "label": "Validate Overlay",
  "type": "shell",
  "command": "python scripts/validate-overlays.py ${workspaceFolder}/overlays"
}
```

### Automation Scripts

```python
#!/usr/bin/env python3
import subprocess
import sys

def validate_and_build_overlay(overlay_path):
    # Validate
    result = subprocess.run([
        'python', 'scripts/validate-overlays.py', overlay_path
    ])
    if result.returncode != 0:
        print("Validation failed")
        return False
    
    # Build
    result = subprocess.run([
        'python', 'scripts/overlay-cli.py', 'build', overlay_path
    ])
    if result.returncode != 0:
        print("Build failed")
        return False
    
    print("Overlay validated and built successfully")
    return True

if __name__ == '__main__':
    overlay_path = sys.argv[1] if len(sys.argv) > 1 else 'overlays/'
    validate_and_build_overlay(overlay_path)
```

## Best Practices

### Development Workflow

1. **Create Overlay**: Use CLI tool with templates
2. **Validate**: Run validation during development
3. **Test**: Comprehensive testing before commit
4. **Register**: Add to registry catalog
5. **Document**: Update overlay documentation

### CI/CD Integration

1. **Pre-commit Hooks**: Local validation
2. **Pull Request**: Automated testing
3. **Merge**: Full validation and testing
4. **Release**: Registry update and documentation

### Quality Assurance

1. **Structure**: Follow overlay structure guidelines
2. **Metadata**: Complete and accurate metadata
3. **Testing**: Comprehensive test coverage
4. **Documentation**: Clear usage instructions

### Security

1. **Scanning**: Regular vulnerability scanning
2. **Validation**: Input validation and sanitization
3. **Access Control**: Proper permissions and RBAC
4. **Audit**: Change tracking and logging

## Troubleshooting

### Common Issues

1. **Validation Failures**
   - Check YAML syntax
   - Verify required files
   - Validate metadata schema

2. **Build Failures**
   - Check resource paths
   - Verify Kustomize syntax
   - Validate dependencies

3. **Test Failures**
   - Check overlay composition
   - Verify resource conflicts
   - Validate dependencies

### Debug Commands

```bash
# Debug validation
python scripts/validate-overlays.py overlays/ --verbose

# Debug build
kustomize build overlays/my-overlay --enable-alpha-plugins

# Debug registry
python scripts/overlay-registry.py validate

# Check dependencies
python scripts/test-overlays.py overlays/ --test-dependencies
```

### Support

For tooling issues:
1. Check tool documentation
2. Review validation reports
3. Examine test results
4. Use verbose mode for debugging
5. Open issue with detailed logs

## Future Enhancements

### Planned Features

1. **GUI Tool**: Web-based overlay management interface
2. **Advanced Search**: Full-text search and filtering
3. **Version Management**: Semantic versioning and compatibility
4. **Dependency Graph**: Visual dependency management
5. **Performance Metrics**: Overlay performance tracking

### Integration Roadmap

1. **IDE Plugins**: VS Code, IntelliJ plugins
2. **Container Registry**: Docker registry integration
3. **Cloud Provider**: AWS, Azure, GCP integration
4. **Monitoring**: Prometheus and Grafana integration
5. **Security**: Advanced security scanning and policy enforcement
