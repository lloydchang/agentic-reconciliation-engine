"""
Unified Observability System for Open SWE Integration

This module provides comprehensive monitoring, metrics collection, distributed tracing,
and alerting across all components of the Open SWE integration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from enum import Enum
import asyncio
import logging
import time
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"      # Monotonically increasing value
    GAUGE = "gauge"         # Value that can go up or down
    HISTOGRAM = "histogram" # Distribution of values
    SUMMARY = "summary"     # Quantiles over sliding time window


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class MetricValue:
    """Individual metric measurement"""
    name: str
    value: Union[int, float]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus format"""
        labels_str = ""
        if self.labels:
            labels_str = "{" + ",".join(f'{k}="{v}"' for k, v in self.labels.items()) + "}"

        return f"{self.name}{labels_str} {self.value} {int(self.timestamp * 1000)}"


@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    query: str  # PromQL-style query or simple expression
    severity: AlertSeverity
    threshold: Union[int, float]
    duration: int  # seconds - how long condition must be true
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def evaluate(self, metrics: Dict[str, MetricValue]) -> bool:
        """Evaluate alert rule against metrics"""
        # Simple threshold evaluation (would be more complex with PromQL)
        try:
            if ">" in self.query:
                metric_name, threshold = self.query.split(">")
                metric_value = metrics.get(metric_name.strip())
                if metric_value and metric_value.value > float(threshold.strip()):
                    return True
            elif "<" in self.query:
                metric_name, threshold = self.query.split("<")
                metric_value = metrics.get(metric_name.strip())
                if metric_value and metric_value.value < float(threshold.strip()):
                    return True
            return False
        except (ValueError, KeyError):
            return False


@dataclass
class Alert:
    """Active alert instance"""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    description: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    starts_at: datetime
    ends_at: Optional[datetime] = None
    generator_url: Optional[str] = None

    @property
    def duration(self) -> Optional[timedelta]:
        """Get alert duration"""
        if self.ends_at:
            return self.ends_at - self.starts_at
        return datetime.now() - self.starts_at


@dataclass
class TraceSpan:
    """Distributed tracing span"""
    id: str
    trace_id: str
    parent_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self):
        """Finish the span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def add_log(self, event: str, payload: Dict[str, Any] = None):
        """Add log entry to span"""
        self.logs.append({
            "timestamp": time.time(),
            "event": event,
            "payload": payload or {}
        })

    def set_tag(self, key: str, value: Any):
        """Set span tag"""
        self.tags[key] = value


@dataclass
class Trace:
    """Complete trace with all spans"""
    id: str
    root_span: TraceSpan
    spans: List[TraceSpan] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    def finish(self):
        """Finish the trace"""
        self.end_time = time.time()
        for span in self.spans:
            if not span.end_time:
                span.finish()

    @property
    def total_duration(self) -> float:
        """Get total trace duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


class MetricsCollector:
    """Metrics collection and storage"""

    def __init__(self, retention_period: int = 3600):  # 1 hour default
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.retention_period = retention_period
        self.collection_tasks: Dict[str, asyncio.Task] = {}

    def record_metric(self, metric: MetricValue):
        """Record a metric measurement"""
        self.metrics[metric.name].append(metric)

        # Clean up old metrics
        self._cleanup_old_metrics()

    def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[MetricValue]:
        """Get latest metric value"""
        metrics = self.metrics.get(name, deque())
        if not metrics:
            return None

        if labels:
            # Find metric with matching labels
            for metric in reversed(metrics):
                if metric.labels == labels:
                    return metric
        else:
            # Return latest metric
            return metrics[-1]

        return None

    def get_metric_series(self, name: str, start_time: float = None,
                         end_time: float = None) -> List[MetricValue]:
        """Get metric time series"""
        metrics = self.metrics.get(name, deque())
        if not metrics:
            return []

        filtered = list(metrics)

        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]
        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]

        return filtered

    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        current = self.get_metric(name, labels)
        new_value = (current.value if current else 0) + value

        metric = MetricValue(
            name=name,
            value=new_value,
            timestamp=time.time(),
            labels=labels or {},
            metric_type=MetricType.COUNTER
        )
        self.record_metric(metric)

    def set_gauge(self, name: str, value: Union[int, float], labels: Dict[str, str] = None):
        """Set a gauge metric"""
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            metric_type=MetricType.GAUGE
        )
        self.record_metric(metric)

    def observe_histogram(self, name: str, value: Union[int, float], labels: Dict[str, str] = None):
        """Observe a histogram metric"""
        metric = MetricValue(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            metric_type=MetricType.HISTOGRAM
        )
        self.record_metric(metric)

    def _cleanup_old_metrics(self):
        """Clean up metrics older than retention period"""
        cutoff_time = time.time() - self.retention_period

        for name, metrics_queue in self.metrics.items():
            while metrics_queue and metrics_queue[0].timestamp < cutoff_time:
                metrics_queue.popleft()

    async def start_collection(self, collection_functions: Dict[str, Callable[[], Awaitable[Dict[str, Any]]]]):
        """Start automatic metrics collection"""
        for name, func in collection_functions.items():
            task = asyncio.create_task(self._collect_metrics(name, func))
            self.collection_tasks[name] = task

    async def stop_collection(self):
        """Stop automatic metrics collection"""
        for task in self.collection_tasks.values():
            task.cancel()
        await asyncio.gather(*self.collection_tasks.values(), return_exceptions=True)

    async def _collect_metrics(self, name: str, func: Callable[[], Awaitable[Dict[str, Any]]]):
        """Collect metrics from function"""
        while True:
            try:
                metrics_data = await func()
                for metric_name, value in metrics_data.items():
                    if isinstance(value, dict):
                        self.set_gauge(metric_name, value.get('value', 0), value.get('labels', {}))
                    else:
                        self.set_gauge(metric_name, value)
                await asyncio.sleep(30)  # Collect every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection failed for {name}: {e}")
                await asyncio.sleep(60)  # Wait longer on error


