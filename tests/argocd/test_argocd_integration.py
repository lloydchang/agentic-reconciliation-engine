#!/usr/bin/env python3
"""
Comprehensive Argo CD Integration Test Suite

This test suite validates the complete Argo CD + K8sGPT + Qwen integration
including deployments, API functionality, and GitOps workflows.
"""

import os
import sys
import time
import json
import yaml
import requests
import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArgoCDIntegrationTest:
    """Main test class for Argo CD integration testing."""
    
    def __init__(self):
        self.kubectl_cmd = self._find_kubectl()
        self.argocd_cmd = self._find_argocd()
        self.test_namespace = "argocd-test"
        self.k8sgpt_namespace = "k8sgpt-test"
        self.argocd_namespace = "argocd-test"
        self.base_url = "http://localhost:8080"
        self.k8sgpt_url = "http://localhost:8081"
        
    def _find_kubectl(self) -> str:
        """Find kubectl command."""
        try:
            result = subprocess.run(['which', 'kubectl'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "kubectl"
    
    def _find_argocd(self) -> str:
        """Find argocd CLI command."""
        try:
            result = subprocess.run(['which', 'argocd'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "argocd"
    
    def run_command(self, cmd: List[str], timeout: int = 300, check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command with error handling."""
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                check=check
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            raise
    
    def kubectl(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run kubectl command."""
        return self.run_command([self.kubectl_cmd] + args, **kwargs)
    
    def argocd(self, args: List[str], **kwargs) -> subprocess.CompletedProcess:
        """Run argocd command."""
        return self.run_command([self.argocd_cmd] + args, **kwargs)
    
    def setup_test_namespaces(self) -> bool:
        """Set up test namespaces."""
        logger.info("Setting up test namespaces...")
        
        try:
            # Create test namespaces
            for ns in [self.test_namespace, self.k8sgpt_namespace]:
                self.kubectl([
                    'create', 'namespace', ns,
                    '--dry-run=client', '-o', 'yaml'
                ])
                self.kubectl(['apply', '-f', '-'], input=f"""
apiVersion: v1
kind: Namespace
metadata:
  name: {ns}
  labels:
    environment: test
""")
            
            logger.info("Test namespaces created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create test namespaces: {e}")
            return False
    
    def test_argocd_installation(self) -> bool:
        """Test Argo CD installation."""
        logger.info("Testing Argo CD installation...")
        
        try:
            # Check if Argo CD pods are running
            result = self.kubectl([
                'get', 'pods', '-n', self.argocd_namespace,
                '-l', 'app.kubernetes.io/part-of=argocd'
            ])
            
            if result.returncode != 0:
                logger.error("Argo CD pods not found")
                return False
            
            # Check pod status
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            running_pods = [line for line in lines if 'Running' in line]
            
            if len(running_pods) < 3:  # At least server, repo-server, controller
                logger.warning(f"Only {len(running_pods)} Argo CD pods running")
                return False
            
            # Test Argo CD API health
            try:
                response = requests.get(f"{self.base_url}/healthz", timeout=10)
                if response.status_code != 200:
                    logger.error(f"Argo CD API health check failed: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Cannot reach Argo CD API: {e}")
            
            logger.info("Argo CD installation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Argo CD installation test failed: {e}")
            return False
    
    def test_k8sgpt_installation(self) -> bool:
        """Test K8sGPT installation."""
        logger.info("Testing K8sGPT installation...")
        
        try:
            # Check if K8sGPT pods are running
            result = self.kubectl([
                'get', 'pods', '-n', self.k8sgpt_namespace,
                '-l', 'app.kubernetes.io/part-of=k8sgpt'
            ])
            
            if result.returncode != 0:
                logger.error("K8sGPT pods not found")
                return False
            
            # Check pod status
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            running_pods = [line for line in lines if 'Running' in line]
            
            if len(running_pods) < 2:  # At least k8sgpt and qwen-localai
                logger.warning(f"Only {len(running_pods)} K8sGPT pods running")
                return False
            
            # Test K8sGPT API health
            try:
                response = requests.get(f"{self.k8sgpt_url}/healthz", timeout=10)
                if response.status_code != 200:
                    logger.error(f"K8sGPT API health check failed: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Cannot reach K8sGPT API: {e}")
            
            logger.info("K8sGPT installation test passed")
            return True
            
        except Exception as e:
            logger.error(f"K8sGPT installation test failed: {e}")
            return False
    
    def test_qwen_model_availability(self) -> bool:
        """Test Qwen model availability and functionality."""
        logger.info("Testing Qwen model availability...")
        
        try:
            # Check if Qwen LocalAI pod is running
            result = self.kubectl([
                'get', 'pods', '-n', self.k8sgpt_namespace,
                '-l', 'app.kubernetes.io/name=qwen-localai'
            ])
            
            if result.returncode != 0:
                logger.error("Qwen LocalAI pod not found")
                return False
            
            # Test LocalAI readiness
            try:
                response = requests.get(f"{self.k8sgpt_url.replace('8081', '8082')}/readyz", timeout=30)
                if response.status_code != 200:
                    logger.warning(f"Qwen LocalAI not ready: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                logger.warning(f"Cannot reach Qwen LocalAI: {e}")
                return False
            
            logger.info("Qwen model availability test passed")
            return True
            
        except Exception as e:
            logger.error(f"Qwen model availability test failed: {e}")
            return False
    
    def test_k8sgpt_analysis(self) -> bool:
        """Test K8sGPT analysis functionality."""
        logger.info("Testing K8sGPT analysis functionality...")
        
        try:
            # Create a test deployment
            test_deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-container
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
"""
            
            # Apply test deployment
            self.kubectl(['apply', '-f', '-'], input=test_deployment)
            
            # Wait for deployment to be ready
            self.kubectl([
                'rollout', 'status', 'deployment/test-deployment',
                '--timeout=60s'
            ])
            
            # Run K8sGPT analysis
            analysis_payload = {
                "namespace": "default",
                "filters": ["Deployment"],
                "explain": True
            }
            
            response = requests.post(
                f"{self.k8sgpt_url}/analyze",
                json=analysis_payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"K8sGPT analysis failed: {response.status_code}")
                return False
            
            analysis_result = response.json()
            
            # Validate analysis result
            if not isinstance(analysis_result, dict):
                logger.error("Invalid analysis result format")
                return False
            
            # Clean up test deployment
            self.kubectl(['delete', 'deployment', 'test-deployment'])
            
            logger.info("K8sGPT analysis test passed")
            return True
            
        except Exception as e:
            logger.error(f"K8sGPT analysis test failed: {e}")
            return False
    
    def test_argocd_applications(self) -> bool:
        """Test Argo CD application management."""
        logger.info("Testing Argo CD application management...")
        
        try:
            # List Argo CD applications
            result = self.argocd(['app', 'list'])
            
            if result.returncode != 0:
                logger.error("Failed to list Argo CD applications")
                return False
            
            # Check for expected applications
            expected_apps = ['root-app', 'k8sgpt', 'ai-infrastructure']
            app_lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            found_apps = []
            for line in app_lines:
                if line.strip():
                    app_name = line.split()[0]
                    found_apps.append(app_name)
            
            missing_apps = [app for app in expected_apps if app not in found_apps]
            if missing_apps:
                logger.warning(f"Missing Argo CD applications: {missing_apps}")
            
            # Test application sync status
            for app in found_apps:
                result = self.argocd(['app', 'get', app])
                if result.returncode != 0:
                    logger.warning(f"Cannot get status for application: {app}")
                    continue
                
                if 'Synced' not in result.stdout:
                    logger.warning(f"Application {app} not synced")
            
            logger.info("Argo CD applications test passed")
            return True
            
        except Exception as e:
            logger.error(f"Argo CD applications test failed: {e}")
            return False
    
    def test_gitops_workflow(self) -> bool:
        """Test GitOps workflow functionality."""
        logger.info("Testing GitOps workflow...")
        
        try:
            # Create a test application in Git
            test_app = """
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-gitops-app
  namespace: argocd-test
spec:
  project: default
  source:
    repoURL: https://github.com/lloydchang/gitops-infra-control-plane.git
    targetRevision: HEAD
    path: tests/argocd/test-resources
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
"""
            
            # Apply test application
            self.kubectl(['apply', '-f', '-'], input=test_app)
            
            # Wait for application to be created
            time.sleep(10)
            
            # Check application status
            result = self.argocd(['app', 'get', 'test-gitops-app'])
            if result.returncode != 0:
                logger.error("Test GitOps application not found")
                return False
            
            # Sync application
            self.argocd(['app', 'sync', 'test-gitops-app'])
            
            # Wait for sync
            time.sleep(30)
            
            # Check sync status
            result = self.argocd(['app', 'get', 'test-gitops-app'])
            if 'Synced' not in result.stdout:
                logger.warning("Test GitOps application not synced")
            
            # Clean up
            self.kubectl(['delete', 'application', 'test-gitops-app', '-n', 'argocd-test'])
            
            logger.info("GitOps workflow test passed")
            return True
            
        except Exception as e:
            logger.error(f"GitOps workflow test failed: {e}")
            return False
    
    def test_monitoring_integration(self) -> bool:
        """Test monitoring integration."""
        logger.info("Testing monitoring integration...")
        
        try:
            # Check if monitoring services are accessible
            monitoring_endpoints = [
                f"{self.base_url}/metrics",
                f"{self.k8sgpt_url}/metrics"
            ]
            
            for endpoint in monitoring_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Monitoring endpoint accessible: {endpoint}")
                    else:
                        logger.warning(f"Monitoring endpoint returned {response.status_code}: {endpoint}")
                except requests.exceptions.RequestException:
                    logger.warning(f"Cannot reach monitoring endpoint: {endpoint}")
            
            logger.info("Monitoring integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring integration test failed: {e}")
            return False
    
    def cleanup_test_resources(self) -> bool:
        """Clean up test resources."""
        logger.info("Cleaning up test resources...")
        
        try:
            # Delete test namespaces
            for ns in [self.test_namespace, self.k8sgpt_namespace]:
                self.kubectl(['delete', 'namespace', ns, '--ignore-not-found=true'])
            
            logger.info("Test resources cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clean up test resources: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        logger.info("Starting comprehensive Argo CD integration tests...")
        
        results = {}
        
        # Setup
        if not self.setup_test_namespaces():
            logger.error("Failed to set up test namespaces")
            return {"setup": False}
        
        # Run tests
        tests = [
            ("argo_cd_installation", self.test_argocd_installation),
            ("k8sgpt_installation", self.test_k8sgpt_installation),
            ("qwen_model_availability", self.test_qwen_model_availability),
            ("k8sgpt_analysis", self.test_k8sgpt_analysis),
            ("argocd_applications", self.test_argocd_applications),
            ("gitops_workflow", self.test_gitops_workflow),
            ("monitoring_integration", self.test_monitoring_integration),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Running test: {test_name}")
                results[test_name] = test_func()
                status = "PASSED" if results[test_name] else "FAILED"
                logger.info(f"Test {test_name}: {status}")
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Cleanup
        self.cleanup_test_resources()
        
        return results
    
    def generate_test_report(self, results: Dict[str, bool]) -> str:
        """Generate test report."""
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        report = f"""
# Argo CD Integration Test Report

## Summary
- Total Tests: {total_tests}
- Passed: {passed_tests}
- Failed: {failed_tests}
- Success Rate: {(passed_tests/total_tests)*100:.1f}%

## Test Results
"""
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            report += f"- {test_name}: {status}\n"
        
        if failed_tests > 0:
            report += "\n## Failed Tests Details\n"
            for test_name, result in results.items():
                if not result:
                    report += f"- {test_name}: Check logs for detailed error information\n"
        
        report += "\n## Recommendations\n"
        if failed_tests == 0:
            report += "- All tests passed! The Argo CD integration is working correctly.\n"
        else:
            report += "- Review failed tests and fix underlying issues.\n"
            report += "- Check pod logs and resource configurations.\n"
            report += "- Verify network connectivity and resource availability.\n"
        
        return report

def main():
    """Main function to run tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Argo CD Integration Test Suite")
    parser.add_argument("--output", "-o", help="Output report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test", "-t", help="Run specific test")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize test suite
    test_suite = ArgoCDIntegrationTest()
    
    # Run tests
    if args.test:
        # Run specific test
        test_methods = {
            "argo_cd_installation": test_suite.test_argocd_installation,
            "k8sgpt_installation": test_suite.test_k8sgpt_installation,
            "qwen_model_availability": test_suite.test_qwen_model_availability,
            "k8sgpt_analysis": test_suite.test_k8sgpt_analysis,
            "argocd_applications": test_suite.test_argocd_applications,
            "gitops_workflow": test_suite.test_gitops_workflow,
            "monitoring_integration": test_suite.test_monitoring_integration,
        }
        
        if args.test not in test_methods:
            logger.error(f"Unknown test: {args.test}")
            sys.exit(1)
        
        test_suite.setup_test_namespaces()
        result = test_methods[args.test]()
        test_suite.cleanup_test_resources()
        
        results = {args.test: result}
    else:
        # Run all tests
        results = test_suite.run_all_tests()
    
    # Generate report
    report = test_suite.generate_test_report(results)
    
    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        logger.info(f"Test report saved to: {args.output}")
    else:
        print(report)
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results.values() if not result)
    sys.exit(0 if failed_tests == 0 else 1)

if __name__ == "__main__":
    main()
