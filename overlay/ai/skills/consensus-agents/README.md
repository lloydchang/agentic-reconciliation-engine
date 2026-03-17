# Consensus-Based Agent Swarm Examples

This directory contains examples of **self-organizing agent swarms** that use **distributed consensus algorithms** to achieve feedback loops and autonomous infrastructure optimization.

## Overview

The consensus-based approach represents an evolution in AI agent orchestration, moving from centralized control to **bottom-up consensus systems**. This enables:

- **Fast Feedback Loops**: Local optimization decisions made in seconds
- **Fault Tolerance**: No single point of failure
- **Coordinated Intelligence**: Complex global behavior from local rules
- **Scalability**: Add more agents without changing architecture

## Files

### `consensus-swarm.yaml`
Defines the complete agent swarm including:
- **AgentSwarm**: Self-organizing swarm configuration
- **AgentConsensusConfig**: Raft-based consensus protocol
- **Deployments**: Leader and worker agent deployments
- **Services**: Agent communication endpoints
- **RBAC**: Permissions for agent operations
- **NetworkPolicies**: Secure agent-to-agent communication
- **Monitoring**: Prometheus metrics collection

### `agent-proposal.yaml`
Examples of consensus proposals:
- **Scaling Proposals**: Infrastructure scaling decisions
- **Security Proposals**: Security policy updates
- **Cost Proposals**: Cost optimization changes
- **Proposal Templates**: Reusable proposal templates

### `kustomization.yaml`
Flux integration with:
- **Dependency Management**: Proper sequencing with dependsOn
- **Tight Feedback Loops**: 1-minute reconciliation interval
- **Health Checks**: Automated health monitoring
- **Configuration Substitution**: Dynamic parameter injection

## Key Concepts

### 1. Tight Feedback Loops

**Micro-Loops (Seconds)**: Local optimization
```python
while True:
    current_state = observe_local_state()
    improvement = identify_local_improvement(current_state)
    if improvement.benefit > threshold:
        propose_to_consensus(improvement)
    time.sleep(30)  # 30-second feedback loop
```

**Meso-Loops (Minutes)**: Agent consensus
- Agents coordinate through Raft consensus
- Critical decisions require quorum approval
- Distributed validation of proposals

**Macro-Loops (Hours)**: Global optimization
- Cross-cloud resource allocation
- Long-term capacity planning
- System-wide learning

### 2. Consensus Protocol

**Raft-Based Consensus**:
- Leader election for coordination
- Log replication for consistency
- Commit guarantees for decisions
- Fault tolerance for failures

**Decision Thresholds**:
- Operational changes: 50% consensus
- Security changes: 80% consensus
- Critical changes: 100% consensus
- Cost changes: 60% consensus

### 3. Agent Specialization

**Cost Optimizer Agents**:
- Monitor resource utilization
- Identify cost-saving opportunities
- Propose scaling decisions
- Vote on budget-related changes

**Security Validator Agents**:
- Continuous security scanning
- Policy compliance checking
- Threat detection
- Vote on security-related changes

**Performance Tuner Agents**:
- Monitor application performance
- Identify optimization opportunities
- Propose configuration changes
- Vote on performance-related changes

## Deployment

### Prerequisites
- Kubernetes cluster with Flux CD
- Proper RBAC permissions
- Network policies for agent communication
- Monitoring stack (Prometheus/Grafana)

### Deploy Agent Swarm
```bash
# Deploy consensus-based agent swarm
kubectl apply -f overlay/examples/complete-hub-spoke/consensus-core/ai/runtime/

# Monitor deployment progress
kubectl get pods -n control-plane -l app=agent-swarm

# Check agent swarm status
kubectl get agentswarm -n control-plane

# View consensus decisions
kubectl get agentproposals -n control-plane
```

