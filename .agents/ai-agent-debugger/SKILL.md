---
name: ai-agent-debugger
description: Comprehensive debugging skill for AI agents running in Kubernetes and distributed systems. Provides automated debugging, LLM-to-LLM analysis, tight feedback loops, and prevention strategies for AI agent infrastructure including memory agents, inference gateways, temporal workflows, and multi-agent coordination systems.
license: AGPLv3
metadata:
  author: gitops-infra-control-plane
  version: "1.0"
  category: debugging
  risk-level: low
  autonomy: fully_auto
compatibility: Requires Python 3.8+, kubectl, jq, curl, and access to Kubernetes clusters with AI agents deployed
allowed-tools: Bash Read Write Grep Kubectl Docker Curl Jq
---

# AI Agent Debugger — Distributed Systems Debugging & Prevention

## Purpose
Enterprise-grade debugging skill for AI agents running in Kubernetes distributed environments. Provides automated debugging capabilities, LLM-to-LLM analysis, tight feedback loops, and comprehensive prevention strategies for complex AI agent infrastructure including memory agents, inference gateways, temporal workflows, and multi-agent coordination systems.

## When to Use
- **AI agent troubleshooting**: When AI agents behave unexpectedly or fail in Kubernetes
- **Distributed system debugging**: When issues span multiple agents, services, or clusters
- **Performance analysis**: When AI agents show degraded performance or resource issues
- **LLM-to-LLM debugging**: When one AI needs to analyze and debug another AI
- **Prevention strategies**: To implement monitoring and prevent future agent failures
- **Multi-agent coordination**: Debugging interactions between multiple AI agents
- **Temporal workflow issues**: When AI agent workflows in Temporal fail or misbehave
- **Inference problems**: When AI model inference or reasoning chains fail

## Inputs
- **operation**: Debugging operation type (required)
  - `diagnose`: Comprehensive health check and issue identification
  - `analyze`: Deep behavioral analysis and pattern recognition
  - `debug`: Interactive debugging session with tight feedback loops
  - `llm-analyze`: LLM-to-LLM debugging and analysis
  - `prevent`: Generate prevention strategies and monitoring enhancements
  - `automate`: Execute automated fixes and recovery procedures
- **targetAgent**: Target AI agent name or type (required)
  - `memory-agent`: Memory management agents
  - `ai-inference-gateway`: Inference request routing and load balancing
  - `temporal-worker`: Temporal workflow execution agents
  - `consensus-agent`: Multi-agent consensus and coordination
  - `all`: Debug all agents in the system
- **namespace**: Kubernetes namespace (optional, default: `ai-infrastructure`)
- **debugLevel**: Analysis depth (optional, default: `medium`)
  - `basic`: Quick health check and immediate issues
  - `detailed`: Comprehensive analysis with behavioral patterns
  - `deep`: Deep dive with LLM analysis and prevention strategies
- **sessionMode**: Debugging session mode (optional, default: `interactive`)
  - `interactive`: Real-time debugging with live feedback
  - `automated`: Fully automated analysis and fixes
  - `llm-collaborative`: LLM-to-LLM collaborative debugging
- **correlationId**: Correlation ID for request tracing (optional, auto-generated)
- **outputFormat**: Output format (optional, default: `comprehensive`)
  - `summary`: Quick overview and key findings
  - `detailed`: Full analysis with recommendations
  - `comprehensive`: Complete session with artifacts and prevention

## Process
1. **Agent Discovery**: Identify target AI agents and their current state
2. **State Collection**: Gather comprehensive agent state from Kubernetes, logs, metrics
3. **Behavioral Analysis**: Analyze patterns, identify anomalies, and detect issues
4. **LLM Integration**: Generate LLM-specific debugging prompts and analysis
5. **Correlation Tracking**: Trace issues across agents and temporal workflows
6. **Automated Debugging**: Execute fixes, restart services, apply configurations
7. **Prevention Planning**: Generate monitoring enhancements and prevention strategies
8. **Session Management**: Create reproducible debugging sessions with artifacts

