package monitoring

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// HTTPMetricsServer exposes metrics via HTTP endpoints
type HTTPMetricsServer struct {
	collector *MetricsCollector
	server    *http.Server
	port      int
}

// DashboardData represents the data structure for the dashboard
type DashboardData struct {
	Agents        []AgentDashboardInfo `json:"agents"`
	Workflows     WorkflowDashboardInfo `json:"workflows"`
	System        SystemDashboardInfo  `json:"system"`
	Timestamp     time.Time            `json:"timestamp"`
}

// AgentDashboardInfo represents agent data for the dashboard
type AgentDashboardInfo struct {
	Name            string            `json:"name"`
	Status          string            `json:"status"`
	Language        string            `json:"language"`
	CurrentActivity string            `json:"currentActivity"`
	Skills          []string          `json:"skills"`
	CPU             float64           `json:"cpu"`
	Memory          float64           `json:"memory"`
	Uptime          string            `json:"uptime"`
	LastExecution   *time.Time        `json:"lastExecution,omitempty"`
	ErrorRate       float64           `json:"errorRate"`
	Score           float64           `json:"score"`
}

// WorkflowDashboardInfo represents workflow data for the dashboard
type WorkflowDashboardInfo struct {
	ActiveWorkflows  int     `json:"activeWorkflows"`
	TotalWorkflows   int     `json:"totalWorkflows"`
	SkillsExecuted   int     `json:"skillsExecuted"`
	AvgResponseTime  int     `json:"avgResponseTime"`
	SuccessRate      float64 `json:"successRate"`
	ErrorRate        float64 `json:"errorRate"`
}

// SystemDashboardInfo represents system data for the dashboard
type SystemDashboardInfo struct {
	Uptime       string  `json:"uptime"`
	MemoryUsed   float64 `json:"memoryUsed"`
	CPUUsed      float64 `json:"cpuUsed"`
	Goroutines   int     `json:"goroutines"`
	Alerts       int     `json:"alerts"`
}

// NewHTTPMetricsServer creates a new HTTP metrics server
func NewHTTPMetricsServer(collector *MetricsCollector, port int) *HTTPMetricsServer {
	return &HTTPMetricsServer{
		collector: collector,
		port:      port,
	}
}

// Start starts the HTTP metrics server
func (hms *HTTPMetricsServer) Start(ctx context.Context) error {
	router := mux.NewRouter()
	
	// Prometheus metrics endpoint
	router.Handle("/metrics", promhttp.Handler()).Methods("GET")
	
	// Dashboard API endpoints
	router.HandleFunc("/api/agents/status", hms.handleAgentsStatus).Methods("GET")
	router.HandleFunc("/api/agents/detailed", hms.handleAgentsDetailed).Methods("GET")
	router.HandleFunc("/api/workflows/status", hms.handleWorkflowsStatus).Methods("GET")
	router.HandleFunc("/api/metrics/real-time", hms.handleRealTimeMetrics).Methods("GET")
	router.HandleFunc("/api/system/health", hms.handleSystemHealth).Methods("GET")
	router.HandleFunc("/api/alerts", hms.handleAlerts).Methods("GET")
	
	// Health check
	router.HandleFunc("/health", hms.handleHealth).Methods("GET")
	
	hms.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", hms.port),
		Handler: router,
	}
	
	go func() {
		if err := hms.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("HTTP server error: %v\n", err)
		}
	}()
	
	return nil
}

// Stop stops the HTTP metrics server
func (hms *HTTPMetricsServer) Stop(ctx context.Context) error {
	if hms.server != nil {
		return hms.server.Shutdown(ctx)
	}
	return nil
}

