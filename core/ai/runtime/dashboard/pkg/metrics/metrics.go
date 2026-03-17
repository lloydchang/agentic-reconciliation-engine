package metrics

import (
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	// Agent metrics
	agentsTotal = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "ai_agents_total",
			Help: "Current number of AI agents by language and status",
		},
		[]string{"language", "status"},
	)

	// Skill execution metrics
	skillExecutions = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "skill_executions_total",
			Help: "Total number of skill executions",
		},
		[]string{"skill_name", "status"},
	)

	skillDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "skill_execution_duration_seconds",
			Help:    "Duration of skill executions in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"skill_name"},
	)

	// API metrics
	apiRequests = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "api_requests_total",
			Help: "Total number of API requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	apiRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "api_request_duration_seconds",
			Help:    "Duration of API requests in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	// WebSocket metrics
	websocketConnections = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "websocket_connections_total",
			Help: "Current number of WebSocket connections",
		},
	)

	// System metrics
	systemErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "system_errors_total",
			Help: "Total number of system errors",
		},
		[]string{"component", "error_type"},
	)
)

func Init() {
	// Register metrics with Prometheus
	prometheus.MustRegister(agentsTotal)
	prometheus.MustRegister(skillExecutions)
	prometheus.MustRegister(skillDuration)
	prometheus.MustRegister(apiRequests)
	prometheus.MustRegister(apiRequestDuration)
	prometheus.MustRegister(websocketConnections)
	prometheus.MustRegister(systemErrors)
}

func Handler() http.Handler {
	return promhttp.Handler()
}

// Metric helper functions
func RecordAgentCount(language, status string, count float64) {
	agentsTotal.WithLabelValues(language, status).Set(count)
}

func RecordSkillExecution(skillName, status string) {
	skillExecutions.WithLabelValues(skillName, status).Inc()
}

func RecordSkillDuration(skillName string, duration float64) {
	skillDuration.WithLabelValues(skillName).Observe(duration)
}

func RecordAPIRequest(method, endpoint, status string) {
	apiRequests.WithLabelValues(method, endpoint, status).Inc()
}

func RecordAPIRequestDuration(method, endpoint string, duration float64) {
	apiRequestDuration.WithLabelValues(method, endpoint).Observe(duration)
}

func RecordWebSocketConnectionCount(count float64) {
	websocketConnections.Set(count)
}

func RecordSystemError(component, errorType string) {
	systemErrors.WithLabelValues(component, errorType).Inc()
}
