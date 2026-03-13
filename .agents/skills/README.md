# Agent Skills

This directory contains skills for the AI Agents Sandbox. These skills follow the skills specification and can be invoked using slash commands (e.g., `/skill-name`).

## Available Skills

### 🔄 temporal-workflow
Create, manage, and monitor Temporal workflows with AI agent orchestration.

**Usage:**
```bash
/temporal-workflow create my-workflow "Description"
/temporal-workflow status my-workflow
/temporal-workflow monitor my-workflow --live
/temporal-workflow debug my-workflow --history=50
```

**Capabilities:**
- Workflow creation and development
- Real-time monitoring
- Debugging and troubleshooting
- Performance metrics

**Files:**
- `SKILL.md` - Main skill instructions
- `examples/compensation-workflow.go` - Compensation pattern example
- `templates/` - Workflow templates

### 📋 backstage-catalog
Manage Backstage software catalog, components, and API documentation.

**Usage:**
```bash
/backstage-catalog create component my-service "Description"
/backstage-catalog list components --owner=team-a
/backstage-catalog validate catalog-info.yaml
/backstage-catalog sync --source=git
```

**Capabilities:**
- Entity management and creation
- Catalog organization
- Validation and health checks
- Bulk operations

**Files:**
- `SKILL.md` - Main skill instructions
- `examples/` - Entity examples
- `templates/` - Entity templates

### 🤖 ai-agent-orchestration
Orchestrate and coordinate multiple AI agents for complex workflows.

**Usage:**
```bash
/ai-agent-orchestration orchestrate compliance-audit production
/ai-agent-orchestration coordinate security-analysis cost-optimization
/ai-agent-orchestration monitor-agents --status=detailed
```

**Capabilities:**
- Multi-agent coordination
- Workflow orchestration patterns
- Agent communication
- Performance optimization

**Files:**
- `SKILL.md` - Main skill instructions
- Subagent execution with `context: fork`

### 🔍 compliance-check
Start and monitor compliance checks for SOC2, GDPR, HIPAA standards.

**Usage:**
```bash
/compliance-check vm-web-server-001 SOC2 high
/compliance-check database-cluster-prod GDPR
/compliance-check all-resources HIPAA critical
```

**Capabilities:**
- Regulatory compliance validation
- Policy checking
- Audit preparation
- Remediation guidance

**Files:**
- `SKILL.md` - Main skill instructions
- API integration with Temporal backend
- Comprehensive reporting

### 💰 cost-optimization
Analyze and optimize cloud infrastructure costs using specialized subagent.

**Usage:**
```bash
/cost-optimization all-resources full 30d
/cost-optimization production-cluster usage 7d
/cost-optimization database-tier optimization 90d
```

**Capabilities:**
- Cost pattern analysis
- Resource optimization
- Forecasting models
- ROI calculations

**Files:**
- `SKILL.md` - Main skill instructions
- Subagent execution with `context: fork`
- Advanced analytics

### 🔐 security-analysis
Perform security vulnerability scanning and analysis.

**Usage:**
```bash
/security-analysis scan production-cluster
/security-analysis analyze security-group sg-12345
/security-analysis audit all-resources
```

**Capabilities:**
- Vulnerability scanning
- Security policy validation
- Threat assessment
- Incident response

**Files:**
- `SKILL.md` - Main skill instructions
- Integration with security tools

### 🔧 workflow-management
Orchestrate and monitor Temporal AI Agent workflows.

**Usage:**
```bash
/workflow-management list active
/workflow-management status workflow-12345
/workflow-management cancel workflow-12345 "Reason"
```

**Capabilities:**
- Workflow discovery and listing
- Real-time status monitoring
- Workflow orchestration
- Performance tracking

**Files:**
- `SKILL.md` - Main skill instructions
- Comprehensive workflow management

### 🌐 infrastructure-discovery
Discover and analyze infrastructure resources and dependencies.

**Usage:**
```bash
/infrastructure-discovery scan aws-region us-west-2
/infrastructure-discovery map-dependencies production
/infrastructure-discovery analyze-network security-groups
```

**Capabilities:**
- Resource discovery
- Dependency mapping
- Network analysis
- Configuration assessment

**Files:**
- `SKILL.md` - Main skill instructions
- Multi-cloud support

## Skill Structure

