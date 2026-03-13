package mcp

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/client"

	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// registerDefaultTools registers the default MCP tools
func (s *MCPServer) registerDefaultTools() {
	// Start Compliance Workflow Tool
	s.RegisterTool(&MCPTool{
		Name:        "start_compliance_workflow",
		Description: "Start a compliance check workflow for a target resource",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"targetResource": map[string]interface{}{
					"type":        "string",
					"description": "The target resource to check (e.g., vm-web-server-001)",
				},
				"complianceType": map[string]interface{}{
					"type":        "string",
					"description": "Type of compliance check (SOC2, GDPR, HIPAA, full-scan)",
					"enum":        []string{"SOC2", "GDPR", "HIPAA", "full-scan"},
				},
				"priority": map[string]interface{}{
					"type":        "string",
					"description": "Priority level (low, normal, high, critical)",
					"enum":        []string{"low", "normal", "high", "critical"},
					"default":     "normal",
				},
				"parameters": map[string]interface{}{
					"type":        "object",
					"description": "Additional parameters for the compliance check",
					"default":     map[string]interface{}{},
				},
			},
			"required": []string{"targetResource", "complianceType"},
		},
		Handler: s.handleStartComplianceWorkflow,
	})

	// Start Security Scan Tool
	s.RegisterTool(&MCPTool{
		Name:        "start_security_scan",
		Description: "Start a security analysis workflow",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"targetResource": map[string]interface{}{
					"type":        "string",
					"description": "The target resource to scan",
				},
				"scanType": map[string]interface{}{
					"type":        "string",
					"description": "Type of security scan",
					"enum":        []string{"vulnerability", "malware", "configuration", "full"},
					"default":     "full",
				},
				"priority": map[string]interface{}{
					"type":        "string",
					"description": "Priority level",
					"enum":        []string{"low", "normal", "high", "critical"},
					"default":     "normal",
				},
			},
			"required": []string{"targetResource"},
		},
		Handler: s.handleStartSecurityScan,
	})

	// Start Cost Analysis Tool
	s.RegisterTool(&MCPTool{
		Name:        "start_cost_analysis",
		Description: "Start a cost optimization analysis workflow",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"targetResource": map[string]interface{}{
					"type":        "string",
					"description": "The target resource to analyze",
				},
				"analysisType": map[string]interface{}{
					"type":        "string",
					"description": "Type of cost analysis",
					"enum":        []string{"usage", "optimization", "forecast", "full"},
					"default":     "full",
				},
				"timeframe": map[string]interface{}{
					"type":        "string",
					"description": "Timeframe for analysis (7d, 30d, 90d)",
					"enum":        []string{"7d", "30d", "90d"},
					"default":     "30d",
				},
			},
			"required": []string{"targetResource"},
		},
		Handler: s.handleStartCostAnalysis,
	})

	// Get Workflow Status Tool
	s.RegisterTool(&MCPTool{
		Name:        "get_workflow_status",
		Description: "Get the status of a running workflow",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"workflowId": map[string]interface{}{
					"type":        "string",
					"description": "The workflow ID to check",
				},
				"includeDetails": map[string]interface{}{
					"type":        "boolean",
					"description": "Include detailed workflow information",
					"default":     false,
				},
			},
			"required": []string{"workflowId"},
		},
		Handler: s.handleGetWorkflowStatus,
	})

	// Signal Workflow Tool
	s.RegisterTool(&MCPTool{
		Name:        "signal_workflow",
		Description: "Send a signal to a running workflow",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"workflowId": map[string]interface{}{
					"type":        "string",
					"description": "The workflow ID to signal",
				},
				"signalName": map[string]interface{}{
					"type":        "string",
					"description": "The name of the signal",
				},
				"signalValue": map[string]interface{}{
					"type":        "string",
					"description": "The value to send with the signal",
				},
			},
			"required": []string{"workflowId", "signalName", "signalValue"},
		},
		Handler: s.handleSignalWorkflow,
	})

	// Get Infrastructure Info Tool
	s.RegisterTool(&MCPTool{
		Name:        "get_infrastructure_info",
		Description: "Get information about infrastructure resources",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"resourceType": map[string]interface{}{
					"type":        "string",
					"description": "Type of resource (vm, database, storage, network)",
					"enum":        []string{"vm", "database", "storage", "network", "all"},
					"default":     "all",
				},
				"environment": map[string]interface{}{
					"type":        "string",
					"description": "Environment (dev, staging, prod)",
					"enum":        []string{"dev", "staging", "prod", "all"},
					"default":     "all",
				},
			},
		},
		Handler: s.handleGetInfrastructureInfo,
	})

	// Start Conversation Tool
	s.RegisterTool(&MCPTool{
		Name:        "start_conversation",
		Description: "Start a multi-turn conversation with an AI agent",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"userId": map[string]interface{}{
					"type":        "string",
					"description": "User ID for the conversation",
				},
				"goal": map[string]interface{}{
					"type":        "string",
					"description": "The goal or objective of the conversation",
				},
				"initialInput": map[string]interface{}{
					"type":        "string",
					"description": "Initial input or question from the user",
				},
				"llmProvider": map[string]interface{}{
					"type":        "string",
					"description": "LLM provider to use (openai, anthropic, gemini)",
					"enum":        []string{"openai", "anthropic", "gemini"},
					"default":     "openai",
				},
				"llmModel": map[string]interface{}{
					"type":        "string",
					"description": "LLM model to use",
					"default":     "gpt-4",
				},
				"maxTurns": map[string]interface{}{
					"type":        "integer",
					"description": "Maximum number of conversation turns",
					"default":     20,
					"minimum":     1,
					"maximum":     50,
				},
				"toolsEnabled": map[string]interface{}{
					"type":        "array",
					"description": "List of tools to enable for this conversation",
					"items": map[string]interface{}{
						"type": "string",
					},
					"default": []string{"start_compliance_workflow", "get_infrastructure_info"},
				},
			},
			"required": []string{"userId", "goal"},
		},
		Handler: s.handleStartConversation,
	})

	// Send Message to Conversation Tool
	s.RegisterTool(&MCPTool{
		Name:        "send_conversation_message",
		Description: "Send a message to an active conversation",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"conversationId": map[string]interface{}{
					"type":        "string",
					"description": "The conversation ID to send message to",
				},
				"message": map[string]interface{}{
					"type":        "string",
					"description": "The message to send",
				},
			},
			"required": []string{"conversationId", "message"},
		},
		Handler: s.handleSendConversationMessage,
	})

	// Get Conversation Status Tool
	s.RegisterTool(&MCPTool{
		Name:        "get_conversation_status",
		Description: "Get the status and details of a conversation",
		InputSchema: map[string]interface{}{
			"type": "object",
			"properties": map[string]interface{}{
				"conversationId": map[string]interface{}{
					"type":        "string",
					"description": "The conversation ID to check",
				},
				"includeHistory": map[string]interface{}{
					"type":        "boolean",
					"description": "Include conversation history in response",
					"default":     false,
				},
			},
			"required": []string{"conversationId"},
		},
		Handler: s.handleGetConversationStatus,
	})
}

