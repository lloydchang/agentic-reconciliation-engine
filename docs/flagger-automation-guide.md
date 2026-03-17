# Flagger Automation Guide

## Overview

This guide covers automated Flagger operations using the AI-powered `flagger-automation` skill. The skill provides intelligent progressive delivery automation with support for canary, A/B testing, and blue/green deployments.

## AI Skill Integration

### Skill Overview

The `flagger-automation` skill provides:
- **Automated Installation**: One-click Flagger deployment with provider configuration
- **Intelligent Configuration**: Smart canary resource generation based on application needs
- **Progressive Deployment**: Automated traffic shifting and analysis
- **Real-time Monitoring**: Continuous deployment analysis and rollback capabilities
- **GitOps Integration**: Seamless integration with Flux/ArgoCD workflows

### Skill Capabilities

| Operation | Description | Autonomy Level |
|-----------|-------------|----------------|
| `install` | Install Flagger operator with provider configuration | `fully_auto` |
| `configure` | Generate and apply canary custom resources | `conditional` |
| `deploy` | Trigger progressive deployment with traffic shifting | `conditional` |
| `analyze` | Analyze deployment progress and metrics | `fully_auto` |
| `rollback` | Automated rollback on failure detection | `conditional` |
| `status` | Get current deployment status and progress | `fully_auto` |
| `scale` | Scale deployments during progressive rollout | `conditional` |
| `test` | Load testing and validation during deployment | `fully_auto` |

## Usage Examples

### Example 1: Complete Setup and Deployment

```json
{
  "operation": "install",
  "strategy": "canary",
  "targetResource": "web-app",
  "namespace": "production",
  "provider": "istio",
  "enable_monitoring": true,
  "metrics": "prometheus",
  "thresholds": {
    "success_rate": 99,
    "duration": 500
  },
  "traffic": {
    "increment": 10,
    "pause_duration": "2m"
  }
}
```

### Example 2: A/B Testing Configuration

```json
{
  "operation": "configure",
  "strategy": "abtest",
  "targetResource": "api-service",
  "namespace": "staging",
  "provider": "nginx",
  "analysis": true,
  "traffic": {
    "split": 50,
    "test_duration": "15m"
  },
  "webhooks": [
    {
      "name": "load-test",
      "url": "http://loadtester.staging/",
      "timeout": "60s"
    }
  ]
}
```

### Example 3: Blue/Green Deployment

```json
{
  "operation": "deploy",
  "strategy": "bluegreen",
  "targetResource": "payment-service",
  "namespace": "production",
  "provider": "linkerd",
  "thresholds": {
    "success_rate": 99.5,
    "duration": 300
  },
  "progress_deadline": "15m"
}
```

## Provider Configurations

### Istio Service Mesh

```json
{
  "operation": "install",
  "provider": "istio",
  "istio_revision": "1-18",
  "enable_monitoring": true,
  "resources": {
    "requests": {
      "cpu": "100m",
      "memory": "128Mi"
    },
    "limits": {
      "cpu": "500m",
      "memory": "512Mi"
    }
  }
}
```

### Linkerd Service Mesh

```json
{
  "operation": "install",
  "provider": "linkerd",
  "linkerd_namespace": "linkerd",
  "enable_webhook": true,
  "log_level": "debug"
}
```

### NGINX Ingress Controller

```json
{
  "operation": "install",
  "provider": "nginx",
  "nginx_ingress_class": "nginx",
  "enable_monitoring": true,
  "prometheus_namespace": "monitoring"
}
```

### Contour Ingress

```json
{
  "operation": "install",
  "provider": "contour",
  "contour_namespace": "contour",
  "enable_webhook": true,
  "timeout": "15m"
}
```

## Advanced Automation

### Custom Metrics Integration

```json
{
  "operation": "configure",
  "strategy": "canary",
  "targetResource": "advanced-app",
  "custom_metrics": [
    {
      "name": "business-transaction-rate",
      "threshold": 1000,
      "interval": "1m",
      "query": "sum(rate(business_transactions_total{namespace=\"{{ namespace }}\"}[2m]))"
    },
    {
      "name": "error-budget-burn",
      "threshold": 5,
      "interval": "30s",
      "query": "sum(rate(error_budget_burn{namespace=\"{{ namespace }}\"}[30s]))"
    }
  ],
  "analysis_templates": [
    {
      "name": "custom-latency",
      "templateRef": {
        "name": "latency-percentile",
        "namespace": "flagger-system"
      }
    }
  ]
}
```

