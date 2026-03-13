package activities

import (
	"context"
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/activity"
)

// ConversationTurnResult represents the result of executing a conversation turn
type ConversationTurnResult struct {
	AgentResponse      string                 `json:"agentResponse"`
	ToolCalls          []ActivityToolCall     `json:"toolCalls"`
	ThinkingProcess    string                 `json:"thinkingProcess"`
	Confidence         float64                `json:"confidence"`
	GoalAchieved       bool                   `json:"goalAchieved"`
	RequiresHumanInput bool                   `json:"requiresHumanInput"`
	UpdatedContext     map[string]interface{} `json:"updatedContext"`
}

// ConversationSummaryResult contains the conversation summary
type ConversationSummaryResult struct {
	Summary     string                 `json:"summary"`
	FinalResult string                 `json:"finalResult,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ActivityToolCall represents a tool call within an activity
type ActivityToolCall struct {
	ToolName      string                 `json:"toolName"`
	Parameters    map[string]interface{} `json:"parameters"`
	Result        map[string]interface{} `json:"result,omitempty"`
	Status        string                 `json:"status"` // pending, completed, failed
	ExecutionTime  time.Duration          `json:"executionTime"`
	Error         string                 `json:"error,omitempty"`
}

// ExecuteConversationTurnActivity executes a single turn in the conversation
func ExecuteConversationTurnActivity(ctx context.Context, turnContext map[string]interface{}) (ConversationTurnResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing conversation turn activity")

	result := ConversationTurnResult{
		ToolCalls:      make([]ActivityToolCall, 0),
		UpdatedContext: make(map[string]interface{}),
		Confidence:     0.8, // Default confidence
	}

	// Extract turn information
	sessionID := turnContext["sessionId"].(string)
	conversationID := turnContext["conversationId"].(string)
	currentTurn := turnContext["currentTurn"].(int)
	goal := turnContext["goal"].(string)
	history := turnContext["history"].([]ConversationTurn)
	context := turnContext["context"].(map[string]interface{})
	toolsEnabled := turnContext["toolsEnabled"].([]string)
	llmProvider := turnContext["llmProvider"].(string)
	llmModel := turnContext["llmModel"].(string)

	logger.Info("Processing conversation turn", 
		"sessionId", sessionID,
		"conversationId", conversationID,
		"turn", currentTurn,
		"goal", goal)

	// Build conversation history for LLM
	conversationHistory := buildConversationHistory(history, context)

	// Determine if we need to call tools
	toolDecision, toolParams := analyzeForToolRequirement(goal, conversationHistory, context, toolsEnabled)
	
	if toolDecision.RequiresTools {
		logger.Info("Tool execution required", "tools", toolDecision.RequiredTools)
		
		// Execute required tools
		for _, toolName := range toolDecision.RequiredTools {
			toolCall, err := executeTool(ctx, toolName, toolParams[toolName], sessionID)
			if err != nil {
				logger.Error("Tool execution failed", "tool", toolName, "error", err)
				toolCall.Status = "failed"
				toolCall.Error = err.Error()
			}
			result.ToolCalls = append(result.ToolCalls, toolCall)
			
			// Update context with tool results
			if toolCall.Status == "completed" && toolCall.Result != nil {
				result.UpdatedContext[fmt.Sprintf("toolResult_%s", toolName)] = toolCall.Result
			}
		}
	}

	// Generate LLM response
	llmRequest := LLMRequest{
		Provider:      llmProvider,
		Model:         llmModel,
		SessionID:     sessionID,
		Goal:          goal,
		History:       conversationHistory,
		Context:       context,
		ToolResults:   extractToolResults(result.ToolCalls),
		CurrentTurn:   currentTurn,
	}

	llmResponse, err := callLLM(ctx, llmRequest)
	if err != nil {
		return ConversationTurnResult{}, fmt.Errorf("LLM call failed: %w", err)
	}

	result.AgentResponse = llmResponse.Response
	result.ThinkingProcess = llmResponse.ThinkingProcess
	result.Confidence = llmResponse.Confidence
	result.GoalAchieved = llmResponse.GoalAchieved
	result.RequiresHumanInput = llmResponse.RequiresHumanInput

	// Merge updated context from LLM
	for k, v := range llmResponse.UpdatedContext {
		result.UpdatedContext[k] = v
	}

	logger.Info("Conversation turn completed", 
		"turn", currentTurn,
		"goalAchieved", result.GoalAchieved,
		"requiresHumanInput", result.RequiresHumanInput,
		"toolsExecuted", len(result.ToolCalls))

	return result, nil
}

// GenerateConversationSummaryActivity generates a summary of the conversation
func GenerateConversationSummaryActivity(ctx context.Context, summaryContext map[string]interface{}) (ConversationSummaryResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating conversation summary")

	// Extract summary information
	sessionID := summaryContext["sessionId"].(string)
	conversationID := summaryContext["conversationId"].(string)
	goal := summaryContext["goal"].(string)
	status := summaryContext["status"].(string)
	totalTurns := summaryContext["totalTurns"].(int)
	history := summaryContext["history"].([]ConversationTurn)
	toolsUsed := summaryContext["toolsUsed"].([]string)
	startTime := summaryContext["startTime"].(time.Time)
	endTime := summaryContext["endTime"].(time.Time)
	llmProvider := summaryContext["llmProvider"].(string)
	llmModel := summaryContext["llmModel"].(string)

	// Generate summary using LLM
	summaryRequest := LLMRequest{
		Provider:    llmProvider,
		Model:       llmModel,
		SessionID:   sessionID,
		Goal:        goal,
		History:     buildConversationHistory(history, nil),
		Context: map[string]interface{}{
			"summaryTask": true,
			"status":      status,
			"totalTurns":  totalTurns,
			"toolsUsed":   toolsUsed,
			"duration":    endTime.Sub(startTime).String(),
		},
	}

	llmResponse, err := callLLMForSummary(ctx, summaryRequest)
	if err != nil {
		// Fallback summary if LLM fails
		fallbackSummary := fmt.Sprintf(
			"Conversation '%s' ended after %d turns with status: %s. Goal: %s. Tools used: %s",
			conversationID, totalTurns, status, goal, strings.Join(toolsUsed, ", "),
		)
		
		return ConversationSummaryResult{
			Summary:  fallbackSummary,
			Metadata: map[string]interface{}{
				"fallback": true,
				"error":    err.Error(),
			},
		}, nil
	}

	result := ConversationSummaryResult{
		Summary:     llmResponse.Response,
		FinalResult: llmResponse.FinalResult,
		Metadata: map[string]interface{}{
			"sessionId":      sessionID,
			"conversationId": conversationID,
			"goal":           goal,
			"status":         status,
			"totalTurns":     totalTurns,
			"toolsUsed":      toolsUsed,
			"duration":       endTime.Sub(startTime).String(),
			"llmProvider":    llmProvider,
			"llmModel":       llmModel,
			"summaryType":    "llm-generated",
		},
	}

	logger.Info("Conversation summary generated", "conversationId", conversationID)
	return result, nil
}

// Supporting types and functions

// ToolDecision represents the decision about tool usage
type ToolDecision struct {
	RequiresTools bool
	RequiredTools []string
	Parameters    map[string]map[string]interface{}
}

// LLMRequest represents a request to an LLM
type LLMRequest struct {
	Provider    string                 `json:"provider"`
	Model       string                 `json:"model"`
	SessionID   string                 `json:"sessionId"`
	Goal        string                 `json:"goal"`
	History     string                 `json:"history"`
	Context     map[string]interface{} `json:"context"`
	ToolResults map[string]interface{} `json:"toolResults"`
	CurrentTurn int                    `json:"currentTurn"`
}

// LLMResponse represents a response from an LLM
type LLMResponse struct {
	Response         string                 `json:"response"`
	ThinkingProcess  string                 `json:"thinkingProcess"`
	Confidence       float64                `json:"confidence"`
	GoalAchieved     bool                   `json:"goalAchieved"`
	RequiresHumanInput bool                 `json:"requiresHumanInput"`
	UpdatedContext   map[string]interface{} `json:"updatedContext"`
	FinalResult      string                 `json:"finalResult,omitempty"`
}

// ConversationTurn is a simplified version for activities
type ConversationTurn struct {
	TurnNumber      int       `json:"turnNumber"`
	Timestamp       time.Time `json:"timestamp"`
	UserInput       string    `json:"userInput,omitempty"`
	AgentResponse   string    `json:"agentResponse"`
	ToolCalls       []ToolCall `json:"toolCalls,omitempty"`
	ThinkingProcess string    `json:"thinkingProcess,omitempty"`
	Confidence      float64   `json:"confidence"`
}

// ToolCall is a simplified version for activities
type ToolCall struct {
	ToolName      string                 `json:"toolName"`
	Parameters    map[string]interface{} `json:"parameters"`
	Result        map[string]interface{} `json:"result,omitempty"`
	Status        string                 `json:"status"`
	ExecutionTime  time.Duration          `json:"executionTime"`
	Error         string                 `json:"error,omitempty"`
}

func buildConversationHistory(history []ConversationTurn, context map[string]interface{}) string {
	if len(history) == 0 {
		return "No previous conversation history."
	}

	var builder strings.Builder
	builder.WriteString("Conversation History:\n\n")
	
	for _, turn := range history {
		builder.WriteString(fmt.Sprintf("Turn %d (%s):\n", turn.TurnNumber, turn.Timestamp.Format("15:04:05")))
		
		if turn.UserInput != "" {
			builder.WriteString(fmt.Sprintf("User: %s\n", turn.UserInput))
		}
		
		if turn.AgentResponse != "" {
			builder.WriteString(fmt.Sprintf("Agent: %s\n", turn.AgentResponse))
		}
		
		if len(turn.ToolCalls) > 0 {
			builder.WriteString("Tools used:\n")
			for _, tc := range turn.ToolCalls {
				builder.WriteString(fmt.Sprintf("  - %s: %s\n", tc.ToolName, tc.Status))
			}
		}
		
		builder.WriteString("\n")
	}
	
	// Add current context if available
	if context != nil && len(context) > 0 {
		builder.WriteString("Current Context:\n")
		for k, v := range context {
			builder.WriteString(fmt.Sprintf("  %s: %v\n", k, v))
		}
	}
	
	return builder.String()
}

func analyzeForToolRequirement(goal, history string, context map[string]interface{}, toolsEnabled []string) (ToolDecision, map[string]map[string]interface{}) {
	decision := ToolDecision{
		RequiresTools: false,
		RequiredTools: make([]string, 0),
		Parameters:    make(map[string]map[string]interface{}),
	}

	// Simple heuristic for tool requirement analysis
	goalLower := strings.ToLower(goal)
	historyLower := strings.ToLower(history)
	
	// Check for compliance/security/cost analysis keywords
	if containsAny(goalLower+historyLower, []string{"compliance", "security", "scan", "check", "analyze", "audit"}) {
		if containsString(toolsEnabled, "start_compliance_workflow") {
			decision.RequiresTools = true
			decision.RequiredTools = append(decision.RequiredTools, "start_compliance_workflow")
			
			// Extract target resource from context or use default
			targetResource := "vm-web-server-001"
			if tr, exists := context["targetResource"]; exists {
				targetResource = tr.(string)
			}
			
			decision.Parameters["start_compliance_workflow"] = map[string]interface{}{
				"targetResource": targetResource,
				"complianceType": "SOC2",
				"priority":       "normal",
			}
		}
	}
	
	// Check for infrastructure queries
	if containsAny(goalLower+historyLower, []string{"infrastructure", "resources", "servers", "databases"}) {
		if containsString(toolsEnabled, "get_infrastructure_info") {
			decision.RequiresTools = true
			decision.RequiredTools = append(decision.RequiredTools, "get_infrastructure_info")
			decision.Parameters["get_infrastructure_info"] = map[string]interface{}{
				"resourceType": "all",
				"environment":  "all",
			}
		}
	}

	return decision, decision.Parameters
}

func executeTool(ctx context.Context, toolName string, parameters map[string]interface{}, sessionID string) (ActivityToolCall, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing tool", "tool", toolName, "sessionId", sessionID)

	startTime := time.Now()
	toolCall := ActivityToolCall{
		ToolName:      toolName,
		Parameters:    parameters,
		Status:        "pending",
		ExecutionTime: 0,
	}

	// Simulate tool execution based on tool name
	switch toolName {
	case "start_compliance_workflow":
		// Simulate compliance workflow execution
		time.Sleep(time.Millisecond * 500) // Simulate work
		toolCall.Result = map[string]interface{}{
			"workflowId":   fmt.Sprintf("comp-%s-%d", sessionID, time.Now().Unix()),
			"status":       "completed",
			"complianceScore": 87.5,
			"riskLevel":    "Low",
			"findings":     []string{"Minor configuration issues detected"},
		}
		toolCall.Status = "completed"

	case "get_infrastructure_info":
		// Simulate infrastructure query
		time.Sleep(time.Millisecond * 200) // Simulate work
		toolCall.Result = map[string]interface{}{
			"resources": []map[string]interface{}{
				{
					"id":      "vm-web-server-001",
					"type":    "vm",
					"status":  "running",
					"region":  "us-west-2",
				},
				{
					"id":      "db-main-001",
					"type":    "database",
					"status":  "available",
					"engine":  "postgresql",
				},
			},
			"total": 2,
		}
		toolCall.Status = "completed"

	default:
		toolCall.Status = "failed"
		toolCall.Error = fmt.Sprintf("Unknown tool: %s", toolName)
	}

	toolCall.ExecutionTime = time.Since(startTime)
	return toolCall, nil
}

func callLLM(ctx context.Context, request LLMRequest) (LLMResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Calling LLM", "provider", request.Provider, "model", request.Model)

	// Simulate LLM call (in real implementation, this would call actual LLM APIs)
	time.Sleep(time.Millisecond * 800) // Simulate LLM processing time

	// Generate contextual response based on goal and history
	response := generateContextualResponse(request)
	
	return LLMResponse{
		Response:          response.Text,
		ThinkingProcess:   response.Thinking,
		Confidence:        response.Confidence,
		GoalAchieved:      response.GoalAchieved,
		RequiresHumanInput: response.RequiresHumanInput,
		UpdatedContext:    response.UpdatedContext,
	}, nil
}

func callLLMForSummary(ctx context.Context, request LLMRequest) (LLMResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Calling LLM for summary", "provider", request.Provider)

	// Simulate LLM call for summary
	time.Sleep(time.Millisecond * 400)

	// Generate summary
	duration := request.Context["duration"].(string)
	totalTurns := request.Context["totalTurns"].(int)
	status := request.Context["status"].(string)
	
	summary := fmt.Sprintf(
		"Conversation completed with status '%s' after %d turns (%s duration). ",
		status, totalTurns, duration,
	)

	if status == "completed" {
		summary += "The goal was successfully achieved through collaborative analysis and tool execution. "
		summary += "Key findings were documented and appropriate actions were taken."
	} else {
		summary += "The conversation ended without fully achieving the goal. "
		summary += "Additional human input or automated actions may be required."
	}

	return LLMResponse{
		Response:     summary,
		Confidence:   0.9,
		FinalResult:  summary,
		UpdatedContext: map[string]interface{}{
			"summarizedAt": time.Now().Format(time.RFC3339),
		},
	}, nil
}

// Helper functions

func containsAny(text string, substrings []string) bool {
	for _, substring := range substrings {
		if strings.Contains(text, substring) {
			return true
		}
	}
	return false
}

func containsString(slice []string, target string) bool {
	for _, item := range slice {
		if item == target {
			return true
		}
	}
	return false
}

func extractToolResults(toolCalls []ActivityToolCall) map[string]interface{} {
	results := make(map[string]interface{})
	for _, tc := range toolCalls {
		if tc.Status == "completed" && tc.Result != nil {
			results[tc.ToolName] = tc.Result
		}
	}
	return results
}

// LLMResponseData represents the structured response from LLM generation
type LLMResponseData struct {
	Text             string
	Thinking         string
	Confidence       float64
	GoalAchieved     bool
	RequiresHumanInput bool
	UpdatedContext   map[string]interface{}
}

func generateContextualResponse(request LLMRequest) LLMResponseData {
	goalLower := strings.ToLower(request.Goal)
	
	// Generate contextual response based on goal
	if strings.Contains(goalLower, "compliance") || strings.Contains(goalLower, "security") {
		return LLMResponseData{
			Text: "I'll help you with the compliance and security analysis. Let me check the current infrastructure status and run a comprehensive security scan.",
			Thinking: "User is asking about compliance/security. I should use the infrastructure info and compliance workflow tools to gather relevant information.",
			Confidence: 0.85,
			GoalAchieved: false,
			RequiresHumanInput: false,
			UpdatedContext: map[string]interface{}{
				"analysisType": "compliance-security",
			},
		}
	}
	
	if strings.Contains(goalLower, "infrastructure") || strings.Contains(goalLower, "resources") {
		return LLMResponseData{
			Text: "I can help you explore the infrastructure. Let me gather information about all available resources across your environments.",
			Thinking: "User wants infrastructure information. I'll use the get_infrastructure_info tool to provide a comprehensive overview.",
			Confidence: 0.9,
			GoalAchieved: false,
			RequiresHumanInput: false,
			UpdatedContext: map[string]interface{}{
				"analysisType": "infrastructure-discovery",
			},
		}
	}
	
	// Default response
	return LLMResponseData{
		Text: fmt.Sprintf("I understand you want to: %s. I'm ready to help you achieve this goal using the available tools and capabilities.", request.Goal),
		Thinking: "General goal provided. I should ask for clarification or proceed with general analysis based on available context.",
		Confidence: 0.7,
		GoalAchieved: false,
		RequiresHumanInput: true,
		UpdatedContext: map[string]interface{}{
			"needsClarification": true,
		},
	}
}
