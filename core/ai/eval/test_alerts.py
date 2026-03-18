#!/usr/bin/env python3
"""
Advanced Alerting System Test Script
Demonstrates alert capabilities and testing
"""

import asyncio
import sys
import json
from pathlib import Path

# Add framework to path
sys.path.append(str(Path(__file__).parent))

from main import TracingEvaluationFramework
from alerts.alert_manager import AlertRule, AlertSeverity, AlertManager
from alerts.api_server import create_alert_api

def test_alert_integration():
    """Test alert integration with evaluation framework"""
    print("🔔 Testing Alert Integration")
    print("=" * 40)
    
    # Initialize framework with alerts
    framework = TracingEvaluationFramework(enable_alerts=True)
    
    if not framework.alert_manager:
        print("❌ Alert manager not initialized")
        print("   Check configuration in config/alerts.json")
        return
    
    print("✅ Alert manager initialized")
    
    # Create test traces that will trigger alerts
    test_traces = [
        {
            "id": "test-trace-1",
            "timestamp": "2026-03-17T14:00:00Z",
            "events": [
                {
                    "name": "skill_invocation",
                    "timestamp": "2026-03-17T14:00:01Z",
                    "level": "ERROR",
                    "type": "SKILL_EXECUTION",
                    "input": {"operation": "deploy"},
                    "output": {"error": "Security policy violation"}
                }
            ],
            "attributes": {
                "operation_type": "deploy",
                "model": "gpt-4",
                "total_duration": 5000,
                "event_count": 1,
                "error_count": 1,
                "success_rate": 0.0
            }
        },
        {
            "id": "test-trace-2", 
            "timestamp": "2026-03-17T14:01:00Z",
            "events": [
                {
                    "name": "performance_check",
                    "timestamp": "2026-03-17T14:01:01Z",
                    "level": "WARNING",
                    "type": "PERFORMANCE",
                    "input": {"operation": "health_check"},
                    "output": {"response_time": 2000}
                }
            ],
            "attributes": {
                "operation_type": "health_check",
                "model": "gpt-4",
                "total_duration": 8000,
                "event_count": 1,
                "error_count": 0,
                "success_rate": 1.0
            }
        }
    ]
    
    print(f"📊 Created {len(test_traces)} test traces")
    
    # Run evaluation (should trigger alerts)
    print("\n🔍 Running evaluation with alerts...")
    results = framework.evaluate_traces(test_traces, ['security', 'performance'])
    
    # Wait a moment for async alert processing
    import time
    time.sleep(2)
    
    # Check alert metrics
    metrics = framework.get_alert_metrics()
    print(f"\n📊 Alert Metrics:")
    print(f"   Total alerts: {metrics.get('total_alerts', 0)}")
    print(f"   Active alerts: {metrics.get('active_alerts', 0)}")
    print(f"   Rules configured: {metrics.get('rules_configured', 0)}")
    
    # Show active alerts
    active_alerts = framework.get_alerts('active')
    if active_alerts:
        print(f"\n🚨 Active Alerts ({len(active_alerts)}):")
        for alert in active_alerts:
            severity_icon = {
                'critical': '🚨',
                'high': '⚠️',
                'medium': '🔸',
                'low': '🔹',
                'info': 'ℹ️'
            }.get(alert['severity'], '❓')
            
            print(f"   {severity_icon} [{alert['severity'].upper()}] {alert['title']}")
            print(f"      ID: {alert['id']}")
            print(f"      Description: {alert['description']}")
    else:
        print("\n✅ No active alerts")
    
    print("\n✅ Alert integration test completed")

def test_alert_rules():
    """Test custom alert rules"""
    print("\n🔧 Testing Custom Alert Rules")
    print("=" * 40)
    
    # Create alert manager
    from alerts.alert_manager import create_alert_manager
    alert_manager = create_alert_manager()
    
    # Create custom rule
    custom_rule = AlertRule(
        id="test-rule",
        name="Test Custom Rule",
        description="Test rule for demonstration",
        severity=AlertSeverity.MEDIUM,
        conditions=[
            {
                "metric_path": "summary.overall_score",
                "operator": "lt",
                "threshold": 0.8
            }
        ],
        actions=["email"],
        cooldown_minutes=5
    )
    
    alert_manager.add_rule(custom_rule)
    print("✅ Added custom alert rule")
    
    # Test rule evaluation
    test_results = {
        "summary": {
            "overall_score": 0.6,
            "evaluators_failed": 1
        },
        "evaluator_results": {
            "security": {"average_score": 0.4},
            "performance": {"average_score": 0.7}
        }
    }
    
    should_trigger = custom_rule.evaluate(test_results)
    print(f"🎯 Rule evaluation result: {'TRIGGER' if should_trigger else 'NO TRIGGER'}")
    
    # Process with alert manager
    asyncio.run(alert_manager.process_evaluation_results(test_results, "test-eval"))
    
    # Check results
    active_alerts = alert_manager.get_active_alerts()
    print(f"📊 Active alerts after rule test: {len(active_alerts)}")
    
    if active_alerts:
        latest_alert = active_alerts[-1]
        print(f"   Latest: {latest_alert.title} ({latest_alert.severity.value})")

