---
name: observability-stack
description: >
  Use this skill to deploy, configure observability stack
  for teams: metrics (Prometheus/Grafana), logging (ELK/Loki),
  distributed tracing (Jaeger/Tempo), and alerting pipelines. Triggers: any
  request to set up monitoring for a new tenant or service, configure log
  aggregation, create dashboards, set up distributed tracing, build alerting
  rules, investigate a missing metric or log gap, or produce an observability
  health assessment.
tools:
  - bash
  - computer
---

# Observability Stack Skill

Deploy and operate a production-grade observability platform covering the
three pillars — metrics, logs, and traces — plus alerting and dashboards.
Automate onboarding of new tenants and services into the observability stack.

---

## Stack Components

| Pillar     | OSS option              | Cloud-native alternative        |
|------------|-------------------------|---------------------------------|
| Metrics    | Prometheus + Grafana    | Azure Monitor / CloudWatch      |
| Logs       | Loki + Grafana / ELK    | Azure Log Analytics / CloudWatch Logs |
| Traces     | Tempo + Grafana / Jaeger | Azure Application Insights      |
| Alerting   | Alertmanager + PagerDuty | Azure Monitor Alerts            |
| Dashboards | Grafana                 | Azure Workbooks                 |
| Synthetics | Blackbox Exporter       | Azure Application Insights URLs |

---

## Deployment

### Full Stack via Helm
```bash
# Prometheus + Grafana + Alertmanager
helm upgrade --install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f observability/values/prometheus-stack.yaml

# Loki + Promtail (log aggregation)
helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=50Gi \
  -f observability/values/loki.yaml

# Tempo (distributed tracing)
helm upgrade --install tempo grafana/tempo \
  --namespace monitoring \
  -f observability/values/tempo.yaml

# Grafana (single pane of glass)
helm upgrade --install grafana grafana/grafana \
  --namespace monitoring \
  -f observability/values/grafana.yaml
```

---

## Tenant Onboarding to Observability

When a new tenant is provisioned, auto-configure:

### 1. Prometheus Scrape Config
```yaml
# Added to prometheus additional scrape configs
- job_name: "tenant-${TENANT_ID}"
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names: ["${TENANT_NAMESPACE}"]
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: "true"
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
    - target_label: tenant
      replacement: "${TENANT_ID}"
```

### 2. Loki Log Routing
```yaml
# Promtail pipeline stage
pipeline_stages:
  - match:
      selector: '{namespace="${TENANT_NAMESPACE}"}'
      stages:
        - labeldrop:
            - filename
        - labels:
            tenant: "${TENANT_ID}"
            env: "${ENV}"
```

### 3. Grafana Provisioning (per-tenant dashboard)
```bash
# Provision tenant dashboard from template
sed "s/TENANT_ID_PLACEHOLDER/${TENANT_ID}/g" \
  dashboards/tenant-template.json > /tmp/tenant-dashboard.json

curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat /tmp/tenant-dashboard.json), \"overwrite\": true, \"folderId\": $TENANT_FOLDER_ID}"
```

---

## Alerting Rules

### Core Platform Alerts (Prometheus)
```yaml
groups:
  - name: platform.rules
    rules:
      # Node not ready
      - alert: NodeNotReady
        expr: kube_node_status_condition{condition="Ready",status="true"} == 0
        for: 5m
        labels: { severity: critical }
        annotations:
          summary: "Node {{ $labels.node }} is not ready"

      # Pod crash-looping
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 * 5 > 0
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash-looping"

      # High memory usage
      - alert: NodeMemoryHigh
        expr: |
          (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Node {{ $labels.instance }} memory usage > 90%"

      # API server slow
      - alert: APIServerHighLatency
        expr: |
          histogram_quantile(0.99,
            rate(apiserver_request_duration_seconds_bucket{verb!="WATCH"}[5m])
          ) > 1
        for: 10m
        labels: { severity: warning }
        annotations:
          summary: "Kubernetes API server p99 latency > 1s"

      # Certificate expiry
      - alert: CertificateExpiringSoon
        expr: |
          (certmanager_certificate_expiration_timestamp_seconds -
            certmanager_certificate_renewal_timestamp_seconds) < 7 * 24 * 3600
        for: 1h
        labels: { severity: warning }
        annotations:
          summary: "Certificate {{ $labels.name }} expires in < 7 days"
```