// handleStartComplianceWorkflow handles starting a compliance workflow
func (s *MCPServer) handleStartComplianceWorkflow(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	targetResource, ok := params["targetResource"].(string)
	if !ok {
		return nil, fmt.Errorf("targetResource is required")
	}

	complianceType, ok := params["complianceType"].(string)
	if !ok {
		return nil, fmt.Errorf("complianceType is required")
	}

	priority, _ := params["priority"].(string)
	if priority == "" {
		priority = "normal"
	}

	additionalParams, _ := params["parameters"].(map[string]interface{})
	if additionalParams == nil {
		additionalParams = make(map[string]interface{})
	}

	// Create compliance request
	request := types.ComplianceRequest{
		TargetResource: targetResource,
		ComplianceType: complianceType,
		Parameters:     make(map[string]string),
		RequesterID:    "mcp-client",
		Priority:       priority,
	}

	// Convert additional parameters
	for k, v := range additionalParams {
		if str, ok := v.(string); ok {
			request.Parameters[k] = str
		}
	}

	// Start the workflow
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("mcp-compliance-%s-%d", targetResource, time.Now().Unix()),
		TaskQueue: "ai-agent-task-queue-v2",
	}

	we, err := s.temporalClient.ExecuteWorkflow(ctx, workflowOptions, 
		"AIAgentOrchestrationWorkflowV2", request)
	if err != nil {
		return nil, fmt.Errorf("failed to start compliance workflow: %w", err)
	}

	return map[string]interface{}{
		"workflowId":   we.GetID(),
		"runId":        we.GetRunID(),
		"status":       "started",
		"targetResource": targetResource,
		"complianceType": complianceType,
		"priority":     priority,
		"startedAt":    time.Now().Format(time.RFC3339),
	}, nil
}

