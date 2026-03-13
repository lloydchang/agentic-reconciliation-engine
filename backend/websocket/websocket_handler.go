package websocket

import (
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// WebSocketMessage represents a WebSocket message
type WebSocketMessage struct {
	Type      string                 `json:"type"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	ID        string                 `json:"id,omitempty"`
}

// WebSocketClient represents a connected WebSocket client
type WebSocketClient struct {
	ID       string
	Conn     *websocket.Conn
	Send     chan WebSocketMessage
	Hub      *WebSocketHub
	LastSeen time.Time
}

// WebSocketHub manages WebSocket connections
type WebSocketHub struct {
	clients    map[*WebSocketClient]bool
	register   chan *WebSocketClient
	unregister chan *WebSocketClient
	broadcast  chan WebSocketMessage
	mu         sync.RWMutex
}

// WorkflowUpdate represents a workflow status update
type WorkflowUpdate struct {
	WorkflowID string                 `json:"workflowId"`
	WorkflowType string               `json:"workflowType"`
	Status     string                 `json:"status"`
	Progress   float64                `json:"progress"`
	Message    string                 `json:"message"`
	Data       map[string]interface{} `json:"data"`
	Timestamp  time.Time              `json:"timestamp"`
}

// AgentUpdate represents an agent status update
type AgentUpdate struct {
	AgentID    string                 `json:"agentId"`
	AgentType  string                 `json:"agentType"`
	Status     string                 `json:"status"`
	Message    string                 `json:"message"`
	Data       map[string]interface{} `json:"data"`
	Timestamp  time.Time              `json:"timestamp"`
}

// SystemUpdate represents a system status update
type SystemUpdate struct {
	Component  string                 `json:"component"`
	Status     string                 `json:"status"`
	Message    string                 `json:"message"`
	Metrics    map[string]interface{} `json:"metrics"`
	Timestamp  time.Time              `json:"timestamp"`
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for development
	},
}

// NewWebSocketHub creates a new WebSocket hub
func NewWebSocketHub() *WebSocketHub {
	return &WebSocketHub{
		clients:    make(map[*WebSocketClient]bool),
		register:   make(chan *WebSocketClient),
		unregister: make(chan *WebSocketClient),
		broadcast:  make(chan WebSocketMessage),
	}
}

// Run starts the WebSocket hub
func (h *WebSocketHub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client] = true
			h.mu.Unlock()
			log.Printf("WebSocket client connected: %s (total: %d)", client.ID, len(h.clients))

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.Send)
				log.Printf("WebSocket client disconnected: %s (total: %d)", client.ID, len(h.clients))
			}
			h.mu.Unlock()

		case message := <-h.broadcast:
			h.mu.RLock()
			for client := range h.clients {
				select {
				case client.Send <- message:
				default:
					// Client send buffer is full, disconnect
					delete(h.clients, client)
					close(client.Send)
				}
			}
			h.mu.RUnlock()
		}
	}
}

// BroadcastMessage broadcasts a message to all connected clients
func (h *WebSocketHub) BroadcastMessage(messageType string, data map[string]interface{}) {
	message := WebSocketMessage{
		Type:      messageType,
		Data:      data,
		Timestamp: time.Now(),
	}

	select {
	case h.broadcast <- message:
	default:
		// Broadcast channel is full, skip this message
		log.Printf("WebSocket broadcast channel full, skipping message")
	}
}

// BroadcastWorkflowUpdate broadcasts a workflow update
func (h *WebSocketHub) BroadcastWorkflowUpdate(update WorkflowUpdate) {
	h.BroadcastMessage("workflow_update", map[string]interface{}{
		"workflow": update,
	})
}

// BroadcastAgentUpdate broadcasts an agent update
func (h *WebSocketHub) BroadcastAgentUpdate(update AgentUpdate) {
	h.BroadcastMessage("agent_update", map[string]interface{}{
		"agent": update,
	})
}

// BroadcastSystemUpdate broadcasts a system update
func (h *WebSocketHub) BroadcastSystemUpdate(update SystemUpdate) {
	h.BroadcastMessage("system_update", map[string]interface{}{
		"system": update,
	})
}

// GetClientCount returns the number of connected clients
func (h *WebSocketHub) GetClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// WebSocketHandler handles WebSocket connections
type WebSocketHandler struct {
	hub *WebSocketHub
}

// NewWebSocketHandler creates a new WebSocket handler
func NewWebSocketHandler() *WebSocketHandler {
	return &WebSocketHandler{
		hub: NewWebSocketHub(),
	}
}

// GetHub returns the WebSocket hub
func (h *WebSocketHandler) GetHub() *WebSocketHub {
	return h.hub
}

// HandleWebSocket handles WebSocket connections
func (h *WebSocketHandler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	clientID := generateClientID()
	client := &WebSocketClient{
		ID:       clientID,
		Conn:     conn,
		Send:     make(chan WebSocketMessage, 256),
		Hub:      h.hub,
		LastSeen: time.Now(),
	}

	client.Hub.register <- client

	// Start goroutines for reading and writing
	go client.writePump()
	go client.readPump()
}

// writePump handles writing messages to the WebSocket connection
func (c *WebSocketClient) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.Conn.WriteJSON(message); err != nil {
				log.Printf("WebSocket write error: %v", err)
				return
			}

		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// readPump handles reading messages from the WebSocket connection
func (c *WebSocketClient) readPump() {
	defer func() {
		c.Hub.unregister <- c
		c.Conn.Close()
	}()

	c.Conn.SetReadLimit(512)
	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		c.LastSeen = time.Now()
		return nil
	})

	for {
		var message WebSocketMessage
		err := c.Conn.ReadJSON(&message)
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket read error: %v", err)
			}
			break
		}

		c.LastSeen = time.Now()
		c.handleMessage(message)
	}
}

// handleMessage handles incoming WebSocket messages
func (c *WebSocketClient) handleMessage(message WebSocketMessage) {
	switch message.Type {
	case "ping":
		// Respond with pong
		response := WebSocketMessage{
			Type:      "pong",
			Data:      map[string]interface{}{"timestamp": time.Now()},
			Timestamp: time.Now(),
		}
		select {
		case c.Send <- response:
		default:
		}

	case "subscribe":
		// Handle subscription to specific events
		if subscriptions, ok := message.Data["subscriptions"].([]interface{}); ok {
			c.handleSubscriptions(subscriptions)
		}

	case "unsubscribe":
		// Handle unsubscription from specific events
		if subscriptions, ok := message.Data["subscriptions"].([]interface{}); ok {
			c.handleUnsubscriptions(subscriptions)
		}

	default:
		log.Printf("Unknown WebSocket message type: %s", message.Type)
	}
}

// handleSubscriptions handles client subscriptions
func (c *WebSocketClient) handleSubscriptions(subscriptions []interface{}) {
	// In a real implementation, this would track client subscriptions
	log.Printf("Client %s subscribed to: %v", c.ID, subscriptions)
}

// handleUnsubscriptions handles client unsubscriptions
func (c *WebSocketClient) handleUnsubscriptions(subscriptions []interface{}) {
	// In a real implementation, this would remove client subscriptions
	log.Printf("Client %s unsubscribed from: %v", c.ID, subscriptions)
}

// generateClientID generates a unique client ID
func generateClientID() string {
	return fmt.Sprintf("client_%d", time.Now().UnixNano())
}

// WorkflowMonitor monitors workflow status and broadcasts updates
type WorkflowMonitor struct {
	hub *WebSocketHub
}

// NewWorkflowMonitor creates a new workflow monitor
func NewWorkflowMonitor(hub *WebSocketHub) *WorkflowMonitor {
	return &WorkflowMonitor{
		hub: hub,
	}
}

// MonitorWorkflow starts monitoring a workflow
func (m *WorkflowMonitor) MonitorWorkflow(workflowID, workflowType string) {
	go func() {
		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()

		progress := 0.0
		for progress < 100 {
			progress += 10.0

			update := WorkflowUpdate{
				WorkflowID:   workflowID,
				WorkflowType: workflowType,
				Status:        "running",
				Progress:     progress,
				Message:       fmt.Sprintf("Workflow progress: %.1f%%", progress),
				Data: map[string]interface{}{
					"currentStep": int(progress/10),
					"totalSteps":   10,
				},
				Timestamp: time.Now(),
			}

			m.hub.BroadcastWorkflowUpdate(update)
			time.Sleep(1 * time.Second)
		}

		// Send completion update
		update := WorkflowUpdate{
			WorkflowID:   workflowID,
			WorkflowType: workflowType,
			Status:        "completed",
			Progress:     100.0,
			Message:       "Workflow completed successfully",
			Data: map[string]interface{}{
				"completedAt": time.Now(),
			},
			Timestamp: time.Now(),
		}

		m.hub.BroadcastWorkflowUpdate(update)
	}()
}

// AgentMonitor monitors agent status and broadcasts updates
type AgentMonitor struct {
	hub *WebSocketHub
}

// NewAgentMonitor creates a new agent monitor
func NewAgentMonitor(hub *WebSocketHub) *AgentMonitor {
	return &AgentMonitor{
		hub: hub,
	}
}

// MonitorAgent starts monitoring an agent
func (m *AgentMonitor) MonitorAgent(agentID, agentType string) {
	go func() {
		ticker := time.NewTicker(3 * time.Second)
		defer ticker.Stop()

		for i := 0; i < 5; i++ {
			update := AgentUpdate{
				AgentID:   agentID,
				AgentType: agentType,
				Status:    "processing",
				Message:   fmt.Sprintf("Agent processing step %d", i+1),
				Data: map[string]interface{}{
					"currentStep": i + 1,
					"totalSteps":  5,
				},
				Timestamp: time.Now(),
			}

			m.hub.BroadcastAgentUpdate(update)
			time.Sleep(2 * time.Second)
		}

		// Send completion update
		update := AgentUpdate{
			AgentID:   agentID,
			AgentType: agentType,
			Status:    "completed",
			Message:   "Agent completed successfully",
			Data: map[string]interface{}{
				"completedAt": time.Now(),
			},
			Timestamp: time.Now(),
		}

		m.hub.BroadcastAgentUpdate(update)
	}()
}

// SystemMonitor monitors system status and broadcasts updates
type SystemMonitor struct {
	hub *WebSocketHub
}

// NewSystemMonitor creates a new system monitor
func NewSystemMonitor(hub *WebSocketHub) *SystemMonitor {
	return &SystemMonitor{
		hub: hub,
	}
}

// StartMonitoring starts system monitoring
func (m *SystemMonitor) StartMonitoring() {
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		for {
			update := SystemUpdate{
				Component: "system",
				Status:    "healthy",
				Message:  "System operating normally",
				Metrics: map[string]interface{}{
					"cpu":    45.2,
					"memory": 67.8,
					"uptime": time.Since(time.Now().Add(-time.Hour)).String(),
				},
				Timestamp: time.Now(),
			}

			m.hub.BroadcastSystemUpdate(update)
			time.Sleep(30 * time.Second)
		}
	}()
}
