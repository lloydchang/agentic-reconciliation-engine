package config

import (
	"os"
	"strconv"

	"github.com/spf13/viper"
)

type Config struct {
	Port           int
	DatabaseURL    string
	TemporalAddress string
	MemoryAgentURL string
	BackendPriority string
	LanguagePriority string
	Environment    string
	Version        string
}

func Load() (*Config, error) {
	// Set defaults
	viper.SetDefault("port", 8081)
	viper.SetDefault("database_url", "postgres://dashboard_user:password@localhost:5432/ai_agents_dashboard?sslmode=disable")
	viper.SetDefault("temporal_address", "temporal-frontend.ai-infrastructure.svc.cluster.local:7233")
	viper.SetDefault("memory_agent_url", "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080")
	viper.SetDefault("backend_priority", "llama-cpp,ollama")
	viper.SetDefault("language_priority", "rust,go,python")
	viper.SetDefault("environment", "development")
	viper.SetDefault("version", "1.0.0")

	// Read from environment variables
	viper.AutomaticEnv()

	// Bind environment variables
	viper.BindEnv("port", "PORT")
	viper.BindEnv("database_url", "DATABASE_URL")
	viper.BindEnv("temporal_address", "TEMPORAL_ADDRESS")
	viper.BindEnv("memory_agent_url", "MEMORY_AGENT_URL")
	viper.BindEnv("backend_priority", "BACKEND_PRIORITY")
	viper.BindEnv("language_priority", "LANGUAGE_PRIORITY")
	viper.BindEnv("environment", "ENVIRONMENT")
	viper.BindEnv("version", "VERSION")

	config := &Config{
		Port:            viper.GetInt("port"),
		DatabaseURL:     viper.GetString("database_url"),
		TemporalAddress: viper.GetString("temporal_address"),
		MemoryAgentURL:  viper.GetString("memory_agent_url"),
		BackendPriority: viper.GetString("backend_priority"),
		LanguagePriority: viper.GetString("language_priority"),
		Environment:     viper.GetString("environment"),
		Version:         viper.GetString("version"),
	}

	// Override with command line arguments if provided
	if port := os.Getenv("PORT"); port != "" {
		if p, err := strconv.Atoi(port); err == nil {
			config.Port = p
		}
	}
	if dbURL := os.Getenv("DATABASE_URL"); dbURL != "" {
		config.DatabaseURL = dbURL
	}
	if temporalAddr := os.Getenv("TEMPORAL_ADDRESS"); temporalAddr != "" {
		config.TemporalAddress = temporalAddr
	}
	if memoryAgentURL := os.Getenv("MEMORY_AGENT_URL"); memoryAgentURL != "" {
		config.MemoryAgentURL = memoryAgentURL
	}
	if backendPriority := os.Getenv("BACKEND_PRIORITY"); backendPriority != "" {
		config.BackendPriority = backendPriority
	}
	if languagePriority := os.Getenv("LANGUAGE_PRIORITY"); languagePriority != "" {
		config.LanguagePriority = languagePriority
	}
	if env := os.Getenv("ENVIRONMENT"); env != "" {
		config.Environment = env
	}
	if version := os.Getenv("VERSION"); version != "" {
		config.Version = version
	}

	return config, nil
}
