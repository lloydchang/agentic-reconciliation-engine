# Implementation

This document provides a comprehensive technical overview of the AI Agents Sandbox implementation, covering the backend architecture, frontend components, infrastructure, and deployment patterns.

## System Architecture

The AI Agents Sandbox implements a multi-layered architecture designed for safe experimentation with AI agent orchestration:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Backstage Framework (TypeScript/React)                │ │
│  │  • Agent Dashboard UI                                  │ │
│  │  • Workflow Management Interface                       │ │
│  │  • Skills Configuration Panel                          │ │
│  │  • Real-time Status Updates                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Coordination Layer                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Agent Orchestration Engine                             │ │
│  │  • Multi-Agent Collaboration                            │ │
│  │  • Human-in-the-Loop Workflows                          │ │
│  │  • Safety Controls & Governance                         │ │
│  │  • Skill Auto-Discovery                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  MCP Server (Model Context Protocol)                    │ │
│  │  • AI Assistant Integration                             │ │
│  │  • Standardized Tool Interface                          │ │
│  │  • Multiple Transport Modes                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execution Layer                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Temporal Workflow Engine (Go)                          │ │
│  │  • Durable Workflow Execution                           │ │
│  │  • State Persistence                                     │ │
│  │  • Retry Logic & Error Handling                          │ │
│  │  • Activity Scheduling                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Infrastructure Emulator                                │ │
│  │  • Safe Cloud Resource Simulation                        │ │
│  │  • Multi-Cloud Support (AWS/Azure/GCP)                  │ │
│  │  • Compliance Testing Environment                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Database                                    │ │
│  │  • Workflow State Persistence                           │ │
│  │  • Audit Trail Storage                                  │ │
│  │  • Configuration Management                             │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Backend Implementation

### Temporal Workflow Engine

The backend is built using Go and the Temporal workflow engine:

#### Core Components
- **Temporal Worker**: Processes workflow tasks and activity executions
- **Workflow Definitions**: Durable workflow orchestration logic
- **Activity Implementations**: Individual task execution units
- **HTTP API Layer**: REST endpoints for external integration

#### Key Workflows
```go
// HelloBackstageWorkflow - Entry point workflow
func HelloBackstageWorkflow(ctx workflow.Context, name string) (string, error) {
    // Activity options with retry policy
    ao := workflow.ActivityOptions{
        StartToCloseTimeout: time.Minute * 5,
        RetryPolicy: &temporal.RetryPolicy{
            InitialInterval: time.Second,
            BackoffCoefficient: 2.0,
            MaximumInterval: time.Minute,
            MaximumAttempts: 5,
        },
    }

    ctx = workflow.WithActivityOptions(ctx, ao)

    // Execute activities
    var fetchResult string
    err := workflow.ExecuteActivity(ctx, FetchDataActivity, name).Get(ctx, &fetchResult)
    if err != nil {
        return "", err
    }

    var processResult string
    err = workflow.ExecuteActivity(ctx, ProcessDataActivity, fetchResult).Get(ctx, &processResult)
    if err != nil {
        return "", err
    }

    return processResult, nil
}
```

#### Activity Implementation
```go
// FetchDataActivity - Data retrieval activity
func FetchDataActivity(ctx context.Context, name string) (string, error) {
    logger := activity.GetLogger(ctx)
    logger.Info("FetchDataActivity started", "name", name)

    // Simulate data fetching
    result := fmt.Sprintf("Fetched data for: %s", name)

    logger.Info("FetchDataActivity completed", "result", result)
    return result, nil
}
```

### REST API Layer

The backend exposes REST endpoints for workflow management:

```go
// HTTP handlers
func startWorkflowHandler(w http.ResponseWriter, r *http.Request) {
    var req StartWorkflowRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    workflowID := uuid.New().String()
    runID, err := startWorkflow(workflowID, req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    response := WorkflowResponse{
        WorkflowID: workflowID,
        RunID:      runID,
        Status:     "started",
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func getWorkflowStatusHandler(w http.ResponseWriter, r *http.Request) {
    workflowID := r.URL.Query().Get("id")
    if workflowID == "" {
        http.Error(w, "Missing workflow ID", http.StatusBadRequest)
        return
    }

    status, err := getWorkflowStatus(workflowID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(status)
}
```

## Frontend Implementation

### Backstage Framework

The frontend is built using the Backstage developer portal framework:

#### Key Components
- **Agent Dashboard**: Visual workflow management interface
- **Skills Management**: Configure and monitor available skills
- **Temporal Integration Plugin**: Native workflow orchestration UI
- **Real-time Updates**: Live status monitoring via polling/WebSocket

#### Plugin Architecture
```typescript
// TemporalIntegrationPlugin
export const TemporalIntegrationPage = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkflows();
    const interval = setInterval(fetchWorkflows, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch('/api/temporal/workflows');
      const data = await response.json();
      setWorkflows(data);
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const startWorkflow = async (workflowType: string) => {
    try {
      await fetch('/api/temporal/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: workflowType }),
      });
      fetchWorkflows(); // Refresh list
    } catch (error) {
      console.error('Failed to start workflow:', error);
    }
  };

  return (
    <Page themeId="tool">
      <Header title="AI Agent Orchestration" />
      <Content>
        <WorkflowTable
          workflows={workflows}
          loading={loading}
          onStartWorkflow={startWorkflow}
        />
      </Content>
    </Page>
  );
};
```

