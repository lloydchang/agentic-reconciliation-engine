package main

import (
	"context"
	"log"
	"os"

	"go.temporal.io/sdk/client"
	"gitops-infra-control-plane/core/ai/workers/temporal/internal/observability"
	"gitops-infra-control-plane/core/ai/workers/temporal/workflow"
)

func main() {
	// Initialize tracing
	ctx := context.Background()
	shutdown, err := observability.InitTracer(ctx)
	if err != nil {
		log.Fatalf("Failed to initialize tracer: %v", err)
	}
	defer func() {
		if err := shutdown(ctx); err != nil {
			log.Printf("Failed to shutdown tracer: %v", err)
		}
	}()

	// Create Temporal client
	c, err := client.Dial(client.Options{
		HostPort: getEnvOrDefault("TEMPORAL_HOST", "localhost:7233"),
	})
	if err != nil {
		log.Fatalf("Failed to create Temporal client: %v", err)
	}
	defer c.Close()

	// Start the test workflow
	workflowOptions := client.StartWorkflowOptions{
		ID:        "langfuse-integration-test-" + os.Getenv("TEST_ID"),
		TaskQueue: "test-task-queue",
	}

	testID := "langfuse-integration-test-001"
	we, err := c.ExecuteWorkflow(ctx, workflowOptions, workflow.TestIntegrationWorkflow, testID)
	if err != nil {
		log.Fatalf("Failed to start workflow: %v", err)
	}

	log.Printf("Started workflow: WorkflowID=%s, RunID=%s", we.GetID(), we.GetRunID())

	// Wait for workflow completion
	var result string
	err = we.Get(ctx, &result)
	if err != nil {
		log.Fatalf("Workflow failed: %v", err)
	}

	log.Printf("Workflow completed successfully: %s", result)
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
