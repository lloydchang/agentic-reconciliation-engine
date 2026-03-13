package multimodel

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/lloydchang/ai-agents-sandbox/backend/bedrock"
)

// ModelProvider represents an AI model provider
type ModelProvider string

const (
	ProviderOpenAI     ModelProvider = "openai"
	ProviderAnthropic  ModelProvider = "anthropic"
	ProviderAmazon     ModelProvider = "amazon"
	ProviderCohere     ModelProvider = "cohere"
	ProviderAI21       ModelProvider = "ai21"
	ProviderGoogle     ModelProvider = "google"
)

// ModelCapability represents a model capability
type ModelCapability string

const (
	CapabilityText         ModelCapability = "text"
	CapabilityConversation ModelCapability = "conversation"
	CapabilityAnalysis     ModelCapability = "analysis"
	CapabilityGeneration   ModelCapability = "generation"
	CapabilityTranslation  ModelCapability = "translation"
	CapabilitySummarization ModelCapability = "summarization"
	CapabilityClassification ModelCapability = "classification"
	CapabilityCode         ModelCapability = "code"
	CapabilityMultimodal   ModelCapability = "multimodal"
)

// ModelConfig represents a model configuration
type ModelConfig struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Provider     ModelProvider          `json:"provider"`
	Capabilities []ModelCapability      `json:"capabilities"`
	MaxTokens    int                    `json:"maxTokens"`
	Temperature  float64                `json:"temperature"`
	TopP         float64                `json:"topP"`
	Parameters   map[string]interface{} `json:"parameters"`
	Enabled      bool                   `json:"enabled"`
	Priority     int                    `json:"priority"` // 1=high, 2=medium, 3=low
}

// MultiModelRequest represents a multi-model request
type MultiModelRequest struct {
	Prompt       string                 `json:"prompt"`
	TaskType     string                 `json:"taskType"` // "text", "conversation", "analysis", etc.
	Capabilities []ModelCapability      `json:"capabilities"`
	MaxTokens    int                    `json:"maxTokens,omitempty"`
	Temperature  float64                `json:"temperature,omitempty"`
	TopP         float64                `json:"topP,omitempty"`
	Parameters   map[string]interface{} `json:"parameters,omitempty"`
	Context      map[string]interface{} `json:"context,omitempty"`
	Strategy     SelectionStrategy       `json:"strategy"` // "best", "all", "ensemble"
}

// SelectionStrategy represents model selection strategy
type SelectionStrategy string

const (
	StrategyBest     SelectionStrategy = "best"     // Use the single best model
	StrategyAll      SelectionStrategy = "all"      // Use all available models
	StrategyEnsemble SelectionStrategy = "ensemble" // Combine results from multiple models
)

// MultiModelResponse represents a multi-model response
type MultiModelResponse struct {
	Results      []ModelResult          `json:"results"`
	Strategy     SelectionStrategy       `json:"strategy"`
	ProcessingTime int64                `json:"processingTime"`
	Ensemble     *EnsembleResult         `json:"ensemble,omitempty"`
	SelectedModel string                 `json:"selectedModel,omitempty"`
}

// ModelResult represents a result from a single model
type ModelResult struct {
	ModelID      string                 `json:"modelId"`
	ModelName    string                 `json:"modelName"`
	Provider     ModelProvider          `json:"provider"`
	Response     string                 `json:"response"`
	Confidence   float64                `json:"confidence"`
	Usage        map[string]interface{} `json:"usage"`
	Error        string                 `json:"error,omitempty"`
	ProcessingTime int64                `json:"processingTime"`
}

// EnsembleResult represents combined results from multiple models
type EnsembleResult struct {
	CombinedResponse string                 `json:"combinedResponse"`
	Confidence       float64                `json:"confidence"`
	VotingResults    []VotingResult         `json:"votingResults"`
	Metrics          map[string]interface{} `json:"metrics"`
}

// VotingResult represents a voting result from ensemble
type VotingResult struct {
	ModelID    string  `json:"modelId"`
	Response   string  `json:"response"`
	Votes      int     `json:"votes"`
	Confidence float64 `json:"confidence"`
}

// MultiModelManager manages multiple AI models
type MultiModelManager struct {
	models      map[string]*ModelConfig
	bedrockClient *bedrock.BedrockClient
}

// NewMultiModelManager creates a new multi-model manager
func NewMultiModelManager(bedrockClient *bedrock.BedrockClient) *MultiModelManager {
	manager := &MultiModelManager{
		models:       make(map[string]*ModelConfig),
		bedrockClient: bedrockClient,
	}

	// Initialize default models
	manager.initializeDefaultModels()
	return manager
}

