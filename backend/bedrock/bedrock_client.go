package bedrock

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime"
)

// BedrockClient represents an AWS Bedrock client
type BedrockClient struct {
	runtimeClient *bedrockruntime.Client
	region       string
}

// BedrockModel represents a Bedrock model configuration
type BedrockModel struct {
	ModelID      string            `json:"modelId"`
	Name         string            `json:"name"`
	Provider     string            `json:"provider"`
	Capabilities []string          `json:"capabilities"`
	MaxTokens    int               `json:"maxTokens"`
	Temperature  float64           `json:"temperature"`
	TopP         float64           `json:"topP"`
	Parameters   map[string]interface{} `json:"parameters"`
}

// BedrockRequest represents a request to Bedrock
type BedrockRequest struct {
	ModelID     string                 `json:"modelId"`
	Prompt      string                 `json:"prompt"`
	MaxTokens   int                    `json:"maxTokens,omitempty"`
	Temperature float64                `json:"temperature,omitempty"`
	TopP        float64                `json:"topP,omitempty"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
}

// BedrockResponse represents a response from Bedrock
type BedrockResponse struct {
	Completion  string                 `json:"completion"`
	Prompt      string                 `json:"prompt"`
	ModelID     string                 `json:"modelId"`
	Usage       map[string]interface{} `json:"usage,omitempty"`
	FinishReason string                `json:"finishReason,omitempty"`
	Error       string                 `json:"error,omitempty"`
	ProcessingTime int64               `json:"processingTime"`
}

// ConversationMessage represents a message in a conversation
type ConversationMessage struct {
	Role    string `json:"role"`    // "user", "assistant", "system"
	Content string `json:"content"`
}

// ConversationRequest represents a conversation request
type ConversationRequest struct {
	ModelID       string                 `json:"modelId"`
	Messages      []ConversationMessage  `json:"messages"`
	MaxTokens     int                    `json:"maxTokens,omitempty"`
	Temperature   float64                `json:"temperature,omitempty"`
	TopP          float64                `json:"topP,omitempty"`
	SystemPrompt  string                 `json:"systemPrompt,omitempty"`
	Parameters    map[string]interface{} `json:"parameters,omitempty"`
}

// ConversationResponse represents a conversation response
type ConversationResponse struct {
	Messages      []ConversationMessage  `json:"messages"`
	ModelID       string                 `json:"modelId"`
	Usage         map[string]interface{} `json:"usage,omitempty"`
	FinishReason  string                 `json:"finishReason,omitempty"`
	Error         string                 `json:"error,omitempty"`
	ProcessingTime int64                `json:"processingTime"`
}

// NewBedrockClient creates a new Bedrock client
func NewBedrockClient(region string) (*BedrockClient, error) {
	cfg, err := config.LoadDefaultConfig(context.Background(),
		config.WithRegion(region),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %w", err)
	}

	client := bedrockruntime.NewFromConfig(cfg)

	return &BedrockClient{
		runtimeClient: client,
		region:       region,
	}, nil
}

// GetAvailableModels returns available Bedrock models
func (bc *BedrockClient) GetAvailableModels() []BedrockModel {
	return []BedrockModel{
		{
			ModelID:      "anthropic.claude-3-sonnet-20240229-v1:0",
			Name:         "Claude 3 Sonnet",
			Provider:     "Anthropic",
			Capabilities: []string{"text", "conversation", "analysis"},
			MaxTokens:    4096,
			Temperature:  0.7,
			TopP:         0.9,
			Parameters: map[string]interface{}{
				"top_k": 250,
			},
		},
		{
			ModelID:      "anthropic.claude-3-haiku-20240307-v1:0",
			Name:         "Claude 3 Haiku",
			Provider:     "Anthropic",
			Capabilities: []string{"text", "conversation", "fast"},
			MaxTokens:    4096,
			Temperature:  0.7,
			TopP:         0.9,
			Parameters: map[string]interface{}{
				"top_k": 250,
			},
		},
		{
			ModelID:      "amazon.titan-text-express-v1",
			Name:         "Titan Text Express",
			Provider:     "Amazon",
			Capabilities: []string{"text", "generation"},
			MaxTokens:    4096,
			Temperature:  0.7,
			TopP:         0.9,
		},
		{
			ModelID:      "ai21.j2-ultra-v1",
			Name:         "Jurassic-2 Ultra",
			Provider:     "AI21",
			Capabilities: []string{"text", "generation"},
			MaxTokens:    8192,
			Temperature:  0.7,
			TopP:         0.9,
		},
		{
			ModelID:      "cohere.command-text-v14",
			Name:         "Command Text",
			Provider:     "Cohere",
			Capabilities: []string{"text", "generation", "conversation"},
			MaxTokens:    4096,
			Temperature:  0.7,
			TopP:         0.75,
		},
	}
}

// InvokeModel invokes a Bedrock model
func (bc *BedrockClient) InvokeModel(ctx context.Context, request BedrockRequest) (*BedrockResponse, error) {
	start := time.Now()
	
	response := &BedrockResponse{
		ModelID:        request.ModelID,
		Prompt:         request.Prompt,
		ProcessingTime: time.Since(start).Milliseconds(),
	}

	// Mock implementation - in real implementation would call AWS Bedrock
	result, err := bc.mockInvokeModel(ctx, request)
	if err != nil {
		response.Error = err.Error()
		return response, err
	}

	response.Completion = result.Completion
	response.Usage = result.Usage
	response.FinishReason = result.FinishReason
	response.ProcessingTime = time.Since(start).Milliseconds()

	return response, nil
}

// InvokeConversation invokes a Bedrock model with conversation
func (bc *BedrockClient) InvokeConversation(ctx context.Context, request ConversationRequest) (*ConversationResponse, error) {
	start := time.Now()
	
	response := &ConversationResponse{
		ModelID:        request.ModelID,
		Messages:       request.Messages,
		ProcessingTime: time.Since(start).Milliseconds(),
	}

	// Mock implementation - in real implementation would call AWS Bedrock
	result, err := bc.mockInvokeConversation(ctx, request)
	if err != nil {
		response.Error = err.Error()
		return response, err
	}

	response.Messages = append(response.Messages, result.Messages...)
	response.Usage = result.Usage
	response.FinishReason = result.FinishReason
	response.ProcessingTime = time.Since(start).Milliseconds()

	return response, nil
}

// Mock implementations for demonstration
func (bc *BedrockClient) mockInvokeModel(ctx context.Context, request BedrockRequest) (*BedrockResponse, error) {
	// Simulate API call delay
	time.Sleep(time.Millisecond * 300)

	// Generate mock response based on model and prompt
	completion := bc.generateMockCompletion(request.ModelID, request.Prompt)

	return &BedrockResponse{
		Completion: completion,
		Usage: map[string]interface{}{
			"prompt_tokens":     len(request.Prompt) / 4,
			"completion_tokens": len(completion) / 4,
			"total_tokens":      (len(request.Prompt) + len(completion)) / 4,
		},
		FinishReason: "stop",
	}, nil
}

func (bc *BedrockClient) mockInvokeConversation(ctx context.Context, request ConversationRequest) (*ConversationResponse, error) {
	// Simulate API call delay
	time.Sleep(time.Millisecond * 400)

	// Build conversation context
	var conversationContext string
	for _, msg := range request.Messages {
		conversationContext += fmt.Sprintf("%s: %s\n", msg.Role, msg.Content)
	}

	if request.SystemPrompt != "" {
		conversationContext = fmt.Sprintf("System: %s\n%s", request.SystemPrompt, conversationContext)
	}

	// Generate mock response
	completion := bc.generateMockCompletion(request.ModelID, conversationContext)

	return &ConversationResponse{
		Messages: []ConversationMessage{
			{
				Role:    "assistant",
				Content: completion,
			},
		},
		Usage: map[string]interface{}{
			"prompt_tokens":     len(conversationContext) / 4,
			"completion_tokens": len(completion) / 4,
			"total_tokens":      (len(conversationContext) + len(completion)) / 4,
		},
		FinishReason: "stop",
	}, nil
}

func (bc *BedrockClient) generateMockCompletion(modelID string, prompt string) string {
	// Generate mock completion based on model and prompt
	switch {
	case strings.Contains(modelID, "claude"):
		return fmt.Sprintf("I'm Claude, and I understand you're asking about: %s. Let me provide a thoughtful response based on my analysis.", prompt)
	case strings.Contains(modelID, "titan"):
		return fmt.Sprintf("As Titan Text Express, I can help you with: %s. Here's my comprehensive response.", prompt)
	case strings.Contains(modelID, "j2"):
		return fmt.Sprintf("Jurassic-2 Ultra analysis of your request: %s. I'll provide detailed insights.", prompt)
	case strings.Contains(modelID, "command"):
		return fmt.Sprintf("Command Text response to: %s. I'll execute this command effectively.", prompt)
	default:
		return fmt.Sprintf("Bedrock model response to: %s. Processing your request with advanced AI capabilities.", prompt)
	}
}

// GetModelByID returns a model by its ID
func (bc *BedrockClient) GetModelByID(modelID string) (*BedrockModel, error) {
	models := bc.GetAvailableModels()
	for _, model := range models {
		if model.ModelID == modelID {
			return &model, nil
		}
	}
	return nil, fmt.Errorf("model not found: %s", modelID)
}

// ListModelsByProvider returns models filtered by provider
func (bc *BedrockClient) ListModelsByProvider(provider string) []BedrockModel {
	var models []BedrockModel
	allModels := bc.GetAvailableModels()
	
	for _, model := range allModels {
		if model.Provider == provider {
			models = append(models, model)
		}
	}
	
	return models
}

// ListModelsByCapability returns models filtered by capability
func (bc *BedrockClient) ListModelsByCapability(capability string) []BedrockModel {
	var models []BedrockModel
	allModels := bc.GetAvailableModels()
	
	for _, model := range allModels {
		for _, cap := range model.Capabilities {
			if cap == capability {
				models = append(models, model)
				break
			}
		}
	}
	
	return models
}

// ValidateRequest validates a Bedrock request
func (bc *BedrockClient) ValidateRequest(request BedrockRequest) error {
	if request.ModelID == "" {
		return fmt.Errorf("model ID is required")
	}
	
	if request.Prompt == "" {
		return fmt.Errorf("prompt is required")
	}
	
	// Check if model exists
	_, err := bc.GetModelByID(request.ModelID)
	if err != nil {
		return fmt.Errorf("invalid model ID: %w", err)
	}
	
	// Validate parameters
	if request.MaxTokens < 0 || request.MaxTokens > 8192 {
		return fmt.Errorf("maxTokens must be between 0 and 8192")
	}
	
	if request.Temperature < 0 || request.Temperature > 2 {
		return fmt.Errorf("temperature must be between 0 and 2")
	}
	
	if request.TopP < 0 || request.TopP > 1 {
		return fmt.Errorf("topP must be between 0 and 1")
	}
	
	return nil
}

// ValidateConversationRequest validates a conversation request
func (bc *BedrockClient) ValidateConversationRequest(request ConversationRequest) error {
	if request.ModelID == "" {
		return fmt.Errorf("model ID is required")
	}
	
	if len(request.Messages) == 0 {
		return fmt.Errorf("at least one message is required")
	}
	
	// Check if model exists
	_, err := bc.GetModelByID(request.ModelID)
	if err != nil {
		return fmt.Errorf("invalid model ID: %w", err)
	}
	
	// Validate messages
	for _, msg := range request.Messages {
		if msg.Role != "user" && msg.Role != "assistant" && msg.Role != "system" {
			return fmt.Errorf("invalid role: %s", msg.Role)
		}
		if msg.Content == "" {
			return fmt.Errorf("message content cannot be empty")
		}
	}
	
	// Validate parameters
	if request.MaxTokens < 0 || request.MaxTokens > 8192 {
		return fmt.Errorf("maxTokens must be between 0 and 8192")
	}
	
	if request.Temperature < 0 || request.Temperature > 2 {
		return fmt.Errorf("temperature must be between 0 and 2")
	}
	
	if request.TopP < 0 || request.TopP > 1 {
		return fmt.Errorf("topP must be between 0 and 1")
	}
	
	return nil
}
