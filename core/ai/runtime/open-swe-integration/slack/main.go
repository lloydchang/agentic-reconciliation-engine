package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
	"go.temporal.io/sdk/client"
	"gopkg.in/yaml.v3"
)

// Config represents the application configuration
type Config struct {
	Slack SlackConfig `yaml:"slack"`
	Temporal TemporalConfig `yaml:"temporal"`
	MemoryAgent MemoryAgentConfig `yaml:"memory_agent"`
	Monitoring MonitoringConfig `yaml:"monitoring"`
	Security SecurityConfig `yaml:"security"`
	FeatureFlags FeatureFlags `yaml:"feature_flags"`
}

type SlackConfig struct {
	BotName     string `yaml:"bot_name"`
	BotIcon     string `yaml:"bot_icon"`
	CommandPrefix string `yaml:"command_prefix"`
	Commands    map[string]CommandConfig `yaml:"commands"`
}

type CommandConfig struct {
	Skill       string                 `yaml:"skill"`
	Description string                 `yaml:"description"`
	Parameters  []ParameterConfig      `yaml:"parameters"`
}

type ParameterConfig struct {
	Name     string   `yaml:"name"`
	Type     string   `yaml:"type"`
	Required bool     `yaml:"required"`
	Default  string   `yaml:"default"`
	Options  []string `yaml:"options"`
}

type TemporalConfig struct {
	Host           string `yaml:"host"`
	TaskQueue      string `yaml:"task_queue"`
	WorkflowTimeout string `yaml:"workflow_timeout"`
	ActivityTimeout string `yaml:"activity_timeout"`
}

type MemoryAgentConfig struct {
	URL           string `yaml:"url"`
	ContextTTL    string `yaml:"context_ttl"`
	MaxContextSize string `yaml:"max_context_size"`
}

type MonitoringConfig struct {
	MetricsPort string `yaml:"metrics_port"`
	HealthPort  string `yaml:"health_port"`
	LogLevel    string `yaml:"log_level"`
}

type SecurityConfig struct {
	MaxRequestSize      string `yaml:"max_request_size"`
	RateLimitPerMinute  int    `yaml:"rate_limit_per_minute"`
	SignatureValidation bool   `yaml:"signature_validation"`
	TimestampValidation bool   `yaml:"timestamp_validation"`
}

type FeatureFlags struct {
	EnableLinearIntegration     bool `yaml:"enable_linear_integration"`
	EnableSubagentParallelism   bool `yaml:"enable_subagent_parallelism"`
	EnableMiddlewareHooks       bool `yaml:"enable_middleware_hooks"`
	EnableContextEnhancement    bool `yaml:"enable_context_enhancement"`
	EnableAdvancedNLP           bool `yaml:"enable_advanced_nlp"`
}

// SlackIntegration handles the main application
type SlackIntegration struct {
	config         Config
	slackHandler   *SlackHandler
	temporalClient client.Client
	logger         *logrus.Logger
}

// NewSlackIntegration creates a new Slack integration instance
func NewSlackIntegration() (*SlackIntegration, error) {
	// Load configuration
	config, err := loadConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to load config: %w", err)
	}

	// Setup logger
	logger := logrus.New()
	level, err := logrus.ParseLevel(config.Monitoring.LogLevel)
	if err != nil {
		level = logrus.InfoLevel
	}
	logger.SetLevel(level)

	// Create Temporal client
	temporalClient, err := client.Dial(client.Options{
		HostPort: config.Temporal.Host,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create Temporal client: %w", err)
	}

	// Create Slack handler
	slackHandler, err := NewSlackHandler(config, temporalClient, logger)
	if err != nil {
		return nil, fmt.Errorf("failed to create Slack handler: %w", err)
	}

	return &SlackIntegration{
		config:       config,
		slackHandler: slackHandler,
		temporalClient: temporalClient,
		logger:       logger,
	}, nil
}

// loadConfig loads configuration from file and environment
func loadConfig() (Config, error) {
	var config Config

	// Load from file if exists
	if data, err := os.ReadFile("/app/config.yaml"); err == nil {
		if err := yaml.Unmarshal(data, &config); err != nil {
			return config, fmt.Errorf("failed to parse config file: %w", err)
		}
	}

	// Override with environment variables
	if port := os.Getenv("PORT"); port != "" {
		config.Monitoring.MetricsPort = port
	}
	if botToken := os.Getenv("SLACK_BOT_TOKEN"); botToken != "" {
		// This will be handled by the Slack handler
	}
	if signingSecret := os.Getenv("SLACK_SIGNING_SECRET"); signingSecret != "" {
		// This will be handled by the Slack handler
	}

	return config, nil
}

// Start starts the Slack integration service
func (si *SlackIntegration) Start() error {
	router := mux.NewRouter()

	// Health endpoints
	router.HandleFunc("/health", si.healthHandler).Methods("GET")
	router.HandleFunc("/ready", si.readyHandler).Methods("GET")
	router.HandleFunc("/metrics", promhttp.Handler().ServeHTTP).Methods("GET")

	// Slack webhook endpoint
	router.HandleFunc("/webhooks/slack", si.slackHandler.HandleWebhook).Methods("POST")

	// Create HTTP server
	port := ":" + si.config.Monitoring.MetricsPort
	server := &http.Server{
		Addr:         port,
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	si.logger.Infof("Starting Slack integration on port %s", port)

	// Start server in goroutine
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			si.logger.Fatalf("Server failed to start: %v", err)
		}
	}()

	return nil
}

// healthHandler handles health check requests
func (si *SlackIntegration) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":    "healthy",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"version":   "v1.0.0",
	})
}

// readyHandler handles readiness check requests
func (si *SlackIntegration) readyHandler(w http.ResponseWriter, r *http.Request) {
	// Check if Temporal client is connected
	if si.temporalClient == nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not ready",
			"reason": "Temporal client not connected",
		})
		return
	}

	// Check Slack configuration
	if os.Getenv("SLACK_BOT_TOKEN") == "" || os.Getenv("SLACK_SIGNING_SECRET") == "" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not ready",
			"reason": "Slack credentials not configured",
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":    "ready",
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	})
}

// Shutdown gracefully shuts down the service
func (si *SlackIntegration) Shutdown(ctx context.Context) error {
	si.logger.Info("Shutting down Slack integration")

	// Close Temporal client
	if si.temporalClient != nil {
		if err := si.temporalClient.Close(); err != nil {
			si.logger.Errorf("Failed to close Temporal client: %v", err)
		}
	}

	si.logger.Info("Slack integration shutdown complete")
	return nil
}

func main() {
	// Create Slack integration
	integration, err := NewSlackIntegration()
	if err != nil {
		log.Fatalf("Failed to create Slack integration: %v", err)
	}

	// Start the service
	if err := integration.Start(); err != nil {
		log.Fatalf("Failed to start Slack integration: %v", err)
	}

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := integration.Shutdown(ctx); err != nil {
		log.Printf("Error during shutdown: %v", err)
	}
}
