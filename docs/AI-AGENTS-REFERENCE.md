# AI Agents Reference Guide

## Overview

This comprehensive reference guide provides detailed technical specifications, API documentation, configuration examples, and troubleshooting information for the Cloud AI Agents ecosystem.

## Architecture Reference

### System Components

#### Memory Agents
```yaml
Memory Agent Specifications:
  Architecture: Multi-language (Rust, Go, Python)
  Storage: SQLite with 10Gi persistent volume
  Backend: Llama.cpp for AI inference
  API: RESTful HTTP endpoints on port 8080
  
  Key Features:
    - Persistent conversation history
    - Entity and topic extraction
    - Memory consolidation
    - Cross-agent knowledge sharing
    
  Deployment:
    Replicas: 1 (horizontal scaling supported)
    Resources: 256Mi-512Mi memory, 100m-500m CPU
    Storage: 10Gi PVC with encryption
```

#### Skills Framework
```yaml
Skills Framework Specifications:
  Total Skills: 64 operational skills
  Categories: Cost, Security, Monitoring, Deployment, Infrastructure, Analysis
  
  Skill Interface:
    type Skill interface {
        Execute(ctx context.Context, input SkillInput) (*SkillOutput, error)
        Validate(input SkillInput) error
        GetMetadata() SkillMetadata
    }
  
  Execution Model:
    - Temporal workflow orchestration
    - Asynchronous execution
    - Result caching and aggregation
    - Error handling and retry logic
```

#### Temporal Orchestration
```yaml
Temporal Cluster Specifications:
  Frontend: API server for workflow execution
  History: Workflow state persistence (Cassandra)
  Matching: Task-to-worker routing
  Workers: Skill execution engines
  
  Configuration:
    Replicas: 1-3 (configurable)
    Storage: Cassandra cluster (1-3 nodes)
    Persistence: Workflow history and events
    Monitoring: Prometheus metrics and Grafana dashboards
```

### Data Models

#### Memory Agent Data Model
```go
// Memory agent data structures
type Memory struct {
    ID          string                 `json:"id" db:"id"`
    Source      string                 `json:"source" db:"source"`
    Summary     string                 `json:"summary" db:"summary"`
    Entities    []string               `json:"entities" db:"entities"`
    Topics      []string               `json:"topics" db:"topics"`
    Connections []Connection           `json:"connections" db:"connections"`
    Importance  float64                `json:"importance" db:"importance"`
    CreatedAt   time.Time              `json:"created_at" db:"created_at"`
    Consolidated bool                  `json:"consolidated" db:"consolidated"`
}

type Connection struct {
    TargetMemoryID string  `json:"target_memory_id"`
    Strength       float64 `json:"strength"`
    Type           string  `json:"type"`
}

type SkillInput struct {
    Parameters map[string]interface{} `json:"parameters"`
    Context    map[string]interface{} `json:"context"`
    Metadata   map[string]interface{} `json:"metadata"`
}

type SkillOutput struct {
    Result    interface{}            `json:"result"`
    Success   bool                   `json:"success"`
    Error     string                 `json:"error,omitempty"`
    Metadata  map[string]interface{} `json:"metadata"`
}
```

#### Workflow Data Model
```go
// Temporal workflow data structures
type WorkflowRequest struct {
    WorkflowID string                 `json:"workflow_id"`
    Type       string                 `json:"type"`
    Input      map[string]interface{} `json:"input"`
    Priority   int                    `json:"priority"`
    Timeout    time.Duration          `json:"timeout"`
}

type WorkflowExecution struct {
    ID            string                 `json:"id"`
    Type          string                 `json:"type"`
    Status        string                 `json:"status"`
    StartTime     time.Time              `json:"start_time"`
    EndTime       *time.Time             `json:"end_time,omitempty"`
    Duration      *time.Duration         `json:"duration,omitempty"`
    Input         map[string]interface{} `json:"input"`
    Output        map[string]interface{} `json:"output,omitempty"`
    Error         string                 `json:"error,omitempty"`
    AgentResults  []AgentResult          `json:"agent_results"`
}
```

