package structured

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/temporal"
)

// StructuredAgentActivities provides activities for structured data handling
type StructuredAgentActivities struct {
	structuredHandler *StructuredDataHandler
	mcpRegistry      *mcp.MCPRegistry
}

// NewStructuredAgentActivities creates new structured agent activities
func NewStructuredAgentActivities() *StructuredAgentActivities {
	return &StructuredAgentActivities{
		structuredHandler: NewStructuredDataHandler(),
		mcpRegistry:      mcp.GetGlobalMCPRegistry(),
	}
}

// StructuredAgentRequest represents a request for structured agent processing
type StructuredAgentRequest struct {
	UserID     string                 `json:"user_id"`
	Message    string                 `json:"message"`
	Context    map[string]interface{} `json:"context,omitempty"`
	ExpectedTypes []ResponseType      `json:"expected_types"`
	AgentType  string                 `json:"agent_type,omitempty"`
}

// StructuredAgentResponse represents the response from structured agent processing
type StructuredAgentResponse struct {
	ResponseType ResponseType        `json:"response_type"`
	Data         interface{}         `json:"data"`
	Validation   *ValidationResult   `json:"validation"`
	ToolCalls    []ToolCall          `json:"tool_calls,omitempty"`
	ProcessedAt  time.Time           `json:"processed_at"`
}

// ProcessStructuredAgentMessage processes a message using structured data handling
func (a *StructuredAgentActivities) ProcessStructuredAgentMessage(ctx context.Context, req StructuredAgentRequest) (*StructuredAgentResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Processing structured agent message",
		"userId", req.UserID,
		"message", req.Message,
		"expectedTypes", req.ExpectedTypes)

	startTime := time.Now()

	// Create structured prompt
	_ = a.structuredHandler.CreateStructuredPrompt(
		fmt.Sprintf("Process this user message: %s", req.Message),
		req.ExpectedTypes,
	)

	// In a real implementation, this would call an LLM with the structured prompt
	// For now, simulate intelligent routing based on message content
	rawResponse := a.simulateStructuredResponse(req.Message, req.ExpectedTypes)

	// Parse and validate the structured response
	parsedResponse, err := a.structuredHandler.ParseStructuredResponse(rawResponse, req.ExpectedTypes)
	if err != nil {
		logger.Error("Failed to parse structured response", "error", err)
		return nil, temporal.NewApplicationError("failed to parse structured response", "VALIDATION_ERROR", err)
	}

	// Validate the response structure
	validation, err := a.structuredHandler.ValidateStructuredResponse(parsedResponse, ResponseType(rawResponse[8:strings.Index(rawResponse[9:], "\"")]))
	if err != nil {
		logger.Error("Failed to validate structured response", "error", err)
		return nil, temporal.NewApplicationError("failed to validate structured response", "VALIDATION_ERROR", err)
	}

	if !validation.Valid {
		logger.Warn("Structured response validation failed", "errors", validation.Errors)
	}

	// Extract tool calls if present
	var toolCalls []ToolCall
	if validation.Valid {
		// Check if response contains tool calls
		if toolCallData, ok := parsedResponse.(map[string]interface{}); ok {
			if toolCall, ok := toolCallData["tool_name"]; ok {
				toolCalls = append(toolCalls, ToolCall{
					BaseResponse: BaseResponse{Type: ResponseTypeToolCall},
					ToolName:     fmt.Sprintf("%v", toolCall),
					Parameters:   toolCallData["parameters"].(map[string]interface{}),
				})
			}
		}
	}

	response := &StructuredAgentResponse{
		Data:        parsedResponse,
		Validation:  validation,
		ToolCalls:   toolCalls,
		ProcessedAt: startTime,
	}

	// Extract response type from the parsed data
	if dataMap, ok := parsedResponse.(map[string]interface{}); ok {
		if respType, ok := dataMap["type"].(string); ok {
			response.ResponseType = ResponseType(respType)
		}
	}

	logger.Info("Structured agent message processed successfully",
		"responseType", response.ResponseType,
		"toolCalls", len(toolCalls),
		"processingTime", time.Since(startTime))

	return response, nil
}

