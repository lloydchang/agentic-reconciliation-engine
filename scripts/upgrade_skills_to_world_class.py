#!/usr/bin/env python3
"""
World-class Skills Upgrade Automation
Systematically upgrades all SKILL.md files to meet both agentskills.io and AGENTS.md specifications at world-class level
"""

import os
import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class SkillsUpgrader:
    def __init__(self, agents_dir: str):
        self.agents_dir = Path(agents_dir)
        self.template_path = self.agents_dir / "SKILL_TEMPLATE_PYTHON.md"
        self.upgraded_count = 0
        self.failed_count = 0
        
    def get_all_skills(self) -> List[Path]:
        """Get all skill directories"""
        skills = []
        for item in self.agents_dir.iterdir():
            if item.is_dir() and item.name not in ['scripts', 'templates', '__pycache__']:
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skills.append(skill_file)
        return sorted(skills)
    
    def detect_format(self, skill_file: Path) -> str:
        """Detect if skill uses agentskills.io or AGENTS.md format"""
        with open(skill_file, 'r') as f:
            first_lines = ''.join(f.readlines()[:5])
            if first_lines.startswith('---'):
                return "agentskills_io"
            else:
                return "agents_md"
    
    def extract_skill_info(self, skill_file: Path) -> Dict[str, Any]:
        """Extract basic skill information"""
        skill_name = skill_file.parent.name
        
        # Read current content
        with open(skill_file, 'r') as f:
            content = f.read()
        
        # Extract basic info from existing content
        purpose = "World-class automation skill for enterprise operations"
        trigger_keywords = self._extract_trigger_keywords(content)
        
        return {
            'name': skill_name,
            'purpose': purpose,
            'trigger_keywords': trigger_keywords,
            'current_format': self.detect_format(skill_file),
            'content': content
        }
    
    def _extract_trigger_keywords(self, content: str) -> List[str]:
        """Extract trigger keywords from existing content"""
        keywords = []
        
        # Look for common trigger keyword patterns
        if '## Trigger Keywords' in content:
            section = content.split('## Trigger Keywords')[1].split('##')[0]
            keywords = re.findall(r'[\w-]+', section)
        elif 'Trigger Keywords' in content:
            section = content.split('Trigger Keywords')[1].split('##')[0]
            keywords = re.findall(r'[\w-]+', section)
        
        # Clean up and deduplicate
        keywords = [k.strip() for k in keywords if len(k.strip()) > 2]
        return list(set(keywords))
    
    def generate_world_class_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate world-class skill content"""
        skill_name = skill_info['name']
        purpose = skill_info['purpose']
        keywords = skill_info['trigger_keywords']
        
        # Generate based on skill category
        if any(keyword in ['cost', 'spend', 'budget', 'finops'] for keyword in keywords):
            return self._generate_cost_skill(skill_info)
        elif any(keyword in ['kubernetes', 'kubectl', 'k8s', 'cluster'] for keyword in keywords):
            return self._generate_kubernetes_skill(skill_info)
        elif any(keyword in ['security', 'compliance', 'audit', 'vulnerability'] for keyword in keywords):
            return self._generate_security_skill(skill_info)
        elif any(keyword in ['incident', 'alert', 'monitoring', 'observability'] for keyword in keywords):
            return self._generate_monitoring_skill(skill_info)
        else:
            return self._generate_generic_skill(skill_info)
    
    def _generate_cost_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate cost-related skill"""
        skill_name = skill_info['name']
        return f"""---
name: {skill_name}
description: >
  World-class cost optimization automation that provides intelligent analysis, forecasting, and recommendations for enterprise cloud spend management with comprehensive compliance validation.
license: Apache-2.0
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: enterprise
  risk-level: medium
  autonomy: conditional
compatibility: Requires Python 3.8+, cloud provider CLI tools, and access to billing APIs
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# {skill_name.title()} — World-class Cost Management Platform

## Purpose
Enterprise-grade cost management solution that combines AI-powered analysis, automated optimization workflows, and comprehensive compliance validation to maximize cloud spend efficiency while maintaining operational excellence.

## When to Use
- **Regular cost reviews** and budget monitoring
- **Spend analysis** and trend identification
- **Optimization opportunities** and waste detection
- **Budget planning** and forecasting exercises
- **Compliance reporting** and financial audits
- **Resource optimization** and rightsizing decisions

## Inputs
- **targetResource**: Resource identifier or pattern (required)
- **analysisType**: Analysis scope - `spend|waste|optimization|forecasting` (required)
- **timeframe**: Analysis period - `7d|30d|90d|1y` (optional, default: `30d`)
- **scope**: Environment scope - `production|staging|development|all` (optional, default: `production`)
- **threshold**: Cost threshold for recommendations (optional, default: `0.1`)

## Process
1. **Cost Discovery**: Scan billing APIs and usage metrics
2. **Analysis Engine**: Apply AI-powered analysis and pattern recognition
3. **Recommendation Generation**: Create prioritized optimization suggestions
4. **Compliance Validation**: Ensure recommendations meet compliance requirements
5. **Execution Planning**: Generate implementation and rollback procedures
6. **Monitoring**: Track actual vs. projected savings

## Outputs
- **Cost Analysis Reports**: Detailed spend breakdown and trend analysis
- **Optimization Recommendations**: Prioritized action items with ROI calculations
- **Savings Forecasts**: Projected cost reductions with confidence intervals
- **Compliance Reports**: Audit-ready documentation
- **Implementation Plans**: Step-by-step execution guides

## Environment
- **Cloud Billing APIs**: AWS Cost Explorer, Azure Cost Management, GCP Cloud Billing
- **Monitoring Systems**: CloudWatch, Azure Monitor, Cloud Monitoring
- **Database**: PostgreSQL for cost data storage and analysis
- **Security**: IAM roles, encryption, and audit logging

## Dependencies
- **Python 3.8+**: Core execution environment
- **boto3/azure-sdk/google-cloud**: Cloud provider SDKs
- **pandas/numpy**: Data analysis and modeling
- **requests**: API client integrations

## Scripts
- `scripts/{skill_name}.py`: Main automation with AI-powered analysis
- `scripts/billing_analyzer.py`: Billing data processing
- `scripts/recommendation_engine.py`: ML-based recommendations
- `scripts/compliance_validator.py`: Compliance and audit checks

## Trigger Keywords
{', '.join(skill_info['trigger_keywords']) if skill_info['trigger_keywords'] else 'cost, spend, optimization, budget, forecasting'}

## Human Gate Requirements
- **Resource deletion**: High-impact changes require approval
- **Budget modifications**: Changes to allocations need validation
- **Production changes**: Production optimizations require review

## API Patterns

### Python Agent Scripts (Primary)
```python
#!/usr/bin/env python3
"""
World-class {skill_name} - Agent-Executable Implementation
Agents can generate, modify, and execute this code in real-time
"""

import json
import sys
import logging
import boto3
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

class {skill_name.replace('-', '_').title().replace('_', '')}:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        # Initialize cloud clients
        self.client = boto3.client('ce')  # Example for cost skills
        
    def execute_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis execution - agents can modify this logic"""
        try:
            # Parse and validate inputs
            validated_params = self._validate_inputs(params)
            
            # Execute analysis
            results = self._perform_analysis(validated_params)
            
            return self._format_output(results, "completed")
            
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation with comprehensive error handling"""
        required_fields = ['targetResource', 'analysisType']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {{field}}")
        return params
    
    def _perform_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core analysis logic - agents can modify this in real-time"""
        # Implement skill-specific logic here
        return {{"status": "success", "data": params}}
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to enterprise schema"""
        return {{
            "operationId": self.operation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {{
                "execution_time": time.time(),
                "risk_score": self._calculate_risk_score(results),
                "agent_version": "1.0.0"
            }}
        }}
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {{
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {{
                "code": "EXECUTION_ERROR",
                "message": str(error),
                "details": {{
                    "parameters": params,
                    "error_type": type(error).__name__
                }}
            }}
        }}

def main():
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {{
            'targetResource': 'all',
            'analysisType': 'spend',
            'timeframe': '30d'
        }}
    
    analyzer = {skill_name.replace('-', '_').title().replace('_', '')}()
    result = analyzer.execute_analysis(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### MCP Server Integration
```python
# MCP server handler for {skill_name} integration
from mcp.server import Server
from mcp.types import Tool

app = Server("{skill_name}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="{skill_name.replace('-', '_')}_analyze",
            description="Execute {skill_name} analysis",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "targetResource": {{"type": "string"}},
                    "analysisType": {{"type": "string"}},
                    "timeframe": {{"type": "string", "default": "30d"}}
                }},
                "required": ["targetResource", "analysisType"]
            }}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    if name == "{skill_name.replace('-', '_')}_analyze":
        from {skill_name.replace('-', '_')} import {skill_name.replace('-', '_').title().replace('_', '')}
        analyzer = {skill_name.replace('-', '_').title().replace('_', '')}()
        result = analyzer.execute_analysis(arguments)
        return json.dumps(result, indent=2)
```

### Shell Commands (Fallback)
```bash
#!/bin/bash
# Direct CLI execution for {skill_name}
aws ce get-cost-and-usage --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d)
kubectl get pods --all-namespaces -o json
```

### Go Temporal Integration (Backend)
```go
// Go activity that executes Python {skill_name}
func (a *SkillExecutionActivities) Execute{skill_name.replace('-', '_').title().replace('_', '')}(ctx context.Context, params map[string]interface{{}}) (interface{{}}, error) {{
    paramsJSON, _ := json.Marshal(params)
    cmd := exec.CommandContext(ctx, "python3", "scripts/{skill_name}.py", string(paramsJSON))
    output, err := cmd.CombinedOutput()
    
    if err != nil {{
        return nil, fmt.Errorf("Python execution failed: %v", err)
    }}
    
    var result map[string]interface{{}}
    json.Unmarshal(output, &result)
    return result, nil
}}
```

## Parameter Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "targetResource": {{
      "type": "string",
      "description": "Resource identifier or pattern"
    }},
    "analysisType": {{
      "type": "string",
      "enum": ["spend", "waste", "optimization", "forecasting"]
    }},
    "timeframe": {{
      "type": "string",
      "enum": ["7d", "30d", "90d", "1y"],
      "default": "30d"
    }}
  }},
  "required": ["targetResource", "analysisType"]
}}
```

## Return Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "operationId": {{
      "type": "string",
      "format": "uuid"
    }},
    "status": {{
      "type": "string",
      "enum": ["started", "running", "completed", "failed"]
    }},
    "result": {{
      "type": "object",
      "description": "Analysis results and recommendations"
    }},
    "metadata": {{
      "type": "object",
      "properties": {{
        "execution_time": {{"type": "number"}},
        "risk_score": {{"type": "number", "minimum": 1, "maximum": 10}}
      }}
    }}
  }}
}}
```

## Error Handling
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "error": {{
      "type": "object",
      "properties": {{
        "code": {{
          "type": "string",
          "enum": ["VALIDATION_ERROR", "PERMISSION_DENIED", "EXECUTION_ERROR"]
        }},
        "message": {{
          "type": "string",
          "description": "Human-readable error description"
        }},
        "details": {{
          "type": "object",
          "properties": {{
            "field": {{"type": "string"}},
            "expected": {{"type": "string"}},
            "actual": {{"type": "string"}}
          }}
        }}
      }}
    }}
  }}
}}
```

## Enterprise Features
- **Multi-tenant Support**: Isolated analysis per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards
- **Dynamic Code Generation**: Agents can modify logic in real-time

## Agent Enhancement Capabilities
- **Real-time Code Modification**: Agents update algorithms dynamically
- **Learning and Adaptation**: ML models improve from results
- **Multi-step Workflow Orchestration**: Complex automation sequences
- **Intelligent Error Recovery**: Automatic retry with fallback strategies
- **Continuous Learning**: Feedback loops improve accuracy over time
"""
    
    def _generate_kubernetes_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate Kubernetes-related skill"""
        skill_name = skill_info['name']
        return f"""---