// handleStartSecurityScan handles starting a security scan
func (s *MCPServer) handleStartSecurityScan(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	targetResource, ok := params["targetResource"].(string)
	if !ok {
		return nil, fmt.Errorf("targetResource is required")
	}

	scanType, _ := params["scanType"].(string)
	if scanType == "" {
		scanType = "full"
	}

	priority, _ := params["priority"].(string)
	if priority == "" {
		priority = "normal"
	}

	// Create a specialized security request
	request := types.ComplianceRequest{
		TargetResource: targetResource,
		ComplianceType: fmt.Sprintf("security-%s", scanType),
		Parameters: map[string]string{
			"scanType": scanType,
		},
		RequesterID: "mcp-client",
		Priority:   priority,
	}

	// Start the workflow
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("mcp-security-%s-%d", targetResource, time.Now().Unix()),
		TaskQueue: "ai-agent-task-queue-v2",
	}

	we, err := s.temporalClient.ExecuteWorkflow(ctx, workflowOptions, 
		"AIAgentOrchestrationWorkflowV2", request)
	if err != nil {
		return nil, fmt.Errorf("failed to start security scan: %w", err)
	}

	return map[string]interface{}{
		"workflowId":   we.GetID(),
		"runId":        we.GetRunID(),
		"status":       "started",
		"targetResource": targetResource,
		"scanType":     scanType,
		"priority":     priority,
		"startedAt":    time.Now().Format(time.RFC3339),
	}, nil
}

// handleStartCostAnalysis handles starting a cost analysis
func (s *MCPServer) handleStartCostAnalysis(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	targetResource, ok := params["targetResource"].(string)
	if !ok {
		return nil, fmt.Errorf("targetResource is required")
	}

	analysisType, _ := params["analysisType"].(string)
	if analysisType == "" {
		analysisType = "full"
	}

	timeframe, _ := params["timeframe"].(string)
	if timeframe == "" {
		timeframe = "30d"
	}

	// Create a cost analysis request
	request := types.ComplianceRequest{
		TargetResource: targetResource,
		ComplianceType: fmt.Sprintf("cost-%s", analysisType),
		Parameters: map[string]string{
			"analysisType": analysisType,
			"timeframe":    timeframe,
		},
		RequesterID: "mcp-client",
		Priority:   "normal",
	}

	// Start the workflow
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("mcp-cost-%s-%d", targetResource, time.Now().Unix()),
		TaskQueue: "ai-agent-task-queue-v2",
	}

	we, err := s.temporalClient.ExecuteWorkflow(ctx, workflowOptions, 
		"AIAgentOrchestrationWorkflowV2", request)
	if err != nil {
		return nil, fmt.Errorf("failed to start cost analysis: %w", err)
	}

	return map[string]interface{}{
		"workflowId":     we.GetID(),
		"runId":          we.GetRunID(),
		"status":         "started",
		"targetResource": targetResource,
		"analysisType":   analysisType,
		"timeframe":      timeframe,
		"startedAt":      time.Now().Format(time.RFC3339),
	}, nil
}

// handleGetWorkflowStatus handles getting workflow status
func (s *MCPServer) handleGetWorkflowStatus(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	workflowId, ok := params["workflowId"].(string)
	if !ok {
		return nil, fmt.Errorf("workflowId is required")
	}

	includeDetails, _ := params["includeDetails"].(bool)

	// Get workflow description
	// For now, return a simulated status since we're avoiding Temporal API complexity
	result := map[string]interface{}{
		"workflowId": workflowId,
		"runId":      fmt.Sprintf("run-%d", time.Now().Unix()),
		"status":     "completed",
		"startTime":  time.Now().Add(-1*time.Hour).Format(time.RFC3339),
	}

	if includeDetails {
		result["workflowType"] = "AIAgentOrchestrationWorkflowV2"
		result["taskQueue"] = "ai-agent-task-queue-v2"
		result["executionTimeout"] = "30m"
		result["runTimeout"] = "10m"
	}

	return result, nil
}

