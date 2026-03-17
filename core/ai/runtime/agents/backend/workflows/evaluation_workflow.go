package workflows

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

// EvaluationWorkflowInput defines input for evaluation workflow
type EvaluationWorkflowInput struct {
	TraceFilePath     string            `json:"trace_file_path"`
	Evaluators        []string          `json:"evaluators"`
	QualityGateScore  float64           `json:"quality_gate_score"`
	QualityGateRate   float64           `json:"quality_gate_pass_rate"`
	TraceCount        int               `json:"trace_count"`
	Labels            map[string]string `json:"labels"`
	NotificationEmail string            `json:"notification_email,omitempty"`
}

// EvaluationWorkflowOutput defines output from evaluation workflow
type EvaluationWorkflowOutput struct {
	OverallScore     float64           `json:"overall_score"`
	PassRate         float64           `json:"pass_rate"`
	TotalEvaluations int               `json:"total_evaluations"`
	ResultsFilePath  string            `json:"results_file_path"`
	Visualizations   map[string]string `json:"visualizations"`
	SecurityIssues   int               `json:"security_issues"`
	ComplianceIssues int               `json:"compliance_issues"`
	Passed           bool              `json:"passed"`
	ExecutionTime    time.Duration     `json:"execution_time"`
	Recommendations  []string          `json:"recommendations"`
}

// EvaluationWorkflow orchestrates AI agent evaluation
func EvaluationWorkflow(ctx workflow.Context, input EvaluationWorkflowInput) (EvaluationWorkflowOutput, error) {
	workflowOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Hour,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 10,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute * 5,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, workflowOptions)

	// Track workflow start time
	startTime := workflow.Now(ctx)
	
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting AI Agent Evaluation Workflow",
		"Evaluators", input.Evaluators,
		"TraceCount", input.TraceCount,
		"QualityGateScore", input.QualityGateScore,
		"QualityGateRate", input.QualityGateRate)

	var output EvaluationWorkflowOutput

	// Step 1: Prepare evaluation environment
	err := workflow.ExecuteActivity(ctx, PrepareEvaluationEnvironment, input)
	if err != nil {
		return output, fmt.Errorf("failed to prepare evaluation environment: %w", err)
	}

	// Step 2: Generate sample traces if needed
	if input.TraceCount > 0 {
		err = workflow.ExecuteActivity(ctx, GenerateSampleTraces, input)
		if err != nil {
			return output, fmt.Errorf("failed to generate sample traces: %w", err)
		}
	}

	// Step 3: Run evaluation
	var evaluationResults map[string]interface{}
	err = workflow.ExecuteActivity(ctx, RunEvaluationActivity, input)
	if err != nil {
		return output, fmt.Errorf("failed to run evaluation: %w", err)
	}

	// Get results from activity
	workflow.ExecuteActivity(ctx, GetEvaluationResults, &evaluationResults)

	// Step 4: Generate visualizations
	var visualizations map[string]string
	err = workflow.ExecuteActivity(ctx, GenerateVisualizations, input)
	if err != nil {
		logger.Warn("Failed to generate visualizations", "Error", err)
		visualizations = make(map[string]string)
	} else {
		workflow.ExecuteActivity(ctx, GetVisualizationPaths, &visualizations)
	}

	// Step 5: Check quality gates
	var qualityGateResult map[string]interface{}
	err = workflow.ExecuteActivity(ctx, CheckQualityGates, input)
	if err != nil {
		return output, fmt.Errorf("quality gate check failed: %w", err)
	}
	workflow.ExecuteActivity(ctx, GetQualityGateResults, &qualityGateResult)

	// Step 6: Generate recommendations
	var recommendations []string
	err = workflow.ExecuteActivity(ctx, GenerateRecommendations, evaluationResults)
	if err != nil {
		logger.Warn("Failed to generate recommendations", "Error", err)
		recommendations = []string{}
	} else {
		workflow.ExecuteActivity(ctx, GetRecommendations, &recommendations)
	}

	// Step 7: Send notifications if configured
	if input.NotificationEmail != "" {
		notificationData := map[string]interface{}{
			"results":         evaluationResults,
			"visualizations":  visualizations,
			"quality_gates":   qualityGateResult,
			"recommendations": recommendations,
			"labels":          input.Labels,
		}
		err = workflow.ExecuteActivity(ctx, SendEvaluationNotification, input.NotificationEmail, notificationData)
		if err != nil {
			logger.Warn("Failed to send notification", "Error", err)
		}
	}

	// Calculate execution time
	executionTime := workflow.Now(ctx).Sub(startTime)

	// Parse results
	if summary, ok := evaluationResults["summary"].(map[string]interface{}); ok {
		output.OverallScore = summary["overall_score"].(float64)
		output.PassRate = summary["overall_pass_rate"].(float64)
		output.TotalEvaluations = int(summary["total_evaluations"].(float64))
	}

	if aggregate, ok := evaluationResults["aggregate_metrics"].(map[string]interface{}); ok {
		if security, ok := aggregate["security_issues"].(float64); ok {
			output.SecurityIssues = int(security)
		}
		if compliance, ok := aggregate["compliance_issues"].(float64); ok {
			output.ComplianceIssues = int(compliance)
		}
	}

	output.ResultsFilePath = fmt.Sprintf("/results/evaluation_%d.json", startTime.Unix())
	output.Visualizations = visualizations
	output.Passed = qualityGateResult["passed"].(bool)
	output.ExecutionTime = executionTime
	output.Recommendations = recommendations

	logger.Info("AI Agent Evaluation Workflow completed",
		"OverallScore", output.OverallScore,
		"PassRate", output.PassRate,
		"Passed", output.Passed,
		"ExecutionTime", executionTime)

	return output, nil
}

