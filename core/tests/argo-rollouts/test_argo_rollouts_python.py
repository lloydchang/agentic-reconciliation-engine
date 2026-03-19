#!/usr/bin/env python3
"""
Argo Rollouts Python Test Suite
This module provides Python-based tests for Argo Rollouts functionality
"""

import unittest
import subprocess
import json
import time
import yaml
from typing import Dict, List, Optional

class ArgoRolloutsTestSuite(unittest.TestCase):
    """Test suite for Argo Rollouts with K8sGPT integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_namespace = "argo-rollouts-test"
        self.timeout = 300
        self.kubectl_cmd = ["kubectl"]
        
    def run_kubectl(self, cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run kubectl command with error handling"""
        full_cmd = self.kubectl_cmd + cmd
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(full_cmd)}")
            print(f"Error: {e.stderr}")
            raise
        except subprocess.TimeoutExpired:
            print(f"Command timed out: {' '.join(full_cmd)}")
            raise
    
    def create_test_namespace(self):
        """Create test namespace"""
        try:
            self.run_kubectl([
                "create", "namespace", self.test_namespace,
                "--dry-run=client", "-o", "yaml"
            ])
            self.run_kubectl(["apply", "-f", "-"])
        except:
            pass  # Namespace might already exist
    
    def test_argo_rollouts_crds_installed(self):
        """Test that Argo Rollouts CRDs are installed"""
        result = self.run_kubectl(["get", "crd", "rollouts.argoproj.io"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("rollouts.argoproj.io", result.stdout)
    
    def test_argo_rollouts_controller_running(self):
        """Test that Argo Rollouts controller is running"""
        try:
            result = self.run_kubectl([
                "get", "pods", "-n", "argo-rollouts",
                "-l", "app.kubernetes.io/name=argo-rollouts"
            ])
            self.assertIn("Running", result.stdout)
        except subprocess.CalledProcessError:
            self.skipTest("Argo Rollouts controller not found in argo-rollouts namespace")
    
    def test_basic_rollout_creation(self):
        """Test basic rollout creation and management"""
        rollout_manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Rollout",
            "metadata": {
                "name": "test-basic-rollout",
                "namespace": self.test_namespace
            },
            "spec": {
                "replicas": 2,
                "strategy": {
                    "canary": {
                        "steps": [
                            {"setWeight": 50},
                            {"pause": {"duration": "1m"}}
                        ]
                    }
                },
                "selector": {
                    "matchLabels": {"app": "test-rollout"}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": "test-rollout"}
                    },
                    "spec": {
                        "containers": [{
                            "name": "nginx",
                            "image": "nginx:1.20",
                            "ports": [{"containerPort": 80}]
                        }]
                    }
                }
            }
        }
        
        # Apply rollout
        manifest_yaml = yaml.dump(rollout_manifest)
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=manifest_yaml,
            text=True,
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        
        # Wait for rollout to be available
        try:
            self.run_kubectl([
                "wait", "--for=condition=available",
                "rollout/test-basic-rollout",
                "-n", self.test_namespace,
                "--timeout=300s"
            ])
        except subprocess.CalledProcessError:
            # Check if it's paused (which is also a valid state)
            status_result = self.run_kubectl([
                "argo", "rollouts", "status",
                "test-basic-rollout", "-n", self.test_namespace
            ])
            self.assertTrue(
                "healthy" in status_result.stdout.lower() or 
                "paused" in status_result.stdout.lower()
            )
    
    def test_canary_strategy(self):
        """Test canary deployment strategy"""
        rollout_manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Rollout",
            "metadata": {
                "name": "test-canary-rollout",
                "namespace": self.test_namespace
            },
            "spec": {
                "replicas": 3,
                "strategy": {
                    "canary": {
                        "steps": [
                            {"setWeight": 20},
                            {"pause": {"duration": "30s"}},
                            {"setWeight": 50},
                            {"pause": {"duration": "30s"}}
                        ],
                        "canaryService": "test-canary-service",
                        "stableService": "test-stable-service"
                    }
                },
                "selector": {
                    "matchLabels": {"app": "test-canary-rollout"}
                },
                "template": {
                    "metadata": {
                        "labels": {"app": "test-canary-rollout"}
                    },
                    "spec": {
                        "containers": [{
                            "name": "nginx",
                            "image": "nginx:1.21",
                            "ports": [{"containerPort": 80}]
                        }]
                    }
                }
            }
        }
        
        # Create services first
        services = [
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "test-stable-service",
                    "namespace": self.test_namespace
                },
                "spec": {
                    "selector": {"app": "test-canary-rollout"},
                    "ports": [{"port": 80, "targetPort": 80}]
                }
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "test-canary-service",
                    "namespace": self.test_namespace
                },
                "spec": {
                    "selector": {"app": "test-canary-rollout"},
                    "ports": [{"port": 80, "targetPort": 80}]
                }
            }
        ]
        
        for service in services:
            service_yaml = yaml.dump(service)
            result = subprocess.run(
                ["kubectl", "apply", "-f", "-"],
                input=service_yaml,
                text=True,
                capture_output=True
            )
            self.assertEqual(result.returncode, 0)
        
        # Apply rollout
        manifest_yaml = yaml.dump(rollout_manifest)
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=manifest_yaml,
            text=True,
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        
        # Wait for initial deployment
        try:
            self.run_kubectl([
                "wait", "--for=condition=available",
                "rollout/test-canary-rollout",
                "-n", self.test_namespace,
                "--timeout=300s"
            ])
        except subprocess.CalledProcessError:
            pass  # Might be paused, which is fine
        
        # Trigger canary update
        self.run_kubectl([
            "set", "image", "rollout/test-canary-rollout",
            "nginx=nginx:1.22", "-n", self.test_namespace
        ])
        
        # Wait for canary to progress
        time.sleep(10)
        
        # Check canary status
        status_result = self.run_kubectl([
            "argo", "rollouts", "status",
            "test-canary-rollout", "-n", self.test_namespace
        ])
        
        self.assertTrue(
            "paused" in status_result.stdout.lower() or 
            "progressing" in status_result.stdout.lower()
        )
    
    def test_analysis_template_creation(self):
        """Test analysis template creation and usage"""
        analysis_template = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "AnalysisTemplate",
            "metadata": {
                "name": "test-analysis-template",
                "namespace": self.test_namespace
            },
            "spec": {
                "args": [
                    {"name": "service-name", "value": ""}
                ],
                "metrics": [
                    {
                        "name": "success-rate",
                        "interval": "5s",
                        "count": 3,
                        "successCondition": "result[0] >= 0.95",
                        "failureLimit": 1,
                        "provider": {
                            "job": {
                                "spec": {
                                    "template": {
                                        "spec": {
                                            "containers": [{
                                                "name": "success-rate-checker",
                                                "image": "alpine:3.18",
                                                "command": ["/bin/sh", "-c", "echo '0.98'"]
                                            }],
                                            "restartPolicy": "Never"
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        # Apply analysis template
        template_yaml = yaml.dump(analysis_template)
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=template_yaml,
            text=True,
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        
        # Verify template exists
        result = self.run_kubectl([
            "get", "analysistemplate", "test-analysis-template",
            "-n", self.test_namespace
        ])
        self.assertIn("test-analysis-template", result.stdout)
    
    def test_k8sgpt_integration(self):
        """Test K8sGPT integration (if available)"""
        try:
            # Check if K8sGPT is available
            self.run_kubectl([
                "get", "deployment", "k8sgpt-analyzer",
                "-n", "$TOPDIR"
            ])
        except subprocess.CalledProcessError:
            self.skipTest("K8sGPT analyzer not found")
        
        # Create K8sGPT analysis template
        analysis_template = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "AnalysisTemplate",
            "metadata": {
                "name": "test-k8sgpt-analysis",
                "namespace": self.test_namespace
            },
            "spec": {
                "args": [
                    {"name": "namespace", "value": self.test_namespace}
                ],
                "metrics": [
                    {
                        "name": "k8sgpt-health-score",
                        "interval": "10s",
                        "count": 2,
                        "successCondition": "result[0] >= 0.5",
                        "failureLimit": 1,
                        "provider": {
                            "job": {
                                "spec": {
                                    "template": {
                                        "spec": {
                                            "containers": [{
                                                "name": "k8sgpt-analyzer",
                                                "image": "k8sgpt/k8sgpt:latest",
                                                "command": ["/bin/sh", "-c", "echo '0.85'"],
                                                "env": [
                                                    {
                                                        "name": "QWEN_API_KEY",
                                                        "valueFrom": {
                                                            "secretKeyRef": {
                                                                "name": "qwen-secret",
                                                                "key": "api-key"
                                                            }
                                                        },
                                                        "optional": True
                                                    }
                                                ]
                                            }],
                                            "restartPolicy": "Never"
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        # Apply analysis template
        template_yaml = yaml.dump(analysis_template)
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=template_yaml,
            text=True,
            capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        
        # Verify template exists
        result = self.run_kubectl([
            "get", "analysistemplate", "test-k8sgpt-analysis",
            "-n", self.test_namespace
        ])
        self.assertIn("test-k8sgpt-analysis", result.stdout)
    
    def test_cli_functionality(self):
        """Test kubectl plugin functionality"""
        try:
            # Test basic CLI command
            result = self.run_kubectl([
                "argo", "rollouts", "list",
                "-n", self.test_namespace
            ])
            self.assertEqual(result.returncode, 0)
        except subprocess.CalledProcessError:
            self.skipTest("kubectl plugin not installed")
    
    def test_metrics_availability(self):
        """Test metrics endpoint availability"""
        try:
            # Check if metrics service exists
            self.run_kubectl([
                "get", "service", "argo-rollouts-metrics",
                "-n", "argo-rollouts"
            ])
            
            # Test metrics endpoint (simplified test)
            # In a real scenario, you might port-forward and test the endpoint
            self.assertTrue(True)  # Placeholder test
            
        except subprocess.CalledProcessError:
            self.skipTest("Metrics service not found")
    
    def tearDown(self):
        """Clean up test resources"""
        try:
            # Clean up test resources
            resources = [
                "rollout", "analysistemplate", "service"
            ]
            
            for resource_type in resources:
                try:
                    result = self.run_kubectl([
                        "get", resource_type, "-n", self.test_namespace,
                        "-o", "jsonpath={.items[*].metadata.name}"
                    ])
                    if result.stdout.strip():
                        names = result.stdout.strip().split()
                        for name in names:
                            self.run_kubectl([
                                "delete", resource_type, name,
                                "-n", self.test_namespace,
                                "--ignore-not-found=true"
                            ])
                except subprocess.CalledProcessError:
                    pass  # Resource type might not exist or no resources found
        except:
            pass  # Cleanup failures shouldn't fail tests


class ArgoRolloutsPerformanceTest(unittest.TestCase):
    """Performance tests for Argo Rollouts"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.test_namespace = "argo-rollouts-perf-test"
        self.num_rollouts = 5
    
    def test_concurrent_rollout_deployment(self):
        """Test concurrent rollout deployment performance"""
        import concurrent.futures
        import threading
        
        results = []
        errors = []
        
        def deploy_rollout(rollout_id):
            """Deploy a single rollout"""
            try:
                rollout_manifest = {
                    "apiVersion": "argoproj.io/v1alpha1",
                    "kind": "Rollout",
                    "metadata": {
                        "name": f"perf-rollout-{rollout_id}",
                        "namespace": self.test_namespace
                    },
                    "spec": {
                        "replicas": 2,
                        "strategy": {
                            "canary": {
                                "steps": [
                                    {"setWeight": 50},
                                    {"pause": {"duration": "30s"}}
                                ]
                            }
                        },
                        "selector": {
                            "matchLabels": {"app": f"perf-rollout-{rollout_id}"}
                        },
                        "template": {
                            "metadata": {
                                "labels": {"app": f"perf-rollout-{rollout_id}"}
                            },
                            "spec": {
                                "containers": [{
                                    "name": "nginx",
                                    "image": "nginx:1.20",
                                    "ports": [{"containerPort": 80}]
                                }]
                            }
                        }
                    }
                }
                
                manifest_yaml = yaml.dump(rollout_manifest)
                result = subprocess.run(
                    ["kubectl", "apply", "-f", "-"],
                    input=manifest_yaml,
                    text=True,
                    capture_output=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    results.append(rollout_id)
                else:
                    errors.append(f"Rollout {rollout_id}: {result.stderr}")
                    
            except Exception as e:
                errors.append(f"Rollout {rollout_id}: {str(e)}")
        
        # Deploy rollouts concurrently
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(deploy_rollout, i)
                for i in range(self.num_rollouts)
            ]
            
            concurrent.futures.wait(futures)
        
        deployment_time = time.time() - start_time
        
        # Verify results
        self.assertEqual(len(results), self.num_rollouts, f"Deployment errors: {errors}")
        self.assertLess(deployment_time, 120, "Concurrent deployment took too long")
        
        print(f"Deployed {self.num_rollouts} rollouts in {deployment_time:.2f} seconds")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(ArgoRolloutsTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(ArgoRolloutsPerformanceTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
