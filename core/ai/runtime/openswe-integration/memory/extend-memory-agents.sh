#!/bin/bash

# Open SWE Memory Agent Extensions
# This script extends existing memory agents with Open SWE context and conversation history

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Extend memory agent configuration
extend_memory_config() {
    log_info "Extending memory agent configuration for Open SWE..."

    # Create Open SWE memory configuration
    cat > /tmp/openswe-memory-config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: openswe-memory-config
  namespace: ai-infrastructure
data:
  memory-types: |
    # Standard memory types
    episodic: "conversation_history"
    semantic: "entity_relationships"
    procedural: "execution_patterns"

    # Open SWE specific memory types
    github_interactions: "github_issue_pr_history"
    platform_context: "slack_linear_conversations"
    sandbox_sessions: "langsmith_execution_context"
    cross_platform_correlation: "event_correlation_ids"

  memory-retention-policies: |
    # Standard retention
    episodic: 30d
    semantic: 365d
    procedural: 180d

    # Open SWE retention
    github_interactions: 90d
    platform_context: 60d
    sandbox_sessions: 30d
    cross_platform_correlation: 7d

  langsmith-integration: |
    enabled: true
    project: "agentic-reconciliation-engine"
    trace-retention: 30d
    metrics-export: true
EOF

    log_success "Memory configuration extended"
}

# Create Open SWE memory agent deployment
create_openswe_memory_agent() {
    log_info "Creating Open SWE memory agent deployment..."

    cat > /tmp/openswe-memory-agent.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openswe-memory-agent
  namespace: ai-infrastructure
  labels:
    app: openswe-memory-agent
    component: memory
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: openswe-memory-agent
  template:
    metadata:
      labels:
        app: openswe-memory-agent
        component: memory
    spec:
      serviceAccountName: memory-agent-sa
      containers:
      - name: memory-agent
        image: gitops/agent-memory-rust:latest
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: MEMORY_TYPES
          valueFrom:
            configMapKeyRef:
              name: openswe-memory-config
              key: memory-types
        - name: LANGSMITH_API_KEY
          valueFrom:
            secretKeyRef:
              name: openswe-secrets
              key: langsmith-api-key
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: openswe-github-app-key
              key: github-app-private-key.pem
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        volumeMounts:
        - name: memory-storage
          mountPath: /data
      volumes:
      - name: memory-storage
        persistentVolumeClaim:
          claimName: openswe-memory-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: openswe-memory-pvc
  namespace: ai-infrastructure
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: fast-ssd
EOF

    log_success "Open SWE memory agent deployment created"
}

# Create memory agent service
create_memory_service() {
    log_info "Creating memory agent service..."

    cat > /tmp/openswe-memory-service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: openswe-memory-agent
  namespace: ai-infrastructure
  labels:
    app: openswe-memory-agent
    component: memory
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: http
    protocol: TCP
    name: http
  selector:
    app: openswe-memory-agent
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: openswe-memory-network-policy
  namespace: ai-infrastructure
spec:
  podSelector:
    matchLabels:
      app: openswe-memory-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: langgraph-server
    - podSelector:
        matchLabels:
          app: openswe-webhook
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: langgraph-server
    ports:
    - protocol: TCP
      port: 2024
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS for external APIs
EOF

    log_success "Memory agent service and network policy created"
}

# Extend existing memory agents
extend_existing_agents() {
    log_info "Extending existing memory agents with Open SWE capabilities..."

    # This would patch existing memory agent deployments
    # For now, we'll create a patch file
    cat > /tmp/extend-existing-memory-agents.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust  # Patch existing deployment
spec:
  template:
    spec:
      containers:
      - name: memory-agent
        env:
        - name: OPENSWE_ENABLED
          value: "true"
        - name: LANGSMITH_INTEGRATION
          value: "true"
        - name: CROSS_PLATFORM_MEMORY
          value: "true"
EOF

    log_success "Extension patch for existing memory agents created"
}

# Create memory monitoring
create_memory_monitoring() {
    log_info "Creating memory monitoring configuration..."

    cat > /tmp/openswe-memory-monitoring.yaml << 'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: openswe-memory-agent-monitor
  namespace: ai-infrastructure
  labels:
    app: openswe-memory-agent
spec:
  selector:
    matchLabels:
      app: openswe-memory-agent
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: openswe-memory-grafana-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "true"
data:
  openswe-memory-dashboard.json: |
    {
      "dashboard": {
        "title": "Open SWE Memory Agent Dashboard",
        "panels": [
          {
            "title": "Memory Usage by Type",
            "type": "bargauge",
            "targets": [
              {
                "expr": "openswe_memory_usage_bytes{type=~\"github_interactions|platform_context|sandbox_sessions\"}",
                "legendFormat": "{{type}}"
              }
            ]
          },
          {
            "title": "Cross-Platform Correlations",
            "type": "table",
            "targets": [
              {
                "expr": "openswe_correlation_events_total",
                "legendFormat": "{{platform}} -> {{action}}"
              }
            ]
          }
        ]
      }
    }
EOF

    log_success "Memory monitoring configuration created"
}

# Main execution
main() {
    echo "🧠 Open SWE Memory Agent Extensions"
    echo "==================================="

    extend_memory_config
    create_openswe_memory_agent
    create_memory_service
    extend_existing_agents
    create_memory_monitoring

    log_success "Memory agent extensions completed!"
    log_info "Apply configurations with:"
    log_info "  kubectl apply -f /tmp/openswe-memory-config.yaml"
    log_info "  kubectl apply -f /tmp/openswe-memory-agent.yaml"
    log_info "  kubectl apply -f /tmp/openswe-memory-service.yaml"
    log_info "  kubectl apply -f /tmp/extend-existing-memory-agents.yaml"
    log_info "  kubectl apply -f /tmp/openswe-memory-monitoring.yaml"
}

# Run main function
main "$@"
