# AI Agents Complete Guide

## Overview

This guide provides comprehensive documentation for the AI agents ecosystem deployed by the GitOps Infrastructure Control Plane quickstart, including detailed information about the RAG chatbot with voice support, agent capabilities, and system architecture.

## Table of Contents

1. [Quickstart Deployment](#quickstart-deployment)
2. [AI Agents Ecosystem](#ai-agents-ecosystem)
3. [RAG Chatbot with Voice Support](#rag-chatbot-with-voice-support)
4. [Agent Capabilities](#agent-capabilities)
5. [System Architecture](#system-architecture)
6. [Autonomy and Safety](#autonomy-and-safety)
7. [Access and Usage](#access-and-usage)
8. [Troubleshooting](#troubleshooting)

## Quickstart Deployment

### What Gets Deployed

The quickstart script (`./core/scripts/automation/quickstart.sh`) deploys a complete AI-powered GitOps infrastructure:

```bash
# One-command MVP setup with AI agents and dashboard
./core/scripts/automation/quickstart.sh
```

**Core Components:**
1. **Bootstrap Cluster** - Recovery anchor for hub cluster
2. **Hub Cluster** - Runs Flux, Crossplane with Kubernetes Provider, Cluster API
3. **Spoke Cluster** - Local kind cluster for workloads
4. **AI Agents Ecosystem** - 64+ operational skills with Temporal orchestration
5. **Interactive Dashboard** - Real-time monitoring and control with FastAPI backend

### Manual Deployment Steps

If you prefer to run steps manually:

```bash
# 1. Validate your environment
./core/scripts/automation/prerequisites.sh

# 2. Setup GitOps configuration
./core/scripts/automation/setup-gitops-config.sh

# 3. Create bootstrap cluster (recovery anchor)
./core/scripts/infrastructure/create-bootstrap-cluster.sh

# 4. Create hub cluster (GitOps control plane)
./core/scripts/automation/create-hub-cluster.sh --provider kind --bootstrap-kubeconfig bootstrap-kubeconfig

# 5. Install Crossplane with Kubernetes provider for local development
./core/scripts/automation/install-crossplane.sh --providers local

# 6. Create spoke cluster (MVP - local emulation)
./core/scripts/automation/create-spoke-clusters.sh

# 7. Deploy AI agents ecosystem with dashboard
./core/scripts/automation/deploy-ai-agents-ecosystem.sh
```

## AI Agents Ecosystem

### Core Components

#### Memory Agents
- **Rust Implementation**: High-performance memory agent with Llama.cpp backend
- **Go Implementation**: Orchestration integration with Ollama fallback
- **Python Implementation**: ML/AI prototyping with transformers support
- **Storage**: 10Gi PVC with SQLite persistence
- **Inference**: Local inference with llama.cpp (privacy-focused)

#### Temporal Orchestration
- **Server**: Temporal workflow coordination
- **Workers**: Go-based agents executing 64+ skills
- **State**: PostgreSQL backend for workflow persistence
- **Monitoring**: Built-in metrics and audit logging

#### Dashboard System
- **Frontend**: React-based interactive dashboard
- **Backend**: FastAPI with real-time APIs
- **API Documentation**: Auto-generated at `/docs` endpoint
- **Monitoring**: Live agent status and performance metrics

### Agent Memory Types

1. **Episodic Memory**: Conversation history across sessions
2. **Semantic Memory**: Learned concepts and entity relationships
3. **Procedural Memory**: Skill execution patterns and outcomes
4. **Working Memory**: Current session context

## RAG Chatbot with Voice Support

### Comprehensive Data Sources

The RAG (Retrieval-Augmented Generation) chatbot integrates with 9 data sources:

#### 1. SQLite (Agent Memory)
- **Purpose**: Agent conversation history, episodic memory, semantic learning
- **Access**: `http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080`
- **Use Case**: Context about previous operations, learned patterns

#### 2. PostgreSQL with pgvector
- **Purpose**: Dashboard state + document embeddings
- **Access**: Direct connection + dashboard APIs
- **Use Case**: Operational data, indexed documentation, vector search

#### 3. Kubernetes API
- **Purpose**: Live cluster state, resource status, events
- **Access**: Kubernetes API server
- **Use Case**: Current infrastructure state, health information

#### 4. Temporal Workflows
- **Purpose**: Workflow execution history, skill outcomes
- **Access**: `temporal-frontend.ai-infrastructure.svc.cluster.local:7233`
- **Use Case**: Historical operation patterns, troubleshooting context

#### 5. Dashboard APIs
- **Purpose**: Agent status, skill execution, system metrics
- **Access**: `/api/v1/agents`, `/api/v1/skills`, `/api/v1/system/metrics`
- **Use Case**: Real-time system state, performance data

#### 6. File System Documentation
- **Purpose**: AGENTS.md, skills docs, configuration files
- **Access**: File system or Git repository
- **Use Case**: Static knowledge base, procedures

#### 7. K8sGPT Analysis
- **Purpose**: AI-powered Kubernetes cluster analysis and troubleshooting
- **Access**: `http://k8sgpt-service:8080/api/analyze`
- **Use Case**: Intelligent cluster insights, problem diagnosis

#### 8. Flux CD APIs
- **Purpose**: GitOps deployment state, synchronization status
- **Access**: Flux Kubernetes API and custom resources
- **Use Case**: Deployment history, sync status, drift detection

#### 9. Argo CD APIs
- **Purpose**: Application deployment state, health checks
- **Access**: Argo CD API server
- **Use Case**: Application lifecycle, deployment strategies

### Voice Chat Features

#### Speech Recognition
- **Technology**: Web Speech API (webkitSpeechRecognition)
- **Languages**: English (US/UK), Spanish, French
- **Real-time**: Interim results and continuous recognition
- **Auto-send**: Automatically sends recognized speech

#### Text-to-Speech
- **Technology**: Speech Synthesis API
- **Voices**: Default, female, male options
- **Controls**: Adjustable speed (0.5x-2x) and pitch (0.5x-2x)
- **Settings**: Persistent configuration in localStorage

#### Voice Interface
```html
<!-- Voice chat accessible at: http://localhost:8080/voice-chat -->
<div class="voice-controls">
    <button class="voice-btn" id="voiceToggle">
        <span>🎤</span>
        <span>Click to Speak</span>
    </button>
    <button class="voice-btn" id="settingsToggle">
        <span>⚙️</span>
        <span>Settings</span>
    </button>
</div>
```

## Agent Capabilities

### 64+ Operational Skills

#### Infrastructure Management
- **Cost Optimization**: Cloud spend analysis and resource right-sizing
- **Security Auditing**: Compliance checks and vulnerability scanning
- **Cluster Management**: Health monitoring, auto-scaling, troubleshooting
- **Network Monitoring**: Traffic analysis and connectivity checks

#### Deployment Operations
- **Deployment Management**: Rollouts, canary deployments, blue-green deployments
- **GitOps Synchronization**: Flux and ArgoCD status monitoring
- **Resource Planning**: Capacity planning and resource allocation
- **Backup Management**: Automated backup operations and recovery

#### Analysis and Monitoring
- **Log Analysis**: Pattern detection and anomaly identification
- **Performance Tuning**: Resource optimization and bottleneck resolution
- **Metrics Collection**: Custom metrics and alerting
- **Health Checks**: Comprehensive system health monitoring

#### Compliance and Governance
- **Compliance Checking**: Policy validation and audit trails
- **Deletion Guards**: Protection against accidental resource deletion
- **Naming Conventions**: Automated resource naming validation
- **Required Labels**: Enforce metadata standards

### Skill Execution Pattern

```
User Request → Skill Selection → Structured JSON Plan → GitOps Pipeline → Kubernetes Reconciliation
```

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                         │
│  ┌─────────────────┐  ┌─────────────────────────────────┐   │
│  │   Dashboard     │  │        Voice Chatbot          │   │
│  │   (React)      │  │     (Web Speech API)         │   │
│  └─────────────────┘  └─────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                RAG Orchestration Layer                       │
│              (Dashboard Backend API)                         │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Query     │ │   Context   │ │     Qwen                 │ │
│  │  Analyzer   │ │   Builder   │ │   Interface              │ │
│  │             │ │             │ │ (llama.cpp)              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└───────────┬───────────────────┬───────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────────┐  ┌───────────────────────────────────┐
│   Data Source Layer    │  │       PostgreSQL + pgvector        │
│                        │  │                                     │
│ ┌─────────────────────┐│  │ ┌─────────────────────────────────┐ │
│ │ SQLite (Agent Mem) ││  │ │ Dashboard State                 │ │
│ │ PostgreSQL (State) ││  │ │ Document Embeddings              │ │
│ │ Kubernetes API     ││  │ │ Vector Search Index             │ │
│ │ Temporal Workflows ││  │ └─────────────────────────────────┘ │
│ │ Dashboard APIs     ││  │                                     │
│ │ File System Docs   ││  │ ┌─────────────────────────────────┐ │
│ │ K8sGPT Analysis    ││  │ │ RAG Documents Table              │ │
│ │ Flux CD APIs       ││  │ │ (content, embedding, source)     │ │
│ │ Argo CD APIs       ││  │ └─────────────────────────────────┘ │
│ └─────────────────────┘│  │                                     │
│                        │  └───────────────────────────────────┘
└───────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│              Execution Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │
│  │   Temporal  │ │   Memory    │ │   GitOps       │ │
│  │  Workflows  │ │   Agents    │ │   Pipeline     │ │
│  │             │ │             │ │ (Flux/ArgoCD) │ │
│  └─────────────┘ └─────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Frontend
- **React**: Modern UI framework
- **Chart.js**: Data visualization
- **Feather Icons**: Icon library
- **Web Speech API**: Voice recognition and synthesis

#### Backend
- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Primary database with pgvector extension
- **SQLite**: Agent memory storage
- **Temporal**: Workflow orchestration

#### AI/ML
- **Llama.cpp**: Local LLM inference
- **Qwen 2.5**: Lightweight 0.5B parameter model
- **pgvector**: Vector similarity search
- **RAG**: Retrieval-augmented generation

#### Infrastructure
- **Kubernetes**: Container orchestration
- **Flux CD**: GitOps continuous delivery
- **Argo CD**: Application deployment
- **Crossplane**: Multi-cloud resource management

## Autonomy and Safety

### Tool-Constrained Agent Pattern

The AI agents follow a **structured tool agent pattern** for safety:

- **LLM decides *what*** actions are needed
- **Deterministic system decides *how*** to execute them
- **No direct LLM execution** on clusters or infrastructure

### Autonomy Levels

#### Fully Autonomous Operations
- Status checks and monitoring
- Log analysis and reporting
- Performance metrics collection
- Health checks and diagnostics

#### Conditional Autonomy
- Resource scaling (within defined limits)
- Backup operations (following schedules)
- Compliance checks (reporting only)
- Cost analysis (recommendations only)

#### Human-Gated Operations
- Resource deletion/modification
- Security policy changes
- Cost changes > $100/day
- Production deployment changes

### Safety Mechanisms

#### GitOps Pipeline Integration
- All changes flow through GitOps pipelines
- Structured JSON plans only - no free-form LLM commands
- PR-tracked changes with audit trails
- Kubernetes reconciliation loops provide final safety layer

#### Risk Assessment
- Automatic risk level assignment for each operation
- Human approval required for high-risk operations
- Rollback capabilities for all changes
- Comprehensive logging and monitoring

#### Compliance and Governance
- Policy-as-code validation (OPA Rego policies)
- Deletion guards for critical resources
- Naming convention enforcement
- Required label validation

## Access and Usage

### Dashboard Access

```bash
# Port forward dashboard service
kubectl port-forward -n ai-infrastructure svc/agent-dashboard-service 8080:80

# Access in browser
open http://localhost:8080
```

### API Access

```bash
# Port forward API service
kubectl port-forward -n ai-infrastructure svc/dashboard-api-service 5000:5000

# Access API documentation
open http://localhost:5000/docs
```

### Voice Chat Access

```bash
# Access voice chat interface
open http://localhost:8080/voice-chat

# Or via main dashboard navigation
open http://localhost:8080
# Click "Voice Assistant" in navigation
```

### Memory Agent Access

```bash
# Port forward memory service
kubectl port-forward -n ai-infrastructure svc/agent-memory-service 8080:8080

# Test memory API
curl http://localhost:8080/health
```

### Temporal Web UI

```bash
# Port forward Temporal UI
kubectl port-forward -n ai-infrastructure svc/temporal-frontend 7233:7233

# Access Temporal dashboard
open http://localhost:7233
```

### Key API Endpoints

#### Dashboard APIs
- `GET /api/v1/agents` - List all active agents
- `GET /api/v1/skills` - List available skills
- `GET /api/v1/system/metrics` - System performance metrics
- `GET /api/v1/activity` - Recent activity feed

#### RAG Chat API
- `POST /api/v1/rag/query` - Query RAG system
- `GET /api/v1/rag/sources` - List data sources
- `GET /api/v1/rag/health` - RAG system health

#### Memory APIs
- `GET /health` - Memory service health
- `POST /memory/store` - Store conversation memory
- `GET /memory/retrieve` - Retrieve conversation history

## Troubleshooting

### Common Issues

#### Dashboard Not Accessible
```bash
# Check dashboard pod status
kubectl get pods -n ai-infrastructure -l component=agent-dashboard

# Check pod logs
kubectl logs -n ai-infrastructure deployment/agent-dashboard

# Restart dashboard
kubectl rollout restart deployment/agent-dashboard -n ai-infrastructure
```

#### Voice Chat Not Working
```bash
# Check browser support
# Open browser developer console and look for:
# - "Speech recognition not supported" error
# - Microphone permission issues

# Test microphone access
# In browser: Settings > Privacy > Microphone > Allow localhost
```

#### Memory Agent Issues
```bash
# Check memory agent pods
kubectl get pods -n ai-infrastructure -l component=agent-memory

# Check PVC status
kubectl get pvc -n ai-infrastructure

# Restart memory agent
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure
```

#### Temporal Workflow Issues
```bash
# Check Temporal server
kubectl get pods -n ai-infrastructure -l app=temporal

# Check workflow history
kubectl port-forward -n ai-infrastructure svc/temporal-frontend 7233:7233
# Open http://localhost:7233 to view workflows

# Restart Temporal workers
kubectl rollout restart deployment/temporal-workers -n ai-infrastructure
```

### Debug Commands

#### System Health Check
```bash
# Quick system health overview
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure
kubectl get pvc -n ai-infrastructure
```

#### Log Analysis
```bash
# Recent logs from all components
kubectl logs -n ai-infrastructure --since=1h --all-containers=true

# Specific component logs
kubectl logs -n ai-infrastructure deployment/agent-dashboard --tail=100
kubectl logs -n ai-infrastructure deployment/dashboard-api --tail=100
kubectl logs -n ai-infrastructure deployment/agent-memory-rust --tail=100
```

#### Performance Monitoring
```bash
# Resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/v1/agents
```

### Recovery Procedures

#### Full System Restart
```bash
# Restart all AI infrastructure components
kubectl rollout restart deployment -n ai-infrastructure --all

# Wait for readiness
kubectl wait --for=condition=available --timeout=300s deployment --all -n ai-infrastructure
```

#### Data Recovery
```bash
# Backup current state
kubectl get pvc -n ai-infrastructure -o yaml > pvc-backup.yaml

# Export agent memory
kubectl exec -n ai-infrastructure deployment/agent-memory-rust -- \
  sqlite3 /data/memory.db ".backup /tmp/memory-backup.db"

# Copy backup locally
kubectl cp -n ai-infrastructure deployment/agent-memory-rust:/tmp/memory-backup.db ./memory-backup.db
```

## Development and Customization

### Adding New Skills

1. **Create Skill Definition**
```yaml
# .agents/new-skill/SKILL.md
---
name: new-skill
description: "Description of what this skill does"
metadata:
  risk_level: low
  autonomy: conditional
  layer: temporal
  human_gate: none
---
```

2. **Implement Skill Logic**
```go
// core/ai/skills/new-skill/main.go
package main

func ExecuteSkill(ctx context.Context, input SkillInput) (SkillOutput, error) {
    // Skill implementation
    return result, nil
}
```

3. **Register with Temporal**
```go
// Register workflow and activities
workflow.Register(NewSkillWorkflow)
activity.Register(NewSkillActivity)
```

### Customizing Voice Chat

#### Adding New Languages
```javascript
// In voice-chatbot.html
const languages = {
    'en-US': 'English (US)',
    'en-GB': 'English (UK)',
    'es-ES': 'Spanish',
    'fr-FR': 'French',
    'de-DE': 'German',  // Add new language
    'it-IT': 'Italian'   // Add new language
};
```

#### Custom Voice Settings
```javascript
// Add custom voice parameters
const voiceSettings = {
    rate: 1.0,        // Speech rate (0.1-10)
    pitch: 1.0,       // Voice pitch (0-2)
    volume: 1.0,      // Volume (0-1)
    voice: 'default'   // Voice selection
};
```

### Extending RAG Data Sources

#### Adding New Data Source
```python
# In dashboard backend
class NewDataSource:
    def __init__(self):
        self.name = "new-source"
        self.endpoint = "http://new-source-service:8080"
    
    async def query(self, query_text):
        # Implementation for querying new data source
        return results

# Register data source
rag_system.register_data_source(NewDataSource())
```

## Best Practices

### Security
- Use RBAC to restrict agent permissions
- Enable audit logging for all operations
- Regular security scans of agent code
- Principle of least privilege for service accounts

### Performance
- Monitor resource usage and set appropriate limits
- Use caching for frequently accessed data
- Optimize database queries and indexing
- Implement circuit breakers for external calls

### Reliability
- Implement health checks and readiness probes
- Use graceful shutdown for all services
- Configure automatic restart policies
- Backup critical data regularly

### Monitoring
- Set up comprehensive metrics collection
- Configure alerts for critical failures
- Use structured logging with correlation IDs
- Regular performance testing and optimization

---

**For more information, see:**
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [COMPREHENSIVE-RAG-IMPLEMENTATION-PLAN.md](COMPREHENSIVE-RAG-IMPLEMENTATION-PLAN.md) - RAG architecture details
- [AGENTS.md](AGENTS.md) - Agent system overview
- [OVERVIEW.md](OVERVIEW.md) - Complete system documentation
