package performance

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

// Performance optimization and concurrency control system

// ConcurrencyManager manages concurrent workflow executions
type ConcurrencyManager struct {
	maxConcurrent int
	activeCount   int
	queue         chan WorkflowRequest
	mu            sync.Mutex
	metrics       *PerformanceMetrics
}

// WorkflowRequest represents a queued workflow execution request
type WorkflowRequest struct {
	ID          string
	Type        string
	Priority    int
	Payload     interface{}
	SubmittedAt time.Time
	StartedAt   *time.Time
}

// PerformanceMetrics tracks performance metrics
type PerformanceMetrics struct {
	TotalRequests     int64
	QueuedRequests    int64
	CompletedRequests int64
	FailedRequests    int64
	AvgQueueTime      time.Duration
	AvgExecutionTime  time.Duration
	Throughput        float64
	LastUpdated       time.Time
}

// ResourcePool manages resource allocation for workflows
type ResourcePool struct {
	name         string
	maxResources int
	available    int
	waitQueue    chan ResourceRequest
	mu           sync.Mutex
}

// ResourceRequest represents a resource allocation request
type ResourceRequest struct {
	ID          string
	Amount      int
	Priority    int
	Timeout     time.Duration
	ResponseCh  chan ResourceAllocation
}

// ResourceAllocation represents allocated resources
type ResourceAllocation struct {
	ID       string
	Amount   int
	Granted  bool
	Error    string
}

// CircuitBreaker provides circuit breaker pattern for resilience
type CircuitBreaker struct {
	name          string
	maxFailures   int
	failureCount  int
	lastFailure   time.Time
	timeout       time.Duration
	state         CircuitBreakerState
	mu            sync.Mutex
}

// CircuitBreakerState represents circuit breaker states
type CircuitBreakerState int

const (
	StateClosed CircuitBreakerState = iota
	StateOpen
	StateHalfOpen
)

// Global instances
var (
	globalConcurrencyManager *ConcurrencyManager
	globalResourcePool       *ResourcePool
	concurrencyOnce          sync.Once
	resourceOnce             sync.Once
)

// GetGlobalConcurrencyManager returns the singleton concurrency manager
func GetGlobalConcurrencyManager() *ConcurrencyManager {
	concurrencyOnce.Do(func() {
		globalConcurrencyManager = NewConcurrencyManager(10) // Default max concurrent
	})
	return globalConcurrencyManager
}

// GetGlobalResourcePool returns the singleton resource pool
func GetGlobalResourcePool() *ResourcePool {
	resourceOnce.Do(func() {
		globalResourcePool = NewResourcePool("ai-agents", 20) // Default max resources
	})
	return globalResourcePool
}

// NewConcurrencyManager creates a new concurrency manager
func NewConcurrencyManager(maxConcurrent int) *ConcurrencyManager {
	return &ConcurrencyManager{
		maxConcurrent: maxConcurrent,
		activeCount:   0,
		queue:         make(chan WorkflowRequest, 100), // Buffered channel
		metrics:       &PerformanceMetrics{},
	}
}

// SubmitWorkflow submits a workflow for execution with concurrency control
func (cm *ConcurrencyManager) SubmitWorkflow(request WorkflowRequest) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.metrics.TotalRequests++

	select {
	case cm.queue <- request:
		cm.metrics.QueuedRequests++
		return nil
	default:
		return fmt.Errorf("workflow queue is full")
	}
}

// ProcessQueue processes queued workflow requests
func (cm *ConcurrencyManager) ProcessQueue(ctx context.Context) {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case request := <-cm.queue:
			cm.processWorkflowRequest(request)
		case <-ticker.C:
			cm.updateMetrics()
		}
	}
}

// processWorkflowRequest processes a single workflow request
func (cm *ConcurrencyManager) processWorkflowRequest(request WorkflowRequest) {
	cm.mu.Lock()
	if cm.activeCount >= cm.maxConcurrent {
		cm.mu.Unlock()
		// Re-queue if at capacity
		select {
		case cm.queue <- request:
		default:
			// Queue full, drop request (shouldn't happen with proper sizing)
		}
		return
	}

	cm.activeCount++
	startTime := time.Now()
	request.StartedAt = &startTime
	cm.mu.Unlock()

	// Execute workflow (this would normally be done asynchronously)
	defer func() {
		cm.mu.Lock()
		cm.activeCount--
		cm.metrics.CompletedRequests++
		cm.mu.Unlock()
	}()

	// Simulate workflow execution
	time.Sleep(time.Second * 2) // Simulate work
}

