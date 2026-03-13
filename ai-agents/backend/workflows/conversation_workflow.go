package workflows

import (
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"

	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// ConversationState tracks the state of a multi-turn conversation
type ConversationState struct {
	SessionID       string                    `json:"sessionId"`
	UserID          string                    `json:"userId"`
	ConversationID  string                    `json:"conversationId"`
	Goal            string                    `json:"goal"`
	GoalName        string                    `json:"goalName,omitempty"`      // Specific goal from registry
	CurrentTurn     int                       `json:"currentTurn"`
	MaxTurns        int                       `json:"maxTurns"`
	Status          string                    `json:"status"` // active, completed, failed, awaiting_input
	History         []ConversationTurn        `json:"history"`
	Context         map[string]interface{}    `json:"context"`
	ToolsUsed       []string                  `json:"toolsUsed"`
	MCPServers      []string                  `json:"mcpServers,omitempty"`    // Enabled MCP servers
	MCPToolsUsed    []mcp.MCPToolCall         `json:"mcpToolsUsed,omitempty"` // MCP tool calls made
	StartTime       time.Time                 `json:"startTime"`
	LastUpdateTime  time.Time                 `json:"lastUpdateTime"`
	LLMProvider     string                    `json:"llmProvider"`
	LLMModel        string                    `json:"llmModel"`
	ValidateInput   bool                      `json:"validateInput"`           // Enable input validation
}

// ConversationTurn represents a single turn in the conversation
type ConversationTurn struct {
	TurnNumber      int                      `json:"turnNumber"`
	Timestamp       time.Time                `json:"timestamp"`
	UserInput       string                   `json:"userInput,omitempty"`
	AgentResponse   string                   `json:"agentResponse,omitempty"`
	ToolCalls       []ToolCall               `json:"toolCalls,omitempty"`
	ThinkingProcess string                   `json:"thinkingProcess,omitempty"`
	Confidence      float64                  `json:"confidence"`
}

// ToolCall represents a tool invocation during conversation
type ToolCall struct {
	ToolName      string                 `json:"toolName"`
	Parameters    map[string]interface{} `json:"parameters"`
	Result        map[string]interface{} `json:"result,omitempty"`
	Status        string                 `json:"status"` // pending, completed, failed
	ExecutionTime  time.Duration          `json:"executionTime"`
	Error         string                 `json:"error,omitempty"`
}

// ConversationRequest initiates a new conversation
type ConversationRequest struct {
	UserID        string                 `json:"userId"`
	Goal          string                 `json:"goal"`
	GoalName      string                 `json:"goalName,omitempty"`      // Specific goal from registry
	InitialInput  string                 `json:"initialInput,omitempty"`
	LLMProvider   string                 `json:"llmProvider"`
	LLMModel      string                 `json:"llmModel"`
	MaxTurns      int                    `json:"maxTurns"`
	Context       map[string]interface{} `json:"context,omitempty"`
	ToolsEnabled  []string               `json:"toolsEnabled"`
	MCPServers    []string               `json:"mcpServers,omitempty"`    // MCP servers to enable
	ValidateInput bool                   `json:"validateInput"`           // Enable LLM input validation
}

// ConversationResponse contains the conversation result
type ConversationResponse struct {
	SessionID      string                   `json:"sessionId"`
	ConversationID string                  `json:"conversationId"`
	Status         string                  `json:"status"`
	FinalResult    string                  `json:"finalResult,omitempty"`
	Summary        string                  `json:"summary"`
	ToolResults    []ToolCall              `json:"toolResults"`
	Metadata       map[string]interface{}  `json:"metadata"`
	CompletedAt    time.Time               `json:"completedAt"`
	TotalTurns     int                     `json:"totalTurns"`
	Success        bool                    `json:"success"`
}

// ConversationalAgentWorkflow - Multi-turn conversation with AI agent
func ConversationalAgentWorkflow(ctx workflow.Context, request ConversationRequest) (*ConversationResponse, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Enhanced Conversational Agent Workflow", "userId", request.UserID, "goal", request.Goal, "goalName", request.GoalName)

	// Validate goal if specified
	var goal *AgentGoal
	if request.GoalName != "" {
		registry := NewGoalRegistry()
		var err error
		goal, err = registry.GetGoal(request.GoalName)
		if err != nil {
			return nil, fmt.Errorf("invalid goal name '%s': %w", request.GoalName, err)
		}
		logger.Info("Using registered goal", "goalName", goal.Name, "description", goal.Description)
	}

	// Initialize conversation state with goal and MCP support
	conversationID := fmt.Sprintf("conv-%s-%d", request.UserID, time.Now().Unix())
	state := &ConversationState{
		SessionID:      fmt.Sprintf("session-%s-%d", request.UserID, time.Now().Unix()),
		ConversationID: conversationID,
		UserID:         request.UserID,
		Goal:           request.Goal,
		GoalName:       request.GoalName,
		CurrentTurn:    0,
		MaxTurns:       request.MaxTurns,
		Status:         "active",
		History:        make([]ConversationTurn, 0),
		Context:        request.Context,
		ToolsUsed:      make([]string, 0),
		MCPServers:     request.MCPServers,
		MCPToolsUsed:   make([]mcp.MCPToolCall, 0),
		StartTime:      workflow.Now(ctx),
		LastUpdateTime: workflow.Now(ctx),
		LLMProvider:    request.LLMProvider,
		LLMModel:       request.LLMModel,
		ValidateInput:  request.ValidateInput,
	}

	// Set defaults
	if state.MaxTurns == 0 {
		if goal != nil {
			state.MaxTurns = goal.MaxTurns
		} else {
			state.MaxTurns = 20
		}
	}
	if state.Context == nil {
		state.Context = make(map[string]interface{})
	}
	if goal != nil {
		// Add goal context
		state.Context["goal_description"] = goal.Description
		state.Context["goal_tools"] = goal.Tools
		state.Context["goal_priority"] = goal.Priority
	}

	// Activity options for LLM and tool interactions
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 10,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 2,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    3,
		},
		HeartbeatTimeout: time.Minute * 2,
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Main conversation loop
	for state.CurrentTurn < state.MaxTurns && state.Status == "active" {
		state.CurrentTurn++
		logger.Info("Starting conversation turn", "turn", state.CurrentTurn, "maxTurns", state.MaxTurns)

		// Execute conversation turn
		turnResult, err := executeConversationTurn(ctx, state, request)
		if err != nil {
			logger.Error("Conversation turn failed", "turn", state.CurrentTurn, "error", err)
			state.Status = "failed"
			break
		}

		// Update state with turn result
		state.History = append(state.History, turnResult.Turn)
		state.Context = turnResult.UpdatedContext
		state.ToolsUsed = append(state.ToolsUsed, turnResult.ToolsUsed...)
		state.LastUpdateTime = workflow.Now(ctx)

		// Check if goal is achieved
		if turnResult.GoalAchieved {
			state.Status = "completed"
			logger.Info("Goal achieved", "turn", state.CurrentTurn)
			break
		}

		// Check if conversation should continue
		if turnResult.RequiresHumanInput {
			state.Status = "awaiting_input"
			logger.Info("Awaiting human input", "turn", state.CurrentTurn)
			
			// Wait for human input signal with timeout
			input, err := waitForHumanInput(ctx, state.ConversationID, time.Minute*30)
			if err != nil {
				logger.Warn("Human input timeout or error", "error", err)
				state.Status = "failed"
				break
			}
			
			// Add human input to context and continue
			state.Context["lastHumanInput"] = input
			state.Status = "active"
		}
	}

	// Generate final response
	response := &ConversationResponse{
		SessionID:      state.SessionID,
		ConversationID: state.ConversationID,
		Status:         state.Status,
		TotalTurns:     state.CurrentTurn,
		CompletedAt:    workflow.Now(ctx),
		Success:        state.Status == "completed",
	}

	// Generate summary and final result
	summaryResult, err := generateConversationSummary(ctx, state)
	if err != nil {
		logger.Warn("Failed to generate summary", "error", err)
		response.Summary = fmt.Sprintf("Conversation ended after %d turns with status: %s", state.CurrentTurn, state.Status)
	} else {
		response.Summary = summaryResult.Summary
		response.FinalResult = summaryResult.FinalResult
		response.Metadata = summaryResult.Metadata
	}

	// Collect all tool results
	response.ToolResults = collectAllToolResults(state.History)

	logger.Info("Conversational Agent Workflow completed", 
		"sessionId", state.SessionID,
		"status", response.Status,
		"turns", response.TotalTurns,
		"success", response.Success)

	return response, nil
}