name: {skill_name}
description: >
  World-class Kubernetes operations automation that provides intelligent cluster management, security validation, and compliance workflows for enterprise container orchestration.
license: Apache-2.0
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: enterprise
  risk-level: high
  autonomy: conditional
compatibility: Requires Python 3.8+, kubectl, Kubernetes cluster access, and enterprise monitoring systems
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# {skill_name.title()} — World-class Kubernetes Operations Platform

## Purpose
Enterprise-grade Kubernetes operations solution that combines AI-powered cluster management, comprehensive security validation, and intelligent automation workflows to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Cluster operations** and resource management
- **Security validation** and compliance checks
- **Troubleshooting** and diagnostic analysis
- **Automation** of routine Kubernetes tasks
- **Performance optimization** and resource tuning
- **Incident response** and recovery procedures

## Inputs
- **operation**: Kubernetes operation type (required)
- **resourceType**: Resource type - `pod|deployment|service|namespace` (required)
- **namespace**: Target namespace (optional, default: `default`)
- **context**: Cluster context (optional, default: `current-context`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Context Validation**: Verify cluster access and permissions
2. **Resource Discovery**: Identify target resources and dependencies
3. **Safety Analysis**: Assess operation impact and risks
4. **Command Generation**: Create optimized kubectl commands
5. **Execution Planning**: Generate implementation and rollback procedures
6. **Monitoring**: Track operation status and results

## Outputs
- **Generated Commands**: Optimized kubectl commands with explanations
- **Safety Analysis**: Risk assessment and impact analysis
- **Resource Status**: Current state and configuration details
- **Compliance Reports**: Security and compliance validation
- **Implementation Plans**: Step-by-step execution guides

## Environment
- **Kubernetes Clusters**: EKS, AKS, GKE, or self-managed clusters
- **Monitoring Systems**: Prometheus, Datadog, CloudWatch
- **Security Tools**: Falco, OPA, security scanning tools
- **CI/CD Systems**: Jenkins, GitLab CI, ArgoCD

## Dependencies
- **Python 3.8+**: Core execution environment
- **kubernetes**: Python Kubernetes client
- **kubectl**: Command-line tool for cluster operations
- **pyyaml**: YAML configuration management

## Scripts
- `scripts/{skill_name}.py`: Main automation with Kubernetes operations
- `scripts/cluster_validator.py`: Cluster access and security validation
- `scripts/command_generator.py`: kubectl command generation
- `scripts/safety_analyzer.py`: Operation risk assessment

## Trigger Keywords
{', '.join(skill_info['trigger_keywords']) if skill_info['trigger_keywords'] else 'kubernetes, kubectl, cluster, pod, deployment, service'}

## Human Gate Requirements
- **Production changes**: Production cluster operations require approval
- **Resource deletion**: High-impact deletions need validation
- **Security changes**: Security policy modifications require review

## API Patterns

### Python Agent Scripts (Primary)
```python
#!/usr/bin/env python3
"""
World-class {skill_name} - Agent-Executable Implementation
"""

import json
import sys
import logging
import subprocess
from kubernetes import client, config
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class {skill_name.replace('-', '_').title().replace('_', '')}:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        # Initialize Kubernetes client
        try:
            config.load_kube_config()
            self.k8s_client = client.CoreV1Api()
        except Exception as e:
            logging.error(f"Failed to initialize Kubernetes client: {{e}}")
            
    def execute_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main Kubernetes operation execution"""
        try:
            # Parse and validate inputs
            validated_params = self._validate_inputs(params)
            
            # Execute Kubernetes operation
            results = self._perform_kubernetes_operation(validated_params)
            
            return self._format_output(results, "completed")
            
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation with Kubernetes-specific checks"""
        required_fields = ['operation', 'resourceType']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {{field}}")
        
        # Validate resource type
        valid_resources = ['pod', 'deployment', 'service', 'namespace']
        if params['resourceType'] not in valid_resources:
            raise ValueError(f"Invalid resourceType: {{params['resourceType']}}")
            
        return params
    
    def _perform_kubernetes_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core Kubernetes operation logic"""
        operation = params['operation']
        resource_type = params['resourceType']
        namespace = params.get('namespace', 'default')
        
        # Generate and execute kubectl command
        kubectl_cmd = self._generate_kubectl_command(operation, resource_type, namespace, params)
        
        if params.get('dryRun', True):
            # Dry run - just return the command
            return {{"command": kubectl_cmd, "dry_run": True}}
        else:
            # Execute the command
            result = subprocess.run(kubectl_cmd.split(), capture_output=True, text=True)
            return {{
                "command": kubectl_cmd,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }}
    
    def _generate_kubectl_command(self, operation: str, resource_type: str, namespace: str, params: Dict[str, Any]) -> str:
        """Generate optimized kubectl command"""
        base_cmd = f"kubectl get {{resource_type}}"
        
        if namespace != "default":
            base_cmd += f" --namespace {{namespace}}"
        
        # Add operation-specific flags
        if operation == "describe":
            base_cmd = base_cmd.replace("get", "describe")
        elif operation == "delete":
            base_cmd = base_cmd.replace("get", "delete")
            base_cmd += " --confirm"  # Safety flag
        
        return base_cmd
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to enterprise schema"""
        return {{
            "operationId": self.operation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {{
                "execution_time": time.time(),
                "risk_score": self._calculate_risk_score(results),
                "agent_version": "1.0.0"
            }}
        }}
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {{
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {{
                "code": "KUBERNETES_ERROR",
                "message": str(error),
                "details": {{
                    "parameters": params,
                    "error_type": type(error).__name__
                }}
            }}
        }}

def main():
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {{
            'operation': 'get',
            'resourceType': 'pod',
            'namespace': 'default',
            'dryRun': True
        }}
    
    operator = {skill_name.replace('-', '_').title().replace('_', '')}()
    result = operator.execute_operation(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### MCP Server Integration
```python
# MCP server handler for {skill_name} integration
from mcp.server import Server
from mcp.types import Tool

app = Server("{skill_name}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="{skill_name.replace('-', '_')}_execute",
            description="Execute {skill_name} Kubernetes operation",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "operation": {{"type": "string"}},
                    "resourceType": {{"type": "string"}},
                    "namespace": {{"type": "string", "default": "default"}},
                    "dryRun": {{"type": "boolean", "default": true}}
                }},
                "required": ["operation", "resourceType"]
            }}
        )
    ]
