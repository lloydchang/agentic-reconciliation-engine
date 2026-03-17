package workflow

import (
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/agents/internal/activities"
)

// AgentWorkflows defines the workflow orchestrations for agent activities
type AgentWorkflows struct {
	CostOptimizationWorkflow  func(ctx workflow.Context, input CostOptimizationInput) (string, error)
	SecurityScanWorkflow     func(ctx workflow.Context, input SecurityScanInput) (string, error)
	ClusterMonitorWorkflow  func(ctx workflow.Context, input ClusterMonitorInput) (string, error)
	DeploymentManagerWorkflow func(ctx workflow.Context, input DeploymentManagerInput) (string, error)
}

// CostOptimizationWorkflow implementation
func CostOptimizationWorkflow(ctx workflow.Context, input CostOptimizationInput) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting cost optimization workflow", "CloudProvider", input.CloudProvider, "Region", input.Region)
	
	// Execute cost optimization activity
	options := workflow.ActivityOptions{
		ScheduleToCloseTimeout: time.Minute * 30,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 5,
			BackoffCoefficient: 2.0,
			MaximumAttempts:    3,
		},
	}
	
	recommendations := workflow.ExecuteActivity(ctx, activities.CostOptimizerActivity, input, options)
	
	// Could execute additional activities based on recommendations
	if recommendations != "" {
		logger.Info("Cost optimization workflow completed", "Recommendations", recommendations)
	}
	
	return recommendations, nil
}

// SecurityScanWorkflow implementation
func SecurityScanWorkflow(ctx workflow.Context, input SecurityScanInput) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting security scan workflow", "Target", input.Target, "Scope", input.Scope)
	
	// Execute security scan activity
	options := workflow.ActivityOptions{
		ScheduleToCloseTimeout: time.Minute * 15,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 3,
			BackoffCoefficient: 1.5,
			MaximumAttempts:    2,
		},
	}
	
	findings := workflow.ExecuteActivity(ctx, activities.SecurityScanActivity, input, options)
	
	logger.Info("Security scan workflow completed", "Findings", findings)
	return findings, nil
}

// ClusterMonitorWorkflow implementation
func ClusterMonitorWorkflow(ctx workflow.Context, input ClusterMonitorInput) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting cluster monitor workflow", "ClusterName", input.ClusterName, "Metrics", input.Metrics)
	
	// Execute cluster monitoring activity
	options := workflow.ActivityOptions{
		ScheduleToCloseTimeout: time.Minute * 10,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 2,
			BackoffCoefficient: 1.2,
			MaximumAttempts:    5,
		},
	}
	
	status := workflow.ExecuteActivity(ctx, activities.ClusterMonitorActivity, input, options)
	
	logger.Info("Cluster monitor workflow completed", "Status", status)
	return status, nil
}

// DeploymentManagerWorkflow implementation
func DeploymentManagerWorkflow(ctx workflow.Context, input DeploymentManagerInput) (string, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting deployment manager workflow", "Application", input.Application, "Environment", input.Environment)
	
	// Execute deployment manager activity
	options := workflow.ActivityOptions{
		ScheduleToCloseTimeout: time.Minute * 45,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 10,
			BackoffCoefficient: 2.0,
			MaximumAttempts:    3,
		},
	}
	
	result := workflow.ExecuteActivity(ctx, activities.DeploymentManagerActivity, input, options)
	
	logger.Info("Deployment manager workflow completed", "Result", result)
	return result, nil
}

// Register workflows with Temporal
func RegisterAgentWorkflows(w workflow.Workflow) {
	workflow.RegisterWorkflowWithOptions(AgentWorkflows{}.CostOptimizationWorkflow, workflow.RegisterOptions{
		Name:        "CostOptimizationWorkflow",
		Description: "Orchestrate cost optimization across cloud providers",
	})
	
	workflow.RegisterWorkflowWithOptions(AgentWorkflows{}.SecurityScanWorkflow, workflow.RegisterOptions{
		Name:        "SecurityScanWorkflow",
		Description: "Orchestrate security scanning and vulnerability assessment",
	})
	
	workflow.RegisterWorkflowWithOptions(AgentWorkflows{}.ClusterMonitorWorkflow, workflow.RegisterOptions{
		Name:        "ClusterMonitorWorkflow", 
		Description: "Orchestrate cluster health monitoring and performance analysis",
	})
	
	workflow.RegisterWorkflowWithOptions(AgentWorkflows{}.DeploymentManagerWorkflow, workflow.RegisterOptions{
		Name:        "DeploymentManagerWorkflow",
		Description: "Orchestrate application deployment and rollout management",
	})
}
