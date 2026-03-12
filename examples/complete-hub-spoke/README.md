# Complete Hub-Spoke AI Integration Example - Consensus-Based Agent Orchestration

This example demonstrates a **revolutionary multi-agent AI system** for GitOps infrastructure management, implementing **consensus-based distributed orchestration** and **tight feedback loops** based on the ai-agents-sandbox architecture.

## Revolutionary Architecture: Self-Organizing Agent Swarms

The example implements **bottom-up orchestration** through distributed consensus, achieving unprecedented response times and fault tolerance:

### Key Innovations from AI Agents Sandbox
- **30-Second Feedback Loops**: Ultra-tight local optimization vs minutes/hours traditional
- **Distributed Consensus**: Raft-based coordination eliminates single points of failure  
- **Self-Organizing Swarms**: Emergent intelligence from local agent interactions
- **Linear Scalability**: Performance scales with agent count, not controller capacity
- **Fault Tolerance**: System continues despite individual agent failures

## Architecture Overview

The example implements four deployment modes with consensus-based orchestration:

### 1. Consensus-First Enterprise Mode (Default)
- **Distributed Agent Consensus**: Raft-based coordination for all decisions
- **Self-Organizing Swarms**: Agents autonomously optimize local environments
- **Multi-Scale Feedback**: 30s micro-loops, 5m meso-loops, 1h macro-loops
- **Byzantine Fault Tolerance**: Handle up to 1/3 malicious agents

```
[Agent Swarms] ◄────────────► [Consensus Layer] ◄────────────► [Infrastructure]
       │                        │                        │
       ▼                        ▼                        ▼
[Local Optimization] ◄─────► [Distributed State] ◄─────► [Global Coordination]
       │                        │                        │
       ▼                        ▼                        ▼
[30-Second Loops] ◄─────► [Raft Consensus] ◄─────► [Emergent Intelligence]
```

### 2. Direct Consensus Mode
- **Direct Agent Coordination**: No gateway overhead, pure consensus protocols
- **Ultra-Fast Performance**: 15-second feedback loops possible
- **Good for development/small teams**

### 3. Local LLM Consensus Mode  
- **Local Consensus**: Uses local LLM service for agent decision-making
- **Maximum Privacy**: No external dependencies for consensus
- **Cost Control**: Predictable resource usage

### 4. Hybrid Consensus Mode
- **Mixed Coordination**: Critical decisions via distributed consensus
- **Local Autonomy**: Non-critical decisions made locally
- **Optimal Performance**: Balance of speed and coordination

## Components

### Agent Workflows (`agent-workflows/`)
- **Purpose**: Consensus-based agent orchestration and coordination
- **Capabilities**: Raft consensus, self-organizing swarms, tight feedback loops
- **Innovation**: Bottom-up orchestration with distributed decision-making
- **When to use**: All production deployments requiring autonomy

### AI Gateway (`ai-gateway/`)
- **Purpose**: Traffic control and basic security filtering (legacy mode)
- **Capabilities**: Regex-based filtering, rate limiting, audit logging
- **Limitations**: Cannot provide content-aware security (see architecture notes)
- **When to use**: Legacy enterprise compliance requirements
- **When to skip**: Consensus-based deployments, development environments

### AI CronJobs (`ai-cronjobs/`)
- **Drift Analysis Agent**: Runs every 4 hours with 30-second optimization loops
- **Validation Agent**: Daily manifest validation with consensus validation
- **Configuration**: Supports all four deployment modes via environment variables

### AI Validation Pipeline (`ai-validation/`)
- **GitOps Integration**: Triggered by Flux on repository changes
- **Real-time Validation**: Validates new manifests before deployment
- **Consensus Validation**: Multiple agents validate changes for reliability

## Deployment Options

### Option 1: Consensus-First Enterprise Mode (Default)
```bash
kubectl apply -f examples/complete-hub-spoke/
```
- Agent Workflows enabled with Raft consensus
- Self-organizing swarms with 30-second feedback loops
- Byzantine fault tolerance for production reliability
- Distributed decision-making across all agents

### Option 2: Direct Consensus Mode
```bash
# Comment out ai-gateway in kustomization.yaml
# Set CONSENSUS_MODE=direct in environment
kubectl apply -f examples/complete-hub-spoke/
```
- Pure agent-to-agent consensus protocols
- Ultra-fast 15-second feedback loops
- No gateway overhead
- Direct Raft-based coordination