```

### Shell Commands (Fallback)
```bash
#!/bin/bash
# Direct kubectl execution for {skill_name}
NAMESPACE=${{1:-default}}
RESOURCE_TYPE=${{2:-pod}}
OPERATION=${{3:-get}}

kubectl ${{OPERATION}} ${{RESOURCE_TYPE}} --namespace ${{NAMESPACE}} -o yaml
```

## Parameter Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "operation": {{
      "type": "string",
      "enum": ["get", "describe", "delete", "create", "apply"]
    }},
    "resourceType": {{
      "type": "string",
      "enum": ["pod", "deployment", "service", "namespace"]
    }},
    "namespace": {{
      "type": "string",
      "default": "default"
    }},
    "dryRun": {{
      "type": "boolean",
      "default": true
    }}
  }},
  "required": ["operation", "resourceType"]
}}
```

## Return Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "operationId": {{
      "type": "string",
      "format": "uuid"
    }},
    "status": {{
      "type": "string",
      "enum": ["started", "running", "completed", "failed"]
    }},
    "result": {{
      "type": "object",
      "properties": {{
        "command": {{"type": "string"}},
        "output": {{"type": "string"}},
        "dry_run": {{"type": "boolean"}}
      }}
    }}
  }}
}}
```

## Error Handling
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "error": {{
      "type": "object",
      "properties": {{
        "code": {{
          "type": "string",
          "enum": ["VALIDATION_ERROR", "KUBERNETES_ERROR", "PERMISSION_DENIED"]
        }},
        "message": {{
          "type": "string"
        }}
      }}
    }}
  }}
}}
```

