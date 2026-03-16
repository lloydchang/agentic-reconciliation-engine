# hello-world Skill Overlay

## Overview

This is a skill overlay template that extends the base `debug` skill with additional capabilities while maintaining agentskills.io compliance.

## Purpose

{{description}}

## When to Use

- **Skill Enhancement**: Add new capabilities to existing skills
- **Custom Logic**: Implement organization-specific logic
- **Integration**: Connect with external systems
- **Compliance**: Add compliance and security features

## Installation

```bash
# Create overlay from template
cp -r overlays/templates/skill-overlay overlays/.agents/hello-world

# Customize overlay configuration
cd overlays/.agents/hello-world
# Edit kustomization.yaml, overlay-metadata.yaml, and other files

# Apply overlay
kustomize build . | kubectl apply -f -
```

## Configuration

### Environment Variables

- `OVERLAY_ENABLED`: Enable overlay functionality (default: true)
- `DEBUG_MODE`: Enable debug logging (default: false)
- `LOG_LEVEL`: Logging level (default: INFO)

### Custom Configuration

Customize the overlay by modifying:
- `kustomization.yaml`: Kustomize configuration
- `overlay-metadata.yaml`: Overlay metadata and schema
- `enhanced-features.yaml`: Feature patches
- `scripts/`: Additional Python scripts

## Usage Examples

### Basic Execution
```bash
python main.py execute \
  --operation analyze \
  --targetResource example \
  --enhanced-features
```

### Custom Configuration
```bash
python main.py execute \
  --operation custom \
  --targetResource example \
  --custom-config '{"param": "value"}'
```

## Development

### File Structure
```
hello-world/
├── kustomization.yaml          # Kustomize configuration
├── overlay-metadata.yaml       # Overlay metadata
├── README.md                   # This file
├── enhanced-features.yaml      # Feature patches
├── scripts/                    # Additional scripts
│   ├── enhanced_handler.py     # Enhanced logic
│   └── utils.py               # Utility functions
└── tests/                      # Test files
    └── test_overlay.py        # Overlay tests
```

### Adding New Features

1. **Update kustomization.yaml**: Add new ConfigMaps, Secrets, or patches
2. **Implement logic**: Add Python scripts in `scripts/`
3. **Update metadata**: Modify `overlay-metadata.yaml` with new inputs/outputs
4. **Add tests**: Create test files in `tests/`
5. **Update documentation**: Modify this README.md

### Testing

```bash
# Run overlay tests
python tests/test_overlay.py

# Validate overlay structure
python ../../scripts/validate-overlays.py .

# Test composition
kustomize build . | kubectl apply --dry-run=client -f -
```

## Compatibility

- **Base Skill**: debug {{base-version}}+
- **agentskills.io**: 1.0+
- **Python**: 3.8+
- **Kubernetes**: 1.20+

## Dependencies

- debug (base skill)
- Additional dependencies listed in overlay-metadata.yaml

## Support

For issues and questions:
1. Check overlay logs with `--debug-mode`
2. Review base skill documentation
3. Open an issue with the `overlay` label
4. Contact maintainer: {{maintainer.email}}

## License

{{license}}

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Version History

- **{{overlay-version}}**: Initial release
- Future versions will be documented here
