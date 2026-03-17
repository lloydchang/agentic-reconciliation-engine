#!/usr/bin/env python3
"""
Cluster Health Check Script

Multi-cloud automation for comprehensive health checks on Kubernetes clusters across AWS, Azure, GCP, and on-premise environments.
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ONPREM = "onprem"
    ALL = "all"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class CheckType(Enum):
    NODES = "nodes"
    PODS = "pods"
    SERVICES = "services"
    STORAGE = "storage"
    NETWORKING = "networking"
    SECURITY = "security"
    PERFORMANCE = "performance"

@dataclass
class HealthCheckResult:
    check_name: str
    check_type: CheckType
    status: HealthStatus
    score: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

@dataclass
class ClusterHealthReport:
    cluster_name: str
    provider: str
    region: str
    overall_status: HealthStatus
    overall_score: float
    check_results: List[HealthCheckResult]
    summary: Dict[str, Any]
    timestamp: datetime

class ClusterHealthChecker:
    def __init__(self, config_file: Optional[str] = None):
        self.providers = {}
        self.config = self._load_config(config_file)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load health check configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'health_thresholds': {
                'node_health_warning': 90.0,
                'node_health_critical': 70.0,
                'pod_health_warning': 95.0,
                'pod_health_critical': 80.0,
                'storage_warning': 85.0,
                'storage_critical': 70.0
            },
            'check_types': ['nodes', 'pods', 'services', 'storage', 'networking']
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def check_cluster_health(self, cluster_name: str, provider: str, check_types: List[CheckType]) -> ClusterHealthReport:
        """Perform comprehensive health check on a cluster"""
        logger.info(f"Checking health for cluster {cluster_name} on {provider}")
        
        if provider not in self.config['providers']:
            raise ValueError(f"Provider {provider} not configured")
        
        if not self.config['providers'][provider]['enabled']:
            raise ValueError(f"Provider {provider} is disabled")
        
        # Initialize provider handler
        handler = self._get_provider_handler(provider)
        if not handler.initialize_client():
            raise RuntimeError(f"Failed to initialize {provider} handler")
        
        # Perform health checks
        check_results = []
        
        for check_type in check_types:
            try:
                result = self._perform_health_check(handler, cluster_name, check_type)
                check_results.append(result)
                logger.info(f"Completed {check_type.value} check: {result.status.value}")
                
            except Exception as e:
                logger.error(f"Failed to perform {check_type.value} check: {e}")
                # Add a failed check result
                check_results.append(HealthCheckResult(
                    check_name=f"{cluster_name}_{check_type.value}",
                    check_type=check_type,
                    status=HealthStatus.UNKNOWN,
                    score=0.0,
                    message=f"Check failed: {str(e)}",
                    details={'error': str(e)},
                    timestamp=datetime.utcnow(),
                    recommendations=["Check provider connectivity and permissions"]
                ))
        
        # Calculate overall health
        overall_status, overall_score = self._calculate_overall_health(check_results)
        
        # Generate summary
        summary = self._generate_summary(check_results)
        
        # Create health report
        report = ClusterHealthReport(
            cluster_name=cluster_name,
            provider=provider,
            region=self.config['providers'][provider]['region'],
            overall_status=overall_status,
            overall_score=overall_score,
            check_results=check_results,
            summary=summary,
            timestamp=datetime.utcnow()
        )
        
        return report
    
    def _get_provider_handler(self, provider: str):
        """Get provider-specific health check handler"""
        from cluster_health_check_handler import get_cluster_health_handler
        region = self.config['providers'][provider]['region']
        return get_cluster_health_handler(provider, region)
    
    def _perform_health_check(self, handler, cluster_name: str, check_type: CheckType) -> HealthCheckResult:
        """Perform a specific health check"""
        if check_type == CheckType.NODES:
            return self._check_nodes_health(handler, cluster_name)
        elif check_type == CheckType.PODS:
            return self._check_pods_health(handler, cluster_name)
        elif check_type == CheckType.SERVICES:
            return self._check_services_health(handler, cluster_name)
        elif check_type == CheckType.STORAGE:
            return self._check_storage_health(handler, cluster_name)
        elif check_type == CheckType.NETWORKING:
            return self._check_networking_health(handler, cluster_name)
        elif check_type == CheckType.SECURITY:
            return self._check_security_health(handler, cluster_name)
        elif check_type == CheckType.PERFORMANCE:
            return self._check_performance_health(handler, cluster_name)
        else:
            raise ValueError(f"Unsupported check type: {check_type}")
    
    def _check_nodes_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster nodes health"""
        try:
            nodes_data = handler.get_cluster_nodes()
            
            if not nodes_data:
                return HealthCheckResult(
                    check_name=f"{cluster_name}_nodes",
                    check_type=CheckType.NODES,
                    status=HealthStatus.UNKNOWN,
                    score=0.0,
                    message="No node data available",
                    details={},
                    timestamp=datetime.utcnow(),
                    recommendations=["Check cluster connectivity"]
                )
            
            total_nodes = len(nodes_data)
            ready_nodes = len([n for n in nodes_data if n.get('status') == 'Ready'])
            node_health_percentage = (ready_nodes / total_nodes * 100) if total_nodes > 0 else 0
            
            # Determine status based on thresholds
            thresholds = self.config['health_thresholds']
            if node_health_percentage >= thresholds['node_health_warning']:
                status = HealthStatus.HEALTHY
            elif node_health_percentage >= thresholds['node_health_critical']:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL
            
            # Generate recommendations
            recommendations = []
            if status != HealthStatus.HEALTHY:
                unhealthy_nodes = [n for n in nodes_data if n.get('status') != 'Ready']
                recommendations.append(f"Investigate {len(unhealthy_nodes)} unhealthy nodes")
                recommendations.append("Check node resource constraints and system logs")
            
            details = {
                'total_nodes': total_nodes,
                'ready_nodes': ready_nodes,
                'unhealthy_nodes': total_nodes - ready_nodes,
                'health_percentage': node_health_percentage,
                'nodes': nodes_data[:5]  # Include first 5 nodes for details
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_nodes",
                check_type=CheckType.NODES,
                status=status,
                score=node_health_percentage,
                message=f"Node health: {ready_nodes}/{total_nodes} nodes ready ({node_health_percentage:.1f}%)",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Node health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_nodes",
                check_type=CheckType.NODES,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Node health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_pods_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster pods health"""
        try:
            pods_data = handler.get_cluster_pods()
            
            if not pods_data:
                return HealthCheckResult(
                    check_name=f"{cluster_name}_pods",
                    check_type=CheckType.PODS,
                    status=HealthStatus.UNKNOWN,
                    score=0.0,
                    message="No pod data available",
                    details={},
                    timestamp=datetime.utcnow(),
                    recommendations=["Check cluster connectivity"]
                )
            
            total_pods = len(pods_data)
            running_pods = len([p for p in pods_data if p.get('phase') == 'Running'])
            failed_pods = len([p for p in pods_data if p.get('phase') in ['Failed', 'CrashLoopBackOff']])
            pending_pods = len([p for p in pods_data if p.get('phase') == 'Pending'])
            
            # Calculate health score
            if total_pods > 0:
                healthy_score = (running_pods / total_pods * 100)
            else:
                healthy_score = 100  # No pods is considered healthy
            
            # Determine status
            thresholds = self.config['health_thresholds']
            if healthy_score >= thresholds['pod_health_warning']:
                status = HealthStatus.HEALTHY
            elif healthy_score >= thresholds['pod_health_critical']:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL
            
            # Generate recommendations
            recommendations = []
            if failed_pods > 0:
                recommendations.append(f"Fix {failed_pods} failed pods")
                recommendations.append("Check pod logs and events")
            if pending_pods > 5:
                recommendations.append(f"Investigate {pending_pods} pending pods")
                recommendations.append("Check resource availability and scheduling")
            
            details = {
                'total_pods': total_pods,
                'running_pods': running_pods,
                'failed_pods': failed_pods,
                'pending_pods': pending_pods,
                'health_percentage': healthy_score,
                'pods_by_namespace': self._group_pods_by_namespace(pods_data)
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_pods",
                check_type=CheckType.PODS,
                status=status,
                score=healthy_score,
                message=f"Pod health: {running_pods}/{total_pods} pods running ({healthy_score:.1f}%)",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Pod health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_pods",
                check_type=CheckType.PODS,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Pod health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_services_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster services health"""
        try:
            services_data = handler.get_cluster_services()
            
            if not services_data:
                return HealthCheckResult(
                    check_name=f"{cluster_name}_services",
                    check_type=CheckType.SERVICES,
                    status=HealthStatus.HEALTHY,
                    score=100.0,
                    message="No services found",
                    details={'total_services': 0},
                    timestamp=datetime.utcnow(),
                    recommendations=[]
                )
            
            total_services = len(services_data)
            healthy_services = len([s for s in services_data if s.get('healthy', False)])
            
            health_percentage = (healthy_services / total_services * 100) if total_services > 0 else 100
            status = HealthStatus.HEALTHY if health_percentage >= 90 else HealthStatus.WARNING
            
            recommendations = []
            if health_percentage < 90:
                unhealthy_services = total_services - healthy_services
                recommendations.append(f"Fix {unhealthy_services} unhealthy services")
                recommendations.append("Check service endpoints and pod connectivity")
            
            details = {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'unhealthy_services': total_services - healthy_services,
                'health_percentage': health_percentage
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_services",
                check_type=CheckType.SERVICES,
                status=status,
                score=health_percentage,
                message=f"Service health: {healthy_services}/{total_services} services healthy ({health_percentage:.1f}%)",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Service health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_services",
                check_type=CheckType.SERVICES,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Service health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_storage_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster storage health"""
        try:
            storage_data = handler.get_cluster_storage()
            
            if not storage_data:
                return HealthCheckResult(
                    check_name=f"{cluster_name}_storage",
                    check_type=CheckType.STORAGE,
                    status=HealthStatus.HEALTHY,
                    score=100.0,
                    message="No storage resources found",
                    details={'total_pvcs': 0},
                    timestamp=datetime.utcnow(),
                    recommendations=[]
                )
            
            total_pvcs = len(storage_data)
            bound_pvcs = len([s for s in storage_data if s.get('status') == 'Bound'])
            
            health_percentage = (bound_pvcs / total_pvcs * 100) if total_pvcs > 0 else 100
            
            thresholds = self.config['health_thresholds']
            if health_percentage >= thresholds['storage_warning']:
                status = HealthStatus.HEALTHY
            elif health_percentage >= thresholds['storage_critical']:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.CRITICAL
            
            recommendations = []
            if health_percentage < 100:
                unbound_pvcs = total_pvcs - bound_pvcs
                recommendations.append(f"Fix {unbound_pvcs} unbound PVCs")
                recommendations.append("Check storage class and availability")
            
            details = {
                'total_pvcs': total_pvcs,
                'bound_pvcs': bound_pvcs,
                'unbound_pvcs': total_pvcs - bound_pvcs,
                'health_percentage': health_percentage
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_storage",
                check_type=CheckType.STORAGE,
                status=status,
                score=health_percentage,
                message=f"Storage health: {bound_pvcs}/{total_pvcs} PVCs bound ({health_percentage:.1f}%)",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_storage",
                check_type=CheckType.STORAGE,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Storage health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_networking_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster networking health"""
        try:
            networking_data = handler.get_cluster_networking()
            
            # Simplified networking health check
            score = 95.0  # Assume healthy unless issues detected
            status = HealthStatus.HEALTHY
            
            # Check for common networking issues
            issues = []
            if networking_data.get('dns_issues', 0) > 0:
                issues.append(f"{networking_data['dns_issues']} DNS resolution issues")
                score -= 10
            
            if networking_data.get('network_policies_blocked', 0) > 5:
                issues.append(f"{networking_data['network_policies_blocked']} blocked connections")
                score -= 5
            
            if score < 80:
                status = HealthStatus.WARNING
            elif score < 60:
                status = HealthStatus.CRITICAL
            
            recommendations = []
            if issues:
                recommendations.extend(issues)
                recommendations.append("Review network policies and DNS configuration")
            
            details = {
                'issues_detected': len(issues),
                'networking_data': networking_data
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_networking",
                check_type=CheckType.NETWORKING,
                status=status,
                score=score,
                message=f"Networking health: {len(issues)} issues detected",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Networking health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_networking",
                check_type=CheckType.NETWORKING,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Networking health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_security_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster security health"""
        try:
            security_data = handler.get_cluster_security()
            
            # Simplified security health check
            score = 90.0
            status = HealthStatus.HEALTHY
            
            issues = []
            if security_data.get('rbac_issues', 0) > 0:
                issues.append(f"{security_data['rbac_issues']} RBAC issues")
                score -= 10
            
            if security_data.get('pod_security_issues', 0) > 0:
                issues.append(f"{security_data['pod_security_issues']} pod security issues")
                score -= 15
            
            if score < 70:
                status = HealthStatus.WARNING
            elif score < 50:
                status = HealthStatus.CRITICAL
            
            recommendations = []
            if issues:
                recommendations.extend(issues)
                recommendations.append("Review RBAC policies and pod security contexts")
            
            details = {
                'security_score': score,
                'issues_detected': len(issues),
                'security_data': security_data
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_security",
                check_type=CheckType.SECURITY,
                status=status,
                score=score,
                message=f"Security health: {len(issues)} issues detected",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Security health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_security",
                check_type=CheckType.SECURITY,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Security health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _check_performance_health(self, handler, cluster_name: str) -> HealthCheckResult:
        """Check cluster performance health"""
        try:
            performance_data = handler.get_cluster_performance()
            
            # Simplified performance health check
            cpu_utilization = performance_data.get('avg_cpu_utilization', 50)
            memory_utilization = performance_data.get('avg_memory_utilization', 60)
            
            # Calculate performance score
            score = 100.0
            if cpu_utilization > 80:
                score -= 20
            elif cpu_utilization > 70:
                score -= 10
            
            if memory_utilization > 85:
                score -= 20
            elif memory_utilization > 75:
                score -= 10
            
            status = HealthStatus.HEALTHY if score >= 80 else HealthStatus.WARNING if score >= 60 else HealthStatus.CRITICAL
            
            recommendations = []
            if cpu_utilization > 80:
                recommendations.append("High CPU utilization detected - consider scaling")
            if memory_utilization > 85:
                recommendations.append("High memory utilization detected - consider scaling")
            
            details = {
                'cpu_utilization': cpu_utilization,
                'memory_utilization': memory_utilization,
                'performance_data': performance_data
            }
            
            return HealthCheckResult(
                check_name=f"{cluster_name}_performance",
                check_type=CheckType.PERFORMANCE,
                status=status,
                score=score,
                message=f"Performance: CPU {cpu_utilization:.1f}%, Memory {memory_utilization:.1f}%",
                details=details,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return HealthCheckResult(
                check_name=f"{cluster_name}_performance",
                check_type=CheckType.PERFORMANCE,
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"Performance health check failed: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.utcnow(),
                recommendations=["Check cluster access and permissions"]
            )
    
    def _group_pods_by_namespace(self, pods_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group pods by namespace"""
        namespace_counts = {}
        for pod in pods_data:
            namespace = pod.get('namespace', 'default')
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
        return namespace_counts
    
    def _calculate_overall_health(self, check_results: List[HealthCheckResult]) -> tuple[HealthStatus, float]:
        """Calculate overall cluster health"""
        if not check_results:
            return HealthStatus.UNKNOWN, 0.0
        
        # Calculate average score
        total_score = sum(r.score for r in check_results)
        avg_score = total_score / len(check_results)
        
        # Determine overall status
        critical_count = len([r for r in check_results if r.status == HealthStatus.CRITICAL])
        warning_count = len([r for r in check_results if r.status == HealthStatus.WARNING])
        
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > len(check_results) / 2:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        return overall_status, avg_score
    
    def _generate_summary(self, check_results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate health check summary"""
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = len([r for r in check_results if r.status == status])
        
        total_recommendations = sum(len(r.recommendations) for r in check_results)
        
        return {
            'total_checks': len(check_results),
            'status_distribution': status_counts,
            'total_recommendations': total_recommendations,
            'highest_priority_issues': [
                {
                    'check': r.check_name,
                    'status': r.status.value,
                    'message': r.message,
                    'recommendations': r.recommendations[:2]  # Top 2 recommendations
                }
                for r in check_results if r.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]
            ]
        }
    
    def generate_health_report(self, reports: List[ClusterHealthReport], output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive health report for multiple clusters"""
        if not reports:
            return {"error": "No health reports available"}
        
        # Calculate overall summary
        total_clusters = len(reports)
        healthy_clusters = len([r for r in reports if r.overall_status == HealthStatus.HEALTHY])
        warning_clusters = len([r for r in reports if r.overall_status == HealthStatus.WARNING])
        critical_clusters = len([r for r in reports if r.overall_status == HealthStatus.CRITICAL])
        
        overall_health_score = sum(r.overall_score for r in reports) / total_clusters if total_clusters > 0 else 0
        
        # Group by provider
        provider_summary = {}
        for report in reports:
            provider = report.provider
            if provider not in provider_summary:
                provider_summary[provider] = {'clusters': [], 'avg_score': 0, 'status_counts': {}}
            
            provider_summary[provider]['clusters'].append(report.cluster_name)
            
            # Update status counts
            status = report.overall_status.value
            provider_summary[provider]['status_counts'][status] = provider_summary[provider]['status_counts'].get(status, 0) + 1
        
        # Calculate average scores per provider
        for provider, data in provider_summary.items():
            provider_reports = [r for r in reports if r.provider == provider]
            data['avg_score'] = sum(r.overall_score for r in provider_reports) / len(provider_reports)
        
        # Generate recommendations
        recommendations = []
        if critical_clusters > 0:
            recommendations.append(f"Address {critical_clusters} critical cluster(s) immediately")
        if warning_clusters > 0:
            recommendations.append(f"Monitor {warning_clusters} cluster(s) with warnings")
        if overall_health_score < 80:
            recommendations.append("Overall cluster health is below optimal - review infrastructure")
        
        report_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_clusters": total_clusters,
                "healthy_clusters": healthy_clusters,
                "warning_clusters": warning_clusters,
                "critical_clusters": critical_clusters,
                "overall_health_score": round(overall_health_score, 1),
                "overall_status": "healthy" if overall_health_score >= 80 else "warning" if overall_health_score >= 60 else "critical"
            },
            "provider_summary": provider_summary,
            "cluster_reports": [
                {
                    "cluster_name": report.cluster_name,
                    "provider": report.provider,
                    "region": report.region,
                    "overall_status": report.overall_status.value,
                    "overall_score": report.overall_score,
                    "check_count": len(report.check_results),
                    "recommendation_count": sum(len(r.recommendations) for r in report.check_results),
                    "timestamp": report.timestamp.isoformat()
                }
                for report in reports
            ],
            "recommendations": recommendations
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Health report saved to: {output_file}")
        
        return report_data

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Cluster Health Checker")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--cluster-name", required=True, help="Cluster name")
    parser.add_argument("--provider", choices=['aws', 'azure', 'gcp', 'onprem'], required=True, help="Cloud provider")
    parser.add_argument("--check-types", nargs="+",
                       choices=[t.value for t in CheckType],
                       default=['nodes', 'pods', 'services', 'storage'], help="Health check types")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize health checker
    checker = ClusterHealthChecker(args.config)
    
    # Convert check types
    check_types = [CheckType(t) for t in args.check_types]
    
    # Perform health check
    try:
        report = checker.check_cluster_health(args.cluster_name, args.provider, check_types)
        
        print(f"\nCluster Health Report for {report.cluster_name}:")
        print(f"Provider: {report.provider} ({report.region})")
        print(f"Overall Status: {report.overall_status.value}")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print(f"Checks Performed: {len(report.check_results)}")
        
        # Print check results
        for result in report.check_results:
            print(f"\n{result.check_type.value.upper()}: {result.status.value} ({result.score:.1f}/100)")
            print(f"  {result.message}")
            if result.recommendations:
                for rec in result.recommendations[:2]:
                    print(f"  - {rec}")
        
        # Generate multi-cluster report if needed
        if args.output:
            multi_report = checker.generate_health_report([report], args.output)
            print(f"\nDetailed report saved to: {args.output}")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
