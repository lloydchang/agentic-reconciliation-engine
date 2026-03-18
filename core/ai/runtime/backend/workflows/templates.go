package workflows

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/workflow"
)

// WorkflowTemplate defines a reusable multi-agent workflow template
type WorkflowTemplate struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Version     string                 `json:"version"`
	Category    string                 `json:"category"`
	Steps       []WorkflowStep         `json:"steps"`
	Inputs      map[string]interface{} `json:"inputs"`
	Outputs     map[string]interface{} `json:"outputs"`
	Metadata    WorkflowMetadata       `json:"metadata"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// WorkflowStep defines a step in a workflow
type WorkflowStep struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	SkillName    string                 `json:"skill_name"`
	Type         StepType               `json:"type"`
	Dependencies []string               `json:"dependencies"`
	Inputs       map[string]interface{} `json:"inputs"`
	Outputs      map[string]interface{} `json:"outputs"`
	Config       StepConfig             `json:"config"`
	Timeout      time.Duration          `json:"timeout"`
	RetryPolicy  *RetryPolicy           `json:"retry_policy,omitempty"`
}

// StepType defines the type of workflow step
type StepType string

const (
	StepTypeSkill     StepType = "skill"
	StepTypeParallel  StepType = "parallel"
	StepTypeSequence  StepType = "sequence"
	StepTypeCondition StepType = "condition"
	StepTypeLoop      StepType = "loop"
)

// StepConfig defines step configuration
type StepConfig struct {
	Async        bool                   `json:"async"`
	Background   bool                   `json:"background"`
	Notifications []NotificationConfig `json:"notifications"`
	Environment  map[string]interface{} `json:"environment"`
}

// RetryPolicy defines retry policy for steps
type RetryPolicy struct {
	MaxAttempts      int           `json:"max_attempts"`
	InitialInterval  time.Duration `json:"initial_interval"`
	MaximumInterval  time.Duration `json:"maximum_interval"`
	BackoffCoefficient float64     `json:"backoff_coefficient"`
	NonRetryableErrors []string    `json:"non_retryable_errors"`
}

// NotificationConfig defines notification configuration
type NotificationConfig struct {
	OnStart   []string `json:"on_start"`
	OnSuccess []string `json:"on_success"`
	OnFailure []string `json:"on_failure"`
	Channels  []string `json:"channels"`
}

// WorkflowMetadata defines workflow metadata
type WorkflowMetadata struct {
	Author      string            `json:"author"`
	Tags        []string          `json:"tags"`
	EstimatedDuration time.Duration `json:"estimated_duration"`
	RiskLevel   string            `json:"risk_level"`
	RequiredRoles []string        `json:"required_roles"`
	Parameters  map[string]Parameter `json:"parameters"`
}

// Parameter defines a workflow parameter
type Parameter struct {
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Required    bool        `json:"required"`
	Default     interface{} `json:"default,omitempty"`
	Description string      `json:"description"`
	Validation  string      `json:"validation,omitempty"`
}

// WorkflowExecution represents a running workflow instance
type WorkflowExecution struct {
	ID          string                 `json:"id"`
	TemplateID  string                 `json:"template_id"`
	Status      ExecutionStatus        `json:"status"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time,omitempty"`
	Inputs      map[string]interface{} `json:"inputs"`
	Outputs     map[string]interface{} `json:"outputs,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Progress    float64                `json:"progress"`
	StepResults map[string]StepResult  `json:"step_results"`
	Metadata    ExecutionMetadata      `json:"metadata"`
}

// ExecutionStatus represents workflow execution status
type ExecutionStatus string

const (
	ExecutionStatusPending   ExecutionStatus = "pending"
	ExecutionStatusRunning   ExecutionStatus = "running"
	ExecutionStatusCompleted ExecutionStatus = "completed"
	ExecutionStatusFailed    ExecutionStatus = "failed"
	ExecutionStatusCancelled ExecutionStatus = "cancelled"
	ExecutionStatusPaused    ExecutionStatus = "paused"
)

// StepResult represents the result of a workflow step
type StepResult struct {
	StepID      string                 `json:"step_id"`
	Status      ExecutionStatus        `json:"status"`
	StartTime   time.Time              `json:"start_time"`
	EndTime     *time.Time             `json:"end_time,omitempty"`
	Output      map[string]interface{} `json:"output,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Duration    time.Duration          `json:"duration"`
	Retries     int                    `json:"retries"`
}

