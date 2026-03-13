package workflows

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// ReActAgentRequest represents a request for ReAct-style agent execution
type ReActAgentRequest struct {
	Query       string                 `json:"query"`
	Context     map[string]interface{} `json:"context"`
	MaxSteps    int                    `json:"maxSteps"`
	LLMProvider string                 `json:"llmProvider"`
	LLMModel    string                 `json:"llmModel"`
	Tools       []string               `json:"tools,omitempty"` // Specific tools to use, empty for auto-selection
}

// ReActStep represents a single step in the ReAct loop
type ReActStep struct {
	StepNumber   int                    `json:"stepNumber"`
	Type         string                 `json:"type"` // "thought", "action", "observation"
	Content      string                 `json:"content"`
	ToolCalls    []mcp.MCPToolCall      `json:"toolCalls,omitempty"`
	ToolResults  []map[string]interface{} `json:"toolResults,omitempty"`
	Timestamp    time.Time              `json:"timestamp"`
	Confidence   float64                `json:"confidence"`
}

// ReActAgentState represents the state of a ReAct agent
type ReActAgentState struct {
	Query        string                 `json:"query"`
	CurrentStep  int                    `json:"currentStep"`
	MaxSteps     int                    `json:"maxSteps"`
	Status       string                 `json:"status"` // "running", "completed", "failed", "max_steps_reached"
	Steps        []ReActStep            `json:"steps"`
	Result       string                 `json:"result"`
	StartTime    time.Time              `json:"startTime"`
	EndTime      time.Time              `json:"endTime"`
	LLMProvider  string                 `json:"llmProvider"`
	LLMModel     string                 `json:"llmModel"`
	Context      map[string]interface{} `json:"context"`
	ToolsUsed    []string               `json:"toolsUsed"`
}

// ReActAgentWorkflow executes a ReAct-style agent with tool use
func ReActAgentWorkflow(ctx workflow.Context, request ReActAgentRequest) (*ReActAgentState, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting ReAct Agent Workflow", "query", request.Query, "maxSteps", request.MaxSteps)

	// Set activity options with retry policy
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 5,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 2,
			BackoffCoefficient: 1.5,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Initialize agent state
	state := &ReActAgentState{
		Query:       request.Query,
		CurrentStep: 0,
		MaxSteps:    request.MaxSteps,
		Status:      "running",
		Steps:       []ReActStep{},
		StartTime:   workflow.Now(ctx),
		LLMProvider: request.LLMProvider,
		LLMModel:    request.LLMModel,
		Context:     request.Context,
		ToolsUsed:   []string{},
	}

	// Get available tools
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	var availableTools []mcp.MCPTool
	
	if len(request.Tools) > 0 {
		// Use specific tools
		allTools := mcpRegistry.ListAllTools()
		for _, tool := range allTools {
			for _, requestedTool := range request.Tools {
				if tool.Name == requestedTool {
					availableTools = append(availableTools, tool)
					break
				}
			}
		}
	} else {
		// Auto-select tools based on query
		availableTools = selectReActTools(request.Query, mcpRegistry)
	}

	logger.Info("Selected tools for ReAct agent", "toolCount", len(availableTools))

	// Execute ReAct loop
	for state.CurrentStep < state.MaxSteps && state.Status == "running" {
		state.CurrentStep++

		// Step 1: Thought
		thought, err := executeReActThought(ctx, state, availableTools)
		if err != nil {
			logger.Error("Failed to generate thought", "step", state.CurrentStep, "error", err)
			state.Status = "failed"
			break
		}

		// Add thought step
		thoughtStep := ReActStep{
			StepNumber: state.CurrentStep,
			Type:       "thought",
			Content:    thought,
			Timestamp:  workflow.Now(ctx),
			Confidence: 0.8,
		}
		state.Steps = append(state.Steps, thoughtStep)

		// Step 2: Action (if needed)
		actions, toolCalls, err := executeReActAction(ctx, state, availableTools)
		if err != nil {
			logger.Error("Failed to execute action", "step", state.CurrentStep, "error", err)
			state.Status = "failed"
			break
		}

		// Add action step
		actionStep := ReActStep{
			StepNumber: state.CurrentStep,
			Type:       "action",
			Content:    actions,
			ToolCalls:  toolCalls,
			Timestamp:  workflow.Now(ctx),
			Confidence: 0.7,
		}
		state.Steps = append(state.Steps, actionStep)

		// Step 3: Observation (if tools were called)
		if len(toolCalls) > 0 {
			observations, err := executeReActObservation(ctx, state, toolCalls)
			if err != nil {
				logger.Error("Failed to generate observation", "step", state.CurrentStep, "error", err)
				state.Status = "failed"
				break
			}

			// Track tools used
			for _, toolCall := range toolCalls {
				state.ToolsUsed = append(state.ToolsUsed, toolCall.ToolName)
			}

			// Add observation step
			observationStep := ReActStep{
				StepNumber:  state.CurrentStep,
				Type:        "observation",
				Content:     observations,
				ToolResults: extractToolResults(toolCalls),
				Timestamp:   workflow.Now(ctx),
				Confidence:  0.9,
			}
			state.Steps = append(state.Steps, observationStep)
		}

		// Check if we have a satisfactory answer
		if isReActCompleted(state, request.Query) {
			state.Status = "completed"
			state.Result = generateFinalResult(state)
			logger.Info("ReAct agent completed successfully", "steps", state.CurrentStep)
			break
		}
	}

	if state.Status == "running" {
		state.Status = "max_steps_reached"
		state.Result = generateFinalResult(state)
		logger.Info("ReAct agent reached max steps", "steps", state.CurrentStep)
	}

	state.EndTime = workflow.Now(ctx)
	return state, nil
}

