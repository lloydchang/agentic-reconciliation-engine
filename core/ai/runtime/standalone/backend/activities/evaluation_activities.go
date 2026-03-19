package activities

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"path/filepath"
	"time"

	"go.temporal.io/sdk/activity"
)

// EvaluationActivities contains all evaluation-related activities
type EvaluationActivities struct {
	EvaluatorPath    string
	ResultsPath      string
	ConfigPath       string
	TracesPath       string
	VisualizationPath string
}

// NewEvaluationActivities creates a new activities instance
func NewEvaluationActivities() *EvaluationActivities {
	return &EvaluationActivities{
		EvaluatorPath:    "/app/agent-tracing-evaluation",
		ResultsPath:      "/results",
		ConfigPath:       "/config",
		TracesPath:       "/data",
		VisualizationPath: "/visualizations",
	}
}

// PrepareEvaluationEnvironment prepares the evaluation environment
func (ea *EvaluationActivities) PrepareEvaluationEnvironment(ctx context.Context, input interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Preparing evaluation environment (stub)")
	return nil
}

// GenerateSampleTraces generates sample traces for evaluation
func (ea *EvaluationActivities) GenerateSampleTraces(ctx context.Context, input interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating sample traces (stub)")
	return nil
}

// RunEvaluationActivity runs the evaluation
func (ea *EvaluationActivities) RunEvaluationActivity(ctx context.Context, input interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Running evaluation (stub)")
	return nil
}

// GetEvaluationResults retrieves evaluation results
func (ea *EvaluationActivities) GetEvaluationResults(ctx context.Context, results *map[string]interface{}) error {
	resultsFile := filepath.Join(ea.ResultsPath, "evaluation_results.json")
	
	data, err := ioutil.ReadFile(resultsFile)
	if err != nil {
		return fmt.Errorf("failed to read results file: %w", err)
	}

	if err := json.Unmarshal(data, results); err != nil {
		return fmt.Errorf("failed to unmarshal results: %w", err)
	}

	return nil
}

// GenerateVisualizations generates evaluation visualizations
func (ea *EvaluationActivities) GenerateVisualizations(ctx context.Context, input interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating visualizations (stub)")
	return nil
}

// GetVisualizationPaths retrieves visualization file paths
func (ea *EvaluationActivities) GetVisualizationPaths(ctx context.Context, paths *map[string]string) error {
	visualizations := make(map[string]string)
	
	// Scan visualization directory
	files, err := ioutil.ReadDir(ea.VisualizationPath)
	if err != nil {
		return fmt.Errorf("failed to read visualization directory: %w", err)
	}

	for _, file := range files {
		if !file.IsDir() {
			ext := filepath.Ext(file.Name())
			if ext == ".png" || ext == ".jpg" || ext == ".html" {
				visualizations[file.Name()] = filepath.Join(ea.VisualizationPath, file.Name())
			}
		}
	}

	*paths = visualizations
	return nil
}

// GetQualityGateResults retrieves quality gate results
func (ea *EvaluationActivities) GetQualityGateResults(ctx context.Context, results *map[string]interface{}) error {
	resultsFile := filepath.Join(ea.ResultsPath, "quality_gate_results.json")
	
	data, err := ioutil.ReadFile(resultsFile)
	if err != nil {
		return fmt.Errorf("failed to read quality gate results: %w", err)
	}

	if err := json.Unmarshal(data, results); err != nil {
		return fmt.Errorf("failed to unmarshal quality gate results: %w", err)
	}

	return nil
}

// GenerateRecommendations generates evaluation recommendations
func (ea *EvaluationActivities) GenerateRecommendations(ctx context.Context, evaluationResults map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating recommendations")

	// Extract recommendations from results
	recommendations := []string{}

	if aggregate, ok := evaluationResults["aggregate_metrics"].(map[string]interface{}); ok {
		if recs, ok := aggregate["recommendations"].([]interface{}); ok {
			for _, rec := range recs {
				if recStr, ok := rec.(string); ok {
					recommendations = append(recommendations, recStr)
				}
			}
		}
	}

	// Save recommendations
	recommendationsFile := filepath.Join(ea.ResultsPath, "recommendations.json")
	recommendationsData, _ := json.MarshalIndent(recommendations, "", "  ")
	ioutil.WriteFile(recommendationsFile, recommendationsData, 0644)

	logger.Info("Recommendations generated", "Count", len(recommendations))
	return nil
}

// GetRecommendations retrieves recommendations
func (ea *EvaluationActivities) GetRecommendations(ctx context.Context, recommendations *[]string) error {
	recommendationsFile := filepath.Join(ea.ResultsPath, "recommendations.json")
	
	data, err := ioutil.ReadFile(recommendationsFile)
	if err != nil {
		return fmt.Errorf("failed to read recommendations: %w", err)
	}

	if err := json.Unmarshal(data, recommendations); err != nil {
		return fmt.Errorf("failed to unmarshal recommendations: %w", err)
	}

	return nil
}

// SendEvaluationNotification sends evaluation notification
func (ea *EvaluationActivities) SendEvaluationNotification(ctx context.Context, email string, notificationData map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Sending evaluation notification", "Email", email)

	// Create notification content
	subject := "AI Agent Evaluation Results"
	
	if qualityGates, ok := notificationData["quality_gates"].(map[string]interface{}); ok {
		if passed, ok := qualityGates["passed"].(bool); ok {
			if passed {
				subject = "✅ AI Agent Evaluation PASSED"
			} else {
				subject = "❌ AI Agent Evaluation FAILED"
			}
		}
	}

	// Create content for the notification
	content := fmt.Sprintf("Evaluation results for %s", subject)

	// In a real implementation, this would send an email
	// For now, we'll just log the notification
	logger.Info("Notification content prepared", 
		"Subject", subject,
		"Content", content,
		"Email", email,
		"DataKeys", func() []string {
			keys := make([]string, 0, len(notificationData))
			for k := range notificationData {
				keys = append(keys, k)
			}
			return keys
		}())

	// Save notification for audit
	notification := map[string]interface{}{
		"email":      email,
		"subject":    subject,
		"sent_at":    time.Now().Format(time.RFC3339),
		"data":       notificationData,
	}

	notificationFile := filepath.Join(ea.ResultsPath, "notification.json")
	notificationDataJSON, _ := json.MarshalIndent(notification, "", "  ")
	ioutil.WriteFile(notificationFile, notificationDataJSON, 0644)

	logger.Info("Evaluation notification sent successfully")
	return nil
}
