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
        """Check if skill was invoked at the correct time"""
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
