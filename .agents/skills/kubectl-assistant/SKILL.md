---
name: kubectl-assistant
description: |
  Generate and explain kubectl commands for Kubernetes cluster operations with safety checks and context awareness.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Kubectl Assistant — World-class Kubernetes Command Generation

Generates safe, executable kubectl commands with AI-powered context awareness, safety validation, and comprehensive explanations for Kubernetes operations.

## When to invoke
- Operators need kubectl command syntax help or troubleshooting guidance.
- Performing cluster operations but unsure of exact flags, selectors, or parameters.
- Generating automation scripts for routine cluster management tasks.
- Learning Kubernetes operations and need guided command generation.
- Validating kubectl commands before execution in production environments.

## Capabilities
- **Command generation**: Create syntactically correct kubectl commands from natural language.
- **Safety validation**: Flag destructive operations and require confirmation for dangerous commands.
- **Context awareness**: Use cluster state, RBAC permissions, and namespace context.
- **Multi-resource support**: Handle pods, services, deployments, configmaps, secrets, etc.
- **Operation modes**: Support query, create, update, delete, and troubleshooting operations.
- **Batch operations**: Generate multiple related commands for complex workflows.

## Invocation patterns
```bash
/kubectl-assistant generate --intent="get pods with issues" --namespace=production
/kubectl-assistant explain --command="kubectl get pods -o wide"
/kubectl-assistant validate --command="kubectl delete pod my-pod" --context=prod-cluster
/kubectl-assistant batch --workflow="rolling-update" --deployment=my-app
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `intent` | Natural language description of desired operation. | `"restart failing pods"` |
| `namespace` | Target Kubernetes namespace. | `production` |
| `resource` | Resource type (pod, deployment, service, etc.). | `deployment` |
| `command` | Raw kubectl command to explain or validate. | `"kubectl get pods"` |
| `context` | Cluster context name. | `prod-cluster` |
| `workflow` | Named workflow for batch command generation. | `rolling-update` |

## Output contract
```json
{
  "operationId": "KA-2026-0315-01",
  "commands": [
    {
      "command": "kubectl get pods --field-selector=status.phase!=Running -n production",
      "explanation": "List pods that are not in Running phase",
      "safety": "safe",
      "expectedOutput": "List of non-running pods with status information"
    }
  ],
  "warnings": [],
  "alternatives": [
    "kubectl get pods -n production | grep -v Running"
  ],
  "prerequisites": [
    "kubectl configured with production cluster context",
    "RBAC permissions for pod list operation"
  ]
}
```

## Dispatcher integration
**Triggers:**
- `cluster-issue`: Generate diagnostic kubectl commands
- `resource-operation`: Create safe kubectl commands for resource management
- `troubleshooting-request`: Provide kubectl-based troubleshooting guidance

**Emits:**
- `kubectl-command-generated`: New command ready for execution
- `safety-warning`: Destructive command flagged for review
- `command-validation-complete`: Command validated and ready

## AI intelligence features
- **Natural language processing**: Understand complex operational requests
- **Context correlation**: Use cluster state and recent operations for better commands
- **Safety intelligence**: Risk assessment for generated commands
- **Learning**: Adapt command patterns based on successful executions
- **Multi-step reasoning**: Break complex operations into safe sequential commands

## Human gates
- **Destructive operations**: Require human approval for delete, scale-to-zero, etc.
- **Production changes**: High-risk commands need SRE review
- **Batch operations**: Complex workflows need validation before execution

## Telemetry and monitoring
- Command generation success rates
- Safety violation attempts blocked
- Execution outcomes and error patterns
- User satisfaction and command utility metrics

## Testing requirements
- Unit tests for command generation logic
- Integration tests with kind/minikube clusters
- Safety validation test suites
- Natural language parsing accuracy tests

## Failure handling
- **Invalid requests**: Provide helpful error messages and suggestions
- **Permission issues**: Explain required RBAC permissions
- **Cluster connectivity**: Retry with exponential backoff, suggest alternatives
- **Command failures**: Provide debugging guidance and alternative approaches

## Related skills
- **k8s-troubleshoot**: Advanced diagnostic capabilities beyond basic kubectl
- **cluster-health-check**: Cluster-wide health assessment and kubectl automation
- **deployment-validation**: Pre-deployment kubectl command validation
- **policy-as-code**: RBAC and security policy integration for kubectl commands

## Security considerations
- Never execute commands automatically - always require user confirmation
- Validate all generated commands against allowlists
- Respect RBAC permissions and never suggest privilege escalation
- Log all command generations for audit trails
- Sanitize user inputs to prevent command injection

## Performance characteristics
- Command generation: <100ms for simple queries
- Safety validation: <50ms per command
- Context correlation: <200ms with cluster state
- Batch operations: Scales linearly with command count

## Scaling considerations
- Stateless design allows horizontal scaling
- Cluster context caching reduces API calls
- Command templates enable efficient generation
- Telemetry aggregation supports large deployments

## Success metrics
- Command generation accuracy >95%
- Safety violation rate <0.1%
- User satisfaction score >4.5/5
- Command execution success rate >90%

## API endpoints
```yaml
# REST API
POST /api/v1/kubectl/generate
POST /api/v1/kubectl/validate
POST /api/v1/kubectl/explain

