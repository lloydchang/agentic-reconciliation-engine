package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"go.temporal.io/sdk/workflow"
)

// WorkflowPattern represents different workflow execution patterns
type WorkflowPattern string

const (
	PatternSequential  WorkflowPattern = "sequential"
	PatternParallel    WorkflowPattern = "parallel"
	PatternConditional WorkflowPattern = "conditional"
	PatternEventDriven WorkflowPattern = "event_driven"
	PatternLoop        WorkflowPattern = "loop"
	PatternCompensation WorkflowPattern = "compensation"
)

// WorkflowStep represents a single step in a complex workflow
type WorkflowStep struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`        // "task", "decision", "wait", "parallel", "compensation"
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
	Timeout     *time.Duration         `json:"timeout,omitempty"`
	RetryPolicy *RetryPolicy           `json:"retry_policy,omitempty"`
	NextSteps   []string               `json:"next_steps,omitempty"`   // For sequential flows
	Conditions  []Condition            `json:"conditions,omitempty"`   // For conditional flows
	ParallelSteps []string             `json:"parallel_steps,omitempty"` // For parallel execution
	CompensationStep string            `json:"compensation_step,omitempty"` // For error compensation
}

// Condition represents a decision condition in workflows
type Condition struct {
	Variable   string      `json:"variable"`
	Operator   string      `json:"operator"` // "equals", "not_equals", "greater_than", "less_than", "contains", "not_contains"
	Value      interface{} `json:"value"`
	NextStepID string      `json:"next_step_id"`
}

// RetryPolicy defines retry behavior for workflow steps
type RetryPolicy struct {
	MaxAttempts      int           `json:"max_attempts"`
	InitialInterval  time.Duration `json:"initial_interval"`
	BackoffCoefficient float64     `json:"backoff_coefficient"`
	MaximumInterval  time.Duration `json:"maximum_interval"`
}

// WorkflowDefinition represents a complete workflow definition
type WorkflowDefinition struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Version     string                 `json:"version"`
	Pattern     WorkflowPattern        `json:"pattern"`
	StartStep   string                 `json:"start_step"`
	Steps       map[string]*WorkflowStep `json:"steps"`
	Variables   map[string]interface{} `json:"variables,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// WorkflowExecution represents the execution state of a workflow
type WorkflowExecution struct {
	InstanceID    string                 `json:"instance_id"`
	DefinitionID  string                 `json:"definition_id"`
	Status        string                 `json:"status"` // "running", "completed", "failed", "compensating"
	CurrentStep   string                 `json:"current_step,omitempty"`
	StepResults   map[string]*StepResult `json:"step_results"`
	Variables     map[string]interface{} `json:"variables"`
	StartTime     time.Time              `json:"start_time"`
	EndTime       *time.Time             `json:"end_time,omitempty"`
	Duration      *time.Duration         `json:"duration,omitempty"`
	Error         string                 `json:"error,omitempty"`
	CompensationLog []string             `json:"compensation_log,omitempty"`
}

// StepResult represents the result of executing a workflow step
type StepResult struct {
	StepID      string      `json:"step_id"`
	Status      string      `json:"status"` // "pending", "running", "completed", "failed", "skipped", "compensated"
	StartTime   time.Time   `json:"start_time"`
	EndTime     *time.Time  `json:"end_time,omitempty"`
	Duration    *time.Duration `json:"duration,omitempty"`
	Result      interface{} `json:"result,omitempty"`
	Error       string      `json:"error,omitempty"`
	Attempts    int         `json:"attempts"`
}

// WorkflowEngine manages complex workflow execution
type WorkflowEngine struct {
	definitions map[string]*WorkflowDefinition
	executions  map[string]*WorkflowExecution
	reasoningEngine *ReasoningEngine
	orchestrator *MultiAgentOrchestrator
}

