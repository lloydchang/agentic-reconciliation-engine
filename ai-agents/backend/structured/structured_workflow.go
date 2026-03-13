package structured

import (
	"fmt"
	"time"

	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

// StructuredAgentWorkflow implements a workflow using structured data handling patterns
type StructuredAgentWorkflow struct {
	mcpRegistry *mcp.MCPRegistry
}

// NewStructuredAgentWorkflow creates a new structured agent workflow
func NewStructuredAgentWorkflow() *StructuredAgentWorkflow {
	return &StructuredAgentWorkflow{
		mcpRegistry: mcp.GetGlobalMCPRegistry(),
	}
}

// StructuredAgentWorkflowRequest represents the workflow input
type StructuredAgentWorkflowRequest struct {
	UserID          string                 `json:"user_id"`
	InitialMessage  string                 `json:"initial_message"`
	Context         map[string]interface{} `json:"context,omitempty"`
	MaxIterations   int                    `json:"max_iterations,omitempty"`
	AgentType       string                 `json:"agent_type,omitempty"`
	AllowedToolCalls []string             `json:"allowed_tool_calls,omitempty"`
}

// StructuredAgentWorkflowResponse represents the workflow output
type StructuredAgentWorkflowResponse struct {
	UserID         string                 `json:"user_id"`
	FinalResponse  interface{}            `json:"final_response"`
	Conversation   []ConversationTurn     `json:"conversation"`
	ToolCalls      []ToolCall             `json:"tool_calls"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Status         string                 `json:"status"`
}

// ConversationTurn represents a turn in the structured conversation
type ConversationTurn struct {
	TurnNumber   int                    `json:"turn_number"`
	UserInput    string                 `json:"user_input,omitempty"`
	AgentResponse interface{}           `json:"agent_response"`
	ToolCalls    []ToolCall             `json:"tool_calls,omitempty"`
	Timestamp    time.Time              `json:"timestamp"`
	ResponseType ResponseType           `json:"response_type"`
}

// StructuredAgentWorkflowState represents the workflow state
type StructuredAgentWorkflowState struct {
	UserID       string             `json:"user_id"`
	Conversation []ConversationTurn `json:"conversation"`
	ToolCalls    []ToolCall         `json:"tool_calls"`
	Context      map[string]interface{} `json:"context"`
	Iteration    int                `json:"iteration"`
	Status       string             `json:"status"`
	StartTime    time.Time          `json:"start_time"`
}

// StructuredAgentWorkflow implements the main workflow logic
func (w *StructuredAgentWorkflow) StructuredAgentWorkflow(ctx workflow.Context, req StructuredAgentWorkflowRequest) (*StructuredAgentWorkflowResponse, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting structured agent workflow",
		"userId", req.UserID,
		"initialMessage", req.InitialMessage)

	startTime := time.Now()

	// Set defaults
	if req.MaxIterations == 0 {
		req.MaxIterations = 5
	}

	// Initialize workflow state
	state := &StructuredAgentWorkflowState{
		UserID:    req.UserID,
		Context:   req.Context,
		Iteration: 0,
		Status:    "active",
		StartTime: startTime,
	}

	if state.Context == nil {
		state.Context = make(map[string]interface{})
	}

	// Add initial message to conversation
	state.Conversation = append(state.Conversation, ConversationTurn{
		TurnNumber:   0,
		UserInput:    req.InitialMessage,
		Timestamp:    startTime,
		ResponseType: ResponseTypeSlackResponse, // Initial input
	})

	// Main workflow loop
	for state.Iteration < req.MaxIterations && state.Status == "active" {
		state.Iteration++

		logger.Info("Processing workflow iteration",
			"iteration", state.Iteration,
			"userId", req.UserID)

		// Process the current message using structured agent
		response, err := w.processStructuredMessage(ctx, req, state)
		if err != nil {
			logger.Error("Failed to process structured message", "error", err)
			state.Status = "error"
			break
		}

		// Add response to conversation
		conversationTurn := ConversationTurn{
			TurnNumber:    state.Iteration,
			AgentResponse: response.Data,
			ToolCalls:     response.ToolCalls,
			Timestamp:     workflow.Now(ctx),
			ResponseType:  response.ResponseType,
		}
		state.Conversation = append(state.Conversation, conversationTurn)

		// Add tool calls to state
		state.ToolCalls = append(state.ToolCalls, response.ToolCalls...)

		// Execute tool calls if present
		if len(response.ToolCalls) > 0 {
			for _, toolCall := range response.ToolCalls {
				toolResult, err := w.executeToolCall(ctx, toolCall)
				if err != nil {
					logger.Error("Tool execution failed", "error", err, "toolName", toolCall.ToolName)
					// Continue with other tool calls even if one fails
					continue
				}

				// Add tool result to context for next iteration
				if state.Context["tool_results"] == nil {
					state.Context["tool_results"] = make(map[string]interface{})
				}
				toolResults := state.Context["tool_results"].(map[string]interface{})
				toolResults[toolCall.ToolName] = toolResult
			}
		}

		// Check if we should continue or finish
		if w.shouldFinishWorkflow(response.ResponseType, state.Iteration, req.MaxIterations) {
			state.Status = "completed"
			break
		}

		// Check for human input signal
		signalChan := workflow.GetSignalChannel(ctx, "human-input")
		var humanInput string
		signalChan.ReceiveAsync(&humanInput)

		// Wait for either timeout or human input
		selector := workflow.NewSelector(ctx)
		selector.AddReceive(signalChan, func(c workflow.ReceiveChannel, more bool) {
			if humanInput != "" {
				// Add human input to conversation
				state.Conversation = append(state.Conversation, ConversationTurn{
					TurnNumber:   state.Iteration + 1,
					UserInput:    humanInput,
					Timestamp:    workflow.Now(ctx),
					ResponseType: ResponseTypeSlackResponse,
				})
			}
		})

		// Timeout after 5 minutes if no human input
		selector.AddFuture(workflow.NewTimer(ctx, 5*time.Minute), func(f workflow.Future) {
			logger.Info("Workflow iteration timeout", "iteration", state.Iteration)
		})

		selector.Select(ctx)
	}

	// Prepare final response
	finalResponse := &StructuredAgentWorkflowResponse{
		UserID:         req.UserID,
		FinalResponse:  state.Conversation[len(state.Conversation)-1].AgentResponse,
		Conversation:   state.Conversation,
		ToolCalls:      state.ToolCalls,
		ProcessingTime: time.Since(startTime),
		Status:         state.Status,
	}

	logger.Info("Structured agent workflow completed",
		"userId", req.UserID,
		"iterations", state.Iteration,
		"status", state.Status,
		"processingTime", finalResponse.ProcessingTime)

	return finalResponse, nil
}

// processStructuredMessage processes a message using structured activities
func (w *StructuredAgentWorkflow) processStructuredMessage(ctx workflow.Context, req StructuredAgentWorkflowRequest, state *StructuredAgentWorkflowState) (*StructuredAgentResponse, error) {
	// Determine current message to process
	var currentMessage string
	if len(state.Conversation) > 0 {
		lastTurn := state.Conversation[len(state.Conversation)-1]
		if lastTurn.UserInput != "" {
			currentMessage = lastTurn.UserInput
		} else {
			// Use the last agent response as input for next iteration
			currentMessage = fmt.Sprintf("%v", lastTurn.AgentResponse)
		}
	}

	// Determine expected response types based on context
	expectedTypes := []ResponseType{
		ResponseTypeNoResponse,
		ResponseTypeSlackResponse,
		ResponseTypeDinnerResearch,
		ResponseTypeToolCall,
		ResponseTypeStructuredOutput,
	}

	// Create activity request
	activityReq := StructuredAgentRequest{
		UserID:       req.UserID,
		Message:      currentMessage,
		Context:      state.Context,
		ExpectedTypes: expectedTypes,
		AgentType:    req.AgentType,
	}

	// Execute structured agent activity
	var response StructuredAgentResponse
	err := workflow.ExecuteActivity(
		workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
			StartToCloseTimeout: 2 * time.Minute,
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Second,
				BackoffCoefficient: 2.0,
				MaximumInterval:    time.Minute,
				MaximumAttempts:    3,
			},
		}),
		"StructuredAgentActivities.ProcessStructuredAgentMessage",
		activityReq,
	).Get(ctx, &response)

	return &response, err
}

// executeToolCall executes a tool call using activities
func (w *StructuredAgentWorkflow) executeToolCall(ctx workflow.Context, toolCall ToolCall) (map[string]interface{}, error) {
	var result map[string]interface{}
	err := workflow.ExecuteActivity(
		workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
			StartToCloseTimeout: 3 * time.Minute,
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Second,
				BackoffCoefficient: 2.0,
				MaximumInterval:    time.Minute,
				MaximumAttempts:    2,
			},
		}),
		"StructuredAgentActivities.ExecuteStructuredToolCall",
		toolCall,
	).Get(ctx, &result)

	return result, err
}

// shouldFinishWorkflow determines if the workflow should finish
func (w *StructuredAgentWorkflow) shouldFinishWorkflow(responseType ResponseType, iteration, maxIterations int) bool {
	// Finish if we have a final response type
	switch responseType {
	case ResponseTypeNoResponse:
		return true // No response needed
	case ResponseTypeSlackResponse:
		// Check if this is a final response (not asking for more info)
		return iteration >= maxIterations
	case ResponseTypeDinnerResearch:
		return true // Research completed
	case ResponseTypeStructuredOutput:
		return true // Structured output provided
	}

	// Continue if we have tool calls or need more iterations
	return iteration >= maxIterations
}

// ValidateStructuredWorkflowInput validates workflow input
func (w *StructuredAgentWorkflow) ValidateStructuredWorkflowInput(ctx workflow.Context, req StructuredAgentWorkflowRequest) error {
	if req.UserID == "" {
		return temporal.NewApplicationError("user_id is required", "VALIDATION_ERROR")
	}
	if req.InitialMessage == "" {
		return temporal.NewApplicationError("initial_message is required", "VALIDATION_ERROR")
	}
	if req.MaxIterations < 0 {
		return temporal.NewApplicationError("max_iterations cannot be negative", "VALIDATION_ERROR")
	}
	return nil
}
