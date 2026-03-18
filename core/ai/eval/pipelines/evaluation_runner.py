#!/usr/bin/env python3
"""
GitOps Evaluation Pipeline Runner

Automated evaluation pipeline for GitOps agents using Langfuse.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import evaluators
from evaluators.skill_invocation_evaluator import GitOpsSkillEvaluator
from evaluators.risk_compliance_evaluator import GitOpsRiskEvaluator

class GitOpsEvaluationPipeline:
    """Automated evaluation pipeline for GitOps agents"""

    def __init__(self, langfuse_api_key: Optional[str] = None, langfuse_host: Optional[str] = None):
        """
        Initialize the evaluation pipeline

        Args:
            langfuse_api_key: Langfuse API key (reads from env if not provided)
            langfuse_host: Langfuse host URL (reads from env if not provided)
        """
        self.api_key = langfuse_api_key or os.getenv("LANGFUSE_API_KEY")
        self.host = langfuse_host or os.getenv("LANGFUSE_HOST", "https://api.langfuse.com")

        # Initialize evaluators
        self.evaluators = [
            GitOpsSkillEvaluator(),
            GitOpsRiskEvaluator()
        ]

        # Setup output directory
        self.results_dir = Path("evaluation-results")
        self.results_dir.mkdir(exist_ok=True)

    async def run_evaluation(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Run evaluation on recent traces

        Args:
            time_range: Time range for traces (e.g., "24h", "7d")

        Returns:
            Comprehensive evaluation report
        """
        print(f"Starting GitOps evaluation pipeline for last {time_range}...")

        # Get traces from specified time range
        traces = await self._get_traces(time_range)

        if not traces:
            print("No traces found for evaluation period")
            return {"error": "No traces available"}

        print(f"Found {len(traces)} traces for evaluation")

        # Evaluate all traces
        results = []
        for trace in traces:
            try:
                trace_results = await self._evaluate_trace(trace)
                results.extend(trace_results)
                print(f"Evaluated trace {trace.get('id', 'unknown')}")
            except Exception as e:
                print(f"Error evaluating trace {trace.get('id', 'unknown')}: {e}")
                results.append({
                    "trace_id": trace.get("id"),
                    "evaluator": "unknown",
                    "error": str(e),
                    "score": 0.0,
                    "passed": False,
                    "timestamp": datetime.now().isoformat()
                })

        # Generate comprehensive report
        report = self._generate_evaluation_report(results, time_range)

        # Store results for dashboard consumption
        await self._store_evaluation_results(report)

        print(f"Evaluation complete. Report saved to {self.results_dir}/latest.json")
        return report

    async def _get_traces(self, time_range: str) -> List[Dict[str, Any]]:
        """
        Get traces from Langfuse for the specified time range

        Args:
            time_range: Time range string (e.g., "24h")

        Returns:
            List of trace data
        """
        # Calculate time range
        end_time = datetime.now()
        if time_range.endswith("h"):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith("d"):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            # Default to 24 hours
            start_time = end_time - timedelta(hours=24)

        # Mock implementation - in real implementation, this would call Langfuse API
        # For now, return sample traces for testing
        return self._get_mock_traces(start_time, end_time)

    def _get_mock_traces(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Generate mock traces for testing"""
        mock_traces = [
            {
                "id": "trace-001",
                "attributes": {
                    "operation_type": "cost-optimization",
                    "skill_invoked": True,
                    "risk_level": "medium",
                    "autonomy_level": "conditional",
                    "human_gate_required": True,
                    "structured_output": True
                },
                "events": [
                    {"name": "skill_loaded", "timestamp": start_time.timestamp() + 100},
                    {"name": "workflow_started", "timestamp": start_time.timestamp() + 200}
                ],
                "timestamp": start_time.isoformat()
            },
            {
                "id": "trace-002",
                "attributes": {
                    "operation_type": "cluster-scaling",
                    "skill_invoked": False,  # Should have invoked skill
                    "risk_level": "high",
                    "autonomy_level": "requires_PR",
                    "human_gate_required": False,  # Should have used gate
                    "structured_output": True
                },
                "events": [
                    {"name": "workflow_started", "timestamp": start_time.timestamp() + 300}
                ],
                "timestamp": start_time.isoformat()
            }
        ]
        return mock_traces

    async def _evaluate_trace(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a single trace with all evaluators

        Args:
            trace: Trace data

        Returns:
            List of evaluation results
        """
        results = []

        for evaluator in self.evaluators:
            try:
                result = evaluator.evaluate(trace)
                result["trace_id"] = trace.get("id")
                result["timestamp"] = datetime.now().isoformat()
                results.append(result)
            except Exception as e:
                results.append({
                    "trace_id": trace.get("id"),
                    "evaluator": evaluator.__class__.__name__,
                    "error": str(e),
                    "score": 0.0,
                    "passed": False,
                    "timestamp": datetime.now().isoformat()
                })

        return results

    def _generate_evaluation_report(self, results: List[Dict[str, Any]], time_range: str) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report

        Args:
            results: List of evaluation results
            time_range: Time range evaluated

        Returns:
            Comprehensive report
        """
        if not results:
            return {"error": "No evaluation results"}

        import pandas as pd

        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)

        # Calculate summary statistics
        summary = {
            "total_traces": len(df),
            "total_evaluations": len(results),
            "average_score": float(df["score"].mean()) if not df.empty else 0.0,
            "pass_rate": float((df["passed"] == True).mean()) if not df.empty else 0.0,
            "evaluation_timestamp": datetime.now().isoformat(),
            "time_range": time_range
        }

        # Group by evaluator
        evaluator_stats = {}
        if not df.empty:
            for evaluator_name, group in df.groupby("evaluator"):
                evaluator_stats[evaluator_name] = {
                    "count": len(group),
                    "average_score": float(group["score"].mean()),
                    "pass_rate": float((group["passed"] == True).mean()),
                    "min_score": float(group["score"].min()),
                    "max_score": float(group["score"].max())
                }

        # Identify failing traces
        failing_traces = df[~df["passed"]] if not df.empty else pd.DataFrame()
        failing_summary = failing_traces.to_dict("records") if not failing_traces.empty else []

        # Calculate trends (mock implementation)
        trends = self._calculate_trends(df)

        return {
            "summary": summary,
            "by_evaluator": evaluator_stats,
            "failing_traces": failing_summary,
            "trends": trends,
            "raw_results": results
        }

    def _calculate_trends(self, df) -> Dict[str, Any]:
        """Calculate performance trends"""
        if df.empty:
            return {"error": "No data for trends"}

        # Mock trend calculation
        return {
            "score_trend": "stable",
            "pass_rate_trend": "improving",
            "recommendations": [
                "Skill invocation timing needs optimization",
                "Risk compliance for high-risk operations improved"
            ]
        }

    async def _store_evaluation_results(self, report: Dict[str, Any]) -> None:
        """
        Store evaluation results for dashboard consumption

        Args:
            report: Evaluation report
        """
        # Save latest results
        latest_file = self.results_dir / "latest.json"
        with open(latest_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save historical results
        history_dir = self.results_dir / "history"
        history_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = history_dir / f"evaluation_{timestamp}.json"
        with open(history_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Results stored: {latest_file} and {history_file}")


async def main():
    """Main entry point for evaluation pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="GitOps Agent Evaluation Pipeline")
    parser.add_argument("--time-range", default="24h", help="Time range for evaluation (e.g., 24h, 7d)")
    parser.add_argument("--api-key", help="Langfuse API key")
    parser.add_argument("--host", help="Langfuse host URL")

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = GitOpsEvaluationPipeline(
        langfuse_api_key=args.api_key,
        langfuse_host=args.host
    )

    # Run evaluation
    try:
        report = await pipeline.run_evaluation(args.time_range)

        # Print summary
        if "error" not in report:
            summary = report["summary"]
            print("
=== Evaluation Summary ===")
            print(f"Total traces: {summary['total_traces']}")
            print(f"Average score: {summary['average_score']:.2f}")
            print(f"Pass rate: {summary['pass_rate']:.2%}")
            print(f"Time range: {summary['time_range']}")
        else:
            print(f"Evaluation failed: {report['error']}")

    except Exception as e:
        print(f"Evaluation pipeline failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