### Golden Signal Alerts (per service)
```yaml
      # Error rate > 1%
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5..",service="${SERVICE}"}[5m])) /
          sum(rate(http_requests_total{service="${SERVICE}"}[5m])) > 0.01
        for: 5m
        labels: { severity: critical, service: "${SERVICE}" }

      # Latency p99 > 2s
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket{service="${SERVICE}"}[5m])
          ) > 2
        for: 5m
        labels: { severity: warning, service: "${SERVICE}" }
```

---

## Log Queries (Loki)

```logql
# All errors for a tenant in last 1h
{tenant="${TENANT_ID}"} |= "ERROR" | json | line_format "{{.timestamp}} {{.message}}"

# Slow requests (> 1s) per service
{namespace="${NAMESPACE}", app="${APP}"} |
  json | duration > 1s |
  line_format "{{.method}} {{.path}} {{.duration}}"

# Failed deployments
{app="argocd-server"} |= "sync failed" | json |
  line_format "{{.app}} failed: {{.message}}"

# Security events
{namespace="kube-system"} |= "AUDIT" |
  json | verb=~"delete|patch|update" |
  line_format "{{.user}} {{.verb}} {{.resource}}/{{.name}}"
```

---

## Distributed Tracing Setup

```yaml
# OpenTelemetry Collector config (inject into each service namespace)
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
  namespace: ${TENANT_NAMESPACE}
spec:
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      batch:
      resource:
        attributes:
          - key: tenant.id
            value: "${TENANT_ID}"
            action: upsert
    exporters:
      otlp:
        endpoint: "tempo.monitoring:4317"
        tls:
          insecure: true
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch, resource]
          exporters: [otlp]
```

---

## Observability Health Check

Automated daily check:

```bash
# Metrics — Prometheus targets up?
curl -s "$PROMETHEUS_URL/api/v1/targets" | \
  jq '[.data.activeTargets[] | select(.health != "up")] |
    length' > /tmp/down_targets.txt

# Logs — Loki ingesting?
curl -s "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode 'query=sum(rate({job="promtail"}[5m]))' | \
  jq '.data.result[0].value[1]'

# Tracing — Tempo receiving spans?
curl -s "$TEMPO_URL/api/search?limit=5" | jq '.traces | length'

# Alertmanager — receivers configured?
curl -s "$ALERTMANAGER_URL/api/v2/status" | jq '.config.receivers[].name'

# Grafana — dashboards loading?
curl -s -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/health"
```

---

## Dashboard Inventory

Standard dashboards provisioned for every environment:

| Dashboard                     | Data source | Refresh  |
|-------------------------------|-------------|----------|
| Cluster Overview              | Prometheus  | 30s      |
| Tenant Resource Usage         | Prometheus  | 1m       |
| Deployment Tracker            | Prometheus  | 1m       |
| SLO / Error Budget            | Prometheus  | 1m       |
| Log Explorer (per tenant)     | Loki        | Live     |
| Distributed Traces            | Tempo       | Live     |
| Cost & Capacity               | Azure CM    | 1h       |
| Security Events               | Loki        | 5m       |

---

## Examples

- "Set up full observability for the newly provisioned tenant-53"
- "Why is the payments-api showing no metrics in Grafana?"
- "Create a Prometheus alert for when AKS memory utilisation exceeds 85%"
- "Show me all error logs for tenant-42 from the last 2 hours"
- "Set up distributed tracing for the order-service namespace"
- "Run an observability health check across all environments"

---

## Output Format

```json
{
  "stack_health": {
    "prometheus": "healthy|degraded|down",
    "loki": "healthy|degraded|down",
    "tempo": "healthy|degraded|down",
    "grafana": "healthy|degraded|down",
    "alertmanager": "healthy|degraded|down"
  },
  "tenants_instrumented": 0,
  "active_alerts": 0,
  "missing_metrics": [],
  "log_ingestion_rate_per_sec": 0,
  "traces_per_min": 0
}
```
