#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pytest>=7.0.0",
#   "pytest-asyncio>=0.21.0",
#   "kubernetes>=25.0.0",
#   "requests>=2.28.0",
#   "pydantic>=1.10.0"
# ]
# ///

"""
Test suite for AI System Debugger
Comprehensive tests for debugging functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from main import AISystemDebugger, DebugSession, DebugFinding, DebugResult
from debug_utils import SystemDebugger

class TestAISystemDebugger:
    """Test cases for AISystemDebugger"""
    
    @pytest.fixture
    def debugger(self):
        """Create debugger instance for testing"""
        return AISystemDebugger(namespace="test", verbose=True)
    
    @pytest.fixture
    def mock_kubectl_output(self):
        """Mock kubectl output"""
        return {
            "pods": json.dumps({
                "items": [
                    {
                        "metadata": {"name": "test-pod-1"},
                        "status": {"phase": "Running"},
                        "status": {
                            "containerStatuses": [{"restartCount": 0}]
                        }
                    },
                    {
                        "metadata": {"name": "test-pod-2"},
                        "status": {"phase": "Failed"},
                        "status": {
                            "containerStatuses": [{"restartCount": 5}]
                        }
                    }
                ]
            }),
            "nodes": "test-node-1   Ready    1d    v1.28.0\ntest-node-2   NotReady    1d    v1.28.0",
            "logs": "INFO: Starting agent\nERROR: Failed to process request\nWARNING: High memory usage\nINFO: Agent ready"
        }
    
    def test_debug_session_creation(self):
        """Test debug session creation"""
        session = DebugSession(
            session_id="test-123",
            start_time=datetime.now(),
            target_component="agents",
            issue_type="errors",
            time_range="1h",
            namespace="temporal",
            verbose=True,
            auto_fix=False
        )
        
        assert session.session_id == "test-123"
        assert session.target_component == "agents"
        assert session.issue_type == "errors"
        assert session.auto_fix is False
    
    def test_debug_finding_creation(self):
        """Test debug finding creation"""
        finding = DebugFinding(
            component="agents",
            severity="critical",
            issue="Test issue",
            root_cause="Test cause",
            evidence=["Evidence 1", "Evidence 2"],
            recommendations=["Fix 1", "Fix 2"]
        )
        
        assert finding.component == "agents"
        assert finding.severity == "critical"
        assert len(finding.evidence) == 2
        assert len(finding.recommendations) == 2
    
    @patch('subprocess.run')
    def test_run_kubectl_success(self, mock_run, debugger, mock_kubectl_output):
        """Test successful kubectl command execution"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_kubectl_output["pods"]
        
        result = debugger.run_kubectl("get pods -o json")
        
        assert result == mock_kubectl_output["pods"]
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_kubectl_failure(self, mock_run, debugger):
        """Test kubectl command failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error: pods not found"
        
        result = debugger.run_kubectl("get pods -o json")
        
        assert result == ""
    
    @patch('requests.get')
    def test_check_api_endpoint_success(self, mock_get, debugger):
        """Test successful API endpoint check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metrics": {"test": "value"}}
        mock_get.return_value = mock_response
        
        result = debugger.check_api_endpoint("/monitoring/metrics")
        
        assert result == {"metrics": {"test": "value"}}
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_check_api_endpoint_failure(self, mock_get, debugger):
        """Test API endpoint failure"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = debugger.check_api_endpoint("/monitoring/metrics")
        
        assert result is None
    
    @patch('subprocess.run')
    def test_debug_agents(self, mock_run, debugger, mock_kubectl_output):
        """Test agent debugging"""
        # Mock kubectl responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout=mock_kubectl_output["pods"]),  # get pods
            Mock(returncode=0, stdout=mock_kubectl_output["logs"]),   # get logs
        ]
        
        findings = debugger.debug_agents("errors", "1h")
        
        assert len(findings) > 0
        # Should find failed pod
        failed_pod_finding = next((f for f in findings if "Failed" in f.issue), None)
        assert failed_pod_finding is not None
        assert failed_pod_finding.severity == "critical"
    
    @patch('subprocess.run')
    def test_debug_workflows(self, mock_run, debugger):
        """Test workflow debugging"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"items": []}'  # No server pods
        
        findings = debugger.debug_workflows("errors", "1h")
        
        assert len(findings) > 0
        # Should find missing temporal server
        server_finding = next((f for f in findings if "server" in f.issue.lower()), None)
        assert server_finding is not None
    
    @patch('subprocess.run')
    def test_debug_infrastructure(self, mock_run, debugger):
        """Test infrastructure debugging"""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="test-node-1   Ready    1d    v1.28.0\ntest-node-2   NotReady    1d    v1.28.0"),  # nodes
            Mock(returncode=0, stdout="test-pod-1    100m    128Mi"),  # top pods
            Mock(returncode=0, stdout=""),  # get pv
        ]
        
        findings = debugger.debug_infrastructure("resource", "1h")
        
        assert len(findings) > 0
        # Should find NotReady node
        node_finding = next((f for f in findings if "NotReady" in f.issue), None)
        assert node_finding is not None
        assert node_finding.severity == "critical"
    
    def test_parse_time_range(self):
        """Test time range parsing"""
        from debug_utils import SystemDebugger
        
        debugger = SystemDebugger()
        
        # Test minutes
        delta = debugger._parse_time_range("30m")
        assert delta == timedelta(minutes=30)
        
        # Test hours
        delta = debugger._parse_time_range("2h")
        assert delta == timedelta(hours=2)
        
        # Test days
        delta = debugger._parse_time_range("1d")
        assert delta == timedelta(days=1)
        
        # Test invalid format
        with pytest.raises(ValueError):
            debugger._parse_time_range("invalid")
    
    def test_find_error_patterns(self):
        """Test error pattern detection"""
        from debug_utils import SystemDebugger
        
        debugger = SystemDebugger()
        logs = [
            "2024-01-01 10:00:00 INFO Starting service",
            "2024-01-01 10:01:00 ERROR Failed to process request",
            "2024-01-01 10:02:00 WARNING High memory usage",
            "2024-01-01 10:03:00 CRITICAL System failure"
        ]
        
        patterns = debugger._find_error_patterns(logs)
        
        assert len(patterns) == 2  # ERROR and CRITICAL
        assert patterns[0]["pattern"] == "ERROR"
        assert patterns[1]["pattern"] == "CRITICAL"
    
    def test_find_warning_patterns(self):
        """Test warning pattern detection"""
        from debug_utils import SystemDebugger
        
        debugger = SystemDebugger()
        logs = [
            "2024-01-01 10:00:00 INFO Starting service",
            "2024-01-01 10:01:00 WARNING High memory usage",
            "2024-01-01 10:02:00 WARN Deprecated API usage"
        ]
        
        patterns = debugger._find_warning_patterns(logs)
        
        assert len(patterns) == 2  # WARNING and WARN
        assert patterns[0]["pattern"] == "WARNING"
        assert patterns[1]["pattern"] == "WARN"
    
    def test_find_performance_patterns(self):
        """Test performance pattern detection"""
        from debug_utils import SystemDebugger
        
        debugger = SystemDebugger()
        logs = [
            "2024-01-01 10:00:00 INFO Starting service",
            "2024-01-01 10:01:00 ERROR Request timeout after 30s",
            "2024-01-01 10:02:00 WARNING High latency detected",
            "2024-01-01 10:03:00 INFO OOM killer activated"
        ]
        
        patterns = debugger._find_performance_patterns(logs)
        
        assert len(patterns) == 3  # timeout, latency, oom
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        from debug_utils import SystemDebugger
        
        debugger = SystemDebugger()
        
        report = {
            "system_metrics": {
                "kubernetes": {
                    "pods": {
                        "failed": 2,
                        "pending": 1
                    }
                }
            },
            "log_analysis": {
                "summary": {
                    "error_count": 15
                }
            },
            "target_component": "agents"
        }
        
        recommendations = debugger._generate_recommendations(report)
        
        assert len(recommendations) > 0
        assert any("failed pods" in rec.lower() for rec in recommendations)
        assert any("high error rate" in rec.lower() for rec in recommendations)
        assert any("agent" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self):
        """Test system metrics collection"""
        debugger = SystemDebugger()
        
        # Mock the individual collection methods
        debugger._collect_k8s_metrics = AsyncMock(return_value={"pods": {"total": 5}})
        debugger._collect_temporal_metrics = AsyncMock(return_value={"workflows": {"total": 10}})
        debugger._collect_monitoring_metrics = AsyncMock(return_value={"health": "ok"})
        
        metrics = await debugger.collect_system_metrics("1h")
        
        assert "timestamp" in metrics
        assert "time_range" in metrics
        assert "kubernetes" in metrics
        assert "temporal" in metrics
        assert "monitoring" in metrics
        assert metrics["kubernetes"]["pods"]["total"] == 5
        assert metrics["temporal"]["workflows"]["total"] == 10
    
    @pytest.mark.asyncio
    async def test_analyze_logs(self):
        """Test log analysis"""
        debugger = SystemDebugger()
        
        # Mock log collection
        debugger._get_agent_logs = AsyncMock(return_value=[
            "2024-01-01 10:00:00 INFO Starting service",
            "2024-01-01 10:01:00 ERROR Failed to process request",
            "2024-01-01 10:02:00 WARNING High memory usage"
        ])
        
        analysis = await debugger.analyze_logs("agents", "1h")
        
        assert "component" in analysis
        assert "time_range" in analysis
        assert "error_patterns" in analysis
        assert "warning_patterns" in analysis
        assert "summary" in analysis
        assert analysis["summary"]["error_count"] == 1
        assert analysis["summary"]["warning_count"] == 1
    
    @pytest.mark.asyncio
    async def test_generate_debug_report(self):
        """Test comprehensive debug report generation"""
        debugger = SystemDebugger()
        
        # Mock all the collection methods
        debugger.collect_system_metrics = AsyncMock(return_value={"kubernetes": {"pods": {"total": 5}}})
        debugger.analyze_logs = AsyncMock(return_value={"summary": {"error_count": 0}})
        debugger._generate_recommendations = Mock(return_value=["Recommendation 1"])
        
        report = await debugger.generate_debug_report("agents", "errors", "1h")
        
        assert "timestamp" in report
        assert "target_component" in report
        assert "issue_type" in report
        assert "system_metrics" in report
        assert "log_analysis" in report
        assert "recommendations" in report
        assert report["target_component"] == "agents"
        assert report["issue_type"] == "errors"
        assert len(report["recommendations"]) == 1

class TestIntegration:
    """Integration tests for the debugger"""
    
    @pytest.mark.asyncio
    async def test_quick_debug_function(self):
        """Test the quick debug utility function"""
        from debug_utils import quick_debug
        
        # Mock SystemDebugger
        with patch('debug_utils.SystemDebugger') as mock_debugger:
            mock_instance = Mock()
            mock_instance.generate_debug_report = AsyncMock(return_value={"test": "report"})
            mock_debugger.return_value = mock_instance
            
            result = await quick_debug("agents", "test-namespace", "30m")
            
            assert result == {"test": "report"}
            mock_debugger.assert_called_once_with(namespace="test-namespace")
            mock_instance.generate_debug_report.assert_called_once_with(
                target_component="agents",
                issue_type="general",
                time_range="30m"
            )
    
    def test_save_debug_report(self):
        """Test saving debug report to file"""
        from debug_utils import save_debug_report
        import tempfile
        import os
        
        report = {
            "timestamp": "2024-01-01T10:00:00",
            "target_component": "agents",
            "findings": ["test finding"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            save_debug_report(report, temp_path)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == report
            assert saved_data["target_component"] == "agents"
            assert len(saved_data["findings"]) == 1
            
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