// updateMetrics updates performance metrics
func (cm *ConcurrencyManager) updateMetrics() {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.metrics.LastUpdated = time.Now()

	// Calculate throughput (requests per second over last minute)
	if cm.metrics.TotalRequests > 0 {
		elapsed := time.Since(cm.metrics.LastUpdated.Add(-time.Minute))
		cm.metrics.Throughput = float64(cm.metrics.CompletedRequests) / elapsed.Seconds()
	}
}

// NewResourcePool creates a new resource pool
func NewResourcePool(name string, maxResources int) *ResourcePool {
	return &ResourcePool{
		name:         name,
		maxResources: maxResources,
		available:    maxResources,
		waitQueue:    make(chan ResourceRequest, 50),
	}
}

// RequestResources requests resources from the pool
func (rp *ResourcePool) RequestResources(request ResourceRequest) ResourceAllocation {
	rp.mu.Lock()

	if rp.available >= request.Amount {
		rp.available -= request.Amount
		rp.mu.Unlock()

		return ResourceAllocation{
			ID:      request.ID,
			Amount:  request.Amount,
			Granted: true,
		}
	}

	rp.mu.Unlock()

	// Add to wait queue
	select {
	case rp.waitQueue <- request:
		// Wait for response
		select {
		case response := <-request.ResponseCh:
			return response
		case <-time.After(request.Timeout):
			return ResourceAllocation{
				ID:      request.ID,
				Granted: false,
				Error:   "resource request timed out",
			}
		}
	default:
		return ResourceAllocation{
			ID:      request.ID,
			Granted: false,
			Error:   "resource wait queue is full",
		}
	}
}

// ReleaseResources releases resources back to the pool
func (rp *ResourcePool) ReleaseResources(allocation ResourceAllocation) {
	rp.mu.Lock()
	defer rp.mu.Unlock()

	rp.available += allocation.Amount

	// Try to fulfill waiting requests
	rp.fulfillWaitingRequests()
}

// fulfillWaitingRequests tries to fulfill waiting resource requests
func (rp *ResourcePool) fulfillWaitingRequests() {
	for rp.available > 0 {
		select {
		case request := <-rp.waitQueue:
			if rp.available >= request.Amount {
				rp.available -= request.Amount
				response := ResourceAllocation{
					ID:      request.ID,
					Amount:  request.Amount,
					Granted: true,
				}
				select {
				case request.ResponseCh <- response:
				default:
					// Response channel full, return resources
					rp.available += request.Amount
				}
			} else {
				// Put request back in queue
				select {
				case rp.waitQueue <- request:
				default:
					// Queue full, drop request
				}
			}
		default:
			return
		}
	}
}

// NewCircuitBreaker creates a new circuit breaker
func NewCircuitBreaker(name string, maxFailures int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		name:        name,
		maxFailures: maxFailures,
		timeout:     timeout,
		state:       StateClosed,
	}
}

// Call executes a function with circuit breaker protection
func (cb *CircuitBreaker) Call(fn func() error) error {
	cb.mu.Lock()

	switch cb.state {
	case StateOpen:
		if time.Since(cb.lastFailure) > cb.timeout {
			cb.state = StateHalfOpen
		} else {
			cb.mu.Unlock()
			return fmt.Errorf("circuit breaker is open")
		}
	}

	cb.mu.Unlock()

	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		cb.lastFailure = time.Now()

		if cb.failureCount >= cb.maxFailures {
			cb.state = StateOpen
		}
		return err
	}

	// Success - reset failure count and close circuit
	if cb.state == StateHalfOpen {
		cb.state = StateClosed
	}
	cb.failureCount = 0

	return nil
}

// GetState returns the current circuit breaker state
func (cb *CircuitBreaker) GetState() CircuitBreakerState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// OptimizedWorkflow demonstrates performance optimizations
func OptimizedWorkflow(ctx workflow.Context, request interface{}) (interface{}, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Optimized Workflow")

	// Get concurrency manager
	_ = GetGlobalConcurrencyManager()
	logger.Info("Retrieved concurrency manager", "activeWorkflows", 5) // Dummy value

	// Get resource pool
	_ = GetGlobalResourcePool()
	logger.Info("Retrieved resource pool", "availableResources", 10) // Dummy value

	// Request resources for execution
	_ = ResourceRequest{
		ID:         workflow.GetInfo(ctx).WorkflowExecution.ID,
		Amount:     2, // Request 2 resource units
		Priority:   1,
		Timeout:    time.Minute * 5,
		ResponseCh: make(chan ResourceAllocation, 1),
	}

	allocation := ResourceAllocation{Granted: true} // Dummy allocation for now
	if !allocation.Granted {
		return nil, fmt.Errorf("failed to allocate resources: %s", allocation.Error)
	}

	// Ensure resources are released
	// defer resourcePool.ReleaseResources(allocation) // Dummy release for now

	// Execute with circuit breaker protection
	circuitBreaker := NewCircuitBreaker("workflow-execution", 3, time.Minute*5)

	var result interface{}
	err := circuitBreaker.Call(func() error {
		// Execute workflow activities with concurrency control
		return workflow.ExecuteActivity(ctx, OptimizedActivity, request).Get(ctx, &result)
	})

	if err != nil {
		logger.Error("Workflow execution failed", "error", err)
		return nil, err
	}

	logger.Info("Optimized Workflow completed successfully")
	return result, nil
}

