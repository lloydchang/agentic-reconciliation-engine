package main

import (
	"log"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/workflow"
	"github.com/lloydchang/gitops-infra-control-plane/core/ai/workers/temporal/internal/activities"
)

func main() {
	// Create Temporal client
	c, err := client.Dial(client.Options{})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	// Create worker
	w := worker.New(c, "cloud-ai-task-queue", worker.Options{})

	// Register workflows
	workflow.RegisterAgentWorkflows(w)

	// Register activities  
	activities.RegisterAgentActivities(w)

	// Run worker
	log.Println("Starting temporal worker...")
	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start worker", err)
	}
}
