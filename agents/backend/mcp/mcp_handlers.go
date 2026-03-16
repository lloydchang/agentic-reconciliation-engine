package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// WebSocketTransport handles WebSocket-based MCP communication
type WebSocketTransport struct {
	server   *MCPServer
	upgrader websocket.Upgrader
	clients  map[*websocket.Conn]bool
	mu       sync.RWMutex
}

// HTTPTransport handles HTTP-based MCP communication
type HTTPTransport struct {
	server *MCPServer
	mux    *http.ServeMux
}

// startWebSocket starts the WebSocket transport
func (s *MCPServer) startWebSocket(ctx context.Context) error {
	s.logger.Println("Starting MCP server with WebSocket transport")

	transport := &WebSocketTransport{
		server: s,
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins for development
			},
		},
		clients: make(map[*websocket.Conn]bool),
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/mcp", transport.handleWebSocket)

	server := &http.Server{
		Addr:    ":" + s.config.Port,
		Handler: mux,
	}

	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		server.Shutdown(shutdownCtx)
	}()

	s.logger.Printf("WebSocket server listening on port %s", s.config.Port)
	return server.ListenAndServe()
}

// handleWebSocket handles WebSocket connections
func (t *WebSocketTransport) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := t.upgrader.Upgrade(w, r, nil)
	if err != nil {
		t.server.logger.Printf("WebSocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	t.mu.Lock()
	t.clients[conn] = true
	t.mu.Unlock()

	defer func() {
		t.mu.Lock()
		delete(t.clients, conn)
		t.mu.Unlock()
	}()

	t.server.logger.Printf("WebSocket client connected from %s", conn.RemoteAddr())

	// Handle WebSocket messages
	for {
		var message MCPMessage
		if err := conn.ReadJSON(&message); err != nil {
			t.server.logger.Printf("WebSocket read error: %v", err)
			break
		}

		response := t.server.handleMessage(context.Background(), message)
		if err := conn.WriteJSON(response); err != nil {
			t.server.logger.Printf("WebSocket write error: %v", err)
			break
		}
	}
}

// startHTTP starts the HTTP transport
func (s *MCPServer) startHTTP(ctx context.Context) error {
	s.logger.Println("Starting MCP server with HTTP transport")

	transport := &HTTPTransport{
		server: s,
		mux:    http.NewServeMux(),
	}

	// Register HTTP endpoints
	transport.mux.HandleFunc("/mcp", transport.handleHTTPRequest)
	transport.mux.HandleFunc("/mcp/tools", transport.handleToolsListHTTP)
	transport.mux.HandleFunc("/mcp/resources", transport.handleResourcesListHTTP)
	transport.mux.HandleFunc("/mcp/tools/", transport.handleToolCallHTTP)
	transport.mux.HandleFunc("/mcp/resources/", transport.handleResourceReadHTTP)

	server := &http.Server{
		Addr:    ":" + s.config.Port,
		Handler: transport.addCORS(transport.addLogging(transport.mux)),
	}

	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		server.Shutdown(shutdownCtx)
	}()

	s.logger.Printf("HTTP server listening on port %s", s.config.Port)
	return server.ListenAndServe()
}

// handleHTTPRequest handles generic HTTP MCP requests
func (t *HTTPTransport) handleHTTPRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var message MCPMessage
	if err := json.NewDecoder(r.Body).Decode(&message); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	response := t.server.handleMessage(context.Background(), message)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response.WriteTo(w)
}

// handleToolsListHTTP handles HTTP tools list requests
func (t *HTTPTransport) handleToolsListHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	message := MCPMessage{
		JSONRPC: "2.0",
		ID:      "http-tools-list",
		Method:  "tools/list",
	}

	response := t.server.handleMessage(context.Background(), message)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response.WriteTo(w)
}

// handleResourcesListHTTP handles HTTP resources list requests
func (t *HTTPTransport) handleResourcesListHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	message := MCPMessage{
		JSONRPC: "2.0",
		ID:      "http-resources-list",
		Method:  "resources/list",
	}

	response := t.server.handleMessage(context.Background(), message)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response.WriteTo(w)
}

// handleToolCallHTTP handles HTTP tool call requests
func (t *HTTPTransport) handleToolCallHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract tool name from URL path
	toolName := r.URL.Path[len("/mcp/tools/"):]
	if toolName == "" {
		http.Error(w, "Tool name is required", http.StatusBadRequest)
		return
	}

	var params map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&params); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	message := MCPMessage{
		JSONRPC: "2.0",
		ID:      fmt.Sprintf("http-tool-%s", toolName),
		Method:  "tools/call",
		Params: map[string]interface{}{
			"name":      toolName,
			"arguments": params,
		},
	}

	response := t.server.handleMessage(context.Background(), message)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response.WriteTo(w)
}

// handleResourceReadHTTP handles HTTP resource read requests
func (t *HTTPTransport) handleResourceReadHTTP(w http.ResponseWriter, r *http.Request) {
	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract resource URI from URL path
	resourceURI := r.URL.Path[len("/mcp/resources/"):]
	if resourceURI == "" {
		http.Error(w, "Resource URI is required", http.StatusBadRequest)
		return
	}

	// Reconstruct full URI
	fullURI := fmt.Sprintf("%s://%s", r.URL.Query().Get("scheme"), resourceURI)
	if r.URL.Query().Get("scheme") == "" {
		fullURI = resourceURI
	}

	message := MCPMessage{
		JSONRPC: "2.0",
		ID:      fmt.Sprintf("http-resource-%s", resourceURI),
		Method:  "resources/read",
		Params: map[string]interface{}{
			"uri": fullURI,
		},
	}

	response := t.server.handleMessage(context.Background(), message)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	response.WriteTo(w)
}

// addCORS adds CORS middleware
func (t *HTTPTransport) addCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// addLogging adds logging middleware
func (t *HTTPTransport) addLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Create a response logger to capture status code
		rl := &responseLogger{ResponseWriter: w, statusCode: http.StatusOK}
		
		next.ServeHTTP(rl, r)
		
		duration := time.Since(start)
		t.server.logger.Printf("HTTP %s %s - Status: %d - Duration: %v", 
			r.Method, r.URL.Path, rl.statusCode, duration)
	})
}

// responseLogger captures response status code for logging
type responseLogger struct {
	http.ResponseWriter
	statusCode int
}

func (rl *responseLogger) WriteHeader(code int) {
	rl.statusCode = code
	rl.ResponseWriter.WriteHeader(code)
}

// WriteTo writes the MCP message to the HTTP response writer
func (m *MCPMessage) WriteTo(w http.ResponseWriter) error {
	encoder := json.NewEncoder(w)
	return encoder.Encode(m)
}