// executeReActThought generates a thought about what to do next
func executeReActThought(ctx workflow.Context, state *ReActAgentState, tools []mcp.MCPTool) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Build context for thought generation
	context := map[string]interface{}{
		"query":        state.Query,
		"currentStep":  state.CurrentStep,
		"previousSteps": formatPreviousSteps(state.Steps),
		"availableTools": formatToolsForLLM(tools),
	}

	if state.Context != nil {
		for k, v := range state.Context {
			context[k] = v
		}
	}

	var thought string
	err := workflow.ExecuteActivity(ctx, activities.GenerateReActThoughtActivity, 
		context, state.LLMProvider, state.LLMModel).Get(ctx, &thought)
	if err != nil {
		return "", fmt.Errorf("failed to generate ReAct thought: %w", err)
	}

	logger.Info("Generated ReAct thought", "step", state.CurrentStep, "thoughtLength", len(thought))
	return thought, nil
}

// executeReActAction determines and executes actions based on the thought
func executeReActAction(ctx workflow.Context, state *ReActAgentState, tools []mcp.MCPTool) (string, []mcp.MCPToolCall, error) {
	logger := workflow.GetLogger(ctx)

	// Get the last thought
	if len(state.Steps) == 0 {
		return "", nil, fmt.Errorf("no thought step found")
	}
	
	lastThought := state.Steps[len(state.Steps)-1]
	if lastThought.Type != "thought" {
		return "", nil, fmt.Errorf("last step is not a thought")
	}

	// Determine actions from thought
	var actions string
	var toolCalls []mcp.MCPToolCall
	err := workflow.ExecuteActivity(ctx, activities.GenerateReActActionActivity, 
		lastThought.Content, state.Query, tools, state.LLMProvider, state.LLMModel).Get(ctx, &actions)
	if err != nil {
		return "", nil, fmt.Errorf("failed to generate ReAct action: %w", err)
	}

	// Parse and execute tool calls if needed
	toolCalls, err = parseAndExecuteToolCalls(ctx, actions, tools)
	if err != nil {
		logger.Warn("Failed to execute tool calls", "error", err)
		// Continue without tool calls
	}

	logger.Info("Executed ReAct action", "step", state.CurrentStep, "toolCalls", len(toolCalls))
	return actions, toolCalls, nil
}

