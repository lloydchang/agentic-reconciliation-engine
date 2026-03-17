package models

import "time"

// EvaluationHealth represents agent health evaluation results
type EvaluationHealth struct {
	WorkerHealth       map[string]interface{} `json:"worker_health"`
	ConversationHealth map[string]interface{} `json:"conversation_health"`
	OverallHealth      string                 `json:"overall_health_status"`
	Recommendations    []string               `json:"recommendations"`
	Timestamp          time.Time              `json:"timestamp"`
}

// EvaluationMonitoring represents monitoring evaluation results
type EvaluationMonitoring struct {
	InfrastructureHealth map[string]interface{} `json:"infrastructure_health"`
	TemporalHealth       map[string]interface{} `json:"temporal_health"`
	AgentHealth          map[string]interface{} `json:"agent_health"`
	CorrelationID        string                 `json:"correlation_id"`
	TotalIssues          int                    `json:"total_issues"`
	Timestamp            time.Time              `json:"timestamp"`
}

// EvaluationIssue represents a detected issue
type EvaluationIssue struct {
	ID          string    `json:"id"`
	Type        string    `json:"type"`
	Severity    string    `json:"severity"`
	Description string    `json:"description"`
	Timestamp   time.Time `json:"timestamp"`
	Target      string    `json:"target,omitempty"`
	Metrics     map[string]interface{} `json:"metrics,omitempty"`
}

// AutoFixStatus represents auto-fix status and history
type AutoFixStatus struct {
	TotalFixes      int                    `json:"total_fixes"`
	FixHistory      []AutoFixAttempt       `json:"fix_history"`
	BackoffPeriods  map[string]interface{} `json:"backoff_periods"`
	Timestamp       time.Time              `json:"timestamp"`
}

// AutoFixAttempt represents an auto-fix attempt
type AutoFixAttempt struct {
	Timestamp     time.Time `json:"timestamp"`
	Action        string    `json:"action"`
	Target        string    `json:"target"`
	Success       bool      `json:"success"`
	ErrorMessage  string    `json:"error_message,omitempty"`
}

// EvaluationSummary represents comprehensive evaluation summary
type EvaluationSummary struct {
	Summary          map[string]interface{} `json:"summary"`
	EvaluatorResults map[string]interface{} `json:"evaluator_results"`
	TraceCount       int                    `json:"trace_count"`
	EvaluatorsRun    []string               `json:"evaluators_run"`
	Timestamp        time.Time              `json:"timestamp"`
}
