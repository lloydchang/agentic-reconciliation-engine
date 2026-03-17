#!/usr/bin/env python3
"""
Auto-Fix Capabilities for Agent Issues

Provides automated remediation for common agent system issues including
pod restarts, workflow clearing, resource adjustments, and health recovery.
"""

import subprocess
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AutoFixAction(Enum):
    RESTART_POD = "restart_pod"
    CLEAR_WORKFLOW = "clear_workflow"
    SCALE_RESOURCES = "scale_resources"
    ADJUST_TIMEOUTS = "adjust_timeouts"
    RESET_CIRCUIT_BREAKER = "reset_circuit_breaker"

@dataclass
class FixAttempt:
    """Represents an attempted auto-fix"""
    action: AutoFixAction
    target: str
    parameters: Dict[str, Any]
    timestamp: datetime
    success: bool = False
    error_message: Optional[str] = None
    verification_result: Optional[str] = None

class AutoFixManager:
    """Manages automated fixes for agent system issues"""

    def __init__(self):
        self.fix_history: List[FixAttempt] = []
        self.backoff_periods = {
            "pod_restart": 300,  # 5 minutes
            "workflow_clear": 60,  # 1 minute
            "resource_scale": 600,  # 10 minutes
        }

    def apply_fixes_for_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply automated fixes for detected issues"""
        results = {
            "fixes_applied": 0,
            "fixes_failed": 0,
            "backoff_prevented": 0,
            "fix_details": []
        }

        for issue in issues:
            if self._should_apply_fix(issue):
                fix_result = self._apply_fix_for_issue(issue)
                results["fix_details"].append(fix_result)

                if fix_result["success"]:
                    results["fixes_applied"] += 1
                else:
                    results["fixes_failed"] += 1
            else:
                results["backoff_prevented"] += 1

        return results

    def _should_apply_fix(self, issue: Dict[str, Any]) -> bool:
        """Determine if fix should be applied based on backoff and severity"""
        severity = issue.get("severity", "low")

        # Always apply critical fixes
        if severity == "critical":
            return True

        # Check backoff period for non-critical fixes
        issue_type = issue.get("type", "unknown")
        backoff_key = self._get_backoff_key(issue_type)

        if backoff_key in self.backoff_periods:
            recent_fixes = self._get_recent_fixes(backoff_key, self.backoff_periods[backoff_key])
            if recent_fixes:
                return False

        return True

    def _apply_fix_for_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific fix for an issue"""
        issue_type = issue.get("type", "unknown")
        issue_id = issue.get("id", "unknown")

        try:
            if issue_type == "agent_failure" and "pod" in issue.get("description", ""):
                return self._fix_pod_restart(issue)
            elif issue_type == "workflow_timeout":
                return self._fix_workflow_timeout(issue)
            elif issue_type == "resource_exhaustion":
                return self._fix_resource_exhaustion(issue)
            elif issue_type == "infrastructure":
                return self._fix_infrastructure_issue(issue)
            else:
                return {
                    "issue_id": issue_id,
                    "success": False,
                    "error": f"No auto-fix available for issue type: {issue_type}"
                }
        except Exception as e:
            logger.error(f"Auto-fix failed for issue {issue_id}: {str(e)}")
            return {
                "issue_id": issue_id,
                "success": False,
                "error": str(e)
            }

    def _fix_pod_restart(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix pod restart issues by restarting unhealthy pods"""
        pod_name = issue.get("metrics", {}).get("pod_name", "unknown")

        if pod_name == "unknown":
            return {"issue_id": issue["id"], "success": False, "error": "Pod name not found"}

        # Record fix attempt
        fix_attempt = FixAttempt(
            action=AutoFixAction.RESTART_POD,
            target=pod_name,
            parameters={"reason": "excessive_restarts"},
            timestamp=datetime.utcnow()
        )

        try:
            # Delete pod to trigger restart
            cmd = ["kubectl", "delete", "pod", pod_name, "--grace-period=0", "--force"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Wait for pod to restart
                time.sleep(10)

                # Verify pod is running
                verify_cmd = ["kubectl", "get", "pod", pod_name, "-o", "jsonpath={.status.phase}"]
                verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)

                if verify_result.returncode == 0 and "Running" in verify_result.stdout:
                    fix_attempt.success = True
                    fix_attempt.verification_result = "Pod restarted successfully"
                else:
                    fix_attempt.error_message = "Pod failed to restart properly"
            else:
                fix_attempt.error_message = f"kubectl delete failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            fix_attempt.error_message = "Pod restart timed out"
        except Exception as e:
            fix_attempt.error_message = str(e)

        self.fix_history.append(fix_attempt)

        return {
            "issue_id": issue["id"],
            "success": fix_attempt.success,
            "action": fix_attempt.action.value,
            "target": fix_attempt.target,
            "error": fix_attempt.error_message,
            "verification": fix_attempt.verification_result
        }

    def _fix_workflow_timeout(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix workflow timeout issues by terminating stuck workflows"""
        workflow_id = issue.get("metrics", {}).get("workflow_id", "unknown")

        if workflow_id == "unknown":
            return {"issue_id": issue["id"], "success": False, "error": "Workflow ID not found"}

        fix_attempt = FixAttempt(
            action=AutoFixAction.CLEAR_WORKFLOW,
            target=workflow_id,
            parameters={"reason": "timeout"},
            timestamp=datetime.utcnow()
        )

        try:
            # Terminate stuck workflow
            cmd = ["temporal", "workflow", "terminate", "--workflow-id", workflow_id]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                fix_attempt.success = True
                fix_attempt.verification_result = "Workflow terminated successfully"
            else:
                fix_attempt.error_message = f"Workflow termination failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            fix_attempt.error_message = "Workflow termination timed out"
        except Exception as e:
            fix_attempt.error_message = str(e)

        self.fix_history.append(fix_attempt)

        return {
            "issue_id": issue["id"],
            "success": fix_attempt.success,
            "action": fix_attempt.action.value,
            "target": fix_attempt.target,
            "error": fix_attempt.error_message,
            "verification": fix_attempt.verification_result
        }

    def _fix_resource_exhaustion(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix resource exhaustion by scaling resources"""
        deployment_name = issue.get("metrics", {}).get("deployment_name", "unknown")

        if deployment_name == "unknown":
            return {"issue_id": issue["id"], "success": False, "error": "Deployment name not found"}

        fix_attempt = FixAttempt(
            action=AutoFixAction.SCALE_RESOURCES,
            target=deployment_name,
            parameters={"cpu_increase": "200m", "memory_increase": "256Mi"},
            timestamp=datetime.utcnow()
        )

        try:
            # Scale up deployment resources
            patch_data = {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{
                                "name": "agent",
                                "resources": {
                                    "requests": {
                                        "cpu": "500m",
                                        "memory": "1Gi"
                                    },
                                    "limits": {
                                        "cpu": "1000m",
                                        "memory": "2Gi"
                                    }
                                }
                            }]
                        }
                    }
                }
            }

            import json
            cmd = ["kubectl", "patch", "deployment", deployment_name,
                   "--type", "merge", "-p", json.dumps(patch_data)]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                fix_attempt.success = True
                fix_attempt.verification_result = "Resource limits increased"
            else:
                fix_attempt.error_message = f"Resource scaling failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            fix_attempt.error_message = "Resource scaling timed out"
        except Exception as e:
            fix_attempt.error_message = str(e)

        self.fix_history.append(fix_attempt)

        return {
            "issue_id": issue["id"],
            "success": fix_attempt.success,
            "action": fix_attempt.action.value,
            "target": fix_attempt.target,
            "error": fix_attempt.error_message,
            "verification": fix_attempt.verification_result
        }

    def _fix_infrastructure_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fix general infrastructure issues"""
        # This is a placeholder for infrastructure-specific fixes
        # Could include node draining, service restarts, etc.
        return {
            "issue_id": issue["id"],
            "success": False,
            "error": "Infrastructure auto-fix not implemented for this issue type"
        }

    def _get_backoff_key(self, issue_type: str) -> str:
        """Get backoff key for issue type"""
        mapping = {
            "agent_failure": "pod_restart",
            "workflow_timeout": "workflow_clear",
            "resource_exhaustion": "resource_scale",
        }
        return mapping.get(issue_type, "unknown")

    def _get_recent_fixes(self, backoff_key: str, time_window_seconds: int) -> List[FixAttempt]:
        """Get recent fixes within time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)

        return [
            fix for fix in self.fix_history
            if fix.action.value == backoff_key and fix.timestamp > cutoff_time
        ]

    def get_fix_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent fix history"""
        return [
            {
                "action": fix.action.value,
                "target": fix.target,
                "timestamp": fix.timestamp.isoformat(),
                "success": fix.success,
                "error": fix.error_message,
                "verification": fix.verification_result
            }
            for fix in self.fix_history[-limit:]
        ]
