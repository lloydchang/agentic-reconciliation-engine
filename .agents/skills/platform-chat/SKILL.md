---
name: platform-chat
description: |
  Intelligent conversational interface for platform operations, providing natural language interaction with infrastructure automation and AI-powered assistance.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Platform Chat — Intelligent Conversational Infrastructure Assistant

AI-powered conversational interface providing natural language interaction with infrastructure operations, automation workflows, and intelligent assistance for platform engineering teams.

## When to invoke
- Complex infrastructure questions requiring detailed explanations.
- Multi-step operations needing guided assistance.
- Troubleshooting scenarios with conversational debugging.
- Learning platform capabilities and best practices.
- Emergency response requiring rapid information gathering.
- Knowledge sharing and documentation queries.

## Capabilities
- **Natural language queries**: Understand and respond to complex infrastructure questions.
- **Conversational debugging**: Interactive troubleshooting with context awareness.
- **Workflow guidance**: Step-by-step assistance for complex operations.
- **Knowledge synthesis**: Aggregate information from multiple sources and systems.
- **Real-time assistance**: Live help during incident response and operations.
- **Learning adaptation**: Improve responses based on user interactions and feedback.

## Invocation patterns
```bash
/platform-chat query --question="Why is the API latency spiking?"
/platform-chat debug --issue="database connection timeouts" --context=production
/platform-chat guide --workflow="cluster upgrade" --step-by-step=true
/platform-chat explain --concept="service mesh" --level=intermediate
/platform-chat assist --incident=INC-2026-0315 --role=first-responder
```

## Common parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `question` | Natural language query about platform or infrastructure. | `"Why is CPU usage high?"` |
| `issue` | Problem description for debugging assistance. | `"pod crashes in production"` |
| `workflow` | Operation workflow needing guidance. | `"blue-green deployment"` |
| `concept` | Platform concept requiring explanation. | `"GitOps principles"` |
| `incident` | Incident ticket or identifier. | `INC-2026-0315` |
| `level` | Detail level for explanations. | `beginner`, `advanced` |

## Output contract
```json
{
  "operationId": "PC-2026-0315-01",
  "conversation": {
    "query": "Why is the API latency spiking?",
    "context": {
      "user": "platform-engineer",
      "environment": "production",
      "timeframe": "last-1h"
    },
    "analysis": {
      "rootCause": "Database connection pool exhaustion",
      "confidence": 0.89,
      "evidence": [
        "Connection count increased 300% in last hour",
        "Database CPU at 95% utilization",
        "Application logs show connection timeout errors"
      ]
    },
    "recommendations": [
      {
        "action": "scale-database-replicas",
        "priority": "critical",
        "impact": "Immediate latency reduction",
        "automated": true,
        "command": "kubectl scale deployment postgres --replicas=5"
      },
      {
        "action": "optimize-connection-pool",
        "priority": "high",
        "impact": "Prevent future occurrences",
        "configuration": "Increase max_connections from 100 to 200"
      }
    ],
    "nextSteps": [
      "Execute automated scaling command",
      "Monitor latency metrics for 15 minutes",
      "Review connection pool configuration"
    ]
  },
  "followUpQuestions": [
    "Would you like me to execute the scaling command?",
    "Should I create a PagerDuty incident for tracking?"
  ]
}
```

## Dispatcher integration
**Triggers:**
- `chat-query`: Natural language infrastructure questions
- `debugging-request`: Interactive troubleshooting assistance
- `incident-chat`: Conversational incident response support
- `learning-request`: Platform knowledge and training queries
- `workflow-guidance`: Step-by-step operational assistance

**Emits:**
- `analysis-complete`: Query analysis and recommendations provided
- `action-suggested`: Specific actions recommended for execution
- `incident-escalation`: Issues requiring human intervention identified
- `knowledge-updated`: Platform knowledge base updated from interactions
- `feedback-collected`: User satisfaction and response quality metrics

## AI intelligence features
- **Context awareness**: Understand user role, environment, and conversation history
- **Multi-source correlation**: Synthesize information from logs, metrics, and configs
- **Conversational memory**: Maintain context across multi-turn interactions
- **Adaptive responses**: Tailor explanations based on user expertise level
- **Predictive assistance**: Anticipate follow-up questions and provide proactive help

## Human gates
- **Production changes**: Destructive actions require explicit approval
- **Security operations**: Sensitive operations need security team validation
- **Emergency actions**: High-impact changes during incidents require review
- **Policy violations**: Actions conflicting with governance require override

## Telemetry and monitoring
- Query success rates and response accuracy
- User satisfaction scores and feedback
- Conversation length and resolution time
- Knowledge base hit rates and updates
- Integration usage patterns and effectiveness

## Testing requirements
- Conversational flow testing with various query types
- Accuracy validation against known infrastructure scenarios
- Multi-turn conversation state management testing
- Integration testing with various data sources
- Performance testing under concurrent user load

## Failure handling
- **Query misunderstanding**: Request clarification with suggested alternatives
- **Data source failures**: Degrade gracefully using cached or partial information
- **Response timeouts**: Provide partial responses with continuation options
- **Integration errors**: Fallback to manual guidance with detailed instructions
- **Context loss**: Recover conversation state with summary and restart options

