package workflow

import (
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/agents/internal/activities"
)

// AgentCommunicationInput defines input for agent communication workflow
type AgentCommunicationInput struct {
	FromAgent    string                 `json:"from_agent"`
	ToAgent      string                 `json:"to_agent"`
	Message      string                 `json:"message"`
	MessageType  string                 `json:"message_type"`
	Priority     string                 `json:"priority"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// AgentCommunicationOutput defines output from agent communication workflow
type AgentCommunicationOutput struct {
	MessageID    string `json:"message_id"`
	Status       string `json:"status"`
	Response     string `json:"response"`
	Timestamp    string `json:"timestamp"`
}

// AgentCommunicationWorkflow enables inter-agent communication via Temporal
func AgentCommunicationWorkflow(ctx workflow.Context, input AgentCommunicationInput) (*AgentCommunicationOutput, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting agent communication workflow", 
		"FromAgent", input.FromAgent, 
		"ToAgent", input.ToAgent, 
		"MessageType", input.MessageType)
	
	// Generate unique message ID
	messageID := workflow.Now(ctx).Format("20060102-150405") + "-" + input.FromAgent + "-" + input.ToAgent
	
	// Execute message delivery activity
	options := workflow.ActivityOptions{
		ScheduleToCloseTimeout: time.Minute * 10,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 2,
			BackoffCoefficient: 2.0,
			MaximumAttempts:    3,
		},
	}
	
	// Deliver message to target agent
	deliveryResult := workflow.ExecuteActivity(ctx, activities.DeliverAgentMessage, activities.AgentMessage{
		ID:          messageID,
		FromAgent:   input.FromAgent,
		ToAgent:     input.ToAgent,
		Message:     input.Message,
		MessageType: input.MessageType,
		Priority:    input.Priority,
		Metadata:    input.Metadata,
		Timestamp:   workflow.Now(ctx),
	}, options)
	
	var deliveryStatus string
	deliveryResult.Get(ctx, &deliveryStatus)
	
	// If message requires acknowledgment, wait for response
	if input.MessageType == "request" || input.MessageType == "command" {
		responseOptions := workflow.ActivityOptions{
			ScheduleToCloseTimeout: time.Minute * 5,
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Second * 1,
				BackoffCoefficient: 1.5,
				MaximumAttempts:    2,
			},
		}
		
		responseResult := workflow.ExecuteActivity(ctx, activities.WaitForAgentResponse, activities.ResponseWaiter{
			MessageID:    messageID,
			FromAgent:    input.ToAgent,
			ToAgent:      input.FromAgent,
			Timeout:      time.Minute * 3,
		}, responseOptions)
		
		var response string
		responseResult.Get(ctx, &response)
		
		return &AgentCommunicationOutput{
			MessageID: messageID,
			Status:    "completed_with_response",
			Response:  response,
			Timestamp: workflow.Now(ctx).Format(time.RFC3339),
		}, nil
	}
	
	return &AgentCommunicationOutput{
		MessageID: messageID,
		Status:    "delivered",
		Response:  "",
		Timestamp: workflow.Now(ctx).Format(time.RFC3339),
	}, nil
}
