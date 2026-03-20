package main

import (
	"context"
	"log"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/workers/temporal/internal/observability"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/workers/temporal/workflow"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/workers/temporal/activities"
)

func main() {
	ctx := context.Background()

	tp, err := observability.InitTracer(ctx)
	if err != nil {
		log.Fatal(err)
	}
	defer tp.Shutdown(ctx)

	c, err := client.Dial(client.Options{})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	interceptor := observability.NewTracingInterceptor()

	w := worker.New(c, "agent-communication", worker.Options{Interceptors: []worker.Interceptor{interceptor}})

	// Register workflows
	workflow.RegisterAgentWorkflows(w)
	
	// Register agent communication workflow
	w.RegisterWorkflow(workflow.AgentCommunicationWorkflow)

	// Register activities  
	activities.RegisterAgentActivities(w)

	// Run worker
	log.Println("Starting temporal worker with agent communication...")
	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start worker", err)
	}
}
