#!/usr/bin/env python3
"""
Comprehensive Test Suite for K8sGPT Integration
Tests K8sGPT analyzer skill, Qwen integration, and Kubernetes deployment
"""

import unittest
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import time

# Add the skill directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core/ai/skills/k8sgpt-analyzer/scripts"))

try:
    from k8sgpt_analyzer import K8sGPTAnalyzer
    from qwen_integration import QwenIntegration
    from cluster_scanner import ClusterScanner
except ImportError as e:
    print(f"Warning: Could not import K8sGPT modules: {e}")
    K8sGPTAnalyzer = None
    QwenIntegration = None
    ClusterScanner = None


class TestK8sGPTAnalyzer(unittest.TestCase):
    """Test K8sGPT Analyzer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "backend": "localai",
            "model": "qwen2.5-7b-instruct",
            "baseurl": "http://localhost:8000/v1",
            "api_key": "test-key",
            "max_tokens": 1000,
            "temperature": 0.7,
            "timeout": 30,
            "cache_enabled": False,
            "log_level": "ERROR"
        }
        
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_config, self.temp_config)
        self.temp_config.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_config.name)
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    def test_analyzer_initialization(self):
        """Test K8sGPT analyzer initialization"""
        analyzer = K8sGPTAnalyzer()
        
        # Test default configuration
        self.assertIsNotNone(analyzer.config)
        self.assertIn('backend', analyzer.config)
        self.assertIn('model', analyzer.config)
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    def test_config_loading(self):
        """Test configuration loading"""
        analyzer = K8sGPTAnalyzer()
        config = analyzer._load_config(self.temp_config.name)
        
        self.assertEqual(config['backend'], 'localai')
        self.assertEqual(config['model'], 'qwen2.5-7b-instruct')
        self.assertEqual(config['baseurl'], 'http://localhost:8000/v1')
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    def test_input_validation(self):
        """Test input validation"""
        analyzer = K8sGPTAnalyzer()
        
        # Valid input
        valid_input = {
            "operation": "analyze",
            "targetResource": "cluster",
            "backend": "qwen"
        }
        self.assertTrue(analyzer._validate_input(valid_input))
        
        # Invalid input - missing operation
        invalid_input = {
            "targetResource": "cluster",
            "backend": "qwen"
        }
        self.assertFalse(analyzer._validate_input(invalid_input))
        
        # Invalid input - invalid operation
        invalid_input2 = {
            "operation": "invalid",
            "targetResource": "cluster",
            "backend": "qwen"
        }
        self.assertFalse(analyzer._validate_input(invalid_input2))
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    @patch('subprocess.run')
    def test_k8sgpt_command_execution(self, mock_run):
        """Test K8sGPT command execution"""
        # Mock successful command execution
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"problems": []}',
            stderr=''
        )
        
        analyzer = K8sGPTAnalyzer()
        result = analyzer._execute_k8sgpt_command(['analyze', '--explain'])
        
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], '{"problems": []}')
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    @patch('subprocess.run')
    def test_k8sgpt_command_failure(self, mock_run):
        """Test K8sGPT command failure handling"""
        # Mock failed command execution
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Error: command failed'
        )
        
        analyzer = K8sGPTAnalyzer()
        result = analyzer._execute_k8sgpt_command(['analyze', '--explain'])
        
        self.assertEqual(result['returncode'], 1)
        self.assertEqual(result['stderr'], 'Error: command failed')


class TestQwenIntegration(unittest.TestCase):
    """Test Qwen LLM integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.qwen_config = {
            "model": "qwen2.5-7b-instruct",
            "baseurl": "http://localhost:8000/v1",
            "api_key": "test-key",
            "timeout": 30
        }
    
    @unittest.skipUnless(QwenIntegration, "QwenIntegration not available")
    def test_qwen_initialization(self):
        """Test Qwen integration initialization"""
        qwen = QwenIntegration()
        
        self.assertIsNotNone(qwen.config)
        self.assertIn('model', qwen.config)
        self.assertIn('baseurl', qwen.config)
    
    @unittest.skipUnless(QwenIntegration, "QwenIntegration not available")
    def test_qwen_config_validation(self):
        """Test Qwen configuration validation"""
        qwen = QwenIntegration()
        
        # Valid configuration
        valid_config = {
            "model": "qwen2.5-7b-instruct",
            "baseurl": "http://localhost:8000/v1",
            "api_key": "test-key"
        }
        self.assertTrue(qwen._validate_config(valid_config))
        
        # Invalid configuration - missing model
        invalid_config = {
            "baseurl": "http://localhost:8000/v1",
            "api_key": "test-key"
        }
        self.assertFalse(qwen._validate_config(invalid_config))
    
    @unittest.skipUnless(QwenIntegration, "QwenIntegration not available")
    @patch('requests.post')
    def test_qwen_connection_test(self, mock_post):
        """Test Qwen connection testing"""
        # Mock successful response
        mock_post.return_value = MagicMock(
            status_code=200,
            json.return_value={"choices": [{"message": {"content": "test response"}}]}
        )
        
        qwen = QwenIntegration()
        result = qwen.test_connection()
        
        self.assertTrue(result['success'])
        self.assertIn('response_time', result)
    
    @unittest.skipUnless(QwenIntegration, "QwenIntegration not available")
    @patch('requests.post')
    def test_qwen_connection_failure(self, mock_post):
        """Test Qwen connection failure"""
        # Mock failed response
        mock_post.return_value = MagicMock(
            status_code=500,
            text="Internal Server Error"
        )
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        qwen = QwenIntegration()
        result = qwen.test_connection()
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestClusterScanner(unittest.TestCase):
    """Test cluster scanning functionality"""
    
    @unittest.skipUnless(ClusterScanner, "ClusterScanner not available")
    def test_scanner_initialization(self):
        """Test cluster scanner initialization"""
        scanner = ClusterScanner()
        self.assertIsNotNone(scanner.logger)
    
    @unittest.skipUnless(ClusterScanner, "ClusterScanner not available")
    @patch('subprocess.run')
    def test_cluster_info_gathering(self, mock_run):
        """Test cluster information gathering"""
        # Mock kubectl commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='test-context\n'),  # current-context
            MagicMock(returncode=0, stdout='Kubernetes control plane\n'),  # cluster-info
            MagicMock(returncode=0, stdout='Client Version: v1.28.0\n'),  # version
        ]
        
        scanner = ClusterScanner()
        info = scanner._get_cluster_info()
        
        self.assertEqual(info['current_context'], 'test-context')
        self.assertIn('cluster_info', info)
        self.assertIn('version', info)
    
    @unittest.skipUnless(ClusterScanner, "ClusterScanner not available")
    @patch('subprocess.run')
    def test_cluster_metrics_gathering(self, mock_run):
        """Test cluster metrics gathering"""
        # Mock kubectl commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='node1 Ready\nnode2 Ready\n'),  # nodes
            MagicMock(returncode=0, stdout='default Active\nkube-system Active\n'),  # namespaces
            MagicMock(returncode=0, stdout='default pod1 Running\n'),  # pods
            MagicMock(returncode=0, stdout='default svc1 ClusterIP\n'),  # services
            MagicMock(returncode=0, stdout='default deploy1 Ready\n'),  # deployments
        ]
        
        scanner = ClusterScanner()
        metrics = scanner._get_cluster_metrics()
        
        self.assertEqual(metrics['node_count'], 2)
        self.assertEqual(metrics['namespace_count'], 2)
        self.assertIn('pod_counts', metrics)
        self.assertEqual(metrics['service_count'], 1)
        self.assertEqual(metrics['deployment_count'], 1)
    
    @unittest.skipUnless(ClusterScanner, "ClusterScanner not available")
    def test_pod_analysis(self):
        """Test pod analysis functionality"""
        scanner = ClusterScanner()
        
        # Test data
        pods = [
            {
                "metadata": {"name": "pod1", "namespace": "default"},
                "status": {
                    "phase": "Running",
                    "containerStatuses": [
                        {
                            "name": "container1",
                            "restartCount": 0,
                            "ready": True,
                            "state": {"running": {}}
                        }
                    ]
                }
            },
            {
                "metadata": {"name": "pod2", "namespace": "default"},
                "status": {
                    "phase": "Pending",
                    "containerStatuses": [
                        {
                            "name": "container1",
                            "restartCount": 5,
                            "ready": False,
                            "state": {
                                "waiting": {
                                    "reason": "ImagePullBackOff"
                                }
                            }
                        }
                    ]
                }
            }
        ]
        
        analysis = scanner._analyze_pods(pods)
        
        self.assertEqual(analysis['status_counts']['Running'], 1)
        self.assertEqual(analysis['status_counts']['Pending'], 1)
        self.assertEqual(analysis['restart_counts']['container1'], 5)
        self.assertEqual(len(analysis['image_pull_issues']), 1)


