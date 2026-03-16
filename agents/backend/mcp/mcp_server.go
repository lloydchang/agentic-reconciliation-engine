package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"sync"

	"go.temporal.io/sdk/client"
)

// MCPServer represents the MCP server implementation
type MCPServer struct {
	temporalClient client.Client
	config         *MCPConfig
	logger         *log.Logger
	tools          map[string]*MCPTool
	resources      map[string]*MCPResource
	mu             sync.RWMutex
}

// MCPConfig holds MCP server configuration
type MCPConfig struct {
	ServerName        string   `json:"serverName"`
	ServerVersion     string   `json:"serverVersion"`
	TransportType     string   `json:"transportType"` // "stdio", "websocket", "http"
	Port              string   `json:"port,omitempty"`
	EnableAuth        bool     `json:"enableAuth"`
	APIKey            string   `json:"apiKey,omitempty"`
	AllowedTools      []string `json:"allowedTools"`
	AllowedResources  []string `json:"allowedResources"`
	LogLevel          string   `json:"logLevel"`
}



// MCPResource represents a resource that can be accessed by MCP clients
type MCPResource struct {
	Name         string `json:"name"`
	Description  string `json:"description"`
	URI          string `json:"uri"`
	MimeType     string `json:"mimeType"`
	Handler      MCPResourceHandler `json:"-"`
}

// MCPToolHandler defines the function signature for tool handlers
type MCPToolHandler func(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error)

// MCPResourceHandler defines the function signature for resource handlers
type MCPResourceHandler func(ctx context.Context, uri string) (interface{}, error)

// MCPMessage represents a JSON-RPC message
type MCPMessage struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      interface{} `json:"id,omitempty"`
	Method  string      `json:"method,omitempty"`
	Params  interface{} `json:"params,omitempty"`
	Result  interface{} `json:"result,omitempty"`
	Error   *MCPError   `json:"error,omitempty"`
}

// MCPError represents an MCP error response
type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// MCPInitializeParams represents initialization parameters
type MCPInitializeParams struct {
	ProtocolVersion string                 `json:"protocolVersion"`
	Capabilities    map[string]interface{} `json:"capabilities"`
	ClientInfo      MCPClientInfo           `json:"clientInfo"`
}

// MCPClientInfo represents client information
type MCPClientInfo struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

// MCPInitializeResult represents initialization result
type MCPInitializeResult struct {
	ProtocolVersion string                 `json:"protocolVersion"`
	Capabilities    map[string]interface{} `json:"capabilities"`
	ServerInfo      MCPServerInfo           `json:"serverInfo"`
}

// MCPServerInfo represents server information
type MCPServerInfo struct {
	Name    string `json:"name"`
	Version string `json:"version"`
}

// NewMCPServer creates a new MCP server instance
func NewMCPServer(temporalClient client.Client, config *MCPConfig) *MCPServer {
	server := &MCPServer{
		temporalClient: temporalClient,
		config:         config,
		logger:         log.New(os.Stderr, "[MCP] ", log.LstdFlags),
		tools:          make(map[string]*MCPTool),
		resources:      make(map[string]*MCPResource),
	}

	// Register default tools and resources
	server.registerDefaultTools()
	server.registerDefaultResources()

	return server
}

// Start starts the MCP server
func (s *MCPServer) Start(ctx context.Context) error {
	s.logger.Printf("Starting MCP server: %s v%s", s.config.ServerName, s.config.ServerVersion)

	switch s.config.TransportType {
	case "stdio":
		return s.startStdIO(ctx)
	case "websocket":
		return s.startWebSocket(ctx)
	case "http":
		return s.startHTTP(ctx)
	default:
		return fmt.Errorf("unsupported transport type: %s", s.config.TransportType)
	}
}

// Stop stops the MCP server
func (s *MCPServer) Stop() error {
	s.logger.Println("Stopping MCP server")
	return nil
}

