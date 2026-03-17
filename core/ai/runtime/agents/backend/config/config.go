package config

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"
)

// Configuration management system for AI agents and workflows

// AgentConfig holds configuration for individual agents
type AgentConfig struct {
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Version         string                 `json:"version"`
	Enabled         bool                   `json:"enabled"`
	Priority        int                    `json:"priority"`
	Timeout         time.Duration          `json:"timeout"`
	MaxRetries      int                    `json:"maxRetries"`
	Parameters      map[string]interface{} `json:"parameters"`
	ScoringWeights  map[string]float64     `json:"scoringWeights"`
	Intelligence    IntelligenceConfig     `json:"intelligence"`
}

// IntelligenceConfig holds AI/ML configuration
type IntelligenceConfig struct {
	Enabled         bool    `json:"enabled"`
	ModelVersion    string  `json:"modelVersion"`
	ConfidenceThreshold float64 `json:"confidenceThreshold"`
	AutoUpdate      bool    `json:"autoUpdate"`
	TrainingData    string  `json:"trainingData"`
}

// WorkflowConfig holds configuration for workflows
type WorkflowConfig struct {
	Name            string                 `json:"name"`
	Version         string                 `json:"version"`
	Description     string                 `json:"description"`
	Enabled         bool                   `json:"enabled"`
	MaxConcurrency  int                    `json:"maxConcurrency"`
	Timeout         time.Duration          `json:"timeout"`
	RetryPolicy     RetryPolicyConfig      `json:"retryPolicy"`
	AgentConfigs    []AgentConfig          `json:"agentConfigs"`
	Parameters      map[string]interface{} `json:"parameters"`
}

// RetryPolicyConfig holds retry policy configuration
type RetryPolicyConfig struct {
	InitialInterval    time.Duration `json:"initialInterval"`
	BackoffCoefficient float64       `json:"backoffCoefficient"`
	MaximumInterval    time.Duration `json:"maximumInterval"`
	MaximumAttempts    int           `json:"maximumAttempts"`
	NonRetryableErrors []string      `json:"nonRetryableErrors"`
}

// GlobalConfig holds global system configuration
type GlobalConfig struct {
	System          SystemConfig          `json:"system"`
	Temporal        TemporalConfig        `json:"temporal"`
	Monitoring      MonitoringConfig      `json:"monitoring"`
	Security        SecurityConfig        `json:"security"`
	Agents          map[string]AgentConfig `json:"agents"`
	Workflows       []WorkflowConfig      `json:"workflows"`
}

// SystemConfig holds general system configuration
type SystemConfig struct {
	Environment     string        `json:"environment"`
	LogLevel        string        `json:"logLevel"`
	MaxConcurrency  int           `json:"maxConcurrency"`
	ShutdownTimeout time.Duration `json:"shutdownTimeout"`
	Features        map[string]bool `json:"features"`
}

// TemporalConfig holds Temporal-specific configuration
type TemporalConfig struct {
	Host             string        `json:"host"`
	Port             int           `json:"port"`
	Namespace        string        `json:"namespace"`
	TaskQueue        string        `json:"taskQueue"`
	WorkerCount      int           `json:"workerCount"`
	HeartbeatTimeout time.Duration `json:"heartbeatTimeout"`
}

// MonitoringConfig holds monitoring and metrics configuration
type MonitoringConfig struct {
	Enabled          bool          `json:"enabled"`
	MetricsInterval  time.Duration `json:"metricsInterval"`
	HealthCheckPort  int           `json:"healthCheckPort"`
	PrometheusPort   int           `json:"prometheusPort"`
	DashboardEnabled bool          `json:"dashboardEnabled"`
	AlertThresholds  AlertThresholds `json:"alertThresholds"`
}

// AlertThresholds holds alert threshold configuration
type AlertThresholds struct {
	WorkflowTimeout    time.Duration `json:"workflowTimeout"`
	AgentFailureRate   float64       `json:"agentFailureRate"`
	HighErrorRate      float64       `json:"highErrorRate"`
	CriticalScoreThreshold float64   `json:"criticalScoreThreshold"`
}

