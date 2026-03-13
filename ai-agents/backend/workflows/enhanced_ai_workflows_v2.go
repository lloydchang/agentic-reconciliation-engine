package workflows

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"

	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// EnhancedAIOrchestrationWorkflowV2 - Second iteration with advanced features
func EnhancedAIOrchestrationWorkflowV2(ctx workflow.Context, request types.ComplianceRequest) (*types.ComplianceResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Enhanced AI Orchestration Workflow V2", "request", request)

	// Enhanced activity options with circuit breaker pattern
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 15,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 5,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute * 2,
			MaximumAttempts:    3,
		},
		HeartbeatTimeout: time.Minute,
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Initialize workflow metrics
	metrics := &types.WorkflowMetrics{
		WorkflowID:   workflow.GetInfo(ctx).WorkflowExecution.ID,
		WorkflowType: "EnhancedAIOrchestrationV2",
		StartTime:    workflow.Now(ctx),
		Status:       "running",
		Stages:       make(map[string]*types.StageMetrics),
		ResourceUsage: types.ResourceUsage{
			AgentCount: 3,
		},
	}

	// Stage 1: Enhanced infrastructure discovery with validation
	logger.Info("Stage 1: Enhanced Infrastructure Discovery")
	metrics.Stages["discovery"] = &types.StageMetrics{
		Name:      "Infrastructure Discovery",
		StartTime: workflow.Now(ctx),
		Status:    "running",
	}

	var infraResult types.InfrastructureResult
	err := workflow.ExecuteActivity(ctx, activities.DiscoverInfrastructureActivity, request.TargetResource).Get(ctx, &infraResult)
	if err != nil {
		metrics.Stages["discovery"].Status = "failed"
		metrics.Stages["discovery"].EndTime = workflow.Now(ctx)
		metrics.ErrorCount++
		return nil, fmt.Errorf("infrastructure discovery failed: %w", err)
	}

	// Enhanced validation
	if err := validateInfrastructureV2(infraResult); err != nil {
		return nil, fmt.Errorf("infrastructure validation failed: %w", err)
	}

	metrics.Stages["discovery"].Status = "completed"
	metrics.Stages["discovery"].EndTime = workflow.Now(ctx)

	// Stage 2: Parallel AI agent execution with enhanced concurrency control
	logger.Info("Stage 2: Enhanced Parallel Agent Execution")
	metrics.Stages["agent-execution"] = &types.StageMetrics{
		Name:      "Agent Execution",
		StartTime: workflow.Now(ctx),
		Status:    "running",
	}

	agentResults, err := executeAgentsWithEnhancedConcurrency(ctx, infraResult, request)
	if err != nil {
		metrics.Stages["agent-execution"].Status = "failed"
		metrics.Stages["agent-execution"].EndTime = workflow.Now(ctx)
		metrics.ErrorCount++
		return nil, fmt.Errorf("agent execution failed: %w", err)
	}

	metrics.Stages["agent-execution"].Status = "completed"
	metrics.Stages["agent-execution"].EndTime = workflow.Now(ctx)
	metrics.AgentResults = agentResults

	// Stage 3: Enhanced result aggregation with ML-based scoring
	logger.Info("Stage 3: Enhanced Result Aggregation")
	metrics.Stages["aggregation"] = &types.StageMetrics{
		Name:      "Result Aggregation",
		StartTime: workflow.Now(ctx),
		Status:    "running",
	}

	var aggregatedResult types.AggregatedResult
	err = workflow.ExecuteActivity(ctx, activities.AggregateAgentResultsActivity, agentResults).Get(ctx, &aggregatedResult)
	if err != nil {
		metrics.Stages["aggregation"].Status = "failed"
		metrics.Stages["aggregation"].EndTime = workflow.Now(ctx)
		metrics.ErrorCount++
		return nil, fmt.Errorf("result aggregation failed: %w", err)
	}

	// Enhanced aggregation with confidence scoring
	aggregatedResult = enhanceAggregationWithConfidence(aggregatedResult, agentResults)

	metrics.Stages["aggregation"].Status = "completed"
	metrics.Stages["aggregation"].EndTime = workflow.Now(ctx)

	// Stage 4: Intelligent human review decision
	logger.Info("Stage 4: Intelligent Human Review Decision")
	metrics.Stages["human-review"] = &types.StageMetrics{
		Name:      "Human Review",
		StartTime: workflow.Now(ctx),
		Status:    "running",
	}

	requiresReview, reviewPriority := intelligentReviewDecisionV2(aggregatedResult, agentResults, request)

	if requiresReview {
		logger.Info("Human review required", "priority", reviewPriority)

		// Enhanced human review with configurable timeout
		reviewCtx := workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
			StartToCloseTimeout: getReviewTimeout(reviewPriority),
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Minute * 30,
				MaximumAttempts:    1, // No retries for human activities
			},
		})

		var reviewResult types.HumanReviewResult
		err = workflow.ExecuteActivity(reviewCtx, activities.HumanReviewActivity, aggregatedResult).Get(ctx, &reviewResult)
		if err != nil {
			// Enhanced fallback logic
			logger.Warn("Human review failed or timed out", "error", err)
			reviewResult = generateFallbackReviewResult(aggregatedResult, request)
		}

		aggregatedResult.HumanReviewResult = &reviewResult
		metrics.Stages["human-review"].Status = "completed"
	} else {
		metrics.Stages["human-review"].Status = "skipped"
		logger.Info("Human review not required - auto-approving")
	}

	metrics.Stages["human-review"].EndTime = workflow.Now(ctx)

	// Stage 5: Enhanced compliance report generation
	logger.Info("Stage 5: Enhanced Compliance Report Generation")
	metrics.Stages["reporting"] = &types.StageMetrics{
		Name:      "Report Generation",
		StartTime: workflow.Now(ctx),
		Status:    "running",
	}

	var finalReport types.ComplianceReport
	err = workflow.ExecuteActivity(ctx, activities.GenerateComplianceReportActivity, aggregatedResult).Get(ctx, &finalReport)
	if err != nil {
		metrics.Stages["reporting"].Status = "failed"
		metrics.Stages["reporting"].EndTime = workflow.Now(ctx)
		metrics.ErrorCount++
		return nil, fmt.Errorf("report generation failed: %w", err)
	}

	// Enhance report with additional metadata
	finalReport = enhanceReportWithV2Features(finalReport, aggregatedResult, request)

	metrics.Stages["reporting"].Status = "completed"
	metrics.Stages["reporting"].EndTime = workflow.Now(ctx)

	// Final result with enhanced metadata
	result := &types.ComplianceResult{
		Report:      finalReport,
		Approved:    determineApprovalStatus(aggregatedResult, request),
		CompletedAt: workflow.Now(ctx),
		Metadata: map[string]interface{}{
			"workflowVersion":    "v2.0",
			"totalAgents":        len(agentResults),
			"humanReviewRequired": requiresReview,
			"reviewPriority":     reviewPriority,
			"autoApproved":       !requiresReview,
			"metrics":           metrics,
			"enhancedFeatures": []string{
				"intelligent-review-decision",
				"enhanced-aggregation",
				"fallback-logic",
				"confidence-scoring",
			},
		},
		ProcessingTime: workflow.Now(ctx).Sub(metrics.StartTime),
		AutoApproved:   !requiresReview,
	}

	// Complete metrics
	metrics.EndTime = workflow.Now(ctx)
	metrics.Duration = metrics.EndTime.Sub(metrics.StartTime)
	metrics.Status = "completed"

	logger.Info("Enhanced AI Orchestration Workflow V2 completed successfully", 
		"duration", metrics.Duration,
		"approved", result.Approved,
		"autoApproved", result.AutoApproved)

	return result, nil
}

