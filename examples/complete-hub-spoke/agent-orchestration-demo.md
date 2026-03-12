# Agent-to-Agent Orchestration in Complete AI Integration Example

This document demonstrates how multiple AI agents orchestrate together in the GitOps Infrastructure Control Plane, specifically in the `examples/complete-hub-spoke/` setup.

## Architecture Overview

The complete example implements a multi-agent AI system where Claude Code agents work together through orchestrated workflows:

```
[Git Repository] ── Flux ──> [Infrastructure Changes]
       │                        │
       │                        ▼
       │              [AI Validation Pipeline]
       │                        │
       ▼                        ▼
[AI CronJobs] ◄────────────► [AI Gateway] ◄────────────► [Claude Code Agents]
       │                        │
       │                        │
       ▼                        ▼
[Reports Storage] ◄────────────► [Audit Logs]
```

## Agent Components

### 1. AI Gateway Agent (`ai-gateway/gateway.yaml`)
**Role**: Traffic controller and security filter for all Claude Code interactions.

**Capabilities**:
- Proxies requests to Anthropic API
- Implements prompt guards to prevent sensitive data exfiltration
- Provides audit logging for compliance
- Rate limiting and authentication

**Orchestration Interface**:
- Receives requests from CronJobs and Validation Pipeline
- Returns filtered responses to agents
- Logs all interactions for monitoring

### 2. AI CronJobs Agents (`ai-cronjobs/cronjobs.yaml`)
**Role**: Scheduled autonomous agents for continuous infrastructure monitoring.

**Capabilities**:
- **Drift Analysis Agent**: Monitors infrastructure state every 4 hours
- **Validation Agent**: Daily manifest validation and security checks

**Orchestration Interface**:
- Queries AI Gateway for Claude Code analysis
- Writes reports to persistent storage
- Triggers alerts on policy violations

### 3. AI Validation Pipeline Agent (`ai-validation/validation.yaml`)
**Role**: GitOps-driven validation agent triggered by repository changes.

**Capabilities**:
- Monitors Git commits for manifest changes
- Runs AI-powered validation on new/updated YAML
- Generates fix suggestions and compliance reports

**Orchestration Interface**:
- Subscribes to Flux GitRepository changes
- Communicates with AI Gateway for validation tasks
- Stores results in validation PVC

## Orchestration Flows

### Flow 1: Scheduled Infrastructure Monitoring

```yaml
# CronJob triggers every 4 hours
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ai-infra-drift-analysis
spec:
  schedule: "0 */4 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: claude-analyzer
            env:
            - name: ANTHROPIC_BASE_URL
              value: "http://claude-code-gateway.control-plane.svc.cluster.local:80"
            command:
            - claude
            - -p
            - "Analyze infrastructure drift..."
```

**Sequence**:
1. **CronJob Agent** wakes up on schedule
2. **CronJob Agent** sends analysis request to **AI Gateway Agent**
3. **AI Gateway Agent** filters request and forwards to Claude Code
4. **Claude Code Agent** performs analysis
5. **AI Gateway Agent** logs interaction and returns results
6. **CronJob Agent** stores report in PVC

### Flow 2: GitOps-Driven Validation

```yaml
# Flux Kustomization watches for Git changes
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: ai-validation-kustomization
spec:
  dependsOn:
  - name: ai-gateway  # Waits for gateway to be ready
  - name: ai-cronjobs # Waits for cronjobs setup
  sourceRef:
    kind: GitRepository
    name: ai-validation-source
  # Triggers validation job on Git changes
```

**Sequence**:
1. **Developer** commits infrastructure changes to Git
2. **Flux** detects changes and reconciles
3. **Validation Pipeline Agent** (Flux Kustomization) triggers
4. **Validation Pipeline Agent** launches Job container
5. **Validation Job** sends validation request to **AI Gateway Agent**
6. **AI Gateway Agent** routes to Claude Code for analysis
7. **Claude Code Agent** validates manifests and generates report
8. **Validation Job** stores results and potentially creates PR comments

### Flow 3: Inter-Agent Communication via Shared Storage

```yaml
# All agents share persistent volumes
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ai-reports-pvc  # Shared by cronjobs
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ai-validation-pvc  # Shared by validation pipeline
```

**Sequence**:
1. **CronJob Agent** writes drift analysis report to `ai-reports-pvc`
2. **Validation Pipeline Agent** reads historical reports for trend analysis
3. **Both agents** use shared storage for collaborative insights

## Security Orchestration

### Network Policies
```yaml
# AI Gateway only accepts traffic from authorized agents
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  podSelector:
    matchLabels:
      app: claude-gateway
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ai-cronjob
    - podSelector:
        matchLabels:
          app: ai-validation
```

### RBAC Coordination
All agents share the same service account with minimal permissions:
- Read secrets for API keys
- Write to designated PVCs
- No cluster-admin access

## Fault Tolerance

### Agent Failure Handling
- **CronJobs** have `backoffLimit: 1` and `restartPolicy: Never`
- **Validation Jobs** run with `activeDeadlineSeconds` to prevent hangs
- **Gateway** has liveness/readiness probes for health checking

### Dependency Management
Flux `dependsOn` ensures proper startup order:
- `ai-gateway` must be ready before `ai-cronjobs`
- `ai-gateway` and `ai-cronjobs` must be ready before `ai-validation`

## Monitoring and Observability

### Agent Metrics
- **Gateway**: Request/response metrics, blocked prompts count
- **CronJobs**: Success/failure rates, execution times
- **Validation**: Validation coverage, false positive rates

### Centralized Logging
All agents log to stdout/stderr, collected by cluster logging solution.

## Scaling Considerations

### Horizontal Scaling
- **Gateway**: Can scale replicas based on request load
- **CronJobs**: Schedule frequency can be adjusted
- **Validation**: Parallel job execution for large repositories

### Resource Management
- **Memory**: Claude Code requires 1-2Gi per agent
- **CPU**: 0.5-1 core per concurrent agent
- **Storage**: 10-20Gi for reports and validation data

## Example: Complete Agent-to-Agent Workflow

```bash
# 1. Deploy the complete system
kubectl apply -f examples/complete-hub-spoke/

# 2. Monitor agent interactions
kubectl logs -f deployment/claude-code-gateway

# 3. Check scheduled job execution
kubectl get cronjobs

# 4. View validation results
kubectl exec -it deployment/claude-code-gateway -- cat /reports/drift-analysis-2026-03-12.json

# 5. Trigger manual validation
kubectl create job manual-validation --from=cronjob/ai-manifest-validation
```

This orchestration enables autonomous infrastructure management where AI agents continuously monitor, validate, and report on infrastructure state through coordinated, secure interactions.
