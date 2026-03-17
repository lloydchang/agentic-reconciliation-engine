# Overlay Examples Repository

This document provides a comprehensive collection of overlay examples, patterns, and use cases to help you understand and implement overlays effectively.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Skill Overlay Examples](#skill-overlay-examples)
3. [Dashboard Overlay Examples](#dashboard-overlay-examples)
4. [Infrastructure Overlay Examples](#infrastructure-overlay-examples)
5. [Composed Overlay Examples](#composed-overlay-examples)
6. [Advanced Patterns](#advanced-patterns)
7. [Real-World Use Cases](#real-world-use-cases)
8. [Troubleshooting Examples](#troubleshooting-examples)

## Quick Start Examples

### 1. Hello World Overlay

The simplest possible overlay to get started:

```yaml
# core/deployment/overlays/core/ai/skills/hello-world/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: hello-world
  namespace: flux-system
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/hello-world.yaml
configMapGenerator:
  - name: hello-world-config
    literals:
      - MESSAGE="Hello, World!"
      - OVERLAY_ENABLED=true
```

```yaml
# core/deployment/overlays/core/ai/skills/hello-world/overlay-metadata.yaml
---
name: hello-world
version: "1.0.0"
description: "Simple hello world overlay for getting started"
category: skills
base_path: "core/ai/skills/debug"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto

maintainer:
  name: "Community"
  email: "community@example.com"

tags:
  - skills
  - example
  - hello-world

compatibility:
  min_base: "1.0.0"
  kubernetes: ">=1.20"

examples:
  - name: "Hello World"
    description: "Run hello world example"
    command: "python main.py hello-world"
    expected_output: "Hello, World!"
```

### 2. Configuration Override Overlay

Simple configuration override example:

```yaml
# core/deployment/overlays/core/ai/skills/config-override/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: config-override
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/config-override.yaml

# Override configuration
configMapGenerator:
  - name: debug-config
    behavior: merge
    literals:
      - LOG_LEVEL=debug
      - TIMEOUT=300
      - RETRY_COUNT=5
```

```yaml
# core/deployment/overlays/core/ai/skills/config-override/patches/config-override.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: debug-config
data:
  # Override existing configuration
  LOG_LEVEL: "debug"
  TIMEOUT: "300"
  RETRY_COUNT: "5"
  
  # Add new configuration
  FEATURE_X_ENABLED: "true"
  CUSTOM_SETTING: "production"
```

## Skill Overlay Examples

### 1. Enhanced Monitoring Skill

Add comprehensive monitoring to existing skills:

```yaml
# core/deployment/overlays/core/ai/skills/monitoring-enhanced/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: monitoring-enhanced
  namespace: flux-system
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/monitoring-patches.yaml
  - patches/metrics-patches.yaml

# Enhanced monitoring configuration
configMapGenerator:
  - name: enhanced-monitoring-config
    files:
      - config/metrics.yaml
      - config/alerts.yaml
      - config/dashboards.yaml
    literals:
      - MONITORING_ENABLED=true
      - METRICS_INTERVAL=30
      - ALERT_THRESHOLD=80

# Monitoring secrets
secretGenerator:
  - name: monitoring-secrets
    envs:
      - .env.monitoring

# Additional monitoring resources
resources:
  - monitoring/prometheus-rules.yaml
  - monitoring/grafana-dashboards.yaml
  - monitoring/alertmanager-config.yaml
```

```yaml
# core/deployment/overlays/core/ai/skills/monitoring-enhanced/patches/monitoring-patches.yaml
---
# Enhanced Deployment with monitoring
apiVersion: apps/v1
kind: Deployment
metadata:
  name: debug
spec:
  template:
    spec:
      containers:
      - name: debug
        # Add monitoring sidecar
        - name: monitoring-sidecar
          image: prom/prometheus:latest
          ports:
          - containerPort: 9090
          volumeMounts:
          - name: monitoring-config
            mountPath: /etc/prometheus
      volumes:
      - name: monitoring-config
        configMap:
          name: enhanced-monitoring-config
```

### 2. Security Hardening Skill

Add security features to skills:

```yaml
# core/deployment/overlays/core/ai/skills/security-hardened/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: security-hardened
resources:
  - ../../../../core/ai/skills/debug
patchesStrategicMerge:
  - patches/security-patches.yaml
  - patches/rbac-patches.yaml

# Security configuration
configMapGenerator:
  - name: security-config
    files:
      - config/security-policies.yaml
      - config/network-policies.yaml
    literals:
      - SECURITY_ENABLED=true
      - AUDIT_LOGGING=true
      - ENCRYPTION_AT_REST=true

# Security context
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: debug
    patch: |-
      - op: add
        path: /spec/template/spec/securityContext
        value:
          runAsNonRoot: true
          runAsUser: 1000
          fsGroup: 2000
      - op: add
        path: /spec/template/spec/containers/0/securityContext
        value:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
              - ALL
```

### 3. Multi-Region Skill

Deploy skill across multiple regions:

```yaml
# core/deployment/overlays/core/ai/skills/multi-region/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-region
resources:
  - ../../../../core/ai/skills/debug

# Region-specific configurations
configurations:
  - configs/us-east-1/
  - configs/us-west-2/
  - configs/eu-west-1/

# Region-specific patches
patchesStrategicMerge:
  - patches/us-east-1.yaml
  - patches/us-west-2.yaml
  - patches/eu-west-1.yaml

# Common labels for multi-region
commonLabels:
  deployment: multi-region
  managed-by: kustomize
```

```yaml
# core/deployment/overlays/core/ai/skills/multi-region/configs/us-east-1/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: us-east-1-config
configMapGenerator:
  - name: region-config
    literals:
      - REGION=us-east-1
      - AVAILABILITY_ZONE=us-east-1a
      - ENDPOINT=https://us-east-1.api.example.com
patchesStrategicMerge:
  - patches/region-specific.yaml
```

## Dashboard Overlay Examples

### 1. Dark Theme Overlay

Complete dark theme implementation:

```yaml
# core/deployment/overlays/core/ai/runtime/dashboard/themes/dark-pro/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: dark-pro-theme
  namespace: flux-system
resources:
  - ../../../../../core/ai/runtime/dashboard
patchesStrategicMerge:
  - patches/theme-patches.yaml
  - patches/component-patches.yaml

# Dark theme configuration
configMapGenerator:
  - name: dark-pro-theme-config
    files:
      - theme/dark-pro.css
      - theme/dark-pro.json
      - theme/variables.css
    literals:
      - THEME_MODE=dark
      - THEME_VARIANT=pro
      - CUSTOM_ANIMATIONS=true

# Theme assets
resources:
  - assets/images/
  - assets/icons/
```

```css
/* core/deployment/overlays/core/ai/runtime/dashboard/themes/dark-pro/theme/dark-pro.css */
:root {
  /* Professional dark color palette */
  --primary-color: #1e88e5;
  --secondary-color: #43a047;
  --accent-color: #e53935;
  --background-primary: #0d1117;
  --background-secondary: #161b22;
  --surface-color: #21262d;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --border-color: #30363d;
  
  /* Professional shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.5);
  
  /* Typography */
  --font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
}

/* Professional dark theme styles */
.dashboard-container {
  background: var(--background-primary);
  color: var(--text-primary);
  font-family: var(--font-family);
}

.card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow-md);
  padding: 1rem;
}

.button-primary {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.button-primary:hover {
  background: #1976d2;
  transform: translateY(-1px);
  box-shadow: var(--shadow-lg);
}
```

### 2. Custom Widgets Overlay

Add custom widgets to dashboard:

```yaml
# core/deployment/overlays/core/ai/runtime/dashboard/widgets/analytics/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: analytics-widgets
  namespace: flux-system
resources:
  - ../../../../../core/ai/runtime/dashboard
patchesStrategicMerge:
  - patches/widget-patches.yaml
  - patches/layout-patches.yaml

# Analytics widget configuration
configMapGenerator:
  - name: analytics-widgets-config
    files:
      - widgets/analytics-widget.js
      - widgets/analytics-widget.html
      - widgets/analytics-widget.css
      - config/analytics-config.json
    literals:
      - WIDGETS_ENABLED=true
      - ANALYTICS_PROVIDER=custom
      - REFRESH_INTERVAL=30
```

```javascript
// core/deployment/overlays/core/ai/runtime/dashboard/widgets/analytics/widgets/analytics-widget.js
class AnalyticsWidget {
  constructor(container, config) {
    this.container = container;
    this.config = config;
    this.chart = null;
    this.init();
  }

  init() {
    this.render();
    this.loadData();
    this.startAutoRefresh();
  }

  render() {
    this.container.innerHTML = `
      <div class="analytics-widget">
        <div class="widget-header">
          <h3>Analytics Dashboard</h3>
          <div class="widget-controls">
            <select id="timeRange">
              <option value="1h">Last Hour</option>
              <option value="24h" selected>Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </div>
        <div class="widget-content">
          <div class="metrics-grid">
            <div class="metric-card">
              <h4>Total Requests</h4>
              <div class="metric-value" id="totalRequests">-</div>
            </div>
            <div class="metric-card">
              <h4>Avg Response Time</h4>
              <div class="metric-value" id="avgResponseTime">-</div>
            </div>
            <div class="metric-card">
              <h4>Error Rate</h4>
              <div class="metric-value" id="errorRate">-</div>
            </div>
            <div class="metric-card">
              <h4>Success Rate</h4>
              <div class="metric-value" id="successRate">-</div>
            </div>
          </div>
          <div class="chart-container">
            <canvas id="analyticsChart"></canvas>
          </div>
        </div>
      </div>
    `;
  }

  async loadData() {
    try {
      const timeRange = document.getElementById('timeRange').value;
      const response = await fetch(`/api/analytics?range=${timeRange}`);
      const data = await response.json();
      
      this.updateMetrics(data);
      this.updateChart(data);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    }
  }

  updateMetrics(data) {
    document.getElementById('totalRequests').textContent = data.totalRequests.toLocaleString();
    document.getElementById('avgResponseTime').textContent = `${data.avgResponseTime}ms`;
    document.getElementById('errorRate').textContent = `${data.errorRate}%`;
    document.getElementById('successRate').textContent = `${data.successRate}%`;
  }

  updateChart(data) {
    const ctx = document.getElementById('analyticsChart').getContext('2d');
    
    if (this.chart) {
      this.chart.destroy();
    }
    
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.timestamps,
        datasets: [{
          label: 'Requests',
          data: data.requestCounts,
          borderColor: '#1e88e5',
          backgroundColor: 'rgba(30, 136, 229, 0.1)',
          tension: 0.4
        }, {
          label: 'Errors',
          data: data.errorCounts,
          borderColor: '#e53935',
          backgroundColor: 'rgba(229, 57, 53, 0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }

  startAutoRefresh() {
    setInterval(() => {
      this.loadData();
    }, this.config.refreshInterval * 1000);
  }
}

// Initialize widget when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('analytics-widget-container');
  if (container) {
    new AnalyticsWidget(container, {
      refreshInterval: 30
    });
  }
});
```

## Infrastructure Overlay Examples

### 1. Enhanced Monitoring Overlay

Comprehensive monitoring for infrastructure:

```yaml
# core/deployment/overlays/core/operators/monitoring/enhanced/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: enhanced-monitoring
  namespace: monitoring
resources:
  - ../../../../../core/operators/monitoring
  - prometheus/
  - grafana/
  - alertmanager/
  - jaeger/

# Enhanced monitoring configuration
configMapGenerator:
  - name: enhanced-monitoring-config
    files:
      - config/prometheus.yaml
      - config/grafana.yaml
      - config/alertmanager.yaml
      - config/dashboards.yaml
    literals:
      - MONITORING_ENABLED=true
      - RETENTION_PERIOD=30d
      - SCRAPE_INTERVAL=30s

# Monitoring secrets
secretGenerator:
  - name: monitoring-secrets
    envs:
      - .env.prometheus
      - .env.grafana

# Service monitors
resources:
  - servicemonitors/
  - prometheusrules/
  - dashboards/
```

```yaml
# core/deployment/overlays/core/operators/monitoring/enhanced/config/prometheus.yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

rule_files:
  - "/etc/prometheus/rules/*.yaml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
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

  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name
```

### 2. Security Policies Overlay

Comprehensive security policies:

```yaml
# core/deployment/overlays/core/operators/security/core/governance/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: security-policies
  namespace: security
resources:
  - network-core/governance/
  - pod-security-core/governance/
  - rbac/
  - security-contexts/

# Security configuration
configMapGenerator:
  - name: security-policies-config
    files:
      - config/network-policies.yaml
      - config/security-contexts.yaml
      - config/compliance-policies.yaml
    literals:
      - SECURITY_ENABLED=true
      - COMPLIANCE_MODE=strict
      - AUDIT_LOGGING=true
```

```yaml
# core/deployment/overlays/core/operators/security/core/governance/network-core/governance/default-deny.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow DNS resolution
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to: []
    ports:
    - protocol: UDP
      port: 53
---
# Allow intra-namespace communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-intra-namespace
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
  egress:
  - to:
    - podSelector: {}
```

## Composed Overlay Examples

### 1. Production Ready Suite

Complete production-ready solution:

```yaml
# core/deployment/overlays/composed/production-suite/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: production-suite
  namespace: production
resources:
  # Base components
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Enhanced skills
  - ../core/ai/skills/debug/enhanced
  - ../core/ai/skills/infrastructure-provisioning/multi-cloud-enhanced
  
  # Dashboard enhancements
  - ../core/ai/runtime/dashboard/themes/dark-pro
  - ../core/ai/runtime/dashboard/widgets/analytics
  - ../core/ai/runtime/dashboard/widgets/cost-calculator
  
  # Infrastructure enhancements
  - ../core/operators/monitoring/enhanced
  - ../core/operators/security/policies
  - ../core/operators/backup/automated

# Production configuration
configMapGenerator:
  - name: production-suite-config
    literals:
      - ENVIRONMENT=production
      - SECURITY_LEVEL=high
      - MONITORING_LEVEL=comprehensive
      - BACKUP_ENABLED=true
      - AUDIT_LOGGING=true
      - MULTI_REGION=true

# Production resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"

# Production labels
commonLabels:
  environment: production
  security-level: high
  monitoring: comprehensive
  backup: enabled
```

### 2. Development Environment

Lightweight development setup:

```yaml
# core/deployment/overlays/composed/development-env/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: development-env
  namespace: development
resources:
  # Base components (minimal)
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Development tools
  - ../core/ai/skills/debug/enhanced
  - ../core/ai/runtime/dashboard/themes/dark-pro
  
  # Lightweight monitoring
  - ../core/operators/monitoring/basic

# Development configuration
configMapGenerator:
  - name: development-env-config
    literals:
      - ENVIRONMENT=development
      - DEBUG_MODE=true
      - LOG_LEVEL=debug
      - HOT_RELOAD=true
      - RESOURCE_LIMITS=minimal

# Development resource requirements
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/resources
        value:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

# Development labels
commonLabels:
  environment: development
  debug: enabled
  hot-reload: true
```

## Advanced Patterns

### 1. Conditional Overlays

Environment-specific overlay selection:

```yaml
# core/deployment/overlays/composed/conditional/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: conditional-overlay
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents

# Conditional components based on environment
components:
  - ../../environments/${ENVIRONMENT}/

# Environment-specific patches
patchesStrategicMerge:
  - patches/${ENVIRONMENT}/

# Environment configuration
configurations:
  - configs/${ENVIRONMENT}/
```

### 2. Dynamic Configuration

Runtime configuration updates:

```yaml
# core/deployment/overlays/core/ai/skills/dynamic-config/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: dynamic-config
resources:
  - ../../../../core/ai/skills/debug

# Dynamic configuration from external source
configMapGenerator:
  - name: dynamic-config
  behavior: merge
  envs:
    - .env.dynamic
  literals:
      - CONFIG_SOURCE=external
      - REFRESH_INTERVAL=300

# Watch for configuration changes
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
      name: debug
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: CONFIG_WATCH_ENABLED
          value: "true"
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: CONFIG_REFRESH_INTERVAL
          value: "300"
```

### 3. Multi-Tenant Overlay

Multi-tenant support:

```yaml
# core/deployment/overlays/composed/multi-tenant/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: multi-tenant
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents

# Tenant-specific configurations
configurations:
  - tenants/tenant-a/
  - tenants/tenant-b/
  - tenants/tenant-c/

# Multi-tenant policies
resources:
  - core/governance/multi-tenant/
  - rbac/multi-tenant/

# Namespace isolation
patchesJson6902:
  - target:
      group: apps
      version: v1
      kind: Deployment
    patch: |-
      - op: add
        path: /spec/template/spec/containers/0/env/-
        value:
          name: TENANT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
```

## Real-World Use Cases

### 1. E-commerce Platform

Complete e-commerce infrastructure:

```yaml
# core/deployment/overlays/composed/ecommerce-platform/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: ecommerce-platform
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # E-commerce specific skills
  - ../core/ai/skills/inventory-management/enhanced
  - ../core/ai/skills/order-processing/multi-region
  - ../core/ai/skills/payment-processing/secure
  - ../core/ai/skills/customer-analytics/ml-enhanced
  
  # E-commerce dashboard
  - ../core/ai/runtime/dashboard/themes/ecommerce
  - ../core/ai/runtime/dashboard/widgets/sales-analytics
  - ../core/ai/runtime/dashboard/widgets/inventory-status
  
  # E-commerce infrastructure
  - ../core/operators/monitoring/ecommerce-focused
  - ../core/operators/security/pci-compliant
  - ../core/operators/backup/geo-redundant

# E-commerce configuration
configMapGenerator:
  - name: ecommerce-config
    literals:
      - PLATFORM_TYPE=ecommerce
      - COMPLIANCE=pci-dss
      - MULTI_REGION=true
      - HIGH_AVAILABILITY=true
```

### 2. Healthcare System

HIPAA-compliant healthcare infrastructure:

```yaml
# core/deployment/overlays/composed/healthcare-system/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: healthcare-system
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Healthcare specific skills
  - ../core/ai/skills/patient-data/secure
  - ../core/ai/skills/medical-imaging/ai-enhanced
  - ../core/ai/skills/clinical-analytics/hipaa-compliant
  
  # Healthcare dashboard
  - ../core/ai/runtime/dashboard/themes/healthcare
  - ../core/ai/runtime/dashboard/widgets/patient-status
  - ../core/ai/runtime/dashboard/widgets/clinical-alerts
  
  # Healthcare infrastructure
  - ../core/operators/monitoring/healthcare-focused
  - ../core/operators/security/hipaa-compliant
  - ../core/operators/backup/encrypted

# Healthcare configuration
configMapGenerator:
  - name: healthcare-config
    literals:
      - INDUSTRY=healthcare
      - COMPLIANCE=hipaa
      - DATA_ENCRYPTION=true
      - AUDIT_LOGGING=full
      - ACCESS_CONTROL=rbac
```

### 3. Financial Services

Financial services with compliance:

```yaml
# core/deployment/overlays/composed/financial-services/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: financial-services
resources:
  - ../../../../control-plane
  - ../../../../.agents
  - ../../../../agents
  
  # Financial services skills
  - ../core/ai/skills/trading-analytics/real-time
  - ../core/ai/skills/risk-assessment/ai-powered
  - ../core/ai/skills/fraud-detection/ml-enhanced
  - ../core/ai/skills/compliance-monitoring/automated
  
  # Financial dashboard
  - ../core/ai/runtime/dashboard/themes/financial
  - ../core/ai/runtime/dashboard/widgets/trading-dashboard
  - ../core/ai/runtime/dashboard/widgets/risk-metrics
  
  # Financial infrastructure
  - ../core/operators/monitoring/financial-focused
  - ../core/operators/security/sox-compliant
  - ../core/operators/backup/tamper-proof

# Financial services configuration
configMapGenerator:
  - name: financial-config
    literals:
      - INDUSTRY=financial
      - COMPLIANCE=sox-gdpr
      - TRANSACTION_LOGGING=true
      - ENCRYPTION_AT_REST=true
      - ENCRYPTION_IN_TRANSIT=true
```

## Troubleshooting Examples

### 1. Common Validation Issues

```bash
# Issue: Missing required files
❌ ERRORS (1):
  - Missing required file: overlay-metadata.yaml

# Solution: Create missing metadata file
cat > core/deployment/overlays/core/ai/skills/my-overlay/overlay-metadata.yaml << EOF
---
name: my-overlay
version: "1.0.0"
description: "My overlay description"
category: skills
base_path: "core/ai/skills/base-skill"
license: "AGPLv3"
risk_level: low
autonomy: fully_auto
EOF

# Issue: Invalid YAML syntax
❌ ERRORS (1):
  - Invalid YAML in kustomization.yaml: mapping values are not allowed here

# Solution: Fix YAML syntax
yamllint core/deployment/overlays/core/ai/skills/my-overlay/kustomization.yaml
```

### 2. Build Failures

```bash
# Issue: Resource path not found
Error: accumulating resources: couldn't make target for path

# Solution: Check and fix resource paths
find core/deployment/overlays/core/ai/skills/my-overlay -name "*.yaml"
# Update kustomization.yaml with correct paths

# Issue: Kustomize build timeout
Error: build timed out after 30 seconds

# Solution: Optimize overlay or increase timeout
# Check for circular dependencies
# Reduce complexity of overlays
# Use kustomize --enable-alpha-plugins for advanced features
```

### 3. Deployment Issues

```bash
# Issue: Resource conflicts
Error: the server could not find the requested resource

# Solution: Check resource names and namespaces
kubectl get all -n flux-system
kubectl describe deployment my-overlay -n flux-system

# Issue: Permission denied
Error: forbidden: User "system:serviceaccount:default" cannot create resource

# Solution: Check RBAC permissions
kubectl auth can-i create deployment --namespace=flux-system
kubectl auth can-i create configmap --namespace=flux-system
```

---

## Next Steps

These examples provide a comprehensive foundation for working with overlays. For more specific use cases and advanced patterns, refer to:

- **[User Guide](OVERLAY-USER-GUIDE.md)**: Complete user documentation
- **[Developer Guide](OVERLAY-DEVELOPER-GUIDE.md)**: Development guidelines
- **[Community Guide](OVERLAY-COMMUNITY-GUIDE.md)**: Community resources

---

*Last updated: March 2026*
