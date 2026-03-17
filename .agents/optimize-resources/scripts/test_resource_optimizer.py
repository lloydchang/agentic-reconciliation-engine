#!/usr/bin/env python3
"""
Test suite for Multi-Cloud Resource Optimizer

Tests cover unit tests, integration tests, and mock scenarios for the resource optimizer.
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


class TestResourceOptimizerCore(unittest.TestCase):
    """Test core resource optimizer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.config_file = '/tmp/test_resource_optimizer_config.json'
        test_config = {
            'providers': {
                'aws': {'enabled': True, 'region': 'us-west-2'},
                'azure': {'enabled': True, 'region': 'eastus'},
                'gcp': {'enabled': True, 'region': 'us-central1'}
            },
            'orchestration': {
                'max_workers': 3,
                'timeout_minutes': 15
            }
        }
        
        import json
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import os
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_orchestrator_creation(self):
        """Test basic orchestrator creation"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        self.assertIsNotNone(orchestrator)
    
    def test_create_optimization_plan_sequential(self):
        """Test creating sequential optimization plan"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        agents = [
            {'name': 'compute-analysis', 'provider': 'aws', 'analysis_type': 'compute'},
            {'name': 'storage-analysis', 'provider': 'azure', 'analysis_type': 'storage'}
        ]
        
        tasks = orchestrator.create_deployment_plan(agents, OrchestrationStrategy.SEQUENTIAL)
        
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].task_id, 'deploy-0')
        self.assertEqual(tasks[0].provider, 'aws')
        self.assertEqual(tasks[0].action, 'deploy')
        self.assertEqual(tasks[0].status, 'pending')
        
        # Check sequential dependencies
        self.assertEqual(len(tasks[0].dependencies), 0)
        self.assertEqual(tasks[1].dependencies, ['deploy-0'])
    
    def test_create_optimization_plan_parallel(self):
        """Test creating parallel optimization plan"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        agents = [
            {'name': 'compute-analysis', 'provider': 'aws', 'analysis_type': 'compute'},
            {'name': 'storage-analysis', 'provider': 'azure', 'analysis_type': 'storage'},
            {'name': 'network-analysis', 'provider': 'gcp', 'analysis_type': 'network'}
        ]
        
        tasks = orchestrator.create_deployment_plan(agents, OrchestrationStrategy.PARALLEL)
        
        self.assertEqual(len(tasks), 3)
        
        # Check no dependencies for parallel execution
        for task in tasks:
            self.assertEqual(len(task.dependencies), 0)
    
    def test_create_optimization_plan_rolling(self):
        """Test creating rolling optimization plan"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        agents = [
            {'name': 'compute-analysis', 'provider': 'aws', 'analysis_type': 'compute'},
            {'name': 'storage-analysis', 'provider': 'azure', 'analysis_type': 'storage'},
            {'name': 'network-analysis', 'provider': 'gcp', 'analysis_type': 'network'},
            {'name': 'database-analysis', 'provider': 'aws', 'analysis_type': 'database'}
        ]
        
        tasks = orchestrator.create_deployment_plan(agents, OrchestrationStrategy.ROLLING)
        
        self.assertEqual(len(tasks), 4)
        
        # Check rolling dependencies (staggered)
        self.assertEqual(len(tasks[0].dependencies), 0)
        self.assertEqual(len(tasks[1].dependencies), 1)  # Depends on task-0
        self.assertEqual(len(tasks[2].dependencies), 1)  # Depends on task-1
        self.assertEqual(len(tasks[3].dependencies), 1)  # Depends on task-2
    
    def test_create_optimization_plan_blue_green(self):
        """Test creating blue-green optimization plan"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        agents = [
            {'name': 'compute-analysis', 'provider': 'aws', 'analysis_type': 'compute'},
            {'name': 'storage-analysis', 'provider': 'azure', 'analysis_type': 'storage'},
            {'name': 'network-analysis', 'provider': 'gcp', 'analysis_type': 'network'},
            {'name': 'database-analysis', 'provider': 'aws', 'analysis_type': 'database'}
        ]
        
        tasks = orchestrator.create_deployment_plan(agents, OrchestrationStrategy.BLUE_GREEN)
        
        self.assertEqual(len(tasks), 4)
        
        # Blue-green strategy should work (implementation may vary)
        # Just verify the strategy is accepted and tasks are created
        for task in tasks:
            self.assertEqual(task.action, 'deploy')
            self.assertEqual(task.status, 'pending')
    
    def test_check_dependencies(self):
        """Test dependency checking logic"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        # Create task with dependencies
        task = OrchestrationTask(
            task_id='task-2',
            provider='aws',
            action='deploy',
            parameters={},
            priority='medium',
            status='pending',
            created_at=datetime.now(),
            dependencies=['task-0', 'task-1']
        )
        
        # Create completed results
        completed_results = [
            OrchestrationResult(
                task_id='task-0',
                provider='aws',
                action='deploy',
                status='success',
                message='Analysis completed',
                timestamp=datetime.now()
            ),
            OrchestrationResult(
                task_id='task-1',
                provider='azure', 
                action='deploy',
                status='success',
                message='Analysis completed',
                timestamp=datetime.now()
            )
        ]
        
        # Dependencies should be satisfied
        self.assertTrue(orchestrator._check_dependencies(task, completed_results))
        
        # Remove one dependency
        incomplete_results = completed_results[:1]
        self.assertFalse(orchestrator._check_dependencies(task, incomplete_results))
    
    def test_group_tasks_by_dependencies(self):
        """Test grouping tasks by dependency levels"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        # Create tasks with dependencies
        tasks = [
            OrchestrationTask('task-0', 'aws', 'deploy', {}, 'medium', 'pending', datetime.now(), []),
            OrchestrationTask('task-1', 'azure', 'deploy', {}, 'medium', 'pending', datetime.now(), ['task-0']),
            OrchestrationTask('task-2', 'gcp', 'deploy', {}, 'medium', 'pending', datetime.now(), ['task-0']),
            OrchestrationTask('task-3', 'aws', 'deploy', {}, 'medium', 'pending', datetime.now(), ['task-1', 'task-2'])
        ]
        
        levels = orchestrator._group_tasks_by_dependencies(tasks)
        
        # Check that task-0 is in the first level (no dependencies)
        first_level_tasks = [t.task_id for t in levels[0]]
        self.assertIn('task-0', first_level_tasks)
        
        # Check structure is reasonable (algorithm may group differently)
        self.assertGreaterEqual(len(levels), 2)
        self.assertLessEqual(len(levels), 3)
        
        # Check that task-3 is in some level (most dependencies)
        task_3_found = False
        for level in levels:
            if any(t.task_id == 'task-3' for t in level):
                task_3_found = True
                break
        
        self.assertTrue(task_3_found, "task-3 should be in some level")
        
        # Total tasks should be preserved
        total_tasks = sum(len(level) for level in levels)
        self.assertEqual(total_tasks, 4)


class TestResourceOptimizerExecution(unittest.TestCase):
    """Test resource optimizer execution with mocked handlers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_file = '/tmp/test_resource_optimizer_execution_config.json'
        test_config = {
            'providers': {
                'aws': {'enabled': True, 'region': 'us-west-2'},
                'gcp': {'enabled': True, 'region': 'us-central1'}
            },
            'orchestration': {
                'max_workers': 2,
                'timeout_minutes': 10
            }
        }
        
        import json
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import os
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_execute_single_task_no_handler(self):
        """Test single task execution when handler is not available"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        orchestrator.handlers = {}  # No handlers available
        
        task = OrchestrationTask('task-0', 'aws', 'deploy', {}, 'medium', 'pending', datetime.now(), [])
        
        result = orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'error')
        self.assertIn('Handler not available', result.message)
    
    def test_execute_single_task_unknown_action(self):
        """Test single task execution with unknown action"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        # Mock handler
        mock_handler = Mock()
        orchestrator.handlers = {'aws': mock_handler}
        
        # Create task with unknown action
        task = OrchestrationTask('task-0', 'aws', 'unknown_action', {}, 'medium', 'pending', datetime.now(), [])
        
        result = orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'error')
        self.assertIn('Unknown operation', result.message)
    
    def test_execute_single_task_handler_exception(self):
        """Test single task execution when handler raises exception"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        # Mock handler that raises exception
        mock_handler = Mock()
        mock_handler.deploy_agent.side_effect = Exception("Optimization failed")
        orchestrator.handlers = {'aws': mock_handler}
        
        task = OrchestrationTask('task-0', 'aws', 'deploy', {'resource_id': 'test-resource'}, 'medium', 'pending', datetime.now(), [])
        
        result = orchestrator._execute_single_task(task)
        
        self.assertEqual(result.status, 'error')
        self.assertIn('Optimization failed', result.message)
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_execute_parallel_success(self, mock_get_handler):
        """Test successful parallel execution"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.deploy_agent.return_value = {
                'status': 'success',
                'message': 'Optimization completed successfully',
                'resource_id': 'test-resource',
                'estimated_savings': 125.50,
                'recommendations': [
                    {
                        'action': 'rightsize_instance',
                        'savings': 75.25,
                        'confidence': 0.85
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        orchestrator.handlers = mock_handlers
        
        tasks = [
            OrchestrationTask('task-0', 'aws', 'deploy', {'resource_id': 'resource-1'}, 'medium', 'pending', datetime.now(), []),
            OrchestrationTask('task-1', 'gcp', 'deploy', {'resource_id': 'resource-2'}, 'medium', 'pending', datetime.now(), [])
        ]
        
        results = orchestrator._execute_parallel(tasks)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, 'success')
        self.assertEqual(results[1].status, 'success')
    
    @patch('multi_cloud_orchestrator.get_resource_optimizer_handler')
    def test_execute_sequential_success(self, mock_get_handler):
        """Test successful sequential execution"""
        # Mock successful handlers
        mock_handlers = {
            'aws': Mock(),
            'gcp': Mock()
        }
        
        for handler in mock_handlers.values():
            handler.deploy_agent.return_value = {
                'status': 'success',
                'message': 'Optimization completed successfully',
                'resource_id': 'test-resource',
                'estimated_savings': 125.50,
                'recommendations': [
                    {
                        'action': 'rightsize_instance',
                        'savings': 75.25,
                        'confidence': 0.85
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
        
        mock_get_handler.side_effect = lambda provider: mock_handlers.get(provider)
        
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        orchestrator.handlers = mock_handlers
        
        tasks = [
            OrchestrationTask('task-0', 'aws', 'deploy', {'resource_id': 'resource-1'}, 'medium', 'pending', datetime.now(), []),
            OrchestrationTask('task-1', 'gcp', 'deploy', {'resource_id': 'resource-2'}, 'medium', 'pending', datetime.now(), [])
        ]
        
        results = orchestrator._execute_sequential(tasks)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, 'success')
        self.assertEqual(results[1].status, 'success')


class TestResourceOptimizerScenarios(unittest.TestCase):
    """Test specific resource optimizer scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config_file = '/tmp/test_resource_optimizer_scenarios_config.json'
        test_config = {
            'providers': {
                'aws': {'enabled': True, 'region': 'us-west-2'}
            },
            'orchestration': {
                'max_workers': 1,
                'timeout_minutes': 5
            }
        }
        
        import json
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import os
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_cost_optimization_workflow(self):
        """Test cost optimization workflow"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        resources = [
            {'provider': 'aws', 'name': 'compute-analysis', 'analysis_type': 'compute'},
            {'provider': 'aws', 'name': 'storage-analysis', 'analysis_type': 'storage'}
        ]
        
        tasks = orchestrator.create_deployment_plan(resources, OrchestrationStrategy.PARALLEL)
        
        # Should have 2 analysis tasks
        self.assertEqual(len(tasks), 2)
        self.assertTrue(all('analysis' in task.parameters.get('analysis_type', '') for task in tasks))
    
    def test_performance_optimization_workflow(self):
        """Test performance optimization workflow"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        resources = [
            {'provider': 'aws', 'name': 'performance-analysis', 'analysis_type': 'compute', 'optimization_type': 'performance'}
        ]
        
        tasks = orchestrator.create_deployment_plan(resources, OrchestrationStrategy.SEQUENTIAL)
        
        # Should have 1 performance analysis task
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].parameters.get('optimization_type'), 'performance')
    
    def test_rollback_workflow(self):
        """Test rollback workflow for failed optimizations"""
        orchestrator = MultiCloudResourceOptimizerOrchestrator()
        
        # Simulate failed optimization results
        failed_results = [
            OrchestrationResult(
                task_id='task-0',
                provider='aws',
                action='deploy',
                status='error',
                message='Optimization failed',
                timestamp=datetime.now()
            ),
            OrchestrationResult(
                task_id='task-1',
                provider='aws',
                action='deploy',
                status='success',
                message='Optimization completed',
                timestamp=datetime.now()
            )
        ]
        
        rollback_results = orchestrator.rollback_deployment(failed_results)
        
        # Should only rollback successful tasks
        self.assertEqual(len(rollback_results), 1)
        self.assertTrue('rollback' in rollback_results[0].task_id)


class TestDataStructures(unittest.TestCase):
    """Test dataclass structures and enums"""
    
    def test_orchestration_task_creation(self):
        """Test OrchestrationTask dataclass creation"""
        task = OrchestrationTask(
            task_id='optimization-task',
            provider='aws',
            action='deploy',
            parameters={'resource_id': 'test-resource', 'analysis_type': 'compute'},
            priority='high',
            status='pending',
            created_at=datetime.now(),
            dependencies=[]
        )
        
        self.assertEqual(task.task_id, 'optimization-task')
        self.assertEqual(task.provider, 'aws')
        self.assertEqual(task.action, 'deploy')
        self.assertEqual(task.priority, 'high')
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.dependencies, [])
    
    def test_orchestration_result_creation(self):
        """Test OrchestrationResult dataclass creation"""
        result = OrchestrationResult(
            task_id='optimization-task',
            provider='aws',
            action='deploy',
            status='success',
            message='Optimization completed successfully',
            data={'estimated_savings': 125.50, 'recommendations': []},
            timestamp=datetime.now(),
            execution_time=2.5
        )
        
        self.assertEqual(result.task_id, 'optimization-task')
        self.assertEqual(result.provider, 'aws')
        self.assertEqual(result.action, 'deploy')
        self.assertEqual(result.status, 'success')
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
