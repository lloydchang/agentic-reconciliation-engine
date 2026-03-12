---
name: infrastructure-manager
description: Manages Kubernetes infrastructure deployments, drift detection, and remediation using consensus-based decision making. Use when infrastructure changes are needed, drift is detected, or consensus decisions are required. Achieves tight feedback loops through local optimization and distributed consensus coordination.
license: Apache-2.0
metadata:
  author: gitops-control-plane
  version: "3.0"
  category: infrastructure
  complexity: advanced
  tags: [kubernetes, consensus, distributed, gitops, feedback-loops]
compatibility: Requires kubectl, helm, flux, and consensus protocol support with Raft implementation
allowed-tools: Bash(kubectl:*) Bash(helm:*) Bash(flux:*) Bash(consensus:*) Read Write
context: fork
agent: Plan
---

# Consensus-Based Infrastructure Manager Skill

## Quick Start
This skill provides infrastructure management capabilities with distributed consensus decision making and fast feedback loops. Use it for:

- **Deploying applications and infrastructure** with consensus validation (30s response)
- **Detecting and fixing infrastructure drift** through agent coordination (5m consensus)
- **Security compliance validation** with distributed voting (weighted decisions)
- **Cost optimization** through swarm intelligence (coordinated behavior)
- **Multi-cloud resource management** with consensus coordination

## Core Capabilities

### 1. Fast Feedback Loop Implementation

#### Micro-Loop (30 seconds): Local Optimization
```bash
#!/bin/bash
# Local optimization with 30-second feedback loop
run_fast_feedback_loop() {
    while true; do
        # 1. Observe local state (no network calls)
        current_state=$(observe_local_metrics)
        
        # 2. Identify local improvement opportunity
        improvement=$(identify_local_improvement "$current_state")
        
        # 3. Propose change to agent network if beneficial
        if [[ -n "$improvement" ]]; then
            propose_to_consensus "$improvement"
            echo "$(date): Proposed optimization: $improvement"
        fi
        
        # 4. Sleep for tight feedback
        sleep 30
    done
}

observe_local_metrics() {
    # Fast local observation (no network calls)
    echo "cpu_usage:$(kubectl top pods -A --no-headers | awk '{sum+=$3} END {print sum}')"
    echo "memory_usage:$(kubectl top pods -A --no-headers | awk '{sum+=$4} END {print sum}')"
    echo "error_rate:$(kubectl get events --sort-by='.lastTimestamp' --field-selector=type=Warning --no-headers | wc -l)"
    echo "response_time:$(curl -s -o /dev/null -w '%{time_total}' http://localhost:8080/healthz)"
}

identify_local_improvement() {
    local state="$1"
    local cpu_usage=$(echo "$state" | grep cpu_usage | cut -d: -f2)
    local memory_usage=$(echo "$state" | grep memory_usage | cut -d: -f2)
    local error_rate=$(echo "$state" | grep error_rate | cut -d: -f2)
    
    # Local optimization algorithm
    if [[ $cpu_usage -gt 80 ]]; then
        echo "PROPOSAL:scale_up:cpu:benefit:0.8:priority:high"
    elif [[ $memory_usage -gt 85 ]]; then
        echo "PROPOSAL:scale_up:memory:benefit:0.9:priority:high"
    elif [[ $error_rate -gt 5 ]]; then
        echo "PROPOSAL:restart_pod:benefit:0.7:priority:medium"
    fi
}

propose_to_consensus() {
    local proposal="$1"
    local timestamp=$(date +%s)
    local proposal_file="/consensus/proposals/infra-${timestamp}.json"
    
    mkdir -p /consensus/proposals
    echo "$proposal" > "$proposal_file"
    
    # Notify consensus coordinator
    curl -X POST -H "Content-Type: application/json" \
         -d "{\"proposal\": \"$proposal\", \"timestamp\": $timestamp, \"agent\": \"infrastructure-manager\"}" \
         http://consensus-controller:8080/proposals
}
```