class TestKubernetesDeployment(unittest.TestCase):
    """Test Kubernetes deployment manifests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).parent.parent.parent
        self.overlay_dir = self.repo_root / "overlay/k8sgpt"
    
    def test_overlay_directory_exists(self):
        """Test that overlay directory exists"""
        self.assertTrue(self.overlay_dir.exists(), "K8sGPT overlay directory should exist")
    
    def test_required_manifests_exist(self):
        """Test that required Kubernetes manifests exist"""
        required_files = [
            "kustomization.yaml",
            "deployments/k8sgpt-analyzer.yaml",
            "services/k8sgpt-analyzer.yaml",
            "configmaps/k8sgpt-config.yaml",
            "rbac/k8sgpt-rbac.yaml",
            "network/networkpolicy.yaml"
        ]
        
        for file_path in required_files:
            full_path = self.overlay_dir / file_path
            self.assertTrue(full_path.exists(), f"Required manifest {file_path} should exist")
    
    def test_kustomization_yaml_valid(self):
        """Test that kustomization.yaml is valid"""
        kustomization_file = self.overlay_dir / "kustomization.yaml"
        
        if kustomization_file.exists():
            content = kustomization_file.read_text()
            
            # Check for required fields
            self.assertIn("apiVersion: kustomize.config.k8s.io/v1beta1", content)
            self.assertIn("kind: Kustomization", content)
            self.assertIn("resources:", content)
    
    def test_deployment_manifest_valid(self):
        """Test that deployment manifest is valid"""
        deployment_file = self.overlay_dir / "deployments/k8sgpt-analyzer.yaml"
        
        if deployment_file.exists():
            content = deployment_file.read_text()
            
            # Check for required fields
            self.assertIn("apiVersion: apps/v1", content)
            self.assertIn("kind: Deployment", content)
            self.assertIn("metadata:", content)
            self.assertIn("spec:", content)
            self.assertIn("selector:", content)
            self.assertIn("template:", content)


class TestIntegrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""
    
    @unittest.skipUnless(os.system("which kubectl > /dev/null 2>&1") == 0, "kubectl not available")
    def test_kubectl_availability(self):
        """Test that kubectl is available and working"""
        result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "kubectl should be available")
    
    @unittest.skipUnless(os.system("which k8sgpt > /dev/null 2>&1") == 0, "k8sgpt not available")
    def test_k8sgpt_availability(self):
        """Test that k8sgpt is available and working"""
        result = subprocess.run(['k8sgpt', 'version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "k8sgpt should be available")
    
    def test_skill_files_exist(self):
        """Test that skill files exist and are readable"""
        repo_root = Path(__file__).parent.parent.parent
        skill_dir = repo_root / "core/ai/skills/k8sgpt-analyzer"
        
        required_files = [
            "SKILL.md",
            "scripts/k8sgpt_analyzer.py",
            "scripts/qwen_integration.py",
            "scripts/cluster_scanner.py"
        ]
        
        for file_path in required_files:
            full_path = skill_dir / file_path
            self.assertTrue(full_path.exists(), f"Skill file {file_path} should exist")
            self.assertTrue(full_path.is_file(), f"Skill file {file_path} should be a file")
    
    def test_documentation_exists(self):
        """Test that documentation files exist"""
        repo_root = Path(__file__).parent.parent.parent
        
        required_docs = [
            "docs/K8SGPT-INTEGRATION-GUIDE.md",
            "docs/K8SGPT-QUICKSTART.md"
        ]
        
        for doc_path in required_docs:
            full_path = repo_root / doc_path
            self.assertTrue(full_path.exists(), f"Documentation {doc_path} should exist")
    
    def test_setup_script_exists(self):
        """Test that setup script exists and is executable"""
        repo_root = Path(__file__).parent.parent.parent
        setup_script = repo_root / "scripts/setup-k8sgpt.sh"
        
        self.assertTrue(setup_script.exists(), "Setup script should exist")
        self.assertTrue(os.access(setup_script, os.X_OK), "Setup script should be executable")


class TestPerformanceAndLoad(unittest.TestCase):
    """Performance and load testing"""
    
    @unittest.skipUnless(K8sGPTAnalyzer, "K8sGPTAnalyzer not available")
    def test_analyzer_performance(self):
        """Test analyzer performance"""
        analyzer = K8sGPTAnalyzer()
        
        # Test configuration loading performance
        start_time = time.time()
        for _ in range(10):
            analyzer._load_default_config()
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        self.assertLess(avg_time, 0.1, "Configuration loading should be fast")
    
    @unittest.skipUnless(ClusterScanner, "ClusterScanner not available")
    @patch('subprocess.run')
    def test_scanner_performance(self, mock_run):
        """Test cluster scanner performance"""
        # Mock fast responses
        mock_run.return_value = MagicMock(returncode=0, stdout="test\n")
        
        scanner = ClusterScanner()
        
        start_time = time.time()
        scanner._get_cluster_info()
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 1.0, "Cluster info gathering should be fast")


def run_integration_tests():
    """Run all integration tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestK8sGPTAnalyzer,
        TestQwenIntegration,
        TestClusterScanner,
        TestKubernetesDeployment,
        TestIntegrationEndToEnd,
        TestPerformanceAndLoad
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return result
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 K8sGPT Integration Test Suite")
    print("=" * 50)
    
    success = run_integration_tests()
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