// executeReActObservation generates observations from tool results
func executeReActObservation(ctx workflow.Context, state *ReActAgentState, toolCalls []mcp.MCPToolCall) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Extract tool results
	toolResults := extractToolResults(toolCalls)

	// Generate observation from tool results
	var observation string
	err := workflow.ExecuteActivity(ctx, activities.GenerateReActObservationActivity, 
		toolResults, state.LLMProvider, state.LLMModel).Get(ctx, &observation)
	if err != nil {
		return "", fmt.Errorf("failed to generate ReAct observation: %w", err)
	}

	logger.Info("Generated ReAct observation", "step", state.CurrentStep, "observationLength", len(observation))
	return observation, nil
}

// selectReActTools selects appropriate tools for ReAct based on the query
func selectReActTools(query string, mcpRegistry *mcp.MCPRegistry) []mcp.MCPTool {
	// Simple keyword-based tool selection
	allTools := mcpRegistry.ListAllTools()
	var selectedTools []mcp.MCPTool

	queryLower := fmt.Sprintf("%v", query)
	
	for _, tool := range allTools {
		if shouldUseToolForReAct(queryLower, tool) {
			selectedTools = append(selectedTools, tool)
		}
	}

	// If no tools selected, return high-priority tools
	if len(selectedTools) == 0 {
		selectedTools = mcpRegistry.GetToolsByPriority(1)
	}

	return selectedTools
}

// shouldUseToolForReAct determines if a tool should be used for ReAct based on the query
func shouldUseToolForReAct(query string, tool mcp.MCPTool) bool {
	switch tool.Name {
	case "web_search":
		return containsAny(query, []string{"search", "find", "information", "research", "what", "who", "when", "where", "why", "how"})
	case "database_query":
		return containsAny(query, []string{"data", "records", "database", "query", "show me", "list", "get"})
	case "stripe_payment":
		return containsAny(query, []string{"payment", "pay", "charge", "billing", "purchase", "buy"})
	case "employee_lookup":
		return containsAny(query, []string{"employee", "staff", "team", "person", "who is", "find employee"})
	case "book_flight":
		return containsAny(query, []string{"travel", "flight", "book", "trip", "vacation", "go to"})
	default:
		return false
	}
}

// parseAndExecuteToolCalls parses action text and executes tool calls
func parseAndExecuteToolCalls(ctx workflow.Context, actions string, tools []mcp.MCPTool) ([]mcp.MCPToolCall, error) {
	var toolCalls []mcp.MCPToolCall

	// This is a simplified implementation
	// In a real implementation, this would use NLP to parse the action text
	// For now, we'll use simple keyword matching

	for _, tool := range tools {
		if shouldExecuteTool(actions, tool) {
			toolCall := mcp.MCPToolCall{
				ToolName:   tool.Name,
				Parameters: extractParametersForReAct(actions, tool),
				ServerName: tool.ServerName,
			}

			// Execute the tool
			err := workflow.ExecuteActivity(ctx, activities.ExecuteMCPToolActivity, &toolCall).Get(ctx, nil)
			if err != nil {
				toolCall.Error = err.Error()
			}

			toolCalls = append(toolCalls, toolCall)
		}
	}

	return toolCalls, nil
}

