#!/bin/bash

# Enhanced Monitoring and Observability Setup
# This script sets up comprehensive monitoring for the GitOps Infra Control Plane

set -euxo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE="monitoring"
FLUX_NAMESPACE="flux-system"
GRAFANA_ADMIN_PASSWORD="admin123"  # Change this in production
PROMETHEUS_RETENTION="30d"
ALERTMANAGER_SMTP="smtp.example.com"

echo -e "${BLUE}📊 Enhanced Monitoring and Observability Setup${NC}"
echo "=============================================="

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites validated${NC}"

# Create monitoring namespace
echo -e "${YELLOW}📁 Creating monitoring namespace...${NC}"
kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus Operator
echo -e "${YELLOW}🚀 Installing Prometheus Operator...${NC}"

cat > prometheus-operator.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: monitoring
    app.kubernetes.io/part-of: agentic-reconciliation-engine
---
apiVersion: helm.cattle.io/v1
kind: HelmChart
metadata:
  name: prometheus-operator
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: prometheus-operator
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  repo: https://prometheus-community.github.io/helm-charts
  chart: kube-prometheus-stack
  version: "45.0.0"
  bootstrap: true
  values:
    # Prometheus configuration
    prometheus:
      enabled: true
      prometheusSpec:
        retention: $PROMETHEUS_RETENTION
        retentionSize: "50GB"
        storageSpec:
          volumeClaimTemplate:
            spec:
              storageClassName: "gp2"
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: "100Gi"
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 4000m
            memory: 8Gi
        ruleSelectorNilUsesHelmValues: false
        ruleSelector:
          matchLabels:
            app.kubernetes.io/name: prometheus-rules
        serviceMonitorSelectorNilUsesHelmValues: false
        serviceMonitorSelector:
          matchLabels:
            app.kubernetes.io/name: service-monitors
        podMonitorSelectorNilUsesHelmValues: false
        podMonitorSelector:
          matchLabels:
            app.kubernetes.io/name: pod-monitors
        additionalScrapeConfigs:
          - job_name: 'kubernetes-apiservers'
            kubernetes_sd_configs:
            - role: endpoints
            scheme: https
            tls_config:
              ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
            bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
            relabel_configs:
            - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
              action: keep
              regex: default;kubernetes;https
    
    # Grafana configuration
    grafana:
      enabled: true
      adminPassword: $GRAFANA_ADMIN_PASSWORD
      persistence:
        enabled: true
        size: "10Gi"
        storageClassName: "gp2"
      resources:
        requests:
          cpu: 500m
          memory: 1Gi
        limits:
          cpu: 1000m
          memory: 2Gi
      grafana.ini:
        server:
          domain: grafana.local
          root_url: "https://grafana.local"
        auth.anonymous:
          enabled: false
        security:
          allow_embedding: true
          content_security_policy: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' ws: wss:;"
      sidecar:
        dashboards:
          enabled: true
          searchNamespace: "ALL"
        datasources:
          enabled: true
          searchNamespace: "ALL"
    
    # Alertmanager configuration
    alertmanager:
      enabled: true
      alertmanagerSpec:
        retention: "120h"
        storage:
          volumeClaimTemplate:
            spec:
              storageClassName: "gp2"
              accessModes: ["ReadWriteOnce"]
              resources:
                requests:
                  storage: "20Gi"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
      config:
        global:
          smtp_smarthost: $ALERTMANAGER_SMTP
          smtp_from: alerts@agentic-reconciliation-engine.local
        route:
          group_by: ['alertname', 'cluster', 'service']
          group_wait: 10s
          group_interval: 10s
          repeat_interval: 1h
          receiver: 'web.hook'
          routes:
          - match:
              severity: critical
            receiver: 'critical-alerts'
          - match:
              severity: warning
            receiver: 'warning-alerts'
        receivers:
        - name: 'web.hook'
          webhook_configs:
          - url: 'http://127.0.0.1:5001/'
        - name: 'critical-alerts'
          email_configs:
          - to: 'admin@example.com'
            subject: '[CRITICAL] Agentic Reconciliation Engine Alert'
            body: |
              {{ range .Alerts }}
              Alert: {{ .Annotations.summary }}
              Description: {{ .Annotations.description }}
              Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
              {{ end }}
        - name: 'warning-alerts'
          email_configs:
          - to: 'ops@example.com'
            subject: '[WARNING] Agentic Reconciliation Engine Alert'
            body: |
              {{ range .Alerts }}
              Alert: {{ .Annotations.summary }}
              Description: {{ .Annotations.description }}
              Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
              {{ end }}
    
    # Node Exporter
    nodeExporter:
      enabled: true
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 200m
          memory: 256Mi
    
    # Kube State Metrics
    kubeStateMetrics:
      enabled: true
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          cpu: 200m
          memory: 512Mi
    
    # Blackbox Exporter
    blackboxExporter:
      enabled: true
      resources:
        requests:
          cpu: 100m
          memory: 128Mi
        limits:
          cpu: 200m
          memory: 256Mi
