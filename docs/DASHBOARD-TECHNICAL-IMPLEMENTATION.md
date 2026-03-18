# Dashboard Technical Implementation Guide

## Architecture Overview

The AI Agents Dashboard consists of three main components:

1. **Frontend (React)** - Web interface for displaying metrics
2. **Backend (Go/Gin)** - API server for data processing
3. **Database (SQLite)** - Data persistence layer

## Component Details

### Frontend Architecture

#### Technology Stack
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Axios** - HTTP client
- **CSS Modules** - Styling

#### Key Components
```
src/
├── components/
│   ├── Dashboard/
│   │   ├── SystemOverview.tsx    # Main metrics display
│   │   ├── AgentList.tsx         # Agent management
│   │   └── SkillMetrics.tsx      # Skill statistics
│   ├── Layout/
│   │   ├── Header.tsx            # Navigation
│   │   └── Sidebar.tsx           # Menu
│   └── Charts/
│       ├── AgentStatusChart.tsx  # Agent status visualization
│       └── SkillExecutionChart.tsx # Skill metrics
├── services/
│   └── api.ts                    # API client
├── types/
│   └── index.ts                  # TypeScript interfaces
└── utils/
    └── formatters.ts             # Data formatting utilities
```

#### API Integration
```typescript
interface ApiService {
  getSystemMetrics(): Promise<SystemMetrics>;
  getAgents(): Promise<Agent[]>;
  getSkills(): Promise<Skill[]>;
  getActivities(): Promise<Activity[]>;
}

class ApiService {
  private baseURL = `${API_BASE_URL}/api/v1`;
  
  async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await axios.get(`${this.baseURL}/system/metrics`);
    return response.data;
  }
}
```

### Backend Architecture

#### Technology Stack
- **Go 1.21+** - Backend language
- **Gin Web Framework** - HTTP router
- **SQLite** - Database (development)
- **Zap** - Structured logging
- **GORM** - ORM (optional)

#### Project Structure
```
cmd/
├── server/
│   └── main.go                    # Application entry point
└── agent-simulator/
    └── main.go                    # Real-time data generator

internal/
├── api/
│   ├── handler.go                 # HTTP handlers
│   ├── middleware.go              # Auth, CORS, logging
│   └── routes.go                  # Route definitions
├── services/
│   ├── system_service.go         # Metrics calculation
│   ├── agent_service.go          # Agent management
│   └── skill_service.go          # Skill tracking
├── database/
│   ├── database.go               # Connection management
│   └── migrations.go             # Schema updates
├── models/
│   ├── agent.go                  # Data structures
│   ├── skill.go
│   └── metrics.go
└── rag/
    ├── qwen_client.go            # LLM integration
    └── data_sources.go           # Knowledge base
```

#### API Endpoints
```go
// System endpoints
GET    /api/v1/system/metrics     // System metrics
GET    /api/v1/system/status      // System status
GET    /api/v1/system/health      // Health check

// Agent endpoints
GET    /api/v1/agents             // List all agents
GET    /api/v1/agents/:id         // Get specific agent
POST   /api/v1/agents/:id/start   // Start agent
POST   /api/v1/agents/:id/stop    // Stop agent
POST   /api/v1/agents/:id/restart // Restart agent

// Skill endpoints
GET    /api/v1/skills             // List all skills
GET    /api/v1/skills/:id         // Get specific skill
POST   /api/v1/skills/:id/execute // Execute skill

// Activity endpoints
GET    /api/v1/activity           // Recent activities
GET    /api/v1/activity/stream    // WebSocket stream
```

#### Data Models
```go
type Agent struct {
    ID           string    `json:"id" db:"id"`
    Name         string    `json:"name" db:"name"`
    Language     string    `json:"language" db:"language"`
    Backend      string    `json:"backend" db:"backend"`
    Status       string    `json:"status" db:"status"`
    Skills       string    `json:"skills" db:"skills"`
    LastActivity time.Time `json:"last_activity" db:"last_activity"`
    SuccessRate  float64   `json:"success_rate" db:"success_rate"`
    CreatedAt    time.Time `json:"created_at" db:"created_at"`
    UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`
}