// RegisterTool registers a new tool
func (s *MCPServer) RegisterTool(tool *MCPTool) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.tools[tool.Name]; exists {
		return fmt.Errorf("tool %s already registered", tool.Name)
	}

	s.tools[tool.Name] = tool
	s.logger.Printf("Registered tool: %s", tool.Name)
	return nil
}

// RegisterResource registers a new resource
func (s *MCPServer) RegisterResource(resource *MCPResource) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, exists := s.resources[resource.Name]; exists {
		return fmt.Errorf("resource %s already registered", resource.Name)
	}

	s.resources[resource.Name] = resource
	s.logger.Printf("Registered resource: %s", resource.Name)
	return nil
}

// GetTools returns all available tools
func (s *MCPServer) GetTools() map[string]*MCPTool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	tools := make(map[string]*MCPTool)
	for name, tool := range s.tools {
		if s.isToolAllowed(name) {
			tools[name] = tool
		}
	}
	return tools
}

// GetResources returns all available resources
func (s *MCPServer) GetResources() map[string]*MCPResource {
	s.mu.RLock()
	defer s.mu.RUnlock()

	resources := make(map[string]*MCPResource)
	for name, resource := range s.resources {
		if s.isResourceAllowed(name) {
			resources[name] = resource
		}
	}
	return resources
}

// isToolAllowed checks if a tool is allowed based on configuration
func (s *MCPServer) isToolAllowed(toolName string) bool {
	if len(s.config.AllowedTools) == 0 {
		return true // No restrictions
	}

	for _, allowed := range s.config.AllowedTools {
		if allowed == toolName {
			return true
		}
	}
	return false
}

// isResourceAllowed checks if a resource is allowed based on configuration
func (s *MCPServer) isResourceAllowed(resourceName string) bool {
	if len(s.config.AllowedResources) == 0 {
		return true // No restrictions
	}

	for _, allowed := range s.config.AllowedResources {
		if allowed == resourceName {
			return true
		}
	}
	return false
}

// startStdIO starts the MCP server with stdio transport
func (s *MCPServer) startStdIO(ctx context.Context) error {
	s.logger.Println("Starting MCP server with stdio transport")

	decoder := json.NewDecoder(os.Stdin)
	encoder := json.NewEncoder(os.Stdout)

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			var message MCPMessage
			if err := decoder.Decode(&message); err != nil {
				if err == io.EOF {
					s.logger.Println("Client disconnected")
					return nil
				}
				s.logger.Printf("Error decoding message: %v", err)
				continue
			}

			response := s.handleMessage(ctx, message)
			if err := encoder.Encode(response); err != nil {
				s.logger.Printf("Error encoding response: %v", err)
				return err
			}
		}
	}
}

// handleMessage processes incoming MCP messages
func (s *MCPServer) handleMessage(ctx context.Context, message MCPMessage) MCPMessage {
	switch message.Method {
	case "initialize":
		return s.handleInitialize(ctx, message)
	case "tools/list":
		return s.handleToolsList(ctx, message)
	case "tools/call":
		return s.handleToolsCall(ctx, message)
	case "resources/list":
		return s.handleResourcesList(ctx, message)
	case "resources/read":
		return s.handleResourcesRead(ctx, message)
	default:
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32601,
				Message: fmt.Sprintf("Method not found: %s", message.Method),
			},
		}
	}
}

// handleInitialize handles the initialize method
func (s *MCPServer) handleInitialize(ctx context.Context, message MCPMessage) MCPMessage {
	s.logger.Println("Handling initialize request")

	result := MCPInitializeResult{
		ProtocolVersion: "2024-11-05",
		Capabilities: map[string]interface{}{
			"tools": map[string]interface{}{
				"listChanged": true,
			},
			"resources": map[string]interface{}{
				"subscribe":   true,
				"listChanged": true,
			},
		},
		ServerInfo: MCPServerInfo{
			Name:    s.config.ServerName,
			Version: s.config.ServerVersion,
		},
	}

	return MCPMessage{
		JSONRPC: "2.0",
		ID:      message.ID,
		Result:  result,
	}
}

