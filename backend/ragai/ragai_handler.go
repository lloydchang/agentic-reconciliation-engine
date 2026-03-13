package ragai

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
)

// RagAIHandler handles RAG AI API endpoints
type RagAIHandler struct {
	mcpRegistry *mcp.MCPRegistry
}

// NewRagAIHandler creates a new RAG AI handler
func NewRagAIHandler() *RagAIHandler {
	return &RagAIHandler{
		mcpRegistry: mcp.GetGlobalMCPRegistry(),
	}
}

// ChatRequest represents a chat request
type ChatRequest struct {
	Message        string `json:"message"`
	Category       string `json:"category,omitempty"`
	IncludeSources bool   `json:"includeSources"`
	MaxTokens      int    `json:"maxTokens,omitempty"`
	Temperature    float64 `json:"temperature,omitempty"`
}

// ChatResponse represents a chat response
type ChatResponse struct {
	Message       string      `json:"message"`
	Sources       []string    `json:"sources"`
	ToolCalls     []ToolCall  `json:"toolCalls"`
	Confidence    float64     `json:"confidence"`
	ProcessingTime int64      `json:"processingTime"`
}

// ToolCall represents a tool call in the response
type ToolCall struct {
	ToolName   string                 `json:"toolName"`
	Parameters map[string]interface{} `json:"parameters"`
	Result     map[string]interface{} `json:"result,omitempty"`
	Error      string                 `json:"error,omitempty"`
	Duration   int64                  `json:"duration"`
}

// SearchRequest represents a search request
type SearchRequest struct {
	Query   string                 `json:"query"`
	Filters map[string]interface{} `json:"filters,omitempty"`
	Limit   int                    `json:"limit,omitempty"`
	Offset  int                    `json:"offset,omitempty"`
}

// SearchResult represents a single search result
type SearchResult struct {
	ID       string                 `json:"id"`
	Title    string                 `json:"title"`
	Content  string                 `json:"content"`
	Source   string                 `json:"source"`
	URL      string                 `json:"url,omitempty"`
	Score    float64                `json:"score"`
	Metadata map[string]interface{} `json:"metadata"`
}

// SearchResponse represents a search response
type SearchResponse struct {
	Results []SearchResult        `json:"results"`
	Total   int                   `json:"total"`
	Facets  map[string]interface{} `json:"facets"`
}

// RegisterRoutes registers RAG AI routes
func (h *RagAIHandler) RegisterRoutes(router *mux.Router) {
	// Chat endpoint
	router.HandleFunc("/chat", h.handleChat).Methods("POST")
	
	// Search endpoint
	router.HandleFunc("/search", h.handleSearch).Methods("GET")
	
	// Tools endpoint
	router.HandleFunc("/tools", h.handleGetTools).Methods("GET")
	router.HandleFunc("/tools/{toolName}", h.handleGetTool).Methods("GET")
	
	// Categories endpoint
	router.HandleFunc("/categories", h.handleGetCategories).Methods("GET")
}

