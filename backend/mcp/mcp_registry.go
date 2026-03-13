package mcp

import (
	"context"
	"fmt"
	"sync"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/log"
)

// MCPClient represents a Model Context Protocol client
type MCPClient struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Version     string                 `json:"version"`
	Endpoint    string                 `json:"endpoint"`
	Tools       []MCPTool             `json:"tools"`
	Enabled     bool                   `json:"enabled"`
	Config      map[string]interface{} `json:"config"`
}

// MCPTool represents a tool provided by an MCP server
type MCPTool struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	InputSchema map[string]interface{} `json:"inputSchema"`
	ToolType    string                 `json:"toolType"` // native, mcp
	ServerName  string                 `json:"serverName,omitempty"`
	Category    string                 `json:"category,omitempty"`    // finance, hr, travel, ecommerce
	Priority    int                    `json:"priority,omitempty"`    // 1=high, 2=medium, 3=low
	GoalAligned []string              `json:"goalAligned,omitempty"`  // Goals this tool supports
	Handler     MCPToolHandler         `json:"-"` // Handler for the tool
}

// MCPToolCall represents a call to an MCP tool
type MCPToolCall struct {
	ToolName    string                 `json:"toolName"`
	Parameters  map[string]interface{} `json:"parameters"`
	ServerName  string                 `json:"serverName,omitempty"`
	Result      map[string]interface{} `json:"result,omitempty"`
	Error       string                 `json:"error,omitempty"`
	Duration    time.Duration          `json:"duration"`
	GoalContext string                 `json:"goalContext,omitempty"`  // Goal this call supports
	AgentType   string                 `json:"agentType,omitempty"`    // Type of agent making the call
}

// MCPRegistry manages MCP servers and tools
type MCPRegistry struct {
	clients map[string]*MCPClient
	mu      sync.RWMutex
	logger  log.Logger
}

// NewMCPRegistry creates a new MCP registry
func NewMCPRegistry() *MCPRegistry {
	return &MCPRegistry{
		clients: make(map[string]*MCPClient),
	}
}

// RegisterClient registers an MCP client
func (mr *MCPRegistry) RegisterClient(client *MCPClient) error {
	mr.mu.Lock()
	defer mr.mu.Unlock()

	if client.Name == "" {
		return fmt.Errorf("client name cannot be empty")
	}

	mr.clients[client.Name] = client
	return nil
}

// GetClient retrieves an MCP client by name
func (mr *MCPRegistry) GetClient(name string) (*MCPClient, error) {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	client, exists := mr.clients[name]
	if !exists {
		return nil, fmt.Errorf("MCP client %s not found", name)
	}
	return client, nil
}

// ListClients returns all registered MCP clients
func (mr *MCPRegistry) ListClients() []*MCPClient {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	clients := make([]*MCPClient, 0, len(mr.clients))
	for _, client := range mr.clients {
		clients = append(clients, client)
	}
	return clients
}

// ListAllTools returns all available tools from all MCP clients
func (mr *MCPRegistry) ListAllTools() []MCPTool {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	var allTools []MCPTool
	for _, client := range mr.clients {
		if client.Enabled {
			allTools = append(allTools, client.Tools...)
		}
	}
	return allTools
}

// GetToolsByCategory returns tools filtered by category
func (mr *MCPRegistry) GetToolsByCategory(category string) []MCPTool {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	var tools []MCPTool
	for _, client := range mr.clients {
		if client.Enabled {
			for _, tool := range client.Tools {
				if tool.Category == category {
					tools = append(tools, tool)
				}
			}
		}
	}
	return tools
}

// GetToolsByGoal returns tools that align with a specific goal
func (mr *MCPRegistry) GetToolsByGoal(goal string) []MCPTool {
	mr.mu.RLock()
	defer mr.mu.RUnlock()

	var tools []MCPTool
	for _, client := range mr.clients {
		if client.Enabled {
			for _, tool := range client.Tools {
				for _, alignedGoal := range tool.GoalAligned {
					if alignedGoal == goal {
						tools = append(tools, tool)
						break
					}
				}
			}
		}
	}
	return tools
}

// GetToolsByPriority returns tools sorted by priority (1=high first)
func (mr *MCPRegistry) GetToolsByPriority(maxPriority int) []MCPTool {
	allTools := mr.ListAllTools()
	
	// Filter by priority
	var filteredTools []MCPTool
	for _, tool := range allTools {
		if tool.Priority <= maxPriority {
			filteredTools = append(filteredTools, tool)
		}
	}
	
	// Sort by priority (simple bubble sort for now)
	for i := 0; i < len(filteredTools)-1; i++ {
		for j := 0; j < len(filteredTools)-i-1; j++ {
			if filteredTools[j].Priority > filteredTools[j+1].Priority {
				filteredTools[j], filteredTools[j+1] = filteredTools[j+1], filteredTools[j]
			}
		}
	}
	
	return filteredTools
}