// SecurityConfig holds security-related configuration
type SecurityConfig struct {
	EncryptionEnabled  bool     `json:"encryptionEnabled"`
	APIKeyAuth         bool     `json:"apiKeyAuth"`
	AllowedIPs         []string `json:"allowedIPs"`
	AuditLogging       bool     `json:"auditLogging"`
	SecureCommunication bool    `json:"secureCommunication"`
	CertificatePath    string   `json:"certificatePath"`
	KeyPath            string   `json:"keyPath"`
}

// ConfigManager manages configuration loading and updates
type ConfigManager struct {
	config     *GlobalConfig
	configFile string
	watcher    *fsnotify.Watcher
	mu         sync.RWMutex
	callbacks  []ConfigUpdateCallback
}

// ConfigUpdateCallback is called when configuration changes
type ConfigUpdateCallback func(oldConfig, newConfig *GlobalConfig)

// NewConfigManager creates a new configuration manager
func NewConfigManager(configFile string) (*ConfigManager, error) {
	manager := &ConfigManager{
		configFile: configFile,
		callbacks:  make([]ConfigUpdateCallback, 0),
	}

	// Load initial configuration
	if err := manager.loadConfig(); err != nil {
		return nil, fmt.Errorf("failed to load initial config: %w", err)
	}

	// Set up file watcher for hot reloading
	if err := manager.setupWatcher(); err != nil {
		return nil, fmt.Errorf("failed to setup config watcher: %w", err)
	}

	return manager, nil
}

// GetConfig returns the current configuration (thread-safe)
func (cm *ConfigManager) GetConfig() *GlobalConfig {
	cm.mu.RLock()
	defer cm.mu.RUnlock()
	return cm.config
}

// GetAgentConfig returns configuration for a specific agent
func (cm *ConfigManager) GetAgentConfig(agentName string) (*AgentConfig, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	agent, exists := cm.config.Agents[agentName]
	if !exists {
		return nil, fmt.Errorf("agent %s not found in configuration", agentName)
	}

	return &agent, nil
}

// GetWorkflowConfig returns configuration for a specific workflow
func (cm *ConfigManager) GetWorkflowConfig(workflowName string) (*WorkflowConfig, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	for _, workflow := range cm.config.Workflows {
		if workflow.Name == workflowName {
			return &workflow, nil
		}
	}

	return nil, fmt.Errorf("workflow %s not found in configuration", workflowName)
}

// UpdateAgentConfig updates configuration for a specific agent
func (cm *ConfigManager) UpdateAgentConfig(agentName string, updates map[string]interface{}) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	oldConfig := cm.cloneConfig()

	agent, exists := cm.config.Agents[agentName]
	if !exists {
		return fmt.Errorf("agent %s not found in configuration", agentName)
	}

	// Apply updates to agent config
	if err := cm.applyUpdates(&agent, updates); err != nil {
		return fmt.Errorf("failed to apply updates to agent %s: %w", agentName, err)
	}

	cm.config.Agents[agentName] = agent

	// Notify callbacks
	cm.notifyCallbacks(oldConfig, cm.config)

	return nil
}

// RegisterCallback registers a callback for configuration changes
func (cm *ConfigManager) RegisterCallback(callback ConfigUpdateCallback) {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	cm.callbacks = append(cm.callbacks, callback)
}

// Close stops the configuration manager
func (cm *ConfigManager) Close() error {
	if cm.watcher != nil {
		return cm.watcher.Close()
	}
	return nil
}

// loadConfig loads configuration from file
func (cm *ConfigManager) loadConfig() error {
	data, err := os.ReadFile(cm.configFile)
	if err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}

	config := &GlobalConfig{}
	if err := json.Unmarshal(data, config); err != nil {
		return fmt.Errorf("failed to parse config file: %w", err)
	}

	// Validate configuration
	if err := cm.validateConfig(config); err != nil {
		return fmt.Errorf("invalid configuration: %w", err)
	}

	cm.config = config
	return nil
}

