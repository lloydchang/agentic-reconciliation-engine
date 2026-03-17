#!/usr/bin/env python3
"""
Simple Test Runner for Agent Tracing Evaluation Framework

Runs basic unit tests for the evaluation patterns without pytest dependencies.
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running Agent Tracing Evaluation Tests...")
    
    try:
        # Test imports
        print("✓ Testing imports...")
        from evaluators.monitoring_evaluator import AgentMonitoringEvaluator, IssueType, IssueSeverity
        from evaluators.auto_fix_evaluator import AutoFixManager, AutoFixAction
        from evaluators.health_check_evaluator import HealthCheckEvaluator
        from main import TracingEvaluationFramework
        print("✓ All imports successful")
        
        # Test basic monitoring evaluator
        print("✓ Testing monitoring evaluator...")
        monitor = AgentMonitoringEvaluator()
        
        # Test with sample traces
        sample_traces = [
            {
                "kubernetes": {
                    "pod_restarts": 8,
                    "pod_name": "agent-worker-1"
                },
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "skill_execution"
                },
                "agent": {
                    "conversation": [{"turn": i} for i in range(55)],
                    "tools": [{"name": "kubectl", "success": False}]
                }
            }
        ]
        
        report = monitor.generate_monitoring_report(sample_traces)
        
        # Verify report structure
        assert "correlation_id" in report
        assert "total_issues" in report
        assert "infrastructure_health" in report
        assert "temporal_health" in report
        assert "agent_health" in report
        print("✓ Monitoring evaluator working correctly")
        
        # Test auto-fix manager
        print("✓ Testing auto-fix manager...")
        auto_fix = AutoFixManager()
        
        critical_issue = {
            "id": "test-issue",
            "type": "agent_failure",
            "severity": "critical",
            "description": "Pod test-pod has restarted 15 times",
            "metrics": {"pod_name": "test-pod"}
        }
        
        should_apply = auto_fix._should_apply_fix(critical_issue)
        assert should_apply == True
        print("✓ Auto-fix manager working correctly")
        
        # Test health check evaluator
        print("✓ Testing health check evaluator...")
        health = HealthCheckEvaluator()
        
        health_traces = [
            {
                "kubernetes": {
                    "worker": {
                        "worker_id": "worker-1",
                        "active_connections": 5,
                        "memory_usage": 70,
                        "cpu_usage": 45,
                        "last_heartbeat": datetime.utcnow().isoformat()
                    }
                }
            }
        ]
        
        health_report = health.generate_health_report(health_traces)
        
        assert "worker_health" in health_report
        assert "overall_health_status" in health_report
        print("✓ Health check evaluator working correctly")
        
        # Test framework integration
        print("✓ Testing framework integration...")
        framework = TracingEvaluationFramework()
        
        # Verify all evaluators are available
        expected_evaluators = [
            "skill_invocation",
            "performance", 
            "cost",
            "monitoring",
            "health_check"
        ]
        
        for evaluator_name in expected_evaluators:
            assert evaluator_name in framework.evaluators
        
        # Test comprehensive evaluation
        results = framework.evaluate_traces(
            sample_traces, 
            evaluator_types=["monitoring", "health_check"]
        )
        
        assert "monitoring" in results
        assert "health_check" in results
        print("✓ Framework integration working correctly")
        
        print("\n🎉 All tests passed! Evaluation patterns are working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_auto_fix():
    """Test auto-fix with mocked subprocess calls"""
    print("✓ Testing auto-fix with mocked subprocess...")
    
    try:
        from unittest.mock import patch
        from evaluators.auto_fix_evaluator import AutoFixManager
        
        auto_fix = AutoFixManager()
        
        # Mock subprocess calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "success"
            
            issue = {
                "id": "test-mock-issue",
                "type": "agent_failure",
                "severity": "critical",
                "description": "Pod test-pod-mock has restarted 20 times",
                "metrics": {"pod_name": "test-pod-mock"}
            }
            
            result = auto_fix._fix_pod_restart(issue)
            
            # Verify fix attempt was recorded
            assert len(auto_fix.fix_history) == 1
            assert auto_fix.fix_history[0].target == "test-pod-mock"
            assert result["success"] == True
            
        print("✓ Mock auto-fix test passed")
        return True
        
    except Exception as e:
        print(f"❌ Mock auto-fix test failed: {str(e)}")
        return False

def test_issue_detection():
    """Test issue detection patterns"""
    print("✓ Testing issue detection patterns...")
    
    try:
        from evaluators.monitoring_evaluator import AgentMonitoringEvaluator, IssueType, IssueSeverity
        
        monitor = AgentMonitoringEvaluator()
        
        # Test pod restart detection
        restart_traces = [
            {"kubernetes": {"pod_restarts": 10, "pod_name": "test-pod"}}
        ]
        
        infra_health = monitor.evaluate_infrastructure_health(restart_traces)
        issues = infra_health["issues"]
        
        assert len(issues) > 0
        assert issues[0].type == IssueType.AGENT_FAILURE
        assert issues[0].severity == IssueSeverity.HIGH
        
        # Test workflow timeout detection
        timeout_traces = [
            {"temporal": {"status": "timeout", "workflow_type": "test-workflow"}}
        ]
        
        temporal_health = monitor.evaluate_temporal_health(timeout_traces)
        timeout_issues = temporal_health["timeout_issues"]
        
        assert len(timeout_issues) > 0
        assert timeout_issues[0].type == IssueType.WORKFLOW_TIMEOUT
        
        print("✓ Issue detection patterns working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Issue detection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Agent Tracing Evaluation Framework Tests\n")
    
    success = True
    
    # Run all tests
    success &= run_basic_tests()
    success &= test_mock_auto_fix()
    success &= test_issue_detection()
    
    if success:
        print("\n🎊 All evaluation pattern tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✓ Monitoring evaluator implemented and tested")
        print("  ✓ Auto-fix manager implemented and tested") 
        print("  ✓ Health check evaluator implemented and tested")
        print("  ✓ Framework integration verified")
        print("  ✓ Issue detection patterns validated")
        print("  ✓ Mock subprocess testing completed")
        print("\n🔧 All evaluation patterns from Temporal AI agents documentation are now functional!")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)
