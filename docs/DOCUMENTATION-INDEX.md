# Documentation Index

## Overview

This document provides a comprehensive index of all AI agent infrastructure documentation, organized by topic and purpose.

## Table of Contents

1. [Deployment & Operations](#deployment--operations)
2. [Build & Development](#build--development)
3. [Integration & Testing](#integration--testing)
4. [Troubleshooting & Maintenance](#troubleshooting--maintenance)
5. [Architecture & Design](#architecture--design)
6. [Security & Compliance](#security--compliance)

---

## Deployment & Operations

### [Agent Timeout Fix Guide](AGENT-TIMEOUT-FIX-GUIDE.md)
**Purpose**: Comprehensive solution for resolving timeout and ImagePullBackOff issues

**Topics Covered**:
- Problem analysis and root causes
- Docker resource optimization
- Image management strategies
- Automated fix scripts
- Manual procedures
- Prevention strategies

**Key Sections**:
- Multi-layer solution architecture
- `fix-timeout-issues.sh` script documentation
- Docker system optimization
- Kubernetes deployment fixes

**Target Audience**: DevOps engineers, system administrators, deployment teams

---

### [Kubernetes Agent Deployment Guide](KUBERNETES-AGENT-DEPLOYMENT-GUIDE.md)
**Purpose**: Complete Kubernetes deployment configurations and operational procedures

**Topics Covered**:
- Deployment architecture and namespace strategy
- Complete deployment manifests for all agents
- Resource management and HPA configuration
- Health monitoring and observability
- Security considerations and RBAC
- Operational procedures and scaling

**Key Sections**:
- Cost Optimizer, Security Scanner, and Swarm Coordinator deployments
- Service configurations and networking
- Horizontal Pod Autoscaling setup
- Security contexts and pod security policies

**Target Audience**: Kubernetes administrators, platform engineers, DevOps teams

---

## Build & Development

### [Agent Docker Build Guide](AGENT-DOCKER-BUILD-GUIDE.md)
**Purpose**: Docker build configurations and optimization strategies for all agents

**Topics Covered**:
- Multi-stage build patterns
- Build optimization strategies
- Cross-platform considerations
- Security hardening
- Build troubleshooting
- CI/CD integration

**Key Sections**:
- Rust, Go, and multi-language build configurations
- Layer caching optimization
- Security best practices
- Performance optimization

**Target Audience**: Developers, build engineers, DevOps teams

---

## Integration & Testing

### [Agent Integration and Testing Guide](AGENT-INTEGRATION-TESTING-GUIDE.md)
**Purpose**: Integration patterns, testing strategies, and validation procedures

**Topics Covered**:
- Integration architecture and communication patterns
- System integration with memory agents and Ollama
- Testing strategies (unit, integration, performance)
- Validation procedures and health checks
- Monitoring and observability
- Performance testing and benchmarking

**Key Sections**:
- HTTP, message queue, and gRPC communication
- End-to-end workflow validation
- Load testing and stress testing
- Distributed tracing and metrics collection

**Target Audience**: QA engineers, developers, system integrators

---

## Troubleshooting & Maintenance

### Quick Reference Troubleshooting

#### Common Issues and Solutions

**ImagePullBackOff Errors**
```bash
# Check image availability
docker exec gitops-hub-control-plane crictl images | grep agent-name

# Reload image
kind load docker-image agent-name:latest --name gitops-hub

# Restart deployment
kubectl delete deployment agent-name -n ai-infrastructure
kubectl apply -f agent-deployment.yaml
```

**kubectl Timeouts**
```bash
# Use explicit timeouts
kubectl get pods --request-timeout=10s

# Check cluster connectivity
kubectl cluster-info

# Restart Docker Desktop if needed
```

**Resource Issues**
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# Clean up resources
docker system prune -f
kubectl delete pods --field-selector=status.phase=Failed -n ai-infrastructure
```

#### Health Check Commands

```bash
# Comprehensive system health check
#!/bin/bash
echo "=== Agent Pod Status ==="
kubectl get pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Recent Events ==="
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -10

echo "=== Resource Usage ==="
kubectl top pods -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"

echo "=== Service Status ==="
kubectl get services -n ai-infrastructure | grep -E "(cost-optimizer|security-scanner|swarm-coordinator)"
```

---

## Architecture & Design

### System Architecture Overview

#### Component Relationships
```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│  Temporal Workers    │    Memory Agents    │ Independent Agents │
│  - Worker 1          │    - Rust Memory    │ - Cost Optimizer   │
│  - Worker 2          │    - Go Memory      │ - Security Scanner  │
│  - Worker N          │    - Python Memory  │ - Swarm Coordinator │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  Kubernetes Cluster  │  Kind Cluster      │ Docker Registry    │
├─────────────────────────────────────────────────────────────┤
│                    Monitoring & Observability                 │
│  Prometheus         │  Grafana           │ Dashboard API       │
└─────────────────────────────────────────────────────────────┘
```

#### Communication Patterns
- **HTTP API**: Direct agent-to-agent communication
- **Message Queues**: Redis-based asynchronous messaging
- **gRPC**: High-performance binary communication
- **Memory Agents**: Shared context and learning

---

## Security & Compliance

### Security Best Practices

#### Container Security
```yaml
# Security context configuration
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

#### Network Security
```yaml
# Network policy example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agent-network-policy
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
```

#### RBAC Configuration
```yaml
# Role-based access control
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: ai-infrastructure
  name: agent-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

---

## Quick Start Guide

### Prerequisites
- Docker Desktop installed and running
- Kind cluster configured
- kubectl configured for cluster access
- Go 1.21+ (for Go agents)
- Rust 1.83+ (for Rust agents)

### Initial Setup
```bash
# 1. Clone repository
git clone https://github.com/organization/gitops-infra-control-plane.git
cd gitops-infra-control-plane

# 2. Build agent images
docker build -t cost-optimizer-agent:latest ./core/ai/agents/cost-optimizer
docker build -t security-scanner-agent:latest ./core/ai/agents/security-scanner
docker build -t agent-swarm-coordinator:latest ./core/ai/agents/swarm-coordinator

# 3. Load images into Kind cluster
kind load docker-image cost-optimizer-agent:latest --name gitops-hub
kind load docker-image security-scanner-agent:latest --name gitops-hub
kind load docker-image agent-swarm-coordinator:latest --name gitops-hub

# 4. Deploy agents
kubectl apply -f core/resources/infrastructure/agents/

# 5. Verify deployment
kubectl get pods -n ai-infrastructure
```

### Troubleshooting First Steps
```bash
# Run the comprehensive fix script
./fix-timeout-issues.sh

# Check system health
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure

# Check recent events
kubectl get events -n ai-infrastructure --sort-by='.lastTimestamp' | tail -10
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily
```bash
# Check agent health
kubectl get pods -n ai-infrastructure

# Monitor resource usage
kubectl top pods -n ai-infrastructure

# Check for failed deployments
kubectl get events -n ai-infrastructure --field-selector reason=Failed
```

#### Weekly
```bash
# Clean up Docker resources
docker system prune -f

# Update agent images
docker build -t cost-optimizer-agent:latest ./core/ai/agents/cost-optimizer
kind load docker-image cost-optimizer-agent:latest --name gitops-hub

# Restart deployments if needed
kubectl rollout restart deployment/cost-optimizer-agent -n ai-infrastructure
```

#### Monthly
```bash
# Review resource limits and adjust if needed
kubectl describe pods -n ai-infrastructure | grep -A 10 "Limits:"

# Update dependencies
cd core/ai/agents/cost-optimizer && cargo update
cd core/ai/agents/security-scanner && go mod tidy

# Performance testing
./scripts/performance-test.sh
```

### Backup and Recovery

#### Configuration Backup
```bash
# Export all configurations
kubectl get all -n ai-infrastructure -o yaml > backup-configs.yaml

# Backup deployment manifests
cp -r core/resources/infrastructure/agents/ backup/agents/
```

#### Disaster Recovery
```bash
# Restore from backup
kubectl apply -f backup-configs.yaml

# Verify restoration
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure
```

---

## Performance Optimization

### Resource Optimization

#### Docker Optimization
```bash
# Clean up unused resources
docker system prune -f

# Monitor resource usage
docker system df

# Optimize build cache
docker builder prune -f
```

#### Kubernetes Optimization
```bash
# Check resource utilization
kubectl top nodes
kubectl top pods -n ai-infrastructure

# Optimize HPA settings
kubectl get hpa -n ai-infrastructure
kubectl edit hpa cost-optimizer-hpa -n ai-infrastructure
```

### Performance Monitoring

#### Key Metrics to Monitor
- **CPU Usage**: Should be below 70% average
- **Memory Usage**: Should be below 80% of limits
- **Response Time**: Should be under 100ms for health checks
- **Error Rate**: Should be below 1%
- **Pod Restart Count**: Should be minimal

#### Alerting Rules
```yaml
# Example Prometheus alerting rules
groups:
- name: agent-alerts
  rules:
  - alert: AgentDown
    expr: up{job="agents"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Agent {{ $labels.instance }} is down"
  
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on {{ $labels.pod }}"
```

---

## Development Workflow

### Local Development Setup

#### Prerequisites
```bash
# Install required tools
brew install docker kubectl kind

# Install Go
brew install go

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

#### Development Environment
```bash
# Start Kind cluster
kind create cluster --name gitops-hub --config kind-config.yaml

# Build and run agents locally
cd core/ai/agents/cost-optimizer
cargo run

# Test with local cluster
kubectl port-forward service/cost-optimizer-service 8080:8080 -n ai-infrastructure
```

### Testing Workflow

#### Unit Tests
```bash
# Run Rust tests
cd core/ai/agents/cost-optimizer
cargo test

# Run Go tests
cd core/ai/agents/security-scanner
go test ./...
```

#### Integration Tests
```bash
# Run integration tests
./scripts/run-integration-tests.sh

# Test agent communication
./scripts/test-agent-communication.sh
```

#### Performance Tests
```bash
# Run load tests
./scripts/run-load-tests.sh

# Run stress tests
./scripts/run-stress-tests.sh
```

---

## API Reference

### Agent Endpoints

#### Cost Optimizer Agent
```
GET  /health          - Health check
GET  /ready           - Readiness check
POST /optimize        - Cost optimization request
GET  /metrics         - Prometheus metrics
```

#### Security Scanner Agent
```
GET  /health          - Health check
GET  /ready           - Readiness check
POST /scan            - Security scan request
GET  /reports         - Scan reports
GET  /metrics         - Prometheus metrics
```

#### Swarm Coordinator Agent
```
GET  /health          - Health check
GET  /ready           - Readiness check
POST /register        - Agent registration
GET  /agents          - List registered agents
GET  /metrics         - Prometheus metrics
```

### Memory Agent Endpoints
```
GET  /health          - Health check
POST /api/memory      - Store memory
GET  /api/memory/search - Retrieve memories
GET  /metrics         - Prometheus metrics
```

---

## Contributing Guidelines

### Code Standards

#### Go Code
- Follow Go formatting standards (`go fmt`)
- Use meaningful variable names
- Add comments for public functions
- Include unit tests for all functions

#### Rust Code
- Follow Rust formatting standards (`rustfmt`)
- Use `clippy` for linting
- Document public APIs
- Include unit tests and integration tests

#### Dockerfiles
- Use multi-stage builds
- Minimize image size
- Use specific version tags
- Include health checks

### Documentation Standards

#### Markdown Format
- Use proper heading hierarchy
- Include code examples
- Add table of contents for long documents
- Use consistent formatting

#### API Documentation
- Include request/response examples
- Document error responses
- Provide curl examples
- Include authentication information

---

## Support and Contact

### Getting Help

#### Documentation Issues
- Check the relevant guide for your issue
- Look in the troubleshooting section
- Search existing GitHub issues

#### Technical Support
- Create GitHub issue with detailed description
- Include logs and error messages
- Provide steps to reproduce
- Specify environment details

#### Community Support
- Join our Slack workspace
- Participate in GitHub discussions
- Attend community meetings
- Contribute to documentation

### Resources

#### External Documentation
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)

#### Tools and Utilities
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Docker Cheat Sheet](https://docs.docker.com/get-started/cheat_sheet/)
- [Go Documentation](https://golang.org/doc/)
- [Rust Documentation](https://doc.rust-lang.org/)

---

## Version History

### v1.0.0 (Current)
- Initial release of comprehensive documentation
- Complete deployment and operation guides
- Integration and testing procedures
- Troubleshooting and maintenance procedures

### Future Releases
- Enhanced monitoring and observability
- Advanced security configurations
- Performance optimization guides
- Multi-cluster deployment strategies

---

*This documentation index is maintained by the AI infrastructure team. For updates or corrections, please create an issue or submit a pull request.*