EOF

kubectl apply -f prometheus-operator.yaml
echo -e "${GREEN}✅ Prometheus Operator installation started${NC}"

# Wait for Prometheus Operator to be ready
echo -e "${YELLOW}⏳ Waiting for Prometheus Operator to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus-operator -n $MONITORING_NAMESPACE --timeout=300s

# Create Flux-specific monitoring
echo -e "${YELLOW}🔧 Creating Flux-specific monitoring...${NC}"

cat > flux-monitoring.yaml << EOF
# Flux ServiceMonitors
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-source-controller
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: source-controller
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: source-controller
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-kustomize-controller
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: kustomize-controller
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: kustomize-controller
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-helm-controller
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: helm-controller
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: helm-controller
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-notification-controller
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: notification-controller
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app: notification-controller
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
# Flux Status Page Monitoring
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flux-ui
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: flux-operator
    app.kubernetes.io/component: ui
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: flux-operator
      app.kubernetes.io/component: ui
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
# Cloud Controllers Monitoring
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: aws-ack-controllers
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: aws-ack
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: aws-ack
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: azure-aso-controllers
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: azure-aso
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: azure-aso
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: gcp-kcc-controllers
  namespace: $FLUX_NAMESPACE
  labels:
    app.kubernetes.io/name: gcp-kcc
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: gcp-kcc
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

kubectl apply -f flux-monitoring.yaml
echo -e "${GREEN}✅ Flux-specific monitoring configured${NC}"

# Create comprehensive alerting rules
echo -e "${YELLOW}🚨 Creating comprehensive alerting rules...${NC}"

