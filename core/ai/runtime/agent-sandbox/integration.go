package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/sandbox"
)

// AgentIntegrator integrates Agent Sandbox with existing agent execution methods
type AgentIntegrator struct {
	executor      *Executor
	sandboxMgr    *sandbox.SandboxManager
	config        *config.AgentSandboxConfig
	temporalInt   *TemporalIntegrator
	piMonoInt     *PiMonoIntegrator
	memoryInt     *MemoryIntegrator
}

// TemporalIntegrator integrates with Temporal workflows
type TemporalIntegrator struct {
	executor *Executor
}

// PiMonoIntegrator integrates with Pi-Mono RPC agents
type PiMonoIntegrator struct {
	executor *Executor
}

// MemoryIntegrator integrates with Memory agents
type MemoryIntegrator struct {
	executor *Executor
}

// NewAgentIntegrator creates a new agent integrator
func NewAgentIntegrator(sandboxMgr *sandbox.SandboxManager, config *config.AgentSandboxConfig) *AgentIntegrator {
	executor := NewExecutor(sandboxMgr, config)
	
	return &AgentIntegrator{
		executor:   executor,
		sandboxMgr: sandboxMgr,
		config:     config,
		temporalInt: &TemporalIntegrator{executor: executor},
		piMonoInt:   &PiMonoIntegrator{executor: executor},
		memoryInt:   &MemoryIntegrator{executor: executor},
	}
}

// ExecuteInTemporal executes code in Agent Sandbox from Temporal workflow
func (ti *TemporalIntegrator) ExecuteInTemporal(ctx context.Context, workflowID, activityID, code string) (*ExecutionResult, error) {
	log.Printf("Executing code in Agent Sandbox from Temporal workflow %s, activity %s", workflowID, activityID)

	request := &ExecutionRequest{
		AgentID:   fmt.Sprintf("temporal-%s-%s", workflowID, activityID),
		AgentType: "temporal",
		Code:      code,
		Language:  "python", // Default to Python for Temporal
		Timeout:   ti.executor.config.Timeout,
		Metadata: map[string]interface{}{
			"workflow_id":  workflowID,
			"activity_id":  activityID,
			"execution_id": fmt.Sprintf("%s-%d", activityID, time.Now().Unix()),
		},
	}

	return ti.executor.Execute(ctx, request)
}

// ExecuteInPiMono executes code in Agent Sandbox from Pi-Mono agent
func (pmi *PiMonoIntegrator) ExecuteInPiMono(ctx context.Context, sessionID, skillName, code string) (*ExecutionResult, error) {
	log.Printf("Executing code in Agent Sandbox from Pi-Mono session %s, skill %s", sessionID, skillName)

	request := &ExecutionRequest{
		AgentID:   fmt.Sprintf("pi-mono-%s-%s", sessionID, skillName),
		AgentType: "pi-mono",
		Code:      code,
		Language:  detectLanguage(code),
		Timeout:   pmi.executor.config.Timeout,
		Metadata: map[string]interface{}{
			"session_id":   sessionID,
			"skill_name":    skillName,
			"execution_id":  fmt.Sprintf("%s-%d", skillName, time.Now().Unix()),
		},
	}

	return pmi.executor.Execute(ctx, request)
}

// ExecuteInMemory executes code in Agent Sandbox from Memory agent
func (mi *MemoryIntegrator) ExecuteInMemory(ctx context.Context, memoryID, query, code string) (*ExecutionResult, error) {
	log.Printf("Executing code in Agent Sandbox from Memory agent %s", memoryID)

	request := &ExecutionRequest{
		AgentID:   fmt.Sprintf("memory-%s", memoryID),
		AgentType: "memory",
		Code:      code,
		Language:  detectLanguage(code),
		Timeout:   mi.executor.config.Timeout,
		Metadata: map[string]interface{}{
			"memory_id":    memoryID,
			"query":        query,
			"execution_id": fmt.Sprintf("memory-%d", time.Now().Unix()),
		},
	}

	return mi.executor.Execute(ctx, request)
}