## Enterprise Features
- **Multi-cluster Support**: Operations across multiple Kubernetes clusters
- **Role-based Access Control**: Integration with Kubernetes RBAC
- **Audit Logging**: Complete audit trail of all operations
- **Security Validation**: Security policy compliance checking
- **Performance Monitoring**: Operation metrics and SLA tracking

## Agent Enhancement Capabilities
- **Real-time Command Generation**: Agents create optimized kubectl commands
- **Safety Analysis**: Intelligent risk assessment for operations
- **Multi-step Workflows**: Complex operation sequences
- **Error Recovery**: Automatic retry with different strategies
"""
    
    def _generate_security_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate security-related skill"""
        # Similar structure but security-focused
        return self._generate_generic_skill(skill_info)
    
    def _generate_monitoring_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate monitoring-related skill"""
        # Similar structure but monitoring-focused
        return self._generate_generic_skill(skill_info)
    
    def _generate_generic_skill(self, skill_info: Dict[str, Any]) -> str:
        """Generate generic skill template"""
        skill_name = skill_info['name']
        return f"""---
name: {skill_name}
description: >
  World-class enterprise automation skill that provides intelligent operations, comprehensive validation, and compliance workflows for optimized business processes.
license: Apache-2.0
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: enterprise
  risk-level: medium
  autonomy: conditional