cat > alerting-rules.yaml << EOF
# Flux Alerting Rules
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: flux-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: alerting
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  groups:
  - name: flux-system
    rules:
    # Flux Controller Alerts
    - alert: FluxControllerDown
      expr: up{job=~"flux-.*-controller"} == 0
      for: 5m
      labels:
        severity: critical
        component: flux
      annotations:
        summary: "Flux controller is down"
        description: "Flux controller {{ $labels.job }} has been down for more than 5 minutes"
    
    - alert: FluxControllerHighErrorRate
      expr: rate(flux_reconcile_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        component: flux
      annotations:
        summary: "Flux controller high error rate"
        description: "Flux controller {{ $labels.job }} error rate is {{ $value }} errors per second"
    
    - alert: FluxControllerHighLatency
      expr: histogram_quantile(0.95, rate(flux_reconcile_duration_seconds_bucket[5m])) > 2
      for: 5m
      labels:
        severity: warning
        component: flux
      annotations:
        summary: "Flux controller high latency"
        description: "Flux controller {{ $labels.job }} 95th percentile latency is {{ $value }}s"
    
    # GitRepository Alerts
    - alert: GitRepositorySyncFailure
      expr: flux_gitrepository_status_condition{status="False",type="Ready"} == 1
      for: 5m
      labels:
        severity: critical
        component: flux
      annotations:
        summary: "GitRepository sync failure"
        description: "GitRepository {{ $labels.name }} has failed to sync"
    
    - alert: GitRepositoryStale
      expr: time() - flux_gitrepository_last_handled_reconcile_at_timestamp > 3600
      for: 10m
      labels:
        severity: warning
        component: flux
      annotations:
        summary: "GitRepository is stale"
        description: "GitRepository {{ $labels.name }} has not synced in over 1 hour"
    
    # Kustomization Alerts
    - alert: KustomizationReconciliationFailure
      expr: flux_kustomization_status_condition{status="False",type="Ready"} == 1
      for: 5m
      labels:
        severity: critical
        component: flux
      annotations:
        summary: "Kustomization reconciliation failure"
        description: "Kustomization {{ $labels.name }} has failed to reconcile"
    
    - alert: KustomizationStalled
      expr: time() - flux_kustomization_last_handled_reconcile_at_timestamp > 3600
      for: 10m
      labels:
        severity: warning
        component: flux
      annotations:
        summary: "Kustomization stalled"
        description: "Kustomization {{ $labels.name }} has not reconciled in over 1 hour"
    
    # HelmRelease Alerts
    - alert: HelmReleaseReconciliationFailure
      expr: flux_helmrelease_status_condition{status="False",type="Ready"} == 1
      for: 5m
      labels:
        severity: critical
        component: flux
      annotations:
        summary: "HelmRelease reconciliation failure"
        description: "HelmRelease {{ $labels.name }} has failed to reconcile"
    
    - alert: HelmReleaseStalled
      expr: time() - flux_helmrelease_last_handled_reconcile_at_timestamp > 3600
      for: 10m
      labels:
        severity: warning
        component: flux
      annotations:
        summary: "HelmRelease stalled"
        description: "HelmRelease {{ $labels.name }} has not reconciled in over 1 hour"
    
    # Dependency Chain Alerts
    - alert: DependencyChainFailure
      expr: |
        (
          flux_kustomization_status_condition{status="False",type="Ready"} == 1
        ) and on (depends_on) (
          flux_kustomization_spec_depends_on{depends_on!=""}
        )
      for: 5m
      labels:
        severity: critical
        component: flux
      annotations:
        summary: "Dependency chain failure"
        description: "Kustomization {{ $labels.name }} depends on failed resource {{ $labels.depends_on }}"
    
    # Flux Status Page Alerts
    - alert: FluxStatusPageDown
      expr: up{job="flux-ui"} == 0
      for: 5m
      labels:
        severity: critical
        component: flux-ui
      annotations:
        summary: "Flux Status Page is down"
        description: "Flux Status Page has been down for more than 5 minutes"
    
    - alert: FluxStatusPageHighErrorRate
      expr: rate(http_requests_total{job="flux-ui",status=~"5.."}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        component: flux-ui
      annotations:
        summary: "Flux Status Page high error rate"
        description: "Flux Status Page error rate is {{ $value }} errors per second"
    
    - alert: FluxStatusPageHighLatency
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="flux-ui"}[5m])) > 1
      for: 5m
      labels:
        severity: warning
        component: flux-ui
      annotations:
        summary: "Flux Status Page high latency"
        description: "Flux Status Page 95th percentile latency is {{ $value }}s"
