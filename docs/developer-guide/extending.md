# Extending the Platform

The AI Agents Sandbox is designed for easy extension and contribution. This guide covers how to add new skills, interfaces, workflows, and integrations to expand the platform's capabilities.

## Contribution Guidelines

### Development Workflow
1. **Fork the repository** and create a feature branch
2. **Follow the coding standards** outlined in agent behavior rules
3. **Write comprehensive tests** for new functionality
4. **Update documentation** for any changes
5. **Submit a pull request** with detailed description

### Code Standards
- **Go backend**: Follow standard Go conventions and effective Go practices
- **TypeScript/React frontend**: Use ESLint configuration and TypeScript strict mode
- **Documentation**: Use Markdown with consistent formatting
- **Testing**: Maintain >80% code coverage for new code

## Adding New AI Skills

### Skill Directory Structure
Create a new directory under `.agents/skills/your-skill-name/`:

```
.agents/skills/your-skill-name/
├── SKILL.md           # Skill definition and documentation
├── activities.go      # Go activity implementations (optional)
├── workflow.go        # Workflow definitions (optional)
├── scripts/           # Helper scripts (optional)
│   └── validate.sh
└── templates/         # Output templates (optional)
    └── report.md
```

### Skill Definition Format
Each skill requires a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: your-skill-name
description: Brief description of what the skill does
version: 1.0.0
category: infrastructure|security|compliance|operations
author: Your Name

# Input parameters
parameters:
  - name: targetResource
    type: string
    required: true
    description: Resource to operate on
  - name: environment
    type: string
    enum: [dev, staging, prod]
    default: dev
    description: Target environment

# Output schema
outputs:
  - name: result
    type: object
    description: Operation result
  - name: status
    type: string
    enum: [success, partial, failed]
  - name: executionTime
    type: number
    description: Execution time in milliseconds

# Human gates and safety controls
human_gates:
  - condition: "environment == 'prod'"
    action: require_approval
    priority: high
    message: "Production changes require approval"

# Tool requirements
tools:
  - name: kubectl
    version: ">=1.25.0"
    permissions: [read, write]
  - name: terraform
    version: ">=1.5.0"
    permissions: [plan, apply]

# Error handling
error_handling:
  retry_count: 3
  backoff_strategy: exponential
  timeout_seconds: 300
---

# Skill Documentation

## Overview
Detailed description of the skill's purpose and capabilities.

## Usage Examples

### Basic Usage
```bash
# CLI usage
./cli skill invoke /your-skill target-resource environment=prod

# REST API
curl -X POST http://localhost:8081/api/skills/your-skill/execute \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"targetResource": "resource-123", "environment": "prod"}'
```

### Advanced Usage
Describe complex usage patterns and edge cases.

## Implementation Details

### Workflow Logic
Describe the step-by-step execution logic.

### Error Scenarios
Document common failure modes and recovery procedures.

### Performance Characteristics
Expected execution times, resource usage, scaling considerations.
```

### Implementing Skill Activities

Create Go activities for skill execution:

```go
// activities.go
package yourskill

import (
    "context"
    "time"

    "go.temporal.io/sdk/activity"
)

// YourSkillActivity implements the core skill logic
func YourSkillActivity(ctx context.Context, input YourSkillInput) (YourSkillOutput, error) {
    logger := activity.GetLogger(ctx)
    logger.Info("Starting your skill activity", "input", input)

    startTime := time.Now()

    // Implement skill logic here
    result, err := executeSkillLogic(input)
    if err != nil {
        logger.Error("Skill execution failed", "error", err)
        return YourSkillOutput{}, err
    }

    executionTime := time.Since(startTime).Milliseconds()

    output := YourSkillOutput{
        Result:        result,
        Status:        "success",
        ExecutionTime: executionTime,
    }

    logger.Info("Skill activity completed", "output", output)
    return output, nil
}

// Input/Output types
type YourSkillInput struct {
    TargetResource string `json:"targetResource"`
    Environment    string `json:"environment"`
}