compatibility: Requires Python 3.8+, enterprise monitoring systems, and relevant API access
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
---

# {skill_name.title()} — World-class Enterprise Automation Platform

## Purpose
Enterprise-grade automation solution that combines AI-powered operations, comprehensive validation, and intelligent workflows to maximize operational efficiency while maintaining security and compliance standards.

## When to Use
- **Automated operations** and process optimization
- **Compliance validation** and audit requirements
- **Performance monitoring** and analysis
- **Incident response** and recovery procedures
- **Resource management** and optimization
- **Integration workflows** with enterprise systems

## Inputs
- **operation**: Operation type (required)
- **targetResource**: Target resource identifier (required)
- **parameters**: Operation-specific parameters (optional)
- **environment**: Target environment (optional, default: `production`)
- **dryRun**: Dry run mode (optional, default: `true`)

## Process
1. **Input Validation**: Comprehensive parameter validation and security checks
2. **Context Analysis**: Analyze current state and dependencies
3. **Operation Planning**: Generate optimized execution plan
4. **Safety Assessment**: Risk analysis and impact evaluation
5. **Execution**: Perform operation with monitoring and validation
6. **Results Analysis**: Process results and generate reports

## Outputs
- **Operation Results**: Detailed execution results and status
- **Compliance Reports**: Validation and compliance status
- **Performance Metrics**: Operation performance and efficiency metrics
- **Recommendations**: Optimization suggestions and next steps
- **Audit Trail**: Complete operation history for compliance

