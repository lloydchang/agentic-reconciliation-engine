# Agent Memory Service

A high-performance Rust-based memory agent service that provides persistent AI memory, event processing, and workflow orchestration for the Agentic Reconciliation Engine.

## Features

- **Persistent Memory**: SQLite-based storage for episodic, semantic, and procedural memory
- **Event Processing**: Alert enrichment and correlation for Argo Events integration
- **Skill Engine**: Dynamic loading and execution of agentskills.io-compliant skills
- **Workflow Orchestration**: Temporal-style workflow definitions for complex operations
- **LLM Integration**: Qwen LLM integration for intelligent analysis and decision-making
- **REST API**: Comprehensive HTTP API for all operations
- **Metrics**: Prometheus metrics for monitoring and observability

## LLaMA.cpp Integration

The Agent Memory Service now uses **native LLaMA.cpp server** with OpenAI-compatible API:

### Setup LLaMA.cpp

```bash
# 1. Install and setup LLaMA.cpp with Qwen model
./setup-llamacpp.sh

# 2. Start LLaMA.cpp server
./start-llamacpp-server.sh /models/qwen2.5-0.5b-instruct.gguf

# 3. Configure service to use LLaMA.cpp
cp .env.llamacpp .env
```

### LLaMA.cpp Features

- **Native OpenAI-compatible API**: `http://localhost:8080/v1/chat/completions`
- **Qwen model support**: Optimized for Qwen2.5 models
- **GPU acceleration**: CUDA support for faster inference
- **Local inference**: No external API calls required
- **Automatic fallback**: Falls back to OpenAI/Ollama if LLaMA.cpp unavailable

### Configuration

```bash
# LLaMA.cpp configuration
LLAMACPP_API_URL=http://localhost:8080
LLAMACPP_MODEL=qwen2.5:0.5b
BACKEND_PRIORITY=llamacpp,openai,ollama
```

### API Usage

```bash
# Test LLaMA.cpp server
curl http://localhost:8080/health

# Test chat completions
curl http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5:0.5b","messages":[{"role":"user","content":"Hello!"}]}'
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Argo Events   │───▶│ Event Processor │───▶│   Memory Store  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Qwen LLM      │◀───│  Skill Engine   │◀───│  Workflow Engine│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## API Endpoints

### Core API
- `GET /api/health` - Health check and service status
- `POST /api/events` - Ingest events from Argo Events
- `POST /api/chat` - Chat with the memory agent
- `GET /api/skills/list` - List available skills
- `POST /api/skills/execute` - Execute a skill
- `GET /api/workflows` - List workflow executions
- `GET /api/incidents` - List incidents

### Integration API
- `POST /api/integration/alerts` - Process Prometheus alerts
- `GET /api/integration/alerts` - List processed alerts
- `GET /api/integration/correlations/:id` - Get event correlation details
- `GET /api/integration/summary` - Get event processing summary
- `POST /api/integration/workflows/trigger` - Manually trigger workflows

### Metrics
- `GET /metrics` - Prometheus metrics endpoint

## Database Schema

The service uses SQLite with the following tables:

- **episodes** - Conversation history and session data
- **semantic_memory** - Learned concepts and relationships
- **procedural_memory** - Skill execution patterns and outcomes
- **working_memory** - Current session context
- **events** - Processed events and metadata
- **workflows** - Workflow execution tracking
- **incidents** - Incident tracking and resolution

## Configuration

The service is configured via environment variables:

```bash
DATABASE_PATH=sqlite:/data/memory.db
BIND_ADDRESS=0.0.0.0
PORT=8080
SKILLS_DIRECTORY=/opt/skills
QWEN_API_URL=http://localhost:8000
QWEN_MODEL=qwen2.5:0.5b
```

See `.env.example` for all available options.

## Building

```bash
# Build the Rust binary and Docker image
./build.sh

# Or manually:
cargo build --release
docker build -t agent-memory-rust:latest .
```

## Deployment

### Docker

```bash
docker run -p 8080:8080 -p 9090:9090 \
  -v $(pwd)/data:/data \
  -v $(pwd)/.env:/app/.env \
  agent-memory-rust:latest
```

### Kubernetes

```bash
# Deploy to Kubernetes
cd k8s
./deploy.sh
```

## Integration with ARE

This service bridges the gap between the theoretical architecture and actual implementation:

1. **Event Ingestion**: Argo Events sensors send alerts to `/api/events`
2. **Memory Queries**: ARE queries SQLite via `/api/chat` for historical context
3. **Skill Selection**: Qwen analyzes events and selects appropriate skills
4. **Workflow Execution**: Temporal workflows are triggered via `/api/integration/workflows/trigger`
5. **Result Storage**: Outcomes are stored back in SQLite for future reference

## Development

### Project Structure

```
src/
├── main.rs              # Application entry point
├── database.rs          # SQLite database initialization
├── models.rs            # Data models and structs
├── qwen.rs              # Qwen LLM integration
├── handlers.rs          # HTTP API handlers
├── skills.rs            # Skill engine implementation
├── workflows.rs         # Workflow orchestration
├── events.rs            # Event processing and correlation
└── integration.rs       # Argo Events integration
```

### Running Tests

```bash
cargo test
```

### Running in Development

```bash
# Set up environment
cp .env.example .env

# Run with hot reload
cargo run

# Or with specific configuration
RUST_LOG=debug cargo run
```

## Monitoring

The service exposes Prometheus metrics on port 9090:

- `agent_memory_episodes_total` - Total episodes in memory
- `agent_memory_events_pending_total` - Number of pending events
- `agent_memory_workflows_total` - Total workflows executed
- `agent_memory_uptime_seconds` - Service uptime

## Security

- JWT-based authentication for sensitive endpoints
- API key validation for external integrations
- Rate limiting and connection limits
- Non-root container execution
- Network policies for Kubernetes deployment

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check `DATABASE_PATH` and volume mounts
2. **Qwen API failures**: Verify `QWEN_API_URL` and network connectivity
3. **Skills not loading**: Ensure `SKILLS_DIRECTORY` is correctly mounted
4. **Memory leaks**: Monitor SQLite database size and clean old episodes

### Debug Mode

Enable debug logging:

```bash
RUST_LOG=debug cargo run
```

### Health Checks

```bash
curl http://localhost:8080/api/health
```

## License

AGPL-3.0-or-later
