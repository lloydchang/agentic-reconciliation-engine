# AI Agents Dashboard Implementation Plan

## Executive Summary

The current dashboard provides a solid visual foundation with modern design and comprehensive UI
elements. This plan outlines the complete implementation to transform it from a mockup into a
fully functional, real-time AI agents control center — while remaining consistent with the
existing repo architecture, GitOps principles, and the agentskills.io specification.

---

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
- Persistent data storage (SQLite for agent memory; PostgreSQL for dashboard state)
- Authentication and security
- Real-time updates via WebSockets

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AI Agents     │
│   (React/TS)    │◄──►│   (Go)          │◄──►│   (Temporal)    │
│                 │    │                 │    │                 │
│ - Dashboard UI  │    │ - REST APIs     │    │ - Skills        │
│ - Charts        │    │ - WebSocket     │    │ - Workflows     │
│ - Controls      │    │ - Auth          │    │ - Memory        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   PostgreSQL    │    │   Monitoring    │
│   (WebSocket)   │    │   (dashboard    │    │   (Prometheus)  │
│                 │    │    state only)  │    │                 │
│ - Real-time     │    │ - Agent State   │    │ - Metrics       │
│ - Updates       │    │ - History       │    │ - Alerts        │
│ - Events        │    │ - Config        │    │ - Logs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Storage Boundaries

| Store | Used For | Location |
|---|---|---|
| SQLite (10Gi PVC) | Agent memory, conversation history, inference state | `core/ai/runtime/backend/` (per memory agent) |
| PostgreSQL | Dashboard state, execution history, UI config | `core/ai/runtime/dashboard/` backend only |

These two stores serve different layers. SQLite is owned by the memory agents and must not be
replaced or duplicated by this dashboard implementation. PostgreSQL is introduced here solely
for dashboard-level persistence.

---

## Phase 1: Backend API Development

### 1.1 Project Structure

All backend code lives under the existing runtime path, not a new top-level directory:

```
core/ai/runtime/
├── backend/                    # Existing: Go Temporal workflows and activities
└── dashboard/
    ├── cmd/server/             # Entry point
    ├── internal/
    │   ├── api/                # HTTP handlers
    │   ├── models/             # Data models
    │   ├── services/           # Business logic
    │   └── ws/                 # WebSocket hub
    └── pkg/                    # Shared utilities
```

```bash
cd core/ai/runtime/dashboard
go mod init github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard
```

### 1.2 Core API Endpoints

```go
// Agent Management
GET    /api/v1/agents              // List all agents
GET    /api/v1/agents/{id}         // Get agent details
POST   /api/v1/agents/{id}/start   // Start agent
POST   /api/v1/agents/{id}/stop    // Stop agent
POST   /api/v1/agents/{id}/restart // Restart agent

// Skills Management
GET    /api/v1/skills              // List all skills
GET    /api/v1/skills/{id}         // Get skill details
POST   /api/v1/skills/{id}/execute // Execute skill (subject to autonomy gating)

// System APIs
GET    /api/v1/system/status       // System status
GET    /api/v1/system/metrics      // System metrics
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
    Language     string    `json:"language"`     // rust, go, python
    Status       string    `json:"status"`       // running, idle, error
    Backend      string    `json:"backend"`      // llama-cpp, ollama
    Skills       []string  `json:"skills"`
    LastActivity time.Time `json:"lastActivity"`
    SuccessRate  float64   `json:"successRate"`
    CreatedAt    time.Time `json:"createdAt"`
    UpdatedAt    time.Time `json:"updatedAt"`
}

// Skill reflects the agentskills.io standard fields plus
// project-specific metadata stored under the metadata key.
type Skill struct {
    // Standard agentskills.io fields
    Name          string            `json:"name"`
    Description   string            `json:"description"`
    License       string            `json:"license,omitempty"`
    Compatibility string            `json:"compatibility,omitempty"`
    // Project-specific metadata (stored under metadata: in SKILL.md frontmatter)
    Metadata      map[string]string `json:"metadata"`
}

// SkillMetadata are project-specific keys stored under metadata: in SKILL.md
type SkillMetadata struct {
    RiskLevel  string `json:"risk_level"`   // low, medium, high
    Autonomy   string `json:"autonomy"`     // fully_auto, conditional, requires_PR
    Layer      string `json:"layer"`        // temporal, gitops
    HumanGate  string `json:"human_gate,omitempty"`
}

type Activity struct {
    ID        string    `json:"id"`
    Type      string    `json:"type"`      // info, warning, error, success
    Agent     string    `json:"agent"`
    Message   string    `json:"message"`
    Timestamp time.Time `json:"timestamp"`
}
```

### 1.4 Database Schema (PostgreSQL — dashboard state only)

