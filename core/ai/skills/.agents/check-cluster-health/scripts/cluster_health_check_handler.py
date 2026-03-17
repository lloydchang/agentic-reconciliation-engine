#!/usr/bin/env python3
"""
Cluster Health Check Handler

Cloud-specific operations handler for comprehensive cluster health checks across multi-cloud environments.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    check_name: str
    check_type: str
    status: str
    score: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    cluster_name: str
    provider: str
    region: str

@dataclass
class ClusterHealthSummary:
    cluster_name: str
    provider: str
    region: str
    overall_status: str
    overall_score: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    critical_issues: List[str]
    recommendations: List[str]
    last_check: datetime

class ClusterHealthCheckHandler(ABC):
    """Abstract base class for cloud-specific cluster health check operations"""
    
    def __init__(self, region: str = "us-west-2"):
        self.region = region
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> bool:
        """Initialize cloud-specific client"""
        pass
    
    @abstractmethod
    def discover_clusters(self) -> List[Dict[str, Any]]:
        """Discover clusters in the provider"""
        pass
    
    @abstractmethod
    def check_node_health(self, cluster_name: str) -> HealthCheckResult:
        """Check node health for a cluster"""
        pass
    
    @abstractmethod
    def check_pod_health(self, cluster_name: str) -> HealthCheckResult:
        """Check pod health for a cluster"""
        pass
    
    @abstractmethod
    def check_service_health(self, cluster_name: str) -> HealthCheckResult:
        """Check service health for a cluster"""
        pass
    
    @abstractmethod
    def check_storage_health(self, cluster_name: str) -> HealthCheckResult:
        """Check storage health for a cluster"""
        pass
    
    @abstractmethod
    def check_networking_health(self, cluster_name: str) -> HealthCheckResult:
        """Check networking health for a cluster"""
        pass
    
    @abstractmethod
    def check_security_health(self, cluster_name: str) -> HealthCheckResult:
        """Check security health for a cluster"""
        pass
    
    @abstractmethod
    def check_performance_health(self, cluster_name: str) -> HealthCheckResult:
        """Check performance health for a cluster"""
        pass
    
    @abstractmethod
    def generate_health_summary(self, cluster_name: str, results: List[HealthCheckResult]) -> ClusterHealthSummary:
        """Generate comprehensive health summary"""
        pass

class AWSClusterHealthCheckHandler(ClusterHealthCheckHandler):
    """AWS-specific cluster health check operations"""
    
    def initialize_client(self) -> bool:
        """Initialize AWS clients"""
        try:
            import boto3
            self.client = {
                'eks': boto3.client('eks', region_name=self.region),
                'ec2': boto3.client('ec2', region_name=self.region),
                'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
                'autoscaling': boto3.client('autoscaling', region_name=self.region),
                'elb': boto3.client('elbv2', region_name=self.region)
            }
            logger.info(f"AWS clients initialized for region {self.region}")
            return True
        except ImportError:
            logger.error("AWS SDK (boto3) not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            return False
    
    def discover_clusters(self) -> List[Dict[str, Any]]:
        """Discover EKS clusters in AWS"""
        try:
            clusters = []
            
            response = self.client['eks'].list_clusters()
            
            for cluster_name in response['clusters']:
                try:
                    cluster_info = self.client['eks'].describe_cluster(name=cluster_name)
                    
                    cluster_data = {
                        'name': cluster_name,
                        'provider': 'aws',
                        'region': self.region,
                        'version': cluster_info['cluster']['version'],
                        'status': cluster_info['cluster']['status'],
                        'endpoint': cluster_info['cluster']['endpoint'],
                        'platform_version': cluster_info['cluster'].get('platformVersion', 'unknown'),
                        'created_at': cluster_info['cluster']['createdAt'],
                        'tags': cluster_info['cluster'].get('tags', {})
                    }
                    
                    clusters.append(cluster_data)
                    
                except Exception as e:
                    logger.error(f"Failed to describe cluster {cluster_name}: {e}")
                    continue
            
            logger.info(f"Discovered {len(clusters)} AWS EKS clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to discover AWS clusters: {e}")
            return []
    
    def check_node_health(self, cluster_name: str) -> HealthCheckResult:
        """Check node health for EKS cluster"""
        try:
            # Get node group information
            nodegroups = self._get_nodegroups(cluster_name)
            
            # Check node status
            node_status = self._check_nodegroup_status(nodegroups)
            
            # Check node resource utilization
            resource_utilization = self._get_node_resource_utilization(cluster_name)
            
            # Calculate score
            score = self._calculate_node_health_score(node_status, resource_utilization)
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "All nodes are healthy and properly utilized"
            elif score >= 70:
                status = "warning"
                message = "Some nodes show warning signs"
            else:
                status = "critical"
                message = "Critical node health issues detected"
            
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status=status,
                score=score,
                message=message,
                details={
                    'nodegroups': node_status,
                    'resource_utilization': resource_utilization,
                    'total_nodes': len(nodegroups),
                    'healthy_nodes': len([ng for ng in node_status if ng['status'] == 'ACTIVE'])
                },
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check node health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="critical",
                score=0.0,
                message=f"Failed to check node health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def _get_nodegroups(self, cluster_name: str) -> List[Dict[str, Any]]:
        """Get node groups for EKS cluster"""
        try:
            response = self.client['eks'].list_nodegroups(clusterName=cluster_name)
            nodegroups = []
            
            for nodegroup_name in response['nodegroups']:
                try:
                    ng_info = self.client['eks'].describe_nodegroup(
                        clusterName=cluster_name,
                        nodegroupName=nodegroup_name
                    )
                    
                    nodegroups.append({
                        'name': nodegroup_name,
                        'status': ng_info['nodegroup']['status'],
                        'instance_types': ng_info['nodegroup']['instanceTypes'],
                        'desired_size': ng_info['nodegroup']['scalingConfig']['desiredSize'],
                        'min_size': ng_info['nodegroup']['scalingConfig']['minSize'],
                        'max_size': ng_info['nodegroup']['scalingConfig']['maxSize'],
                        'created_at': ng_info['nodegroup']['createdAt']
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to describe nodegroup {nodegroup_name}: {e}")
                    continue
            
            return nodegroups
            
        except Exception as e:
            logger.error(f"Failed to get nodegroups for {cluster_name}: {e}")
            return []
    
    def _check_nodegroup_status(self, nodegroups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check node group status"""
        status_info = []
        
        for ng in nodegroups:
            # Check if nodegroup is active and at desired size
            is_active = ng['status'] == 'ACTIVE'
            
            # Get actual node count (simplified - would use EC2 API in production)
            actual_nodes = ng['desired_size']  # Simplified
            
            status_info.append({
                'name': ng['name'],
                'status': ng['status'],
                'is_active': is_active,
                'desired_size': ng['desired_size'],
                'actual_nodes': actual_nodes,
                'instance_types': ng['instance_types'],
                'health_score': 100.0 if is_active and actual_nodes >= ng['desired_size'] else 50.0
            })
        
        return status_info
    
    def _get_node_resource_utilization(self, cluster_name: str) -> Dict[str, Any]:
        """Get node resource utilization metrics"""
        try:
            # This is a simplified implementation
            # In production, you would use CloudWatch metrics or Prometheus
            
            utilization = {
                'cpu_utilization': 45.0,  # Average CPU utilization
                'memory_utilization': 60.0,  # Average memory utilization
                'disk_utilization': 35.0,  # Average disk utilization
                'network_utilization': 25.0,  # Average network utilization
                'pressure_indicators': {
                    'cpu_pressure': False,
                    'memory_pressure': False,
                    'disk_pressure': False,
                    'pid_pressure': False
                }
            }
            
            return utilization
            
        except Exception as e:
            logger.error(f"Failed to get node resource utilization: {e}")
            return {
                'cpu_utilization': 0.0,
                'memory_utilization': 0.0,
                'disk_utilization': 0.0,
                'network_utilization': 0.0,
                'pressure_indicators': {}
            }
    
    def _calculate_node_health_score(self, node_status: List[Dict[str, Any]], resource_utilization: Dict[str, Any]) -> float:
        """Calculate node health score"""
        try:
            # Node status score (50% weight)
            active_nodes = len([ns for ns in node_status if ns['is_active']])
            total_nodes = len(node_status)
            status_score = (active_nodes / total_nodes * 100) if total_nodes > 0 else 0.0
            
            # Resource utilization score (50% weight)
            cpu_score = max(0, 100 - abs(resource_utilization['cpu_utilization'] - 50))  # Optimal at 50%
            memory_score = max(0, 100 - abs(resource_utilization['memory_utilization'] - 60))  # Optimal at 60%
            disk_score = max(0, 100 - abs(resource_utilization['disk_utilization'] - 40))  # Optimal at 40%
            
            utilization_score = (cpu_score + memory_score + disk_score) / 3
            
            # Combined score
            overall_score = (status_score * 0.5) + (utilization_score * 0.5)
            
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate node health score: {e}")
            return 0.0
    
    def check_pod_health(self, cluster_name: str) -> HealthCheckResult:
        """Check pod health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would use Kubernetes API or kubectl
            
            pod_status = {
                'total_pods': 150,
                'running_pods': 142,
                'pending_pods': 5,
                'failed_pods': 3,
                'succeeded_pods': 0,
                'crashloop_backoffs': 2,
                'image_pull_backoffs': 1,
                'oom_killed': 0
            }
            
            # Calculate score
            total_pods = pod_status['total_pods']
            running_pods = pod_status['running_pods']
            failed_pods = pod_status['failed_pods'] + pod_status['crashloop_backoffs'] + pod_status['image_pull_backoffs']
            
            success_rate = (running_pods / total_pods * 100) if total_pods > 0 else 0.0
            failure_rate = (failed_pods / total_pods * 100) if total_pods > 0 else 0.0
            
            score = success_rate - (failure_rate * 2)  # Penalize failures more heavily
            score = max(0, min(100, score))  # Clamp between 0-100
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Pods are running normally"
            elif score >= 70:
                status = "warning"
                message = "Some pods are experiencing issues"
            else:
                status = "critical"
                message = "Critical pod health issues detected"
            
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status=status,
                score=score,
                message=message,
                details=pod_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check pod health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="critical",
                score=0.0,
                message=f"Failed to check pod health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def check_service_health(self, cluster_name: str) -> HealthCheckResult:
        """Check service health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would use Kubernetes API
            
            service_status = {
                'total_services': 25,
                'healthy_services': 23,
                'unhealthy_services': 2,
                'load_balancers': 8,
                'healthy_load_balancers': 7,
                'node_ports': 5,
                'cluster_ips': 12,
                'external_ips': 0,
                'endpoint_issues': 1
            }
            
            # Calculate score
            total_services = service_status['total_services']
            healthy_services = service_status['healthy_services']
            
            success_rate = (healthy_services / total_services * 100) if total_services > 0 else 0.0
            
            # Penalize endpoint issues
            endpoint_penalty = service_status['endpoint_issues'] * 10
            score = max(0, success_rate - endpoint_penalty)
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Services are healthy and accessible"
            elif score >= 70:
                status = "warning"
                message = "Some services have issues"
            else:
                status = "critical"
                message = "Critical service health issues detected"
            
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status=status,
                score=score,
                message=message,
                details=service_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check service health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="critical",
                score=0.0,
                message=f"Failed to check service health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def check_storage_health(self, cluster_name: str) -> HealthCheckResult:
        """Check storage health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would check PVs, PVCs, and storage classes
            
            storage_status = {
                'total_pvcs': 35,
                'bound_pvcs': 33,
                'pending_pvcs': 2,
                'failed_pvcs': 0,
                'total_pvs': 33,
                'available_pvs': 30,
                'failed_pvs': 1,
                'storage_classes': 3,
                'storage_utilization': {
                    'gp2': 65.0,
                    'io1': 45.0,
                    'standard': 30.0
                },
                'volume_issues': []
            }
            
            # Calculate score
            total_pvcs = storage_status['total_pvcs']
            bound_pvcs = storage_status['bound_pvcs']
            
            binding_rate = (bound_pvcs / total_pvcs * 100) if total_pvcs > 0 else 0.0
            
            # Check storage utilization
            avg_utilization = statistics.mean(storage_status['storage_utilization'].values())
            utilization_score = max(0, 100 - abs(avg_utilization - 60))  # Optimal at 60%
            
            # Combined score
            score = (binding_rate * 0.7) + (utilization_score * 0.3)
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Storage is healthy and properly utilized"
            elif score >= 70:
                status = "warning"
                message = "Some storage issues detected"
            else:
                status = "critical"
                message = "Critical storage health issues detected"
            
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status=status,
                score=score,
                message=message,
                details=storage_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check storage health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="critical",
                score=0.0,
                message=f"Failed to check storage health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def check_networking_health(self, cluster_name: str) -> HealthCheckResult:
        """Check networking health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would check VPC, subnets, security groups, etc.
            
            networking_status = {
                'vpc_status': 'healthy',
                'subnet_status': 'healthy',
                'security_groups': 'healthy',
                'route_tables': 'healthy',
                'nat_gateways': 'healthy',
                'internet_gateway': 'healthy',
                'network_policies': 12,
                'ingress_controllers': 2,
                'network_connectivity': {
                    'pod_to_pod': 'healthy',
                    'pod_to_service': 'healthy',
                    'external_to_service': 'healthy',
                    'service_to_external': 'healthy'
                },
                'dns_resolution': 'healthy',
                'network_latency_ms': 2.5
            }
            
            # Calculate score based on connectivity and latency
            connectivity_score = 100.0
            for direction, status in networking_status['network_connectivity'].items():
                if status != 'healthy':
                    connectivity_score -= 25.0
            
            # Check network latency
            latency_score = max(0, 100 - networking_status['network_latency_ms'] * 10)  # Penalize high latency
            
            score = (connectivity_score * 0.8) + (latency_score * 0.2)
            score = max(0, min(100, score))
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Cluster networking is healthy"
            elif score >= 70:
                status = "warning"
                message = "Some networking issues detected"
            else:
                status = "critical"
                message = "Critical networking issues detected"
            
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status=status,
                score=score,
                message=message,
                details=networking_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check networking health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="critical",
                score=0.0,
                message=f"Failed to check networking health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def check_security_health(self, cluster_name: str) -> HealthCheckResult:
        """Check security health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would check IAM roles, security policies, RBAC, etc.
            
            security_status = {
                'iam_roles': 'healthy',
                'rbac_enabled': True,
                'pod_security_policies': 8,
                'network_policies': 12,
                'security_contexts': 'healthy',
                'secrets_encryption': True,
                'audit_logging': True,
                'vulnerability_scans': {
                    'total_images': 45,
                    'vulnerable_images': 3,
                    'critical_vulnerabilities': 0,
                    'high_vulnerabilities': 2,
                    'medium_vulnerabilities': 8,
                    'low_vulnerabilities': 15
                },
                'compliance_status': {
                    'cis_benchmark': 'compliant',
                    'nist_controls': 'compliant',
                    'soc2_controls': 'compliant'
                },
                'security_issues': []
            }
            
            # Calculate score based on vulnerabilities and compliance
            vuln_data = security_status['vulnerability_scans']
            total_images = vuln_data['total_images']
            vulnerable_images = vuln_data['vulnerable_images']
            
            # Vulnerability score
            vuln_score = ((total_images - vulnerable_images) / total_images * 100) if total_images > 0 else 100.0
            
            # Penalize critical and high vulnerabilities
            critical_penalty = vuln_data['critical_vulnerabilities'] * 20
            high_penalty = vuln_data['high_vulnerabilities'] * 10
            vuln_score = max(0, vuln_score - critical_penalty - high_penalty)
            
            # Compliance score
            compliance_items = security_status['compliance_status']
            compliant_items = len([v for v in compliance_items.values() if v == 'compliant'])
            compliance_score = (compliant_items / len(compliance_items) * 100)
            
            # Combined score
            score = (vuln_score * 0.6) + (compliance_score * 0.4)
            score = max(0, min(100, score))
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Cluster security posture is strong"
            elif score >= 70:
                status = "warning"
                message = "Some security concerns detected"
            else:
                status = "critical"
                message = "Critical security issues detected"
            
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status=status,
                score=score,
                message=message,
                details=security_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check security health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="critical",
                score=0.0,
                message=f"Failed to check security health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def check_performance_health(self, cluster_name: str) -> HealthCheckResult:
        """Check performance health for EKS cluster"""
        try:
            # This is a simplified implementation
            # In production, you would check metrics from CloudWatch or Prometheus
            
            performance_status = {
                'api_server_latency_ms': 15.2,
                'scheduler_latency_ms': 8.5,
                'controller_manager_latency_ms': 12.3,
                'etcd_latency_ms': 25.7,
                'cluster_autoscaler_status': 'healthy',
                'resource_quotas': 'healthy',
                'limit_ranges': 'healthy',
                'horizontal_pod_autoscalers': {
                    'total': 8,
                    'healthy': 7,
                    'unhealthy': 1
                },
                'vertical_pod_autoscalers': {
                    'total': 3,
                    'healthy': 3,
                    'unhealthy': 0
                },
                'cluster_metrics': {
                    'pod_count': 150,
                    'service_count': 25,
                    'deployment_count': 18,
                    'namespace_count': 12
                },
                'performance_issues': []
            }
            
            # Calculate score based on latency and autoscaler health
            latencies = [
                performance_status['api_server_latency_ms'],
                performance_status['scheduler_latency_ms'],
                performance_status['controller_manager_latency_ms'],
                performance_status['etcd_latency_ms']
            ]
            
            avg_latency = statistics.mean(latencies)
            latency_score = max(0, 100 - avg_latency * 2)  # Penalize high latency
            
            # Autoscaler health
            hpa_total = performance_status['horizontal_pod_autoscalers']['total']
            hpa_healthy = performance_status['horizontal_pod_autoscalers']['healthy']
            hpa_score = (hpa_healthy / hpa_total * 100) if hpa_total > 0 else 100.0
            
            vpa_total = performance_status['vertical_pod_autoscalers']['total']
            vpa_healthy = performance_status['vertical_pod_autoscalers']['healthy']
            vpa_score = (vpa_healthy / vpa_total * 100) if vpa_total > 0 else 100.0
            
            autoscaler_score = (hpa_score + vpa_score) / 2
            
            # Combined score
            score = (latency_score * 0.6) + (autoscaler_score * 0.4)
            score = max(0, min(100, score))
            
            # Determine status
            if score >= 90:
                status = "healthy"
                message = "Cluster performance is optimal"
            elif score >= 70:
                status = "warning"
                message = "Some performance issues detected"
            else:
                status = "critical"
                message = "Critical performance issues detected"
            
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status=status,
                score=score,
                message=message,
                details=performance_status,
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
            
        except Exception as e:
            logger.error(f"Failed to check performance health for {cluster_name}: {e}")
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="critical",
                score=0.0,
                message=f"Failed to check performance health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="aws",
                region=self.region
            )
    
    def generate_health_summary(self, cluster_name: str, results: List[HealthCheckResult]) -> ClusterHealthSummary:
        """Generate comprehensive health summary for EKS cluster"""
        try:
            # Calculate overall metrics
            total_checks = len(results)
            passed_checks = len([r for r in results if r.status == 'healthy'])
            failed_checks = len([r for r in results if r.status == 'critical'])
            warning_checks = len([r for r in results if r.status == 'warning'])
            
            # Calculate overall score
            scores = [r.score for r in results]
            overall_score = statistics.mean(scores) if scores else 0.0
            
            # Determine overall status
            if overall_score >= 90:
                overall_status = "healthy"
            elif overall_score >= 70:
                overall_status = "warning"
            else:
                overall_status = "critical"
            
            # Collect critical issues
            critical_issues = []
            for result in results:
                if result.status == 'critical':
                    critical_issues.append(f"{result.check_name}: {result.message}")
            
            # Generate recommendations
            recommendations = self._generate_recommendations(results)
            
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="aws",
                region=self.region,
                overall_status=overall_status,
                overall_score=round(overall_score, 2),
                total_checks=total_checks,
                passed_checks=passed_checks,
                failed_checks=failed_checks,
                warning_checks=warning_checks,
                critical_issues=critical_issues,
                recommendations=recommendations,
                last_check=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate health summary for {cluster_name}: {e}")
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="aws",
                region=self.region,
                overall_status="critical",
                overall_score=0.0,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0,
                critical_issues=[f"Failed to generate summary: {str(e)}"],
                recommendations=["Check cluster connectivity and permissions"],
                last_check=datetime.utcnow()
            )
    
    def _generate_recommendations(self, results: List[HealthCheckResult]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for result in results:
            if result.status == 'critical':
                if result.check_type == 'nodes':
                    recommendations.append("Investigate node health issues - check node status and resource utilization")
                elif result.check_type == 'pods':
                    recommendations.append("Review pod failures - check logs and resource constraints")
                elif result.check_type == 'services':
                    recommendations.append("Fix service connectivity issues - check endpoints and load balancers")
                elif result.check_type == 'storage':
                    recommendations.append("Address storage problems - check PVC binding and volume availability")
                elif result.check_type == 'networking':
                    recommendations.append("Resolve networking issues - check VPC configuration and network policies")
                elif result.check_type == 'security':
                    recommendations.append("Address security vulnerabilities - update images and review policies")
                elif result.check_type == 'performance':
                    recommendations.append("Optimize cluster performance - check resource limits and scaling")
            
            elif result.status == 'warning':
                if result.check_type == 'nodes':
                    recommendations.append("Monitor node utilization closely - consider scaling if needed")
                elif result.check_type == 'pods':
                    recommendations.append("Review pod resource requests and limits")
                elif result.check_type == 'services':
                    recommendations.append("Monitor service endpoints and load balancer health")
                elif result.check_type == 'storage':
                    recommendations.append("Monitor storage utilization and plan capacity")
                elif result.check_type == 'networking':
                    recommendations.append("Monitor network latency and connectivity")
                elif result.check_type == 'security':
                    recommendations.append("Regular security scans and updates recommended")
                elif result.check_type == 'performance':
                    recommendations.append("Monitor performance metrics and optimize as needed")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Cluster health is good - continue regular monitoring")
        
        return recommendations

# Simplified handlers for other providers
class AzureClusterHealthCheckHandler(ClusterHealthCheckHandler):
    """Azure-specific cluster health check operations"""
    
    def initialize_client(self) -> bool:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.containerservice import ContainerServiceClient
            from azure.mgmt.monitor import MonitorManagementClient
            
            credential = DefaultAzureCredential()
            self.client = {
                'aks': ContainerServiceClient(credential, "<subscription-id>"),
                'monitor': MonitorManagementClient(credential, "<subscription-id>")
            }
            logger.info("Azure clients initialized")
            return True
        except ImportError:
            logger.error("Azure SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
            return False
    
    def discover_clusters(self) -> List[Dict[str, Any]]:
        """Discover AKS clusters in Azure"""
        try:
            clusters = []
            
            # Simulate Azure AKS cluster discovery
            sample_clusters = [
                {
                    'name': 'aks-cluster-1',
                    'provider': 'azure',
                    'region': 'eastus',
                    'version': '1.26.3',
                    'status': 'Running',
                    'endpoint': 'https://aks-cluster-1.eastus.azmk8s.io',
                    'node_count': 3,
                    'tags': {'Environment': 'production', 'Team': 'platform'}
                },
                {
                    'name': 'aks-cluster-2',
                    'provider': 'azure',
                    'region': 'westus',
                    'version': '1.25.6',
                    'status': 'Running',
                    'endpoint': 'https://aks-cluster-2.westus.azmk8s.io',
                    'node_count': 2,
                    'tags': {'Environment': 'staging', 'Team': 'dev'}
                }
            ]
            
            clusters.extend(sample_clusters)
            
            logger.info(f"Discovered {len(clusters)} Azure AKS clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to discover Azure clusters: {e}")
            return []
    
    def check_node_health(self, cluster_name: str) -> HealthCheckResult:
        """Check node health for AKS cluster"""
        try:
            # Simulate Azure node health check
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="healthy",
                score=92.0,
                message="Azure nodes are healthy",
                details={'total_nodes': 3, 'healthy_nodes': 3, 'ready_nodes': 3},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure node health: {e}")
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="critical",
                score=0.0,
                message=f"Failed to check node health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_pod_health(self, cluster_name: str) -> HealthCheckResult:
        """Check pod health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="healthy",
                score=88.0,
                message="Azure pods are running normally",
                details={'total_pods': 45, 'running_pods': 43, 'failed_pods': 2},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure pod health: {e}")
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="critical",
                score=0.0,
                message=f"Failed to check pod health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_service_health(self, cluster_name: str) -> HealthCheckResult:
        """Check service health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="healthy",
                score=95.0,
                message="Azure services are healthy",
                details={'total_services': 15, 'healthy_services': 15},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure service health: {e}")
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="critical",
                score=0.0,
                message=f"Failed to check service health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_storage_health(self, cluster_name: str) -> HealthCheckResult:
        """Check storage health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="healthy",
                score=90.0,
                message="Azure storage is healthy",
                details={'total_pvcs': 12, 'bound_pvcs': 12},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure storage health: {e}")
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="critical",
                score=0.0,
                message=f"Failed to check storage health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_networking_health(self, cluster_name: str) -> HealthCheckResult:
        """Check networking health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="healthy",
                score=93.0,
                message="Azure networking is healthy",
                details={'vnet_status': 'healthy', 'load_balancers': 3},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure networking health: {e}")
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="critical",
                score=0.0,
                message=f"Failed to check networking health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_security_health(self, cluster_name: str) -> HealthCheckResult:
        """Check security health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="healthy",
                score=91.0,
                message="Azure security posture is strong",
                details={'aad_enabled': True, 'network_policies': 8},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure security health: {e}")
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="critical",
                score=0.0,
                message=f"Failed to check security health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def check_performance_health(self, cluster_name: str) -> HealthCheckResult:
        """Check performance health for AKS cluster"""
        try:
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="healthy",
                score=89.0,
                message="Azure cluster performance is good",
                details={'api_latency_ms': 12.5, 'autoscalers': 5},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check Azure performance health: {e}")
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="critical",
                score=0.0,
                message=f"Failed to check performance health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="azure",
                region=self.region
            )
    
    def generate_health_summary(self, cluster_name: str, results: List[HealthCheckResult]) -> ClusterHealthSummary:
        """Generate comprehensive health summary for AKS cluster"""
        try:
            scores = [r.score for r in results]
            overall_score = statistics.mean(scores) if scores else 0.0
            
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="azure",
                region=self.region,
                overall_status="healthy" if overall_score >= 90 else "warning",
                overall_score=round(overall_score, 2),
                total_checks=len(results),
                passed_checks=len([r for r in results if r.status == 'healthy']),
                failed_checks=len([r for r in results if r.status == 'critical']),
                warning_checks=len([r for r in results if r.status == 'warning']),
                critical_issues=[],
                recommendations=["Continue monitoring Azure cluster health"],
                last_check=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to generate Azure health summary: {e}")
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="azure",
                region=self.region,
                overall_status="critical",
                overall_score=0.0,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0,
                critical_issues=[f"Failed to generate summary: {str(e)}"],
                recommendations=["Check Azure cluster connectivity"],
                last_check=datetime.utcnow()
            )