// ExecutionMetadata represents execution metadata
type ExecutionMetadata struct {
	UserID      string    `json:"user_id"`
	SessionID   string    `json:"session_id"`
	TriggeredBy string    `json:"triggered_by"`
	Environment string    `json:"environment"`
	TraceID     string    `json:"trace_id"`
}

// WorkflowEngine manages workflow templates and executions
type WorkflowEngine struct {
	mu           sync.RWMutex
	templates    map[string]*WorkflowTemplate
	executions   map[string]*WorkflowExecution
	temporalClient client.Client
	config       *EngineConfig
}

// EngineConfig defines workflow engine configuration
type EngineConfig struct {
	TemporalAddr         string        `json:"temporal_addr"`
	DefaultTimeout       time.Duration `json:"default_timeout"`
	MaxConcurrentWorkflows int         `json:"max_concurrent_workflows"`
	ExecutionRetention   time.Duration `json:"execution_retention"`
	TemplateStorage      string        `json:"template_storage"`
}

// NewWorkflowEngine creates a new workflow engine
func NewWorkflowEngine(config *EngineConfig) (*WorkflowEngine, error) {
	temporalClient, err := client.Dial(client.Options{
		HostPort: config.TemporalAddr,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create temporal client: %w", err)
	}

	return &WorkflowEngine{
		templates:     make(map[string]*WorkflowTemplate),
		executions:    make(map[string]*WorkflowExecution),
		temporalClient: temporalClient,
		config:        config,
	}, nil
}

// RegisterTemplate registers a new workflow template
func (we *WorkflowEngine) RegisterTemplate(template *WorkflowTemplate) error {
	we.mu.Lock()
	defer we.mu.Unlock()

	// Validate template
	if err := we.validateTemplate(template); err != nil {
		return fmt.Errorf("template validation failed: %w", err)
	}

	// Store template
	we.templates[template.ID] = template

	log.Printf("Registered workflow template: %s (%s)", template.ID, template.Name)
	return nil
}

// GetTemplate retrieves a workflow template
func (we *WorkflowEngine) GetTemplate(templateID string) (*WorkflowTemplate, error) {
	we.mu.RLock()
	defer we.mu.RUnlock()

	template, exists := we.templates[templateID]
	if !exists {
		return nil, fmt.Errorf("template not found: %s", templateID)
	}

	return template, nil
}

// ListTemplates lists available workflow templates
func (we *WorkflowEngine) ListTemplates(category string) ([]*WorkflowTemplate, error) {
	we.mu.RLock()
	defer we.mu.RUnlock()

	var templates []*WorkflowTemplate
	for _, template := range we.templates {
		if category == "" || template.Category == category {
			templates = append(templates, template)
		}
	}

	return templates, nil
}

// ExecuteWorkflow executes a workflow template
func (we *WorkflowEngine) ExecuteWorkflow(ctx context.Context, templateID string, inputs map[string]interface{}, metadata ExecutionMetadata) (*WorkflowExecution, error) {
	we.mu.Lock()
	defer we.mu.Unlock()

	// Get template
	template, exists := we.templates[templateID]
	if !exists {
		return nil, fmt.Errorf("template not found: %s", templateID)
	}

	// Validate inputs
	if err := we.validateInputs(template, inputs); err != nil {
		return nil, fmt.Errorf("input validation failed: %w", err)
	}

	// Create execution
	execution := &WorkflowExecution{
		ID:          generateExecutionID(),
		TemplateID:  templateID,
		Status:      ExecutionStatusPending,
		StartTime:   time.Now(),
		Inputs:      inputs,
		Progress:    0.0,
		StepResults: make(map[string]StepResult),
		Metadata:    metadata,
	}

	// Store execution
	we.executions[execution.ID] = execution

	// Start execution
	go we.executeWorkflowAsync(ctx, template, execution)

	log.Printf("Started workflow execution: %s for template: %s", execution.ID, templateID)
	return execution, nil
}

// GetExecution retrieves a workflow execution
func (we *WorkflowEngine) GetExecution(executionID string) (*WorkflowExecution, error) {
	we.mu.RLock()
	defer we.mu.RUnlock()

	execution, exists := we.executions[executionID]
	if !exists {
		return nil, fmt.Errorf("execution not found: %s", executionID)
	}

	return execution, nil
}

// CancelExecution cancels a running workflow execution
func (we *WorkflowEngine) CancelExecution(ctx context.Context, executionID string) error {
	we.mu.Lock()
	defer we.mu.Unlock()

	execution, exists := we.executions[executionID]
	if !exists {
		return fmt.Errorf("execution not found: %s", executionID)
	}

	if execution.Status != ExecutionStatusRunning && execution.Status != ExecutionStatusPending {
		return fmt.Errorf("execution cannot be cancelled (current status: %s)", execution.Status)
	}

	execution.Status = ExecutionStatusCancelled
	if execution.EndTime == nil {
		now := time.Now()
		execution.EndTime = &now
	}

	log.Printf("Cancelled workflow execution: %s", executionID)
	return nil
}

// executeWorkflowAsync executes a workflow asynchronously
func (we *WorkflowEngine) executeWorkflowAsync(ctx context.Context, template *WorkflowTemplate, execution *WorkflowExecution) {
	execution.Status = ExecutionStatusRunning
	
	// Execute workflow steps
	if err := we.executeSteps(ctx, template, execution); err != nil {
		execution.Status = ExecutionStatusFailed
		execution.Error = err.Error()
	} else {
		execution.Status = ExecutionStatusCompleted
	}

	// Set end time
	now := time.Now()
	execution.EndTime = &now

	log.Printf("Completed workflow execution: %s with status: %s", execution.ID, execution.Status)
}

// executeSteps executes workflow steps
func (we *WorkflowEngine) executeSteps(ctx context.Context, template *WorkflowTemplate, execution *WorkflowExecution) error {
	// Build dependency graph
	stepGraph := we.buildStepGraph(template.Steps)

	// Execute steps in dependency order
	for _, step := range template.Steps {
		// Check if dependencies are completed
		if !we.checkDependencies(step, execution.StepResults) {
			return fmt.Errorf("dependencies not satisfied for step: %s", step.ID)
		}

		// Execute step
		result, err := we.executeStep(ctx, step, execution)
		if err != nil {
			return fmt.Errorf("step %s failed: %w", step.ID, err)
		}

		// Store result
		execution.StepResults[step.ID] = result

		// Update progress
		execution.Progress = float64(len(execution.StepResults)) / float64(len(template.Steps)) * 100
	}

	return nil
}

// executeStep executes a single workflow step
func (we *WorkflowEngine) executeStep(ctx context.Context, step WorkflowStep, execution *WorkflowExecution) (StepResult, error) {
	startTime := time.Now()
	result := StepResult{
		StepID:    step.ID,
		Status:    ExecutionStatusRunning,
		StartTime: startTime,
	}

	// Execute based on step type
	switch step.Type {
	case StepTypeSkill:
		output, err := we.executeSkillStep(ctx, step, execution)
		if err != nil {
			result.Status = ExecutionStatusFailed
			result.Error = err.Error()
		} else {
			result.Status = ExecutionStatusCompleted
			result.Output = output
		}
	case StepTypeParallel:
		output, err := we.executeParallelStep(ctx, step, execution)
		if err != nil {
			result.Status = ExecutionStatusFailed
			result.Error = err.Error()
		} else {
			result.Status = ExecutionStatusCompleted
			result.Output = output
		}
	case StepTypeSequence:
		output, err := we.executeSequenceStep(ctx, step, execution)
		if err != nil {
			result.Status = ExecutionStatusFailed
			result.Error = err.Error()
		} else {
			result.Status = ExecutionStatusCompleted
			result.Output = output
		}
	default:
		return result, fmt.Errorf("unsupported step type: %s", step.Type)
	}

	// Set end time and duration
	endTime := time.Now()
	result.EndTime = &endTime
	result.Duration = endTime.Sub(startTime)

	return result, nil
}

// executeSkillStep executes a skill step
func (we *WorkflowEngine) executeSkillStep(ctx context.Context, step WorkflowStep, execution *WorkflowExecution) (map[string]interface{}, error) {
	// Merge step inputs with execution inputs
	inputs := make(map[string]interface{})
	for k, v := range step.Inputs {
		inputs[k] = v
	}
	for k, v := range execution.Inputs {
		inputs[k] = v
	}

	// Execute skill via Temporal
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("skill-%s-%s", step.SkillName, execution.ID),
		TaskQueue: "skill-queue",
	}

	we, err := we.temporalClient.ExecuteWorkflow(ctx, workflowOptions, step.SkillName, inputs)
	if err != nil {
		return nil, fmt.Errorf("failed to execute skill workflow: %w", err)
	}

	var result map[string]interface{}
	err = we.Get(ctx, &result)
	if err != nil {
		return nil, fmt.Errorf("skill workflow execution failed: %w", err)
	}

	return result, nil
}

