package workflow

import (
	"context"
	"time"

	"go.temporal.io/sdk/workflow"
	"agentic-reconciliation-engine/core/ai/workers/temporal/internal/activities"
)

// TestIntegrationWorkflow executes a comprehensive test of Langfuse tracing integration
func TestIntegrationWorkflow(ctx workflow.Context, testID string) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Langfuse integration test workflow", "testID", testID)

	ao := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	// Test LLM activity with tracing
	var llmResult string
	err := workflow.ExecuteActivity(ctx, activities.TestLLMActivity, "Test prompt for Langfuse integration").Get(ctx, &llmResult)
	if err != nil {
		logger.Error("LLM activity failed", "error", err)
		return "", err
	}

	// Test memory agent activity with tracing
	var memoryResult string
	err = workflow.ExecuteActivity(ctx, activities.TestMemoryActivity, "Test memory query").Get(ctx, &memoryResult)
	if err != nil {
		logger.Error("Memory activity failed", "error", err)
		return "", err
	}

	// Test error scenario
	err = workflow.ExecuteActivity(ctx, activities.TestErrorActivity).Get(ctx, nil)
	if err != nil {
		logger.Info("Expected error activity completed with error", "error", err)
	}

	result := "Integration test completed: LLM=" + llmResult + ", Memory=" + memoryResult + ", TestID=" + testID
	logger.Info("Langfuse integration test workflow completed", "result", result)
	return result, nil
}