type SystemMetrics struct {
    Timestamp     time.Time     `json:"timestamp"`
    AgentMetrics  AgentMetrics  `json:"agentMetrics"`
    SkillMetrics  SkillMetrics  `json:"skillMetrics"`
    Performance   Performance   `json:"performance"`
}
```

### Database Schema

#### Tables Design
```sql
-- Agents table
CREATE TABLE agents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('rust', 'go', 'python')),
    backend TEXT NOT NULL CHECK (backend IN ('llama-cpp', 'ollama')),
    status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('running', 'idle', 'errored', 'stopped')),
    skills TEXT DEFAULT '[]',
    last_activity DATETIME,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0 AND success_rate <= 100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Skills table
CREATE TABLE skills (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL UNIQUE CHECK (length(name) <= 64),
    description TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Agent executions table
CREATE TABLE agent_executions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    agent_id TEXT REFERENCES agents(id),
    skill_name TEXT REFERENCES skills(name),
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    result TEXT,
    error_message TEXT
);
```

#### Indexes for Performance
```sql
-- Performance indexes
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_language ON agents(language);
CREATE INDEX idx_agents_updated_at ON agents(updated_at DESC);

CREATE INDEX idx_skills_name ON skills(name);

CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_skill_name ON agent_executions(skill_name);
CREATE INDEX idx_agent_executions_started_at ON agent_executions(started_at DESC);
```

## Real-Time Data System

### Agent Simulator

#### Architecture
```go
type AgentSimulator struct {
    db *sql.DB
}

func (as *AgentSimulator) StartSimulation() {
    // Simulate agent status changes
    go as.simulateAgentActivity("agent-1", "Memory Agent")
    go as.simulateAgentActivity("agent-2", "Temporal Agent")
    go as.simulateAgentActivity("agent-3", "Rust Agent")
    
    // Simulate skill executions
    go as.simulateSkillExecutions()
}
```

#### Activity Patterns
```go
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
        }
        
        // Random interval: 5-30 seconds
        time.Sleep(time.Duration(5+rand.Intn(25)) * time.Second)
    }
}
```

### Metrics Calculation

#### Real-Time Metrics
```go
func (s *SystemService) GetSystemMetrics(ctx context.Context) (*models.SystemMetrics, error) {
    metrics := &models.SystemMetrics{
        Timestamp: time.Now(),
    }

    // Get agent metrics
    agentMetrics, err := s.getAgentMetrics(ctx)
    if err != nil {
        return nil, err
    }
    metrics.AgentMetrics = agentMetrics

    // Get skill metrics
    skillMetrics, err := s.getSkillMetrics(ctx)
    if err != nil {
        return nil, err
    }
    metrics.SkillMetrics = skillMetrics

    return metrics, nil
}
```

#### Agent Metrics Calculation
```go
func (s *SystemService) getAgentMetrics(ctx context.Context) (models.AgentMetrics, error) {
    var metrics models.AgentMetrics

    // Get total agents
    err := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM agents").Scan(&metrics.Total)
    if err != nil {
        return metrics, err
    }

    // Get agents by status
    statuses := []string{"running", "idle", "errored", "stopped"}
    counts := []*int64{&metrics.Running, &metrics.Idle, &metrics.Errored, &metrics.Stopped}

    for i, status := range statuses {
        err := s.db.QueryRowContext(ctx, 
            "SELECT COUNT(*) FROM agents WHERE status = $1", status).Scan(counts[i])
        if err != nil {
            return metrics, err
        }
    }

    return metrics, nil
}
```

## Configuration Management

### Environment Variables
```bash
# Database Configuration
DATABASE_URL="sqlite:/tmp/dashboard.db"

# Server Configuration
PORT="8081"
GIN_MODE="debug"

# Feature Flags
RAG_ENABLED="false"
VOICE_ENABLED="false"

# External Services
TEMPORAL_ADDRESS="temporal-frontend.ai-infrastructure.svc.cluster.local:7233"
MEMORY_AGENT_URL="http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"

# Backend Priorities
BACKEND_PRIORITY="llama-cpp,ollama"
LANGUAGE_PRIORITY="rust,go,python"
```

### Configuration Loading
```go
type Config struct {
    Port            int    `mapstructure:"port"`
    DatabaseURL     string `mapstructure:"database_url"`
    TemporalAddress string `mapstructure:"temporal_address"`
    MemoryAgentURL  string `mapstructure:"memory_agent_url"`
    BackendPriority  string `mapstructure:"backend_priority"`
    LanguagePriority string `mapstructure:"language_priority"`
    Environment     string `mapstructure:"environment"`
    Version         string `mapstructure:"version"`
}