## Outputs
- **Health Assessment**: Comprehensive health status of target AI agents
- **Issue Identification**: Detailed analysis of detected problems and root causes
- **Behavioral Patterns**: Analysis of agent behavior and interaction patterns
- **LLM Debugging Prompts**: Specific prompts for LLM-to-LLM debugging sessions
- **Automated Fixes**: Applied fixes and recovery procedures with validation
- **Prevention Strategies**: Monitoring enhancements and prevention recommendations
- **Session Artifacts**: Complete debugging session with reproducible artifacts
- **Correlation Reports**: Request tracing across distributed agent systems

## Environment
- **Kubernetes**: AI agent deployments, services, configmaps, and statefulsets
- **Temporal**: Workflow execution, activity logs, and distributed tracing
- **Monitoring**: Prometheus metrics, Grafana dashboards, and log aggregation
- **Service Mesh**: Istio/Linkerd for inter-agent communication debugging
- **AI Infrastructure**: Ollama, model storage, inference endpoints, and memory systems
- **Multi-Cluster**: Hub-spoke topologies and cross-cluster agent coordination

## Dependencies
- **Python 3.8+**: Core debugging and analysis engine
- **Kubernetes**: kubectl for agent state collection and debugging
- **jq**: JSON processing and analysis of agent states
- **curl**: Health endpoint checking and API interactions
- **Docker**: Container inspection and image analysis
- **Temporal CLI**: Workflow and activity debugging
- **Prometheus**: Metrics collection and analysis
- **LLM Integration**: OpenAI/Claude API for LLM-to-LLM debugging

## Scripts
- `scripts/ai_agent_debugger.py`: Main debugging engine with comprehensive analysis
- `scripts/k8s_agent_collector.py`: Kubernetes agent state collection and monitoring
- `scripts/behavioral_analyzer.py`: Pattern recognition and behavioral analysis
- `scripts/llm_debug_integration.py`: LLM-to-LLM debugging and prompt generation
- `scripts/automated_fixer.py`: Automated fix execution and validation
- `scripts/prevention_planner.py`: Prevention strategies and monitoring enhancements
- `scripts/session_manager.py`: Debugging session management and artifact creation

## Trigger Keywords
debug, ai-agent, troubleshooting, kubernetes, distributed-systems, llm-debugging, temporal, memory-agent, inference-gateway, consensus, multi-agent, performance, monitoring, prevention, automation

## Human Gate Requirements
- **Production fixes**: Critical production agent fixes require approval
- **Major configuration changes**: Significant agent configuration modifications
- **Security-related debugging**: Security issue analysis and fixes
- **Multi-cluster changes**: Cross-cluster debugging and fixes

## API Patterns

