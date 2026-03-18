#!/bin/bash

# Automated Argo Events Setup Script
# Complete autonomous setup with monitoring, alerts, and integrations

set -euo pipefail

# Configuration
NAMESPACE="argo-events"
ARGO_EVENTS_VERSION="v1.9.0"
CLUSTER_NAME="${CLUSTER_NAME:-default}"
ENVIRONMENT="${ENVIRONMENT:-development}"
ENABLE_MONITORING="${ENABLE_MONITORING:-true}"
ENABLE_ALERTS="${ENABLE_ALERTS:-true}"
ENABLE_K8SGPT="${ENABLE_K8SGPT:-true}"
QWEN_MODEL="${QWEN_MODEL:-qwen2.5:7b}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✓ $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠ $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✗ $1"
}

# Check cluster readiness
check_cluster() {
    log "Checking cluster readiness..."
    
    if ! kubectl cluster-info &>/dev/null; then
        error "Cannot connect to cluster"
        exit 1
    fi
    
    if ! kubectl get nodes &>/dev/null; then
        error "Cannot get cluster nodes"
        exit 1
    fi
    
    # Check for required storage classes
    if ! kubectl get storageclass &>/dev/null; then
        warning "No storage classes found"
    fi
    
    success "Cluster is ready"
}

# Install Argo Events with all components
install_argo_events() {
    log "Installing Argo Events ${ARGO_EVENTS_VERSION}..."
    
    # Create namespace with labels
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | \
    kubectl apply -f - -l app.kubernetes.io/name=argo-events,app.kubernetes.io/component=events
    
    # Add network policies
    cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argo-events-netpol
  namespace: ${NAMESPACE}
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: argo-events
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
EOF
    
    # Install Argo Events
    if kubectl apply -n "${NAMESPACE}" -f "https://raw.githubusercontent.com/argoproj/argo-events/${ARGO_EVENTS_VERSION}/manifests/install.yaml"; then
        success "Argo Events installation initiated"
    else
        error "Failed to install Argo Events"
        exit 1
    fi
    
    # Wait for readiness
    log "Waiting for Argo Events to be ready..."
    kubectl wait --for condition=available --timeout=300s deployment/argo-events-controller -n "${NAMESPACE}"
    
    success "Argo Events is ready"
}

# Setup monitoring
setup_monitoring() {
    if [[ "${ENABLE_MONITORING}" != "true" ]]; then
        return
    fi
    
    log "Setting up monitoring..."
    
    # Create ServiceMonitor for Prometheus
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argo-events-controller
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: argo-events
    app.kubernetes.io/component: monitoring
spec:
  selector:
    matchLabels:
      app: argo-events-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
    
    # Create Grafana dashboard ConfigMap
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: argo-events-dashboard
  namespace: ${NAMESPACE}
  labels:
    grafana_dashboard: "1"
data:
  argo-events.json: |
    {
      "dashboard": {
        "title": "Argo Events",
        "panels": [
          {
            "title": "Event Processing Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(argo_events_events_processed_total[5m])",
                "legendFormat": "{{event_source}}/{{event_name}}"
              }
            ]
          },
          {
            "title": "Sensor Trigger Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(argo_events_sensor_triggers_total[5m])",
                "legendFormat": "{{sensor}}"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(argo_events_errors_total[5m])",
                "legendFormat": "{{component}}"
              }
            ]
          }
        ]
      }
    }
EOF
    
    success "Monitoring setup completed"
}

