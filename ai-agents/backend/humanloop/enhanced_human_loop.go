package humanloop

import (
	"context"
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// EnhancedHumanInTheLoopWorkflow provides sophisticated human-in-the-loop capabilities
func EnhancedHumanInTheLoopWorkflow(ctx workflow.Context, task types.HumanTask) (*types.HumanTaskResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Enhanced Human-in-the-Loop Workflow", "task", task)

	// Set up enhanced query handlers for real-time status updates
	err := workflow.SetQueryHandler(ctx, "taskStatus", func() (types.HumanTaskStatus, error) {
		return task.Status, nil
	})
	if err != nil {
		return nil, fmt.Errorf("failed to set query handler: %w", err)
	}

	// Set up query handler for task details
	err = workflow.SetQueryHandler(ctx, "taskDetails", func() (types.HumanTask, error) {
		return task, nil
	})
	if err != nil {
		return nil, fmt.Errorf("failed to set task details handler: %w", err)
	}

	// Initialize human interaction manager
	him := NewHumanInteractionManager(task)

	// Phase 1: Intelligent task routing and notification
	err = workflow.ExecuteActivity(ctx, RouteTaskActivity, task).Get(ctx, &task)
	if err != nil {
		logger.Warn("Task routing failed, proceeding with original assignment", "error", err)
	}

	// Phase 2: Enhanced waiting with multiple interaction channels
	result, err := him.WaitForHumanInteraction(ctx)
	if err != nil {
		return nil, fmt.Errorf("human interaction failed: %w", err)
	}

	// Phase 3: Post-interaction processing and audit
	err = workflow.ExecuteActivity(ctx, ProcessHumanDecisionActivity, result).Get(ctx, &result)
	if err != nil {
		logger.Warn("Post-processing failed, but continuing with result", "error", err)
	}

	logger.Info("Enhanced Human-in-the-Loop Workflow completed", "approved", result.Approved)
	return result, nil
}

// HumanInteractionManager manages complex human interactions
type HumanInteractionManager struct {
	task            types.HumanTask
	notificationChannels []string
	escalationPolicy   EscalationPolicy
	timeoutManager     *TimeoutManager
	interactionLog     []InteractionEvent
}

// InteractionEvent represents a human interaction event
type InteractionEvent struct {
	Timestamp   time.Time              `json:"timestamp"`
	Type        string                 `json:"type"`
	Actor       string                 `json:"actor"`
	Action      string                 `json:"action"`
	Details     map[string]interface{} `json:"details"`
}

// EscalationPolicy defines when and how to escalate tasks
type EscalationPolicy struct {
	Levels         []EscalationLevel    `json:"levels"`
	MaxEscalations int                  `json:"maxEscalations"`
	TimeBased      bool                 `json:"timeBased"`
	ConditionBased bool                 `json:"conditionBased"`
}

// EscalationLevel defines an escalation level
type EscalationLevel struct {
	Level       int           `json:"level"`
	Timeout     time.Duration `json:"timeout"`
	Assignees   []string      `json:"assignees"`
	Channels    []string      `json:"channels"`
	Priority    string        `json:"priority"`
}

// TimeoutManager manages various timeout scenarios
type TimeoutManager struct {
	baseTimeout    time.Duration
	escalationTimeouts []time.Duration
	reminderIntervals []time.Duration
	lastReminder   time.Time
	escalationCount int
}

// NewHumanInteractionManager creates a new human interaction manager
func NewHumanInteractionManager(task types.HumanTask) *HumanInteractionManager {
	return &HumanInteractionManager{
		task: task,
		notificationChannels: []string{"email", "slack", "ui"},
		escalationPolicy: EscalationPolicy{
			Levels: []EscalationLevel{
				{
					Level:     1,
					Timeout:   time.Hour * 4,
					Assignees: []string{"team-lead"},
					Channels:  []string{"email", "slack", "sms"},
					Priority:  "high",
				},
				{
					Level:     2,
					Timeout:   time.Hour * 24,
					Assignees: []string{"manager", "compliance-officer"},
					Channels:  []string{"email", "slack", "sms", "phone"},
					Priority:  "critical",
				},
			},
			MaxEscalations: 2,
			TimeBased:      true,
			ConditionBased: false,
		},
		timeoutManager: NewTimeoutManager(time.Hour * 24),
		interactionLog: make([]InteractionEvent, 0),
	}
}

// NewTimeoutManager creates a new timeout manager
func NewTimeoutManager(baseTimeout time.Duration) *TimeoutManager {
	return &TimeoutManager{
		baseTimeout: baseTimeout,
		escalationTimeouts: []time.Duration{
			time.Hour * 4,
			time.Hour * 24,
		},
		reminderIntervals: []time.Duration{
			time.Hour * 1,
			time.Hour * 4,
			time.Hour * 12,
		},
		escalationCount: 0,
	}
}

// WaitForHumanInteraction waits for human interaction with enhanced handling
func (him *HumanInteractionManager) WaitForHumanInteraction(ctx workflow.Context) (*types.HumanTaskResult, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Waiting for human interaction", "taskId", him.task.ID)

	// Set up multiple signal channels for different interaction types
	approvalCh := workflow.GetSignalChannel(ctx, "humanApproval")
	rejectionCh := workflow.GetSignalChannel(ctx, "humanRejection")
	commentCh := workflow.GetSignalChannel(ctx, "humanComment")
	escalationCh := workflow.GetSignalChannel(ctx, "requestEscalation")

	// Record interaction start
	him.recordInteraction("interaction_started", "system", "start", nil)

	// Set up selector for handling multiple signals
	selector := workflow.NewSelector(ctx)

	var result *types.HumanTaskResult
	var completed bool

	// Handle approval signal
	selector.AddReceive(approvalCh, func(c workflow.ReceiveChannel, more bool) {
		ch := c.(workflow.Channel)
		var approval HumanApproval
		ch.Receive(ctx, &approval)

		him.recordInteraction("approval_received", approval.UserID, "approve", map[string]interface{}{
			"comments": approval.Comments,
			"priority": approval.Priority,
		})

		result = &types.HumanTaskResult{
			TaskID:    him.task.ID,
			Approved:  true,
			Decision:  fmt.Sprintf("Approved by %s: %s", approval.UserID, approval.Comments),
			CompletedAt: workflow.Now(ctx),
		}
		completed = true
	})

	// Handle rejection signal
	selector.AddReceive(rejectionCh, func(c workflow.ReceiveChannel, more bool) {
		ch := c.(workflow.Channel)
		var rejection HumanRejection
		ch.Receive(ctx, &rejection)

		him.recordInteraction("rejection_received", rejection.UserID, "reject", map[string]interface{}{
			"reason":   rejection.Reason,
			"comments": rejection.Comments,
		})

		result = &types.HumanTaskResult{
			TaskID:    him.task.ID,
			Approved:  false,
			Decision:  fmt.Sprintf("Rejected by %s: %s - %s", rejection.UserID, rejection.Reason, rejection.Comments),
			CompletedAt: workflow.Now(ctx),
		}
		completed = true
	})

	// Handle comment signal (non-decision)
	selector.AddReceive(commentCh, func(c workflow.ReceiveChannel, more bool) {
		ch := c.(workflow.Channel)
		var comment HumanComment
		ch.Receive(ctx, &comment)

		him.recordInteraction("comment_received", comment.UserID, "comment", map[string]interface{}{
			"comment": comment.Text,
		})

		// Comments don't complete the task, just log and continue waiting
		logger.Info("Comment received", "user", comment.UserID, "comment", comment.Text)
	})

	// Handle escalation request
	selector.AddReceive(escalationCh, func(c workflow.ReceiveChannel, more bool) {
		ch := c.(workflow.Channel)
		var escalation EscalationRequest
		ch.Receive(ctx, &escalation)

		him.recordInteraction("escalation_requested", escalation.UserID, "escalate", map[string]interface{}{
			"reason": escalation.Reason,
		})

		// Process escalation
		err := him.processEscalation(ctx, escalation)
		if err != nil {
			logger.Warn("Escalation processing failed", "error", err)
		}
	})

	// Set up timeout handling with escalation
	timeoutCh := workflow.NewTimer(ctx, him.timeoutManager.baseTimeout)
	selector.AddFuture(timeoutCh, func(f workflow.Future) {
		logger.Warn("Task timed out, escalating", "taskId", him.task.ID)

		him.recordInteraction("timeout_occurred", "system", "timeout", nil)

		// Attempt escalation
		err := him.escalateTask(ctx)
		if err != nil {
			logger.Error("Escalation failed", "error", err)
			// Auto-reject on escalation failure
			result = &types.HumanTaskResult{
				TaskID:    him.task.ID,
				Approved:  false,
				Decision:  "Auto-rejected due to timeout and escalation failure",
				CompletedAt: workflow.Now(ctx),
			}
			completed = true
		} else {
			// Continue waiting after escalation
			logger.Info("Escalation successful, continuing to wait")
		}
	})

	// Main interaction loop
	for !completed {
		selector.Select(ctx)

		// Check if we need to send reminders
		if him.shouldSendReminder() {
			err := him.sendReminder(ctx)
			if err != nil {
				logger.Warn("Failed to send reminder", "error", err)
			}
		}
	}

	him.recordInteraction("interaction_completed", "system", "complete", map[string]interface{}{
		"approved": result.Approved,
		"decision": result.Decision,
	})

	return result, nil
}

// processEscalation processes an escalation request
func (him *HumanInteractionManager) processEscalation(ctx workflow.Context, request EscalationRequest) error {
	logger := workflow.GetLogger(ctx)

	if him.timeoutManager.escalationCount >= len(him.escalationPolicy.Levels) {
		return fmt.Errorf("maximum escalation levels reached")
	}

	level := him.escalationPolicy.Levels[him.timeoutManager.escalationCount]

	// Update task assignment
	him.task.AssignedTo = level.Assignees[0] // Assign to first person in level
	him.task.Priority = level.Priority

	// Send notifications via all channels for this level
	for _, channel := range level.Channels {
		err := workflow.ExecuteActivity(ctx, SendNotificationActivity, NotificationRequest{
			TaskID:   him.task.ID,
			Channel:  channel,
			Assignee: him.task.AssignedTo,
			Message:  fmt.Sprintf("ESCALATION: %s requires immediate attention", him.task.Title),
			Priority: level.Priority,
		}).Get(ctx, nil)

		if err != nil {
			logger.Warn("Failed to send escalation notification", "channel", channel, "error", err)
		}
	}

	him.timeoutManager.escalationCount++
	return nil
}

// escalateTask performs automatic escalation based on timeout
func (him *HumanInteractionManager) escalateTask(ctx workflow.Context) error {
	return him.processEscalation(ctx, EscalationRequest{
		UserID: "system",
		Reason: "Timeout exceeded",
	})
}

// shouldSendReminder determines if a reminder should be sent
func (him *HumanInteractionManager) shouldSendReminder() bool {
	if len(him.timeoutManager.reminderIntervals) == 0 {
		return false
	}

	now := time.Now()
	elapsed := now.Sub(him.task.DueAt)

	for _, interval := range him.timeoutManager.reminderIntervals {
		if elapsed >= interval && (him.timeoutManager.lastReminder.IsZero() || now.Sub(him.timeoutManager.lastReminder) >= interval) {
			return true
		}
	}

	return false
}

// sendReminder sends a reminder notification
func (him *HumanInteractionManager) sendReminder(ctx workflow.Context) error {
	him.timeoutManager.lastReminder = time.Now()

	return workflow.ExecuteActivity(ctx, SendNotificationActivity, NotificationRequest{
		TaskID:   him.task.ID,
		Channel:  "slack", // Primary reminder channel
		Assignee: him.task.AssignedTo,
		Message:  fmt.Sprintf("REMINDER: %s is still pending review", him.task.Title),
		Priority: him.task.Priority,
	}).Get(ctx, nil)
}

// recordInteraction records an interaction event
func (him *HumanInteractionManager) recordInteraction(eventType, actor, action string, details map[string]interface{}) {
	event := InteractionEvent{
		Timestamp: time.Now(),
		Type:      eventType,
		Actor:     actor,
		Action:    action,
		Details:   details,
	}

	him.interactionLog = append(him.interactionLog, event)
}

// Data structures for human interactions

type HumanApproval struct {
	UserID   string `json:"userId"`
	Comments string `json:"comments"`
	Priority string `json:"priority"`
}

type HumanRejection struct {
	UserID   string `json:"userId"`
	Reason   string `json:"reason"`
	Comments string `json:"comments"`
}

type HumanComment struct {
	UserID string `json:"userId"`
	Text   string `json:"text"`
}

type EscalationRequest struct {
	UserID string `json:"userId"`
	Reason string `json:"reason"`
}

type NotificationRequest struct {
	TaskID   string `json:"taskId"`
	Channel  string `json:"channel"`
	Assignee string `json:"assignee"`
	Message  string `json:"message"`
	Priority string `json:"priority"`
}

// Activity functions for human interaction management

// RouteTaskActivity routes tasks to appropriate reviewers
func RouteTaskActivity(ctx context.Context, task types.HumanTask) (types.HumanTask, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Routing task to appropriate reviewer", "taskId", task.ID)

	// Intelligent routing logic based on task content and priority
	if task.Priority == "critical" {
		// Route to senior reviewers for critical tasks
		task.AssignedTo = "senior-reviewer"
	} else if task.Data != nil {
		// Route based on task data content
		if containsKeyword(task.Data, "security") {
			task.AssignedTo = "security-team"
		} else if containsKeyword(task.Data, "compliance") {
			task.AssignedTo = "compliance-officer"
		}
	}

	logger.Info("Task routed", "assignedTo", task.AssignedTo)
	return task, nil
}

// SendNotificationActivity sends notifications via various channels
func SendNotificationActivity(ctx context.Context, request NotificationRequest) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Sending notification", "channel", request.Channel, "assignee", request.Assignee)

	// Simulate sending notification
	// In real implementation, this would integrate with email, Slack, SMS, etc.
	switch request.Channel {
	case "email":
		// Send email notification
		logger.Info("Email notification sent", "to", request.Assignee, "message", request.Message)
	case "slack":
		// Send Slack notification
		logger.Info("Slack notification sent", "to", request.Assignee, "message", request.Message)
	case "sms":
		// Send SMS notification
		logger.Info("SMS notification sent", "to", request.Assignee, "message", request.Message)
	default:
		logger.Warn("Unknown notification channel", "channel", request.Channel)
	}

	return nil
}

// ProcessHumanDecisionActivity processes and validates human decisions
func ProcessHumanDecisionActivity(ctx context.Context, result types.HumanTaskResult) (types.HumanTaskResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Processing human decision", "taskId", result.TaskID, "approved", result.Approved)

	// Validate decision
	if result.Decision == "" {
		return result, fmt.Errorf("decision cannot be empty")
	}

	// Add audit trail
	result.Metadata = map[string]interface{}{
		"processedAt": time.Now(),
		"validated":   true,
		"auditTrail":  fmt.Sprintf("Decision processed and validated at %s", time.Now().Format(time.RFC3339)),
	}

	// Log decision for compliance
	logger.Info("Human decision processed and logged", "decision", result.Decision)

	return result, nil
}

// Helper functions

func containsKeyword(data map[string]interface{}, keyword string) bool {
	// Simple keyword search in task data
	for _, value := range data {
		if str, ok := value.(string); ok {
			if strings.Contains(strings.ToLower(str), strings.ToLower(keyword)) {
				return true
			}
		}
	}
	return false
}
