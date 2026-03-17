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

	_, span := tracer.Start(ctx, "ExecuteActivity",
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

	_, span := tracer.Start(ctx, "ExecuteWorkflow",
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
