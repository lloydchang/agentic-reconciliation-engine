# Overlay Developer Guide

This guide is for developers who want to contribute to the overlay system, create new overlays, or extend the overlay functionality.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Overlay Development](#overlay-development)
3. [Testing Strategy](#testing-strategy)
4. [Code Standards](#code-standards)
5. [Contribution Process](#contribution-process)
6. [Advanced Development](#advanced-development)
7. [Tool Development](#tool-development)
8. [Community Guidelines](#community-guidelines)

## Development Setup

### Prerequisites

- **Python 3.8+**
- **Kubernetes 1.20+**
- **Kustomize 4.0+**
- **kubectl**
- **Git**
- **Docker** (for local testing)

### Local Development Environment

1. **Clone Repository**:
   ```bash
   git clone https://github.com/gitops-infra-control-plane/gitops-infra-control-plane.git
   cd gitops-infra-control-plane
   ```

2. **Set Up Python Environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r dev-requirements.txt
   ```

3. **Install Development Tools**:
   ```bash
   # Install pre-commit hooks
   pre-commit install
   
   # Make CLI tools executable
   chmod +x scripts/*.py
   
   # Add to PATH
   export PATH="$PWD/scripts:$PATH"
   ```

4. **Verify Setup**:
   ```bash
   # Test CLI tools
   python scripts/overlay-cli.py list
   python scripts/validate-overlays.py overlays/ --verbose
   
   # Test registry
   python scripts/overlay-registry.py validate
   ```

### Development Workflow

```bash
# 1. Create feature branch
git checkout -b feature/my-new-overlay

# 2. Create overlay
python scripts/overlay-cli.py create my-overlay skills base-skill --template skill-overlay

# 3. Develop and test
cd overlays/.agents/my-overlay
# ... make changes ...
python scripts/validate-overlays.py .
python scripts/test-overlays.py .

# 4. Register overlay
python scripts/overlay-registry.py register overlays/.agents/my-overlay

# 5. Commit changes
git add .
git commit -m "Add my-new-overlay with enhanced functionality"

# 6. Test integration
python scripts/test-overlays.py overlays/

# 7. Push and create PR
git push origin feature/my-new-overlay
```

## Overlay Development

### Understanding Overlay Architecture

#### Layer System
```
┌─────────────────────────────────────┐
│           User Applications          │
├─────────────────────────────────────┤
│         Composed Overlays           │  ← Multiple overlays combined
├─────────────────────────────────────┤
│    Individual Overlays (Skills,     │  ← Single overlay extensions
│    Dashboard, Infrastructure)       │
├─────────────────────────────────────┤
│         Base Components             │  ← Immutable core system
└─────────────────────────────────────┘
```

#### Mirror Structure
Overlays mirror the base directory structure for intuitive mapping:

```
base/                    overlays/
├── .agents/            ├── .agents/
│   ├── skill-a/        │   ├── skill-a-enhanced/
│   └── skill-b/        │   └── skill-b-multi-cloud/
├── agents/             ├── agents/
│   └── dashboard/      │       └── dashboard/
└── control-plane/      ├── control-plane/
    ├── flux/                   ├── flux/
    └── monitoring/             └── monitoring-enhanced/
```

### Creating New Overlays

#### 1. Choose Overlay Type

**Skill Overlays**: Extend AI agent capabilities
- Add new skills or enhance existing ones
- Location: `overlays/.agents/`

**Dashboard Overlays**: Customize UI/UX
- Themes, widgets, visual enhancements
- Location: `overlays/agents/dashboard/`

**Infrastructure Overlays**: Enhance infrastructure
- Monitoring, security, networking
- Location: `overlays/control-plane/`

**Composed Overlays**: Combine multiple overlays
- Complete solutions and bundles
- Location: `overlays/composed/`

#### 2. Use Templates

Templates provide a solid foundation:

```bash
# Create skill overlay
python scripts/overlay-cli.py create my-skill skills base-skill --template skill-overlay

# Create dashboard overlay
python scripts/overlay-cli.py create my-theme dashboard themes --template dashboard-overlay

# Create infrastructure overlay
python scripts/overlay-cli.py create my-infra infrastructure flux --template infra-overlay
```

#### 3. Customize Overlay

**Step 1: Update Metadata**
```yaml
# overlay-metadata.yaml
---
name: my-skill-enhanced
version: "1.0.0"
description: "Enhanced skill with ML capabilities and advanced analytics"
category: skills
base_path: ".agents/base-skill"
license: "AGPLv3"
risk_level: medium
autonomy: conditional

maintainer:
  name: "Your Name"
  email: "your.email@example.com"
  organization: "Your Organization"

tags:
  - skills
  - machine-learning
  - analytics
  - enhanced

compatibility:
  min_base: "1.0.0"
  max_base: "2.0.0"
  agentskills.io: ">=1.0"
  python: ">=3.8"
  kubernetes: ">=1.20"

dependencies:
  - name: "base-skill"
    version: ">=1.0.0"
    optional: false
  - name: "ml-libraries"
    version: ">=1.0.0"
    optional: true

inputs:
  type: object
  properties:
    operation:
      type: string
      enum: ["analyze", "predict", "optimize"]
    target:
      type: string
    ml_enabled:
      type: boolean
      default: true
  required:
    - operation
    - target

outputs:
  type: object
  properties:
    result:
      type: object
    confidence:
      type: number
    execution_time:
      type: number
  required:
    - result
    - confidence

examples:
  - name: "ML Analysis"
    description: "Run ML-powered analysis"
    command: "python main.py analyze --target data.csv --ml-enabled"
    expected_output: "Analysis results with confidence scores"

resources:
  cpu: "500m"
  memory: "1Gi"

human_gate:
  required: true
  description: "ML operations require approval for production"
  approvers: ["ml-team@company.com"]
  timeout_minutes: 30
```

**Step 2: Customize Kustomization**
```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: my-skill-enhanced
  namespace: flux-system
  annotations:
    overlay.name: "my-skill-enhanced"
    overlay.version: "1.0.0"
    overlay.category: "skills"
    overlay.base-skill: "base-skill"

resources:
  # Reference to base skill
  - ../../../../.agents/base-skill

# Patches to enhance functionality
patchesStrategicMerge:
  - patches/enhanced-features.yaml
  - patches/ml-integration.yaml

# Additional configurations
configMapGenerator:
  - name: my-skill-enhanced-config
    files:
      - config/ml-models.yaml
      - config/analytics-config.yaml
    literals:
      - OVERLAY_ENABLED=true
      - ML_ENABLED=true
      - ANALYTICS_LEVEL=advanced

# Secret generation for sensitive data
secretGenerator:
  - name: my-skill-enhanced-secrets
    envs:
      - .env.secrets

# Common labels
commonLabels:
  overlay: "my-skill-enhanced"
  overlay-type: "skill"
  base-skill: "base-skill"
  managed-by: "kustomize"

# Resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: base-skill
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: ML_ENABLED
          value: "true"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "1Gi"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "2Gi"
```

**Step 3: Add Patches**
```yaml
# patches/enhanced-features.yaml
---
# Enhanced ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-skill-enhanced-features
  labels:
    overlay: my-skill-enhanced
data:
  enhanced_features.yaml: |
    # Enhanced skill configuration
    enabled: true
    features:
      - ml_analysis
      - predictive_modeling
      - real_time_processing
      - advanced_analytics
    
    ml_configuration:
      model_type: "ensemble"
      confidence_threshold: 0.8
      batch_size: 32
      max_execution_time: 300
    
    analytics:
      enable_metrics: true
      export_format: "json"
      retention_period: "30d"

---
# Enhanced Deployment patch
apiVersion: apps/v1
kind: Deployment
metadata:
  name: base-skill
  labels:
    overlay: my-skill-enhanced
spec:
  template:
    spec:
      containers:
      - name: base-skill
        env:
        - name: ENHANCED_FEATURES_ENABLED
          value: "true"
        - name: ML_MODEL_PATH
          value: "/models/enhanced"
        volumeMounts:
        - name: enhanced-config
          mountPath: /etc/enhanced-config
          readOnly: true
        - name: ml-models
          mountPath: /models
          readOnly: true
      volumes:
      - name: enhanced-config
        configMap:
          name: my-skill-enhanced-features
      - name: ml-models
        persistentVolumeClaim:
          claimName: my-skill-ml-models
```

### Advanced Overlay Patterns

#### 1. Conditional Features

```yaml
# Conditional configuration based on environment
configMapGenerator:
  - name: conditional-config
    behavior: merge
    literals:
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG_MODE=${DEBUG_MODE:-false}
      - LOG_LEVEL=${LOG_LEVEL:-info}
```

#### 2. Multi-Environment Support

```yaml
# Environment-specific overlays
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
components:
  - ../../environments/${ENVIRONMENT}
patchesStrategicMerge:
  - patches/${ENVIRONMENT}/
configurations:
  - configs/${ENVIRONMENT}/
```

#### 3. Dynamic Resource Generation

```yaml
# Generate resources dynamically
resources:
- generated/
- ../../base/components

generators:
- config.yaml
```

#### 4. Cross-Overlay Dependencies

```yaml
# dependencies.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: overlay-dependencies
data:
  dependencies.yaml: |
    required_overlays:
      - name: "base-monitoring"
        version: ">=2.0.0"
      - name: "security-policies"
        version: ">=1.5.0"
    optional_overlays:
      - name: "advanced-logging"
        version: ">=1.0.0"
```

## Testing Strategy

### Test Pyramid

```
    /\
   /  \  E2E Tests (Integration)
  /____\
 /      \ Unit Tests (Components)
/__________\
```

### 1. Unit Tests

Test individual components:

```python
# tests/test_overlay_validation.py
import pytest
from scripts.validate_overlays import OverlayValidator

class TestOverlayValidation:
    def test_valid_overlay_structure(self):
        validator = OverlayValidator("overlays/.agents/my-skill")
        assert validator.validate_structure()
    
    def test_metadata_validation(self):
        validator = OverlayValidator("overlays/.agents/my-skill")
        assert validator.validate_metadata()
    
    def test_kustomization_build(self):
        validator = OverlayValidator("overlays/.agents/my-skill")
        assert validator.validate_kustomization()
```

### 2. Integration Tests

Test overlay composition:

```python
# tests/test_overlay_composition.py
import pytest
from scripts.test_overlays import OverlayTester

class TestOverlayComposition:
    def test_multiple_overlay_composition(self):
        tester = OverlayTester("overlays/")
        assert tester.test_multiple_composition()
    
    def test_dependency_resolution(self):
        tester = OverlayTester("overlays/")
        assert tester.test_dependency_resolution()
    
    def test_conflict_detection(self):
        tester = OverlayTester("overlays/")
        assert tester.test_overlay_conflicts()
```

### 3. End-to-End Tests

Test complete deployment:

```python
# tests/test_e2e_deployment.py
import pytest
import subprocess
from pathlib import Path

class TestE2EDeployment:
    def test_overlay_deployment(self, k8s_cluster):
        # Build overlay
        result = subprocess.run([
            "kustomize", "build", "overlays/.agents/my-skill"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # Deploy to test cluster
        result = subprocess.run([
            "kubectl", "apply", "-f", "-", "--dry-run=client"
        ], input=result.stdout, capture_output=True, text=True)
        
        assert result.returncode == 0
    
    def test_overlay_functionality(self, k8s_cluster):
        # Deploy overlay
        # Test functionality
        # Verify results
        pass
```

### Test Configuration

```yaml
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=scripts
    --cov-report=html
    --cov-report=term-missing
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_overlay_validation.py

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run integration tests
pytest tests/test_integration/ -m integration

# Run E2E tests
pytest tests/test_e2e/ -m e2e
```

## Code Standards

### Python Code Standards

#### 1. Formatting

Use `black` for code formatting:

```bash
# Format code
black scripts/*.py

# Check formatting
black --check scripts/*.py
```

#### 2. Linting

Use `flake8` for linting:

```bash
# Lint code
flake8 scripts/*.py

# Lint with configuration
flake8 --config=.flake8 scripts/*.py
```

#### 3. Type Hints

Use type hints for all functions:

```python
from typing import Dict, List, Optional, Any

def validate_overlay(
    overlay_path: str,
    strict_mode: bool = False
) -> Tuple[bool, List[str]]:
    """Validate overlay structure and metadata.
    
    Args:
        overlay_path: Path to overlay directory
        strict_mode: Enable strict validation mode
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    pass
```

#### 4. Documentation

Use docstrings for all modules, classes, and functions:

```python
class OverlayValidator:
    """Validates overlay structure, metadata, and compliance.
    
    This class provides comprehensive validation for overlays including
    structure validation, metadata schema validation, and agentskills.io
    compliance checking.
    
    Attributes:
        overlay_dir: Path to overlay directory
        schema: Validation schema for metadata
    """
    
    def validate_structure(self) -> bool:
        """Validate overlay directory structure.
        
        Checks for required files, proper YAML syntax, and
        directory structure compliance.
        
        Returns:
            True if structure is valid, False otherwise
        """
        pass
```

### YAML Standards

#### 1. Formatting

Use 2 spaces for indentation:

```yaml
# Good
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
  labels:
    app: my-app
data:
  key1: value1
  key2: value2

# Bad
apiVersion: v1
kind: ConfigMap
metadata:
    name: my-config
    labels:
        app: my-app
data:
    key1: value1
    key2: value2
```

#### 2. Naming Conventions

Use kebab-case for names:

```yaml
# Good
metadata:
  name: my-skill-enhanced
  labels:
    overlay-type: skill
    base-skill: debug

# Bad
metadata:
  name: mySkillEnhanced
  labels:
    overlayType: skill
    baseSkill: aiAgentDebugger
```

#### 3. Comments

Add comments for complex configurations:

```yaml
# Enhanced ML configuration for skill overlay
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-configuration
data:
  # ML model configuration
  model_config.yaml: |
    # Model type and parameters
    model_type: "ensemble"
    confidence_threshold: 0.8
    
    # Training configuration
    batch_size: 32
    epochs: 100
```

### Documentation Standards

#### 1. README Files

Each overlay should have a README.md:

```markdown
# My Skill Enhanced Overlay

## Overview
Brief description of what this overlay does.

## Prerequisites
List any prerequisites or dependencies.

## Installation
How to install and use the overlay.

## Configuration
Configuration options and their meanings.

## Examples
Usage examples.

## Troubleshooting
Common issues and solutions.
```

#### 2. Inline Documentation

Add comments for complex logic:

```yaml
# patches/enhanced-features.yaml
---
# Enhanced ConfigMap for ML capabilities
apiVersion: v1
kind: ConfigMap
metadata:
  name: enhanced-ml-config
data:
  # ML model configuration
  # Defines model parameters and training settings
  ml_config.yaml: |
    model_type: "ensemble"
    # Higher confidence threshold for production
    confidence_threshold: 0.8
```

## Contribution Process

### 1. Development Workflow

```bash
# 1. Fork repository
# 2. Create feature branch
git checkout -b feature/my-new-overlay

# 3. Develop overlay
python scripts/overlay-cli.py create my-overlay skills base-skill --template skill-overlay
# ... make changes ...

# 4. Test thoroughly
python scripts/validate-overlays.py overlays/.agents/my-overlay
python scripts/test-overlays.py overlays/.agents/my-overlay

# 5. Update documentation
# Update README.md, add examples

# 6. Commit changes
git add .
git commit -m "Add my-overlay: Enhanced skill with ML capabilities"

# 7. Push and create PR
git push origin feature/my-new-overlay
# Create pull request on GitHub
```

### 2. Pull Request Requirements

#### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Validation
- [ ] Overlay validation passes
- [ ] Registry updated
- [ ] Documentation updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

#### Required Checks

- **Validation**: All overlays must pass validation
- **Testing**: All tests must pass
- **Documentation**: Documentation must be updated
- **Registry**: Overlay must be registered in catalog

### 3. Code Review Process

#### Review Checklist

1. **Structure**: Overlay follows correct structure
2. **Metadata**: Complete and accurate metadata
3. **Validation**: Passes all validation checks
4. **Testing**: Comprehensive test coverage
5. **Documentation**: Clear and complete documentation
6. **Security**: No security vulnerabilities
7. **Performance**: No performance regressions

#### Review Guidelines

- Be constructive and specific
- Explain reasoning for suggestions
- Focus on code quality and best practices
- Verify overlay functionality
- Check for potential issues

### 4. Release Process

#### Version Management

```bash
# Update version
sed -i 's/version: "1.0.0"/version: "1.1.0"/' overlay-metadata.yaml

# Test changes
python scripts/test-overlays.py overlays/.agents/my-overlay

# Update registry
python scripts/overlay-registry.py register overlays/.agents/my-overlay

# Tag release
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

#### Release Notes

```markdown
# Release v1.1.0

## Features
- Enhanced ML capabilities
- Improved performance
- New configuration options

## Bug Fixes
- Fixed memory leak in processing
- Resolved configuration validation issue

## Breaking Changes
- Updated configuration schema
- Deprecated old parameters

## Migration
- Update configuration files
- Run migration script
```

## Advanced Development

### 1. Custom Overlay Types

Create custom overlay types for specific use cases:

```python
# scripts/custom_overlay_types.py
from enum import Enum
from typing import Dict, Any

class CustomOverlayType(Enum):
    SECURITY = "security"
    NETWORKING = "networking"
    STORAGE = "storage"

class CustomOverlayValidator:
    def __init__(self, overlay_type: CustomOverlayType):
        self.overlay_type = overlay_type
    
    def validate_custom_requirements(self, overlay_path: str) -> bool:
        """Validate custom overlay type requirements."""
        # Implement custom validation logic
        pass
```

### 2. Plugin System

Create plugin system for extensibility:

```python
# scripts/overlay_plugins.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class OverlayPlugin(ABC):
    @abstractmethod
    def validate(self, overlay_path: str) -> bool:
        """Validate overlay with plugin logic."""
        pass
    
    @abstractmethod
    def enhance(self, overlay_path: str) -> Dict[str, Any]:
        """Enhance overlay with plugin features."""
        pass

class SecurityPlugin(OverlayPlugin):
    def validate(self, overlay_path: str) -> bool:
        # Security-specific validation
        pass
    
    def enhance(self, overlay_path: str) -> Dict[str, Any]:
        # Security enhancements
        pass
```

### 3. Advanced Testing

#### Property-Based Testing

```python
# tests/test_property_based.py
import hypothesis
from hypothesis import given, strategies as st

class TestOverlayProperties:
    @given(st.text(min_size=1, max_size=50))
    def test_overlay_name_validation(self, name):
        """Test overlay name validation with various inputs."""
        validator = OverlayValidator()
        # Test property: valid names should pass validation
        if self.is_valid_name(name):
            assert validator.validate_name(name)
    
    def is_valid_name(self, name: str) -> bool:
        """Check if name follows naming conventions."""
        return all(c.islower() or c == '-' for c in name)
```

#### Performance Testing

```python
# tests/test_performance.py
import time
import pytest

class TestOverlayPerformance:
    def test_build_performance(self, benchmark):
        """Test overlay build performance."""
        overlay_path = "overlays/.agents/my-overlay"
        
        def build_overlay():
            result = subprocess.run([
                "kustomize", "build", overlay_path
            ], capture_output=True, text=True)
            return result.returncode == 0
        
        # Benchmark should complete within 5 seconds
        result = benchmark(build_overlay)
        assert result is True
```

### 4. Tool Development

#### CLI Extensions

```python
# scripts/overlay_cli_extensions.py
import click
from scripts.overlay_cli import OverlayCLI

@click.group()
def advanced():
    """Advanced overlay operations."""
    pass

@advanced.command()
@click.argument('overlay_path')
@click.option('--profile', help='Performance profile')
def benchmark(overlay_path, profile):
    """Benchmark overlay performance."""
    cli = OverlayCLI()
    result = cli.benchmark_overlay(overlay_path, profile)
    click.echo(f"Benchmark result: {result}")

@advanced.command()
@click.argument('overlay_path')
@click.option('--format', type=click.Choice(['json', 'yaml', 'table']))
def analyze(overlay_path, format):
    """Analyze overlay composition."""
    cli = OverlayCLI()
    analysis = cli.analyze_overlay(overlay_path)
    click.echo(f"Analysis: {analysis}")
```

#### Registry Extensions

```python
# scripts/registry_extensions.py
from typing import Dict, List, Any
from scripts.overlay_registry import OverlayRegistry

class ExtendedRegistry(OverlayRegistry):
    def __init__(self, registry_dir: str):
        super().__init__(registry_dir)
        self.analytics = OverlayAnalytics()
    
    def register_with_analytics(self, overlay_path: str) -> bool:
        """Register overlay with analytics tracking."""
        success = super().register_overlay(overlay_path)
        if success:
            self.analytics.track_registration(overlay_path)
        return success
    
    def get_popular_overlays(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular overlays."""
        return self.analytics.get_popular_overlays(limit)
```

## Tool Development

### 1. CLI Tool Development

#### Adding New Commands

```python
# scripts/overlay_cli.py
@click.group()
def cli():
    """Overlay CLI Tool."""
    pass

@cli.command()
@click.argument('overlay_path')
@click.option('--deep', is_flag=True, help='Deep analysis')
def analyze(overlay_path, deep):
    """Analyze overlay composition and dependencies."""
    cli = OverlayCLI()
    result = cli.analyze_overlay(overlay_path, deep)
    click.echo(f"Analysis: {result}")
```

#### Command Validation

```python
# scripts/overlay_cli_validation.py
import click
from typing import Callable, Any

def validate_overlay_path(ctx, param, value):
    """Validate overlay path parameter."""
    if not Path(value).exists():
        raise click.BadParameter(f"Overlay path does not exist: {value}")
    return value

def validate_category(ctx, param, value):
    """Validate category parameter."""
    valid_categories = ['skills', 'dashboard', 'infrastructure', 'composed']
    if value not in valid_categories:
        raise click.BadParameter(f"Invalid category: {value}")
    return value
```

### 2. Registry Tool Development

#### Advanced Search

```python
# scripts/registry_search.py
from typing import List, Dict, Any
from scripts.overlay_registry import OverlayRegistry

class AdvancedSearch(OverlayRegistry):
    def __init__(self, registry_dir: str):
        super().__init__(registry_dir)
        self.search_index = self._build_search_index()
    
    def _build_search_index(self) -> Dict[str, List[str]]:
        """Build search index for fast lookups."""
        index = {}
        catalog = self._load_catalog()
        
        for overlay in catalog['overlays']:
            # Index by name
            index[overlay['name'].lower()] = [overlay]
            
            # Index by tags
            for tag in overlay.get('tags', []):
                if tag.lower() not in index:
                    index[tag.lower()] = []
                index[tag.lower()].append(overlay)
        
        return index
    
    def fuzzy_search(self, query: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Fuzzy search for overlays."""
        from difflib import get_close_matches
        
        results = []
        for key, overlays in self.search_index.items():
            matches = get_close_matches(query, [key], n=1, cutoff=threshold)
            if matches:
                results.extend(overlays)
        
        return results
```

### 3. Validation Framework Development

#### Custom Validators

```python
# scripts/custom_validators.py
from abc import ABC, abstractmethod
from typing import List, Tuple

class CustomValidator(ABC):
    @abstractmethod
    def validate(self, overlay_path: str) -> Tuple[bool, List[str]]:
        """Validate overlay with custom logic."""
        pass

class SecurityValidator(CustomValidator):
    def validate(self, overlay_path: str) -> Tuple[bool, List[str]]:
        """Validate security aspects of overlay."""
        errors = []
        
        # Check for security issues
        if self._check_for_secrets(overlay_path):
            errors.append("Potential secrets found in overlay")
        
        if self._check_for_insecure_configs(overlay_path):
            errors.append("Insecure configurations detected")
        
        return len(errors) == 0, errors

class PerformanceValidator(CustomValidator):
    def validate(self, overlay_path: str) -> Tuple[bool, List[str]]:
        """Validate performance aspects of overlay."""
        errors = []
        
        # Check for performance issues
        if self._check_resource_limits(overlay_path):
            errors.append("Resource limits not specified")
        
        if self._check_for_inefficient_configs(overlay_path):
            errors.append("Inefficient configurations detected")
        
        return len(errors) == 0, errors
```

## Community Guidelines

### 1. Code of Conduct

#### Our Pledge

- Be inclusive and welcoming
- Be respectful and professional
- Focus on what is best for the community
- Show empathy towards other community members

#### Standards

- Use welcoming and inclusive language
- Respect different viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community

### 2. Contribution Guidelines

#### Before Contributing

1. **Read Documentation**: Understand the system architecture
2. **Search Issues**: Check if your idea already exists
3. **Discuss First**: Open an issue to discuss major changes
4. **Start Small**: Begin with small contributions

#### Contribution Types

1. **Bug Reports**: Report issues with detailed information
2. **Feature Requests**: Propose new features with use cases
3. **Documentation**: Improve documentation and examples
4. **Code**: Submit pull requests for new features
5. **Reviews**: Help review pull requests

### 3. Communication Channels

#### GitHub

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

#### Community Forum

- **Questions**: Get help from community
- **Showcase**: Share your overlays and use cases
- **Feedback**: Provide feedback and suggestions

### 4. Recognition

#### Contributor Recognition

- **Contributors List**: Recognize all contributors
- **Release Notes**: Mention contributors in releases
- **Community Highlights**: Feature outstanding contributions

#### Overlay Recognition

- **Featured Overlays**: Highlight popular overlays
- **Community Awards**: Awards for best overlays
- **Success Stories**: Share success stories

---

Happy contributing! 🚀

For questions or help, reach out through our [community channels](https://github.com/gitops-infra-control-plane/discussions).