class AlertManager:
    """Alert management and notification"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_handlers: List[Callable[[Alert], Awaitable[None]]] = []

    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_rules[rule.id] = rule

    def remove_alert_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]

    def add_notification_handler(self, handler: Callable[[Alert], Awaitable[None]]):
        """Add alert notification handler"""
        self.notification_handlers.append(handler)

    async def evaluate_alerts(self):
        """Evaluate all alert rules"""
        # Get latest metrics for evaluation
        latest_metrics = {}
        for rule in self.alert_rules.values():
            # Extract metric names from queries (simplified)
            if ">" in rule.query or "<" in rule.query:
                metric_name = rule.query.split()[0]
                metric = self.metrics.get_metric(metric_name)
                if metric:
                    latest_metrics[metric_name] = metric

        # Evaluate each rule
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            alert_id = f"{rule.id}_{hash(str(latest_metrics))}"

            if rule.evaluate(latest_metrics):
                # Check if alert is already firing
                if alert_id not in self.active_alerts:
                    # Create new alert
                    alert = Alert(
                        id=alert_id,
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        status=AlertStatus.FIRING,
                        description=rule.description,
                        labels=rule.labels,
                        annotations=rule.annotations,
                        starts_at=datetime.now()
                    )
                    self.active_alerts[alert_id] = alert
                    self.alert_history.append(alert)

                    # Notify handlers
                    await self._notify_handlers(alert)
                # Alert is already firing, do nothing
            else:
                # Check if alert was firing and should be resolved
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.status = AlertStatus.RESOLVED
                    alert.ends_at = datetime.now()
                    del self.active_alerts[alert_id]

                    # Notify handlers of resolution
                    await self._notify_handlers(alert)

    async def _notify_handlers(self, alert: Alert):
        """Notify all notification handlers"""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert notification failed: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]


class TraceCollector:
    """Distributed tracing collection"""

    def __init__(self, retention_period: int = 3600):
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, TraceSpan] = {}
        self.retention_period = retention_period
        self.trace_cleanup_task: Optional[asyncio.Task] = None

    def start_trace(self, name: str, trace_id: str = None) -> TraceSpan:
        """Start a new trace"""
        if not trace_id:
            trace_id = f"{int(time.time() * 1000000)}_{asyncio.get_event_loop().time()}"

        root_span = TraceSpan(
            id=f"{trace_id}_root",
            trace_id=trace_id,
            parent_id=None,
            name=name,
            start_time=time.time()
        )

        trace = Trace(id=trace_id, root_span=root_span)
        self.traces[trace_id] = trace
        self.active_spans[root_span.id] = root_span

        return root_span

    def start_span(self, name: str, parent_span: TraceSpan = None) -> TraceSpan:
        """Start a new span within a trace"""
        parent_id = parent_span.id if parent_span else None
        trace_id = parent_span.trace_id if parent_span else None

        if not trace_id:
            # Create new trace if no parent
            return self.start_trace(name)

        span = TraceSpan(
            id=f"{trace_id}_{len(self.traces[trace_id].spans)}",
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time()
        )

        self.traces[trace_id].spans.append(span)
        self.active_spans[span.id] = span

        return span

    def finish_span(self, span: TraceSpan):
        """Finish a span"""
        span.finish()
        if span.id in self.active_spans:
            del self.active_spans[span.id]

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get complete trace"""
        return self.traces.get(trace_id)

    def get_active_traces(self) -> List[Trace]:
        """Get traces with active spans"""
        active_trace_ids = {span.trace_id for span in self.active_spans.values()}
        return [self.traces[trace_id] for trace_id in active_trace_ids if trace_id in self.traces]

    async def start_cleanup(self):
        """Start periodic trace cleanup"""
        self.trace_cleanup_task = asyncio.create_task(self._cleanup_traces())

    async def stop_cleanup(self):
        """Stop trace cleanup"""
        if self.trace_cleanup_task:
            self.trace_cleanup_task.cancel()
            try:
                await self.trace_cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_traces(self):
        """Clean up old traces"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                cutoff_time = time.time() - self.retention_period

                traces_to_remove = []
                for trace_id, trace in self.traces.items():
                    if trace.end_time and trace.end_time < cutoff_time:
                        traces_to_remove.append(trace_id)

                for trace_id in traces_to_remove:
                    del self.traces[trace_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trace cleanup failed: {e}"


class ObservabilitySystem:
    """Unified observability system"""

    def __init__(self):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager(self.metrics)
        self.traces = TraceCollector()
        self.started = False

    async def start(self):
        """Start the observability system"""
        if self.started:
            return

        # Start trace cleanup
        await self.traces.start_cleanup()

        # Start metrics collection for system components
        await self.metrics.start_collection({
            "system_metrics": self._collect_system_metrics,
            "component_health": self._collect_component_health
        })

        # Set up default alert rules
        self._setup_default_alerts()

        self.started = True
        logger.info("Observability system started")

    async def stop(self):
        """Stop the observability system"""
        await self.metrics.stop_collection()
        await self.traces.stop_cleanup()
        self.started = False
        logger.info("Observability system stopped")

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics"""
        return {
            "cpu_usage": 0.0,  # Would integrate with psutil or similar
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_connections": 0
        }

    async def _collect_component_health(self) -> Dict[str, Any]:
        """Collect component health metrics"""
        return {
            "gateway_healthy": 1,
            "agents_active": 5,
            "requests_per_second": 10.5,
            "error_rate": 0.02
        }

    def _setup_default_alerts(self):
        """Set up default alert rules"""
        alerts = [
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate is above threshold",
                query="error_rate > 0.05",
                severity=AlertSeverity.WARNING,
                threshold=0.05,
                duration=300
            ),
            AlertRule(
                id="gateway_unhealthy",
                name="Gateway Unhealthy",
                description="Gateway service is not responding",
                query="gateway_healthy < 1",
                severity=AlertSeverity.CRITICAL,
                threshold=1,
                duration=60
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is critically high",
                query="memory_usage > 0.9",
                severity=AlertSeverity.ERROR,
                threshold=0.9,
                duration=120
            )
        ]

        for alert in alerts:
            self.alerts.add_alert_rule(alert)

    # Convenience methods for common operations

    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.metrics.increment_counter("http_requests_total", labels={"method": method, "status": str(status_code)})
        self.metrics.observe_histogram("http_request_duration", duration, {"method": method})

    def record_agent_execution(self, agent_name: str, success: bool, duration: float):
        """Record agent execution metrics"""
        status = "success" if success else "failure"
        self.metrics.increment_counter("agent_executions_total", labels={"agent": agent_name, "status": status})
        self.metrics.observe_histogram("agent_execution_duration", duration, {"agent": agent_name})

    def record_platform_request(self, platform: str, success: bool):
        """Record platform request metrics"""
        status = "success" if success else "failure"
        self.metrics.increment_counter("platform_requests_total", labels={"platform": platform, "status": status})

    def create_trace_span(self, name: str, parent: TraceSpan = None) -> TraceSpan:
        """Create a new trace span"""
        return self.traces.start_span(name, parent)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "total_metrics": sum(len(metrics) for metrics in self.metrics.metrics.values()),
            "active_alerts": len(self.alerts.get_active_alerts()),
            "active_traces": len(self.traces.get_active_traces()),
            "total_traces": len(self.traces.traces)
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        active_alerts = self.alerts.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]

        status = "healthy"
        if critical_alerts:
            status = "critical"
        elif active_alerts:
            status = "warning"

        return {
            "status": status,
            "active_alerts": len(active_alerts),
            "critical_alerts": len(critical_alerts),
            "uptime": time.time() - (asyncio.get_event_loop().time() if hasattr(asyncio.get_event_loop(), 'time') else time.time())
        }


# Export key classes
__all__ = [
    'MetricType',
    'AlertSeverity',
    'AlertStatus',
    'MetricValue',
    'AlertRule',
    'Alert',
    'TraceSpan',
    'Trace',
    'MetricsCollector',
    'AlertManager',
    'TraceCollector',
    'ObservabilitySystem'
]