// Enhanced helper functions

func executeAgentsWithEnhancedConcurrency(ctx workflow.Context, infra types.InfrastructureResult, request types.ComplianceRequest) ([]types.AgentResult, error) {
	// Enhanced agent configurations with priority-based execution
	agentConfigs := []AgentConfigV2{
		{
			Type:         "security",
			Priority:     1,
			Timeout:      time.Minute * 5,
			MaxRetries:   3,
			Required:     true,
			Dependencies: []string{},
		},
		{
			Type:         "compliance",
			Priority:     1,
			Timeout:      time.Minute * 7,
			MaxRetries:   3,
			Required:     true,
			Dependencies: []string{},
		},
		{
			Type:         "cost-optimization",
			Priority:     2,
			Timeout:      time.Minute * 4,
			MaxRetries:   2,
			Required:     false,
			Dependencies: []string{"security", "compliance"},
		},
	}

	return executeAgentsWithDependencies(ctx, infra, agentConfigs)
}

func executeAgentsWithDependencies(ctx workflow.Context, infra types.InfrastructureResult, configs []AgentConfigV2) ([]types.AgentResult, error) {
	var results []types.AgentResult
	completedAgents := make(map[string]bool)

	// Execute in priority order with dependency resolution
	for _, config := range configs {
		// Check dependencies
		allDepsMet := true
		for _, dep := range config.Dependencies {
			if !completedAgents[dep] {
				allDepsMet = false
				break
			}
		}

		if !allDepsMet {
			continue // Skip if dependencies not met
		}

		var result types.AgentResult
		var err error

		switch config.Type {
		case "security":
			err = workflow.ExecuteActivity(ctx, activities.SecurityAgentActivity, infra).Get(ctx, &result)
		case "compliance":
			err = workflow.ExecuteActivity(ctx, activities.ComplianceAgentActivity, infra).Get(ctx, &result)
		case "cost-optimization":
			err = workflow.ExecuteActivity(ctx, activities.CostOptimizationAgentActivity, infra).Get(ctx, &result)
		default:
			return nil, fmt.Errorf("unknown agent type: %s", config.Type)
		}

		if err != nil {
			if config.Required {
				return nil, fmt.Errorf("required agent %s failed: %w", config.Type, err)
			}
			// Log but continue for optional agents
			workflow.GetLogger(ctx).Warn("Optional agent failed", "agent", config.Type, "error", err)
			continue
		}

		results = append(results, result)
		completedAgents[config.Type] = true
	}

	return results, nil
}