### Frontmatter Configuration
Each skill includes YAML frontmatter with configuration:

```yaml
---
name: skill-name
description: When to use this skill
argument-hint: "[param1] [param2] [param3]"
disable-model-invocation: false
user-invocable: true
allowed-tools: 
  - Bash
  - Read
  - Write
  - Grep
context: fork          # Optional: for subagent execution
agent: Plan           # Optional: for subagent execution
---
```

### Key Configuration Options

- **name**: Skill identifier (used in slash commands)
- **description**: When the skill should trigger implicitly
- **argument-hint**: Command line argument format
- **context**: Use `fork` for isolated subagent execution
- **agent**: Specific agent type for subagent execution
- **allowed-tools**: Tools the skill can use

## Advanced Patterns

### Subagent Execution
Some skills use `context: fork` for isolated execution:
- Cost optimization uses `agent: Plan` for analytical tasks
- AI agent orchestration coordinates multiple specialized agents

### Tool Integration
Skills can integrate with:
- **Temporal workflows**: Through API endpoints
- **Backstage catalog**: Via catalog API
- **External services**: Using HTTP clients
- **Local tools**: Bash, file operations, grep

### Error Handling
Comprehensive error handling includes:
- Invalid input validation
- API connectivity issues
- Permission problems
- Timeout scenarios

## Development Guidelines

### Creating New Skills

1. Create skill directory:
```bash
mkdir -p .agents/skills/new-skill
```

2. Create SKILL.md with frontmatter
3. Define skill instructions and usage examples
4. Add supporting files (examples, templates, scripts)
5. Test skill functionality

### Best Practices

1. **Clear Scope**: Define exactly when skill should and shouldn't trigger
2. **Argument Validation**: Parse and validate command arguments
3. **Error Recovery**: Handle failures gracefully
4. **Integration**: Connect to appropriate backend services
5. **Documentation**: Provide comprehensive examples
6. **Testing**: Include validation and testing procedures

### File Organization
```
skill-name/
├── SKILL.md                    # Main skill file (required)
├── examples/                   # Usage examples
├── templates/                  # Template files
├── scripts/                    # Helper scripts
└── assets/                     # Supporting assets
```

## Integration Architecture

### Backend Integration
Skills connect to backend services through:
- **Temporal API**: `http://localhost:8081/api/v1/`
- **Workflow Engine**: Temporal workflows and activities
- **Database**: Configuration and state storage

### Frontend Integration
Skills interact with frontend components:
- **Backstage Catalog**: Entity management
- **Temporal UI**: Workflow monitoring
- **Custom Dashboards**: Skill-specific interfaces

### External Services
Skills can integrate with:
- **Cloud Providers**: AWS, GCP, Azure APIs
- **Monitoring Tools**: Prometheus, Grafana
- **Security Tools**: Vulnerability scanners
- **Cost Tools**: Cloud cost APIs

## Monitoring and Observability

### Skill Metrics
- Execution success rates
- Performance timing
- Error frequencies
- Resource usage

### Logging
- Structured logging with correlation IDs
- Error tracking and debugging
- Audit trail for compliance

### Debugging
- Detailed error messages
- Step-by-step execution traces
- Integration testing tools

## Troubleshooting

### Common Issues

1. **Skill Not Triggering**: Check description matching
2. **Argument Parsing**: Verify argument-hint format
3. **Tool Permissions**: Ensure allowed-tools includes needed tools
4. **API Connectivity**: Check backend service status
5. **Timeout Issues**: Adjust operation timeouts

### Debug Commands
```bash
# Test skill parsing
/echo "Testing skill parsing"

# Check tool access
/ls -la .agents/skills/

# Validate skill syntax
# Check SKILL.md frontmatter formatting
```

## Security Considerations

### Tool Restrictions
- Limit allowed-tools to necessary permissions
- Use disable-model-invocation for sensitive operations
- Implement proper access controls

### Input Validation
- Sanitize all user inputs
- Validate argument formats
- Check resource permissions

### Audit Trail
- Log all skill executions
- Track parameter values
- Monitor for abuse patterns

## Skills Integration

Skills can be invoked using the `$` prefix or through the `/skills` command.

### Available Skills

#### 🔄 temporal-workflow
Manage and monitor Temporal workflows with AI agent orchestration.

**Usage:**
```bash
$temporal-workflow
```