// ExecuteStructuredToolCall executes a tool call from structured response
func (a *StructuredAgentActivities) ExecuteStructuredToolCall(ctx context.Context, toolCall ToolCall) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing structured tool call",
		"toolName", toolCall.ToolName,
		"toolId", toolCall.ToolID)

	startTime := time.Now()

	// Convert to MCP tool call
	mcpToolCall := mcp.MCPToolCall{
		ToolName:   toolCall.ToolName,
		Parameters: toolCall.Parameters,
	}

	// Execute the tool using MCP registry
	err := a.mcpRegistry.ExecuteTool(ctx, &mcpToolCall)
	if err != nil {
		logger.Error("Tool execution failed", "error", err, "toolName", toolCall.ToolName)
		return nil, temporal.NewApplicationError("tool execution failed", "TOOL_EXECUTION_ERROR", err)
	}

	result := map[string]interface{}{
		"tool_name":   toolCall.ToolName,
		"result":      mcpToolCall.Result,
		"duration":    time.Since(startTime).Milliseconds(),
		"executed_at": startTime,
	}

	logger.Info("Structured tool call executed successfully",
		"toolName", toolCall.ToolName,
		"duration", result["duration"])

	return result, nil
}

// ValidateStructuredInput validates user input against structured requirements
func (a *StructuredAgentActivities) ValidateStructuredInput(ctx context.Context, input interface{}, schema map[string]interface{}) (*ValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating structured input")

	// For now, basic validation - in a real implementation, this would use
	// more sophisticated validation against JSON schemas
	result := &ValidationResult{Valid: true}

	// Check if input is a map (JSON object)
	inputMap, ok := input.(map[string]interface{})
	if !ok {
		result.Valid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "root",
			Message: "Input must be a JSON object",
			Value:   input,
		})
		return result, nil
	}

	// Validate required fields from schema
	if schema != nil {
		if required, ok := schema["required"].([]interface{}); ok {
			for _, reqField := range required {
				fieldName := fmt.Sprintf("%v", reqField)
				if _, exists := inputMap[fieldName]; !exists {
					result.Valid = false
					result.Errors = append(result.Errors, ValidationError{
						Field:   fieldName,
						Message: "Required field is missing",
					})
				}
			}
		}
	}

	result.Data = input
	return result, nil
}

// simulateStructuredResponse simulates an AI response for demonstration
// In production, this would call an actual LLM with the structured prompt
func (a *StructuredAgentActivities) simulateStructuredResponse(message string, expectedTypes []ResponseType) string {
	message = strings.ToLower(message)

	// Simulate intelligent routing based on message content
	if strings.Contains(message, "dinner") || strings.Contains(message, "food") || strings.Contains(message, "restaurant") {
		if strings.Contains(message, "where") || strings.Contains(message, "what") {
			// Need more information
			return `{"type": "slack-response", "response": "I'd be happy to help you find dinner options! Could you tell me your location and any cuisine preferences?"}`
		} else {
			// Have enough info for research
			return `{"type": "dinner-research", "location": "downtown", "cuisine_preferences": "italian", "dietary_restrictions": "none", "price_preferences": "moderate"}`
		}
	} else if strings.Contains(message, "search") || strings.Contains(message, "find") {
		// Need to use search tool
		return `{"type": "tool-call", "tool_name": "web_search", "parameters": {"query": "` + message + `"}}`
	} else if strings.Contains(message, "hello") || strings.Contains(message, "hi") {
		// Simple greeting
		return `{"type": "slack-response", "response": "Hello! How can I help you today?"}`
	} else {
		// Users talking among themselves
		return `{"type": "no-response", "reason": "general conversation"}`
	}
}