#### Meso-Loop (5 minutes): Agent Coordination
```bash
#!/bin/bash
# Consensus coordination with 5-minute feedback loop
run_consensus_coordination() {
    while true; do
        # 1. Collect pending proposals
        proposals=$(find /consensus/proposals -name "*.json" -mmin -5 -type f)
        
        for proposal in $proposals; do
            # 2. Broadcast proposal to all agents
            responses=$(broadcast_proposal "$proposal")
            
            # 3. Collect votes within timeout
            votes=$(collect_votes "$responses" 30)
            
            # 4. Apply consensus rules
            if reaches_quorum "$votes"; then
                execute_consensus "$proposal" "$votes"
                echo "$(date): Consensus reached on $(basename "$proposal")"
            else
                reject_proposal "$proposal" "$votes"
                echo "$(date): Consensus failed on $(basename "$proposal")"
            fi
        done
        
        # 5. Sleep for meso-loop timing
        sleep 300  # 5 minutes
    done
}

broadcast_proposal() {
    local proposal_file="$1"
    local proposal_content=$(cat "$proposal_file")
    local responses=""
    
    # Send to all agents in the swarm
    for agent in cost-optimizer security-validator performance-monitor; do
        response=$(curl -s -X POST -H "Content-Type: application/json" \
                   -d "$proposal_content" \
                   "http://${agent}:8080/vote")
        responses="$responses $response"
    done
    
    echo "$responses"
}

collect_votes() {
    local responses="$1"
    local timeout="$2"
    local votes=""
    local start_time=$(date +%s)
    
    # Wait for votes or timeout
    while [[ $(($(date +%s) - start_time) -lt timeout ]]; do
        for response in $responses; do
            if [[ -n "$response" ]]; then
                votes="$votes $response"
            fi
        done
        sleep 1
    done
    
    echo "$votes"
}

reaches_quorum() {
    local votes="$1"
    local total_weight=0
    local approve_weight=0
    
    # Calculate weighted votes
    for vote in $votes; do
        local agent_weight=$(get_agent_weight "$vote")
        local decision=$(echo "$vote" | jq -r '.decision')
        
        total_weight=$((total_weight + agent_weight))
        if [[ "$decision" == "APPROVE" ]]; then
            approve_weight=$((approve_weight + agent_weight))
        fi
    done
    
    # Apply consensus thresholds
    local proposal_type=$(echo "$votes" | jq -r '.[0].type')
    case "$proposal_type" in
        "security")
            [[ $((approve_weight * 100 / total_weight)) -ge 80 ]]
            ;;
        "operational")
            [[ $((approve_weight * 100 / total_weight)) -ge 50 ]]
            ;;
        "critical")
            [[ $((approve_weight * 100 / total_weight)) -eq 100 ]]
            ;;
    esac
}
```

#### Macro-Loop (1 hour): Global Optimization
```bash
#!/bin/bash
# Global optimization with 1-hour feedback loop
run_global_optimization() {
    while true; do
        # 1. Aggregate local optimizations into global strategy
        local_decisions=$(collect_agent_decisions)
        global_strategy=$(synthesize_strategy "$local_decisions")
        
        # 2. Update agent coordination policies
        update_consensus_rules "$global_strategy"
        
        # 3. Generate optimization report
        generate_optimization_report "$global_strategy"
        
        # 4. Sleep for macro-loop timing
        sleep 3600  # 1 hour
    done
}

collect_agent_decisions() {
    # Collect decisions from all agents
    local decisions=""
    for agent in cost-optimizer security-validator performance-monitor; do
        local agent_decisions=$(curl -s "http://${agent}:8080/decisions")
        decisions="$decisions $agent_decisions"
    done
    echo "$decisions"
}

synthesize_strategy() {
    local decisions="$1"
    # Synthesize global strategy from local decisions
    echo "$decisions" | jq -s '
        group_by(.agent) |
        map({
            agent: .[0].agent,
            optimizations: length,
            success_rate: map(select(.decision == "APPROVED")) | length / length,
            avg_benefit: map(.benefit) | add / length
        }) |
        {
            strategy: "emergent_optimization",
            swarm_size: length,
            total_optimizations: map(.optimizations) | add,
            overall_success_rate: map(.success_rate) | add / length,
            recommended_actions: map(select(.success_rate > 0.8)) | .agent
        }
    '
}

update_consensus_rules() {
    local strategy="$1"
    # Update consensus coordination policies
    local new_weights=$(echo "$strategy" | jq -r '.recommended_weights')
    
    curl -X PUT -H "Content-Type: application/json" \
         -d "$new_weights" \
         http://consensus-controller:8080/config/weights
}
```