### Webhook Automation

```json
{
  "operation": "configure",
  "strategy": "canary",
  "targetResource": "webhook-app",
  "webhooks": [
    {
      "name": "load-test",
      "url": "http://loadtester.default/",
      "timeout": "30s",
      "metadata": {
        "cmd": "hey -z 2m -q 10 -c 5 http://frontend.default/",
        "expected_status": "200"
      }
    },
    {
      "name": "security-scan",
      "url": "http://security-scanner.default/",
      "timeout": "60s",
      "metadata": {
        "scan_type": "vulnerability",
        "severity_threshold": "medium"
      }
    },
    {
      "name": "slack-notify",
      "url": "http://slack-bot.default/",
      "timeout": "10s",
      "metadata": {
        "channel": "#deployments",
        "message": "Canary deployment for {{ target }} in {{ namespace }} is {{ status }}"
      }
    }
  ]
}
```

### Multi-Environment Automation

```json
{
  "operation": "deploy",
  "strategy": "canary",
  "targetResource": "multi-env-app",
  "environments": [
    {
      "namespace": "staging",
      "provider": "nginx",
      "thresholds": { "success_rate": 95, "duration": 1000 },
      "traffic": { "increment": 20, "pause_duration": "1m" }
    },
    {
      "namespace": "production",
      "provider": "istio",
      "thresholds": { "success_rate": 99.5, "duration": 300 },
      "traffic": { "increment": 5, "pause_duration": "5m" }
    }
  ]
}
```

## Monitoring and Observability

### Automated Monitoring Setup

```json
{
  "operation": "install",
  "enable_monitoring": true,
  "monitoring_config": {
    "prometheus": {
      "enabled": true,
      "namespace": "monitoring",
      "service_monitor": true
    },
    "grafana": {
      "enabled": true,
      "dashboard": true,
      "namespace": "monitoring"
    },
    "alerting": {
      "enabled": true,
      "rules": [
        {
          "name": "flagger-deployment-failure",
          "condition": "flagger_canary_failure_total > 0",
          "severity": "critical"
        },
        {
          "name": "flagger-deployment-stuck",
          "condition": "flagger_canary_duration_seconds > 1800",
          "severity": "warning"
        }
      ]
    }
  }
}
```

### Real-time Analysis

```json
{
  "operation": "analyze",
  "targetResource": "realtime-app",
  "analysis_config": {
    "real_time": true,
    "alerting": true,
    "dashboard": true,
    "metrics": [
      "request-success-rate",
      "request-duration",
      "custom-business-metric"
    ],
    "notifications": {
      "slack": "#deployments",
      "email": ["devops@company.com"],
      "webhook": "http://alertmanager.company.com"
    }
  }
}
```

## GitOps Integration

### Flux GitOps Workflow

```yaml
# flux-system/gotk-components.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- flagger-install.yaml
- flagger-configs/
- monitoring/
```

```yaml
# flagger-configs/web-app-canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: web-app
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 10s
    threshold: 99
    iterations: 10
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 1m
```

### ArgoCD Integration

