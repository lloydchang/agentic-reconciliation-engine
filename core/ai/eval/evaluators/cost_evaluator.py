#!/usr/bin/env python3
"""
Cost Evaluator for Pi-Mono Agent

Evaluates cost efficiency and spending patterns from Langfuse traces.
Analyzes token usage, model costs, and budget compliance.
"""

import json
from typing import Dict, Any, List
from datetime import datetime

class CostEvaluator:
    """Evaluates cost metrics for Pi-Mono agent operations"""

    def __init__(self):
        # Model pricing (cost per 1M tokens)
        self.model_pricing = {
            "anthropic:claude-3-5-sonnet-20241022": {
                "input": 3.0,      # $3.00 per 1M input tokens
                "output": 15.0,    # $15.00 per 1M output tokens
                "context": 0.075    # $0.075 per 1M context tokens
            },
            "anthropic:claude-3-haiku-20240307": {
                "input": 0.25,
                "output": 1.25,
                "context": 0.00625
            },
            "openai:gpt-4": {
                "input": 30.0,
                "output": 60.0,
                "context": 0.0
            },
            "openai:gpt-4-turbo": {
                "input": 10.0,
                "output": 30.0,
                "context": 0.0
            },
            "openai:gpt-3.5-turbo": {
                "input": 0.5,
                "output": 1.5,
                "context": 0.0
            }
        }
        
        # Cost thresholds
        self.cost_thresholds = {
            "daily_budget": 100.0,      # $100 per day
            "request_max": 1.0,         # $1 per single request
            "hourly_limit": 10.0,        # $10 per hour
            "efficiency_target": 0.8       # 80% efficiency target
        }

    def evaluate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate cost metrics from a single trace

        Args:
            trace: Langfuse trace data

        Returns:
            Cost evaluation with score and details
        """
        # Extract cost data
        cost_data = self._extract_cost_data(trace)
        
        # Calculate individual scores
        request_cost_score = self._score_request_cost(cost_data["request_cost"])
        efficiency_score = self._score_efficiency(cost_data)
        budget_compliance_score = self._score_budget_compliance(cost_data)
        
        # Calculate overall score
        overall_score = (request_cost_score + efficiency_score + budget_compliance_score) / 3

        # Determine cost tier
        cost_tier = self._get_cost_tier(overall_score)

        return {
            "score": overall_score,
            "cost_tier": cost_tier,
            "passed": overall_score >= 0.7,
            "cost_data": cost_data,
            "individual_scores": {
                "request_cost": request_cost_score,
                "efficiency": efficiency_score,
                "budget_compliance": budget_compliance_score
            },
            "evaluator": "CostEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def _extract_cost_data(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cost-related data from trace"""
        cost_data = {}
        
        # Extract usage data
        usage = trace.get("usage", {})
        cost_data.update({
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0)
        })
        
        # Get model information
        attributes = trace.get("attributes", {})
        model = attributes.get("model", "anthropic:claude-3-5-sonnet-20241022")
        cost_data["model"] = model
        
        # Calculate costs
        model_pricing = self.model_pricing.get(model, self.model_pricing["anthropic:claude-3-5-sonnet-20241022"])
        
        input_cost = (cost_data["input_tokens"] / 1000000) * model_pricing["input"]
        output_cost = (cost_data["output_tokens"] / 1000000) * model_pricing["output"]
        
        cost_data.update({
            "input_cost": input_cost,
            "output_cost": output_cost,
            "request_cost": input_cost + output_cost,
            "cost_per_token": (input_cost + output_cost) / cost_data["total_tokens"] if cost_data["total_tokens"] > 0 else 0
        })
        
        # Extract timing for cost rate analysis
        duration = trace.get("duration", {})
        if isinstance(duration, dict):
            cost_data["duration_ms"] = duration.get("duration_ms", 0)
        else:
            cost_data["duration_ms"] = float(duration) if duration else 0
        
        # Calculate cost per second
        if cost_data["duration_ms"] > 0:
            cost_data["cost_per_second"] = cost_data["request_cost"] / (cost_data["duration_ms"] / 1000)
        else:
            cost_data["cost_per_second"] = 0
        
        return cost_data

    def _score_request_cost(self, request_cost: float) -> float:
        """Score individual request cost"""
        max_cost = self.cost_thresholds["request_max"]
        
        if request_cost <= max_cost * 0.5:
            return 1.0  # Excellent: very low cost
        elif request_cost <= max_cost * 0.8:
            return 0.8  # Good: reasonable cost
        elif request_cost <= max_cost:
            return 0.6  # Acceptable: at limit
        elif request_cost <= max_cost * 1.5:
            return 0.4  # Poor: over limit
        else:
            return 0.2  # Very poor: way over limit

    def _score_efficiency(self, cost_data: Dict[str, Any]) -> float:
        """Score cost efficiency based on tokens per cost"""
        if cost_data["total_tokens"] == 0:
            return 1.0
        
        # Calculate efficiency (tokens per dollar)
        tokens_per_dollar = cost_data["total_tokens"] / cost_data["request_cost"] if cost_data["request_cost"] > 0 else float('inf')
        
        # Benchmark: Claude 3.5 Sonnet should get ~66,667 tokens per dollar
        benchmark_efficiency = 66667
        
        efficiency_ratio = min(tokens_per_dollar / benchmark_efficiency, 2.0)  # Cap at 200% of benchmark
        
        if efficiency_ratio >= 1.2:
            return 1.0  # Excellent: very efficient
        elif efficiency_ratio >= 1.0:
            return 0.8  # Good: efficient
        elif efficiency_ratio >= 0.8:
            return 0.6  # Acceptable: moderately efficient
        elif efficiency_ratio >= 0.6:
            return 0.4  # Poor: inefficient
        else:
            return 0.2  # Very poor: very inefficient

    def _score_budget_compliance(self, cost_data: Dict[str, Any]) -> float:
        """Score budget compliance (placeholder without time context)"""
        # Without time context, assume reasonable request cost
        request_cost = cost_data["request_cost"]
        daily_budget = self.cost_thresholds["daily_budget"]
        
        # Estimate daily usage from single request (very rough)
        estimated_daily_cost = request_cost * 100  # Assume 100 requests per day
        
        if estimated_daily_cost <= daily_budget * 0.5:
            return 1.0  # Excellent: well under budget
        elif estimated_daily_cost <= daily_budget * 0.8:
            return 0.8  # Good: reasonable usage
        elif estimated_daily_cost <= daily_budget:
            return 0.6  # Acceptable: at budget limit
        elif estimated_daily_cost <= daily_budget * 1.2:
            return 0.4  # Poor: over budget
        else:
            return 0.2  # Very poor: way over budget

    def _get_cost_tier(self, score: float) -> str:
        """Determine cost tier from score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "acceptable"
        else:
            return "poor"

    def evaluate_batch(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate multiple traces and return aggregate cost metrics

        Args:
            traces: List of Langfuse trace data

        Returns:
            Aggregate cost evaluation
        """
        results = []
        scores = []
        cost_tiers = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}
        
        # Aggregate cost data
        total_cost = 0
        total_tokens = 0
        model_usage = {}
        
        for trace in traces:
            result = self.evaluate(trace)
            results.append(result)
            scores.append(result["score"])
            cost_tiers[result["cost_tier"]] += 1
            
            # Aggregate costs
            cost_data = result["cost_data"]
            total_cost += cost_data["request_cost"]
            total_tokens += cost_data["total_tokens"]
            
            # Track model usage
            model = cost_data["model"]
            if model not in model_usage:
                model_usage[model] = {"count": 0, "cost": 0, "tokens": 0}
            model_usage[model]["count"] += 1
            model_usage[model]["cost"] += cost_data["request_cost"]
            model_usage[model]["tokens"] += cost_data["total_tokens"]

        # Calculate aggregate metrics
        total_traces = len(results)
        avg_score = sum(scores) / total_traces if total_traces > 0 else 0
        avg_cost_per_request = total_cost / total_traces if total_traces > 0 else 0
        avg_tokens_per_request = total_tokens / total_traces if total_traces > 0 else 0
        
        # Calculate cost efficiency
        overall_efficiency = total_tokens / total_cost if total_cost > 0 else float('inf')

        return {
            "total_traces": total_traces,
            "average_score": avg_score,
            "cost_distribution": cost_tiers,
            "pass_rate": sum(1 for r in results if r["passed"]) / total_traces if total_traces > 0 else 0,
            "aggregate_metrics": {
                "total_cost": total_cost,
                "average_cost_per_request": avg_cost_per_request,
                "total_tokens": total_tokens,
                "average_tokens_per_request": avg_tokens_per_request,
                "overall_efficiency_tokens_per_dollar": overall_efficiency
            },
            "model_usage": model_usage,
            "results": results,
            "evaluator": "CostEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def get_cost_trends(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze cost trends over time

        Args:
            traces: List of Langfuse trace data with timestamps

        Returns:
            Cost trend analysis
        """
        # Sort traces by timestamp
        sorted_traces = sorted(traces, key=lambda x: x.get("timestamp", 0))
        
        # Extract time series data
        time_series = []
        for trace in sorted_traces:
            cost_data = self._extract_cost_data(trace)
            time_series.append({
                "timestamp": trace.get("timestamp"),
                "request_cost": cost_data["request_cost"],
                "tokens_per_dollar": cost_data["total_tokens"] / cost_data["request_cost"] if cost_data["request_cost"] > 0 else 0,
                "model": cost_data["model"]
            })

        if len(time_series) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Calculate trends
        costs = [point["request_cost"] for point in time_series]
        efficiencies = [point["tokens_per_dollar"] for point in time_series]
        
        cost_trend = self._calculate_trend(costs)
        efficiency_trend = self._calculate_trend(efficiencies)

        return {
            "time_series": time_series,
            "trends": {
                "cost": cost_trend,
                "efficiency": efficiency_trend
            },
            "summary": {
                "total_points": len(time_series),
                "time_span_hours": (time_series[-1]["timestamp"] - time_series[0]["timestamp"]) / 3600000 if len(time_series) > 1 else 0
            },
            "evaluator": "CostEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate simple trend for a series of values"""
        if len(values) < 2:
            return {"direction": "stable", "slope": 0}

        # Simple linear regression
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

        if abs(slope) < 0.001:
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        return {
            "direction": direction,
            "slope": slope,
            "start_value": values[0],
            "end_value": values[-1],
            "change_percent": ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        }

    def generate_cost_report(self, evaluation_result: Dict[str, Any]) -> str:
        """Generate human-readable cost report"""
        aggregate = evaluation_result["aggregate_metrics"]
        model_usage = evaluation_result["model_usage"]
        
        lines = []
        lines.append("=" * 60)
        lines.append("COST EVALUATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {evaluation_result['timestamp']}")
        lines.append(f"Total Requests: {evaluation_result['total_traces']}")
        lines.append(f"Average Score: {evaluation_result['average_score']:.2f}")
        lines.append("")
        
        # Cost summary
        lines.append("COST SUMMARY:")
        lines.append(f"  Total Cost: ${aggregate['total_cost']:.4f}")
        lines.append(f"  Average Cost per Request: ${aggregate['average_cost_per_request']:.4f}")
        lines.append(f"  Total Tokens: {aggregate['total_tokens']:,}")
        lines.append(f"  Average Tokens per Request: {aggregate['average_tokens_per_request']:.0f}")
        lines.append(f"  Overall Efficiency: {aggregate['overall_efficiency_tokens_per_dollar']:.0f} tokens/$")
        lines.append("")
        
        # Model usage breakdown
        lines.append("MODEL USAGE BREAKDOWN:")
        for model, usage in model_usage.items():
            lines.append(f"  {model}:")
            lines.append(f"    Requests: {usage['count']}")
            lines.append(f"    Cost: ${usage['cost']:.4f}")
            lines.append(f"    Tokens: {usage['tokens']:,}")
            if usage['cost'] > 0:
                efficiency = usage['tokens'] / usage['cost']
                lines.append(f"    Efficiency: {efficiency:.0f} tokens/$")
            lines.append("")
        
        # Cost distribution
        lines.append("COST DISTRIBUTION:")
        distribution = evaluation_result["cost_distribution"]
        lines.append(f"  Excellent: {distribution['excellent']} requests")
        lines.append(f"  Good: {distribution['good']} requests")
        lines.append(f"  Acceptable: {distribution['acceptable']} requests")
        lines.append(f"  Poor: {distribution['poor']} requests")
        lines.append("")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    evaluator = CostEvaluator()

    # Example trace
    test_trace = {
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

    result = evaluator.evaluate(test_trace)
    print(json.dumps(result, indent=2))

    # Test batch evaluation
    test_traces = [
        test_trace,
        {
            "usage": {
                "input_tokens": 500,
                "output_tokens": 250,
                "total_tokens": 750
            },
            "attributes": {
                "model": "anthropic:claude-3-haiku-20240307"
            },
            "duration": {"duration_ms": 1000}
        }
    ]

    batch_result = evaluator.evaluate_batch(test_traces)
    print("\nBatch Evaluation:")
    print(json.dumps(batch_result, indent=2))

    # Generate report
    report = evaluator.generate_cost_report(batch_result)
    print("\nCost Report:")
    print(report)