// EvaluationTriggerWorkflow handles event-driven evaluation triggers
func EvaluationTriggerWorkflow(ctx workflow.Context, triggerData map[string]interface{}) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Evaluation trigger received", "TriggerData", triggerData)

	// Parse trigger data
	traceSource, _ := triggerData["trace_source"].(string)
	operationType, _ := triggerData["operation_type"].(string)
	urgency, _ := triggerData["urgency"].(string)
	
	// Determine evaluation parameters based on trigger
	input := EvaluationWorkflowInput{
		TraceFilePath:     fmt.Sprintf("/data/traces_%s.json", traceSource),
		Evaluators:        []string{"skill_invocation", "performance", "cost", "monitoring", "health_check"},
		QualityGateScore:  0.8,
		QualityGatePassRate: 0.85,
		TraceCount:        50,
		Labels: map[string]string{
			"trigger_source":   traceSource,
			"operation_type":   operationType,
			"urgency":          urgency,
			"workflow_type":    "event_driven",
		},
	}

	// Add security/compliance evaluators for high-urgency triggers
	if urgency == "high" || urgency == "critical" {
		input.Evaluators = append(input.Evaluators, "security", "compliance")
	}

	// Run evaluation workflow
	_, err := workflow.ExecuteChildWorkflow(ctx, workflow.ChildWorkflowOptions{
		WorkflowID: fmt.Sprintf("evaluation-%s-%d", traceSource, workflow.Now(ctx).Unix()),
	}, EvaluationWorkflow, input)

	if err != nil {
		return fmt.Errorf("failed to execute evaluation workflow: %w", err)
	}

	logger.Info("Event-driven evaluation completed successfully")
	return nil
}

// ScheduledEvaluationWorkflow handles periodic evaluations
func ScheduledEvaluationWorkflow(ctx workflow.Context) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting scheduled evaluation workflow")

	input := EvaluationWorkflowInput{
		TraceFilePath:     "/data/latest_traces.json",
		Evaluators:        []string{"skill_invocation", "performance", "cost", "monitoring", "health_check", "security", "compliance"},
		QualityGateScore:  0.8,
		QualityGatePassRate: 0.85,
		TraceCount:        100,
		Labels: map[string]string{
			"workflow_type": "scheduled",
			"schedule":      "hourly",
		},
		NotificationEmail: "dev-team@company.com",
	}

	_, err := workflow.ExecuteChildWorkflow(ctx, workflow.ChildWorkflowOptions{
		WorkflowID: fmt.Sprintf("scheduled-evaluation-%d", workflow.Now(ctx).Unix()),
	}, EvaluationWorkflow, input)

	if err != nil {
		return fmt.Errorf("failed to execute scheduled evaluation: %w", err)
	}

	logger.Info("Scheduled evaluation completed successfully")
	return nil
}