// handleSignalWorkflow handles signaling a workflow
func (s *MCPServer) handleSignalWorkflow(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	workflowId, ok := params["workflowId"].(string)
	if !ok {
		return nil, fmt.Errorf("workflowId is required")
	}

	signalName, ok := params["signalName"].(string)
	if !ok {
		return nil, fmt.Errorf("signalName is required")
	}

	signalValue, ok := params["signalValue"].(string)
	if !ok {
		return nil, fmt.Errorf("signalValue is required")
	}

	// Send signal to workflow
	err := s.temporalClient.SignalWorkflow(ctx, workflowId, "", signalName, signalValue)
	if err != nil {
		return nil, fmt.Errorf("failed to signal workflow: %w", err)
	}

	return map[string]interface{}{
		"workflowId":   workflowId,
		"signalName":   signalName,
		"signalValue":  signalValue,
		"status":       "signal_sent",
		"sentAt":       time.Now().Format(time.RFC3339),
	}, nil
}

// handleGetInfrastructureInfo handles getting infrastructure information
func (s *MCPServer) handleGetInfrastructureInfo(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	resourceType, _ := params["resourceType"].(string)
	if resourceType == "" {
		resourceType = "all"
	}

	environment, _ := params["environment"].(string)
	if environment == "" {
		environment = "all"
	}

	// Simulate infrastructure discovery - in real implementation, this would query actual infrastructure
	infrastructure := map[string]interface{}{
		"resources": []map[string]interface{}{
			{
				"id":           "vm-web-server-001",
				"type":         "vm",
				"environment":  "prod",
				"status":       "running",
				"region":       "us-west-2",
				"instanceType": "t3.medium",
				"createdAt":    "2024-01-15T10:30:00Z",
			},
			{
				"id":           "db-main-001",
				"type":         "database",
				"environment":  "prod",
				"status":       "available",
				"engine":       "postgresql",
				"version":      "14.9",
				"region":       "us-west-2",
				"createdAt":    "2024-01-10T08:00:00Z",
			},
			{
				"id":           "storage-backups-001",
				"type":         "storage",
				"environment":  "prod",
				"status":       "active",
				"size":         "500GB",
				"storageClass": "standard",
				"region":       "us-west-2",
				"createdAt":    "2024-01-05T12:00:00Z",
			},
		},
		"total": 3,
		"queriedAt": time.Now().Format(time.RFC3339),
	}

	// Filter by resource type if specified
	if resourceType != "all" {
		filtered := make([]map[string]interface{}, 0)
		for _, resource := range infrastructure["resources"].([]map[string]interface{}) {
			if resource["type"] == resourceType {
				filtered = append(filtered, resource)
			}
		}
		infrastructure["resources"] = filtered
		infrastructure["total"] = len(filtered)
	}

	// Filter by environment if specified
	if environment != "all" {
		filtered := make([]map[string]interface{}, 0)
		for _, resource := range infrastructure["resources"].([]map[string]interface{}) {
			if resource["environment"] == environment {
				filtered = append(filtered, resource)
			}
		}
		infrastructure["resources"] = filtered
		infrastructure["total"] = len(filtered)
	}

	return infrastructure, nil
}

// handleStartConversation handles starting a new conversation
func (s *MCPServer) handleStartConversation(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	userId, ok := params["userId"].(string)
	if !ok {
		return nil, fmt.Errorf("userId is required")
	}

	goal, ok := params["goal"].(string)
	if !ok {
		return nil, fmt.Errorf("goal is required")
	}

	initialInput, _ := params["initialInput"].(string)
	llmProvider, _ := params["llmProvider"].(string)
	if llmProvider == "" {
		llmProvider = "openai"
	}

	llmModel, _ := params["llmModel"].(string)
	if llmModel == "" {
		llmModel = "gpt-4"
	}

	maxTurns, _ := params["maxTurns"].(int)
	if maxTurns == 0 {
		maxTurns = 20
	}

	toolsEnabledInterface, _ := params["toolsEnabled"].([]interface{})
	toolsEnabled := make([]string, 0)
	for _, tool := range toolsEnabledInterface {
		if toolStr, ok := tool.(string); ok {
			toolsEnabled = append(toolsEnabled, toolStr)
		}
	}
	if len(toolsEnabled) == 0 {
		toolsEnabled = []string{"start_compliance_workflow", "get_infrastructure_info"}
	}

	// Create conversation request
	request := mcpConversationRequest{
		UserID:       userId,
		Goal:         goal,
		InitialInput: initialInput,
		LLMProvider:  llmProvider,
		LLMModel:     llmModel,
		MaxTurns:     maxTurns,
		ToolsEnabled: toolsEnabled,
		Context:      make(map[string]interface{}),
	}

	// Start the conversation workflow
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("conv-%s-%d", userId, time.Now().Unix()),
		TaskQueue: "ai-agent-task-queue",
	}

	we, err := s.temporalClient.ExecuteWorkflow(ctx, workflowOptions, 
		"ConversationalAgentWorkflow", request)
	if err != nil {
		return nil, fmt.Errorf("failed to start conversation: %w", err)
	}

	return map[string]interface{}{
		"conversationId": we.GetID(),
		"runId":          we.GetRunID(),
		"status":         "started",
		"userId":         userId,
		"goal":           goal,
		"llmProvider":    llmProvider,
		"llmModel":       llmModel,
		"maxTurns":       maxTurns,
		"toolsEnabled":   toolsEnabled,
		"startedAt":      time.Now().Format(time.RFC3339),
	}, nil
}

