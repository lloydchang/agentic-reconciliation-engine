---
name: k8sgpt-analyzer
description: Provides AI-powered Kubernetes cluster analysis and troubleshooting using K8sGPT with Qwen LLM. Use when diagnosing cluster issues, analyzing problems, or getting intelligent insights about Kubernetes resources and configurations.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: enterprise
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for cluster-wide changes
compatibility: Requires Python 3.8+, kubectl, K8sGPT CLI, and access to Kubernetes clusters
allowed-tools: Bash Read Write Grep Kubectl
---

# K8sGPT Analyzer — AI-Powered Kubernetes Intelligence

## Purpose
Enterprise-grade AI-powered Kubernetes cluster analysis and troubleshooting solution that leverages K8sGPT with Qwen LLM to provide intelligent insights, automated problem detection, and contextual recommendations across multi-cloud Kubernetes environments.

## When to Use
- **Cluster analysis** and automated problem detection
- **Intelligent troubleshooting** with AI-powered insights
- **Resource optimization** and configuration recommendations
- **Multi-cluster monitoring** and health assessments
- **Incident response** and root cause analysis
- **Capacity planning** and performance optimization

## Inputs
- **operation**: Operation type - `analyze|diagnose|optimize|monitor|report` (required)
- **targetResource**: Target resource identifier - `namespace|deployment|pod|service|cluster` (required)
- **scope**: Analysis scope - `cluster|namespace|resource|all` (optional, default: `cluster`)
- **backend**: LLM backend - `qwen|openai|localai|ollama` (optional, default: `qwen`)
- **explain**: Enable AI explanations (optional, default: `true`)
- **output**: Output format - `json|yaml|table|summary` (optional, default: `json`)
- **filters**: Resource filters and constraints (optional)
- **environment**: Target environment (optional, default: `production`)

## Process
1. **Environment Validation**: Verify Kubernetes connectivity and permissions
2. **K8sGPT Configuration**: Setup Qwen LLM backend and authentication
3. **Resource Discovery**: Identify target resources based on scope and filters
4. **AI Analysis**: Execute K8sGPT analysis with specified parameters
5. **Intelligence Processing**: Process AI insights and recommendations
6. **Context Enrichment**: Add operational context and historical data
7. **Report Generation**: Create comprehensive analysis reports
8. **Action Planning**: Generate actionable recommendations

## Outputs
- **AI Analysis Results**: Detailed findings from K8sGPT analysis
- **Problem Detection**: Identified issues and their severity levels
- **Recommendations**: Actionable improvement suggestions
- **Resource Insights**: Performance and configuration analysis
- **Risk Assessment**: Security and compliance evaluation
- **Optimization Opportunities**: Cost and performance improvements
- **Audit Trail**: Complete analysis history and changes

## Environment
- **Kubernetes**: Multi-cluster support across EKS, AKS, GKE, and on-premise
- **K8sGPT**: Latest stable version with Qwen LLM integration
- **Qwen LLM**: Local or cloud-hosted Qwen models for AI inference
- **Monitoring**: Prometheus, Grafana, and observability stack integration
- **Storage**: Persistent storage for analysis results and configurations

## Dependencies
- **Python 3.8+**: Core execution environment
- **K8sGPT CLI**: Latest version for Kubernetes analysis
- **Kubernetes**: kubectl and cluster access
- **Qwen LLM**: Local inference or API access
- **PyYAML**: Configuration file processing
- **Requests**: HTTP client for API interactions
- **JSON Schema**: Validation and schema processing

## Scripts
- `scripts/k8sgpt_analyzer.py`: Main analysis engine and orchestration
- `scripts/qwen_integration.py`: Qwen LLM backend configuration
- `scripts/cluster_scanner.py`: Multi-cluster resource discovery
- `scripts/report_generator.py`: Comprehensive report generation
- `scripts/automation_helper.py`: Automated setup and configuration

## Trigger Keywords
k8sgpt, analyzer, kubernetes, troubleshooting, AI, qwen, analysis, monitoring, optimization, cluster, diagnostics