# GraphQL
mutation GenerateKubectlCommand($intent: String!) {
  generateKubectlCommand(intent: $intent) {
    commands {
      command
      explanation
      safety
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/kubectl-assistant

# Generate command
kubectl-assistant generate "show me failing pods in production"

# Validate command
kubectl-assistant validate "kubectl delete pod my-pod"

# Interactive mode
kubectl-assistant --interactive
```

## Configuration
```yaml
kubectlAssistant:
  clusterContexts:
    - name: production
      apiserver: https://prod-k8s.example.com
      rbacChecks: true
    - name: staging
      apiserver: https://staging-k8s.example.com
      rbacChecks: false
  safetyRules:
    deleteCommands: require-approval
    productionChanges: require-review
  commandTemplates:
    getFailingPods: "kubectl get pods --field-selector=status.phase!=Running"
```

## Examples

### Basic pod inspection
```bash
/kubectl-assistant generate --intent="show me all pods in the web namespace"

# Generated: kubectl get pods -n web -o wide
# Explanation: List all pods in web namespace with detailed output
```

### Troubleshooting deployment
```bash
/kubectl-assistant generate --intent="debug why my deployment is failing"

# Generated: kubectl describe deployment my-deployment
# Generated: kubectl logs -l app=my-app --tail=100
# Generated: kubectl get events --sort-by=.metadata.creationTimestamp
```

### Safe resource deletion
```bash
/kubectl-assistant generate --intent="safely delete the test pod"

# Generated: kubectl delete pod test-pod --grace-period=30
# Warning: This will delete the pod. Confirm before execution.
# Alternative: kubectl scale deployment test-deployment --replicas=0
```

## Migration guide

### From manual kubectl usage
1. Identify common command patterns
2. Configure kubectl-assistant with cluster contexts
3. Train team on natural language command generation
4. Implement approval workflows for destructive operations

### From other tools
- **k9s**: kubectl-assistant provides AI-powered command generation
- **kubectl plugins**: Integrates with existing kubectl workflows
- **Custom scripts**: Replace with validated, auditable commands

## Troubleshooting

### Common issues
- **Permission denied**: Check RBAC permissions and cluster context
- **Command not found**: Ensure kubectl is in PATH and properly configured
- **Invalid syntax**: Review generated command and cluster API version
- **Network timeouts**: Check cluster connectivity and API server status

### Debug mode
```bash
kubectl-assistant --debug generate --intent="get pods"
# Shows: parsing steps, context correlation, safety checks
```

## Future roadmap
- Integration with kubectl plugins ecosystem
- Advanced AI reasoning for complex multi-step operations
- Real-time command execution with streaming output
- Integration with GitOps workflows for automated kubectl operations
- Machine learning-based command optimization

---

*Last updated: March 15, 2026*
*Version: 1.0.0*
