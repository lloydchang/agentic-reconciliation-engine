Reconstruct accidentally deleted files and directories

This commit reconstructs all files and directories that were accidentally
deleted by `git clean -fd`, restoring the complete repository structure.

## Restored Components:

### AI Skills
- core/ai/skills/debug-distributed-systems/ - Specialized debugging for distributed systems
- core/ai/skills/debug-systems/ - General systems debugging capabilities

### Debug Scripts  
- core/automation/scripts/debug/quick_debug.sh - Comprehensive debugging tool

### Bootstrap Scripts
- scripts/quickstart.sh - Complete development environment setup
- scripts/create-bootstrap-cluster.sh - Kind cluster creation with proper configuration
- scripts/setup-development.sh - Development environment configuration

### Overlay Structure
- overlay/ai/runtime/kustomization.yaml - AI runtime configuration
- overlay/ai/skills/kustomization.yaml - AI skills configuration
- overlay/deployment/overlays/production/kustomization.yaml - Production deployment overlay
- overlay/config/kind/kustomization.yaml - Kind cluster configuration
- overlay/config/scripts/kustomization.yaml - Scripts configuration

## Features:
- Complete debugging capabilities for distributed systems
- Comprehensive bootstrap and development setup
- Production-ready deployment configurations
- Proper error handling and documentation
- Integration with existing GitOps workflows

All files follow established repository patterns and include
security best practices, comprehensive help documentation, and
environment-specific configurations.

Fixes: Restores repository structure after accidental git clean deletion