## Human Gate Requirements
- **Cluster-wide changes**: Operations affecting entire clusters require approval
- **Production modifications**: Changes to production environments need validation
- **Security configurations**: Security-related modifications require review
- **Resource scaling**: Major resource changes need oversight

## API Patterns

### Python Agent Implementation
```python
#!/usr/bin/env python3
"""
K8sGPT Analyzer - AI-Powered Kubernetes Intelligence
Integrates K8sGPT with Qwen LLM for intelligent cluster analysis
"""

import json
import sys
import uuid
import logging
import subprocess
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class K8sGPTAnalyzer:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.config = self._load_config()
        self.k8sgpt_path = self._find_k8sgpt()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        config_path = Path.home() / '.k8sgpt' / 'config.yaml'
        default_config = {
            'backend': 'qwen',
            'model': 'qwen2.5-7b-instruct',
            'baseurl': 'http://localhost:8000/v1',
            'max_tokens': 4096,
            'temperature': 0.7,
            'namespace': 'default',
            'output_format': 'json'
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _find_k8sgpt(self) -> str:
        """Find K8sGPT binary in PATH"""
        try:
            result = subprocess.run(['which', 'k8sgpt'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("K8sGPT CLI not found. Please install K8sGPT first.")
    
    def execute_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main operation execution"""
        try:
            validated_params = self._validate_inputs(params)
            self._setup_k8sgpt_backend(validated_params)
            results = self._perform_analysis(validated_params)
            return self._format_output(results, "completed")
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation"""
        required_fields = ['operation', 'targetResource']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
        
        valid_operations = ['analyze', 'diagnose', 'optimize', 'monitor', 'report']
        if params['operation'] not in valid_operations:
            raise ValueError(f"Invalid operation: {params['operation']}")
        
        return params
    
    def _setup_k8sgpt_backend(self, params: Dict[str, Any]) -> None:
        """Configure K8sGPT backend (Qwen by default)"""
        backend = params.get('backend', self.config['backend'])
        
        if backend == 'qwen':
            # Configure Qwen backend via LocalAI/OpenAI compatible API
            cmd = [
                'k8sgpt', 'auth', 'add',
                '--backend', 'localai',
                '--model', self.config['model'],
                '--baseurl', self.config['baseurl']
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        
        logging.info(f"K8sGPT backend configured: {backend}")
    
    def _perform_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute K8sGPT analysis"""
        operation = params['operation']
        target = params['targetResource']
        scope = params.get('scope', 'cluster')
        explain = params.get('explain', True)
        
        # Build K8sGPT command
        cmd = ['k8sgpt', 'analyze']
        
        if scope != 'cluster':
            cmd.extend(['--namespace', scope])
        
        if target != 'cluster':
            cmd.extend(['--filter', target])
        
        if explain:
            cmd.append('--explain')
        
        # Add backend specification
        cmd.extend(['--backend', params.get('backend', self.config['backend'])])
        
        # Execute analysis
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse and enhance results
        analysis_data = self._parse_k8sgpt_output(result.stdout)
        
        return {
            'operation': operation,
            'target': target,
            'scope': scope,
            'analysis': analysis_data,
            'timestamp': datetime.utcnow().isoformat(),
            'backend': params.get('backend', self.config['backend'])
        }
    
    def _parse_k8sgpt_output(self, output: str) -> Dict[str, Any]:
        """Parse K8sGPT output into structured format"""
        try:
            # Try JSON first
            return json.loads(output)
        except json.JSONDecodeError:
            # Parse text output
            lines = output.strip().split('\n')
            return {
                'format': 'text',
                'content': output,
                'lines': lines,
                'summary': lines[0] if lines else "No analysis available"
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
                "risk_score": 3,
                "agent_version": "1.0.0",
                "k8sgpt_version": "latest",
                "backend": self.config['backend']
            }
        }
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": str(error),
                "details": {
                    "parameters": params,
                    "error_type": type(error).__name__
                }
            }
        }

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {
            'operation': 'analyze',
            'targetResource': 'cluster',
            'scope': 'cluster',
            'backend': 'qwen',
            'explain': True
        }
    
    analyzer = K8sGPTAnalyzer()
    result = analyzer.execute_operation(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### Shell Commands Integration
```bash
#!/bin/bash
# K8sGPT Analyzer Shell Integration
OPERATION=${1:-analyze}
TARGET=${2:-cluster}
SCOPE=${3:-cluster}
BACKEND=${4:-qwen}