// setupWatcher sets up file system watcher for configuration changes
func (cm *ConfigManager) setupWatcher() error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}

	cm.watcher = watcher

	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}

				if event.Has(fsnotify.Write) && event.Name == cm.configFile {
					if err := cm.handleConfigChange(); err != nil {
						// Log error but don't crash
						fmt.Printf("Error handling config change: %v\n", err)
					}
				}

			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				fmt.Printf("Config watcher error: %v\n", err)
			}
		}
	}()

	return watcher.Add(cm.configFile)
}

// handleConfigChange handles configuration file changes
func (cm *ConfigManager) handleConfigChange() error {
	oldConfig := cm.cloneConfig()

	if err := cm.loadConfig(); err != nil {
		return fmt.Errorf("failed to reload config: %w", err)
	}

	cm.notifyCallbacks(oldConfig, cm.config)
	return nil
}

// validateConfig validates the configuration structure
func (cm *ConfigManager) validateConfig(config *GlobalConfig) error {
	if config.System.Environment == "" {
		return fmt.Errorf("system environment is required")
	}

	if config.Temporal.Host == "" {
		return fmt.Errorf("temporal host is required")
	}

	// Validate agent configurations
	for name, agent := range config.Agents {
		if agent.Name == "" {
			agent.Name = name
		}
		if agent.Type == "" {
			return fmt.Errorf("agent %s type is required", name)
		}
	}

	// Validate workflow configurations
	for _, workflow := range config.Workflows {
		if workflow.Name == "" {
			return fmt.Errorf("workflow name is required")
		}
		if len(workflow.AgentConfigs) == 0 {
			return fmt.Errorf("workflow %s must have at least one agent", workflow.Name)
		}
	}

	return nil
}

// applyUpdates applies configuration updates
func (cm *ConfigManager) applyUpdates(agent *AgentConfig, updates map[string]interface{}) error {
	// This would implement dynamic configuration updates
	// For now, we'll use a simple approach
	for key, value := range updates {
		switch key {
		case "enabled":
			if enabled, ok := value.(bool); ok {
				agent.Enabled = enabled
			}
		case "priority":
			if priority, ok := value.(float64); ok {
				agent.Priority = int(priority)
			}
		case "timeout":
			if timeout, ok := value.(string); ok {
				if duration, err := time.ParseDuration(timeout); err == nil {
					agent.Timeout = duration
				}
			}
		// Add more fields as needed
		}
	}

	return nil
}

// cloneConfig creates a deep copy of the configuration
func (cm *ConfigManager) cloneConfig() *GlobalConfig {
	data, _ := json.Marshal(cm.config)
	var cloned GlobalConfig
	json.Unmarshal(data, &cloned)
	return &cloned
}

// notifyCallbacks notifies all registered callbacks of configuration changes
func (cm *ConfigManager) notifyCallbacks(oldConfig, newConfig *GlobalConfig) {
	for _, callback := range cm.callbacks {
		go callback(oldConfig, newConfig)
	}
}

