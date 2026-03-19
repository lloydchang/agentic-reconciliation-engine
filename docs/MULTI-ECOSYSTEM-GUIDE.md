# Multi-Ecosystem Support Guide

## Overview

The GitOps Infra Control Plane provides comprehensive support for multiple programming language ecosystems. Each ecosystem can be swapped in/out while maintaining the same DAG structure through Flux dependsOn relationships.

## Supported Ecosystems

### 1. Rust Ecosystem

**Label:** `ecosystem: rust`

**Characteristics:**

- Memory-safe, high-performance applications
- Cargo-based dependency management
- Tokio async runtime support
- Actix-web and Warp frameworks
- Ideal for: Performance-critical services, system tools

**Directory Structure:**

```
core/resources/tenants/3-workloads/rust/
├── cargo-workloads/
│   ├── kustomization.yaml
│   ├── cargo-deployment.yaml
│   └── rust-service.yaml
├── tokio-services/
│   ├── kustomization.yaml
│   ├── async-runtime.yaml
│   └── tokio-deployment.yaml
└── actix-web-apps/
    ├── kustomization.yaml
    ├── web-server.yaml
    └── actix-config.yaml
```

**Sample Kustomization:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
metadata:
  name: rust-workloads
  namespace: flux-system
resources:
  - cargo-workloads/
  - tokio-services/
  - actix-web-apps/
dependsOn:
  - cluster-infra
labels:
  - pairs:
      managed-by: flux
      component: rust-workloads
      ecosystem: rust
      tier: application
```

### 2. Go Ecosystem

**Label:** `ecosystem: go`

**Characteristics:**

- Cloud-native applications
- Kubernetes operators
- gRPC and HTTP services
- Gin and Echo frameworks
- Ideal for: Microservices, Kubernetes tooling

**Directory Structure:**

```
core/resources/tenants/3-workloads/go/
├── gin-services/
│   ├── kustomization.yaml
│   ├── gin-api.yaml
│   └── go-deployment.yaml
├── kubernetes-operators/
│   ├── kustomization.yaml
│   ├── operator.yaml
│   └── crd.yaml
└── grpc-services/
    ├── kustomization.yaml
    ├── grpc-server.yaml
    └── proto-config.yaml
```

### 3. Python/uv Ecosystem

**Label:** `ecosystem: python`

**Characteristics:**

- Data science and AI workloads
- FastAPI and Django frameworks
- Apache Airflow orchestration
- Jupyter notebook support
- Poetry and uv package management
- Ideal for: AI/ML, data processing, web applications

**Directory Structure:**

```
core/resources/tenants/3-workloads/python/
├── fastapi-apps/
│   ├── kustomization.yaml
│   ├── api-server.yaml
│   └── requirements.txt
├── apache-airflow/
│   ├── kustomization.yaml
│   ├── airflow-deployment.yaml
│   └── dags/
├── jupyter-notebooks/
│   ├── kustomization.yaml
│   ├── jupyter-hub.yaml
│   └── notebook-config.yaml
└── poetry-workloads/
    ├── kustomization.yaml
    ├── poetry-deployment.yaml
    └── pyproject.toml
```

### 4. TypeScript/Node.js Ecosystem

**Label:** `ecosystem: typescript`

**Characteristics:**

- Modern web applications
- React and Vue.js frontends
- NestJS and Express backends
- npm/yarn package management
- Ideal for: Full-stack applications, APIs

**Directory Structure:**

```
core/resources/tenants/3-workloads/typescript/
├── nextjs-apps/
│   ├── kustomization.yaml
│   ├── nextjs-deployment.yaml
│   └── package.json
├── nestjs-services/
│   ├── kustomization.yaml
│   ├── nestjs-api.yaml
│   └── nest-config.yaml
├── express-apis/
│   ├── kustomization.yaml
│   ├── express-server.yaml
│   └── node-deployment.yaml
└── react-frontends/
    ├── kustomization.yaml
    ├── spa-deployment.yaml
    └── build-config.yaml
```

### 5. C#/.NET Ecosystem

**Label:** `ecosystem: dotnet`

**Characteristics:**

- Enterprise applications
- ASP.NET Core web apps
- Blazor web assembly
- Entity Framework ORM
- NuGet package management
- Ideal for: Enterprise applications, Windows services

**Directory Structure:**

```
core/resources/tenants/3-workloads/dotnet/
├── aspnet-core-apps/
│   ├── kustomization.yaml
│   ├── webapp-deployment.yaml
│   └── appsettings.json
├── blazor-apps/
│   ├── kustomization.yaml
│   ├── blazor-deployment.yaml
│   └── blazor-config.yaml
└── entity-framework/
    ├── kustomization.yaml
    ├── database-migration.yaml
    └── ef-config.yaml
