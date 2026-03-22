# AI Agent Deployment & Crossplane Fixes

This plan aims to resolve the deployment issues for the AI agents (ADE, Memory Selector, Standalone Backend) and improve the Crossplane setup.

## Proposed Changes

- [x] Fix Memory Selector memory and image pull issues.
- [x] Fix Standalone Backend image pull issues.
- [x] Fix ADE compilation and nil pointer crash.
- [ ] Verify ADE in cluster.

### AI Agent Deployments

#### [NEW] [kustomization.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/kustomization.yaml)
Create a kustomization file for the ADE agent.
- Include [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/deployment.yaml), [pvc.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/pvc.yaml), [service.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/service.yaml).
- Exclude [servicemonitor.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/servicemonitor.yaml) for now as the CRD is missing.

#### [NEW] [kustomization.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/memory-selector/kustomization.yaml)
Create a kustomization file for the Memory Selector agent.
- Include [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/deployment.yaml), [service.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/service.yaml).
- Exclude [servicemonitor.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/servicemonitor.yaml).

#### [NEW] [kustomization.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/standalone-backend/kustomization.yaml)
Create a kustomization file for the Standalone Backend agent.
- Include [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/deployment.yaml), [service.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/service.yaml), [configmap.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/standalone-backend/configmap.yaml), [agent-skills-configmap.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/standalone-backend/agent-skills-configmap.yaml).
- Exclude [servicemonitor.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/servicemonitor.yaml).

#### [MODIFY] [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/ade/deployment.yaml)
- Reduce memory requests to `128Mi`.
- Reduce CPU requests to `50m`.
- Reduce replicas to `1`.

#### [MODIFY] [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/memory-selector/deployment.yaml)
- Reduce memory requests to `32Mi`.
- Reduce CPU requests to `20m`.
- Reduce replicas to `1`.

#### [MODIFY] [deployment.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/deployments/agents/standalone-backend/deployment.yaml)
- Reduce memory requests to `128Mi`.
- Reduce CPU requests to `50m`.

### Crossplane Enhancements

#### [MODIFY] [provider-config-aws.yaml](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/resources/infrastructure/crossplane/providers/provider-config-aws.yaml)
Ensure it uses a valid secret reference for when credentials are provided.

## Verification Plan

### Automated Tests
1.  **Kustomize Build**: Run `kubectl kustomize core/ai/deployments/agents/` to ensure the structure is valid.
2.  **Dry Run Apply**: Run `kubectl apply --dry-run=client -k core/ai/deployments/agents/` to verify Kubernetes accepts the resources.
3.  **Actual Apply**: Apply the changes and check pod status: `kubectl get pods -n ai-infrastructure`.

### Manual Verification
1.  Check logs of the agents: `kubectl logs -l layer=ai-agents -n ai-infrastructure`.
2.  Verify the memory footprint: `kubectl top pods -n ai-infrastructure` (if available).
