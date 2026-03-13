package workflows

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// GoalBasedAgentRequest represents a request for goal-based agent execution
type GoalBasedAgentRequest struct {
	Goal        string                 `json:"goal"`
	Context     map[string]interface{} `json:"context"`
	UserID      string                 `json:"userId"`
	AgentType   string                 `json:"agentType"` // single, multi
	MaxTurns    int                    `json:"maxTurns"`
	LLMProvider string                 `json:"llmProvider"`
	LLMModel    string                 `json:"llmModel"`
}

// GoalBasedAgentState represents the state of a goal-based agent
type GoalBasedAgentState struct {
	Goal           string                 `json:"goal"`
	CurrentTurn    int                    `json:"currentTurn"`
	MaxTurns       int                    `json:"maxTurns"`
	Status         string                 `json:"status"`
	ToolsUsed      []string               `json:"toolsUsed"`
	Conversation   []GoalConversationTurn     `json:"conversation"`
	StartTime      time.Time              `json:"startTime"`
	LastUpdateTime time.Time              `json:"lastUpdateTime"`
	LLMProvider     string                 `json:"llmProvider"`
	LLMModel        string                 `json:"llmModel"`
	Context         map[string]interface{} `json:"context"`
}

// GoalConversationTurn represents a single turn in the conversation
type GoalConversationTurn struct {
	TurnNumber   int                    `json:"turnNumber"`
	AgentType    string                 `json:"agentType"`
	Message      string                 `json:"message"`
	ToolCalls    []mcp.MCPToolCall      `json:"toolCalls"`
	Response     string                 `json:"response"`
	Timestamp    time.Time              `json:"timestamp"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// GoalBasedAgentWorkflow executes a goal-based agent with MCP tool support
func GoalBasedAgentWorkflow(ctx workflow.Context, request GoalBasedAgentRequest) (*GoalBasedAgentState, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Goal-Based Agent Workflow", "goal", request.Goal, "agentType", request.AgentType)

	// Set activity options with retry policy
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 10,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 5,
			BackoffCoefficient: 1.5,
			MaximumInterval:    time.Minute * 2,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Initialize agent state
	state := &GoalBasedAgentState{
		Goal:            request.Goal,
		CurrentTurn:     0,
		MaxTurns:        request.MaxTurns,
		Status:          "running",
		ToolsUsed:       []string{},
		Conversation:    []GoalConversationTurn{},
		StartTime:       workflow.Now(ctx),
		LastUpdateTime:  workflow.Now(ctx),
		LLMProvider:     request.LLMProvider,
		LLMModel:        request.LLMModel,
		Context:         request.Context,
	}

	// Get MCP registry
	mcpRegistry := mcp.GetGlobalMCPRegistry()

	// Get tools aligned with the goal
	goalTools := mcpRegistry.GetToolsByGoal(request.Goal)
	logger.Info("Found tools for goal", "goal", request.Goal, "toolCount", len(goalTools))

	if len(goalTools) == 0 {
		logger.Warn("No tools found for goal, using all available tools")
		goalTools = mcpRegistry.GetToolsByPriority(2) // Get high and medium priority tools
	}

	// Execute agent turns
	for state.CurrentTurn < state.MaxTurns && state.Status == "running" {
		state.CurrentTurn++
		state.LastUpdateTime = workflow.Now(ctx)

		// Execute conversation turn
		turn, err := executeGoalConversationTurn(ctx, state, goalTools, request.AgentType)
		if err != nil {
			logger.Error("Failed to execute conversation turn", "turn", state.CurrentTurn, "error", err)
			state.Status = "failed"
			break
		}

		// Add turn to conversation
		state.Conversation = append(state.Conversation, *turn)

		// Track tools used
		for _, toolCall := range turn.ToolCalls {
			state.ToolsUsed = append(state.ToolsUsed, toolCall.ToolName)
		}

		// Check if goal is achieved
		if isGoalAchieved(state, request.Goal) {
			state.Status = "completed"
			logger.Info("Goal achieved", "goal", request.Goal, "turns", state.CurrentTurn)
			break
		}

		// Check for human input if needed
		if needsHumanInput(turn) {
			logger.Info("Waiting for human input", "turn", state.CurrentTurn)
			humanInput, err := waitForGoalHumanInput(ctx, fmt.Sprintf("human-input-%d", state.CurrentTurn))
			if err != nil {
				logger.Error("Failed to get human input", "error", err)
				state.Status = "failed"
				break
			}

			// Add human input as a turn
			humanTurn := GoalConversationTurn{
				TurnNumber: state.CurrentTurn,
				AgentType:  "human",
				Message:    humanInput,
				ToolCalls:  []mcp.MCPToolCall{},
				Response:   "",
				Timestamp:  workflow.Now(ctx),
				Metadata:   map[string]interface{}{"source": "human"},
			}
			state.Conversation = append(state.Conversation, humanTurn)
		}
	}

	if state.Status == "running" {
		state.Status = "max_turns_reached"
		logger.Info("Max turns reached without completing goal", "goal", request.Goal)
	}

	return state, nil
}

// executeGoalConversationTurn executes a single conversation turn
func executeGoalConversationTurn(ctx workflow.Context, state *GoalBasedAgentState, availableTools []mcp.MCPTool, agentType string) (*GoalConversationTurn, error) {
	logger := workflow.GetLogger(ctx)

	turn := &GoalConversationTurn{
		TurnNumber: state.CurrentTurn,
		AgentType:  agentType,
		Timestamp:  workflow.Now(ctx),
		Metadata:   make(map[string]interface{}),
	}

	// Determine agent type and tools to use
	var toolsToUse []mcp.MCPTool
	if agentType == "multi" {
		// Multi-agent mode: select tools based on current context
		toolsToUse = selectToolsForContext(availableTools, state)
	} else {
		// Single-agent mode: use all available tools
		toolsToUse = availableTools
	}

	// Generate agent message using LLM
	var agentMessage string
	err := workflow.ExecuteActivity(ctx, activities.GenerateAgentMessageActivity, 
		state.Goal, state.Context, toolsToUse, state.LLMProvider, state.LLMModel).Get(ctx, &agentMessage)
	if err != nil {
		return nil, fmt.Errorf("failed to generate agent message: %w", err)
	}

	turn.Message = agentMessage

	// Determine if tools need to be called
	toolDecisions, err := determineToolCalls(ctx, agentMessage, toolsToUse, state.Goal)
	if err != nil {
		return nil, fmt.Errorf("failed to determine tool calls: %w", err)
	}

	// Execute tool calls
	for _, decision := range toolDecisions {
		toolCall := mcp.MCPToolCall{
			ToolName:    decision.ToolName,
			Parameters:  decision.Parameters,
			ServerName:  decision.ServerName,
			GoalContext: state.Goal,
			AgentType:   agentType,
		}

		// Execute the tool
		err := workflow.ExecuteActivity(ctx, activities.ExecuteMCPToolActivity, &toolCall).Get(ctx, nil)
		if err != nil {
			logger.Warn("Tool execution failed", "tool", toolCall.ToolName, "error", err)
			toolCall.Error = err.Error()
		}

		turn.ToolCalls = append(turn.ToolCalls, toolCall)
	}

	// Generate response based on tool results
	var response string
	err = workflow.ExecuteActivity(ctx, activities.GenerateAgentResponseActivity, 
		agentMessage, turn.ToolCalls, state.Context, state.LLMProvider, state.LLMModel).Get(ctx, &response)
	if err != nil {
		return nil, fmt.Errorf("failed to generate agent response: %w", err)
	}

	turn.Response = response

	// Update context with turn results
	updateContext(state, turn)

	return turn, nil
}

// ToolDecision represents a decision to call a tool
type ToolDecision struct {
	ToolName   string                 `json:"toolName"`
	Parameters map[string]interface{} `json:"parameters"`
	ServerName string                 `json:"serverName"`
	Confidence float64                `json:"confidence"`
}

// selectToolsForContext selects appropriate tools based on current context
func selectToolsForContext(availableTools []mcp.MCPTool, state *GoalBasedAgentState) []mcp.MCPTool {
	// Simple implementation: prioritize tools based on turn number and context
	// In a real implementation, this would use more sophisticated logic
	
	var selectedTools []mcp.MCPTool
	
	// For early turns, prioritize high-priority tools
	if state.CurrentTurn <= 2 {
		for _, tool := range availableTools {
			if tool.Priority == 1 {
				selectedTools = append(selectedTools, tool)
			}
		}
	} else {
		// For later turns, include more tools
		selectedTools = availableTools
	}
	
	return selectedTools
}

// determineToolCalls determines which tools to call based on the agent message
func determineToolCalls(ctx workflow.Context, message string, tools []mcp.MCPTool, goal string) ([]ToolDecision, error) {
	var decisions []ToolDecision
	
	// This is a simplified implementation
	// In a real implementation, this would use the LLM to analyze the message and determine tool calls
	
	// For now, we'll use a simple keyword-based approach
	for _, tool := range tools {
		if shouldCallTool(message, tool, goal) {
			decision := ToolDecision{
				ToolName:   tool.Name,
				Parameters: extractToolParameters(message, tool),
				ServerName: tool.ServerName,
				Confidence: 0.8,
			}
			decisions = append(decisions, decision)
		}
	}
	
	return decisions, nil
}

// shouldCallTool determines if a tool should be called based on the message
func shouldCallTool(message string, tool mcp.MCPTool, goal string) bool {
	// Simple keyword matching - in a real implementation, this would be more sophisticated
	messageLower := fmt.Sprintf("%s %s", message, goal)
	
	switch tool.Name {
	case "stripe_payment":
		return containsAny(messageLower, []string{"payment", "pay", "charge", "billing"})
	case "database_query":
		return containsAny(messageLower, []string{"query", "data", "database", "records"})
	case "web_search":
		return containsAny(messageLower, []string{"search", "find", "research", "information"})
	case "employee_lookup":
		return containsAny(messageLower, []string{"employee", "staff", "team", "person"})
	case "book_flight":
		return containsAny(messageLower, []string{"travel", "flight", "book", "trip"})
	default:
		return false
	}
}

// containsAny checks if the text contains any of the keywords
func containsAny(text string, keywords []string) bool {
	for _, keyword := range keywords {
		if len(text) > 0 && len(keyword) > 0 {
			// Simple contains check
			for i := 0; i <= len(text)-len(keyword); i++ {
				if text[i:i+len(keyword)] == keyword {
					return true
				}
			}
		}
	}
	return false
}

// extractToolParameters extracts parameters for a tool from the message
func extractToolParameters(message string, tool mcp.MCPTool) map[string]interface{} {
	// Simplified parameter extraction - in a real implementation, this would use NLP
	params := make(map[string]interface{})
	
	switch tool.Name {
	case "stripe_payment":
		// Mock extraction - would use NLP in real implementation
		params["amount"] = 10000 // $100.00 in cents
		params["currency"] = "usd"
		params["source"] = "tok_mock"
	case "database_query":
		params["query"] = "SELECT * FROM users LIMIT 10"
	case "web_search":
		params["query"] = message
		params["limit"] = 10
	case "employee_lookup":
		params["employee_id"] = "emp123"
		params["fields"] = []string{"name", "email", "department"}
	case "book_flight":
		params["origin"] = "SFO"
		params["destination"] = "NYC"
		params["date"] = "2024-12-25"
		params["passengers"] = 1
	}
	
	return params
}

// isGoalAchieved determines if the goal has been achieved
func isGoalAchieved(state *GoalBasedAgentState, goal string) bool {
	// Simple implementation - in a real implementation, this would use more sophisticated logic
	
	// Check if we have enough conversation turns
	if len(state.Conversation) < 2 {
		return false
	}
	
	// Check if the last response indicates completion
	lastTurn := state.Conversation[len(state.Conversation)-1]
	if lastTurn.Response == "" {
		return false
	}
	
	// Simple keyword-based completion detection
	responseLower := lastTurn.Response
	return containsAny(responseLower, []string{"completed", "done", "finished", "successful", "achieved"})
}

// needsHumanInput determines if human input is needed
func needsHumanInput(turn *GoalConversationTurn) bool {
	// Simple implementation - check if the response asks for input
	return containsAny(turn.Response, []string{"?", "please", "need", "require", "clarify"})
}

// waitForGoalHumanInput waits for human input via a signal
func waitForGoalHumanInput(ctx workflow.Context, signalName string) (string, error) {
	signalChan := workflow.GetSignalChannel(ctx, signalName)
	
	var input string
	signalChan.Receive(ctx, &input)
	
	return input, nil
}

// updateContext updates the agent context with turn results
func updateContext(state *GoalBasedAgentState, turn *GoalConversationTurn) {
	// Add turn results to context
	if state.Context == nil {
		state.Context = make(map[string]interface{})
	}
	
	// Store tool results
	toolResults := make(map[string]interface{})
	for _, toolCall := range turn.ToolCalls {
		if toolCall.Error == "" {
			toolResults[toolCall.ToolName] = toolCall.Result
		}
	}
	
	state.Context["lastToolResults"] = toolResults
	state.Context["lastMessage"] = turn.Message
	state.Context["lastResponse"] = turn.Response
	state.Context["turnCount"] = state.CurrentTurn
}

// GetGoalBasedAgentStateQuery returns the current state of the goal-based agent
func GetGoalBasedAgentStateQuery(ctx workflow.Context, state *GoalBasedAgentState) (*GoalBasedAgentState, error) {
	return state, nil
}