## Related skills
- **incident-triage-runbook**: Conversational incident response integration
- **k8s-troubleshoot**: Interactive Kubernetes debugging assistance
- **log-classifier**: Log analysis explanation and guidance
- **observability-stack**: Metrics and monitoring query assistance

## Security considerations
- Query sanitization to prevent information disclosure
- Access control based on user roles and permissions
- Audit trails for all conversations and recommendations
- Encryption of sensitive data in responses
- Rate limiting to prevent abuse and resource exhaustion

## Performance characteristics
- Query response time: <3 seconds for standard queries
- Complex analysis: <10 seconds for multi-source correlation
- Concurrent conversations: Support for 1000+ simultaneous users
- Context retention: 30-day conversation history per user
- Knowledge synthesis: Real-time aggregation from 50+ data sources

## Scaling considerations
- Distributed conversation processing across multiple nodes
- Sharded knowledge base for fast retrieval
- Caching layer for frequently asked questions
- Queue-based processing for complex analysis requests
- Horizontal scaling based on user load and query complexity

## Success metrics
- Query resolution rate: >85% of queries answered completely
- User satisfaction: >4.2/5 average rating for responses
- Time to resolution: <5 minutes average for supported scenarios
- Knowledge accuracy: >95% factual correctness in responses
- Adoption rate: >70% of platform engineers using daily

## API endpoints
```yaml
# REST API
POST /api/v1/chat/query
POST /api/v1/chat/debug
POST /api/v1/chat/guide
POST /api/v1/chat/explain

# GraphQL
query PlatformChat($question: String!, $context: String) {
  platformChat(question: $question, context: $context) {
    response
    recommendations {
      action
      priority
    }
  }
}
```

## CLI usage
```bash
# Install
npm install -g @agentskills/platform-chat

# Query infrastructure
platform-chat query --question="Why are pods restarting?"

# Debug with context
platform-chat debug --issue="service unavailable" --context=production

# Get workflow guidance
platform-chat guide --workflow="certificate rotation"
```

## Configuration
```yaml
platformChat:
  knowledgeBase:
    sources:
      - type: elasticsearch
        index: platform-logs
      - type: prometheus
        endpoint: http://prometheus:9090
      - type: kubernetes
        apiserver: https://k8s-api.example.com
  conversation:
    maxTurns: 50
    contextWindow: 24h
    retentionPeriod: 30d
  intelligence:
    model: gpt-4-turbo
    temperature: 0.3
    maxTokens: 2000
  security:
    auditLogging: true
    querySanitization: true
    rateLimit: "100/minute"
  integrations:
    slack: enabled
    teams: enabled
    discord: disabled
```

## Examples

### Infrastructure query
```bash
/platform-chat query --question="Why is the checkout service slow?"

# Analysis: Multi-source correlation completed
# Root cause: Database query optimization needed
# Evidence: Slow query logs, increased DB CPU usage
# Recommendation: Add database indexes on user_id, order_id columns
# Impact: Expected 60% latency reduction
# Next step: Generate index creation script
```

### Interactive debugging
```bash
/platform-chat debug --issue="pod crashes" --context=production

# Debug session: Interactive troubleshooting initiated
# Initial analysis: Image pull failures detected
# Question: "Are you seeing 'ImagePullBackOff' in pod status?"
# User response: "Yes, authentication errors"
# Resolution: Registry credentials expired, rotation initiated
# Result: Pods recovering, service restored
```

### Workflow guidance
```bash
/platform-chat guide --workflow="cluster upgrade" --step-by-step=true

# Workflow: Kubernetes cluster upgrade (1.27 → 1.28)
# Step 1: Backup etcd and critical data ✅
# Step 2: Update control plane nodes (current: processing node-01)
# Step 3: Wait for control plane readiness
# Step 4: Update worker nodes in batches
# Step 5: Validate cluster health
# Progress: 35% complete, ETA 45 minutes
```

## Migration guide

### From existing chat interfaces
1. Export conversation history and knowledge base
2. Configure platform-chat with existing data sources
3. Migrate user permissions and access controls
4. Train AI model on organizational knowledge
5. Implement gradual rollout with feature flags

### From documentation systems
- **Internal wikis**: platform-chat provides conversational access
- **Knowledge bases**: Enhanced with AI-powered search and explanation
- **ChatOps tools**: Extended with infrastructure intelligence
- **Documentation sites**: Interactive exploration and guidance

## Troubleshooting

### Common issues
- **Query misunderstanding**: Use more specific terminology
- **Data source access**: Verify API permissions and network connectivity
- **Response latency**: Check system load and consider query optimization
- **Context loss**: Start new conversation or provide additional context
- **Integration failures**: Verify third-party service credentials and endpoints

### Debug mode
```bash
platform-chat --debug query --question="cluster status" --verbose
# Shows: data source queries, analysis steps, reasoning process
```

## Future roadmap
- Multi-modal interactions (voice, images, diagrams)
- Advanced AI reasoning for complex infrastructure scenarios
- Predictive problem solving and proactive recommendations
- Integration with AR/VR for immersive troubleshooting
- Quantum-accelerated analysis for massive datasets
- Cross-platform conversational continuity

---

*Last updated: March 15, 2026*
*Version: 1.0.0*
