package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"
)

// Sample workflow definitions for testing
func createSampleWorkflows() []*WorkflowDefinition {
	workflows := []*WorkflowDefinition{}

	// 1. Sequential workflow example
	sequentialWorkflow := &WorkflowDefinition{
		ID:          "sequential-deployment",
		Name:        "Sequential Application Deployment",
		Description: "Deploy an application through sequential steps",
		Version:     "1.0",
		Pattern:     PatternSequential,
		StartStep:   "validate-config",
		Steps: map[string]*WorkflowStep{
			"validate-config": {
				ID:          "validate-config",
				Name:        "Validate Configuration",
				Type:        "task",
				Description: "Validate deployment configuration",
				Parameters: map[string]interface{}{
					"task_type": "validation",
				},
				NextSteps: []string{"build-image"},
			},
			"build-image": {
				ID:          "build-image",
				Name:        "Build Docker Image",
				Type:        "task",
				Description: "Build application Docker image",
				Parameters: map[string]interface{}{
					"task_type": "build",
				},
				NextSteps: []string{"deploy-staging"},
			},
			"deploy-staging": {
				ID:          "deploy-staging",
				Name:        "Deploy to Staging",
				Type:        "task",
				Description: "Deploy application to staging environment",
				Parameters: map[string]interface{}{
					"task_type": "deployment",
					"environment": "staging",
				},
				NextSteps: []string{"run-tests"},
			},
			"run-tests": {
				ID:          "run-tests",
				Name:        "Run Integration Tests",
				Type:        "task",
				Description: "Execute integration test suite",
				Parameters: map[string]interface{}{
					"task_type": "testing",
				},
				NextSteps: []string{"deploy-production"},
			},
			"deploy-production": {
				ID:          "deploy-production",
				Name:        "Deploy to Production",
				Type:        "task",
				Description: "Deploy application to production environment",
				Parameters: map[string]interface{}{
					"task_type": "deployment",
					"environment": "production",
				},
				CompensationStep: "rollback-production",
			},
			"rollback-production": {
				ID:          "rollback-production",
				Name:        "Rollback Production",
				Type:        "task",
				Description: "Rollback production deployment",
				Parameters: map[string]interface{}{
					"task_type": "rollback",
					"environment": "production",
				},
			},
		},
		Variables: map[string]interface{}{
			"app_name": "my-app",
			"version": "1.2.3",
			"timeout": "300s",
		},
	}

	// 2. Parallel workflow example
	parallelWorkflow := &WorkflowDefinition{
		ID:          "parallel-monitoring-setup",
		Name:        "Parallel Monitoring Setup",
		Description: "Set up monitoring components in parallel",
		Version:     "1.0",
		Pattern:     PatternParallel,
		StartStep:   "setup-monitoring",
		Steps: map[string]*WorkflowStep{
			"setup-monitoring": {
				ID:          "setup-monitoring",
				Name:        "Setup Monitoring Infrastructure",
				Type:        "parallel",
				Description: "Set up monitoring components concurrently",
				ParallelSteps: []string{"setup-prometheus", "setup-grafana", "setup-alertmanager"},
			},
			"setup-prometheus": {
				ID:          "setup-prometheus",
				Name:        "Setup Prometheus",
				Type:        "task",
				Description: "Deploy Prometheus monitoring system",
				Parameters: map[string]interface{}{
					"task_type": "monitoring",
					"component": "prometheus",
				},
			},
			"setup-grafana": {
				ID:          "setup-grafana",
				Name:        "Setup Grafana",
				Type:        "task",
				Description: "Deploy Grafana dashboard",
				Parameters: map[string]interface{}{
					"task_type": "monitoring",
					"component": "grafana",
				},
			},
			"setup-alertmanager": {
				ID:          "setup-alertmanager",
				Name:        "Setup AlertManager",
				Type:        "task",
				Description: "Deploy AlertManager for notifications",
				Parameters: map[string]interface{}{
					"task_type": "monitoring",
					"component": "alertmanager",
				},
			},
		},
	}

	// 3. Conditional workflow example
	conditionalWorkflow := &WorkflowDefinition{
		ID:          "conditional-deployment",
		Name:        "Conditional Deployment",
		Description: "Deploy based on environment conditions",
		Version:     "1.0",
		Pattern:     PatternConditional,
		StartStep:   "check-environment",
		Steps: map[string]*WorkflowStep{
			"check-environment": {
				ID:          "check-environment",
				Name:        "Check Environment Status",
				Type:        "decision",
				Description: "Evaluate deployment conditions",
				Parameters: map[string]interface{}{
					"question": "Should we proceed with deployment?",
					"options": []interface{}{
						map[string]interface{}{
							"description": "Deploy to production if tests pass",
							"risk_level":  "medium",
							"impact":      "high",
						},
						map[string]interface{}{
							"description": "Deploy to staging for testing",
							"risk_level":  "low",
							"impact":      "medium",
						},
						map[string]interface{}{
							"description": "Cancel deployment due to issues",
							"risk_level":  "low",
							"impact":      "low",
						},
					},
				},
				Conditions: []Condition{
					{
						Variable:   "test_results",
						Operator:   "equals",
						Value:      "passed",
						NextStepID: "deploy-production",
					},
					{
						Variable:   "environment",
						Operator:   "equals",
						Value:      "staging",
						NextStepID: "deploy-staging",
					},
				},
			},
			"deploy-production": {
				ID:          "deploy-production",
				Name:        "Deploy to Production",
				Type:        "task",
				Description: "Production deployment",
				Parameters: map[string]interface{}{
					"task_type": "deployment",
					"environment": "production",
				},
			},
			"deploy-staging": {
				ID:          "deploy-staging",
				Name:        "Deploy to Staging",
				Type:        "task",
				Description: "Staging deployment",
				Parameters: map[string]interface{}{
					"task_type": "deployment",
					"environment": "staging",
				},
			},
		},
	}

	workflows = append(workflows, sequentialWorkflow, parallelWorkflow, conditionalWorkflow)
	return workflows
}

