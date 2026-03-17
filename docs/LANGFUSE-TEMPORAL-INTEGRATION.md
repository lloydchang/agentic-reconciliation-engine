# Langfuse Temporal Integration Guide

## Overview

This guide demonstrates how to integrate Langfuse observability into the GitOps Infra Control Plane's Temporal workflows. Langfuse provides comprehensive monitoring, debugging, and evaluation capabilities for AI agents and LLM-powered applications running on Temporal.

**Reference Documentation**: [Langfuse Temporal Integration](https://langfuse.com/integrations/frameworks/temporal)

## What This Integration Provides

- **Workflow Tracing**: Complete visibility into Temporal workflow execution
- **LLM Call Monitoring**: Track prompts, completions, token usage, and costs
- **Performance Metrics**: Latency tracking and bottleneck identification
- **Error Debugging**: Detailed failure analysis and root cause identification
- **Cost Optimization**: Monitor and optimize LLM API usage costs

## Architecture Integration

The integration fits into the existing four-layer architecture:

```
User Request → Temporal Orchestration → GitOps Control → Monitoring & Observability
                           ↑
                     Langfuse Tracing
                           ↓
                 OpenTelemetry Spans
```

## Prerequisites

### 1. Langfuse Account Setup

1. Sign up for [Langfuse Cloud](https://cloud.langfuse.com) or self-host Langfuse
2. Get your API keys from the project settings:
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
   - `LANGFUSE_BASE_URL`

### 2. Dependencies

Add to your Go modules:

```go
// go.mod
require (
    github.com/temporalio/sdk-go v1.26.0
    go.opentelemetry.io/otel v1.24.0
    go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc v1.24.0
    github.com/langfuse/langfuse-go v0.0.1
)
```

## Configuration

### Environment Variables

Add to your deployment configuration:

```yaml
# Kubernetes deployment env vars
env:
- name: LANGFUSE_PUBLIC_KEY
  valueFrom:
    secretKeyRef:
      name: langfuse-secrets
      key: public-key
- name: LANGFUSE_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: langfuse-secrets
      key: secret-key
- name: LANGFUSE_BASE_URL
  value: "https://cloud.langfuse.com"  # or your self-hosted URL
- name: OTEL_SERVICE_NAME
  value: "gitops-temporal-worker"
- name: OTEL_TRACES_EXPORTER
  value: "otlp"
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "https://cloud.langfuse.com/api/public/otel"  # Langfuse OTLP endpoint
```

### OpenTelemetry Setup

Create `internal/observability/tracing.go`:

```go
package observability

import (
    "context"
    "log"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
)

func InitTracer(ctx context.Context) (*trace.TracerProvider, error) {
    // Create OTLP exporter to Langfuse
    exporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint(os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
        otlptracegrpc.WithHeaders(map[string]string{
            "Authorization": "Bearer " + os.Getenv("LANGFUSE_SECRET_KEY"),
        }),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
    }

    // Create resource
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceNameKey.String("gitops-temporal-worker"),
            semconv.ServiceVersionKey.String("1.0.0"),
            attribute.String("service.environment", "production"),
        ),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // Create tracer provider
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(res),
        trace.WithSampler(trace.AlwaysSample()),
    )

    otel.SetTracerProvider(tp)
    return tp, nil
}

func GetTracer(name string) trace.Tracer {
    return otel.Tracer(name)
}
```

## Workflow Integration

### Enhanced Workflow Tracing

Modify your existing workflows to include Langfuse tracing. Update `core/ai/workers/temporal/internal/workflow/agent_workflows.go`:

```go
package workflow

import (
    "context"
    "time"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "go.temporal.io/sdk/workflow"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/observability"
)

// CostOptimizationWorkflow with Langfuse tracing
func CostOptimizationWorkflow(ctx workflow.Context, input CostOptimizationInput) (string, error) {
    tracer := observability.GetTracer("cost-optimization-workflow")

    // Create workflow span
    wfCtx, wfSpan := tracer.Start(ctx, "CostOptimizationWorkflow",
        trace.WithAttributes(
            attribute.String("workflow.type", "cost-optimization"),
            attribute.String("cloud.provider", input.CloudProvider),
            attribute.String("region", input.Region),
        ))
    defer wfSpan.End()

    logger := workflow.GetLogger(ctx)
    logger.Info("Starting cost optimization workflow",
        "CloudProvider", input.CloudProvider,
        "Region", input.Region)

    // Execute cost optimization activity with tracing
    activityCtx := workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
        ScheduleToCloseTimeout: time.Minute * 30,
        RetryPolicy: &temporal.RetryPolicy{
            InitialInterval:    time.Second * 5,
            BackoffCoefficient: 2.0,
            MaximumAttempts:    3,
        },
    })

    var result string
    activityErr := workflow.ExecuteActivity(activityCtx, activities.CostOptimizerActivity, input).Get(ctx, &result)
    if activityErr != nil {
        wfSpan.RecordError(activityErr)
        wfSpan.SetStatus(codes.Error, "Cost optimization failed")
        return "", activityErr
    }

    // Record successful completion
    wfSpan.SetAttributes(
        attribute.String("workflow.result", "success"),
        attribute.Int("recommendations.count", len(strings.Split(result, "\n"))),
    )

    logger.Info("Cost optimization workflow completed", "Recommendations", result)
    return result, nil
}
```

### Activity-Level Tracing

Enhance activities to include detailed tracing. Update `core/ai/workers/temporal/internal/activities/agent_activities.go`:

```go
package activities

import (
    "context"
    "fmt"
    "time"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "go.temporal.io/sdk/activity"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/observability"
)

// CostOptimizerActivity with comprehensive tracing
func CostOptimizerActivity(ctx context.Context, input CostOptimizationInput) (string, error) {
    tracer := observability.GetTracer("cost-optimizer-activity")

    // Create activity span
    actCtx, actSpan := tracer.Start(ctx, "CostOptimizerActivity",
        trace.WithAttributes(
            attribute.String("activity.type", "cost-optimization"),
            attribute.String("cloud.provider", input.CloudProvider),
            attribute.String("region", input.Region),
            attribute.StringSlice("services", input.Services),
            attribute.String("time.range", input.TimeRange),
        ))
    defer actSpan.End()

    logger := activity.GetLogger(ctx)
    startTime := time.Now()

    logger.Info("Starting cost optimization activity",
        "CloudProvider", input.CloudProvider,
        "Region", input.Region)

    // Simulate cost analysis (replace with actual LLM/memory agent call)
    recommendations, err := performCostAnalysis(actCtx, input)
    if err != nil {
        actSpan.RecordError(err)
        actSpan.SetStatus(codes.Error, "Cost analysis failed")
        return "", err
    }

    // Record metrics
    duration := time.Since(startTime)
    actSpan.SetAttributes(
        attribute.Float64("activity.duration_ms", float64(duration.Milliseconds())),
        attribute.Int("recommendations.length", len(recommendations)),
        attribute.String("activity.status", "success"),
    )

    logger.Info("Cost optimization completed",
        "Recommendations", recommendations,
        "Duration", duration)

    return recommendations, nil
}

func performCostAnalysis(ctx context.Context, input CostOptimizationInput) (string, error) {
    tracer := observability.GetTracer("cost-analysis")

    // Create sub-span for LLM/memory agent interaction
    _, llmSpan := tracer.Start(ctx, "LLM-Cost-Analysis",
        trace.WithAttributes(
            attribute.String("llm.provider", "memory-agent"),
            attribute.String("analysis.type", "cost-optimization"),
        ))
    defer llmSpan.End()

    // Simulate LLM call to memory agent
    // In reality, this would call the memory agent service
    recommendations := fmt.Sprintf("Cost optimization recommendations for %s in %s region", input.CloudProvider, input.Region)

    // Record LLM metrics (would come from actual LLM response)
    llmSpan.SetAttributes(
        attribute.Int("llm.tokens.prompt", 150),
        attribute.Int("llm.tokens.completion", 300),
        attribute.Float64("llm.cost_usd", 0.015),
        attribute.String("llm.model", "gpt-4"),
    )

    return recommendations, nil
}
```

## Memory Agent Integration

### Tracing Memory Agent Calls

For memory agent interactions, add tracing to capture LLM calls. Create `internal/memory/client.go`:

```go
package memory

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/observability"
)

type MemoryClient struct {
    baseURL string
    client  *http.Client
}

type MemoryRequest struct {
    Action string      `json:"action"`
    Input  interface{} `json:"input"`
    TraceID string     `json:"trace_id,omitempty"`
}

type MemoryResponse struct {
    Result string `json:"result"`
    TokensUsed int `json:"tokens_used,omitempty"`
    Cost float64 `json:"cost,omitempty"`
}

func (mc *MemoryClient) CallMemoryAgent(ctx context.Context, action string, input interface{}) (*MemoryResponse, error) {
    tracer := observability.GetTracer("memory-agent-client")

    // Create memory agent call span
    memCtx, memSpan := tracer.Start(ctx, "MemoryAgentCall",
        trace.WithAttributes(
            attribute.String("memory.action", action),
            attribute.String("memory.service", "agent-memory-rust"),
        ))
    defer memSpan.End()

    startTime := time.Now()

    req := MemoryRequest{
        Action: action,
        Input:  input,
    }

    jsonData, err := json.Marshal(req)
    if err != nil {
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "Failed to marshal request")
        return nil, err
    }

    httpReq, err := http.NewRequestWithContext(memCtx, "POST",
        mc.baseURL+"/api/memory/infer", bytes.NewBuffer(jsonData))
    if err != nil {
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "Failed to create request")
        return nil, err
    }
    httpReq.Header.Set("Content-Type", "application/json")

    resp, err := mc.client.Do(httpReq)
    if err != nil {
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "HTTP request failed")
        return nil, err
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "Failed to read response")
        return nil, err
    }

    if resp.StatusCode != http.StatusOK {
        err := fmt.Errorf("memory agent returned status %d: %s", resp.StatusCode, string(body))
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "Memory agent error")
        return nil, err
    }

    var memResp MemoryResponse
    if err := json.Unmarshal(body, &memResp); err != nil {
        memSpan.RecordError(err)
        memSpan.SetStatus(codes.Error, "Failed to unmarshal response")
        return nil, err
    }

    // Record successful metrics
    duration := time.Since(startTime)
    memSpan.SetAttributes(
        attribute.Float64("memory.call.duration_ms", float64(duration.Milliseconds())),
        attribute.Int("memory.tokens.used", memResp.TokensUsed),
        attribute.Float64("memory.cost_usd", memResp.Cost),
        attribute.String("memory.status", "success"),
    )

    return &memResp, nil
}
```

## Worker Initialization

Update the Temporal worker to include tracing. Modify `core/ai/workers/temporal/cmd/worker/main.go`:

```go
package main

import (
    "context"
    "log"
    "os"
    "os/signal"

    "go.temporal.io/sdk/client"
    "go.temporal.io/sdk/worker"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/observability"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/workflow"
    "github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/activities"
)

func main() {
    // Initialize OpenTelemetry tracing
    ctx := context.Background()
    tp, err := observability.InitTracer(ctx)
    if err != nil {
        log.Fatalf("Failed to initialize tracer: %v", err)
    }
    defer func() {
        if err := tp.Shutdown(ctx); err != nil {
            log.Printf("Error shutting down tracer provider: %v", err)
        }
    }()

    // Create Temporal client
    c, err := client.Dial(client.Options{
        HostPort:  os.Getenv("TEMPORAL_ADDRESS"),
        Namespace: os.Getenv("TEMPORAL_NAMESPACE"),
    })
    if err != nil {
        log.Fatalln("Unable to create client", err)
    }
    defer c.Close()

    // Create worker with tracing interceptors
    w := worker.New(c, os.Getenv("TEMPORAL_TASK_QUEUE"), worker.Options{
        Interceptors: []worker.Interceptor{
            observability.NewTracingInterceptor(),
        },
    })

    // Register workflows and activities
    workflow.RegisterAgentWorkflows(w)
    activities.RegisterAgentActivities(w)

    // Handle graceful shutdown
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, os.Interrupt)

    // Start worker
    log.Println("Starting temporal worker with Langfuse tracing...")
    err = w.Start()
    if err != nil {
        log.Fatalln("Unable to start worker", err)
    }

    <-sigChan
    log.Println("Shutting down worker...")
}
```

## Tracing Interceptor

Create a tracing interceptor for automatic span creation. Add `internal/observability/interceptor.go`:

```go
package observability

import (
    "context"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "go.temporal.io/sdk/worker"
    "go.temporal.io/sdk/workflow"
)

type TracingInterceptor struct{}

func NewTracingInterceptor() *TracingInterceptor {
    return &TracingInterceptor{}
}

func (t *TracingInterceptor) InterceptActivity(ctx context.Context, next worker.ActivityInboundInterceptor) worker.ActivityInboundInterceptor {
    return &activityTracingInterceptor{next: next}
}

func (t *TracingInterceptor) InterceptWorkflow(ctx workflow.Context, next worker.WorkflowInboundInterceptor) worker.WorkflowInboundInterceptor {
    return &workflowTracingInterceptor{next: next}
}

type activityTracingInterceptor struct {
    next worker.ActivityInboundInterceptor
}

func (a *activityTracingInterceptor) Init(outbound worker.ActivityOutboundInterceptor) error {
    return a.next.Init(outbound)
}

func (a *activityTracingInterceptor) ExecuteActivity(ctx context.Context, in *worker.ExecuteActivityInput) (interface{}, error) {
    tracer := GetTracer("temporal-activity")

    ctx, span := tracer.Start(ctx, "ExecuteActivity",
        trace.WithAttributes(
            attribute.String("temporal.activity.type", in.ActivityType),
            attribute.String("temporal.workflow.id", in.Header.Get("WorkflowID")),
        ))
    defer span.End()

    result, err := a.next.ExecuteActivity(ctx, in)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "Activity failed")
    } else {
        span.SetStatus(codes.Ok, "Activity completed")
    }

    return result, err
}

type workflowTracingInterceptor struct {
    next worker.WorkflowInboundInterceptor
}

func (w *workflowTracingInterceptor) Init(outbound worker.WorkflowOutboundInterceptor) error {
    return w.next.Init(outbound)
}

func (w *workflowTracingInterceptor) ExecuteWorkflow(ctx workflow.Context, in *worker.ExecuteWorkflowInput) (interface{}, error) {
    tracer := GetTracer("temporal-workflow")

    ctx, span := tracer.Start(ctx, "ExecuteWorkflow",
        trace.WithAttributes(
            attribute.String("temporal.workflow.type", in.WorkflowType),
            attribute.String("temporal.workflow.id", in.WorkflowID),
        ))
    defer span.End()

    result, err := w.next.ExecuteWorkflow(ctx, in)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "Workflow failed")
    } else {
        span.SetStatus(codes.Ok, "Workflow completed")
    }

    return result, err
}
```

## Backend API Integration

Update the backend API to include tracing for workflow starts. Modify `core/ai/runtime/agents/backend/main.go`:

```go
// Enhanced workflow endpoints with tracing
r.HandleFunc("/workflow/start-ai-orchestration", func(w http.ResponseWriter, r *http.Request) {
    tracer := observability.GetTracer("api-workflow-start")

    ctx, span := tracer.Start(r.Context(), "StartAIOrchestrationWorkflow",
        trace.WithAttributes(
            attribute.String("api.endpoint", "/workflow/start-ai-orchestration"),
            attribute.String("workflow.type", "ai-orchestration"),
        ))
    defer span.End()

    request := types.ComplianceRequest{
        TargetResource: "vm-web-server-001",
        ComplianceType: "full-scan",
        Parameters:     make(map[string]string),
        RequesterID:    "backstage-user",
        Priority:       "normal",
    }

    we, err := c.ExecuteWorkflow(ctx, client.StartWorkflowOptions{
        ID:        "ai-orchestration-" + time.Now().Format("20060102150405"),
        TaskQueue: "ai-agent-task-queue",
    }, workflows.AIAgentOrchestrationWorkflowV2, request)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "Failed to start workflow")
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    span.SetAttributes(
        attribute.String("workflow.id", we.GetID()),
        attribute.String("workflow.run_id", we.GetRunID()),
        attribute.String("api.response.status", "success"),
    )

    w.Header().Set("Content-Type", "text/plain")
    w.Write([]byte(we.GetID()))
}).Methods("POST", "OPTIONS")
```

## Monitoring and Debugging

### Viewing Traces in Langfuse

1. **Access Langfuse Dashboard**: Go to your Langfuse instance
2. **Navigate to Traces**: View real-time traces of workflow executions
3. **Filter by Service**: Filter traces by `gitops-temporal-worker`
4. **Analyze Performance**: Monitor latency, error rates, and costs

### Key Metrics to Monitor

- **Workflow Execution Time**: Identify bottlenecks in long-running workflows
- **Activity Success Rates**: Monitor activity failure patterns
- **LLM Token Usage**: Track costs and optimize prompts
- **Error Patterns**: Debug common failure modes

### Example Trace Structure

```
Workflow: CostOptimizationWorkflow
├── Activity: CostOptimizerActivity
│   ├── LLM Call: Memory Agent Inference
│   │   ├── Tokens: 450
│   │   ├── Cost: $0.022
│   │   └── Duration: 2.3s
│   └── Duration: 15.7s
└── Duration: 18.2s
```

## Deployment

### Kubernetes Manifest Updates

Add tracing sidecar and environment variables to your Temporal worker deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-worker
spec:
  template:
    spec:
      containers:
      - name: temporal-worker
        env:
        - name: LANGFUSE_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: public-key
        - name: LANGFUSE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: secret-key
        - name: LANGFUSE_BASE_URL
          value: "https://cloud.langfuse.com"
        - name: OTEL_SERVICE_NAME
          value: "gitops-temporal-worker"
        - name: OTEL_TRACES_EXPORTER
          value: "otlp"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "https://cloud.langfuse.com/api/public/otel"
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        # Configuration for collecting traces
```

## Best Practices

### 1. Structured Logging
Use consistent attribute naming for better filtering:

```go
span.SetAttributes(
    attribute.String("workflow.type", "cost-optimization"),
    attribute.String("cloud.provider", "aws"),
    attribute.String("operation.status", "success"),
)
```

### 2. Error Handling
Always record errors with context:

```go
if err != nil {
    span.RecordError(err)
    span.SetStatus(codes.Error, "Operation failed")
    return err
}
```

### 3. Cost Monitoring
Track LLM costs at the span level:

```go
span.SetAttributes(
    attribute.Float64("llm.cost_usd", 0.015),
    attribute.Int("llm.tokens_total", 450),
)
```

### 4. Sampling Strategy
Configure sampling for production:

```go
// Sample 10% of traces in production
trace.WithSampler(trace.TraceIDRatioBased(0.1))
```

## Troubleshooting

### Common Issues

1. **Traces Not Appearing**: Check OTLP endpoint configuration
2. **Missing LLM Metrics**: Ensure memory agent responses include token/cost data
3. **High Latency**: Monitor network calls and database queries
4. **Authentication Errors**: Verify Langfuse API keys and endpoints

### Debug Commands

```bash
# Check tracing configuration
kubectl logs -f deployment/temporal-worker | grep trace

# Verify OTLP exporter
curl -H "Authorization: Bearer $LANGFUSE_SECRET_KEY" \
     https://cloud.langfuse.com/api/public/health

# View recent traces
kubectl exec -it deployment/temporal-worker -- \
  curl http://localhost:4318/v1/traces
```

## Next Steps

1. **Implement Tracing**: Add the observability components to your workflows
2. **Configure Langfuse**: Set up your Langfuse instance and API keys
3. **Deploy and Test**: Roll out the integration and monitor initial traces
4. **Optimize Performance**: Use Langfuse insights to improve workflow efficiency
5. **Expand Coverage**: Add tracing to additional workflows and activities

This integration provides comprehensive observability into your AI agent workflows, enabling better debugging, performance monitoring, and cost optimization.
