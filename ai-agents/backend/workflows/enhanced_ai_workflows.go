package workflows

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// Enhanced AI Orchestration Workflow with improved error handling and monitoring
func AIAgentOrchestrationWorkflowV2(ctx workflow.Context, request types.ComplianceRequest) (*types.ComplianceResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Enhanced AI Orchestration Workflow V2", "request", request)

	// Enhanced activity options with improved retry policies
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 15,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:        time.Second * 5,
			BackoffCoefficient:     1.5,
			MaximumInterval:        time.Minute * 5,
			MaximumAttempts:        5,
			NonRetryableErrorTypes: []string{"ValidationError", "AuthenticationError"},
		},
		HeartbeatTimeout: time.Minute * 2,
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Initialize workflow metrics and monitoring
	metrics := &WorkflowMetrics{
		StartTime:      workflow.Now(ctx),
		Stages:         make(map[string]*StageMetrics),
		AgentResults:   make([]types.AgentResult, 0),
		ErrorCount:     0,
		RetryCount:     0,
	}

	defer func() {
		metrics.EndTime = workflow.Now(ctx)
		metrics.Duration = metrics.EndTime.Sub(metrics.StartTime)
		logger.Info("Workflow completed", "metrics", metrics)
	}()

	// Enhanced error handling with circuit breaker pattern
	var circuitBreaker CircuitBreaker
	circuitBreaker.Init("ai-orchestration", 3, time.Minute*10)

	// Stage 1: Infrastructure discovery with enhanced validation
	logger.Info("Stage 1: Infrastructure Discovery")
	metrics.Stages["discovery"] = &StageMetrics{StartTime: workflow.Now(ctx)}

	var infraResult types.InfrastructureResult
	err := workflow.ExecuteActivity(ctx, activities.DiscoverInfrastructureActivity, request.TargetResource).Get(ctx, &infraResult)
	if err != nil {
		metrics.Stages["discovery"].EndTime = workflow.Now(ctx)
		metrics.Stages["discovery"].Status = "failed"
		metrics.ErrorCount++
		return nil, fmt.Errorf("infrastructure discovery failed: %w", err)
	}
	metrics.Stages["discovery"].EndTime = workflow.Now(ctx)
	metrics.Stages["discovery"].Status = "completed"

	// Validate infrastructure result
	if err := validateInfrastructureResult(infraResult); err != nil {
		return nil, fmt.Errorf("infrastructure validation failed: %w", err)
	}

	// Stage 2: Parallel AI agent analysis with enhanced error handling
	logger.Info("Stage 2: Parallel Agent Analysis")
	metrics.Stages["agent-analysis"] = &StageMetrics{StartTime: workflow.Now(ctx)}

	// Execute agents with enhanced concurrency control
	agentResults, err := executeAgentsWithConcurrencyControl(ctx, infraResult, &circuitBreaker)
	if err != nil {
		metrics.Stages["agent-analysis"].EndTime = workflow.Now(ctx)
		metrics.Stages["agent-analysis"].Status = "failed"
		metrics.ErrorCount++
		return nil, fmt.Errorf("agent analysis failed: %w", err)
	}

	metrics.Stages["agent-analysis"].EndTime = workflow.Now(ctx)
	metrics.Stages["agent-analysis"].Status = "completed"
	metrics.AgentResults = agentResults

	// Stage 3: Enhanced result aggregation with ML-based scoring
	logger.Info("Stage 3: Enhanced Result Aggregation")
	metrics.Stages["aggregation"] = &StageMetrics{StartTime: workflow.Now(ctx)}

	var aggregatedResult types.AggregatedResult
	err = workflow.ExecuteActivity(ctx, activities.AggregateAgentResultsActivity, agentResults).Get(ctx, &aggregatedResult)
	if err != nil {
		metrics.Stages["aggregation"].EndTime = workflow.Now(ctx)
		metrics.Stages["aggregation"].Status = "failed"
		metrics.ErrorCount++
		return nil, fmt.Errorf("result aggregation failed: %w", err)
	}

	metrics.Stages["aggregation"].EndTime = workflow.Now(ctx)
	metrics.Stages["aggregation"].Status = "completed"

	// Stage 4: Intelligent human review decision with enhanced logic
	logger.Info("Stage 4: Intelligent Human Review Decision")

	requiresReview, reviewPriority := intelligentHumanReviewDecision(aggregatedResult, agentResults, infraResult)

	if requiresReview {
		logger.Info("Human review required", "priority", reviewPriority)

		var reviewResult types.HumanReviewResult
		reviewCtx := workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
			StartToCloseTimeout: time.Hour * 24, // 24 hour timeout for human review
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Minute * 30,
				MaximumAttempts:    1, // No retries for human activities
			},
		})

		err = workflow.ExecuteActivity(reviewCtx, activities.HumanReviewActivity, aggregatedResult).Get(ctx, &reviewResult)
		if err != nil {
			// Handle human review timeout or failure
			logger.Warn("Human review failed or timed out", "error", err)
			reviewResult = types.HumanReviewResult{
				ReviewerID: "system-fallback",
				Approved:   aggregatedResult.OverallScore >= 90.0, // Auto-approve high scores
				Decision:   "System fallback decision based on high compliance score",
				Comments:   "Human review was not completed within timeout period",
				ReviewedAt: workflow.Now(ctx),
			}
		}
		aggregatedResult.HumanReviewResult = &reviewResult
	}

	// Stage 5: Enhanced compliance report generation
	logger.Info("Stage 5: Enhanced Compliance Report Generation")
	metrics.Stages["reporting"] = &StageMetrics{StartTime: workflow.Now(ctx)}

	var finalReport types.ComplianceReport
	err = workflow.ExecuteActivity(ctx, activities.GenerateComplianceReportActivity, aggregatedResult).Get(ctx, &finalReport)
	if err != nil {
		metrics.Stages["reporting"].EndTime = workflow.Now(ctx)
		metrics.Stages["reporting"].Status = "failed"
		metrics.ErrorCount++
		return nil, fmt.Errorf("report generation failed: %w", err)
	}

	metrics.Stages["reporting"].EndTime = workflow.Now(ctx)
	metrics.Stages["reporting"].Status = "completed"

	// Final result with enhanced metadata
	result := &types.ComplianceResult{
		Report:      finalReport,
		Approved:    aggregatedResult.HumanReviewResult == nil || aggregatedResult.HumanReviewResult.Approved,
		CompletedAt: workflow.Now(ctx),
	}

	logger.Info("Enhanced AI Orchestration Workflow V2 completed successfully", "result", result)
	return result, nil
}

