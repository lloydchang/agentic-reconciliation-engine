package structured

import (
	"encoding/json"
	"fmt"
	"reflect"
	"strings"
)

// StructuredDataHandler provides type-safe structured data handling
// inspired by PydanticAI patterns for AI agent responses
type StructuredDataHandler struct{}

// NewStructuredDataHandler creates a new structured data handler
func NewStructuredDataHandler() *StructuredDataHandler {
	return &StructuredDataHandler{}
}

// ResponseType represents different types of AI agent responses
type ResponseType string

const (
	ResponseTypeNoResponse               ResponseType = "no-response"
	ResponseTypeSlackResponse            ResponseType = "slack-response"
	ResponseTypeDinnerResearch           ResponseType = "dinner-research"
	ResponseTypeToolCall                 ResponseType = "tool-call"
	ResponseTypeStructuredOutput         ResponseType = "structured-output"
)

// BaseResponse provides common fields for all structured responses
type BaseResponse struct {
	Type ResponseType `json:"type"`
}

// NoResponse indicates no response is needed
type NoResponse struct {
	BaseResponse
	Reason string `json:"reason,omitempty"`
}

// SlackResponse represents an immediate response to send
type SlackResponse struct {
	BaseResponse
	Response string `json:"response"`
	Blocks   []SlackBlock `json:"blocks,omitempty"`
}

// SlackBlock represents a Slack message block
type SlackBlock struct {
	Type string                 `json:"type"`
	Text string                 `json:"text,omitempty"`
	Fields map[string]interface{} `json:"fields,omitempty"`
}

// DinnerResearchRequest represents a request for dinner research
type DinnerResearchRequest struct {
	BaseResponse
	Location            string `json:"location"`
	CuisinePreferences  string `json:"cuisine_preferences"`
	DietaryRestrictions string `json:"dietary_restrictions"`
	PricePreferences    string `json:"price_preferences"`
	GroupSize           int    `json:"group_size,omitempty"`
	TimeFrame           string `json:"time_frame,omitempty"`
}

// ToolCall represents a tool execution request
type ToolCall struct {
	BaseResponse
	ToolName   string                 `json:"tool_name"`
	Parameters map[string]interface{} `json:"parameters"`
	ToolID     string                 `json:"tool_id,omitempty"`
}

