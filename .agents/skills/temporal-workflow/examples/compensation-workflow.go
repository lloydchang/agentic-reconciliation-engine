package main

import (
    "time"
    "go.temporal.io/sdk/workflow"
    "go.temporal.io/sdk/temporal"
)

// CompensationWorkflow demonstrates compensation pattern
func CompensationWorkflow(ctx workflow.Context, input WorkflowInput) error {
    logger := workflow.GetLogger(ctx)
    logger.Info("Starting compensation workflow", "input", input)

    // Setup activity options
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

    // Define compensation function
    var compensation workflow.Compensation

    // Step 1: Create resource
    err := workflow.ExecuteActivity(ctx, CreateResourceActivity, input.ResourceID).Get(ctx, nil)
    if err != nil {
        return err
    }

    // Set compensation for Step 1
    compensation = func(ctx workflow.Context) error {
        return workflow.ExecuteActivity(ctx, DeleteResourceActivity, input.ResourceID).Get(ctx, nil)
    }

    // Step 2: Configure resource
    err = workflow.ExecuteActivity(ctx, ConfigureResourceActivity, input.ResourceID).Get(ctx, nil)
    if err != nil {
        // Trigger compensation
        if compensationErr := compensation(ctx); compensationErr != nil {
            logger.Error("Compensation failed", "error", compensationErr)
        }
        return err
    }

    // Update compensation for both steps
    previousCompensation := compensation
    compensation = func(ctx workflow.Context) error {
        // Undo Step 2
        err := workflow.ExecuteActivity(ctx, UnconfigureResourceActivity, input.ResourceID).Get(ctx, nil)
        if err != nil {
            return err
        }
        // Undo Step 1
        return previousCompensation(ctx)
    }

    // Step 3: Activate resource
    err = workflow.ExecuteActivity(ctx, ActivateResourceActivity, input.ResourceID).Get(ctx, nil)
    if err != nil {
        // Trigger full compensation
        if compensationErr := compensation(ctx); compensationErr != nil {
            logger.Error("Compensation failed", "error", compensationErr)
        }
        return err
    }

    logger.Info("Compensation workflow completed successfully")
    return nil
}
