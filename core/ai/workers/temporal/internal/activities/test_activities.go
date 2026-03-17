package activities

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
	"go.temporal.io/sdk/activity"
)

// TestLLMActivity simulates an LLM call with comprehensive tracing
func TestLLMActivity(ctx context.Context, prompt string) (string, error) {
	logger := activity.GetLogger(ctx)
	span := trace.SpanFromContext(ctx)

	logger.Info("Starting LLM activity", "prompt", prompt)
	span.SetAttributes(
		attribute.String("llm.prompt", prompt),
		attribute.String("llm.model", "gpt-4"),
		attribute.Float64("llm.temperature", 0.7),
	)

	// Simulate LLM processing time
	time.Sleep(100 * time.Millisecond)

	// Simulate token usage metrics
	inputTokens := 25
	outputTokens := 150
	totalTokens := inputTokens + outputTokens

	span.SetAttributes(
		attribute.Int("llm.tokens.input", inputTokens),
		attribute.Int("llm.tokens.output", outputTokens),
		attribute.Int("llm.tokens.total", totalTokens),
		attribute.Float64("llm.cost.usd", 0.0025), // Simulated cost
		attribute.String("llm.response", "This is a test response from the LLM activity"),
	)

	result := fmt.Sprintf("LLM processed prompt '%s' with %d tokens", prompt, totalTokens)
	logger.Info("LLM activity completed", "result", result)
	return result, nil
}

// TestMemoryActivity simulates a memory agent call with tracing
func TestMemoryActivity(ctx context.Context, query string) (string, error) {
	logger := activity.GetLogger(ctx)
	span := trace.SpanFromContext(ctx)

	logger.Info("Starting memory activity", "query", query)
	span.SetAttributes(
		attribute.String("memory.query", query),
		attribute.String("memory.agent", "rust-memory-agent"),
	)

	// Simulate HTTP call to memory agent
	startTime := time.Now()
	time.Sleep(50 * time.Millisecond) // Simulate network latency

	// Simulate memory response
	memoryResult := fmt.Sprintf("Memory retrieved for query: %s", query)
	duration := time.Since(startTime)

	span.SetAttributes(
		attribute.String("memory.response", memoryResult),
		attribute.Int("memory.items_returned", 3),
		attribute.String("http.method", "POST"),
		attribute.Int("http.status_code", 200),
		attribute.String("http.url", "http://memory-agent:8080/query"),
		attribute.String("memory.agent.language", "rust"),
		attribute.Float64("memory.response_time_ms", float64(duration.Milliseconds())),
	)

	logger.Info("Memory activity completed", "result", memoryResult)
	return memoryResult, nil
}

// TestErrorActivity simulates an activity that fails with tracing
func TestErrorActivity(ctx context.Context) error {
	logger := activity.GetLogger(ctx)
	span := trace.SpanFromContext(ctx)

	logger.Info("Starting error activity (will fail)")
	span.SetAttributes(
		attribute.String("activity.type", "error_test"),
		attribute.String("error.expected", "true"),
	)

	// Simulate some processing before error
	time.Sleep(25 * time.Millisecond)

	// Simulate an HTTP error
	err := fmt.Errorf("simulated HTTP error: %d", http.StatusInternalServerError)
	span.RecordError(err)
	span.SetAttributes(
		attribute.String("error.type", "http_error"),
		attribute.Int("error.code", http.StatusInternalServerError),
		attribute.String("error.message", err.Error()),
	)

	logger.Error("Error activity failed as expected", "error", err)
	return err
}