### 2. Consensus-Based Deployment

#### Deploy with Consensus Validation
```bash
#!/bin/bash
deploy_with_consensus() {
    local app_name="$1"
    local version="$2"
    local namespace="$3"
    
    echo "$(date): Starting consensus-based deployment of $app_name v$version to $namespace"
    
    # Step 1: Local validation
    kubeconform infrastructure/**/*.yaml
    kube-score score infrastructure/**/*.yaml
    
    # Step 2: Create deployment proposal
    local proposal="{
        \"type\": \"deployment\",
        \"app\": \"$app_name\",
        \"version\": \"$version\",
        \"namespace\": \"$namespace\",
        \"benefit\": \"0.8\",
        \"priority\": \"high\",
        \"timestamp\": $(date +%s),
        \"agent\": \"infrastructure-manager\"
    }"
    
    # Step 3: Propose to consensus
    local proposal_id=$(echo "$proposal" | curl -X POST -H "Content-Type: application/json" \
                            -d @- \
                            http://consensus-controller:8080/proposals | jq -r '.id')
    
    echo "$(date): Proposed deployment $proposal_id to consensus"
    
    # Step 4: Wait for consensus (30s timeout)
    local consensus_result=""
    local timeout=30
    while [[ $timeout -gt 0 && -z "$consensus_result" ]]; do
        consensus_result=$(curl -s "http://consensus-controller:8080/proposals/$proposal_id/result")
        sleep 1
        timeout=$((timeout - 1))
    done
    
    # Step 5: Execute deployment if approved
    if [[ "$consensus_result" == "APPROVED" ]]; then
        echo "$(date): Consensus approved, executing deployment"
        flux reconcile kustomization "$app_name" --with-source
        kubectl get pods -l app="$app_name" -w
    else
        echo "$(date): Consensus rejected deployment: $consensus_result"
        return 1
    fi
}
```

### 3. Distributed Drift Detection and Remediation

#### Agent-Based Drift Analysis
```bash
#!/bin/bash
detect_and_fix_drift() {
    echo "$(date): Starting distributed drift detection"
    
    while true; do
        # Step 1: Local drift detection (30s loop)
        local current_state_file="/tmp/current-state-$(date +%s).yaml"
        kubectl get all -A -o yaml > "$current_state_file"
        
        # Step 2: Get desired state from Git
        local desired_state_file="/tmp/desired-state-$(date +%s).yaml"
        git checkout main -- infrastructure/
        kustomize build infrastructure/ > "$desired_state_file"
        
        # Step 3: Compare states
        local drift_diff=$(diff "$current_state_file" "$desired_state_file")
        
        # Step 4: If drift detected, propose to consensus
        if [[ -n "$drift_diff" ]]; then
            local severity=$(calculate_drift_severity "$drift_diff")
            local drift_proposal="{
                \"type\": \"drift_remediation\",
                \"severity\": \"$severity\",
                \"drift_detected\": $(date +%s),
                \"current_state\": \"$current_state_file\",
                \"desired_state\": \"$desired_state_file\",
                \"benefit\": \"$severity\",
                \"priority\": \"high\",
                \"timestamp\": $(date +%s),
                \"agent\": \"infrastructure-manager\"
            }"
            
            echo "$(date): Drift detected (severity: $severity), proposing remediation"
            echo "$drift_proposal" | curl -X POST -H "Content-Type: application/json" \
                                         -d @- \
                                         http://consensus-controller:8080/proposals
        fi
        
        # Step 5: Sleep for tight feedback
        sleep 30
    done
}

calculate_drift_severity() {
    local drift_diff="$1"
    
    # Analyze drift severity
    if echo "$drift_diff" | grep -q "deleted"; then
        echo "critical"
    elif echo "$drift_diff" | grep -q "modified.*replicas\|modified.*image"; then
        echo "high"
    elif echo "$drift_diff" | grep -q "modified.*labels\|modified.*annotations"; then
        echo "medium"
    else
        echo "low"
    fi
}
```