// handleChat handles chat requests
func (h *RagAIHandler) handleChat(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	
	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Set defaults
	if req.MaxTokens == 0 {
		req.MaxTokens = 1000
	}
	if req.Temperature == 0 {
		req.Temperature = 0.7
	}

	// Process the message
	response, err := h.processChatMessage(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	response.ProcessingTime = time.Since(start).Milliseconds()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleSearch handles search requests
func (h *RagAIHandler) handleSearch(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("query")
	if query == "" {
		http.Error(w, "query parameter is required", http.StatusBadRequest)
		return
	}

	req := SearchRequest{
		Query: query,
	}

	// Parse optional parameters
	if limit := r.URL.Query().Get("limit"); limit != "" {
		if l, err := fmt.Sscanf(limit, "%d", &req.Limit); err != nil || l != 1 {
			req.Limit = 10
		}
	} else {
		req.Limit = 10
	}

	if offset := r.URL.Query().Get("offset"); offset != "" {
		if o, err := fmt.Sscanf(offset, "%d", &req.Offset); err != nil || o != 1 {
			req.Offset = 0
		}
	} else {
		req.Offset = 0
	}

	// Parse filters
	if filters := r.URL.Query().Get("filters"); filters != "" {
		var filterMap map[string]interface{}
		if err := json.Unmarshal([]byte(filters), &filterMap); err == nil {
			req.Filters = filterMap
		}
	}

	response, err := h.processSearch(r.Context(), req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleGetTools handles getting all tools
func (h *RagAIHandler) handleGetTools(w http.ResponseWriter, r *http.Request) {
	category := r.URL.Query().Get("category")
	goal := r.URL.Query().Get("goal")

	var tools []mcp.MCPTool
	switch {
	case goal != "":
		tools = h.mcpRegistry.GetToolsByGoal(goal)
	case category != "":
		tools = h.mcpRegistry.GetToolsByCategory(category)
	default:
		tools = h.mcpRegistry.ListAllTools()
	}

	response := map[string]interface{}{
		"tools": tools,
		"count": len(tools),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleGetTool handles getting a specific tool
func (h *RagAIHandler) handleGetTool(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	toolName := vars["toolName"]

	if toolName == "" {
		http.Error(w, "tool name is required", http.StatusBadRequest)
		return
	}

	// Find the tool
	allTools := h.mcpRegistry.ListAllTools()
	var foundTool *mcp.MCPTool
	for _, tool := range allTools {
		if tool.Name == toolName {
			foundTool = &tool
			break
		}
	}

	if foundTool == nil {
		http.Error(w, "tool not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(foundTool)
}

// handleGetCategories handles getting all categories
func (h *RagAIHandler) handleGetCategories(w http.ResponseWriter, r *http.Request) {
	allTools := h.mcpRegistry.ListAllTools()
	categories := make(map[string]bool)
	for _, tool := range allTools {
		if tool.Category != "" {
			categories[tool.Category] = true
		}
	}

	// Convert to slice
	var categoryList []string
	for category := range categories {
		categoryList = append(categoryList, category)
	}

	response := map[string]interface{}{
		"categories": categoryList,
		"count":      len(categoryList),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// processChatMessage processes a chat message and generates a response
func (h *RagAIHandler) processChatMessage(ctx context.Context, req ChatRequest) (*ChatResponse, error) {
	// This is a simplified implementation
	// In a real implementation, this would:
	// 1. Use the message to search for relevant documents
	// 2. Use LLM to generate a response based on the context
	// 3. Call appropriate tools if needed

	response := &ChatResponse{
		Sources:    []string{},
		ToolCalls:  []ToolCall{},
		Confidence: 0.8,
	}

	// Determine if any tools should be called based on the message
	toolsToCall := h.determineToolsFromMessage(req.Message)
	
	for _, tool := range toolsToCall {
		toolCall := mcp.MCPToolCall{
			ToolName:   tool.Name,
			Parameters: h.extractParametersFromMessage(req.Message, tool),
			ServerName: tool.ServerName,
		}

		// Execute the tool
		err := h.mcpRegistry.ExecuteTool(ctx, &toolCall)
		if err != nil {
			toolCall.Error = err.Error()
		}

		response.ToolCalls = append(response.ToolCalls, ToolCall{
			ToolName:   toolCall.ToolName,
			Parameters: toolCall.Parameters,
			Result:     toolCall.Result,
			Error:      toolCall.Error,
			Duration:   toolCall.Duration.Milliseconds(),
		})
	}

	// Generate response based on tool results and message
	response.Message = h.generateResponse(req.Message, response.ToolCalls)
	
	// Add mock sources for demonstration
	if req.IncludeSources {
		response.Sources = []string{
			"Internal Documentation",
			"Catalog Data",
			"API Documentation",
		}
	}

	return response, nil
}

// processSearch processes a search request
func (h *RagAIHandler) processSearch(ctx context.Context, req SearchRequest) (*SearchResponse, error) {
	// This is a simplified implementation
	// In a real implementation, this would search the actual knowledge base

	results := []SearchResult{
		{
			ID:      "1",
			Title:   "Sample Document 1",
			Content: "This is a sample document that matches your query: " + req.Query,
			Source:  "Documentation",
			Score:   0.9,
			Metadata: map[string]interface{}{
				"type":     "document",
				"created":  time.Now().AddDate(0, -1, 0).Format(time.RFC3339),
			},
		},
		{
			ID:      "2",
			Title:   "Sample Document 2",
			Content: "Another relevant document about: " + req.Query,
			Source:  "Catalog",
			Score:   0.8,
			Metadata: map[string]interface{}{
				"type":     "catalog",
				"created":  time.Now().AddDate(0, -2, 0).Format(time.RFC3339),
			},
		},
	}

	// Apply limit and offset
	total := len(results)
	if req.Offset < total {
		end := req.Offset + req.Limit
		if end > total {
			end = total
		}
		results = results[req.Offset:end]
	} else {
		results = []SearchResult{}
	}

	return &SearchResponse{
		Results: results,
		Total:   total,
		Facets: map[string]interface{}{
			"sources": map[string]int{
				"Documentation": 1,
				"Catalog":       1,
			},
			"types": map[string]int{
				"document": 1,
				"catalog":  1,
			},
		},
	}, nil
}

// determineToolsFromMessage determines which tools to call based on the message
func (h *RagAIHandler) determineToolsFromMessage(message string) []mcp.MCPTool {
	var tools []mcp.MCPTool
	allTools := h.mcpRegistry.ListAllTools()

	messageLower := strings.ToLower(message)

	for _, tool := range allTools {
		if h.shouldCallTool(messageLower, tool) {
			tools = append(tools, tool)
		}
	}

	return tools
}

// shouldCallTool determines if a tool should be called based on the message
func (h *RagAIHandler) shouldCallTool(message string, tool mcp.MCPTool) bool {
	switch tool.Name {
	case "stripe_payment":
		return containsAny(message, []string{"payment", "pay", "charge", "billing"})
	case "database_query":
		return containsAny(message, []string{"query", "data", "database", "records"})
	case "web_search":
		return containsAny(message, []string{"search", "find", "research", "information"})
	case "employee_lookup":
		return containsAny(message, []string{"employee", "staff", "team", "person"})
	case "book_flight":
		return containsAny(message, []string{"travel", "flight", "book", "trip"})
	default:
		return false
	}
}

// extractParametersFromMessage extracts parameters for a tool from the message
func (h *RagAIHandler) extractParametersFromMessage(message string, tool mcp.MCPTool) map[string]interface{} {
	params := make(map[string]interface{})

	switch tool.Name {
	case "stripe_payment":
		params["amount"] = 10000 // $100.00 in cents
		params["currency"] = "usd"
		params["source"] = "tok_mock"
	case "database_query":
		params["query"] = "SELECT * FROM users LIMIT 10"
	case "web_search":
		params["query"] = message
		params["limit"] = 10
	case "employee_lookup":
		params["employee_id"] = "emp123"
		params["fields"] = []string{"name", "email", "department"}
	case "book_flight":
		params["origin"] = "SFO"
		params["destination"] = "NYC"
		params["date"] = "2024-12-25"
		params["passengers"] = 1
	}

	return params
}

// generateResponse generates a response based on the message and tool results
func (h *RagAIHandler) generateResponse(message string, toolCalls []ToolCall) string {
	if len(toolCalls) == 0 {
		return fmt.Sprintf("I understand you're asking about: %s. Let me help you with that information.", message)
	}

	var responses []string
	for _, toolCall := range toolCalls {
		if toolCall.Error != "" {
			responses = append(responses, fmt.Sprintf("There was an issue with %s: %s", toolCall.ToolName, toolCall.Error))
		} else {
			switch toolCall.ToolName {
			case "stripe_payment":
				responses = append(responses, "I've processed the payment successfully.")
			case "database_query":
				responses = append(responses, "I found the requested data in our database.")
			case "web_search":
				responses = append(responses, "I found relevant information for your search query.")
			case "employee_lookup":
				responses = append(responses, "I found the employee information you requested.")
			case "book_flight":
				responses = append(responses, "I've found available flights for your travel dates.")
			default:
				responses = append(responses, fmt.Sprintf("Successfully completed %s operation.", toolCall.ToolName))
			}
		}
	}

	return strings.Join(responses, " ") + " Is there anything else I can help you with?"
}

// containsAny checks if the text contains any of the keywords
func containsAny(text string, keywords []string) bool {
	for _, keyword := range keywords {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	return false
}