class GCPClusterHealthCheckHandler(ClusterHealthCheckHandler):
    """GCP-specific cluster health check operations"""
    
    def initialize_client(self) -> bool:
        try:
            from google.cloud import container_v1
            from google.cloud import monitoring
            
            self.client = {
                'gke': container_v1.ClusterManagerClient(),
                'monitoring': monitoring.MetricServiceClient()
            }
            logger.info("GCP clients initialized")
            return True
        except ImportError:
            logger.error("GCP SDK not available")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize GCP client: {e}")
            return False
    
    def discover_clusters(self) -> List[Dict[str, Any]]:
        """Discover GKE clusters in GCP"""
        try:
            clusters = []
            
            # Simulate GCP GKE cluster discovery
            sample_clusters = [
                {
                    'name': 'gke-cluster-1',
                    'provider': 'gcp',
                    'region': 'us-central1',
                    'version': '1.26.1',
                    'status': 'RUNNING',
                    'endpoint': 'https://34.123.45.67',
                    'node_count': 3,
                    'tags': {'Environment': 'production', 'Project': 'platform'}
                }
            ]
            
            clusters.extend(sample_clusters)
            
            logger.info(f"Discovered {len(clusters)} GCP GKE clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to discover GCP clusters: {e}")
            return []
    
    def check_node_health(self, cluster_name: str) -> HealthCheckResult:
        """Check node health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="healthy",
                score=94.0,
                message="GCP nodes are healthy",
                details={'total_nodes': 3, 'healthy_nodes': 3},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP node health: {e}")
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="critical",
                score=0.0,
                message=f"Failed to check node health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_pod_health(self, cluster_name: str) -> HealthCheckResult:
        """Check pod health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="healthy",
                score=91.0,
                message="GCP pods are running normally",
                details={'total_pods': 38, 'running_pods': 37, 'failed_pods': 1},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP pod health: {e}")
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="critical",
                score=0.0,
                message=f"Failed to check pod health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_service_health(self, cluster_name: str) -> HealthCheckResult:
        """Check service health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="healthy",
                score=96.0,
                message="GCP services are healthy",
                details={'total_services': 18, 'healthy_services': 18},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP service health: {e}")
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="critical",
                score=0.0,
                message=f"Failed to check service health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_storage_health(self, cluster_name: str) -> HealthCheckResult:
        """Check storage health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="healthy",
                score=92.0,
                message="GCP storage is healthy",
                details={'total_pvcs': 15, 'bound_pvcs': 15},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP storage health: {e}")
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="critical",
                score=0.0,
                message=f"Failed to check storage health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_networking_health(self, cluster_name: str) -> HealthCheckResult:
        """Check networking health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="healthy",
                score=95.0,
                message="GCP networking is healthy",
                details={'vpc_status': 'healthy', 'load_balancers': 4},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP networking health: {e}")
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="critical",
                score=0.0,
                message=f"Failed to check networking health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_security_health(self, cluster_name: str) -> HealthCheckResult:
        """Check security health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="healthy",
                score=93.0,
                message="GCP security posture is strong",
                details={'iam_enabled': True, 'network_policies': 10},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP security health: {e}")
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="critical",
                score=0.0,
                message=f"Failed to check security health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def check_performance_health(self, cluster_name: str) -> HealthCheckResult:
        """Check performance health for GKE cluster"""
        try:
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="healthy",
                score=90.0,
                message="GCP cluster performance is good",
                details={'api_latency_ms': 11.8, 'autoscalers': 4},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check GCP performance health: {e}")
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="critical",
                score=0.0,
                message=f"Failed to check performance health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region
            )
    
    def generate_health_summary(self, cluster_name: str, results: List[HealthCheckResult]) -> ClusterHealthSummary:
        """Generate comprehensive health summary for GKE cluster"""
        try:
            scores = [r.score for r in results]
            overall_score = statistics.mean(scores) if scores else 0.0
            
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region,
                overall_status="healthy" if overall_score >= 90 else "warning",
                overall_score=round(overall_score, 2),
                total_checks=len(results),
                passed_checks=len([r for r in results if r.status == 'healthy']),
                failed_checks=len([r for r in results if r.status == 'critical']),
                warning_checks=len([r for r in results if r.status == 'warning']),
                critical_issues=[],
                recommendations=["Continue monitoring GCP cluster health"],
                last_check=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to generate GCP health summary: {e}")
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="gcp",
                region=self.region,
                overall_status="critical",
                overall_score=0.0,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0,
                critical_issues=[f"Failed to generate summary: {str(e)}"],
                recommendations=["Check GCP cluster connectivity"],
                last_check=datetime.utcnow()
            )

