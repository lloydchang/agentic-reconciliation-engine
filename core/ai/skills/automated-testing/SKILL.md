---
name: automated-testing
description: >
  Executes comprehensive automated testing suites on pull request changes including unit tests, integration tests, performance tests, and security scans.
metadata:
  risk_level: low
  autonomy: fully_auto
  layer: temporal
  human_gate: None - test execution only
  cost_management:
    token_limit: 300
    cost_threshold: 0.10
    model_preference: "local:llama.cpp"
---

# Automated Testing Skill

This skill executes comprehensive automated testing on pull request changes, ensuring code quality and preventing regressions before deployment.

## Test Categories

### 1. Unit Testing
- **Function Tests**: Individual function and method validation
- **Class Tests**: Object-oriented code testing
- **Module Tests**: Component-level functionality verification
- **Mock Testing**: External dependency isolation and testing

### 2. Integration Testing
- **API Testing**: RESTful and GraphQL endpoint validation
- **Database Testing**: Data persistence and query verification
- **Service Integration**: Inter-service communication testing
- **Contract Testing**: API contract compliance validation

### 3. Performance Testing
- **Load Testing**: Concurrent user simulation
- **Stress Testing**: System limits and failure point identification
- **Endurance Testing**: Long-duration stability verification
- **Spike Testing**: Sudden load increase simulation

### 4. Security Testing
- **Static Analysis**: Code vulnerability scanning (SAST)
- **Dynamic Analysis**: Runtime vulnerability detection (DAST)
- **Dependency Scanning**: Third-party library security assessment
- **Container Scanning**: Docker image security verification

### 5. Quality Assurance
- **Code Coverage**: Test coverage percentage requirements
- **Mutation Testing**: Test effectiveness validation
- **Regression Testing**: Existing functionality preservation
- **Smoke Testing**: Basic functionality verification

## Test Execution Environment

### Containerized Testing
- **Isolated Environments**: Clean test execution per PR
- **Dependency Management**: Automatic dependency resolution
- **Resource Limits**: CPU and memory constraints per test suite
- **Artifact Storage**: Test results and logs persistence

### Parallel Execution
- **Concurrent Test Runs**: Multiple test suites simultaneously
- **Resource Optimization**: Efficient use of compute resources
- **Timeout Management**: Automatic termination of hung tests
- **Result Aggregation**: Unified test reporting across suites

## Integration Points

### CI/CD Pipeline Integration
- **GitHub Actions**: Native workflow integration
- **Jenkins Integration**: Legacy pipeline support
- **GitLab CI**: Cross-platform compatibility
- **Custom Webhooks**: Flexible integration options

### Notification Systems
- **PR Comments**: Test results posted to pull requests
- **Slack Integration**: Team notifications for test failures
- **Email Alerts**: Stakeholder notifications for critical issues
- **Dashboard Updates**: Real-time test status visualization

## Test Result Analysis

### Success Criteria
```yaml
test_requirements:
  unit_tests:
    coverage_minimum: 80%
    pass_rate: 100%
  integration_tests:
    pass_rate: 95%
    timeout_seconds: 300
  performance_tests:
    response_time_max: 2000ms
    throughput_minimum: 1000rpm
  security_scans:
    critical_vulnerabilities: 0
    high_vulnerabilities_max: 5
```

### Failure Analysis
- **Root Cause Detection**: Identify failing test sources
- **Impact Assessment**: Determine deployment blocking status
- **Regression Detection**: Identify unintended functionality changes
- **Flaky Test Identification**: Distinguish between real failures and test instability

## Usage Examples

### Basic Test Execution
```yaml
workflows:
  pr-testing:
    on: pull_request
    skills:
      - automated-testing
    inputs:
      test_scope: ["unit", "integration"]
      environment: "staging"
      timeout_minutes: 30
```

### Full CI Pipeline
```yaml
workflows:
  comprehensive-ci:
    on: pull_request
    steps:
      - skill: pr-analysis
      - skill: automated-testing
        inputs:
          test_categories: ["unit", "integration", "performance", "security"]
          coverage_required: 85%
      - skill: risk-assessment
      - gate: approval_required
        condition: risk_score > 7
```

### Performance Regression Testing
```yaml
workflows:
  performance-gate:
    triggers:
      - files_changed: ["src/**/*.go", "pkg/**/*.go"]
    skills:
      - automated-testing
    inputs:
      test_types: ["performance"]
      baseline_comparison: true
      regression_threshold: 10%
```

## Output Format

```json
{
  "summary": {
    "total_tests": 1250,
    "passed": 1185,
    "failed": 15,
    "skipped": 50,
    "duration_seconds": 420,
    "overall_status": "partial_success"
  },
  "categories": {
    "unit": {
      "status": "passed",
      "coverage": 87.5,
      "tests": 850,
      "failures": 0
    },
    "integration": {
      "status": "partial_success",
      "coverage": 92.1,
      "tests": 320,
      "failures": 8
    },
    "performance": {
      "status": "passed",
      "metrics": {
        "avg_response_time": 145,
        "throughput": 1250,
        "error_rate": 0.02
      }
    },
    "security": {
      "status": "warning",
      "vulnerabilities": {
        "critical": 0,
        "high": 2,
        "medium": 15,
        "low": 23
      }
    }
  },
  "failures": [
    {
      "test": "UserServiceTest.testCreateUserValidation",
      "category": "integration",
      "error": "Expected status 201, got 400",
      "details": "Email validation failing for international domains"
    }
  ],
  "recommendations": [
    {
      "type": "fix_required",
      "description": "Update email validation regex to support international domains",
      "severity": "medium"
    }
  ]
}
```

## Configuration Options

### Test Environment Configuration
```yaml
test_environment:
  database:
    type: postgres
    version: "13"
    persistence: ephemeral
  cache:
    type: redis
    version: "6.2"
  messaging:
    type: kafka
    version: "2.8"
```

### Quality Gates
```yaml
quality_gates:
  - name: "unit_coverage"
    threshold: 80
    action: "block_merge"
  - name: "integration_pass_rate"
    threshold: 95
    action: "require_review"
  - name: "security_critical"
    threshold: 0
    action: "block_merge"
```

## Failure Handling

### Test Flakiness Management
- **Retry Logic**: Automatic retry for known flaky tests
- **Quarantine**: Isolation of consistently failing tests
- **Investigation**: Automated root cause analysis for failures
- **Alerting**: Notification for test stability issues

### Environment Issues
- **Resource Constraints**: Automatic scaling for resource-intensive tests
- **Dependency Failures**: Fallback to alternative test environments
- **Network Issues**: Retry logic for external service dependencies
- **Timeout Management**: Progressive timeout increases for slow tests

## Reporting and Analytics

### Test Metrics Dashboard
- **Historical Trends**: Test performance over time
- **Failure Patterns**: Common failure modes and causes
- **Coverage Trends**: Code coverage progression
- **Performance Benchmarks**: Performance test results tracking

### Team Insights
- **Productivity Metrics**: Tests per commit, failure rates
- **Quality Indicators**: Defect escape rates, rework metrics
- **Process Improvements**: Test automation effectiveness
- **Risk Assessment**: Deployment confidence scoring