```sql
-- Agents table (mirrors live Kubernetes state)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    language VARCHAR(50) NOT NULL,   -- rust, go, python
    backend VARCHAR(50) NOT NULL,    -- llama-cpp, ollama
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    skills JSONB DEFAULT '[]',
    last_activity TIMESTAMP WITH TIME ZONE,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Skills table: standard agentskills.io fields + metadata JSONB for custom fields
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL UNIQUE,    -- agentskills.io: max 64 chars, lowercase
    description TEXT NOT NULL,           -- agentskills.io: required
    license VARCHAR(255),                -- agentskills.io: optional
    compatibility VARCHAR(500),          -- agentskills.io: optional, max 500 chars
    metadata JSONB DEFAULT '{}',         -- project keys: risk_level, autonomy, layer, human_gate
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activities table
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    agent_id UUID REFERENCES agents(id),
    message TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent executions table
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id),
    skill_name VARCHAR(64) REFERENCES skills(name),
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT
);
```

---

## Phase 2: Frontend Development

The existing dashboard UI (HTML5/CSS3/JavaScript with Chart.js and Feather Icons) is extended
rather than replaced. A React/TypeScript layer is added on top of the existing visual foundation.

### 2.1 Setup

```bash
cd core/ai/runtime/dashboard
npx create-react-app frontend --template typescript
cd frontend
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
│   │   ├── ActiveAgents.tsx
│   │   ├── AvailableSkills.tsx
│   │   ├── RecentActivity.tsx
│   │   └── SystemControls.tsx
│   ├── Layout/
│   │   ├── Header.tsx
│   │   └── Sidebar.tsx
│   └── Common/
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
    └── constants.ts
```

### 2.3 Real-time Data Integration

```typescript
// WebSocket service — URL from environment variable, not hardcoded
const WS_URL = process.env.REACT_APP_API_URL || 'http://ai-agents-backend.ai-infrastructure.svc.cluster.local:8081';

class WebSocketService {
    private socket: Socket | null = null;

    connect() {
        this.socket = io(WS_URL);

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

// API service — base URL from environment variable
class ApiService {
    private baseURL = `${process.env.REACT_APP_API_URL || WS_URL}/api/v1`;

    async getAgents(): Promise<Agent[]> {
        const response = await fetch(`${this.baseURL}/agents`);
        return response.json();
    }

    async startAgent(id: string): Promise<void> {
        await fetch(`${this.baseURL}/agents/${id}/start`, { method: 'POST' });
    }
}
```

---

## Phase 3: AI Agents Integration

### 3.1 Temporal Workflow Integration

```go
// Temporal client — use the correct SDK call (ExecuteWorkflow, not ExecuteClient)
func (s *SkillService) ExecuteSkill(ctx context.Context, skillName string, params map[string]interface{}) (interface{}, error) {
    options := client.StartWorkflowOptions{
        ID:        fmt.Sprintf("skill-%s-%d", skillName, time.Now().Unix()),
        TaskQueue: "agent-tasks",
    }

    run, err := s.temporalClient.ExecuteWorkflow(ctx, options, ExecuteSkillWorkflow, skillName, params)
    if err != nil {
        return nil, fmt.Errorf("failed to start skill workflow: %w", err)
    }

    var output interface{}
    if err := run.Get(ctx, &output); err != nil {
        return nil, fmt.Errorf("skill workflow failed: %w", err)
    }
    return output, nil
}

func ExecuteSkillWorkflow(ctx workflow.Context, skillName string, params map[string]interface{}) (interface{}, error) {
    skill, err := loadSkillMetadata(skillName)
    if err != nil {
        return nil, err
    }

    // Autonomy gating — read from metadata, not top-level fields
    autonomy := skill.Metadata["autonomy"]
    switch autonomy {
    case "fully_auto":
        return executeSkillDirectly(ctx, skill, params)
    case "conditional":
        return executeSkillWithApproval(ctx, skill, params)
    case "requires_PR":
        return executeSkillWithPR(ctx, skill, params)
    default:
        return nil, fmt.Errorf("unknown autonomy level: %s", autonomy)
    }
}
```

### 3.2 Memory Agent Integration

The dashboard backend communicates with memory agents (Rust, Go, Python) via their HTTP APIs.
All inference uses the local llama.cpp backend (Ollama as fallback) — no external API calls.

