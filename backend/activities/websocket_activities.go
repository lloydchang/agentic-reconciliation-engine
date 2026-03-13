package activities

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/websocket"
)

// WebSocketActivities provides activities for WebSocket integration
type WebSocketActivities struct {
	hub *websocket.WebSocketHub
}

// NewWebSocketActivities creates new WebSocket activities
func NewWebSocketActivities(hub *websocket.WebSocketHub) *WebSocketActivities {
	return &WebSocketActivities{
		hub: hub,
	}
}

// BroadcastWorkflowUpdateActivity broadcasts a workflow update
func (wsa *WebSocketActivities) BroadcastWorkflowUpdateActivity(ctx context.Context, workflowID, workflowType, status string, progress float64, message string, data map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting workflow update", "workflowId", workflowID, "status", status, "progress", progress)

	update := websocket.WorkflowUpdate{
		WorkflowID:   workflowID,
		WorkflowType: workflowType,
		Status:       status,
		Progress:     progress,
		Message:      message,
		Data:         data,
		Timestamp:    time.Now(),
	}

	wsa.hub.BroadcastWorkflowUpdate(update)
	return nil
}

// BroadcastAgentUpdateActivity broadcasts an agent update
func (wsa *WebSocketActivities) BroadcastAgentUpdateActivity(ctx context.Context, agentID, agentType, status string, message string, data map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting agent update", "agentId", agentID, "status", status)

	update := websocket.AgentUpdate{
		AgentID:   agentID,
		AgentType: agentType,
		Status:    status,
		Message:   message,
		Data:      data,
		Timestamp: time.Now(),
	}

	wsa.hub.BroadcastAgentUpdate(update)
	return nil
}

// BroadcastSystemUpdateActivity broadcasts a system update
func (wsa *WebSocketActivities) BroadcastSystemUpdateActivity(ctx context.Context, component, status, message string, metrics map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting system update", "component", component, "status", status)

	update := websocket.SystemUpdate{
		Component: component,
		Status:    status,
		Message:   message,
		Metrics:   metrics,
		Timestamp: time.Now(),
	}

	wsa.hub.BroadcastSystemUpdate(update)
	return nil
}

// StartWorkflowMonitoringActivity starts monitoring a workflow
func (wsa *WebSocketActivities) StartWorkflowMonitoringActivity(ctx context.Context, workflowID, workflowType string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Starting workflow monitoring", "workflowId", workflowID, "type", workflowType)

	monitor := websocket.NewWorkflowMonitor(wsa.hub)
	monitor.MonitorWorkflow(workflowID, workflowType)

	return nil
}

// StartAgentMonitoringActivity starts monitoring an agent
func (wsa *WebSocketActivities) StartAgentMonitoringActivity(ctx context.Context, agentID, agentType string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Starting agent monitoring", "agentId", agentID, "type", agentType)

	monitor := websocket.NewAgentMonitor(wsa.hub)
	monitor.MonitorAgent(agentID, agentType)

	return nil
}

// StartSystemMonitoringActivity starts system monitoring
func (wsa *WebSocketActivities) StartSystemMonitoringActivity(ctx context.Context) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Starting system monitoring")

	monitor := websocket.NewSystemMonitor(wsa.hub)
	monitor.StartMonitoring()

	return nil
}

// GetConnectedClientsActivity returns the number of connected clients
func (wsa *WebSocketActivities) GetConnectedClientsActivity(ctx context.Context) (int, error) {
	logger := activity.GetLogger(ctx)
	
	clientCount := wsa.hub.GetClientCount()
	logger.Info("Retrieved connected clients count", "count", clientCount)

	return clientCount, nil
}

// BroadcastCustomMessageActivity broadcasts a custom message
func (wsa *WebSocketActivities) BroadcastCustomMessageActivity(ctx context.Context, messageType string, data map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting custom message", "type", messageType)

	wsa.hub.BroadcastMessage(messageType, data)
	return nil
}

