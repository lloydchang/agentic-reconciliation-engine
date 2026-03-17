# Argo Events - Event-Driven Automation for Kubernetes

## Overview

Argo Events is a cloud-native event-driven automation framework that enables you to trigger workflows and other actions based on events from various sources. It's part of the Argo Project ecosystem and integrates seamlessly with Argo Workflows.

## Architecture

### Core Components

1. **Event Sources**: Connect to external systems and emit events
2. **Sensors**: Listen to events and trigger actions
3. **Triggers**: Define what happens when events are received (workflows, HTTP calls, etc.)

### Supported Event Sources

- **Webhook**: HTTP-based event ingestion
- **Calendar**: Time-based scheduled events
- **Kafka**: Apache Kafka message streams
- **GitHub**: GitHub webhook events
- **S3**: AWS S3 object events
- **Redis**: Redis pub/sub messages
- **NATS**: NATS messaging system
- **AMQP**: RabbitMQ and other AMQP brokers
- **GCP Pub/Sub**: Google Cloud messaging
- **Azure Event Hubs**: Azure messaging service
- **Custom**: Build your own event sources

## Installation

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Argo Workflows (optional, for workflow triggers)

### Quick Installation

```bash
# Install Argo Events in the argo-events namespace
kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml
```

### GitOps Installation (This Repository)

```bash
# Apply the Argo Events resources
kubectl apply -k core/resources/infrastructure/tenants/3-workloads/argo-events/
```

## Configuration

### Namespace and RBAC

Argo Events requires proper RBAC permissions:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argo-events-sa
  namespace: argo-events
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argo-events-role
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argo-events-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argo-events-role
subjects:
- kind: ServiceAccount
  name: argo-events-sa
  namespace: argo-events
```

## Usage Examples

### 1. Webhook Event Source

Create a simple webhook that triggers an Argo Workflow:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: webhook-event-source
  namespace: argo-events
spec:
  webhook:
    example:
      port: "12000"
      endpoint: /example
      method: POST
```

### 2. Sensor to Connect Events to Workflows

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: webhook-to-workflow-sensor
  namespace: argo-events
spec:
  dependencies:
    - name: test-dep
      eventSourceName: webhook-event-source
      eventName: example
  triggers:
    - template:
        name: argo-workflow-trigger
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
                generateName: webhook-workflow-
                namespace: argo-workflows
```

### 3. Calendar-based Events

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: calendar-event-source
  namespace: argo-events
spec:
  calendar:
    daily-report:
      schedule: "0 9 * * *"  # Daily at 9 AM
```

### 4. Kafka Integration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: kafka-event-source
  namespace: argo-events
spec:
  kafka:
    alerts:
      bootstrapServers:
        - kafka-broker-1:9092
      topics:
        - alerts
      consumerGroup: argo-events
```

## Advanced Features

### Event Filtering

Sensors can filter events based on content:

```yaml
spec:
  dependencies:
    - name: github-dep
      eventSourceName: github-event-source
      eventName: github-webhook
      filters:
        - data:
            - path: body.action
              type: string
              value: ["opened", "synchronize"]
```

### Data Transformation

Transform event data before triggering:

```yaml
triggers:
  - template:
      name: transformed-trigger
      http:
        url: http://service:8080/endpoint
        method: POST
        payload:
          - name: transformed-data
            value: "{{github-dep.body.repository.name}}-{{github-dep.body.after[:8]}}"
```

### Multiple Triggers

A single event can trigger multiple actions:

```yaml
triggers:
  - template:
      name: workflow-trigger
      argoWorkflow:
        # ... workflow configuration
  - template:
      name: slack-trigger
      slack:
        # ... Slack notification
  - template:
      name: email-trigger
      email:
        # ... Email notification
```

## Monitoring and Observability

### Metrics

Argo Events exposes Prometheus metrics:

- `/metrics` endpoint on port 8080
- Event processing metrics
- Sensor performance metrics
- Error rates and latency

### Logging

Configure log levels:

```yaml
env:
- name: LOG_LEVEL
  value: "info"  # debug, info, warn, error
```

### Health Checks

- `/healthz` - Liveness probe
- `/readyz` - Readiness probe

## Security

### Authentication

Event sources support various authentication methods:

- **Webhook**: Token-based, basic auth, OAuth
- **Kafka**: SASL/SSL, mTLS
- **GitHub**: Personal access tokens
- **AWS**: IAM roles, access keys

### Network Policies

Restrict network access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argo-events-netpol
  namespace: argo-events
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: argo-events
  policyTypes:
  - Ingress
  - Egress
```

## Best Practices

1. **Namespace Isolation**: Use dedicated namespaces for Argo Events
2. **Resource Limits**: Set appropriate CPU/memory limits
3. **Event Filtering**: Filter events at the source to reduce processing
4. **Error Handling**: Implement retry logic and dead-letter queues
5. **Security**: Use RBAC and network policies
6. **Monitoring**: Set up alerts for event processing failures

## Troubleshooting

### Common Issues

1. **Event Source Not Connecting**
   - Check credentials and network connectivity
   - Verify RBAC permissions
   - Review event source logs

2. **Sensor Not Triggering**
   - Verify dependency names match event source names
   - Check event filters
   - Review sensor logs

3. **Workflow Not Starting**
   - Ensure Argo Workflows is installed
   - Check workflow permissions
   - Verify workflow template syntax

### Debug Commands

```bash
# Check event sources
kubectl get eventsources -n argo-events

# Check sensors
kubectl get sensors -n argo-events

# View logs
kubectl logs -n argo-events deployment/argo-events-controller

# Describe resources
kubectl describe eventsource webhook-event-source -n argo-events
kubectl describe sensor webhook-to-workflow-sensor -n argo-events
```

## Integration with K8sGPT

Argo Events can integrate with K8sGPT for intelligent event processing:

```yaml
# Sensor that triggers K8sGPT analysis
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: k8sgpt-analysis-sensor
  namespace: argo-events
spec:
  dependencies:
    - name: alert-dep
      eventSourceName: prometheus-event-source
      eventName: alerts
  triggers:
    - template:
        name: k8sgpt-trigger
        http:
          url: http://k8sgpt-service:8080/analyze
          method: POST
          payload:
            - name: alert-data
              value: "{{alert-dep.body}}"
```

## Next Steps

1. Review the [Argo Events Documentation](https://argoproj.github.io/argo-events/)
2. Explore the example configurations in this repository
3. Set up monitoring and alerting
4. Integrate with your existing event sources
5. Build custom event sources if needed

## Support and Community

- [GitHub Repository](https://github.com/argoproj/argo-events)
- [Slack Community](https://argoproj.github.io/community/join-slack)
- [Documentation](https://argoproj.github.io/argo-events/)
- [CNCF Project](https://www.cncf.io/projects/argo/)