// executeParallelStep executes parallel steps
func (we *WorkflowEngine) executeParallelStep(ctx context.Context, step WorkflowStep, execution *WorkflowExecution) (map[string]interface{}, error) {
	// In a real implementation, this would execute multiple steps in parallel
	// For now, we'll simulate parallel execution
	return map[string]interface{}{
		"result": "parallel execution completed",
		"step":   step.ID,
	}, nil
}

// executeSequenceStep executes sequence steps
func (we *WorkflowEngine) executeSequenceStep(ctx context.Context, step WorkflowStep, execution *WorkflowExecution) (map[string]interface{}, error) {
	// In a real implementation, this would execute steps in sequence
	// For now, we'll simulate sequence execution
	return map[string]interface{}{
		"result": "sequence execution completed",
		"step":   step.ID,
	}, nil
}

// buildStepGraph builds a dependency graph for steps
func (we *WorkflowEngine) buildStepGraph(steps []WorkflowStep) map[string][]string {
	graph := make(map[string][]string)
	for _, step := range steps {
		graph[step.ID] = step.Dependencies
	}
	return graph
}

// checkDependencies checks if step dependencies are satisfied
func (we *WorkflowEngine) checkDependencies(step WorkflowStep, results map[string]StepResult) bool {
	for _, depID := range step.Dependencies {
		result, exists := results[depID]
		if !exists || result.Status != ExecutionStatusCompleted {
			return false
		}
	}
	return true
}

