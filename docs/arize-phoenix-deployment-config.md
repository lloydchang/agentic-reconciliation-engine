# Arize Phoenix Deployment Configuration

## Kubernetes Deployment

```yaml
# arize-phoenix-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arize-phoenix
  namespace: staging
  labels:
    app: arize-phoenix
    component: observability
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurplus: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: arize-phoenix
  template:
    metadata:
      labels:
        app: arize-phoenix
        component: observability
    spec:
      containers:
      - name: phoenix
        image: arizephoenix/phoenix:latest
        ports:
        - containerPort: 6006
          name: http
          protocol: TCP
        - containerPort: 4317
          name: otlp-grpc
          protocol: TCP
        - containerPort: 4318
          name: otlp-http
          protocol: TCP
        env:
        - name: PHOENIX_STORAGE_PATH
          value: "/tmp/phoenix"
        - name: PHOENIX_PORT
          value: "6006"
        - name: PHOENIX_HOST
          value: "0.0.0.0"
        volumeMounts:
        - name: phoenix-storage
          mountPath: /tmp/phoenix
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 6006
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 6006
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          successThreshold: 1
          failureThreshold: 3
      volumes:
      - name: phoenix-storage
        persistentVolumeClaim:
          claimName: phoenix-storage-pvc
```

## Persistent Volume Claim

```yaml
# arize-phoenix-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: phoenix-storage-pvc
  namespace: staging
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: standard
```

## Service Configuration

```yaml
# arize-phoenix-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: arize-phoenix
  namespace: staging
  labels:
    app: arize-phoenix
    component: observability
spec:
  selector:
    app: arize-phoenix
  ports:
  - name: http
    port: 6006
    targetPort: 6006
    protocol: TCP
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
    protocol: TCP
  - name: otlp-http
    port: 4318
    targetPort: 4318
    protocol: TCP
  type: ClusterIP
```

## Ingress Configuration

```yaml
# arize-phoenix-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: arize-phoenix
  namespace: staging
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - phoenix.staging.internal.example.com
    secretName: phoenix-tls
  rules:
  - host: phoenix.staging.internal.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: arize-phoenix
            port:
              number: 6006
```

## OpenTelemetry Collector (Optional Proxy)

```yaml
# otel-collector-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: staging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        ports:
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 4318
          name: otlp-http
        - containerPort: 8888
          name: metrics
        volumeMounts:
        - name: config
          mountPath: /etc/otelcol
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: config
        configMap:
          name: otel-collector-config
```

## OpenTelemetry Collector Config

```yaml
# otel-collector-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: staging
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024

    exporters:
      otlp:
        endpoint: "arize-phoenix:4317"
        insecure: true

    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [otlp]
        metrics:
          receivers: [otlp]
          processors: [batch]
          exporters: [otlp]
```

## Temporal Worker OpenTelemetry Configuration

```yaml
# temporal-worker-config.yaml
# Add to existing temporal worker configuration
opentelemetry:
  exporter:
    otlp:
      endpoint: "arize-phoenix.staging.svc.cluster.local:4317"
      insecure: true
  resource:
    service.name: "temporal-worker"
    service.version: "1.0.0"
    service.instance.id: "${HOSTNAME}"
  traces:
    sampler: "always_on"
    spanLimits:
      maxLength: 2048
      maxAttributeLength: 512
  metrics:
    readers:
      - pull:
          exporter:
            prometheus:
              host: localhost
              port: 9090
    views:
      - instrument_name: temporal_activity_execution_duration
        aggregation: explicit_bucket_histogram
        bucket_boundaries: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
```

## Memory Agent Tracing (Go Example)

```go
// memory-agent/main.go
package main

import (
    "context"
    "log"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
    "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() *trace.TracerProvider {
    exporter, err := otlptracegrpc.New(
        context.Background(),
        otlptracegrpc.WithEndpoint("arize-phoenix.staging.svc.cluster.local:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        log.Fatalf("Failed to create OTLP exporter: %v", err)
    }

    res, err := resource.New(
        context.Background(),
        resource.WithAttributes(
            semconv.ServiceNameKey.String("memory-agent"),
            semconv.ServiceVersionKey.String("1.0.0"),
        ),
    )
    if err != nil {
        log.Fatalf("Failed to create resource: %v", err)
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(res),
    )

    otel.SetTracerProvider(tp)
    return tp
}

func retrieveContext(ctx context.Context, query string) string {
    tracer := otel.Tracer("memory-agent")

    ctx, span := tracer.Start(ctx, "retrieve_context",
        trace.WithAttributes(
            attribute.String("query", query),
            attribute.String("agent.type", "memory"),
        ))
    defer span.End()

    // Memory retrieval logic here
    result := performMemoryQuery(query)

    span.SetAttributes(
        attribute.Int("memory.hits", len(result)),
        attribute.String("memory.type", "semantic"),
    )

    return result
}
```

## Skill Invocation Tracing

```go
// temporal-workflows/skill_workflow.go
func ExecuteSkillWorkflow(ctx workflow.Context, req SkillExecutionRequest) error {
    tracer := otel.Tracer("temporal-workflow")

    ctx, span := tracer.Start(ctx, "execute_skill",
        trace.WithAttributes(
            attribute.String("skill.name", req.SkillName),
            attribute.String("skill.risk_level", req.RiskLevel),
            attribute.Bool("skill.human_gate_required", req.HumanGateRequired),
        ))
    defer span.End()

    // Skill invocation logic
    span.AddEvent("skill_invocation_started")

    result, err := invokeSkill(ctx, req)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return err
    }

    span.AddEvent("skill_invocation_completed",
        trace.WithAttributes(
            attribute.Bool("skill.success", result.Success),
            attribute.Int("skill.tools_executed", len(result.ToolsUsed)),
            attribute.Int("skill.token_usage", result.TokenUsage),
        ))

    return nil
}
```

## Basic Health Check Script

```bash
#!/bin/bash
# phoenix-health-check.sh

PHOENIX_URL="http://phoenix.staging.internal.example.com"

echo "Checking Phoenix health..."
if curl -f -s "${PHOENIX_URL}/health" > /dev/null; then
    echo "✅ Phoenix is healthy"
else
    echo "❌ Phoenix is not responding"
    exit 1
fi

echo "Checking OTLP endpoint..."
if curl -f -s "${PHOENIX_URL}/health" > /dev/null; then
    echo "✅ OTLP endpoint accessible"
else
    echo "❌ OTLP endpoint not accessible"
    exit 1
fi

echo "Health check completed successfully"
```

## Dashboard Configuration (JSON)

```json
{
  "dashboard": {
    "title": "Agent Observability - Staging",
    "description": "Arize Phoenix monitoring for GitOps Infra Control Plane agents",
    "widgets": [
      {
        "type": "metric",
        "title": "Workflow Completion Rate",
        "query": "rate(temporal_workflow_completed_total[5m]) / rate(temporal_workflow_started_total[5m])",
        "thresholds": {
          "warning": 0.95,
          "error": 0.90
        }
      },
      {
        "type": "metric",
        "title": "Skill Trigger Success Rate",
        "query": "rate(skill_trigger_success_total[5m]) / rate(skill_trigger_attempts_total[5m])",
        "thresholds": {
          "warning": 0.90,
          "error": 0.80
        }
      },
      {
        "type": "trace_table",
        "title": "Recent Agent Executions",
        "filters": {
          "service.name": ["temporal-worker", "memory-agent"],
          "span.kind": "server"
        },
        "columns": ["timestamp", "service.name", "operation", "duration", "status"]
      }
    ]
  }
}
```
