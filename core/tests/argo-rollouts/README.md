# Argo Rollouts Test Suite

This directory contains comprehensive tests for Argo Rollouts with K8sGPT Qwen integration.

## Test Files

### Shell Tests
- `test-argo-rollouts.sh` - Comprehensive shell-based test suite
- `integration-test.sh` - Integration tests for complete workflows
- `performance-test.sh` - Performance and load testing

### Python Tests
- `test_argo_rollouts_python.py` - Python-based unit and integration tests
- `test_performance.py` - Performance benchmarking tests
- `test_k8sgpt_integration.py` - K8sGPT integration specific tests

### Test Fixtures
- `fixtures/` - Test manifests and configurations
- `mocks/` - Mock services and endpoints for testing

## Running Tests

### Quick Test Run
```bash
# Run all shell tests
./test-argo-rollouts.sh

# Run Python tests
python3 test_argo_rollouts_python.py

# Run specific test categories
./test-argo-rollouts.sh --category basic
./test-argo-rollouts.sh --category integration
./test-argo-rollouts.sh --category performance
```

### Comprehensive Test Suite
```bash
# Run all tests with detailed output
make test-argo-rollouts

# Run tests with coverage
make test-coverage

# Run performance benchmarks
make test-performance
```

### Test Categories

#### 1. Basic Functionality Tests
- Rollout creation and management
- Strategy execution (canary, blue-green, A/B)
- CLI functionality
- CRD validation

#### 2. Integration Tests
- K8sGPT integration
- Analysis templates
- Metrics and monitoring
- Security configuration

#### 3. Performance Tests
- Concurrent rollout deployment
- Resource usage analysis
- Scalability testing
- Load testing

#### 4. Security Tests
- RBAC configuration
- Network policies
- Secret management
- Pod security policies

## Test Configuration

### Environment Variables
```bash
# Test namespace
export TEST_NAMESPACE="argo-rollouts-test"

# Timeout settings
export TEST_TIMEOUT="300s"
export ROLLOUT_TIMEOUT="600s"

# K8sGPT configuration
export K8SGPT_NAMESPACE="$TOPDIR"
export QWEN_MODEL="qwen2.5-7b-instruct"

# Performance test settings
export NUM_CONCURRENT_ROLLOUTS="5"
export PERFORMANCE_THRESHOLD="120s"
```

### Test Configuration File
```yaml
# test-config.yaml
test:
  namespace: "argo-rollouts-test"
  timeout: "300s"
  cleanup: true
  
rollouts:
  basic:
    replicas: 2
    image: "nginx:1.20"
  
  canary:
    replicas: 3
    steps:
      - setWeight: 20
      - pause: {duration: "30s"}
      - setWeight: 50
      - pause: {duration: "30s"}
  
  performance:
    concurrent: 5
    threshold: "120s"

k8sgpt:
  enabled: true
  namespace: "$TOPDIR"
  model: "qwen2.5-7b-instruct"
  
monitoring:
  enabled: true
  metrics_port: 8090
  health_check: true
```

## Test Results

### Expected Results
- **Basic Tests**: Should pass in any properly configured Argo Rollouts installation
- **Integration Tests**: Require K8sGPT and monitoring setup
- **Performance Tests**: May require cluster with sufficient resources

### Test Report Format
```
================================================================
Argo Rollouts Test Results Summary
================================================================
Total Tests: 15
Tests Passed: 14
Tests Failed: 1

✅ Basic Rollout Creation - PASSED
✅ Canary Strategy - PASSED
✅ Blue-Green Strategy - PASSED
✅ Analysis Templates - PASSED
✅ K8sGPT Integration - PASSED
✅ Rollout Rollback - PASSED
✅ Metrics and Monitoring - PASSED
✅ CLI Functionality - PASSED
✅ Security Configuration - PASSED
✅ Performance Test - PASSED
❌ Network Policies - FAILED (optional)

🎉 14/15 tests passed!
```

## Troubleshooting

### Common Test Failures

#### 1. Rollout Creation Failed
```bash
# Check Argo Rollouts installation
kubectl get crd rollouts.argoproj.io
kubectl get pods -n argo-rollouts

# Check permissions
kubectl auth can-i create rollouts --as=system:serviceaccount:argo-rollouts:argo-rollouts
```

#### 2. K8sGPT Integration Failed
```bash
# Check K8sGPT deployment
kubectl get pods -n $TOPDIR | grep k8sgpt

# Check Qwen configuration
kubectl get secret qwen-secret -n $TOPDIR
kubectl get configmap qwen-config -n $TOPDIR
```

#### 3. Performance Test Failed
```bash
# Check cluster resources
kubectl top nodes
kubectl describe nodes

# Increase timeout
export TEST_TIMEOUT="600s"
```

