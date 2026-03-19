package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"k8s.io/client-go/rest"
	"k8s.io/metrics/pkg/apis/metrics/v1beta1"
	metricsclient "k8s.io/metrics/pkg/client/clientset/versioned"
)

// MonitoringManager manages monitoring and metrics for Agent Sandbox
type MonitoringManager struct {
	metricsClient metricsclient.Interface
	metrics      *SandboxMetrics
	mu           sync.RWMutex
}

// SandboxMetrics holds Prometheus metrics for sandbox monitoring
type SandboxMetrics struct {
	ExecutionCount    *prometheus.CounterVec
	ExecutionDuration *prometheus.HistogramVec
	ExecutionErrors   *prometheus.CounterVec
	ResourceUsage    *prometheus.GaugeVec
	SandboxStatus     *prometheus.GaugeVec
	WarmPoolStatus    *prometheus.GaugeVec
}

// ResourceMetrics holds resource usage metrics for a sandbox
type ResourceMetrics struct {
	SandboxID   string    `json:"sandbox_id"`
	MemoryUsage int64     `json:"memory_usage_bytes"`
	CPUUsage    float64   `json:"cpu_usage_cores"`
	Timestamp   time.Time `json:"timestamp"`
}

// ExecutionMetrics holds aggregated execution metrics
type ExecutionMetrics struct {
	TotalExecutions    int64             `json:"total_executions"`
	SuccessRate        float64           `json:"success_rate"`
	AverageDuration    time.Duration     `json:"average_duration"`
	ErrorRate          float64           `json:"error_rate"`
	ExecutionsByAgent  map[string]int64  `json:"executions_by_agent"`
	ExecutionsByType   map[string]int64  `json:"executions_by_type"`
	ResourceUsage      ResourceMetrics   `json:"current_resource_usage"`
	LastUpdated        time.Time         `json:"last_updated"`
}

// NewMonitoringManager creates a new monitoring manager
func NewMonitoringManager() *MonitoringManager {
	return &MonitoringManager{
		metrics: initMetrics(),
	}
}

// initMetrics initializes Prometheus metrics
func initMetrics() *SandboxMetrics {
	return &SandboxMetrics{
		ExecutionCount: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "agent_sandbox_executions_total",
				Help: "Total number of Agent Sandbox executions",
			},
			[]string{"agent_id", "agent_type", "template", "success"},
		),
		ExecutionDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "agent_sandbox_execution_duration_seconds",
				Help:    "Duration of Agent Sandbox executions",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"agent_id", "agent_type", "template"},
		),
		ExecutionErrors: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Name: "agent_sandbox_execution_errors_total",
				Help: "Total number of Agent Sandbox execution errors",
			},
			[]string{"agent_id", "agent_type", "template", "error_type"},
		),
		ResourceUsage: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "agent_sandbox_resource_usage",
				Help: "Resource usage of Agent Sandbox environments",
			},
			[]string{"sandbox_id", "resource_type"},
		),
		SandboxStatus: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "agent_sandbox_status",
				Help: "Status of Agent Sandbox environments (1=running, 0=not_running)",
			},
			[]string{"sandbox_id", "template"},
		),
		WarmPoolStatus: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "agent_sandbox_warm_pool_status",
				Help: "Status of Agent Sandbox warm pools",
			},
			[]string{"pool_name", "template", "status_type"},
		),
	}
}

