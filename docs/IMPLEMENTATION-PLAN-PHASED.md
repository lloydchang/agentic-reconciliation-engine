# AI Agents Implementation Plan: Phased Approach

## 🎯 **Strategy: Option 1 First, Option 2 Afterward**

### **Implementation Order:**
1. **Phase 1:** Complete Temporal Worker Model (Option 1)
2. **Phase 2:** Complete Independent Agent Model (Option 2)

---

## 🚀 **Phase 1: Temporal Worker Model**

### **1.1 Deploy Temporal Server**
**File to Create:** `core/resources/infrastructure/temporal/temporal-server-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-server
  namespace: ai-infrastructure
  labels:
    component: temporal-server
    app: temporal
spec:
  replicas: 1
  selector:
    matchLabels:
      component: temporal-server
      app: temporal
  template:
    metadata:
      labels:
        component: temporal-server
        app: temporal
    spec:
      containers:
      - name: temporal
        image: temporalio/server:1.22.0
        ports:
        - containerPort: 7233
        - containerPort: 7234
        env:
        - name: DB
          value: postgresql
        - name: DB_PORT
          value: "5432"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: temporal-secrets
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: temporal-secrets
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 7233
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 7233
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: temporal-server-service
  namespace: ai-infrastructure
spec:
  selector:
    component: temporal-server
    app: temporal
  ports:
  - name: temporal-ui
    port: 7233
    targetPort: 7233
  - name: temporal-grpc
    port: 7234
    targetPort: 7234
```

### **1.2 Deploy Temporal Workers**
**File to Create:** `core/resources/infrastructure/temporal/temporal-workers-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-workers
  namespace: ai-infrastructure
  labels:
    component: temporal-workers
    app: temporal-workers
spec:
  replicas: 3
  selector:
    matchLabels:
      component: temporal-workers
      app: temporal-workers
  template:
    metadata:
      labels:
        component: temporal-workers
        app: temporal-workers
    spec:
      serviceAccountName: temporal-workers-sa
      containers:
      - name: worker
        image: temporal-workers:latest
        env:
        - name: TEMPORAL_HOST
          value: "temporal-server:7233"
        - name: TEMPORAL_PORT
          value: "7233"
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: TASK_QUEUE
          value: "cloud-ai-task-queue"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: MODEL
          value: "qwen2.5:0.5b"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: temporal-workers-service
  namespace: ai-infrastructure
spec:
  selector:
    component: temporal-workers
    app: temporal-workers
  ports:
  - name: worker-http
    port: 8080
    targetPort: 8080
```

### **1.3 Build Temporal Workers Image**
**File to Create:** `core/ai/workers/temporal/Dockerfile`

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY cmd/worker/main.go .
COPY internal/workflow/ ./internal/workflow/
COPY internal/activities/ ./internal/activities/

# Build the worker
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o worker ./cmd/worker/main.go

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/worker .

EXPOSE 8080

CMD ["./worker"]
```

### **1.4 Update Deployment Script**
**File to Modify:** `core/automation/scripts/deploy-ai-agents-ecosystem.sh`

```bash
# Add these functions:

deploy_temporal_server() {
    log_info "Deploying Temporal server..."
    
    # Create namespace if not exists
    kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy PostgreSQL for Temporal
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: temporal-secrets
  namespace: ai-infrastructure
type: Opaque
data:
  username: $(echo -n 'temporal' | base64)
  password: $(echo -n 'temporal' | base64)
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: temporal-postgres
  namespace: ai-infrastructure
spec:
  serviceName: temporal-postgres
  replicas: 1
  selector:
    matchLabels:
      app: temporal-postgres
  template:
    metadata:
      labels:
        app: temporal-postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: temporal
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: temporal-secrets
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: temporal-secrets
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
EOF
    
    # Deploy Temporal server
    kubectl apply -f core/resources/infrastructure/temporal/temporal-server-deployment.yaml
    
    log_success "Temporal server deployed"
}