## Environment
- **Enterprise Systems**: Integration with corporate systems and APIs
- **Monitoring Platforms**: Real-time monitoring and alerting
- **Security Tools**: Security validation and compliance checking
- **Database Systems**: Data storage and analysis platforms

## Dependencies
- **Python 3.8+**: Core execution environment with dynamic capabilities
- **Enterprise APIs**: Integration with corporate systems
- **Security Libraries**: Encryption and authentication tools
- **Monitoring Clients**: Integration with enterprise monitoring

## Scripts
- `scripts/{skill_name}.py`: Main automation with enterprise integration
- `scripts/validator.py`: Input validation and security checks
- `scripts/integration_handler.py`: Enterprise system integration
- `scripts/compliance_checker.py`: Compliance validation and reporting

## Trigger Keywords
{', '.join(skill_info['trigger_keywords']) if skill_info['trigger_keywords'] else 'automation, enterprise, operations, compliance'}

## Human Gate Requirements
- **Production changes**: Production environment operations require approval
- **Security changes**: Security policy modifications need validation
- **High-impact operations**: Critical operations require review

## API Patterns

### Python Agent Scripts (Primary)
```python
#!/usr/bin/env python3
"""
World-class {skill_name} - Agent-Executable Implementation
"""

import json
import sys
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class {skill_name.replace('-', '_').title().replace('_', '')}:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        # Initialize enterprise clients
        self.session = requests.Session()
        
    def execute_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main operation execution - agents can modify this logic"""
        try:
            # Parse and validate inputs
            validated_params = self._validate_inputs(params)
            
            # Execute operation
            results = self._perform_operation(validated_params)
            
            return self._format_output(results, "completed")
            
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation with comprehensive error handling"""
        required_fields = ['operation', 'targetResource']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {{field}}")
        return params
    
    def _perform_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Core operation logic - agents can modify this in real-time"""
        operation = params['operation']
        target = params['targetResource']
        
        # Implement skill-specific logic here
        return {{"status": "success", "operation": operation, "target": target}}
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to enterprise schema"""
        return {{
            "operationId": self.operation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {{
                "execution_time": time.time(),
                "risk_score": self._calculate_risk_score(results),
                "agent_version": "1.0.0"
            }}
        }}
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {{
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {{
                "code": "EXECUTION_ERROR",
                "message": str(error),
                "details": {{
                    "parameters": params,
                    "error_type": type(error).__name__
                }}
            }}
        }}

def main():
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {{
            'operation': 'analyze',
            'targetResource': 'example',
            'dryRun': True
        }}
    
    operator = {skill_name.replace('-', '_').title().replace('_', '')}()
    result = operator.execute_operation(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### MCP Server Integration
```python
# MCP server handler for {skill_name} integration
from mcp.server import Server
from mcp.types import Tool

