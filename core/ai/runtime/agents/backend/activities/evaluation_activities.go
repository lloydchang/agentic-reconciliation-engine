package activities

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
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
func (ea *EvaluationActivities) PrepareEvaluationEnvironment(ctx context.Context, input EvaluationWorkflowInput) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Preparing evaluation environment")

	// Create directories
	dirs := []string{ea.ResultsPath, ea.VisualizationPath}
	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Set environment variables
	os.Setenv("EVALUATORS", fmt.Sprintf("%v", input.Evaluators))
	os.Setenv("QUALITY_GATE_SCORE", fmt.Sprintf("%f", input.QualityGateScore))
	os.Setenv("QUALITY_GATE_PASS_RATE", fmt.Sprintf("%f", input.QualityGatePassRate))

	logger.Info("Evaluation environment prepared successfully")
	return nil
}

// GenerateSampleTraces generates sample traces for evaluation
func (ea *EvaluationActivities) GenerateSampleTraces(ctx context.Context, input EvaluationWorkflowInput) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating sample traces", "Count", input.TraceCount)

	// Change to evaluator directory
	if err := os.Chdir(ea.EvaluatorPath); err != nil {
		return fmt.Errorf("failed to change to evaluator directory: %w", err)
	}

	// Generate sample traces
	cmd := exec.CommandContext(ctx, "python", "cli.py", "--generate-sample", 
		fmt.Sprintf("%d", input.TraceCount), 
		"--file", filepath.Join(ea.TracesPath, "sample_traces.json"))
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.Error("Failed to generate sample traces", "Output", string(output))
		return fmt.Errorf("failed to generate sample traces: %w", err)
	}

	logger.Info("Sample traces generated successfully")
	return nil
}

// RunEvaluationActivity runs the evaluation
func (ea *EvaluationActivities) RunEvaluationActivity(ctx context.Context, input EvaluationWorkflowInput) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Running evaluation", "Evaluators", input.Evaluators)

	// Change to evaluator directory
	if err := os.Chdir(ea.EvaluatorPath); err != nil {
		return fmt.Errorf("failed to change to evaluator directory: %w", err)
	}

	// Build evaluator list
	evaluatorList := fmt.Sprintf("%v", input.Evaluators)
	if evaluatorList == "[skill_invocation performance cost monitoring health_check security compliance]" {
		evaluatorList = "skill_invocation,performance,cost,monitoring,health_check,security,compliance"
	}

	// Run evaluation
	cmd := exec.CommandContext(ctx, "python", "cli.py",
		"--file", filepath.Join(ea.TracesPath, "sample_traces.json"),
		"--evaluators", evaluatorList,
		"--format", "json",
		"--output", filepath.Join(ea.ResultsPath, "evaluation_results.json"))
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.Error("Evaluation failed", "Output", string(output))
		return fmt.Errorf("evaluation failed: %w", err)
	}

	logger.Info("Evaluation completed successfully")
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
func (ea *EvaluationActivities) GenerateVisualizations(ctx context.Context, input EvaluationWorkflowInput) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating visualizations")

	// Change to evaluator directory
	if err := os.Chdir(ea.EvaluatorPath); err != nil {
		return fmt.Errorf("failed to change to evaluator directory: %w", err)
	}

	// Generate visualizations
	cmd := exec.CommandContext(ctx, "python", "cli.py",
		"--file", filepath.Join(ea.TracesPath, "sample_traces.json"),
		"--visualize",
		"--report-dir", ea.VisualizationPath)
	
	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.Error("Visualization generation failed", "Output", string(output))
		return fmt.Errorf("visualization generation failed: %w", err)
	}

	logger.Info("Visualizations generated successfully")
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

// CheckQualityGates checks quality gate compliance
func (ea *EvaluationActivities) CheckQualityGates(ctx context.Context, input EvaluationWorkflowInput) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Checking quality gates")

	// Read evaluation results
	resultsFile := filepath.Join(ea.ResultsPath, "evaluation_results.json")
	data, err := ioutil.ReadFile(resultsFile)
	if err != nil {
		return fmt.Errorf("failed to read results for quality gate check: %w", err)
	}

	var results map[string]interface{}
	if err := json.Unmarshal(data, &results); err != nil {
		return fmt.Errorf("failed to unmarshal results for quality gate check: %w", err)
	}

	// Extract metrics
	summary, ok := results["summary"].(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid results format: missing summary")
	}

	overallScore := summary["overall_score"].(float64)
	passRate := summary["overall_pass_rate"].(float64)

	// Check quality gates
	passed := true
	if overallScore < input.QualityGateScore {
		passed = false
	}
	if passRate < input.QualityGatePassRate {
		passed = false
	}

	// Save quality gate results
	qualityGateResults := map[string]interface{}{
		"passed":           passed,
		"overall_score":    overallScore,
		"pass_rate":        passRate,
		"score_threshold":  input.QualityGateScore,
		"rate_threshold":   input.QualityGatePassRate,
		"checked_at":       time.Now().Format(time.RFC3339),
	}

	qualityGateFile := filepath.Join(ea.ResultsPath, "quality_gate_results.json")
	qualityGateData, _ := json.MarshalIndent(qualityGateResults, "", "  ")
	ioutil.WriteFile(qualityGateFile, qualityGateData, 0644)

	logger.Info("Quality gate check completed", "Passed", passed)
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
