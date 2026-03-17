# Agent Deployment Timeout & ImagePullBackOff Fix Guide

## Overview

This guide documents the comprehensive solution for resolving intermittent timeouts and `ImagePullBackOff` issues when deploying independent AI agents to Kubernetes. The solution addresses Docker API timeouts, kubectl connectivity issues, and proper image management in Kind clusters.

## Table of Contents

1. [Problem Analysis](#problem-analysis)
2. [Solution Architecture](#solution-architecture)
3. [Implementation Details](#implementation-details)
4. [Automated Fix Script](#automated-fix-script)
5. [Manual Procedures](#manual-procedures)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Prevention Strategies](#prevention-strategies)
8. [Best Practices](#best-practices)

## Problem Analysis

### Root Causes Identified

1. **Docker API Timeouts**
   - System resource constraints causing intermittent API failures
   - Build cache accumulation affecting performance
   - Container runtime resource exhaustion

2. **kubectl Connectivity Issues**
   - Network timeouts during cluster operations
   - Resource contention during pod operations
   - Insufficient timeout handling in automated scripts

3. **ImagePullBackOff Errors**
   - Incorrect image references in deployment manifests
   - Images not properly loaded into Kind cluster
   - Registry configuration mismatches

### Impact Assessment

- **Agent Deployment Failures**: All three independent agents (cost-optimizer, security-scanner, swarm-coordinator) stuck in `ImagePullBackOff` state
- **Development Workflow Interruption**: Intermittent timeouts preventing reliable deployment automation
- **Resource Waste**: Stuck pods consuming cluster resources without providing functionality

## Solution Architecture

### Multi-Layer Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    Solution Layers                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Docker Resource Optimization                              │
│    - System cleanup and cache management                    │
│    - Build optimization and resource monitoring             │
├─────────────────────────────────────────────────────────────┤
│ 2. Image Management Strategy                                 │
│    - Proper image loading into Kind cluster                  │
│    - Correct image reference configuration                   │
│    - Image verification and validation                       │
├─────────────────────────────────────────────────────────────┤
│ 3. Deployment Automation                                     │
│    - Timeout-aware kubectl operations                       │
│    - Rollout status monitoring                               │
│    - Health verification and recovery                        │
├─────────────────────────────────────────────────────────────┤
│ 4. System Health Monitoring                                  │
│    - Cluster connectivity checks                            │
│    - Resource usage monitoring                              │
│    - Performance metrics collection                          │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Docker Resource Optimization

#### System Cleanup Commands
```bash
# Remove unused containers, networks, images, and build cache
docker system prune -f

# Monitor resource usage
docker system df

# Check system health
docker system info
```

#### Build Optimization
```bash
# Use multi-stage builds to reduce image size
FROM rust:1.83-alpine AS builder
# ... build stages ...
FROM alpine:latest
# ... runtime stage ...

# Optimize layer caching
COPY go.mod ./
RUN go mod download
COPY . .
RUN go build -o app .
```

### 2. Image Management Strategy

#### Image Loading Process
```bash
# Build images with correct tagging
docker build -t cost-optimizer-agent:latest .
docker build -t security-scanner-agent:latest .
docker build -t agent-swarm-coordinator:latest .

# Load images into Kind cluster
kind load docker-image cost-optimizer-agent:latest --name gitops-hub
kind load docker-image security-scanner-agent:latest --name gitops-hub
kind load docker-image agent-swarm-coordinator:latest --name gitops-hub
```

#### Image Verification
```bash
# Verify images in cluster
docker exec gitops-hub-control-plane crictl images | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

# Check image availability
kubectl get pods -n ai-infrastructure -o wide
```

### 3. Deployment Manifest Configuration

#### Correct Image References
```yaml
# Use plain image names (no localhost:5000 prefix)
spec:
  containers:
  - name: cost-optimizer
    image: cost-optimizer-agent:latest
  - name: security-scanner
    image: security-scanner-agent:latest
  - name: swarm-coordinator
    image: agent-swarm-coordinator:latest
```

#### Probe Configuration Fix
```yaml
# Correct probe structure (initialDelaySeconds at probe level, not httpGet level)
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
```

### 4. Timeout-Aware Operations

#### kubectl Timeout Handling
```bash
# Use explicit timeouts
kubectl get pods --request-timeout=10s
kubectl apply -f deployment.yaml --timeout=30s
kubectl rollout status deployment/app --timeout=60s
```

#### Retry Logic Implementation
```bash
# Function to retry commands with timeout
execute_with_timeout() {
    local cmd="$1"
    local timeout_duration="${2:-30}"
    local description="${3:-command}"
    
    echo "⏱️ Executing: $description"
    timeout "$timeout_duration" bash -c "$cmd" 2>/dev/null
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Success: $description"
        return 0
    elif [ $exit_code -eq 124 ]; then
        echo "⏰ Timeout: $description after ${timeout_duration}s"
        return 1
    else
        echo "❌ Failed: $description (exit code: $exit_code)"
        return 1
    fi
}
```

## Automated Fix Script

### Script Overview

The `fix-timeout-issues.sh` script provides a comprehensive, automated solution for resolving timeout and ImagePullBackOff issues.

### Script Structure

```bash
#!/bin/bash

echo "🔧 Fixing agent deployment timeouts and ImagePullBackOff issues..."

# 1. Docker Resource Optimization
execute_with_timeout "docker system prune -f" 60 "docker system prune"

# 2. Image Verification
execute_with_timeout "docker exec gitops-hub-control-plane crictl images | grep -E '(cost-optimizer|security-scanner|swarm-coordinator)'" 30 "check cluster images"

# 3. Resource Cleanup
execute_with_timeout "kubectl delete pods -l agent-type=cost-optimizer -n ai-infrastructure --force --grace-period=0" 15 "delete cost-optimizer pods"
execute_with_timeout "kubectl delete pods -l agent-type=security-scanner -n ai-infrastructure --force --grace-period=0" 15 "delete security-scanner pods"
execute_with_timeout "kubectl delete pods -l component=agent-swarm-coordinator -n ai-infrastructure --force --grace-period=0" 15 "delete swarm-coordinator pods"

# 4. Deployment Application
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/cost-optimizer-deployment.yaml" 30 "apply cost-optimizer deployment"
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/security-scanner-deployment.yaml" 30 "apply security-scanner deployment"
execute_with_timeout "kubectl apply -f core/resources/infrastructure/agents/agent-swarm-coordinator-deployment.yaml" 30 "apply swarm-coordinator deployment"

# 5. Rollout Monitoring
execute_with_timeout "kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=60s" 70 "cost-optimizer rollout"
execute_with_timeout "kubectl rollout status deployment/security-scanner-agent -n ai-infrastructure --timeout=60s" 70 "security-scanner rollout"
execute_with_timeout "kubectl rollout status deployment/agent-swarm-coordinator -n ai-infrastructure --timeout=60s" 70 "swarm-coordinator rollout"

# 6. System Health Verification
execute_with_timeout "kubectl cluster-info" 20 "cluster connectivity check"
execute_with_timeout "docker system df" 15 "docker resource usage"

echo "✅ Agent deployment fix completed!"
```

### Script Usage

```bash
# Make script executable
chmod +x fix-timeout-issues.sh

# Run the comprehensive fix
./fix-timeout-issues.sh

# Monitor progress
./fix-timeout-issues.sh | tee deployment-fix.log
```

## Manual Procedures

### Step-by-Step Manual Fix

#### 1. Resource Cleanup
```bash
# Clean Docker resources
docker system prune -f

# Delete stuck pods
kubectl delete pods -l agent-type=cost-optimizer -n ai-infrastructure --force --grace-period=0
kubectl delete pods -l agent-type=security-scanner -n ai-infrastructure --force --grace-period=0
kubectl delete pods -l component=agent-swarm-coordinator -n ai-infrastructure --force --grace-period=0
```

#### 2. Image Management
```bash
# Verify images in cluster
docker exec gitops-hub-control-plane crictl images | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

# Reload images if needed
kind load docker-image cost-optimizer-agent:latest --name gitops-hub
kind load docker-image security-scanner-agent:latest --name gitops-hub
kind load docker-image agent-swarm-coordinator:latest --name gitops-hub
```

#### 3. Deployment Update
```bash
# Apply corrected deployments
kubectl apply -f core/resources/infrastructure/agents/cost-optimizer-deployment.yaml
kubectl apply -f core/resources/infrastructure/agents/security-scanner-deployment.yaml
kubectl apply -f core/resources/infrastructure/agents/agent-swarm-coordinator-deployment.yaml
```

#### 4. Rollout Monitoring
```bash
# Monitor deployment progress
kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=60s
kubectl rollout status deployment/security-scanner-agent -n ai-infrastructure --timeout=60s
kubectl rollout status deployment/agent-swarm-coordinator -n ai-infrastructure --timeout=60s
```

#### 5. Verification
```bash
# Check pod status
kubectl get pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

# Verify cluster health
kubectl cluster-info
docker system df
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Persistent ImagePullBackOff
**Symptoms**: Pods remain in ImagePullBackOff state despite image loading

**Solutions**:
```bash
# Check image availability in cluster
docker exec gitops-hub-control-plane crictl images | grep <image-name>

# Verify deployment image references
kubectl get deployment <deployment-name> -n ai-infrastructure -o yaml | grep image:

# Force recreate deployment
kubectl delete deployment <deployment-name> -n ai-infrastructure
kubectl apply -f <deployment-manifest.yaml>
```

#### 2. kubectl Timeouts
**Symptoms**: Commands timeout with "WaitDelay expired" errors

**Solutions**:
```bash
# Use explicit timeouts
kubectl get pods --request-timeout=10s

# Check cluster connectivity
kubectl cluster-info

# Restart Docker Desktop (if applicable)
```

#### 3. Docker API Issues
**Symptoms**: Docker commands fail or timeout

**Solutions**:
```bash
# Check Docker status
docker system info

# Clean up resources
docker system prune -f

# Restart Docker service
sudo systemctl restart docker  # Linux
# Restart Docker Desktop        # macOS/Windows
```

#### 4. Resource Exhaustion
**Symptoms**: System becomes unresponsive during operations

**Solutions**:
```bash
# Monitor resource usage
docker system df
kubectl top nodes
kubectl top pods -n ai-infrastructure

# Clean up unused resources
docker system prune -f
kubectl delete pods --field-selector=status.phase=Failed -n ai-infrastructure
```

### Debug Commands

```bash
# Comprehensive system check
echo "=== Docker Status ==="
docker system info | head -10
docker system df

echo "=== Cluster Status ==="
kubectl cluster-info
kubectl get nodes
kubectl get pods -n ai-infrastructure

echo "=== Agent Pod Status ==="
kubectl get pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Recent Events ==="
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -10
```

## Prevention Strategies

### 1. Proactive Resource Management

#### Regular Cleanup Schedule
```bash
# Add to cron or scheduled task
0 2 * * * /usr/local/bin/docker system prune -f
0 3 * * 0 /usr/local/bin/kubectl delete pods --field-selector=status.phase=Failed -n ai-infrastructure
```

#### Resource Monitoring
```bash
# Monitor script
#!/bin/bash
while true; do
    echo "$(date): Checking system resources..."
    docker system df
    kubectl top pods -n ai-infrastructure
    sleep 300  # Check every 5 minutes
done
```

### 2. Deployment Best Practices

#### Gradual Rollout Strategy
```bash
# Deploy one agent at a time
kubectl apply -f cost-optimizer-deployment.yaml
kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=120s

# Wait for success before next deployment
kubectl apply -f security-scanner-deployment.yaml
kubectl rollout status deployment/security-scanner-agent -n ai-infrastructure --timeout=120s
```

#### Health Check Implementation
```bash
# Pre-deployment health check
check_deployment_health() {
    local deployment="$1"
    local namespace="$2"
    
    # Check if deployment exists and is ready
    kubectl get deployment "$deployment" -n "$namespace" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Deployment $deployment not found"
        return 1
    fi
    
    # Check rollout status
    kubectl rollout status deployment/"$deployment" -n "$namespace" --timeout=60s
    return $?
}
```

### 3. System Optimization

#### Docker Configuration
```json
// /etc/docker/daemon.json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 3
}
```

#### Kubernetes Resource Limits
```yaml
# Example resource configuration
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## Best Practices

### 1. Development Workflow

#### Before Deployment
```bash
# 1. Clean environment
docker system prune -f
kubectl delete pods --field-selector=status.phase=Failed -n ai-infrastructure

# 2. Verify images
docker images | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"
docker exec gitops-hub-control-plane crictl images | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

# 3. Check cluster health
kubectl cluster-info
kubectl get nodes
```

#### During Deployment
```bash
# 1. Use timeout-aware commands
kubectl apply -f deployment.yaml --timeout=30s

# 2. Monitor rollout progress
kubectl rollout status deployment/app -n ai-infrastructure --timeout=120s

# 3. Verify pod health
kubectl get pods -n ai-infrastructure -w
```

#### After Deployment
```bash
# 1. Verify functionality
kubectl get pods -n ai-infrastructure
kubectl logs -l app=cost-optimizer -n ai-infrastructure

# 2. Check system resources
docker system df
kubectl top pods -n ai-infrastructure
```

### 2. CI/CD Integration

#### Pipeline Configuration
```yaml
# Example GitHub Actions workflow
- name: Fix Timeout Issues
  run: |
    chmod +x fix-timeout-issues.sh
    ./fix-timeout-issues.sh

- name: Verify Deployment
  run: |
    kubectl get pods -n ai-infrastructure
    kubectl rollout status deployment/cost-optimizer-agent -n ai-infrastructure --timeout=120s
```

### 3. Monitoring and Alerting

#### Health Check Endpoints
```go
// Example health check implementation
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
    // Check system resources
    if isSystemHealthy() {
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
    } else {
        w.WriteHeader(http.StatusServiceUnavailable)
        json.NewEncoder(w).Encode(map[string]string{"status": "unhealthy"})
    }
}
```

#### Monitoring Metrics
```yaml
# Prometheus monitoring configuration
- name: agent_deployment_status
  help: "Status of agent deployments"
  type: gauge
  labels: [agent_type, namespace]

- name: docker_resource_usage
  help: "Docker resource usage statistics"
  type: gauge
  labels: [resource_type]
```

## Conclusion

This comprehensive solution addresses the root causes of timeout and ImagePullBackOff issues through a multi-layered approach:

1. **Resource Optimization**: Proactive Docker and Kubernetes resource management
2. **Image Management**: Proper image loading and verification processes
3. **Timeout Handling**: Robust timeout-aware operations with retry logic
4. **Health Monitoring**: Continuous system health verification
5. **Automation**: Comprehensive scripts for reliable deployment processes

By implementing these solutions and following the best practices outlined in this guide, you can achieve reliable, automated deployment of independent AI agents to Kubernetes without timeout or ImagePullBackOff issues.

## References

- [Docker System Management](https://docs.docker.com/engine/reference/commandline/system_prune/)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kind Cluster Image Loading](https://kind.sigs.k8s.io/docs/user/quick-start/#loading-an-image-into-your-cluster)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-application/)
