#!/usr/bin/env python3
"""
Multi-Cloud Incident Summary Orchestrator

Cross-provider coordination for incident summary operations across multiple cloud environments.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from incident_summary_handler import get_incident_handler

logger = logging.getLogger(__name__)

@dataclass
class IncidentData:
    id: str
    title: str
    severity: str
    provider: str
    timestamp: datetime
    alerts: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]
    resources: List[Dict[str, Any]]

class MultiCloudIncidentOrchestrator:
    """Multi-cloud incident summary orchestration engine"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.handlers = {}
        self.incidents = []
        self.config = self._load_config(config_file)
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load orchestration configuration"""
        default_config = {
            'providers': {
                'aws': {'region': 'us-west-2', 'enabled': True},
                'azure': {'region': 'eastus', 'enabled': True},
                'gcp': {'region': 'us-central1', 'enabled': True},
                'onprem': {'region': 'default', 'enabled': True}
            },
            'incident_retention_days': 30,
            'alert_time_range_hours': 24,
            'max_concurrent_incidents': 50
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config
    
    def initialize_providers(self, providers: List[str]) -> Dict[str, bool]:
        """Initialize cloud provider handlers"""
        results = {}
        
        for provider in providers:
            try:
                if provider not in self.config['providers']:
                    logger.warning(f"Provider {provider} not in configuration")
                    results[provider] = False
                    continue
                
                if not self.config['providers'][provider]['enabled']:
                    logger.info(f"Provider {provider} is disabled")
                    results[provider] = False
                    continue
                
                region = self.config['providers'][provider]['region']
                handler = get_incident_handler(provider, region)
                
                if handler.initialize_client():
                    self.handlers[provider] = handler
                    results[provider] = True
                    logger.info(f"Provider {provider} initialized successfully")
                else:
                    results[provider] = False
                    logger.error(f"Failed to initialize provider {provider}")
                    
            except Exception as e:
                logger.error(f"Error initializing provider {provider}: {e}")
                results[provider] = False
        
        return results
    
    def collect_incident_data(self, incident_id: str, providers: List[str]) -> IncidentData:
        """Collect incident data from multiple providers"""
        logger.info(f"Collecting incident data for {incident_id}")
        
        all_alerts = []
        all_logs = []
        all_resources = []
        incident_severity = 'low'
        
        # Collect data from each provider in parallel
        futures = {}
        for provider in providers:
            if provider in self.handlers:
                future = self.executor.submit(self._collect_provider_data, provider, incident_id)
                futures[future] = provider
        
        for future in as_completed(futures):
            provider = futures[future]
            try:
                provider_data = future.result()
                all_alerts.extend(provider_data.get('alerts', []))
                all_logs.extend(provider_data.get('logs', []))
                all_resources.extend(provider_data.get('resources', []))
                
                # Update severity based on provider data
                provider_severity = self._calculate_provider_severity(provider_data)
                if self._compare_severity(provider_severity, incident_severity) > 0:
                    incident_severity = provider_severity
                    
            except Exception as e:
                logger.error(f"Failed to collect data from provider {provider}: {e}")
        
        # Create incident data object
        incident = IncidentData(
            id=incident_id,
            title=self._generate_incident_title(all_alerts, all_logs),
            severity=incident_severity,
            provider='multi-cloud',
            timestamp=datetime.utcnow(),
            alerts=all_alerts,
            logs=all_logs,
            resources=all_resources
        )
        
        self.incidents.append(incident)
        return incident
    
    def _collect_provider_data(self, provider: str, incident_id: str) -> Dict[str, Any]:
        """Collect incident data from a single provider"""
        handler = self.handlers[provider]
        
        try:
            # Get alerts
            time_range = f"{self.config['alert_time_range_hours']}h"
            alerts = handler.get_incident_alerts(time_range)
            
            # Get logs
            logs = handler.get_incident_logs(incident_id)
            
            # Get resource status
            resources = []
            for alert in alerts:
                if 'resource_id' in alert:
                    resource_status = handler.get_resource_status(alert['resource_id'])
                    resources.append(resource_status)
            
            return {
                'provider': provider,
                'alerts': alerts,
                'logs': logs,
                'resources': resources
            }
            
        except Exception as e:
            logger.error(f"Failed to collect data from provider {provider}: {e}")
            return {
                'provider': provider,
                'alerts': [],
                'logs': [],
                'resources': []
            }
    
    def _calculate_provider_severity(self, provider_data: Dict[str, Any]) -> str:
        """Calculate severity based on provider data"""
        alerts = provider_data.get('alerts', [])
        
        if not alerts:
            return 'low'
        
        # Check for critical alerts
        critical_count = len([a for a in alerts if a.get('severity') == 'critical'])
        if critical_count > 0:
            return 'critical'
        
        # Check for warning alerts
        warning_count = len([a for a in alerts if a.get('severity') == 'warning'])
        if warning_count > 5:
            return 'high'
        elif warning_count > 2:
            return 'medium'
        
        return 'low'
    
    def _compare_severity(self, severity1: str, severity2: str) -> int:
        """Compare two severity levels"""
        severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        return severity_order.get(severity1, 0) - severity_order.get(severity2, 0)
    
    def _generate_incident_title(self, alerts: List[Dict[str, Any]], logs: List[Dict[str, Any]]) -> str:
        """Generate incident title based on alerts and logs"""
        if not alerts and not logs:
            return "Multi-Cloud Incident"
        
        # Extract common themes
        services = set()
        error_types = set()
        
        for alert in alerts:
            if 'service' in alert:
                services.add(alert['service'])
            if 'message' in alert:
                message = alert['message'].lower()
                if 'timeout' in message:
                    error_types.add('timeout')
                elif 'connection' in message:
                    error_types.add('connection')
                elif 'memory' in message:
                    error_types.add('memory')
                elif 'disk' in message:
                    error_types.add('disk')
        
        # Generate title
        if services and error_types:
            return f"{'/'.join(services)} - {'/'.join(error_types)} Issues"
        elif services:
            return f"{'/'.join(services)} Service Issues"
        elif error_types:
            return f"{'/'.join(error_types)} Issues"
        else:
            return "Multi-Cloud Infrastructure Issues"
    
    def generate_incident_summary(self, incident_id: str) -> Dict[str, Any]:
        """Generate comprehensive incident summary"""
        incident = next((i for i in self.incidents if i.id == incident_id), None)
        
        if not incident:
            return {'error': f'Incident {incident_id} not found'}
        
        # Analyze timeline
        timeline = self._create_incident_timeline(incident)
        
        # Identify root causes
        root_causes = self._identify_root_causes(incident)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(incident, root_causes)
        
        # Calculate impact metrics
        impact_metrics = self._calculate_impact_metrics(incident)
        
        summary = {
            'incident_id': incident.id,
            'title': incident.title,
            'severity': incident.severity,
            'timestamp': incident.timestamp.isoformat(),
            'summary': {
                'total_alerts': len(incident.alerts),
                'total_logs': len(incident.logs),
                'affected_resources': len(incident.resources),
                'providers_involved': list(set(a.get('source', 'unknown') for a in incident.alerts))
            },
            'timeline': timeline,
            'root_causes': root_causes,
            'recommendations': recommendations,
            'impact_metrics': impact_metrics,
            'affected_services': list(set(a.get('service', 'unknown') for a in incident.alerts)),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return summary
    
    def _create_incident_timeline(self, incident: IncidentData) -> List[Dict[str, Any]]:
        """Create incident timeline"""
        timeline_events = []
        
        # Add alert events
        for alert in incident.alerts:
            timeline_events.append({
                'timestamp': alert.get('timestamp', incident.timestamp.isoformat()),
                'type': 'alert',
                'severity': alert.get('severity', 'unknown'),
                'source': alert.get('source', 'unknown'),
                'service': alert.get('service', 'unknown'),
                'message': alert.get('message', '')
            })
        
        # Add log events
        for log in incident.logs:
            if log.get('level') in ['ERROR', 'CRITICAL']:
                timeline_events.append({
                    'timestamp': log.get('timestamp', incident.timestamp.isoformat()),
                    'type': 'log',
                    'severity': 'error',
                    'source': log.get('source', 'unknown'),
                    'service': log.get('service', 'unknown'),
                    'message': log.get('message', '')
                })
        
        # Sort timeline
        timeline_events.sort(key=lambda x: x['timestamp'])
        
        return timeline_events[:20]  # Limit to 20 most recent events
    
    def _identify_root_causes(self, incident: IncidentData) -> List[str]:
        """Identify potential root causes"""
        root_causes = []
        
        # Analyze alerts for patterns
        alert_messages = [a.get('message', '').lower() for a in incident.alerts]
        log_messages = [l.get('message', '').lower() for l in incident.logs]
        all_messages = alert_messages + log_messages
        
        # Common patterns
        if any('timeout' in msg for msg in all_messages):
            root_causes.append('Network timeouts or service unresponsiveness')
        
        if any('memory' in msg or 'out of memory' in msg for msg in all_messages):
            root_causes.append('Memory exhaustion or memory leaks')
        
        if any('connection refused' in msg or 'connection failed' in msg for msg in all_messages):
            root_causes.append('Service connectivity issues or port conflicts')
        
        if any('disk' in msg or 'storage' in msg for msg in all_messages):
            root_causes.append('Disk space or storage issues')
        
        if any('permission' in msg or 'access denied' in msg for msg in all_messages):
            root_causes.append('Permission or access control issues')
        
        # If no specific patterns found
        if not root_causes:
            root_causes.append('Unknown - requires further investigation')
        
        return root_causes[:5]  # Limit to top 5 potential causes
    
    def _generate_recommendations(self, incident: IncidentData, root_causes: List[str]) -> List[Dict[str, Any]]:
        """Generate incident recommendations"""
        recommendations = []
        
        for cause in root_causes:
            if 'timeout' in cause.lower():
                recommendations.append({
                    'category': 'infrastructure',
                    'priority': 'high',
                    'action': 'Review service timeouts and implement circuit breakers',
                    'rationale': 'Multiple timeout events detected'
                })
            elif 'memory' in cause.lower():
                recommendations.append({
                    'category': 'application',
                    'priority': 'high',
                    'action': 'Optimize memory usage and increase memory limits',
                    'rationale': 'Memory exhaustion detected'
                })
            elif 'connection' in cause.lower():
                recommendations.append({
                    'category': 'network',
                    'priority': 'medium',
                    'action': 'Verify network connectivity and service discovery',
                    'rationale': 'Service connectivity issues detected'
                })
            elif 'disk' in cause.lower():
                recommendations.append({
                    'category': 'storage',
                    'priority': 'medium',
                    'action': 'Clean up disk space and monitor storage usage',
                    'rationale': 'Disk space issues detected'
                })
            elif 'permission' in cause.lower():
                recommendations.append({
                    'category': 'security',
                    'priority': 'low',
                    'action': 'Review and update access permissions',
                    'rationale': 'Permission issues detected'
                })
        
        # Add general recommendations
        recommendations.extend([
            {
                'category': 'monitoring',
                'priority': 'medium',
                'action': 'Enhance monitoring and alerting coverage',
                'rationale': 'Improve incident detection and response time'
            },
            {
                'category': 'documentation',
                'priority': 'low',
                'action': 'Update runbooks and documentation',
                'rationale': 'Improve incident response procedures'
            }
        ])
        
        return recommendations[:8]  # Limit to top 8 recommendations
    
    def _calculate_impact_metrics(self, incident: IncidentData) -> Dict[str, Any]:
        """Calculate incident impact metrics"""
        # Calculate affected services
        affected_services = list(set(a.get('service', 'unknown') for a in incident.alerts))
        
        # Calculate provider distribution
        provider_distribution = {}
        for alert in incident.alerts:
            source = alert.get('source', 'unknown')
            provider_distribution[source] = provider_distribution.get(source, 0) + 1
        
        # Calculate severity distribution
        severity_distribution = {}
        for alert in incident.alerts:
            severity = alert.get('severity', 'unknown')
            severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        return {
            'affected_services_count': len(affected_services),
            'affected_services': affected_services,
            'provider_distribution': provider_distribution,
            'severity_distribution': severity_distribution,
            'total_alerts': len(incident.alerts),
            'total_logs': len(incident.logs),
            'affected_resources': len(incident.resources)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Cloud Incident Orchestrator")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--incident-id", required=True, help="Incident ID")
    parser.add_argument("--providers", nargs="+", 
                       choices=['aws', 'azure', 'gcp', 'onprem'],
                       default=['aws', 'azure', 'gcp', 'onprem'], help="Cloud providers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = MultiCloudIncidentOrchestrator(args.config)
    
    # Initialize providers
    init_results = orchestrator.initialize_providers(args.providers)
    print(f"Provider initialization results: {init_results}")
    
    # Collect incident data
    incident = orchestrator.collect_incident_data(args.incident_id, args.providers)
    print(f"Collected incident data: {len(incident.alerts)} alerts, {len(incident.logs)} logs")
    
    # Generate summary
    summary = orchestrator.generate_incident_summary(args.incident_id)
    print(f"\nIncident Summary:\n{json.dumps(summary, indent=2)}")
    
    # Cleanup
    orchestrator.cleanup()

if __name__ == "__main__":
    main()
