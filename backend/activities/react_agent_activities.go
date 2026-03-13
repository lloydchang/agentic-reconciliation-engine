package activities

import (
	"context"
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// GenerateReActThoughtActivity generates a thought for the ReAct agent
func GenerateReActThoughtActivity(ctx context.Context, contextData map[string]interface{}, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating ReAct thought", "provider", llmProvider, "model", llmModel)

	// Build prompt for thought generation
	_ = buildReActThoughtPrompt(contextData)
	
	// Mock LLM implementation - in real implementation, this would call actual LLM
	time.Sleep(time.Millisecond * 300)
	
	// Generate mock thought based on context
	thought := generateMockReActThought(contextData)
	
	logger.Info("Generated ReAct thought", "length", len(thought))
	return thought, nil
}

// GenerateReActActionActivity generates an action based on the thought
func GenerateReActActionActivity(ctx context.Context, thought string, query string, tools []mcp.MCPTool, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating ReAct action", "tools", len(tools))

	// Build prompt for action generation
	_ = buildReActActionPrompt(thought, query, tools)
	
	// Mock LLM implementation
	time.Sleep(time.Millisecond * 200)
	
	// Generate mock action
	action := generateMockReActAction(thought, query, tools)
	
	logger.Info("Generated ReAct action", "length", len(action))
	return action, nil
}

// GenerateReActObservationActivity generates an observation from tool results
func GenerateReActObservationActivity(ctx context.Context, toolResults []map[string]interface{}, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating ReAct observation", "results", len(toolResults))

	// Build prompt for observation generation
	_ = buildReActObservationPrompt(toolResults)
	
	// Mock LLM implementation
	time.Sleep(time.Millisecond * 200)
	
	// Generate mock observation
	observation := generateMockReActObservation(toolResults)
	
	logger.Info("Generated ReAct observation", "length", len(observation))
	return observation, nil
}

// buildReActThoughtPrompt builds a prompt for thought generation
func buildReActThoughtPrompt(contextData map[string]interface{}) string {
	prompt := "You are a helpful AI assistant using the ReAct (Reasoning and Acting) framework. "
	prompt += "Your task is to think step by step about how to answer the user's query.\n\n"

	if query, ok := contextData["query"]; ok {
		prompt += fmt.Sprintf("User Query: %v\n\n", query)
	}

	if currentStep, ok := contextData["currentStep"]; ok {
		prompt += fmt.Sprintf("Current Step: %v\n\n", currentStep)
	}

	if previousSteps, ok := contextData["previousSteps"]; ok {
		prompt += fmt.Sprintf("Previous Steps:\n%v\n\n", previousSteps)
	}

	if availableTools, ok := contextData["availableTools"]; ok {
		prompt += fmt.Sprintf("Available Tools:\n%v\n\n", availableTools)
	}

	prompt += "Please think about what you need to do next to answer the user's query. "
	prompt += "Consider whether you need to use any tools or if you have enough information to provide an answer. "
	prompt += "Be specific about your reasoning."

	return prompt
}

// buildReActActionPrompt builds a prompt for action generation
func buildReActActionPrompt(thought string, query string, tools []mcp.MCPTool) string {
	prompt := "Based on your thought, determine what action to take next.\n\n"
	prompt += fmt.Sprintf("Thought: %s\n\n", thought)
	prompt += fmt.Sprintf("Original Query: %s\n\n", query)
	prompt += "Available Tools:\n"
	
	for _, tool := range tools {
		prompt += fmt.Sprintf("- %s: %s\n", tool.Name, tool.Description)
	}
	
	prompt += "\nIf you need to use tools, specify which ones and what parameters to use. "
	prompt += "If you have enough information to answer, say so directly."

	return prompt
}

// buildReActObservationPrompt builds a prompt for observation generation
func buildReActObservationPrompt(toolResults []map[string]interface{}) string {
	prompt := "Based on the tool results, provide an observation about what you learned.\n\n"
	prompt += "Tool Results:\n"
	
	for i, result := range toolResults {
		prompt += fmt.Sprintf("Result %d: %v\n", i+1, result)
	}
	
	prompt += "\nWhat did you learn from these results? How do they help answer the original query?"

	return prompt
}

// generateMockReActThought generates a mock thought for ReAct
func generateMockReActThought(contextData map[string]interface{}) string {
	query := ""
	if q, ok := contextData["query"]; ok {
		query = fmt.Sprintf("%v", q)
	}

	currentStep := 1
	if cs, ok := contextData["currentStep"]; ok {
		if step, ok := cs.(int); ok {
			currentStep = step
		}
	}

	// Generate thought based on query and step
	queryLower := strings.ToLower(query)
	
	switch {
	case strings.Contains(queryLower, "search") || strings.Contains(queryLower, "find"):
		return fmt.Sprintf("Step %d: I need to search for information to answer this query. The user is asking about '%s'. I should use the web search tool to find relevant information.", currentStep, query)
		
	case strings.Contains(queryLower, "data") || strings.Contains(queryLower, "records"):
		return fmt.Sprintf("Step %d: The user is asking about data or records. I should query the database to find the requested information.", currentStep)
		
	case strings.Contains(queryLower, "payment") || strings.Contains(queryLower, "pay"):
		return fmt.Sprintf("Step %d: The user is asking about a payment. I need to use the payment processing tool to handle this request.", currentStep)
		
	case strings.Contains(queryLower, "employee") || strings.Contains(queryLower, "staff"):
		return fmt.Sprintf("Step %d: The user is asking about an employee. I should use the employee lookup tool to find the requested information.", currentStep)
		
	case strings.Contains(queryLower, "travel") || strings.Contains(queryLower, "flight"):
		return fmt.Sprintf("Step %d: The user is asking about travel arrangements. I should use the flight booking tool to help with this request.", currentStep)
		
	default:
		return fmt.Sprintf("Step %d: I need to analyze this query: '%s'. Let me think about what information I need and whether I have tools available to help answer it.", currentStep, query)
	}
}

// generateMockReActAction generates a mock action for ReAct
func generateMockReActAction(thought string, query string, tools []mcp.MCPTool) string {
	thoughtLower := strings.ToLower(thought)


	// Determine action based on thought and available tools
	if strings.Contains(thoughtLower, "search") && hasTool(tools, "web_search") {
		return "I will use the web search tool to find information about: " + query
	}
	
	if strings.Contains(thoughtLower, "data") && hasTool(tools, "database_query") {
		return "I will query the database to find the requested information."
	}
	
	if strings.Contains(thoughtLower, "payment") && hasTool(tools, "stripe_payment") {
		return "I will process the payment using the Stripe integration."
	}
	
	if strings.Contains(thoughtLower, "employee") && hasTool(tools, "employee_lookup") {
		return "I will look up the employee information in the HR system."
	}
	
	if strings.Contains(thoughtLower, "travel") && hasTool(tools, "book_flight") {
		return "I will search for available flights using the booking system."
	}

	// If no specific tool is needed, provide a direct answer
	return "Based on my analysis, I can provide a direct answer without using additional tools."
}

// generateMockReActObservation generates a mock observation for ReAct
func generateMockReActObservation(toolResults []map[string]interface{}) string {
	if len(toolResults) == 0 {
		return "No tool results were obtained from the action."
	}

	var observations []string
	
	for i, result := range toolResults {
		obs := fmt.Sprintf("From tool result %d, I learned: ", i+1)
		
		// Generate observation based on result content
		if result != nil {
			if status, ok := result["status"]; ok {
				obs += fmt.Sprintf("The operation returned status '%v'. ", status)
			}
			
			if data, ok := result["data"]; ok {
				obs += fmt.Sprintf("The data shows: %v. ", data)
			}
			
			if message, ok := result["message"]; ok {
				obs += fmt.Sprintf("Additional information: %v. ", message)
			}
		}
		
		observations = append(observations, obs)
	}

	return strings.Join(observations, " ") + "This information helps me provide a comprehensive answer to the user's query."
}

// hasTool checks if a specific tool is available
func hasTool(tools []mcp.MCPTool, toolName string) bool {
	for _, tool := range tools {
		if tool.Name == toolName {
			return true
		}
	}
	return false
}

// AnalyzeReActPerformanceActivity analyzes the performance of a ReAct agent execution
func AnalyzeReActPerformanceActivity(ctx context.Context, steps []interface{}, toolsUsed []string, totalTime time.Duration) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing ReAct performance", "steps", len(steps), "tools", len(toolsUsed))

	analysis := make(map[string]interface{})
	
	// Count step types
	stepTypes := make(map[string]int)
	toolUsage := make(map[string]int)
	
	for _, step := range steps {
		if stepMap, ok := step.(map[string]interface{}); ok {
			if stepType, ok := stepMap["type"].(string); ok {
				stepTypes[stepType]++
			}
		}
	}
	
	for _, tool := range toolsUsed {
		toolUsage[tool]++
	}
	
	analysis["stepTypes"] = stepTypes
	analysis["toolUsage"] = toolUsage
	analysis["totalSteps"] = len(steps)
	analysis["totalTime"] = totalTime.Milliseconds()
	analysis["averageStepTime"] = totalTime.Milliseconds() / int64(len(steps))
	
	// Calculate efficiency metrics
	thoughtSteps := stepTypes["thought"]
	actionSteps := stepTypes["action"]
	observationSteps := stepTypes["observation"]
	
	analysis["efficiency"] = map[string]interface{}{
		"thoughtToActionRatio": float64(thoughtSteps) / float64(actionSteps),
		"actionToObservationRatio": float64(actionSteps) / float64(observationSteps),
		"completionRate": float64(observationSteps) / float64(len(steps)),
	}
	
	logger.Info("ReAct performance analysis completed", "efficiency", analysis["efficiency"])
	return analysis, nil
}