```

### 6. Java/JVM Ecosystem

**Label:** `ecosystem: java`

**Characteristics:**

- Spring Boot applications
- Quarkus cloud-native apps
- Maven and Gradle builds
- Enterprise Java standards
- Ideal for: Enterprise applications, microservices

**Directory Structure:**

```
core/resources/tenants/3-workloads/java/
├── spring-boot-apps/
│   ├── kustomization.yaml
│   ├── spring-deployment.yaml
│   └── application.yml
├── quarkus-services/
│   ├── kustomization.yaml
│   ├── quarkus-deployment.yaml
│   └── quarkus-config.yaml
└── maven-gradle/
    ├── kustomization.yaml
    ├── build-pipeline.yaml
    └── build-config.yaml
```

### 7. Shell/Bash Ecosystem

**Label:** `ecosystem: shell`

**Characteristics:**

- System automation scripts
- Cron job management
- Configuration management
- Simple deployment scripts
- Ideal for: System administration, simple automation

**Directory Structure:**

```
core/resources/tenants/3-workloads/shell/
├── cron-jobs/
│   ├── kustomization.yaml
│   ├── cronjob.yaml
│   └── backup-script.sh
├── bash-scripts/
│   ├── kustomization.yaml
│   ├── script-runner.yaml
│   └── automation-scripts/
└── system-core/automation/ci-cd/
    ├── kustomization.yaml
    ├── maintenance-job.yaml
    └── system-scripts/
```

## Ecosystem Swapping

### Method 1: Label-Based Selection

Update ecosystem labels in kustomization.yaml:

```yaml
labels:
  - pairs:
      ecosystem: python  # Change to rust, go, typescript, dotnet, java, shell
```

### Method 2: Resource Inclusion

Comment/uncomment ecosystem-specific resources:

```yaml
resources:
  # Core workloads
  - cert-manager/
  - monitoring/
  
  # Ecosystem-specific (choose one)
  - python/        # Uncomment for Python ecosystem
  # - go/          # Uncomment for Go ecosystem
  # - rust/        # Uncomment for Rust ecosystem
  # - typescript/  # Uncomment for TypeScript ecosystem
  # - dotnet/      # Uncomment for .NET ecosystem
  # - java/        # Uncomment for Java ecosystem
  # - shell/       # Uncomment for Shell ecosystem
```

### Method 3: ConfigMap Configuration

```yaml
configMapGenerator:
- name: ecosystem-config
  literals:
  - ECOSYSTEM=python
  - PACKAGE_MANAGER=uv
  - FRAMEWORK=fastapi
  - DEPLOYMENT_MODE=kubernetes
```

## Multi-Ecosystem Deployments

### Hybrid Architecture

Deploy multiple ecosystems simultaneously:

```yaml
resources:
  # Backend services (Go)
  - go/gin-services/
  - go/grpc-services/
  
  # Frontend applications (TypeScript)
  - typescript/nextjs-apps/
  - typescript/react-frontends/
  
  # AI/ML workloads (Python)
  - python/apache-airflow/
  - python/jupyter-notebooks/
  
  # System automation (Shell)
  - shell/cron-jobs/
  - shell/system-core/automation/ci-cd/
```

### Cross-Ecosystem Communication

Enable communication between ecosystems:

```yaml
# Service mesh configuration
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: cross-ecosystem-routing
spec:
  http:
  - match:
    - uri:
        prefix: "/api/v1"
    route:
    - destination:
        host: go-api-service
        port:
          number: 8080
  - match:
    - uri:
        prefix: "/ml"
    route:
    - destination:
        host: python-ml-service
        port:
          number: 8000
```

## Ecosystem-Specific Dependencies

### Common Dependencies

All ecosystems depend on:

- `cluster-infra` (for compute resources)
- `network-infra` (for networking)
- `cert-manager` (for TLS certificates)

### Ecosystem-Specific Dependencies

**Rust:**

- `cargo-registry` (for package caching)
- `rust-toolchain` (for compiler management)

**Go:**

- `go-proxy` (for module caching)
- `go-build-tools` (for compilation)

**Python:**

- `pypi-cache` (for package caching)
- `python-runtime` (for interpreter management)

**TypeScript:**

- `npm-registry` (for package caching)
- `node-runtime` (for Node.js runtime)

**C#/.NET:**

- `nuget-cache` (for package caching)
- `dotnet-runtime` (for .NET runtime)

**Java:**

- `maven-repository` (for artifact caching)
- `jvm-runtime` (for Java runtime)

**Shell:**

- `script-repository` (for script storage)
- `cron-scheduler` (for job scheduling)

## Best Practices

1. **Isolation**: Keep ecosystems in separate namespaces when possible
2. **Resource Limits**: Set appropriate resource limits per ecosystem
3. **Monitoring**: Use ecosystem-specific monitoring tools
4. **Security**: Apply security policies appropriate to each ecosystem
5. **Backup**: Backup ecosystem-specific configurations and data

## Validation

Check ecosystem deployment status:

```bash
# List all ecosystem workloads
kubectl get kustomizations -l ecosystem=python

# Check ecosystem-specific pods
kubectl get pods -l ecosystem=go

# Verify cross-ecosystem connectivity
kubectl exec -it $(kubectl get pod -l ecosystem=typescript -o name | head -1) -- curl http://go-api-service:8080/health
```

Generate ecosystem-specific DAG:

```bash
./core/scripts/automation/generate-dag-visualization.sh | grep -A 50 "Ecosystem"
```
