---
name: internal-platform-cli
description: Use when working with the internal platform CLI wrapper. Documents every subcommand with examples and common usage patterns for platform operations.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: library-reference
  risk_level: low
  autonomy: fully_auto
  layer: temporal
compatibility: Requires internal platform CLI tool, platform admin access
allowed-tools: Bash Read Write Grep
---

# Internal Platform CLI Reference

## Purpose
Comprehensive reference for the internal platform CLI wrapper, documenting all subcommands, examples, and usage patterns for platform operations.

## When to Use
- **Platform operations**: When you need to interact with the internal platform
- **Resource management**: For creating, updating, or deleting platform resources
- **Configuration changes**: When modifying platform settings
- **Debugging**: For troubleshooting platform issues
- **Automation**: When scripting platform operations

## Available Commands

### Core Commands

#### `platform init`
Initialize a new platform project or workspace.
```bash
platform init --project-name my-app --environment dev
platform init --template microservice --region us-west-2
```

#### `platform deploy`
Deploy applications to the platform.
```bash
platform deploy --app my-service --env staging
platform deploy --all --dry-run
platform deploy --config deploy.yaml --wait
```

#### `platform status`
Check status of platform resources and deployments.
```bash
platform status --app my-service
platform status --cluster production
platform status --all --verbose
```

### Resource Management

#### `platform resource create`
Create new platform resources.
```bash
platform resource create --type database --name users-db
platform resource create --type queue --name events --config queue.yaml
platform resource create --type secret --name api-key --from-file
```

#### `platform resource list`
List existing resources with filtering.
```bash
platform resource list --type database
platform resource list --env production --owner team-a
platform resource list --status running
```

#### `platform resource update`
Update existing resources.
```bash
platform resource update --name users-db --set version=2.0
platform resource update --name events --config new-config.yaml
```

### Configuration Management

#### `platform config get`
Retrieve configuration values.
```bash
platform config get --key database.url
platform config get --app my-service --env prod
platform config get --all --format yaml
```

#### `platform config set`
Set configuration values.
```bash
platform config set --key database.url --value "postgres://..."
platform config set --app my-service --env prod --file config.yaml
```

#### `platform config validate`
Validate configuration files.
```bash
platform config validate --file platform.yaml
platform config validate --all --strict
```

### Monitoring & Logs

#### `platform logs`
Access application and platform logs.
```bash
platform logs --app my-service --tail 100
platform logs --cluster prod --since 1h
platform logs --filter "error" --level warning
```

#### `platform metrics`
View platform and application metrics.
```bash
platform metrics --app my-service --metric cpu
platform metrics --cluster prod --interval 5m
platform metrics --all --export prometheus
```

#### `platform health`
Check health status of platform components.
```bash
platform health --cluster production
platform health --app my-service --detailed
platform health --all --alert-threshold 80
```

## Gotchas

### Common Pitfalls
- **Environment Confusion**: Always specify `--env` explicitly. Default environment can change based on context.
- **Resource Naming**: Resource names must be lowercase with hyphens only. Underscores cause validation errors.
- **Configuration Conflicts**: Setting config with `--file` overwrites individual `--key` settings.

### Edge Cases
- **Large Deployments**: Use `--wait` flag for deployments with >10 containers to ensure completion.
- **Cross-Environment Dependencies**: Resources created in one environment aren't visible in others.
- **Rate Limiting**: Bulk operations (>50 resources) may hit API limits. Use `--batch-size 25`.

### Performance Issues
- **Status Commands**: `platform status --all` can be slow in large clusters. Use `--filter` to scope.
- **Log Retrieval**: Long time ranges with `--since` may timeout. Use smaller windows or export to file.
- **Configuration Validation**: Strict validation (`--strict`) adds 30-60 seconds to processing time.

### Security Considerations
- **Secret Handling**: Never use `--from-file` with sensitive data in CI logs. Use stdin instead.
- **API Tokens**: Tokens expire after 24 hours. Use `platform auth refresh` before long operations.
- **Cross-Account Access**: Some commands require explicit `--account` parameter in multi-account setups.

### Troubleshooting
- **Authentication Issues**: Run `platform auth whoami` to verify current identity
- **Network Timeouts**: Increase timeout with `--timeout 300` for slow networks
- **Resource Not Found**: Check environment with `platform resource list --env <env>`

## Environment Variables
```bash
PLATFORM_ENV=production          # Default environment
PLATFORM_REGION=us-west-2       # Default region
PLATFORM_TIMEOUT=60             # Command timeout in seconds
PLATFORM_LOG_LEVEL=info         # Logging verbosity
PLATFORM_CONFIG_FILE=~/.platform/config.yaml  # Config file location
```

## Configuration Files

### ~/.platform/config.yaml
```yaml
default:
  environment: development
  region: us-west-2
  timeout: 60
  
environments:
  production:
    region: us-east-1
    timeout: 120
    verify_ssl: true
    
  staging:
    region: us-west-2
    timeout: 60
    
accounts:
  main:
    id: "123456789012"
    role: "PlatformAdmin"
    
aliases:
  ps = "platform status"
  pd = "platform deploy"
  pl = "platform logs"
```

### platform.yaml (Project Config)
```yaml
name: my-application
version: "1.0.0"
type: microservice

environments:
  dev:
    replicas: 1
    resources:
      cpu: 100m
      memory: 128Mi
      
  prod:
    replicas: 3
    resources:
      cpu: 500m
      memory: 512Mi

resources:
  - type: database
    name: users-db
    engine: postgres
    version: "13"
    
  - type: queue
    name: events
    engine: sqs
```

## Integration Examples

### CI/CD Pipeline
```bash
#!/bin/bash
# Deploy to staging
platform config set --key build.number --value $BUILD_NUMBER
platform deploy --app $APP_NAME --env staging --wait
platform health --app $APP_NAME --env staging

# Promote to production if health checks pass
if [ $? -eq 0 ]; then
  platform deploy --app $APP_NAME --env production --wait
fi
```

### Local Development
```bash
# Setup local environment
platform init --project-name my-local-dev --template local
platform resource create --type database --name local-db --local-only
platform config set --key database.url --value "postgresql://localhost:5432/db"

# Run with local config
platform run --config local-config.yaml --port 8080
```

## Scripts and Automation

### Batch Resource Creation
```bash
#!/bin/bash
# Create multiple queues from configuration file
for queue in $(cat queues.txt); do
  platform resource create --type queue --name $queue --config queue-template.yaml
done
```

### Environment Sync
```bash
#!/bin/bash
# Sync configuration between environments
platform config get --env staging --all --format yaml > staging-config.yaml
platform config set --env production --file staging-config.yaml
```

## References

Load these files when needed:
- `scripts/platform-helpers.sh` - Common platform automation scripts
- `templates/resource-templates/` - Resource configuration templates
- `examples/` - Complete usage examples and patterns
- `references/api-specs.md` - Detailed API documentation