# Setup alerts
setup_alerts() {
    if [[ "${ENABLE_ALERTS}" != "true" ]]; then
        return
    fi
    
    log "Setting up alerts..."
    
    # Create PrometheusRule for alerts
    cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: argo-events-alerts
  namespace: ${NAMESPACE}
spec:
  groups:
  - name: argo-events.rules
    rules:
    - alert: ArgoEventsDown
      expr: up{job="argo-events-controller"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Argo Events controller is down"
        description: "Argo Events controller has been down for more than 1 minute."
    
    - alert: ArgoEventsHighErrorRate
      expr: rate(argo_events_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Argo Events high error rate"
        description: "Argo Events error rate is {{ \$value }} errors per second."
    
    - alert: ArgoEventsEventSourceNotReady
      expr: argo_events_eventsource_ready == 0
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Event source not ready"
        description: "Event source {{ \$labels.event_source }} is not ready."
EOF
    
    success "Alerts setup completed"
}

# Setup K8sGPT integration
setup_k8sgpt() {
    if [[ "${ENABLE_K8SGPT}" != "true" ]]; then
        return
    fi
    
    log "Setting up K8sGPT integration with Qwen model..."
    
    # Create K8sGPT configuration
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: k8sgpt-config
  namespace: ${NAMESPACE}
data:
  config.yaml: |
    model: ${QWEN_MODEL}
    backend: local
    temperature: 0.7
    max_tokens: 1000
    filters:
      - Pod
      - Deployment
      - Service
      - Ingress
      - StatefulSet
      - DaemonSet
      - Job
      - CronJob
      - ReplicaSet
      - PersistentVolumeClaim
      - PersistentVolume
      - ConfigMap
      - Secret
      - ServiceAccount
      - Role
      - RoleBinding
      - ClusterRole
      - ClusterRoleBinding
    exclude:
      - kube-system
      - kube-public
      - kube-node-lease
EOF
    
    # Create K8sGPT deployment
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8sgpt
  namespace: ${NAMESPACE}
  labels:
    app: k8sgpt
    app.kubernetes.io/name: k8sgpt
    app.kubernetes.io/component: ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8sgpt
  template:
    metadata:
      labels:
        app: k8sgpt
    spec:
      containers:
      - name: k8sgpt
        image: ghcr.io/k8sgpt-ai/k8sgpt:v0.3.5
        command: ["/bin/sh"]
        args:
        - -c
        - |
          echo "Starting K8sGPT with Qwen model..."
          while true; do
            k8sgpt analyze --backend=local --model=${QWEN_MODEL} --namespace=${NAMESPACE} --output=json || true
            sleep 300
          done
        env:
        - name: K8SGPT_MODEL
          value: "${QWEN_MODEL}"
        - name: K8SGPT_BACKEND
          value: "local"
        volumeMounts:
        - name: config
          mountPath: /etc/k8sgpt
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "1Gi"
      volumes:
      - name: config
        configMap:
          name: k8sgpt-config
EOF
    
    success "K8sGPT integration setup completed"
}

# Create comprehensive examples
create_examples() {
    log "Creating comprehensive examples..."
    
    # Multiple event sources
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: comprehensive-webhook
  namespace: ${NAMESPACE}
spec:
  webhook:
    api-events:
      port: "12001"
      endpoint: /api
      method: POST
    ci-events:
      port: "12002"
      endpoint: /ci
      method: POST
    monitoring-events:
      port: "12003"
      endpoint: /monitoring
      method: POST
---
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: comprehensive-calendar
  namespace: ${NAMESPACE}
spec:
  calendar:
    daily-report:
      schedule: "0 9 * * *"
    hourly-cleanup:
      schedule: "0 * * * *"
    weekly-maintenance:
      schedule: "0 2 * * 0"
EOF
    
    # Advanced sensors with multiple triggers
    cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: comprehensive-sensor
  namespace: ${NAMESPACE}
spec:
  dependencies:
    - name: api-dep
      eventSourceName: comprehensive-webhook
      eventName: api-events
    - name: ci-dep
      eventSourceName: comprehensive-webhook
      eventName: ci-events
    - name: monitoring-dep
      eventSourceName: comprehensive-webhook
      eventName: monitoring-events
    - name: daily-dep
      eventSourceName: comprehensive-calendar
      eventName: daily-report
    - name: hourly-dep
      eventSourceName: comprehensive-calendar
      eventName: hourly-cleanup
  triggers:
    - template:
        name: api-workflow-trigger
        argoWorkflow:
          group: argoproj.io
          version: v1alpha1
          resource: workflows
          operation: submit
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: api-processing-
                namespace: argo-workflows
              spec:
                entrypoint: main
                arguments:
                  parameters:
                  - name: event-data
                    value: "{{api-dep.body}}"
                templates:
                - name: main
                  container:
                    image: python:3.9-alpine
                    command: [python]
                    args: ["-c", "import json; data = json.loads('{{workflow.parameters.event-data}}'); print(f'Processing API event: {data.get(\"type\", \"unknown\")}')"]
    - template:
        name: ci-workflow-trigger
        argoWorkflow:
          group: argoproj.io
          version: v1alpha1
          resource: workflows
          operation: submit
          source:
            resource:
              apiVersion: argoproj.io/v1alpha1
              kind: Workflow
              metadata:
                generateName: ci-pipeline-
                namespace: argo-workflows
              spec:
                entrypoint: ci
                arguments:
                  parameters:
                  - name: ci-data
                    value: "{{ci-dep.body}}"
                templates:
                - name: ci
                  container:
                    image: alpine/git:latest
                    command: [sh]
                    args: ["-c", "echo 'Running CI pipeline for {{workflow.parameters.ci-data.repository}}'"]
    - template:
        name: monitoring-alert-trigger
        http:
          url: http://alertmanager:9093/api/v1/alerts
          method: POST
          headers:
            - name: Content-Type
              value: application/json
          payload:
            - name: alerts
              value: |
                [
                  {
                    "labels": {
                      "alertname": "ArgoEventsTriggered",
                      "severity": "info",
                      "event": "{{monitoring-dep.body.alertname}}"
                    },
                    "annotations": {
                      "description": "Argo Events triggered monitoring alert: {{monitoring-dep.body.alertname}}"
                    }
                  }
                ]
    - template:
        name: daily-report-trigger
        log:
          level: info
          message: "Daily report generated at {{daily-dep.time}}"
    - template:
        name: hourly-cleanup-trigger
        log:
          level: info
          message: "Hourly cleanup started at {{hourly-dep.time}}"
EOF
    
    success "Comprehensive examples created"
}

# Setup automated scaling
setup_autoscaling() {
    log "Setting up automated scaling..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: argo-events-controller-hpa
  namespace: ${NAMESPACE}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: argo-events-controller
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
    
    success "Automated scaling setup completed"
}

# Create test suite
create_test_suite() {
    log "Creating test suite..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: argo-events-tests
  namespace: ${NAMESPACE}
data:
  test-webhook.sh: |
    #!/bin/bash
    set -e
    
    echo "Testing webhook event sources..."
    
    # Test API webhook
    curl -X POST http://comprehensive-webhook-api-events:12001/api \
      -H "Content-Type: application/json" \
      -d '{"type": "user_created", "user_id": "12345", "timestamp": "'$(date -Iseconds)'"}'
    
    # Test CI webhook
    curl -X POST http://comprehensive-webhook-ci-events:12002/ci \
      -H "Content-Type: application/json" \
      -d '{"repository": "test-repo", "branch": "main", "commit": "abc123", "status": "success"}'
    
    # Test monitoring webhook
    curl -X POST http://comprehensive-webhook-monitoring-events:12003/monitoring \
      -H "Content-Type: application/json" \
      -d '{"alertname": "HighCPU", "instance": "pod-1", "severity": "warning"}'
    
    echo "Webhook tests completed"
  
  test-sensors.sh: |
    #!/bin/bash
    set -e
    
    echo "Testing sensors..."
    
    # Check sensor status
    kubectl get sensors -n ${NAMESPACE} -o wide
    
    # Check event source status
    kubectl get eventsources -n ${NAMESPACE} -o wide
    
    # Check recent events
    kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'
    
    echo "Sensor tests completed"
EOF
    
    success "Test suite created"
}

# Run verification
verify_setup() {
    log "Verifying complete setup..."
    
    # Check all components
    local components=(
        "deployment/argo-events-controller"
        "eventsources.argoproj.io"
        "sensors.argoproj.io"
    )
    
    for component in "${components[@]}"; do
        if kubectl get "${component}" -n "${NAMESPACE}" &>/dev/null; then
            success "✓ ${component} is available"
        else
            error "✗ ${component} is not available"
            return 1
        fi
    done
    
    # Check monitoring components
    if [[ "${ENABLE_MONITORING}" == "true" ]]; then
        if kubectl get servicemonitor -n "${NAMESPACE}" argo-events-controller &>/dev/null; then
            success "✓ ServiceMonitor is configured"
        else
            warning "⚠ ServiceMonitor not found"
        fi
    fi
    
    # Check alerts
    if [[ "${ENABLE_ALERTS}" == "true" ]]; then
        if kubectl get prometheusrule -n "${NAMESPACE}" argo-events-alerts &>/dev/null; then
            success "✓ PrometheusRule is configured"
        else
            warning "⚠ PrometheusRule not found"
        fi
    fi
    
    # Check K8sGPT
    if [[ "${ENABLE_K8SGPT}" == "true" ]]; then
        if kubectl get deployment -n "${NAMESPACE}" k8sgpt &>/dev/null; then
            success "✓ K8sGPT deployment is configured"
        else
            warning "⚠ K8sGPT deployment not found"
        fi
    fi
    
    success "Setup verification completed"
}

# Show dashboard URLs
show_dashboards() {
    log "Dashboard and access information:"
    echo
    echo "=== Argo Events ==="
    echo "Controller metrics: http://$(kubectl get svc argo-events-controller -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080/metrics"
    echo
    echo "=== Monitoring ==="
    echo "Prometheus: http://prometheus.{{.Release.Namespace}}.svc.cluster.local:9090"
    echo "Grafana: http://grafana.{{.Release.Namespace}}.svc.cluster.local:3000"
    echo
    echo "=== K8sGPT ==="
    if [[ "${ENABLE_K8SGPT}" == "true" ]]; then
        echo "K8sGPT logs: kubectl logs -n ${NAMESPACE} deployment/k8sgpt -f"
    fi
    echo
    echo "=== Testing ==="
    echo "Run tests: kubectl exec -n ${NAMESPACE} $(kubectl get pod -n ${NAMESPACE} -l app=test-suite -o jsonpath='{.items[0].metadata.name}') -- /scripts/test-webhook.sh"
}

# Main execution
main() {
    log "Starting automated Argo Events setup..."
    log "Environment: ${ENVIRONMENT}"
    log "Cluster: ${CLUSTER_NAME}"
    log "Namespace: ${NAMESPACE}"
    echo
    
    # Execute setup steps
    check_cluster
    install_argo_events
    setup_monitoring
    setup_alerts
    setup_k8sgpt
    create_examples
    setup_autoscaling
    create_test_suite
    verify_setup
    show_dashboards
    
    echo
    success "🎉 Argo Events automated setup completed successfully!"
    echo
    echo "Next steps:"
    echo "1. Check the status with: kubectl get all -n ${NAMESPACE}"
    echo "2. View logs: kubectl logs -n ${NAMESPACE} deployment/argo-events-controller -f"
    echo "3. Test webhooks: kubectl exec -n ${NAMESPACE} -it $(kubectl get pod -n ${NAMESPACE} -l app=test-suite -o jsonpath='{.items[0].metadata.name}') -- /scripts/test-webhook.sh"
    echo "4. Check K8sGPT analysis: kubectl logs -n ${NAMESPACE} deployment/k8sgpt"
    echo "5. Monitor metrics: http://prometheus.{{.Release.Namespace}}.svc.cluster.local:9090"
}

# Run main function
main "$@"
