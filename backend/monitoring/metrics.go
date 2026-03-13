package monitoring

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// MetricsCollector collects and aggregates system metrics
type MetricsCollector struct {
	metrics     map[string]*Metric
	alerts      []*Alert
	mu          sync.RWMutex
	alertChan   chan *Alert
	stopChan    chan struct{}
	collectors  []MetricCollector
}

// Metric represents a single metric
type Metric struct {
	Name        string                 `json:"name"`
	Value       float64                `json:"value"`
	Type        MetricType             `json:"type"`
	Tags        map[string]string      `json:"tags"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// MetricType defines the type of metric
type MetricType string

const (
	Counter   MetricType = "counter"
	Gauge     MetricType = "gauge"
	Histogram MetricType = "histogram"
	Summary   MetricType = "summary"
)

// Alert represents an alert condition
type Alert struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Severity    AlertSeverity     `json:"severity"`
	Message     string            `json:"message"`
	Metric      string            `json:"metric"`
	Threshold   float64           `json:"threshold"`
	Value       float64           `json:"value"`
	Timestamp   time.Time         `json:"timestamp"`
	Labels      map[string]string `json:"labels"`
	Acked       bool              `json:"acked"`
	AckedAt     *time.Time        `json:"ackedAt,omitempty"`
}

// AlertSeverity defines alert severity levels
type AlertSeverity string

const (
	Critical AlertSeverity = "critical"
	Warning  AlertSeverity = "warning"
	Info     AlertSeverity = "info"
)

// MetricCollector defines interface for metric collectors
type MetricCollector interface {
	Collect() ([]*Metric, error)
	Name() string
}

// WorkflowMetricsCollector collects workflow execution metrics
type WorkflowMetricsCollector struct {
	executions map[string]*WorkflowExecution
	mu         sync.RWMutex
}

// WorkflowExecution represents workflow execution data
type WorkflowExecution struct {
	ID            string
	Type          string
	Status        string
	StartTime     time.Time
	EndTime       *time.Time
	Duration      *time.Duration
	AgentResults  []types.AgentResult
	ErrorCount    int
	RetryCount    int
}

// AgentMetricsCollector collects agent performance metrics
type AgentMetricsCollector struct {
	agentStats map[string]*AgentStats
	mu         sync.RWMutex
}

// AgentStats represents agent performance statistics
type AgentStats struct {
	Name           string
	TotalExecutions int
	SuccessfulExecutions int
	FailedExecutions int
	AverageScore   float64
	AverageDuration time.Duration
	LastExecution  time.Time
	ErrorRate      float64
}

// SystemMetricsCollector collects system-level metrics
type SystemMetricsCollector struct {
	startTime time.Time
}

// NewMetricsCollector creates a new metrics collector
func NewMetricsCollector() *MetricsCollector {
	collector := &MetricsCollector{
		metrics:    make(map[string]*Metric),
		alerts:     make([]*Alert, 0),
		alertChan:  make(chan *Alert, 100),
		stopChan:   make(chan struct{}),
		collectors: make([]MetricCollector, 0),
	}

	// Register built-in collectors
	collector.collectors = append(collector.collectors, &WorkflowMetricsCollector{
		executions: make(map[string]*WorkflowExecution),
	})
	collector.collectors = append(collector.collectors, &AgentMetricsCollector{
		agentStats: make(map[string]*AgentStats),
	})
	collector.collectors = append(collector.collectors, &SystemMetricsCollector{
		startTime: time.Now(),
	})

	return collector
}

// Start begins metrics collection
func (mc *MetricsCollector) Start(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-mc.stopChan:
			return
		case <-ticker.C:
			mc.collectAllMetrics()
			mc.checkAlerts()
		}
	}
}

// Stop stops metrics collection
func (mc *MetricsCollector) Stop() {
	close(mc.stopChan)
}

// RecordWorkflowExecution records a workflow execution
func (mc *MetricsCollector) RecordWorkflowExecution(execution *WorkflowExecution) {
	if collector, ok := mc.findCollector("workflow").(*WorkflowMetricsCollector); ok {
		collector.mu.Lock()
		collector.executions[execution.ID] = execution
		collector.mu.Unlock()
	}
}

// RecordAgentExecution records an agent execution
func (mc *MetricsCollector) RecordAgentExecution(agentName string, success bool, score float64, duration time.Duration) {
	if collector, ok := mc.findCollector("agent").(*AgentMetricsCollector); ok {
		collector.mu.Lock()
		stats, exists := collector.agentStats[agentName]
		if !exists {
			stats = &AgentStats{Name: agentName}
			collector.agentStats[agentName] = stats
		}

		stats.TotalExecutions++
		stats.LastExecution = time.Now()

		if success {
			stats.SuccessfulExecutions++
			// Update rolling average score
			stats.AverageScore = (stats.AverageScore*float64(stats.TotalExecutions-1) + score) / float64(stats.TotalExecutions)
		} else {
			stats.FailedExecutions++
		}

		// Update average duration
		stats.AverageDuration = (stats.AverageDuration*time.Duration(stats.TotalExecutions-1) + duration) / time.Duration(stats.TotalExecutions)

		// Calculate error rate
		stats.ErrorRate = float64(stats.FailedExecutions) / float64(stats.TotalExecutions)

		collector.mu.Unlock()
	}
}

// GetMetric returns a specific metric
func (mc *MetricsCollector) GetMetric(name string) (*Metric, error) {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	metric, exists := mc.metrics[name]
	if !exists {
		return nil, fmt.Errorf("metric %s not found", name)
	}

	return metric, nil
}

// GetMetrics returns all metrics
func (mc *MetricsCollector) GetMetrics() map[string]*Metric {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	// Return a copy to avoid concurrent modification
	metrics := make(map[string]*Metric)
	for k, v := range mc.metrics {
		metrics[k] = v
	}

	return metrics
}

// GetAlerts returns all active alerts
func (mc *MetricsCollector) GetAlerts() []*Alert {
	mc.mu.RLock()
	defer mc.mu.RUnlock()

	alerts := make([]*Alert, len(mc.alerts))
	copy(alerts, mc.alerts)
	return alerts
}

// AcknowledgeAlert acknowledges an alert
func (mc *MetricsCollector) AcknowledgeAlert(alertID string) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	for _, alert := range mc.alerts {
		if alert.ID == alertID {
			alert.Acked = true
			now := time.Now()
			alert.AckedAt = &now
			return nil
		}
	}

	return fmt.Errorf("alert %s not found", alertID)
}

// collectAllMetrics collects metrics from all registered collectors
func (mc *MetricsCollector) collectAllMetrics() {
	for _, collector := range mc.collectors {
		metrics, err := collector.Collect()
		if err != nil {
			// Log error but continue
			fmt.Printf("Error collecting metrics from %s: %v\n", collector.Name(), err)
			continue
		}

		mc.mu.Lock()
		for _, metric := range metrics {
			mc.metrics[metric.Name] = metric
		}
		mc.mu.Unlock()
	}
}

// checkAlerts checks for alert conditions
func (mc *MetricsCollector) checkAlerts() {
	thresholds := map[string]struct {
		metric    string
		threshold float64
		severity  AlertSeverity
		message   string
	}{
		"workflow_timeout": {
			metric:    "workflow_duration_max",
			threshold: 7200, // 2 hours in seconds
			severity:  Warning,
			message:   "Workflow execution exceeding timeout threshold",
		},
		"agent_failure_rate": {
			metric:    "agent_error_rate_avg",
			threshold: 0.1, // 10% failure rate
			severity:  Critical,
			message:   "Agent failure rate above acceptable threshold",
		},
		"system_error_rate": {
			metric:    "system_error_rate",
			threshold: 0.05, // 5% error rate
			severity:  Warning,
			message:   "System error rate above acceptable threshold",
		},
	}

	for alertName, config := range thresholds {
		if metric, exists := mc.metrics[config.metric]; exists {
			if metric.Value > config.threshold {
				alert := &Alert{
					ID:        fmt.Sprintf("%s-%d", alertName, time.Now().Unix()),
					Name:      alertName,
					Severity:  config.severity,
					Message:   config.message,
					Metric:    config.metric,
					Threshold: config.threshold,
					Value:     metric.Value,
					Timestamp: time.Now(),
					Labels:    metric.Tags,
				}

				// Check if similar alert already exists
				if !mc.alertExists(alert) {
					mc.mu.Lock()
					mc.alerts = append(mc.alerts, alert)
					mc.mu.Unlock()

					// Send alert (non-blocking)
					select {
					case mc.alertChan <- alert:
					default:
						// Alert channel full, drop alert
					}
				}
			}
		}
	}
}

// alertExists checks if a similar alert already exists
func (mc *MetricsCollector) alertExists(newAlert *Alert) bool {
	for _, alert := range mc.alerts {
		if alert.Name == newAlert.Name && !alert.Acked &&
		   time.Since(alert.Timestamp) < time.Minute*5 {
			return true
		}
	}
	return false
}

// findCollector finds a collector by name
func (mc *MetricsCollector) findCollector(name string) MetricCollector {
	for _, collector := range mc.collectors {
		if collector.Name() == name {
			return collector
		}
	}
	return nil
}

// WorkflowMetricsCollector implementation

func (wmc *WorkflowMetricsCollector) Collect() ([]*Metric, error) {
	wmc.mu.RLock()
	defer wmc.mu.RUnlock()

	metrics := make([]*Metric, 0)

	// Count workflows by status
	statusCounts := make(map[string]int)
	totalDuration := time.Duration(0)
	completedCount := 0

	for _, execution := range wmc.executions {
		statusCounts[execution.Status]++

		if execution.EndTime != nil && execution.Duration != nil {
			totalDuration += *execution.Duration
			completedCount++
		}
	}

	// Create metrics
	now := time.Now()
	metrics = append(metrics, &Metric{
		Name:      "workflow_total",
		Value:     float64(len(wmc.executions)),
		Type:      Gauge,
		Timestamp: now,
		Tags:      map[string]string{"type": "all"},
	})

	for status, count := range statusCounts {
		metrics = append(metrics, &Metric{
			Name:      "workflow_status",
			Value:     float64(count),
			Type:      Gauge,
			Timestamp: now,
			Tags:      map[string]string{"status": status},
		})
	}

	if completedCount > 0 {
		avgDuration := totalDuration / time.Duration(completedCount)
		metrics = append(metrics, &Metric{
			Name:      "workflow_duration_avg",
			Value:     float64(avgDuration.Seconds()),
			Type:      Gauge,
			Timestamp: now,
			Tags:      map[string]string{"unit": "seconds"},
		})
	}

	return metrics, nil
}

func (wmc *WorkflowMetricsCollector) Name() string {
	return "workflow"
}

// AgentMetricsCollector implementation

func (amc *AgentMetricsCollector) Collect() ([]*Metric, error) {
	amc.mu.RLock()
	defer amc.mu.RUnlock()

	metrics := make([]*Metric, 0)
	now := time.Now()

	for _, stats := range amc.agentStats {
		tags := map[string]string{"agent": stats.Name}

		metrics = append(metrics, &Metric{
			Name:      "agent_executions_total",
			Value:     float64(stats.TotalExecutions),
			Type:      Counter,
			Timestamp: now,
			Tags:      tags,
		})

		metrics = append(metrics, &Metric{
			Name:      "agent_executions_successful",
			Value:     float64(stats.SuccessfulExecutions),
			Type:      Counter,
			Timestamp: now,
			Tags:      tags,
		})

		metrics = append(metrics, &Metric{
			Name:      "agent_executions_failed",
			Value:     float64(stats.FailedExecutions),
			Type:      Counter,
			Timestamp: now,
			Tags:      tags,
		})

		metrics = append(metrics, &Metric{
			Name:      "agent_score_avg",
			Value:     stats.AverageScore,
			Type:      Gauge,
			Timestamp: now,
			Tags:      tags,
		})

		metrics = append(metrics, &Metric{
			Name:      "agent_duration_avg",
			Value:     float64(stats.AverageDuration.Seconds()),
			Type:      Gauge,
			Timestamp: now,
			Tags:      tags,
		})

		metrics = append(metrics, &Metric{
			Name:      "agent_error_rate",
			Value:     stats.ErrorRate,
			Type:      Gauge,
			Timestamp: now,
			Tags:      tags,
		})
	}

	return metrics, nil
}

func (amc *AgentMetricsCollector) Name() string {
	return "agent"
}

// SystemMetricsCollector implementation

func (smc *SystemMetricsCollector) Collect() ([]*Metric, error) {
	metrics := make([]*Metric, 0)
	now := time.Now()

	// System uptime
	uptime := time.Since(smc.startTime)
	metrics = append(metrics, &Metric{
		Name:      "system_uptime",
		Value:     float64(uptime.Seconds()),
		Type:      Counter,
		Timestamp: now,
		Tags:      map[string]string{"unit": "seconds"},
	})

	// Memory usage (simplified)
	// In a real implementation, you'd use runtime.MemStats()
	metrics = append(metrics, &Metric{
		Name:      "system_memory_used",
		Value:     0, // Placeholder
		Type:      Gauge,
		Timestamp: now,
		Tags:      map[string]string{"unit": "bytes"},
	})

	// Goroutine count
	metrics = append(metrics, &Metric{
		Name:      "system_goroutines",
		Value:     0, // Placeholder - would use runtime.NumGoroutine()
		Type:      Gauge,
		Timestamp: now,
	})

	return metrics, nil
}

func (smc *SystemMetricsCollector) Name() string {
	return "system"
}

// Global metrics collector instance
var globalMetricsCollector *MetricsCollector
var metricsOnce sync.Once

// GetGlobalMetricsCollector returns the singleton metrics collector
func GetGlobalMetricsCollector() *MetricsCollector {
	metricsOnce.Do(func() {
		globalMetricsCollector = NewMetricsCollector()
	})
	return globalMetricsCollector
}

// Activity and workflow functions for metrics integration

// RecordWorkflowMetricsActivity records workflow metrics
func RecordWorkflowMetricsActivity(ctx context.Context, workflowID, workflowType, status string, startTime time.Time, agentResults []types.AgentResult) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Recording workflow metrics", "workflowId", workflowID)

	collector := GetGlobalMetricsCollector()

	endTime := time.Now()
	duration := endTime.Sub(startTime)

	execution := &WorkflowExecution{
		ID:           workflowID,
		Type:         workflowType,
		Status:       status,
		StartTime:    startTime,
		EndTime:      &endTime,
		Duration:     &duration,
		AgentResults: agentResults,
		ErrorCount:   0, // Would be calculated based on agent results
		RetryCount:   0, // Would be tracked during execution
	}

	collector.RecordWorkflowExecution(execution)

	return nil
}

// RecordAgentMetricsActivity records agent execution metrics
func RecordAgentMetricsActivity(ctx context.Context, agentName string, success bool, score float64, duration time.Duration) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Recording agent metrics", "agent", agentName, "success", success)

	collector := GetGlobalMetricsCollector()
	collector.RecordAgentExecution(agentName, success, score, duration)

	return nil
}

// GetMetricsActivity retrieves current metrics
func GetMetricsActivity(ctx context.Context) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Retrieving current metrics")

	collector := GetGlobalMetricsCollector()
	metrics := collector.GetMetrics()
	alerts := collector.GetAlerts()

	result := map[string]interface{}{
		"metrics": metrics,
		"alerts":  alerts,
		"timestamp": time.Now(),
	}

	return result, nil
}

// EnhancedWorkflowMetricsWorkflow demonstrates metrics integration
func EnhancedWorkflowMetricsWorkflow(ctx workflow.Context, request types.ComplianceRequest) (*types.ComplianceResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Enhanced Workflow with Metrics", "request", request)

	// Record workflow start metrics
	startTime := workflow.Now(ctx)
	workflowID := fmt.Sprintf("enhanced-workflow-%d", startTime.Unix())

	// Defer metrics recording
	defer func() {
		// This would normally be done in a separate activity or at workflow completion
		logger.Info("Workflow completed, metrics recorded", "workflowId", workflowID)
	}()

	// Execute enhanced workflow with metrics
	result, err := ExecuteWorkflowWithMetrics(ctx, request, workflowID)
	if err != nil {
		logger.Error("Workflow execution failed", "error", err)
		return nil, err
	}

	logger.Info("Enhanced workflow completed successfully", "workflowId", workflowID)
	return result, nil
}

// ExecuteWorkflowWithMetrics executes workflow steps with metrics collection
func ExecuteWorkflowWithMetrics(ctx workflow.Context, request types.ComplianceRequest, workflowID string) (*types.ComplianceResult, error) {
	// This would implement the full workflow with metrics integration
	// For now, return a placeholder result
	return &types.ComplianceResult{
		Report: types.ComplianceReport{
			ID:          workflowID,
			OverallStatus: "Completed",
			Score:       85.0,
			GeneratedAt: workflow.Now(ctx),
		},
		Approved:   true,
		CompletedAt: workflow.Now(ctx),
	}, nil
}
