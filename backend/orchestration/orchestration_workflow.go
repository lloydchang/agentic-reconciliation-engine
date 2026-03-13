package orchestration

import (
	"fmt"
	"time"

	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
	"go.temporal.io/sdk/workflow"
)

// OrchestrationAgentType represents different types of orchestration agents
type OrchestrationAgentType string

const (
	OrchestrationAgentTypeSimple    OrchestrationAgentType = "simple"
	OrchestrationAgentTypeToolBased OrchestrationAgentType = "tool_based"
	OrchestrationAgentTypeResearch  OrchestrationAgentType = "research"
	OrchestrationAgentTypeMultiAgent OrchestrationAgentType = "multi_agent"
)

// OrchestrationWorkflowRequest represents the input for orchestration workflows
type OrchestrationWorkflowRequest struct {
	UserID          string                 `json:"user_id"`
	Query           string                 `json:"query"`
	AgentType       OrchestrationAgentType `json:"agent_type"`
	MaxSteps        int                    `json:"max_steps,omitempty"`
	Context         map[string]interface{} `json:"context,omitempty"`
	AllowedTools    []string              `json:"allowed_tools,omitempty"`
	ResearchDepth   string                 `json:"research_depth,omitempty"`
	InteractiveMode bool                   `json:"interactive_mode"`
}

// OrchestrationWorkflowResponse represents the output from orchestration workflows
type OrchestrationWorkflowResponse struct {
	UserID         string                 `json:"user_id"`
	Query          string                 `json:"query"`
	Response       string                 `json:"response"`
	AgentType      OrchestrationAgentType `json:"agent_type"`
	Steps          []OrchestrationStep    `json:"steps"`
	ToolCalls      []ToolExecution        `json:"tool_calls"`
	ProcessingTime time.Duration          `json:"processing_time"`
	Status         string                 `json:"status"`
}

// OrchestrationStep represents a single step in the orchestration process
type OrchestrationStep struct {
	StepNumber     int                    `json:"step_number"`
	AgentName      string                 `json:"agent_name"`
	Action         string                 `json:"action"`
	Input          interface{}            `json:"input"`
	Output         interface{}            `json:"output"`
	ToolCalls      []ToolExecution        `json:"tool_calls,omitempty"`
	Duration       time.Duration          `json:"duration"`
	Timestamp      time.Time              `json:"timestamp"`
}

// ToolExecution represents a tool call execution
type ToolExecution struct {
	ToolName   string                 `json:"tool_name"`
	Parameters map[string]interface{} `json:"parameters"`
	Result     interface{}            `json:"result"`
	Error      string                 `json:"error,omitempty"`
	Duration   time.Duration          `json:"duration"`
}

// OrchestrationWorkflow implements the main orchestration logic
type OrchestrationWorkflow struct {
	mcpRegistry *mcp.MCPRegistry
}

// NewOrchestrationWorkflow creates a new orchestration workflow
func NewOrchestrationWorkflow() *OrchestrationWorkflow {
	return &OrchestrationWorkflow{
		mcpRegistry: mcp.GetGlobalMCPRegistry(),
	}
}

// OrchestrationWorkflow executes the main orchestration logic
func (w *OrchestrationWorkflow) OrchestrationWorkflow(ctx workflow.Context, req OrchestrationWorkflowRequest) (*OrchestrationWorkflowResponse, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting orchestration workflow",
		"userId", req.UserID,
		"query", req.Query,
		"agentType", req.AgentType)

	startTime := time.Now()
	steps := []OrchestrationStep{}
	toolCalls := []ToolExecution{}

	// Set defaults
	if req.MaxSteps == 0 {
		req.MaxSteps = 10
	}

	// Route to appropriate agent based on type
	var response string
	var err error

	switch req.AgentType {
	case OrchestrationAgentTypeSimple:
		response, err = w.executeSimpleAgent(ctx, req, &steps, &toolCalls)
	case OrchestrationAgentTypeToolBased:
		response, err = w.executeToolBasedAgent(ctx, req, &steps, &toolCalls)
	case OrchestrationAgentTypeResearch:
		response, err = w.executeResearchAgent(ctx, req, &steps, &toolCalls)
	case OrchestrationAgentTypeMultiAgent:
		response, err = w.executeMultiAgent(ctx, req, &steps, &toolCalls)
	default:
		return nil, fmt.Errorf("unsupported agent type: %s", req.AgentType)
	}

	if err != nil {
		logger.Error("Orchestration workflow failed", "error", err)
		return &OrchestrationWorkflowResponse{
			UserID:         req.UserID,
			Query:          req.Query,
			Response:       fmt.Sprintf("Error: %v", err),
			AgentType:      req.AgentType,
			Steps:          steps,
			ToolCalls:      toolCalls,
			ProcessingTime: time.Since(startTime),
			Status:         "error",
		}, nil
	}

	logger.Info("Orchestration workflow completed successfully",
		"userId", req.UserID,
		"agentType", req.AgentType,
		"steps", len(steps),
		"toolCalls", len(toolCalls))

	return &OrchestrationWorkflowResponse{
		UserID:         req.UserID,
		Query:          req.Query,
		Response:       response,
		AgentType:      req.AgentType,
		Steps:          steps,
		ToolCalls:      toolCalls,
		ProcessingTime: time.Since(startTime),
		Status:         "completed",
	}, nil
}
