package shared

import (
	"context"
	"time"
)

// TriggerEvent represents a unified event from any platform
type TriggerEvent struct {
	ID          string                 `json:"id"`
	Platform    string                 `json:"platform"`    // "github", "linear", "slack"
	Type        string                 `json:"type"`        // "issue", "pr", "comment", "command"
	Action      string                 `json:"action"`      // "created", "updated", "comment", "approve"
	UserID      string                 `json:"user_id"`
	UserEmail   string                 `json:"user_email"`
	Repository  RepoMapping            `json:"repository"`
	Timestamp   time.Time              `json:"timestamp"`
	Data        map[string]interface{} `json:"data"`
	CorrelationID string               `json:"correlation_id,omitempty"`
}

// RepoMapping defines how platforms map to GitHub repositories
type RepoMapping struct {
	Owner    string `json:"owner"`
	Name     string `json:"name"`
	Token    string `json:"token"`
	BasePath string `json:"base_path"`
}

// TriggerDispatcher handles routing events to appropriate handlers
type TriggerDispatcher interface {
	Dispatch(ctx context.Context, event TriggerEvent) error
	RegisterHandler(platform, eventType string, handler TriggerHandler) error
}

// TriggerHandler processes events for specific platforms/types
type TriggerHandler interface {
	HandleEvent(ctx context.Context, event TriggerEvent) error
}

// ToolResult represents the result of a tool execution
type ToolResult struct {
	Success bool                   `json:"success"`
	Message string                 `json:"message"`
	Data    map[string]interface{} `json:"data,omitempty"`
	Error   string                 `json:"error,omitempty"`
}

// WorkflowContext provides context for workflow execution
type WorkflowContext struct {
	WorkflowID   string                 `json:"workflow_id"`
	Platform     string                 `json:"platform"`
	UserID       string                 `json:"user_id"`
	Repository   RepoMapping            `json:"repository"`
	StartTime    time.Time              `json:"start_time"`
	Status       string                 `json:"status"`
	Metadata     map[string]interface{} `json:"metadata"`
	CorrelationID string                `json:"correlation_id"`
}

// ApprovalRequest represents a request requiring human approval
type ApprovalRequest struct {
	ID          string      `json:"id"`
	WorkflowID  string      `json:"workflow_id"`
	Type        string      `json:"type"`
	Description string      `json:"description"`
	RiskLevel   string      `json:"risk_level"`
	Requester   string      `json:"requester"`
	Timestamp   time.Time   `json:"timestamp"`
	Deadline    *time.Time  `json:"deadline,omitempty"`
	Data        map[string]interface{} `json:"data"`
}