// NewWorkflowEngine creates a new workflow engine
func NewWorkflowEngine(reasoningEngine *ReasoningEngine, orchestrator *MultiAgentOrchestrator) *WorkflowEngine {
	return &WorkflowEngine{
		definitions: make(map[string]*WorkflowDefinition),
		executions:  make(map[string]*WorkflowExecution),
		reasoningEngine: reasoningEngine,
		orchestrator: orchestrator,
	}
}

// RegisterWorkflow registers a new workflow definition
func (we *WorkflowEngine) RegisterWorkflow(definition *WorkflowDefinition) error {
	// Validate workflow definition
	if err := we.validateWorkflowDefinition(definition); err != nil {
		return fmt.Errorf("invalid workflow definition: %v", err)
	}

	we.definitions[definition.ID] = definition
	log.Printf("Registered workflow: %s (%s)", definition.Name, definition.ID)
	return nil
}

// validateWorkflowDefinition validates a workflow definition
func (we *WorkflowEngine) validateWorkflowDefinition(definition *WorkflowDefinition) error {
	if definition.ID == "" {
		return fmt.Errorf("workflow ID is required")
	}
	if definition.StartStep == "" {
		return fmt.Errorf("start step is required")
	}
	if len(definition.Steps) == 0 {
		return fmt.Errorf("at least one step is required")
	}

	// Check that start step exists
	if _, exists := definition.Steps[definition.StartStep]; !exists {
		return fmt.Errorf("start step '%s' not found in steps", definition.StartStep)
	}

	// Validate step references
	for stepID, step := range definition.Steps {
		if step.ID != stepID {
			return fmt.Errorf("step ID mismatch: %s vs %s", step.ID, stepID)
		}

		// Validate next steps exist
		for _, nextStep := range step.NextSteps {
			if _, exists := definition.Steps[nextStep]; !exists {
				return fmt.Errorf("next step '%s' not found in step '%s'", nextStep, stepID)
			}
		}

		// Validate parallel steps exist
		for _, parallelStep := range step.ParallelSteps {
			if _, exists := definition.Steps[parallelStep]; !exists {
				return fmt.Errorf("parallel step '%s' not found in step '%s'", parallelStep, stepID)
			}
		}

		// Validate compensation step exists
		if step.CompensationStep != "" {
			if _, exists := definition.Steps[step.CompensationStep]; !exists {
				return fmt.Errorf("compensation step '%s' not found in step '%s'", step.CompensationStep, stepID)
			}
		}
	}

	return nil
}

// StartWorkflow starts execution of a workflow
func (we *WorkflowEngine) StartWorkflow(ctx context.Context, definitionID string, inputVariables map[string]interface{}) (*WorkflowExecution, error) {
	definition, exists := we.definitions[definitionID]
	if !exists {
		return nil, fmt.Errorf("workflow definition '%s' not found", definitionID)
	}

	execution := &WorkflowExecution{
		InstanceID:   fmt.Sprintf("wf-%s-%d", definitionID, time.Now().Unix()),
		DefinitionID: definitionID,
		Status:       "running",
		CurrentStep:  definition.StartStep,
		StepResults:  make(map[string]*StepResult),
		Variables:    make(map[string]interface{}),
		StartTime:    time.Now(),
	}

	// Merge input variables with default variables
	for k, v := range definition.Variables {
		execution.Variables[k] = v
	}
	for k, v := range inputVariables {
		execution.Variables[k] = v
	}

	we.executions[execution.InstanceID] = execution

	log.Printf("Started workflow execution: %s for definition: %s", execution.InstanceID, definitionID)

	// Start execution in background
	go we.executeWorkflow(ctx, execution)

	return execution, nil
}

