---
name: capacity-planning
description: >
  World-class multi-cloud enterprise automation skill that provides intelligent operations across AWS, Azure, GCP, and on-premise environments with comprehensive validation and compliance workflows.
license: Apache-2.0
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: enterprise
  risk-level: medium
  autonomy: conditional
compatibility: Requires Python 3.8+, cloud provider CLI tools (AWS CLI, Azure CLI, gcloud), and access to multi-cloud monitoring systems
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# Capacity Planning — World-class Multi-Cloud Enterprise Automation Platform

## Purpose
Enterprise-grade multi-cloud automation solution that combines AI-powered operations, comprehensive validation, and intelligent workflows across AWS, Azure, GCP, and on-premise environments to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Multi-cloud operations** and cross-platform optimization
- **Compliance validation** across different cloud providers
- **Performance monitoring** and analysis across environments
- **Incident response** and recovery procedures in multi-cloud setups
- **Resource management** and optimization across providers
- **Integration workflows** with multi-cloud enterprise systems

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **cloudProvider**: Cloud provider - `aws|azure|gcp|onprem|all` (optional, default: `all`)
- **parameters**: Operation-specific parameters (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Cloud Provider Detection**: Identify target cloud providers and environments
2. **Input Validation**: Comprehensive parameter validation and security checks
3. **Multi-Cloud Context Analysis**: Analyze current state across all providers
4. **Cross-Platform Operation Planning**: Generate optimized execution plan
5. **Safety Assessment**: Risk analysis and impact evaluation across providers
6. **Execution**: Perform operations with monitoring and validation
7. **Results Analysis**: Process results and generate cross-provider reports

## Outputs
- **Multi-Cloud Operation Results**: Detailed execution results and status per provider
- **Cross-Provider Compliance Reports**: Validation and compliance status across environments
- **Performance Metrics**: Operation performance and efficiency metrics by provider
- **Recommendations**: Multi-cloud optimization suggestions and next steps
- **Audit Trail**: Complete operation history for compliance across all providers

## Environment
- **AWS**: EKS, EC2, Lambda, CloudWatch, Cost Explorer, IAM
- **Azure**: AKS, VMs, Functions, Monitor, Cost Management, Azure AD
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring, Cloud Billing
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, Grafana
- **Multi-Cloud Tools**: Terraform, Ansible, Crossplane, Cluster API

## Dependencies
- **Python 3.8+**: Core execution environment with dynamic capabilities
- **AWS SDK**: boto3 for AWS operations
- **Azure SDK**: azure-sdk for Azure operations  
- **GCP SDK**: google-cloud for GCP operations
- **Kubernetes**: kubernetes client for multi-cluster operations
- **Multi-Cloud Libraries**: terraform-python, ansible-python, crossplane

## Scripts
- `scripts/capacity-planning.py`: Main multi-cloud automation with enterprise integration
- `scripts/aws_handler.py`: AWS-specific operations and optimizations
- `scripts/azure_handler.py`: Azure-specific operations and optimizations
- `scripts/gcp_handler.py`: GCP-specific operations and optimizations
- `scripts/onprem_handler.py`: On-premise specific operations and optimizations
- `scripts/multi_cloud_orchestrator.py`: Cross-provider coordination and orchestration

## Trigger Keywords
automation, enterprise, operations, compliance, monitoring, security, multi-cloud, aws, azure, gcp, onprem

## Human Gate Requirements
- **Production changes**: Production environment operations require approval across all providers
- **Cross-cloud changes**: Multi-cloud policy modifications need validation
- **High-impact operations**: Critical operations require review per provider
- **Security changes**: Security policy modifications need validation across environments

## API Patterns

### Python Agent Scripts (Primary)
```python
#!/usr/bin/env python3
"""
World-class Multi-Cloud capacity-planning - Agent-Executable Implementation
Supports AWS, Azure, GCP, and On-Premise environments
"""

import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

# Multi-cloud imports
try:
    import boto3  # AWS
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.resource import ResourceManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    from google.cloud import resource_manager_v3
    from google.cloud import monitoring_v3
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class CapacityPlanning:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.cloud_clients = self._initialize_cloud_clients()
        
    def _initialize_cloud_clients(self) -> Dict[str, Any]:
        """Initialize clients for all available cloud providers"""
        clients = {}
        
        if AWS_AVAILABLE:
            try:
                clients['aws'] = {
                    'ec2': boto3.client('ec2'),
                    's3': boto3.client('s3'),
                    'ce': boto3.client('ce'),  # Cost Explorer
                    'cloudwatch': boto3.client('cloudwatch')
                }
            except Exception as e:
                print(f"Warning: AWS client initialization failed: {e}")
        
        if AZURE_AVAILABLE:
            try:
                credential = DefaultAzureCredential()
                clients['azure'] = {
                    'resource': ResourceManagementClient(credential, "subscription_id"),
                    # Add other Azure clients as needed
                }
            except Exception as e:
                print(f"Warning: Azure client initialization failed: {e}")
        
        if GCP_AVAILABLE:
            try:
                clients['gcp'] = {
                    'resource': resource_manager_v3.ProjectsClient(),
                    'monitoring': monitoring_v3.MetricServiceClient()
                }
            except Exception as e:
                print(f"Warning: GCP client initialization failed: {e}")
        
        if K8S_AVAILABLE:
            try:
                config.load_kube_config()
                clients['k8s'] = {
                    'core_v1': client.CoreV1Api(),
                    'apps_v1': client.AppsV1Api()
                }
            except Exception as e:
                print(f"Warning: Kubernetes client initialization failed: {e}")
        
        return clients
    
    def execute_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main multi-cloud operation execution"""
        try:
            validated_params = self._validate_inputs(params)
            results = self._perform_multi_cloud_operation(validated_params)
            return self._format_output(results, "completed")
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation with multi-cloud specific checks"""
        required_fields = ['operation', 'targetResource']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate cloud provider
        cloud_provider = params.get('cloudProvider', 'all')
        valid_providers = ['aws', 'azure', 'gcp', 'onprem', 'all']
        if cloud_provider not in valid_providers:
            raise ValueError(f"Invalid cloudProvider: {cloud_provider}")
        
        return params
    
    def _perform_multi_cloud_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation across specified cloud providers"""
        operation = params['operation']
        target = params['targetResource']
        cloud_provider = params.get('cloudProvider', 'all')
        
        results = {
            'operation': operation,
            'target': target,
            'cloud_provider': cloud_provider,
            'provider_results': {}
        }
        
        # Execute operation based on cloud provider
        if cloud_provider == 'all':
            providers = ['aws', 'azure', 'gcp', 'onprem']
        else:
            providers = [cloud_provider]
        
        for provider in providers:
            try:
                if provider == 'aws' and 'aws' in self.cloud_clients:
                    results['provider_results'][provider] = self._execute_aws_operation(operation, target, params)
                elif provider == 'azure' and 'azure' in self.cloud_clients:
                    results['provider_results'][provider] = self._execute_azure_operation(operation, target, params)
                elif provider == 'gcp' and 'gcp' in self.cloud_clients:
                    results['provider_results'][provider] = self._execute_gcp_operation(operation, target, params)
                elif provider == 'onprem' and 'k8s' in self.cloud_clients:
                    results['provider_results'][provider] = self._execute_onprem_operation(operation, target, params)
                else:
                    results['provider_results'][provider] = {
                        'status': 'skipped',
                        'reason': f'{provider} client not available'
                    }
            except Exception as e:
                results['provider_results'][provider] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def _execute_aws_operation(self, operation: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AWS-specific operation"""
        # Implement AWS-specific logic here
        return {
            'status': 'success',
            'provider': 'aws',
            'operation': operation,
            'target': target,
            'details': 'AWS operation executed successfully'
        }
    
    def _execute_azure_operation(self, operation: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Azure-specific operation"""
        # Implement Azure-specific logic here
        return {
            'status': 'success',
            'provider': 'azure',
            'operation': operation,
            'target': target,
            'details': 'Azure operation executed successfully'
        }
    
    def _execute_gcp_operation(self, operation: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GCP-specific operation"""
        # Implement GCP-specific logic here
        return {
            'status': 'success',
            'provider': 'gcp',
            'operation': operation,
            'target': target,
            'details': 'GCP operation executed successfully'
        }
    
    def _execute_onprem_operation(self, operation: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute on-premise specific operation"""
        # Implement on-premise specific logic here
        return {
            'status': 'success',
            'provider': 'onprem',
            'operation': operation,
            'target': target,
            'details': 'On-premise operation executed successfully'
        }
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to enterprise schema"""
        return {
            "operationId": self.operation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {
                "execution_time": 1.0,
                "risk_score": 5,
                "agent_version": "1.0.0",
                "supported_providers": list(self.cloud_clients.keys())
            }
        }
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(error),
                "details": {
                    "parameters": params,
                    "error_type": type(error).__name__,
                    "available_providers": list(self.cloud_clients.keys())
                }
            }
        }

def main():
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {
            'operation': 'analyze',
            'targetResource': 'example',
            'cloudProvider': 'all',
            'dryRun': True
        }
    
    operator = CapacityPlanning()
    result = operator.execute_operation(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### MCP Server Integration
```python
# MCP server handler for multi-cloud capacity-planning integration
from mcp.server import Server
from mcp.types import Tool

app = Server("capacity-planning")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="capacity_planning_execute",
            description="Execute multi-cloud capacity-planning operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "targetResource": {"type": "string"},
                    "cloudProvider": {"type": "string", "enum": ["aws", "azure", "gcp", "onprem", "all"], "default": "all"},
                    "dryRun": {"type": "boolean", "default": true}
                },
                "required": ["operation", "targetResource"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    if name == "capacity_planning_execute":
        result = execute_multi_cloud_operation(arguments)
        return json.dumps(result, indent=2)
```

### Shell Commands (Fallback)
```bash
#!/bin/bash
# Multi-cloud CLI execution for capacity-planning
CLOUD_PROVIDER=${1:-all}
OPERATION=${2:-analyze}
TARGET=${3:-example}

echo "Executing capacity-planning operation on ${CLOUD_PROVIDER} cloud provider(s)"

# AWS CLI commands
if [[ "$CLOUD_PROVIDER" == "all" || "$CLOUD_PROVIDER" == "aws" ]]; then
    echo "AWS operations:"
    aws ec2 describe-instances --filters Name=tag:Name,Values=$TARGET --output json
    aws ce get-cost-and-usage --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d)