```yaml
# argocd-apps/flagger-configs.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flagger-configs
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/flagger-configs
    targetRevision: HEAD
    path: .
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

## Error Handling and Recovery

### Automated Rollback

```json
{
  "operation": "deploy",
  "strategy": "canary",
  "targetResource": "critical-app",
  "rollback_config": {
    "automatic": true,
    "triggers": [
      "success_rate < 95",
      "duration > 1000ms",
      "error_rate > 5%"
    ],
    "rollback_timeout": "5m",
    "notification": {
      "slack": "#alerts",
      "email": ["devops@company.com"],
      "pagerduty": "devops-team"
    }
  }
}
```

### Failure Analysis

```json
{
  "operation": "analyze",
  "targetResource": "failed-app",
  "failure_analysis": {
    "deep_dive": true,
    "root_cause": true,
    "remediation": true,
    "report": true,
    "metrics_history": "24h",
    "events_analysis": true
  }
}
```

## Security and Compliance

### Security Scanning Integration

```json
{
  "operation": "configure",
  "strategy": "canary",
  "targetResource": "secure-app",
  "security_config": {
    "vulnerability_scanning": true,
    "policy_validation": true,
    "compliance_checks": [
      "SOC2",
      "HIPAA",
      "GDPR"
    ],
    "security_webhooks": [
      {
        "name": "security-scan",
        "url": "http://security-scanner.default/",
        "metadata": {
          "scan_level": "deep",
          "fail_threshold": "medium"
        }
      }
    ]
  }
}
```

### Audit and Compliance

```json
{
  "operation": "deploy",
  "strategy": "canary",
  "targetResource": "compliant-app",
  "audit_config": {
    "enable_audit": true,
    "audit_level": "detailed",
    "retention": "90d",
    "compliance_reports": true,
    "audit_webhooks": [
      {
        "name": "audit-log",
        "url": "http://audit-logger.default/",
        "metadata": {
          "log_level": "info",
          "include_secrets": false
        }
      }
    ]
  }
}
```

## Performance Optimization

### Resource Optimization

```json
{
  "operation": "install",
  "resource_config": {
    "flagger_resources": {
      "requests": {
        "cpu": "200m",
        "memory": "256Mi"
      },
      "limits": {
        "cpu": "1000m",
        "memory": "1Gi"
      }
    },
    "autoscaling": {
      "enabled": true,
      "min_replicas": 2,
      "max_replicas": 10,
      "target_cpu": 70,
      "target_memory": 80
    }
  }
}
```

### Performance Tuning

```json
{
  "operation": "configure",
  "strategy": "canary",
  "targetResource": "perf-app",
  "performance_config": {
    "analysis_interval": "5s",
    "concurrent_analysis": 3,
    "cache_size": "100Mi",
    "metrics_batch_size": 50,
    "timeout": "30s",
    "retry_policy": {
      "max_retries": 3,
      "backoff": "exponential"
    }
  }
}
```

## Best Practices

### Configuration Best Practices

1. **Start with conservative thresholds** and adjust based on experience
2. **Use environment-specific configurations** for different deployment stages
3. **Implement proper monitoring** before enabling canary deployments
4. **Configure automated rollback** for critical applications
5. **Use webhooks for custom validation** and testing
6. **Enable comprehensive logging** for troubleshooting

### Operational Best Practices

1. **Test configurations in staging** before production deployment
2. **Monitor Flagger performance** and resource usage
3. **Regularly review and update thresholds** based on application behavior
4. **Document rollback procedures** and incident response
5. **Use GitOps for configuration management** and version control
6. **Implement proper alerting** for deployment events

### Security Best Practices

1. **Enable security scanning** for all deployments
2. **Use role-based access control** for Flagger operations
3. **Implement network policies** for Flagger components
4. **Audit all deployment activities** and maintain logs
5. **Regular security updates** for Flagger and dependencies

## Troubleshooting

### Common Issues and Solutions

1. **Flagger installation fails**
   - Check provider compatibility
   - Verify cluster permissions
   - Review resource requirements

2. **Canary deployment stuck**
   - Check metrics availability
   - Verify service mesh configuration
   - Review canary resource configuration

3. **Rollback not working**
   - Check rollback permissions
   - Verify service mesh rules
   - Review webhook configurations

### Debug Commands

```bash
# Check Flagger status
kubectl get canaries -A
kubectl describe canary <name>

# Check Flagger logs
kubectl logs -n flagger-system deployment/flagger -f

# Verify metrics
kubectl port-forward -n flagger-system svc/flagger 8080:8080
curl http://localhost:8080/metrics
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/flagger-deploy.yml
name: Flagger Progressive Deployment
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Trigger Flagger Deployment
      run: |
        curl -X POST "http://ai-agent:8080/api/skills/flagger-automation/execute" \
          -H "Content-Type: application/json" \
          -d '{
            "operation": "deploy",
            "strategy": "canary",
            "targetResource": "web-app",
            "namespace": "production"
          }'
```

### Slack Integration

```json
{
  "operation": "configure",
  "strategy": "canary",
  "targetResource": "slack-app",
  "notifications": {
    "slack": {
      "webhook_url": "https://hooks.slack.com/services/...",
      "channel": "#deployments",
      "username": "Flagger Bot",
      "template": "Canary deployment for {{ target }} is {{ status }}: {{ message }}"
    }
  }
}
```

## Resources

- [Flagger Documentation](https://fluxcd.io/flagger/)
- [AI Skills Documentation](../core/ai/skills/flagger-automation/SKILL.md)
- [Progressive Delivery Best Practices](https://fluxcd.io/flagger/tutorials/)
- [GitOps Integration Guide](../docs/gitops-integration.md)
