# AI Agents Dashboard

A comprehensive dashboard for monitoring and managing AI agents in the Agentic Reconciliation Engine.

## Architecture

The dashboard follows a **dual-database architecture** to separate concerns:

- **Backend**: Go-based API server with WebSocket support
- **Frontend**: React TypeScript with real-time updates
- **Database**: PostgreSQL for dashboard state (separate from agent memory SQLite)
- **Deployment**: Kubernetes with GitOps compliance

### 🗄️ Database Architecture

| Database | Purpose | Owner | Use Case |
|---|---|---|---|
| **PostgreSQL** | Dashboard operational state | Dashboard backend | Multi-user access, analytics, audit trails |
| **SQLite (10Gi PVC)** | Agent memory & inference | Individual agents | Local AI reasoning, conversation history |

#### Why PostgreSQL for Dashboard?

PostgreSQL is chosen specifically for **dashboard operations** because:

1. **Multi-user Concurrency** - Multiple operators viewing dashboard simultaneously
2. **Complex Analytics** - Historical queries across agents and skills
3. **Enterprise Features** - Backup, replication, monitoring integration
4. **ACID Compliance** - Critical for operational state integrity
5. **Performance** - Better for concurrent reads/writes than SQLite

**Important**: PostgreSQL **does not replace** agent SQLite databases - they serve different layers in the architecture.

## Features

- 📊 **System Overview**: Real-time metrics for agents, skills, and success rates
- 🤖 **Agent Management**: Monitor and control AI agents (Rust, Go, Python)
- 🛠️ **Skills Management**: View and execute agentskills.io-compliant skills
- 📋 **Activity Feed**: Real-time activity monitoring
- ⚡ **Performance Metrics**: System performance charts
- 🎛️ **System Controls**: Deploy, stop, restart agents

## Quick Start

### Prerequisites

- Go 1.21+
- Node.js 18+
- PostgreSQL 15+
- Kubernetes cluster (for deployment)

### Local Development

1. **Backend Setup**:
   ```bash
   cd core/ai/runtime/dashboard
   go mod download
   go run cmd/server/main.go
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Database Setup**:
   ```bash
   # Create PostgreSQL database (dashboard state only)
   createdb ai_agents_dashboard
   
   # The backend will auto-run migrations on startup
   # Note: This is separate from agent SQLite databases
   ```

### Kubernetes Deployment

1. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f deployment/kubernetes/namespace.yaml
   kubectl apply -f deployment/kubernetes/postgres-deployment.yaml
   kubectl apply -f deployment/kubernetes/dashboard-deployment.yaml
   kubectl apply -f deployment/kubernetes/ingress.yaml
   ```

2. **Access the Dashboard**:
   ```bash
   # Port forward for local access
   kubectl port-forward -n ai-infrastructure svc/ai-agents-dashboard 8081:8081
   
   # Or access via ingress (if configured)
   # http://ai-agents-dashboard.local
   ```

## API Endpoints

### Agents
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{id}` - Get agent details
- `POST /api/v1/agents/{id}/start` - Start agent
- `POST /api/v1/agents/{id}/stop` - Stop agent
- `POST /api/v1/agents/{id}/restart` - Restart agent

### Skills
- `GET /api/v1/skills` - List all skills
- `GET /api/v1/skills/{id}` - Get skill details
- `POST /api/v1/skills/{id}/execute` - Execute skill

### System
- `GET /api/v1/system/status` - System status
- `GET /api/v1/system/metrics` - System metrics
- `GET /api/v1/system/health` - Health check

### Activity
- `GET /api/v1/activity` - Recent activities
- `GET /api/v1/activity/stream` - WebSocket stream

## Configuration

Environment variables:

```bash
# Database
DATABASE_URL=postgres://dashboard_user:password@localhost:5432/ai_agents_dashboard?sslmode=disable

# Services
TEMPORAL_ADDRESS=temporal-frontend.ai-infrastructure.svc.cluster.local:7233
MEMORY_AGENT_URL=http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080

# Backend Configuration
BACKEND_PRIORITY=llama-cpp,ollama
LANGUAGE_PRIORITY=rust,go,python

# Server
PORT=8081
ENVIRONMENT=development
```

## agentskills.io Compliance

The dashboard fully supports the agentskills.io specification:

- Skills are validated against the specification
- Project-specific metadata stored under `metadata:` key
- Risk levels and autonomy gates enforced
- CI/CD pipeline includes `skills-ref validate` as required gate

## Monitoring

- **Metrics**: Available at `/metrics` (Prometheus format)
- **Health**: Available at `/health`
- **Real-time Updates**: WebSocket connections at `/api/v1/activity/stream`

## Security

- JWT-based authentication (planned)
- RBAC authorization (planned)
- HTTPS enforcement in production
- Secure WebSocket connections

## Development

### Project Structure

```
core/ai/runtime/dashboard/
├── cmd/server/              # Main application entry point
├── internal/
│   ├── api/                 # HTTP handlers
│   ├── models/              # Data models
│   ├── services/            # Business logic
│   ├── ws/                  # WebSocket hub
│   └── config/              # Configuration
├── pkg/metrics/             # Prometheus metrics
├── frontend/                # React TypeScript frontend
├── deployment/kubernetes/   # Kubernetes manifests
├── Dockerfile              # Multi-stage build
└── README.md               # This file
```

### Adding New Features

1. **Backend**: Add models, services, and API handlers
2. **Frontend**: Create React components with TypeScript
3. **Database**: Add migrations to `internal/database/database.go`
4. **Tests**: Add unit and integration tests

## GitOps Compliance

The dashboard follows GitOps principles:

- All deployments via Kubernetes manifests
- CI/CD updates image tags, never applies directly
- Infrastructure as code in version control
- Automated rollback capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is part of the Agentic Reconciliation Engine repository.
