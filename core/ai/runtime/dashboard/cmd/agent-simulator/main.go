package main

import (
	"database/sql"
	"fmt"
	"log"
	"math/rand"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

type AgentSimulator struct {
	db *sql.DB
}

func NewAgentSimulator(dbPath string) (*AgentSimulator, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &AgentSimulator{db: db}, nil
}

func (as *AgentSimulator) StartSimulation() {
	log.Println("Starting real-time agent simulation...")
	
	// Start goroutines for each agent
	go as.simulateAgentActivity("agent-1", "Memory Agent")
	go as.simulateAgentActivity("agent-2", "Temporal Agent")
	go as.simulateAgentActivity("agent-3", "Rust Agent")
	
	// Simulate skill executions
	go as.simulateSkillExecutions()
}

func (as *AgentSimulator) simulateAgentActivity(agentID, agentName string) {
	statuses := []string{"running", "idle", "errored", "stopped"}
	
	for {
		// Random status change
		newStatus := statuses[rand.Intn(len(statuses))]
		
		_, err := as.db.Exec(`
			UPDATE agents 
			SET status = $1, last_activity = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
			WHERE id = $2
		`, newStatus, agentID)
		
		if err != nil {
			log.Printf("Failed to update agent %s status: %v", agentName, err)
		} else {
			log.Printf("Agent %s status changed to: %s", agentName, newStatus)
		}
		
		// Random interval between 5-30 seconds
		time.Sleep(time.Duration(5+rand.Intn(25)) * time.Second)
	}
}

func (as *AgentSimulator) simulateSkillExecutions() {
	skills := []string{"cost-optimizer", "health-check", "security-audit", "auto-scaling", "backup-management"}
	
	for {
		// Random skill execution
		skill := skills[rand.Intn(len(skills))]
		status := "completed"
		if rand.Float32() < 0.1 { // 10% failure rate
			status = "failed"
		}
		
		_, err := as.db.Exec(`
			INSERT INTO agent_executions (agent_id, skill_name, status, started_at, completed_at)
			VALUES (
				(SELECT id FROM agents ORDER BY RANDOM() LIMIT 1),
				$1,
				$2,
				DATETIME('now', '-5 minutes'),
				CURRENT_TIMESTAMP
			)
		`, skill, status)
		
		if err != nil {
			log.Printf("Failed to record skill execution: %v", err)
		} else {
			log.Printf("Skill execution recorded: %s - %s", skill, status)
		}
		
		// Random interval between 10-60 seconds
		time.Sleep(time.Duration(10+rand.Intn(50)) * time.Second)
	}
}

func (as *AgentSimulator) Close() error {
	return as.db.Close()
}

func main() {
	simulator, err := NewAgentSimulator("/tmp/dashboard.db")
	if err != nil {
		log.Fatal(err)
	}
	defer simulator.Close()
	
	simulator.StartSimulation()
	
	// Keep running
	select {}
}
