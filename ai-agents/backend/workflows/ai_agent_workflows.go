package workflows

import (
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// AIOrchestrationWorkflow orchestrates multiple AI agents for compliance checking
func AIOrchestrationWorkflow(ctx workflow.Context, request types.ComplianceRequest) (*types.ComplianceResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting AI Orchestration Workflow", "request", request)

	// Set activity options with retry policy
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 10,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Step 1: Infrastructure discovery and emulation
	var infraResult types.InfrastructureResult
	err := workflow.ExecuteActivity(ctx, activities.DiscoverInfrastructureActivity, request.TargetResource).Get(ctx, &infraResult)
	if err != nil {
		return nil, err
	}

	// Step 2: Parallel AI agent checks
	// Security Agent
	var securityResult types.AgentResult
	securityFuture := workflow.ExecuteActivity(ctx, activities.SecurityAgentActivity, infraResult)

	// Compliance Agent  
	var complianceResult types.AgentResult
	complianceFuture := workflow.ExecuteActivity(ctx, activities.ComplianceAgentActivity, infraResult)

	// Cost Optimization Agent
	var costResult types.AgentResult
	costFuture := workflow.ExecuteActivity(ctx, activities.CostOptimizationAgentActivity, infraResult)

	// Wait for all agents to complete
	err = securityFuture.Get(ctx, &securityResult)
	if err != nil {
		return nil, err
	}

	err = complianceFuture.Get(ctx, &complianceResult)
	if err != nil {
		return nil, err
	}

	err = costFuture.Get(ctx, &costResult)
	if err != nil {
		return nil, err
	}

	agentResults := []types.AgentResult{securityResult, complianceResult, costResult}

	// Step 3: Aggregate results
	var aggregatedResult types.AggregatedResult
	err = workflow.ExecuteActivity(ctx, activities.AggregateAgentResultsActivity, agentResults).Get(ctx, &aggregatedResult)
	if err != nil {
		return nil, err
	}

	// Step 4: Human review if required
	if aggregatedResult.RequiresHumanReview {
		var humanResult types.HumanReviewResult
		err = workflow.ExecuteActivity(ctx, activities.HumanReviewActivity, aggregatedResult).Get(ctx, &humanResult)
		if err != nil {
			return nil, err
		}
		aggregatedResult.HumanReviewResult = &humanResult
	}

	// Step 5: Generate compliance report
	var complianceReport types.ComplianceReport
	err = workflow.ExecuteActivity(ctx, activities.GenerateComplianceReportActivity, aggregatedResult).Get(ctx, &complianceReport)
	if err != nil {
		return nil, err
	}

	result := &types.ComplianceResult{
		Report:     complianceReport,
		Approved:   !aggregatedResult.RequiresHumanReview || aggregatedResult.HumanReviewResult.Approved,
		CompletedAt: time.Now(),
	}

	return result, nil
}

// HumanInTheLoopWorkflow creates a workflow that waits for human interaction
func HumanInTheLoopWorkflow(ctx workflow.Context, task types.HumanTask) (*types.HumanTaskResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Human-in-the-Loop Workflow", "task", task)

	// Set up query handler for status updates
	err := workflow.SetQueryHandler(ctx, "taskStatus", func() (types.HumanTaskStatus, error) {
		return task.Status, nil
	})
	if err != nil {
		return nil, err
	}

	// Wait for human signal (approval/rejection)
	decisionCh := workflow.GetSignalChannel(ctx, "humanDecision")
	var decision string
	decisionCh.Receive(ctx, &decision)

	// Process human decision
	var result types.HumanTaskResult
	if decision == "approve" {
		result.Approved = true
		result.Decision = "Approved by human reviewer"
	} else {
		result.Approved = false
		result.Decision = "Rejected by human reviewer: " + decision
	}

	result.CompletedAt = workflow.Now(ctx)
	result.TaskID = task.ID

	return &result, nil
}

// MultiAgentCollaborationWorkflow demonstrates agent-to-agent communication
func MultiAgentCollaborationWorkflow(ctx workflow.Context, request types.CollaborationRequest) (*types.CollaborationResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Multi-Agent Collaboration Workflow")

	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 15,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute * 2,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Step 1: Primary agent analysis
	var primaryResult types.AgentResult
	err := workflow.ExecuteActivity(ctx, activities.PrimaryAgentActivity, request).Get(ctx, &primaryResult)
	if err != nil {
		return nil, err
	}

	// Step 2: Send results to secondary agents for validation
	validationFutures := make([]workflow.Future, 0)
	
	for _, agentType := range request.ValidationAgents {
		future := workflow.ExecuteActivity(ctx, activities.ValidationAgentActivity, agentType, primaryResult)
		validationFutures = append(validationFutures, future)
	}

	// Step 3: Collect validation results
	validationResults := make([]types.AgentResult, 0)
	for _, future := range validationFutures {
		var result types.AgentResult
		err := future.Get(ctx, &result)
		if err != nil {
			return nil, err
		}
		validationResults = append(validationResults, result)
	}

	// Step 4: Build consensus
	var consensus types.ConsensusResult
	err = workflow.ExecuteActivity(ctx, activities.BuildConsensusActivity, primaryResult, validationResults).Get(ctx, &consensus)
	if err != nil {
		return nil, err
	}

	// Step 5: Generate final recommendation
	var collaborationResult types.CollaborationResult
	err = workflow.ExecuteActivity(ctx, activities.GenerateFinalRecommendationActivity, consensus).Get(ctx, &collaborationResult)
	if err != nil {
		return nil, err
	}

	return &collaborationResult, nil
}