// DefaultConfig returns a default configuration
func DefaultConfig() *GlobalConfig {
	return &GlobalConfig{
		System: SystemConfig{
			Environment:     "development",
			LogLevel:        "info",
			MaxConcurrency:  10,
			ShutdownTimeout: time.Minute * 5,
			Features: map[string]bool{
				"intelligence":    true,
				"monitoring":      true,
				"security":        true,
				"autoRemediation": false,
			},
		},
		Temporal: TemporalConfig{
			Host:             "localhost",
			Port:             7233,
			Namespace:        "default",
			TaskQueue:        "ai-agent-task-queue",
			WorkerCount:      5,
			HeartbeatTimeout: time.Minute * 2,
		},
		Monitoring: MonitoringConfig{
			Enabled:          true,
			MetricsInterval:  time.Second * 30,
			HealthCheckPort:  8082,
			PrometheusPort:   9090,
			DashboardEnabled: true,
			AlertThresholds: AlertThresholds{
				WorkflowTimeout:       time.Hour * 2,
				AgentFailureRate:      0.1,
				HighErrorRate:         0.05,
				CriticalScoreThreshold: 50.0,
			},
		},
		Security: SecurityConfig{
			EncryptionEnabled:     false,
			APIKeyAuth:           false,
			AllowedIPs:           []string{},
			AuditLogging:         true,
			SecureCommunication:  false,
		},
		Agents: map[string]AgentConfig{
			"security": {
				Name:       "security",
				Type:       "Security",
				Version:    "v2.0",
				Enabled:    true,
				Priority:   1,
				Timeout:    time.Minute * 5,
				MaxRetries: 3,
				Parameters: map[string]interface{}{
					"scanDepth":     "comprehensive",
					"includeML":     true,
					"threatIntel":   true,
				},
				ScoringWeights: map[string]float64{
					"vulnerabilities": 0.4,
					"configuration":  0.3,
					"threatIntel":    0.3,
				},
				Intelligence: IntelligenceConfig{
					Enabled:             true,
					ModelVersion:        "v2.1",
					ConfidenceThreshold: 0.8,
					AutoUpdate:          true,
				},
			},
			"compliance": {
				Name:       "compliance",
				Type:       "Compliance",
				Version:    "v2.0",
				Enabled:    true,
				Priority:   1,
				Timeout:    time.Minute * 7,
				MaxRetries: 3,
				Parameters: map[string]interface{}{
					"standards":     []string{"SOC2", "GDPR", "HIPAA"},
					"autoUpdate":    true,
					"intelligence":  true,
				},
				ScoringWeights: map[string]float64{
					"controls":     0.5,
					"gaps":         0.3,
					"intelligence": 0.2,
				},
				Intelligence: IntelligenceConfig{
					Enabled:             true,
					ModelVersion:        "v2.1",
					ConfidenceThreshold: 0.85,
					AutoUpdate:          true,
				},
			},
			"cost-optimization": {
				Name:       "cost-optimization",
				Type:       "CostOptimization",
				Version:    "v2.0",
				Enabled:    true,
				Priority:   2,
				Timeout:    time.Minute * 4,
				MaxRetries: 2,
				Parameters: map[string]interface{}{
					"predictive":    true,
					"marketData":    true,
					"forecastDays":  30,
				},
				ScoringWeights: map[string]float64{
					"optimization":  0.5,
					"prediction":    0.3,
					"marketData":    0.2,
				},
				Intelligence: IntelligenceConfig{
					Enabled:             true,
					ModelVersion:        "v2.1",
					ConfidenceThreshold: 0.75,
					AutoUpdate:          true,
				},
			},
		},
		Workflows: []WorkflowConfig{
			{
				Name:           "ai-orchestration-v2",
				Version:        "v2.0",
				Description:    "Enhanced AI agent orchestration with intelligent decision making",
				Enabled:        true,
				MaxConcurrency: 5,
				Timeout:        time.Hour * 2,
				RetryPolicy: RetryPolicyConfig{
					InitialInterval:    time.Second * 5,
					BackoffCoefficient: 1.5,
					MaximumInterval:    time.Minute * 5,
					MaximumAttempts:    5,
					NonRetryableErrors: []string{"ValidationError", "AuthenticationError"},
				},
				Parameters: map[string]interface{}{
					"circuitBreakerEnabled": true,
					"intelligentReview":     true,
					"mlEnabled":            true,
				},
			},
		},
	}
}

// SaveConfig saves the current configuration to file
func (cm *ConfigManager) SaveConfig() error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	data, err := json.MarshalIndent(cm.config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(cm.configFile, data, 0644); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}
