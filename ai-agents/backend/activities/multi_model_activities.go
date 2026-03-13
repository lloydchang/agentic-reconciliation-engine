package activities

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/multimodel"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// MultiModelActivities provides activities for multi-model AI operations
type MultiModelActivities struct {
	manager *multimodel.MultiModelManager
}

// NewMultiModelActivities creates new multi-model activities
func NewMultiModelActivities(manager *multimodel.MultiModelManager) *MultiModelActivities {
	return &MultiModelActivities{
		manager: manager,
	}
}

// ProcessMultiModelRequestActivity processes a multi-model request
func (mma *MultiModelActivities) ProcessMultiModelRequestActivity(ctx context.Context, request multimodel.MultiModelRequest) (*multimodel.MultiModelResponse, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Processing multi-model request", "strategy", request.Strategy, "taskType", request.TaskType, "capabilities", len(request.Capabilities))

	response, err := mma.manager.ProcessRequest(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to process multi-model request: %w", err)
	}

	logger.Info("Multi-model request processed", "results", len(response.Results), "strategy", response.Strategy, "processingTime", response.ProcessingTime)
	return response, nil
}

// GetAvailableModelsActivity returns available models
func (mma *MultiModelActivities) GetAvailableModelsActivity(ctx context.Context) ([]*multimodel.ModelConfig, error) {
	logger := activity.GetLogger(ctx)

	models := mma.manager.GetAvailableModels()

	logger.Info("Retrieved available models", "count", len(models))
	return models, nil
}

// GetModelsByProviderActivity returns models by provider
func (mma *MultiModelActivities) GetModelsByProviderActivity(ctx context.Context, provider multimodel.ModelProvider) ([]*multimodel.ModelConfig, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting models by provider", "provider", provider)

	models := mma.manager.GetModelsByProvider(provider)

	logger.Info("Retrieved models by provider", "provider", provider, "count", len(models))
	return models, nil
}

// GetModelsByCapabilityActivity returns models by capability
func (mma *MultiModelActivities) GetModelsByCapabilityActivity(ctx context.Context, capability multimodel.ModelCapability) ([]*multimodel.ModelConfig, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting models by capability", "capability", capability)

	models := mma.manager.GetModelsByCapability(capability)

	logger.Info("Retrieved models by capability", "capability", capability, "count", len(models))
	return models, nil
}

// CompareMultiModelsActivity compares multiple models on the same task
func (mma *MultiModelActivities) CompareMultiModelsActivity(ctx context.Context, prompt string, modelIDs []string, strategy multimodel.SelectionStrategy) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Comparing models", "models", len(modelIDs), "strategy", strategy)

	request := multimodel.MultiModelRequest{
		Prompt:   prompt,
		Strategy: strategy,
	}

	response, err := mma.manager.ProcessRequest(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to compare models: %w", err)
	}

	comparison := map[string]interface{}{
		"prompt":          prompt,
		"strategy":        strategy,
		"results":         response.Results,
		"processingTime":  response.ProcessingTime,
		"ensemble":        response.Ensemble,
		"timestamp":       time.Now().Format(time.RFC3339),
	}

	logger.Info("Model comparison completed", "results", len(response.Results))
	return comparison, nil
}

// EnsembleModelsActivity creates an ensemble result from multiple models
func (mma *MultiModelActivities) EnsembleModelsActivity(ctx context.Context, prompt string, modelIDs []string) (*multimodel.EnsembleResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Creating ensemble", "models", len(modelIDs), "promptLength", len(prompt))

	request := multimodel.MultiModelRequest{
		Prompt:   prompt,
		Strategy: multimodel.StrategyEnsemble,
	}

	response, err := mma.manager.ProcessRequest(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to create ensemble: %w", err)
	}

	if response.Ensemble == nil {
		return nil, fmt.Errorf("no ensemble result generated")
	}

	logger.Info("Ensemble created", "confidence", response.Ensemble.Confidence, "votingResults", len(response.Ensemble.VotingResults))
	return response.Ensemble, nil
}

// SelectBestModelActivity selects the best model for a task
func (mma *MultiModelActivities) SelectBestModelActivity(ctx context.Context, taskType string, capabilities []multimodel.ModelCapability) (*multimodel.ModelConfig, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Selecting best model", "taskType", taskType, "capabilities", len(capabilities))

	request := multimodel.MultiModelRequest{
		TaskType:     taskType,
		Capabilities: capabilities,
		Strategy:     multimodel.StrategyBest,
	}

	response, err := mma.manager.ProcessRequest(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to select best model: %w", err)
	}

	if len(response.Results) == 0 {
		return nil, fmt.Errorf("no models available for task")
	}

	bestResult := response.Results[0]
	bestModel := &multimodel.ModelConfig{
		ID:   bestResult.ModelID,
		Name: bestResult.ModelName,
	}

	logger.Info("Best model selected", "modelId", bestModel.ID, "modelName", bestModel.Name)
	return bestModel, nil
}