echo "Executing K8sGPT ${OPERATION} on ${TARGET} in ${SCOPE} scope"

# Setup Qwen backend if needed
if [[ "$BACKEND" == "qwen" ]]; then
    echo "Configuring Qwen LLM backend..."
    k8sgpt auth add --backend localai --model qwen2.5-7b-instruct --baseurl http://localhost:8000/v1
fi

# Execute analysis
case $OPERATION in
    "analyze")
        k8sgpt analyze --explain --backend $BACKEND ${TARGET:+--filter $TARGET} ${SCOPE:+--namespace $SCOPE}
        ;;
    "diagnose")
        k8sgpt analyze --explain --backend $BACKEND --filter "problems" ${TARGET:+--filter $TARGET}
        ;;
    "optimize")
        k8sgpt analyze --explain --backend $BACKEND --filter "resources" ${TARGET:+--filter $TARGET}
        ;;
    "monitor")
        k8sgpt analyze --backend $BACKEND --output json ${TARGET:+--filter $TARGET}
        ;;
    *)
        echo "Unknown operation: $OPERATION"
        echo "Available: analyze, diagnose, optimize, monitor"
        exit 1
        ;;
esac
```

## Parameter Schema
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["analyze", "diagnose", "optimize", "monitor", "report"],
      "description": "Type of analysis to perform"
    },
    "targetResource": {
      "type": "string",
      "description": "Target resource for analysis"
    },
    "scope": {
      "type": "string",
      "enum": ["cluster", "namespace", "resource", "all"],
      "default": "cluster",
      "description": "Analysis scope"
    },
    "backend": {
      "type": "string",
      "enum": ["qwen", "openai", "localai", "ollama"],
      "default": "qwen",
      "description": "LLM backend to use"
    },
    "explain": {
      "type": "boolean",
      "default": true,
      "description": "Enable AI explanations"
    },
    "output": {
      "type": "string",
      "enum": ["json", "yaml", "table", "summary"],
      "default": "json",
      "description": "Output format"
    }
  },
  "required": ["operation", "targetResource"]
}
```

## Enterprise Features
- **Multi-Cluster Support**: Analyze across multiple Kubernetes clusters
- **Qwen LLM Integration**: Local AI inference with Qwen models
- **Intelligent Filtering**: Smart resource filtering and targeting
- **Contextual Analysis**: Historical data and operational context
- **Automated Reporting**: Comprehensive analysis reports
- **Security Scanning**: AI-powered security vulnerability detection
- **Performance Optimization**: Resource usage and performance recommendations
- **Compliance Monitoring**: Policy compliance and governance checks

## Best Practices
- **Backend Configuration**: Ensure Qwen LLM is properly configured and accessible
- **Resource Scoping**: Use appropriate scopes to limit analysis scope
- **Output Management**: Choose appropriate output formats for integration
- **Error Handling**: Implement robust error handling for API failures
- **Security**: Validate permissions and access controls before analysis
- **Performance**: Monitor analysis execution time and resource usage

## Integration Examples
- **GitOps Workflows**: Integrate with Flux/ArgoCD for automated analysis
- **CI/CD Pipelines**: Add cluster analysis to deployment pipelines
- **Monitoring Stack**: Integrate with Prometheus/Grafana dashboards
- **Alerting Systems**: Connect to AlertManager for intelligent alerting
- **ChatOps**: Enable Slack/Teams integration for cluster insights
- **Documentation**: Auto-generate cluster documentation and reports
