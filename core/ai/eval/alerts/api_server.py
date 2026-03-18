#!/usr/bin/env python3
"""
Alert API Server for AI Agent Evaluation Framework
REST API for managing alerts and alert rules
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

from alerts.alert_manager import AlertManager, AlertRule, AlertSeverity, create_alert_manager

logger = logging.getLogger(__name__)

class AlertAPI:
    """REST API for alert management"""
    
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'alert-api'
            })
        
        @self.app.route('/alerts', methods=['GET'])
        def get_alerts():
            """Get alerts"""
            alert_type = request.args.get('type', 'active')
            limit = int(request.args.get('limit', 100))
            
            if alert_type == 'active':
                alerts = self.alert_manager.get_active_alerts()
            elif alert_type == 'history':
                alerts = self.alert_manager.get_alert_history(limit)
            else:
                return jsonify({'error': 'Invalid alert type'}), 400
            
            return jsonify({
                'alerts': [alert.to_dict() for alert in alerts],
                'count': len(alerts),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.app.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
        def acknowledge_alert(alert_id):
            """Acknowledge an alert"""
            data = request.get_json() or {}
            acknowledged_by = data.get('acknowledged_by', 'unknown')
            
            success = self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)
            
            if success:
                return jsonify({
                    'message': 'Alert acknowledged',
                    'alert_id': alert_id,
                    'acknowledged_by': acknowledged_by,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({'error': 'Alert not found'}), 404
        
        @self.app.route('/alerts/<alert_id>/resolve', methods=['POST'])
        def resolve_alert(alert_id):
            """Resolve an alert"""
            success = self.alert_manager.resolve_alert(alert_id)
            
            if success:
                return jsonify({
                    'message': 'Alert resolved',
                    'alert_id': alert_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({'error': 'Alert not found'}), 404
        
        @self.app.route('/rules', methods=['GET'])
        def get_rules():
            """Get alert rules"""
            rules = {}
            for rule_id, rule in self.alert_manager.rules.items():
                rules[rule_id] = {
                    'id': rule.id,
                    'name': rule.name,
                    'description': rule.description,
                    'severity': rule.severity.value,
                    'enabled': rule.enabled,
                    'conditions': rule.conditions,
                    'actions': rule.actions,
                    'cooldown_minutes': rule.cooldown_minutes,
                    'tags': rule.tags
                }
            
            return jsonify({
                'rules': rules,
                'count': len(rules),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.app.route('/rules', methods=['POST'])
        def create_rule():
            """Create a new alert rule"""
            try:
                data = request.get_json()
                
                rule = AlertRule(
                    id=data['id'],
                    name=data['name'],
                    description=data['description'],
                    severity=AlertSeverity(data['severity']),
                    enabled=data.get('enabled', True),
                    conditions=data.get('conditions', []),
                    actions=data.get('actions', []),
                    cooldown_minutes=data.get('cooldown_minutes', 15),
                    tags=data.get('tags', [])
                )
                
                self.alert_manager.add_rule(rule)
                
                return jsonify({
                    'message': 'Rule created',
                    'rule_id': rule.id,
                    'timestamp': datetime.utcnow().isoformat()
                }), 201
                
            except Exception as e:
                logger.error(f"Error creating rule: {e}")
                return jsonify({'error': str(e)}), 400
        
        @self.app.route('/rules/<rule_id>', methods=['DELETE'])
        def delete_rule(rule_id):
            """Delete an alert rule"""
            success = self.alert_manager.remove_rule(rule_id)
            
            if success:
                return jsonify({
                    'message': 'Rule deleted',
                    'rule_id': rule_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                return jsonify({'error': 'Rule not found'}), 404
        
        @self.app.route('/rules/<rule_id>/toggle', methods=['POST'])
        def toggle_rule(rule_id):
            """Toggle alert rule enabled status"""
            if rule_id not in self.alert_manager.rules:
                return jsonify({'error': 'Rule not found'}), 404
            
            rule = self.alert_manager.rules[rule_id]
            rule.enabled = not rule.enabled
            
            return jsonify({
                'message': f'Rule {"enabled" if rule.enabled else "disabled"}',
                'rule_id': rule_id,
                'enabled': rule.enabled,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.app.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get alert system metrics"""
            metrics = self.alert_manager.get_metrics()
            return jsonify(metrics)
        
        @self.app.route('/test', methods=['POST'])
        def test_alert():
            """Trigger a test alert"""
            try:
                data = request.get_json()
                
                # Create test evaluation results that will trigger alerts
                test_results = {
                    'summary': {
                        'overall_score': data.get('overall_score', 0.3),
                        'evaluators_failed': data.get('evaluators_failed', 3)
                    },
                    'evaluator_results': {
                        'security': {
                            'average_score': data.get('security_score', 0.2)
                        },
                        'performance': {
                            'average_score': data.get('performance_score', 0.4)
                        },
                        'compliance': {
                            'average_score': data.get('compliance_score', 0.5)
                        }
                    }
                }
                
                # Process test results
                evaluation_id = f"test_{int(datetime.utcnow().timestamp())}"
                asyncio.create_task(
                    self.alert_manager.process_evaluation_results(test_results, evaluation_id)
                )
                
                return jsonify({
                    'message': 'Test alert triggered',
                    'evaluation_id': evaluation_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error triggering test alert: {e}")
                return jsonify({'error': str(e)}), 400
    
    def run(self, host: str = '0.0.0.0', port: int = 8081, debug: bool = False):
        """Run the alert API server"""
        logger.info(f"Starting Alert API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def create_alert_api(config_path: Optional[str] = None) -> AlertAPI:
    """Create alert API with configuration"""
    alert_manager = create_alert_manager(config_path)
    return AlertAPI(alert_manager)

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run API
    api = create_alert_api('config/alerts.json')
    api.run(host='0.0.0.0', port=8081)
