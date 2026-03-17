#!/usr/bin/env python3
"""
Systems Debugger

General systems debugging tool for infrastructure components, applications,
and services across the technology stack.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from kubernetes import client, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemsDebugger:
    """Main debugger class for general systems analysis."""
    
    def __init__(self, namespace: str = "default", kubeconfig_path: Optional[str] = None):
        """Initialize debugger with target namespace."""
        self.namespace = namespace
        self.kubeconfig_path = kubeconfig_path
        
        # Load Kubernetes configuration
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            config.load_kube_config()
        
        # Initialize API clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    def debug_performance(self, target_component: str, time_range: str) -> Dict:
        """Debug performance issues for system components."""
        logger.info(f"Starting performance analysis for {target_component}...")
        
        results = {
            'component': target_component,
            'time_range': time_range,
            'metrics': {},
            'bottlenecks': [],
            'recommendations': []
        }
        
        # Collect performance metrics
        if target_component == "all" or target_component == "application":
            app_metrics = self._collect_application_metrics()
            results['metrics']['application'] = app_metrics
        
        if target_component == "all" or target_component == "infrastructure":
            infra_metrics = self._collect_infrastructure_metrics()
            results['metrics']['infrastructure'] = infra_metrics
        
        # Analyze bottlenecks
        results['bottlenecks'] = self._analyze_bottlenecks(results['metrics'])
        
        # Generate recommendations
        results['recommendations'] = self._generate_performance_recommendations(results)
        
        return results
    
    def debug_connectivity(self, target_component: str) -> Dict:
        """Debug connectivity issues for system components."""
        logger.info(f"Starting connectivity analysis for {target_component}...")
        
        results = {
            'component': target_component,
            'connectivity_matrix': {},
            'dns_resolution': {},
            'service_endpoints': {},
            'issues': [],
            'recommendations': []
        }
        
        # Test connectivity between components
        if target_component == "database":
            db_connectivity = self._test_database_connectivity()
            results['connectivity_matrix']['database'] = db_connectivity
        
        if target_component == "cache":
            cache_connectivity = self._test_cache_connectivity()
            results['connectivity_matrix']['cache'] = cache_connectivity
        
        if target_component == "all":
            all_connectivity = self._test_all_connectivity()
            results['connectivity_matrix'] = self._merge_connectivity_results(all_connectivity)
        
        # Check DNS resolution
        results['dns_resolution'] = self._check_dns_resolution()
        
        # Get service endpoints
        results['service_endpoints'] = self._get_service_endpoints()
        
        # Identify issues
        results['issues'] = self._identify_connectivity_issues(results)
        
        return results
    
    def debug_errors(self, target_component: str, time_range: str) -> Dict:
        """Debug error patterns and issues."""
        logger.info(f"Starting error analysis for {target_component}...")
        
        results = {
            'component': target_component,
            'time_range': time_range,
            'error_patterns': {},
            'log_analysis': {},
            'trend_analysis': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(target_component, time_range)
        results['error_patterns'] = error_patterns
        
        # Analyze logs
        log_analysis = self._analyze_logs(target_component, time_range)
        results['log_analysis'] = log_analysis
        
        # Trend analysis
        trend_analysis = self._analyze_error_trends(target_component, time_range)
        results['trend_analysis'] = trend_analysis
        
        # Identify critical issues
        results['critical_issues'] = self._identify_critical_errors(results)
        
        # Generate recommendations
        results['recommendations'] = self._generate_error_recommendations(results)
        
        return results
    
    def _collect_application_metrics(self) -> Dict:
        """Collect application-level performance metrics."""
        # Mock implementation - would collect real metrics
        return {
            'response_time': {'avg': 250, 'p95': 450, 'p99': 800},
            'throughput': {'requests_per_second': 1200},
            'error_rate': {'percentage': 2.5, 'count': 30},
            'cpu_usage': {'percentage': 65},
            'memory_usage': {'percentage': 78}
        }
    
    def _collect_infrastructure_metrics(self) -> Dict:
        """Collect infrastructure-level performance metrics."""
        # Mock implementation - would collect real metrics
        return {
            'node_cpu': {'avg': 45, 'max': 85},
            'node_memory': {'avg': 60, 'max': 92},
            'disk_io': {'read_iops': 1500, 'write_iops': 800},
            'network_io': {'rx_mbps': 250, 'tx_mbps': 180},
            'pod_restarts': {'total': 5, 'last_hour': 2}
        }
    
    def _analyze_bottlenecks(self, metrics: Dict) -> List[Dict]:
        """Identify performance bottlenecks from metrics."""
        bottlenecks = []
        
        # Check application bottlenecks
        if 'application' in metrics:
            app_metrics = metrics['application']
            if app_metrics['response_time']['p95'] > 500:
                bottlenecks.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'value': app_metrics['response_time']['p95'],
                    'threshold': 500
                })
            
            if app_metrics['error_rate']['percentage'] > 5:
                bottlenecks.append({
                    'type': 'high_error_rate',
                    'severity': 'critical',
                    'value': app_metrics['error_rate']['percentage'],
                    'threshold': 5
                })
        
        # Check infrastructure bottlenecks
        if 'infrastructure' in metrics:
            infra_metrics = metrics['infrastructure']
            if infra_metrics['node_memory']['max'] > 90:
                bottlenecks.append({
                    'type': 'high_memory_usage',
                    'severity': 'warning',
                    'value': infra_metrics['node_memory']['max'],
                    'threshold': 90
                })
        
        return bottlenecks
    
    def _generate_performance_recommendations(self, results: Dict) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        for bottleneck in results['bottlenecks']:
            if bottleneck['type'] == 'high_response_time':
                recommendations.append("Consider optimizing application code or adding horizontal scaling")
            elif bottleneck['type'] == 'high_error_rate':
                recommendations.append("Investigate error logs and fix underlying application issues")
            elif bottleneck['type'] == 'high_memory_usage':
                recommendations.append("Add more memory or optimize memory usage in applications")
        
        return recommendations
    
    def _test_database_connectivity(self) -> Dict:
        """Test database connectivity and performance."""
        # Mock implementation - would perform actual tests
        return {
            'connection_status': 'healthy',
            'response_time_ms': 25,
            'connection_pool': {'active': 8, 'idle': 12, 'max': 20},
            'replication_lag_seconds': 2
        }
    
    def _test_cache_connectivity(self) -> Dict:
        """Test cache connectivity and performance."""
        # Mock implementation - would perform actual tests
        return {
            'connection_status': 'healthy',
            'hit_rate_percentage': 85,
            'response_time_ms': 5,
            'memory_usage_percentage': 45
        }
    
    def _test_all_connectivity(self) -> Dict:
        """Test connectivity for all major components."""
        return {
            'database': self._test_database_connectivity(),
            'cache': self._test_cache_connectivity(),
            'external_apis': {'status': 'healthy', 'avg_latency_ms': 150}
        }
    
    def _merge_connectivity_results(self, results: Dict) -> Dict:
        """Merge connectivity test results."""
        return results
    
    def _check_dns_resolution(self) -> Dict:
        """Check DNS resolution for services."""
        # Mock implementation - would perform actual DNS checks
        return {
            'internal_services': {'resolved': True, 'latency_ms': 2},
            'external_services': {'resolved': True, 'latency_ms': 15}
        }
    
    def _get_service_endpoints(self) -> Dict:
        """Get current service endpoints."""
        try:
            services = self.core_v1.list_namespaced_service(self.namespace)
            endpoints = {}
            
            for svc in services.items:
                if svc.spec.type == "LoadBalancer":
                    endpoints[svc.metadata.name] = {
                        'type': 'LoadBalancer',
                        'endpoints': [f"{ip}:{port}" for ip, port in 
                                    [(ip.ip, port.port) for port in svc.spec.ports 
                                     for ip in svc.status.load_balancer.ingress or []]]
                    }
                elif svc.spec.type == "ClusterIP":
                    endpoints[svc.metadata.name] = {
                        'type': 'ClusterIP',
                        'cluster_ip': svc.spec.cluster_ip,
                        'ports': [(port.port, port.protocol) for port in svc.spec.ports]
                    }
            
            return endpoints
        except Exception as e:
            logger.error(f"Failed to get service endpoints: {e}")
            return {}
    
    def _identify_connectivity_issues(self, results: Dict) -> List[Dict]:
        """Identify connectivity issues from test results."""
        issues = []
        
        for component, metrics in results['connectivity_matrix'].items():
            if metrics.get('connection_status') != 'healthy':
                issues.append({
                    'component': component,
                    'issue': 'connection_failure',
                    'severity': 'critical'
                })
            
            if metrics.get('response_time_ms', 0) > 100:
                issues.append({
                    'component': component,
                    'issue': 'high_latency',
                    'severity': 'warning'
                })
        
        return issues
    
    def _analyze_error_patterns(self, component: str, time_range: str) -> Dict:
        """Analyze error patterns from logs."""
        # Mock implementation - would analyze actual logs
        return {
            'error_types': {
                'timeout_errors': 15,
                'connection_errors': 8,
                'authentication_errors': 3
            },
            'frequency': {'per_hour': 26},
            'trend': 'increasing'
        }
    
    def _analyze_logs(self, component: str, time_range: str) -> Dict:
        """Analyze logs for patterns and issues."""
        # Mock implementation - would analyze actual logs
        return {
            'total_logs': 15000,
            'error_logs': 390,
            'warning_logs': 1200,
            'info_logs': 13410,
            'error_rate_percentage': 2.6
        }
    
    def _analyze_error_trends(self, component: str, time_range: str) -> Dict:
        """Analyze error trends over time."""
        # Mock implementation - would analyze actual trends
        return {
            'trend_direction': 'increasing',
            'rate_of_change': '+15%',
            'peak_times': ['14:00-15:00', '20:00-21:00'],
            'correlation_with_load': True
        }
    
    def _identify_critical_errors(self, results: Dict) -> List[Dict]:
        """Identify critical errors requiring immediate attention."""
        critical_issues = []
        
        error_patterns = results.get('error_patterns', {})
        if error_patterns.get('frequency', {}).get('per_hour', 0) > 50:
            critical_issues.append({
                'type': 'high_error_frequency',
                'severity': 'critical',
                'value': error_patterns['frequency']['per_hour'],
                'threshold': 50
            })
        
        return critical_issues
    
    def _generate_error_recommendations(self, results: Dict) -> List[str]:
        """Generate error resolution recommendations."""
        recommendations = []
        
        error_patterns = results.get('error_patterns', {})
        if error_patterns.get('error_types', {}).get('timeout_errors', 0) > 10:
            recommendations.append("Investigate timeout issues and consider increasing timeout values")
        
        if error_patterns.get('error_types', {}).get('connection_errors', 0) > 5:
            recommendations.append("Check network connectivity and service health")
        
        return recommendations
    
    def auto_fix(self, issue_type: str, component: str) -> Dict:
        """Attempt automatic fixes for common issues."""
        logger.info(f"Attempting auto-fix for {issue_type} in {component}...")
        
        fixes_applied = []
        
        if issue_type == "connectivity" and component == "database":
            # Mock auto-fix: restart database connection pool
            fixes_applied.append("Restarted database connection pool")
        
        elif issue_type == "performance" and component == "application":
            # Mock auto-fix: clear application cache
            fixes_applied.append("Cleared application cache")
        
        return {
            'fixes_applied': fixes_applied,
            'success': True,
            'message': f"Applied {len(fixes_applied)} automatic fixes"
        }
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive debugging report."""
        report = []
        report.append("# Systems Debug Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Component: {results.get('component', 'N/A')}")
        report.append("")
        
        # Add metrics summary
        if 'metrics' in results:
            report.append("## Performance Metrics")
            for category, metrics in results['metrics'].items():
                report.append(f"### {category.title()}")
                for metric, value in metrics.items():
                    if isinstance(value, dict):
                        report.append(f"- {metric}: {json.dumps(value)}")
                    else:
                        report.append(f"- {metric}: {value}")
            report.append("")
        
        # Add bottlenecks
        if 'bottlenecks' in results and results['bottlenecks']:
            report.append("## Identified Bottlenecks")
            for bottleneck in results['bottlenecks']:
                severity_emoji = "🔴" if bottleneck['severity'] == 'critical' else "🟡"
                report.append(f"- {severity_emoji} {bottleneck['type']}: {bottleneck['value']} "
                            f"(threshold: {bottleneck['threshold']})")
            report.append("")
        
        # Add connectivity issues
        if 'issues' in results and results['issues']:
            report.append("## Connectivity Issues")
            for issue in results['issues']:
                severity_emoji = "🔴" if issue['severity'] == 'critical' else "🟡"
                report.append(f"- {severity_emoji} {issue['component']}: {issue['issue']}")
            report.append("")
        
        # Add recommendations
        if 'recommendations' in results and results['recommendations']:
            report.append("## Recommendations")
            for i, rec in enumerate(results['recommendations'], 1):
                report.append(f"{i}. {rec}")
        
        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Systems Debugger")
    parser.add_argument("--target-component", choices=["application", "database", "cache", "infrastructure", "all"],
                       required=True, help="Component to debug")
    parser.add_argument("--issue-type", choices=["performance", "connectivity", "errors"],
                       required=True, help="Type of issue to debug")
    parser.add_argument("--time-range", default="1h", 
                       help="Time range for analysis (e.g., 30m, 2h, 1d)")
    parser.add_argument("--namespace", default="default",
                       help="Kubernetes namespace to analyze")
    parser.add_argument("--generate-report", action="store_true",
                       help="Generate detailed report")
    parser.add_argument("--auto-fix", action="store_true",
                       help="Attempt automatic fixes")
    parser.add_argument("--include-dependencies", action="store_true",
                       help="Include dependency analysis")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize debugger
    debugger = SystemsDebugger(namespace=args.namespace)
    
    # Run appropriate analysis
    results = {}
    
    if args.issue_type == "performance":
        results = debugger.debug_performance(args.target_component, args.time_range)
    elif args.issue_type == "connectivity":
        results = debugger.debug_connectivity(args.target_component)
    elif args.issue_type == "errors":
        results = debugger.debug_errors(args.target_component, args.time_range)
    
    # Apply auto-fixes if requested
    if args.auto_fix:
        fix_results = debugger.auto_fix(args.issue_type, args.target_component)
        results['auto_fix'] = fix_results
    
    # Output results
    if args.generate_report:
        report = debugger.generate_report(results)
        print(report)
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