type YourSkillOutput struct {
    Result        interface{} `json:"result"`
    Status        string      `json:"status"`
    ExecutionTime int64       `json:"executionTime"`
}
```

### Workflow Integration

Create workflow definitions for complex multi-step skills:

```go
// workflow.go
func YourSkillWorkflow(ctx workflow.Context, input YourSkillInput) (YourSkillOutput, error) {
    // Activity options with retry policy
    ao := workflow.ActivityOptions{
        StartToCloseTimeout: time.Minute * 10,
        RetryPolicy: &temporal.RetryPolicy{
            InitialInterval: time.Second * 5,
            BackoffCoefficient: 2.0,
            MaximumInterval: time.Minute * 2,
            MaximumAttempts: 3,
        },
    }
    ctx = workflow.WithActivityOptions(ctx, ao)

    // Execute validation step
    var validationResult ValidationOutput
    err := workflow.ExecuteActivity(ctx, ValidateInputActivity, input).Get(ctx, &validationResult)
    if err != nil {
        return YourSkillOutput{}, err
    }

    // Check for human gate
    if validationResult.RequiresApproval {
        approvalSignal := workflow.GetSignalChannel(ctx, "approval")
        approvalSignal.Receive(ctx, nil) // Wait for approval signal
    }

    // Execute main activity
    var result YourSkillOutput
    err = workflow.ExecuteActivity(ctx, YourSkillActivity, input).Get(ctx, &result)
    if err != nil {
        return YourSkillOutput{}, err
    }

    // Cleanup activities
    workflow.ExecuteActivity(ctx, CleanupActivity, input).Get(ctx, nil)

    return result, nil
}
```

## Interface Development

### Adding New Interface Types

#### REST API Extensions
Extend the backend with new endpoints:

```go
// Add to main.go or separate router
func setupRoutes(router *mux.Router) {
    // Existing routes...
    router.HandleFunc("/api/your-endpoint", yourEndpointHandler).Methods("GET", "POST")
}

// Handler implementation
func yourEndpointHandler(w http.ResponseWriter, r *http.Request) {
    // Parse request
    var req YourRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Process request
    result, err := processYourRequest(req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Return response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(result)
}
```

#### MCP Server Extensions
Add new tools to the MCP server:

```go
// Add to mcp/server.go
func setupMCPServer() *mcpserver.Server {
    server := mcpserver.NewServer()

    // Register existing tools...

    // Add your tool
    server.RegisterTool("your-tool", &mcpserver.Tool{
        Name:        "your-tool",
        Description: "Description of your tool",
        InputSchema: yourToolSchema,
        Handler:     yourToolHandler,
    })

    return server
}

func yourToolHandler(ctx context.Context, request *mcpserver.ToolRequest) (*mcpserver.ToolResponse, error) {
    // Implement tool logic
    result := executeYourTool(request.Parameters)

    return &mcpserver.ToolResponse{
        Content: []mcpserver.Content{
            {
                Type: "text",
                Text: result,
            },
        },
    }, nil
}
```

#### Frontend Plugins
Create new Backstage plugins:

```typescript
// plugins/your-plugin/src/plugin.ts
import { createPlugin, createRoutableExtension } from '@backstage/core-plugin-api';

export const yourPlugin = createPlugin({
  id: 'your-plugin',
  routes: {
    root: yourPluginRouteRef,
  },
});

export const YourPluginPage = yourPlugin.provide(
  createRoutableExtension({
    name: 'YourPluginPage',
    component: () => import('./components/YourComponent').then(m => m.YourComponent),
    mountPoint: yourPluginRouteRef,
  }),
);
```

### WebMCP Client Extensions
Enhance the browser-based MCP client:

```typescript
// frontend/src/components/WebMCPClient.tsx
export const WebMCPClient = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedTool, setSelectedTool] = useState<string>('');

  useEffect(() => {
    // Fetch available tools
    fetch('/mcp/tools')
      .then(res => res.json())
      .then(setTools);
  }, []);

  const executeTool = async (toolName: string, params: any) => {
    const response = await fetch('/mcp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: params,
        },
      }),
    });

    const result = await response.json();
    return result;
  };

  return (
    <div>
      <ToolSelector tools={tools} onSelect={setSelectedTool} />
      <ToolExecutor
        tool={selectedTool}
        onExecute={(params) => executeTool(selectedTool, params)}
      />
    </div>
  );
};
```

## Advanced Orchestration Patterns

### Multi-Agent Collaboration
Implement workflows that coordinate multiple agents:

```go
func MultiAgentWorkflow(ctx workflow.Context, input MultiAgentInput) (MultiAgentOutput, error) {
    // Start security agent
    var securityResult SecurityOutput
    securityFuture := workflow.ExecuteActivity(ctx, SecurityAgentActivity, input)
    defer func() {
        if securityFuture.IsReady() {
            securityFuture.Get(ctx, &securityResult)
        }
    }()

    // Start compliance agent
    var complianceResult ComplianceOutput
    complianceFuture := workflow.ExecuteActivity(ctx, ComplianceAgentActivity, input)

    // Start cost optimization agent
    var costResult CostOutput
    costFuture := workflow.ExecuteActivity(ctx, CostOptimizationAgentActivity, input)

    // Wait for all agents to complete
    selector := workflow.NewSelector(ctx)

    completed := 0
    totalAgents := 3

    for completed < totalAgents {
        selector.AddFuture(securityFuture, func(f workflow.Future) {
            f.Get(ctx, &securityResult)
            completed++
        })

        selector.AddFuture(complianceFuture, func(f workflow.Future) {
            f.Get(ctx, &complianceResult)
            completed++
        })

        selector.AddFuture(costFuture, func(f workflow.Future) {
            f.Get(ctx, &costResult)
            completed++
        })

        selector.Select(ctx)
    }

    // Consensus building
    consensus := buildConsensus(securityResult, complianceResult, costResult)

    // Human review if consensus not reached
    if !consensus.agreed {
        approvalFuture := workflow.RequestHumanApproval(ctx, consensus)
        approvalFuture.Get(ctx, nil)
    }

    return consensus.finalDecision, nil
}
```

### Dynamic Workflow Generation
Create workflows based on runtime conditions:

```go
func DynamicWorkflow(ctx workflow.Context, input DynamicInput) (DynamicOutput, error) {
    // Analyze requirements
    requirements := analyzeRequirements(input)

    // Build workflow dynamically
    activities := []interface{}{}

    if requirements.needsSecurityScan {
        activities = append(activities, SecurityScanActivity)
    }

    if requirements.needsComplianceCheck {
        activities = append(activities, ComplianceCheckActivity)
    }

    if requirements.needsCostAnalysis {
        activities = append(activities, CostAnalysisActivity)
    }

    // Execute activities in sequence
    results := []interface{}{}
    for _, activity := range activities {
        var result interface{}
        err := workflow.ExecuteActivity(ctx, activity, input).Get(ctx, &result)
        if err != nil {
            return DynamicOutput{}, err
        }
        results = append(results, result)
    }

    // Aggregate results
    finalResult := aggregateResults(results)

    return finalResult, nil
}
```

## Cloud Provider Integrations

### Adding New Cloud Providers
Extend the infrastructure emulator:

```go
// backend/infrastructure/providers/yourcloud.go
package providers