---
# Cloud Controller Alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cloud-controller-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: cloud-controllers
    app.kubernetes.io/component: alerting
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  groups:
  - name: cloud-controllers
    rules:
    - alert: CloudControllerDown
      expr: up{job=~"aws-ack-controllers|azure-aso-controllers|gcp-kcc-controllers"} == 0
      for: 5m
      labels:
        severity: critical
        component: cloud-controllers
      annotations:
        summary: "Cloud controller is down"
        description: "Cloud controller {{ $labels.job }} has been down for more than 5 minutes"
    
    - alert: CloudControllerHighErrorRate
      expr: rate(controller_runtime_reconcile_errors_total[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
        component: cloud-controllers
      annotations:
        summary: "Cloud controller high error rate"
        description: "Cloud controller {{ $labels.job }} error rate is {{ $value }} errors per second"
    
    - alert: CloudControllerHighLatency
      expr: histogram_quantile(0.95, rate(controller_runtime_reconcile_duration_seconds_bucket[5m])) > 30
      for: 5m
      labels:
        severity: warning
        component: cloud-controllers
      annotations:
        summary: "Cloud controller high latency"
        description: "Cloud controller {{ $labels.job }} 95th percentile latency is {{ $value }}s"
---
# Agentic Reconciliation Engine Alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: agentic-reconciliation-engine-alerts
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: agentic-reconciliation-engine
    app.kubernetes.io/component: alerting
    app.kubernetes.io/part-of: agentic-reconciliation-engine
spec:
  groups:
  - name: agentic-reconciliation-engine
    rules:
    - alert: InfrastructureResourceFailure
      expr: |
        (
          kube_resource_status{status="Failed"} == 1
        ) and on (namespace, resource)
        (
          kube_namespace_labels{label_gitops_infrastructure_control_plane_part_of="agentic-reconciliation-engine"}
        )
      for: 5m
      labels:
        severity: critical
        component: infrastructure
      annotations:
        summary: "Infrastructure resource failure"
        description: "Resource {{ $labels.resource }} in namespace {{ $labels.namespace }} has failed"
    
    - alert: InfrastructureHighResourceUsage
      expr: |
        (
          container_cpu_usage_seconds_total / on (pod) kube_pod_container_info * 100
        ) > 80
      for: 10m
      labels:
        severity: warning
        component: infrastructure
      annotations:
        summary: "Infrastructure high CPU usage"
        description: "Container {{ $labels.container }} in pod {{ $labels.pod }} is using {{ $value }}% CPU"
    
    - alert: InfrastructureHighMemoryUsage
      expr: |
        (
          container_memory_working_set_bytes / on (pod) kube_pod_container_info * 100
        ) > 80
      for: 10m
      labels:
        severity: warning
        component: infrastructure
      annotations:
        summary: "Infrastructure high memory usage"
        description: "Container {{ $labels.container }} in pod {{ $labels.pod }} is using {{ $value }}% memory"
    
    - alert: InfrastructurePodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
      for: 5m
      labels:
        severity: critical
        component: infrastructure
      annotations:
        summary: "Infrastructure pod crash looping"
        description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is crash looping"
EOF

kubectl apply -f alerting-rules.yaml
echo -e "${GREEN}✅ Comprehensive alerting rules created${NC}"

# Create Grafana dashboards
echo -e "${YELLOW}📊 Creating Grafana dashboards...${NC}"

cat > grafana-dashboards.yaml << EOF
# Flux Overview Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: flux-overview-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: flux
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  flux-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Flux Overview",
        "tags": ["flux", "gitops"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Flux Controllers Status",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "up{job=~\"flux-.*-controller\"}",
                "legendFormat": "{{job}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                },
                "mappings": [
                  {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
                  {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
                ]
              }
            }
          },
          {
            "title": "Reconciliation Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "rate(flux_reconcile_total[5m])",
                "legendFormat": "{{controller}}"
              }
            ],
            "yAxes": [{"label": "Reconciliations/sec"}]
          },
          {
            "title": "GitRepository Status",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "flux_gitrepository_status_condition{type=\"Ready\"}",
                "legendFormat": "{{name}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          },
          {
            "title": "Kustomization Status",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "flux_kustomization_status_condition{type=\"Ready\"}",
                "legendFormat": "{{name}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          },
          {
            "title": "Reconciliation Duration",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(flux_reconcile_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              },
              {
                "expr": "histogram_quantile(0.50, rate(flux_reconcile_duration_seconds_bucket[5m]))",
                "legendFormat": "50th percentile"
              }
            ],
            "yAxes": [{"label": "Duration (seconds)"}]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
            "targets": [
              {
                "expr": "rate(flux_reconcile_errors_total[5m])",
                "legendFormat": "{{controller}}"
              }
            ],
            "yAxes": [{"label": "Errors/sec"}]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
---
# Cloud Controllers Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloud-controllers-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: cloud-controllers
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  cloud-controllers.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Cloud Controllers",
        "tags": ["cloud", "controllers"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Controller Status",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "up{job=~\"aws-ack-controllers|azure-aso-controllers|gcp-kcc-controllers\"}",
                "legendFormat": "{{job}}"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "green", "value": 1}
                  ]
                }
              }
            }
          },
          {
            "title": "Reconciliation Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "rate(controller_runtime_reconcile_total[5m])",
                "legendFormat": "{{controller}}"
              }
            ],
            "yAxes": [{"label": "Reconciliations/sec"}]
          },
          {
            "title": "API Request Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "rate(controller_runtime_api_requests_total[5m])",
                "legendFormat": "{{controller}}-{{method}}"
              }
            ],
            "yAxes": [{"label": "Requests/sec"}]
          },
          {
            "title": "Reconciliation Duration",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(controller_runtime_reconcile_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              }
            ],
            "yAxes": [{"label": "Duration (seconds)"}]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