```go
// Memory agent client — language selected by LANGUAGE_PRIORITY env var
type MemoryAgentClient struct {
    baseURL string
    client  *http.Client
}

func NewMemoryAgentClient() *MemoryAgentClient {
    // Service address from env — not hardcoded
    url := os.Getenv("MEMORY_AGENT_URL")
    if url == "" {
        url = "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"
    }
    return &MemoryAgentClient{baseURL: url, client: &http.Client{Timeout: 30 * time.Second}}
}

func (c *MemoryAgentClient) Chat(ctx context.Context, message string, conversationID string) (string, error) {
    body, _ := json.Marshal(map[string]string{
        "message":         message,
        "conversation_id": conversationID,
    })
    resp, err := c.client.Post(c.baseURL+"/api/chat", "application/json", bytes.NewBuffer(body))
    if err != nil {
        return "", fmt.Errorf("memory agent unreachable: %w", err)
    }
    defer resp.Body.Close()

    var result struct{ Response string `json:"response"` }
    json.NewDecoder(resp.Body).Decode(&result)
    return result.Response, nil
}
```

### 3.3 Inference Backend Priority

The system always prefers local inference to preserve the privacy principle (data stays on-prem):

```yaml
env:
- name: BACKEND_PRIORITY
  value: "llama-cpp,ollama"
- name: LANGUAGE_PRIORITY
  value: "rust,go,python"
- name: MEMORY_AGENT_URL
  value: "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"
```

---

## Phase 4: Database & Persistence

### 4.1 PostgreSQL Setup (dashboard state only)

```yaml
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
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: "ai_agents_dashboard"
        - name: POSTGRES_USER
          value: "dashboard_user"
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
type MigrationService struct{ db *sql.DB }

func (m *MigrationService) Up() error {
    migrations := []string{
        createAgentsTable,
        createSkillsTable,
        createActivitiesTable,
        createAgentExecutionsTable,
    }
    for _, migration := range migrations {
        if _, err := m.db.Exec(migration); err != nil {
            return fmt.Errorf("migration failed: %w", err)
        }
    }
    return nil
}
```

---

## Phase 5: Authentication & Security

### 5.1 JWT Middleware

```go
func JWTMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        claims, err := validateJWT(token)
        if err != nil {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }
        ctx := context.WithValue(r.Context(), "user", claims)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

### 5.2 RBAC

```go
type Permission string

const (
    PermissionReadAgents    Permission = "agents:read"
    PermissionWriteAgents   Permission = "agents:write"
    PermissionExecuteSkills Permission = "skills:execute"
    PermissionReadLogs      Permission = "logs:read"
)

var roles = map[string][]Permission{
    "admin":  {PermissionReadAgents, PermissionWriteAgents, PermissionExecuteSkills, PermissionReadLogs},
    "viewer": {PermissionReadAgents, PermissionReadLogs},
}
```

---

## Phase 6: Monitoring & Observability

### 6.1 Prometheus Metrics

```go
var (
    agentsTotal = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{Name: "ai_agents_total", Help: "Current number of AI agents by language and status"},
        []string{"language", "status"},
    )
    skillExecutions = prometheus.NewCounterVec(
        prometheus.CounterOpts{Name: "skill_executions_total", Help: "Total skill executions"},
        []string{"skill_name", "status"},
    )
    skillDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{Name: "skill_execution_duration_seconds", Help: "Skill execution duration"},
        []string{"skill_name"},
    )
)
```

### 6.2 Health Checks

```go
func (s *Server) HealthCheck(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]interface{}{
        "status":    "healthy",
        "timestamp": time.Now(),
        "version":   s.version,
        "checks": map[string]interface{}{
            "database":     s.checkDatabase(),
            "temporal":     s.checkTemporal(),
            "memory_agent": s.checkMemoryAgent(),
        },
    })
}
```

---

## Phase 7: Testing Strategy

### 7.1 Unit Tests

```go
func TestAgentService_CreateAgent(t *testing.T) {
    service := NewAgentService(testDB)
    agent := &Agent{Name: "Test Agent", Language: "rust", Backend: "llama-cpp"}
    created, err := service.CreateAgent(context.Background(), agent)
    assert.NoError(t, err)
    assert.NotEmpty(t, created.ID)
}
```

### 7.2 Integration Tests

```go
func TestWorkflow_ExecuteSkill(t *testing.T) {
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()

    result, err := testEnv.SkillService.ExecuteSkill(
        context.Background(),
        "cost-optimizer",
        map[string]interface{}{"cluster": "test"},
    )
    assert.NoError(t, err)
    assert.NotNil(t, result)
}
```

---

## Phase 8: Deployment & CI/CD

### 8.1 Kubernetes Manifests

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agents-dashboard-backend
  namespace: ai-infrastructure
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agents-dashboard-backend
  template:
    spec:
      containers:
      - name: backend
        image: ai-agents/dashboard-backend:latest
        ports:
        - containerPort: 8081
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: TEMPORAL_ADDRESS
          value: "temporal-frontend.ai-infrastructure.svc.cluster.local:7233"
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"
        - name: BACKEND_PRIORITY
          value: "llama-cpp,ollama"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 8.2 GitHub Actions CI/CD

Deployments follow the GitOps principle: CI validates and builds; it does **not** run
`kubectl apply` directly. Instead, it updates the image tag in the GitOps manifests repo
and lets Flux/ArgoCD reconcile the change.

```yaml
name: AI Agents Dashboard CI/CD