// initializeDefaultModels initializes the default model configurations
func (m *MultiModelManager) initializeDefaultModels() {
	// Bedrock models
	bedrockModels := m.bedrockClient.GetAvailableModels()
	for _, model := range bedrockModels {
		config := &ModelConfig{
			ID:          model.ModelID,
			Name:        model.Name,
			Provider:    mapProviderFromName(model.Provider),
			Capabilities: mapCapabilitiesFromList(model.Capabilities),
			MaxTokens:   model.MaxTokens,
			Temperature: model.Temperature,
			TopP:        model.TopP,
			Parameters:  model.Parameters,
			Enabled:     true,
			Priority:    2, // Medium priority by default
		}
		m.models[model.ModelID] = config
	}

	// Add OpenAI models (mock)
	m.models["gpt-4"] = &ModelConfig{
		ID:          "gpt-4",
		Name:        "GPT-4",
		Provider:    ProviderOpenAI,
		Capabilities: []ModelCapability{CapabilityText, CapabilityConversation, CapabilityAnalysis, CapabilityCode},
		MaxTokens:   4096,
		Temperature: 0.7,
		TopP:        0.9,
		Enabled:     true,
		Priority:    1, // High priority
	}

	m.models["gpt-3.5-turbo"] = &ModelConfig{
		ID:          "gpt-3.5-turbo",
		Name:        "GPT-3.5 Turbo",
		Provider:    ProviderOpenAI,
		Capabilities: []ModelCapability{CapabilityText, CapabilityConversation, CapabilityGeneration},
		MaxTokens:   4096,
		Temperature: 0.7,
		TopP:        0.9,
		Enabled:     true,
		Priority:    2,
	}

	// Add Google models (mock)
	m.models["gemini-pro"] = &ModelConfig{
		ID:          "gemini-pro",
		Name:        "Gemini Pro",
		Provider:    ProviderGoogle,
		Capabilities: []ModelCapability{CapabilityText, CapabilityConversation, CapabilityMultimodal, CapabilityGeneration},
		MaxTokens:   4096,
		Temperature: 0.7,
		TopP:        0.9,
		Enabled:     true,
		Priority:    1,
	}
}

// ProcessRequest processes a multi-model request
func (m *MultiModelManager) ProcessRequest(ctx context.Context, request MultiModelRequest) (*MultiModelResponse, error) {
	start := time.Now()
	
	response := &MultiModelResponse{
		Strategy: request.Strategy,
	}

	// Select models based on strategy and capabilities
	selectedModels := m.selectModels(request)
	
	switch request.Strategy {
	case StrategyBest:
		result, err := m.processWithBestModel(ctx, request, selectedModels)
		if err != nil {
			return nil, err
		}
		response.Results = []ModelResult{*result}
		response.SelectedModel = result.ModelID

	case StrategyAll:
		results, err := m.processWithAllModels(ctx, request, selectedModels)
		if err != nil {
			return nil, err
		}
		response.Results = results

	case StrategyEnsemble:
		results, err := m.processWithAllModels(ctx, request, selectedModels)
		if err != nil {
			return nil, err
		}
		response.Results = results
		
		// Create ensemble result
		ensemble := m.createEnsembleResult(results)
		response.Ensemble = ensemble
	}

	response.ProcessingTime = time.Since(start).Milliseconds()
	return response, nil
}

// selectModels selects models based on request criteria
func (m *MultiModelManager) selectModels(request MultiModelRequest) []*ModelConfig {
	var selectedModels []*ModelConfig

	for _, model := range m.models {
		if !model.Enabled {
			continue
		}

		// Check capabilities
		if !m.hasRequiredCapabilities(model, request.Capabilities) {
			continue
		}

		// Check task type
		if !m.supportsTaskType(model, request.TaskType) {
			continue
		}

		selectedModels = append(selectedModels, model)
	}

	// Sort by priority
	m.sortModelsByPriority(selectedModels)

	return selectedModels
}

// processWithBestModel processes request with the best available model
func (m *MultiModelManager) processWithBestModel(ctx context.Context, request MultiModelRequest, models []*ModelConfig) (*ModelResult, error) {
	if len(models) == 0 {
		return nil, fmt.Errorf("no models available for request")
	}

	bestModel := models[0] // Already sorted by priority
	return m.processWithModel(ctx, request, bestModel)
}

