# Local Development Setup

## Zero-Touch Installation

After cloning the repository, run a single command to get a fully functional autonomous AI agents ecosystem running locally:

```bash
# One-command setup - installs everything and opens dashboard
./scripts/setup-local-ai-agents.sh
```

This script automatically:
- ✅ Installs Docker Desktop, kubectl, Helm, Minikube
- ✅ Starts local Kubernetes cluster with ingress
- ✅ Builds AI agent container images
- ✅ Deploys complete ecosystem (AI agents, skills, monitoring, dashboard)
- ✅ Sets up port forwarding for local access
- ✅ Opens dashboard in web browser

## What You Get

### 🌐 **Web Dashboard** (http://localhost:8080)
Real-time view of all AI agents and their activities:
- **Agent Status**: Which agents are running, thinking, or idle
- **Skill Execution**: Live view of autonomous skill workflows
- **Storage Metrics**: PVC usage, memory pruning, compression status
- **AI Inference**: Request throughput, model performance
- **Alert Dashboard**: Capacity warnings, anomaly detection

### 🤖 **Autonomous AI Agents**
- **Memory Agents**: Rust/Go/Python agents with persistent SQLite storage
- **Skill Integration**: 64 operational skills enhanced with AI analysis
- **Intelligent Operations**: Incident triage, cost optimization, deployment validation
- **Self-Management**: Auto-scaling storage, memory pruning, monitoring

### 🔄 **Temporal Workflows** (http://localhost:8081)
- Durable workflow orchestration
- Skill execution tracking
- Failure recovery and retries
- Workflow history and analytics

## Architecture

```
Local Machine
├── Minikube Cluster
│   ├── AI Memory Agents (Rust/Go/Python)
│   ├── Skills Framework (64 skills)
│   ├── Temporal Server
│   ├── Storage Management
│   └── Monitoring Stack
└── Host Machine
    ├── Port Forwarding (8080→dashboard, 8081→temporal)
    └── Web Browser → http://localhost:8080
```

## Prerequisites

**None required!** The setup script installs everything automatically.

If you prefer manual installation:

```bash
# Install prerequisites
brew install docker kubectl helm minikube

# Start cluster
minikube start -p ai-agents-local --memory=4096 --cpus=2

# Deploy ecosystem
./scripts/deploy-ai-agents-ecosystem.sh
```

## Usage Examples

### View Agent Activity
```bash
# Watch real-time agent logs
kubectl logs -f deployment/memory-agent-rust -n ai-infrastructure

# Check agent status
kubectl get pods -n ai-infrastructure
```

### Access Services
```bash
# Dashboard
open http://localhost:8080

# Temporal UI
open http://localhost:8081

# Minikube dashboard
minikube dashboard -p ai-agents-local
```

### Stop/Start
```bash
# Stop local setup (keeps cluster)
./scripts/stop-local-setup.sh

# Restart
./scripts/setup-local-ai-agents.sh
```

## Agent Activities Dashboard

The dashboard shows real-time insights into agent behavior:

### 🤖 Agent States
- **🟢 Active**: Processing inference requests
- **🟡 Thinking**: Analyzing data, making decisions
- **⚪ Idle**: Waiting for tasks
- **🔴 Error**: Recovery in progress

### 📊 Metrics
- **Inference Requests**: Per minute, success rate
- **Skill Executions**: Completed workflows, success rate
- **Storage Usage**: PVC utilization, growth trends
- **Memory Management**: Pruning cycles, compression savings

### 🔄 Autonomous Decisions
- **Capacity Planning**: "Detected 80% storage usage → expanding PVC"
- **Incident Response**: "High latency detected → triggering rollback"
- **Cost Optimization**: "Identified $500/month savings → implementing"

## Troubleshooting

### Minikube Issues
```bash
# Reset cluster
minikube delete -p ai-agents-local
./scripts/setup-local-ai-agents.sh
```

### Docker Issues
```bash
# Check Docker status
docker ps
docker system df

# Restart Docker Desktop
```

### Port Conflicts
```bash
# Check port usage
lsof -i :8080
lsof -i :8081

# Kill conflicting processes
./scripts/stop-local-setup.sh
```

## Resource Requirements

- **RAM**: 4GB minimum (8GB recommended)
- **CPU**: 2 cores minimum (4 cores recommended)
- **Disk**: 20GB free space
- **Network**: Internet connection for image downloads

## Next Steps

After setup, explore:
1. **Agent Dashboard**: Watch autonomous decision-making
2. **Skill Execution**: Trigger skills and observe AI enhancement
3. **Storage Management**: Monitor auto-scaling behavior
4. **Custom Skills**: Add your own AI-enhanced skills

The system demonstrates **fully autonomous AI-powered infrastructure management** running entirely locally!
