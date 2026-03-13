package workflows

import (
	"time"

	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// SkillExecutionWorkflow orchestrates the execution of a skill's steps
func SkillExecutionWorkflow(ctx workflow.Context, req types.SkillExecutionRequest) (types.SkillExecutionStatus, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting SkillExecutionWorkflow", "skill", req.SkillName)

	options := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, options)

	var acts *activities.SkillExecutionActivities

	// 1. Get Skill Definition
	var skillContent string
	err := workflow.ExecuteActivity(ctx, acts.GetSkillContentActivity, req.SkillName, req.Arguments).Get(ctx, &skillContent)
	if err != nil {
		return types.SkillExecutionStatus{Status: "Failed"}, err
	}

	// 2. Parse Steps
	var steps []types.SkillStep
	err = workflow.ExecuteActivity(ctx, acts.ParseSkillStepsActivity, skillContent).Get(ctx, &steps)
	if err != nil {
		return types.SkillExecutionStatus{Status: "Failed"}, err
	}

	status := types.SkillExecutionStatus{
		SkillName:   req.SkillName,
		TotalSteps:  len(steps),
		Status:      "Running",
		StepResults: make([]types.StepResult, 0),
	}

	// Set up query handler
	err = workflow.SetQueryHandler(ctx, "GetSkillExecutionStatus", func() (types.SkillExecutionStatus, error) {
		return status, nil
	})
	if err != nil {
		return types.SkillExecutionStatus{Status: "Failed"}, err
	}

	// 3. Execute Steps
	for i, step := range steps {
		status.CurrentStep = i + 1
		
		// Handle Human Gate
		if step.IsHumanGate {
			status.Status = "Paused"
			workflow.GetSignalChannel(ctx, "HumanApprovalSignal").Receive(ctx, nil)
			status.Status = "Running"
		}

		// Execute Step Activity
		var output string
		err = workflow.ExecuteActivity(ctx, acts.ExecuteSkillStepActivity, step).Get(ctx, &output)
		
		res := types.StepResult{
			StepNumber: step.Number,
			Output:     output,
			Success:    err == nil,
		}
		status.StepResults = append(status.StepResults, res)

		if err != nil {
			status.Status = "Failed"
			return status, err
		}
	}

	status.Status = "Completed"
	return status, nil
}