// validateTemplate validates a workflow template
func (we *WorkflowEngine) validateTemplate(template *WorkflowTemplate) error {
	if template.ID == "" {
		return fmt.Errorf("template ID is required")
	}
	if template.Name == "" {
		return fmt.Errorf("template name is required")
	}
	if len(template.Steps) == 0 {
		return fmt.Errorf("template must have at least one step")
	}

	// Validate steps
	stepIDs := make(map[string]bool)
	for _, step := range template.Steps {
		if step.ID == "" {
			return fmt.Errorf("step ID is required")
		}
		if stepIDs[step.ID] {
			return fmt.Errorf("duplicate step ID: %s", step.ID)
		}
		stepIDs[step.ID] = true

		// Validate dependencies
		for _, dep := range step.Dependencies {
			if !stepIDs[dep] && dep != "" {
				return fmt.Errorf("step %s depends on non-existent step: %s", step.ID, dep)
			}
		}
	}

	return nil
}

// validateInputs validates workflow inputs
func (we *WorkflowEngine) validateInputs(template *WorkflowTemplate, inputs map[string]interface{}) error {
	// Validate required parameters
	for name, param := range template.Metadata.Parameters {
		if param.Required {
			if _, exists := inputs[name]; !exists {
				return fmt.Errorf("required parameter missing: %s", name)
			}
		}
	}
	return nil
}

// generateExecutionID generates a unique execution ID
func generateExecutionID() string {
	return fmt.Sprintf("exec-%d-%s", time.Now().UnixNano(), randomString(8))
}

// randomString generates a random string
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// Predefined workflow templates

