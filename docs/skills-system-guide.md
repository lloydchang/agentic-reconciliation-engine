# Temporal AI Agents Skills System

This document describes the AI Agent Skills system implemented for the Temporal AI Agents platform, based on the Claude Code and OpenAI Codex skills specifications.

## Overview

The Skills system enables AI agents to execute specialized, reusable capabilities through structured skill definitions. Skills are defined as directories containing `SKILL.md` files with YAML frontmatter and markdown instructions, allowing for both explicit invocation and implicit activation based on context.

## Architecture

### Backend Components

- **Skill Manager** (`backend/skills/skill.go`): Core skill parsing and management
- **Skill Service** (`backend/skills/service.go`): HTTP API endpoints for skill operations
- **Skill Discovery**: Automatic scanning of `.agents/skills/` directories
- **Skill Execution**: Runtime skill processing with argument substitution

### Frontend Components

- **Skills Management UI** (`frontend/src/components/SkillsManagement.tsx`): React component for skill browsing and execution
- **API Integration**: RESTful communication with backend skill service

### CLI Integration

- **Skill Commands**: Extended CLI with skill invocation and management commands
- **Interactive Mode**: Skill support in interactive shell sessions

## Skill Structure

Skills are organized in the following directory structure:

```
.agents/skills/
├── skill-name/
│   ├── SKILL.md          # Required: Skill definition and instructions
│   ├── template.md       # Optional: Template for structured output
│   ├── examples.md       # Optional: Usage examples
│   ├── reference.md      # Optional: Detailed reference material
│   ├── scripts/          # Optional: Executable scripts
│   └── assets/           # Optional: Static resources
│   └── agents/
│       └── openai.yaml   # Optional: UI metadata and dependencies
```

## SKILL.md Format

### Frontmatter Configuration

```yaml
---
name: skill-name
description: Brief description of what the skill does
disable-model-invocation: false  # Set to true to prevent implicit activation
user-invocable: true            # Whether users can invoke directly
allowed-tools: []               # Tools the skill can use
model: "specific-model"         # Model to use for execution
context: "fork"                 # "fork" for isolated execution
agent: "agent-type"             # Agent type for forked execution
argument-hint: "[param1] [param2]"  # Help text for arguments
---
```

### Content Instructions

The markdown content after the frontmatter contains the skill's instructions. Skills support:

- **Argument Substitution**: `$ARGUMENTS`, `$0`, `$1`, etc.
- **Session Variables**: `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`
- **Dynamic Context**: `!`command`` syntax (planned feature)

## Skill Discovery

Skills are automatically discovered from:

1. **Project Skills**: `.agents/skills/` in current directory and parent directories
2. **User Skills**: `~/.agents/skills/` (personal skills)
3. **Enterprise Skills**: Managed settings (future feature)

Priority order: Enterprise > Personal > Project (repo root) > Project (subdirs)

## Available Skills

### Core Skills

#### `compliance-check`
Initiates compliance validation workflows for infrastructure resources.

**Usage:**
```
/compliance-check <resource-id> [compliance-type] [priority]
```

**Parameters:**
- `resource-id`: Target resource identifier
- `compliance-type`: "SOC2", "GDPR", "HIPAA", "full-scan"
- `priority`: "low", "normal", "high", "critical"

#### `security-scan`
Executes security analysis workflows.

**Usage:**
```
/security-scan <resource-id> [scan-type] [priority]
```

**Parameters:**
- `resource-id`: Target resource identifier
- `scan-type`: "vulnerability", "malware", "configuration", "full"
- `priority`: "low", "normal", "high", "critical"

#### `cost-analysis`
Performs cost optimization analysis.

**Usage:**
```
/cost-analysis <resource-id> [analysis-type] [timeframe]
```

**Parameters:**
- `resource-id`: Target resource identifier
- `analysis-type`: "usage", "optimization", "forecast", "full"
- `timeframe`: "7d", "30d", "90d", "1y"

#### `workflow-management`
Manages Temporal AI Agents workflows.

**Usage:**
```
/workflow-management <action> [parameters]
```

**Actions:**
- `list [type]`: List active workflows
- `details <id>`: Get workflow details
- `cancel <id> [reason]`: Cancel workflow
- `status <id>`: Get workflow status
- `metrics [timeframe]`: Get workflow metrics

## Using Skills via CLI

### Command Line Interface

```bash
# List available skills
temporal-agents skill list

# Get skill information
temporal-agents skill info compliance-check

# Invoke a skill
temporal-agents skill invoke compliance-check prod-web-server-001 SOC2 high

# Short syntax
temporal-agents skill invoke /compliance-check prod-web-server-001 SOC2 high
```

### Interactive Mode

