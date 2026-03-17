# AI Agents Dashboard Implementation Plan

## Executive Summary

The current dashboard provides an excellent visual foundation with modern design and comprehensive UI elements. This plan outlines the complete implementation to transform it from a mockup to a fully functional, real-time AI agents control center.

## Current State Analysis

### ✅ What's Working
- Modern, responsive web design with Chart.js and Feather Icons
- Complete UI layout with all required sections
- Proper CSS styling and component organization
- Kubernetes deployment configuration
- Port-forward accessible at http://localhost:8080

### 🔄 What Needs Implementation
- Real-time data connectivity to actual AI agents
- Backend API services for data retrieval
- Agent lifecycle management functionality
- Temporal workflow integration
- Persistent data storage
- Authentication and security
- Real-time updates via WebSockets

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Agents    │
│   (React/Vue)   │◄──►│   (Go/Python)   │◄──►│   (Temporal)   │
│                 │    │                 │    │                 │
│ - Dashboard UI  │    │ - REST APIs     │    │ - Skills       │
│ - Charts        │    │ - WebSocket     │    │ - Workflows    │
│ - Controls      │    │ - Auth          │    │ - Memory       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Database      │    │   Monitoring    │
│   (WebSocket)   │    │   (PostgreSQL)  │    │   (Prometheus)  │
│                 │    │                 │    │                 │
│ - Real-time     │    │ - Agent State   │    │ - Metrics       │
│ - Updates       │    │ - History       │    │ - Alerts       │
│ - Events        │    │ - Config        │    │ - Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Phase 1: Backend API Development

### 1.1 API Server Setup
```bash
# Create backend service
mkdir -p ai-agents/backend/{cmd,internal/{api,models,services},pkg}
cd ai-agents/backend

# Initialize Go module
go mod init github.com/lloydchang/gitops-infra-control-plane/ai-agents/backend
```

### 1.2 Core API Endpoints
```go
// Agent Management APIs
GET    /api/v1/agents              // List all agents
GET    /api/v1/agents/{id}         // Get agent details
POST   /api/v1/agents              // Create new agent
PUT    /api/v1/agents/{id}         // Update agent
DELETE /api/v1/agents/{id}         // Delete agent
POST   /api/v1/agents/{id}/start   // Start agent
POST   /api/v1/agents/{id}/stop    // Stop agent
POST   /api/v1/agents/{id}/restart // Restart agent

// Skills Management APIs
GET    /api/v1/skills              // List all skills
GET    /api/v1/skills/{id}         // Get skill details
POST   /api/v1/skills/{id}/execute // Execute skill

// System APIs
GET    /api/v1/system/status       // System status
GET    /api/v1/system/metrics      // System metrics
GET    /api/v1/system/logs         // System logs
GET    /api/v1/system/health       // Health check

// Activity APIs
GET    /api/v1/activity            // Recent activities
GET    /api/v1/activity/stream     // WebSocket stream
```

### 1.3 Data Models
```go
type Agent struct {
    ID           string    `json:"id"`
    Name         string    `json:"name"`
    Type         string    `json:"type"`         // rust, go, python
    Status       string    `json:"status"`       // running, idle, error
    Skills       []string  `json:"skills"`
    LastActivity time.Time `json:"lastActivity"`
    SuccessRate  float64   `json:"successRate"`
    CreatedAt    time.Time `json:"createdAt"`
    UpdatedAt    time.Time `json:"updatedAt"`
}

type Skill struct {
    ID          string            `json:"id"`
    Name        string            `json:"name"`
    Category    string            `json:"category"`
    Description string            `json:"description"`
    RiskLevel   string            `json:"riskLevel"`
    Autonomy    string            `json:"autonomy"`
    Metadata    map[string]string `json:"metadata"`
}

type Activity struct {
    ID        string    `json:"id"`
    Type      string    `json:"type"`      // info, warning, error, success
    Agent     string    `json:"agent"`
    Message   string    `json:"message"`
    Timestamp time.Time `json:"timestamp"`
    Icon      string    `json:"icon"`
}
```

