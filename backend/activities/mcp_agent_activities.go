package activities

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
	"go.temporal.io/sdk/activity"
)

// GenerateAgentMessageActivity generates an agent message using LLM
func GenerateAgentMessageActivity(ctx context.Context, goal string, contextData map[string]interface{}, tools []mcp.MCPTool, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating agent message", "goal", goal, "provider", llmProvider, "model", llmModel)

	// Mock LLM implementation - in real implementation, this would call actual LLM
	_ = buildAgentPrompt(goal, contextData, tools)
	
	// Simulate LLM call
	time.Sleep(time.Millisecond * 500)
	
	// Generate mock response based on goal and available tools
	response := generateMockAgentMessage(goal, tools, contextData)
	
	logger.Info("Generated agent message", "length", len(response))
	return response, nil
}

// ExecuteMCPToolActivity executes an MCP tool
func ExecuteMCPToolActivity(ctx context.Context, toolCall *mcp.MCPToolCall) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing MCP tool", "tool", toolCall.ToolName, "server", toolCall.ServerName)

	// Get MCP registry
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	
	// Execute the tool
	err := mcpRegistry.ExecuteTool(ctx, toolCall)
	if err != nil {
		logger.Error("Tool execution failed", "tool", toolCall.ToolName, "error", err)
		return err
	}
	
	logger.Info("Tool executed successfully", "tool", toolCall.ToolName, "duration", toolCall.Duration)
	return nil
}

// GenerateAgentResponseActivity generates an agent response based on tool results
func GenerateAgentResponseActivity(ctx context.Context, message string, toolCalls []mcp.MCPToolCall, contextData map[string]interface{}, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating agent response", "toolCalls", len(toolCalls), "provider", llmProvider)

	// Mock LLM implementation - in real implementation, this would call actual LLM
	_ = buildResponsePrompt(message, toolCalls, contextData)
	
	// Simulate LLM call
	time.Sleep(time.Millisecond * 300)
	
	// Generate mock response based on tool results
	response := generateMockAgentResponse(message, toolCalls, contextData)
	
	logger.Info("Generated agent response", "length", len(response))
	return response, nil
}

// DiscoverGoalsActivity discovers available goals for the agent
func DiscoverGoalsActivity(ctx context.Context, contextData map[string]interface{}) ([]string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Discovering available goals")

	// Get MCP registry
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	allTools := mcpRegistry.ListAllTools()
	
	// Extract unique goals from tools
	goals := make(map[string]bool)
	for _, tool := range allTools {
		for _, goal := range tool.GoalAligned {
			goals[goal] = true
		}
	}
	
	// Convert to slice
	var goalList []string
	for goal := range goals {
		goalList = append(goalList, goal)
	}
	
	logger.Info("Discovered goals", "count", len(goalList))
	return goalList, nil
}

// GetToolsForGoalActivity returns tools that align with a specific goal
func GetToolsForGoalActivity(ctx context.Context, goal string) ([]mcp.MCPTool, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting tools for goal", "goal", goal)

	// Get MCP registry
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	tools := mcpRegistry.GetToolsByGoal(goal)
	
	logger.Info("Found tools for goal", "goal", goal, "count", len(tools))
	return tools, nil
}

// ListCategoriesActivity returns all available tool categories
func ListCategoriesActivity(ctx context.Context) ([]string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Listing tool categories")

	// Get MCP registry
	mcpRegistry := mcp.GetGlobalMCPRegistry()
	allTools := mcpRegistry.ListAllTools()
	
	// Extract unique categories
	categories := make(map[string]bool)
	for _, tool := range allTools {
		if tool.Category != "" {
			categories[tool.Category] = true
		}
	}
	
	// Convert to slice
	var categoryList []string
	for category := range categories {
		categoryList = append(categoryList, category)
	}
	
	logger.Info("Found categories", "count", len(categoryList))
	return categoryList, nil
}