// ValidateMultiModelRequestActivity validates a multi-model request
func (mma *MultiModelActivities) ValidateMultiModelRequestActivity(ctx context.Context, request multimodel.MultiModelRequest) (*types.ValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating multi-model request", "strategy", request.Strategy)

	var errors []string
	isValid := true

	// Validate strategy
	validStrategies := []multimodel.SelectionStrategy{
		multimodel.StrategyBest,
		multimodel.StrategyAll,
		multimodel.StrategyEnsemble,
	}

	validStrategy := false
	for _, strategy := range validStrategies {
		if request.Strategy == strategy {
			validStrategy = true
			break
		}
	}

	if !validStrategy {
		errors = append(errors, fmt.Sprintf("invalid strategy: %s", request.Strategy))
		isValid = false
	}

	// Validate prompt
	if request.Prompt == "" {
		errors = append(errors, "prompt is required")
		isValid = false
	}

	// Check if models are available for the request
	availableModels := mma.manager.GetAvailableModels()
	var selectedModels []*multimodel.ModelConfig
	for _, model := range availableModels {
		if model.Enabled {
			// Check capabilities
			hasCapabilities := true
			for _, reqCap := range request.Capabilities {
				hasCap := false
				for _, modelCap := range model.Capabilities {
					if modelCap == reqCap {
						hasCap = true
						break
					}
				}
				if !hasCap {
					hasCapabilities = false
					break
				}
			}
			if hasCapabilities {
				selectedModels = append(selectedModels, model)
			}
		}
	}

	if len(selectedModels) == 0 {
		errors = append(errors, "no models available for the specified requirements")
		isValid = false
	}

	logger.Info("Multi-model request validation completed", "valid", isValid, "errors", len(errors), "availableModels", len(selectedModels))
	return &types.ValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}

// GetModelStatisticsActivity returns statistics about available models
func (mma *MultiModelActivities) GetModelStatisticsActivity(ctx context.Context) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)

	models := mma.manager.GetAvailableModels()

	stats := map[string]interface{}{
		"totalModels": len(models),
		"enabledModels": 0,
		"disabledModels": 0,
		"providers": make(map[string]int),
		"capabilities": make(map[string]int),
		"priorityDistribution": map[string]int{
			"high":   0,
			"medium": 0,
			"low":    0,
		},
	}

	for _, model := range models {
		if model.Enabled {
			stats["enabledModels"] = stats["enabledModels"].(int) + 1
		} else {
			stats["disabledModels"] = stats["disabledModels"].(int) + 1
		}

		// Count providers
		providerCount := stats["providers"].(map[string]int)
		providerCount[string(model.Provider)] = providerCount[string(model.Provider)] + 1

		// Count capabilities
		capCount := stats["capabilities"].(map[string]int)
		for _, cap := range model.Capabilities {
			capCount[string(cap)] = capCount[string(cap)] + 1
		}

		// Count priorities
		priorityDist := stats["priorityDistribution"].(map[string]int)
		switch model.Priority {
		case 1:
			priorityDist["high"] = priorityDist["high"] + 1
		case 2:
			priorityDist["medium"] = priorityDist["medium"] + 1
		case 3:
			priorityDist["low"] = priorityDist["low"] + 1
		}
	}

	logger.Info("Model statistics generated", "totalModels", stats["totalModels"])
	return stats, nil
}

// EnableModelActivity enables a model
func (mma *MultiModelActivities) EnableModelActivity(ctx context.Context, modelID string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Enabling model", "modelId", modelID)

	err := mma.manager.EnableModel(modelID)
	if err != nil {
		return fmt.Errorf("failed to enable model: %w", err)
	}

	logger.Info("Model enabled successfully", "modelId", modelID)
	return nil
}

// DisableModelActivity disables a model
func (mma *MultiModelActivities) DisableModelActivity(ctx context.Context, modelID string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Disabling model", "modelId", modelID)

	err := mma.manager.DisableModel(modelID)
	if err != nil {
		return fmt.Errorf("failed to disable model: %w", err)
	}

	logger.Info("Model disabled successfully", "modelId", modelID)
	return nil
}

