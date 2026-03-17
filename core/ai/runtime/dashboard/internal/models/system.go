package models

import "time"

type SystemStatus struct {
	Status      string            `json:"status"`
	Timestamp   time.Time         `json:"timestamp"`
	Version     string            `json:"version"`
	Components  map[string]string `json:"components"`
	Environment string            `json:"environment"`
}

type SystemMetrics struct {
	AgentMetrics    AgentMetrics    `json:"agentMetrics"`
	SkillMetrics    SkillMetrics    `json:"skillMetrics"`
	Performance     Performance     `json:"performance"`
	Timestamp       time.Time       `json:"timestamp"`
}

type AgentMetrics struct {
	Total     int64 `json:"total"`
	Running   int64 `json:"running"`
	Idle      int64 `json:"idle"`
	Errored   int64 `json:"errored"`
	Stopped   int64 `json:"stopped"`
}

type SkillMetrics struct {
	Total          int64 `json:"total"`
	Executions24h  int64 `json:"executions24h"`
	SuccessRate    float64 `json:"successRate"`
	AvgDuration    float64 `json:"avgDuration"` // in seconds
}

type Performance struct {
	CPUUsage    float64 `json:"cpuUsage"`    // percentage
	MemoryUsage float64 `json:"memoryUsage"` // percentage
	DiskUsage   float64 `json:"diskUsage"`   // percentage
	NetworkIO   float64 `json:"networkIO"`   // MB/s
}

type HealthCheck struct {
	Status      string            `json:"status"`
	Timestamp   time.Time         `json:"timestamp"`
	Version     string            `json:"version"`
	Checks      map[string]string `json:"checks"`
}