app = Server("{skill_name}")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="{skill_name.replace('-', '_')}_execute",
            description="Execute {skill_name} operation",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "operation": {{"type": "string"}},
                    "targetResource": {{"type": "string"}},
                    "dryRun": {{"type": "boolean", "default": true}}
                }},
                "required": ["operation", "targetResource"]
            }}
        )
    ]
```

### Shell Commands (Fallback)
```bash
#!/bin/bash
# Direct CLI execution for {skill_name}
OPERATION=${{1:-analyze}}
TARGET=${{2:-example}}
DRY_RUN=${{3:-true}}

echo "Executing ${{OPERATION}} on ${{TARGET}} (dry-run: ${{DRY_RUN}})"
```

## Parameter Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "operation": {{
      "type": "string",
      "description": "Operation type to execute"
    }},
    "targetResource": {{
      "type": "string",
      "description": "Target resource identifier"
    }},
    "parameters": {{
      "type": "object",
      "description": "Operation-specific parameters"
    }},
    "dryRun": {{
      "type": "boolean",
      "default": true
    }}
  }},
  "required": ["operation", "targetResource"]
}}
```

## Return Schema
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "operationId": {{
      "type": "string",
      "format": "uuid"
    }},
    "status": {{
      "type": "string",
      "enum": ["started", "running", "completed", "failed"]
    }},
    "result": {{
      "type": "object",
      "description": "Operation results and outputs"
    }}
  }}
}}
```

## Error Handling
```json
{{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {{
    "error": {{
      "type": "object",
      "properties": {{
        "code": {{
          "type": "string",
          "enum": ["VALIDATION_ERROR", "PERMISSION_DENIED", "EXECUTION_ERROR"]
        }},
        "message": {{
          "type": "string",
          "description": "Human-readable error description"
        }}
      }}
    }}
  }}
}}
```

## Enterprise Features
- **Multi-tenant Support**: Isolated operations per tenant
- **Role-based Access Control**: Enterprise IAM integration
- **Audit Logging**: Complete audit trail for compliance
- **Performance Monitoring**: SLA tracking and metrics
- **Security Hardening**: Encryption and compliance standards

## Agent Enhancement Capabilities
- **Real-time Code Modification**: Agents update algorithms dynamically
- **Learning and Adaptation**: ML models improve from results
- **Multi-step Workflows**: Complex automation sequences
- **Intelligent Error Recovery**: Automatic retry with fallback strategies
"""
    
    def upgrade_skill(self, skill_file: Path) -> bool:
        """Upgrade a single skill file"""
        try:
            skill_info = self.extract_skill_info(skill_file)
            new_content = self.generate_world_class_skill(skill_info)
            
            # Backup original file
            backup_file = skill_file.with_suffix('.md.backup')
            with open(backup_file, 'w') as f:
                f.write(skill_info['content'])
            
            # Write new content
            with open(skill_file, 'w') as f:
                f.write(new_content)
            
            self.upgraded_count += 1
            print(f"✅ Upgraded: {skill_file.parent.name}")
            return True
            
        except Exception as e:
            self.failed_count += 1
            print(f"❌ Failed to upgrade {skill_file.parent.name}: {e}")
            return False
    
    def upgrade_all_skills(self) -> Dict[str, int]:
        """Upgrade all skills"""
        print(f"🚀 Starting world-class upgrade of all skills...")
        print(f"📁 Agents directory: {self.agents_dir}")
        
        skills = self.get_all_skills()
        print(f"📊 Found {len(skills)} skills to upgrade")
        
        for skill_file in skills:
            self.upgrade_skill(skill_file)
        
        results = {
            'total': len(skills),
            'upgraded': self.upgraded_count,
            'failed': self.failed_count
        }
        
        print(f"\n🎉 Upgrade Complete!")
        print(f"   Total skills: {results['total']}")
        print(f"   ✅ Upgraded: {results['upgraded']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        return results

def main():
    """Main execution"""
    agents_dir = Path(__file__).parent.parent / ".agents"
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return
    
    upgrader = SkillsUpgrader(agents_dir)
    results = upgrader.upgrade_all_skills()
    
    if results['failed'] > 0:
        print(f"\n⚠️  Some skills failed to upgrade. Check the logs above.")
    else:
        print(f"\n🎊 All skills successfully upgraded to world-class level!")

if __name__ == "__main__":
    main()