// executeWorkflow executes a workflow instance
func (we *WorkflowEngine) executeWorkflow(ctx context.Context, execution *WorkflowExecution) {
	definition := we.definitions[execution.DefinitionID]

	defer func() {
		if r := recover(); r != nil {
			execution.Status = "failed"
			execution.Error = fmt.Sprintf("panic: %v", r)
			now := time.Now()
			execution.EndTime = &now
			duration := time.Since(execution.StartTime)
			execution.Duration = &duration
			log.Printf("Workflow %s failed with panic: %v", execution.InstanceID, r)
		}
	}()

	switch definition.Pattern {
	case PatternSequential:
		we.executeSequentialWorkflow(ctx, execution, definition)
	case PatternParallel:
		we.executeParallelWorkflow(ctx, execution, definition)
	case PatternConditional:
		we.executeConditionalWorkflow(ctx, execution, definition)
	case PatternEventDriven:
		we.executeEventDrivenWorkflow(ctx, execution, definition)
	case PatternLoop:
		we.executeLoopWorkflow(ctx, execution, definition)
	case PatternCompensation:
		we.executeCompensationWorkflow(ctx, execution, definition)
	default:
		execution.Status = "failed"
		execution.Error = fmt.Sprintf("unsupported workflow pattern: %s", definition.Pattern)
	}

	now := time.Now()
	execution.EndTime = &now
	duration := time.Since(execution.StartTime)
	execution.Duration = &duration

	if execution.Status == "running" {
		execution.Status = "completed"
	}

	log.Printf("Workflow %s completed with status: %s", execution.InstanceID, execution.Status)
}

// executeSequentialWorkflow executes steps in sequence
func (we *WorkflowEngine) executeSequentialWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	currentStepID := definition.StartStep

	for currentStepID != "" {
		step := definition.Steps[currentStepID]

		// Execute current step
		result, err := we.executeStep(ctx, execution, step)
		execution.StepResults[step.ID] = result

		if err != nil {
			execution.Status = "failed"
			execution.Error = fmt.Sprintf("step %s failed: %v", step.ID, err)
			we.executeCompensation(ctx, execution, definition, step)
			return
		}

		// Determine next step
		if len(step.NextSteps) > 0 {
			currentStepID = step.NextSteps[0]
		} else {
			currentStepID = ""
		}
	}
}

// executeParallelWorkflow executes multiple steps in parallel
func (we *WorkflowEngine) executeParallelWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	startStep := definition.Steps[definition.StartStep]

	if len(startStep.ParallelSteps) == 0 {
		execution.Status = "failed"
		execution.Error = "parallel workflow requires parallel steps"
		return
	}

	// Execute all parallel steps concurrently
	type stepResult struct {
		stepID string
		result *StepResult
		err    error
	}

	results := make(chan stepResult, len(startStep.ParallelSteps))

	for _, stepID := range startStep.ParallelSteps {
		go func(sid string) {
			step := definition.Steps[sid]
			result, err := we.executeStep(ctx, execution, step)
			results <- stepResult{stepID: sid, result: result, err: err}
		}(stepID)
	}

	// Collect results
	var errors []string
	for i := 0; i < len(startStep.ParallelSteps); i++ {
		res := <-results
		execution.StepResults[res.stepID] = res.result
		if res.err != nil {
			errors = append(errors, fmt.Sprintf("step %s: %v", res.stepID, res.err))
		}
	}

	if len(errors) > 0 {
		execution.Status = "failed"
		execution.Error = fmt.Sprintf("parallel execution failed: %v", errors)
	}
}

// executeConditionalWorkflow executes steps based on conditions
func (we *WorkflowEngine) executeConditionalWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	currentStepID := definition.StartStep

	for currentStepID != "" {
		step := definition.Steps[currentStepID]

		// Execute current step
		result, err := we.executeStep(ctx, execution, step)
		execution.StepResults[step.ID] = result

		if err != nil {
			execution.Status = "failed"
			execution.Error = fmt.Sprintf("step %s failed: %v", step.ID, err)
			we.executeCompensation(ctx, execution, definition, step)
			return
		}

		// Evaluate conditions to determine next step
		currentStepID = we.evaluateConditions(step.Conditions, execution.Variables)
	}
}