deploy_temporal_workers() {
    log_info "Deploying Temporal workers..."
    
    # Build worker image
    cd core/ai/workers/temporal
    docker build -t temporal-workers:latest .
    
    # Deploy workers
    kubectl apply -f core/resources/infrastructure/temporal/temporal-workers-deployment.yaml
    
    log_success "Temporal workers deployed"
}

# Update main function
main() {
    # ... existing code ...
    
    create_namespace
    deploy_inference_backend
    build_agent_images
    deploy_ai_agents
    deploy_temporal_server  # NEW
    deploy_temporal_workers  # NEW
    deploy_ai_gateway
    # Skip Temporal due to timeout issues
    # deploy_temporal  # REMOVED - now deployed separately
    # deploy_ingress
    validate_deployment
    print_access_info
    log_success "🎯 Phase 1 Complete! Temporal Worker Model deployed."
}
```

### **1.5 Update FastAPI Agent Detection**
**File to Modify:** `dashboard-api.yaml`

```python
# Update get_agents() function:

def get_agents():
    agents = []
    
    # Detect memory agent
    memory_output = get_kubectl_data("kubectl get pods -n ai-infrastructure -l component=agent-memory --no-headers")
    for line in memory_output.split('\n'):
        if line.strip():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 6:
                name = parts[0]
                if 'memory' in name:
                    agents.append({
                        'id': name,
                        'name': 'Memory Agent',
                        'type': 'Rust',
                        'status': parts[1],
                        'skills': 1,
                        'lastActivity': '1 min ago',
                        'successRate': 99.9
                    })
    
    # Detect temporal workers (contains all agent activities)
    worker_output = get_kubectl_data("kubectl get pods -n ai-infrastructure -l component=temporal-workers --no-headers")
    for line in worker_output.split('\n'):
        if line.strip():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 6:
                name = parts[0]
                if 'worker' in name:
                    agents.append({
                        'id': name,
                        'name': 'AI Agent Worker',
                        'type': 'Go',
                        'status': parts[1],
                        'skills': 64,  # All activities available
                        'lastActivity': '1 min ago',
                        'successRate': 98.5
                    })
    
    return jsonify({'agents': agents})
```

---

## 🚀 **Phase 2: Independent Agent Model**

### **2.1 Deploy Individual Agent Containers**
**Files to Create:** `core/resources/infrastructure/agents/`

```yaml
# cost-optimizer-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-optimizer-agent
  namespace: ai-infrastructure
  labels:
    agent-type: cost-optimizer
    language: rust
spec:
  replicas: 2
  selector:
    matchLabels:
      agent-type: cost-optimizer
  template:
    metadata:
      labels:
        agent-type: cost-optimizer
        language: rust
    spec:
      containers:
      - name: cost-optimizer
        image: cost-optimizer-agent:latest
        env:
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: AGENT_TYPE
          value: "cost-optimizer"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"

# security-scanner-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-scanner-agent
  namespace: ai-infrastructure
  labels:
    agent-type: security-scanner
    language: go
spec:
  replicas: 2
  selector:
    matchLabels:
      agent-type: security-scanner
  template:
    metadata:
      labels:
        agent-type: security-scanner
        language: go
    spec:
      containers:
      - name: security-scanner
        image: security-scanner-agent:latest
        env:
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: AGENT_TYPE
          value: "security-scanner"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### **2.2 Build Agent Container Images**
**Files to Create:** `core/ai/agents/[agent-name]/Dockerfile`

```dockerfile
# Cost Optimizer Dockerfile
FROM rust:1.80-slim AS builder

WORKDIR /app

COPY Cargo.toml ./
COPY src ./src

RUN cargo update && cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/cost-optimizer .

EXPOSE 8080

CMD ["./cost-optimizer"]

# Security Scanner Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ ./cmd/
COPY internal/ ./internal/

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o security-scanner ./cmd/security-scanner/main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/security-scanner .

EXPOSE 8080

CMD ["./security-scanner"]
```