---
# Agentic Reconciliation Engine Dashboard
apiVersion: v1
kind: ConfigMap
metadata:
  name: agentic-reconciliation-engine-dashboard
  namespace: $MONITORING_NAMESPACE
  labels:
    grafana_dashboard: "1"
    app.kubernetes.io/name: agentic-reconciliation-engine
    app.kubernetes.io/component: dashboards
    app.kubernetes.io/part-of: agentic-reconciliation-engine
data:
  agentic-reconciliation-engine.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Agentic Reconciliation Engine",
        "tags": ["gitops", "infrastructure"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Cluster Overview",
            "type": "stat",
            "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "kube_node_info",
                "legendFormat": "Nodes"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [{"options": {"from": 0, "to": 10, "result": {"color": "green"}}}, "type": "range"]
              }
            }
          },
          {
            "title": "Pod Status",
            "type": "pie",
            "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
            "targets": [
              {
                "expr": "sum by (phase) (kube_pod_status_phase)",
                "legendFormat": "{{phase}}"
              }
            ]
          },
          {
            "title": "Resource Usage",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "rate(container_cpu_usage_seconds_total[5m])",
                "legendFormat": "CPU"
              },
              {
                "expr": "rate(container_memory_working_set_bytes[5m])",
                "legendFormat": "Memory"
              }
            ],
            "yAxes": [{"label": "Usage"}]
          },
          {
            "title": "GitOps Resources",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "kube_resource_status{namespace=~\"flux-system|monitoring\"}",
                "legendFormat": "{{namespace}}/{{resource}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          },
          {
            "title": "Dependency Chain Status",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "flux_kustomization_status_condition{type=\"Ready\"}",
                "legendFormat": "{{name}}"
              }
            ],
            "yAxes": [{"label": "Status"}]
          },
          {
            "title": "Alert Status",
            "type": "table",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
            "targets": [
              {
                "expr": "ALERTS{alertname=~\".*\"}",
                "legendFormat": "{{alertname}}"
              }
            ],
            "transformations": [
              {"id": "organize", "options": {"excludeByName": {"Time": true}}}
            ]
          }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
      }
    }
EOF

kubectl apply -f grafana-dashboards.yaml
echo -e "${GREEN}✅ Grafana dashboards created${NC}"

# Create Ingress for monitoring services
echo -e "${YELLOW"🌐 Creating Ingress for monitoring services...${NC}"

