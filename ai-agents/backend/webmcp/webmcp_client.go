package webmcp

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// WebMCPClient represents a web-based MCP client
type WebMCPClient struct {
	mcpServer    *mcp.MCPServer
	connections  map[string]*WebSocketConnection
	connectionsMu sync.RWMutex
	upgrader     websocket.Upgrader
	logger       *log.Logger
}

// WebSocketConnection represents a WebSocket connection to a web client
type WebSocketConnection struct {
	conn       *websocket.Conn
	clientID   string
	sessionID  string
	sendChan   chan []byte
	connected  bool
	lastActive time.Time
}

// WebMCPMessage represents messages exchanged with web clients
type WebMCPMessage struct {
	Type      string      `json:"type"`
	SessionID string      `json:"sessionId,omitempty"`
	RequestID string      `json:"requestId,omitempty"`
	Method    string      `json:"method,omitempty"`
	Params    interface{} `json:"params,omitempty"`
	Result    interface{} `json:"result,omitempty"`
	Error     *WebMCPError `json:"error,omitempty"`
}

// WebMCPError represents errors sent to web clients
type WebMCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// NewWebMCPClient creates a new WebMCP client handler
func NewWebMCPClient(mcpServer *mcp.MCPServer) *WebMCPClient {
	return &WebMCPClient{
		mcpServer:   mcpServer,
		connections: make(map[string]*WebSocketConnection),
		upgrader: websocket.Upgrader{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			CheckOrigin: func(r *http.Request) bool {
				// Allow connections from any origin for development
				// In production, implement proper origin checking
				return true
			},
		},
		logger: log.New(log.Writer(), "[WebMCP] ", log.LstdFlags),
	}
}

// HandleWebSocket handles WebSocket connections from web clients
func (w *WebMCPClient) HandleWebSocket(rw http.ResponseWriter, r *http.Request) {
	conn, err := w.upgrader.Upgrade(rw, r, nil)
	if err != nil {
		w.logger.Printf("Failed to upgrade connection: %v", err)
		return
	}

	// Create new connection
	wsConn := &WebSocketConnection{
		conn:       conn,
		clientID:   fmt.Sprintf("web-%d", time.Now().UnixNano()),
		sessionID:  "",
		sendChan:   make(chan []byte, 256),
		connected:  true,
		lastActive: time.Now(),
	}

	// Register connection
	w.connectionsMu.Lock()
	w.connections[wsConn.clientID] = wsConn
	w.connectionsMu.Unlock()

	w.logger.Printf("New WebSocket connection: %s", wsConn.clientID)

	// Start goroutines for this connection
	go w.handleWebSocketReads(wsConn)
	go w.handleWebSocketWrites(wsConn)

	// Send welcome message
	welcomeMsg := WebMCPMessage{
		Type:      "welcome",
		SessionID: wsConn.sessionID,
		Result: map[string]interface{}{
			"clientId":     wsConn.clientID,
			"capabilities": w.getServerCapabilities(),
			"version":      "1.0.0",
		},
	}
	w.sendMessage(wsConn, welcomeMsg)
}

// getServerCapabilities returns the server's MCP capabilities for web clients
func (w *WebMCPClient) getServerCapabilities() map[string]interface{} {
	return map[string]interface{}{
		"tools": map[string]interface{}{
			"listChanged": true,
			"call":        true,
		},
		"resources": map[string]interface{}{
			"listChanged":   true,
			"read":          true,
			"subscribe":     true,
			"unsubscribe":   true,
		},
		"logging": map[string]interface{}{
			"level": "info",
		},
		"experimental": map[string]interface{}{
			"webInterface": true,
		},
	}
}

