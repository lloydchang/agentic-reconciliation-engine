#!/usr/bin/env python3
"""
Alert Summarization Script for Incident Summary Skill

This script processes monitoring alerts and generates structured summaries
for Cloud AI incident response and documentation.
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class AlertSummarizer:
    def __init__(self):
        self.severity_levels = {
            'critical': 4,
            'warning': 3,
            'info': 2,
            'debug': 1
        }
    
    def parse_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure alert data"""
        return {
            'timestamp': alert_data.get('timestamp', datetime.utcnow().isoformat()),
            'severity': alert_data.get('severity', 'info'),
            'service': alert_data.get('service', 'unknown'),
            'message': alert_data.get('message', ''),
            'labels': alert_data.get('labels', {}),
            'annotations': alert_data.get('annotations', {})
        }
    
    def generate_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate incident summary from multiple alerts"""
        if not alerts:
            return {'error': 'No alerts provided'}
        
        # Sort alerts by severity and timestamp
        sorted_alerts = sorted(alerts, key=lambda x: (
            self.severity_levels.get(x.get('severity', 'info'), 0),
            x.get('timestamp', '')
        ), reverse=True)
        
        # Extract key information
        affected_services = list(set(alert.get('service', 'unknown') for alert in sorted_alerts))
        max_severity = max(self.severity_levels.get(alert.get('severity', 'info'), 0) for alert in sorted_alerts)
        
        # Generate timeline
        timeline = []
        for alert in sorted_alerts[:10]:  # Limit to first 10 alerts
            timeline.append({
                'time': alert.get('timestamp', ''),
                'event': f"{alert.get('service', 'unknown')}: {alert.get('message', '')[:100]}...",
                'severity': alert.get('severity', 'info')
            })
        
        # Identify potential root causes
        potential_causes = self._identify_causes(sorted_alerts)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(sorted_alerts)
        
        return {
            'incident_id': f"inc-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            'summary': {
                'title': f"{'Critical' if max_severity == 4 else 'Warning' if max_severity == 3 else 'Info'}: {', '.join(affected_services)}",
                'severity': max_severity,
                'affected_services': affected_services,
                'alert_count': len(alerts),
                'first_alert': sorted_alerts[-1].get('timestamp', ''),
                'latest_alert': sorted_alerts[0].get('timestamp', '')
            },
            'timeline': timeline,
            'potential_causes': potential_causes,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _identify_causes(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Identify potential root causes from alert patterns"""
        causes = []
        
        # Common patterns
        error_patterns = {
            'CrashLoopBackOff': 'Pod restart loops detected',
            'ImagePullBackOff': 'Container image pull failures',
            'MemoryPressure': 'Insufficient memory resources',
            'DiskPressure': 'Insufficient disk space',
            'NetworkUnavailable': 'Network connectivity issues'
        }
        
        for alert in alerts:
            message = alert.get('message', '')
            for pattern, cause in error_patterns.items():
                if pattern in message:
                    if cause not in causes:
                        causes.append(cause)
        
        return causes[:5]  # Limit to top 5 potential causes
    
    def _generate_recommendations(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check for common issues
        for alert in alerts:
            message = alert.get('message', '').lower()
            service = alert.get('service', '')
            
            if 'crashloop' in message:
                recommendations.append(f"Check pod logs for {service}: kubectl logs -l app={service}")
            elif 'memory' in message:
                recommendations.append(f"Review memory limits for {service} and consider scaling")
            elif 'disk' in message:
                recommendations.append("Check node disk usage and clean up if needed")
            elif 'network' in message:
                recommendations.append("Verify network policies and service connectivity")
        
        # Add general recommendations
        if not recommendations:
            recommendations = [
                "Review recent deployments for potential causes",
                "Check cluster resource utilization",
                "Verify service dependencies and health"
            ]
        
        return recommendations[:5]  # Limit to top 5 recommendations

def main():
    """Main function to process alerts from stdin or file"""
    if len(sys.argv) < 2:
        print("Usage: python3 summarize_alerts.py <alert_file.json>")
        print("Or pipe JSON alerts to stdin")
        sys.exit(1)
    
    try:
        # Read alerts from file or stdin
        if sys.argv[1] == '-':
            # Read from stdin
            alerts_data = json.load(sys.stdin)
        else:
            # Read from file
            with open(sys.argv[1], 'r') as f:
                alerts_data = json.load(f)
        
        # Ensure we have a list of alerts
        if isinstance(alerts_data, dict):
            alerts = [alerts_data]
        else:
            alerts = alerts_data
        
        # Generate summary
        summarizer = AlertSummarizer()
        summary = summarizer.generate_summary(alerts)
        
        # Output JSON summary
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"Error processing alerts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