#### 4. CLI Functionality Failed
```bash
# Install kubectl plugin
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verify installation
kubectl argo rollouts version
```

## Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/argo-rollouts-test.yml
name: Argo Rollouts Tests

on:
  push:
    paths:
      - 'overlay/argo-rollouts/**'
      - 'tests/argo-rollouts/**'
  pull_request:
    paths:
      - 'overlay/argo-rollouts/**'
      - 'tests/argo-rollouts/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Kubernetes
        uses: helm/kind-action@v1.4.0
        with:
          cluster_name: test-cluster
          
      - name: Install Argo Rollouts
        run: |
          kubectl create namespace argo-rollouts
          kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
          
      - name: Run Tests
        run: |
          chmod +x tests/argo-rollouts/test-argo-rollouts.sh
          ./tests/argo-rollouts/test-argo-rollouts.sh
```

### Jenkins Pipeline Integration
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'kubectl create namespace argo-rollouts-test --dry-run=client -o yaml | kubectl apply -f -'
                sh 'kubectl apply -n argo-rollouts-test -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml'
            }
        }
        
        stage('Test') {
            steps {
                sh 'chmod +x tests/argo-rollouts/test-argo-rollouts.sh'
                sh './tests/argo-rollouts/test-argo-rollouts.sh'
            }
        }
        
        stage('Cleanup') {
            steps {
                sh 'kubectl delete namespace argo-rollouts-test --ignore-not-found=true'
            }
        }
    }
}
```

## Test Data and Mocks

### Mock Services
```yaml
# mocks/mock-prometheus.yaml
apiVersion: v1
kind: Service
metadata:
  name: mock-prometheus
  namespace: argo-rollouts-test
spec:
  selector:
    app: mock-prometheus
  ports:
  - port: 9090
    targetPort: 9090
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mock-prometheus
  namespace: argo-rollouts-test
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mock-prometheus
  template:
    metadata:
      labels:
        app: mock-prometheus
    spec:
      containers:
      - name: mock-prometheus
        image: nginx:1.20
        ports:
        - containerPort: 9090
```

### Test Metrics
```python
# test_metrics.py
def generate_mock_metrics():
    """Generate mock Prometheus metrics for testing"""
    return """
# HELP argo_rollouts_rollout_phase Current phase of rollout
# TYPE argo_rollouts_rollout_phase gauge
argo_rollouts_rollout_phase{namespace="test",rollout="test-rollout",phase="Healthy"} 1

# HELP argo_rollouts_controller_reconcile_duration_seconds Time taken to reconcile rollout
# TYPE argo_rollouts_controller_reconcile_duration_seconds histogram
argo_rollouts_controller_reconcile_duration_seconds_bucket{le="0.1"} 1
argo_rollouts_controller_reconcile_duration_seconds_bucket{le="1.0"} 1
argo_rollouts_controller_reconcile_duration_seconds_bucket{le="+Inf"} 1
argo_rollouts_controller_reconcile_duration_seconds_count 1
argo_rollouts_controller_reconcile_duration_seconds_sum 0.05
"""
```

## Best Practices

### Test Design
1. **Isolation**: Each test should run independently
2. **Cleanup**: Clean up resources after each test
3. **Idempotency**: Tests should be runnable multiple times
4. **Timeouts**: Set appropriate timeouts for cluster operations
5. **Error Handling**: Handle expected failures gracefully

### Performance Testing
1. **Baseline**: Establish performance baselines
2. **Thresholds**: Set realistic performance thresholds
3. **Monitoring**: Monitor resource usage during tests
4. **Scaling**: Test with different cluster sizes
5. **Concurrency**: Test concurrent operations

### Security Testing
1. **RBAC**: Test with different permission levels
2. **Network**: Test network policies and restrictions
3. **Secrets**: Test secret management and access
4. **Pod Security**: Test pod security policies
5. **Audit**: Test audit logging and compliance

## Contributing

When adding new tests:

1. **Follow naming conventions**: Use descriptive test names
2. **Add documentation**: Document test purpose and expected results
3. **Include cleanup**: Ensure tests clean up resources
4. **Handle dependencies**: Check for required dependencies
5. **Update CI**: Update CI pipelines as needed

## Test Coverage

### Coverage Areas
- ✅ Rollout creation and management
- ✅ Strategy execution (canary, blue-green, A/B)
- ✅ Analysis templates and runs
- ✅ K8sGPT integration
- ✅ CLI functionality
- ✅ Metrics and monitoring
- ✅ Security configuration
- ✅ Performance and scalability
- ⏳ Multi-cluster deployments
- ⏳ Advanced traffic routing
- ⏳ Custom analysis providers

### Coverage Goals
- **Functionality**: 95% code coverage
- **Integration**: 90% test coverage
- **Performance**: 80% benchmark coverage
- **Security**: 100% security test coverage
