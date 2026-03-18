#!/usr/bin/env python3
"""
OpenSWE Integration Test Suite
Tests the complete OpenSWE integration with Temporal and GitOps
"""

import unittest
import subprocess
import os
import tempfile
import shutil
import time
from pathlib import Path
import yaml
import json

class TestOpenSWEIntegration(unittest.TestCase):
    """Test suite for OpenSWE integration functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="openswe_test_")
        self.project_root = Path(__file__).parent.parent.parent.parent.parent

        # Test repository setup
        self.test_repo = Path(self.test_dir) / "test_repo"
        self.test_repo.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=self.test_repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_repo, check=True)

        # Create test file
        test_file = self.test_repo / "hello.py"
        test_file.write_text("""
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")

        subprocess.run(["git", "add", "hello.py"], cwd=self.test_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_repo, check=True)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_openswe_agent_communication(self):
        """Test basic agent communication layer"""
        # Import the agent communication module
        import sys
        sys.path.insert(0, str(self.project_root / "core/ai/runtime/openswe-integration"))

        try:
            from agents.communication import OpenSWEAgent

            # Test agent initialization
            agent = OpenSWEAgent()
            self.assertIsNotNone(agent)

            # Test basic message handling
            result = agent.handle_request({
                "action": "ping",
                "data": {"message": "test"}
            })

            self.assertIn("status", result)
            self.assertEqual(result["status"], "success")

        except ImportError as e:
            self.skipTest(f"Agent module not available: {e}")

    def test_safety_engine_validation(self):
        """Test safety engine validation rules"""
        try:
            from components.safety import SafetyEngine

            engine = SafetyEngine()

            # Test allowed operation
            safe_request = {
                "action": "edit_file",
                "file": "test.py",
                "content": "print('safe code')"
            }

            result = engine.validate_request(safe_request)
            self.assertTrue(result["allowed"])

            # Test blocked operation
            unsafe_request = {
                "action": "delete_file",
                "file": "/etc/passwd"
            }

            result = engine.validate_request(unsafe_request)
            self.assertFalse(result["allowed"])

        except ImportError as e:
            self.skipTest(f"Safety engine not available: {e}")

    def test_workflow_orchestration(self):
        """Test Temporal workflow orchestration"""
        try:
            from workflows.session import OpenSWEWorkflow

            # Test workflow initialization
            workflow = OpenSWEWorkflow()
            self.assertIsNotNone(workflow)

            # Test session creation
            session_id = workflow.create_session({
                "user": "test_user",
                "repository": str(self.test_repo),
                "task": "Add error handling to hello.py"
            })

            self.assertIsNotNone(session_id)
            self.assertIsInstance(session_id, str)

        except ImportError as e:
            self.skipTest(f"Workflow module not available: {e}")

    def test_kubernetes_deployments(self):
        """Test Kubernetes deployment manifests"""
        deployment_path = self.project_root / "core/ai/runtime/openswe-integration/deployments"

        # Check if deployment files exist
        self.assertTrue((deployment_path / "kustomization.yaml").exists())
        self.assertTrue((deployment_path / "openswe-agent-deployment.yaml").exists())

        # Validate YAML syntax
        with open(deployment_path / "kustomization.yaml") as f:
            kustomization = yaml.safe_load(f)
            self.assertIn("resources", kustomization)

        with open(deployment_path / "openswe-agent-deployment.yaml") as f:
            deployment = yaml.safe_load(f)
            self.assertEqual(deployment["kind"], "Deployment")
            self.assertEqual(deployment["metadata"]["name"], "openswe-agent")

    def test_gitops_integration(self):
        """Test GitOps integration components"""
        # Test that deployment follows GitOps patterns
        deployment_file = self.project_root / "core/ai/runtime/openswe-integration/deployments/openswe-agent-deployment.yaml"

        with open(deployment_file) as f:
            deployment = yaml.safe_load(f)

        # Check for required labels
        metadata = deployment["metadata"]
        self.assertIn("labels", metadata)

        labels = metadata["labels"]
        self.assertIn("app", labels)
        self.assertIn("component", labels)

        # Check for resource limits
        spec = deployment["spec"]["template"]["spec"]
        containers = spec["containers"]
        self.assertTrue(len(containers) > 0)

        container = containers[0]
        self.assertIn("resources", container)
        self.assertIn("limits", container["resources"])
        self.assertIn("requests", container["resources"])

    def test_monitoring_setup(self):
        """Test monitoring and observability setup"""
        # This would test Prometheus metrics, health checks, etc.
        # For now, just check that monitoring endpoints are defined
        try:
            from components.monitoring import MonitoringService

            service = MonitoringService()

            # Test metrics collection
            metrics = service.get_metrics()
            self.assertIsInstance(metrics, dict)
            self.assertIn("uptime", metrics)

        except ImportError:
            self.skipTest("Monitoring service not available")

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # This is a comprehensive test that would simulate:
        # 1. Creating a development session
        # 2. Making AI-assisted code changes
        # 3. Validating changes through safety checks
        # 4. Committing changes via GitOps
        # 5. Deploying through CI/CD pipeline

        # For now, skip this as it requires full environment setup
        self.skipTest("End-to-end test requires full environment setup")


if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOpenSWEIntegration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    exit(0 if (len(result.failures) == 0 and len(result.errors) == 0) else 1)
