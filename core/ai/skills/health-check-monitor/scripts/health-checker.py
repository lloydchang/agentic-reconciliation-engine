#!/usr/bin/env python3
"""
Health Check Monitor - Kubernetes Cluster Monitoring Skill

This script monitors Kubernetes cluster health, resource utilization,
and generates alerts for potential issues.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import re

class HealthCheckMonitor:
    """Kubernetes health monitoring agent."""

    def __init__(self, cluster: str = "", namespace: str = ""):
        self.cluster = cluster or self._get_current_context()
        self.namespace = namespace
        self.alerts: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}

    def _get_current_context(self) -> str:
        """Get current kubectl context."""
        try:
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _run_kubectl(self, command: List[str]) -> Dict[str, Any]:
        """Run kubectl command and return parsed JSON."""
        try:
            cmd = ["kubectl"] + command
            if self.namespace and "--all-namespaces" not in command:
                cmd.extend(["-n", self.namespace])

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running kubectl: {e}", file=sys.stderr)
            return {}
        except json.JSONDecodeError:
            print(f"Error parsing kubectl output: {result.stdout}", file=sys.stderr)
            return {}

    def check_node_health(self) -> None:
        """Check health of cluster nodes."""
        nodes = self._run_kubectl(["get", "nodes", "-o", "json"])

        for node in nodes.get("items", []):
            node_name = node["metadata"]["name"]
            status = node["status"]

            # Check node conditions
            for condition in status.get("conditions", []):
                if condition["type"] == "Ready" and condition["status"] != "True":
                    self._add_alert("CRITICAL", f"Node {node_name} is not ready",
                                  {"node": node_name, "condition": condition})

                if condition["type"] == "MemoryPressure" and condition["status"] == "True":
                    self._add_alert("WARNING", f"Node {node_name} has memory pressure",
                                  {"node": node_name})

                if condition["type"] == "DiskPressure" and condition["status"] == "True":
                    self._add_alert("WARNING", f"Node {node_name} has disk pressure",
                                  {"node": node_name})

            # Check resource allocation
            alloc = status.get("allocatable", {})
            capacity = status.get("capacity", {})

            cpu_usage = self._calculate_cpu_usage(alloc, capacity)
            memory_usage = self._calculate_memory_usage(alloc, capacity)

            self.metrics[f"node_{node_name}_cpu"] = cpu_usage
            self.metrics[f"node_{node_name}_memory"] = memory_usage

            if cpu_usage > 80:
                self._add_alert("WARNING", f"Node {node_name} CPU usage high: {cpu_usage:.1f}%",
                              {"node": node_name, "usage": cpu_usage})

            if memory_usage > 85:
                self._add_alert("WARNING", f"Node {node_name} memory usage high: {memory_usage:.1f}%",
                              {"node": node_name, "usage": memory_usage})

    def check_pod_health(self) -> None:
        """Check health of pods."""
        pods = self._run_kubectl(["get", "pods", "-o", "json"])

        for pod in pods.get("items", []):
            pod_name = pod["metadata"]["name"]
            namespace = pod["metadata"]["namespace"]
            status = pod["status"]

            phase = status["phase"]
            if phase in ["Failed", "CrashLoopBackOff"]:
                self._add_alert("CRITICAL", f"Pod {namespace}/{pod_name} in {phase} state",
                              {"pod": pod_name, "namespace": namespace, "phase": phase})

            elif phase == "Pending":
                # Check how long it's been pending
                start_time = status.get("startTime")
                if start_time:
                    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    duration = datetime.now().astimezone() - start
                    if duration.total_seconds() > 300:  # 5 minutes
                        self._add_alert("WARNING", f"Pod {namespace}/{pod_name} pending for {duration}",
                                      {"pod": pod_name, "namespace": namespace, "duration": str(duration)})

            # Check container statuses
            for container in status.get("containerStatuses", []):
                if not container.get("ready", False):
                    self._add_alert("WARNING", f"Container {container['name']} in pod {namespace}/{pod_name} not ready",
                                  {"pod": pod_name, "namespace": namespace, "container": container["name"]})

                # Check restarts
                restart_count = container.get("restartCount", 0)
                if restart_count > 5:
                    self._add_alert("WARNING", f"Container {container['name']} restarted {restart_count} times",
                                  {"pod": pod_name, "namespace": namespace, "container": container["name"], "restarts": restart_count})

    def check_resource_quotas(self) -> None:
        """Check resource quota usage."""
        try:
            quotas = self._run_kubectl(["get", "resourcequota", "-o", "json"])
        except:
            return  # Resource quotas may not be defined

        for quota in quotas.get("items", []):
            name = quota["metadata"]["name"]
            namespace = quota["metadata"]["namespace"]
            status = quota["status"]

            used = status.get("used", {})
            hard = status.get("hard", {})

            for resource, hard_limit in hard.items():
                used_amount = used.get(resource, "0")
                usage_percent = self._calculate_quota_usage(used_amount, hard_limit)

                self.metrics[f"quota_{namespace}_{name}_{resource}"] = usage_percent

                if usage_percent > 90:
                    self._add_alert("WARNING", f"Resource quota {namespace}/{name} {resource} usage: {usage_percent:.1f}%",
                                  {"namespace": namespace, "quota": name, "resource": resource, "usage": usage_percent})

    def _calculate_cpu_usage(self, alloc: Dict, capacity: Dict) -> float:
        """Calculate CPU usage percentage."""
        try:
            alloc_cpu = self._parse_cpu(alloc.get("cpu", "0"))
            capacity_cpu = self._parse_cpu(capacity.get("cpu", "0"))
            if capacity_cpu > 0:
                return ((capacity_cpu - alloc_cpu) / capacity_cpu) * 100
        except:
            pass
        return 0.0

    def _calculate_memory_usage(self, alloc: Dict, capacity: Dict) -> float:
        """Calculate memory usage percentage."""
        try:
            alloc_mem = self._parse_memory(alloc.get("memory", "0"))
            capacity_mem = self._parse_memory(capacity.get("memory", "0"))
            if capacity_mem > 0:
                return ((capacity_mem - alloc_mem) / capacity_mem) * 100
        except:
            pass
        return 0.0

    def _calculate_quota_usage(self, used: str, hard: str) -> float:
        """Calculate resource quota usage percentage."""
        try:
            used_val = self._parse_resource_quantity(used)
            hard_val = self._parse_resource_quantity(hard)
            if hard_val > 0:
                return (used_val / hard_val) * 100
        except:
            pass
        return 0.0

    def _parse_cpu(self, cpu_str: str) -> float:
        """Parse CPU quantity to cores."""
        cpu_str = cpu_str.lower().strip()
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)

    def _parse_memory(self, mem_str: str) -> float:
        """Parse memory quantity to bytes."""
        mem_str = mem_str.lower().strip()
        if mem_str.endswith('ki'):
            return float(mem_str[:-2]) * 1024
        elif mem_str.endswith('mi'):
            return float(mem_str[:-2]) * 1024 * 1024
        elif mem_str.endswith('gi'):
            return float(mem_str[:-2]) * 1024 * 1024 * 1024
        return float(mem_str)

    def _parse_resource_quantity(self, qty_str: str) -> float:
        """Parse Kubernetes resource quantity."""
        qty_str = qty_str.lower().strip()
        if qty_str.endswith('m'):  # milli-units
            return float(qty_str[:-1]) / 1000
        elif qty_str.endswith('ki'):
            return float(qty_str[:-2]) * 1024
        elif qty_str.endswith('mi'):
            return float(qty_str[:-2]) * 1024 * 1024
        elif qty_str.endswith('gi'):
            return float(qty_str[:-2]) * 1024 * 1024 * 1024
        elif qty_str.endswith('k'):
            return float(qty_str[:-1]) * 1000
        elif qty_str.endswith('m'):
            return float(qty_str[:-1]) * 1000 * 1000
        elif qty_str.endswith('g'):
            return float(qty_str[:-1]) * 1000 * 1000 * 1000
        return float(qty_str)

    def _add_alert(self, severity: str, message: str, details: Dict[str, Any]) -> None:
        """Add an alert to the alerts list."""
        alert = {
            "severity": severity,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "cluster": self.cluster
        }
        self.alerts.append(alert)

    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results."""
        print(f"Running health checks for cluster: {self.cluster}")

        self.check_node_health()
        self.check_pod_health()
        self.check_resource_quotas()

        result = {
            "cluster": self.cluster,
            "namespace": self.namespace or "all",
            "timestamp": datetime.now().isoformat(),
            "alerts": self.alerts,
            "metrics": self.metrics,
            "summary": {
                "total_alerts": len(self.alerts),
                "critical_alerts": len([a for a in self.alerts if a["severity"] == "CRITICAL"]),
                "warning_alerts": len([a for a in self.alerts if a["severity"] == "WARNING"])
            }
        }

        return result

    def print_report(self, result: Dict[str, Any]) -> None:
        """Print a human-readable health report."""
        print("\n" + "="*60)
        print(f"KUBERNETES HEALTH REPORT - {result['cluster']}")
        print("="*60)
        print(f"Timestamp: {result['timestamp']}")
        print(f"Namespace: {result['namespace']}")
        print()

        summary = result["summary"]
        print("SUMMARY:")
        print(f"  Total Alerts: {summary['total_alerts']}")
        print(f"  Critical: {summary['critical_alerts']}")
        print(f"  Warnings: {summary['warning_alerts']}")
        print()

        if result["alerts"]:
            print("ALERTS:")
            for alert in result["alerts"]:
                print(f"  [{alert['severity']}] {alert['message']}")
                for key, value in alert["details"].items():
                    print(f"    {key}: {value}")
                print()
        else:
            print("✅ No alerts found - cluster appears healthy")

        print("METRICS:")
        for key, value in result["metrics"].items():
            if isinstance(value, float):
                print(".1f"            else:
                print(f"  {key}: {value}")

def main():
    parser = argparse.ArgumentParser(description="Kubernetes Health Check Monitor")
    parser.add_argument("--cluster", help="Target cluster name")
    parser.add_argument("--namespace", "-n", help="Target namespace")
    parser.add_argument("--output", "-o", choices=["json", "text"], default="text",
                       help="Output format")

    args = parser.parse_args()

    monitor = HealthCheckMonitor(cluster=args.cluster, namespace=args.namespace)
    result = monitor.run_health_checks()

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        monitor.print_report(result)

if __name__ == "__main__":
    main()
