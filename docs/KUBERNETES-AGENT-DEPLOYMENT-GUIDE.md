# Kubernetes Agent Deployment Guide

## Overview

This guide documents the Kubernetes deployment configurations for independent AI agents, including deployment manifests, service configurations, and operational best practices.

## Table of Contents

1. [Deployment Architecture](#deployment-architecture)
2. [Agent Deployment Manifests](#agent-deployment-manifests)
3. [Service Configurations](#service-configurations)
4. [Resource Management](#resource-management)
5. [Health Monitoring](#health-monitoring)
6. [Security Considerations](#security-considerations)
7. [Operational Procedures](#operational-procedures)
8. [Troubleshooting](#troubleshooting)

## Deployment Architecture

### Namespace Strategy

```yaml
# ai-infrastructure namespace
apiVersion: v1
kind: Namespace
metadata:
  name: ai-infrastructure
  labels:
    environment: production
    component: ai-agents
    managed-by: gitops
```

### Service Account Configuration

```yaml
# Agent service account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: agent-swarm-sa
  namespace: ai-infrastructure
  labels:
    component: agent-swarm-coordinator
    security-level: restricted
```

### Network Policies

```yaml
# Network policy for agent communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-network-policy
  namespace: ai-infrastructure
spec:
  podSelector:
    matchLabels:
      component: agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
    - podSelector:
        matchLabels:
          component: temporal
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: ai-infrastructure
  - to: []
    ports:
    - protocol: TCP
      port: 8080
  - to: []
    ports:
    - protocol: TCP
      port: 7233
```

## Agent Deployment Manifests

### Cost Optimizer Agent

#### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-optimizer-agent
  namespace: ai-infrastructure
  labels:
    agent-type: cost-optimizer
    language: rust
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      agent-type: cost-optimizer
  template:
    metadata:
      labels:
        agent-type: cost-optimizer
        language: rust
        component: independent-agent
    spec:
      serviceAccountName: agent-swarm-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: cost-optimizer
        image: cost-optimizer-agent:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: AGENT_TYPE
          value: "cost-optimizer"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: MODEL
          value: "qwen2.5:0.5b"
        - name: LOG_LEVEL
          value: "info"
        - name: PORT
          value: "8080"
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
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
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

#### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: cost-optimizer-service
  namespace: ai-infrastructure
  labels:
    agent-type: cost-optimizer
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  selector:
    agent-type: cost-optimizer
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
  sessionAffinity: None
```

### Security Scanner Agent

#### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-scanner-agent
  namespace: ai-infrastructure
  labels:
    agent-type: security-scanner
    language: go
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      agent-type: security-scanner
  template:
    metadata:
      labels:
        agent-type: security-scanner
        language: go
        component: independent-agent
    spec:
      serviceAccountName: agent-swarm-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: security-scanner
        image: security-scanner-agent:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: AGENT_TYPE
          value: "security-scanner"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: MODEL
          value: "qwen2.5:0.5b"
        - name: LOG_LEVEL
          value: "info"
        - name: PORT
          value: "8080"
        - name: SCAN_INTERVAL
          value: "300"  # 5 minutes
        - name: SEVERITY_THRESHOLD
          value: "medium"
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
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
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /cache
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

#### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: security-scanner-service
  namespace: ai-infrastructure
  labels:
    agent-type: security-scanner
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  selector:
    agent-type: security-scanner
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
  sessionAffinity: None
```

### Agent Swarm Coordinator

#### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-swarm-coordinator
  namespace: ai-infrastructure
  labels:
    component: agent-swarm-coordinator
    language: go
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      component: agent-swarm-coordinator
  template:
    metadata:
      labels:
        component: agent-swarm-coordinator
        language: go
        component: independent-agent
    spec:
      serviceAccountName: agent-swarm-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: swarm-coordinator
        image: agent-swarm-coordinator:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: CONSENSUS_PROTOCOL
          value: "raft"
        - name: AGENT_REGISTRY_URL
          value: "http://agent-registry:8080"
        - name: COORDINATION_PORT
          value: "8080"
        - name: MEMORY_AGENT_URL
          value: "http://agent-memory-rust:8080"
        - name: LANGUAGE_PRIORITY
          value: "rust,go,python"
        - name: BACKEND_PRIORITY
          value: "llama.cpp,ollama"
        - name: OLLAMA_URL
          value: "http://ollama-service:11434"
        - name: MODEL
          value: "qwen2.5:0.5b"
        - name: LOG_LEVEL
          value: "info"
        - name: PORT
          value: "8080"
        - name: SWARM_SIZE
          value: "10"
        - name: HEARTBEAT_INTERVAL
          value: "30"
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
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
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: data
          mountPath: /data
      volumes:
      - name: tmp
        emptyDir: {}
      - name: data
        emptyDir: {}
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

#### Service Configuration
```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-swarm-coordinator-service
  namespace: ai-infrastructure
  labels:
    component: agent-swarm-coordinator
    component: independent-agent
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  type: ClusterIP
  selector:
    component: agent-swarm-coordinator
  ports:
  - name: http
    port: 8080
    targetPort: 8080
    protocol: TCP
  sessionAffinity: None
```

## Resource Management

### Resource Limits and Requests

#### CPU and Memory Allocation
```yaml
# Resource allocation strategy
resources:
  requests:
    memory: "256Mi"    # Minimum memory required
    cpu: "100m"        # Minimum CPU required
  limits:
    memory: "512Mi"    # Maximum memory allowed
    cpu: "500m"        # Maximum CPU allowed
```

#### Resource Classes by Agent Type
```yaml
# Cost Optimizer - Lightweight
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Security Scanner - Medium
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"

# Swarm Coordinator - Heavy
resources:
  requests:
    memory: "512Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Horizontal Pod Autoscaling

#### HPA Configuration
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cost-optimizer-hpa
  namespace: ai-infrastructure
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cost-optimizer-agent
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### Resource Quotas

#### Namespace Resource Limits
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ai-infrastructure-quota
  namespace: ai-infrastructure
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    persistentvolumeclaims: "10"
    pods: "20"
    services: "20"
    secrets: "20"
    configmaps: "20"
```

## Health Monitoring

### Probe Configurations

#### Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1
```

#### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

#### Startup Probe
```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30
  successThreshold: 1
```

### Monitoring Endpoints

#### Health Check Implementation
```go
// Go health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
    health := struct {
        Status    string `json:"status"`
        Version   string `json:"version"`
        Timestamp string `json:"timestamp"`
        Checks    map[string]bool `json:"checks"`
    }{
        Status:    "healthy",
        Version:   "1.0.0",
        Timestamp: time.Now().UTC().Format(time.RFC3339),
        Checks: map[string]bool{
            "memory_agent": checkMemoryAgent(),
            "ollama":      checkOllama(),
            "database":    checkDatabase(),
        },
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(health)
}
```

#### Metrics Collection
```go
// Prometheus metrics endpoint
func metricsHandler(w http.ResponseWriter, r *http.Request) {
    // Custom metrics
    httpRequestsTotal := prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )
    
    requestDuration := prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "http_request_duration_seconds",
            Help: "HTTP request duration in seconds",
        },
        []string{"method", "endpoint"},
    )
    
    // Expose metrics
    promhttp.Handler().ServeHTTP(w, r)
}
```

## Security Considerations

### Pod Security Context
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001
  seccompProfile:
    type: RuntimeDefault
```

### Container Security Context
```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
  runAsNonRoot: true
  runAsUser: 1001
```

### Pod Security Policy
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: agent-psp
  namespace: ai-infrastructure
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### RBAC Configuration
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ai-infrastructure
  name: agent-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: agent-rolebinding
  namespace: ai-infrastructure
subjects:
- kind: ServiceAccount
  name: agent-swarm-sa
  namespace: ai-infrastructure
roleRef:
  kind: Role
  name: agent-role
  apiGroup: rbac.authorization.k8s.io
```

## Operational Procedures

### Deployment Rollout

#### Blue-Green Deployment
```bash
# Deploy new version
kubectl apply -f cost-optimizer-deployment-v2.yaml

# Wait for new pods to be ready
kubectl wait --for=condition=ready pod -l agent-type=cost-optimizer -n ai-infrastructure --timeout=300s

# Switch traffic
kubectl patch service cost-optimizer-service -p '{"spec":{"selector":{"version":"v2"}}}'
```

#### Canary Deployment
```bash
# Create canary deployment
kubectl apply -f cost-optimizer-canary.yaml

# Monitor canary
kubectl get pods -l agent-type=cost-optimizer,version=canary -n ai-infrastructure

# Gradually increase canary traffic
kubectl patch service cost-optimizer-service -p '{"spec":{"selector":{"version":"canary","weight":"10"}}}'
```

### Rolling Updates

#### Update Strategy
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Number of additional pods
      maxUnavailable: 0  # Number of unavailable pods
```

#### Rollout Commands
```bash
# Update deployment
kubectl set image deployment/cost-optimizer-agent cost-optimizer=cost-optimizer-agent:v2 -n ai-infrastructure

# Monitor rollout
kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=300s

# Rollback if needed
kubectl rollout undo deployment/cost-optimizer-agent -n ai-infrastructure
```

### Scaling Operations

#### Manual Scaling
```bash
# Scale up
kubectl scale deployment cost-optimizer-agent --replicas=5 -n ai-infrastructure

# Scale down
kubectl scale deployment cost-optimizer-agent --replicas=2 -n ai-infrastructure
```

#### Auto Scaling
```bash
# Enable HPA
kubectl autoscale deployment cost-optimizer-agent --cpu-percent=70 --min=2 --max=10 -n ai-infrastructure

# Check HPA status
kubectl get hpa -n ai-infrastructure
```

## Troubleshooting

### Common Issues

#### ImagePullBackOff
```bash
# Check image availability
docker exec gitops-hub-control-plane crictl images | grep cost-optimizer

# Check deployment image reference
kubectl get deployment cost-optimizer-agent -n ai-infrastructure -o yaml | grep image:

# Reload image
kind load docker-image cost-optimizer-agent:latest --name gitops-hub
```

#### Pod Crashing
```bash
# Check pod logs
kubectl logs cost-optimizer-agent-xxx -n ai-infrastructure

# Check pod events
kubectl describe pod cost-optimizer-agent-xxx -n ai-infrastructure

# Check pod status
kubectl get pods -n ai-infrastructure -o wide
```

#### Resource Issues
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# Check resource limits
kubectl describe pod cost-optimizer-agent-xxx -n ai-infrastructure | grep -A 10 "Limits:"
```

#### Network Issues
```bash
# Check service connectivity
kubectl exec cost-optimizer-agent-xxx -n ai-infrastructure -- wget -qO- http://cost-optimizer-service:8080/health

# Check network policies
kubectl get networkpolicy -n ai-infrastructure

# Check DNS resolution
kubectl exec cost-optimizer-agent-xxx -n ai-infrastructure -- nslookup cost-optimizer-service.ai-infrastructure.svc.cluster.local
```

### Debug Commands

#### Comprehensive Health Check
```bash
#!/bin/bash
echo "=== Agent Pod Status ==="
kubectl get pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Recent Events ==="
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -10

echo "=== Resource Usage ==="
kubectl top pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Service Status ==="
kubectl get services -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Deployment Status ==="
kubectl get deployments -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"
```

#### Log Analysis
```bash
# Stream logs from all agent pods
kubectl logs -l agent-type=cost-optimizer -n ai-infrastructure -f

# Check recent logs
kubectl logs -l agent-type=cost-optimizer -n ai-infrastructure --since=10m

# Check error logs
kubectl logs -l agent-type=cost-optimizer -n ai-infrastructure | grep -i error
```

## Conclusion

This comprehensive guide covers all aspects of deploying independent AI agents to Kubernetes:

1. **Deployment Architecture**: Namespace strategy, service accounts, and network policies
2. **Agent Manifests**: Complete deployment configurations for all agent types
3. **Resource Management**: Resource limits, HPA, and quotas
4. **Health Monitoring**: Probes, metrics, and observability
5. **Security**: Security contexts, RBAC, and pod security policies
6. **Operations**: Deployment strategies, scaling, and troubleshooting

By following these configurations and procedures, you can achieve reliable, scalable, and secure deployments of independent AI agents in your Kubernetes environment.

## References

- [Kubernetes Deployment Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