import (
    "context"
    "fmt"

    "github.com/yourorg/ai-agents-sandbox/backend/infrastructure"
)

type YourCloudProvider struct{}

func (p *YourCloudProvider) ListResources(ctx context.Context, filters map[string]string) ([]infrastructure.Resource, error) {
    // Implement resource discovery
    resources := []infrastructure.Resource{}

    // Your cloud API calls here
    // ...

    return resources, nil
}

func (p *YourCloudProvider) GetResource(ctx context.Context, id string) (*infrastructure.Resource, error) {
    // Implement resource retrieval
    // Your cloud API calls here
    // ...

    return &resource, nil
}

func (p *YourCloudProvider) ValidateResource(ctx context.Context, resource infrastructure.Resource) ([]infrastructure.ValidationIssue, error) {
    // Implement resource validation
    issues := []infrastructure.ValidationIssue{}

    // Your validation logic here
    // ...

    return issues, nil
}

// Register provider
func init() {
    infrastructure.RegisterProvider("yourcloud", &YourCloudProvider{})
}
```

### Multi-Cloud Orchestration
Create workflows that span multiple cloud providers:

```go
func MultiCloudWorkflow(ctx workflow.Context, input MultiCloudInput) (MultiCloudOutput, error) {
    // Deploy to AWS
    var awsResult AWSDeploymentResult
    err := workflow.ExecuteActivity(ctx, DeployToAWSActivity, input).Get(ctx, &awsResult)
    if err != nil {
        return MultiCloudOutput{}, fmt.Errorf("AWS deployment failed: %w", err)
    }

    // Deploy to Azure
    var azureResult AzureDeploymentResult
    err = workflow.ExecuteActivity(ctx, DeployToAzureActivity, input).Get(ctx, &azureResult)
    if err != nil {
        return MultiCloudOutput{}, fmt.Errorf("Azure deployment failed: %w", err)
    }

    // Configure cross-cloud networking
    var networkResult NetworkConfigResult
    err = workflow.ExecuteActivity(ctx, ConfigureCrossCloudNetworkingActivity, MultiCloudNetworkInput{
        AWSResources:   awsResult.Resources,
        AzureResources: azureResult.Resources,
    }).Get(ctx, &networkResult)
    if err != nil {
        return MultiCloudOutput{}, fmt.Errorf("Network configuration failed: %w", err)
    }

    return MultiCloudOutput{
        AWSDeployment:   awsResult,
        AzureDeployment: azureResult,
        NetworkConfig:   networkResult,
    }, nil
}
```

## Compliance Framework Extensions

### Adding New Compliance Standards
Implement additional regulatory compliance checks:

```go
// backend/skills/compliance/yourframework.go
package compliance

