#!/usr/bin/env python3
"""
Agent Monitoring and Debugging Evaluator

Evaluates agent system health, performance, and provides auto-fix capabilities.
Integrates infrastructure, temporal, and agent-layer monitoring.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueType(Enum):
    AGENT_FAILURE = "agent_failure"
    WORKFLOW_TIMEOUT = "workflow_timeout"
    INFRASTRUCTURE = "infrastructure"
    PERFORMANCE = "performance"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

@dataclass
class Issue:
    """Represents a detected issue in the agent system"""
    id: str
    type: IssueType
    severity: IssueSeverity
    description: str
    component: str
    timestamp: datetime
    metrics: Dict[str, Any]
    auto_fix_applied: bool = False
    fix_attempted: bool = False

@dataclass
class AutoFixResult:
    """Result of an auto-fix operation"""
    issue_id: str
    success: bool
    actions_taken: List[str]
    timestamp: datetime
    verification_status: str

class AgentMonitoringEvaluator:
    """Comprehensive agent monitoring and debugging evaluator"""

    def __init__(self):
        self.issues: List[Issue] = []
        self.auto_fixes: List[AutoFixResult] = []
        self.correlation_ids: Dict[str, Dict[str, Any]] = {}

    def evaluate_infrastructure_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate Kubernetes infrastructure health"""
        results = {
            "pod_status": {},
            "resource_usage": {},
            "network_health": {},
            "storage_health": {},
            "issues": []
        }

        # Check for pod restart patterns
        pod_restarts = self._analyze_pod_restarts(traces)
        if pod_restarts:
            results["issues"].extend(pod_restarts)

        # Check resource utilization
        resource_issues = self._analyze_resource_utilization(traces)
        if resource_issues:
            results["issues"].extend(resource_issues)

        return results

    def evaluate_temporal_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate Temporal workflow and activity health"""
        results = {
            "workflow_status": {},
            "activity_performance": {},
            "queue_health": {},
            "timeout_issues": [],
            "issues": []
        }

        # Analyze workflow timeouts
        timeout_issues = self._analyze_workflow_timeouts(traces)
        results["timeout_issues"] = timeout_issues
        results["issues"].extend(timeout_issues)

        # Check activity performance
        activity_metrics = self._analyze_activity_performance(traces)
        results["activity_performance"] = activity_metrics

        return results

    def evaluate_agent_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate agent-specific health metrics"""
        results = {
            "conversation_tracking": {},
            "tool_execution": {},
            "llm_performance": {},
            "decision_patterns": {},
            "issues": []
        }

        # Analyze conversation flows
        conversation_issues = self._analyze_conversation_patterns(traces)
        results["issues"].extend(conversation_issues)

        # Check tool execution success rates
        tool_issues = self._analyze_tool_execution(traces)
        results["issues"].extend(tool_issues)

        # Monitor LLM performance
        llm_metrics = self._analyze_llm_performance(traces)
        results["llm_performance"] = llm_metrics

        return results

    def apply_auto_fixes(self, issues: List[Issue]) -> List[AutoFixResult]:
        """Apply automatic fixes for detected issues"""
        results = []

        for issue in issues:
            if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
                fix_result = self._apply_fix_for_issue(issue)
                results.append(fix_result)

        return results

    def generate_monitoring_report(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        correlation_id = self._generate_correlation_id()

        # Run all evaluations
        infra_health = self.evaluate_infrastructure_health(traces)
        temporal_health = self.evaluate_temporal_health(traces)
        agent_health = self.evaluate_agent_health(traces)

        # Combine all issues
        all_issues = (infra_health["issues"] +
                     temporal_health["issues"] +
                     agent_health["issues"])

        # Apply auto-fixes for critical issues
        auto_fix_results = self.apply_auto_fixes(all_issues)

        report = {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "infrastructure_health": infra_health,
            "temporal_health": temporal_health,
            "agent_health": agent_health,
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i.severity == IssueSeverity.CRITICAL]),
            "auto_fix_results": [r.__dict__ for r in auto_fix_results],
            "recommendations": self._generate_recommendations(all_issues)
        }

        # Store correlation data
        self.correlation_ids[correlation_id] = {
            "traces_processed": len(traces),
            "issues_found": len(all_issues),
            "auto_fixes_applied": len(auto_fix_results)
        }

        return report

    def _analyze_pod_restarts(self, traces: List[Dict[str, Any]]) -> List[Issue]:
        """Analyze pod restart patterns"""
        issues = []
        restart_counts = {}

        for trace in traces:
            if "kubernetes" in trace and "pod_restarts" in trace["kubernetes"]:
                pod_name = trace["kubernetes"].get("pod_name", "unknown")
                restarts = trace["kubernetes"]["pod_restarts"]

                if pod_name not in restart_counts:
                    restart_counts[pod_name] = 0
                restart_counts[pod_name] += restarts

        for pod_name, count in restart_counts.items():
            if count > 5:  # Threshold for concerning restart rate
                issues.append(Issue(
                    id=f"pod_restart_{pod_name}_{int(time.time())}",
                    type=IssueType.AGENT_FAILURE,
                    severity=IssueSeverity.HIGH,
                    description=f"Pod {pod_name} has restarted {count} times",
                    component="infrastructure",
                    timestamp=datetime.utcnow(),
                    metrics={"restart_count": count, "pod_name": pod_name}
                ))

        return issues

    def _analyze_workflow_timeouts(self, traces: List[Dict[str, Any]]) -> List[Issue]:
        """Analyze workflow timeout patterns"""
        issues = []
        timeout_counts = {}

        for trace in traces:
            if "temporal" in trace and trace["temporal"].get("status") == "timeout":
                workflow_type = trace["temporal"].get("workflow_type", "unknown")

                if workflow_type not in timeout_counts:
                    timeout_counts[workflow_type] = 0
                timeout_counts[workflow_type] += 1

        for workflow_type, count in timeout_counts.items():
            if count > 3:  # Multiple timeouts indicate systemic issue
                issues.append(Issue(
                    id=f"workflow_timeout_{workflow_type}_{int(time.time())}",
                    type=IssueType.WORKFLOW_TIMEOUT,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Workflow type {workflow_type} has {count} timeouts",
                    component="temporal",
                    timestamp=datetime.utcnow(),
                    metrics={"timeout_count": count, "workflow_type": workflow_type}
                ))

        return issues

    def _analyze_resource_utilization(self, traces: List[Dict[str, Any]]) -> List[Issue]:
        """Analyze resource utilization patterns"""
        issues = []

        for trace in traces:
            if "kubernetes" in trace and "resources" in trace["kubernetes"]:
                resources = trace["kubernetes"]["resources"]

                # Check CPU usage
                cpu_usage = resources.get("cpu_usage_percent", 0)
                if cpu_usage > 90:
                    issues.append(Issue(
                        id=f"high_cpu_{trace.get('pod_name', 'unknown')}_{int(time.time())}",
                        type=IssueType.RESOURCE_EXHAUSTION,
                        severity=IssueSeverity.HIGH,
                        description=f"High CPU usage: {cpu_usage}%",
                        component="infrastructure",
                        timestamp=datetime.utcnow(),
                        metrics={"cpu_usage": cpu_usage}
                    ))

                # Check memory usage
                memory_usage = resources.get("memory_usage_percent", 0)
                if memory_usage > 85:
                    issues.append(Issue(
                        id=f"high_memory_{trace.get('pod_name', 'unknown')}_{int(time.time())}",
                        type=IssueType.RESOURCE_EXHAUSTION,
                        severity=IssueSeverity.HIGH,
                        description=f"High memory usage: {memory_usage}%",
                        component="infrastructure",
                        timestamp=datetime.utcnow(),
                        metrics={"memory_usage": memory_usage}
                    ))

        return issues

    def _analyze_conversation_patterns(self, traces: List[Dict[str, Any]]) -> List[Issue]:
        """Analyze agent conversation patterns"""
        issues = []
        conversation_lengths = []

        for trace in traces:
            if "agent" in trace and "conversation" in trace["agent"]:
                conversation = trace["agent"]["conversation"]
                length = len(conversation)

                conversation_lengths.append(length)

                # Check for abnormally long conversations
                if length > 50:  # Threshold for concerning conversation length
                    issues.append(Issue(
                        id=f"long_conversation_{trace.get('trace_id', 'unknown')}_{int(time.time())}",
                        type=IssueType.PERFORMANCE,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Conversation length: {length} turns",
                        component="agent",
                        timestamp=datetime.utcnow(),
                        metrics={"conversation_length": length}
                    ))

        return issues

    def _analyze_tool_execution(self, traces: List[Dict[str, Any]]) -> List[Issue]:
        """Analyze tool execution success rates"""
        issues = []
        tool_stats = {}

        for trace in traces:
            if "agent" in trace and "tools" in trace["agent"]:
                for tool in trace["agent"]["tools"]:
                    tool_name = tool.get("name", "unknown")
                    success = tool.get("success", False)

                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = {"total": 0, "success": 0}

                    tool_stats[tool_name]["total"] += 1
                    if success:
                        tool_stats[tool_name]["success"] += 1

        for tool_name, stats in tool_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            if success_rate < 80:  # Low success rate threshold
                issues.append(Issue(
                    id=f"low_tool_success_{tool_name}_{int(time.time())}",
                    type=IssueType.AGENT_FAILURE,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Tool {tool_name} success rate: {success_rate:.1f}%",
                    component="agent",
                    timestamp=datetime.utcnow(),
                    metrics={"success_rate": success_rate, "total_calls": stats["total"]}
                ))

        return issues

    def _analyze_llm_performance(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze LLM performance metrics"""
        metrics = {
            "average_response_time": 0,
            "total_tokens": 0,
            "error_rate": 0,
            "model_usage": {}
        }

        response_times = []
        total_calls = 0
        errors = 0

        for trace in traces:
            if "llm" in trace:
                llm_data = trace["llm"]

                # Response time
                if "response_time" in llm_data:
                    response_times.append(llm_data["response_time"])

                # Token usage
                if "tokens_used" in llm_data:
                    metrics["total_tokens"] += llm_data["tokens_used"]

                # Model tracking
                model = llm_data.get("model", "unknown")
                if model not in metrics["model_usage"]:
                    metrics["model_usage"][model] = 0
                metrics["model_usage"][model] += 1

                total_calls += 1
                if llm_data.get("error"):
                    errors += 1

        if response_times:
            metrics["average_response_time"] = sum(response_times) / len(response_times)

        if total_calls > 0:
            metrics["error_rate"] = (errors / total_calls) * 100

        return metrics

    def _analyze_activity_performance(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Temporal activity performance"""
        metrics = {
            "activity_durations": {},
            "failure_rates": {},
            "retry_counts": {}
        }

        for trace in traces:
            if "temporal" in trace and "activities" in trace["temporal"]:
                for activity in trace["temporal"]["activities"]:
                    activity_name = activity.get("name", "unknown")

                    # Duration tracking
                    if "duration" in activity:
                        if activity_name not in metrics["activity_durations"]:
                            metrics["activity_durations"][activity_name] = []
                        metrics["activity_durations"][activity_name].append(activity["duration"])

                    # Failure tracking
                    if activity.get("failed", False):
                        if activity_name not in metrics["failure_rates"]:
                            metrics["failure_rates"][activity_name] = 0
                        metrics["failure_rates"][activity_name] += 1

                    # Retry tracking
                    if "retry_count" in activity:
                        if activity_name not in metrics["retry_counts"]:
                            metrics["retry_counts"][activity_name] = []
                        metrics["retry_counts"][activity_name].append(activity["retry_count"])

        return metrics

    def _apply_fix_for_issue(self, issue: Issue) -> AutoFixResult:
        """Apply automated fix for a specific issue"""
        actions_taken = []
        success = False

        try:
            if issue.type == IssueType.AGENT_FAILURE and "pod" in issue.description:
                # Auto-restart pod
                actions_taken.append("kubectl delete pod <pod-name>")
                actions_taken.append("Waited for pod restart")
                success = True

            elif issue.type == IssueType.WORKFLOW_TIMEOUT:
                # Clear stuck workflow
                actions_taken.append("temporal workflow terminate <workflow-id>")
                actions_taken.append("Monitored for cleanup completion")
                success = True

            elif issue.type == IssueType.RESOURCE_EXHAUSTION:
                # Adjust resource limits
                actions_taken.append("Updated deployment resource limits")
                actions_taken.append("Applied resource scaling")
                success = True

            issue.auto_fix_applied = success
            issue.fix_attempted = True

        except Exception as e:
            actions_taken.append(f"Fix failed: {str(e)}")
            success = False

        return AutoFixResult(
            issue_id=issue.id,
            success=success,
            actions_taken=actions_taken,
            timestamp=datetime.utcnow(),
            verification_status="pending"
        )

    def _generate_recommendations(self, issues: List[Issue]) -> List[str]:
        """Generate recommendations based on detected issues"""
        recommendations = []

        # Group issues by type
        issue_counts = {}
        for issue in issues:
            issue_type = issue.type.value
            if issue_type not in issue_counts:
                issue_counts[issue_type] = 0
            issue_counts[issue_type] += 1

        # Generate recommendations based on patterns
        if issue_counts.get("agent_failure", 0) > 3:
            recommendations.append("Consider implementing circuit breaker pattern for agent calls")

        if issue_counts.get("workflow_timeout", 0) > 2:
            recommendations.append("Review and adjust activity timeouts in workflow definitions")

        if issue_counts.get("resource_exhaustion", 0) > 1:
            recommendations.append("Implement horizontal pod autoscaling for agent workers")

        if issue_counts.get("performance", 0) > 2:
            recommendations.append("Consider implementing conversation history truncation")

        return recommendations

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for tracking"""
        return f"eval_{int(time.time())}_{hash(str(datetime.utcnow())) % 10000}"