on:
  push:
    paths:
    - 'core/ai/runtime/dashboard/**'
    - 'core/ai/skills/**'
  pull_request:
    paths:
    - 'core/ai/runtime/dashboard/**'
    - 'core/ai/skills/**'

jobs:
  validate-skills:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Validate agentskills.io compliance
      run: |
        npm install -g skills-ref
        skills-ref validate ./core/ai/skills/

  test:
    needs: validate-skills
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-go@v4
      with:
        go-version: '1.21'
    - name: Run backend tests
      run: |
        cd core/ai/runtime/dashboard
        go test -v ./...

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and push Docker images
      run: |
        docker build -t ghcr.io/${{ github.repository }}/dashboard-backend:${{ github.sha }} \
          core/ai/runtime/dashboard
        docker push ghcr.io/${{ github.repository }}/dashboard-backend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Update GitOps manifest (triggers Flux/ArgoCD reconciliation)
      run: |
        # Update image tag in gitops/ manifests — never kubectl apply directly
        sed -i "s|dashboard-backend:.*|dashboard-backend:${{ github.sha }}|" \
          gitops/ai-infrastructure/dashboard-backend-deployment.yaml
        git config user.email "ci@github.com"
        git config user.name "CI"
        git commit -am "chore: update dashboard-backend to ${{ github.sha }}"
        git push
```

---

## Implementation Timeline

Assumes a 2-engineer team working in parallel on backend and frontend within each phase.
Phases 1–2 are independent; Phase 3 depends on Phase 1 completing first.

### Week 1–2: Backend Foundation
- [ ] Set up Go project under `core/ai/runtime/dashboard/`
- [ ] Implement core API endpoints
- [ ] PostgreSQL schema and migrations
- [ ] Docker containerization

### Week 3–4: Frontend Development (parallel with Week 3–4 backend hardening)
- [ ] React TypeScript setup extending existing HTML/CSS/JS foundation
- [ ] Component development
- [ ] API + WebSocket integration (env-var-based URLs)

### Week 5–6: AI Agents Integration (depends on Week 1–2 complete)
- [ ] Temporal workflow implementation with correct SDK calls
- [ ] Memory agent HTTP client
- [ ] llama.cpp/Ollama backend priority wiring
- [ ] Real-time status updates

### Week 7–8: Advanced Features
- [ ] Authentication & RBAC
- [ ] Prometheus metrics and Grafana dashboards
- [ ] Full test suite (unit + integration)
- [ ] agentskills.io validation in CI gate

### Week 9–10: Production Readiness
- [ ] Performance optimisation and load testing
- [ ] Security hardening
- [ ] GitOps-compliant CI/CD pipeline (no direct kubectl apply)
- [ ] Production deployment via Flux/ArgoCD

---

## Success Metrics

| Category | Metric | Target |
|---|---|---|
| Performance | API p95 response time | < 100ms |
| Performance | WebSocket latency | < 50ms |
| Reliability | System uptime | > 99.9% |
| Reliability | Agent success rate | > 95% |
| UX | Dashboard load time | < 2s |
| UX | Interaction response | < 200ms |
| Quality | Test coverage | > 80% |
| Compliance | Skills passing `skills-ref validate` | 100% |

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Temporal service downtime | Circuit breakers and workflow retry policies |
| Memory agent unavailable | Health check endpoint; dashboard degrades gracefully |
| llama.cpp backend slow | Ollama fallback; async skill execution with status polling |
| PostgreSQL performance | Connection pooling; index on `activities.timestamp` |
| Direct kubectl in CI/CD | Enforced by policy: all deploys via GitOps manifest update only |
| Skills out of spec | `skills-ref validate` as mandatory CI gate before build |

---

## Conclusion

This plan transforms the dashboard mockup into a production-ready control center consistent
with the repo's GitOps principles, memory agent architecture, and agentskills.io compliance.

Key design decisions:
- **SQLite stays with memory agents** — PostgreSQL is dashboard-only, not a replacement
- **Local inference first** — llama.cpp/Ollama, no external API dependencies
- **GitOps-compliant deploys** — CI updates manifests; Flux/ArgoCD reconciles
- **agentskills.io compliance enforced in CI** — `skills-ref validate` is a required gate
- **No hardcoded URLs** — all service addresses via environment variables

---

**Last Updated**: 2026-03-16
**Version**: 1.1.0
**Maintainer**: Cloud AI Agents Team