// evaluateConditions evaluates workflow conditions
func (we *WorkflowEngine) evaluateConditions(conditions []Condition, variables map[string]interface{}) string {
	for _, condition := range conditions {
		variableValue, exists := variables[condition.Variable]
		if !exists {
			continue
		}

		matches := false

		switch condition.Operator {
		case "equals":
			matches = variableValue == condition.Value
		case "not_equals":
			matches = variableValue != condition.Value
		case "greater_than":
			if v, ok := variableValue.(float64); ok {
				if c, ok := condition.Value.(float64); ok {
					matches = v > c
				}
			}
		case "less_than":
			if v, ok := variableValue.(float64); ok {
				if c, ok := condition.Value.(float64); ok {
					matches = v < c
				}
			}
		case "contains":
			if v, ok := variableValue.(string); ok {
				if c, ok := condition.Value.(string); ok {
					matches = strings.Contains(v, c)
				}
			}
		case "not_contains":
			if v, ok := variableValue.(string); ok {
				if c, ok := condition.Value.(string); ok {
					matches = !strings.Contains(v, c)
				}
			}
		}

		if matches {
			return condition.NextStepID
		}
	}

	return "" // No condition matched
}

// executeEventDrivenWorkflow executes steps based on events
func (we *WorkflowEngine) executeEventDrivenWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	// Simplified event-driven execution - in practice, this would listen for events
	currentStepID := definition.StartStep

	for currentStepID != "" {
		step := definition.Steps[currentStepID]

		// For event-driven steps, wait for events
		if step.Type == "wait" {
			eventName, ok := step.Parameters["event"].(string)
			if ok {
				log.Printf("Workflow %s waiting for event: %s", execution.InstanceID, eventName)
				// In a real implementation, this would wait for external events
				time.Sleep(1 * time.Second) // Simulate waiting
			}
		}

		// Execute step
		result, err := we.executeStep(ctx, execution, step)
		execution.StepResults[step.ID] = result

		if err != nil {
			execution.Status = "failed"
			execution.Error = fmt.Sprintf("step %s failed: %v", step.ID, err)
			return
		}

		// Simple progression to next step
		if len(step.NextSteps) > 0 {
			currentStepID = step.NextSteps[0]
		} else {
			currentStepID = ""
		}
	}
}

// executeLoopWorkflow executes steps in a loop
func (we *WorkflowEngine) executeLoopWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	maxIterations := 10 // Default max iterations
	if val, ok := definition.Metadata["max_iterations"].(float64); ok {
		maxIterations = int(val)
	}

	iterations := 0
	currentStepID := definition.StartStep

	for currentStepID != "" && iterations < maxIterations {
		step := definition.Steps[currentStepID]

		// Execute step
		result, err := we.executeStep(ctx, execution, step)
		execution.StepResults[fmt.Sprintf("%s_%d", step.ID, iterations)] = result

		if err != nil {
			execution.Status = "failed"
			execution.Error = fmt.Sprintf("step %s failed at iteration %d: %v", step.ID, iterations, err)
			return
		}

		// Check loop condition
		if we.shouldContinueLoop(step, execution.Variables) {
			// Reset to start step for next iteration
			currentStepID = definition.StartStep
			iterations++
		} else {
			// Exit loop
			if len(step.NextSteps) > 0 {
				currentStepID = step.NextSteps[0]
			} else {
				currentStepID = ""
			}
		}
	}

	if iterations >= maxIterations {
		execution.Status = "failed"
		execution.Error = "maximum loop iterations exceeded"
	}
}

// shouldContinueLoop determines if a loop should continue
func (we *WorkflowEngine) shouldContinueLoop(step *WorkflowStep, variables map[string]interface{}) bool {
	if conditionVar, ok := step.Parameters["loop_condition"].(string); ok {
		if value, exists := variables[conditionVar]; exists {
			if boolVal, ok := value.(bool); ok {
				return boolVal
			}
		}
	}
	return false // Default to not continuing
}

