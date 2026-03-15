#!/usr/bin/env python3
"""
Simplified test suite for Multi-Cloud Resource Optimizer

Tests cover the actual API methods available in the resource optimizer.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os
import logging

# Add the current directory to the path to import the optimizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_cloud_orchestrator import (
    MultiCloudResourceOptimizerOrchestrator, OrchestrationTask, OrchestrationResult,
    OrchestrationStrategy
)
from resource_optimizer_handler import (
    ResourceOptimizerHandler, ResourceUtilization, OptimizationRecommendation
)

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)


class TestResourceOptimizerSimple(unittest.TestCase):
    """Test resource optimizer functionality with simplified API"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.orchestrator = MultiCloudResourceOptimizerOrchestrator(max_workers=2)
    
    def test_orchestrator_creation(self):
        """Test basic orchestrator creation"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.max_workers, 4)
        self.assertEqual(len(orchestrator.handlers), 0)
        self.assertEqual(len(orchestrator.tasks), 0)
        self.assertEqual(len(orchestrator.results), 0)
    
    def test_orchestrator_creation_with_custom_workers(self):
        """Test orchestrator creation with custom max_workers"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator(max_workers=8)
        self.assertEqual(orchestrator.max_workers, 8)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_initialize_handlers_success(self, mock_get_handler):
        """Test successful handler initialization"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'azure': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.initialize_client.return_value = True
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        providers = ['aws', 'azure', 'gcp']
        regions = {'aws': 'us-west-2', 'azure': 'eastus', 'gcp': 'us-central1'}
        
        result = self.orchestrator.initialize_handlers(providers, regions)
        
        self.assertTrue(result)
        self.assertEqual(len(self.orchestrator.handlers), 3)
        self.assertIn('aws', self.orchestrator.handlers)
        self.assertIn('azure', self.orchestrator.handlers)
        self.assertIn('gcp', self.orchestrator.handlers)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_initialize_handlers_partial_failure(self, mock_get_handler):
        """Test handler initialization with partial failures"""
        # Mock handlers with one failure
        mock_handlers = {
            'aws': Mock(),
            'azure': Mock(),
            'gcp': Mock()
        }
        
        mock_handlers['aws'].initialize_client.return_value = True
        mock_handlers['azure'].initialize_client.return_value = False
        mock_handlers['gcp'].initialize_client.return_value = True
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        providers = ['aws', 'azure', 'gcp']
        regions = {'aws': 'us-west-2', 'azure': 'eastus', 'gcp': 'us-central1'}
        
        result = self.orchestrator.initialize_handlers(providers, regions)
        
        self.assertFalse(result)  # Should return False due to azure failure
        self.assertEqual(len(self.orchestrator.handlers), 2)  # Only successful handlers
        self.assertIn('aws', self.orchestrator.handlers)
        self.assertNotIn('azure', self.orchestrator.handlers)
        self.assertIn('gcp', self.orchestrator.handlers)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_orchestrate_resource_analysis(self, mock_get_handler):
        """Test resource analysis orchestration"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.initialize_client.return_value = True
            # Mock utilization data
            handler.get_compute_utilization.return_value = [
                ResourceUtilization(
                    resource_id='i-12345',
                    resource_name='web-server',
                    resource_type='ec2_instance',
                    provider='aws',
                    region='us-west-2',
                    environment='production',
                    current_capacity=4.0,
                    current_utilization=45.2,
                    peak_utilization=78.5,
                    average_utilization=52.3,
                    utilization_trend='stable',
                    cost_per_hour=0.192,
                    monthly_cost=140.16,
                    tags={'Environment': 'production'}
                )
            ]
            handler.get_storage_utilization.return_value = []
            handler.get_network_utilization.return_value = []
            handler.get_database_utilization.return_value = []
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        # Initialize handlers
        providers = ['aws', 'gcp']
        regions = {'aws': 'us-west-2', 'gcp': 'us-central1'}
        self.orchestrator.initialize_handlers(providers, regions)
        
        # Run analysis
        summary = self.orchestrator.orchestrate_resource_analysis(
            providers=providers,
            resource_types=['compute']
        )
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_tasks, 2)  # One task per provider
        self.assertGreaterEqual(summary.completed_tasks, 0)
        self.assertGreaterEqual(summary.successful_tasks, 0)
        self.assertIn('compute', summary.resource_types)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_orchestrate_optimization_recommendations(self, mock_get_handler):
        """Test optimization recommendations orchestration"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.initialize_client.return_value = True
            # Mock utilization data for optimization
            handler.get_compute_utilization.return_value = [
                ResourceUtilization(
                    resource_id='i-12345',
                    resource_name='web-server',
                    resource_type='ec2_instance',
                    provider='aws',
                    region='us-west-2',
                    environment='production',
                    current_capacity=4.0,
                    current_utilization=25.0,  # Low utilization
                    peak_utilization=45.0,
                    average_utilization=30.0,
                    utilization_trend='decreasing',
                    cost_per_hour=0.192,
                    monthly_cost=140.16,
                    tags={'Environment': 'production'}
                )
            ]
            handler.get_storage_utilization.return_value = []
            handler.get_network_utilization.return_value = []
            handler.get_database_utilization.return_value = []
            # Mock optimization recommendations
            handler.generate_optimization_recommendations.return_value = [
                OptimizationRecommendation(
                    resource_id='i-12345',
                    resource_name='web-server',
                    resource_type='ec2_instance',
                    provider='aws',
                    current_state={'instance_type': 'm5.large'},
                    recommended_action='rightsize_instance',
                    recommended_capacity=2.0,
                    estimated_savings=75.25,
                    implementation_effort='low',
                    risk_level='low',
                    confidence=0.85,
                    rationale='Low utilization suggests right-sizing opportunity',
                    implementation_steps=['Stop instance', 'Change instance type', 'Start instance']
                )
            ]
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        # Initialize handlers
        providers = ['aws', 'gcp']
        regions = {'aws': 'us-west-2', 'gcp': 'us-central1'}
        self.orchestrator.initialize_handlers(providers, regions)
        
        # Run optimization analysis first
        analysis_summary = self.orchestrator.orchestrate_resource_analysis(
            providers=providers,
            resource_types=['compute']
        )
        
        # Then run optimization recommendations
        summary = self.orchestrator.orchestrate_optimization_recommendations(
            providers=providers,
            resource_types=['compute']
        )
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_tasks, 2)  # One task per provider
        self.assertGreaterEqual(summary.completed_tasks, 0)
        self.assertGreaterEqual(summary.successful_tasks, 0)
        self.assertGreaterEqual(summary.estimated_savings, 0.0)
    
    def test_generate_analysis_tasks(self):
        """Test analysis task generation"""
        providers = ['aws', 'azure', 'gcp']
        resource_types = ['compute', 'storage']
        
        tasks = self.orchestrator._generate_analysis_tasks(providers, resource_types)
        
        # Should generate one task per provider per resource type
        expected_tasks = len(providers) * len(resource_types)
        self.assertEqual(len(tasks), expected_tasks)
        
        # Check task structure
        for task in tasks:
            self.assertIn(task.provider, providers)
            self.assertEqual(task.action, 'analyze')
            self.assertIn(task.parameters['resource_type'], resource_types)
            self.assertEqual(task.status, 'pending')
    
    def test_generate_optimization_tasks(self):
        """Test optimization task generation"""
        # Create mock utilization data
        resources = [
            ResourceUtilization(
                resource_id='i-12345',
                resource_name='web-server',
                resource_type='ec2_instance',
                provider='aws',
                region='us-west-2',
                environment='production',
                current_capacity=4.0,
                current_utilization=25.0,
                peak_utilization=45.0,
                average_utilization=30.0,
                utilization_trend='decreasing',
                cost_per_hour=0.192,
                monthly_cost=140.16,
                tags={'Environment': 'production'}
            ),
            ResourceUtilization(
                resource_id='vol-67890',
                resource_name='data-volume',
                resource_type='ebs_volume',
                provider='aws',
                region='us-west-2',
                environment='production',
                current_capacity=100.0,
                current_utilization=60.0,
                peak_utilization=80.0,
                average_utilization=65.0,
                utilization_trend='stable',
                cost_per_hour=0.01,
                monthly_cost=7.30,
                tags={'Environment': 'production'}
            )
        ]
        
        tasks = self.orchestrator._generate_optimization_tasks(resources)
        
        # Should generate one task per resource
        self.assertEqual(len(tasks), len(resources))
        
        # Check task structure
        for i, task in enumerate(tasks):
            self.assertEqual(task.action, 'optimize')
            self.assertEqual(task.resource_id, resources[i].resource_id)
            self.assertEqual(task.provider, resources[i].provider)
            self.assertEqual(task.status, 'pending')
    
    def test_execute_single_task_no_handler(self):
        """Test single task execution when handler is not available"""
        task = OrchestrationTask(
            task_id='test-task',
            provider='aws',
            action='analyze',
            parameters={'resource_type': 'compute'},
            priority='medium',
            status='pending',
            created_at=datetime.now()
        )
        
        result = self.orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'failed')
        self.assertIn('Handler not available', result.message)
    
    def test_execute_single_task_unknown_action(self):
        """Test single task execution with unknown action"""
        # Mock handler
        mock_handler = Mock()
        self.orchestrator.handlers = {'aws': mock_handler}
        
        task = OrchestrationTask(
            task_id='test-task',
            provider='aws',
            action='unknown_action',
            parameters={'resource_type': 'compute'},
            priority='medium',
            status='pending',
            created_at=datetime.now()
        )
        
        result = self.orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'failed')
        self.assertIn('Unknown operation', result.message)
    
    def test_execute_single_task_handler_exception(self):
        """Test single task execution when handler raises exception"""
        # Mock handler that raises exception
        mock_handler = Mock()
        mock_handler.analyze_agent.side_effect = Exception("Analysis failed")
        self.orchestrator.handlers = {'aws': mock_handler}
        
        task = OrchestrationTask(
            task_id='test-task',
            provider='aws',
            action='analyze',
            parameters={'resource_type': 'compute'},
            priority='medium',
            status='pending',
            created_at=datetime.now()
        )
        
        result = self.orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'failed')
        self.assertIn('Analysis failed', result.message)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_execute_tasks_sequential(self, mock_get_handler):
        """Test sequential task execution"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.analyze_agent.return_value = {
                'status': 'success',
                'message': 'Analysis completed successfully',
                'utilization_data': {'current_utilization': 45.2},
                'timestamp': datetime.now().isoformat()
            }
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        self.orchestrator.handlers = mock_handlers
        
        tasks = [
            OrchestrationTask('task-0', 'aws', 'analyze', {'resource_type': 'compute'}, 'medium', 'pending', datetime.now()),
            OrchestrationTask('task-1', 'gcp', 'analyze', {'resource_type': 'compute'}, 'medium', 'pending', datetime.now())
        ]
        
        results = self.orchestrator._execute_tasks_sequential(tasks)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, 'success')
        self.assertEqual(results[1].status, 'success')
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_execute_tasks_parallel(self, mock_get_handler):
        """Test parallel task execution"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.analyze_agent.return_value = {
                'status': 'success',
                'message': 'Analysis completed successfully',
                'utilization_data': {'current_utilization': 45.2},
                'timestamp': datetime.now().isoformat()
            }
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        self.orchestrator.handlers = mock_handlers
        
        tasks = [
            OrchestrationTask('task-0', 'aws', 'analyze', {'resource_type': 'compute'}, 'medium', 'pending', datetime.now()),
            OrchestrationTask('task-1', 'gcp', 'analyze', {'resource_type': 'compute'}, 'medium', 'pending', datetime.now())
        ]
        
        results = self.orchestrator._execute_tasks_parallel(tasks)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, 'success')
        self.assertEqual(results[1].status, 'success')
    
    def test_get_orchestration_status(self):
        """Test getting orchestration status"""
        # Create a mock summary
        from multi_cloud_orchestrator import ResourceOptimizationSummary
        summary = ResourceOptimizationSummary(
            orchestration_id='test-orchestration',
            total_tasks=5,
            completed_tasks=3,
            successful_tasks=2,
            failed_tasks=1,
            total_resources=10,
            estimated_savings=125.50,
            success_rate=40.0,
            providers=['aws', 'gcp'],
            resource_types=['compute', 'storage'],
            start_time=datetime.now(),
            status='in_progress'
        )
        
        # Add to orchestrator
        self.orchestrator.orchestrations['test-orchestration'] = summary
        
        # Get status
        status = self.orchestrator.get_orchestration_status('test-orchestration')
        
        self.assertIsNotNone(status)
        self.assertEqual(status.orchestration_id, 'test-orchestration')
        self.assertEqual(status.total_tasks, 5)
        self.assertEqual(status.successful_tasks, 2)
        
        # Test non-existent orchestration
        nonexistent = self.orchestrator.get_orchestration_status('non-existent')
        self.assertIsNone(nonexistent)
    
    def test_get_all_orchestrations(self):
        """Test getting all orchestrations"""
        # Initially should be empty
        all_orchestrations = self.orchestrator.get_all_orchestrations()
        self.assertEqual(len(all_orchestrations), 0)
        
        # Add a mock orchestration
        from multi_cloud_orchestrator import ResourceOptimizationSummary
        summary = ResourceOptimizationSummary(
            orchestration_id='test-orchestration',
            total_tasks=5,
            completed_tasks=3,
            successful_tasks=2,
            failed_tasks=1,
            total_resources=10,
            estimated_savings=125.50,
            success_rate=40.0,
            providers=['aws'],
            resource_types=['compute'],
            start_time=datetime.now(),
            status='completed'
        )
        
        self.orchestrator.orchestrations['test-orchestration'] = summary
        
        # Get all orchestrations
        all_orchestrations = self.orchestrator.get_all_orchestrations()
        self.assertEqual(len(all_orchestrations), 1)
        self.assertIn('test-orchestration', all_orchestrations)


class TestDataStructures(unittest.TestCase):
    """Test dataclass structures"""
    
    def test_orchestration_task_creation(self):
        """Test OrchestrationTask dataclass creation"""
        task = OrchestrationTask(
            task_id='optimization-task',
            provider='aws',
            action='analyze',
            parameters={'resource_type': 'compute'},
            priority='high',
            status='pending',
            created_at=datetime.now()
        )
        
        self.assertEqual(task.task_id, 'optimization-task')
        self.assertEqual(task.provider, 'aws')
        self.assertEqual(task.action, 'analyze')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.status, 'pending')
    
    def test_orchestration_result_creation(self):
        """Test OrchestrationResult dataclass creation"""
        result = OrchestrationResult(
            task_id='optimization-task',
            provider='aws',
            action='analyze',
            status='success',
            success=True,
            result={'utilization': 45.2},
            execution_time=2.5,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        self.assertEqual(result.task_id, 'optimization-task')
        self.assertEqual(result.provider, 'aws')
        self.assertEqual(result.action, 'analyze')
        self.assertEqual(result.status, 'success')
        self.assertTrue(result.success)
        self.assertEqual(result.execution_time, 2.5)
    
    def test_resource_utilization_creation(self):
        """Test ResourceUtilization dataclass creation"""
        utilization = ResourceUtilization(
            resource_id='i-1234567890abcdef0',
            resource_name='web-server',
            resource_type='ec2_instance',
            provider='aws',
            region='us-west-2',
            environment='production',
            current_capacity=4.0,
            current_utilization=45.2,
            peak_utilization=78.5,
            average_utilization=52.3,
            utilization_trend='stable',
            cost_per_hour=0.192,
            monthly_cost=140.16,
            tags={'Environment': 'production', 'Team': 'backend'}
        )
        
        self.assertEqual(utilization.resource_id, 'i-1234567890abcdef0')
        self.assertEqual(utilization.resource_type, 'ec2_instance')
        self.assertEqual(utilization.provider, 'aws')
        self.assertEqual(utilization.current_utilization, 45.2)
        self.assertEqual(utilization.monthly_cost, 140.16)
    
    def test_optimization_recommendation_creation(self):
        """Test OptimizationRecommendation dataclass creation"""
        recommendation = OptimizationRecommendation(
            resource_id='i-1234567890abcdef0',
            resource_name='web-server',
            resource_type='ec2_instance',
            provider='aws',
            current_state={'instance_type': 'm5.large', 'utilization': 45.2},
            recommended_action='rightsize_instance',
            recommended_capacity=2.0,
            estimated_savings=75.25,
            implementation_effort='low',
            risk_level='low',
            confidence=0.85,
            rationale='Low utilization suggests right-sizing opportunity',
            implementation_steps=['Stop instance', 'Change instance type', 'Start instance']
        )
        
        self.assertEqual(recommendation.resource_id, 'i-1234567890abcdef0')
        self.assertEqual(recommendation.recommended_action, 'rightsize_instance')
        self.assertEqual(recommendation.estimated_savings, 75.25)
        self.assertEqual(recommendation.confidence, 0.85)
        self.assertEqual(len(recommendation.implementation_steps), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