// buildAgentPrompt builds a prompt for the agent
func buildAgentPrompt(goal string, contextData map[string]interface{}, tools []mcp.MCPTool) string {
	prompt := fmt.Sprintf("You are an AI assistant helping with the goal: %s\n\n", goal)
	
	if len(contextData) > 0 {
		prompt += "Context:\n"
		for key, value := range contextData {
			prompt += fmt.Sprintf("- %s: %v\n", key, value)
		}
		prompt += "\n"
	}
	
	if len(tools) > 0 {
		prompt += "Available tools:\n"
		for _, tool := range tools {
			prompt += fmt.Sprintf("- %s: %s\n", tool.Name, tool.Description)
		}
		prompt += "\n"
	}
	
	prompt += "Please provide a helpful response to progress toward the goal."
	return prompt
}

// buildResponsePrompt builds a prompt for generating a response
func buildResponsePrompt(message string, toolCalls []mcp.MCPToolCall, contextData map[string]interface{}) string {
	prompt := fmt.Sprintf("Previous message: %s\n\n", message)
	
	if len(toolCalls) > 0 {
		prompt += "Tool results:\n"
		for _, toolCall := range toolCalls {
			if toolCall.Error == "" {
				prompt += fmt.Sprintf("- %s: %v\n", toolCall.ToolName, toolCall.Result)
			} else {
				prompt += fmt.Sprintf("- %s: ERROR - %s\n", toolCall.ToolName, toolCall.Error)
			}
		}
		prompt += "\n"
	}
	
	if len(contextData) > 0 {
		prompt += "Additional context:\n"
		for key, value := range contextData {
			if key != "lastToolResults" && key != "lastMessage" && key != "lastResponse" {
				prompt += fmt.Sprintf("- %s: %v\n", key, value)
			}
		}
		prompt += "\n"
	}
	
	prompt += "Please provide a helpful response based on the tool results and context."
	return prompt
}

// generateMockAgentMessage generates a mock agent message
func generateMockAgentMessage(goal string, tools []mcp.MCPTool, contextData map[string]interface{}) string {
	// Simple mock implementation based on goal and available tools
	switch {
	case strings.Contains(goal, "payment") || strings.Contains(goal, "billing"):
		return "I can help you process payments using our Stripe integration. Let me gather the necessary payment information."
		
	case strings.Contains(goal, "data") || strings.Contains(goal, "query"):
		return "I can query the database to retrieve the information you need. What specific data are you looking for?"
		
	case strings.Contains(goal, "research") || strings.Contains(goal, "search"):
		return "I can search the web to find relevant information for your research. What would you like me to search for?"
		
	case strings.Contains(goal, "employee") || strings.Contains(goal, "staff"):
		return "I can look up employee information in our HR system. Which employee would you like me to find?"
		
	case strings.Contains(goal, "travel") || strings.Contains(goal, "booking"):
		return "I can help you book travel arrangements. Let me check flight options for you."
		
	default:
		return fmt.Sprintf("I understand you want to: %s. I have access to several tools that can help. Let me work on this for you.", goal)
	}
}

// generateMockAgentResponse generates a mock agent response
func generateMockAgentResponse(message string, toolCalls []mcp.MCPToolCall, contextData map[string]interface{}) string {
	if len(toolCalls) == 0 {
		return "I don't need to use any tools for this. Let me help you directly with your request."
	}
	
	var responses []string
	
	for _, toolCall := range toolCalls {
		if toolCall.Error != "" {
			responses = append(responses, fmt.Sprintf("There was an issue with %s: %s", toolCall.ToolName, toolCall.Error))
		} else {
			switch toolCall.ToolName {
			case "stripe_payment":
				responses = append(responses, "Payment processed successfully! Transaction ID: pi_mock_123")
			case "database_query":
				responses = append(responses, "I found the requested data in the database. Here are the results...")
			case "web_search":
				responses = append(responses, "I found several relevant search results for your query.")
			case "employee_lookup":
				responses = append(responses, "I found the employee information you requested.")
			case "book_flight":
				responses = append(responses, "I've found available flights for your travel dates. Here are the options...")
			default:
				responses = append(responses, fmt.Sprintf("Successfully completed %s operation.", toolCall.ToolName))
			}
		}
	}
	
	return strings.Join(responses, " ") + " Is there anything else you need help with?"
}

