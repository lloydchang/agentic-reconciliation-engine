package main

import (
	"fmt"
	"strings"
)

// WorkflowTranslator converts Backstage workflow definitions to Temporal workflows
type WorkflowTranslator struct{}

// WorkflowStep represents a step in the visual workflow builder
type WorkflowStep struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Config      map[string]interface{} `json:"config"`
}

// WorkflowDefinition represents the complete workflow from the UI
type WorkflowDefinition struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Steps       []WorkflowStep `json:"steps"`
}

// TranslateToTemporalWorkflow converts a workflow definition to Temporal workflow code
func (wt *WorkflowTranslator) TranslateToTemporalWorkflow(def WorkflowDefinition) (string, error) {
	var workflowCode strings.Builder

	// Generate workflow function
	workflowCode.WriteString(fmt.Sprintf(`
// %s - %s
func %sWorkflow(ctx workflow.Context, request types.ComplianceRequest) (*types.ComplianceResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting %s", "request", request)

	// Activity options
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

`, def.Name, def.Description, sanitizeWorkflowName(def.Name), def.Name))

	// Add workflow steps
	for i, step := range def.Steps {
		stepCode := wt.generateStepCode(step, i)
		workflowCode.WriteString(stepCode)
	}

	// Add final result construction
	workflowCode.WriteString(`
	// Construct final result
	result := &types.ComplianceResult{
		Report:      complianceReport,
		Approved:    aggregatedResult.HumanReviewResult == nil || aggregatedResult.HumanReviewResult.Approved,
		CompletedAt: time.Now(),
	}

	return result, nil
}
`)

	return workflowCode.String(), nil
}

// generateStepCode generates the code for a single workflow step
func (wt *WorkflowTranslator) generateStepCode(step WorkflowStep, index int) string {
	switch step.Type {
	case "infrastructure":
		return wt.generateInfrastructureStep(step, index)
	case "agent":
		return wt.generateAgentStep(step, index)
	case "aggregation":
		return wt.generateAggregationStep(step, index)
	case "human":
		return wt.generateHumanStep(step, index)
	default:
		return fmt.Sprintf("\t// Unsupported step type: %s\n", step.Type)
	}
}

// generateInfrastructureStep generates infrastructure discovery step
func (wt *WorkflowTranslator) generateInfrastructureStep(step WorkflowStep, index int) string {
	targetResource := "vm-web-server-001" // Default
	if val, ok := step.Config["targetResource"].(string); ok {
		targetResource = val
	}

	return fmt.Sprintf(`
	// Step %d: %s
	logger.Info("Step %d: %s")
	var infraResult%d types.InfrastructureResult
	err := workflow.ExecuteActivity(ctx, activities.DiscoverInfrastructureActivity, "%s").Get(ctx, &infraResult%d)
	if err != nil {
		return nil, fmt.Errorf("%s failed: %%w", err)
	}
`, index+1, step.Name, index+1, step.Name, index+1, targetResource, index+1, step.Name)
}

// generateAgentStep generates AI agent execution step
func (wt *WorkflowTranslator) generateAgentStep(step WorkflowStep, index int) string {
	agentType := "security" // Default
	if val, ok := step.Config["agentType"].(string); ok {
		agentType = val
	}

	var activityName string
	switch agentType {
	case "security":
		activityName = "activities.SecurityAgentActivity"
	case "compliance":
		activityName = "activities.ComplianceAgentActivity"
	case "cost-optimization":
		activityName = "activities.CostOptimizationAgentActivity"
	default:
		activityName = "activities.SecurityAgentActivity"
	}

	return fmt.Sprintf(`
	// Step %d: %s (%s)
	logger.Info("Step %d: %s")
	var agentResult%d types.AgentResult
	err := workflow.ExecuteActivity(ctx, %s, infraResult%d).Get(ctx, &agentResult%d)
	if err != nil {
		return nil, fmt.Errorf("%s failed: %%w", err)
	}
`, index+1, step.Name, agentType, index+1, step.Name, index+1, activityName, index, index+1, step.Name)
}