```bash
temporal-agents --interactive

> skills list
> skill compliance-check prod-db-001 full-scan critical
> /security-scan compromised-server malware high
```

## Using Skills via API

### List Skills
```bash
GET /api/skills
```

### Get Skill Details
```bash
GET /api/skills/{name}
```

### Execute Skill
```bash
POST /api/skills/{name}/execute
Content-Type: application/json

{
  "arguments": ["arg1", "arg2"]
}
```

### Discover Skills
```bash
POST /api/skills/discover
```

## Frontend Usage

Navigate to `/skills` in the web application to:

- Browse available skills with descriptions and metadata
- View skill details and configuration
- Execute skills with argument input
- Monitor execution results and status

## Creating Custom Skills

### Basic Skill Template

Create `.agents/skills/my-skill/SKILL.md`:

```yaml
---
name: my-skill
description: Description of what this skill does
---
# Skill Instructions

This skill performs the following tasks:

1. Step 1: Do something
2. Step 2: Process results
3. Step 3: Return output

## Parameters

- `$0`: First parameter (required)
- `$1`: Second parameter (optional)

## Usage Examples

/my-skill resource-123 option-value
```

### Advanced Skill Features

#### Supporting Files

Add supporting files in the skill directory:

- `template.md`: Structured output templates
- `examples.md`: Usage examples and patterns
- `reference.md`: Detailed API documentation
- `scripts/helper.py`: Utility scripts

#### Agent Metadata

Create `agents/openai.yaml` for UI configuration:

```yaml
interface:
  display_name: "User-Friendly Name"
  short_description: "Brief description for UI"
  icon_small: "./assets/icon.svg"
  brand_color: "#3B82F6"
  default_prompt: "Suggested prompt text"

policy:
  allow_implicit_invocation: false

dependencies:
  tools:
    - type: "mcp"
      value: "required-tool"
      description: "Tool description"
      transport: "streamable_http"
      url: "https://tool-endpoint.com"
```

## Security Considerations

### Tool Restrictions

Skills can be restricted to specific tools via `allowed-tools` frontmatter:

```yaml
allowed-tools: ["Read", "Grep", "Run"]  # Limited tool access
```

### Execution Isolation

Skills with `context: fork` run in isolated execution contexts, preventing interference with other operations.

### Command Execution

Dynamic command execution (`!`command``) requires security review and is currently disabled for safety.

## Best Practices

### Skill Design

1. **Single Responsibility**: Each skill should do one thing well
2. **Clear Descriptions**: Write descriptions that enable implicit activation
3. **Progressive Disclosure**: Keep main instructions focused, use supporting files for details
4. **Error Handling**: Include error scenarios and recovery steps

### Skill Organization

1. **Naming**: Use lowercase, hyphen-separated names
2. **Scope**: Place skills in appropriate directories based on intended usage
3. **Versioning**: Include version information in descriptions for API changes
4. **Testing**: Test skills with various input scenarios

### Performance

1. **Resource Awareness**: Consider execution time and resource usage
2. **Caching**: Use appropriate caching for expensive operations
3. **Async Operations**: Design for asynchronous execution where appropriate
4. **Monitoring**: Include logging and metrics collection

## Troubleshooting

### Common Issues

1. **Skills not appearing**: Run skill discovery or restart the backend
2. **Execution failures**: Check skill syntax and argument validation
3. **Permission errors**: Verify tool permissions and user access
4. **Performance issues**: Monitor execution times and optimize as needed

### Debug Commands

```bash
# Check backend logs
tail -f backend/logs/app.log

# Test API connectivity
curl http://localhost:8081/api/skills

# Validate skill syntax
temporal-agents skill info <skill-name>
```

## Future Enhancements

### Planned Features

1. **Dynamic Context Injection**: Safe command execution with `!`command`` syntax
2. **Skill Dependencies**: Automatic dependency resolution and loading
3. **Skill Marketplace**: Community skill sharing and discovery
4. **Advanced Permissions**: Granular access control and auditing
5. **Skill Composition**: Building complex skills from simpler components

### Integration Opportunities

1. **MCP Protocol**: Enhanced Model Context Protocol integration
2. **Plugin System**: Third-party skill extensions
3. **Workflow Integration**: Skills as workflow steps
4. **Multi-agent Coordination**: Skills for agent collaboration

## Contributing

To contribute new skills:

1. Follow the skill structure guidelines
2. Include comprehensive documentation
3. Add usage examples and error handling
4. Test with various scenarios
5. Submit via pull request with skill documentation

## Support

For issues with the skills system:

1. Check the troubleshooting guide
2. Review skill syntax and configuration
3. Examine backend and frontend logs
4. Create an issue with skill definition and error details

The skills system provides a powerful framework for extending AI agent capabilities while maintaining safety, performance, and usability standards.