// handleWebSocketReads handles incoming messages from web clients
func (w *WebMCPClient) handleWebSocketReads(wsConn *WebSocketConnection) {
	defer func() {
		w.connectionsMu.Lock()
		delete(w.connections, wsConn.clientID)
		w.connectionsMu.Unlock()
		wsConn.conn.Close()
		wsConn.connected = false
		close(wsConn.sendChan)
		w.logger.Printf("WebSocket connection closed: %s", wsConn.clientID)
	}()

	wsConn.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	wsConn.conn.SetPongHandler(func(string) error {
		wsConn.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		wsConn.lastActive = time.Now()
		return nil
	})

	for {
		messageType, data, err := wsConn.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				w.logger.Printf("WebSocket error: %v", err)
			}
			break
		}

		if messageType != websocket.TextMessage {
			continue
		}

		var msg WebMCPMessage
		if err := json.Unmarshal(data, &msg); err != nil {
			w.sendError(wsConn, "", &WebMCPError{Code: -32700, Message: "Parse error"})
			continue
		}

		wsConn.lastActive = time.Now()
		w.handleWebMCPMessage(wsConn, &msg)
	}
}

// handleWebSocketWrites handles outgoing messages to web clients
func (w *WebMCPClient) handleWebSocketWrites(wsConn *WebSocketConnection) {
	ticker := time.NewTicker(54 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case message, ok := <-wsConn.sendChan:
			if !ok {
				wsConn.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			wsConn.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := wsConn.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}

		case <-ticker.C:
			wsConn.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := wsConn.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// handleWebMCPMessage processes messages from web clients
func (w *WebMCPClient) handleWebMCPMessage(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	switch msg.Type {
	case "initialize":
		w.handleInitialize(wsConn, msg)
	case "tools/list":
		w.handleToolsList(wsConn, msg)
	case "tools/call":
		w.handleToolsCall(wsConn, msg)
	case "resources/list":
		w.handleResourcesList(wsConn, msg)
	case "resources/read":
		w.handleResourcesRead(wsConn, msg)
	default:
		w.sendError(wsConn, msg.RequestID, &WebMCPError{
			Code:    -32601,
			Message: "Method not found",
		})
	}
}

// handleInitialize handles client initialization
func (w *WebMCPClient) handleInitialize(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	wsConn.sessionID = fmt.Sprintf("session-%d", time.Now().UnixNano())

	response := WebMCPMessage{
		Type:      "response",
		RequestID: msg.RequestID,
		SessionID: wsConn.sessionID,
		Result: map[string]interface{}{
			"protocolVersion": "2024-11-05",
			"capabilities":    w.getServerCapabilities(),
			"serverInfo": map[string]interface{}{
				"name":    "Temporal AI Agents WebMCP",
				"version": "1.0.0",
			},
		},
	}
	w.sendMessage(wsConn, response)
}

// handleToolsList handles listing available tools
func (w *WebMCPClient) handleToolsList(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	tools := w.mcpServer.GetTools()

	toolList := make([]map[string]interface{}, 0, len(tools))
	for _, tool := range tools {
		toolList = append(toolList, map[string]interface{}{
			"name":        tool.Name,
			"description": tool.Description,
			"inputSchema": tool.InputSchema,
		})
	}

	response := WebMCPMessage{
		Type:      "response",
		RequestID: msg.RequestID,
		SessionID: wsConn.sessionID,
		Result: map[string]interface{}{
			"tools": toolList,
		},
	}
	w.sendMessage(wsConn, response)
}

// handleToolsCall handles tool execution requests
func (w *WebMCPClient) handleToolsCall(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	params, ok := msg.Params.(map[string]interface{})
	if !ok {
		w.sendError(wsConn, msg.RequestID, &WebMCPError{
			Code:    -32602,
			Message: "Invalid params",
		})
		return
	}

	toolName, ok := params["name"].(string)
	if !ok {
		w.sendError(wsConn, msg.RequestID, &WebMCPError{
			Code:    -32602,
			Message: "Tool name required",
		})
		return
	}

	toolArgs, _ := params["arguments"].(map[string]interface{})

	// Execute tool asynchronously
	go func() {
		ctx := context.Background()
		var result map[string]interface{}
		var err error
		if tool, exists := w.mcpServer.GetTools()[toolName]; !exists {
			err = fmt.Errorf("tool not found")
		} else {
			result, err = tool.Handler(ctx, toolArgs)
		}

		var response WebMCPMessage
		if err != nil {
			response = WebMCPMessage{
				Type:      "response",
				RequestID: msg.RequestID,
				SessionID: wsConn.sessionID,
				Error: &WebMCPError{
					Code:    -32000,
					Message: err.Error(),
				},
			}
		} else {
			response = WebMCPMessage{
				Type:      "response",
				RequestID: msg.RequestID,
				SessionID: wsConn.sessionID,
				Result:    result,
			}
		}

		w.sendMessage(wsConn, response)
	}()
}

// handleResourcesList handles listing available resources
func (w *WebMCPClient) handleResourcesList(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	resources := w.mcpServer.GetResources()

	resourceList := make([]map[string]interface{}, 0, len(resources))
	for _, resource := range resources {
		resourceList = append(resourceList, map[string]interface{}{
			"name":        resource.Name,
			"description": resource.Description,
			"uri":         resource.URI,
			"mimeType":    resource.MimeType,
		})
	}

	response := WebMCPMessage{
		Type:      "response",
		RequestID: msg.RequestID,
		SessionID: wsConn.sessionID,
		Result: map[string]interface{}{
			"resources": resourceList,
		},
	}
	w.sendMessage(wsConn, response)
}

// handleResourcesRead handles resource read requests
func (w *WebMCPClient) handleResourcesRead(wsConn *WebSocketConnection, msg *WebMCPMessage) {
	params, ok := msg.Params.(map[string]interface{})
	if !ok {
		w.sendError(wsConn, msg.RequestID, &WebMCPError{
			Code:    -32602,
			Message: "Invalid params",
		})
		return
	}

	uri, ok := params["uri"].(string)
	if !ok {
		w.sendError(wsConn, msg.RequestID, &WebMCPError{
			Code:    -32602,
			Message: "URI required",
		})
		return
	}

	// Read resource asynchronously
	go func() {
		ctx := context.Background()
		var content interface{}
		var err error
		if resource, exists := w.mcpServer.GetResources()[uri]; !exists {
			err = fmt.Errorf("resource not found")
		} else {
			content, err = resource.Handler(ctx, uri)
		}

		var response WebMCPMessage
		if err != nil {
			response = WebMCPMessage{
				Type:      "response",
				RequestID: msg.RequestID,
				SessionID: wsConn.sessionID,
				Error: &WebMCPError{
					Code:    -32000,
					Message: err.Error(),
				},
			}
		} else {
			response = WebMCPMessage{
				Type:      "response",
				RequestID: msg.RequestID,
				SessionID: wsConn.sessionID,
				Result: map[string]interface{}{
					"contents": []map[string]interface{}{
						{
							"uri":      uri,
							"mimeType": "application/json",
							"text":     fmt.Sprintf("%v", content),
						},
					},
				},
			}
		}

		w.sendMessage(wsConn, response)
	}()
}

// sendMessage sends a message to a web client
func (w *WebMCPClient) sendMessage(wsConn *WebSocketConnection, msg WebMCPMessage) {
	data, err := json.Marshal(msg)
	if err != nil {
		w.logger.Printf("Failed to marshal message: %v", err)
		return
	}

	select {
	case wsConn.sendChan <- data:
	default:
		w.logger.Printf("Send channel full for client %s", wsConn.clientID)
	}
}

// sendError sends an error message to a web client
func (w *WebMCPClient) sendError(wsConn *WebSocketConnection, requestID string, err *WebMCPError) {
	msg := WebMCPMessage{
		Type:      "response",
		RequestID: requestID,
		SessionID: wsConn.sessionID,
		Error:     err,
	}
	w.sendMessage(wsConn, msg)
}

// GetStats returns connection statistics
func (w *WebMCPClient) GetStats() map[string]interface{} {
	w.connectionsMu.RLock()
	defer w.connectionsMu.RUnlock()

	activeConnections := 0
	for _, conn := range w.connections {
		if conn.connected {
			activeConnections++
		}
	}

	return map[string]interface{}{
		"activeConnections": activeConnections,
		"totalConnections":  len(w.connections),
		"timestamp":         time.Now(),
	}
}
