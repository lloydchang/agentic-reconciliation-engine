---
name: backstage-catalog
description: Manage Backstage software catalog, components, and API documentation. Use when creating catalog entities, managing component metadata, or organizing software inventory.
argument-hint: "[action] [entityType] [entityName] [parameters]"
disable-model-invocation: false
user-invocable: true
allowed-tools: 
  - Bash
  - Read
  - Write
  - Grep
---

# Backstage Catalog Skill

Comprehensive Backstage catalog management for the AI Agents sandbox. This skill handles entity creation, catalog organization, and integration with other systems.

## Usage
```bash
/backstage-catalog create component my-service "Frontend service for user management"
/backstage-catalog create api user-api "REST API for user operations"
/backstage-catalog list components --owner=team-a
/backstage-catalog validate catalog-info.yaml
/backstage-catalog sync --source=git --auto-import
```

## Core Capabilities

### 1. Entity Management
```bash
# Create component
/backstage-catalog create component payment-service "Handles payment processing"

# Create API entity
/backstage-catalog create api payment-api "Payment processing REST API"

# Create resource entity
/backstage-catalog create resource postgres-db "Production database"

# Create system entity
/backstage-catalog create system payment-system "Payment processing system"
```

### 2. Catalog Organization
```bash
# List entities by type
/backstage-catalog list components
/backstage-catalog list apis
/backstage-catalog list resources

# Filter by owner
/backstage-catalog list components --owner=platform-team

# Search entities
/backstage-catalog search "payment" --type=component

# Export catalog data
/backstage-catalog export --format=yaml --output=catalog-backup.yaml
```

### 3. Validation & Health
```bash
# Validate entity definitions
/backstage-catalog validate catalog-info.yaml

# Check catalog health
/backstage-catalog health --detailed

# Find orphaned entities
/backstage-catalog find-orphans

# Check entity relationships
/backstage-catalog check-relationships --component=my-service
```

## Entity Templates

### Component Template
```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: $COMPONENT_NAME
  description: $COMPONENT_DESCRIPTION
  tags:
    - $TAG_1
    - $TAG_2
  annotations:
    backstage.io/techdocs-ref: dir:.
spec:
  type: service
  lifecycle: production
  owner: $TEAM_NAME
  providesApis:
    - $API_NAME
  dependsOn:
    - resource:$DATABASE_NAME
    - component:$DEPENDENCY_SERVICE
```

### API Template
```yaml
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: $API_NAME
  description: $API_DESCRIPTION
  tags:
    - api
    - $TECH_STACK
spec:
  type: openapi
  lifecycle: production
  owner: $TEAM_NAME
  definition:
    $text: |
      openapi: 3.0.0
      info:
        title: $API_TITLE
        version: 1.0.0
      paths:
        /health:
          get:
            summary: Health check endpoint
```

### Resource Template
```yaml
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: $RESOURCE_NAME
  description: $RESOURCE_DESCRIPTION
spec:
  type: database
  lifecycle: production
  owner: $TEAM_NAME
  dependsOn:
    - resource:$PARENT_RESOURCE
```

## Integration Patterns

### Temporal Workflow Integration
```yaml
# Component with Temporal workflow
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: workflow-service
  annotations:
    temporal.io/workflows: |
      - order-processing
      - payment-validation
    temporal.io/ui-url: http://localhost:8233
spec:
  type: service
  owner: platform-team
```

### AI Agent Integration
```yaml
# Component with AI agents
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: ai-orchestrator
  annotations:
    ai-agents.sandbox/skills: |
      - compliance-check
      - cost-optimization
      - security-analysis
    ai-agents.sandbox/workflows: |
      - agent-coordination
      - automated-remediation
spec:
  type: service
  owner: ai-team
```

## Catalog Configuration

### App Configuration
```yaml
# frontend/app-config.yaml
catalog:
  rules:
    - allow: [Component, API, Resource, System, Group]
  locations:
    - type: file
      target: ../../catalog-info.yaml
    - type: url
      target: https://github.com/org/repo/blob/main/catalog-info.yaml
```

### Processing Rules
```yaml
# Custom entity processing rules
catalog:
  processing:
    # Automatic tagging based on annotations
    tags:
      - pattern: "tech-stack:react"
        tags: ["frontend", "react"]
      - pattern: "tech-stack:go"
        tags: ["backend", "go"]
    
    # Automatic lifecycle assignment
    lifecycle:
      - pattern: "env:production"
        lifecycle: "production"
      - pattern: "env:staging"
        lifecycle: "staging"
```

## Bulk Operations

### Mass Entity Creation
```bash
# Create from template file
/backstage-catalog bulk-create --template=component-template.yaml --input=services.csv

# Import from external source
/backstage-catalog import --source=aws --resource-type=ecs

# Sync with Git repository
/backstage-catalog sync --git-repo=org/catalog --auto-merge
```

