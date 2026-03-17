# Argo Events Quickstart Guide

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Helm (optional)

## 1. Installation

### Option A: Direct Manifest Installation

```bash
# Install Argo Events
kubectl create namespace argo-events
kubectl apply -n argo-events -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml

# Wait for installation
kubectl wait --for condition=available --timeout=300s deployment/argo-events-controller -n argo-events
```

### Option B: GitOps Installation (This Repository)

```bash
# Apply using Kustomize
kubectl apply -k core/resources/infrastructure/tenants/3-workloads/argo-events/

# Verify installation
kubectl get pods -n argo-events
```

## 2. Verify Installation

```bash
# Check controller is running
kubectl get pods -n argo-events

# Check services
kubectl get svc -n argo-events

# Check CRDs
kubectl get crd | grep argoproj.io
```

Expected output:
```
NAME                                          CREATED AT
eventsources.argoproj.io                      2024-01-01T00:00:00Z
sensors.argoproj.io                           2024-01-01T00:00:00Z
```

## 3. Create Your First Event Source

### Webhook Event Source

Create `webhook-source.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: webhook-source
  namespace: argo-events
spec:
  webhook:
    example:
      port: "12000"
      endpoint: /example
      method: POST
```

```bash
kubectl apply -f webhook-source.yaml
```

## 4. Create a Sensor

Create `webhook-sensor.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: webhook-sensor
  namespace: argo-events
spec:
  dependencies:
    - name: test-dep
      eventSourceName: webhook-source
      eventName: example
  triggers:
    - template:
        name: log-trigger
        log:
          level: info
          message: "Received webhook event: {{test-dep.body}}"
```

```bash
kubectl apply -f webhook-sensor.yaml
```

## 5. Test the Webhook

### Port Forward the Event Source

```bash
kubectl port-forward -n argo-events svc/webhook-source-example 12000:12000
```

### Send Test Event

In another terminal:

```bash
curl -X POST http://localhost:12000/example \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Argo Events!", "timestamp": "'$(date -Iseconds)'"}'
```

### Check the Logs

```bash
# Check sensor logs
kubectl logs -n argo-events deployment/argo-events-controller -c sensor

# Check event source logs
kubectl logs -n argo-events deployment/argo-events-controller -c eventsource
```

## 6. Advanced Example: Calendar Events

### Create Calendar Event Source

```yaml
apiVersion: argoproj.io/v1alpha1
kind: EventSource
metadata:
  name: calendar-source
  namespace: argo-events
spec:
  calendar:
    every-minute:
      schedule: "* * * * *"  # Every minute
```

```bash
kubectl apply -f calendar-source.yaml
```

### Create Calendar Sensor

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: calendar-sensor
  namespace: argo-events
spec:
  dependencies:
    - name: time-dep
      eventSourceName: calendar-source
      eventName: every-minute
  triggers:
    - template:
        name: log-trigger
        log:
          level: info
          message: "Timer triggered at {{time-dep.time}}"
```

```bash
kubectl apply -f calendar-sensor.yaml
```

## 7. Integration with Argo Workflows

### Install Argo Workflows (if not already installed)

```bash
kubectl create namespace argo-workflows
kubectl apply -n argo-workflows -f https://github.com/argoproj/argo-workflows/releases/latest/download/install.yaml
```

### Create Workflow-triggering Sensor

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Sensor
metadata:
  name: workflow-sensor
  namespace: argo-events
spec:
  dependencies:
    - name: webhook-dep
      eventSourceName: webhook-source
      eventName: example
  triggers:
    - template:
        name: workflow-trigger
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
              spec:
                entrypoint: main
                arguments:
                  parameters:
                  - name: message
                    value: "{{webhook-dep.body.message}}"
                templates:
                - name: main
                  container:
                    image: alpine:latest
                    command: [echo]
                    args: ["Processing: {{workflow.parameters.message}}"]
```

```bash
kubectl apply -f workflow-sensor.yaml
```

## 8. Monitor and Debug

### Check Resource Status

```bash
# Event sources
kubectl get eventsources -n argo-events

# Sensors
kubectl get sensors -n argo-events

# Events
kubectl get events -n argo-events
```

### View Logs

```bash
# Controller logs
kubectl logs -n argo-events deployment/argo-events-controller

# Specific component logs
kubectl logs -n argo-events deployment/argo-events-controller -c eventsource
kubectl logs -n argo-events deployment/argo-events-controller -c sensor
```

### Describe Resources

```bash
kubectl describe eventsource webhook-source -n argo-events
kubectl describe sensor webhook-sensor -n argo-events
```

## 9. Clean Up

```bash
# Delete resources
kubectl delete -f webhook-source.yaml
kubectl delete -f webhook-sensor.yaml
kubectl delete -f calendar-source.yaml
kubectl delete -f calendar-sensor.yaml
kubectl delete -f workflow-sensor.yaml

# Uninstall Argo Events (if needed)
kubectl delete -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml
kubectl delete namespace argo-events
```

## Next Steps

1. **Explore Event Sources**: Try Kafka, GitHub, S3, and other event sources
2. **Build Complex Workflows**: Create multi-step workflows triggered by events
3. **Add Filters**: Filter events based on content
4. **Set Up Monitoring**: Configure Prometheus and Grafana
5. **Security**: Configure authentication and network policies

## Troubleshooting

### Common Issues

1. **Port Forward Not Working**
   ```bash
   # Check if service exists
   kubectl get svc -n argo-events
   
   # Check service endpoints
   kubectl get endpoints -n argo-events
   ```

2. **Sensor Not Triggering**
   ```bash
   # Check sensor status
   kubectl get sensors -n argo-events -o wide
   
   # Check event source status
   kubectl get eventsources -n argo-events -o wide
   ```

3. **Workflow Not Starting**
   ```bash
   # Check Argo Workflows
   kubectl get workflows -n argo-workflows
   
   # Check RBAC
   kubectl auth can-i create workflows -n argo-workflows
   ```

### Debug Commands

```bash
# Get detailed resource information
kubectl get eventsources -n argo-events -o yaml
kubectl get sensors -n argo-events -o yaml

# Check events
kubectl get events -n argo-events --sort-by='.lastTimestamp'

# Port forward to UI (if Argo Workflows installed)
kubectl port-forward -n argo-workflows svc/argo-workflows-server 2746:2746
```

## Resources

- [Argo Events Documentation](https://argoproj.github.io/argo-events/)
- [Argo Events Examples](https://github.com/argoproj/argo-events/tree/master/examples)
- [Argo Project Website](https://argoproj.github.io/)
- [CNCF Argo Project](https://www.cncf.io/projects/argo/)
