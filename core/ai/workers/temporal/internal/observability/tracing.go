package observability

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	"go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

// InitTracer initializes OpenTelemetry tracing with Langfuse OTLP exporter
func InitTracer(ctx context.Context) (*trace.TracerProvider, error) {
	// Create OTLP gRPC exporter for Langfuse
	endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if endpoint == "" {
		endpoint = "https://cloud.langfuse.com/api/public/otel"
	}

	exporter, err := otlptracegrpc.New(ctx,
		otlptracegrpc.WithEndpoint(endpoint),
		otlptracegrpc.WithHeaders(map[string]string{
			"Authorization": "Bearer " + os.Getenv("LANGFUSE_SECRET_KEY"),
		}),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create OTLP exporter: %w", err)
	}

	// Create resource with service information
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceNameKey.String(getServiceName()),
			semconv.ServiceVersionKey.String("1.0.0"),
			semconv.ServiceNamespaceKey.String("gitops-infra-control-plane"),
			attribute.String("service.environment", getEnvironment()),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create resource: %w", err)
	}

	// Create tracer provider with batching
	tp := trace.NewTracerProvider(
		trace.WithBatcher(exporter,
			trace.WithBatchTimeout(5*time.Second),
			trace.WithMaxExportBatchSize(512),
		),
		trace.WithResource(res),
		trace.WithSampler(getSampler()),
	)

	otel.SetTracerProvider(tp)
	return tp, nil
}

// ShutdownTracer gracefully shuts down the tracer provider
func ShutdownTracer(ctx context.Context, tp *trace.TracerProvider) error {
	if tp == nil {
		return nil
	}
	return tp.Shutdown(ctx)
}

// GetTracer returns a tracer for the given name
func GetTracer(name string) trace.Tracer {
	return otel.Tracer(name)
}

// TracingInterceptor provides automatic tracing for Temporal workflows and activities
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
			attribute.String("temporal.activity.id", in.Header.Get("ActivityID")),
		))
	defer span.End()

	startTime := time.Now()
	result, err := a.next.ExecuteActivity(ctx, in)

	// Record execution metrics
	duration := time.Since(startTime)
	span.SetAttributes(
		attribute.Float64("temporal.activity.duration_ms", float64(duration.Milliseconds())),
		attribute.String("temporal.activity.status", getStatusFromError(err)),
	)

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
			attribute.String("temporal.run.id", in.WorkflowRunID),
		))
	defer span.End()

	startTime := time.Now()
	result, err := w.next.ExecuteWorkflow(ctx, in)

	// Record execution metrics
	duration := time.Since(startTime)
	span.SetAttributes(
		attribute.Float64("temporal.workflow.duration_ms", float64(duration.Milliseconds())),
		attribute.String("temporal.workflow.status", getStatusFromError(err)),
	)

	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, "Workflow failed")
	} else {
		span.SetStatus(codes.Ok, "Workflow completed")
	}

	return result, err
}

// Helper functions

func getServiceName() string {
	if name := os.Getenv("OTEL_SERVICE_NAME"); name != "" {
		return name
	}
	return "gitops-temporal-worker"
}

func getEnvironment() string {
	if env := os.Getenv("ENVIRONMENT"); env != "" {
		return env
	}
	return "production"
}

func getSampler() trace.Sampler {
	// Use trace ID ratio sampling for production performance
	if ratio := os.Getenv("OTEL_TRACES_SAMPLER_ARG"); ratio != "" {
		if r, err := trace.ParseFloat64SamplerArg(ratio); err == nil {
			return trace.TraceIDRatioBased(r)
		}
	}
	// Default to always sample for development/debugging
	return trace.AlwaysSample()
}

func getStatusFromError(err error) string {
	if err != nil {
		return "error"
	}
	return "success"
}

// CreateWorkflowSpan creates a child span for workflow operations
func CreateWorkflowSpan(ctx workflow.Context, name string, attrs ...attribute.KeyValue) workflow.Context {
	tracer := GetTracer("temporal-workflow")

	// Convert workflow.Context to context.Context for tracing
	wfCtx, span := tracer.Start(context.Background(), name, trace.WithAttributes(attrs...))

	// Note: In Temporal, we can't directly modify the workflow context
	// This span will be separate but correlated via trace ID
	defer span.End()

	return ctx
}

// CreateActivitySpan creates a child span for activity operations
func CreateActivitySpan(ctx context.Context, name string, attrs ...attribute.KeyValue) (context.Context, func()) {
	tracer := GetTracer("temporal-activity")

	ctx, span := tracer.Start(ctx, name, trace.WithAttributes(attrs...))

	return ctx, func() { span.End() }
}

// RecordLLMCall records LLM API call metrics
func RecordLLMCall(ctx context.Context, provider, model string, promptTokens, completionTokens int, cost float64, err error) {
	tracer := GetTracer("llm-call")

	_, span := tracer.Start(ctx, "LLM-API-Call",
		trace.WithAttributes(
			attribute.String("llm.provider", provider),
			attribute.String("llm.model", model),
			attribute.Int("llm.tokens.prompt", promptTokens),
			attribute.Int("llm.tokens.completion", completionTokens),
			attribute.Int("llm.tokens.total", promptTokens+completionTokens),
			attribute.Float64("llm.cost_usd", cost),
		))
	defer span.End()

	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, "LLM call failed")
	} else {
		span.SetStatus(codes.Ok, "LLM call completed")
	}
}

// RecordMemoryAgentCall records memory agent interaction metrics
func RecordMemoryAgentCall(ctx context.Context, action string, tokensUsed int, cost float64, err error) {
	tracer := GetTracer("memory-agent")

	_, span := tracer.Start(ctx, "MemoryAgent-Call",
		trace.WithAttributes(
			attribute.String("memory.action", action),
			attribute.String("memory.service", "agent-memory-rust"),
			attribute.Int("memory.tokens.used", tokensUsed),
			attribute.Float64("memory.cost_usd", cost),
		))
	defer span.End()

	if err != nil {
		span.RecordError(err)
		span.SetStatus(codes.Error, "Memory agent call failed")
	} else {
		span.SetStatus(codes.Ok, "Memory agent call completed")
	}
}