// executeAgentsWithConcurrencyControl manages parallel agent execution with enhanced error handling
func executeAgentsWithConcurrencyControl(ctx workflow.Context, infra types.InfrastructureResult, circuitBreaker *CircuitBreaker) ([]types.AgentResult, error) {
	// Define agent configurations with priority and dependencies
	agentConfigs := []AgentConfig{
		{Type: "security", Priority: 1, Timeout: time.Minute * 5, MaxRetries: 3},
		{Type: "compliance", Priority: 1, Timeout: time.Minute * 7, MaxRetries: 3},
		{Type: "cost-optimization", Priority: 2, Timeout: time.Minute * 4, MaxRetries: 2},
	}

	// Execute high-priority agents first
	highPriorityAgents := filterAgentsByPriority(agentConfigs, 1)
	lowPriorityAgents := filterAgentsByPriority(agentConfigs, 2)

	var results []types.AgentResult

	// Execute high-priority agents in parallel
	highPriorityFutures := make([]workflow.Future, 0, len(highPriorityAgents))
	for _, config := range highPriorityAgents {
		if circuitBreaker.ShouldAttempt() {
			future := executeAgentWithConfig(ctx, config, infra)
			highPriorityFutures = append(highPriorityFutures, future)
		}
	}

	// Wait for high-priority agents and collect results
	for _, future := range highPriorityFutures {
		var result types.AgentResult
		err := future.Get(ctx, &result)
		if err != nil {
			circuitBreaker.RecordFailure()
			// Continue with other agents but log the failure
			workflow.GetLogger(ctx).Error("High-priority agent failed", "error", err)
		} else {
			results = append(results, result)
		}
	}

	// Execute low-priority agents only if circuit breaker allows
	if circuitBreaker.ShouldAttempt() {
		lowPriorityFutures := make([]workflow.Future, 0, len(lowPriorityAgents))
		for _, config := range lowPriorityAgents {
			future := executeAgentWithConfig(ctx, config, infra)
			lowPriorityFutures = append(lowPriorityFutures, future)
		}

		for _, future := range lowPriorityFutures {
			var result types.AgentResult
			err := future.Get(ctx, &result)
			if err != nil {
				// Low-priority failures are less critical
				workflow.GetLogger(ctx).Warn("Low-priority agent failed", "error", err)
			} else {
				results = append(results, result)
			}
		}
	}

	if len(results) == 0 {
		return nil, fmt.Errorf("all agents failed execution")
	}

	return results, nil
}

