#!/usr/bin/env python3
"""
GitOps Skill Invocation Evaluator

Evaluates whether skills are properly invoked for GitOps tasks.
"""

import json
from typing import Dict, Any, List
from datetime import datetime

class GitOpsSkillEvaluator:
    """Evaluates skill invocation effectiveness for GitOps operations"""

    def __init__(self):
        self.skill_operations = {
            "cost-optimization", "security-scan", "deployment-strategy",
            "infrastructure-provisioning", "database-maintenance",
            "cluster-scaling", "network-configuration", "secret-rotation"
        }

    def evaluate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate skill invocation effectiveness

        Args:
            trace: Langfuse trace data

        Returns:
            Evaluation result with score, pass/fail, and details
        """
        # Extract trace attributes
        attributes = trace.get("attributes", {})
        operation_type = attributes.get("operation_type", "")
        skill_invoked = attributes.get("skill_invoked", False)
        events = trace.get("events", [])

        # Check if operation should use skills
        should_use_skill = operation_type in self.skill_operations

        # Check invocation timing
        timing_correct = self._check_invocation_timing(events)

        # Calculate score
        score = self._calculate_score(skill_invoked, should_use_skill, timing_correct)

        # Determine pass/fail
        passed = score >= 0.8

        return {
            "score": score,
            "passed": passed,
            "details": {
                "skill_invoked": skill_invoked,
                "should_use_skill": should_use_skill,
                "timing_correct": timing_correct,
                "operation_type": operation_type
            },
            "evaluator": "GitOpsSkillEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def _check_invocation_timing(self, events: List[Dict[str, Any]]) -> bool:
        """Check if skill was invoked at correct time"""
        skill_load_events = [e for e in events if e.get("name") == "skill_loaded"]
        execution_events = [e for e in events if e.get("name") == "workflow_started"]

        if not skill_load_events or not execution_events:
            return False

        # Skill should be loaded before execution starts
        skill_load_time = skill_load_events[0].get("timestamp", 0)
        execution_time = execution_events[0].get("timestamp", 0)

        return skill_load_time < execution_time

    def _calculate_score(self, skill_invoked: bool, should_use_skill: bool, timing_correct: bool) -> float:
        """Calculate evaluation score based on invocation criteria"""
        if skill_invoked and should_use_skill and timing_correct:
            return 1.0  # Perfect invocation
        elif not should_use_skill and not skill_invoked:
            return 1.0  # Correctly didn't invoke for non-skill operations
        elif skill_invoked and not should_use_skill:
            return 0.5  # Wrongly invoked skill
        elif should_use_skill and not skill_invoked:
            return 0.3  # Failed to invoke when should have
        elif should_use_skill and skill_invoked and not timing_correct:
            return 0.7  # Invoked but at wrong time
        else:
            return 0.0  # Other failure cases

    def evaluate_batch(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate multiple traces and return aggregate results

        Args:
            traces: List of Langfuse trace data

        Returns:
            Aggregate evaluation results
        """
        results = []
        scores = []
        passed_count = 0

        for trace in traces:
            result = self.evaluate(trace)
            results.append(result)
            scores.append(result["score"])
            if result["passed"]:
                passed_count += 1

        return {
            "total_evaluations": len(results),
            "passed_count": passed_count,
            "failed_count": len(results) - passed_count,
            "pass_rate": passed_count / len(results) if results else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "results": results,
            "evaluator": "GitOpsSkillEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def get_skill_coverage_report(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate skill coverage report from traces

        Args:
            traces: List of Langfuse trace data

        Returns:
            Skill coverage statistics
        """
        skill_usage = {}
        operation_counts = {}
        total_traces = len(traces)

        for trace in traces:
            attributes = trace.get("attributes", {})
            operation_type = attributes.get("operation_type", "")
            skill_invoked = attributes.get("skill_invoked", False)

            # Count operations
            operation_counts[operation_type] = operation_counts.get(operation_type, 0) + 1

            # Count skill usage
            if skill_invoked:
                skill_usage[operation_type] = skill_usage.get(operation_type, 0) + 1

        # Calculate coverage percentages
        coverage = {}
        for operation in self.skill_operations:
            count = operation_counts.get(operation, 0)
            coverage[operation] = {
                "total_operations": count,
                "skill_invocations": skill_usage.get(operation, 0),
                "coverage_percentage": (skill_usage.get(operation, 0) / count * 100) if count > 0 else 0
            }

        return {
            "total_traces": total_traces,
            "skill_operations": list(self.skill_operations),
            "operation_counts": operation_counts,
            "skill_usage": skill_usage,
            "coverage": coverage,
            "evaluator": "GitOpsSkillEvaluator",
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Example usage for testing
    evaluator = GitOpsSkillEvaluator()

    # Example trace data
    test_trace = {
        "attributes": {
            "operation_type": "cost-optimization",
            "skill_invoked": True
        },
        "events": [
            {"name": "skill_loaded", "timestamp": 1000},
            {"name": "workflow_started", "timestamp": 1100}
        ]
    }

    result = evaluator.evaluate(test_trace)
    print(json.dumps(result, indent=2))

    # Test batch evaluation
    test_traces = [
        test_trace,
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

    batch_result = evaluator.evaluate_batch(test_traces)
    print("\nBatch Evaluation:")
    print(json.dumps(batch_result, indent=2))

    coverage_report = evaluator.get_skill_coverage_report(test_traces)
    print("\nSkill Coverage Report:")
    print(json.dumps(coverage_report, indent=2))