### Python Main Debugger
```python
#!/usr/bin/env python3
"""
AI Agent Debugger - Distributed Systems Debugging & Prevention
Comprehensive debugging for AI agents in Kubernetes with LLM-to-LLM analysis
"""

import json
import sys
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import subprocess
import time

# Kubernetes and monitoring imports
try:
    from kubernetes import client, config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class DebugOperation(Enum):
    DIAGNOSE = "diagnose"
    ANALYZE = "analyze"
    DEBUG = "debug"
    LLM_ANALYZE = "llm-analyze"
    PREVENT = "prevent"
    AUTOMATE = "automate"

class DebugLevel(Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    DEEP = "deep"

class SessionMode(Enum):
    INTERACTIVE = "interactive"
    AUTOMATED = "automated"
    LLM_COLLABORATIVE = "llm-collaborative"

class AIAgentDebugger:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.correlation_id = None
        self.k8s_client = self._initialize_k8s()
        self.session_artifacts = {}
        
    def _initialize_k8s(self):
        """Initialize Kubernetes client"""
        if not K8S_AVAILABLE:
            logging.warning("Kubernetes client not available")
            return None
            
        try:
            config.load_kube_config()
            return {
                'core_v1': client.CoreV1Api(),
                'apps_v1': client.AppsV1Api(),
                'extensions_v1beta1': client.ExtensionsV1beta1Api()
            }
        except Exception as e:
            logging.error(f"Kubernetes client initialization failed: {e}")
            return None
    
    def execute_debugging(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main debugging execution"""
        try:
            validated_params = self._validate_inputs(params)
            self.correlation_id = validated_params.get('correlationId', f"debug-{int(time.time())}")
            
            # Execute based on operation type
            operation = DebugOperation(validated_params['operation'])
            
            if operation == DebugOperation.DIAGNOSE:
                result = self._execute_diagnose(validated_params)
            elif operation == DebugOperation.ANALYZE:
                result = self._execute_analyze(validated_params)
            elif operation == DebugOperation.DEBUG:
                result = self._execute_debug(validated_params)
            elif operation == DebugOperation.LLM_ANALYZE:
                result = self._execute_llm_analyze(validated_params)
            elif operation == DebugOperation.PREVENT:
                result = self._execute_prevent(validated_params)
            elif operation == DebugOperation.AUTOMATE:
                result = self._execute_automate(validated_params)
            else:
                raise ValueError(f"Unsupported operation: {operation.value}")
            
            return self._format_output(result, "completed")
            
        except Exception as e:
            return self._handle_error(e, params)
    
    def _execute_diagnose(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive diagnosis"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        debug_level = DebugLevel(params.get('debugLevel', 'medium'))
        
        results = {
            'operation': 'diagnose',
            'target_agent': target_agent,
            'namespace': namespace,
            'debug_level': debug_level.value,
            'timestamp': datetime.utcnow().isoformat(),
            'health_assessment': {},
            'immediate_issues': [],
            'resource_status': {},
            'connectivity_check': {}
        }
        
        # Collect agent health
        results['health_assessment'] = self._collect_agent_health(namespace, target_agent)
        
        # Check immediate issues
        results['immediate_issues'] = self._identify_immediate_issues(results['health_assessment'])
        
        # Resource status
        results['resource_status'] = self._check_resource_status(namespace, target_agent)
        
        # Connectivity checks
        results['connectivity_check'] = self._perform_connectivity_checks(namespace, target_agent)
        
        return results
    
    def _execute_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deep behavioral analysis"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        debug_level = DebugLevel(params.get('debugLevel', 'detailed'))
        
        results = {
            'operation': 'analyze',
            'target_agent': target_agent,
            'namespace': namespace,
            'debug_level': debug_level.value,
            'timestamp': datetime.utcnow().isoformat(),
            'behavioral_patterns': {},
            'performance_metrics': {},
            'log_analysis': {},
            'temporal_workflow_analysis': {},
            'agent_interactions': {}
        }
        
        # Behavioral pattern analysis
        results['behavioral_patterns'] = self._analyze_behavioral_patterns(namespace, target_agent)
        
        # Performance metrics
        results['performance_metrics'] = self._collect_performance_metrics(namespace, target_agent)
        
        # Log analysis
        results['log_analysis'] = self._perform_log_analysis(namespace, target_agent)
        
        # Temporal workflow analysis
        results['temporal_workflow_analysis'] = self._analyze_temporal_workflows(namespace, target_agent)
        
        # Agent interactions
        results['agent_interactions'] = self._analyze_agent_interactions(namespace, target_agent)
        
        return results
    
    def _execute_debug(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute interactive debugging session"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        session_mode = SessionMode(params.get('sessionMode', 'interactive'))
        
        results = {
            'operation': 'debug',
            'target_agent': target_agent,
            'namespace': namespace,
            'session_mode': session_mode.value,
            'timestamp': datetime.utcnow().isoformat(),
            'debugging_session': {
                'session_id': self.session_id,
                'correlation_id': self.correlation_id,
                'steps': [],
                'findings': [],
                'fixes_applied': [],
                'validation_results': []
            }
        }
        
        # Start debugging session
        session_results = self._run_debugging_session(namespace, target_agent, session_mode)
        results['debugging_session'].update(session_results)
        
        return results
    
    def _execute_llm_analyze(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM-to-LLM debugging analysis"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        
        results = {
            'operation': 'llm-analyze',
            'target_agent': target_agent,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'llm_analysis': {
                'agent_state_collection': {},
                'debugging_prompts': [],
                'analysis_results': {},
                'recommendations': []
            }
        }
        
        # Collect agent state for LLM analysis
        agent_state = self._collect_comprehensive_agent_state(namespace, target_agent)
        results['llm_analysis']['agent_state_collection'] = agent_state
        
        # Generate LLM debugging prompts
        prompts = self._generate_llm_debugging_prompts(agent_state)
        results['llm_analysis']['debugging_prompts'] = prompts
        
        # Store session for LLM collaboration
        self._create_llm_debugging_session(agent_state, prompts)
        
        return results
    
    def _execute_prevent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prevention strategies"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        
        results = {
            'operation': 'prevent',
            'target_agent': target_agent,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'prevention_strategies': {
                'monitoring_enhancements': {},
                'alerting_rules': [],
                'health_checks': {},
                'automated_recovery': {},
                'best_practices': []
            }
        }
        
        # Generate monitoring enhancements
        results['prevention_strategies']['monitoring_enhancements'] = self._generate_monitoring_enhancements(namespace, target_agent)
        
        # Create alerting rules
        results['prevention_strategies']['alerting_rules'] = self._create_alerting_rules(namespace, target_agent)
        
        # Health check recommendations
        results['prevention_strategies']['health_checks'] = self._recommend_health_checks(namespace, target_agent)
        
        # Automated recovery procedures
        results['prevention_strategies']['automated_recovery'] = self._design_automated_recovery(namespace, target_agent)
        
        # Best practices
        results['prevention_strategies']['best_practices'] = self._compile_best_practices(namespace, target_agent)
        
        return results
    
    def _execute_automate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automated fixes"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        
        results = {
            'operation': 'automate',
            'target_agent': target_agent,
            'namespace': namespace,
            'timestamp': datetime.utcnow().isoformat(),
            'automated_fixes': {
                'fixes_applied': [],
                'validation_results': [],
                'rollback_procedures': [],
                'success_rate': 0
            }
        }
        
        # Apply automated fixes
        fixes_applied = self._apply_automated_fixes(namespace, target_agent)
        results['automated_fixes']['fixes_applied'] = fixes_applied
        
        # Validate fixes
        validation_results = self._validate_fixes(namespace, target_agent, fixes_applied)
        results['automated_fixes']['validation_results'] = validation_results
        
        # Calculate success rate
        successful_fixes = len([f for f in validation_results if f['status'] == 'success'])
        results['automated_fixes']['success_rate'] = (successful_fixes / len(fixes_applied)) * 100 if fixes_applied else 0
        
        return results
    
    def _collect_agent_health(self, namespace: str, target_agent: str) -> Dict[str, Any]:
        """Collect comprehensive agent health information"""
        if not self.k8s_client:
            return {'error': 'Kubernetes client not available'}
        
        health_info = {
            'pods': {},
            'services': {},
            'deployments': {},
            'overall_health': 'unknown'
        }
        
        try:
            # Get pods
            pods = self.k8s_client['core_v1'].list_namespaced_pod(
                namespace=namespace,
                label_selector=f"component={target_agent}" if target_agent != 'all' else None
            )
            
            for pod in pods.items:
                health_info['pods'][pod.metadata.name] = {
                    'status': pod.status.phase,
                    'ready': self._is_pod_ready(pod),
                    'restarts': self._get_restart_count(pod),
                    'age': self._calculate_age(pod.metadata.creation_timestamp),
                    'node': pod.spec.node_name
                }
            
            # Get services
            services = self.k8s_client['core_v1'].list_namespaced_service(
                namespace=namespace,
                label_selector=f"component={target_agent}" if target_agent != 'all' else None
            )
            
            for service in services.items:
                health_info['services'][service.metadata.name] = {
                    'type': service.spec.type,
                    'ports': [{'port': p.port, 'target_port': p.target_port} for p in service.spec.ports or []],
                    'selector': service.spec.selector
                }
            
            # Get deployments
            deployments = self.k8s_client['apps_v1'].list_namespaced_deployment(
                namespace=namespace,
                label_selector=f"component={target_agent}" if target_agent != 'all' else None
            )
            
            for deployment in deployments.items:
                health_info['deployments'][deployment.metadata.name] = {
                    'replicas': deployment.spec.replicas,
                    'ready_replicas': deployment.status.ready_replicas or 0,
                    'available_replicas': deployment.status.available_replicas or 0,
                    'conditions': self._extract_deployment_conditions(deployment)
                }
            
            # Calculate overall health
            health_info['overall_health'] = self._calculate_overall_health(health_info)
            
        except Exception as e:
            health_info['error'] = str(e)
        
        return health_info
    
    def _generate_llm_debugging_prompts(self, agent_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific debugging prompts for LLM analysis"""
        prompts = []
        
        # Health assessment prompt
        health_prompt = {
            'id': 'health-assessment',
            'title': 'AI Agent Health Assessment',
            'prompt': f"""You are an expert AI systems debugger analyzing a Kubernetes-based AI agent infrastructure.

Agent State Data:
{json.dumps(agent_state, indent=2)}

Tasks:
1. Analyze the overall health status of all AI agents
2. Identify critical issues that need immediate attention
3. Assess the impact of each issue on system performance
4. Prioritize fixes based on severity and impact
5. Recommend specific debugging steps for each issue

Focus on:
- Pod health and restart patterns
- Resource constraints and OOM kills
- Network connectivity issues
- Service availability and response times
- Inter-agent communication problems

Provide specific, actionable recommendations with exact commands to execute.""",
            'context': 'health-analysis',
            'priority': 'high'
        }
        prompts.append(health_prompt)
        
        # Behavioral analysis prompt
        behavioral_prompt = {
            'id': 'behavioral-analysis',
            'title': 'Agent Behavior Pattern Analysis',
            'prompt': f"""Analyze the behavioral patterns of AI agents in this Kubernetes infrastructure:

Agent State:
{json.dumps(agent_state, indent=2)}

Analysis Tasks:
1. Identify unusual behavioral patterns or anomalies
2. Analyze temporal workflow execution patterns
3. Detect performance degradation trends
4. Identify coordination issues between multiple agents
5. Assess inference request/response patterns

Key Areas:
- Memory agent state management patterns
- Inference gateway request routing behavior
- Temporal workflow execution reliability
- Multi-agent consensus and coordination
- Resource utilization patterns over time

Provide insights into:
- Root causes of behavioral issues
- Performance optimization opportunities
- Reliability improvement strategies
- Prevention measures for future issues""",
            'context': 'behavioral-analysis',
            'priority': 'medium'
        }
        prompts.append(behavioral_prompt)
        
        # LLM-to-LLM collaboration prompt
        collaboration_prompt = {
            'id': 'llm-collaboration',
            'title': 'LLM-to-LLM Collaborative Debugging',
            'prompt': f"""You are debugging another AI (LLM) running in Kubernetes. This is a meta-debugging session where one AI analyzes another AI's behavior.

Target AI Agent State:
{json.dumps(agent_state, indent=2)}

Meta-Debugging Tasks:
1. Analyze the target AI's decision-making patterns
2. Identify potential issues in the AI's reasoning chains
3. Assess the quality of the AI's inference outputs
4. Detect any self-referential loops or circular reasoning
5. Evaluate the AI's learning and adaptation patterns

AI-Specific Analysis:
- Model inference quality and consistency
- Prompt engineering and response patterns
- Learning loop effectiveness
- Memory management and state persistence
- Inter-AI communication protocols

Collaborative Debugging Approach:
1. What questions would you ask the target AI?
2. What test scenarios would you run to validate fixes?
3. How would you verify the AI's understanding of its role?
4. What metrics would indicate successful debugging?

Provide both technical fixes and AI-specific behavioral corrections.""",
            'context': 'llm-collaboration',
            'priority': 'high'
        }
        prompts.append(collaboration_prompt)
        
        return prompts
    
    def _create_llm_debugging_session(self, agent_state: Dict[str, Any], prompts: List[Dict[str, Any]]) -> str:
        """Create a reproducible LLM debugging session"""
        session_data = {
            'session_id': self.session_id,
            'correlation_id': self.correlation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_state': agent_state,
            'debugging_prompts': prompts,
            'session_type': 'llm-collaborative-debugging'
        }
        
        # Save session to file for sharing with other LLMs
        session_file = f"llm-debug-session-{self.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return session_file
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to skill specification"""
        return {
            "operationId": self.session_id,
            "correlationId": self.correlation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {
                "execution_time": 1.0,
                "risk_score": 2,
                "agent_version": "1.0.0",
                "debugging_capabilities": [
                    "health-assessment",
                    "behavioral-analysis",
                    "llm-collaboration",
                    "automated-fixes",
                    "prevention-strategies"
                ]
            }
        }
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {
            "operationId": self.session_id,
            "correlationId": self.correlation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "code": "DEBUGGING_ERROR",
                "message": str(error),
                "details": {
                    "parameters": params,
                    "error_type": type(error).__name__,
                    "troubleshooting_steps": [
                        "Check Kubernetes cluster connectivity",
                        "Verify agent deployment status",
                        "Validate debugging parameters",
                        "Check required tool availability"
                    ]
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
            'operation': 'diagnose',
            'targetAgent': 'all',
            'namespace': 'ai-infrastructure',
            'debugLevel': 'medium'
        }
    
    debugger = AIAgentDebugger()
    result = debugger.execute_debugging(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### Shell Integration
```bash
#!/bin/bash
# AI Agent Debugging Shell Integration
AGENT_TYPE=${1:-all}
NAMESPACE=${2:-ai-infrastructure}
OPERATION=${3:-diagnose}
DEBUG_LEVEL=${4:-medium}

