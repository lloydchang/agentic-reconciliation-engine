#!/usr/bin/env python3
# /// script
# dependencies = [
#   "kubernetes>=25.0.0",
#   "requests>=2.28.0",
#   "pydantic>=1.10.0",
#   "temporalio>=1.0.0"
# ]
# ///

"""
Debug utilities for AI system debugging
Common functions and helpers for distributed system debugging
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import subprocess
import logging

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

try:
    from temporalio import service
    TEMPORAL_AVAILABLE = True
except ImportError:
    TEMPORAL_AVAILABLE = False

class SystemDebugger:
    """Advanced debugging utilities for distributed AI systems"""
    
    def __init__(self, namespace: str = "temporal", kubeconfig: Optional[str] = None):
        self.namespace = namespace
        self.kubeconfig = kubeconfig
        self.logger = self._setup_logger()
        
        # Initialize clients
        self.k8s_client = None
        self.temporal_client = None
        
        if K8S_AVAILABLE:
            try:
                if kubeconfig:
                    config.load_kube_config(config_file=kubeconfig)
                else:
                    config.load_incluster_config()
                self.k8s_client = client.CoreV1Api()
                self.logger.info("Kubernetes client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Kubernetes client: {e}")
        
        if TEMPORAL_AVAILABLE:
            try:
                # Temporal client initialization would go here
                self.logger.info("Temporal client available")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Temporal client: {e}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logging"""
        logger = logging.getLogger("ai_debugger")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def collect_system_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "time_range": time_range,
            "kubernetes": {},
            "temporal": {},
            "monitoring": {}
        }
        
        # Kubernetes metrics
        if self.k8s_client:
            metrics["kubernetes"] = await self._collect_k8s_metrics(time_range)
        
        # Temporal metrics
        metrics["temporal"] = await self._collect_temporal_metrics(time_range)
        
        # Monitoring API metrics
        metrics["monitoring"] = await self._collect_monitoring_metrics()
        
        return metrics
    
    async def _collect_k8s_metrics(self, time_range: str) -> Dict[str, Any]:
        """Collect Kubernetes-specific metrics"""
        if not self.k8s_client:
            return {"error": "Kubernetes client not available"}
        
        try:
            # Pod metrics
            pods = self.k8s_client.list_namespaced_pod(self.namespace)
            pod_metrics = {
                "total": len(pods.items),
                "running": len([p for p in pods.items if p.status.phase == "Running"]),
                "failed": len([p for p in pods.items if p.status.phase == "Failed"]),
                "pending": len([p for p in pods.items if p.status.phase == "Pending"]),
                "details": []
            }
            
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "restart_count": sum(
                        container.restart_count or 0 
                        for container in (pod.status.container_statuses or [])
                    ),
                    "node": pod.spec.node_name,
                    "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                }
                pod_metrics["details"].append(pod_info)
            
            # Node metrics
            nodes = self.k8s_client.list_node()
            node_metrics = {
                "total": len(nodes.items),
                "ready": len([n for n in nodes.items 
                             if any(c.type == "Ready" and c.status == "True" 
                                   for c in n.status.conditions)]),
                "details": []
            }
            
            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "ready": any(c.type == "Ready" and c.status == "True" 
                                for c in node.status.conditions),
                    "capacity": node.status.capacity if node.status.capacity else {},
                    "allocatable": node.status.allocatable if node.status.allocatable else {}
                }
                node_metrics["details"].append(node_info)
            
            return {
                "pods": pod_metrics,
                "nodes": node_metrics,
                "namespace": self.namespace
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect K8s metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_temporal_metrics(self, time_range: str) -> Dict[str, Any]:
        """Collect Temporal workflow metrics"""
        try:
            # This would connect to Temporal API
            # For now, return placeholder structure
            return {
                "workflows": {
                    "total": 0,
                    "running": 0,
                    "completed": 0,
                    "failed": 0
                },
                "activities": {
                    "total": 0,
                    "running": 0,
                    "completed": 0,
                    "failed": 0
                },
                "task_queues": {}
            }
        except Exception as e:
            self.logger.error(f"Failed to collect Temporal metrics: {e}")
            return {"error": str(e)}
    
    async def _collect_monitoring_metrics(self) -> Dict[str, Any]:
        """Collect metrics from monitoring API"""
        if not REQUESTS_AVAILABLE:
            return {"error": "Requests library not available"}
        
        try:
            base_url = f"http://temporal-worker.{self.namespace}.svc.cluster.local:8080"
            endpoints = [
                "/monitoring/metrics",
                "/monitoring/alerts",
                "/health"
            ]
            
            results = {}
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        results[endpoint.replace("/", "_").strip("_")] = response.json()
                    else:
                        results[endpoint.replace("/", "_").strip("_")] = {
                            "error": f"HTTP {response.status_code}"
                        }
                except Exception as e:
                    results[endpoint.replace("/", "_").strip("_")] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to collect monitoring metrics: {e}")
            return {"error": str(e)}
    
    async def analyze_logs(self, component: str, time_range: str = "1h") -> Dict[str, Any]:
        """Analyze logs for specific component"""
        log_analysis = {
            "component": component,
            "time_range": time_range,
            "error_patterns": [],
            "warning_patterns": [],
            "performance_issues": [],
            "summary": {}
        }
        
        try:
            # Parse time range
            time_delta = self._parse_time_range(time_range)
            
            # Get logs based on component
            if component == "agents":
                logs = await self._get_agent_logs(time_delta)
            elif component == "workflows":
                logs = await self._get_workflow_logs(time_delta)
            elif component == "infrastructure":
                logs = await self._get_infrastructure_logs(time_delta)
            else:
                logs = []
            
            # Analyze log patterns
            log_analysis["error_patterns"] = self._find_error_patterns(logs)
            log_analysis["warning_patterns"] = self._find_warning_patterns(logs)
            log_analysis["performance_issues"] = self._find_performance_patterns(logs)
            
            # Generate summary
            log_analysis["summary"] = {
                "total_lines": len(logs),
                "error_count": len(log_analysis["error_patterns"]),
                "warning_count": len(log_analysis["warning_patterns"]),
                "performance_issues": len(log_analysis["performance_issues"])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze logs for {component}: {e}")
            log_analysis["error"] = str(e)
        
        return log_analysis
    
    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string into timedelta"""
        unit = time_range[-1]
        value = int(time_range[:-1])
        
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        else:
            raise ValueError(f"Invalid time range format: {time_range}")
    
    async def _get_agent_logs(self, time_delta: timedelta) -> List[str]:
        """Get agent-related logs"""
        try:
            # Use kubectl to get logs
            cmd = [
                "kubectl", "logs", 
                f"--since={int(time_delta.total_seconds())}s",
                "-n", self.namespace,
                "deployment/temporal-worker"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                self.logger.error(f"Failed to get agent logs: {result.stderr}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting agent logs: {e}")
            return []
    
    async def _get_workflow_logs(self, time_delta: timedelta) -> List[str]:
        """Get workflow-related logs"""
        # Similar to agent logs but focused on temporal-server
        try:
            cmd = [
                "kubectl", "logs",
                f"--since={int(time_delta.total_seconds())}s",
                "-n", self.namespace,
                "deployment/temporal-server"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting workflow logs: {e}")
            return []
    
    async def _get_infrastructure_logs(self, time_delta: timedelta) -> List[str]:
        """Get infrastructure-related logs"""
        # This could pull from various sources
        return []
    
    def _find_error_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Find error patterns in logs"""
        error_patterns = []
        error_keywords = ["ERROR", "FATAL", "CRITICAL", "PANIC", "EXCEPTION"]
        
        for i, log_line in enumerate(logs):
            for keyword in error_keywords:
                if keyword in log_line.upper():
                    error_patterns.append({
                        "line_number": i,
                        "pattern": keyword,
                        "message": log_line.strip(),
                        "timestamp": self._extract_timestamp(log_line)
                    })
                    break
        
        return error_patterns
    
    def _find_warning_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Find warning patterns in logs"""
        warning_patterns = []
        warning_keywords = ["WARNING", "WARN", "DEPRECATED"]
        
        for i, log_line in enumerate(logs):
            for keyword in warning_keywords:
                if keyword in log_line.upper():
                    warning_patterns.append({
                        "line_number": i,
                        "pattern": keyword,
                        "message": log_line.strip(),
                        "timestamp": self._extract_timestamp(log_line)
                    })
                    break
        
        return warning_patterns
    
    def _find_performance_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Find performance-related patterns in logs"""
        performance_patterns = []
        perf_keywords = ["timeout", "slow", "latency", "bottleneck", "oom"]
        
        for i, log_line in enumerate(logs):
            for keyword in perf_keywords:
                if keyword in log_line.lower():
                    performance_patterns.append({
                        "line_number": i,
                        "pattern": keyword,
                        "message": log_line.strip(),
                        "timestamp": self._extract_timestamp(log_line)
                    })
                    break
        
        return performance_patterns
    
    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Simple timestamp extraction - could be enhanced
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, log_line)
        return match.group() if match else None
    
    async def generate_debug_report(self, target_component: str, issue_type: str, 
                                  time_range: str) -> Dict[str, Any]:
        """Generate comprehensive debug report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "target_component": target_component,
            "issue_type": issue_type,
            "time_range": time_range,
            "system_metrics": await self.collect_system_metrics(time_range),
            "log_analysis": await self.analyze_logs(target_component, time_range),
            "recommendations": []
        }
        
        # Generate recommendations based on analysis
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Analyze system metrics
        k8s_metrics = report.get("system_metrics", {}).get("kubernetes", {})
        if "pods" in k8s_metrics:
            pod_metrics = k8s_metrics["pods"]
            if pod_metrics.get("failed", 0) > 0:
                recommendations.append("Investigate failed pods and restart if necessary")
            if pod_metrics.get("pending", 0) > 0:
                recommendations.append("Check resource quotas and node availability for pending pods")
        
        # Analyze log patterns
        log_analysis = report.get("log_analysis", {})
        error_count = log_analysis.get("summary", {}).get("error_count", 0)
        if error_count > 10:
            recommendations.append("High error rate detected - review application logs and fix root causes")
        
        # Component-specific recommendations
        component = report.get("target_component")
        if component == "agents":
            recommendations.extend([
                "Monitor agent execution patterns",
                "Check skill configurations",
                "Review resource allocation for agent pods"
            ])
        elif component == "workflows":
            recommendations.extend([
                "Check workflow timeouts",
                "Review activity configurations",
                "Monitor task queue health"
            ])
        elif component == "infrastructure":
            recommendations.extend([
                "Monitor node health",
                "Check resource utilization",
                "Review network connectivity"
            ])
        
        return recommendations

# Utility functions for external use
async def quick_debug(component: str, namespace: str = "temporal", 
                    time_range: str = "1h") -> Dict[str, Any]:
    """Quick debug function for external usage"""
    debugger = SystemDebugger(namespace=namespace)
    return await debugger.generate_debug_report(
        target_component=component,
        issue_type="general",
        time_range=time_range
    )

def save_debug_report(report: Dict[str, Any], output_path: str):
    """Save debug report to file"""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        debugger = SystemDebugger()
        report = await debugger.generate_debug_report(
            target_component="agents",
            issue_type="performance",
            time_range="1h"
        )
        print(json.dumps(report, indent=2, default=str))
    
    asyncio.run(main())