import (
    "context"
    "fmt"
)

type YourFrameworkChecker struct{}

func (c *YourFrameworkChecker) CheckCompliance(ctx context.Context, resource interface{}) (*ComplianceResult, error) {
    result := &ComplianceResult{
        Framework:   "YOUR_FRAMEWORK",
        Score:       0,
        Issues:      []ComplianceIssue{},
        Passed:      true,
    }

    // Implement your framework's compliance checks
    // ...

    // Example checks
    if !hasRequiredEncryption(resource) {
        result.Issues = append(result.Issues, ComplianceIssue{
            Severity: "HIGH",
            Description: "Resource missing required encryption",
            Remediation: "Enable encryption at rest and in transit",
        })
        result.Passed = false
    }

    if !hasProperAccessControls(resource) {
        result.Issues = append(result.Issues, ComplianceIssue{
            Severity: "MEDIUM",
            Description: "Access controls not properly configured",
            Remediation: "Implement least privilege access policies",
        })
        result.Passed = false
    }

    // Calculate score
    if result.Passed {
        result.Score = 100
    } else {
        result.Score = calculateScore(result.Issues)
    }

    return result, nil
}

func (c *YourFrameworkChecker) GetRequirements() []ComplianceRequirement {
    return []ComplianceRequirement{
        {
            ControlID:   "YF-001",
            Description: "Encryption at rest must be enabled",
            Severity:    "HIGH",
        },
        {
            ControlID:   "YF-002",
            Description: "Access controls must follow least privilege",
            Severity:    "MEDIUM",
        },
        // Add more requirements...
    }
}

// Register checker
func init() {
    RegisterComplianceChecker("yourframework", &YourFrameworkChecker{})
}
```

## Testing & Validation

### Skill Testing Framework
Create comprehensive tests for new skills:

```go
// backend/skills/yourskill/yourskill_test.go
package yourskill

import (
    "testing"
    "time"

    "github.com/stretchr/testify/assert"
    "go.temporal.io/sdk/testsuite"
)

func TestYourSkillWorkflow(t *testing.T) {
    suite := &testsuite.WorkflowTestSuite{}
    env := suite.NewTestWorkflowEnvironment()

    // Mock activities
    env.OnActivity(YourSkillActivity, mock.Anything).Return(mockOutput, nil)

    // Execute workflow
    env.ExecuteWorkflow(YourSkillWorkflow, testInput)

    // Verify expectations
    assert.True(t, env.IsWorkflowCompleted())
    assert.NoError(t, env.GetWorkflowError())

    var result YourSkillOutput
    env.GetWorkflowResult(&result)
    assert.Equal(t, "success", result.Status)
}

func TestYourSkillActivity(t *testing.T) {
    // Unit test for activity
    result, err := YourSkillActivity(context.Background(), testInput)

    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Equal(t, "expected_output", result.Result)
}
```

### Integration Testing
Test skill integration with the broader system:

```bash
# Test skill auto-discovery
go test ./backend/skills/... -run TestSkillDiscovery

# Test workflow execution
go test ./backend/workflows/... -run TestYourWorkflow

# Test API endpoints
go test ./backend/api/... -run TestYourSkillAPI

# Full integration test
./scripts/validate.sh
```

## Documentation Updates

### Updating Skill Documentation
When adding new skills, update the documentation:

1. **Add to skills reference**: Update `docs/user-guide/skills-reference.md`
2. **Add API documentation**: Update `docs/developer-guide/skills-api.md`
3. **Update workflow docs**: Add to `docs/user-guide/workflows.md` if creating new composite workflows
4. **Update implementation**: Document in `docs/developer-guide/implementation.md`

### Version Management
Follow semantic versioning for skill updates:
- **MAJOR**: Breaking changes to input/output schemas
- **MINOR**: New features or enhancements
- **PATCH**: Bug fixes and minor improvements

This extensible architecture allows the AI Agents Sandbox to continuously evolve with new capabilities while maintaining safety, reliability, and ease of integration.
