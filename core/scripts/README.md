# Scripts Organization

This document describes the reorganized script structure in the agentic-reconciliation-engine repository.

## Directory Structure

```
scripts/
├── access/          # Access and UI scripts
├── deployment/      # Deployment and setup scripts
├── services/        # Service management scripts
├── utils/           # Utility and fix scripts
├── validation/      # Testing and validation scripts
└── .gitkeep
```

## Script Categories

### Access (`scripts/access/`)
- `access-dashboard.sh` - Access the AI dashboard
- `access-temporal.sh` - Access the Temporal UI

### Deployment (`scripts/deployment/`)
- `deploy-agentic-ai-production.sh` - Production deployment
- `deploy-agentic-ai-staging.sh` - Staging deployment
- `deploy-open-swe-gateway.sh` - Open SWE gateway deployment
- `deploy-open-swe-integration.sh` - Open SWE integration deployment
- `deploy-open-swe-staging.sh` - Open SWE staging deployment
- `rollback-open-swe-integration.sh` - Rollback script
- `setup-agentic-ai-monitoring.sh` - Monitoring setup

### Services (`scripts/services/`)
- `start-mcp-servers.sh` - Start MCP servers
- `start-real-services.sh` - Start real services
- `start-services.sh` - Start all services
- `start_services.py` - Python service starter
- `stop-mcp-servers.sh` - Stop MCP servers
- `stop-real-services.sh` - Stop real services

### Utils (`scripts/utils/`)
- `fix-commonlabels.sh` - Fix common labels
- `fix-langfuse-secrets.sh` - Fix Langfuse secrets
- `fix-temporal.sh` - Fix Temporal issues
- `monitor-open-swe-integration.sh` - Monitor Open SWE integration
- `quick-fix-temporal.sh` - Quick Temporal fix
- `set-topdir.sh` - Set top directory
- `set_topdir.sh` - Alternative top directory setter
- `update-dashboard-real-data.sh` - Update dashboard data

### Validation (`scripts/validation/`)
- `load-testing.sh` - Load testing
- `test-open-swe-integration.sh` - Test Open SWE integration
- `validate-agentic-skills.sh` - Validate agentic skills
- `validate-cost-tracking.sh` - Validate cost tracking
- `validate-mcp-gateway.sh` - Validate MCP gateway
- `validate-parallel-workflows.sh` - Validate parallel workflows
- `validate-topdir.sh` - Validate top directory

## Usage

Scripts should now be called with their full path:

```bash
# Instead of: ./scripts/deploy-agentic-ai-production.sh
# Use: ./scripts/deployment/deploy-agentic-ai-production.sh

# Instead of: ./scripts/access-dashboard.sh
# Use: ./scripts/access/access-dashboard.sh

# Instead of: ./scripts/validate-agentic-skills.sh
# Use: ./scripts/validation/validate-agentic-skills.sh
```

## Migration Notes

- All scripts have been moved from the top-level `scripts/` directory to appropriate sub-directories
- Internal script references have been updated
- Documentation files have been updated to reflect the new paths
- No functional changes were made to the scripts themselves