// generateAggregationStep generates result aggregation step
func (wt *WorkflowTranslator) generateAggregationStep(step WorkflowStep, index int) string {
	return fmt.Sprintf(`
	// Step %d: %s
	logger.Info("Step %d: %s")
	agentResults := []types.AgentResult{agentResult1, agentResult2, agentResult3} // Collect all agent results

	var aggregatedResult types.AggregatedResult
	err := workflow.ExecuteActivity(ctx, activities.AggregateAgentResultsActivity, agentResults).Get(ctx, &aggregatedResult)
	if err != nil {
		return nil, fmt.Errorf("%s failed: %%w", err)
	}
`, index+1, step.Name, index+1, step.Name, step.Name)
}

// generateHumanStep generates human review step
func (wt *WorkflowTranslator) generateHumanStep(step WorkflowStep, index int) string {
	return fmt.Sprintf(`
	// Step %d: %s
	logger.Info("Step %d: %s")
	if aggregatedResult.RequiresHumanReview {
		var humanResult types.HumanReviewResult
		reviewCtx := workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
			StartToCloseTimeout: time.Hour * 24,
			RetryPolicy: &temporal.RetryPolicy{
				InitialInterval:    time.Minute * 30,
				MaximumAttempts:    1,
			},
		})

		err := workflow.ExecuteActivity(reviewCtx, activities.HumanReviewActivity, aggregatedResult).Get(ctx, &humanResult)
		if err != nil {
			logger.Warn("%s failed or timed out", err)
			humanResult = types.HumanReviewResult{
				ReviewerID: "system-fallback",
				Approved:   aggregatedResult.OverallScore >= 90.0,
				Decision:   "System fallback decision based on high compliance score",
				Comments:   "Human review was not completed within timeout period",
				ReviewedAt: workflow.Now(ctx),
			}
		}
		aggregatedResult.HumanReviewResult = &humanResult
	}
`, index+1, step.Name, index+1, step.Name, step.Name)
}

// generateComplianceReportStep generates compliance report generation
func (wt *WorkflowTranslator) generateComplianceReportStep() string {
	return `
	// Generate compliance report
	var complianceReport types.ComplianceReport
	err = workflow.ExecuteActivity(ctx, activities.GenerateComplianceReportActivity, aggregatedResult).Get(ctx, &complianceReport)
	if err != nil {
		return nil, fmt.Errorf("report generation failed: %w", err)
	}
`
}

// sanitizeWorkflowName converts workflow name to valid Go function name
func sanitizeWorkflowName(name string) string {
	// Remove spaces and special characters, capitalize words
	words := strings.Fields(strings.ReplaceAll(strings.ReplaceAll(name, "-", " "), "_", " "))
	var result strings.Builder

	for _, word := range words {
		if len(word) > 0 {
			result.WriteString(strings.ToUpper(word[:1]) + strings.ToLower(word[1:]))
		}
	}

	return result.String()
}

// ValidateWorkflowDefinition checks if a workflow definition is valid
func (wt *WorkflowTranslator) ValidateWorkflowDefinition(def WorkflowDefinition) []string {
	var errors []string

	if def.Name == "" {
		errors = append(errors, "Workflow name is required")
	}

	if len(def.Steps) == 0 {
		errors = append(errors, "Workflow must have at least one step")
	}

	// Check for required step types
	hasInfrastructure := false
	hasAgent := false
	hasAggregation := false

	for _, step := range def.Steps {
		switch step.Type {
		case "infrastructure":
			hasInfrastructure = true
		case "agent":
			hasAgent = true
		case "aggregation":
			hasAggregation = true
		}
	}

	if !hasInfrastructure {
		errors = append(errors, "Workflow must include at least one infrastructure discovery step")
	}

	if !hasAgent {
		errors = append(errors, "Workflow must include at least one AI agent step")
	}

	if !hasAggregation {
		errors = append(errors, "Workflow must include a result aggregation step")
	}

	return errors
}

// GenerateWorkflowMetadata generates metadata for workflow execution
func (wt *WorkflowTranslator) GenerateWorkflowMetadata(def WorkflowDefinition) map[string]interface{} {
	return map[string]interface{}{
		"name":        def.Name,
		"description": def.Description,
		"stepCount":   len(def.Steps),
		"hasHumanReview": func() bool {
			for _, step := range def.Steps {
				if step.Type == "human" {
					return true
				}
			}
			return false
		}(),
		"agentTypes": func() []string {
			var types []string
			for _, step := range def.Steps {
				if step.Type == "agent" {
					if agentType, ok := step.Config["agentType"].(string); ok {
						types = append(types, agentType)
					}
				}
			}
			return types
		}(),
	}
}