## API Reference

### Memory Agent API

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "llamacpp": "healthy",
    "api": "healthy"
  }
}
```

#### Memory Operations

**Create Memory**
```http
POST /api/memories
Content-Type: application/json

{
  "source": "user-input",
  "summary": "User requested cost optimization for production cluster",
  "entities": ["production-cluster", "cost-optimization"],
  "topics": ["cost-management", "infrastructure"],
  "importance": 0.8
}
```

**Response:**
```json
{
  "id": "memory-12345",
  "source": "user-input",
  "summary": "User requested cost optimization for production cluster",
  "entities": ["production-cluster", "cost-optimization"],
  "topics": ["cost-management", "infrastructure"],
  "importance": 0.8,
  "created_at": "2024-03-15T10:30:00Z",
  "consolidated": false
}
```

**Get Memory**
```http
GET /api/memories/{id}
```

**Response:**
```json
{
  "id": "memory-12345",
  "source": "user-input",
  "summary": "User requested cost optimization for production cluster",
  "entities": ["production-cluster", "cost-optimization"],
  "topics": ["cost-management", "infrastructure"],
  "connections": [
    {
      "target_memory_id": "memory-67890",
      "strength": 0.7,
      "type": "related"
    }
  ],
  "importance": 0.8,
  "created_at": "2024-03-15T10:30:00Z",
  "consolidated": false
}
```

**Search Memories**
```http
GET /api/memories/search?q=cost-optimization&limit=10&offset=0
```

**Response:**
```json
{
  "memories": [
    {
      "id": "memory-12345",
      "source": "user-input",
      "summary": "User requested cost optimization for production cluster",
      "entities": ["production-cluster", "cost-optimization"],
      "topics": ["cost-management", "infrastructure"],
      "importance": 0.8,
      "created_at": "2024-03-15T10:30:00Z",
      "consolidated": false
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

**Update Memory**
```http
PUT /api/memories/{id}
Content-Type: application/json

{
  "summary": "Updated summary for cost optimization request",
  "importance": 0.9
}
```

**Delete Memory**
```http
DELETE /api/memories/{id}
```

#### Inference Operations

**Generate Text**
```http
POST /api/inference
Content-Type: application/json

{
  "prompt": "Analyze the cost optimization opportunities in this cluster configuration",
  "model": "qwen2.5:0.5b",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "text": "Based on the cluster configuration, I can identify several cost optimization opportunities...",
  "model": "qwen2.5:0.5b",
  "tokens_used": 245,
  "inference_time_ms": 1250,
  "created_at": "2024-03-15T10:30:00Z"
}
```

### Skills API

#### List Skills
```http
GET /api/skills
```

**Response:**
```json
{
  "skills": [
    {
      "id": "cost-analysis",
      "name": "Cost Analysis",
      "description": "Analyze cluster costs and identify optimization opportunities",
      "category": "cost-management",
      "version": "1.0.0",
      "parameters": {
        "cluster": {
          "type": "string",
          "required": true,
          "description": "Cluster name to analyze"
        },
        "time_range": {
          "type": "string",
          "required": false,
          "default": "7d",
          "description": "Time range for analysis"
        }
      }
    }
  ]
}
```

#### Execute Skill
```http
POST /api/skills/{skill_id}/execute
Content-Type: application/json

{
  "parameters": {
    "cluster": "production",
    "time_range": "7d"
  },
  "context": {
    "user_id": "user-123",
    "request_id": "req-456"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec-789",
  "skill_id": "cost-analysis",
  "status": "running",
  "started_at": "2024-03-15T10:30:00Z",
  "estimated_duration": "2m"
}
```

#### Get Skill Execution Status
```http
GET /api/skills/executions/{execution_id}
```

**Response:**
```json
{
  "execution_id": "exec-789",
  "skill_id": "cost-analysis",
  "status": "completed",
  "started_at": "2024-03-15T10:30:00Z",
  "completed_at": "2024-03-15T10:32:15Z",
  "duration_ms": 135000,
  "result": {
    "total_savings": "$1,234.56",
    "optimization_count": 5,
    "recommendations": [
      "Downsize underutilized nodes",
      "Use spot instances for workloads",
      "Enable autoscaling"
    ]
  },
  "error": null
}
```

### Dashboard API

#### System Status
```http
GET /api/cluster-status
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "components": {
    "agents": {
      "total": 3,
      "running": 2,
      "idle": 1,
      "error": 0
    },
    "skills": {
      "total": 64,
      "available": 58,
      "executing": 6,
      "failed": 0
    },
    "temporal": {
      "status": "healthy",
      "active_workflows": 12,
      "completed_today": 145
    }
  },
  "metrics": {
    "success_rate": 0.987,
    "avg_response_time_ms": 1250,
    "requests_per_minute": 45
  }
}
```

#### Agent Status
```http
GET /api/agents/status
```

**Response:**
```json
{
  "agents": [
    {
      "id": "agent-1",
      "name": "agent-memory-rust",
      "type": "rust",
      "status": "running",
      "last_activity": "2024-03-15T10:29:30Z",
      "skills_executed": 23,
      "success_rate": 0.987,
      "avg_duration_ms": 1100,
      "memory_usage_mb": 256,
      "cpu_usage_percent": 15.5
    }
  ]
}
```

## Configuration Reference

### Environment Variables

#### Memory Agent Configuration
```yaml
Environment Variables:
  DATABASE_PATH:
    Default: "/data/memory.db"
    Description: Path to SQLite database file
    
  INBOX_PATH:
    Default: "/data/inbox"
    Description: Path to inbox directory for incoming tasks
    
  BACKEND_PRIORITY:
    Default: "llama.cpp,ollama"
    Description: Priority order for inference backends
    
  LANGUAGE_PRIORITY:
    Default: "rust,go,python"
    Description: Priority order for agent languages
    
  OLLAMA_URL:
    Default: "http://ollama-service:11434"
    Description: URL for Ollama service (fallback)
    
  MODEL:
    Default: "qwen2.5:0.5b"
    Description: Default AI model to use
    
  LOG_LEVEL:
    Default: "info"
    Description: Logging level (debug, info, warn, error)
    
  METRICS_PORT:
    Default: "9090"
    Description: Port for Prometheus metrics
    
  HEALTH_PORT:
    Default: "8080"
    Description: Port for health checks
```

#### Temporal Configuration
```yaml
Temporal Environment Variables:
  TEMPORAL_ADDRESS:
    Default: "temporal-frontend:7233"
    Description: Temporal frontend address
    
  TEMPORAL_NAMESPACE:
    Default: "default"
    Description: Temporal namespace
    
  TEMPORAL_CLIENT_CERT_PATH:
    Default: ""
    Description: Path to client certificate
    
  TEMPORAL_CLIENT_KEY_PATH:
    Default: ""
    Description: Path to client private key
    
  TEMPORAL_SERVER_CA_PATH:
    Default: ""
    Description: Path to server CA certificate
```

### Configuration Files

#### Memory Agent Config
```yaml
# config/agent-memory.yaml
server:
  host: "0.0.0.0"
  port: 8080
  read_timeout: "30s"
  write_timeout: "30s"
  idle_timeout: "60s"

database:
  path: "/data/memory.db"
  max_connections: 10
  connection_timeout: "30s"
  vacuum_interval: "1h"

inference:
  backend: "llama.cpp"
  model: "qwen2.5:0.5b"
  max_tokens: 2048
  temperature: 0.7
  timeout: "30s"

memory:
  max_memories_per_search: 100
  consolidation_threshold: 0.8
  consolidation_interval: "6h"
  importance_decay_rate: 0.1

logging:
  level: "info"
  format: "json"
  output: "stdout"
  file_path: "/var/log/agent-memory.log"

metrics:
  enabled: true
  port: 9090
  path: "/metrics"
  interval: "30s"

security:
  enable_auth: true
  jwt_secret: "your-secret-key"
  token_duration: "24h"
  rate_limit: 100
```

#### Skills Configuration
```yaml
# config/skills.yaml
skills:
  cost-analysis:
    enabled: true
    version: "1.0.0"
    timeout: "5m"
    max_retries: 3
    parameters:
      cluster:
        type: "string"
        required: true
        validation: "^[a-z0-9-]+$"
      time_range:
        type: "string"
        required: false
        default: "7d"
        validation: "^[1-9][0-9]*[dwmy]$"

  security-scan:
    enabled: true
    version: "1.2.0"
    timeout: "10m"
    max_retries: 2
    parameters:
      target:
        type: "string"
        required: true
        validation: "^(cluster|namespace|pod)$"
      severity:
        type: "string"
        required: false
        default: "medium"
        validation: "^(low|medium|high|critical)$"

  cluster-health:
    enabled: true
    version: "1.1.0"
    timeout: "3m"
    max_retries: 3
    parameters:
      checks:
        type: "array"
        required: false
        default: ["pods", "nodes", "services"]
        validation: "^(pods|nodes|services|storage|network)$"
```

### Kubernetes Resources

#### Deployment Templates
```yaml
# deployment-template.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust
  namespace: ai-infrastructure
  labels:
    component: agent-memory
    language: rust
    version: v1.0.0
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      component: agent-memory
      language: rust
  template:
    metadata:
      labels:
        component: agent-memory
        language: rust
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: ai-agents-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      initContainers:
      - name: init-memory-db
        image: alpine:3.18
        command: ["sh", "-c"]
        args:
        - |
          if [ ! -f /data/memory.db ]; then
            echo "Initializing empty memory.db"
            touch /data/memory.db
            chmod 600 /data/memory.db
          else
            echo "Using existing memory.db"
          fi
        volumeMounts:
        - name: memory-storage
          mountPath: /data
        resources:
          requests:
            memory: "32Mi"
            cpu: "10m"
          limits:
            memory: "64Mi"
            cpu: "50m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      containers:
      - name: agent-memory
        image: agent-memory-rust:v1.0.0
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        env:
        - name: DATABASE_PATH
          value: "/data/memory.db"
        - name: INBOX_PATH
          value: "/data/inbox"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: MODEL
          value: "qwen2.5:0.5b"
        - name: LOG_LEVEL
          value: "info"
        - name: METRICS_PORT
          value: "9090"
        - name: HEALTH_PORT
          value: "8080"
        volumeMounts:
        - name: memory-storage
          mountPath: /data
          readOnly: false
        - name: config
          mountPath: /config
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
      volumes:
      - name: memory-storage
        persistentVolumeClaim:
          claimName: agent-memory-pvc
      - name: config
        configMap:
          name: agent-memory-config
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
      dnsPolicy: ClusterFirst
      schedulerName: default-scheduler
```

## Troubleshooting Reference

### Common Issues

#### Pod Startup Issues
```bash
# Check pod status and events
kubectl describe pod <pod-name> -n ai-infrastructure

# Check recent events
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -20

# Check resource constraints
kubectl describe node <node-name> | grep -A 10 "Allocated resources"

# Check PVC status
kubectl get pvc -n ai-infrastructure
kubectl describe pvc agent-memory-pvc -n ai-infrastructure
```

#### Database Issues
```bash
# Check database connectivity
kubectl exec -it <pod-name> -n ai-infrastructure -- \
  sqlite3 /data/memory.db ".tables"

# Check database integrity
kubectl exec -it <pod-name> -n ai-infrastructure -- \
  sqlite3 /data/memory.db "PRAGMA integrity_check;"

# Check database size
kubectl exec -it <pod-name> -n ai-infrastructure -- \
  ls -lh /data/memory.db

# Backup database
kubectl exec <pod-name> -n ai-infrastructure -- \
  sqlite3 /data/memory.db ".backup /backup/memory-$(date +%Y%m%d).db"
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# Check metrics
curl -s http://localhost:9090/metrics | grep agent_execution_duration

# Check logs for errors
kubectl logs <pod-name> -n ai-infrastructure --since=1h | grep -i error

# Check network connectivity
kubectl exec -it <pod-name> -n ai-infrastructure -- \
  ping temporal-frontend.ai-infrastructure.svc.cluster.local
```

#### API Issues
```bash
# Test API endpoints
curl -v http://localhost:8080/health
curl -v http://localhost:8080/api/memories

# Check service endpoints
kubectl get endpoints -n ai-infrastructure

# Test service connectivity
kubectl run test-pod --image=busybox --rm -it -- \
  wget -qO- http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080/health
```

### Debug Commands

#### Memory Agent Debug
```bash
# Enable debug logging
kubectl set env deployment/agent-memory-rust LOG_LEVEL=debug -n ai-infrastructure

# Restart with debug mode
kubectl rollout restart deployment/agent-memory-rust -n ai-infrastructure

# Access debug shell
kubectl exec -it <pod-name> -n ai-infrastructure -- /bin/sh

# Monitor debug logs
kubectl logs -f <pod-name> -n ai-infrastructure | grep DEBUG
```

#### Temporal Debug
```bash
# Check Temporal status
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- \
  tctl --ns default cluster health

# List workflows
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- \
  tctl --ns default workflow list

# Describe workflow
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- \
  tctl --ns default workflow describe --workflow-id <workflow-id>

# Check worker status
kubectl exec -it temporal-frontend-xxx -n ai-infrastructure -- \
  tctl --ns default worker list
```

#### Skills Debug
```bash
# Check skill execution
kubectl logs -f deployment/skills-orchestrator -n ai-infrastructure

# Test skill directly
curl -X POST http://localhost:5000/api/skills/cost-analysis/execute \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"cluster": "test"}}'

# Check skill registration
kubectl exec -it skills-orchestrator-xxx -n ai-infrastructure -- \
  python -c "import skills; print(skills.list_skills())"
```

### Performance Tuning

#### Database Optimization
```sql
-- SQLite optimization commands
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456; -- 256MB
PRAGMA optimize;
VACUUM;
ANALYZE;
```

#### Resource Tuning
```yaml
# Resource limits for production
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-memory-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-memory-rust
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Development Reference

### Local Development Setup

#### Development Environment
```bash
# Clone repository
git clone https://github.com/your-org/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# Setup kind cluster
kind create cluster --name ai-agents-dev --config config/kind-dev.yaml

# Build memory agent
cd infrastructure/ai-inference/rust-agent
cargo build --release

# Build Docker image
docker build -t agent-memory-rust:dev .

# Load image into kind
kind load docker-image agent-memory-rust:dev --name ai-agents-dev

# Deploy for development
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-memory-rust-dev
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent-memory-rust-dev
  template:
    metadata:
      labels:
        app: agent-memory-rust-dev
    spec:
      containers:
      - name: agent-memory
        image: agent-memory-rust:dev
        ports:
        - containerPort: 8080
        env:
        - name: LOG_LEVEL
          value: "debug"
        - name: DATABASE_PATH
          value: "/tmp/memory.db"
EOF
```

#### Testing Framework
```go
// tests/integration_test.go
package tests

import (
    "context"
    "testing"
    "time"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestMemoryAgentIntegration(t *testing.T) {
    // Setup test environment
    ctx := context.Background()
    
    // Test health check
    resp, err := http.Get("http://localhost:8080/health")
    require.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)
    
    // Test memory creation
    memory := Memory{
        Source:   "test",
        Summary:  "Test memory",
        Entities: []string{"test"},
        Topics:   []string{"testing"},
    }
    
    created, err := createMemory(ctx, memory)
    require.NoError(t, err)
    assert.NotEmpty(t, created.ID)
    
    // Test memory retrieval
    retrieved, err := getMemory(ctx, created.ID)
    require.NoError(t, err)
    assert.Equal(t, memory.Summary, retrieved.Summary)
    
    // Test memory search
    results, err := searchMemories(ctx, "test", 10, 0)
    require.NoError(t, err)
    assert.Len(t, results.Memories, 1)
    
    // Test inference
    inferenceResp, err := generateText(ctx, InferenceRequest{
        Prompt:     "Test prompt",
        Model:      "qwen2.5:0.5b",
        MaxTokens:  100,
        Temperature: 0.7,
    })
    require.NoError(t, err)
    assert.NotEmpty(t, inferenceResp.Text)
}

func TestSkillExecution(t *testing.T) {
    ctx := context.Background()
    
    // Test skill execution
    execution, err := executeSkill(ctx, "cost-analysis", SkillInput{
        Parameters: map[string]interface{}{
            "cluster":    "test-cluster",
            "time_range": "7d",
        },
    })
    require.NoError(t, err)
    assert.NotEmpty(t, execution.ExecutionID)
    
    // Wait for completion
    for i := 0; i < 30; i++ {
        status, err := getExecutionStatus(ctx, execution.ExecutionID)
        require.NoError(t, err)
        
        if status.Status == "completed" {
            assert.NotNil(t, status.Result)
            return
        }
        
        time.Sleep(1 * time.Second)
    }
    
    t.Fatal("Skill execution did not complete within timeout")
}
```

### Code Quality

#### Rust Development
```rust
// src/lib.rs - Memory agent implementation
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

pub struct MemoryAgent {
    database: Arc<RwLock<sqlx::SqlitePool>>,
    inference: Arc<dyn InferenceBackend>,
    config: Config,
}

impl MemoryAgent {
    pub async fn new(config: Config) -> Result<Self, Error> {
        let database = Arc::new(RwLock::new(
            sqlx::sqlite::SqlitePool::connect(&config.database_url).await?
        ));
        
        let inference: Arc<dyn InferenceBackend> = match config.backend.as_str() {
            "llamacpp" => Arc::new(LlamaCppBackend::new(&config.model_path).await?),
            "ollama" => Arc::new(OllamaBackend::new(&config.ollama_url).await?),
            _ => return Err(Error::InvalidBackend(config.backend)),
        };
        
        Ok(Self {
            database,
            inference,
            config,
        })
    }
    
    pub async fn create_memory(&self, memory: CreateMemoryRequest) -> Result<Memory, Error> {
        let db = self.database.read().await;
        
        let memory = sqlx::query_as!(
            Memory,
            r#"
            INSERT INTO memories (source, summary, entities, topics, importance)
            VALUES (?1, ?2, ?3, ?4, ?5)
            RETURNING id, source, summary, entities, topics, importance, created_at, consolidated
            "#,
            memory.source,
            memory.summary,
            serde_json::to_string(&memory.entities)?,
            serde_json::to_string(&memory.topics)?,
            memory.importance
        )
        .fetch_one(&*db)
        .await?;
        
        Ok(memory)
    }
    
    pub async fn search_memories(&self, query: &str, limit: i64, offset: i64) -> Result<SearchResult, Error> {
        let db = self.database.read().await;
        
        let memories = sqlx::query_as!(
            Memory,
            r#"
            SELECT id, source, summary, entities, topics, importance, created_at, consolidated
            FROM memories
            WHERE summary LIKE ?1 OR entities LIKE ?1 OR topics LIKE ?1
            ORDER BY created_at DESC
            LIMIT ?2 OFFSET ?3
            "#,
            format!("%{}%", query),
            limit,
            offset
        )
        .fetch_all(&*db)
        .await?;
        
        let total = sqlx::query_scalar!(
            "SELECT COUNT(*) FROM memories WHERE summary LIKE ?1 OR entities LIKE ?1 OR topics LIKE ?1",
            format!("%{}%", query)
        )
        .fetch_one(&*db)
        .await?;
        
        Ok(SearchResult {
            memories,
            total,
            limit,
            offset,
        })
    }
}
```

#### Go Development
```go
// pkg/memory/agent.go - Memory agent implementation
package memory

import (
    "context"
    "database/sql"
    "encoding/json"
    "time"
    
    "github.com/jmoiron/sqlx"
    _ "github.com/mattn/go-sqlite3"
)

type Agent struct {
    db        *sqlx.DB
    inference InferenceBackend
    config    Config
}

func NewAgent(config Config) (*Agent, error) {
    db, err := sqlx.Open("sqlite3", config.DatabasePath)
    if err != nil {
        return nil, err
    }
    
    // Initialize database schema
    if err := initSchema(db); err != nil {
        return nil, err
    }
    
    var inference InferenceBackend
    switch config.Backend {
    case "llamacpp":
        inference = NewLlamaCppBackend(config.ModelPath)
    case "ollama":
        inference = NewOllamaBackend(config.OllamaURL)
    default:
        return nil, fmt.Errorf("unsupported backend: %s", config.Backend)
    }
    
    return &Agent{
        db:        db,
        inference: inference,
        config:    config,
    }, nil
}

func (a *Agent) CreateMemory(ctx context.Context, req CreateMemoryRequest) (*Memory, error) {
    entitiesJSON, err := json.Marshal(req.Entities)
    if err != nil {
        return nil, err
    }
    
    topicsJSON, err := json.Marshal(req.Topics)
    if err != nil {
        return nil, err
    }
    
    query := `
        INSERT INTO memories (source, summary, entities, topics, importance)
        VALUES (?, ?, ?, ?, ?)
        RETURNING id, source, summary, entities, topics, importance, created_at, consolidated
    `
    
    var memory Memory
    err = a.db.QueryRowContext(ctx, query,
        req.Source, req.Summary, string(entitiesJSON), string(topicsJSON), req.Importance,
    ).Scan(
        &memory.ID, &memory.Source, &memory.Summary, &memory.Entities, &memory.Topics,
        &memory.Importance, &memory.CreatedAt, &memory.Consolidated,
    )
    
    if err != nil {
        return nil, err
    }
    
    return &memory, nil
}

func (a *Agent) SearchMemories(ctx context.Context, query string, limit, offset int) (*SearchResult, error) {
    searchQuery := "%" + query + "%"
    
    // Get memories
    rows, err := a.db.QueryxContext(ctx, `
        SELECT id, source, summary, entities, topics, importance, created_at, consolidated
        FROM memories
        WHERE summary LIKE ? OR entities LIKE ? OR topics LIKE ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    `, searchQuery, searchQuery, searchQuery, limit, offset)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var memories []Memory
    for rows.Next() {
        var memory Memory
        if err := rows.StructScan(&memory); err != nil {
            return nil, err
        }
        memories = append(memories, memory)
    }
    
    // Get total count
    var total int
    err = a.db.QueryRowContext(ctx, `
        SELECT COUNT(*) FROM memories
        WHERE summary LIKE ? OR entities LIKE ? OR topics LIKE ?
    `, searchQuery, searchQuery, searchQuery).Scan(&total)
    if err != nil {
        return nil, err
    }
    
    return &SearchResult{
        Memories: memories,
        Total:    total,
        Limit:    limit,
        Offset:   offset,
    }, nil
}
```

## Conclusion

This reference guide provides comprehensive technical documentation for the AI Agents ecosystem. It serves as a complete resource for developers, operators, and system administrators working with the platform.

For additional information, refer to the specific guides in the documentation directory:
- Architecture Guide: System design and component interactions
- Deployment Guide: Installation and setup procedures
- Operation Guide: Day-to-day management procedures
- Monitoring Guide: Observability and alerting setup
- Security Guide: Security best practices and compliance

The reference guide is continuously updated to reflect the latest features and improvements in the AI Agents ecosystem.