// processWithAllModels processes request with all available models
func (m *MultiModelManager) processWithAllModels(ctx context.Context, request MultiModelRequest, models []*ModelConfig) ([]ModelResult, error) {
	var results []ModelResult

	for _, model := range models {
		result, err := m.processWithModel(ctx, request, model)
		if err != nil {
			// Create error result
			results = append(results, ModelResult{
				ModelID: model.ID,
				ModelName: model.Name,
				Provider: model.Provider,
				Error: err.Error(),
			})
			continue
		}
		results = append(results, *result)
	}

	return results, nil
}

// processWithModel processes request with a specific model
func (m *MultiModelManager) processWithModel(ctx context.Context, request MultiModelRequest, model *ModelConfig) (*ModelResult, error) {
	start := time.Now()



	// Process based on provider
	switch model.Provider {
	case ProviderAnthropic, ProviderAmazon, ProviderCohere, ProviderAI21:
		return m.processWithBedrock(ctx, request, model, start)
	case ProviderOpenAI:
		return m.processWithOpenAI(ctx, request, model, start)
	case ProviderGoogle:
		return m.processWithGoogle(ctx, request, model, start)
	default:
		return nil, fmt.Errorf("unsupported provider: %s", model.Provider)
	}
}

// processWithBedrock processes request with Bedrock model
func (m *MultiModelManager) processWithBedrock(ctx context.Context, request MultiModelRequest, model *ModelConfig, start time.Time) (*ModelResult, error) {
	bedrockRequest := bedrock.BedrockRequest{
		ModelID:     model.ID,
		Prompt:      request.Prompt,
		MaxTokens:   request.MaxTokens,
		Temperature: request.Temperature,
		TopP:        request.TopP,
		Parameters:  request.Parameters,
	}

	response, err := m.bedrockClient.InvokeModel(ctx, bedrockRequest)
	if err != nil {
		return nil, fmt.Errorf("Bedrock invocation failed: %w", err)
	}

	return &ModelResult{
		ModelID:        model.ID,
		ModelName:      model.Name,
		Provider:       model.Provider,
		Response:       response.Completion,
		Confidence:     0.85, // Mock confidence
		Usage:          response.Usage,
		ProcessingTime: time.Since(start).Milliseconds(),
	}, nil
}

// processWithOpenAI processes request with OpenAI model (mock)
func (m *MultiModelManager) processWithOpenAI(ctx context.Context, request MultiModelRequest, model *ModelConfig, start time.Time) (*ModelResult, error) {
	// Mock OpenAI processing
	time.Sleep(time.Millisecond * 300) // Simulate API call

	response := fmt.Sprintf("OpenAI %s response to: %s", model.Name, request.Prompt)

	return &ModelResult{
		ModelID:        model.ID,
		ModelName:      model.Name,
		Provider:       model.Provider,
		Response:       response,
		Confidence:     0.9, // Mock confidence
		Usage:          map[string]interface{}{"prompt_tokens": 100, "completion_tokens": 50},
		ProcessingTime: time.Since(start).Milliseconds(),
	}, nil
}

// processWithGoogle processes request with Google model (mock)
func (m *MultiModelManager) processWithGoogle(ctx context.Context, request MultiModelRequest, model *ModelConfig, start time.Time) (*ModelResult, error) {
	// Mock Google processing
	time.Sleep(time.Millisecond * 250) // Simulate API call

	response := fmt.Sprintf("Google %s response to: %s", model.Name, request.Prompt)

	return &ModelResult{
		ModelID:        model.ID,
		ModelName:      model.Name,
		Provider:       model.Provider,
		Response:       response,
		Confidence:     0.88, // Mock confidence
		Usage:          map[string]interface{}{"prompt_tokens": 90, "completion_tokens": 45},
		ProcessingTime: time.Since(start).Milliseconds(),
	}, nil
}

// createEnsembleResult creates an ensemble result from multiple model results
func (m *MultiModelManager) createEnsembleResult(results []ModelResult) *EnsembleResult {
	if len(results) == 0 {
		return nil
	}

	// Simple ensemble: combine responses and calculate confidence
	var combinedResponse strings.Builder
	var totalConfidence float64
	var validResults []ModelResult

	for _, result := range results {
		if result.Error == "" {
			combinedResponse.WriteString(fmt.Sprintf("[%s]: %s\n", result.ModelName, result.Response))
			totalConfidence += result.Confidence
			validResults = append(validResults, result)
		}
	}

	avgConfidence := totalConfidence / float64(len(validResults))

	// Create voting results
	votingResults := make([]VotingResult, len(validResults))
	for i, result := range validResults {
		votingResults[i] = VotingResult{
			ModelID:    result.ModelID,
			Response:   result.Response,
			Votes:      1, // Simple voting
			Confidence: result.Confidence,
		}
	}

	return &EnsembleResult{
		CombinedResponse: combinedResponse.String(),
		Confidence:       avgConfidence,
		VotingResults:    votingResults,
		Metrics: map[string]interface{}{
			"totalModels":    len(results),
			"validModels":    len(validResults),
			"avgConfidence":  avgConfidence,
		},
	}
}