func Load() (*Config, error) {
    viper.SetDefault("port", 8081)
    viper.SetDefault("database_url", "sqlite:/tmp/dashboard.db")
    viper.SetDefault("gin_mode", "debug")
    
    viper.AutomaticEnv()
    
    var config Config
    if err := viper.Unmarshal(&config); err != nil {
        return nil, err
    }
    
    return &config, nil
}
```

## Error Handling

### Structured Error Handling
```go
type APIError struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
    Details string `json:"details,omitempty"`
}

func (e APIError) Error() string {
    return fmt.Sprintf("API Error %d: %s", e.Code, e.Message)
}

func (h *Handler) handleError(c *gin.Context, err error) {
    logger.Error("Request failed", zap.Error(err))
    
    var apiErr APIError
    switch {
    case errors.Is(err, sql.ErrNoRows):
        apiErr = APIError{Code: 404, Message: "Resource not found"}
    case errors.Is(err, context.DeadlineExceeded):
        apiErr = APIError{Code: 504, Message: "Request timeout"}
    default:
        apiErr = APIError{Code: 500, Message: "Internal server error"}
    }
    
    c.JSON(apiErr.Code, apiErr)
}
```

### Validation
```go
type AgentRequest struct {
    Name     string `json:"name" binding:"required,min=1,max=255"`
    Language string `json:"language" binding:"required,oneof=rust go python"`
    Backend  string `json:"backend" binding:"required,oneof=llama-cpp ollama"`
}

func (h *Handler) CreateAgent(c *gin.Context) {
    var req AgentRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    
    // Process request...
}
```

## Testing Strategy

### Unit Tests
```go
func TestSystemService_GetAgentMetrics(t *testing.T) {
    db := setupTestDB(t)
    service := NewSystemService(db, zap.NewNop())
    
    // Insert test data
    _, err := db.Exec(`
        INSERT INTO agents (id, name, language, backend, status) VALUES 
        ('test-1', 'Test Agent', 'go', 'llama-cpp', 'running'),
        ('test-2', 'Test Agent 2', 'rust', 'ollama', 'idle')
    `)
    require.NoError(t, err)
    
    metrics, err := service.getAgentMetrics(context.Background())
    require.NoError(t, err)
    
    assert.Equal(t, int64(2), metrics.Total)
    assert.Equal(t, int64(1), metrics.Running)
    assert.Equal(t, int64(1), metrics.Idle)
}
```

### Integration Tests
```go
func TestAPI_GetSystemMetrics(t *testing.T) {
    router := setupTestRouter(t)
    
    req, _ := http.NewRequest("GET", "/api/v1/system/metrics", nil)
    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)
    
    assert.Equal(t, 200, w.Code)
    
    var metrics models.SystemMetrics
    err := json.Unmarshal(w.Body.Bytes(), &metrics)
    require.NoError(t, err)
    
    assert.Greater(t, metrics.AgentMetrics.Total, int64(0))
}
```

### Performance Tests
```go
func BenchmarkSystemMetrics(b *testing.B) {
    service := setupSystemService(b)
    ctx := context.Background()
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := service.GetSystemMetrics(ctx)
        if err != nil {
            b.Fatal(err)
        }
    }
}
```

## Monitoring and Observability

### Structured Logging
```go
logger.Info("Agent status updated",
    zap.String("agent_id", agentID),
    zap.String("old_status", oldStatus),
    zap.String("new_status", newStatus),
    zap.Duration("processing_time", duration),
)
```

### Metrics Collection
```go
var (
    agentsTotal = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "agents_total",
            Help: "Total number of agents",
        },
        []string{"status"},
    )
    
    apiRequests = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "api_requests_total",
            Help: "Total number of API requests",
        },
        []string{"method", "endpoint", "status"},
    )
)
```

### Health Checks
```go
func (h *Handler) GetHealth(c *gin.Context) {
    health := map[string]interface{}{
        "status": "healthy",
        "timestamp": time.Now(),
        "version": h.config.Version,
        "checks": map[string]interface{}{
            "database": h.checkDatabase(),
            "memory": h.checkMemory(),
            "disk": h.checkDisk(),
        },
    }
    
    c.JSON(200, health)
}
```

---

**This technical guide provides detailed implementation information for developers working on the dashboard system.**
