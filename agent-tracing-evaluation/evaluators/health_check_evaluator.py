#!/usr/bin/env python3
"""
Health Check Evaluator for Agent Systems

Evaluates agent worker health, conversation completion tracking,
and overall system readiness patterns.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Represents a health metric for an agent component"""
    component: str
    metric_name: str
    value: Any
    threshold: Any
    status: str  # "healthy", "warning", "critical"
    timestamp: datetime
    details: Optional[str] = None

@dataclass
class ConversationHealth:
    """Represents health metrics for agent conversations"""
    conversation_id: str
    completion_rate: float
    average_duration: float
    error_rate: float
    last_activity: datetime
    status: str

class HealthCheckEvaluator:
    """Evaluates health of agent workers and conversations"""

    def __init__(self):
        self.health_metrics: List[HealthMetric] = []
        self.conversation_health: Dict[str, ConversationHealth] = {}

    def evaluate_worker_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate health of agent workers"""
        results = {
            "worker_status": {},
            "readiness_probes": {},
            "liveness_probes": {},
            "resource_health": {},
            "overall_health_score": 0.0
        }

        worker_metrics = self._analyze_worker_metrics(traces)
        results["worker_status"] = worker_metrics

        # Evaluate readiness probes
        readiness = self._check_readiness_probes(traces)
        results["readiness_probes"] = readiness

        # Evaluate liveness probes
        liveness = self._check_liveness_probes(traces)
        results["liveness_probes"] = liveness

        # Resource health check
        resources = self._evaluate_resource_health(traces)
        results["resource_health"] = resources

        # Calculate overall health score
        results["overall_health_score"] = self._calculate_health_score(
            worker_metrics, readiness, liveness, resources
        )

        return results

    def evaluate_conversation_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate health of agent conversations"""
        results = {
            "completion_tracking": {},
            "duration_analysis": {},
            "error_patterns": {},
            "stuck_conversations": [],
            "health_summary": {}
        }

        # Analyze conversation completion rates
        completion_data = self._analyze_conversation_completion(traces)
        results["completion_tracking"] = completion_data

        # Analyze conversation durations
        duration_data = self._analyze_conversation_durations(traces)
        results["duration_analysis"] = duration_data

        # Identify error patterns
        error_data = self._analyze_conversation_errors(traces)
        results["error_patterns"] = error_data

        # Detect stuck conversations
        stuck_convs = self._detect_stuck_conversations(traces)
        results["stuck_conversations"] = stuck_convs

        # Generate health summary
        results["health_summary"] = self._generate_conversation_health_summary(
            completion_data, duration_data, error_data, stuck_convs
        )

        return results

    def evaluate_system_readiness(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate overall system readiness"""
        results = {
            "system_status": "unknown",
            "components_ready": [],
            "blocking_issues": [],
            "estimated_recovery_time": None,
            "readiness_score": 0.0
        }

        # Check component readiness
        components_ready = self._check_component_readiness(traces)
        results["components_ready"] = components_ready

        # Identify blocking issues
        blocking_issues = self._identify_blocking_issues(traces)
        results["blocking_issues"] = blocking_issues

        # Calculate readiness score
        readiness_score = len(components_ready) / max(1, len(components_ready) + len(blocking_issues))
        results["readiness_score"] = readiness_score

        # Determine overall system status
        if readiness_score >= 0.9:
            results["system_status"] = "ready"
        elif readiness_score >= 0.7:
            results["system_status"] = "degraded"
            results["estimated_recovery_time"] = "30 minutes"
        else:
            results["system_status"] = "unhealthy"
            results["estimated_recovery_time"] = "2+ hours"

        return results

    def generate_health_report(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        worker_health = self.evaluate_worker_health(traces)
        conversation_health = self.evaluate_conversation_health(traces)
        system_readiness = self.evaluate_system_readiness(traces)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": f"health_{int(time.time())}",
            "worker_health": worker_health,
            "conversation_health": conversation_health,
            "system_readiness": system_readiness,
            "overall_health_status": self._determine_overall_status(
                worker_health, conversation_health, system_readiness
            ),
            "recommendations": self._generate_health_recommendations(
                worker_health, conversation_health, system_readiness
            )
        }

        return report

    def _analyze_worker_metrics(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze metrics from agent workers"""
        worker_stats = {}

        for trace in traces:
            if "kubernetes" in trace and "worker" in trace["kubernetes"]:
                worker_data = trace["kubernetes"]["worker"]
                worker_id = worker_data.get("worker_id", "unknown")

                if worker_id not in worker_stats:
                    worker_stats[worker_id] = {
                        "active_connections": 0,
                        "memory_usage": 0,
                        "cpu_usage": 0,
                        "last_heartbeat": None,
                        "status": "unknown"
                    }

                # Update worker stats
                stats = worker_stats[worker_id]
                stats["active_connections"] = max(
                    stats["active_connections"],
                    worker_data.get("active_connections", 0)
                )
                stats["memory_usage"] = worker_data.get("memory_usage", 0)
                stats["cpu_usage"] = worker_data.get("cpu_usage", 0)
                stats["last_heartbeat"] = worker_data.get("last_heartbeat")

                # Determine status based on heartbeat
                if stats["last_heartbeat"]:
                    heartbeat_time = datetime.fromisoformat(stats["last_heartbeat"].replace('Z', '+00:00'))
                    time_diff = datetime.utcnow() - heartbeat_time

                    if time_diff < timedelta(minutes=5):
                        stats["status"] = "healthy"
                    elif time_diff < timedelta(minutes=15):
                        stats["status"] = "warning"
                    else:
                        stats["status"] = "unhealthy"

        return worker_stats

    def _check_readiness_probes(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check readiness probe status"""
        readiness_stats = {
            "total_probes": 0,
            "passing_probes": 0,
            "failing_probes": 0,
            "details": []
        }

        for trace in traces:
            if "kubernetes" in trace and "readiness_probe" in trace["kubernetes"]:
                probe_data = trace["kubernetes"]["readiness_probe"]
                readiness_stats["total_probes"] += 1

                if probe_data.get("status") == "passing":
                    readiness_stats["passing_probes"] += 1
                else:
                    readiness_stats["failing_probes"] += 1
                    readiness_stats["details"].append({
                        "component": probe_data.get("component", "unknown"),
                        "reason": probe_data.get("failure_reason", "unknown"),
                        "timestamp": trace.get("timestamp")
                    })

        return readiness_stats

    def _check_liveness_probes(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check liveness probe status"""
        liveness_stats = {
            "total_probes": 0,
            "passing_probes": 0,
            "failing_probes": 0,
            "restart_triggers": 0
        }

        for trace in traces:
            if "kubernetes" in trace and "liveness_probe" in trace["kubernetes"]:
                probe_data = trace["kubernetes"]["liveness_probe"]
                liveness_stats["total_probes"] += 1

                if probe_data.get("status") == "passing":
                    liveness_stats["passing_probes"] += 1
                else:
                    liveness_stats["failing_probes"] += 1
                    if probe_data.get("triggered_restart", False):
                        liveness_stats["restart_triggers"] += 1

        return liveness_stats

    def _evaluate_resource_health(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate resource utilization health"""
        resource_health = {
            "cpu_health": "healthy",
            "memory_health": "healthy",
            "disk_health": "healthy",
            "network_health": "healthy",
            "issues": []
        }

        for trace in traces:
            if "kubernetes" in trace and "resources" in trace["kubernetes"]:
                resources = trace["kubernetes"]["resources"]

                # CPU health check
                cpu_usage = resources.get("cpu_usage_percent", 0)
                if cpu_usage > 95:
                    resource_health["cpu_health"] = "critical"
                    resource_health["issues"].append(f"CPU usage critical: {cpu_usage}%")
                elif cpu_usage > 85:
                    resource_health["cpu_health"] = "warning"

                # Memory health check
                memory_usage = resources.get("memory_usage_percent", 0)
                if memory_usage > 95:
                    resource_health["memory_health"] = "critical"
                    resource_health["issues"].append(f"Memory usage critical: {memory_usage}%")
                elif memory_usage > 85:
                    resource_health["memory_health"] = "warning"

                # Disk health check
                disk_usage = resources.get("disk_usage_percent", 0)
                if disk_usage > 95:
                    resource_health["disk_health"] = "critical"
                    resource_health["issues"].append(f"Disk usage critical: {disk_usage}%")
                elif disk_usage > 90:
                    resource_health["disk_health"] = "warning"

        return resource_health

    def _calculate_health_score(self, worker_metrics: Dict, readiness: Dict,
                               liveness: Dict, resources: Dict) -> float:
        """Calculate overall health score (0.0 to 1.0)"""
        score_components = []

        # Worker health (40% weight)
        healthy_workers = sum(1 for w in worker_metrics.values() if w["status"] == "healthy")
        total_workers = len(worker_metrics)
        worker_score = healthy_workers / max(1, total_workers)
        score_components.append(worker_score * 0.4)

        # Readiness probes (30% weight)
        readiness_score = readiness.get("passing_probes", 0) / max(1, readiness.get("total_probes", 1))
        score_components.append(readiness_score * 0.3)

        # Liveness probes (20% weight)
        liveness_score = liveness.get("passing_probes", 0) / max(1, liveness.get("total_probes", 1))
        score_components.append(liveness_score * 0.2)

        # Resource health (10% weight)
        resource_issues = len(resources.get("issues", []))
        resource_score = max(0, 1 - (resource_issues * 0.2))  # Deduct 20% per issue
        score_components.append(resource_score * 0.1)

        return sum(score_components)

    def _analyze_conversation_completion(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation completion rates"""
        conversations = {}
        total_conversations = 0
        completed_conversations = 0

        for trace in traces:
            if "agent" in trace and "conversation" in trace["agent"]:
                conv_data = trace["agent"]["conversation"]
                
                # Handle both dict and list formats
                if isinstance(conv_data, dict):
                    conv_id = conv_data.get("conversation_id", "unknown")
                elif isinstance(conv_data, list):
                    # For list format, generate an ID based on trace
                    conv_id = trace.get("trace_id", f"conv-{total_conversations}")
                else:
                    continue

                if conv_id not in conversations:
                    conversations[conv_id] = {
                        "turns": 0,
                        "completed": False,
                        "errors": 0
                    }
                    total_conversations += 1

                if isinstance(conv_data, dict):
                    conversations[conv_id]["turns"] += conv_data.get("turns", 0)
                    if conv_data.get("completed", False):
                        conversations[conv_id]["completed"] = True
                        completed_conversations += 1
                    if conv_data.get("error"):
                        conversations[conv_id]["errors"] += 1
                elif isinstance(conv_data, list):
                    conversations[conv_id]["turns"] = len(conv_data)
                    # Assume list conversations are incomplete unless marked otherwise
                    if trace.get("completed", False):
                        conversations[conv_id]["completed"] = True
                        completed_conversations += 1

        completion_rate = completed_conversations / max(1, total_conversations)

        return {
            "total_conversations": total_conversations,
            "completed_conversations": completed_conversations,
            "completion_rate": completion_rate,
            "average_turns": sum(c["turns"] for c in conversations.values()) / max(1, len(conversations))
        }

    def _analyze_conversation_durations(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation duration patterns"""
        durations = []

        for trace in traces:
            if "agent" in trace and "conversation" in trace["agent"]:
                conv_data = trace["agent"]["conversation"]
                
                # Handle both dict and list formats
                if isinstance(conv_data, dict):
                    start_time = conv_data.get("start_time")
                    end_time = conv_data.get("end_time")

                    if start_time and end_time:
                        try:
                            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            duration = (end - start).total_seconds()
                            durations.append(duration)
                        except (ValueError, AttributeError):
                            continue
                elif isinstance(conv_data, list):
                    # For list format, use trace timestamps if available
                    trace_start = trace.get("start_time")
                    trace_end = trace.get("end_time")
                    
                    if trace_start and trace_end:
                        try:
                            start = datetime.fromisoformat(trace_start.replace('Z', '+00:00'))
                            end = datetime.fromisoformat(trace_end.replace('Z', '+00:00'))
                            duration = (end - start).total_seconds()
                            durations.append(duration)
                        except (ValueError, AttributeError):
                            continue

        if durations:
            return {
                "average_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": sorted(durations)[int(len(durations) * 0.95)]
            }
        else:
            return {
                "average_duration": 0,
                "min_duration": 0,
                "max_duration": 0,
                "p95_duration": 0
            }

    def _analyze_conversation_errors(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conversation error patterns"""
        error_patterns = {}
        total_conversations = 0
        conversations_with_errors = 0

        for trace in traces:
            if "agent" in trace and "conversation" in trace["agent"]:
                conv_data = trace["agent"]["conversation"]
                
                # Handle both dict and list formats
                if isinstance(conv_data, dict):
                    conv_id = conv_data.get("conversation_id", "unknown")
                    error = conv_data.get("error")

                    if conv_id not in error_patterns:
                        error_patterns[conv_id] = {"errors": [], "error_count": 0}

                    if error:
                        error_patterns[conv_id]["errors"].append(error)
                        error_patterns[conv_id]["error_count"] += 1
                        conversations_with_errors += 1

                    total_conversations += 1
                elif isinstance(conv_data, list):
                    # For list format, use trace ID and check for errors
                    conv_id = trace.get("trace_id", f"conv-{total_conversations}")
                    error = trace.get("error")

                    if conv_id not in error_patterns:
                        error_patterns[conv_id] = {"errors": [], "error_count": 0}

                    if error:
                        error_patterns[conv_id]["errors"].append(error)
                        error_patterns[conv_id]["error_count"] += 1
                        conversations_with_errors += 1

                    total_conversations += 1

        error_rate = conversations_with_errors / max(1, total_conversations)

        return {
            "total_conversations": total_conversations,
            "conversations_with_errors": conversations_with_errors,
            "error_rate": error_rate,
            "common_errors": self._extract_common_errors(error_patterns)
        }

    def _detect_stuck_conversations(self, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conversations that appear to be stuck"""
        stuck_conversations = []
        cutoff_time = datetime.utcnow() - timedelta(hours=1)  # 1 hour threshold

        for trace in traces:
            if "agent" in trace and "conversation" in trace["agent"]:
                conv_data = trace["agent"]["conversation"]
                
                # Handle both dict and list formats
                if isinstance(conv_data, dict):
                    last_activity = conv_data.get("last_activity")
                    completed = conv_data.get("completed", False)

                    if last_activity and not completed:
                        try:
                            activity_time = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                            if activity_time < cutoff_time:
                                stuck_conversations.append({
                                    "conversation_id": conv_data.get("conversation_id", "unknown"),
                                    "last_activity": last_activity,
                                    "turns": conv_data.get("turns", 0),
                                    "current_step": conv_data.get("current_step", "unknown")
                                })
                        except (ValueError, AttributeError):
                            continue
                elif isinstance(conv_data, list):
                    # For list format, use trace timestamp
                    last_activity = trace.get("last_activity")
                    completed = trace.get("completed", False)

                    if last_activity and not completed:
                        try:
                            activity_time = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                            if activity_time < cutoff_time:
                                stuck_conversations.append({
                                    "conversation_id": trace.get("trace_id", "unknown"),
                                    "last_activity": last_activity,
                                    "turns": len(conv_data),
                                    "current_step": trace.get("current_step", "unknown")
                                })
                        except (ValueError, AttributeError):
                            continue

        return stuck_conversations

    def _generate_conversation_health_summary(self, completion_data: Dict,
                                            duration_data: Dict, error_data: Dict,
                                            stuck_conversations: List) -> Dict[str, Any]:
        """Generate summary of conversation health"""
        summary = {
            "overall_health": "healthy",
            "issues": []
        }

        # Check completion rate
        if completion_data.get("completion_rate", 1.0) < 0.8:
            summary["issues"].append(f"Low completion rate: {completion_data['completion_rate']:.1%}")
            summary["overall_health"] = "warning"

        # Check error rate
        if error_data.get("error_rate", 0) > 0.1:
            summary["issues"].append(f"High error rate: {error_data['error_rate']:.1%}")
            summary["overall_health"] = "warning"

        # Check for stuck conversations
        if len(stuck_conversations) > 0:
            summary["issues"].append(f"{len(stuck_conversations)} stuck conversations detected")
            summary["overall_health"] = "critical"

        # Check duration outliers
        avg_duration = duration_data.get("average_duration", 0)
        if avg_duration > 3600:  # Over 1 hour average
            summary["issues"].append(f"High average conversation duration: {avg_duration/60:.1f} minutes")
            summary["overall_health"] = "warning"

        return summary

    def _check_component_readiness(self, traces: List[Dict[str, Any]]) -> List[str]:
        """Check which components are ready"""
        ready_components = set()

        for trace in traces:
            if "system" in trace and "components" in trace["system"]:
                for component in trace["system"]["components"]:
                    if component.get("ready", False):
                        ready_components.add(component["name"])

        return list(ready_components)

    def _identify_blocking_issues(self, traces: List[Dict[str, Any]]) -> List[str]:
        """Identify issues that block system operation"""
        blocking_issues = []

        for trace in traces:
            if "system" in trace and "blocking_issues" in trace["system"]:
                blocking_issues.extend(trace["system"]["blocking_issues"])

        return list(set(blocking_issues))  # Remove duplicates

    def _determine_overall_status(self, worker_health: Dict, conversation_health: Dict,
                                 system_readiness: Dict) -> str:
        """Determine overall system health status"""
        health_score = system_readiness.get("readiness_score", 0)

        if health_score >= 0.9:
            return "healthy"
        elif health_score >= 0.7:
            return "degraded"
        else:
            return "unhealthy"

    def _generate_health_recommendations(self, worker_health: Dict,
                                       conversation_health: Dict,
                                       system_readiness: Dict) -> List[str]:
        """Generate health recommendations"""
        recommendations = []

        # Worker health recommendations
        if worker_health.get("overall_health_score", 1.0) < 0.8:
            recommendations.append("Consider scaling agent workers or optimizing resource allocation")

        # Conversation health recommendations
        conv_summary = conversation_health.get("health_summary", {})
        if conv_summary.get("overall_health") == "critical":
            recommendations.append("Address stuck conversations and implement timeout mechanisms")

        if conv_summary.get("overall_health") == "warning":
            recommendations.append("Monitor conversation completion rates and error patterns")

        # System readiness recommendations
        if system_readiness.get("system_status") != "ready":
            blocking = system_readiness.get("blocking_issues", [])
            if blocking:
                recommendations.append(f"Resolve blocking issues: {', '.join(blocking[:3])}")

        return recommendations

    def _extract_common_errors(self, error_patterns: Dict) -> List[Dict[str, Any]]:
        """Extract most common error patterns"""
        error_counts = {}

        for conv_errors in error_patterns.values():
            for error in conv_errors["errors"]:
                error_type = error.get("type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

        # Return top 5 most common errors
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted_errors[:5]
        ]