// NewToilAutomationTemplate creates a toil automation workflow template
func NewToilAutomationTemplate() *WorkflowTemplate {
	return &WorkflowTemplate{
		ID:          "toil-automation-v1",
		Name:        "Infrastructure Toil Automation",
		Description: "Automates routine infrastructure maintenance tasks",
		Version:     "1.0.0",
		Category:    "maintenance",
		Steps: []WorkflowStep{
			{
				ID:        "cert-rotation",
				Name:      "Certificate Rotation",
				SkillName: "certificate-rotation",
				Type:      StepTypeSkill,
				Config: StepConfig{
					Async:      true,
					Background: true,
				},
				Timeout: 30 * time.Minute,
			},
			{
				ID:        "dependency-updates",
				Name:      "Dependency Updates",
				SkillName: "dependency-updates",
				Type:      StepTypeSkill,
				Config: StepConfig{
					Async:      true,
					Background: true,
				},
				Timeout: 45 * time.Minute,
			},
			{
				ID:        "cleanup",
				Name:      "Resource Cleanup",
				SkillName: "resource-cleanup",
				Type:      StepTypeSkill,
				Dependencies: []string{"cert-rotation", "dependency-updates"},
				Config: StepConfig{
					Async:      true,
					Background: true,
				},
				Timeout: 15 * time.Minute,
			},
		},
		Inputs: map[string]interface{}{
			"scope":        "all",
			"dry_run":     false,
			"notification": true,
		},
		Outputs: map[string]interface{}{
			"certificates_rotated": 0,
			"dependencies_updated": 0,
			"resources_cleaned":    0,
		},
		Metadata: WorkflowMetadata{
			Author:            "AI Agent Team",
			Tags:              []string{"maintenance", "automation", "toil"},
			EstimatedDuration: 90 * time.Minute,
			RiskLevel:         "medium",
			RequiredRoles:     []string{"admin", "devops"},
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// NewCostOptimizationTemplate creates a cost optimization workflow template
func NewCostOptimizationTemplate() *WorkflowTemplate {
	return &WorkflowTemplate{
		ID:          "cost-optimization-v1",
		Name:        "Cloud Cost Optimization",
		Description: "Optimizes cloud resource costs across all environments",
		Version:     "1.0.0",
		Category:    "optimization",
		Steps: []WorkflowStep{
			{
				ID:        "cost-analysis",
				Name:      "Cost Analysis",
				SkillName: "cost-analyzer",
				Type:      StepTypeSkill,
				Config: StepConfig{
					Async: true,
				},
				Timeout: 20 * time.Minute,
			},
			{
				ID:        "recommendations",
				Name:      "Generate Recommendations",
				SkillName: "cost-optimizer",
				Type:      StepTypeSkill,
				Dependencies: []string{"cost-analysis"},
				Config: StepConfig{
					Async: true,
				},
				Timeout: 15 * time.Minute,
			},
			{
				ID:        "apply-changes",
				Name:      "Apply Optimizations",
				SkillName: "cost-applier",
				Type:      StepTypeSkill,
				Dependencies: []string{"recommendations"},
				Config: StepConfig{
					Async:      true,
					Background: true,
				},
				Timeout: 60 * time.Minute,
			},
		},
		Inputs: map[string]interface{}{
			"environments": []string{"production", "staging"},
			"target_savings": 100.0,
			"auto_apply":    false,
		},
		Outputs: map[string]interface{}{
			"total_savings":    0.0,
			"recommendations":  []interface{}{},
			"applied_changes":  []interface{}{},
		},
		Metadata: WorkflowMetadata{
			Author:            "AI Agent Team",
			Tags:              []string{"cost", "optimization", "finance"},
			EstimatedDuration: 95 * time.Minute,
			RiskLevel:         "high",
			RequiredRoles:     []string{"admin", "finance"},
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

// NewSecurityAuditTemplate creates a security audit workflow template
func NewSecurityAuditTemplate() *WorkflowTemplate {
	return &WorkflowTemplate{
		ID:          "security-audit-v1",
		Name:        "Security Audit and Remediation",
		Description: "Performs comprehensive security audit and applies fixes",
		Version:     "1.0.0",
		Category:    "security",
		Steps: []WorkflowStep{
			{
				ID:        "vulnerability-scan",
				Name:      "Vulnerability Scanning",
				SkillName: "security-scanner",
				Type:      StepTypeSkill,
				Config: StepConfig{
					Async: true,
				},
				Timeout: 45 * time.Minute,
			},
			{
				ID:        "policy-check",
				Name:      "Policy Compliance Check",
				SkillName: "policy-validator",
				Type:      StepTypeSkill,
				Dependencies: []string{"vulnerability-scan"},
				Config: StepConfig{
					Async: true,
				},
				Timeout: 30 * time.Minute,
			},
			{
				ID:        "remediation",
				Name:      "Security Remediation",
				SkillName: "security-fixer",
				Type:      StepTypeSkill,
				Dependencies: []string{"vulnerability-scan", "policy-check"},
				Config: StepConfig{
					Async:      true,
					Background: true,
				},
				Timeout: 90 * time.Minute,
			},
		},
		Inputs: map[string]interface{}{
			"scan_scope":     "all",
			"severity_level": "medium",
			"auto_fix":      false,
		},
		Outputs: map[string]interface{}{
			"vulnerabilities_found": 0,
			"policy_violations":     0,
			"issues_fixed":          0,
		},
		Metadata: WorkflowMetadata{
			Author:            "AI Agent Team",
			Tags:              []string{"security", "audit", "compliance"},
			EstimatedDuration: 165 * time.Minute,
			RiskLevel:         "high",
			RequiredRoles:     []string{"admin", "security"},
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}