**Capabilities:**
- Workflow creation and development
- Activity integration
- Testing and validation
- Monitoring and debugging

**Files:**
- `SKILL.md` - Main skill instructions
- `agents/openai.yaml` - UI configuration and dependencies
- `examples/basic-workflow.go` - Example workflow implementation
- `scripts/validate-workflow.sh` - Workflow validation script

#### 📋 backstage-catalog
Manage Backstage software catalog and components.

**Usage:**
```bash
$backstage-catalog
```

**Capabilities:**
- Entity management and registration
- Catalog organization
- API documentation
- Component relationships

**Files:**
- `SKILL.md` - Main skill instructions
- `agents/openai.yaml` - UI configuration and dependencies
- `examples/payment-service.yaml` - Example component definition
- `templates/component-template.yaml` - Component creation template

#### 🤖 ai-agent-orchestration
Orchestrate AI agents and manage agent workflows.

**Usage:**
```bash
$ai-agent-orchestration
```

**Capabilities:**
- Agent design and coordination
- Workflow orchestration
- Communication patterns
- Resource management

**Files:**
- `SKILL.md` - Main skill instructions
- `agents/openai.yaml` - UI configuration and dependencies

#### 🔍 compliance-check
Perform automated compliance checks and policy validation.

**Usage:**
```bash
$compliance-check
```

**Capabilities:**
- Policy definition and validation
- Configuration analysis
- Automated checks
- Remediation guidance

**Files:**
- `SKILL.md` - Main skill instructions
- `agents/openai.yaml` - UI configuration and dependencies

#### 💰 cost-optimization
Optimize resource costs and spending across infrastructure.

**Usage:**
```bash
$cost-optimization
```

**Capabilities:**
- Cost analysis and trends
- Resource assessment
- Optimization opportunities
- Implementation tracking

**Files:**
- `SKILL.md` - Main skill instructions
- `agents/openai.yaml` - UI configuration and dependencies

### Configuration

#### agents/openai.yaml Structure
Each integrated skill includes an `agents/openai.yaml` configuration file that defines:

```yaml
interface:
  display_name: "Display Name"
  short_description: "Brief description"
  icon_small: "./assets/icon.svg"
  icon_large: "./assets/logo.png"
  brand_color: "#COLOR"
  default_prompt: "Default prompt text"

policy:
  allow_implicit_invocation: true

dependencies:
  tools:
    - type: "mcp"
      value: "tool-name"
      description: "Tool description"
      transport: "streamable_http"
      url: "http://localhost:PORT"
```

### Skill Development

#### Creating New Skills

1. Create skill directory:
```bash
mkdir -p .agents/skills/new-skill
```

2. Create SKILL.md:
```markdown
---
name: new-skill
description: What this skill does and when to use it
---

# Skill instructions here...
```

3. Create agents/openai.yaml for UI configuration
4. Add examples and supporting files as needed

#### Skill Structure
```
skill-name/
├── SKILL.md                    # Main skill instructions (required)
├── agents/
│   └── openai.yaml            # UI configuration (optional)
├── examples/                   # Usage examples (optional)
├── scripts/                    # Helper scripts (optional)
├── templates/                  # Template files (optional)
└── assets/                     # Icons and images (optional)
```

### Integration

#### Temporal Integration
skills integrate with Temporal workflows through:
- Workflow definitions in `backend/workflows/`
- Activity implementations in `backend/activities/`
- API endpoints at `http://localhost:8081`

#### Backstage Integration
skills connect to Backstage through:
- Catalog entities in `catalog-info.yaml` files
- App configuration in `frontend/app-config.yaml`
- Plugin integrations in `frontend/plugins/`

### Best Practices

1. **Clear Descriptions**: Write detailed skill descriptions for implicit invocation
2. **Structured Content**: Use clear sections and code examples
3. **Error Handling**: Include comprehensive error handling guidance
4. **Integration Points**: Clearly define integration with other systems
5. **Examples**: Provide practical usage examples
6. **Testing**: Include validation and testing procedures

### Troubleshooting

#### Skill Not Detected
- Restart after adding new skills
- Check SKILL.md syntax
- Verify directory structure

#### UI Configuration Issues
- Validate openai.yaml syntax
- Check icon file paths
- Verify URL endpoints

#### Integration Problems
- Check backend service status
- Verify API endpoints
- Review network connectivity