### **2.3 Deploy Agent Swarm Coordination**
**File to Create:** `core/resources/infrastructure/agents/agent-swarm-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-swarm-coordinator
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent-swarm
  template:
    metadata:
      labels:
        app: agent-swarm
    spec:
      containers:
      - name: swarm-coordinator
        image: agent-swarm-coordinator:latest
        env:
        - name: CONSENSUS_PROTOCOL
          value: "raft"
        - name: AGENT_REGISTRY_URL
          value: "http://agent-registry:8080"
        - name: COORDINATION_PORT
          value: "8080"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### **2.4 Update Agent Detection for Independent Model**
**File to Modify:** `dashboard-api.yaml`

```python
# Add to get_agents() function:

def get_agents():
    agents = []
    
    # Detect memory agent
    # ... existing code ...
    
    # Detect temporal workers
    # ... existing code ...
    
    # Detect independent agents
    agent_output = get_kubectl_data("kubectl get pods -n ai-infrastructure -l agent-type --no-headers")
    for line in agent_output.split('\n'):
        if line.strip():
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 6:
                name = parts[0]
                labels = get_pod_labels(name)  # Function to get pod labels
                
                agent_type = labels.get('agent-type', 'Unknown')
                language = labels.get('language', 'Unknown')
                
                agents.append({
                    'id': name,
                    'name': agent_type.replace('-', ' ').title(),
                    'type': language.title(),
                    'status': parts[1],
                    'skills': get_agent_skill_count(agent_type),
                    'lastActivity': '1 min ago',
                    'successRate': 98.5
                })
    
    return jsonify({'agents': agents})
```

---

## 📋 **Implementation Timeline**

### **Phase 1: Temporal Worker Model (Week 1-2)**
- [ ] **Day 1-2:** Create Temporal server deployment
- [ ] **Day 3-4:** Create Temporal workers deployment
- [ ] **Day 5:** Build Temporal workers image
- [ ] **Day 6-7:** Update deployment script
- [ ] **Day 8-10:** Update FastAPI detection
- [ ] **Day 11-14:** Test Phase 1 complete system

### **Phase 2: Independent Agent Model (Week 3-4)**
- [ ] **Day 15-18:** Create individual agent deployments
- [ ] **Day 19-22:** Build agent container images
- [ ] **Day 23-25:** Deploy agent swarm coordination
- [ ] **Day 26-28:** Update FastAPI for hybrid detection
- [ ] **Day 29-30:** Test Phase 2 complete system

### **Phase 3: Integration & Testing (Week 5-6)**
- [ ] **Day 31-35:** Test both models working together
- [ ] **Day 36-40:** Performance optimization
- [ ] **Day 41-45:** Documentation updates
- [ ] **Day 46-50:** Production readiness validation

---

## 🎯 **Success Criteria**

### **Phase 1 Complete:**
- [ ] Temporal server deployed and healthy
- [ ] Temporal workers deployed (3+ replicas)
- [ ] Dashboard shows "AI Agent Worker" entries
- [ ] Agent activities accessible via workflows
- [ ] Memory agent integration working

### **Phase 2 Complete:**
- [ ] Individual agent containers deployed
- [ ] Agent swarm coordination working
- [ ] Dashboard shows individual agent entries
- [ ] Agent-to-agent communication working
- [ ] Hybrid detection logic functional

### **Full System Complete:**
- [ ] Both models deployed and functional
- [ ] Dashboard shows all agent types
- [ ] Workflow orchestration working
- [ ] Memory agent serving all models
- [ ] Performance metrics available
- [ ] Production ready

---

## 🚀 **Next Steps**

1. **Start with Phase 1** (Temporal Worker Model)
2. **Validate Phase 1** before proceeding to Phase 2
3. **Implement hybrid detection** to support both models
4. **Test integration** between models
5. **Document lessons learned** for future improvements

**This phased approach ensures we get a working system quickly, then add flexibility with the second model!** 🎯
