package activities

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/bedrock"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// BedrockActivities provides activities for AWS Bedrock integration
type BedrockActivities struct {
	client *bedrock.BedrockClient
}

// NewBedrockActivities creates new Bedrock activities
func NewBedrockActivities(region string) (*BedrockActivities, error) {
	client, err := bedrock.NewBedrockClient(region)
	if err != nil {
		return nil, fmt.Errorf("failed to create Bedrock client: %w", err)
	}

	return &BedrockActivities{
		client: client,
	}, nil
}

// GenerateTextWithBedrockActivity generates text using Bedrock
func (ba *BedrockActivities) GenerateTextWithBedrockActivity(ctx context.Context, prompt string, modelID string, maxTokens int, temperature float64) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating text with Bedrock", "model", modelID, "promptLength", len(prompt))

	request := bedrock.BedrockRequest{
		ModelID:     modelID,
		Prompt:      prompt,
		MaxTokens:   maxTokens,
		Temperature: temperature,
	}

	response, err := ba.client.InvokeModel(ctx, request)
	if err != nil {
		return "", fmt.Errorf("failed to invoke Bedrock model: %w", err)
	}

	logger.Info("Text generated with Bedrock", "completionLength", len(response.Completion), "processingTime", response.ProcessingTime)
	return response.Completion, nil
}

// ConductConversationWithBedrockActivity conducts a conversation using Bedrock
func (ba *BedrockActivities) ConductConversationWithBedrockActivity(ctx context.Context, messages []bedrock.ConversationMessage, modelID string, systemPrompt string, maxTokens int, temperature float64) ([]bedrock.ConversationMessage, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Conducting conversation with Bedrock", "model", modelID, "messageCount", len(messages))

	request := bedrock.ConversationRequest{
		ModelID:      modelID,
		Messages:     messages,
		SystemPrompt: systemPrompt,
		MaxTokens:    maxTokens,
		Temperature:  temperature,
	}

	response, err := ba.client.InvokeConversation(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to invoke Bedrock conversation: %w", err)
	}

	logger.Info("Conversation conducted with Bedrock", "responseLength", len(response.Messages[len(response.Messages)-1].Content), "processingTime", response.ProcessingTime)
	return response.Messages, nil
}

// AnalyzeWithBedrockActivity analyzes text using Bedrock
func (ba *BedrockActivities) AnalyzeWithBedrockActivity(ctx context.Context, text string, analysisType string, modelID string) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing text with Bedrock", "model", modelID, "analysisType", analysisType, "textLength", len(text))

	// Build analysis prompt based on type
	prompt := ba.buildAnalysisPrompt(text, analysisType)

	request := bedrock.BedrockRequest{
		ModelID:     modelID,
		Prompt:      prompt,
		MaxTokens:   1000,
		Temperature: 0.3, // Lower temperature for analysis
	}

	response, err := ba.client.InvokeModel(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to invoke Bedrock for analysis: %w", err)
	}

	// Parse analysis response (simplified)
	analysis := map[string]interface{}{
		"type":        analysisType,
		"model":       modelID,
		"result":      response.Completion,
		"confidence":  0.85, // Mock confidence
		"processedAt": time.Now().Format(time.RFC3339),
		"usage":       response.Usage,
	}

	logger.Info("Text analyzed with Bedrock", "analysisType", analysisType)
	return analysis, nil
}

// SummarizeWithBedrockActivity summarizes text using Bedrock
func (ba *BedrockActivities) SummarizeWithBedrockActivity(ctx context.Context, text string, summaryLength string, modelID string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Summarizing text with Bedrock", "model", modelID, "summaryLength", summaryLength, "textLength", len(text))

	prompt := ba.buildSummaryPrompt(text, summaryLength)

	request := bedrock.BedrockRequest{
		ModelID:     modelID,
		Prompt:      prompt,
		MaxTokens:    500,
		Temperature: 0.5,
	}

	response, err := ba.client.InvokeModel(ctx, request)
	if err != nil {
		return "", fmt.Errorf("failed to invoke Bedrock for summarization: %w", err)
	}

	logger.Info("Text summarized with Bedrock", "summaryLength", len(response.Completion))
	return response.Completion, nil
}

// TranslateWithBedrockActivity translates text using Bedrock
func (ba *BedrockActivities) TranslateWithBedrockActivity(ctx context.Context, text string, sourceLanguage string, targetLanguage string, modelID string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Translating text with Bedrock", "model", modelID, "source", sourceLanguage, "target", targetLanguage)

	prompt := ba.buildTranslationPrompt(text, sourceLanguage, targetLanguage)

	request := bedrock.BedrockRequest{
		ModelID:     modelID,
		Prompt:      prompt,
		MaxTokens:   1000,
		Temperature: 0.3,
	}

	response, err := ba.client.InvokeModel(ctx, request)
	if err != nil {
		return "", fmt.Errorf("failed to invoke Bedrock for translation: %w", err)
	}

	logger.Info("Text translated with Bedrock", "translationLength", len(response.Completion))
	return response.Completion, nil
}