### Integration with Flux
```bash
# Apply kustomization with proper dependencies
kubectl apply -f overlay/examples/complete-hub-spoke/consensus-core/ai/runtime/kustomization.yaml

# Monitor Flux reconciliation
flux get kustomizations -A

# Check agent swarm health
kubectl logs -f deployment/agent-swarm-leader -n control-plane
```

## Monitoring

### Agent Metrics
- **Consensus Latency**: Time to reach consensus decisions
- **Proposal Success Rate**: Percentage of successful consensus proposals
- **Agent Health**: Health status of all agents in swarm
- **Feedback Loop Frequency**: Rate of local optimizations

### Prometheus Queries
```promql
# Consensus decision rate
rate(agent_consensus_decisions_total[5m])

# Agent health status
up{job="agent-swarm"}

# Feedback loop frequency
rate(agent_optimization_loops_total[5m])

# Proposal success rate
rate(agent_proposals_success_total[5m]) / rate(agent_proposals_total[5m])
```

## Usage Examples

### 1. Manual Consensus Proposal
```bash
# Create a scaling proposal
kubectl apply -f - <<EOF
apiVersion: consensus.gitops.io/v1alpha1
kind: AgentProposal
metadata:
  name: manual-scale-up
spec:
  proposal: "Scale production cluster due to high load"
  proposer: "manual-operator"
  requiredVotes: 3
  timeout: "5m"
  voters: ["security-agent", "cost-agent", "performance-agent"]
EOF
```

### 2. Monitor Consensus Process
```bash
# Watch consensus decisions in real-time
kubectl get agentproposals -n control-plane -w

# View agent swarm logs
kubectl logs -f deployment/agent-swarm-leader -n control-plane

# Check agent health
kubectl get pods -n control-plane -l app=agent-swarm -o wide
```

### 3. Emergency Override
```bash
# Emergency override for critical situations
kubectl annotate agentproposal emergency-proposal \
  consensus.gitops.io/emergency="true" \
  consensus.gitops.io/override-votes="true"
```

## Architecture Benefits

### 1. **True Tight Feedback Loops**
- Local decisions made without central coordination
- Rapid response to changing conditions
- Continuous optimization at multiple time scales

### 2. **Fault Tolerance and Resilience**
- No single point of failure
- Automatic leader re-election
- Graceful degradation under failures

### 3. **Scalability**
- Horizontal agent scaling
- Distributed decision making
- Local resource optimization

### 4. **Coordinated Intelligence**
- Swarm behavior from simple rules
- Adaptive learning
- Self-organization

## Migration Path

### Phase 1: Foundation
1. Deploy basic consensus protocol
2. Implement feedback loops
3. Add agent-to-agent communication

### Phase 2: Advanced Features
1. Multi-cloud consensus
2. Coordinated behavior patterns
3. Dynamic agent specialization

### Phase 3: Production Readiness
1. Enterprise security features
2. Advanced monitoring
3. Performance optimization

## Troubleshooting

### Common Issues

**Consensus Deadlock**:
- Check agent network connectivity
- Verify quorum requirements
- Review proposal timeout settings

**High Consensus Latency**:
- Optimize agent communication
- Check resource constraints
- Review consensus protocol configuration

**Agent Failures**:
- Review agent logs
- Check resource limits
- Verify RBAC permissions

### Debug Commands
```bash
# Check agent connectivity
kubectl exec -it deployment/agent-swarm-leader -- nc -zv agent-swarm-workers 8080

# Review consensus logs
kubectl logs deployment/agent-swarm-leader --since=1h

# Check resource usage
kubectl top pods -n control-plane -l app=agent-swarm
```

## Security Considerations

- **Agent Isolation**: Each agent runs with minimal permissions
- **Encrypted Communication**: All agent-to-agent communication encrypted
- **Audit Logging**: All consensus decisions logged and auditable
- **Network Segmentation**: Agent communication restricted to secure channels

This consensus-based approach transforms infrastructure management from centralized control to distributed intelligence, enabling autonomous optimization through tight feedback loops while maintaining system coherence through lightweight consensus protocols.