### 1.4 Database Schema
```sql
-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    skills JSONB DEFAULT '[]',
    last_activity TIMESTAMP WITH TIME ZONE,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Skills table
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    autonomy VARCHAR(20) NOT NULL DEFAULT 'conditional',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activities table
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    message TEXT NOT NULL,
    icon VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent executions table
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    skill_id UUID REFERENCES skills(id),
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT
);
```

## Phase 2: Frontend Enhancement

### 2.1 Modern Frontend Framework
```bash
# Create React frontend
npx create-react-app ai-agents/frontend --template typescript
cd ai-agents/frontend

# Install dependencies
npm install @types/node @types/react @types/react-dom
npm install axios chart.js react-chartjs-2 feather-icons-react
npm install @mui/material @emotion/react @emotion/styled
npm install socket.io-client react-router-dom
```

### 2.2 Component Structure
```
src/
├── components/
│   ├── Dashboard/
│   │   ├── SystemOverview.tsx
│   │   ├── PerformanceMetrics.tsx
│   │   ├── SkillsDistribution.tsx
│   │   ├── ActiveAgents.tsx
│   │   ├── AvailableSkills.tsx
│   │   ├── RecentActivity.tsx
│   │   └── SystemControls.tsx
│   ├── Layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── Common/
│       ├── Chart.tsx
│       ├── MetricCard.tsx
│       └── ActivityItem.tsx
├── services/
│   ├── api.ts
│   ├── websocket.ts
│   └── types.ts
├── hooks/
│   ├── useAgents.ts
│   ├── useSkills.ts
│   └── useActivity.ts
└── utils/
    ├── constants.ts
    └── helpers.ts
```

### 2.3 Real-time Data Integration
```typescript
// WebSocket service
class WebSocketService {
    private socket: Socket | null = null;
    
    connect() {
        this.socket = io('ws://localhost:8081');
        
        this.socket.on('agent-status', (data: Agent) => {
            // Update agent status in real-time
        });
        
        this.socket.on('activity', (data: Activity) => {
            // Add new activity to feed
        });
        
        this.socket.on('metrics', (data: Metrics) => {
            // Update performance charts
        });
    }
}

// API service
class ApiService {
    private baseURL = 'http://localhost:8081/api/v1';
    
    async getAgents(): Promise<Agent[]> {
        const response = await fetch(`${this.baseURL}/agents`);
        return response.json();
    }
    
    async startAgent(id: string): Promise<void> {
        await fetch(`${this.baseURL}/agents/${id}/start`, {
            method: 'POST'
        });
    }
}
```

## Phase 3: AI Agents Integration

### 3.1 Temporal Workflow Integration
```go
// Temporal client for agent management
type AgentWorkflow struct {
    workflows.Client
}

func (w *AgentWorkflow) ExecuteSkill(ctx context.Context, skillID string, params map[string]interface{}) (interface{}, error) {
    options := workflow.StartOptions{
        ID:          fmt.Sprintf("skill-%s-%d", skillID, time.Now().Unix()),
        TaskQueue:   "agent-tasks",
    }
    
    result, err := workflow.ExecuteClient(ctx, options, ExecuteSkillWorkflow, skillID, params)
    if err != nil {
        return nil, err
    }
    
    var output interface{}
    result.Get(&output)
    return output, nil
}

func ExecuteSkillWorkflow(ctx workflow.Context, skillID string, params map[string]interface{}) (interface{}, error) {
    // Load skill configuration
    skill, err := loadSkill(skillID)
    if err != nil {
        return nil, err
    }
    
    // Execute skill based on autonomy level
    switch skill.Autonomy {
    case "fully_auto":
        return executeSkillDirectly(ctx, skill, params)
    case "conditional":
        return executeSkillWithApproval(ctx, skill, params)
    case "requires_PR":
        return executeSkillWithPR(ctx, skill, params)
    default:
        return nil, fmt.Errorf("unknown autonomy level: %s", skill.Autonomy)
    }
}
```