// GetAvailableModels returns all available models
func (m *MultiModelManager) GetAvailableModels() []*ModelConfig {
	var models []*ModelConfig
	for _, model := range m.models {
		models = append(models, model)
	}
	return models
}

// GetModelsByProvider returns models filtered by provider
func (m *MultiModelManager) GetModelsByProvider(provider ModelProvider) []*ModelConfig {
	var models []*ModelConfig
	for _, model := range m.models {
		if model.Provider == provider {
			models = append(models, model)
		}
	}
	return models
}

// GetModelsByCapability returns models filtered by capability
func (m *MultiModelManager) GetModelsByCapability(capability ModelCapability) []*ModelConfig {
	var models []*ModelConfig
	for _, model := range m.models {
		if m.hasCapability(model, capability) {
			models = append(models, model)
		}
	}
	return models
}

// Helper functions

func mapProviderFromName(providerName string) ModelProvider {
	switch strings.ToLower(providerName) {
	case "anthropic":
		return ProviderAnthropic
	case "amazon":
		return ProviderAmazon
	case "cohere":
		return ProviderCohere
	case "ai21":
		return ProviderAI21
	default:
		return ModelProvider(providerName)
	}
}

func mapCapabilitiesFromList(capabilities []string) []ModelCapability {
	var result []ModelCapability
	for _, cap := range capabilities {
		result = append(result, ModelCapability(cap))
	}
	return result
}

func (m *MultiModelManager) hasRequiredCapabilities(model *ModelConfig, required []ModelCapability) bool {
	if len(required) == 0 {
		return true
	}

	for _, reqCap := range required {
		if !m.hasCapability(model, reqCap) {
			return false
		}
	}
	return true
}

func (m *MultiModelManager) hasCapability(model *ModelConfig, capability ModelCapability) bool {
	for _, cap := range model.Capabilities {
		if cap == capability {
			return true
		}
	}
	return false
}

func (m *MultiModelManager) supportsTaskType(model *ModelConfig, taskType string) bool {
	// Simple task type mapping
	switch taskType {
	case "text", "generation":
		return m.hasCapability(model, CapabilityText) || m.hasCapability(model, CapabilityGeneration)
	case "conversation":
		return m.hasCapability(model, CapabilityConversation)
	case "analysis":
		return m.hasCapability(model, CapabilityAnalysis)
	case "translation":
		return m.hasCapability(model, CapabilityTranslation)
	case "summarization":
		return m.hasCapability(model, CapabilitySummarization)
	case "classification":
		return m.hasCapability(model, CapabilityClassification)
	case "code":
		return m.hasCapability(model, CapabilityCode)
	case "multimodal":
		return m.hasCapability(model, CapabilityMultimodal)
	default:
		return true // Allow unknown task types
	}
}

func (m *MultiModelManager) sortModelsByPriority(models []*ModelConfig) {
	for i := 0; i < len(models)-1; i++ {
		for j := 0; j < len(models)-i-1; j++ {
			if models[j].Priority > models[j+1].Priority {
				models[j], models[j+1] = models[j+1], models[j]
			}
		}
	}
}

// EnableModel enables a model
func (m *MultiModelManager) EnableModel(modelID string) error {
	if model, exists := m.models[modelID]; exists {
		model.Enabled = true
		return nil
	}
	return fmt.Errorf("model not found: %s", modelID)
}

// DisableModel disables a model
func (m *MultiModelManager) DisableModel(modelID string) error {
	if model, exists := m.models[modelID]; exists {
		model.Enabled = false
		return nil
	}
	return fmt.Errorf("model not found: %s", modelID)
}

// UpdateModelPriority updates a model's priority
func (m *MultiModelManager) UpdateModelPriority(modelID string, priority int) error {
	if model, exists := m.models[modelID]; exists {
		model.Priority = priority
		return nil
	}
	return fmt.Errorf("model not found: %s", modelID)
}
