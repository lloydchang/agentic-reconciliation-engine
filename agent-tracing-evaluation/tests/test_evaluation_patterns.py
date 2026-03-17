#!/usr/bin/env python3
"""
Comprehensive Test Suite for Agent Tracing Evaluation Framework

Tests all evaluation patterns including monitoring, auto-fix, health checks,
and integration with existing debugging knowledge base.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import evaluators
from evaluators.monitoring_evaluator import AgentMonitoringEvaluator, Issue, IssueType, IssueSeverity
from evaluators.auto_fix_evaluator import AutoFixManager, FixAttempt, AutoFixAction
from evaluators.health_check_evaluator import HealthCheckEvaluator, HealthMetric, ConversationHealth

class TestAgentMonitoringEvaluator(unittest.TestCase):
    """Test suite for AgentMonitoringEvaluator"""

    def setUp(self):
        self.evaluator = AgentMonitoringEvaluator()

    def test_evaluate_infrastructure_health(self):
        """Test infrastructure health evaluation"""
        traces = [
            {
                "kubernetes": {
                    "pod_restarts": 10,
                    "pod_name": "agent-worker-1"
                }
            },
            {
                "kubernetes": {
                    "resources": {
                        "cpu_usage_percent": 95,
                        "memory_usage_percent": 90
                    },
                    "pod_name": "agent-worker-2"
                }
            }
        ]

        results = self.evaluator.evaluate_infrastructure_health(traces)

        # Should detect pod restart issue
        self.assertEqual(len(results["issues"]), 2)
        
        # Check pod restart issue
        restart_issue = results["issues"][0]
        self.assertEqual(restart_issue.type, IssueType.AGENT_FAILURE)
        self.assertEqual(restart_issue.severity, IssueSeverity.HIGH)
        self.assertIn("10 times", restart_issue.description)

    def test_evaluate_temporal_health(self):
        """Test temporal workflow health evaluation"""
        traces = [
            {
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "agent_execution"
                }
            },
            {
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "agent_execution"
                },
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "agent_execution"
                }
            }
        ]

        results = self.evaluator.evaluate_temporal_health(traces)

        # Should detect workflow timeout issue
        self.assertEqual(len(results["timeout_issues"]), 3)
        
        # Check timeout issue
        timeout_issue = results["timeout_issues"][0]
        self.assertEqual(timeout_issue.type, IssueType.WORKFLOW_TIMEOUT)
        self.assertEqual(timeout_issue.severity, IssueSeverity.MEDIUM)

    def test_evaluate_agent_health(self):
        """Test agent-specific health evaluation"""
        traces = [
            {
                "agent": {
                    "conversation": [
                        {"turn": 1}, {"turn": 2}, {"turn": 3}, {"turn": 4}, {"turn": 5},
                        {"turn": 6}, {"turn": 7}, {"turn": 8}, {"turn": 9}, {"turn": 10},
                        {"turn": 11}, {"turn": 12}, {"turn": 13}, {"turn": 14}, {"turn": 15},
                        {"turn": 16}, {"turn": 17}, {"turn": 18}, {"turn": 19}, {"turn": 20},
                        {"turn": 21}, {"turn": 22}, {"turn": 23}, {"turn": 24}, {"turn": 25},
                        {"turn": 26}, {"turn": 27}, {"turn": 28}, {"turn": 29}, {"turn": 30},
                        {"turn": 31}, {"turn": 32}, {"turn": 33}, {"turn": 34}, {"turn": 35},
                        {"turn": 36}, {"turn": 37}, {"turn": 38}, {"turn": 39}, {"turn": 40},
                        {"turn": 41}, {"turn": 42}, {"turn": 43}, {"turn": 44}, {"turn": 45},
                        {"turn": 46}, {"turn": 47}, {"turn": 48}, {"turn": 49}, {"turn": 50},
                        {"turn": 51}
                    ]
                },
                "trace_id": "test-trace-1"
            },
            {
                "agent": {
                    "tools": [
                        {"name": "kubectl", "success": False},
                        {"name": "kubectl", "success": False},
                        {"name": "kubectl", "success": True},
                        {"name": "kubectl", "success": True}
                    ]
                }
            }
        ]

        results = self.evaluator.evaluate_agent_health(traces)

        # Should detect long conversation and low tool success rate
        self.assertEqual(len(results["issues"]), 2)
        
        # Check conversation length issue
        conv_issue = results["issues"][0]
        self.assertEqual(conv_issue.type, IssueType.PERFORMANCE)
        self.assertEqual(conv_issue.severity, IssueSeverity.MEDIUM)

    def test_generate_monitoring_report(self):
        """Test comprehensive monitoring report generation"""
        traces = [
            {
                "kubernetes": {
                    "pod_restarts": 10,
                    "pod_name": "agent-worker-1"
                },
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "agent_execution"
                },
                "agent": {
                    "conversation": [{"turn": 1}, {"turn": 2}]
                }
            }
        ]

        report = self.evaluator.generate_monitoring_report(traces)

        # Verify report structure
        self.assertIn("correlation_id", report)
        self.assertIn("timestamp", report)
        self.assertIn("infrastructure_health", report)
        self.assertIn("temporal_health", report)
        self.assertIn("agent_health", report)
        self.assertIn("total_issues", report)
        self.assertIn("critical_issues", report)
        self.assertIn("auto_fix_results", report)
        self.assertIn("recommendations", report)

        # Verify correlation ID tracking
        self.assertIn(report["correlation_id"], self.evaluator.correlation_ids)

    def test_llm_performance_analysis(self):
        """Test LLM performance metrics analysis"""
        traces = [
            {
                "llm": {
                    "response_time": 2.5,
                    "tokens_used": 150,
                    "model": "gpt-4",
                    "error": None
                }
            },
            {
                "llm": {
                    "response_time": 1.8,
                    "tokens_used": 100,
                    "model": "gpt-3.5-turbo",
                    "error": None
                }
            },
            {
                "llm": {
                    "response_time": 3.2,
                    "tokens_used": 200,
                    "model": "gpt-4",
                    "error": "rate_limit_exceeded"
                }
            }
        ]

        metrics = self.evaluator._analyze_llm_performance(traces)

        # Verify metrics calculation
        self.assertEqual(metrics["total_tokens"], 450)
        self.assertAlmostEqual(metrics["average_response_time"], 2.5, places=1)
        self.assertAlmostEqual(metrics["error_rate"], 33.33, places=1)
        self.assertEqual(metrics["model_usage"]["gpt-4"], 2)
        self.assertEqual(metrics["model_usage"]["gpt-3.5-turbo"], 1)


class TestAutoFixManager(unittest.TestCase):
    """Test suite for AutoFixManager"""

    def setUp(self):
        self.auto_fix_manager = AutoFixManager()

    @patch('subprocess.run')
    def test_fix_pod_restart(self, mock_run):
        """Test pod restart auto-fix"""
        # Mock successful kubectl delete
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "pod 'test-pod' deleted"

        issue = {
            "id": "test-issue-1",
            "type": "agent_failure",
            "description": "Pod test-pod has restarted 10 times",
            "metrics": {"pod_name": "test-pod"}
        }

        result = self.auto_fix_manager._fix_pod_restart(issue)

        # Verify fix attempt was recorded
        self.assertEqual(len(self.auto_fix_manager.fix_history), 1)
        fix_attempt = self.auto_fix_manager.fix_history[0]
        self.assertEqual(fix_attempt.action, AutoFixAction.RESTART_POD)
        self.assertEqual(fix_attempt.target, "test-pod")

        # Verify kubectl was called
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_fix_workflow_timeout(self, mock_run):
        """Test workflow timeout auto-fix"""
        # Mock successful temporal workflow terminate
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Workflow terminated"

        issue = {
            "id": "test-issue-2",
            "type": "workflow_timeout",
            "metrics": {"workflow_id": "test-workflow-123"}
        }

        result = self.auto_fix_manager._fix_workflow_timeout(issue)

        # Verify fix attempt was recorded
        self.assertEqual(len(self.auto_fix_manager.fix_history), 1)
        fix_attempt = self.auto_fix_manager.fix_history[0]
        self.assertEqual(fix_attempt.action, AutoFixAction.CLEAR_WORKFLOW)
        self.assertEqual(fix_attempt.target, "test-workflow-123")

    @patch('subprocess.run')
    def test_fix_resource_exhaustion(self, mock_run):
        """Test resource exhaustion auto-fix"""
        # Mock successful kubectl patch
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "deployment patched"

        issue = {
            "id": "test-issue-3",
            "type": "resource_exhaustion",
            "metrics": {"deployment_name": "agent-deployment"}
        }

        result = self.auto_fix_manager._fix_resource_exhaustion(issue)

        # Verify fix attempt was recorded
        self.assertEqual(len(self.auto_fix_manager.fix_history), 1)
        fix_attempt = self.auto_fix_manager.fix_history[0]
        self.assertEqual(fix_attempt.action, AutoFixAction.SCALE_RESOURCES)
        self.assertEqual(fix_attempt.target, "agent-deployment")

    def test_backoff_prevention(self):
        """Test backoff period prevents repeated fixes"""
        # Add a recent fix attempt
        recent_fix = FixAttempt(
            action=AutoFixAction.RESTART_POD,
            target="test-pod",
            parameters={},
            timestamp=datetime.utcnow() - timedelta(minutes=2)  # 2 minutes ago
        )
        self.auto_fix_manager.fix_history.append(recent_fix)

        # Try to apply same fix type again
        issue = {
            "id": "test-issue-4",
            "type": "agent_failure",
            "severity": "medium",  # Not critical, so backoff applies
            "description": "Pod test-pod has restarted 5 times"
        }

        should_apply = self.auto_fix_manager._should_apply_fix(issue)
        self.assertFalse(should_apply)  # Should be prevented by backoff

    def test_critical_issues_bypass_backoff(self):
        """Test critical issues bypass backoff period"""
        # Add a recent fix attempt
        recent_fix = FixAttempt(
            action=AutoFixAction.RESTART_POD,
            target="test-pod",
            parameters={},
            timestamp=datetime.utcnow() - timedelta(minutes=2)
        )
        self.auto_fix_manager.fix_history.append(recent_fix)

        # Try to apply critical fix
        issue = {
            "id": "test-issue-5",
            "type": "agent_failure",
            "severity": "critical",  # Critical, so bypass backoff
            "description": "Pod test-pod has restarted 20 times"
        }

        should_apply = self.auto_fix_manager._should_apply_fix(issue)
        self.assertTrue(should_apply)  # Should bypass backoff

    def test_apply_fixes_for_issues(self):
        """Test applying fixes for multiple issues"""
        issues = [
            {
                "id": "test-issue-6",
                "type": "agent_failure",
                "severity": "critical",
                "description": "Pod test-pod-1 has restarted 15 times",
                "metrics": {"pod_name": "test-pod-1"}
            },
            {
                "id": "test-issue-7",
                "type": "workflow_timeout",
                "severity": "high",
                "description": "Workflow test-workflow-1 timed out",
                "metrics": {"workflow_id": "test-workflow-1"}
            }
        ]

        # Mock subprocess calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            results = self.auto_fix_manager.apply_fixes_for_issues(issues)

            # Verify results
            self.assertEqual(results["fixes_applied"], 2)
            self.assertEqual(results["fixes_failed"], 0)
            self.assertEqual(len(results["fix_details"]), 2)


class TestHealthCheckEvaluator(unittest.TestCase):
    """Test suite for HealthCheckEvaluator"""

    def setUp(self):
        self.evaluator = HealthCheckEvaluator()

    def test_evaluate_worker_health(self):
        """Test worker health evaluation"""
        traces = [
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
            },
            {
                "kubernetes": {
                    "worker": {
                        "worker_id": "worker-2",
                        "active_connections": 3,
                        "memory_usage": 85,
                        "cpu_usage": 65,
                        "last_heartbeat": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
                    }
                }
            }
        ]

        results = self.evaluator.evaluate_worker_health(traces)

        # Verify worker status
        self.assertEqual(len(results["worker_status"]), 2)
        self.assertEqual(results["worker_status"]["worker-1"]["status"], "healthy")
        self.assertEqual(results["worker_status"]["worker-2"]["status"], "warning")

    def test_evaluate_conversation_health(self):
        """Test conversation health evaluation"""
        traces = [
            {
                "agent": {
                    "conversation": {
                        "conversation_id": "conv-1",
                        "completed": True,
                        "start_time": "2023-01-01T10:00:00Z",
                        "end_time": "2023-01-01T10:05:00Z",
                        "turns": 10,
                        "error": None
                    }
                }
            },
            {
                "agent": {
                    "conversation": {
                        "conversation_id": "conv-2",
                        "completed": False,
                        "start_time": "2023-01-01T09:00:00Z",
                        "turns": 5,
                        "last_activity": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                        "error": "timeout_error"
                    }
                }
            }
        ]

        results = self.evaluator.evaluate_conversation_health(traces)

        # Verify conversation tracking
        self.assertEqual(results["completion_tracking"]["total_conversations"], 2)
        self.assertEqual(results["completion_tracking"]["completed_conversations"], 1)
        self.assertEqual(results["completion_tracking"]["completion_rate"], 0.5)

        # Verify stuck conversation detection
        self.assertEqual(len(results["stuck_conversations"]), 1)
        self.assertEqual(results["stuck_conversations"][0]["conversation_id"], "conv-2")

    def test_evaluate_system_readiness(self):
        """Test system readiness evaluation"""
        traces = [
            {
                "system": {
                    "components": [
                        {"name": "database", "ready": True},
                        {"name": "redis", "ready": True},
                        {"name": "temporal", "ready": False}
                    ]
                },
                "blocking_issues": ["database_connection_failed"]
            }
        ]

        results = self.evaluator.evaluate_system_readiness(traces)

        # Verify component readiness
        self.assertEqual(len(results["components_ready"]), 2)
        self.assertIn("database", results["components_ready"])
        self.assertIn("redis", results["components_ready"])

        # Verify blocking issues
        self.assertEqual(len(results["blocking_issues"]), 1)
        self.assertIn("database_connection_failed", results["blocking_issues"])

        # Verify readiness score calculation
        self.assertAlmostEqual(results["readiness_score"], 2/3, places=2)
        self.assertEqual(results["system_status"], "degraded")

    def test_generate_health_report(self):
        """Test comprehensive health report generation"""
        traces = [
            {
                "kubernetes": {
                    "worker": {
                        "worker_id": "worker-1",
                        "active_connections": 5,
                        "memory_usage": 70,
                        "cpu_usage": 45,
                        "last_heartbeat": datetime.utcnow().isoformat()
                    }
                },
                "agent": {
                    "conversation": {
                        "conversation_id": "conv-1",
                        "completed": True,
                        "turns": 10
                    }
                },
                "system": {
                    "components": [
                        {"name": "database", "ready": True}
                    ]
                }
            }
        ]

        report = self.evaluator.generate_health_report(traces)

        # Verify report structure
        self.assertIn("timestamp", report)
        self.assertIn("correlation_id", report)
        self.assertIn("worker_health", report)
        self.assertIn("conversation_health", report)
        self.assertIn("system_readiness", report)
        self.assertIn("overall_health_status", report)
        self.assertIn("recommendations", report)

    def test_health_score_calculation(self):
        """Test health score calculation"""
        worker_metrics = {"worker-1": {"status": "healthy"}, "worker-2": {"status": "warning"}}
        readiness = {"total_probes": 4, "passing_probes": 3}
        liveness = {"total_probes": 4, "passing_probes": 4}
        resources = {"issues": []}

        score = self.evaluator._calculate_health_score(worker_metrics, readiness, liveness, resources)

        # Verify score calculation (should be between 0 and 1)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestIntegrationWithDebuggingKnowledge(unittest.TestCase):
    """Test integration with existing debugging knowledge base"""

    def setUp(self):
        self.monitoring_evaluator = AgentMonitoringEvaluator()
        self.auto_fix_manager = AutoFixManager()
        self.health_evaluator = HealthCheckEvaluator()

    def test_debugging_pattern_correlation(self):
        """Test correlation with debugging patterns from memory"""
        # Create traces that match known debugging patterns
        traces = [
            {
                "kubernetes": {
                    "pod_restarts": 8,
                    "pod_name": "temporal-worker-1"
                },
                "temporal": {
                    "status": "timeout",
                    "workflow_type": "skill_execution"
                },
                "agent": {
                    "conversation": [{"turn": i} for i in range(60)],  # Long conversation
                    "tools": [
                        {"name": "kubectl", "success": False},
                        {"name": "kubectl", "success": False},
                        {"name": "kubectl", "success": True}
                    ]
                }
            }
        ]

        # Run monitoring evaluation
        monitoring_report = self.monitoring_evaluator.generate_monitoring_report(traces)

        # Verify issues match known patterns
        issues = monitoring_report["total_issues"]
        self.assertGreater(issues, 0)

        # Verify recommendations include debugging knowledge
        recommendations = monitoring_report["recommendations"]
        self.assertTrue(len(recommendations) > 0)

    def test_auto_fix_safety_integration(self):
        """Test auto-fix safety mechanisms align with debugging knowledge"""
        # Create critical issue that should trigger auto-fix
        critical_issue = {
            "id": "critical-pod-failure",
            "type": "agent_failure",
            "severity": "critical",
            "description": "Pod temporal-worker-1 has restarted 25 times",
            "metrics": {"pod_name": "temporal-worker-1"}
        }

        # Mock subprocess for safe testing
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0

            # Apply fix
            result = self.auto_fix_manager._fix_pod_restart(critical_issue)

            # Verify fix was applied safely
            self.assertTrue(result["success"])
            self.assertEqual(len(self.auto_fix_manager.fix_history), 1)

            # Verify backoff prevents repeated fixes
            should_apply_again = self.auto_fix_manager._should_apply_fix({
                "id": "another-issue",
                "type": "agent_failure", 
                "severity": "medium",
                "description": "Pod temporal-worker-1 has restarted 6 times"
            })
            self.assertFalse(should_apply_again)

    def test_health_monitoring_integration(self):
        """Test health monitoring integrates with debugging endpoints"""
        traces = [
            {
                "kubernetes": {
                    "readiness_probe": {
                        "status": "passing",
                        "component": "agent-worker"
                    },
                    "liveness_probe": {
                        "status": "passing",
                        "component": "agent-worker"
                    },
                    "resources": {
                        "cpu_usage_percent": 92,
                        "memory_usage_percent": 88
                    }
                }
            }
        ]

        health_report = self.health_evaluator.generate_health_report(traces)

        # Verify health metrics align with debugging knowledge
        worker_health = health_report["worker_health"]
        self.assertIn("readiness_probes", worker_health)
        self.assertIn("liveness_probes", worker_health)
        self.assertIn("resource_health", worker_health)

        # Verify resource health warnings
        resource_health = worker_health["resource_health"]
        self.assertEqual(resource_health["cpu_health"], "warning")
        self.assertEqual(resource_health["memory_health"], "warning")


class TestFrameworkIntegration(unittest.TestCase):
    """Test integration of all evaluators in the main framework"""

    def setUp(self):
        # Import main framework
        from main import TracingEvaluationFramework
        self.framework = TracingEvaluationFramework()

    def test_all_evaluators_available(self):
        """Test all evaluators are properly integrated"""
        expected_evaluators = [
            "skill_invocation",
            "performance", 
            "cost",
            "monitoring",
            "health_check"
        ]

        for evaluator_name in expected_evaluators:
            self.assertIn(evaluator_name, self.framework.evaluators)

    def test_comprehensive_evaluation(self):
        """Test comprehensive evaluation with all evaluators"""
        traces = [
            {
                "kubernetes": {
                    "pod_restarts": 12,
                    "pod_name": "agent-worker-1",
                    "resources": {
                        "cpu_usage_percent": 94,
                        "memory_usage_percent": 89
                    }
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

        # Run evaluation with all evaluators
        results = self.framework.evaluate_traces(
            traces, 
            evaluator_types=["monitoring", "health_check"]
        )

        # Verify results structure
        self.assertIn("monitoring", results)
        self.assertIn("health_check", results)

        # Verify monitoring detected issues
        monitoring_results = results["monitoring"]
        self.assertGreater(monitoring_results["total_issues"], 0)

        # Verify health check provided assessment
        health_results = results["health_check"]
        self.assertIn("worker_health", health_results)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