cat > monitoring-ingress.yaml << EOF
# Prometheus Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prometheus-ingress
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: prometheus
    app.kubernetes.io/component: ingress
    app.kubernetes.io/part-of: agentic-reconciliation-engine
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - prometheus.example.com
    secretName: prometheus-tls
  rules:
  - host: prometheus.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-operated
            port:
              number: 9090
---
# Grafana Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: grafana
    app.kubernetes.io/component: ingress
    app.kubernetes.io/part-of: agentic-reconciliation-engine
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - grafana.example.com
    secretName: grafana-tls
  rules:
  - host: grafana.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
---
# Alertmanager Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: alertmanager-ingress
  namespace: $MONITORING_NAMESPACE
  labels:
    app.kubernetes.io/name: alertmanager
    app.kubernetes.io/component: ingress
    app.kubernetes.io/part-of: agentic-reconciliation-engine
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - alertmanager.example.com
    secretName: alertmanager-tls
  rules:
  - host: alertmanager.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: alertmanager-operated
            port:
              number: 9093
EOF

kubectl apply -f monitoring-ingress.yaml
echo -e "${GREEN}✅ Monitoring Ingress created${NC}"

# Wait for monitoring stack to be ready
echo -e "${YELLOW}⏳ Waiting for monitoring stack to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n $MONITORING_NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n $MONITORING_NAMESPACE --timeout=300s

# Test monitoring setup
echo -e "${YELLOW}🧪 Testing monitoring setup...${NC}"

# Test Prometheus
kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-operated 9090:9090 &
PROM_PF_PID=$!

sleep 5

if curl -s http://localhost:9090/api/v1/query?query=up > /dev/null; then
    echo -e "${GREEN}✅ Prometheus is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Prometheus not yet ready${NC}"
fi

kill $PROM_PF_PID 2>/dev/null || true

# Test Grafana
kubectl port-forward -n $MONITORING_NAMESPACE svc/grafana 3000:3000 &
GRAFANA_PF_PID=$!

sleep 5

if curl -s http://localhost:3000/api/health > /dev/null; then
    echo -e "${GREEN}✅ Grafana is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana not yet ready${NC}"
fi

kill $GRAFANA_PF_PID 2>/dev/null || true

# Cleanup temporary files
rm -f prometheus-operator.yaml flux-monitoring.yaml alerting-rules.yaml grafana-dashboards.yaml monitoring-ingress.yaml

echo -e "${GREEN}✅ Enhanced monitoring and observability setup complete!${NC}"
echo ""
echo -e "${BLUE}🎯 Monitoring Components:${NC}"
echo "  📊 Prometheus: Metrics collection and storage"
echo "  📈 Grafana: Visualization and dashboards"
echo "  🚨 Alertmanager: Alert routing and notification"
echo "  🔍 Node Exporter: System metrics"
echo "  📊 Kube State Metrics: Kubernetes state"
echo "  🔍 Blackbox Exporter: Endpoint monitoring"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "  Prometheus: http://prometheus.example.com"
echo "  Grafana: http://grafana.example.com (admin/$GRAFANA_ADMIN_PASSWORD)"
echo "  Alertmanager: http://alertmanager.example.com"
echo ""
echo -e "${BLUE}📊 Dashboards:${NC}"
echo "  Flux Overview: GitOps status and performance"
echo "  Cloud Controllers: Multi-cloud controller metrics"
echo "  Agentic Reconciliation Engine: Cluster and resource overview"
echo ""
echo -e "${BLUE}🚨 Alerts:${NC}"
echo "  Flux controller failures and performance issues"
echo "  GitRepository and Kustomization problems"
echo "  Cloud controller errors and latency"
echo "  Infrastructure resource failures"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo "  1. Configure DNS records for monitoring domains"
echo "  2. Update Grafana admin password"
echo "  3. Configure SMTP settings for Alertmanager"
echo "  4. Set up additional custom dashboards"
echo "  5. Configure alert routing and escalation"

echo -e "${GREEN}🎉 Monitoring and observability setup complete!${NC}"