echo "🔍 AI Agent Debugging Session Started"
echo "Target: $AGENT_TYPE"
echo "Namespace: $NAMESPACE"
echo "Operation: $OPERATION"
echo "Debug Level: $DEBUG_LEVEL"
echo ""

# Run comprehensive debugging
python3 scripts/ai_agent_debugger.py << EOF
{
  "operation": "$OPERATION",
  "targetAgent": "$AGENT_TYPE",
  "namespace": "$NAMESPACE",
  "debugLevel": "$DEBUG_LEVEL",
  "sessionMode": "interactive",
  "correlationId": "debug-$(date +%s)"
}
EOF

echo ""
echo "📊 Debugging session completed. Check generated artifacts for detailed analysis."
```

## Parameter Schema
```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["diagnose", "analyze", "debug", "llm-analyze", "prevent", "automate"],
      "description": "Debugging operation type"
    },
    "targetAgent": {
      "type": "string",
      "enum": ["memory-agent", "ai-inference-gateway", "temporal-worker", "consensus-agent", "all"],
      "description": "Target AI agent name or type"
    },
    "namespace": {
      "type": "string",
      "default": "ai-infrastructure",
      "description": "Kubernetes namespace"
    },
    "debugLevel": {
      "type": "string",
      "enum": ["basic", "detailed", "deep"],
      "default": "medium",
      "description": "Analysis depth"
    },
    "sessionMode": {
      "type": "string",
      "enum": ["interactive", "automated", "llm-collaborative"],
      "default": "interactive",
      "description": "Debugging session mode"
    },
    "correlationId": {
      "type": "string",
      "description": "Correlation ID for request tracing"
    },
    "outputFormat": {
      "type": "string",
      "enum": ["summary", "detailed", "comprehensive"],
      "default": "comprehensive",
      "description": "Output format"
    }
  },
  "required": ["operation", "targetAgent"]
}
```

## Return Schema
```json
{
  "type": "object",
  "properties": {
    "operationId": {
      "type": "string",
      "format": "uuid"
    },
    "correlationId": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["started", "running", "completed", "failed"]
    },
    "result": {
      "type": "object",
      "properties": {
        "operation": {"type": "string"},
        "target_agent": {"type": "string"},
        "health_assessment": {
          "type": "object",
          "description": "Comprehensive health status of agents"
        },
        "behavioral_patterns": {
          "type": "object",
          "description": "Analysis of agent behavior patterns"
        },
        "llm_analysis": {
          "type": "object",
          "description": "LLM-to-LLM debugging analysis and prompts"
        },
        "prevention_strategies": {
          "type": "object",
          "description": "Monitoring enhancements and prevention measures"
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "execution_time": {"type": "number"},
        "risk_score": {"type": "number", "minimum": 1, "maximum": 10},
        "debugging_capabilities": {
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
          "enum": ["VALIDATION_ERROR", "KUBERNETES_ERROR", "AGENT_NOT_FOUND", "DEBUGGING_ERROR", "LLM_ANALYSIS_ERROR"]
        },
        "message": {"type": "string"},
        "details": {
          "type": "object",
          "properties": {
            "troubleshooting_steps": {
              "type": "array",
              "items": {"type": "string"}
            },
            "affected_agents": {
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
- **Distributed Debugging**: Debug AI agents across multiple clusters and environments
- **LLM Collaboration**: Enable multiple LLMs to collaboratively debug agent issues
- **Automated Prevention**: Generate monitoring and alerting to prevent future issues
- **Session Management**: Reproducible debugging sessions with full artifact preservation
- **Real-time Analysis**: Live debugging with tight feedback loops
- **Cross-System Correlation**: Trace issues across agents, workflows, and infrastructure
- **Performance Optimization**: Identify and resolve performance bottlenecks in AI systems
- **Security Integration**: Debug security-related issues while maintaining compliance

## Integration Examples
- **Kubernetes Native**: Direct integration with agent deployments and services
- **Temporal Workflows**: Debug AI agent workflows and activity execution
- **Service Mesh**: Analyze inter-agent communication through Istio/Linkerd
- **Monitoring Stack**: Integration with Prometheus, Grafana, and log aggregation
- **Multi-Cluster**: Debugging across hub-spoke topologies
- **LLM Ecosystem**: Integration with OpenAI, Claude, and other LLM providers

## Best Practices
- **Incremental Debugging**: Start with basic diagnosis before deep analysis
- **Correlation Tracking**: Use correlation IDs to trace issues across systems
- **Session Preservation**: Save debugging sessions for future reference and collaboration
- **Prevention First**: Always generate prevention strategies alongside fixes
- **LLM Collaboration**: Leverage multiple LLMs for complex debugging scenarios
- **Automated Validation**: Always validate applied fixes and measure success rates
- **Documentation**: Document debugging findings for knowledge base improvement

## Agent Enhancement Capabilities
- **Self-Debugging**: Agents can analyze their own behavior and identify issues
- **Collaborative Debugging**: Multiple agents can work together to solve complex problems
- **Learning from Debugging**: Agents learn from debugging sessions to prevent future issues
- **Adaptive Debugging**: Debugging strategies adapt based on agent type and issue patterns
- **Predictive Analysis**: Agents can predict potential issues before they occur
- **Cross-Domain Debugging**: Debug issues that span multiple domains (infrastructure, AI, workflows)
- **Automated Recovery**: Agents can automatically recover from common failure modes
- **Knowledge Transfer**: Debugging knowledge is shared across the agent ecosystem