// UpdateModelPriorityActivity updates a model's priority
func (mma *MultiModelActivities) UpdateModelPriorityActivity(ctx context.Context, modelID string, priority int) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Updating model priority", "modelId", modelID, "priority", priority)

	err := mma.manager.UpdateModelPriority(modelID, priority)
	if err != nil {
		return fmt.Errorf("failed to update model priority: %w", err)
	}

	logger.Info("Model priority updated successfully", "modelId", modelID, "priority", priority)
	return nil
}

// BenchmarkModelsActivity benchmarks multiple models
func (mma *MultiModelActivities) BenchmarkModelsActivity(ctx context.Context, prompts []string, modelIDs []string) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Benchmarking models", "prompts", len(prompts), "models", len(modelIDs))

	benchmark := map[string]interface{}{
		"prompts": prompts,
		"models":  modelIDs,
		"results": make(map[string]interface{}),
		"timestamp": time.Now().Format(time.RFC3339),
	}

	modelResults := benchmark["results"].(map[string]interface{})

	for _, modelID := range modelIDs {
		modelBenchmark := map[string]interface{}{
			"totalProcessingTime": int64(0),
			"averageConfidence":  0.0,
			"successCount":       0,
			"errorCount":         0,
			"promptResults":      make([]map[string]interface{}, 0),
		}

		for _, prompt := range prompts {
			request := multimodel.MultiModelRequest{
				Prompt:   prompt,
				Strategy: multimodel.StrategyBest,
				Parameters: map[string]interface{}{
					"model_id": modelID,
				},
			}

			response, err := mma.manager.ProcessRequest(ctx, request)
			if err != nil {
				modelBenchmark["errorCount"] = modelBenchmark["errorCount"].(int) + 1
				continue
			}

			if len(response.Results) > 0 {
				result := response.Results[0]
				modelBenchmark["totalProcessingTime"] = modelBenchmark["totalProcessingTime"].(int64) + result.ProcessingTime
				modelBenchmark["averageConfidence"] = modelBenchmark["averageConfidence"].(float64) + result.Confidence
				modelBenchmark["successCount"] = modelBenchmark["successCount"].(int) + 1

				promptResult := map[string]interface{}{
					"prompt":          prompt,
					"response":        result.Response,
					"confidence":       result.Confidence,
					"processingTime":   result.ProcessingTime,
				}
				modelBenchmark["promptResults"] = append(modelBenchmark["promptResults"].([]map[string]interface{}), promptResult)
			}
		}

		// Calculate averages
		if modelBenchmark["successCount"].(int) > 0 {
			modelBenchmark["averageConfidence"] = modelBenchmark["averageConfidence"].(float64) / float64(modelBenchmark["successCount"].(int))
			modelBenchmark["averageProcessingTime"] = modelBenchmark["totalProcessingTime"].(int64) / int64(modelBenchmark["successCount"].(int))
		}

		modelResults[modelID] = modelBenchmark
	}

	logger.Info("Model benchmark completed", "models", len(modelResults))
	return benchmark, nil
}

// GetModelRecommendationsActivity gets model recommendations for a task
func (mma *MultiModelActivities) GetModelRecommendationsActivity(ctx context.Context, taskType string, capabilities []multimodel.ModelCapability, maxRecommendations int) ([]*multimodel.ModelConfig, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Getting model recommendations", "taskType", taskType, "capabilities", len(capabilities), "max", maxRecommendations)


	selectedModels := mma.manager.GetAvailableModels()
	var recommendedModels []*multimodel.ModelConfig
	for _, model := range selectedModels {
		if model.Enabled {
			// Check capabilities
			hasCapabilities := true
			for _, reqCap := range capabilities {
				hasCap := false
				for _, modelCap := range model.Capabilities {
					if modelCap == reqCap {
						hasCap = true
						break
					}
				}
				if !hasCap {
					hasCapabilities = false
					break
				}
			}
			if hasCapabilities {
				recommendedModels = append(recommendedModels, model)
			}
		}
	}
	
	// Sort by priority
	for i := 0; i < len(recommendedModels)-1; i++ {
		for j := 0; j < len(recommendedModels)-i-1; j++ {
			if recommendedModels[j].Priority > recommendedModels[j+1].Priority {
				recommendedModels[j], recommendedModels[j+1] = recommendedModels[j+1], recommendedModels[j]
			}
		}
	}
	
	// Limit to maxRecommendations
	if len(recommendedModels) > maxRecommendations {
		recommendedModels = recommendedModels[:maxRecommendations]
	}

	logger.Info("Model recommendations generated", "recommendations", len(recommendedModels))
	return recommendedModels, nil
}