// AnalyzeToolUsageActivity analyzes tool usage patterns
func AnalyzeToolUsageActivity(ctx context.Context, toolCalls []mcp.MCPToolCall) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing tool usage", "toolCalls", len(toolCalls))

	analysis := make(map[string]interface{})
	
	// Count tool usage by category
	categoryCount := make(map[string]int)
	toolCount := make(map[string]int)
	
	for _, toolCall := range toolCalls {
		toolCount[toolCall.ToolName]++
		
		// Get tool category (simplified - in real implementation would look up from registry)
		category := getToolCategory(toolCall.ToolName)
		categoryCount[category]++
	}
	
	analysis["toolCount"] = toolCount
	analysis["categoryCount"] = categoryCount
	analysis["totalCalls"] = len(toolCalls)
	
	// Calculate average duration
	var totalDuration time.Duration
	for _, toolCall := range toolCalls {
		totalDuration += toolCall.Duration
	}
	
	if len(toolCalls) > 0 {
		analysis["averageDuration"] = totalDuration / time.Duration(len(toolCalls))
	}
	
	logger.Info("Tool usage analysis completed", "categories", len(categoryCount))
	return analysis, nil
}

// getToolCategory returns the category for a tool (simplified implementation)
func getToolCategory(toolName string) string {
	switch {
	case strings.Contains(toolName, "stripe") || strings.Contains(toolName, "payment"):
		return "finance"
	case strings.Contains(toolName, "database") || strings.Contains(toolName, "query"):
		return "general"
	case strings.Contains(toolName, "search"):
		return "research"
	case strings.Contains(toolName, "employee") || strings.Contains(toolName, "hr"):
		return "hr"
	case strings.Contains(toolName, "travel") || strings.Contains(toolName, "flight"):
		return "travel"
	default:
		return "unknown"
	}
}

// ToolValidationResult represents the result of parameter validation
type ToolValidationResult struct {
	IsValid bool     `json:"isValid"`
	Errors  []string `json:"errors,omitempty"`
}

// ValidateToolParametersActivity validates tool parameters
func ValidateToolParametersActivity(ctx context.Context, toolName string, parameters map[string]interface{}) (*ToolValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating tool parameters", "tool", toolName)

	var errors []string
	
	// Simple validation based on tool name
	switch toolName {
	case "stripe_payment":
		if _, ok := parameters["amount"]; !ok {
			errors = append(errors, "amount is required")
		}
		if _, ok := parameters["currency"]; !ok {
			errors = append(errors, "currency is required")
		}
		if _, ok := parameters["source"]; !ok {
			errors = append(errors, "source is required")
		}
		
	case "database_query":
		if _, ok := parameters["query"]; !ok {
			errors = append(errors, "query is required")
		}
		
	case "web_search":
		if _, ok := parameters["query"]; !ok {
			errors = append(errors, "query is required")
		}
		
	case "employee_lookup":
		if _, ok := parameters["employee_id"]; !ok {
			errors = append(errors, "employee_id is required")
		}
		
	case "book_flight":
		required := []string{"origin", "destination", "date"}
		for _, req := range required {
			if _, ok := parameters[req]; !ok {
				errors = append(errors, fmt.Sprintf("%s is required", req))
			}
		}
	}
	
	isValid := len(errors) == 0
	logger.Info("Parameter validation completed", "valid", isValid, "errors", len(errors))
	
	return &ToolValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}
