package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"go.temporal.io/sdk/workflow"
)

// Agent represents a specialized AI agent with specific capabilities
type Agent struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Role        string                 `json:"role"`        // e.g., "infrastructure", "security", "monitoring"
	Capabilities []string             `json:"capabilities"` // e.g., ["kubernetes", "networking", "security"]
	Status      string                 `json:"status"`       // "idle", "busy", "offline"
	LastActive  time.Time              `json:"last_active"`
	LoadFactor  float64                `json:"load_factor"` // 0.0 to 1.0
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Task represents a unit of work for agent execution
type Task struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`        // "infrastructure", "security", "monitoring", etc.
	Priority    int                    `json:"priority"`    // 1=low, 2=medium, 3=high, 4=critical
	Description string                 `json:"description"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
	Deadline    *time.Time             `json:"deadline,omitempty"`
	AssignedTo  string                 `json:"assigned_to,omitempty"`
	Status      string                 `json:"status"` // "pending", "assigned", "in_progress", "completed", "failed"
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Result      interface{}            `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
}

// OrchestrationRequest represents a request for multi-agent orchestration
type OrchestrationRequest struct {
	RequestID   string                 `json:"request_id"`
	Description string                 `json:"description"`
	Tasks       []Task                 `json:"tasks"`
	Strategy    string                 `json:"strategy"` // "sequential", "parallel", "hybrid"
	Priority    int                    `json:"priority"`
	Deadline    *time.Time             `json:"deadline,omitempty"`
	Context     map[string]interface{} `json:"context,omitempty"`
}

// OrchestrationResult represents the result of multi-agent orchestration
type OrchestrationResult struct {
	RequestID     string                 `json:"request_id"`
	Status        string                 `json:"status"` // "completed", "failed", "partial"
	Results       []TaskResult           `json:"results"`
	Duration      time.Duration          `json:"duration"`
	CompletedAt   time.Time              `json:"completed_at"`
	Metrics       OrchestrationMetrics   `json:"metrics"`
	Error         string                 `json:"error,omitempty"`
}

// TaskResult represents the result of a single task
type TaskResult struct {
	TaskID    string      `json:"task_id"`
	AgentID   string      `json:"agent_id"`
	Status    string      `json:"status"`
	Result    interface{} `json:"result,omitempty"`
	Error     string      `json:"error,omitempty"`
	Duration  time.Duration `json:"duration"`
	StartTime time.Time   `json:"start_time"`
	EndTime   time.Time   `json:"end_time"`
}

// OrchestrationMetrics tracks performance metrics
type OrchestrationMetrics struct {
	TotalTasks      int           `json:"total_tasks"`
	CompletedTasks  int           `json:"completed_tasks"`
	FailedTasks     int           `json:"failed_tasks"`
	AverageDuration time.Duration `json:"average_duration"`
	ResourceUtilization float64   `json:"resource_utilization"`
	AgentEfficiency map[string]float64 `json:"agent_efficiency"`
}

// MultiAgentOrchestrator manages coordination of multiple specialized agents
type MultiAgentOrchestrator struct {
	agents         map[string]*Agent
	tasks          map[string]*Task
	activeRequests map[string]*OrchestrationRequest
	mutex          sync.RWMutex
	reasoningEngine *ReasoningEngine
}

// NewMultiAgentOrchestrator creates a new orchestrator
func NewMultiAgentOrchestrator(reasoningEngine *ReasoningEngine) *MultiAgentOrchestrator {
	return &MultiAgentOrchestrator{
		agents:         make(map[string]*Agent),
		tasks:          make(map[string]*Task),
		activeRequests: make(map[string]*OrchestrationRequest),
		reasoningEngine: reasoningEngine,
	}
}

// RegisterAgent registers a new agent with the orchestrator
func (mao *MultiAgentOrchestrator) RegisterAgent(agent *Agent) {
	mao.mutex.Lock()
	defer mao.mutex.Unlock()

	agent.Status = "idle"
	agent.LastActive = time.Now()
	agent.LoadFactor = 0.0
	mao.agents[agent.ID] = agent

	log.Printf("Registered agent: %s (%s) with capabilities: %v", agent.Name, agent.Role, agent.Capabilities)
}

// GetAvailableAgent finds an available agent for a specific task type
func (mao *MultiAgentOrchestrator) GetAvailableAgent(taskType string) *Agent {
	mao.mutex.RLock()
	defer mao.mutex.RUnlock()

	var bestAgent *Agent
	minLoad := 1.1 // Higher than max possible load

	for _, agent := range mao.agents {
		if agent.Status == "offline" {
			continue
		}

		// Check if agent has the required capability
		hasCapability := false
		for _, cap := range agent.Capabilities {
			if cap == taskType {
				hasCapability = true
				break
			}
		}

		if !hasCapability {
			continue
		}

		// Select agent with lowest load factor
		if agent.LoadFactor < minLoad {
			minLoad = agent.LoadFactor
			bestAgent = agent
		}
	}

	return bestAgent
}

// AssignTask assigns a task to an available agent
func (mao *MultiAgentOrchestrator) AssignTask(task *Task) error {
	mao.mutex.Lock()
	defer mao.mutex.Unlock()

	agent := mao.GetAvailableAgent(task.Type)
	if agent == nil {
		return fmt.Errorf("no available agent found for task type: %s", task.Type)
	}

	task.AssignedTo = agent.ID
	task.Status = "assigned"
	task.UpdatedAt = time.Now()

	agent.Status = "busy"
	agent.LoadFactor += 0.2 // Increase load factor
	if agent.LoadFactor > 1.0 {
		agent.LoadFactor = 1.0
	}

	mao.tasks[task.ID] = task

	log.Printf("Assigned task %s to agent %s (%s)", task.ID, agent.Name, agent.Role)
	return nil
}

// CompleteTask marks a task as completed and updates agent status
func (mao *MultiAgentOrchestrator) CompleteTask(taskID string, result interface{}, err error) {
	mao.mutex.Lock()
	defer mao.mutex.Unlock()

	task, exists := mao.tasks[taskID]
	if !exists {
		log.Printf("Warning: task %s not found in orchestrator", taskID)
		return
	}

	task.UpdatedAt = time.Now()

	if err != nil {
		task.Status = "failed"
		task.Error = err.Error()
	} else {
		task.Status = "completed"
		task.Result = result
	}

	// Update agent status
	if agent, exists := mao.agents[task.AssignedTo]; exists {
		agent.Status = "idle"
		agent.LastActive = time.Now()
		agent.LoadFactor -= 0.2 // Decrease load factor
		if agent.LoadFactor < 0.0 {
			agent.LoadFactor = 0.0
		}
	}

	log.Printf("Completed task %s with status: %s", taskID, task.Status)
}

// OrchestrateRequest orchestrates multiple tasks across available agents
func (mao *MultiAgentOrchestrator) OrchestrateRequest(ctx context.Context, request *OrchestrationRequest) (*OrchestrationResult, error) {
	startTime := time.Now()

	mao.mutex.Lock()
	mao.activeRequests[request.RequestID] = request
	mao.mutex.Unlock()

	defer func() {
		mao.mutex.Lock()
		delete(mao.activeRequests, request.RequestID)
		mao.mutex.Unlock()
	}()

	result := &OrchestrationResult{
		RequestID: request.RequestID,
		Status:    "in_progress",
		Results:   make([]TaskResult, 0, len(request.Tasks)),
		Metrics: OrchestrationMetrics{
			TotalTasks:      len(request.Tasks),
			AgentEfficiency: make(map[string]float64),
		},
	}

	// Use reasoning engine to optimize task assignment strategy
	if mao.reasoningEngine != nil {
		decision, err := mao.optimizeTaskAssignment(request)
		if err != nil {
			log.Printf("Failed to optimize task assignment: %v", err)
		} else {
			log.Printf("Task assignment optimized with confidence: %.2f", decision.Confidence)
		}
	}

	// Execute tasks based on strategy
	switch request.Strategy {
	case "sequential":
		err := mao.executeSequential(ctx, request, result)
		if err != nil {
			result.Status = "failed"
			result.Error = err.Error()
		} else {
			result.Status = "completed"
		}
	case "parallel":
		err := mao.executeParallel(ctx, request, result)
		if err != nil {
			result.Status = "failed"
			result.Error = err.Error()
		} else {
			result.Status = "completed"
		}
	case "hybrid":
		err := mao.executeHybrid(ctx, request, result)
		if err != nil {
			result.Status = "failed"
			result.Error = err.Error()
		} else {
			result.Status = "completed"
		}
	default:
		return nil, fmt.Errorf("unsupported orchestration strategy: %s", request.Strategy)
	}

	result.Duration = time.Since(startTime)
	result.CompletedAt = time.Now()
	result.Metrics.CompletedTasks = len(result.Results)

	// Calculate metrics
	mao.calculateMetrics(result)

	return result, nil
}

// optimizeTaskAssignment uses reasoning to optimize task assignment
func (mao *MultiAgentOrchestrator) optimizeTaskAssignment(request *OrchestrationRequest) (*Decision, error) {
	// Convert tasks to decision options
	var options []DecisionOption
	for i, task := range request.Tasks {
		option := DecisionOption{
			OptionID:    task.ID,
			Description: fmt.Sprintf("Task %d: %s (%s)", i+1, task.Description, task.Type),
			RiskLevel:   mao.calculateTaskRisk(task),
			Impact:      mao.calculateTaskImpact(task),
			Score:       float64(task.Priority) * 0.1, // Base score from priority
			Metadata: map[string]interface{}{
				"task_type": task.Type,
				"priority":  task.Priority,
			},
		}

		// Calculate pros and cons based on agent availability
		agent := mao.GetAvailableAgent(task.Type)
		if agent != nil {
			option.Pros = []string{
				fmt.Sprintf("Available agent: %s", agent.Name),
				fmt.Sprintf("Load factor: %.1f", agent.LoadFactor),
			}
			if agent.LoadFactor < 0.5 {
				option.Pros = append(option.Pros, "Low load - fast execution expected")
			}
		} else {
			option.Cons = []string{"No available agent found"}
			option.Score -= 0.5 // Penalty for no available agent
		}

		options = append(options, option)
	}

	taskDescription := fmt.Sprintf("Optimize assignment of %d tasks with strategy '%s'", len(request.Tasks), request.Strategy)
	context := map[string]interface{}{
		"strategy":       request.Strategy,
		"deadline":       request.Deadline,
		"priority":       request.Priority,
		"max_risk_level": "high", // Allow high-risk tasks
		"impact_weight":  0.3,    // Weight for impact in decision
	}

	return mao.reasoningEngine.AnalyzeOptions(context.Background(), taskDescription, options, context)
}

// calculateTaskRisk determines the risk level of a task
func (mao *MultiAgentOrchestrator) calculateTaskRisk(task *Task) string {
	// Simple risk calculation based on task type and priority
	switch task.Type {
	case "security", "compliance":
		if task.Priority >= 4 {
			return "high"
		}
		return "medium"
	case "infrastructure":
		if task.Priority >= 3 {
			return "medium"
		}
		return "low"
	default:
		return "low"
	}
}

// calculateTaskImpact determines the impact level of a task
func (mao *MultiAgentOrchestrator) calculateTaskImpact(task *Task) string {
	if task.Priority >= 4 {
		return "high"
	} else if task.Priority >= 3 {
		return "medium"
	}
	return "low"
}

// executeSequential executes tasks one after another
func (mao *MultiAgentOrchestrator) executeSequential(ctx context.Context, request *OrchestrationRequest, result *OrchestrationResult) error {
	for _, task := range request.Tasks {
		// Simulate task execution (in real implementation, this would be actual agent calls)
		taskResult, err := mao.executeTask(ctx, &task)
		result.Results = append(result.Results, *taskResult)

		if err != nil {
			result.Metrics.FailedTasks++
			return err
		}

		// Check deadline
		if request.Deadline != nil && time.Now().After(*request.Deadline) {
			return fmt.Errorf("deadline exceeded during sequential execution")
		}
	}

	return nil
}

// executeParallel executes tasks concurrently
func (mao *MultiAgentOrchestrator) executeParallel(ctx context.Context, request *OrchestrationRequest, result *OrchestrationResult) error {
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstError error

	for _, task := range request.Tasks {
		wg.Add(1)
		go func(t Task) {
			defer wg.Done()

			taskResult, err := mao.executeTask(ctx, &t)

			mu.Lock()
			result.Results = append(result.Results, *taskResult)
			if err != nil && firstError == nil {
				firstError = err
				result.Metrics.FailedTasks++
			}
			mu.Unlock()
		}(task)
	}

	wg.Wait()
	return firstError
}

// executeHybrid uses a hybrid approach combining sequential and parallel execution
func (mao *MultiAgentOrchestrator) executeHybrid(ctx context.Context, request *OrchestrationRequest, result *OrchestrationResult) error {
	// Group tasks by priority for hybrid execution
	highPriority := make([]Task, 0)
	mediumPriority := make([]Task, 0)
	lowPriority := make([]Task, 0)

	for _, task := range request.Tasks {
		switch {
		case task.Priority >= 4:
			highPriority = append(highPriority, task)
		case task.Priority >= 2:
			mediumPriority = append(mediumPriority, task)
		default:
			lowPriority = append(lowPriority, task)
		}
	}

	// Execute high priority tasks sequentially first
	for _, task := range highPriority {
		taskResult, err := mao.executeTask(ctx, &task)
		result.Results = append(result.Results, *taskResult)
		if err != nil {
			result.Metrics.FailedTasks++
			return err
		}
	}

	// Execute medium and low priority tasks in parallel
	parallelTasks := append(mediumPriority, lowPriority...)
	if len(parallelTasks) > 0 {
		requestCopy := *request
		requestCopy.Tasks = parallelTasks
		return mao.executeParallel(ctx, &requestCopy, result)
	}

	return nil
}

// executeTask simulates task execution (in real implementation, this would call actual agents)
func (mao *MultiAgentOrchestrator) executeTask(ctx context.Context, task *Task) (*TaskResult, error) {
	startTime := time.Now()

	// Assign task to agent
	err := mao.AssignTask(task)
	if err != nil {
		return &TaskResult{
			TaskID:    task.ID,
			Status:    "failed",
			Error:     err.Error(),
			StartTime: startTime,
			EndTime:   time.Now(),
		}, err
	}

	// Simulate task execution time based on complexity
	executionTime := time.Duration(task.Priority*100) * time.Millisecond
	select {
	case <-time.After(executionTime):
		// Task completed successfully
		result := map[string]interface{}{
			"task_type": task.Type,
			"executed_by": task.AssignedTo,
			"duration_ms": executionTime.Milliseconds(),
		}

		mao.CompleteTask(task.ID, result, nil)

		return &TaskResult{
			TaskID:    task.ID,
			AgentID:   task.AssignedTo,
			Status:    "completed",
			Result:    result,
			Duration:  executionTime,
			StartTime: startTime,
			EndTime:   time.Now(),
		}, nil

	case <-ctx.Done():
		// Context cancelled
		mao.CompleteTask(task.ID, nil, ctx.Err())
		return &TaskResult{
			TaskID:    task.ID,
			AgentID:   task.AssignedTo,
			Status:    "failed",
			Error:     "context cancelled",
			StartTime: startTime,
			EndTime:   time.Now(),
		}, ctx.Err()
	}
}

// calculateMetrics calculates orchestration performance metrics
func (mao *MultiAgentOrchestrator) calculateMetrics(result *OrchestrationResult) {
	totalDuration := time.Duration(0)
	agentTasks := make(map[string]int)

	for _, taskResult := range result.Results {
		totalDuration += taskResult.Duration
		if taskResult.Status == "completed" {
			agentTasks[taskResult.AgentID]++
		}
	}

	if len(result.Results) > 0 {
		result.Metrics.AverageDuration = totalDuration / time.Duration(len(result.Results))
	}

	// Calculate agent efficiency
	for agentID, taskCount := range agentTasks {
		if agent, exists := mao.agents[agentID]; exists {
			efficiency := float64(taskCount) / float64(result.Metrics.TotalTasks)
			result.Metrics.AgentEfficiency[agent.Name] = efficiency
		}
	}

	// Calculate resource utilization (simplified)
	totalLoad := 0.0
	for _, agent := range mao.agents {
		totalLoad += agent.LoadFactor
	}
	if len(mao.agents) > 0 {
		result.Metrics.ResourceUtilization = totalLoad / float64(len(mao.agents))
	}
}

// WorkflowOrchestrationActivity is a Temporal activity for multi-agent orchestration
func WorkflowOrchestrationActivity(ctx context.Context, request *OrchestrationRequest) (*OrchestrationResult, error) {
	// Note: In a real implementation, this would get orchestrator from global instance
	return GlobalOrchestrator.OrchestrateRequest(ctx, request)
}

// MultiAgentOrchestrationWorkflow is a Temporal workflow for complex multi-agent orchestration
func MultiAgentOrchestrationWorkflow(ctx workflow.Context, request *OrchestrationRequest) (*OrchestrationResult, error) {
	// Configure workflow options
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 300 * time.Second, // 5 minutes
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    60 * time.Second,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result *OrchestrationResult
	err := workflow.ExecuteActivity(ctx, WorkflowOrchestrationActivity, request).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	// Log orchestration completion
	workflow.GetLogger(ctx).Info("Multi-agent orchestration completed",
		"request_id", result.RequestID,
		"status", result.Status,
		"tasks_completed", result.Metrics.CompletedTasks,
		"duration", result.Duration)

	return result, nil
}

// Global orchestrator instance
var GlobalOrchestrator *MultiAgentOrchestrator

// InitOrchestrator initializes the global multi-agent orchestrator
func InitOrchestrator(reasoningEngine *ReasoningEngine) error {
	GlobalOrchestrator = NewMultiAgentOrchestrator(reasoningEngine)
	return nil
}

// Orchestrate provides a simple interface for multi-agent orchestration
func Orchestrate(description string, tasks []Task, strategy string, priority int) (*OrchestrationResult, error) {
	if GlobalOrchestrator == nil {
		return nil, fmt.Errorf("orchestrator not initialized")
	}

	request := &OrchestrationRequest{
		RequestID:   fmt.Sprintf("orch-%d", time.Now().Unix()),
		Description: description,
		Tasks:       tasks,
		Strategy:    strategy,
		Priority:    priority,
		Context:     make(map[string]interface{}),
	}

	return GlobalOrchestrator.OrchestrateRequest(context.Background(), request)
}