// Mock reasoning engine for testing
type MockReasoningEngine struct{}

func (mre *MockReasoningEngine) AnalyzeOptions(ctx context.Context, question string, options []DecisionOption, context map[string]interface{}) (*DecisionResult, error) {
	// Simple mock implementation - always return first option
	if len(options) > 0 {
		return &DecisionResult{
			ChosenOption: options[0],
			Confidence:   0.8,
			Reasoning:    "Mock decision for testing",
			RiskLevel:    options[0].RiskLevel,
		}, nil
	}
	return nil, fmt.Errorf("no options provided")
}

// Mock orchestrator for testing
type MockOrchestrator struct{}

func (mo *MockOrchestrator) Orchestrate(description string, tasks []Task, strategy string, priority int) (*OrchestrationResult, error) {
	results := []TaskResult{}
	for _, task := range tasks {
		results = append(results, TaskResult{
			TaskID:    task.ID,
			AgentID:   "mock-agent",
			Status:    "completed",
			Result:    map[string]interface{}{"output": "Task completed successfully"},
			Duration:  time.Second * 2,
			StartTime: time.Now().Add(-time.Second * 2),
			EndTime:   time.Now(),
		})
	}

	return &OrchestrationResult{
		RequestID:   fmt.Sprintf("req-%d", time.Now().Unix()),
		Status:      "completed",
		Results:     results,
		Duration:    time.Second * 5,
		CompletedAt: time.Now(),
		Metrics: OrchestrationMetrics{
			TotalTasks:     len(tasks),
			CompletedTasks: len(tasks),
			FailedTasks:    0,
			AverageDuration: time.Second * 2,
		},
	}, nil
}