### 4. Error Handling and Troubleshooting

#### Common Issues and Solutions
```bash
#!/bin/bash
troubleshoot_consensus() {
    echo "$(date): Starting consensus troubleshooting"
    
    # Check 1: Consensus controller health
    if ! curl -f http://consensus-controller:8080/healthz; then
        echo "ERROR: Consensus controller is unhealthy"
        kubectl logs -l app=consensus-controller --tail=50
        return 1
    fi
    
    # Check 2: Agent connectivity
    local agents_down=""
    for agent in cost-optimizer security-validator performance-monitor; do
        if ! curl -f "http://${agent}:8080/healthz"; then
            agents_down="$agents_down $agent"
        fi
    done
    
    if [[ -n "$agents_down" ]]; then
        echo "ERROR: Agents down: $agents_down"
        kubectl get pods -l app=swarm-agent -A
        return 1
    fi
    
    # Check 3: Consensus timeout issues
    local timeout_count=$(curl -s http://consensus-controller:8080/metrics | grep consensus_timeouts_total | awk '{print $2}')
    if [[ $timeout_count -gt 5 ]]; then
        echo "WARNING: High consensus timeout count: $timeout_count"
        echo "Suggestion: Check network connectivity between agents"
        echo "Suggestion: Increase consensus timeout value"
    fi
    
    # Check 4: Split brain detection
    local leader_elections=$(curl -s http://consensus-controller:8080/metrics | grep consensus_leader_elections_total | awk '{print $2}')
    if [[ $leader_elections -gt 3 ]]; then
        echo "CRITICAL: Split brain detected - multiple leader elections"
        echo "Action: Check network partition"
        echo "Action: Verify agent configuration"
        return 1
    fi
    
    echo "$(date): Consensus system healthy"
    return 0
}
```

## Integration Examples

### Quick Start Commands
```bash
# Deploy consensus-based infrastructure management
kubectl apply -f examples/complete-hub-spoke-consensus/

# Monitor consensus operations
kubectl logs -l app=consensus-controller -f

# Check swarm status
kubectl get agentswarms -A
kubectl describe agentswarm infrastructure-optimizers

# View consensus proposals
kubectl get consensusproposals -A

# Monitor metrics
kubectl port-forward svc/consensus-controller 8080:8080 &
curl http://localhost:8080/metrics
```

## Best Practices

### 1. Always Use Consensus for Critical Changes
- Security changes require 80% consensus
- Operational changes require 50% consensus
- Critical changes require 100% consensus

### 2. Monitor Feedback Loop Performance
- Micro-loops should complete within 30 seconds
- Meso-loops should complete within 5 minutes
- Macro-loops should complete within 1 hour

### 3. Handle Consensus Failures Gracefully
- Implement retry logic with exponential backoff
- Log all consensus attempts and results
- Provide fallback mechanisms for critical operations

### 4. Optimize Agent Communication
- Use efficient serialization formats (JSON)
- Implement connection pooling for agent communication
- Monitor network latency between agents

## Performance Considerations

- **Resource Usage**: This skill requires 1-2Gi memory and 1-2 CPU cores per agent
- **Network Latency**: Consensus performance depends on inter-agent network latency
- **Storage**: Consensus state requires fast SSD storage for optimal performance
- **Scaling**: Add more agents to increase throughput and fault tolerance

## Security Considerations

- **Consensus Integrity**: Validate all proposals and votes
- **Agent Authentication**: Use mTLS for agent-to-agent communication
- **Audit Logging**: Log all consensus decisions and proposals
- **Least Privilege**: Each agent has minimal required permissions
