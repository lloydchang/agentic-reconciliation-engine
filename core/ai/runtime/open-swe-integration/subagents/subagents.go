package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Subagent represents an autonomous agent that can handle specific tasks
type Subagent interface {
	Name() string
	Type() string
	CanHandle(task *Task) bool
	Execute(ctx context.Context, task *Task) (*Result, error)
	GetCapabilities() []string
	GetStatus() *Status
}

// Task represents a unit of work for subagents
type Task struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Priority    int                    `json:"priority"`
	Data        map[string]interface{} `json:"data"`
	Context     map[string]interface{} `json:"context"`
	Timeout     time.Duration          `json:"timeout"`
	CreatedAt   time.Time              `json:"created_at"`
	StartedAt   time.Time              `json:"started_at,omitempty"`
	CompletedAt time.Time              `json:"completed_at,omitempty"`
	AssignedTo  string                 `json:"assigned_to,omitempty"`
	Status      string                 `json:"status"` // "pending", "assigned", "running", "completed", "failed"
}

// Result represents the output from a subagent execution
type Result struct {
	TaskID      string                 `json:"task_id"`
	Subagent    string                 `json:"subagent"`
	Status      string                 `json:"status"`
	Data        map[string]interface{} `json:"data"`
	Error       string                 `json:"error,omitempty"`
	Duration    time.Duration          `json:"duration"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Status represents the current status of a subagent
type Status struct {
	Name         string    `json:"name"`
	Type         string    `json:"type"`
	State        string    `json:"state"` // "idle", "busy", "error", "offline"
	TasksHandled int       `json:"tasks_handled"`
	LastActive   time.Time `json:"last_active"`
	ErrorRate    float64   `json:"error_rate"`
	AvgDuration  time.Duration `json:"avg_duration"`
}

// SubagentManager manages multiple subagents and task distribution
type SubagentManager struct {
	subagents    map[string]Subagent
	taskQueue    chan *Task
	resultQueue  chan *Result
	logger       *Logger
	mu           sync.RWMutex
	parallelism  int
	running      bool
	wg           sync.WaitGroup
}

// NewSubagentManager creates a new subagent manager
func NewSubagentManager(parallelism int, logger *Logger) *SubagentManager {
	return &SubagentManager{
		subagents:   make(map[string]Subagent),
		taskQueue:   make(chan *Task, 1000),
		resultQueue: make(chan *Result, 1000),
		logger:      logger,
		parallelism: parallelism,
		running:     false,
	}
}

// RegisterSubagent registers a new subagent
func (sm *SubagentManager) RegisterSubagent(subagent Subagent) {
	sm.mu.Lock()
	defer sm.mu.Unlock()
	
	sm.subagents[subagent.Name()] = subagent
	sm.logger.Info("Registered subagent", "name", subagent.Name(), "type", subagent.Type())
}

// Start starts the subagent manager
func (sm *SubagentManager) Start(ctx context.Context) error {
	sm.mu.Lock()
	if sm.running {
		sm.mu.Unlock()
		return fmt.Errorf("subagent manager already running")
	}
	sm.running = true
	sm.mu.Unlock()

	sm.logger.Info("Starting subagent manager", "parallelism", sm.parallelism)

	// Start worker goroutines
	for i := 0; i < sm.parallelism; i++ {
		sm.wg.Add(1)
		go sm.worker(ctx, i)
	}

	// Start result processor
	sm.wg.Add(1)
	go sm.resultProcessor(ctx)

	return nil
}

// Stop stops the subagent manager
func (sm *SubagentManager) Stop() {
	sm.mu.Lock()
	if !sm.running {
		sm.mu.Unlock()
		return
	}
	sm.running = false
	sm.mu.Unlock()

	close(sm.taskQueue)
	close(sm.resultQueue)
	
	sm.wg.Wait()
	sm.logger.Info("Subagent manager stopped")
}

// SubmitTask submits a task for processing
func (sm *SubagentManager) SubmitTask(task *Task) error {
	if !sm.running {
		return fmt.Errorf("subagent manager not running")
	}

	task.Status = "pending"
	task.CreatedAt = time.Now()

	select {
	case sm.taskQueue <- task:
		sm.logger.Info("Task submitted", "task_id", task.ID, "type", task.Type)
		return nil
	default:
		return fmt.Errorf("task queue is full")
	}
}

// GetResult returns a result from the result queue
func (sm *SubagentManager) GetResult(ctx context.Context) (*Result, error) {
	select {
	case result := <-sm.resultQueue:
		return result, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// worker processes tasks from the queue
func (sm *SubagentManager) worker(ctx context.Context, workerID int) {
	defer sm.wg.Done()
	
	sm.logger.Info("Worker started", "worker_id", workerID)
	
	for {
		select {
		case task, ok := <-sm.taskQueue:
			if !ok {
				sm.logger.Info("Worker stopping", "worker_id", workerID)
				return
			}
			sm.processTask(ctx, task, workerID)
		case <-ctx.Done():
			sm.logger.Info("Worker stopping", "worker_id", workerID)
			return
		}
	}
}

// processTask processes a single task
func (sm *SubagentManager) processTask(ctx context.Context, task *Task, workerID int) {
	sm.logger.Info("Processing task", "task_id", task.ID, "worker_id", workerID)
	
	// Find suitable subagent
	subagent := sm.findSubagent(task)
	if subagent == nil {
		result := &Result{
			TaskID:    task.ID,
			Status:    "failed",
			Error:     "no suitable subagent found",
			Timestamp: time.Now(),
		}
		sm.resultQueue <- result
		return
	}

	// Assign task to subagent
	task.AssignedTo = subagent.Name()
	task.StartedAt = time.Now()
	task.Status = "running"

	// Execute task with timeout
	taskCtx := ctx
	if task.Timeout > 0 {
		var cancel context.CancelFunc
		taskCtx, cancel = context.WithTimeout(ctx, task.Timeout)
		defer cancel()
	}

	start := time.Now()
	result, err := subagent.Execute(taskCtx, task)
	duration := time.Since(start)

	if err != nil {
		result = &Result{
			TaskID:    task.ID,
			Subagent:  subagent.Name(),
			Status:    "failed",
			Error:     err.Error(),
			Duration:  duration,
			Timestamp: time.Now(),
		}
	} else {
		result.Duration = duration
		result.Timestamp = time.Now()
	}

	task.CompletedAt = time.Now()
	task.Status = result.Status

	sm.resultQueue <- result
	sm.logger.Info("Task completed", "task_id", task.ID, "status", result.Status, "duration", duration)
}

// findSubagent finds the best subagent for a task
func (sm *SubagentManager) findSubagent(task *Task) Subagent {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	var bestSubagent Subagent
	bestScore := 0.0

	for _, subagent := range sm.subagents {
		if !subagent.CanHandle(task) {
			continue
		}

		// Calculate subagent score based on current load and capabilities
		status := subagent.GetStatus()
		score := sm.calculateScore(subagent, status, task)

		if score > bestScore {
			bestScore = score
			bestSubagent = subagent
		}
	}

	return bestSubagent
}

// calculateScore calculates a score for subagent selection
func (sm *SubagentManager) calculateScore(subagent Subagent, status *Status, task *Task) float64 {
	score := 1.0

	// Penalize busy subagents
	if status.State == "busy" {
		score *= 0.5
	} else if status.State == "error" {
		score *= 0.1
	} else if status.State == "offline" {
		score *= 0.0
		return 0
	}

	// Penalize high error rate
	if status.ErrorRate > 0.1 {
		score *= (1.0 - status.ErrorRate)
	}

	// Prefer subagents with lower average duration
	if status.AvgDuration > 0 {
		score *= 1.0 / (1.0 + status.AvgDuration.Seconds())
	}

	return score
}

// resultProcessor processes results from the result queue
func (sm *SubagentManager) resultProcessor(ctx context.Context) {
	defer sm.wg.Done()

	for {
		select {
		case result, ok := <-sm.resultQueue:
			if !ok {
				return
			}
			sm.handleResult(result)
		case <-ctx.Done():
			return
		}
	}
}

// handleResult handles a single result
func (sm *SubagentManager) handleResult(result *Result) {
	sm.logger.Info("Handling result", "task_id", result.TaskID, "status", result.Status)
	
	// Update subagent statistics
	sm.mu.RLock()
	if subagent, exists := sm.subagents[result.Subagent]; exists {
		status := subagent.GetStatus()
		// Update statistics (would be implemented in actual subagent)
		_ = status
	}
	sm.mu.RUnlock()

	// Store result for retrieval (would be implemented with proper storage)
	_ = result
}

// GetStatus returns the status of all subagents
func (sm *SubagentManager) GetStatus() map[string]*Status {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	status := make(map[string]*Status)
	for name, subagent := range sm.subagents {
		status[name] = subagent.GetStatus()
	}
	return status
}

// GetQueueStatus returns queue statistics
func (sm *SubagentManager) GetQueueStatus() map[string]interface{} {
	return map[string]interface{}{
		"queue_length":   len(sm.taskQueue),
		"parallelism":    sm.parallelism,
		"running":        sm.running,
		"subagents":      len(sm.subagents),
	}
}

// DeploymentSubagent handles deployment-related tasks
type DeploymentSubagent struct {
	name    string
	status  *Status
	logger  *Logger
}

func NewDeploymentSubagent(logger *Logger) *DeploymentSubagent {
	return &DeploymentSubagent{
		name: "deployment-agent",
		status: &Status{
			Name:         "deployment-agent",
			Type:         "deployment",
			State:        "idle",
			TasksHandled: 0,
			LastActive:   time.Now(),
			ErrorRate:    0.0,
			AvgDuration:  0,
		},
		logger: logger,
	}
}

func (ds *DeploymentSubagent) Name() string { return ds.name }
func (ds *DeploymentSubagent) Type() string { return "deployment" }

func (ds *DeploymentSubagent) CanHandle(task *Task) bool {
	return task.Type == "deploy" || task.Type == "scale" || task.Type == "rollback"
}

func (ds *DeploymentSubagent) Execute(ctx context.Context, task *Task) (*Result, error) {
	ds.status.State = "busy"
	ds.status.LastActive = time.Now()
	defer func() { ds.status.State = "idle" }()

	ds.logger.Info("Executing deployment task", "task_id", task.ID, "type", task.Type)

	// Simulate deployment work
	time.Sleep(2 * time.Second)

	// Update statistics
	ds.status.TasksHandled++
	
	result := &Result{
		TaskID:   task.ID,
		Subagent: ds.name,
		Status:   "completed",
		Data: map[string]interface{}{
			"deployment_id": fmt.Sprintf("deploy-%d", time.Now().Unix()),
			"environment":   task.Data["environment"],
			"service":       task.Data["service"],
		},
		Timestamp: time.Now(),
	}

	return result, nil
}

func (ds *DeploymentSubagent) GetCapabilities() []string {
	return []string{"deploy", "scale", "rollback", "blue-green", "canary"}
}

func (ds *DeploymentSubagent) GetStatus() *Status {
	return ds.status
}

// SecuritySubagent handles security-related tasks
type SecuritySubagent struct {
	name    string
	status  *Status
	logger  *Logger
}

func NewSecuritySubagent(logger *Logger) *SecuritySubagent {
	return &SecuritySubagent{
		name: "security-agent",
		status: &Status{
			Name:         "security-agent",
			Type:         "security",
			State:        "idle",
			TasksHandled: 0,
			LastActive:   time.Now(),
			ErrorRate:    0.0,
			AvgDuration:  0,
		},
		logger: logger,
	}
}

func (ss *SecuritySubagent) Name() string { return ss.name }
func (ss *SecuritySubagent) Type() string { return "security" }

func (ss *SecuritySubagent) CanHandle(task *Task) bool {
	return task.Type == "security" || task.Type == "audit" || task.Type == "compliance"
}

func (ss *SecuritySubagent) Execute(ctx context.Context, task *Task) (*Result, error) {
	ss.status.State = "busy"
	ss.status.LastActive = time.Now()
	defer func() { ss.status.State = "idle" }()

	ss.logger.Info("Executing security task", "task_id", task.ID, "type", task.Type)

	// Simulate security scan
	time.Sleep(3 * time.Second)

	ss.status.TasksHandled++

	result := &Result{
		TaskID:   task.ID,
		Subagent: ss.name,
		Status:   "completed",
		Data: map[string]interface{}{
			"scan_id":   fmt.Sprintf("scan-%d", time.Now().Unix()),
			"findings":  []string{"No critical vulnerabilities found"},
			"severity":  "low",
		},
		Timestamp: time.Now(),
	}

	return result, nil
}

func (ss *SecuritySubagent) GetCapabilities() []string {
	return []string{"vulnerability-scan", "compliance-check", "audit", "penetration-test"}
}

func (ss *SecuritySubagent) GetStatus() *Status {
	return ss.status
}