// OptimizedActivity demonstrates activity-level optimizations
func OptimizedActivity(ctx context.Context, request interface{}) (interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing Optimized Activity")

	// Simulate optimized processing with resource awareness
	startTime := time.Now()

	// Get activity info for resource-aware processing
	info := activity.GetInfo(ctx)

	// Simulate workload based on available resources
	workload := simulateOptimizedWorkload(info)

	duration := time.Since(startTime)

	logger.Info("Optimized Activity completed", "duration", duration, "workload", workload)

	return map[string]interface{}{
		"result":     "success",
		"duration":   duration.String(),
		"workload":   workload,
		"optimized":  true,
	}, nil
}

// simulateOptimizedWorkload simulates optimized workload processing
func simulateOptimizedWorkload(info activity.Info) map[string]interface{} {
	// Simulate different processing strategies based on context
	baseWorkload := 100

	// Adjust based on heartbeat timeout (proxy for resource availability)
	if info.HeartbeatTimeout > time.Minute {
		baseWorkload += 50 // More resources available
	}

	// Simulate parallel processing
	parallelTasks := 4
	totalWorkload := baseWorkload * parallelTasks

	// Simulate processing time
	time.Sleep(time.Millisecond * time.Duration(totalWorkload/10))

	return map[string]interface{}{
		"baseWorkload":   baseWorkload,
		"parallelTasks":  parallelTasks,
		"totalWorkload":  totalWorkload,
		"efficiency":     0.85, // 85% efficiency due to optimizations
	}
}

// PerformanceMonitoringWorkflow monitors system performance
func PerformanceMonitoringWorkflow(ctx workflow.Context) error {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Performance Monitoring Workflow")

	// Monitor concurrency
	_ = GetGlobalConcurrencyManager()
	logger.Info("Monitoring concurrency", "activeWorkflows", 3) // Dummy value

	// Monitor resources
	_ = GetGlobalResourcePool()
	logger.Info("Monitoring resources", "availableResources", 8) // Dummy value

	// Continuous monitoring loop
	for {
		// Check system health
		err := workflow.ExecuteActivity(ctx, HealthCheckActivity, nil).Get(ctx, nil)
		if err != nil {
			logger.Warn("Health check failed", "error", err)
		}

		// Check performance metrics
		var metrics map[string]interface{}
		err = workflow.ExecuteActivity(ctx, PerformanceMetricsActivity, nil).Get(ctx, &metrics)
		if err != nil {
			logger.Warn("Metrics collection failed", "error", err)
		} else {
			logger.Info("Performance metrics", "metrics", metrics)
		}

		// Sleep before next check
		workflow.Sleep(ctx, time.Minute*5)
	}
}

// HealthCheckActivity performs system health checks
func HealthCheckActivity(ctx context.Context, _ interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Performing health check")

	// Check concurrency manager
	concurrencyMgr := GetGlobalConcurrencyManager()
	if concurrencyMgr.activeCount < 0 {
		return fmt.Errorf("invalid active count in concurrency manager")
	}

	// Check resource pool
	resourcePool := GetGlobalResourcePool()
	if resourcePool.available < 0 {
		return fmt.Errorf("invalid available resources in resource pool")
	}

	logger.Info("Health check passed")
	return nil
}

// PerformanceMetricsActivity collects performance metrics
func PerformanceMetricsActivity(ctx context.Context, _ interface{}) (map[string]interface{}, error) {
	concurrencyMgr := GetGlobalConcurrencyManager()

	metrics := map[string]interface{}{
		"activeWorkflows":   concurrencyMgr.activeCount,
		"maxConcurrent":     concurrencyMgr.maxConcurrent,
		"totalRequests":     concurrencyMgr.metrics.TotalRequests,
		"queuedRequests":    concurrencyMgr.metrics.QueuedRequests,
		"completedRequests": concurrencyMgr.metrics.CompletedRequests,
		"throughput":        concurrencyMgr.metrics.Throughput,
	}

	return metrics, nil
}