## Infrastructure & Deployment

### Docker Configuration

#### Backend Dockerfile
```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .

EXPOSE 8081
CMD ["./main"]
```

#### Docker Compose Setup
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  temporal:
    image: temporalio/auto-setup:1.21.0
    depends_on:
      - postgres
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgres
    ports:
      - "7233:7233"
      - "8080:8080"
    volumes:
      - temporal_data:/data

volumes:
  postgres_data:
  temporal_data:
```

### Development Tooling

#### Automated Scripts
- **dev.sh**: Orchestrates infrastructure startup and service initialization
- **build.sh**: Creates production Docker images for all components
- **validate.sh**: Comprehensive environment and integration testing

#### Testing Strategy
```bash
# Backend unit tests
cd backend && go test ./...

# Integration tests
cd backend && go test -tags=integration ./...

# Frontend tests
cd frontend && yarn test

# End-to-end validation
./scripts/validate.sh
```

## Skills System Architecture

### Skill Auto-Discovery

Skills are automatically discovered from the `.agents/skills/` directory:

```go
// Skill loader implementation
func loadSkills() ([]Skill, error) {
    skills := []Skill{}

    skillDirs, err := filepath.Glob(".agents/skills/*")
    if err != nil {
        return nil, err
    }

    for _, dir := range skillDirs {
        skill, err := loadSkillFromDir(dir)
        if err != nil {
            log.Printf("Failed to load skill from %s: %v", dir, err)
            continue
        }
        skills = append(skills, skill)
    }

    return skills, nil
}
```

### Skill Definition Format

Each skill is defined by a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: compliance-check
description: SOC2/GDPR/HIPAA compliance scanning
parameters:
  - name: targetResource
    type: string
    required: true
    description: Resource to check
  - name: complianceType
    type: string
    enum: [SOC2, GDPR, HIPAA, full-scan]
    default: full-scan
outputs:
  - name: complianceScore
    type: number
    description: Compliance score (0-100)
  - name: issuesFound
    type: number
    description: Number of issues identified
human_gates:
  - condition: "complianceScore < 80"
    action: request_review
    priority: high
---

# Skill Implementation
Skill logic and workflow definition go here...
```

## Monitoring & Observability

### Temporal UI Integration
- **Workflow Visualization**: Real-time workflow execution graphs
- **Activity Monitoring**: Individual activity status and logs
- **Performance Metrics**: Execution times, retry counts, error rates
- **Historical Analysis**: Past workflow execution patterns

### Logging Architecture
```go
// Structured logging implementation
type Logger struct {
    *zap.Logger
}

func (l *Logger) LogWorkflowExecution(workflowID string, duration time.Duration, status string) {
    l.Info("Workflow execution completed",
        zap.String("workflow_id", workflowID),
        zap.Duration("duration", duration),
        zap.String("status", status),
    )
}

func (l *Logger) LogActivityExecution(activityName string, input interface{}, output interface{}, err error) {
    fields := []zap.Field{
        zap.String("activity", activityName),
        zap.Any("input", input),
    }

    if err != nil {
        fields = append(fields, zap.Error(err))
        l.Error("Activity execution failed", fields...)
    } else {
        fields = append(fields, zap.Any("output", output))
        l.Info("Activity execution completed", fields...)
    }
}
```

## Security Implementation

### Sandbox Boundaries
- **Tool Execution Limits**: Configurable blast radius for each skill
- **Network Isolation**: Restricted external connectivity
- **Resource Quotas**: CPU, memory, and storage limits
- **Audit Logging**: Comprehensive action tracking

### Authentication & Authorization
- **API Key Management**: Secure token-based authentication
- **Role-Based Access**: Permission levels for different operations
- **Session Management**: Secure session handling and timeouts

## Scaling & Performance

### Horizontal Scaling
- **Worker Pool Management**: Multiple Temporal workers for load distribution
- **Database Sharding**: Workflow state distribution across multiple PostgreSQL instances
- **Caching Layer**: Redis integration for frequently accessed data
- **Load Balancing**: Distribute requests across multiple backend instances

### Performance Optimization
- **Workflow Optimization**: Minimize activity overhead and network calls
- **Batch Processing**: Group similar operations for efficiency
- **Async Processing**: Non-blocking operations for better responsiveness
- **Resource Pooling**: Connection pooling for database and external services

## Deployment Patterns

### Development Environment
```bash
# Local development setup
./scripts/dev.sh  # Starts all services locally
```

### Production Deployment
```bash
# Build production images
./scripts/build.sh

# Deploy to Kubernetes
kubectl apply -f k8s/
```

### Cloud Deployment Options
- **AWS ECS/Fargate**: Containerized deployment with load balancing
- **Azure Container Apps**: Serverless container platform
- **Google Cloud Run**: Managed container execution
- **Kubernetes**: Full orchestration with Helm charts

This implementation provides a robust, scalable foundation for AI agent orchestration while maintaining safety, observability, and extensibility.
