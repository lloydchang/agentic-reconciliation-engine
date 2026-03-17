package models

import (
	"time"
)

type Agent struct {
	ID           string    `json:"id" db:"id"`
	Name         string    `json:"name" db:"name"`
	Language     string    `json:"language" db:"language"`     // rust, go, python
	Status       string    `json:"status" db:"status"`       // running, idle, error
	Backend      string    `json:"backend" db:"backend"`      // llama-cpp, ollama
	Skills       []string  `json:"skills" db:"skills"`
	LastActivity *time.Time `json:"lastActivity" db:"last_activity"`
	SuccessRate  float64   `json:"successRate" db:"success_rate"`
	CreatedAt    time.Time `json:"createdAt" db:"created_at"`
	UpdatedAt    time.Time `json:"updatedAt" db:"updated_at"`
}

type AgentStatus string

const (
	AgentStatusRunning AgentStatus = "running"
	AgentStatusIdle    AgentStatus = "idle"
	AgentStatusError   AgentStatus = "error"
	AgentStatusStopped AgentStatus = "stopped"
)

type AgentLanguage string

const (
	AgentLanguageRust   AgentLanguage = "rust"
	AgentLanguageGo     AgentLanguage = "go"
	AgentLanguagePython AgentLanguage = "python"
)

type AgentBackend string

const (
	AgentBackendLlamaCPP AgentBackend = "llama-cpp"
	AgentBackendOllama   AgentBackend = "ollama"
)
