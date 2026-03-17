# Argo Workflows User Guide

## Complete User Guide for Argo Workflows with Qwen LLM Integration

This comprehensive guide covers all aspects of using Argo Workflows with Qwen LLM integration, from basic concepts to advanced workflows and AI-powered automation.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Workflow Design](#workflow-design)
3. [Qwen LLM Integration](#qwen-llm-integration)
4. [Advanced Workflows](#advanced-workflows)
5. [Monitoring and Debugging](#monitoring-and-debugging)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Core Concepts

### Argo Workflows Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Argo Workflows                           │
├─────────────────────────────────────────────────────────────┤
│  Workflow Controller                                       │
│  ├── Manages workflow lifecycle                            │
│  ├── Executes workflow steps                               │
│  ├── Handles artifacts and parameters                      │
│  └── Integrates with Kubernetes API                        │
├─────────────────────────────────────────────────────────────┤
│  Workflow Server (UI)                                     │
│  ├── Web interface for workflows                          │
│  ├── REST API for programmatic access                     │
│  ├── Authentication and authorization                    │
│  └── Real-time workflow updates                           │
├─────────────────────────────────────────────────────────────┤
│  Workflow Execution                                        │
│  ├── Pods for workflow steps                             │
│  ├── Artifact storage                                    │
│  ├── Parameter passing                                  │
│  └── Result collection                                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### Workflows
- **Definition**: Container-native workflow specification
- **Execution**: Runs as Kubernetes pods
- **State**: Maintained by the controller
- **Lifecycle**: Created, executed, completed, archived

#### Templates
- **Reusable**: Define step logic once, use many times
- **Types**: Container, script, resource, dag, steps
- **Parameters**: Input/output parameter handling
- **Artifacts**: Input/output artifact management

#### Executors
- **PNS**: Process namespace sharing (default)
- **Docker**: Docker-in-docker execution
- **K8sAPI**: Kubernetes API-based execution
- **Custom**: Custom executor implementations

### Qwen LLM Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Qwen LLM Stack                           │
├─────────────────────────────────────────────────────────────┤
│  Qwen K8sGPT Service                                        │
│  ├── REST API for analysis                                 │
│  ├── Kubernetes resource inspection                        │
│  ├── Workflow analysis capabilities                        │
│  └── Integration with LocalAI                               │
├─────────────────────────────────────────────────────────────┤
│  Qwen LocalAI Model                                        │
│  ├── Local LLM inference                                   │
│  ├── Model loading and caching                             │
│  ├── API endpoint for K8sGPT                              │
│  └── Resource optimization                                 │
├─────────────────────────────────────────────────────────────┤
│  Integration Points                                         │
│  ├── Workflow hooks                                         │
│  ├── Event-driven analysis                                 │
│  ├── Automated troubleshooting                             │
│  └── Performance optimization                             │
└─────────────────────────────────────────────────────────────┘
```

## Workflow Design

### Basic Workflow Structure

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: example-workflow
  namespace: argo-workflows
  labels:
    app.kubernetes.io/name: argo-workflows
    app.kubernetes.io/component: example
spec:
  # Workflow entry point
  entrypoint: main
  
  # Input parameters
  arguments:
    parameters:
    - name: message
      value: "Hello World"
  
  # Workflow templates
  templates:
  - name: main
    # Template definition
    container:
      image: alpine:latest
      command: [echo]
      args: ["{{workflow.parameters.message}}"]
```

### Template Types

#### 1. Container Template

```yaml
- name: container-step
  container:
    image: python:3.9-alpine
    command: [python, -c]
    args: |
      print("Running container step")
      print("Input: {{inputs.parameters.input}}")
    resources:
      requests:
        cpu: "100m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
```

#### 2. Script Template

```yaml
- name: script-step
  script:
    image: alpine:latest
    command: [sh]
    source: |
      echo "Running script step"
      echo "Current directory: $(pwd)"
      echo "Files: $(ls -la)"
```

#### 3. Resource Template

```yaml
- name: resource-step
  resource:
    action: create
    manifest: |
      apiVersion: v1
      kind: ConfigMap
      metadata:
        name: test-config
        namespace: argo-workflows
      data:
        key: value
```

#### 4. DAG Template

```yaml
- name: dag-workflow
  dag:
    tasks:
    - name: task-a
      template: task-template
    - name: task-b
      template: task-template
      dependencies: [task-a]
    - name: task-c
      template: task-template
      dependencies: [task-a]
    - name: task-d
      template: task-template
      dependencies: [task-b, task-c]
```

#### 5. Steps Template

```yaml
- name: steps-workflow
  steps:
  - - name: step-1
      template: step-template
      arguments:
        parameters:
        - name: input
          value: "Step 1 input"
  - - name: step-2a
      template: step-template
      arguments:
        parameters:
        - name: input
          value: "Step 2a input"
    - name: step-2b
      template: step-template
      arguments:
        parameters:
        - name: input
          value: "Step 2b input"
```

### Parameters and Artifacts

#### Input Parameters

```yaml
spec:
  arguments:
    parameters:
    - name: string-param
      value: "default value"
    - name: number-param
      value: "42"
    - name: boolean-param
      value: "true"
    - name: list-param
      value: "item1,item2,item3"
```

#### Output Parameters

```yaml
- name: generate-output
  container:
    image: alpine:latest
    command: [sh, -c]
    args: |
      echo "generated-value" > /tmp/output.txt
  outputs:
    parameters:
    - name: result
      valueFrom:
        path: /tmp/output.txt
```

#### Input Artifacts

```yaml
- name: process-artifact
  inputs:
    artifacts:
    - name: input-data
      path: /tmp/input.json
      raw:
        data: '{"key": "value"}'
    - name: config-file
      path: /tmp/config.yaml
      configMap:
        name: workflow-config
        key: config.yaml
  container:
    image: alpine:latest
    command: [cat]
    args: ["/tmp/input.json"]
```

#### Output Artifacts

```yaml
- name: generate-artifact
  outputs:
    artifacts:
    - name: output-data
      path: /tmp/output.json
      s3:
        endpoint: minio:9000
        bucket: argo-workflows
        key: artifacts/output-{{workflow.uid}}.json
        accessKeySecret:
          name: argo-workflows-minio
          key: accesskey
        secretKeySecret:
          name: argo-workflows-minio
          key: secretkey
  container:
    image: alpine:latest
    command: [sh, -c]
    args: |
      echo '{"result": "success", "timestamp": "'$(date -Iseconds)'"}' > /tmp/output.json
```

### Workflow Hooks

#### Running Hook

```yaml
spec:
  hooks:
    running:
    - template: qwen-analysis-hook
      arguments:
        parameters:
        - name: workflow-name
          value: "{{workflow.name}}"
        - name: workflow-status
          value: "{{workflow.status}}"
```

#### Exit Hook

```yaml
spec:
  onExit: exit-handler
  templates:
  - name: exit-handler
    container:
      image: alpine:latest
      command: [sh, -c]
      args: |
        echo "Workflow {{workflow.name}} completed with status {{workflow.status}}"
        echo "Duration: {{workflow.duration}}"
```

## Qwen LLM Integration

### Qwen K8sGPT API

#### Basic Analysis Request

```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "workflow_analysis",
    "namespace": "argo-workflows",
    "component": "my-workflow",
    "severity": "info",
    "description": "Analyze workflow execution",
    "timestamp": "'$(date -Iseconds)'",
    "analysis_context": "performance-analysis"
  }'
```

#### Pod Troubleshooting

```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "pod_troubleshooting",
    "namespace": "default",
    "component": "failing-pod",
    "severity": "warning",
    "description": "Pod is in CrashLoopBackOff state",
    "timestamp": "'$(date -Iseconds)'",
    "analysis_context": "pod-issue-diagnosis",
    "pod_data": {
      "name": "failing-pod",
      "status": "CrashLoopBackOff",
      "restart_count": 5,
      "last_error": "Exit code 1"
    }
  }'
```

#### Deployment Analysis

```bash
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "deployment_analysis",
    "namespace": "production",
    "component": "web-app",
    "severity": "info",
    "description": "Deployment rollout analysis",
    "timestamp": "'$(date -Iseconds)'",
    "analysis_context": "deployment-optimization",
    "deployment_data": {
      "replicas": 3,
      "ready_replicas": 2,
      "strategy": "RollingUpdate",
      "image": "myapp:v1.2.0"
    }
  }'
```

### Workflow Integration

#### Qwen Analysis Workflow

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: qwen-analysis-workflow
  namespace: argo-workflows
  labels:
    app.kubernetes.io/name: argo-workflows
    app.kubernetes.io/llm: qwen
spec:
  entrypoint: analyze-with-qwen
  arguments:
    parameters:
    - name: target-workflow
      value: ""
    - name: analysis-type
      value: "comprehensive"
  templates:
  - name: analyze-with-qwen
    steps:
    - - name: collect-workflow-data
        template: collect-data
        arguments:
          parameters:
          - name: target
            value: "{{workflow.parameters.target-workflow}}"
    - - name: analyze-with-qwen
        template: qwen-analysis
        arguments:
          parameters:
          - name: analysis-type
            value: "{{workflow.parameters.analysis-type}}"
          - name: workflow-data
            value: "{{steps.collect-workflow-data.outputs.result}}"
    - - name: generate-report
        template: create-report
        arguments:
          parameters:
          - name: analysis-result
            value: "{{steps.analyze-with-qwen.outputs.result}}"
  
  - name: collect-data
    inputs:
      parameters:
      - name: target
    container:
      image: bitnami/kubectl:latest
      command: [sh, -c]
      args: |
        if [ -n "{{inputs.parameters.target}}" ]; then
          kubectl get workflow {{inputs.parameters.target}} -n argo-workflows -o json
        else
          kubectl get workflows -n argo-workflows -o json
        fi
  
  - name: qwen-analysis
    inputs:
      parameters:
      - name: analysis-type
      - name: workflow-data
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import requests
        
        analysis_request = {
            "event_type": "workflow_analysis",
            "namespace": "argo-workflows",
            "component": "{{workflow.parameters.target-workflow}}",
            "severity": "info",
            "description": "{{inputs.parameters.analysis-type}} analysis",
            "timestamp": "$(date -Iseconds)",
            "analysis_context": "workflow-performance-analysis",
            "workflow_data": json.loads("""{{inputs.parameters.workflow-data}}""")
        }
        
        response = requests.post(
            "http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze",
            json=analysis_request,
            timeout=60
        )
        
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Analysis failed: {response.status_code}")
            exit(1)
  
  - name: create-report
    inputs:
      parameters:
      - name: analysis-result
    container:
      image: alpine:latest
      command: [sh, -c]
      args: |
        echo "=== Qwen Analysis Report ==="
        echo "Generated at: $(date)"
        echo "Analysis Type: {{workflow.parameters.analysis-type}}"
        echo "Target: {{workflow.parameters.target-workflow}}"
        echo ""
        echo "Results:"
        echo "{{inputs.parameters.analysis-result}}"
```

#### AI-Powered Troubleshooting

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: ai-troubleshooting
  namespace: argo-workflows
spec:
  entrypoint: troubleshoot
  arguments:
    parameters:
    - name: target-pod
      value: ""
    - name: namespace
      value: "default"
  templates:
  - name: troubleshoot
    steps:
    - - name: collect-pod-info
        template: collect-pod-data
    - - name: analyze-with-qwen
        template: qwen-pod-analysis
    - - name: apply-fixes
        template: apply-recommendations
  
  - name: qwen-pod-analysis
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import requests
        import os
        
        # Get pod information from previous step
        with open('/tmp/pod-info.json', 'r') as f:
            pod_info = json.load(f)
        
        analysis_request = {
            "event_type": "pod_troubleshooting",
            "namespace": "{{workflow.parameters.namespace}}",
            "component": "{{workflow.parameters.target-pod}}",
            "severity": "warning",
            "description": "AI-powered pod troubleshooting",
            "timestamp": "$(date -Iseconds)",
            "analysis_context": "automated-troubleshooting",
            "pod_data": pod_info
        }
        
        response = requests.post(
            "http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze",
            json=analysis_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("AI Analysis Results:")
            print(json.dumps(result, indent=2))
            
            # Save recommendations for next step
            with open('/tmp/recommendations.json', 'w') as f:
                json.dump(result.get('recommendations', []), f)
        else:
            print(f"Analysis failed: {response.status_code}")
            exit(1)
```

### Custom Analysis Prompts

#### Workflow Performance Analysis

```yaml
# In qwen-configmap.yaml
analysis-prompts.yaml: |
  workflow_performance_analysis: |
    Analyze this Argo Workflow execution for performance optimization:
    
    Workflow Details:
    - Name: {{.workflow_name}}
    - Status: {{.status}}
    - Duration: {{.duration}}
    - Steps: {{.steps}}
    - Resource Usage: {{.resource_usage}}
    
    Focus Areas:
    1. Performance bottlenecks and optimization opportunities
    2. Resource utilization efficiency
    3. Step execution time analysis
    4. Parallelization opportunities
    5. Cost optimization recommendations
    
    Provide:
    - Detailed performance analysis
    - Specific optimization recommendations
    - Resource allocation suggestions
    - Implementation steps
```

#### Security Analysis

```yaml
  security_analysis: |
    Perform security analysis of this Kubernetes resource:
    
    Resource Details:
    - Type: {{.resource_type}}
    - Name: {{.resource_name}}
    - Namespace: {{.namespace}}
    - Configuration: {{.configuration}}
    
    Security Focus Areas:
    1. RBAC permissions and access control
    2. Security contexts and capabilities
    3. Network policies and isolation
    4. Secret management practices
    5. Vulnerability assessments
    6. Compliance requirements
    
    Provide:
    - Security risk assessment
    - Vulnerability identification
    - Hardening recommendations
    - Compliance checklist
```

## Advanced Workflows

### CI/CD Pipeline

#### Complete CI/CD Workflow

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: ci-cd-pipeline
  namespace: argo-workflows
  labels:
    app.kubernetes.io/name: argo-workflows
    app.kubernetes.io/component: ci-cd
spec:
  entrypoint: pipeline
  arguments:
    parameters:
    - name: repo-url
      value: "https://github.com/example/app.git"
    - name: branch
      value: "main"
    - name: commit-sha
      value: ""
    - name: docker-image
      value: "example/app:latest"
    - name: deploy-environment
      value: "staging"
  templates:
  - name: pipeline
    steps:
    - - name: checkout-code
        template: git-checkout
    - - name: run-tests
        template: test-suite
        arguments:
          artifacts:
          - name: source-code
            from: "{{steps.checkout-code.outputs.artifacts.source}}"
    - - name: security-scan
        template: security-analysis
        arguments:
          artifacts:
          - name: source-code
            from: "{{steps.checkout-code.outputs.artifacts.source}}"
    - - name: build-image
        template: docker-build
        arguments:
          artifacts:
          - name: source-code
            from: "{{steps.checkout-code.outputs.artifacts.source}}"
    - - name: qwen-analysis
        template: qwen-pipeline-analysis
    - - name: deploy
        template: deploy-app
        when: "{{steps.qwen-analysis.outputs.result}} == 'success'"
        arguments:
          parameters:
          - name: environment
            value: "{{workflow.parameters.deploy-environment}}"
          - name: image
            value: "{{workflow.parameters.docker-image}}"
  
  - name: git-checkout
    container:
      image: alpine/git:latest
      command: [sh, -c]
      args: |
        git clone {{workflow.parameters.repo-url}} /src
        cd /src
        git checkout {{workflow.parameters.branch}}
        if [ -n "{{workflow.parameters.commit-sha}}" ]; then
          git checkout {{workflow.parameters.commit-sha}}
        fi
        echo "Checked out commit: $(git rev-parse HEAD)"
    outputs:
      artifacts:
      - name: source-code
        path: /src
  
  - name: test-suite
    inputs:
      artifacts:
      - name: source-code
        path: /src
    container:
      image: golang:1.21-alpine
      workingDir: /src
      command: [sh, -c]
      args: |
        echo "Running test suite..."
        go mod download
        go test -v ./...
        go test -coverprofile=coverage.out ./...
        echo "Tests completed successfully"
    outputs:
      artifacts:
      - name: test-results
        path: /src/coverage.out
  
  - name: security-analysis
    inputs:
      artifacts:
      - name: source-code
        path: /src
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import requests
        import json
        
        # Send source code to Qwen for security analysis
        analysis_request = {
            "event_type": "security_scan",
            "namespace": "argo-workflows",
            "component": "ci-cd-pipeline",
            "severity": "high",
            "description": "Security analysis of source code",
            "timestamp": "$(date -Iseconds)",
            "analysis_context": "security-vulnerability-assessment",
            "source_code_path": "/src"
        }
        
        response = requests.post(
            "http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze",
            json=analysis_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Security Analysis Results:")
            print(json.dumps(result, indent=2))
            
            # Save results
            with open('/tmp/security-results.json', 'w') as f:
                json.dump(result, f)
        else:
            print(f"Security analysis failed: {response.status_code}")
            exit(1)
    outputs:
      artifacts:
      - name: security-results
        path: /tmp/security-results.json
  
  - name: docker-build
    inputs:
      artifacts:
      - name: source-code
        path: /src
    container:
      image: docker:latest
      command: [sh, -c]
      args: |
        echo "Building Docker image..."
        cd /src
        docker build -t {{workflow.parameters.docker-image}} .
        echo "Image built successfully"
        docker save {{workflow.parameters.docker-image}} > /tmp/image.tar
    outputs:
      artifacts:
      - name: docker-image
        path: /tmp/image.tar
  
  - name: qwen-pipeline-analysis
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import requests
        
        # Comprehensive pipeline analysis
        analysis_request = {
            "event_type": "ci_cd_pipeline_analysis",
            "namespace": "argo-workflows",
            "component": "ci-cd-pipeline",
            "severity": "info",
            "description": "CI/CD pipeline analysis using Qwen LLM",
            "timestamp": "$(date -Iseconds)",
            "analysis_context": "pipeline-performance-analysis",
            "pipeline_data": {
                "repository": "{{workflow.parameters.repo-url}}",
                "branch": "{{workflow.parameters.branch}}",
                "commit": "{{workflow.parameters.commit-sha}}",
                "image": "{{workflow.parameters.docker-image}}",
                "environment": "{{workflow.parameters.deploy-environment}}"
            }
        }
        
        response = requests.post(
            "http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze",
            json=analysis_request,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Qwen Pipeline Analysis Result:")
            print(json.dumps(result, indent=2))
            
            # Determine if pipeline should proceed
            if result.get('status') == 'success':
                print("success")
            else:
                print("failure")
        else:
            print(f"Analysis failed with status {response.status_code}")
            print("failure")
  
  - name: deploy-app
    inputs:
      parameters:
      - name: environment
      - name: image
    container:
      image: bitnami/kubectl:latest
      command: [sh, -c]
      args: |
        echo "Deploying to {{inputs.parameters.environment}}..."
        
        # Update deployment with new image
        kubectl set image deployment/app app={{inputs.parameters.image}} -n {{inputs.parameters.environment}}
        
        # Wait for rollout
        kubectl rollout status deployment/app -n {{inputs.parameters.environment}} --timeout=300s
        
        echo "Deployment completed successfully"
        
        # Send deployment info to Qwen for analysis
        curl -X POST http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze \
          -H "Content-Type: application/json" \
          -d '{
            "event_type": "deployment_analysis",
            "namespace": "{{inputs.parameters.environment}}",
            "component": "app",
            "severity": "info",
            "description": "Deployment completed successfully",
            "timestamp": "'$(date -Iseconds)'",
            "analysis_context": "deployment-success-analysis"
          }'
```

### Data Processing Pipeline

#### ETL Workflow with Qwen Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: data-processing-pipeline
  namespace: argo-workflows
spec:
  entrypoint: data-pipeline
  arguments:
    parameters:
    - name: data-source
      value: "s3://data-bucket/input/"
    - name: output-path
      value: "s3://data-bucket/output/"
    - name: processing-type
      value: "etl"
  templates:
  - name: data-pipeline
    dag:
      tasks:
      - name: extract-data
        template: extract
        arguments:
          parameters:
          - name: source
            value: "{{workflow.parameters.data-source}}"
      - name: validate-data
        template: validate
        dependencies: [extract-data]
        arguments:
          artifacts:
          - name: raw-data
            from: "{{tasks.extract-data.outputs.artifacts.data}}"
      - name: analyze-data-quality
        template: qwen-data-analysis
        dependencies: [validate-data]
        arguments:
          artifacts:
          - name: validated-data
            from: "{{tasks.validate-data.outputs.artifacts.data}}"
      - name: transform-data
        template: transform
        dependencies: [validate-data, analyze-data-quality]
        arguments:
          artifacts:
          - name: data
            from: "{{tasks.validate-data.outputs.artifacts.data}}"
          - name: analysis-results
            from: "{{tasks.analyze-data-quality.outputs.artifacts.results}}"
      - name: load-data
        template: load
        dependencies: [transform-data]
        arguments:
          artifacts:
          - name: processed-data
            from: "{{tasks.transform-data.outputs.artifacts.data}}"
          parameters:
          - name: destination
            value: "{{workflow.parameters.output-path}}"
  
  - name: extract
    inputs:
      parameters:
      - name: source
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import boto3
        import json
        import os
        
        # Extract data from source
        s3 = boto3.client('s3', endpoint_url='http://minio:9000')
        
        # List and download files
        response = s3.list_objects_v2(Bucket='data-bucket', Prefix='input/')
        
        for obj in response.get('Contents', []):
            file_key = obj['Key']
            file_name = file_key.split('/')[-1]
            
            s3.download_file('data-bucket', file_key, f'/tmp/{file_name}')
            print(f"Extracted: {file_name}")
        
        print("Data extraction completed")
    outputs:
      artifacts:
      - name: data
        path: /tmp
  
  - name: validate
    inputs:
      artifacts:
      - name: raw-data
        path: /tmp/raw-data
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import pandas as pd
        import os
        
        # Validate data quality
        data_files = [f for f in os.listdir('/tmp/raw-data') if f.endswith('.csv')]
        
        validation_results = []
        for file in data_files:
            try:
                df = pd.read_csv(f'/tmp/raw-data/{file}')
                
                validation = {
                    'file': file,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'null_values': df.isnull().sum().sum(),
                    'duplicates': df.duplicated().sum(),
                    'valid': True
                }
                
                validation_results.append(validation)
                print(f"Validated {file}: {validation['rows']} rows")
                
            except Exception as e:
                validation = {
                    'file': file,
                    'error': str(e),
                    'valid': False
                }
                validation_results.append(validation)
                print(f"Validation failed for {file}: {e}")
        
        # Save validation results
        with open('/tmp/validation-results.json', 'w') as f:
            json.dump(validation_results, f)
        
        # Move validated files
        os.makedirs('/tmp/validated-data', exist_ok=True)
        for file in data_files:
            os.rename(f'/tmp/raw-data/{file}', f'/tmp/validated-data/{file}')
        
        print("Data validation completed")
    outputs:
      artifacts:
      - name: data
        path: /tmp/validated-data
  
  - name: qwen-data-analysis
    inputs:
      artifacts:
      - name: validated-data
        path: /tmp/validated-data
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import requests
        import os
        
        # Analyze data with Qwen
        analysis_request = {
            "event_type": "data_quality_analysis",
            "namespace": "argo-workflows",
            "component": "data-processing-pipeline",
            "severity": "info",
            "description": "Data quality analysis using Qwen LLM",
            "timestamp": "$(date -Iseconds)",
            "analysis_context": "data-quality-assessment",
            "data_info": {
                "processing_type": "{{workflow.parameters.processing-type}}",
                "source": "{{workflow.parameters.data-source}}",
                "files": [f for f in os.listdir('/tmp/validated-data')]
            }
        }
        
        response = requests.post(
            "http://qwen-k8sgpt.argo-workflows.svc.cluster.local:8080/analyze",
            json=analysis_request,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Qwen Data Analysis Results:")
            print(json.dumps(result, indent=2))
            
            # Save analysis results
            with open('/tmp/analysis-results.json', 'w') as f:
                json.dump(result, f)
        else:
            print(f"Data analysis failed: {response.status_code}")
            exit(1)
    outputs:
      artifacts:
      - name: results
        path: /tmp/analysis-results.json
  
  - name: transform
    inputs:
      artifacts:
      - name: data
        path: /tmp/data
      - name: analysis-results
        path: /tmp/analysis-results.json
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import json
        import pandas as pd
        import os
        
        # Load analysis results
        with open('/tmp/analysis-results.json', 'r') as f:
            analysis = json.load(f)
        
        # Transform data based on analysis recommendations
        data_files = [f for f in os.listdir('/tmp/data') if f.endswith('.csv')]
        
        for file in data_files:
            df = pd.read_csv(f'/tmp/data/{file}')
            
            # Apply transformations based on Qwen recommendations
            if analysis.get('recommendations'):
                for rec in analysis['recommendations']:
                    if rec.get('type') == 'remove_duplicates':
                        df = df.drop_duplicates()
                    elif rec.get('type') == 'fill_nulls':
                        df = df.fillna(rec.get('value', 0))
                    elif rec.get('type') == 'convert_types':
                        for col, dtype in rec.get('columns', {}).items():
                            if col in df.columns:
                                df[col] = df[col].astype(dtype)
            
            # Save transformed data
            df.to_csv(f'/tmp/processed/{file}', index=False)
            print(f"Transformed {file}: {len(df)} rows")
        
        print("Data transformation completed")
    outputs:
      artifacts:
      - name: data
        path: /tmp/processed
  
  - name: load
    inputs:
      artifacts:
      - name: processed-data
        path: /tmp/processed-data
      parameters:
      - name: destination
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import boto3
        import os
        
        # Load processed data to destination
        s3 = boto3.client('s3', endpoint_url='http://minio:9000')
        
        for file in os.listdir('/tmp/processed-data'):
            if file.endswith('.csv'):
                s3.upload_file(
                    f'/tmp/processed-data/{file}',
                    'data-bucket',
                    f"output/{file}"
                )
                print(f"Loaded: {file}")
        
        print("Data loading completed")
```

## Monitoring and Debugging

### Workflow Monitoring

#### Real-time Monitoring

```bash
# Watch workflow status
kubectl get workflows -n argo-workflows -w

# Watch specific workflow
kubectl get workflow my-workflow -n argo-workflows -w

# Get workflow events
kubectl get events -n argo-workflows --field-selector involvedObject.kind=Workflow
```

#### Detailed Workflow Information

```bash
# Get workflow details
kubectl describe workflow my-workflow -n argo-workflows

# Get workflow YAML
kubectl get workflow my-workflow -n argo-workflows -o yaml

# Get workflow logs
kubectl logs -n argo-workflows -l workflow=my-workflow -c main

# Get specific step logs
kubectl logs -n argo-workflows my-workflow-<step-name> -c main
```

### Performance Monitoring

#### Resource Usage

```bash
# Get pod resource usage
kubectl top pods -n argo-workflows

# Get node resource usage
kubectl top nodes

# Get detailed metrics
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/namespaces/argo-workflows/pods"
```

#### Workflow Metrics

```bash
# Query Prometheus for workflow metrics
curl -s "http://localhost:9090/api/v1/query?query=argo_workflows_workflow_status_total" | jq

# Query Qwen metrics
curl -s "http://localhost:9090/api/v1/query?query=qwen_analysis_requests_total" | jq

# Query resource usage
curl -s "http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total" | jq
```

### Debugging Tools

#### Argo CLI

```bash
# Install Argo CLI
curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/argo-linux-amd64
chmod +x argo-linux-amd64
sudo mv argo-linux-amd64 /usr/local/bin/argo

# List workflows
argo list -n argo-workflows

# Get workflow details
argo get my-workflow -n argo-workflows

# Watch workflow logs
argo logs my-workflow -n argo-workflows --follow

# Submit workflow
argo submit -n argo-workflows my-workflow.yaml

# Delete workflow
argo delete my-workflow -n argo-workflows
```

#### Debug Workflows

```yaml
# Debug workflow with verbose logging
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: debug-workflow
  namespace: argo-workflows
spec:
  entrypoint: debug-steps
  templates:
  - name: debug-steps
    steps:
    - - name: step-1
        template: debug-step
        arguments:
          parameters:
          - name: step-name
            value: "step-1"
    - - name: step-2
        template: debug-step
        arguments:
          parameters:
          - name: step-name
            value: "step-2"
  
  - name: debug-step
    inputs:
      parameters:
      - name: step-name
    container:
      image: alpine:latest
      command: [sh, -c]
      args: |
        echo "=== Debug Information for {{inputs.parameters.step-name}} ==="
        echo "Timestamp: $(date)"
        echo "Pod Name: $(hostname)"
        echo "Namespace: $(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)"
        echo "Service Account: $(cat /var/run/secrets/kubernetes.io/serviceaccount/service-account)"
        echo "Environment Variables:"
        env | sort
        echo "Current Directory: $(pwd)"
        echo "Files in Current Directory:"
        ls -la
        echo "Memory Usage:"
        free -h
        echo "Disk Usage:"
        df -h
        echo "=== End Debug Info ==="
```

### Qwen LLM Debugging

#### Qwen Service Health

```bash
# Check Qwen service status
kubectl get deployment qwen-k8sgpt -n argo-workflows
kubectl get pods -l app=qwen-k8sgpt -n argo-workflows

# Check Qwen logs
kubectl logs -n argo-workflows deployment/qwen-k8sgpt --tail=100

# Test Qwen health endpoint
kubectl exec -n argo-workflows deployment/qwen-k8sgpt -- curl http://localhost:8080/health

# Test Qwen API
kubectl exec -n argo-workflows deployment/qwen-k8sgpt -- \
  curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","namespace":"argo-workflows","component":"debug"}'
```

#### Qwen Analysis Debugging

```bash
# Enable debug mode in Qwen
kubectl patch configmap qwen-k8sgpt-config -n argo-workflows --patch '{"data":{"LOG_LEVEL":"debug","QWEN_DEBUG_MODE":"true"}}'

# Restart Qwen service
kubectl rollout restart deployment/qwen-k8sgpt -n argo-workflows

# Monitor Qwen metrics
kubectl port-forward -n argo-workflows svc/qwen-k8sgpt 9090:9090 &
curl -s http://localhost:9090/metrics | grep qwen
```

## Best Practices

### Workflow Design Best Practices

#### 1. Resource Management

```yaml
# Always specify resource requests and limits
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

# Use appropriate resource limits based on workload
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

#### 2. Error Handling and Retries

```yaml
# Implement retry strategies
- name: retry-step
    container:
      image: python:3.9-alpine
      command: [python, -c]
      args: |
        import requests
        import time
        
        for attempt in range(3):
            try:
                response = requests.get("https://api.example.com/data", timeout=30)
                response.raise_for_status()
                print("Success!")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
```

#### 3. Timeout Management

```yaml
# Set appropriate timeouts
spec:
  activeDeadlineSeconds: 3600  # Workflow timeout
  templates:
  - name: timeout-step
    container:
      image: alpine:latest
      command: [timeout, 300s, sh, -c]
      args: |
        echo "Step with 5 minute timeout"
        sleep 600  # This will timeout after 5 minutes
```

#### 4. Artifact Management

```yaml
# Use artifacts for data passing
- name: data-processor
  inputs:
    artifacts:
    - name: input-data
      path: /tmp/input.json
      s3:
        key: input/{{workflow.uid}}.json
  outputs:
    artifacts:
    - name: output-data
      path: /tmp/output.json
      s3:
        key: output/{{workflow.uid}}.json
  container:
    image: python:3.9-alpine
    command: [python, process_data.py]
```

### Security Best Practices

#### 1. RBAC Configuration

```yaml
# Use least privilege principle
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: workflow-role
  namespace: argo-workflows
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["argoproj.io"]
  resources: ["workflows"]
  verbs: ["create", "get", "list", "watch"]
```

#### 2. Security Contexts

```yaml
# Use security contexts
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

#### 3. Secret Management

```yaml
# Use Kubernetes secrets
- name: secure-step
    container:
      image: alpine:latest
      env:
      - name: API_KEY
        valueFrom:
          secretKeyRef:
            name: api-secrets
            key: api-key
      - name: CONFIG_FILE
        valueFrom:
          configMapKeyRef:
            name: app-config
            key: config.yaml
```

### Performance Best Practices

#### 1. Parallel Execution

```yaml
# Use parallel steps for better performance
- name: parallel-steps
  steps:
  - - name: parallel-task-1
      template: task-template
    - name: parallel-task-2
      template: task-template
    - name: parallel-task-3
      template: task-template
```

#### 2. DAG for Complex Dependencies

```yaml
# Use DAG for complex workflow dependencies
- name: complex-workflow
  dag:
    tasks:
    - name: task-a
      template: task-template
    - name: task-b
      template: task-template
      dependencies: [task-a]
    - name: task-c
      template: task-template
      dependencies: [task-a]
    - name: task-d
      template: task-template
      dependencies: [task-b, task-c]
```

#### 3. Caching and Optimization

```yaml
# Use caching for expensive operations
- name: cached-operation
    container:
      image: alpine:latest
      command: [sh, -c]
      args: |
        # Check cache first
        if [ -f "/cache/result-{{inputs.parameters.cache-key}}" ]; then
          echo "Using cached result"
          cat "/cache/result-{{inputs.parameters.cache-key}}"
        else
          # Perform expensive operation
          echo "Performing expensive operation..."
          result=$(expensive_operation)
          echo "$result" > "/cache/result-{{inputs.parameters.cache-key}}"
          echo "$result"
        fi
    volumeMounts:
    - name: cache
      mountPath: /cache
```

### Qwen LLM Best Practices

#### 1. Analysis Request Optimization

```python
# Optimize Qwen analysis requests
def create_analysis_request(event_type, component, context):
    """Create optimized analysis request for Qwen"""
    return {
        "event_type": event_type,
        "namespace": "argo-workflows",
        "component": component,
        "severity": "info",
        "description": f"Analysis of {component}",
        "timestamp": datetime.now().isoformat(),
        "analysis_context": context,
        # Include only relevant data
        "relevant_data": get_relevant_data(component),
        # Optimize for LLM processing
        "max_tokens": 4096,
        "temperature": 0.7
    }
```

#### 2. Response Handling

```python
# Handle Qwen responses gracefully
def handle_qwen_response(response):
    """Handle Qwen LLM response with error handling"""
    try:
        if response.status_code == 200:
            result = response.json()
            
            # Validate response structure
            if 'analysis' in result:
                return result
            else:
                logger.warning("Unexpected response structure")
                return {"analysis": "Analysis completed but response format unexpected"}
        else:
            logger.error(f"Qwen API error: {response.status_code}")
            return {"error": f"API error: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error processing Qwen response: {e}")
        return {"error": f"Response processing error: {str(e)}"}
```

#### 3. Caching and Performance

```python
# Implement caching for Qwen analysis
class QwenAnalyzer:
    def __init__(self, cache_ttl=3600):
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def analyze(self, request):
        cache_key = self.generate_cache_key(request)
        
        # Check cache first
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        # Perform analysis
        result = self.call_qwen_api(request)
        
        # Cache result
        self.cache[cache_key] = (result, time.time())
        
        return result
```

## Troubleshooting

### Common Workflow Issues

#### 1. Workflows Stuck in Pending

**Symptoms**: Workflow stays in pending state

**Causes**:
- Controller not running
- RBAC permissions issue
- Resource constraints
- Image pull issues

**Solutions**:
```bash
# Check controller status
kubectl get deployment argo-workflows-controller -n argo-workflows
kubectl logs -n argo-workflows deployment/argo-workflows-controller

# Check RBAC
kubectl auth can-i create workflows -n argo-workflows

# Check events
kubectl get events -n argo-workflows --sort-by='.lastTimestamp'
```

#### 2. Workflows Failing with ImagePullBackOff

**Symptoms**: Pod fails with ImagePullBackOff

**Causes**:
- Invalid image name
- Private registry credentials
- Network connectivity
- Image not available

**Solutions**:
```bash
# Check pod status
kubectl describe pod <pod-name> -n argo-workflows

# Check image availability
kubectl run test-pod --image=<image-name> --rm -it --restart=Never

# Check image pull secrets
kubectl get secret <secret-name> -n argo-workflows -o yaml
```

#### 3. Workflows Running Slowly

**Symptoms**: Workflows taking longer than expected

**Causes**:
- Resource constraints
- Network latency
- Large data processing
- Inefficient workflow design

**Solutions**:
```bash
# Check resource usage
kubectl top pods -n argo-workflows

# Analyze workflow steps
kubectl describe workflow <workflow-name> -n argo-workflows

# Optimize workflow design
# - Use parallel execution
# - Increase resource limits
# - Optimize container images
```

### Qwen LLM Issues

#### 1. Qwen Service Not Responding

**Symptoms**: API calls to Qwen timeout or fail

**Causes**:
- Service not running
- Port forwarding issues
- Resource exhaustion
- Model loading issues

**Solutions**:
```bash
# Check service status
kubectl get deployment qwen-k8sgpt -n argo-workflows
kubectl get pods -l app=qwen-k8sgpt -n argo-workflows

# Check logs
kubectl logs -n argo-workflows deployment/qwen-k8sgpt

# Test connectivity
kubectl exec -n argo-workflows deployment/qwen-k8sgpt -- curl http://localhost:8080/health

# Check resources
kubectl top pods -l app=qwen-k8sgpt -n argo-workflows
```

#### 2. Qwen Analysis Quality Issues

**Symptoms**: Poor quality or irrelevant analysis results

**Causes**:
- Insufficient context
- Poor prompt engineering
- Model limitations
- Incomplete data

**Solutions**:
```yaml
# Improve analysis prompts
analysis-prompts.yaml: |
  enhanced_workflow_analysis: |
    You are an expert Kubernetes and Argo Workflows analyst.
    
    Analyze this workflow execution with focus on:
    1. Performance bottlenecks and optimization opportunities
    2. Resource utilization efficiency
    3. Security considerations
    4. Cost optimization recommendations
    5. Best practices compliance
    
    Workflow Details:
    - Name: {{.workflow_name}}
    - Status: {{.status}}
    - Duration: {{.duration}}
    - Steps: {{.steps}}
    - Resource Usage: {{.resource_usage}}
    - Errors: {{.errors}}
    
    Provide specific, actionable recommendations with implementation steps.
```

#### 3. Qwen Performance Issues

**Symptoms**: Slow response times or timeouts

**Causes**:
- Insufficient resources
- Model loading time
- Large input data
- Concurrent request overload

**Solutions**:
```yaml
# Increase Qwen resources
resources:
  requests:
    cpu: "2000m"
    memory: "4Gi"
  limits:
    cpu: "6000m"
    memory: "12Gi"

# Enable caching
env:
- name: QWEN_CACHE_ENABLED
  value: "true"
- name: QWEN_CACHE_TTL
  value: "3600"

# Optimize request size
env:
- name: QWEN_MAX_INPUT_SIZE
  value: "1000000"
```

### Monitoring Issues

#### 1. Metrics Not Available

**Symptoms**: No metrics in Prometheus or Grafana

**Causes**:
- ServiceMonitor not configured
- Metrics endpoint not exposed
- Network policies blocking access
- Prometheus not scraping

**Solutions**:
```bash
# Check ServiceMonitor
kubectl get servicemonitor -n argo-workflows

# Check metrics endpoint
kubectl port-forward -n argo-workflows svc/argo-workflows-controller 9090:9090 &
curl http://localhost:9090/metrics

# Check network policies
kubectl get networkpolicy -n argo-workflows

# Check Prometheus configuration
kubectl get prometheus -n monitoring -o yaml
```

#### 2. Grafana Dashboard Issues

**Symptoms**: Dashboards not showing data

**Causes**:
- Incorrect data source configuration
- Dashboard not imported
- Time range issues
- Metric name changes

**Solutions**:
```bash
# Check Grafana data source
kubectl get configmap grafana-datasources -n monitoring -o yaml

# Import dashboard
kubectl apply -f overlay/argo-workflows/monitoring/grafana-dashboard.yaml

# Check metric names
curl -s "http://localhost:9090/api/v1/label/__name__/values" | jq '.data[]'
```

### Advanced Troubleshooting

#### 1. Workflow Controller Debug Mode

```bash
# Enable debug logging
kubectl patch configmap workflow-controller-configmap -n argo-workflows --patch '{"data":{"LOG_LEVEL":"debug"}}'

# Restart controller
kubectl rollout restart deployment argo-workflows-controller -n argo-workflows

# Monitor debug logs
kubectl logs -n argo-workflows deployment/argo-workflows-controller --follow
```

#### 2. Qwen Model Debugging

```bash
# Check model loading
kubectl exec -n argo-workflows deployment/qwen-localai -- ls -la /models/

# Test model directly
kubectl exec -n argo-workflows deployment/qwen-localai -- \
  curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","prompt":"Hello","max_tokens":10}'

# Check model performance
kubectl exec -n argo-workflows deployment/qwen-localai -- \
  curl -s http://localhost:8080/v1/models | jq
```

#### 3. Network Connectivity Debugging

```bash
# Test service connectivity
kubectl run connectivity-test --rm -i --restart=Never --image=nicolaka/netshoot \
  --namespace=argo-workflows -- \
  nslookup qwen-k8sgpt.argo-workflows.svc.cluster.local

# Test port connectivity
kubectl run port-test --rm -i --restart=Never --image=alpine/netcat-openbsd \
  --namespace=argo-workflows -- \
  nc -zv qwen-k8sgpt.argo-workflows.svc.cluster.local 8080

# Check network policies
kubectl get networkpolicy -n argo-workflows -o yaml
```

---

This comprehensive user guide covers all aspects of using Argo Workflows with Qwen LLM integration. For more specific use cases and advanced configurations, refer to the main documentation and examples in the repository.
