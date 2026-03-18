"""
Sandbox Manager for Open SWE Gateway
Kubernetes-native sandbox provisioning and management
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class SandboxManager:
    """Manages isolated sandboxes for agent task execution"""

    def __init__(self, namespace: str = "ai-infrastructure"):
        self.namespace = namespace
        self.core_v1 = None
        self.apps_v1 = None
        self.active_sandboxes = {}

        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    async def create_sandbox(self, task_id: str, resources: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an isolated sandbox for task execution"""

        if resources is None:
            resources = self._get_default_resources()

        sandbox_id = str(uuid.uuid4())
        sandbox_namespace = f"sandbox-{task_id}"

        try:
            # Create isolated namespace
            await self._create_namespace(sandbox_namespace)

            # Create sandbox pod
            pod_manifest = self._create_pod_manifest(
                sandbox_id, task_id, sandbox_namespace, resources
            )
            pod = await self._create_pod(sandbox_namespace, pod_manifest)

            # Store sandbox info
            sandbox_info = {
                "id": sandbox_id,
                "task_id": task_id,
                "namespace": sandbox_namespace,
                "pod_name": pod.metadata.name,
                "status": "creating",
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=2),
                "resources": resources
            }

            self.active_sandboxes[task_id] = sandbox_info

            logger.info(f"Created sandbox {sandbox_id} for task {task_id}")
            return sandbox_info

        except Exception as e:
            logger.error(f"Failed to create sandbox for task {task_id}: {str(e)}")
            await self._cleanup_failed_sandbox(sandbox_namespace)
            raise

    async def get_sandbox_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of sandbox for task"""

        if task_id not in self.active_sandboxes:
            return None

        sandbox_info = self.active_sandboxes[task_id]

        try:
            # Get pod status
            pod = await self._get_pod(
                sandbox_info["namespace"],
                sandbox_info["pod_name"]
            )

            sandbox_info["status"] = self._map_pod_status(pod.status.phase)
            sandbox_info["last_checked"] = datetime.utcnow()

            return sandbox_info

        except Exception as e:
            logger.error(f"Failed to get sandbox status for task {task_id}: {str(e)}")
            return None

    async def destroy_sandbox(self, task_id: str) -> bool:
        """Destroy sandbox for task"""

        if task_id not in self.active_sandboxes:
            return False

        sandbox_info = self.active_sandboxes[task_id]

        try:
            # Delete namespace (cascading delete)
            await self._delete_namespace(sandbox_info["namespace"])

            # Remove from active sandboxes
            del self.active_sandboxes[task_id]

            logger.info(f"Destroyed sandbox for task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to destroy sandbox for task {task_id}: {str(e)}")
            return False

    async def cleanup_expired_sandboxes(self):
        """Clean up expired sandboxes"""

        current_time = datetime.utcnow()
        expired_tasks = []

        for task_id, sandbox_info in self.active_sandboxes.items():
            if current_time > sandbox_info["expires_at"]:
                expired_tasks.append(task_id)

        for task_id in expired_tasks:
            await self.destroy_sandbox(task_id)
            logger.info(f"Cleaned up expired sandbox for task {task_id}")

    def _get_default_resources(self) -> Dict[str, Any]:
        """Get default resource limits for sandboxes"""

        return {
            "requests": {
                "cpu": "100m",
                "memory": "256Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "1Gi",
                "ephemeral-storage": "2Gi"
            }
        }

    async def _create_namespace(self, namespace: str):
        """Create isolated namespace for sandbox"""

        ns_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace,
                "labels": {
                    "app": "open-swe-sandbox",
                    "managed-by": "sandbox-operator"
                }
            }
        }

        try:
            self.core_v1.create_namespace(ns_manifest)
        except ApiException as e:
            if e.status != 409:  # Namespace already exists
                raise

    async def _create_pod(self, namespace: str, pod_manifest: Dict[str, Any]):
        """Create sandbox pod"""

        return self.core_v1.create_namespaced_pod(namespace, pod_manifest)

    async def _get_pod(self, namespace: str, pod_name: str):
        """Get pod information"""

        return self.core_v1.read_namespaced_pod(pod_name, namespace)

    async def _delete_namespace(self, namespace: str):
        """Delete sandbox namespace"""

        self.core_v1.delete_namespace(namespace)

    async def _cleanup_failed_sandbox(self, namespace: str):
        """Clean up resources from failed sandbox creation"""

        try:
            await self._delete_namespace(namespace)
        except:
            pass  # Ignore cleanup errors

    def _create_pod_manifest(self, sandbox_id: str, task_id: str,
                           namespace: str, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Create pod manifest for sandbox"""

        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": f"sandbox-pod-{task_id}",
                "namespace": namespace,
                "labels": {
                    "app": "open-swe-sandbox",
                    "sandbox-id": sandbox_id,
                    "task-id": task_id,
                    "managed-by": "sandbox-operator"
                }
            },
            "spec": {
                "containers": [{
                    "name": "agent-sandbox",
                    "image": "gitops-infra-control-plane/agent-sandbox:latest",
                    "resources": resources,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 1000,
                        "readOnlyRootFilesystem": True,
                        "capabilities": {
                            "drop": ["ALL"]
                        }
                    },
                    "volumeMounts": [{
                        "name": "workspace",
                        "mountPath": "/workspace"
                    }]
                }],
                "volumes": [{
                    "name": "workspace",
                    "emptyDir": {}
                }],
                "restartPolicy": "Never"
            }
        }

    def _map_pod_status(self, phase: str) -> str:
        """Map Kubernetes pod phase to sandbox status"""

        status_mapping = {
            "Pending": "creating",
            "Running": "running",
            "Succeeded": "completed",
            "Failed": "failed",
            "Unknown": "unknown"
        }

        return status_mapping.get(phase, "unknown")

# Background cleanup task
async def run_cleanup_loop(sandbox_manager: SandboxManager, interval: int = 300):
    """Run periodic cleanup of expired sandboxes"""

    while True:
        try:
            await sandbox_manager.cleanup_expired_sandboxes()
        except Exception as e:
            logger.error(f"Sandbox cleanup failed: {str(e)}")

        await asyncio.sleep(interval)