### Option 3: Local LLM Consensus Mode
```bash
# Comment out ai-gateway in kustomization.yaml
# Set CONSENSUS_MODE=local and CLAUDE_BASE_URL to local endpoint
kubectl apply -f examples/complete-hub-spoke/
```
- Local consensus decision-making
- Maximum privacy and cost control
- Local LLM service for agent coordination
- No external API dependencies

### Option 4: Hybrid Consensus Mode
```bash
# Set CONSENSUS_MODE=hybrid in environment
kubectl apply -f examples/complete-hub-spoke/
```
- Critical decisions via distributed consensus
- Local autonomy for non-critical operations
- Optimal balance of speed and coordination
- Adaptive feedback loop intervals

## Configuration

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `CONSENSUS_MODE` | `distributed` | `distributed`, `direct`, `local`, `hybrid` | Consensus deployment mode |
| `FEEDBACK_LOOP_INTERVAL` | `30s` | `15s`, `30s`, `60s` | Agent optimization frequency |
| `CLAUDE_BASE_URL` | Gateway URL | Any valid endpoint | LLM service URL |
| `AGENT_QUORUM` | `3` | `1-10` | Consensus quorum size |
| `BYZANTINE_TOLERANCE` | `enabled` | `enabled`, `disabled` | Fault tolerance mode |

### Kustomization Overrides

```yaml
# For local LLM setup
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../control-plane/
  # - ai-gateway/  # Disabled for local LLM
  - ai-cronjobs/
  - ai-validation/
configMapGenerator:
- name: ai-deployment-config
  literals:
  - GATEWAY_MODE=local
  - CLAUDE_BASE_URL=http://local-llm-service.default.svc.cluster.local:8080
```

## Architecture Limitations

### AI Gateway Catch-22
The AI Gateway cannot effectively filter LLM requests without already processing content through an LLM, creating a circular dependency. Current implementation only provides:
- Basic regex pattern matching
- Rate limiting and authentication
- Request metadata logging

**What it cannot do**:
- Content-aware security filtering
- Semantic analysis of prompts
- Sophisticated data exfiltration prevention

### Recommended Alternatives

**For Enterprise Compliance**:
- Use API Gateway with rate limiting and audit logging
- Implement client-side data sanitization
- Use network policies and RBAC

**For Local LLM Setups**:
- Bypass AI Gateway entirely
- Use local network policies for security
- Implement application-level filtering if needed

## Monitoring

### Agent Metrics
- **Gateway**: Request count, rate limit events, pattern matches
- **CronJobs**: Success/failure rates, execution times
- **Validation**: Validation coverage, error rates

### Logs Collection
All agents log to stdout/stderr for collection by cluster logging solution.

## Security Considerations

### Network Policies
- AI Gateway only accepts traffic from authorized agents
- CronJobs and Validation have egress restrictions
- Local LLM mode requires different network configuration

### RBAC
- Minimal permissions per component
- Service accounts with least privilege
- No cluster-admin access required

## Troubleshooting

### Common Issues

1. **Gateway Not Ready**
   ```bash
   kubectl get deployment claude-code-gateway
   kubectl logs deployment/claude-code-gateway
   ```

2. **CronJobs Failing**
   ```bash
   kubectl get cronjobs
   kubectl get jobs
   kubectl logs job/<job-name>
   ```

3. **Validation Pipeline Issues**
   ```bash
   kubectl get kustomization ai-validation-kustomization
   kubectl describe kustomization ai-validation-kustomization
   ```

### Mode Switching

To switch between deployment modes:
1. Update `kustomization.yaml` resources section
2. Modify `configMapGenerator` literals
3. Apply changes: `kubectl apply -k examples/complete-hub-spoke/`

## Example Workflows

### Scheduled Infrastructure Monitoring
1. CronJob triggers every 4 hours
2. Sends analysis request to configured LLM endpoint
3. LLM analyzes infrastructure state
4. Results stored in persistent volume
5. Alerts triggered on policy violations

### GitOps-Driven Validation
1. Developer commits changes to Git
2. Flux detects changes and triggers validation
3. Validation Job runs AI analysis
4. Results stored and potentially create PR comments
5. Changes only applied if validation passes

## Cost Considerations

### Enterprise Mode
- Gateway overhead: ~128Mi RAM, 100m CPU per replica
- Audit logging storage: ~1GB/month
- API costs through Claude

### Direct API Mode
- No gateway overhead
- Direct API costs
- Faster response times

### Local LLM Mode
- LLM service resource requirements
- No external API costs
- Maximum privacy

This example provides flexible deployment options while maintaining clear documentation of architectural trade-offs and limitations.