// ReActStepValidationResult represents the validation outcome
type ReActStepValidationResult struct {
	IsValid bool     `json:"isValid"`
	Errors  []string `json:"errors,omitempty"`
}

// ValidateReActStepActivity validates a ReAct step
func ValidateReActStepActivity(ctx context.Context, stepType string, content string, stepNumber int) (*ReActStepValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating ReAct step", "type", stepType, "step", stepNumber)

	var errors []string
	isValid := true

	// Validate based on step type
	switch stepType {
	case "thought":
		if len(content) < 10 {
			errors = append(errors, "Thought is too short")
			isValid = false
		}
		if !containsAny(content, []string{"think", "consider", "analyze", "need", "should"}) {
			errors = append(errors, "Thought should contain reasoning keywords")
			isValid = false
		}
		
	case "action":
		if !containsAny(content, []string{"use", "call", "execute", "process", "search", "query"}) {
			errors = append(errors, "Action should specify what to do")
			isValid = false
		}
		
	case "observation":
		if !containsAny(content, []string{"result", "found", "learned", "observed", "returned"}) {
			errors = append(errors, "Observation should describe what was learned")
			isValid = false
		}
		
	default:
		errors = append(errors, fmt.Sprintf("Unknown step type: %s", stepType))
		isValid = false
	}

	logger.Info("ReAct step validation completed", "valid", isValid, "errors", len(errors))
	return &ReActStepValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}
