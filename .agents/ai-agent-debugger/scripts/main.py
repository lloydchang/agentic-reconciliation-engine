# /// script
# dependencies = [
#   "kubernetes>=25.0.0",
#   "requests>=2.28.0",
#   "pydantic>=1.10.0",
#   "asyncio",
#   "aiohttp>=3.8.0",
#   "prometheus-client>=0.15.0"
# ]
# ///

#!/usr/bin/env python3
"""
AI Agent Debugger - Main Implementation
Comprehensive debugging for AI agents in Kubernetes distributed systems
"""

import json
import sys
import uuid
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import subprocess
import time
import os
from pathlib import Path

# Kubernetes imports
try:
    from kubernetes import client, config, watch
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

# Monitoring imports
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
        self.start_time = datetime.utcnow()
        
    def _initialize_k8s(self):
        """Initialize Kubernetes client with fallback options"""
        if not K8S_AVAILABLE:
            logging.warning("Kubernetes client not available")
            return None
            
        try:
            # Try in-cluster config first
            config.load_incluster_config()
            logging.info("Using in-cluster Kubernetes configuration")
        except:
            try:
                # Fall back to kubeconfig
                config.load_kube_config()
                logging.info("Using kubeconfig Kubernetes configuration")
            except Exception as e:
                logging.error(f"Kubernetes configuration failed: {e}")
                return None
        
        try:
            return {
                'core_v1': client.CoreV1Api(),
                'apps_v1': client.AppsV1Api(),
                'extensions_v1beta1': client.ExtensionsV1beta1Api(),
                'custom_objects': client.CustomObjectsApi()
            }
        except Exception as e:
            logging.error(f"Kubernetes client initialization failed: {e}")
            return None
    
    def execute_debugging(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main debugging execution with comprehensive error handling"""
        try:
            validated_params = self._validate_inputs(params)
            self.correlation_id = validated_params.get('correlationId', f"debug-{int(time.time())}")
            
            logging.info(f"Starting debugging session {self.session_id} for agent {validated_params.get('targetAgent')}")
            
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
            logging.error(f"Debugging execution failed: {e}")
            return self._handle_error(e, params)
    
    def _execute_diagnose(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive diagnosis with multi-layer analysis"""
        namespace = params.get('namespace', 'ai-infrastructure')
        target_agent = params.get('targetAgent', 'all')
        debug_level = DebugLevel(params.get('debugLevel', 'medium'))
        
        logging.info(f"Executing diagnosis for {target_agent} in {namespace}")
        
        results = {
            'operation': 'diagnose',
            'target_agent': target_agent,
            'namespace': namespace,
            'debug_level': debug_level.value,
            'timestamp': datetime.utcnow().isoformat(),
            'health_assessment': {},
            'immediate_issues': [],
            'resource_status': {},
            'connectivity_check': {},
            'cluster_health': {}
        }
        
        # Collect agent health
        results['health_assessment'] = self._collect_agent_health(namespace, target_agent)
        
        # Check immediate issues
        results['immediate_issues'] = self._identify_immediate_issues(results['health_assessment'])
        
        # Resource status
        results['resource_status'] = self._check_resource_status(namespace, target_agent)
        
        # Connectivity checks
        results['connectivity_check'] = self._perform_connectivity_checks(namespace, target_agent)
        
        # Cluster health
        results['cluster_health'] = self._check_cluster_health(namespace)
        
        return results
    
    def _collect_agent_health(self, namespace: str, target_agent: str) -> Dict[str, Any]:
        """Collect comprehensive agent health information with detailed analysis"""
        if not self.k8s_client:
            return {'error': 'Kubernetes client not available'}
        
        health_info = {
            'pods': {},
            'services': {},
            'deployments': {},
            'configmaps': {},
            'secrets': {},
            'events': [],
            'overall_health': 'unknown',
            'health_score': 0
        }
        
        try:
            # Get pods with detailed status
            label_selector = f"component={target_agent}" if target_agent != 'all' else None
            pods = self.k8s_client['core_v1'].list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector
            )
            
            total_pods = len(pods.items)
            healthy_pods = 0
            
            for pod in pods.items:
                pod_health = {
                    'status': pod.status.phase,
                    'ready': self._is_pod_ready(pod),
                    'restarts': self._get_restart_count(pod),
                    'age': self._calculate_age(pod.metadata.creation_timestamp),
                    'node': pod.spec.node_name,
                    'conditions': self._extract_pod_conditions(pod),
                    'containers': self._get_container_status(pod),
                    'resources': self._get_pod_resources(pod),
                    'ip': pod.status.pod_ip,
                    'events': self._get_pod_events(namespace, pod.metadata.name)
                }
                
                health_info['pods'][pod.metadata.name] = pod_health
                
                if pod_health['ready'] and pod_health['status'] == 'Running':
                    healthy_pods += 1
            
            # Calculate health score
            if total_pods > 0:
                health_info['health_score'] = (healthy_pods / total_pods) * 100
            
            # Get services
            services = self.k8s_client['core_v1'].list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector
            )
            
            for service in services.items:
                health_info['services'][service.metadata.name] = {
                    'type': service.spec.type,
                    'ports': [{'port': p.port, 'target_port': p.target_port, 'protocol': p.protocol} for p in service.spec.ports or []],
                    'selector': service.spec.selector,
                    'cluster_ip': service.spec.cluster_ip,
                    'external_ips': service.spec.external_ips or [],
                    'endpoints': self._get_service_endpoints(namespace, service.metadata.name)
                }
            
            # Get deployments
            deployments = self.k8s_client['apps_v1'].list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
            
            for deployment in deployments.items:
                health_info['deployments'][deployment.metadata.name] = {
                    'replicas': deployment.spec.replicas,
                    'ready_replicas': deployment.status.ready_replicas or 0,
                    'available_replicas': deployment.status.available_replicas or 0,
                    'unavailable_replicas': deployment.status.unavailable_replicas or 0,
                    'conditions': self._extract_deployment_conditions(deployment),
                    'strategy': deployment.spec.strategy.type if deployment.spec.strategy else 'RollingUpdate',
                    'rolling_update_config': self._get_rolling_update_config(deployment)
                }
            
            # Get recent events
            events = self.k8s_client['core_v1'].list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={target_agent}" if target_agent != 'all' else None
            )
            
            health_info['events'] = [
                {
                    'type': event.type,
                    'reason': event.reason,
                    'message': event.message,
                    'timestamp': event.last_timestamp.isoformat() if event.last_timestamp else None,
                    'object': event.involved_object.name if event.involved_object else None
                }
                for event in events.items[-20:]  # Last 20 events
            ]
            
            # Calculate overall health
            health_info['overall_health'] = self._calculate_overall_health(health_info)
            
        except Exception as e:
            health_info['error'] = str(e)
            logging.error(f"Health collection failed: {e}")
        
        return health_info
    
    def _is_pod_ready(self, pod) -> bool:
        """Check if pod is ready"""
        if not pod.status.container_statuses:
            return False
        
        for container_status in pod.status.container_statuses:
            if not container_status.ready:
                return False
        
        return pod.status.phase == 'Running'
    
    def _get_restart_count(self, pod) -> int:
        """Get total restart count for pod"""
        if not pod.status.container_statuses:
            return 0
        
        total_restarts = 0
        for container_status in pod.status.container_statuses:
            total_restarts += container_status.restart_count
        
        return total_restarts
    
    def _calculate_age(self, creation_timestamp) -> str:
        """Calculate age from creation timestamp"""
        if not creation_timestamp:
            return "Unknown"
        
        age = datetime.utcnow() - creation_timestamp.replace(tzinfo=None)
        
        if age.days > 0:
            return f"{age.days}d"
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return f"{hours}h"
        elif age.seconds > 60:
            minutes = age.seconds // 60
            return f"{minutes}m"
        else:
            return f"{age.seconds}s"
    
    def _extract_pod_conditions(self, pod) -> List[Dict[str, Any]]:
        """Extract pod conditions"""
        conditions = []
        if pod.status.conditions:
            for condition in pod.status.conditions:
                conditions.append({
                    'type': condition.type,
                    'status': condition.status,
                    'reason': condition.reason,
                    'message': condition.message,
                    'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else None
                })
        return conditions
    
    def _get_container_status(self, pod) -> Dict[str, Any]:
        """Get detailed container status"""
        containers = {}
        if pod.status.container_statuses:
            for container_status in pod.status.container_statuses:
                containers[container_status.name] = {
                    'ready': container_status.ready,
                    'restart_count': container_status.restart_count,
                    'image': container_status.image,
                    'image_id': container_status.image_id,
                    'state': self._extract_container_state(container_status.state)
                }
        return containers
    
    def _get_pod_resources(self, pod) -> Dict[str, Any]:
        """Get pod resource requests and limits"""
        resources = {'requests': {}, 'limits': {}}
        
        if pod.spec.containers:
            for container in pod.spec.containers:
                if container.resources:
                    if container.resources.requests:
                        resources['requests'] = dict(container.resources.requests)
                    if container.resources.limits:
                        resources['limits'] = dict(container.resources.limits)
        
        return resources
    
    def _calculate_overall_health(self, health_info: Dict[str, Any]) -> str:
        """Calculate overall health status"""
        if 'error' in health_info:
            return 'error'
        
        health_score = health_info.get('health_score', 0)
        
        if health_score >= 90:
            return 'healthy'
        elif health_score >= 70:
            return 'degraded'
        elif health_score >= 50:
            return 'unhealthy'
        else:
            return 'critical'
    
    def _identify_immediate_issues(self, health_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify immediate issues that need attention"""
        issues = []
        
        # Check pod issues
        for pod_name, pod_info in health_assessment.get('pods', {}).items():
            if pod_info.get('status') != 'Running':
                issues.append({
                    'type': 'pod_not_running',
                    'severity': 'high',
                    'component': pod_name,
                    'message': f"Pod {pod_name} is in {pod_info.get('status')} state",
                    'recommendation': 'Check pod logs and events for troubleshooting'
                })
            
            if pod_info.get('restarts', 0) > 5:
                issues.append({
                    'type': 'high_restart_count',
                    'severity': 'medium',
                    'component': pod_name,
                    'message': f"Pod {pod_name} has restarted {pod_info.get('restarts')} times",
                    'recommendation': 'Investigate crash loops and resource constraints'
                })
        
        # Check deployment issues
        for deployment_name, deployment_info in health_assessment.get('deployments', {}).items():
            ready = deployment_info.get('ready_replicas', 0)
            desired = deployment_info.get('replicas', 0)
            
            if ready < desired:
                issues.append({
                    'type': 'deployment_not_ready',
                    'severity': 'high',
                    'component': deployment_name,
                    'message': f"Deployment {deployment_name}: {ready}/{desired} replicas ready",
                    'recommendation': 'Check deployment conditions and resource availability'
                })
        
        # Check service issues
        for service_name, service_info in health_assessment.get('services', {}).items():
            endpoints = service_info.get('endpoints', [])
            if not endpoints:
                issues.append({
                    'type': 'no_endpoints',
                    'severity': 'medium',
                    'component': service_name,
                    'message': f"Service {service_name} has no ready endpoints",
                    'recommendation': 'Check pod selector and pod readiness'
                })
        
        return issues
    
    def _perform_connectivity_checks(self, namespace: str, target_agent: str) -> Dict[str, Any]:
        """Perform connectivity checks between agents and services"""
        connectivity = {
            'service_endpoints': {},
            'health_checks': {},
            'network_policies': {},
            'dns_resolution': {}
        }
        
        try:
            # Check service endpoints
            services = self.k8s_client['core_v1'].list_namespaced_service(namespace=namespace)
            
            for service in services.items:
                if target_agent == 'all' or service.metadata.labels.get('component') == target_agent:
                    endpoints = self.k8s_client['core_v1'].list_namespaced_endpoints(
                        namespace=namespace,
                        field_selector=f"metadata.name={service.metadata.name}"
                    )
                    
                    connectivity['service_endpoints'][service.metadata.name] = {
                        'ready': len([addr for addr in endpoints.items[0].subsets if addr.addresses]) > 0 if endpoints.items else False,
                        'addresses': [addr.ip for subset in endpoints.items[0].subsets for addr in (subset.addresses or [])] if endpoints.items else [],
                        'ports': [port.port for subset in endpoints.items[0].subsets for port in (subset.ports or [])] if endpoints.items else []
                    }
            
            # Check health endpoints
            for service_name, service_info in connectivity['service_endpoints'].items():
                if service_info['ready'] and service_info['ports']:
                    # Try to connect to health endpoint
                    port = service_info['ports'][0]  # Use first port
                    health_status = self._check_health_endpoint(namespace, service_name, port)
                    connectivity['health_checks'][service_name] = health_status
        
        except Exception as e:
            connectivity['error'] = str(e)
        
        return connectivity
    
    def _check_health_endpoint(self, namespace: str, service_name: str, port: int) -> Dict[str, Any]:
        """Check health endpoint of a service"""
        try:
            # Port-forward and check health
            pf_cmd = f"kubectl port-forward -n {namespace} service/{service_name} 8080:{port}"
            pf_process = subprocess.Popen(pf_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for port-forward
            time.sleep(2)
            
            # Check health endpoint
            try:
                response = requests.get("http://localhost:8080/health", timeout=5)
                health_status = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            except:
                health_status = {
                    'status': 'unreachable',
                    'error': 'Could not reach health endpoint'
                }
            finally:
                # Clean up port-forward
                pf_process.terminate()
                pf_process.wait()
            
            return health_status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation with comprehensive checks"""
        required_fields = ['operation', 'targetAgent']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate operation
        operation = params.get('operation')
        valid_operations = [op.value for op in DebugOperation]
        if operation not in valid_operations:
            raise ValueError(f"Invalid operation: {operation}. Valid operations: {valid_operations}")
        
        # Validate target agent
        target_agent = params.get('targetAgent')
        valid_agents = ['memory-agent', 'ai-inference-gateway', 'temporal-worker', 'consensus-agent', 'all']
        if target_agent not in valid_agents:
            raise ValueError(f"Invalid targetAgent: {target_agent}. Valid agents: {valid_agents}")
        
        # Validate debug level
        debug_level = params.get('debugLevel', 'medium')
        valid_levels = [level.value for level in DebugLevel]
        if debug_level not in valid_levels:
            raise ValueError(f"Invalid debugLevel: {debug_level}. Valid levels: {valid_levels}")
        
        return params
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to skill specification"""
        execution_time = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "operationId": self.session_id,
            "correlationId": self.correlation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {
                "execution_time": execution_time,
                "risk_score": 2,
                "agent_version": "1.0.0",
                "debugging_capabilities": [
                    "health-assessment",
                    "behavioral-analysis",
                    "llm-collaboration",
                    "automated-fixes",
                    "prevention-strategies",
                    "connectivity-checks",
                    "resource-analysis"
                ]
            }
        }
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling with troubleshooting guidance"""
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
                        "Check Kubernetes cluster connectivity: kubectl cluster-info",
                        "Verify agent deployment status: kubectl get pods -n ai-infrastructure",
                        "Validate debugging parameters",
                        "Check required tool availability: kubectl, jq, curl",
                        "Verify RBAC permissions for debugging operations"
                    ],
                    "common_solutions": [
                        "Ensure kubectl is configured correctly",
                        "Check if namespace exists and is accessible",
                        "Verify agent labels and selectors",
                        "Check network policies blocking access",
                        "Review recent events for issues"
                    ]
                }
            }
        }

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Parse parameters
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            logger.error("Invalid JSON parameters")
            sys.exit(1)
    else:
        # Default parameters for testing
        params = {
            'operation': 'diagnose',
            'targetAgent': 'all',
            'namespace': 'ai-infrastructure',
            'debugLevel': 'medium'
        }
    
    # Execute debugging
    debugger = AIAgentDebugger()
    result = debugger.execute_debugging(params)
    
    # Output result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