def test_alert_api():
    """Test alert API endpoints"""
    print("\n🌐 Testing Alert API")
    print("=" * 40)
    
    try:
        # Create alert API
        api = create_alert_api('config/alerts.json')
        
        # Test health check
        print("✅ Alert API created successfully")
        print("   Health endpoint: http://localhost:8081/health")
        print("   Alerts endpoint: http://localhost:8081/alerts")
        print("   Rules endpoint: http://localhost:8081/rules")
        print("   Metrics endpoint: http://localhost:8081/metrics")
        
        print("\n📝 To test API endpoints:")
        print("   # Start API server:")
        print("   python alerts/api_server.py")
        print("")
        print("   # Test endpoints:")
        print("   curl http://localhost:8081/health")
        print("   curl http://localhost:8081/alerts")
        print("   curl http://localhost:8081/metrics")
        
    except Exception as e:
        print(f"❌ Alert API test failed: {e}")

def demonstrate_cli_usage():
    """Demonstrate CLI alert commands"""
    print("\n💻 CLI Alert Commands")
    print("=" * 40)
    
    examples = [
        {
            "description": "Show alert status and metrics",
            "command": "python cli.py --alerts"
        },
        {
            "description": "Show alert history",
            "command": "python cli.py --alerts --alert-type history"
        },
        {
            "description": "Acknowledge an alert",
            "command": "python cli.py --acknowledge-alert low-overall-score_1647571200"
        },
        {
            "description": "Resolve an alert",
            "command": "python cli.py --resolve-alert low-overall-score_1647571200"
        },
        {
            "description": "Run evaluation with alerts disabled",
            "command": "python cli.py --file traces.json --disable-alerts"
        },
        {
            "description": "Trigger test alert via API",
            "command": "curl -X POST http://localhost:8081/test -H 'Content-Type: application/json' -d '{\"overall_score\": 0.2}'"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}:")
        print(f"   {example['command']}")

def show_configuration_guide():
    """Show configuration guide"""
    print("\n⚙️  Alert Configuration Guide")
    print("=" * 40)
    
    config_info = [
        {
            "file": "config/alerts.json",
            "description": "Main alert configuration",
            "key_settings": [
                "actions.email - SMTP settings for email alerts",
                "actions.slack - Slack webhook configuration", 
                "actions.webhook - Generic webhook settings",
                "rules.enable_default_rules - Enable built-in rules",
                "settings.max_alerts_per_hour - Rate limiting"
            ]
        },
        {
            "file": "Environment Variables",
            "description": "Runtime configuration",
            "key_settings": [
                "LANGFUSE_API_KEY - For Langfuse integration",
                "ALERT_SMTP_HOST - SMTP server for email alerts",
                "ALERT_SLACK_WEBHOOK - Slack webhook URL",
                "ALERT_WEBHOOK_URL - Generic webhook endpoint"
            ]
        }
    ]
    
    for config in config_info:
        print(f"\n{config['file']}:")
        print(f"   Description: {config['description']}")
        print("   Key settings:")
        for setting in config['key_settings']:
            print(f"   - {setting}")

def main():
    """Main test function"""
    print("🚀 Advanced Alerting System Test Suite")
    print("=" * 50)
    
    # Run tests
    test_alert_integration()
    test_alert_rules()
    test_alert_api()
    
    # Show usage information
    demonstrate_cli_usage()
    show_configuration_guide()
    
    print("\n📚 Additional Resources:")
    print("   - Documentation: docs/AI-AGENT-EVALUATION-FRAMEWORK.md")
    print("   - Alert API: alerts/api_server.py")
    print("   - Alert Manager: alerts/alert_manager.py")
    print("   - Configuration: config/alerts.json")
    
    print("\n✅ Alerting system test completed successfully!")

if __name__ == "__main__":
    main()