// handleToolsList handles the tools/list method
func (s *MCPServer) handleToolsList(ctx context.Context, message MCPMessage) MCPMessage {
	s.logger.Println("Handling tools/list request")

	tools := s.GetTools()
	toolsList := make([]map[string]interface{}, 0, len(tools))

	for _, tool := range tools {
		toolsList = append(toolsList, map[string]interface{}{
			"name":        tool.Name,
			"description": tool.Description,
			"inputSchema": tool.InputSchema,
		})
	}

	result := map[string]interface{}{
		"tools": toolsList,
	}

	return MCPMessage{
		JSONRPC: "2.0",
		ID:      message.ID,
		Result:  result,
	}
}

// handleToolsCall handles the tools/call method
func (s *MCPServer) handleToolsCall(ctx context.Context, message MCPMessage) MCPMessage {
	params, ok := message.Params.(map[string]interface{})
	if !ok {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32602,
				Message: "Invalid params",
			},
		}
	}

	toolName, ok := params["name"].(string)
	if !ok {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32602,
				Message: "Tool name is required",
			},
		}
	}

	s.logger.Printf("Handling tools/call request for tool: %s", toolName)

	tools := s.GetTools()
	tool, exists := tools[toolName]
	if !exists {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32601,
				Message: fmt.Sprintf("Tool not found: %s", toolName),
			},
		}
	}

	arguments, _ := params["arguments"].(map[string]interface{})
	result, err := tool.Handler(ctx, arguments)
	if err != nil {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32603,
				Message: err.Error(),
			},
		}
	}

	response := map[string]interface{}{
		"content": []map[string]interface{}{
			{
				"type": "text",
				"text": fmt.Sprintf("%v", result),
			},
		},
		"isError": false,
	}

	return MCPMessage{
		JSONRPC: "2.0",
		ID:      message.ID,
		Result:  response,
	}
}

// handleResourcesList handles the resources/list method
func (s *MCPServer) handleResourcesList(ctx context.Context, message MCPMessage) MCPMessage {
	s.logger.Println("Handling resources/list request")

	resources := s.GetResources()
	resourcesList := make([]map[string]interface{}, 0, len(resources))

	for _, resource := range resources {
		resourcesList = append(resourcesList, map[string]interface{}{
			"uri":         resource.URI,
			"name":        resource.Name,
			"description": resource.Description,
			"mimeType":    resource.MimeType,
		})
	}

	result := map[string]interface{}{
		"resources": resourcesList,
	}

	return MCPMessage{
		JSONRPC: "2.0",
		ID:      message.ID,
		Result:  result,
	}
}

// handleResourcesRead handles the resources/read method
func (s *MCPServer) handleResourcesRead(ctx context.Context, message MCPMessage) MCPMessage {
	params, ok := message.Params.(map[string]interface{})
	if !ok {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32602,
				Message: "Invalid params",
			},
		}
	}

	uri, ok := params["uri"].(string)
	if !ok {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32602,
				Message: "URI is required",
			},
		}
	}

	s.logger.Printf("Handling resources/read request for URI: %s", uri)

	// Find resource by URI
	var targetResource *MCPResource
	resources := s.GetResources()
	for _, resource := range resources {
		if resource.URI == uri {
			targetResource = resource
			break
		}
	}

	if targetResource == nil {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32601,
				Message: fmt.Sprintf("Resource not found: %s", uri),
			},
		}
	}

	result, err := targetResource.Handler(ctx, uri)
	if err != nil {
		return MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32603,
				Message: err.Error(),
			},
		}
	}

	response := map[string]interface{}{
		"contents": []map[string]interface{}{
			{
				"uri":      uri,
				"mimeType": targetResource.MimeType,
				"text":     fmt.Sprintf("%v", result),
			},
		},
	}

	return MCPMessage{
		JSONRPC: "2.0",
		ID:      message.ID,
		Result:  response,
	}
}

// Placeholder methods for other transport types - moved to mcp_handlers.go