// handleAgentsStatus returns basic agent status
func (hms *HTTPMetricsServer) handleAgentsStatus(w http.ResponseWriter, r *http.Request) {
	data := hms.getDashboardData()
	
	response := map[string]interface{}{
		"agent_count":       len(data.Agents),
		"active_agents":    hms.countActiveAgents(data.Agents),
		"skills_executed":   data.Workflows.SkillsExecuted,
		"avg_response_time": data.Workflows.AvgResponseTime,
		"timestamp":         time.Now(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleAgentsDetailed returns detailed agent information
func (hms *HTTPMetricsServer) handleAgentsDetailed(w http.ResponseWriter, r *http.Request) {
	data := hms.getDashboardData()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data.Agents)
}

// handleWorkflowsStatus returns workflow status information
func (hms *HTTPMetricsServer) handleWorkflowsStatus(w http.ResponseWriter, r *http.Request) {
	data := hms.getDashboardData()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data.Workflows)
}

// handleRealTimeMetrics returns real-time metrics
func (hms *HTTPMetricsServer) handleRealTimeMetrics(w http.ResponseWriter, r *http.Request) {
	data := hms.getDashboardData()
	
	response := map[string]interface{}{
		"agent_count":              len(data.Agents),
		"skills_executed":          data.Workflows.SkillsExecuted,
		"errors_last_24h":          hms.calculate24HourErrors(),
		"avg_response_time":        data.Workflows.AvgResponseTime,
		"temporal_workflows_active": data.Workflows.ActiveWorkflows,
		"memory_usage_mb":          data.System.MemoryUsed,
		"timestamp":                time.Now(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleSystemHealth returns system health information
func (hms *HTTPMetricsServer) handleSystemHealth(w http.ResponseWriter, r *http.Request) {
	data := hms.getDashboardData()
	
	response := map[string]interface{}{
		"status":      "healthy",
		"uptime":      data.System.Uptime,
		"agents":      len(data.Agents),
		"workflows":   data.Workflows.ActiveWorkflows,
		"alerts":      data.System.Alerts,
		"timestamp":   time.Now(),
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleAlerts returns current alerts
func (hms *HTTPMetricsServer) handleAlerts(w http.ResponseWriter, r *http.Request) {
	alerts := hms.collector.GetAlerts()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(alerts)
}

// handleHealth returns health status
func (hms *HTTPMetricsServer) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

// getDashboardData aggregates data for the dashboard
func (hms *HTTPMetricsServer) getDashboardData() *DashboardData {
	// Get metrics from collector
	metrics := hms.collector.GetMetrics()
	
	// Build agent data
	agents := hms.buildAgentInfo(metrics)
	
	// Build workflow data
	workflows := hms.buildWorkflowInfo(metrics)
	
	// Build system data
	system := hms.buildSystemInfo(metrics)
	
	return &DashboardData{
		Agents:    agents,
		Workflows: workflows,
		System:    system,
		Timestamp: time.Now(),
	}
}

// buildAgentInfo creates agent dashboard information from metrics
func (hms *HTTPMetricsServer) buildAgentInfo(metrics map[string]*Metric) []AgentDashboardInfo {
	agents := make([]AgentDashboardInfo, 0)
	
	// Define known agents with their properties
	knownAgents := map[string]struct {
		language         string
		skills           []string
		defaultActivity  string
	}{
		"memory-agent-rust": {
			language:        "Rust",
			skills:          []string{"memory-consolidation", "context-retention", "inference-caching", "data-persistence"},
			defaultActivity: "Processing memory consolidation for active workflows",
		},
		"orchestration-agent-temporal": {
			language:        "Go",
			skills:          []string{"workflow-orchestration", "skill-coordination", "task-scheduling", "error-handling"},
			defaultActivity: "Coordinating workflows across skills",
		},
		"inference-gateway-python": {
			language:        "Python",
			skills:          []string{"ai-inference", "model-serving", "request-routing", "load-balancing"},
			defaultActivity: "Ready for inference requests",
		},
	}
	
	for agentName, agentInfo := range knownAgents {
		// Get agent-specific metrics
		agentMetrics := hms.getAgentMetrics(agentName, metrics)
		
		agent := AgentDashboardInfo{
			Name:            agentName,
			Status:          hms.determineAgentStatus(agentMetrics),
			Language:        agentInfo.language,
			CurrentActivity: agentInfo.defaultActivity,
			Skills:          agentInfo.skills,
			CPU:             hms.getAgentCPU(agentMetrics),
			Memory:          hms.getAgentMemory(agentMetrics),
			Uptime:          hms.getAgentUptime(agentMetrics),
			ErrorRate:       hms.getAgentErrorRate(agentMetrics),
			Score:           hms.getAgentScore(agentMetrics),
		}
		
		agents = append(agents, agent)
	}
	
	return agents
}

// buildWorkflowInfo creates workflow dashboard information
func (hms *HTTPMetricsServer) buildWorkflowInfo(metrics map[string]*Metric) WorkflowDashboardInfo {
	info := WorkflowDashboardInfo{
		ActiveWorkflows:  0, // Would be calculated from real workflow data
		TotalWorkflows:   0, // Would be calculated from real workflow data
		SkillsExecuted:   0, // Would be calculated from skill execution metrics
		AvgResponseTime:  0, // Would be calculated from response time metrics
		SuccessRate:     0, // Would be calculated from success/failure ratio
		ErrorRate:       0, // Would be calculated from error metrics
	}
	
	// Extract from metrics
	if metric, exists := metrics["workflow_total"]; exists {
		info.TotalWorkflows = int(metric.Value)
	}
	
	if metric, exists := metrics["workflow_status"]; exists {
		if metric.Tags["status"] == "running" {
			info.ActiveWorkflows = int(metric.Value)
		}
	}
	
	if metric, exists := metrics["workflow_duration_avg"]; exists {
		info.AvgResponseTime = int(metric.Value / 1000) // Convert to milliseconds
	}
	
	// Calculate skills executed from agent metrics
	for _, metric := range metrics {
		if metric.Name == "agent_executions_successful" {
			info.SkillsExecuted += int(metric.Value)
		}
	}
	
	return info
}

// buildSystemInfo creates system dashboard information
func (hms *HTTPMetricsServer) buildSystemInfo(metrics map[string]*Metric) SystemDashboardInfo {
	info := SystemDashboardInfo{
		Uptime:     "0h 0m",
		MemoryUsed: 0,
		CPUUsed:    0,
		Goroutines: 0,
		Alerts:     len(hms.collector.GetAlerts()),
	}
	
	// Extract from metrics
	if metric, exists := metrics["system_uptime"]; exists {
		uptime := time.Duration(metric.Value * 1000 * 1000 * 1000) // Convert from seconds
		hours := int(uptime.Hours())
		minutes := int(uptime.Minutes()) % 60
		info.Uptime = fmt.Sprintf("%dh %dm", hours, minutes)
	}
	
	if metric, exists := metrics["system_memory_used"]; exists {
		info.MemoryUsed = metric.Value / (1024 * 1024) // Convert to MB
	}
	
	if metric, exists := metrics["system_goroutines"]; exists {
		info.Goroutines = int(metric.Value)
	}
	
	return info
}

// Helper methods for extracting agent-specific metrics
func (hms *HTTPMetricsServer) getAgentMetrics(agentName string, metrics map[string]*Metric) map[string]*Metric {
	agentMetrics := make(map[string]*Metric)
	
	for key, metric := range metrics {
		if metric.Tags["agent"] == agentName {
			agentMetrics[key] = metric
		}
	}
	
	return agentMetrics
}

func (hms *HTTPMetricsServer) determineAgentMetrics(agentMetrics map[string]*Metric) string {
	// Determine status based on recent activity and error rate
	if errorRate, exists := agentMetrics["agent_error_rate"]; exists && errorRate.Value > 0.1 {
		return "error"
	}
	
	if lastExecution, exists := agentMetrics["agent_last_execution"]; exists {
		if time.Since(lastExecution.Timestamp) > time.Minute*5 {
			return "idle"
		}
		return "active"
	}
	
	return "unknown"
}

func (hms *HTTPMetricsServer) determineAgentStatus(agentMetrics map[string]*Metric) string {
	// Determine status based on recent activity and error rate
	if errorRate, exists := agentMetrics["agent_error_rate"]; exists && errorRate.Value > 0.1 {
		return "error"
	}
	
	// Check if agent has recent executions
	if executions, exists := agentMetrics["agent_executions_total"]; exists && executions.Value > 0 {
		return "active"
	}
	
	return "idle"
}

func (hms *HTTPMetricsServer) getAgentCPU(agentMetrics map[string]*Metric) float64 {
	// In a real implementation, this would come from actual CPU monitoring
	// For now, return a reasonable default based on agent type
	return 45.0 // Default placeholder
}

func (hms *HTTPMetricsServer) getAgentMemory(agentMetrics map[string]*Metric) float64 {
	// In a real implementation, this would come from actual memory monitoring
	// For now, return a reasonable default based on agent type
	return 128.0 // Default placeholder in MB
}

func (hms *HTTPMetricsServer) getAgentUptime(agentMetrics map[string]*Metric) string {
	// In a real implementation, this would come from actual uptime tracking
	// For now, return a reasonable default
	return "2h 15m" // Default placeholder
}

func (hms *HTTPMetricsServer) getAgentErrorRate(agentMetrics map[string]*Metric) float64 {
	if metric, exists := agentMetrics["agent_error_rate"]; exists {
		return metric.Value
	}
	return 0.0
}

func (hms *HTTPMetricsServer) getAgentScore(agentMetrics map[string]*Metric) float64 {
	if metric, exists := agentMetrics["agent_score_avg"]; exists {
		return metric.Value
	}
	return 0.0
}

func (hms *HTTPMetricsServer) countActiveAgents(agents []AgentDashboardInfo) int {
	count := 0
	for _, agent := range agents {
		if agent.Status == "active" {
			count++
		}
	}
	return count
}

func (hms *HTTPMetricsServer) calculate24HourErrors() int {
	// In a real implementation, this would calculate errors from the last 24 hours
	// For now, return a reasonable default
	return 2
}