// ExecuteToolForGoal executes a tool in the context of a specific goal
func (mr *MCPRegistry) ExecuteToolForGoal(ctx context.Context, toolCall *MCPToolCall, goal string, agentType string) error {
	toolCall.GoalContext = goal
	toolCall.AgentType = agentType
	return mr.ExecuteTool(ctx, toolCall)
}

// ExecuteTool executes an MCP tool
func (mr *MCPRegistry) ExecuteTool(ctx context.Context, toolCall *MCPToolCall) error {
	start := time.Now()

	client, err := mr.GetClient(toolCall.ServerName)
	if err != nil {
		return fmt.Errorf("failed to get MCP client: %w", err)
	}

	if !client.Enabled {
		return fmt.Errorf("MCP client %s is disabled", client.Name)
	}

	// Find the tool
	var tool *MCPTool
	for _, t := range client.Tools {
		if t.Name == toolCall.ToolName {
			tool = &t
			break
		}
	}

	if tool == nil {
		return fmt.Errorf("tool %s not found in client %s", toolCall.ToolName, client.Name)
	}

	// Execute the tool (mock implementation - would connect to actual MCP server)
	result, err := mr.executeMCPTool(ctx, client, tool, toolCall.Parameters)
	if err != nil {
		toolCall.Error = err.Error()
		toolCall.Duration = time.Since(start)
		return err
	}

	toolCall.Result = result
	toolCall.Duration = time.Since(start)
	return nil
}

// executeMCPTool executes a tool on an MCP server (mock implementation)
func (mr *MCPRegistry) executeMCPTool(ctx context.Context, client *MCPClient, tool *MCPTool, params map[string]interface{}) (map[string]interface{}, error) {
	// This is a mock implementation. In a real implementation, this would:
	// 1. Connect to the MCP server endpoint
	// 2. Send the tool execution request
	// 3. Handle the response

	logger := activity.GetLogger(ctx)
	logger.Info("Executing MCP tool", "client", client.Name, "tool", tool.Name, "params", params)

	// Mock responses for different tool types
	switch tool.Name {
	case "stripe_payment":
		return map[string]interface{}{
			"status": "success",
			"payment_id": "pi_mock_123",
			"amount": params["amount"],
			"currency": params["currency"],
		}, nil

	case "database_query":
		return map[string]interface{}{
			"rows": []map[string]interface{}{
				{"id": 1, "name": "example"},
			},
			"count": 1,
		}, nil

	case "web_search":
		return map[string]interface{}{
			"results": []string{
				"Result 1: Information about " + fmt.Sprintf("%v", params["query"]),
				"Result 2: More details found",
			},
			"total_results": 2,
		}, nil

	default:
		return map[string]interface{}{
			"status": "completed",
			"message": fmt.Sprintf("Tool %s executed successfully", tool.Name),
			"params": params,
		}, nil
	}
}

