package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "sync"
    "time"

    "github.com/hashicorp/consensus"
)

type AgentRegistration struct {
    ID       string `json:"id"`
    Type     string `json:"type"`
    Status   string `json:"status"`
    Endpoint string `json:"endpoint"`
}

type HealthResponse struct {
    Status  string `json:"status"`
    Version string `json:"version"`
    Agents  []AgentRegistration `json:"agents"`
}

var (
    registeredAgents = make(map[string]AgentRegistration)
    consensus       *consensus.Consensus
    agentCounter    int64 = 0
)

func main() {
    log.Printf("🐝 Agent Swarm Coordinator Starting...")
    
    // Initialize Raft consensus
    consensus, err := consensus.NewConsensus(
        consensus.WithID("swarm-coordinator"),
        consensus.WithStorage(consensus.NewInmemStorage()),
        consensus.WithPeers(),
    )
    if err != nil {
        log.Fatalf("Failed to initialize consensus: %v", err)
    }
    
    go runConsensus(consensus)
    
    // Set up HTTP server
    http.HandleFunc("/register", registerAgentHandler)
    http.HandleFunc("/health", healthHandler)
    http.HandleFunc("/agents", listAgentsHandler)
    
    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }
    
    log.Printf("✅ Swarm Coordinator ready on port %s", port)
    log.Fatal(http.ListenAndServe(":"+port, nil))
}

func runConsensus(c *consensus.Consensus) {
    for {
        select {
        case <-c.LeaderCh():
            log.Printf("👑 Became leader, coordinating agents")
        case <-c.ObserveCh():
            log.Printf("👀 Observing consensus changes")
        case <-c.ErrorCh():
            log.Printf("❌ Consensus error: %v", <-c.ErrorCh())
        }
    }
}

func registerAgentHandler(w http.ResponseWriter, r *http.Request) {
    log.Printf("📝 Agent registration request")
    
    var req struct {
        ID      string `json:"id"`
        Type    string `json:"type"`
        Endpoint string `json:"endpoint"`
    }
    
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    // Register agent in consensus
    agent := AgentRegistration{
        ID:       req.ID,
        Type:     req.Type,
        Status:   "active",
        Endpoint: req.Endpoint,
    }
    
    registeredAgents[req.ID] = agent
    agentCounter++
    
    // Propagate to consensus
    if consensus != nil {
        // In real implementation, this would update consensus state
        log.Printf("✅ Registered agent %s (%s)", req.ID, req.Type)
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(agent)
    
    log.Printf("📊 Total registered agents: %d", agentCounter)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    response := HealthResponse{
        Status:  "healthy",
        Version: "1.0.0",
        Agents:  getRegisteredAgents(),
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func listAgentsHandler(w http.ResponseWriter, r *http.Request) {
    response := HealthResponse{
        Status:  "healthy",
        Version: "1.0.0",
        Agents:  getRegisteredAgents(),
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func getRegisteredAgents() []AgentRegistration {
    agents := make([]AgentRegistration, 0, len(registeredAgents))
    i := 0
    for _, agent := range registeredAgents {
        agents[i] = agent
        i++
    }
    return agents
}
