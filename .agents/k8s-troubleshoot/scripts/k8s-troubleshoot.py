#!/usr/bin/env python3
"""
Kubernetes Troubleshooting Script
Diagnoses and troubleshoots Kubernetes workload failures and cluster issues.
"""

import json
import subprocess
import sys
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter


class K8sTroubleshooter:
    def __init__(self, cluster_context: str = "default"):
        self.cluster_context = cluster_context
        self.common_failure_patterns = {
            'CrashLoopBackOff': {
                'category': 'container_failure',
                'causes': ['Application crash', 'Configuration error', 'Resource limits'],
                'diagnostics': ['kubectl logs', 'kubectl describe pod'],
                'remediation': ['Check application logs', 'Verify configuration', 'Adjust resources']
            },
            'ImagePullBackOff': {
                'category': 'image_issue',
                'causes': ['Invalid image name', 'Registry access', 'Authentication'],
                'diagnostics': ['kubectl describe pod', 'kubectl get events'],
                'remediation': ['Verify image name', 'Check registry access', 'Update image pull secrets']
            },
            'Pending': {
                'category': 'scheduling_issue',
                'causes': ['Insufficient resources', 'Taints/tolerations', 'Node selectors'],
                'diagnostics': ['kubectl describe pod', 'kubectl get nodes'],
                'remediation': ['Check resource usage', 'Verify node affinity', 'Scale cluster']
            },
            'Terminating': {
                'category': 'termination_issue',
                'causes': ['Finalizer stuck', 'Force deletion needed', 'Resource cleanup'],
                'diagnostics': ['kubectl describe pod', 'kubectl get events'],
                'remediation': ['Check finalizers', 'Force delete if needed', 'Verify cleanup']
            },
            'ErrImagePull': {
                'category': 'image_issue',
                'causes': ['Network connectivity', 'Image not found', 'Registry error'],
                'diagnostics': ['kubectl describe pod', 'docker pull test'],
                'remediation': ['Check network', 'Verify image exists', 'Test registry access']
            },
            'RunContainerError': {
                'category': 'runtime_error',
                'causes': ['Port conflicts', 'Volume mounts', 'Security context'],
                'diagnostics': ['kubectl logs', 'kubectl describe pod'],
                'remediation': ['Check port configuration', 'Verify volumes', 'Review security policies']
            }
        }
    
    def get_pod_info(self, pod_name: str, namespace: str = "default") -> Dict:
        """Get comprehensive pod information"""
        try:
            # Get pod details
            describe_cmd = ['kubectl', 'describe', 'pod', pod_name, '-n', namespace]
            describe_result = subprocess.run(describe_cmd, capture_output=True, text=True, timeout=30)
            
            # Get pod logs
            logs_cmd = ['kubectl', 'logs', pod_name, '-n', namespace, '--tail=50']
            logs_result = subprocess.run(logs_cmd, capture_output=True, text=True, timeout=30)
            
            # Get pod events
            events_cmd = ['kubectl', 'get', 'events', '-n', namespace, '--field-selector', f'involvedObject.name={pod_name}']
            events_result = subprocess.run(events_cmd, capture_output=True, text=True, timeout=30)
            
            # Parse pod status
            status_cmd = ['kubectl', 'get', 'pod', pod_name, '-n', namespace, '-o', 'json']
            status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=30)
            
            pod_data = {}
            if status_result.returncode == 0:
                pod_data = json.loads(status_result.stdout)
            
            return {
                'pod_name': pod_name,
                'namespace': namespace,
                'describe_output': describe_result.stdout,
                'logs_output': logs_result.stdout,
                'events_output': events_result.stdout,
                'pod_data': pod_data,
                'status': self._extract_pod_status(pod_data),
                'errors': [describe_result.stderr, logs_result.stderr, events_result.stderr]
            }
            
        except Exception as e:
            return {
                'pod_name': pod_name,
                'namespace': namespace,
                'error': str(e),
                'status': 'error'
            }
    
    def _extract_pod_status(self, pod_data: Dict) -> Dict:
        """Extract detailed pod status information"""
        if not pod_data or 'status' not in pod_data:
            return {'phase': 'Unknown'}
        
        status = pod_data['status']
        container_statuses = []
        
        for container_status in status.get('containerStatuses', []):
            container_info = {
                'name': container_status.get('name', ''),
                'ready': container_status.get('ready', False),
                'restart_count': container_status.get('restartCount', 0),
                'state': list(container_status.get('state', {}).keys())[0] if container_status.get('state') else 'unknown',
                'waiting_reason': container_status.get('state', {}).get('waiting', {}).get('reason', ''),
                'terminated_reason': container_status.get('state', {}).get('terminated', {}).get('reason', '')
            }
            container_statuses.append(container_info)
        
        return {
            'phase': status.get('phase', 'Unknown'),
            'pod_ip': status.get('podIP', ''),
            'node_name': status.get('nodeName', ''),
            'start_time': status.get('startTime', ''),
            'container_statuses': container_statuses,
            'conditions': status.get('conditions', [])
        }
    
    def analyze_pod_failure(self, pod_info: Dict) -> Dict:
        """Analyze pod failure and identify root causes"""
        pod_name = pod_info.get('pod_name', '')
        status = pod_info.get('status', {})
        container_statuses = status.get('container_statuses', [])
        
        # Identify failure patterns
        failure_patterns = []
        for container in container_statuses:
            state = container.get('state', '')
            waiting_reason = container.get('waiting_reason', '')
            terminated_reason = container.get('terminated_reason', '')
            
            if waiting_reason in self.common_failure_patterns:
                pattern = self.common_failure_patterns[waiting_reason]
                failure_patterns.append({
                    'container': container.get('name', ''),
                    'pattern': waiting_reason,
                    'category': pattern['category'],
                    'potential_causes': pattern['causes'],
                    'restart_count': container.get('restart_count', 0)
                })
            elif terminated_reason in self.common_failure_patterns:
                pattern = self.common_failure_patterns[terminated_reason]
                failure_patterns.append({
                    'container': container.get('name', ''),
                    'pattern': terminated_reason,
                    'category': pattern['category'],
                    'potential_causes': pattern['causes'],
                    'restart_count': container.get('restart_count', 0)
                })
            elif state == 'waiting' and waiting_reason:
                # Handle unknown waiting reasons
                failure_patterns.append({
                    'container': container.get('name', ''),
                    'pattern': waiting_reason,
                    'category': 'unknown_waiting',
                    'potential_causes': ['Resource scheduling', 'Dependency issues', 'Configuration error'],
                    'restart_count': container.get('restart_count', 0)
                })
        
        # Analyze logs for error patterns
        log_analysis = self._analyze_logs(pod_info.get('logs_output', ''))
        
        # Analyze events for issues
        event_analysis = self._analyze_events(pod_info.get('events_output', ''))
        
        # Generate diagnostic commands
        diagnostic_commands = self._generate_diagnostic_commands(pod_name, pod_info.get('namespace', 'default'))
        
        # Generate remediation steps
        remediation_steps = self._generate_remediation_steps(failure_patterns, log_analysis, event_analysis)
        
        return {
            'pod_name': pod_name,
            'namespace': pod_info.get('namespace', ''),
            'status_phase': status.get('phase', 'Unknown'),
            'failure_patterns': failure_patterns,
            'log_analysis': log_analysis,
            'event_analysis': event_analysis,
            'diagnostic_commands': diagnostic_commands,
            'remediation_steps': remediation_steps,
            'severity': self._calculate_severity(failure_patterns, status),
            'estimated_resolution_time': self._estimate_resolution_time(failure_patterns)
        }
    
    def _analyze_logs(self, logs_output: str) -> Dict:
        """Analyze pod logs for error patterns"""
        if not logs_output:
            return {'error': 'No logs available'}
        
        log_patterns = {
            'OutOfMemoryError': 'memory_exhaustion',
            'Connection refused': 'network_issue',
            'Permission denied': 'permission_error',
            'File not found': 'file_missing',
            'Timeout': 'timeout_error',
            'Exception': 'application_error',
            'Error': 'general_error'
        }
        
        found_patterns = []
        for pattern, category in log_patterns.items():
            if pattern in logs_output:
                found_patterns.append({
                    'pattern': pattern,
                    'category': category,
                    'count': logs_output.count(pattern)
                })
        
        # Extract recent errors (last 10 lines)
        lines = logs_output.strip().split('\n')
        recent_errors = [line for line in lines[-10:] if any(error in line for error in ['Error', 'Exception', 'Failed'])]
        
        return {
            'patterns_found': found_patterns,
            'recent_errors': recent_errors,
            'total_lines': len(lines),
            'has_errors': len(found_patterns) > 0 or len(recent_errors) > 0
        }
    
    def _analyze_events(self, events_output: str) -> Dict:
        """Analyze Kubernetes events for issues"""
        if not events_output:
            return {'error': 'No events available'}
        
        lines = events_output.strip().split('\n')[1:]  # Skip header
        events = []
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = re.split(r'\s+', line)
            if len(parts) >= 6:
                events.append({
                    'timestamp': parts[0] + ' ' + parts[1],
                    'type': parts[2],
                    'reason': parts[3],
                    'object': parts[4],
                    'message': ' '.join(parts[5:])
                })
        
        # Categorize events
        warning_events = [e for e in events if e['type'] == 'Warning']
        error_events = [e for e in events if 'Error' in e['reason'] or 'Failed' in e['reason']]
        
        # Common event patterns
        event_patterns = Counter([e['reason'] for e in warning_events])
        
        return {
            'total_events': len(events),
            'warning_events': len(warning_events),
            'error_events': len(error_events),
            'common_patterns': dict(event_patterns.most_common(5)),
            'recent_warnings': warning_events[-5:] if warning_events else []
        }
    
    def _generate_diagnostic_commands(self, pod_name: str, namespace: str) -> List[Dict]:
        """Generate diagnostic commands for troubleshooting"""
        commands = [
            {
                'purpose': 'Check pod status',
                'command': f'kubectl get pod {pod_name} -n {namespace} -o wide',
                'description': 'Get current pod status and node information'
            },
            {
                'purpose': 'Get detailed pod information',
                'command': f'kubectl describe pod {pod_name} -n {namespace}',
                'description': 'Get detailed pod configuration and events'
            },
            {
                'purpose': 'Check pod logs',
                'command': f'kubectl logs {pod_name} -n {namespace} --tail=100',
                'description': 'Get recent pod logs for error analysis'
            },
            {
                'purpose': 'Check previous container logs',
                'command': f'kubectl logs {pod_name} -n {namespace} -p',
                'description': 'Get logs from previous container instance'
            },
            {
                'purpose': 'Check namespace events',
                'command': f'kubectl get events -n {namespace} --sort-by=.metadata.creationTimestamp',
                'description': 'Get recent events in the namespace'
            },
            {
                'purpose': 'Check node status',
                'command': f'kubectl get nodes -o wide',
                'description': 'Check cluster node status'
            },
            {
                'purpose': 'Check resource usage',
                'command': f'kubectl top pods -n {namespace}',
                'description': 'Check pod resource usage'
            }
        ]
        
        return commands
    
    def _generate_remediation_steps(self, failure_patterns: List[Dict], log_analysis: Dict, event_analysis: Dict) -> List[Dict]:
        """Generate remediation steps based on analysis"""
        steps = []
        
        # Based on failure patterns
        for pattern in failure_patterns:
            pattern_name = pattern['pattern']
            if pattern_name in self.common_failure_patterns:
                pattern_info = self.common_failure_patterns[pattern_name]
                for remediation in pattern_info['remediation']:
                    steps.append({
                        'category': 'pattern_based',
                        'step': remediation,
                        'priority': 'high',
                        'pattern': pattern_name
                    })
        
        # Based on log analysis
        if log_analysis.get('has_errors'):
            for log_pattern in log_analysis.get('patterns_found', []):
                category = log_pattern['category']
                if category == 'memory_exhaustion':
                    steps.append({
                        'category': 'log_based',
                        'step': 'Increase memory limits or optimize memory usage',
                        'priority': 'high',
                        'evidence': f"Found {log_pattern['count']} memory errors in logs"
                    })
                elif category == 'network_issue':
                    steps.append({
                        'category': 'log_based',
                        'step': 'Check network policies and service connectivity',
                        'priority': 'medium',
                        'evidence': f"Found {log_pattern['count']} network errors in logs"
                    })
        
        # Based on event analysis
        common_patterns = event_analysis.get('common_patterns', {})
        if 'FailedScheduling' in common_patterns:
            steps.append({
                'category': 'event_based',
                'step': 'Check resource availability and node capacity',
                'priority': 'high',
                'evidence': f"Found {common_patterns['FailedScheduling']} scheduling failures"
            })
        
        # Generic remediation steps
        if not steps:
            steps = [
                {
                    'category': 'generic',
                    'step': 'Review recent configuration changes',
                    'priority': 'medium',
                    'description': 'Check for recent deployments or configuration updates'
                },
                {
                    'category': 'generic',
                    'step': 'Verify resource requirements',
                    'priority': 'medium',
                    'description': 'Ensure CPU and memory requests are appropriate'
                }
            ]
        
        return steps
    
    def _calculate_severity(self, failure_patterns: List[Dict], status: Dict) -> str:
        """Calculate issue severity"""
        if not failure_patterns:
            return 'low'
        
        # Check for critical patterns
        critical_patterns = ['CrashLoopBackOff', 'ImagePullBackOff']
        for pattern in failure_patterns:
            if pattern['pattern'] in critical_patterns:
                return 'critical'
        
        # Check restart count
        max_restarts = max([p.get('restart_count', 0) for p in failure_patterns])
        if max_restarts > 5:
            return 'high'
        elif max_restarts > 2:
            return 'medium'
        
        return 'low'
    
    def _estimate_resolution_time(self, failure_patterns: List[Dict]) -> Dict:
        """Estimate resolution time based on failure patterns"""
        if not failure_patterns:
            return {'minutes': 5, 'confidence': 'low'}
        
        # Base time estimates by pattern
        time_estimates = {
            'CrashLoopBackOff': {'minutes': 15, 'confidence': 'medium'},
            'ImagePullBackOff': {'minutes': 10, 'confidence': 'high'},
            'Pending': {'minutes': 20, 'confidence': 'medium'},
            'ErrImagePull': {'minutes': 10, 'confidence': 'high'},
            'RunContainerError': {'minutes': 15, 'confidence': 'medium'}
        }
        
        max_time = 0
        total_confidence = 0
        pattern_count = len(failure_patterns)
        
        for pattern in failure_patterns:
            pattern_name = pattern['pattern']
            if pattern_name in time_estimates:
                estimate = time_estimates[pattern_name]
                max_time = max(max_time, estimate['minutes'])
                total_confidence += estimate['confidence']
        
        avg_confidence = total_confidence / pattern_count if pattern_count > 0 else 'low'
        
        return {
            'minutes': max_time,
            'confidence': avg_confidence
        }
    
    def troubleshoot_pod(self, pod_name: str, namespace: str = "default") -> Dict:
        """Main troubleshooting function"""
        # Get pod information
        pod_info = self.get_pod_info(pod_name, namespace)
        
        if 'error' in pod_info:
            return {
                'pod_name': pod_name,
                'namespace': namespace,
                'error': pod_info['error'],
                'status': 'failed_to_get_info'
            }
        
        # Analyze failure
        analysis = self.analyze_pod_failure(pod_info)
        
        # Add metadata
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['cluster_context'] = self.cluster_context
        
        return analysis
    
    def troubleshoot_namespace(self, namespace: str = "default") -> Dict:
        """Troubleshoot all problematic pods in a namespace"""
        try:
            # Get all pods in namespace
            cmd = ['kubectl', 'get', 'pods', '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {'error': 'Failed to get pods', 'stderr': result.stderr}
            
            pod_data = json.loads(result.stdout)
            pods = pod_data.get('items', [])
            
            # Find problematic pods
            problematic_pods = []
            for pod in pods:
                pod_name = pod['metadata']['name']
                pod_phase = pod['status'].get('phase', 'Unknown')
                
                # Check for problematic states
                container_statuses = pod['status'].get('containerStatuses', [])
                has_issues = False
                
                for container in container_statuses:
                    waiting = container.get('state', {}).get('waiting', {})
                    if waiting.get('reason'):
                        has_issues = True
                        break
                
                if pod_phase != 'Running' or has_issues:
                    problematic_pods.append(pod_name)
            
            # Troubleshoot each problematic pod
            results = []
            for pod_name in problematic_pods[:10]:  # Limit to 10 pods
                result = self.troubleshoot_pod(pod_name, namespace)
                results.append(result)
            
            return {
                'namespace': namespace,
                'total_pods': len(pods),
                'problematic_pods': len(problematic_pods),
                'pod_names': problematic_pods,
                'troubleshooting_results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}


def main():
    """Example usage"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_pod.py <pod_name> [namespace]")
        print("Example: python analyze_pod.py my-pod default")
        sys.exit(1)
    
    try:
        pod_name = sys.argv[1]
        namespace = sys.argv[2] if len(sys.argv) > 2 else "default"
        
        troubleshooter = K8sTroubleshooter()
        result = troubleshooter.troubleshoot_pod(pod_name, namespace)
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
