#!/usr/bin/env python3
"""
Performance Evaluator for Pi-Mono Agent

Evaluates performance metrics from Langfuse traces including latency,
throughput, and resource utilization.
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

class PerformanceEvaluator:
    """Evaluates performance metrics for Pi-Mono agent operations"""

    def __init__(self):
        self.performance_thresholds = {
            "latency_ms": {
                "excellent": 500,    # < 500ms
                "good": 1000,        # < 1s
                "acceptable": 2000,    # < 2s
                "poor": 5000          # >= 5s
            },
            "throughput_rpm": {
                "excellent": 60,       # > 60 req/min
                "good": 30,           # > 30 req/min
                "acceptable": 15,       # > 15 req/min
                "poor": 5             # <= 5 req/min
            },
            "error_rate": {
                "excellent": 0.01,     # < 1%
                "good": 0.05,           # < 5%
                "acceptable": 0.10,      # < 10%
                "poor": 0.20             # >= 20%
            },
            "memory_usage_mb": {
                "excellent": 512,      # < 512MB
                "good": 1024,           # < 1GB
                "acceptable": 2048,       # < 2GB
                "poor": 4096             # >= 4GB
            }
        }

    def evaluate(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate performance metrics from a single trace

        Args:
            trace: Langfuse trace data

        Returns:
            Performance evaluation with score and details
        """
        # Extract metrics
        metrics = self._extract_metrics(trace)
        
        # Calculate individual scores
        latency_score = self._score_latency(metrics.get("latency_ms", 0))
        throughput_score = self._score_throughput(metrics.get("throughput_rpm", 0))
        error_rate_score = self._score_error_rate(metrics.get("error_rate", 0))
        memory_score = self._score_memory_usage(metrics.get("memory_usage_mb", 0))

        # Calculate overall score
        overall_score = (latency_score + throughput_score + 
                       error_rate_score + memory_score) / 4

        # Determine performance tier
        performance_tier = self._get_performance_tier(overall_score)

        return {
            "score": overall_score,
            "performance_tier": performance_tier,
            "passed": overall_score >= 0.7,
            "metrics": metrics,
            "individual_scores": {
                "latency": latency_score,
                "throughput": throughput_score,
                "error_rate": error_rate_score,
                "memory_usage": memory_score
            },
            "evaluator": "PerformanceEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def _extract_metrics(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics from trace data"""
        metrics = {}

        # Extract duration/latency
        duration = trace.get("duration", {})
        if isinstance(duration, dict):
            metrics["latency_ms"] = duration.get("duration_ms", 0)
        else:
            metrics["latency_ms"] = float(duration) if duration else 0

        # Extract usage data
        usage = trace.get("usage", {})
        if isinstance(usage, dict):
            metrics.update({
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            })

        # Extract events for performance analysis
        events = trace.get("events", [])
        metrics.update(self._analyze_events(events))

        # Extract resource usage from attributes
        attributes = trace.get("attributes", {})
        metrics.update({
            "memory_usage_mb": attributes.get("memory_usage_mb", 0),
            "cpu_usage_percent": attributes.get("cpu_usage_percent", 0)
        })

        return metrics

    def _analyze_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze events to derive performance metrics"""
        if not events:
            return {"error_rate": 0, "throughput_rpm": 0}

        # Count error events
        error_events = [e for e in events if e.get("level") == "error"]
        total_events = len(events)
        error_rate = len(error_events) / total_events if total_events > 0 else 0

        # Calculate throughput from timestamps
        timestamps = [e.get("timestamp", 0) for e in events if e.get("timestamp")]
        if len(timestamps) < 2:
            return {"error_rate": error_rate, "throughput_rpm": 0}

        duration_ms = max(timestamps) - min(timestamps)
        duration_minutes = duration_ms / 60000  # Convert to minutes
        throughput_rpm = (total_events - 1) / duration_minutes if duration_minutes > 0 else 0

        return {
            "error_rate": error_rate,
            "throughput_rpm": throughput_rpm,
            "total_events": total_events,
            "error_events": len(error_events)
        }

    def _score_latency(self, latency_ms: float) -> float:
        """Score latency based on thresholds"""
        thresholds = self.performance_thresholds["latency_ms"]
        if latency_ms <= thresholds["excellent"]:
            return 1.0
        elif latency_ms <= thresholds["good"]:
            return 0.8
        elif latency_ms <= thresholds["acceptable"]:
            return 0.6
        elif latency_ms <= thresholds["poor"]:
            return 0.4
        else:
            return 0.2

    def _score_throughput(self, throughput_rpm: float) -> float:
        """Score throughput based on thresholds"""
        thresholds = self.performance_thresholds["throughput_rpm"]
        if throughput_rpm >= thresholds["excellent"]:
            return 1.0
        elif throughput_rpm >= thresholds["good"]:
            return 0.8
        elif throughput_rpm >= thresholds["acceptable"]:
            return 0.6
        elif throughput_rpm >= thresholds["poor"]:
            return 0.4
        else:
            return 0.2

    def _score_error_rate(self, error_rate: float) -> float:
        """Score error rate based on thresholds"""
        thresholds = self.performance_thresholds["error_rate"]
        if error_rate <= thresholds["excellent"]:
            return 1.0
        elif error_rate <= thresholds["good"]:
            return 0.8
        elif error_rate <= thresholds["acceptable"]:
            return 0.6
        elif error_rate <= thresholds["poor"]:
            return 0.4
        else:
            return 0.2

    def _score_memory_usage(self, memory_mb: float) -> float:
        """Score memory usage based on thresholds"""
        thresholds = self.performance_thresholds["memory_usage_mb"]
        if memory_mb <= thresholds["excellent"]:
            return 1.0
        elif memory_mb <= thresholds["good"]:
            return 0.8
        elif memory_mb <= thresholds["acceptable"]:
            return 0.6
        elif memory_mb <= thresholds["poor"]:
            return 0.4
        else:
            return 0.2

    def _get_performance_tier(self, score: float) -> str:
        """Determine performance tier from score"""
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
        Evaluate multiple traces and return aggregate performance metrics

        Args:
            traces: List of Langfuse trace data

        Returns:
            Aggregate performance evaluation
        """
        results = []
        scores = []
        performance_tiers = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}

        for trace in traces:
            result = self.evaluate(trace)
            results.append(result)
            scores.append(result["score"])
            performance_tiers[result["performance_tier"]] += 1

        # Calculate aggregate metrics
        total_traces = len(results)
        avg_score = sum(scores) / total_traces if total_traces > 0 else 0

        return {
            "total_traces": total_traces,
            "average_score": avg_score,
            "performance_distribution": performance_tiers,
            "pass_rate": sum(1 for r in results if r["passed"]) / total_traces if total_traces > 0 else 0,
            "results": results,
            "evaluator": "PerformanceEvaluator",
            "timestamp": datetime.now().isoformat()
        }

    def get_performance_trends(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze performance trends over time

        Args:
            traces: List of Langfuse trace data with timestamps

        Returns:
            Performance trend analysis
        """
        # Sort traces by timestamp
        sorted_traces = sorted(traces, key=lambda x: x.get("timestamp", 0))
        
        # Extract time series data
        time_series = []
        for trace in sorted_traces:
            metrics = self._extract_metrics(trace)
            time_series.append({
                "timestamp": trace.get("timestamp"),
                "latency_ms": metrics.get("latency_ms", 0),
                "throughput_rpm": metrics.get("throughput_rpm", 0),
                "error_rate": metrics.get("error_rate", 0),
                "memory_usage_mb": metrics.get("memory_usage_mb", 0)
            })

        # Calculate trends
        if len(time_series) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Simple linear trend calculation
        latencies = [point["latency_ms"] for point in time_series]
        error_rates = [point["error_rate"] for point in time_series]
        
        latency_trend = self._calculate_trend(latencies)
        error_trend = self._calculate_trend(error_rates)

        return {
            "time_series": time_series,
            "trends": {
                "latency": latency_trend,
                "error_rate": error_trend
            },
            "summary": {
                "total_points": len(time_series),
                "time_span_hours": (time_series[-1]["timestamp"] - time_series[0]["timestamp"]) / 3600000 if len(time_series) > 1 else 0
            },
            "evaluator": "PerformanceEvaluator",
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

        if abs(slope) < 0.01:
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


if __name__ == "__main__":
    # Example usage
    evaluator = PerformanceEvaluator()

    # Example trace
    test_trace = {
        "duration": {"duration_ms": 800},
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150
        },
        "attributes": {
            "memory_usage_mb": 750,
            "cpu_usage_percent": 45
        },
        "events": [
            {"name": "request_start", "level": "info", "timestamp": 1000},
            {"name": "skill_loaded", "level": "info", "timestamp": 1100},
            {"name": "response", "level": "info", "timestamp": 1800}
        ]
    }

    result = evaluator.evaluate(test_trace)
    print(json.dumps(result, indent=2))
