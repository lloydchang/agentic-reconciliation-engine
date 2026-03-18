#!/usr/bin/env python3
"""
Cluster Scanner for K8sGPT Analyzer
Discovers and analyzes Kubernetes resources across clusters
"""

import json
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import yaml

class ClusterScanner:
    """Multi-cluster resource discovery and analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def scan_cluster(self, scope: str = 'cluster', namespace: Optional[str] = None) -> Dict[str, Any]:
        """Scan Kubernetes cluster for resources and issues"""
        try:
            scan_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'scope': scope,
                'namespace': namespace,
                'cluster_info': self._get_cluster_info(),
                'resources': {},
                'issues': [],
                'metrics': {}
            }
            
            # Get basic cluster metrics
            scan_result['metrics'] = self._get_cluster_metrics()
            
            # Scan resources based on scope
            if scope == 'cluster':
                scan_result['resources'] = self._scan_all_resources()
            elif scope == 'namespace':
                if not namespace:
                    raise ValueError("Namespace required for namespace scope")
                scan_result['resources'] = self._scan_namespace_resources(namespace)
            else:
                scan_result['resources'] = self._scan_specific_resources(scope)
            
            # Identify potential issues
            scan_result['issues'] = self._identify_issues(scan_result['resources'])
            
            return scan_result
            
        except Exception as e:
            self.logger.error(f"Cluster scan failed: {e}")
            raise
    
    def _get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information"""
        try:
            info = {}
            
            # Get current context
            try:
                result = subprocess.run(
                    ['kubectl', 'config', 'current-context'],
                    capture_output=True, text=True, check=True
                )
                info['current_context'] = result.stdout.strip()
            except subprocess.CalledProcessError:
                info['current_context'] = 'unknown'
            
            # Get cluster info
            try:
                result = subprocess.run(
                    ['kubectl', 'cluster-info'],
                    capture_output=True, text=True, check=True
                )
                info['cluster_info'] = result.stdout.strip()
            except subprocess.CalledProcessError:
                info['cluster_info'] = 'unavailable'
            
            # Get version info
            try:
                result = subprocess.run(
                    ['kubectl', 'version', '--short'],
                    capture_output=True, text=True, check=True
                )
                info['version'] = result.stdout.strip()
            except subprocess.CalledProcessError:
                info['version'] = 'unavailable'
            
            return info
            
        except Exception as e:
            self.logger.warning(f"Failed to get cluster info: {e}")
            return {'error': str(e)}
    
    def _get_cluster_metrics(self) -> Dict[str, Any]:
        """Get cluster resource metrics"""
        metrics = {}
        
        try:
            # Node information
            result = subprocess.run(
                ['kubectl', 'get', 'nodes', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            nodes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            metrics['node_count'] = len([n for n in nodes if n.strip()])
            
            # Namespace count
            result = subprocess.run(
                ['kubectl', 'get', 'namespaces', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            namespaces = result.stdout.strip().split('\n') if result.stdout.strip() else []
            metrics['namespace_count'] = len([n for n in namespaces if n.strip()])
            
            # Pod counts
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '--all-namespaces', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            pods = result.stdout.strip().split('\n') if result.stdout.strip() else []
            total_pods = len([p for p in pods if p.strip()])
            
            # Count by status
            status_counts = {}
            for pod_line in pods:
                if not pod_line.strip():
                    continue
                parts = pod_line.split()
                if len(parts) >= 4:
                    status = parts[3]
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            metrics['pod_counts'] = {
                'total': total_pods,
                'by_status': status_counts
            }
            
            # Service counts
            result = subprocess.run(
                ['kubectl', 'get', 'services', '--all-namespaces', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            metrics['service_count'] = len([s for s in services if s.strip()])
            
            # Deployment counts
            result = subprocess.run(
                ['kubectl', 'get', 'deployments', '--all-namespaces', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            deployments = result.stdout.strip().split('\n') if result.stdout.strip() else []
            metrics['deployment_count'] = len([d for d in deployments if d.strip()])
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to get cluster metrics: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _scan_all_resources(self) -> Dict[str, Any]:
        """Scan all resources in the cluster"""
        resources = {}
        
        # Common resource types to scan
        resource_types = [
            'pods', 'services', 'deployments', 'replicasets', 'statefulsets',
            'daemonsets', 'configmaps', 'secrets', 'persistentvolumes',
            'persistentvolumeclaims', 'ingresses', 'networkpolicies',
            'resourcequotas', 'limitranges', 'horizontalpodautoscalers'
        ]
        
        for resource_type in resource_types:
            try:
                resources[resource_type] = self._get_resource_info(resource_type, '--all-namespaces')
            except Exception as e:
                self.logger.warning(f"Failed to scan {resource_type}: {e}")
                resources[resource_type] = {'error': str(e)}
        
        return resources
    
    def _scan_namespace_resources(self, namespace: str) -> Dict[str, Any]:
        """Scan resources in a specific namespace"""
        resources = {}
        
        # Common resource types to scan
        resource_types = [
            'pods', 'services', 'deployments', 'replicasets', 'statefulsets',
            'daemonsets', 'configmaps', 'secrets', 'persistentvolumeclaims',
            'ingresses', 'networkpolicies', 'horizontalpodautoscalers'
        ]
        
        for resource_type in resource_types:
            try:
                resources[resource_type] = self._get_resource_info(resource_type, f'--namespace={namespace}')
            except Exception as e:
                self.logger.warning(f"Failed to scan {resource_type} in {namespace}: {e}")
                resources[resource_type] = {'error': str(e)}
        
        return resources
    
    def _scan_specific_resources(self, resource_filter: str) -> Dict[str, Any]:
        """Scan specific resources based on filter"""
        resources = {}
        
        try:
            # Try to parse the filter (e.g., "pods", "core/deployment/my-app", "namespace/pods")
            if '/' in resource_filter:
                parts = resource_filter.split('/')
                if len(parts) == 2:
                    resource_type, resource_name = parts
                    resources[resource_type] = self._get_specific_resource(resource_type, resource_name)
                else:
                    # Assume it's a namespace/resource format
                    namespace, resource_type = parts[0], parts[1]
                    resources[resource_type] = self._get_resource_info(resource_type, f'--namespace={namespace}')
            else:
                # Single resource type
                resources[resource_filter] = self._get_resource_info(resource_filter, '--all-namespaces')
                
        except Exception as e:
            self.logger.error(f"Failed to scan specific resources: {e}")
            resources['error'] = str(e)
        
        return resources
    
    def _get_resource_info(self, resource_type: str, namespace_flag: str) -> Dict[str, Any]:
        """Get information about a specific resource type"""
        try:
            # Get basic resource list
            result = subprocess.run(
                ['kubectl', 'get', resource_type, namespace_flag, '-o', 'json'],
                capture_output=True, text=True, check=True
            )
            
            data = json.loads(result.stdout)
            
            resource_info = {
                'items': data.get('items', []),
                'count': len(data.get('items', [])),
                'api_version': data.get('apiVersion', 'unknown'),
                'kind': data.get('kind', 'unknown')
            }
            
            # Add detailed analysis for common resource types
            if resource_type == 'pods':
                resource_info['analysis'] = self._analyze_pods(data.get('items', []))
            elif resource_type == 'deployments':
                resource_info['analysis'] = self._analyze_deployments(data.get('items', []))
            elif resource_type == 'services':
                resource_info['analysis'] = self._analyze_services(data.get('items', []))
            elif resource_type == 'nodes':
                resource_info['analysis'] = self._analyze_nodes(data.get('items', []))
            
            return resource_info
            
        except subprocess.CalledProcessError as e:
            return {'error': f"Failed to get {resource_type}: {e.stderr}"}
    
    def _get_specific_resource(self, resource_type: str, resource_name: str) -> Dict[str, Any]:
        """Get information about a specific resource"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', resource_type, resource_name, '-o', 'json'],
                capture_output=True, text=True, check=True
            )
            
            data = json.loads(result.stdout)
            
            return {
                'item': data,
                'name': resource_name,
                'namespace': data.get('metadata', {}).get('namespace', 'default'),
                'api_version': data.get('apiVersion', 'unknown'),
                'kind': data.get('kind', 'unknown')
            }
            
        except subprocess.CalledProcessError as e:
            return {'error': f"Failed to get {resource_type}/{resource_name}: {e.stderr}"}
    
    def _analyze_pods(self, pods: List[Dict]) -> Dict[str, Any]:
        """Analyze pod resources for issues"""
        analysis = {
            'status_counts': {},
            'restart_counts': {},
            'image_pull_issues': [],
            'resource_issues': [],
            'networking_issues': []
        }
        
        for pod in pods:
            status = pod.get('status', {})
            metadata = pod.get('metadata', {})
            spec = pod.get('spec', {})
            
            # Status analysis
            phase = status.get('phase', 'Unknown')
            analysis['status_counts'][phase] = analysis['status_counts'].get(phase, 0) + 1
            
            # Restart analysis
            for container_status in status.get('containerStatuses', []):
                restart_count = container_status.get('restartCount', 0)
                if restart_count > 0:
                    container_name = container_status.get('name', 'unknown')
                    analysis['restart_counts'][container_name] = restart_count
                
                # Image pull issues
                if container_status.get('state', {}).get('waiting', {}).get('reason') == 'ImagePullBackOff':
                    analysis['image_pull_issues'].append({
                        'pod': metadata.get('name'),
                        'container': container_status.get('name'),
                        'namespace': metadata.get('namespace')
                    })
            
            # Resource issues
            if status.get('phase') == 'Pending':
                for condition in status.get('conditions', []):
                    if condition.get('type') == 'PodScheduled' and condition.get('reason') == 'Unschedulable':
                        analysis['resource_issues'].append({
                            'pod': metadata.get('name'),
                            'namespace': metadata.get('namespace'),
                            'reason': 'Unschedulable'
                        })
            
            # Networking issues
            for container_status in status.get('containerStatuses', []):
                if not container_status.get('ready', False):
                    state = container_status.get('state', {})
                    if 'waiting' in state and state['waiting'].get('reason') in ['CrashLoopBackOff', 'Error']:
                        analysis['networking_issues'].append({
                            'pod': metadata.get('name'),
                            'container': container_status.get('name'),
                            'namespace': metadata.get('namespace'),
                            'reason': state['waiting'].get('reason')
                        })
        
        return analysis
    
    def _analyze_deployments(self, deployments: List[Dict]) -> Dict[str, Any]:
        """Analyze deployment resources for issues"""
        analysis = {
            'replica_issues': [],
            'update_issues': [],
            'readiness_issues': []
        }
        
        for deployment in deployments:
            metadata = deployment.get('metadata', {})
            status = deployment.get('status', {})
            spec = deployment.get('spec', {})
            
            name = metadata.get('name')
            namespace = metadata.get('namespace')
            
            # Replica issues
            replicas = spec.get('replicas', 0)
            available_replicas = status.get('availableReplicas', 0)
            ready_replicas = status.get('readyReplicas', 0)
            
            if available_replicas < replicas:
                analysis['replica_issues'].append({
                    'deployment': name,
                    'namespace': namespace,
                    'desired': replicas,
                    'available': available_replicas,
                    'ready': ready_replicas
                })
            
            # Update issues
            if status.get('updatedReplicas', 0) < replicas:
                analysis['update_issues'].append({
                    'deployment': name,
                    'namespace': namespace,
                    'desired': replicas,
                    'updated': status.get('updatedReplicas', 0)
                })
            
            # Readiness issues
            conditions = status.get('conditions', [])
            for condition in conditions:
                if condition.get('type') == 'Progressing' and condition.get('status') != 'True':
                    analysis['readiness_issues'].append({
                        'deployment': name,
                        'namespace': namespace,
                        'condition': 'Progressing',
                        'status': condition.get('status'),
                        'reason': condition.get('reason')
                    })
        
        return analysis
    
    def _analyze_services(self, services: List[Dict]) -> Dict[str, Any]:
        """Analyze service resources for issues"""
        analysis = {
            'endpoint_issues': [],
            'type_distribution': {},
            'port_conflicts': []
        }
        
        for service in services:
            metadata = service.get('metadata', {})
            spec = service.get('spec', {})
            
            name = metadata.get('name')
            namespace = metadata.get('namespace')
            
            # Type distribution
            service_type = spec.get('type', 'ClusterIP')
            analysis['type_distribution'][service_type] = analysis['type_distribution'].get(service_type, 0) + 1
            
            # Endpoint issues (would need additional API calls to fully check)
            # This is a placeholder for more comprehensive endpoint checking
            
        return analysis
    
    def _analyze_nodes(self, nodes: List[Dict]) -> Dict[str, Any]:
        """Analyze node resources for issues"""
        analysis = {
            'status_counts': {},
            'resource_pressure': [],
            'version_distribution': {}
        }
        
        for node in nodes:
            metadata = node.get('metadata', {})
            status = node.get('status', {})
            
            name = metadata.get('name')
            
            # Status analysis
            conditions = status.get('conditions', [])
            node_ready = False
            for condition in conditions:
                if condition.get('type') == 'Ready':
                    node_ready = condition.get('status') == 'True'
                    break
            
            status_key = 'Ready' if node_ready else 'NotReady'
            analysis['status_counts'][status_key] = analysis['status_counts'].get(status_key, 0) + 1
            
            # Resource pressure
            for condition in conditions:
                if condition.get('type') in ['MemoryPressure', 'DiskPressure', 'PIDPressure']:
                    if condition.get('status') == 'True':
                        analysis['resource_pressure'].append({
                            'node': name,
                            'condition': condition.get('type'),
                            'status': condition.get('status')
                        })
            
            # Version distribution
            version = metadata.get('labels', {}).get('kubernetes.io/os', 'unknown')
            analysis['version_distribution'][version] = analysis['version_distribution'].get(version, 0) + 1
        
        return analysis
    
    def _identify_issues(self, resources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues across all scanned resources"""
        issues = []
        
        for resource_type, resource_data in resources.items():
            if isinstance(resource_data, dict) and 'analysis' in resource_data:
                analysis = resource_data['analysis']
                
                # Check for common issue patterns
                if 'restart_counts' in analysis and analysis['restart_counts']:
                    for container, count in analysis['restart_counts'].items():
                        if count > 5:  # High restart threshold
                            issues.append({
                                'type': 'high_restarts',
                                'severity': 'warning',
                                'resource_type': resource_type,
                                'details': f'Container {container} has restarted {count} times'
                            })
                
                if 'replica_issues' in analysis and analysis['replica_issues']:
                    for replica_issue in analysis['replica_issues']:
                        issues.append({
                            'type': 'replica_mismatch',
                            'severity': 'error',
                            'resource_type': resource_type,
                            'details': f"Deployment {replica_issue['deployment']}/{replica_issue['namespace']} has {replica_issue['available']}/{replica_issue['desired']} replicas available"
                        })
                
                if 'image_pull_issues' in analysis and analysis['image_pull_issues']:
                    for image_issue in analysis['image_pull_issues']:
                        issues.append({
                            'type': 'image_pull_failure',
                            'severity': 'error',
                            'resource_type': resource_type,
                            'details': f"Pod {image_issue['pod']}/{image_issue['namespace']} container {image_issue['container']} has ImagePullBackOff"
                        })
        
        return issues

def main():
    """CLI interface for cluster scanning"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cluster Scanner for K8sGPT')
    parser.add_argument('--scope', default='cluster',
                       choices=['cluster', 'namespace'],
                       help='Scan scope')
    parser.add_argument('--namespace', help='Namespace to scan (required for namespace scope)')
    parser.add_argument('--output', choices=['json', 'yaml'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    scanner = ClusterScanner()
    
    try:
        result = scanner.scan_cluster(args.scope, args.namespace)
        
        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(yaml.dump(result, default_flow_style=False))
            
    except Exception as e:
        print(f"Scan failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
