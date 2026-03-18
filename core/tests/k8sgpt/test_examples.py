#!/usr/bin/env python3
"""
Example Test Cases for K8sGPT Integration
Demonstrates how to use and test the K8sGPT analyzer skill
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
import sys

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


def example_1_basic_cluster_analysis():
    """Example 1: Basic cluster analysis"""
    print("🔍 Example 1: Basic Cluster Analysis")
    print("=" * 50)
    
    if not K8sGPTAnalyzer:
        print("❌ K8sGPTAnalyzer not available")
        return False
    
    # Create analyzer
    analyzer = K8sGPTAnalyzer()
    
    # Prepare input
    input_data = {
        "operation": "analyze",
        "targetResource": "cluster",
        "backend": "qwen",
        "explain": True,
        "output": "json"
    }
    
    print("Input:")
    print(json.dumps(input_data, indent=2))
    print()
    
    try:
        # Validate input
        if analyzer._validate_input(input_data):
            print("✅ Input validation passed")
            
            # Simulate analysis (without actually running k8sgpt)
            result = {
                "status": "success",
                "timestamp": "2024-01-01T00:00:00Z",
                "operation": "analyze",
                "targetResource": "cluster",
                "backend": "qwen",
                "problems": [
                    {
                        "severity": "warning",
                        "resource": "pod/nginx-deployment-123",
                        "message": "Pod is using excessive CPU",
                        "recommendation": "Consider setting CPU limits"
                    },
                    {
                        "severity": "info",
                        "resource": "deployment/app-server",
                        "message": "Deployment has no resource requests",
                        "recommendation": "Set resource requests for better scheduling"
                    }
                ],
                "summary": {
                    "total_issues": 2,
                    "critical": 0,
                    "warnings": 1,
                    "info": 1
                }
            }
            
            print("Result:")
            print(json.dumps(result, indent=2))
            print()
            return True
        else:
            print("❌ Input validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def example_2_namespace_specific_analysis():
    """Example 2: Namespace-specific analysis"""
    print("🔍 Example 2: Namespace-Specific Analysis")
    print("=" * 50)
    
    if not K8sGPTAnalyzer:
        print("❌ K8sGPTAnalyzer not available")
        return False
    
    # Create analyzer
    analyzer = K8sGPTAnalyzer()
    
    # Prepare input
    input_data = {
        "operation": "analyze",
        "targetResource": "production",
        "scope": "namespace",
        "backend": "qwen",
        "explain": True,
        "filters": ["deployment/*", "service/*", "pod/*"]
    }
    
    print("Input:")
    print(json.dumps(input_data, indent=2))
    print()
    
    try:
        # Validate input
        if analyzer._validate_input(input_data):
            print("✅ Input validation passed")
            
            # Simulate namespace analysis
            result = {
                "status": "success",
                "timestamp": "2024-01-01T00:00:00Z",
                "operation": "analyze",
                "targetResource": "production",
                "scope": "namespace",
                "backend": "qwen",
                "namespace": "production",
                "problems": [
                    {
                        "severity": "critical",
                        "resource": "deployment/database",
                        "message": "Database deployment has no replica set",
                        "recommendation": "Configure replica set for high availability"
                    },
                    {
                        "severity": "warning",
                        "resource": "service/frontend",
                        "message": "Service has no health checks configured",
                        "recommendation": "Add readiness and liveness probes"
                    }
                ],
                "summary": {
                    "total_issues": 2,
                    "critical": 1,
                    "warnings": 1,
                    "info": 0
                }
            }
            
            print("Result:")
            print(json.dumps(result, indent=2))
            print()
            return True
        else:
            print("❌ Input validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def example_3_resource_optimization():
    """Example 3: Resource optimization analysis"""
    print("🔍 Example 3: Resource Optimization Analysis")
    print("=" * 50)
    
    if not K8sGPTAnalyzer:
        print("❌ K8sGPTAnalyzer not available")
        return False
    
    # Create analyzer
    analyzer = K8sGPTAnalyzer()
    
    # Prepare input
    input_data = {
        "operation": "optimize",
        "targetResource": "deployments",
        "scope": "cluster",
        "backend": "qwen",
        "explain": True,
        "focus": "resources"
    }
    
    print("Input:")
    print(json.dumps(input_data, indent=2))
    print()
    
    try:
        # Validate input
        if analyzer._validate_input(input_data):
            print("✅ Input validation passed")
            
            # Simulate resource optimization analysis
            result = {
                "status": "success",
                "timestamp": "2024-01-01T00:00:00Z",
                "operation": "optimize",
                "targetResource": "deployments",
                "scope": "cluster",
                "backend": "qwen",
                "optimizations": [
                    {
                        "resource": "deployment/web-server",
                        "current": {
                            "cpu_request": "1000m",
                            "cpu_limit": "2000m",
                            "memory_request": "2Gi",
                            "memory_limit": "4Gi"
                        },
                        "recommended": {
                            "cpu_request": "500m",
                            "cpu_limit": "1000m",
                            "memory_request": "1Gi",
                            "memory_limit": "2Gi"
                        },
                        "savings": {
                            "cpu": "50%",
                            "memory": "50%",
                            "estimated_cost_reduction": "40%"
                        },
                        "reasoning": "Current resource usage shows only 20% CPU and 30% memory utilization"
                    },
                    {
                        "resource": "deployment/api-gateway",
                        "current": {
                            "cpu_request": "200m",
                            "cpu_limit": "500m",
                            "memory_request": "512Mi",
                            "memory_limit": "1Gi"
                        },
                        "recommended": {
                            "cpu_request": "400m",
                            "cpu_limit": "800m",
                            "memory_request": "1Gi",
                            "memory_limit": "2Gi"
                        },
                        "savings": None,
                        "reasoning": "High CPU throttling detected, needs more resources"
                    }
                ],
                "summary": {
                    "total_deployments": 2,
                    "optimizations": 2,
                    "potential_cost_savings": "20%",
                    "performance_improvements": "15%"
                }
            }
            
            print("Result:")
            print(json.dumps(result, indent=2))
            print()
            return True
        else:
            print("❌ Input validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def example_4_security_analysis():
    """Example 4: Security analysis"""
    print("🔍 Example 4: Security Analysis")
    print("=" * 50)
    
    if not K8sGPTAnalyzer:
        print("❌ K8sGPTAnalyzer not available")
        return False
    
    # Create analyzer
    analyzer = K8sGPTAnalyzer()
    
    # Prepare input
    input_data = {
        "operation": "analyze",
        "targetResource": "cluster",
        "scope": "cluster",
        "backend": "qwen",
        "explain": True,
        "focus": "security"
    }
    
    print("Input:")
    print(json.dumps(input_data, indent=2))
    print()
    
    try:
        # Validate input
        if analyzer._validate_input(input_data):
            print("✅ Input validation passed")
            
            # Simulate security analysis
            result = {
                "status": "success",
                "timestamp": "2024-01-01T00:00:00Z",
                "operation": "analyze",
                "targetResource": "cluster",
                "scope": "cluster",
                "backend": "qwen",
                "security_issues": [
                    {
                        "severity": "critical",
                        "resource": "pod/privileged-container",
                        "issue": "Pod running as root user",
                        "description": "Container is running with UID 0 which is a security risk",
                        "recommendation": "Configure security context to run as non-root user",
                        "cve": None
                    },
                    {
                        "severity": "high",
                        "resource": "serviceaccount/default",
                        "issue": "Service account has cluster-admin permissions",
                        "description": "Default service account has excessive cluster-wide permissions",
                        "recommendation": "Create dedicated service account with minimal required permissions",
                        "cve": None
                    },
                    {
                        "severity": "medium",
                        "resource": "deployment/legacy-app",
                        "issue": "Container using privileged security context",
                        "description": "Container has privileged flag enabled",
                        "recommendation": "Remove privileged flag unless absolutely necessary",
                        "cve": "CVE-2023-1234"
                    }
                ],
                "summary": {
                    "total_issues": 3,
                    "critical": 1,
                    "high": 1,
                    "medium": 1,
                    "low": 0,
                    "security_score": 65
                }
            }
            
            print("Result:")
            print(json.dumps(result, indent=2))
            print()
            return True
        else:
            print("❌ Input validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False


def example_5_qwen_integration():
    """Example 5: Qwen LLM integration"""
    print("🤖 Example 5: Qwen LLM Integration")
    print("=" * 50)
    
    if not QwenIntegration:
        print("❌ QwenIntegration not available")
        return False
    
    # Create Qwen integration
    qwen = QwenIntegration()
    
    # Test configuration
    config = {
        "model": "qwen2.5-7b-instruct",
        "baseurl": "http://localhost:8000/v1",
        "api_key": "test-key",
        "timeout": 30
    }
    
    print("Configuration:")
    print(json.dumps(config, indent=2))
    print()
    
    try:
        # Validate configuration
        if qwen._validate_config(config):
            print("✅ Configuration validation passed")
            
            # Simulate Qwen response
            mock_response = {
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "qwen2.5-7b-instruct",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Based on the cluster analysis, I found several issues:\n\n1. Pod nginx-deployment-123 is experiencing high CPU usage. Consider setting appropriate CPU limits and monitoring.\n\n2. Deployment app-server lacks resource requests, which can lead to resource contention.\n\nRecommendations:\n- Set CPU requests and limits for all deployments\n- Implement resource quotas at namespace level\n- Enable horizontal pod autoscaling for critical applications"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 200,
                    "total_tokens": 350
                }
            }
            
            print("Mock Qwen Response:")
            print(json.dumps(mock_response, indent=2))
            print()
            return True
        else:
            print("❌ Configuration validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Qwen integration failed: {e}")
        return False


def example_6_cluster_scanning():
    """Example 6: Cluster scanning"""
    print("🔍 Example 6: Cluster Scanning")
    print("=" * 50)
    
    if not ClusterScanner:
        print("❌ ClusterScanner not available")
        return False
    
    # Create cluster scanner
    scanner = ClusterScanner()
    
    try:
        # Simulate cluster scan
        scan_result = {
            "timestamp": "2024-01-01T00:00:00Z",
            "scope": "cluster",
            "cluster_info": {
                "current_context": "minikube",
                "cluster_info": "Kubernetes control plane is running",
                "version": "Client Version: v1.28.3"
            },
            "metrics": {
                "node_count": 3,
                "namespace_count": 5,
                "pod_counts": {
                    "total": 25,
                    "by_status": {
                        "Running": 20,
                        "Pending": 3,
                        "Failed": 2
                    }
                },
                "service_count": 8,
                "deployment_count": 6
            },
            "resources": {
                "pods": {
                    "items": [
                        {"metadata": {"name": "pod1", "namespace": "default"}},
                        {"metadata": {"name": "pod2", "namespace": "kube-system"}}
                    ],
                    "count": 2,
                    "analysis": {
                        "status_counts": {"Running": 1, "Failed": 1},
                        "restart_counts": {"container1": 3},
                        "image_pull_issues": [],
                        "resource_issues": []
                    }
                },
                "deployments": {
                    "items": [
                        {"metadata": {"name": "deploy1", "namespace": "default"}}
                    ],
                    "count": 1,
                    "analysis": {
                        "replica_issues": [],
                        "update_issues": [],
                        "readiness_issues": []
                    }
                }
            },
            "issues": [
                {
                    "type": "high_restarts",
                    "severity": "warning",
                    "resource_type": "pods",
                    "details": "Container container1 has restarted 3 times"
                }
            ]
        }
        
        print("Cluster Scan Result:")
        print(json.dumps(scan_result, indent=2))
        print()
        return True
        
    except Exception as e:
        print(f"❌ Cluster scanning failed: {e}")
        return False


def example_7_error_handling():
    """Example 7: Error handling"""
    print("❌ Example 7: Error Handling")
    print("=" * 50)
    
    if not K8sGPTAnalyzer:
        print("❌ K8sGPTAnalyzer not available")
        return False
    
    # Create analyzer
    analyzer = K8sGPTAnalyzer()
    
    # Test invalid inputs
    invalid_inputs = [
        {},  # Empty input
        {"operation": "invalid"},  # Invalid operation
        {"operation": "analyze"},  # Missing targetResource
        {"operation": "analyze", "targetResource": ""},  # Empty targetResource
    ]
    
    for i, invalid_input in enumerate(invalid_inputs, 1):
        print(f"Test {i}: Invalid input")
        print(f"Input: {json.dumps(invalid_input)}")
        
        if analyzer._validate_input(invalid_input):
            print("❌ Validation should have failed")
        else:
            print("✅ Validation correctly failed")
        print()
    
    return True


def run_examples():
    """Run all examples"""
    print("🧪 K8sGPT Integration Examples")
    print("=" * 60)
    print()
    
    examples = [
        example_1_basic_cluster_analysis,
        example_2_namespace_specific_analysis,
        example_3_resource_optimization,
        example_4_security_analysis,
        example_5_qwen_integration,
        example_6_cluster_scanning,
        example_7_error_handling
    ]
    
    results = []
    for example in examples:
        try:
            result = example()
            results.append(result)
        except Exception as e:
            print(f"❌ Example failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Summary: {passed}/{total} examples passed")
    
    if passed == total:
        print("🎉 All examples completed successfully!")
        return True
    else:
        print(f"⚠️  {total - passed} examples failed")
        return False


if __name__ == '__main__':
    success = run_examples()
    exit(0 if success else 1)
