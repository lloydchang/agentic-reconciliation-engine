package main
import (
	"log"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"github.com/lloydchang/gitops-infra-control-plane/ai-agents/internal/workflow"
)
func main() {
	c, _ := client.Dial(client.Options{})
	defer c.Close()
	w := worker.New(c, "cloud-ai-task-queue", worker.Options{})
	w.RegisterWorkflow(workflow.SecurityDriftWorkflow)
	err := w.Run(worker.InterruptCh())
	if err != nil { log.Fatalln("Unable to start worker", err) }
}