// TurnResult represents the result of a single conversation turn
type TurnResult struct {
	Turn            ConversationTurn
	GoalAchieved    bool
	RequiresHumanInput bool
	UpdatedContext  map[string]interface{}
	ToolsUsed       []string
}

// executeConversationTurn executes a single turn in the conversation
func executeConversationTurn(ctx workflow.Context, state *ConversationState, request ConversationRequest) (*TurnResult, error) {
	logger := workflow.GetLogger(ctx)

	// Prepare turn context with goal and MCP information
	turnContext := map[string]interface{}{
		"sessionId":      state.SessionID,
		"conversationId": state.ConversationID,
		"currentTurn":    state.CurrentTurn,
		"goal":           state.Goal,
		"goalName":       state.GoalName,
		"history":        state.History,
		"context":        state.Context,
		"toolsEnabled":   request.ToolsEnabled,
		"mcpServers":     state.MCPServers,
		"llmProvider":    state.LLMProvider,
		"llmModel":       state.LLMModel,
		"validateInput":  state.ValidateInput,
	}

	// Add MCP tools information
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	var availableMCPTools []mcp.MCPTool
	for _, serverName := range state.MCPServers {
		if client, err := mcpRegistry.GetClient(serverName); err == nil && client.Enabled {
			availableMCPTools = append(availableMCPTools, client.Tools...)
		}
	}
	turnContext["mcpTools"] = availableMCPTools

	// Execute LLM interaction activity
	var turnActivityResult activities.ConversationTurnResult
	err := workflow.ExecuteActivity(ctx, activities.ExecuteConversationTurnActivity, turnContext).Get(ctx, &turnActivityResult)
	if err != nil {
		return nil, fmt.Errorf("failed to execute conversation turn: %w", err)
	}

	// Handle MCP tool calls
	var mcpToolResults []mcp.MCPToolCall
	for _, activityToolCall := range turnActivityResult.ToolCalls {
		// Check if this is an MCP tool call
		if isMCPTool(activityToolCall.ToolName, availableMCPTools) {
			mcpToolCall := &mcp.MCPToolCall{
				ToolName:   activityToolCall.ToolName,
				Parameters: activityToolCall.Parameters,
				ServerName: getServerForTool(activityToolCall.ToolName, state.MCPServers, mcpRegistry),
			}

			// Execute MCP tool
			err := workflow.ExecuteActivity(ctx, activities.ExecuteMCPToolActivity, mcpToolCall).Get(ctx, nil)
			if err != nil {
				logger.Warn("MCP tool execution failed", "tool", activityToolCall.ToolName, "error", err)
				mcpToolCall.Error = err.Error()
			}

			mcpToolResults = append(mcpToolResults, *mcpToolCall)
			state.MCPToolsUsed = append(state.MCPToolsUsed, *mcpToolCall)
		}
	}

	// Create turn record
	turn := ConversationTurn{
		TurnNumber:      state.CurrentTurn,
		Timestamp:       workflow.Now(ctx),
		AgentResponse:   turnActivityResult.AgentResponse,
		ToolCalls:       convertActivityToolCalls(turnActivityResult.ToolCalls),
		ThinkingProcess: turnActivityResult.ThinkingProcess,
		Confidence:      turnActivityResult.Confidence,
	}

	// Add user input if available
	if userInput, exists := state.Context["lastHumanInput"]; exists {
		turn.UserInput = userInput.(string)
		delete(state.Context, "lastHumanInput")
	}

	// Validate input if enabled
	if state.ValidateInput && turn.UserInput != "" {
		isValid, validationMessage := validateUserInput(ctx, turn.UserInput, state)
		if !isValid {
			logger.Info("User input validation failed", "input", turn.UserInput, "message", validationMessage)
			turn.ThinkingProcess += "\nInput validation: " + validationMessage
		}
	}

	result := &TurnResult{
		Turn:             turn,
		GoalAchieved:     turnActivityResult.GoalAchieved,
		RequiresHumanInput: turnActivityResult.RequiresHumanInput,
		UpdatedContext:   turnActivityResult.UpdatedContext,
		ToolsUsed:        extractToolNames(turnActivityResult.ToolCalls),
	}

	logger.Info("Enhanced conversation turn completed", 
		"turn", state.CurrentTurn,
		"goalAchieved", result.GoalAchieved,
		"requiresHumanInput", result.RequiresHumanInput,
		"toolsUsed", len(result.ToolsUsed),
		"mcpToolsUsed", len(mcpToolResults))

	return result, nil
}