func intelligentReviewDecisionV2(aggregated types.AggregatedResult, agentResults []types.AgentResult, request types.ComplianceRequest) (bool, string) {
	// Enhanced decision logic with more factors

	// Always require review for critical findings
	if aggregated.RiskLevel == "Critical" {
		return true, "critical"
	}

	// Check if auto-approval is enabled and conditions are met
	if request.AutoApproval && 
		aggregated.OverallScore >= request.RequiredScore &&
		aggregated.RiskLevel == "Low" &&
		request.Priority == "Low" {
		return false, ""
	}

	// Score-based decision
	if aggregated.OverallScore >= 95.0 && aggregated.RiskLevel == "Low" {
		return false, ""
	}

	// Consensus-based decision
	scoreVariance := calculateScoreVariance(agentResults)
	if scoreVariance > 20.0 { // High disagreement
		return true, "high"
	}

	// Risk-based decision
	if aggregated.RiskLevel == "High" {
		return true, "high"
	}

	// Score-based thresholds
	if aggregated.OverallScore < 85.0 {
		return true, "medium"
	}

	// Environment-based decision
	if request.Priority == "High" {
		return true, "medium"
	}

	return false, ""
}

func enhanceAggregationWithConfidence(aggregated types.AggregatedResult, agentResults []types.AgentResult) types.AggregatedResult {
	// Calculate confidence score based on agent consensus
	if len(agentResults) == 0 {
		return aggregated
	}

	scoreVariance := calculateScoreVariance(agentResults)
	consensusScore := 100.0 - scoreVariance // Higher consensus = lower variance

	// Adjust confidence based on number of agents
	agentCountBonus := float64(len(agentResults)) * 2.0
	confidenceScore := consensusScore + agentCountBonus

	// Cap confidence at 100
	if confidenceScore > 100.0 {
		confidenceScore = 100.0
	}

	aggregated.ConfidenceScore = confidenceScore
	aggregated.AggregationMethod = "enhanced-consensus-v2"
	aggregated.ProcessedAt = time.Now()

	return aggregated
}

func enhanceReportWithV2Features(report types.ComplianceReport, aggregated types.AggregatedResult, request types.ComplianceRequest) types.ComplianceReport {
	// Add V2 enhancements to the report
	report.ReportVersion = "v2.0"
	report.Confidence = aggregated.ConfidenceScore
	report.ComplianceFramework = request.ComplianceType

	// Add processing metadata
	if report.GeneratedAt.IsZero() {
		report.GeneratedAt = time.Now()
	}

	return report
}

func determineApprovalStatus(aggregated types.AggregatedResult, request types.ComplianceRequest) bool {
	// Enhanced approval logic
	if aggregated.HumanReviewResult != nil {
		return aggregated.HumanReviewResult.Approved
	}

	// Auto-approval logic
	if aggregated.OverallScore >= request.RequiredScore &&
		aggregated.RiskLevel != "Critical" &&
		aggregated.ConfidenceScore >= 80.0 {
		return true
	}

	return false
}

func generateFallbackReviewResult(aggregated types.AggregatedResult, request types.ComplianceRequest) types.HumanReviewResult {
	// Enhanced fallback logic
	autoApprove := aggregated.OverallScore >= 90.0 && aggregated.RiskLevel != "Critical"

	return types.HumanReviewResult{
		ReviewerID:      "system-fallback-v2",
		Approved:       autoApprove,
		Decision:       fmt.Sprintf("System fallback: %s", map[bool]string{true: "Auto-approved", false: "Auto-rejected"}[autoApprove]),
		Comments:       fmt.Sprintf("Human review timeout - Auto-%s based on score %.1f and risk level %s", 
			map[bool]string{true: "approved", false: "rejected"}[autoApprove], 
			aggregated.OverallScore, 
			aggregated.RiskLevel),
		ReviewedAt:      time.Now(),
		ReviewDuration:  0,
		Confidence:      aggregated.ConfidenceScore,
		EscalationLevel: 0,
	}
}

func getReviewTimeout(priority string) time.Duration {
	switch priority {
	case "critical":
		return time.Hour * 2
	case "high":
		return time.Hour * 8
	case "medium":
		return time.Hour * 24
	default:
		return time.Hour * 48
	}
}

func validateInfrastructureV2(result types.InfrastructureResult) error {
	// Enhanced validation
	if result.ResourceID == "" {
		return fmt.Errorf("resource ID is required")
	}
	if result.ResourceType == "" {
		return fmt.Errorf("resource type is required")
	}
	if result.Properties == nil {
		return fmt.Errorf("resource properties are required")
	}

	// Additional validation
	if result.ValidationStatus == "" {
		result.ValidationStatus = "pending"
	}

	return nil
}

// Enhanced configuration types
type AgentConfigV2 struct {
	Type         string
	Priority     int
	Timeout      time.Duration
	MaxRetries   int
	Required     bool
	Dependencies []string
}