// executeCompensationWorkflow executes a compensation workflow
func (we *WorkflowEngine) executeCompensationWorkflow(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition) {
	// Compensation workflows handle error scenarios
	currentStepID := definition.StartStep

	for currentStepID != "" {
		step := definition.Steps[currentStepID]

		// Execute compensation step
		result, err := we.executeStep(ctx, execution, step)
		execution.StepResults[step.ID] = result

		if err != nil {
			log.Printf("Compensation step %s failed: %v", step.ID, err)
			// Continue with other compensation steps even if one fails
		}

		// Move to next compensation step
		if len(step.NextSteps) > 0 {
			currentStepID = step.NextSteps[0]
		} else {
			currentStepID = ""
		}
	}
}

// executeStep executes a single workflow step
func (we *WorkflowEngine) executeStep(ctx context.Context, execution *WorkflowExecution, step *WorkflowStep) (*StepResult, error) {
	startTime := time.Now()

	result := &StepResult{
		StepID:    step.ID,
		Status:    "running",
		StartTime: startTime,
		Attempts:  0,
	}

	// Apply timeout if specified
	stepCtx := ctx
	if step.Timeout != nil {
		var cancel context.CancelFunc
		stepCtx, cancel = context.WithTimeout(ctx, *step.Timeout)
		defer cancel()
	}

	var lastErr error
	var stepResult interface{}

	// Apply retry policy
	maxAttempts := 1
	if step.RetryPolicy != nil {
		maxAttempts = step.RetryPolicy.MaxAttempts
	}

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		result.Attempts = attempt

		// Execute step based on type
		switch step.Type {
		case "task":
			stepResult, lastErr = we.executeTaskStep(stepCtx, execution, step)
		case "decision":
			stepResult, lastErr = we.executeDecisionStep(stepCtx, execution, step)
		case "wait":
			stepResult, lastErr = we.executeWaitStep(stepCtx, execution, step)
		case "parallel":
			stepResult, lastErr = we.executeParallelStep(stepCtx, execution, step)
		default:
			lastErr = fmt.Errorf("unsupported step type: %s", step.Type)
		}

		if lastErr == nil {
			break
		}

		// Wait before retry if not the last attempt
		if attempt < maxAttempts && step.RetryPolicy != nil {
			retryDelay := time.Duration(float64(step.RetryPolicy.InitialInterval) * pow(step.RetryPolicy.BackoffCoefficient, attempt-1))
			if retryDelay > step.RetryPolicy.MaximumInterval {
				retryDelay = step.RetryPolicy.MaximumInterval
			}
			time.Sleep(retryDelay)
		}
	}

	endTime := time.Now()
	duration := time.Since(startTime)
	result.EndTime = &endTime
	result.Duration = &duration

	if lastErr != nil {
		result.Status = "failed"
		result.Error = lastErr.Error()
	} else {
		result.Status = "completed"
		result.Result = stepResult
	}

	return result, lastErr
}

// executeTaskStep executes a task step using the orchestrator
func (we *WorkflowEngine) executeTaskStep(ctx context.Context, execution *WorkflowExecution, step *WorkflowStep) (interface{}, error) {
	taskType, ok := step.Parameters["task_type"].(string)
	if !ok {
		return nil, fmt.Errorf("task_type parameter required for task step")
	}

	task := Task{
		ID:          fmt.Sprintf("%s_%s", execution.InstanceID, step.ID),
		Type:        taskType,
		Description: step.Description,
		Priority:    2, // Default priority
		Parameters:  step.Parameters,
		Status:      "pending",
		CreatedAt:   time.Now(),
	}

	if priority, ok := step.Parameters["priority"].(float64); ok {
		task.Priority = int(priority)
	}

	// Execute task through orchestrator
	tasks := []Task{task}
	result, err := Orchestrate(fmt.Sprintf("Workflow step: %s", step.Name), tasks, "sequential", task.Priority)
	if err != nil {
		return nil, err
	}

	if len(result.Results) == 0 {
		return nil, fmt.Errorf("no results from task execution")
	}

	taskResult := result.Results[0]
	if taskResult.Status != "completed" {
		return nil, fmt.Errorf("task failed: %s", taskResult.Error)
	}

	return taskResult.Result, nil
}

