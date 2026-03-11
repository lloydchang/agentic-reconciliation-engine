# Comprehensive Testing Suite for GitOps Infrastructure Control Plane

This directory contains all testing scripts and documentation for validating the GitOps infrastructure platform locally and in CI/CD pipelines.

## Test Scripts

### Core Test Suites

#### `test-local-suite.sh` - Full Local Enterprise Test Suite
Comprehensive end-to-end validation of the entire GitOps platform locally:
- **Infrastructure Tests**: Flux controllers, cert-manager, certificate issuance
- **Cloud Emulator Tests**: LocalStack (AWS), Azurite (Azure), GCP services connectivity
- **Workload Tests**: Sample applications, databases, service connectivity
- **Monitoring Tests**: Prometheus, Grafana, OpenTelemetry collector deployment
- **Security Tests**: SealedSecrets, OPA Gatekeeper, Kyverno policy enforcement
- **Service Mesh Tests**: Istio and Linkerd with mTLS validation
- **Data Pipeline Tests**: Kafka connectivity, Airflow workflow orchestration
- **CI/CD Tests**: Argo CD, Argo Workflows, Kong API Gateway

```bash
# Run the complete local test suite
./tests/test-local-suite.sh
```

#### `test-components.sh` - Individual Component Testing
Quick validation of specific components without full suite:
```bash
./tests/test-components.sh flux         # Flux GitOps controllers
./tests/test-components.sh emulators    # Cloud service emulators
./tests/test-components.sh workloads    # Application deployments
./tests/test-components.sh security     # Security policies and controls
./tests/test-components.sh networking   # Ingress and service connectivity
./tests/test-components.sh all          # Run all component tests
```

#### `drift-test.sh` - GitOps Drift Detection
Validates that deployed resources match Git state:
```bash
./tests/drift-test.sh
```

## Cloud Service Emulators

### Current Coverage

#### AWS (LocalStack)
- **Services**: S3, SQS, SNS, Lambda, API Gateway, DynamoDB, RDS, ECS, EKS simulation
- **Usage**: `kubectl port-forward svc/localstack 4566:4566`
- **Test**: `curl http://localhost:4566/_localstack/health`

#### Azure (Azurite)
- **Services**: Blob Storage, Queue Storage, Table Storage
- **Usage**: `kubectl port-forward svc/azurite 10000:10000`
- **Test**: `curl http://localhost:10000/devstoreaccount1?comp=list`

#### GCP (Custom Emulators)
- **Services**: BigQuery, Cloud Storage, Pub/Sub, Cloud Functions
- **Usage**: Individual service deployments with LoadBalancer services

### Managed Kubernetes Emulation

#### EKS Emulation (AWS)
- **Tool**: LocalStack + Kind cluster
- **Features**: Simulates EKS control plane APIs
- **Deployment**: `kubectl apply -k infrastructure/tenants/aws/eks-emulator/`

#### AKS Emulation (Azure)
- **Tool**: Azure AKS emulator in LocalStack
- **Features**: AKS API simulation
- **Deployment**: `kubectl apply -k infrastructure/tenants/azure/aks-emulator/`

#### GKE Emulation (GCP)
- **Tool**: GKE emulator with Minikube + GCP auth
- **Features**: GKE API simulation
- **Deployment**: `kubectl apply -k infrastructure/tenants/gcp/gke-emulator/`

## Networking Emulators

### VPN & Mesh Networking
- **Tailscale**: Mesh VPN for Kubernetes clusters
- **WireGuard**: Kubernetes-native VPN tunnels
- **Ditto**: Edge computing and networking

### Edge & CDN
- **CDN Emulators**: Nginx/Varnish for content delivery simulation
- **WAF**: ModSecurity with Nginx for web application firewall testing

## Testing Methodologies

### Static Testing
- **SonarQube**: Code quality and security analysis
- **ESLint**: JavaScript/TypeScript linting

### Dynamic Testing
- **Jest**: JavaScript unit testing
- **pytest**: Python unit testing

### Integration Testing
- **TestContainers**: Real dependency testing with Docker

### Contract/API Testing
- **Pact**: Consumer-driven contract testing
- **REST Assured**: API validation

### Load & Stress Testing
- **k6**: Modern load testing
- **JMeter**: Enterprise load testing

### End-to-End Testing
- **Playwright**: Browser automation
- **Selenium Grid**: Distributed UI testing

### Chaos Testing
- **Chaos Mesh**: Kubernetes chaos engineering
- **Litmus**: Cloud-native chaos experiments

### Penetration Testing
- **Nuclei**: Vulnerability scanning

## Running Tests

### Local Development
```bash
# Full test suite
./tests/test-local-suite.sh

# Individual components
./tests/test-components.sh workloads

# Drift detection
./tests/drift-test.sh
```

### CI/CD Integration
Tests are automatically run via GitHub Actions (`.github/workflows/gitops-ci.yml`):
- YAML validation
- Local testing
- Security scanning
- Drift testing

## Test Coverage

| Category | Tools | Coverage |
|----------|-------|----------|
| Infrastructure | Flux, cert-manager | Complete |
| Cloud Services | LocalStack, Azurite, GCP emulators | Extensive |
| Security | SealedSecrets, OPA, Kyverno | Complete |
| Networking | Istio, Linkerd, Ingress | Complete |
| Monitoring | Prometheus, Jaeger, OpenTelemetry | Complete |
| CI/CD | Argo CD, Argo Workflows | Complete |
| Testing | 20+ testing frameworks | Complete |

## Adding New Tests

1. Create test script in `tests/` directory
2. Update this README with documentation
3. Add to CI/CD pipeline if applicable
4. Test locally before committing

## Troubleshooting

### Common Issues
- **Port conflicts**: Change port-forwarding ports in test scripts
- **Resource limits**: Increase memory/CPU in local cluster
- **Network issues**: Ensure local DNS resolution works

### Debug Mode
```bash
# Run with verbose output
DEBUG=1 ./tests/test-local-suite.sh
```

This testing suite enables comprehensive local validation of the entire GitOps infrastructure platform, ensuring production readiness without cloud costs.
