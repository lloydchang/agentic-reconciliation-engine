# Getting Started

Welcome to the AI Agents Sandbox! This guide will help you get up and running quickly with the platform.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Go 1.25+** - Required for the backend Temporal workflows
- **Node.js 16+** - Required for the frontend React application
- **Docker & Docker Compose** - Required for running the infrastructure (Temporal server, PostgreSQL)
- **Make** *(optional)* - For using the provided Makefiles

### Verifying Prerequisites

```bash
# Check Go version
go version

# Check Node.js version
node --version
npm --version

# Check Docker
docker --version
docker-compose --version
```

## Quick Start

### Option 1: Automated Setup

The easiest way to get started is using the automated setup script:

```bash
# Clone the repository
git clone https://github.com/lloydchang/ai-agents-sandbox.git
cd ai-agents-sandbox

# Run the automated setup
./bootstrap.sh

# Start everything at once
./scripts/dev.sh
```

### Option 2: Manual Setup

If you prefer to set up components individually:

#### 1. Start Infrastructure

```bash
cd backend && docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432 (database for workflow state)
- **Temporal Server** on port 7233 (workflow orchestration engine)
- **Temporal UI** on port 8080 (web interface for monitoring workflows)

#### 2. Start Backend

```bash
cd backend
go mod tidy
go run main.go
```

This launches:
- REST API on `:8081`
- MCP server for AI assistant integration
- WebMCP client interface
- Infrastructure emulator
- CLI-ready endpoints

#### 3. Start Frontend

```bash
cd frontend
yarn install
yarn start
```

This starts the Backstage application at `http://localhost:3000`.

## Health Checks

### Backend Health Check

```bash
curl http://localhost:8081/health
```

### Infrastructure Health Check

```bash
# Check Temporal server
curl http://localhost:7233/health

# Check Temporal UI
curl http://localhost:8080
```

## First Steps

### Web Interface

1. Open `http://localhost:3000/temporal` in your browser
2. Click "Start HelloBackstage Workflow"
3. Monitor the workflow status in the table
4. View detailed execution logs at `http://localhost:8080` (Temporal UI)

### CLI Usage

```bash
# List available skills
./cli skill list

# Get info about a specific skill
./cli skill info compliance-check

# Start a simple workflow
./cli workflow start hello-backstage
```

### REST API

```bash
# Start a workflow
curl -X POST http://localhost:8081/workflow/start

# Check workflow status
curl http://localhost:8081/workflow/status?id=<workflow-id>
```

## Next Steps

Now that you have the platform running, explore:

- **[Skills Reference](../user-guide/skills-reference.md)** - Learn about the 28 available AI agent skills
- **[Workflows](../user-guide/workflows.md)** - Understand composite workflows and multi-agent orchestration
- **[Troubleshooting](../user-guide/troubleshooting.md)** - Solutions to common setup issues

## Architecture Overview

The AI Agents Sandbox consists of:

- **Temporal Engine** (Go backend) - Durable workflow orchestration
- **Multi-Agent Framework** - Specialized agents for compliance, security, and cost optimization
- **Interface Layer** - REST APIs, MCP server, CLI, and web interfaces
- **Infrastructure Emulator** - Safe simulation of cloud resources

All components run within defined **sandbox boundaries** to ensure safe experimentation without affecting production systems.

## Need Help?

If you encounter issues during setup, check the **[Troubleshooting](../user-guide/troubleshooting.md)** guide or refer to the main [README](../../README.md) for additional documentation.