// SendProgressUpdateActivity sends a series of progress updates
func (wsa *WebSocketActivities) SendProgressUpdateActivity(ctx context.Context, workflowID, workflowType string, steps []string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Sending progress updates", "workflowId", workflowID, "steps", len(steps))

	totalSteps := len(steps)
	for i, step := range steps {
		progress := float64(i+1) / float64(totalSteps) * 100

		update := websocket.WorkflowUpdate{
			WorkflowID:   workflowID,
			WorkflowType: workflowType,
			Status:       "running",
			Progress:     progress,
			Message:      fmt.Sprintf("Step %d/%d: %s", i+1, totalSteps, step),
			Data: map[string]interface{}{
				"currentStep": i + 1,
				"totalSteps":  totalSteps,
				"stepName":   step,
			},
			Timestamp: time.Now(),
		}

		wsa.hub.BroadcastWorkflowUpdate(update)

		// Add delay between updates
		time.Sleep(500 * time.Millisecond)
	}

	// Send completion update
	update := websocket.WorkflowUpdate{
		WorkflowID:   workflowID,
		WorkflowType: workflowType,
		Status:       "completed",
		Progress:     100.0,
		Message:      "All steps completed successfully",
		Data: map[string]interface{}{
			"completedAt": time.Now(),
		},
		Timestamp: time.Now(),
	}

	wsa.hub.BroadcastWorkflowUpdate(update)
	return nil
}

// SendAgentLifecycleActivity sends agent lifecycle updates
func (wsa *WebSocketActivities) SendAgentLifecycleActivity(ctx context.Context, agentID, agentType string, lifecycleSteps []string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Sending agent lifecycle updates", "agentId", agentID, "steps", len(lifecycleSteps))

	for i, step := range lifecycleSteps {
		update := websocket.AgentUpdate{
			AgentID:   agentID,
			AgentType: agentType,
			Status:    "active",
			Message:   fmt.Sprintf("Agent lifecycle: %s", step),
			Data: map[string]interface{}{
				"lifecycleStep": i + 1,
				"totalSteps":    len(lifecycleSteps),
				"stepName":      step,
			},
			Timestamp: time.Now(),
		}

		wsa.hub.BroadcastAgentUpdate(update)

		// Add delay between updates
		time.Sleep(1 * time.Second)
	}

	// Send completion update
	update := websocket.AgentUpdate{
		AgentID:   agentID,
		AgentType: agentType,
		Status:    "completed",
		Message:   "Agent lifecycle completed",
		Data: map[string]interface{}{
			"completedAt": time.Now(),
		},
		Timestamp: time.Now(),
	}

	wsa.hub.BroadcastAgentUpdate(update)
	return nil
}

// BroadcastErrorActivity broadcasts an error message
func (wsa *WebSocketActivities) BroadcastErrorActivity(ctx context.Context, component, errorType, message string, details map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting error message", "component", component, "type", errorType)

	errorData := map[string]interface{}{
		"component": component,
		"type":      errorType,
		"message":   message,
		"details":   details,
		"timestamp": time.Now(),
	}

	wsa.hub.BroadcastMessage("error", errorData)
	return nil
}

// BroadcastMetricsActivity broadcasts system metrics
func (wsa *WebSocketActivities) BroadcastMetricsActivity(ctx context.Context, metrics map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Broadcasting system metrics")

	update := websocket.SystemUpdate{
		Component: "metrics",
		Status:    "healthy",
		Message:   "System metrics update",
		Metrics:   metrics,
		Timestamp: time.Now(),
	}

	wsa.hub.BroadcastSystemUpdate(update)
	return nil
}

// ValidateWebSocketConnectionActivity validates WebSocket connectivity
func (wsa *WebSocketActivities) ValidateWebSocketConnectionActivity(ctx context.Context) (bool, error) {
	logger := activity.GetLogger(ctx)

	clientCount := wsa.hub.GetClientCount()
	isConnected := clientCount > 0

	logger.Info("WebSocket connection validation", "connected", isConnected, "clients", clientCount)

	// Broadcast a test message to validate connectivity
	if isConnected {
		testData := map[string]interface{}{
			"test":      true,
			"timestamp": time.Now(),
			"clients":   clientCount,
		}

		wsa.hub.BroadcastMessage("connection_test", testData)
	}

	return isConnected, nil
}

// CreateNotificationActivity creates and broadcasts a notification
func (wsa *WebSocketActivities) CreateNotificationActivity(ctx context.Context, notificationType, title, message string, data map[string]interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Creating notification", "type", notificationType, "title", title)

	notificationData := map[string]interface{}{
		"type":      notificationType,
		"title":     title,
		"message":   message,
		"data":      data,
		"timestamp": time.Now(),
	}

	wsa.hub.BroadcastMessage("notification", notificationData)
	return nil
}

// SendHeartbeatActivity sends a heartbeat message
func (wsa *WebSocketActivities) SendHeartbeatActivity(ctx context.Context) error {
	_ = activity.GetLogger(ctx)

	heartbeatData := map[string]interface{}{
		"status":    "alive",
		"timestamp": time.Now(),
		"clients":   wsa.hub.GetClientCount(),
	}

	wsa.hub.BroadcastMessage("heartbeat", heartbeatData)
	return nil
}