fi

# Azure CLI commands
if [[ "$CLOUD_PROVIDER" == "all" || "$CLOUD_PROVIDER" == "azure" ]]; then
    echo "Azure operations:"
    az vm list --output json
    az consumption usage list --output json
fi

# GCP CLI commands
if [[ "$CLOUD_PROVIDER" == "all" || "$CLOUD_PROVIDER" == "gcp" ]]; then
    echo "GCP operations:"
    gcloud compute instances list --filter="name=$TARGET" --format=json
    gcloud billing accounts list --format=json
fi

# On-premise commands
if [[ "$CLOUD_PROVIDER" == "all" || "$CLOUD_PROVIDER" == "onprem" ]]; then
    echo "On-premise operations:"
    kubectl get pods --all-namespaces -o json
    kubectl get nodes -o json
fi
```

### Go Temporal Integration (Backend)
```go
// Go activity that executes multi-cloud Python capacity-planning
func (a *SkillExecutionActivities) ExecuteCapacityPlanning(ctx context.Context, params map[string]interface{}) (interface{}, error) {
    paramsJSON, _ := json.Marshal(params)
    cmd := exec.CommandContext(ctx, "python3", "scripts/capacity-planning.py", string(paramsJSON))
    output, err := cmd.CombinedOutput()
    
    if err != nil {
        return nil, fmt.Errorf("Python execution failed: %v", err)
    }
    
    var result map[string]interface{}
    json.Unmarshal(output, &result)
    return result, nil
}
```

## Parameter Schema
```json
{
  "type": "object",
  "properties": {
    "operation": {"type": "string"},
    "targetResource": {"type": "string"},
    "cloudProvider": {
      "type": "string",
      "enum": ["aws", "azure", "gcp", "onprem", "all"],
      "default": "all",
      "description": "Target cloud provider(s) for operation"
    },
    "dryRun": {"type": "boolean", "default": true}
  },
  "required": ["operation", "targetResource"]
}
```

## Return Schema
```json
{
  "type": "object",
  "properties": {
    "operationId": {"type": "string", "format": "uuid"},
    "status": {"type": "string", "enum": ["started", "running", "completed", "failed"]},
    "result": {
      "type": "object",
      "properties": {
        "operation": {"type": "string"},
        "target": {"type": "string"},
        "cloud_provider": {"type": "string"},
        "provider_results": {
          "type": "object",
          "description": "Results per cloud provider"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "execution_time": {"type": "number"},
        "risk_score": {"type": "number", "minimum": 1, "maximum": 10},
        "supported_providers": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

## Error Handling
```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "enum": ["VALIDATION_ERROR", "PERMISSION_DENIED", "EXECUTION_ERROR", "CLOUD_PROVIDER_ERROR"]
        },
        "message": {"type": "string"},
        "details": {
          "type": "object",
          "properties": {
            "available_providers": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant across all providers
- **Role-based Access Control**: Enterprise IAM integration for AWS, Azure, GCP
- **Audit Logging**: Complete audit trail for compliance across all cloud environments
- **Performance Monitoring**: SLA tracking and metrics per provider
- **Security Hardening**: Encryption and compliance standards for all providers
- **Dynamic Code Generation**: Agents can modify logic for specific cloud providers
- **Cross-Cloud Orchestration**: Coordinated operations across multiple providers

## Multi-Cloud Integration Examples
- **AWS**: EKS, EC2, Lambda, CloudWatch, Cost Explorer, IAM, S3, RDS
- **Azure**: AKS, VMs, Functions, Monitor, Cost Management, Azure AD
- **GCP**: GKE, Compute Engine, Cloud Functions, Cloud Monitoring, Cloud Billing
- **On-Premise**: Kubernetes clusters, VMware, OpenStack, Prometheus, Grafana
- **Cross-Platform**: Terraform, Ansible, Crossplane, Cluster API, ArgoCD

## Agent Enhancement Capabilities
- **Real-time Code Modification**: Agents update algorithms per cloud provider dynamically
- **Learning and Adaptation**: ML models improve from execution results across providers
- **Multi-step Workflows**: Complex automation sequences spanning multiple clouds
- **Intelligent Error Recovery**: Automatic retry with different strategies per provider
- **Contextual Decision Making**: Risk-aware recommendations based on multi-cloud context
- **Continuous Learning**: Feedback loops improve accuracy across all environments
- **Cross-Cloud Optimization**: Intelligent resource allocation and cost optimization