// executeAgentWithConfig executes a single agent with specific configuration
func executeAgentWithConfig(ctx workflow.Context, config AgentConfig, infra types.InfrastructureResult) workflow.Future {
	agentOptions := workflow.ActivityOptions{
		StartToCloseTimeout: config.Timeout,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 10,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    int32(config.MaxRetries),
		},
		HeartbeatTimeout: time.Minute,
	}

	agentCtx := workflow.WithActivityOptions(ctx, agentOptions)

	switch config.Type {
	case "security":
		return workflow.ExecuteActivity(agentCtx, activities.SecurityAgentActivity, infra)
	case "compliance":
		return workflow.ExecuteActivity(agentCtx, activities.ComplianceAgentActivity, infra)
	case "cost-optimization":
		return workflow.ExecuteActivity(agentCtx, activities.CostOptimizationAgentActivity, infra)
	default:
		// This should not happen, but handle gracefully
		panic(fmt.Sprintf("Unknown agent type: %s", config.Type))
	}
}

// intelligentHumanReviewDecision makes smart decisions about when human review is needed
func intelligentHumanReviewDecision(aggregated types.AggregatedResult, agentResults []types.AgentResult, infra types.InfrastructureResult) (bool, string) {
	// Always require review for high-risk or critical findings
	if aggregated.RiskLevel == "High" || aggregated.RiskLevel == "Critical" {
		return true, "high"
	}

	// Require review if consensus is low among agents
	scoreVariance := calculateScoreVariance(agentResults)
	if scoreVariance > 15.0 { // High variance indicates disagreement
		return true, "medium"
	}

	// Require review for production environments or sensitive data
	if infra.Properties != nil {
		if env, ok := infra.Properties["environment"].(string); ok && env == "production" {
			return true, "medium"
		}
		if sensitive, ok := infra.Properties["containsSensitiveData"].(bool); ok && sensitive {
			return true, "high"
		}
	}

	// Require review if overall score is borderline
	if aggregated.OverallScore < 85.0 {
		return true, "medium"
	}

	// No review needed for high-confidence results
	return false, ""
}

// validateInfrastructureResult performs enhanced validation of infrastructure results
func validateInfrastructureResult(result types.InfrastructureResult) error {
	if result.ResourceID == "" {
		return fmt.Errorf("resource ID is required")
	}
	if result.ResourceType == "" {
		return fmt.Errorf("resource type is required")
	}
	if result.Properties == nil {
		return fmt.Errorf("resource properties are required")
	}
	return nil
}

// calculateScoreVariance calculates the variance in agent scores
func calculateScoreVariance(results []types.AgentResult) float64 {
	if len(results) < 2 {
		return 0.0
	}

	sum := 0.0
	for _, result := range results {
		sum += result.Score
	}
	mean := sum / float64(len(results))

	variance := 0.0
	for _, result := range results {
		diff := result.Score - mean
		variance += diff * diff
	}
	variance /= float64(len(results))

	return variance
}

// Helper types and functions

type WorkflowMetrics struct {
	StartTime    time.Time                    `json:"startTime"`
	EndTime      time.Time                    `json:"endTime"`
	Duration     time.Duration                `json:"duration"`
	Stages       map[string]*StageMetrics     `json:"stages"`
	AgentResults []types.AgentResult          `json:"agentResults"`
	ErrorCount   int                          `json:"errorCount"`
	RetryCount   int                          `json:"retryCount"`
}

type StageMetrics struct {
	StartTime time.Time `json:"startTime"`
	EndTime   time.Time `json:"endTime"`
	Status    string    `json:"status"`
	Duration  time.Duration `json:"duration"`
}

type AgentConfig struct {
	Type       string        `json:"type"`
	Priority   int           `json:"priority"`
	Timeout    time.Duration `json:"timeout"`
	MaxRetries int           `json:"maxRetries"`
}

type CircuitBreaker struct {
	Name         string
	FailureCount int
	LastFailure  time.Time
	Timeout      time.Duration
	MaxFailures  int
}

func (cb *CircuitBreaker) Init(name string, maxFailures int, timeout time.Duration) {
	cb.Name = name
	cb.MaxFailures = maxFailures
	cb.Timeout = timeout
	cb.FailureCount = 0
}

func (cb *CircuitBreaker) ShouldAttempt() bool {
	if cb.FailureCount >= cb.MaxFailures {
		if time.Since(cb.LastFailure) > cb.Timeout {
			cb.FailureCount = 0 // Reset after timeout
			return true
		}
		return false
	}
	return true
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.FailureCount++
	cb.LastFailure = time.Now()
}

func (cb *CircuitBreaker) GetState() string {
	if cb.FailureCount >= cb.MaxFailures {
		if time.Since(cb.LastFailure) > cb.Timeout {
			return "half-open"
		}
		return "open"
	}
	return "closed"
}

func filterAgentsByPriority(configs []AgentConfig, priority int) []AgentConfig {
	var filtered []AgentConfig
	for _, config := range configs {
		if config.Priority == priority {
			filtered = append(filtered, config)
		}
	}
	return filtered
}
