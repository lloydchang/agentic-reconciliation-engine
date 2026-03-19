package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/sandbox"
)

// Executor manages Agent Sandbox execution for all agent types
type Executor struct {
	sandboxManager *sandbox.SandboxManager
	config         *config.AgentSandboxConfig
	templates      map[string]*TemplateManager
	warmPools      map[string]*WarmPoolManager
	monitoring     *MonitoringManager
}

// ExecutionRequest represents a request to execute code in an Agent Sandbox
type ExecutionRequest struct {
	AgentID       string                 `json:"agent_id"`
	AgentType     string                 `json:"agent_type"` // temporal, pi-mono, memory
	Code          string                 `json:"code"`
	Language      string                 `json:"language"`
	Template      string                 `json:"template"`
	Resources     sandbox.ResourceSpec   `json:"resources"`
	Environment   map[string]string      `json:"environment"`
	Timeout       time.Duration          `json:"timeout"`
	NetworkAccess bool                   `json:"network_access"`
	Metadata      map[string]interface{} `json:"metadata"`
}

// ExecutionResult represents the result of sandbox execution
type ExecutionResult struct {
	AgentID      string        `json:"agent_id"`
	SandboxID    string        `json:"sandbox_id"`
	ExitCode     int           `json:"exit_code"`
	Stdout       string        `json:"stdout"`
	Stderr       string        `json:"stderr"`
	Duration     time.Duration `json:"duration"`
	MemoryUsage  int64         `json:"memory_usage"`
	CPUUsage     float64       `json:"cpu_usage"`
	Success      bool          `json:"success"`
	Error        string        `json:"error,omitempty"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// NewExecutor creates a new Agent Sandbox executor
func NewExecutor(sandboxManager *sandbox.SandboxManager, config *config.AgentSandboxConfig) *Executor {
	executor := &Executor{
		sandboxManager: sandboxManager,
		config:         config,
		templates:      make(map[string]*TemplateManager),
		warmPools:      make(map[string]*WarmPoolManager),
		monitoring:     NewMonitoringManager(),
	}

	// Initialize template managers
	for _, template := range config.Templates {
		executor.templates[template.Name] = NewTemplateManager(template, config)
	}

	// Initialize warm pool managers
	for _, pool := range config.WarmPools {
		executor.warmPools[pool.Name] = NewWarmPoolManager(pool, config)
	}

	return executor
}

// Execute executes code in an Agent Sandbox environment
func (e *Executor) Execute(ctx context.Context, request *ExecutionRequest) (*ExecutionResult, error) {
	log.Printf("Executing Agent Sandbox request for agent %s (type: %s)", request.AgentID, request.AgentType)

	startTime := time.Now()
	
	// Determine template to use
	templateName := request.Template
	if templateName == "" {
		templateName = e.config.DefaultTemplate
	}

	// Validate template exists
	template, exists := e.templates[templateName]
	if !exists {
		return nil, fmt.Errorf("template %s not found", templateName)
	}

	// Create sandbox configuration
	sandboxConfig := sandbox.SandboxConfig{
		Provider:     "agent-sandbox",
		Image:        template.GetImage(),
		Resources:    request.Resources,
		Timeout:      request.Timeout,
		Environment:  request.Environment,
		NetworkAccess: request.NetworkAccess,
	}

	// Add template-specific environment variables
	templateEnv := template.GetEnvironment()
	for k, v := range templateEnv {
		if sandboxConfig.Environment == nil {
			sandboxConfig.Environment = make(map[string]string)
		}
		sandboxConfig.Environment[k] = v
	}

	// Create sandbox environment
	env, err := e.sandboxManager.CreateEnvironment(ctx, "agent-sandbox", sandboxConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create sandbox environment: %w", err)
	}

	// Ensure cleanup
	defer func() {
		if err := e.sandboxManager.DestroyEnvironment(context.Background(), "agent-sandbox", env.ID); err != nil {
			log.Printf("Failed to destroy sandbox environment %s: %v", env.ID, err)
		}
	}()

	// Wait for sandbox to be ready
	if err := e.waitForSandboxReady(ctx, env.ID); err != nil {
		return nil, fmt.Errorf("sandbox not ready: %w", err)
	}

	// Execute the code
	command := sandbox.Command{
		Cmd:       e.getExecutionCommand(request.Language, request.Code),
		Env:       request.Environment,
		Timeout:   request.Timeout,
		WorkingDir: "/workspace",
	}

	result, err := e.sandboxManager.ExecuteCommand(ctx, "agent-sandbox", env.ID, command)
	if err != nil {
		return nil, fmt.Errorf("failed to execute command: %w", err)
	}

	// Get resource usage metrics
	metrics, _ := e.monitoring.GetMetrics(ctx, env.ID)

	// Create execution result
	executionResult := &ExecutionResult{
		AgentID:     request.AgentID,
		SandboxID:   env.ID,
		ExitCode:    result.ExitCode,
		Stdout:      result.Stdout,
		Stderr:      result.Stderr,
		Duration:    time.Since(startTime),
		MemoryUsage: metrics.MemoryUsage,
		CPUUsage:    metrics.CPUUsage,
		Success:     result.ExitCode == 0,
		Metadata: map[string]interface{}{
			"template":      templateName,
			"agent_type":    request.AgentType,
			"language":      request.Language,
			"created_at":    startTime,
			"completed_at":  time.Now(),
		},
	}

	if result.Error != nil {
		executionResult.Error = result.Error.Error()
	}

	// Record execution metrics
	e.monitoring.RecordExecution(executionResult)

	log.Printf("Agent Sandbox execution completed for agent %s: success=%v, duration=%v", 
		request.AgentID, executionResult.Success, executionResult.Duration)

	return executionResult, nil
}

// ExecuteAsync executes code asynchronously
func (e *Executor) ExecuteAsync(ctx context.Context, request *ExecutionRequest) (<-chan *ExecutionResult, error) {
	resultChan := make(chan *ExecutionResult, 1)

	go func() {
		defer close(resultChan)
		
		result, err := e.Execute(ctx, request)
		if err != nil {
			result = &ExecutionResult{
				AgentID: request.AgentID,
				Success: false,
				Error:   err.Error(),
				Metadata: map[string]interface{}{
					"agent_type": request.AgentType,
					"language":   request.Language,
				},
			}
		}
		
		select {
		case resultChan <- result:
		case <-ctx.Done():
			log.Printf("Context cancelled, dropping result for agent %s", request.AgentID)
		}
	}()

	return resultChan, nil
}

// waitForSandboxReady waits for a sandbox to become ready
func (e *Executor) waitForSandboxReady(ctx context.Context, envID string) error {
	timeout := time.After(e.config.Timeout)
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("context cancelled while waiting for sandbox")
		case <-timeout:
			return fmt.Errorf("timeout waiting for sandbox to become ready")
		case <-ticker.C:
			status, err := e.sandboxManager.GetStatus(ctx, "agent-sandbox", envID)
			if err != nil {
				log.Printf("Error checking sandbox status: %v", err)
				continue
			}
			if status == sandbox.StatusRunning {
				return nil
			}
		}
	}
}

// getExecutionCommand returns the appropriate command for the given language
func (e *Executor) getExecutionCommand(language, code string) string {
	switch language {
	case "python":
		return fmt.Sprintf("python3 -c '%s'", code)
	case "bash", "shell":
		return fmt.Sprintf("bash -c '%s'", code)
	case "javascript", "js":
		return fmt.Sprintf("node -e '%s'", code)
	case "go":
		return fmt.Sprintf("go run - <<'EOF'\n%s\nEOF", code)
	default:
		// Default to bash
		return fmt.Sprintf("bash -c '%s'", code)
	}
}

// GetTemplates returns available templates
func (e *Executor) GetTemplates() map[string]*config.TemplateSpec {
	templates := make(map[string]*config.TemplateSpec)
	for name, template := range e.templates {
		templates[name] = template.GetSpec()
	}
	return templates
}

// GetWarmPools returns available warm pools
func (e *Executor) GetWarmPools() map[string]*config.WarmPoolSpec {
	pools := make(map[string]*config.WarmPoolSpec)
	for name, pool := range e.warmPools {
		pools[name] = pool.GetSpec()
	}
	return pools
}

// GetMetrics returns execution metrics
func (e *Executor) GetMetrics(ctx context.Context) (*ExecutionMetrics, error) {
	return e.monitoring.GetAggregatedMetrics(ctx)
}

// Cleanup performs cleanup operations
func (e *Executor) Cleanup(ctx context.Context) error {
	log.Printf("Cleaning up Agent Sandbox executor")
	
	// Cleanup template managers
	for _, template := range e.templates {
		if err := template.Cleanup(ctx); err != nil {
			log.Printf("Error cleaning up template: %v", err)
		}
	}
	
	// Cleanup warm pool managers
	for _, pool := range e.warmPools {
		if err := pool.Cleanup(ctx); err != nil {
			log.Printf("Error cleaning up warm pool: %v", err)
		}
	}
	
	return nil
}