// executeDecisionStep executes a decision step using the reasoning engine
func (we *WorkflowEngine) executeDecisionStep(ctx context.Context, execution *WorkflowExecution, step *WorkflowStep) (interface{}, error) {
	if we.reasoningEngine == nil {
		return nil, fmt.Errorf("reasoning engine not available for decision step")
	}

	question, ok := step.Parameters["question"].(string)
	if !ok {
		return nil, fmt.Errorf("question parameter required for decision step")
	}

	var options []DecisionOption
	if opts, ok := step.Parameters["options"].([]interface{}); ok {
		for i, opt := range opts {
			if optMap, ok := opt.(map[string]interface{}); ok {
				desc, _ := optMap["description"].(string)
				risk, _ := optMap["risk_level"].(string)
				impact, _ := optMap["impact"].(string)

				option := DecisionOption{
					OptionID:    fmt.Sprintf("option_%d", i),
					Description: desc,
					RiskLevel:   risk,
					Impact:      impact,
					Score:       0.5, // Default score
				}
				options = append(options, option)
			}
		}
	}

	context := map[string]interface{}{
		"workflow_context": execution.Variables,
		"max_risk_level":   "high",
		"impact_weight":    0.3,
	}

	decision, err := we.reasoningEngine.AnalyzeOptions(ctx, question, options, context)
	if err != nil {
		return nil, err
	}

	// Store decision result in execution variables
	execution.Variables[fmt.Sprintf("decision_%s", step.ID)] = decision.ChosenOption.OptionID

	return decision, nil
}

