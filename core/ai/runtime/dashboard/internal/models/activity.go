package models

import (
	"time"
)

type Activity struct {
	ID        string    `json:"id" db:"id"`
	Type      string    `json:"type" db:"type"`      // info, warning, error, success
	AgentID   string    `json:"agent" db:"agent_id"`
	AgentName string    `json:"agentName" db:"agent_name"`
	Message   string    `json:"message" db:"message"`
	Timestamp time.Time `json:"timestamp" db:"timestamp"`
}

type ActivityType string

const (
	ActivityTypeInfo    ActivityType = "info"
	ActivityTypeWarning ActivityType = "warning"
	ActivityTypeError   ActivityType = "error"
	ActivityTypeSuccess ActivityType = "success"
)

type AgentExecution struct {
	ID           string     `json:"id" db:"id"`
	AgentID      string     `json:"agentId" db:"agent_id"`
	SkillName    string     `json:"skillName" db:"skill_name"`
	Status       string     `json:"status" db:"status"`
	StartedAt    time.Time  `json:"startedAt" db:"started_at"`
	CompletedAt  *time.Time `json:"completedAt" db:"completed_at"`
	Result       string     `json:"result" db:"result"`
	ErrorMessage string     `json:"errorMessage" db:"error_message"`
}

type ExecutionStatus string

const (
	ExecutionStatusRunning   ExecutionStatus = "running"
	ExecutionStatusCompleted ExecutionStatus = "completed"
	ExecutionStatusFailed    ExecutionStatus = "failed"
	ExecutionStatusCancelled ExecutionStatus = "cancelled"
)