// LoadDefaultMCPClients loads default MCP client configurations
func (mr *MCPRegistry) LoadDefaultMCPClients() error {
	// Stripe MCP client - Finance category
	stripeClient := &MCPClient{
		Name:        "stripe",
		Description: "Stripe payment processing integration",
		Version:     "1.0.0",
		Endpoint:    "https://api.stripe.com/v1",
		Enabled:     true,
		Config: map[string]interface{}{
			"api_key": "sk_test_...",
		},
		Tools: []MCPTool{
			{
				Name:        "stripe_payment",
				Description: "Process a payment through Stripe",
				ToolType:    "mcp",
				ServerName:  "stripe",
				Category:    "finance",
				Priority:    1,
				GoalAligned: []string{"payment-processing", "billing", "subscription-management"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"amount": map[string]interface{}{
							"type": "number",
							"description": "Payment amount in cents",
						},
						"currency": map[string]interface{}{
							"type": "string",
							"description": "Currency code (e.g., usd)",
						},
						"source": map[string]interface{}{
							"type": "string",
							"description": "Payment source token",
						},
					},
					"required": []string{"amount", "currency", "source"},
				},
			},
			{
				Name:        "stripe_refund",
				Description: "Process a refund through Stripe",
				ToolType:    "mcp",
				ServerName:  "stripe",
				Category:    "finance",
				Priority:    2,
				GoalAligned: []string{"payment-processing", "billing"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"payment_id": map[string]interface{}{
							"type": "string",
							"description": "Payment ID to refund",
						},
						"amount": map[string]interface{}{
							"type": "number",
							"description": "Refund amount in cents",
						},
					},
					"required": []string{"payment_id"},
				},
			},
		},
	}

	// Database MCP client - General purpose
	dbClient := &MCPClient{
		Name:        "database",
		Description: "Database query and management",
		Version:     "1.0.0",
		Endpoint:    "postgresql://localhost:5432",
		Enabled:     true,
		Config: map[string]interface{}{
			"connection_string": "postgres://user:pass@localhost/db",
		},
		Tools: []MCPTool{
			{
				Name:        "database_query",
				Description: "Execute a database query",
				ToolType:    "mcp",
				ServerName:  "database",
				Category:    "general",
				Priority:    1,
				GoalAligned: []string{"data-analysis", "reporting", "audit"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"query": map[string]interface{}{
							"type": "string",
							"description": "SQL query to execute",
						},
						"params": map[string]interface{}{
							"type": "array",
							"description": "Query parameters",
						},
					},
					"required": []string{"query"},
				},
			},
		},
	}

	// Web search MCP client - Research category
	searchClient := &MCPClient{
		Name:        "web_search",
		Description: "Web search and information retrieval",
		Version:     "1.0.0",
		Endpoint:    "https://api.search.example.com",
		Enabled:     true,
		Config: map[string]interface{}{
			"api_key": "search_api_key",
		},
		Tools: []MCPTool{
			{
				Name:        "web_search",
				Description: "Search the web for information",
				ToolType:    "mcp",
				ServerName:  "web_search",
				Category:    "research",
				Priority:    1,
				GoalAligned: []string{"research", "information-gathering", "competitive-analysis"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"query": map[string]interface{}{
							"type": "string",
							"description": "Search query",
						},
						"limit": map[string]interface{}{
							"type": "number",
							"description": "Maximum number of results",
							"default": 10,
						},
					},
					"required": []string{"query"},
				},
			},
		},
	}

	// HR MCP client - HR category
	hrClient := &MCPClient{
		Name:        "hr_system",
		Description: "Human resources management system",
		Version:     "1.0.0",
		Endpoint:    "https://api.company-hr.com",
		Enabled:     true,
		Config: map[string]interface{}{
			"api_key": "hr_api_key",
		},
		Tools: []MCPTool{
			{
				Name:        "employee_lookup",
				Description: "Look up employee information",
				ToolType:    "mcp",
				ServerName:  "hr_system",
				Category:    "hr",
				Priority:    1,
				GoalAligned: []string{"employee-management", "onboarding", "team-coordination"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"employee_id": map[string]interface{}{
							"type": "string",
							"description": "Employee ID",
						},
						"fields": map[string]interface{}{
							"type": "array",
							"description": "Fields to return",
							"items": map[string]interface{}{
								"type": "string",
							},
						},
					},
					"required": []string{"employee_id"},
				},
			},
			{
				Name:        "leave_request",
				Description: "Submit a leave request",
				ToolType:    "mcp",
				ServerName:  "hr_system",
				Category:    "hr",
				Priority:    2,
				GoalAligned: []string{"leave-management", "employee-requests"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"employee_id": map[string]interface{}{
							"type": "string",
							"description": "Employee ID",
						},
						"start_date": map[string]interface{}{
							"type": "string",
							"description": "Start date (YYYY-MM-DD)",
						},
						"end_date": map[string]interface{}{
							"type": "string",
							"description": "End date (YYYY-MM-DD)",
						},
						"reason": map[string]interface{}{
							"type": "string",
							"description": "Reason for leave",
						},
					},
					"required": []string{"employee_id", "start_date", "end_date"},
				},
			},
		},
	}

	// Travel MCP client - Travel category
	travelClient := &MCPClient{
		Name:        "travel_booking",
		Description: "Travel booking and management",
		Version:     "1.0.0",
		Endpoint:    "https://api.travel.example.com",
		Enabled:     true,
		Config: map[string]interface{}{
			"api_key": "travel_api_key",
		},
		Tools: []MCPTool{
			{
				Name:        "book_flight",
				Description: "Book a flight",
				ToolType:    "mcp",
				ServerName:  "travel_booking",
				Category:    "travel",
				Priority:    1,
				GoalAligned: []string{"travel-booking", "business-travel"},
				InputSchema: map[string]interface{}{
					"type": "object",
					"properties": map[string]interface{}{
						"origin": map[string]interface{}{
							"type": "string",
							"description": "Origin airport code",
						},
						"destination": map[string]interface{}{
							"type": "string",
							"description": "Destination airport code",
						},
						"date": map[string]interface{}{
							"type": "string",
							"description": "Travel date (YYYY-MM-DD)",
						},
						"passengers": map[string]interface{}{
							"type": "number",
							"description": "Number of passengers",
							"default": 1,
						},
					},
					"required": []string{"origin", "destination", "date"},
				},
			},
		},
	}

	// Register all clients
	clients := []*MCPClient{stripeClient, dbClient, searchClient, hrClient, travelClient}
	for _, client := range clients {
		if err := mr.RegisterClient(client); err != nil {
			return err
		}
	}

	return nil
}

// Global MCP registry instance
var globalMCPRegistry *MCPRegistry
var mcpOnce sync.Once

// GetGlobalMCPRegistry returns the global MCP registry instance
func GetGlobalMCPRegistry() *MCPRegistry {
	mcpOnce.Do(func() {
		globalMCPRegistry = NewMCPRegistry()
		globalMCPRegistry.LoadDefaultMCPClients()
	})
	return globalMCPRegistry
}