// ExecuteSkill executes a skill in Agent Sandbox
func (ai *AgentIntegrator) ExecuteSkill(ctx context.Context, skillName, agentType, code string, resources sandbox.ResourceSpec) (*ExecutionResult, error) {
	log.Printf("Executing skill %s in Agent Sandbox for agent type %s", skillName, agentType)

	// Determine template based on skill requirements
	template := ai.selectTemplateForSkill(skillName, agentType)

	request := &ExecutionRequest{
		AgentID:   fmt.Sprintf("%s-%s", agentType, skillName),
		AgentType: agentType,
		Code:      code,
		Language:  detectLanguage(code),
		Template:  template,
		Resources: resources,
		Timeout:   ai.config.Timeout,
		Metadata: map[string]interface{}{
			"skill_name":   skillName,
			"execution_id": fmt.Sprintf("%s-%d", skillName, time.Now().Unix()),
		},
	}

	return ai.executor.Execute(ctx, request)
}

// selectTemplateForSkill selects appropriate template based on skill and agent type
func (ai *AgentIntegrator) selectTemplateForSkill(skillName, agentType string) string {
	// Logic to select template based on skill requirements
	switch agentType {
	case "temporal":
		// Temporal workflows typically use Python
		return "python-runtime-template"
	case "pi-mono":
		// Pi-Mono agents may use various languages
		return "python-runtime-template" // Default
	case "memory":
		// Memory agents typically use Python
		return "python-runtime-template"
	default:
		return ai.config.DefaultTemplate
	}
}

// GetExecutor returns the executor instance
func (ai *AgentIntegrator) GetExecutor() *Executor {
	return ai.executor
}

// GetTemporalIntegrator returns the Temporal integrator
func (ai *AgentIntegrator) GetTemporalIntegrator() *TemporalIntegrator {
	return ai.temporalInt
}

// GetPiMonoIntegrator returns the Pi-Mono integrator
func (ai *AgentIntegrator) GetPiMonoIntegrator() *PiMonoIntegrator {
	return ai.piMonoInt
}

// GetMemoryIntegrator returns the Memory integrator
func (ai *AgentIntegrator) GetMemoryIntegrator() *MemoryIntegrator {
	return ai.memoryInt
}

// detectLanguage detects the programming language from code
func detectLanguage(code string) string {
	// Simple language detection based on code content
	if contains(code, []string{"import ", "def ", "print(", "python"}) {
		return "python"
	}
	if contains(code, []string{"#!/bin/bash", "echo ", "export ", "bash"}) {
		return "bash"
	}
	if contains(code, []string{"func ", "package ", "import\"", "go run"}) {
		return "go"
	}
	if contains(code, []string{"console.log", "const ", "let ", "require("}) {
		return "javascript"
	}
	
	// Default to bash
	return "bash"
}

// contains checks if code contains any of the patterns
func contains(code string, patterns []string) bool {
	for _, pattern := range patterns {
		if len(code) > len(pattern) {
			// Simple substring check
			for i := 0; i <= len(code)-len(pattern); i++ {
				if code[i:i+len(pattern)] == pattern {
					return true
				}
			}
		}
	}
	return false
}

// Initialize initializes the agent integrator
func (ai *AgentIntegrator) Initialize(ctx context.Context) error {
	log.Printf("Initializing Agent Sandbox integrator")

	// Initialize templates and warm pools
	for _, template := range ai.executor.templates {
		if err := template.Create(ctx); err != nil {
			log.Printf("Failed to create template %s: %v", template.GetSpec().Name, err)
			// Continue with other templates
		}
	}

	for _, pool := range ai.executor.warmPools {
		if err := pool.Create(ctx); err != nil {
			log.Printf("Failed to create warm pool %s: %v", pool.GetSpec().Name, err)
			// Continue with other pools
		}
	}

	// Initialize monitoring
	if ai.config.Kubeconfig != nil {
		if err := ai.executor.monitoring.InitializeMetricsClient(ai.config.Kubeconfig); err != nil {
			log.Printf("Failed to initialize metrics client: %v", err)
			// Continue without metrics
		}
	}

	log.Printf("Agent Sandbox integrator initialized successfully")
	return nil
}

// Cleanup cleans up the agent integrator
func (ai *AgentIntegrator) Cleanup(ctx context.Context) error {
	log.Printf("Cleaning up Agent Sandbox integrator")

	// Cleanup executor
	if err := ai.executor.Cleanup(ctx); err != nil {
		log.Printf("Error during executor cleanup: %v", err)
	}

	log.Printf("Agent Sandbox integrator cleanup completed")
	return nil
}