// shouldExecuteTool determines if a tool should be executed based on action text
func shouldExecuteTool(actions string, tool mcp.MCPTool) bool {
	actionsLower := fmt.Sprintf("%v", actions)
	
	switch tool.Name {
	case "web_search":
		return containsAny(actionsLower, []string{"search", "look up", "find", "research"})
	case "database_query":
		return containsAny(actionsLower, []string{"query", "check", "get data", "look up records"})
	case "stripe_payment":
		return containsAny(actionsLower, []string{"process payment", "charge", "pay"})
	case "employee_lookup":
		return containsAny(actionsLower, []string{"find employee", "look up staff", "get employee"})
	case "book_flight":
		return containsAny(actionsLower, []string{"book flight", "search flights", "find travel"})
	default:
		return false
	}
}

// extractParametersForReAct extracts parameters for ReAct tool execution
func extractParametersForReAct(actions string, tool mcp.MCPTool) map[string]interface{} {
	params := make(map[string]interface{})

	switch tool.Name {
	case "web_search":
		params["query"] = actions // Simplified - would extract actual query
		params["limit"] = 10
	case "database_query":
		params["query"] = "SELECT * FROM users LIMIT 10" // Simplified
	case "stripe_payment":
		params["amount"] = 10000
		params["currency"] = "usd"
		params["source"] = "tok_mock"
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

// formatPreviousSteps formats previous steps for LLM context
func formatPreviousSteps(steps []ReActStep) string {
	if len(steps) == 0 {
		return "No previous steps."
	}

	var formatted string
	for _, step := range steps {
		formatted += fmt.Sprintf("Step %d (%s): %s\n", step.StepNumber, step.Type, step.Content)
	}
	return formatted
}

// formatToolsForLLM formats tools for LLM context
func formatToolsForLLM(tools []mcp.MCPTool) string {
	if len(tools) == 0 {
		return "No tools available."
	}

	var formatted string
	for _, tool := range tools {
		formatted += fmt.Sprintf("- %s: %s\n", tool.Name, tool.Description)
	}
	return formatted
}

// extractToolResults extracts results from tool calls
func extractToolResults(toolCalls []mcp.MCPToolCall) []map[string]interface{} {
	var results []map[string]interface{}
	for _, toolCall := range toolCalls {
		if toolCall.Error == "" && toolCall.Result != nil {
			results = append(results, toolCall.Result)
		}
	}
	return results
}

// isReActCompleted determines if the ReAct process is completed
func isReActCompleted(state *ReActAgentState, query string) bool {
	// Simple completion check
	if len(state.Steps) < 2 {
		return false
	}

	// Check if the last step provides a satisfactory answer
	lastStep := state.Steps[len(state.Steps)-1]
	
	// Look for completion indicators
	completionIndicators := []string{
		"final answer", "conclusion", "result", "answer is", "completed", "finished",
	}

	contentLower := fmt.Sprintf("%v", lastStep.Content)
	for _, indicator := range completionIndicators {
		if containsAny(contentLower, []string{indicator}) {
			return true
		}
	}

	// Check if we have tool results and an observation
	hasObservation := false
	hasToolResults := false
	for _, step := range state.Steps {
		if step.Type == "observation" {
			hasObservation = true
			if len(step.ToolResults) > 0 {
				hasToolResults = true
			}
		}
	}

	return hasObservation && hasToolResults && state.CurrentStep >= 3
}

// generateFinalResult generates the final result from the ReAct process
func generateFinalResult(state *ReActAgentState) string {
	if len(state.Steps) == 0 {
		return "No steps were executed."
	}

	// Find the last observation or action step
	var lastStep ReActStep
	for i := len(state.Steps) - 1; i >= 0; i-- {
		if state.Steps[i].Type == "observation" || state.Steps[i].Type == "action" {
			lastStep = state.Steps[i]
			break
		}
	}

	if lastStep.Content == "" {
		return "Process completed but no final result was generated."
	}

	return fmt.Sprintf("Based on the analysis: %s", lastStep.Content)
}

// GetReActAgentStateQuery returns the current state of the ReAct agent
func GetReActAgentStateQuery(ctx workflow.Context, state *ReActAgentState) (*ReActAgentState, error) {
	return state, nil
}