### Catalog Maintenance
```bash
# Clean up orphaned entities
/backstage-catalog cleanup --dry-run

# Update entity metadata
/backstage-catalog update-metadata --field=owner --value=new-team

# Validate all entities
/backstage-catalog validate-all --fix-issues
```

## API Integration

### External Service Registration
```bash
# Register AWS services
/backstage-catalog register-aws --region=us-west-2 --services=rds,ecs,lambda

# Register Kubernetes resources
/backstage-catalog register-k8s --cluster=prod --namespace=default

# Register CI/CD pipelines
/backstage-catalog register-cicd --provider=github-actions --repo=org/repo
```

### Custom API Endpoints
```bash
# Add custom API documentation
/backstage-catalog add-api --component=my-service --spec=openapi.yaml

# Link external documentation
/backstage-catalog link-docs --component=my-service --url=https://docs.example.com

# Add monitoring links
/backstage-catalog add-monitoring --component=my-service --dashboard=http://grafana/dashboard/123
```

## Search and Discovery

### Advanced Search
```bash
# Search by multiple criteria
/backstage-catalog search --type=component --owner=platform-team --lifecycle=production

# Full-text search
/backstage-catalog search "payment processing" --full-text

# Relationship search
/backstage-catalog search --depends-on=postgres-db

# Tag-based search
/backstage-catalog search --tags=go,backend,microservice
```

### Catalog Analytics
```bash
# Entity statistics
/backstage-catalog stats --by-type --by-owner

# Usage metrics
/backstage-catalog metrics --popular-components --top-apis

# Completeness report
/backstage-catalog completeness --missing-docs --incomplete-metadata
```

## Troubleshooting

### Common Issues
- **Entity Not Showing**: Check YAML syntax and location configuration
- **Relationship Problems**: Verify entity references and dependency chains
- **Performance Issues**: Review catalog size and indexing configuration
- **Sync Failures**: Check external service connectivity and permissions

### Debug Commands
```bash
# Check catalog configuration
/backstage-catalog config-check

# Test entity parsing
/backstage-catalog test-parse catalog-info.yaml

# Check location processing
/backstage-catalog check-locations --verbose

# Validate relationships
/backstage-catalog validate-relationships --component=my-service
```

## Best Practices

1. **Consistent Naming**: Use clear, consistent naming conventions
2. **Complete Metadata**: Fill all required fields and relevant optional fields
3. **Proper Relationships**: Define accurate dependencies and relationships
4. **Regular Validation**: Periodically validate catalog integrity
5. **Documentation**: Keep entity descriptions and documentation up to date
6. **Access Control**: Implement proper ownership and access controls

## Related Skills

- `/temporal-workflow`: Manage Temporal workflow components
- `/ai-agent-orchestration`: Orchestrate AI agent components
- `/infrastructure-discovery`: Auto-discover infrastructure resources
- `/security-analysis`: Validate security configurations

## File Locations

- **Catalog Config**: `frontend/app-config.yaml`
- **Entity Definitions**: `catalog-info.yaml` files throughout the codebase
- **Templates**: `templates/catalog/`
- **Scripts**: `scripts/catalog/`
- **Documentation**: `docs/backstage/`

## OpenAI Codex Integration

This section documents the OpenAI Codex-style backstage catalog management that has been integrated into the Claude skills framework.

### Basic Catalog Management Guidelines

When working with Backstage catalog, follow these guidelines:

#### 1. Entity Management
- Create and update catalog-info.yaml files
- Define proper component, API, and resource entities
- Use correct entity relationships and dependencies
- Follow Backstage entity specification

#### 2. Component Registration
- Register new components in the catalog
- Define component ownership and lifecycle
- Add proper metadata and tags
- Set up component documentation

#### 3. API Documentation
- Create API entities with OpenAPI specs
- Define API endpoints and schemas
- Document API contracts and usage
- Link APIs to consuming components

#### 4. Catalog Organization
- Organize entities by domain and team
- Use proper naming conventions
- Define entity hierarchies
- Set up catalog filters and views

### Key File Locations
- Catalog config: `frontend/app-config.yaml`
- Entity definitions: `catalog-info.yaml` files
- Plugin configurations: `frontend/plugins/`

### Common Tasks Example
```yaml
# Component entity example
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: my-component
  description: Component description
spec:
  type: service
  owner: team-name
  lifecycle: production
```

### Best Practices
- Use consistent entity naming
- Maintain proper ownership information
- Keep entity documentation up to date
- Validate entity YAML syntax
- Test catalog registration in development

### Integration Points
- Link components to Temporal workflows
- Connect APIs to documentation
- Associate resources with infrastructure
- Map teams to organizational structure