// waitForHumanInput waits for human input via signal
func waitForHumanInput(ctx workflow.Context, conversationID string, timeout time.Duration) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Waiting for human input", "conversationId", conversationID, "timeout", timeout)

	// Create signal channel for human input
	inputCh := workflow.GetSignalChannel(ctx, fmt.Sprintf("human-input-%s", conversationID))

	// Create timer for timeout
	timerCtx, cancelTimer := workflow.WithCancel(ctx)
	timer := workflow.NewTimer(timerCtx, timeout)

	// Create selector to wait for either signal or timeout
	selector := workflow.NewSelector(ctx)
	var input string
	
	selector.AddReceive(inputCh, func(c workflow.ReceiveChannel, more bool) {
		c.Receive(ctx, &input)
		cancelTimer() // Cancel timer if input received
	})
	
	selector.AddFuture(timer, func(f workflow.Future) {
		// Timer expired
		input = ""
	})

	// Wait for either signal or timer
	selector.Select(ctx)

	if input == "" {
		return "", fmt.Errorf("human input timeout after %v", timeout)
	}

	logger.Info("Received human input", "conversationId", conversationID, "inputLength", len(input))
	return input, nil
}

// ConversationSummaryResult contains the conversation summary
type ConversationSummaryResult struct {
	Summary     string                 `json:"summary"`
	FinalResult string                 `json:"finalResult,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// generateConversationSummary generates a summary of the conversation
func generateConversationSummary(ctx workflow.Context, state *ConversationState) (*ConversationSummaryResult, error) {
	logger := workflow.GetLogger(ctx)

	// Prepare summary context
	summaryContext := map[string]interface{}{
		"sessionId":      state.SessionID,
		"conversationId": state.ConversationID,
		"goal":           state.Goal,
		"status":         state.Status,
		"totalTurns":     state.CurrentTurn,
		"history":        state.History,
		"toolsUsed":      state.ToolsUsed,
		"startTime":      state.StartTime,
		"endTime":        state.LastUpdateTime,
		"llmProvider":    state.LLMProvider,
		"llmModel":       state.LLMModel,
	}

	// Execute summary generation activity
	var summaryResult ConversationSummaryResult
	err := workflow.ExecuteActivity(ctx, activities.GenerateConversationSummaryActivity, summaryContext).Get(ctx, &summaryResult)
	if err != nil {
		return nil, fmt.Errorf("failed to generate conversation summary: %w", err)
	}

	logger.Info("Conversation summary generated", "conversationId", state.ConversationID)
	return &summaryResult, nil
}

// Helper functions for MCP tool management

func isMCPTool(toolName string, availableTools []mcp.MCPTool) bool {
	for _, tool := range availableTools {
		if tool.Name == toolName {
			return true
		}
	}
	return false
}

func getServerForTool(toolName string, servers []string, registry *mcp.MCPRegistry) string {
	for _, serverName := range servers {
		if client, err := registry.GetClient(serverName); err == nil {
			for _, tool := range client.Tools {
				if tool.Name == toolName {
					return serverName
				}
			}
		}
	}
	return ""
}

// validateUserInput performs LLM-based validation of user input
func validateUserInput(ctx workflow.Context, userInput string, state *ConversationState) (bool, string) {
	// This is a simplified validation - in practice, this would call an LLM to validate input
	// For now, we'll do basic validation based on goal requirements
	
	registry := NewGoalRegistry()
	if state.GoalName != "" {
		if goal, err := registry.GetGoal(state.GoalName); err == nil {
			// Check if input contains required keywords based on goal
			switch goal.Name {
			case "infrastructure_analysis":
				requiredTerms := []string{"infrastructure", "analyze", "scan", "resource", "system"}
				return containsAnyTerm(userInput, requiredTerms), "Input should contain infrastructure analysis terms"
			case "compliance_check":
				requiredTerms := []string{"compliance", "check", "audit", "policy", "gdpr", "hipaa"}
				return containsAnyTerm(userInput, requiredTerms), "Input should contain compliance-related terms"
			case "cost_optimization":
				requiredTerms := []string{"cost", "optimize", "budget", "saving", "resource", "usage"}
				return containsAnyTerm(userInput, requiredTerms), "Input should contain cost optimization terms"
			}
		}
	}
	
	// Default validation - basic length and content check
	if len(userInput) < 3 {
		return false, "Input too short - please provide more detail"
	}
	
	return true, "Input validated successfully"
}

func containsAnyTerm(input string, terms []string) bool {
	inputLower := strings.ToLower(input)
	for _, term := range terms {
		if strings.Contains(inputLower, strings.ToLower(term)) {
			return true
		}
	}
	return false
}

func convertActivityToolCalls(activityToolCalls []activities.ActivityToolCall) []ToolCall {
	toolCalls := make([]ToolCall, len(activityToolCalls))
	for i, atc := range activityToolCalls {
		toolCalls[i] = ToolCall{
			ToolName:      atc.ToolName,
			Parameters:    atc.Parameters,
			Result:        atc.Result,
			Status:        atc.Status,
			ExecutionTime:  atc.ExecutionTime,
			Error:         atc.Error,
		}
	}
	return toolCalls
}

func extractToolNames(toolCalls []activities.ActivityToolCall) []string {
	names := make([]string, len(toolCalls))
	for i, tc := range toolCalls {
		names[i] = tc.ToolName
	}
	return names
}

func collectAllToolResults(history []ConversationTurn) []ToolCall {
	var allToolCalls []ToolCall
	for _, turn := range history {
		allToolCalls = append(allToolCalls, turn.ToolCalls...)
	}
	return allToolCalls
}

// GetConversationStateQuery returns the current conversation state (for queries)
func GetConversationStateQuery(ctx workflow.Context, state *ConversationState) (*ConversationState, error) {
	return state, nil
}

// SignalHumanInputSignal allows external signals to provide human input
func SignalHumanInputSignal(ctx workflow.Context, state *ConversationState, input string) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Received human input signal", "input", input)
	
	// Store input in context for next turn
	if state.Context == nil {
		state.Context = make(map[string]interface{})
	}
	state.Context["lastHumanInput"] = input
	state.Status = "active" // Resume conversation
	
	return nil
}