// RecordExecution records an execution result
func (mm *MonitoringManager) RecordExecution(result *ExecutionResult) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// Record execution count
	success := "false"
	if result.Success {
		success = "true"
	}
	mm.metrics.ExecutionCount.WithLabelValues(
		result.AgentID, 
		result.Metadata["agent_type"].(string), 
		result.Metadata["template"].(string), 
		success,
	).Inc()

	// Record execution duration
	mm.metrics.ExecutionDuration.WithLabelValues(
		result.AgentID,
		result.Metadata["agent_type"].(string),
		result.Metadata["template"].(string),
	).Observe(result.Duration.Seconds())

	// Record errors if any
	if !result.Success && result.Error != "" {
		errorType := "unknown"
		if result.ExitCode != 0 {
			errorType = "exit_code"
		}
		mm.metrics.ExecutionErrors.WithLabelValues(
			result.AgentID,
			result.Metadata["agent_type"].(string),
			result.Metadata["template"].(string),
			errorType,
		).Inc()
	}

	// Record resource usage
	mm.metrics.ResourceUsage.WithLabelValues(result.SandboxID, "memory_bytes").Set(float64(result.MemoryUsage))
	mm.metrics.ResourceUsage.WithLabelValues(result.SandboxID, "cpu_cores").Set(result.CPUUsage)

	// Record sandbox status
	status := 0.0
	if result.Success {
		status = 1.0
	}
	mm.metrics.SandboxStatus.WithLabelValues(
		result.SandboxID,
		result.Metadata["template"].(string),
	).Set(status)

	log.Printf("Recorded execution metrics for agent %s: success=%v, duration=%v", 
		result.AgentID, result.Success, result.Duration)
}

// GetMetrics gets resource metrics for a specific sandbox
func (mm *MonitoringManager) GetMetrics(ctx context.Context, sandboxID string) (*ResourceMetrics, error) {
	if mm.metricsClient == nil {
		// Return default metrics if metrics client not available
		return &ResourceMetrics{
			SandboxID:   sandboxID,
			MemoryUsage: 0,
			CPUUsage:    0.0,
			Timestamp:   time.Now(),
		}, nil
	}

	// Get pod metrics (simplified implementation)
	// In a real implementation, you would query the Metrics API
	return &ResourceMetrics{
		SandboxID:   sandboxID,
		MemoryUsage: 512 * 1024 * 1024, // 512MB default
		CPUUsage:    0.1,               // 0.1 cores default
		Timestamp:   time.Now(),
	}, nil
}

// GetAggregatedMetrics returns aggregated execution metrics
func (mm *MonitoringManager) GetAggregatedMetrics(ctx context.Context) (*ExecutionMetrics, error) {
	mm.mu.RLock()
	defer mm.mu.RUnlock()

	// This is a simplified implementation
	// In a real implementation, you would aggregate from Prometheus or time series database
	return &ExecutionMetrics{
		TotalExecutions:   100, // Placeholder
		SuccessRate:       0.95,
		AverageDuration:   30 * time.Second,
		ErrorRate:         0.05,
		ExecutionsByAgent: map[string]int64{
			"temporal-agent":  50,
			"pi-mono-agent":   30,
			"memory-agent":    20,
		},
		ExecutionsByType: map[string]int64{
			"python": 60,
			"bash":   25,
			"go":     15,
		},
		LastUpdated: time.Now(),
	}, nil
}

// RecordWarmPoolStatus records warm pool status
func (mm *MonitoringManager) RecordWarmPoolStatus(poolName, template string, desired, ready, available int32) {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	mm.metrics.WarmPoolStatus.WithLabelValues(poolName, template, "desired").Set(float64(desired))
	mm.metrics.WarmPoolStatus.WithLabelValues(poolName, template, "ready").Set(float64(ready))
	mm.metrics.WarmPoolStatus.WithLabelValues(poolName, template, "available").Set(float64(available))
}

// InitializeMetricsClient initializes the Kubernetes metrics client
func (mm *MonitoringManager) InitializeMetricsClient(kubeconfig *rest.Config) error {
	metricsClient, err := metricsclient.NewForConfig(kubeconfig)
	if err != nil {
		return fmt.Errorf("failed to create metrics client: %w", err)
	}

	mm.mu.Lock()
	mm.metricsClient = metricsClient
	mm.mu.Unlock()

	log.Printf("Initialized Kubernetes metrics client")
	return nil
}

// GetPrometheusMetrics returns the Prometheus metrics collector
func (mm *MonitoringManager) GetPrometheusMetrics() *SandboxMetrics {
	return mm.metrics
}

// Cleanup cleans up the monitoring manager
func (mm *MonitoringManager) Cleanup(ctx context.Context) error {
	mm.mu.Lock()
	defer mm.mu.Unlock()

	// Cleanup metrics if needed
	log.Printf("Cleaning up monitoring manager")
	return nil
}