func main() {
	fmt.Println("🚀 Workflow Engine Test Example")
	fmt.Println("=================================")

	// Initialize mock components
	mockReasoningEngine := &MockReasoningEngine{}
	mockOrchestrator := &MockOrchestrator{}

	// Initialize workflow engine
	err := InitWorkflowEngine(mockReasoningEngine, mockOrchestrator)
	if err != nil {
		log.Fatalf("Failed to initialize workflow engine: %v", err)
	}

	// Register sample workflows
	workflows := createSampleWorkflows()
	for _, workflow := range workflows {
		err := GlobalWorkflowEngine.RegisterWorkflow(workflow)
		if err != nil {
			log.Printf("Failed to register workflow %s: %v", workflow.ID, err)
			continue
		}
		fmt.Printf("✅ Registered workflow: %s\n", workflow.Name)
	}

	// Test sequential workflow
	fmt.Println("\n📋 Testing Sequential Workflow...")
	seqExecution, err := GlobalWorkflowEngine.StartWorkflow(nil, "sequential-deployment", map[string]interface{}{
		"app_name": "test-app",
		"version":  "1.0.0",
	})
	if err != nil {
		log.Printf("Failed to start sequential workflow: %v", err)
	} else {
		fmt.Printf("Started workflow execution: %s\n", seqExecution.InstanceID)
		time.Sleep(2 * time.Second) // Wait for completion
		fmt.Printf("Workflow status: %s\n", seqExecution.Status)
	}

	// Test parallel workflow
	fmt.Println("\n🔄 Testing Parallel Workflow...")
	parallelExecution, err := GlobalWorkflowEngine.StartWorkflow(nil, "parallel-monitoring-setup", map[string]interface{}{})
	if err != nil {
		log.Printf("Failed to start parallel workflow: %v", err)
	} else {
		fmt.Printf("Started workflow execution: %s\n", parallelExecution.InstanceID)
		time.Sleep(3 * time.Second) // Wait for completion
		fmt.Printf("Workflow status: %s\n", parallelExecution.Status)
	}

	// Test conditional workflow
	fmt.Println("\n🔀 Testing Conditional Workflow...")
	conditionalExecution, err := GlobalWorkflowEngine.StartWorkflow(nil, "conditional-deployment", map[string]interface{}{
		"test_results": "passed",
		"environment":  "production",
	})
	if err != nil {
		log.Printf("Failed to start conditional workflow: %v", err)
	} else {
		fmt.Printf("Started workflow execution: %s\n", conditionalExecution.InstanceID)
		time.Sleep(2 * time.Second) // Wait for completion
		fmt.Printf("Workflow status: %s\n", conditionalExecution.Status)
	}

	// Display execution results
	fmt.Println("\n📊 Execution Results Summary:")
	executions := GlobalWorkflowEngine.ListExecutions()
	for _, exec := range executions {
		fmt.Printf("\nWorkflow: %s\n", exec.InstanceID)
		fmt.Printf("Definition: %s\n", exec.DefinitionID)
		fmt.Printf("Status: %s\n", exec.Status)
		fmt.Printf("Duration: %v\n", exec.Duration)
		if exec.Error != "" {
			fmt.Printf("Error: %s\n", exec.Error)
		}
		fmt.Printf("Steps completed: %d\n", len(exec.StepResults))

		// Show step details
		for stepID, result := range exec.StepResults {
			fmt.Printf("  - %s: %s (%v)\n", stepID, result.Status, result.Duration)
		}
	}

	// Export workflow definitions as JSON
	fmt.Println("\n💾 Exporting workflow definitions...")
	for _, workflow := range workflows {
		jsonData, err := json.MarshalIndent(workflow, "", "  ")
		if err != nil {
			log.Printf("Failed to marshal workflow %s: %v", workflow.ID, err)
			continue
		}
		fmt.Printf("\n--- %s ---\n%s\n", workflow.Name, string(jsonData))
	}

	fmt.Println("\n✅ Workflow Engine Test Complete!")
}
