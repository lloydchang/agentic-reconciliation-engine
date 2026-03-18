#!/usr/bin/env python3
"""
Test Suite for AI Agent Tracing Evaluation Framework

Comprehensive tests for all evaluators and framework components.
"""

import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.skill_invocation_evaluator import GitOpsSkillEvaluator
from evaluators.performance_evaluator import PerformanceEvaluator
from evaluators.cost_evaluator import CostEvaluator
from main import TracingEvaluationFramework


class TestSkillInvocationEvaluator(unittest.TestCase):
    """Test cases for Skill Invocation Evaluator"""

    def setUp(self):
        self.evaluator = GitOpsSkillEvaluator()

    def test_perfect_skill_invocation(self):
        """Test perfect skill invocation scenario"""
        trace = {
            "attributes": {
                "operation_type": "cost-optimization",
                "skill_invoked": True
            },
            "events": [
                {"name": "skill_loaded", "timestamp": 1000},
                {"name": "workflow_started", "timestamp": 1100}
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertEqual(result["score"], 1.0)
        self.assertTrue(result["passed"])
        self.assertTrue(result["details"]["skill_invoked"])
        self.assertTrue(result["details"]["should_use_skill"])
        self.assertTrue(result["details"]["timing_correct"])

    def test_no_skill_needed(self):
        """Test scenario where no skill should be invoked"""
        trace = {
            "attributes": {
                "operation_type": "simple-query",
                "skill_invoked": False
            },
            "events": [
                {"name": "workflow_started", "timestamp": 1000}
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertEqual(result["score"], 1.0)
        self.assertTrue(result["passed"])
        self.assertFalse(result["details"]["skill_invoked"])
        self.assertFalse(result["details"]["should_use_skill"])

    def test_wrong_skill_invocation(self):
        """Test scenario where wrong skill is invoked"""
        trace = {
            "attributes": {
                "operation_type": "simple-query",
                "skill_invoked": True
            },
            "events": [
                {"name": "skill_loaded", "timestamp": 1000},
                {"name": "workflow_started", "timestamp": 1100}
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertEqual(result["score"], 0.5)
        self.assertFalse(result["passed"])
        self.assertTrue(result["details"]["skill_invoked"])
        self.assertFalse(result["details"]["should_use_skill"])

    def test_timing_incorrect(self):
        """Test scenario with incorrect timing"""
        trace = {
            "attributes": {
                "operation_type": "cost-optimization",
                "skill_invoked": True
            },
            "events": [
                {"name": "workflow_started", "timestamp": 1000},
                {"name": "skill_loaded", "timestamp": 1100}  # Loaded after start
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertEqual(result["score"], 0.7)
        self.assertFalse(result["passed"])
        self.assertTrue(result["details"]["skill_invoked"])
        self.assertTrue(result["details"]["should_use_skill"])
        self.assertFalse(result["details"]["timing_correct"])

    def test_batch_evaluation(self):
        """Test batch evaluation functionality"""
        traces = [
            {
                "attributes": {
                    "operation_type": "cost-optimization",
                    "skill_invoked": True
                },
                "events": [
                    {"name": "skill_loaded", "timestamp": 1000},
                    {"name": "workflow_started", "timestamp": 1100}
                ]
            },
            {
                "attributes": {
                    "operation_type": "security-scan",
                    "skill_invoked": False
                },
                "events": [
                    {"name": "workflow_started", "timestamp": 2000}
                ]
            }
        ]
        
        result = self.evaluator.evaluate_batch(traces)
        
        self.assertEqual(result["total_evaluations"], 2)
        self.assertEqual(result["passed_count"], 1)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(result["pass_rate"], 0.5)


class TestPerformanceEvaluator(unittest.TestCase):
    """Test cases for Performance Evaluator"""

    def setUp(self):
        self.evaluator = PerformanceEvaluator()

    def test_excellent_performance(self):
        """Test excellent performance scenario"""
        trace = {
            "duration": {"duration_ms": 300},  # Excellent latency
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            },
            "attributes": {
                "memory_usage_mb": 400,  # Excellent memory
                "cpu_usage_percent": 30
            },
            "events": [
                {"name": "request_start", "level": "info", "timestamp": 1000},
                {"name": "response", "level": "info", "timestamp": 1300}
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertGreaterEqual(result["score"], 0.9)
        self.assertTrue(result["passed"])
        self.assertEqual(result["performance_tier"], "excellent")

    def test_poor_performance(self):
        """Test poor performance scenario"""
        trace = {
            "duration": {"duration_ms": 6000},  # Poor latency
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            },
            "attributes": {
                "memory_usage_mb": 5000,  # Poor memory
                "cpu_usage_percent": 90
            },
            "events": [
                {"name": "request_start", "level": "info", "timestamp": 1000},
                {"name": "error", "level": "error", "timestamp": 2000},
                {"name": "error", "level": "error", "timestamp": 3000},
                {"name": "response", "level": "info", "timestamp": 7000}
            ]
        }
        
        result = self.evaluator.evaluate(trace)
        
        self.assertLess(result["score"], 0.5)
        self.assertFalse(result["passed"])
        self.assertEqual(result["performance_tier"], "poor")

    def test_batch_performance(self):
        """Test batch performance evaluation"""
        traces = [
            {
                "duration": {"duration_ms": 300},
                "attributes": {"memory_usage_mb": 400},
                "events": [{"name": "request_start", "level": "info", "timestamp": 1000}]
            },
            {
                "duration": {"duration_ms": 6000},
                "attributes": {"memory_usage_mb": 5000},
                "events": [
                    {"name": "error", "level": "error", "timestamp": 1000},
                    {"name": "response", "level": "info", "timestamp": 2000}
                ]
            }
        ]
        
        result = self.evaluator.evaluate_batch(traces)
        
        self.assertEqual(result["total_traces"], 2)
        self.assertGreater(result["average_score"], 0.5)
        self.assertLess(result["average_score"], 1.0)


class TestCostEvaluator(unittest.TestCase):
    """Test cases for Cost Evaluator"""

    def setUp(self):
        self.evaluator = CostEvaluator()

    def test_efficient_cost(self):
        """Test cost-efficient scenario"""
        trace = {
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500
            },
            "attributes": {
                "model": "anthropic:claude-3-5-sonnet-20241022"
            },
            "duration": {"duration_ms": 2000}
        }
        
        result = self.evaluator.evaluate(trace)
        
        # Should be efficient (good score)
        self.assertGreaterEqual(result["score"], 0.7)
        self.assertTrue(result["passed"])
        
        # Check cost calculations
        cost_data = result["cost_data"]
        expected_input_cost = (1000 / 1000000) * 3.0  # $3.00 per 1M tokens
        expected_output_cost = (500 / 1000000) * 15.0  # $15.00 per 1M tokens
        expected_total = expected_input_cost + expected_output_cost
        
        self.assertAlmostEqual(cost_data["input_cost"], expected_input_cost, places=6)
        self.assertAlmostEqual(cost_data["output_cost"], expected_output_cost, places=6)
        self.assertAlmostEqual(cost_data["request_cost"], expected_total, places=6)

    def test_expensive_cost(self):
        """Test expensive cost scenario"""
        trace = {
            "usage": {
                "input_tokens": 10000,  # High token usage
                "output_tokens": 5000,
                "total_tokens": 15000
            },
            "attributes": {
                "model": "anthropic:claude-3-5-sonnet-20241022"
            },
            "duration": {"duration_ms": 2000}
        }
        
        result = self.evaluator.evaluate(trace)
        
        # Should be expensive (poor score)
        self.assertLess(result["score"], 0.7)
        
        cost_data = result["cost_data"]
        self.assertGreater(cost_data["request_cost"], 1.0)  # Over $1 per request

    def test_model_pricing(self):
        """Test different model pricing"""
        models_to_test = [
            "anthropic:claude-3-5-sonnet-20241022",
            "anthropic:claude-3-haiku-20240307",
            "openai:gpt-4",
            "openai:gpt-3.5-turbo"
        ]
        
        for model in models_to_test:
            trace = {
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "total_tokens": 1500
                },
                "attributes": {"model": model},
                "duration": {"duration_ms": 2000}
            }
            
            result = self.evaluator.evaluate(trace)
            cost_data = result["cost_data"]
            
            # Should have calculated costs
            self.assertGreater(cost_data["request_cost"], 0)
            self.assertEqual(cost_data["model"], model)


class TestTracingFramework(unittest.TestCase):
    """Test cases for main tracing framework"""

    def setUp(self):
        self.framework = TracingEvaluationFramework()

    def test_load_traces_from_file(self):
        """Test loading traces from file"""
        # Create temporary test data
        test_traces = {
            "traces": [
                {
                    "id": "test-1",
                    "attributes": {"operation_type": "test"}
                }
            ]
        }
        
        # Write to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_traces, f)
            temp_file = f.name
        
        # Test loading
        traces = self.framework.load_traces_from_file(temp_file)
        
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0]["id"], "test-1")

    def test_evaluate_with_all_evaluators(self):
        """Test framework with all evaluators"""
        traces = [
            {
                "attributes": {
                    "operation_type": "cost-optimization",
                    "skill_invoked": True,
                    "model": "anthropic:claude-3-5-sonnet-20241022"
                },
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "total_tokens": 1500
                },
                "duration": {"duration_ms": 800},
                "events": [
                    {"name": "skill_loaded", "timestamp": 1000},
                    {"name": "workflow_started", "timestamp": 1100}
                ]
            }
        ]
        
        result = self.framework.evaluate_traces(traces)
        
        # Should have results from all evaluators
        self.assertIn("skill_invocation", result["evaluator_results"])
        self.assertIn("performance", result["evaluator_results"])
        self.assertIn("cost", result["evaluator_results"])
        
        # Should have summary
        self.assertIn("summary", result)
        self.assertIn("overall_score", result["summary"])

    def test_generate_summary_report(self):
        """Test summary report generation"""
        evaluation_result = {
            "summary": {
                "overall_score": 0.85,
                "overall_pass_rate": 0.9,
                "total_evaluations": 10,
                "evaluator_summaries": {
                    "skill_invocation": {"average_score": 0.9, "pass_rate": 0.95},
                    "performance": {"average_score": 0.8, "pass_rate": 0.85},
                    "cost": {"average_score": 0.85, "pass_rate": 0.9}
                }
            },
            "trace_count": 10,
            "evaluators_run": ["skill_invocation", "performance", "cost"],
            "timestamp": "2026-03-17T00:00:00Z"
        }
        
        report = self.framework.generate_report(evaluation_result, "summary")
        
        self.assertIn("AI AGENT TRACING EVALUATION REPORT", report)
        self.assertIn("Overall Score: 0.85", report)
        self.assertIn("Pass Rate: 90.0%", report)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete framework"""

    def test_end_to_end_evaluation(self):
        """Test complete end-to-end evaluation workflow"""
        # Create comprehensive test traces
        traces = [
            {
                "id": "trace-1",
                "timestamp": 1678901234567,
                "attributes": {
                    "operation_type": "cost-optimization",
                    "skill_invoked": True,
                    "model": "anthropic:claude-3-5-sonnet-20241022",
                    "memory_usage_mb": 750,
                    "cpu_usage_percent": 45
                },
                "usage": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "total_tokens": 1500
                },
                "duration": {"duration_ms": 800},
                "events": [
                    {"name": "skill_loaded", "level": "info", "timestamp": 1000},
                    {"name": "workflow_started", "level": "info", "timestamp": 1100},
                    {"name": "response", "level": "info", "timestamp": 1800}
                ]
            },
            {
                "id": "trace-2",
                "timestamp": 1678902345678,
                "attributes": {
                    "operation_type": "security-scan",
                    "skill_invoked": False,
                    "model": "anthropic:claude-3-haiku-20240307",
                    "memory_usage_mb": 300,
                    "cpu_usage_percent": 25
                },
                "usage": {
                    "input_tokens": 500,
                    "output_tokens": 250,
                    "total_tokens": 750
                },
                "duration": {"duration_ms": 400},
                "events": [
                    {"name": "workflow_started", "level": "info", "timestamp": 2000},
                    {"name": "response", "level": "info", "timestamp": 2400}
                ]
            }
        ]
        
        # Run full evaluation
        framework = TracingEvaluationFramework()
        result = framework.evaluate_traces(traces)
        
        # Validate structure
        self.assertIn("summary", result)
        self.assertIn("evaluator_results", result)
        self.assertEqual(result["trace_count"], 2)
        self.assertEqual(len(result["evaluators_run"]), 3)
        
        # Validate individual evaluators
        skill_result = result["evaluator_results"]["skill_invocation"]
        perf_result = result["evaluator_results"]["performance"]
        cost_result = result["evaluator_results"]["cost"]
        
        # All should have processed the traces
        self.assertEqual(skill_result["total_evaluations"], 2)
        self.assertEqual(perf_result["total_traces"], 2)
        self.assertEqual(cost_result["total_traces"], 2)
        
        # Generate reports
        json_report = framework.generate_report(result, "json")
        summary_report = framework.generate_report(result, "summary")
        
        self.assertIsInstance(json.loads(json_report), dict)
        self.assertIn("EVALUATION REPORT", summary_report)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSkillInvocationEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestCostEvaluator))
    suite.addTests(loader.loadTestsFromTestCase(TestTracingFramework))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return results
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful()
    }


if __name__ == "__main__":
    print("Running AI Agent Tracing Evaluation Framework Tests")
    print("=" * 60)
    
    test_results = run_tests()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Tests Run: {test_results['tests_run']}")
    print(f"Failures: {test_results['failures']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Success: {test_results['success']}")
    
    if test_results['success']:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
