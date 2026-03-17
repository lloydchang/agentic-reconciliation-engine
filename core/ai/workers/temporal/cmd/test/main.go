package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"gitops-infra-control-plane/core/ai/workers/temporal/internal/activities"
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

	// Create worker with tracing interceptor
	w := worker.New(c, "test-task-queue", worker.Options{})

	// Register test workflow and activities
	w.RegisterWorkflow(workflow.TestIntegrationWorkflow)
	w.RegisterActivity(activities.TestLLMActivity)
	w.RegisterActivity(activities.TestMemoryActivity)
	w.RegisterActivity(activities.TestErrorActivity)

	// Start worker
	log.Println("Starting test worker...")
	err = w.Start()
	if err != nil {
		log.Fatalf("Failed to start worker: %v", err)
	}

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down test worker...")
}

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