// executeWaitStep executes a wait step
func (we *WorkflowEngine) executeWaitStep(ctx context.Context, execution *WorkflowExecution, step *WorkflowStep) (interface{}, error) {
	durationStr, ok := step.Parameters["duration"].(string)
	if !ok {
		return nil, fmt.Errorf("duration parameter required for wait step")
	}

	duration, err := time.ParseDuration(durationStr)
	if err != nil {
		return nil, fmt.Errorf("invalid duration format: %v", err)
	}

	select {
	case <-time.After(duration):
		return map[string]interface{}{"waited": duration.String()}, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// executeParallelStep executes multiple steps in parallel within a single step
func (we *WorkflowEngine) executeParallelStep(ctx context.Context, execution *WorkflowExecution, step *WorkflowStep) (interface{}, error) {
	if len(step.ParallelSteps) == 0 {
		return nil, fmt.Errorf("parallel step requires parallel_steps parameter")
	}

	type parallelResult struct {
		stepID string
		result interface{}
		err    error
	}

	results := make(chan parallelResult, len(step.ParallelSteps))

	for _, stepID := range step.ParallelSteps {
		go func(sid string) {
			pStep := we.definitions[execution.DefinitionID].Steps[sid]
			result, err := we.executeStep(ctx, execution, pStep)
			var res interface{}
			if result != nil {
				res = result.Result
			}
			results <- parallelResult{stepID: sid, result: res, err: err}
		}(stepID)
	}

	parallelResults := make(map[string]interface{})
	var errors []string

	for i := 0; i < len(step.ParallelSteps); i++ {
		res := <-results
		if res.err != nil {
			errors = append(errors, fmt.Sprintf("%s: %v", res.stepID, res.err))
		} else {
			parallelResults[res.stepID] = res.result
		}
	}

	if len(errors) > 0 {
		return parallelResults, fmt.Errorf("parallel execution errors: %v", errors)
	}

	return parallelResults, nil
}

// executeCompensation executes compensation steps when a step fails
func (we *WorkflowEngine) executeCompensation(ctx context.Context, execution *WorkflowExecution, definition *WorkflowDefinition, failedStep *WorkflowStep) {
	if failedStep.CompensationStep == "" {
		return
	}

	execution.Status = "compensating"
	log.Printf("Starting compensation for failed step: %s", failedStep.ID)

	compensationStep := definition.Steps[failedStep.CompensationStep]
	result, err := we.executeStep(ctx, execution, compensationStep)

	if execution.CompensationLog == nil {
		execution.CompensationLog = make([]string, 0)
	}

	if err != nil {
		execution.CompensationLog = append(execution.CompensationLog, fmt.Sprintf("Compensation failed for step %s: %v", failedStep.ID, err))
		log.Printf("Compensation failed for step %s: %v", failedStep.ID, err)
	} else {
		execution.CompensationLog = append(execution.CompensationLog, fmt.Sprintf("Compensation completed for step %s", failedStep.ID))
		log.Printf("Compensation completed for step %s", failedStep.ID)
	}

	execution.StepResults[compensationStep.ID] = result
}

// pow calculates power for retry backoff
func pow(base float64, exp int) float64 {
	result := 1.0
	for i := 0; i < exp; i++ {
		result *= base
	}
	return result
}

// GetExecution returns a workflow execution by ID
func (we *WorkflowEngine) GetExecution(instanceID string) (*WorkflowExecution, error) {
	execution, exists := we.executions[instanceID]
	if !exists {
		return nil, fmt.Errorf("workflow execution '%s' not found", instanceID)
	}
	return execution, nil
}

// ListExecutions returns all workflow executions
func (we *WorkflowEngine) ListExecutions() []*WorkflowExecution {
	executions := make([]*WorkflowExecution, 0, len(we.executions))
	for _, execution := range we.executions {
		executions = append(executions, execution)
	}
	return executions
}

// WorkflowExecutionActivity is a Temporal activity for workflow execution
func WorkflowExecutionActivity(ctx context.Context, definitionID string, inputVariables map[string]interface{}) (*WorkflowExecution, error) {
	return GlobalWorkflowEngine.StartWorkflow(ctx, definitionID, inputVariables)
}

// ComplexWorkflowExecutionWorkflow is a Temporal workflow for complex workflow execution
func ComplexWorkflowExecutionWorkflow(ctx workflow.Context, definitionID string, inputVariables map[string]interface{}) (*WorkflowExecution, error) {
	// Configure workflow options
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 600 * time.Second, // 10 minutes for complex workflows
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    60 * time.Second,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result *WorkflowExecution
	err := workflow.ExecuteActivity(ctx, WorkflowExecutionActivity, definitionID, inputVariables).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	// Wait for workflow completion (simplified - in practice, this would use signals/queries)
	for result.Status == "running" {
		workflow.Sleep(ctx, 5*time.Second)
		// In a real implementation, you'd use workflow side effects or queries to check status
		result, _ = GlobalWorkflowEngine.GetExecution(result.InstanceID)
		if result == nil {
			break
		}
	}

	return result, nil
}

// Global workflow engine instance
var GlobalWorkflowEngine *WorkflowEngine

// InitWorkflowEngine initializes the global workflow engine
func InitWorkflowEngine(reasoningEngine *ReasoningEngine, orchestrator *MultiAgentOrchestrator) error {
	GlobalWorkflowEngine = NewWorkflowEngine(reasoningEngine, orchestrator)
	return nil
}

// ExecuteWorkflow provides a simple interface for workflow execution
func ExecuteWorkflow(definitionID string, inputVariables map[string]interface{}) (*WorkflowExecution, error) {
	if GlobalWorkflowEngine == nil {
		return nil, fmt.Errorf("workflow engine not initialized")
	}

	return GlobalWorkflowEngine.StartWorkflow(context.Background(), definitionID, inputVariables)
}

// CreateWorkflowDefinition creates a workflow definition from a JSON string
func CreateWorkflowDefinition(jsonDefinition string) (*WorkflowDefinition, error) {
	var definition WorkflowDefinition
	err := json.Unmarshal([]byte(jsonDefinition), &definition)
	if err != nil {
		return nil, fmt.Errorf("failed to parse workflow definition: %v", err)
	}
	return &definition, nil
}