// StructuredOutput represents any structured data output
type StructuredOutput struct {
	BaseResponse
	Data map[string]interface{} `json:"data"`
	Schema string              `json:"schema,omitempty"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Value   interface{} `json:"value,omitempty"`
}

// ValidationResult contains validation results
type ValidationResult struct {
	Valid  bool              `json:"valid"`
	Errors []ValidationError `json:"errors,omitempty"`
	Data   interface{}       `json:"data,omitempty"`
}

// ValidateStructuredResponse validates that a response matches expected structure
func (h *StructuredDataHandler) ValidateStructuredResponse(data interface{}, expectedType ResponseType) (*ValidationResult, error) {
	result := &ValidationResult{Valid: true}

	// Convert to JSON and back to validate structure
	jsonData, err := json.Marshal(data)
	if err != nil {
		result.Valid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "marshal",
			Message: fmt.Sprintf("Failed to marshal data: %v", err),
		})
		return result, err
	}

	// Unmarshal into base response to check type
	var baseResp BaseResponse
	if err := json.Unmarshal(jsonData, &baseResp); err != nil {
		result.Valid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "base_type",
			Message: fmt.Sprintf("Invalid base response structure: %v", err),
		})
		return result, err
	}

	// Check if response type matches expected
	if baseResp.Type != expectedType {
		result.Valid = false
		result.Errors = append(result.Errors, ValidationError{
			Field:   "type",
			Message: fmt.Sprintf("Expected type %s, got %s", expectedType, baseResp.Type),
			Value:   baseResp.Type,
		})
	}

	// Type-specific validation
	switch expectedType {
	case ResponseTypeNoResponse:
		var resp NoResponse
		if err := json.Unmarshal(jsonData, &resp); err != nil {
			result.Valid = false
			result.Errors = append(result.Errors, ValidationError{
				Field:   "no_response",
				Message: fmt.Sprintf("Invalid NoResponse structure: %v", err),
			})
		}
	case ResponseTypeSlackResponse:
		var resp SlackResponse
		if err := json.Unmarshal(jsonData, &resp); err != nil {
			result.Valid = false
			result.Errors = append(result.Errors, ValidationError{
				Field:   "slack_response",
				Message: fmt.Sprintf("Invalid SlackResponse structure: %v", err),
			})
		}
	case ResponseTypeDinnerResearch:
		var resp DinnerResearchRequest
		if err := json.Unmarshal(jsonData, &resp); err != nil {
			result.Valid = false
			result.Errors = append(result.Errors, ValidationError{
				Field:   "dinner_research",
				Message: fmt.Sprintf("Invalid DinnerResearchRequest structure: %v", err),
			})
		}
	case ResponseTypeToolCall:
		var resp ToolCall
		if err := json.Unmarshal(jsonData, &resp); err != nil {
			result.Valid = false
			result.Errors = append(result.Errors, ValidationError{
				Field:   "tool_call",
				Message: fmt.Sprintf("Invalid ToolCall structure: %v", err),
			})
		}
	}

	result.Data = data
	return result, nil
}

// ParseStructuredResponse parses and validates a structured response from AI output
func (h *StructuredDataHandler) ParseStructuredResponse(jsonStr string, expectedTypes []ResponseType) (interface{}, error) {
	var rawData interface{}
	if err := json.Unmarshal([]byte(jsonStr), &rawData); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Try each expected type until one validates successfully
	for _, expectedType := range expectedTypes {
		result, err := h.ValidateStructuredResponse(rawData, expectedType)
		if err == nil && result.Valid {
			return rawData, nil
		}
	}

	return nil, fmt.Errorf("response does not match any expected structure")
}

// CreateStructuredPrompt creates a prompt that encourages structured output
func (h *StructuredDataHandler) CreateStructuredPrompt(task string, outputTypes []ResponseType) string {
	typeExamples := make([]string, len(outputTypes))
	for i, respType := range outputTypes {
		switch respType {
		case ResponseTypeNoResponse:
			typeExamples[i] = `{"type": "no-response", "reason": "users are discussing among themselves"}`
		case ResponseTypeSlackResponse:
			typeExamples[i] = `{"type": "slack-response", "response": "I'll help you find dinner options!"}`
		case ResponseTypeDinnerResearch:
			typeExamples[i] = `{"type": "dinner-research", "location": "downtown", "cuisine_preferences": "italian", "dietary_restrictions": "vegetarian", "price_preferences": "moderate"}`
		case ResponseTypeToolCall:
			typeExamples[i] = `{"type": "tool-call", "tool_name": "web_search", "parameters": {"query": "restaurants"}}`
		}
	}

	return fmt.Sprintf(`%s

You must respond with one of the following structured JSON formats:
%s

Choose the most appropriate response type based on the user's request and available information.`, task, strings.Join(typeExamples, "\n"))
}

// ValidateField validates a single field against constraints
func (h *StructuredDataHandler) ValidateField(value interface{}, fieldName string, constraints map[string]interface{}) *ValidationError {
	if constraints == nil {
		return nil
	}

	// Check required fields
	if required, ok := constraints["required"].(bool); ok && required {
		if value == nil || (reflect.TypeOf(value).Kind() == reflect.String && value.(string) == "") {
			return &ValidationError{
				Field:   fieldName,
				Message: "Field is required",
				Value:   value,
			}
		}
	}

	// Check string length
	if minLen, ok := constraints["min_length"].(float64); ok {
		if str, ok := value.(string); ok && len(str) < int(minLen) {
			return &ValidationError{
				Field:   fieldName,
				Message: fmt.Sprintf("String must be at least %d characters", int(minLen)),
				Value:   value,
			}
		}
	}

	// Check numeric range
	if minVal, ok := constraints["min"].(float64); ok {
		if num, ok := value.(float64); ok && num < minVal {
			return &ValidationError{
				Field:   fieldName,
				Message: fmt.Sprintf("Value must be at least %g", minVal),
				Value:   value,
			}
		}
	}

	return nil
}