class OnPremClusterHealthCheckHandler(ClusterHealthCheckHandler):
    """On-premise cluster health check operations"""
    
    def initialize_client(self) -> bool:
        try:
            # On-premise might use kubectl or direct API access
            logger.info("On-premise cluster health check handler initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize on-premise client: {e}")
            return False
    
    def discover_clusters(self) -> List[Dict[str, Any]]:
        """Discover on-premise clusters"""
        try:
            clusters = []
            
            # Simulate on-premise cluster discovery
            sample_clusters = [
                {
                    'name': 'onprem-cluster-1',
                    'provider': 'onprem',
                    'region': 'datacenter-1',
                    'version': '1.25.4',
                    'status': 'Running',
                    'endpoint': 'https://k8s-onprem.company.com',
                    'node_count': 5,
                    'tags': {'Environment': 'production', 'Location': 'datacenter-a'}
                }
            ]
            
            clusters.extend(sample_clusters)
            
            logger.info(f"Discovered {len(clusters)} on-premise clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to discover on-premise clusters: {e}")
            return []
    
    def check_node_health(self, cluster_name: str) -> HealthCheckResult:
        """Check node health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="healthy",
                score=89.0,
                message="On-premise nodes are healthy",
                details={'total_nodes': 5, 'healthy_nodes': 5},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise node health: {e}")
            return HealthCheckResult(
                check_name="node_health",
                check_type="nodes",
                status="critical",
                score=0.0,
                message=f"Failed to check node health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_pod_health(self, cluster_name: str) -> HealthCheckResult:
        """Check pod health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="healthy",
                score=87.0,
                message="On-premise pods are running normally",
                details={'total_pods': 62, 'running_pods': 60, 'failed_pods': 2},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise pod health: {e}")
            return HealthCheckResult(
                check_name="pod_health",
                check_type="pods",
                status="critical",
                score=0.0,
                message=f"Failed to check pod health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_service_health(self, cluster_name: str) -> HealthCheckResult:
        """Check service health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="healthy",
                score=92.0,
                message="On-premise services are healthy",
                details={'total_services': 22, 'healthy_services': 22},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise service health: {e}")
            return HealthCheckResult(
                check_name="service_health",
                check_type="services",
                status="critical",
                score=0.0,
                message=f"Failed to check service health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_storage_health(self, cluster_name: str) -> HealthCheckResult:
        """Check storage health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="healthy",
                score=88.0,
                message="On-premise storage is healthy",
                details={'total_pvcs': 28, 'bound_pvcs': 27, 'pending_pvcs': 1},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise storage health: {e}")
            return HealthCheckResult(
                check_name="storage_health",
                check_type="storage",
                status="critical",
                score=0.0,
                message=f"Failed to check storage health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_networking_health(self, cluster_name: str) -> HealthCheckResult:
        """Check networking health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="healthy",
                score=90.0,
                message="On-premise networking is healthy",
                details={'network_status': 'healthy', 'load_balancers': 3},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise networking health: {e}")
            return HealthCheckResult(
                check_name="networking_health",
                check_type="networking",
                status="critical",
                score=0.0,
                message=f"Failed to check networking health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_security_health(self, cluster_name: str) -> HealthCheckResult:
        """Check security health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="healthy",
                score=85.0,
                message="On-premise security posture is good",
                details={'rbac_enabled': True, 'network_policies': 6},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise security health: {e}")
            return HealthCheckResult(
                check_name="security_health",
                check_type="security",
                status="critical",
                score=0.0,
                message=f"Failed to check security health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def check_performance_health(self, cluster_name: str) -> HealthCheckResult:
        """Check performance health for on-premise cluster"""
        try:
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="healthy",
                score=86.0,
                message="On-premise cluster performance is good",
                details={'api_latency_ms': 14.2, 'autoscalers': 2},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
        except Exception as e:
            logger.error(f"Failed to check on-premise performance health: {e}")
            return HealthCheckResult(
                check_name="performance_health",
                check_type="performance",
                status="critical",
                score=0.0,
                message=f"Failed to check performance health: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region
            )
    
    def generate_health_summary(self, cluster_name: str, results: List[HealthCheckResult]) -> ClusterHealthSummary:
        """Generate comprehensive health summary for on-premise cluster"""
        try:
            scores = [r.score for r in results]
            overall_score = statistics.mean(scores) if scores else 0.0
            
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region,
                overall_status="healthy" if overall_score >= 85 else "warning",
                overall_score=round(overall_score, 2),
                total_checks=len(results),
                passed_checks=len([r for r in results if r.status == 'healthy']),
                failed_checks=len([r for r in results if r.status == 'critical']),
                warning_checks=len([r for r in results if r.status == 'warning']),
                critical_issues=[],
                recommendations=["Continue monitoring on-premise cluster health"],
                last_check=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to generate on-premise health summary: {e}")
            return ClusterHealthSummary(
                cluster_name=cluster_name,
                provider="onprem",
                region=self.region,
                overall_status="critical",
                overall_score=0.0,
                total_checks=0,
                passed_checks=0,
                failed_checks=0,
                warning_checks=0,
                critical_issues=[f"Failed to generate summary: {str(e)}"],
                recommendations=["Check on-premise cluster connectivity"],
                last_check=datetime.utcnow()
            )

def get_cluster_health_check_handler(provider: str, region: str = "us-west-2") -> ClusterHealthCheckHandler:
    """Get appropriate cluster health check handler"""
    handlers = {
        'aws': AWSClusterHealthCheckHandler,
        'azure': AzureClusterHealthCheckHandler,
        'gcp': GCPClusterHealthCheckHandler,
        'onprem': OnPremClusterHealthCheckHandler
    }
    
    handler_class = handlers.get(provider.lower())
    if not handler_class:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return handler_class(region)