### 3.2 Agent Implementation
```go
// Base agent interface
type Agent interface {
    ID() string
    Name() string
    Type() string
    Start(ctx context.Context) error
    Stop(ctx context.Context) error
    ExecuteSkill(ctx context.Context, skillID string, params map[string]interface{}) (interface{}, error)
    Status() AgentStatus
}

// Rust agent implementation
type RustAgent struct {
    id     string
    name   string
    status AgentStatus
    client *http.Client
}

func (r *RustAgent) ExecuteSkill(ctx context.Context, skillID string, params map[string]interface{}) (interface{}, error) {
    // Call Rust agent service
    reqBody, _ := json.Marshal(map[string]interface{}{
        "skill_id": skillID,
        "params":   params,
    })
    
    resp, err := r.client.Post(fmt.Sprintf("http://localhost:8082/execute"), "application/json", bytes.NewBuffer(reqBody))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    return result, nil
}
```

## Phase 4: Database & Persistence

### 4.1 PostgreSQL Setup
```yaml
# postgresql.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "ai_agents"
        - name: POSTGRES_USER
          value: "ai_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

### 4.2 Database Migration
```go
// Migration service
type MigrationService struct {
    db *sql.DB
}

func (m *MigrationService) Up() error {
    migrations := []string{
        `CREATE TABLE IF NOT EXISTS agents (...)`,
        `CREATE TABLE IF NOT EXISTS skills (...)`,
        `CREATE TABLE IF NOT EXISTS activities (...)`,
        `CREATE TABLE IF NOT EXISTS agent_executions (...)`,
    }
    
    for _, migration := range migrations {
        if _, err := m.db.Exec(migration); err != nil {
            return err
        }
    }
    return nil
}
```

## Phase 5: Authentication & Security

### 5.1 OAuth2 Integration
```go
// JWT middleware
func JWTMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        
        // Validate JWT token
        claims, err := validateJWT(token)
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }
        
        // Add user context to request
        ctx := context.WithValue(r.Context(), "user", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### 5.2 RBAC Implementation
```go
// Role-based access control
type Permission string

const (
    PermissionReadAgents    Permission = "agents:read"
    PermissionWriteAgents   Permission = "agents:write"
    PermissionExecuteSkills Permission = "skills:execute"
    PermissionReadLogs      Permission = "logs:read"
)

type Role struct {
    Name        string
    Permissions []Permission
}

var roles = map[string]Role{
    "admin": {
        Name: "admin",
        Permissions: []Permission{
            PermissionReadAgents,
            PermissionWriteAgents,
            PermissionExecuteSkills,
            PermissionReadLogs,
        },
    },
    "viewer": {
        Name: "viewer",
        Permissions: []Permission{
            PermissionReadAgents,
            PermissionReadLogs,
        },
    },
}
```

## Phase 6: Monitoring & Observability

### 6.1 Prometheus Metrics
```go
// Metrics collection
var (
    agentsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "ai_agents_total",
            Help: "Total number of AI agents",
        },
        []string{"type", "status"},
    )
    
    skillExecutions = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "skill_executions_total",
            Help: "Total number of skill executions",
        },
        []string{"skill_id", "status"},
    )
    
    skillDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "skill_execution_duration_seconds",
            Help: "Duration of skill executions",
        },
        []string{"skill_id"},
    )
)
```

### 6.2 Health Checks
```go
// Health check endpoints
func (s *Server) HealthCheck(w http.ResponseWriter, r *http.Request) {
    status := map[string]interface{}{
        "status": "healthy",
        "timestamp": time.Now(),
        "version": s.version,
        "checks": map[string]interface{}{
            "database": s.checkDatabase(),
            "temporal": s.checkTemporal(),
            "agents": s.checkAgents(),
        },
    }
    
    json.NewEncoder(w).Encode(status)
}
```

## Phase 7: Testing Strategy

### 7.1 Unit Tests
```go
// Agent service tests
func TestAgentService_CreateAgent(t *testing.T) {
    service := NewAgentService(db)
    
    agent := &Agent{
        Name: "Test Agent",
        Type: "rust",
        Skills: []string{"cost-analysis"},
    }
    
    created, err := service.CreateAgent(context.Background(), agent)
    assert.NoError(t, err)
    assert.NotEmpty(t, created.ID)
    assert.Equal(t, agent.Name, created.Name)
}
```

### 7.2 Integration Tests
```go
// End-to-end workflow tests
func TestWorkflow_ExecuteSkill(t *testing.T) {
    // Setup test environment
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    // Execute skill
    result, err := testEnv.Workflow.ExecuteSkill(
        context.Background(),
        "cost-analysis",
        map[string]interface{}{"cluster": "test"},
    )
    
    assert.NoError(t, err)
    assert.NotNil(t, result)
}
```

## Phase 8: Deployment & CI/CD

### 8.1 Kubernetes Manifests
```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agents-backend
  namespace: ai-infrastructure
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agents-backend
  template:
    metadata:
      labels:
        app: ai-agents-backend
    spec:
      containers:
      - name: backend
        image: ai-agents/backend:latest
        ports:
        - containerPort: 8081
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: TEMPORAL_ADDRESS
          value: "temporal-frontend:7233"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: ai-agents-backend
  namespace: ai-infrastructure
spec:
  selector:
    app: ai-agents-backend
  ports:
  - port: 8081
    targetPort: 8081
  type: ClusterIP
```

### 8.2 GitHub Actions Workflow
```yaml
# .github/workflows/ai-agents.yml
name: AI Agents CI/CD

on:
  push:
    paths:
    - 'ai-agents/**'
  pull_request:
    paths:
    - 'ai-agents/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    - name: Run tests
      run: |
        cd ai-agents/backend
        go test -v ./...
        
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker images
      run: |
        docker build -t ai-agents/backend:latest ai-agents/backend
        docker build -t ai-agents/frontend:latest ai-agents/frontend
        
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f ai-agents/k8s/
```

## Implementation Timeline

### Week 1-2: Backend Foundation
- [ ] Set up Go backend project structure
- [ ] Implement basic API endpoints
- [ ] Database schema and migrations
- [ ] Docker containerization

### Week 3-4: Frontend Development
- [ ] React TypeScript setup
- [ ] Component development
- [ ] API integration
- [ ] WebSocket implementation

### Week 5-6: AI Agents Integration
- [ ] Temporal workflow implementation
- [ ] Agent service development
- [ ] Skills execution engine
- [ ] Real-time status updates

### Week 7-8: Advanced Features
- [ ] Authentication & authorization
- [ ] Monitoring & metrics
- [ ] Testing suite
- [ ] Documentation

### Week 9-10: Production Readiness
- [ ] Performance optimization
- [ ] Security hardening
- [ ] CI/CD pipeline
- [ ] Production deployment

## Success Metrics

### Technical Metrics
- **API Response Time**: < 100ms for 95% of requests
- **WebSocket Latency**: < 50ms for real-time updates
- **System Uptime**: > 99.9%
- **Database Query Performance**: < 10ms for indexed queries

### Functional Metrics
- **Agent Success Rate**: > 95%
- **Skill Execution Time**: < 30 seconds average
- **Dashboard Load Time**: < 2 seconds
- **Real-time Update Accuracy**: 100%

### User Experience Metrics
- **Page Load Time**: < 3 seconds
- **Interaction Response**: < 200ms
- **Error Rate**: < 0.1%
- **User Satisfaction**: > 4.5/5

## Risk Mitigation

### Technical Risks
1. **Temporal Service Downtime**
   - Mitigation: Implement circuit breakers and fallback mechanisms
   
2. **Database Performance Issues**
   - Mitigation: Implement connection pooling and query optimization
   
3. **Frontend Performance**
   - Mitigation: Implement code splitting and lazy loading

### Operational Risks
1. **Agent Failures**
   - Mitigation: Implement health checks and auto-restart mechanisms
   
2. **Security Vulnerabilities**
   - Mitigation: Regular security audits and dependency updates
   
3. **Scalability Issues**
   - Mitigation: Horizontal scaling and load testing

## Conclusion

This implementation plan provides a comprehensive roadmap to transform the current dashboard mockup into a fully functional, production-ready AI agents control center. The phased approach ensures manageable development cycles while delivering value incrementally.

The key success factors are:
1. **Modular Architecture**: Clean separation of concerns
2. **Real-time Communication**: WebSocket-based updates
3. **Scalable Design**: Horizontal scaling capabilities
4. **Robust Testing**: Comprehensive test coverage
5. **Production Ready**: Security, monitoring, and observability

With this plan, the dashboard will evolve from a visual mockup to a powerful tool for managing AI agents in production environments.