// ClassifyWithBedrockActivity classifies text using Bedrock
func (ba *BedrockActivities) ClassifyWithBedrockActivity(ctx context.Context, text string, categories []string, modelID string) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Classifying text with Bedrock", "model", modelID, "categories", len(categories), "textLength", len(text))

	prompt := ba.buildClassificationPrompt(text, categories)

	request := bedrock.BedrockRequest{
		ModelID:     modelID,
		Prompt:      prompt,
		MaxTokens:   300,
		Temperature: 0.2, // Low temperature for classification
	}

	response, err := ba.client.InvokeModel(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to invoke Bedrock for classification: %w", err)
	}

	// Parse classification response (simplified)
	classification := map[string]interface{}{
		"predictedCategory": response.Completion,
		"categories":        categories,
		"model":             modelID,
		"confidence":        0.9, // Mock confidence
		"processedAt":       time.Now().Format(time.RFC3339),
	}

	logger.Info("Text classified with Bedrock", "predicted", response.Completion)
	return classification, nil
}

// GetBedrockModelsActivity gets available Bedrock models
func (ba *BedrockActivities) GetBedrockModelsActivity(ctx context.Context) ([]bedrock.BedrockModel, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting available Bedrock models")

	models := ba.client.GetAvailableModels()

	logger.Info("Retrieved Bedrock models", "count", len(models))
	return models, nil
}

// ValidateBedrockRequestActivity validates a Bedrock request
func (ba *BedrockActivities) ValidateBedrockRequestActivity(ctx context.Context, request bedrock.BedrockRequest) (*types.ValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating Bedrock request", "model", request.ModelID)

	err := ba.client.ValidateRequest(request)
	isValid := err == nil
	var errors []string

	if err != nil {
		errors = []string{err.Error()}
	}

	logger.Info("Bedrock request validation completed", "valid", isValid, "errors", len(errors))
	return &types.ValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}

// ValidateBedrockConversationActivity validates a Bedrock conversation request
func (ba *BedrockActivities) ValidateBedrockConversationActivity(ctx context.Context, request bedrock.ConversationRequest) (*types.ValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating Bedrock conversation request", "model", request.ModelID, "messages", len(request.Messages))

	err := ba.client.ValidateConversationRequest(request)
	isValid := err == nil
	var errors []string

	if err != nil {
		errors = []string{err.Error()}
	}

	logger.Info("Bedrock conversation validation completed", "valid", isValid, "errors", len(errors))
	return &types.ValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}

// CompareBedrockModelsActivity compares multiple Bedrock models
func (ba *BedrockActivities) CompareBedrockModelsActivity(ctx context.Context, prompt string, modelIDs []string) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Comparing Bedrock models", "models", len(modelIDs), "promptLength", len(prompt))

	comparison := map[string]interface{}{
		"prompt":    prompt,
		"models":    make(map[string]interface{}),
		"timestamp": time.Now().Format(time.RFC3339),
	}

	modelResults := comparison["models"].(map[string]interface{})

	for _, modelID := range modelIDs {
		request := bedrock.BedrockRequest{
			ModelID:     modelID,
			Prompt:      prompt,
			MaxTokens:   500,
			Temperature: 0.7,
		}

		response, err := ba.client.InvokeModel(ctx, request)
		if err != nil {
			logger.Warn("Failed to invoke model for comparison", "model", modelID, "error", err)
			modelResults[modelID] = map[string]interface{}{
				"error": err.Error(),
			}
			continue
		}

		modelResults[modelID] = map[string]interface{}{
			"completion":     response.Completion,
			"usage":          response.Usage,
			"processingTime": response.ProcessingTime,
			"finishReason":   response.FinishReason,
		}
	}

	logger.Info("Bedrock model comparison completed", "models", len(modelResults))
	return comparison, nil
}

// Helper methods for building prompts

func (ba *BedrockActivities) buildAnalysisPrompt(text string, analysisType string) string {
	switch analysisType {
	case "sentiment":
		return fmt.Sprintf("Analyze the sentiment of the following text. Respond with 'positive', 'negative', or 'neutral' and provide a brief explanation:\n\n%s", text)
	case "keywords":
		return fmt.Sprintf("Extract the main keywords from the following text. Provide them as a comma-separated list:\n\n%s", text)
	case "entities":
		return fmt.Sprintf("Identify the named entities (people, organizations, locations) in the following text:\n\n%s", text)
	case "topics":
		return fmt.Sprintf("Identify the main topics in the following text. Provide them as a comma-separated list:\n\n%s", text)
	default:
		return fmt.Sprintf("Analyze the following text and provide insights:\n\n%s", text)
	}
}

func (ba *BedrockActivities) buildSummaryPrompt(text string, summaryLength string) string {
	switch summaryLength {
	case "short":
		return fmt.Sprintf("Provide a brief summary (2-3 sentences) of the following text:\n\n%s", text)
	case "medium":
		return fmt.Sprintf("Provide a medium-length summary (1 paragraph) of the following text:\n\n%s", text)
	case "long":
		return fmt.Sprintf("Provide a detailed summary (2-3 paragraphs) of the following text:\n\n%s", text)
	default:
		return fmt.Sprintf("Summarize the following text:\n\n%s", text)
	}
}

func (ba *BedrockActivities) buildTranslationPrompt(text string, sourceLanguage string, targetLanguage string) string {
	return fmt.Sprintf("Translate the following text from %s to %s. Provide only the translation without additional commentary:\n\n%s", sourceLanguage, targetLanguage, text)
}

func (ba *BedrockActivities) buildClassificationPrompt(text string, categories []string) string {
	categoriesStr := fmt.Sprintf("%v", categories)
	return fmt.Sprintf("Classify the following text into one of these categories: %s. Respond with only the category name:\n\n%s", categoriesStr, text)
}