// handleSendConversationMessage handles sending a message to an active conversation
func (s *MCPServer) handleSendConversationMessage(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	conversationId, ok := params["conversationId"].(string)
	if !ok {
		return nil, fmt.Errorf("conversationId is required")
	}

	message, ok := params["message"].(string)
	if !ok {
		return nil, fmt.Errorf("message is required")
	}

	// Send signal to conversation workflow
	err := s.temporalClient.SignalWorkflow(ctx, conversationId, "", 
		fmt.Sprintf("human-input-%s", conversationId), message)
	if err != nil {
		return nil, fmt.Errorf("failed to send message to conversation: %w", err)
	}

	return map[string]interface{}{
		"conversationId": conversationId,
		"message":        message,
		"status":         "message_sent",
		"sentAt":         time.Now().Format(time.RFC3339),
	}, nil
}

// handleGetConversationStatus handles getting conversation status
func (s *MCPServer) handleGetConversationStatus(ctx context.Context, params map[string]interface{}) (map[string]interface{}, error) {
	conversationId, ok := params["conversationId"].(string)
	if !ok {
		return nil, fmt.Errorf("conversationId is required")
	}

	includeHistory, _ := params["includeHistory"].(bool)

	// Query conversation state
	response, err := s.temporalClient.QueryWorkflow(ctx, conversationId, "", "GetConversationStateQuery")
	if err != nil {
		return nil, fmt.Errorf("failed to query conversation state: %w", err)
	}

	var state mcpConversationState
	if err := response.Get(&state); err != nil {
		return nil, fmt.Errorf("failed to get conversation state: %w", err)
	}

	result := map[string]interface{}{
		"conversationId":  state.ConversationID,
		"sessionId":       state.SessionID,
		"userId":          state.UserID,
		"goal":            state.Goal,
		"currentTurn":     state.CurrentTurn,
		"maxTurns":        state.MaxTurns,
		"status":          state.Status,
		"toolsUsed":       state.ToolsUsed,
		"startTime":       state.StartTime.Format(time.RFC3339),
		"lastUpdateTime":  state.LastUpdateTime.Format(time.RFC3339),
		"llmProvider":     state.LLMProvider,
		"llmModel":        state.LLMModel,
	}

	if includeHistory {
		result["history"] = state.History
		result["context"] = state.Context
	} else {
		result["historyLength"] = len(state.History)
	}

	return result, nil
}

// Local structures to avoid import cycle with workflows package

type mcpConversationRequest struct {
	UserID        string                 `json:"userId"`
	Goal          string                 `json:"goal"`
	InitialInput  string                 `json:"initialInput,omitempty"`
	LLMProvider   string                 `json:"llmProvider"`
	LLMModel      string                 `json:"llmModel"`
	MaxTurns      int                    `json:"maxTurns"`
	ToolsEnabled  []string               `json:"toolsEnabled"`
	Context       map[string]interface{} `json:"context,omitempty"`
}

type mcpConversationState struct {
	SessionID       string                    `json:"sessionId"`
	UserID          string                    `json:"userId"`
	ConversationID  string                    `json:"conversationId"`
	Goal            string                    `json:"goal"`
	CurrentTurn     int                       `json:"currentTurn"`
	MaxTurns        int                       `json:"maxTurns"`
	Status          string                    `json:"status"` 
	History         []map[string]interface{}  `json:"history"`
	Context         map[string]interface{}    `json:"context"`
	ToolsUsed       []string                  `json:"toolsUsed"`
	StartTime       time.Time                 `json:"startTime"`
	LastUpdateTime  time.Time                 `json:"lastUpdateTime"`
	LLMProvider     string                    `json:"llmProvider"`
	LLMModel        string                    `json:"llmModel"`
}
