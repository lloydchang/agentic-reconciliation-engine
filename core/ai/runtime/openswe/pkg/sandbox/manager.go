package sandbox

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
)

// SandboxProvider defines the interface for different sandbox providers
type SandboxProvider interface {
	CreateEnvironment(ctx context.Context, config SandboxConfig) (*Environment, error)
	ExecuteCommand(ctx context.Context, envID string, cmd Command) (*Result, error)
	DestroyEnvironment(ctx context.Context, envID string) error
	GetLogs(ctx context.Context, envID string) ([]LogEntry, error)
	GetStatus(ctx context.Context, envID string) (EnvironmentStatus, error)
}

// SandboxConfig defines the configuration for sandbox environments
type SandboxConfig struct {
	Provider    string            `json:"provider"`
	Image       string            `json:"image,omitempty"`
	Resources   ResourceSpec      `json:"resources,omitempty"`
	Timeout     time.Duration     `json:"timeout,omitempty"`
	Environment map[string]string `json:"environment,omitempty"`
	WorkingDir  string            `json:"working_dir,omitempty"`
	NetworkAccess bool            `json:"network_access,omitempty"`
}

// ResourceSpec defines resource requirements for sandbox environments
type ResourceSpec struct {
	CPU    string `json:"cpu,omitempty"`
	Memory string `json:"memory,omitempty"`
	GPU    string `json:"gpu,omitempty"`
	Disk   string `json:"disk,omitempty"`
}

// Environment represents a sandbox environment
type Environment struct {
	ID          string            `json:"id"`
	Provider    string            `json:"provider"`
	Status      EnvironmentStatus `json:"status"`
	CreatedAt   time.Time         `json:"created_at"`
	Config      SandboxConfig     `json:"config"`
	Endpoint    string            `json:"endpoint,omitempty"`
	AccessToken string            `json:"access_token,omitempty"`
}

// EnvironmentStatus represents the status of a sandbox environment
type EnvironmentStatus string

const (
	StatusCreating  EnvironmentStatus = "creating"
	StatusRunning   EnvironmentStatus = "running"
	StatusFailed    EnvironmentStatus = "failed"
	StatusDestroyed EnvironmentStatus = "destroyed"
)

// Command represents a command to execute in the sandbox
type Command struct {
	Cmd       string            `json:"cmd"`
	Args      []string          `json:"args,omitempty"`
	Env       map[string]string `json:"env,omitempty"`
	WorkingDir string           `json:"working_dir,omitempty"`
	Timeout   time.Duration     `json:"timeout,omitempty"`
	Stdin     string            `json:"stdin,omitempty"`
}

// Result represents the result of command execution
type Result struct {
	ExitCode int               `json:"exit_code"`
	Stdout   string            `json:"stdout"`
	Stderr   string            `json:"stderr"`
	Duration time.Duration     `json:"duration"`
	Error    error             `json:"error,omitempty"`
}

// LogEntry represents a log entry from the sandbox
type LogEntry struct {
	Timestamp time.Time `json:"timestamp"`
	Level     string    `json:"level"`
	Message   string    `json:"message"`
	Source    string    `json:"source,omitempty"`
}

// SandboxManager manages sandbox environments across different providers
type SandboxManager struct {
	providers map[string]SandboxProvider
	config    *config.Config
}

// NewSandboxManager creates a new sandbox manager
func NewSandboxManager(cfg *config.Config) *SandboxManager {
	sm := &SandboxManager{
		providers: make(map[string]SandboxProvider),
		config:    cfg,
	}

	// Initialize providers based on configuration
	if cfg.Sandbox.Modal.Enabled {
		sm.providers["modal"] = NewModalProvider(cfg.Sandbox.Modal)
	}
	if cfg.Sandbox.Daytona.Enabled {
		sm.providers["daytona"] = NewDaytonaProvider(cfg.Sandbox.Daytona)
	}
	if cfg.Sandbox.Runloop.Enabled {
		sm.providers["runloop"] = NewRunloopProvider(cfg.Sandbox.Runloop)
	}
	if cfg.Sandbox.LangSmith.Enabled {
		sm.providers["langsmith"] = NewLangSmithProvider(cfg.Sandbox.LangSmith)
	}
	if cfg.Sandbox.AgentSandbox.Enabled {
		provider, err := NewAgentSandboxProvider(cfg.Sandbox.AgentSandbox)
		if err != nil {
			log.Printf("Failed to initialize Agent Sandbox provider: %v", err)
		} else {
			sm.providers["agent-sandbox"] = provider
		}
	}

	return sm
}

// CreateEnvironment creates a new sandbox environment
func (sm *SandboxManager) CreateEnvironment(ctx context.Context, provider string, config SandboxConfig) (*Environment, error) {
	p, exists := sm.providers[provider]
	if !exists {
		return nil, fmt.Errorf("provider %s not configured", provider)
	}

	return p.CreateEnvironment(ctx, config)
}

// ExecuteCommand executes a command in the specified environment
func (sm *SandboxManager) ExecuteCommand(ctx context.Context, provider, envID string, cmd Command) (*Result, error) {
	p, exists := sm.providers[provider]
	if !exists {
		return nil, fmt.Errorf("provider %s not configured", provider)
	}

	return p.ExecuteCommand(ctx, envID, cmd)
}

// DestroyEnvironment destroys the specified environment
func (sm *SandboxManager) DestroyEnvironment(ctx context.Context, provider, envID string) error {
	p, exists := sm.providers[provider]
	if !exists {
		return fmt.Errorf("provider %s not configured", provider)
	}

	return p.DestroyEnvironment(ctx, envID)
}

// GetLogs retrieves logs from the specified environment
func (sm *SandboxManager) GetLogs(ctx context.Context, provider, envID string) ([]LogEntry, error) {
	p, exists := sm.providers[provider]
	if !exists {
		return nil, fmt.Errorf("provider %s not configured", provider)
	}

	return p.GetLogs(ctx, envID)
}

// GetStatus retrieves the status of the specified environment
func (sm *SandboxManager) GetStatus(ctx context.Context, provider, envID string) (EnvironmentStatus, error) {
	p, exists := sm.providers[provider]
	if !exists {
		return "", fmt.Errorf("provider %s not configured", provider)
	}

	return p.GetStatus(ctx, envID)
}
