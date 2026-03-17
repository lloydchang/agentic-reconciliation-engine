#!/usr/bin/env python3
"""
Canary Manager - Progressive Delivery Configuration
Manages canary custom resources and progressive delivery strategies
"""

import json
import sys
import uuid
import logging
import subprocess
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class CanaryManager:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.config = self._load_config()
        self.kubectl_path = self._find_kubectl()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        config_path = Path.home() / '.flagger' / 'config.yaml'
        default_config = {
            'default_namespace': 'default',
            'default_provider': 'istio',
            'default_metrics': 'prometheus',
            'analysis_interval': '10s',
            'success_threshold': 99,
            'failure_threshold': 1,
            'traffic_increment': 10,
            'max_iterations': 10,
            'progress_deadline': '10m',
            'rollback_timeout': '5m'
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _find_kubectl(self) -> str:
        """Find kubectl binary in PATH"""
        try:
            result = subprocess.run(['which', 'kubectl'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("kubectl not found. Please install kubectl first.")
    
    def create_canary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create canary custom resource"""
        strategy = params['strategy']
        target = params['targetResource']
        namespace = params.get('namespace', self.config['default_namespace'])
        provider = params.get('provider', self.config['default_provider'])
        
        logging.info(f"Creating {strategy} canary for {target} in {namespace}")
        
        try:
            # Generate canary manifest
            canary_manifest = self._generate_canary_manifest(strategy, target, namespace, provider, params)
            
            # Validate manifest
            self._validate_canary_manifest(canary_manifest)
            
            # Apply canary configuration
            apply_result = self._apply_canary_manifest(canary_manifest)
            
            # Verify canary creation
            verification_result = self._verify_canary_creation(target, namespace)
            
            return {
                'operation': 'create_canary',
                'strategy': strategy,
                'target': target,
                'namespace': namespace,
                'provider': provider,
                'manifest': canary_manifest,
                'apply_result': apply_result,
                'verification': verification_result,
                'status': 'created'
            }
            
        except Exception as e:
            logging.error(f"Canary creation failed: {e}")
            return {
                'operation': 'create_canary',
                'strategy': strategy,
                'target': target,
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def update_canary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing canary configuration"""
        target = params['targetResource']
        namespace = params.get('namespace', self.config['default_namespace'])
        
        try:
            # Get current canary configuration
            current_canary = self._get_canary_config(target, namespace)
            
            # Generate updated manifest
            updated_manifest = self._update_canary_manifest(current_canary, params)
            
            # Apply updated configuration
            apply_result = self._apply_canary_manifest(updated_manifest)
            
            return {
                'operation': 'update_canary',
                'target': target,
                'namespace': namespace,
                'previous_config': current_canary,
                'updated_manifest': updated_manifest,
                'apply_result': apply_result,
                'status': 'updated'
            }
            
        except Exception as e:
            return {
                'operation': 'update_canary',
                'target': target,
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def delete_canary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete canary custom resource"""
        target = params['targetResource']
        namespace = params.get('namespace', self.config['default_namespace'])
        
        try:
            # Get canary status before deletion
            status_result = self._get_canary_status(target, namespace)
            
            # Delete canary
            cmd = [self.kubectl_path, 'delete', 'canary', target, '-n', namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                'operation': 'delete_canary',
                'target': target,
                'namespace': namespace,
                'previous_status': status_result,
                'delete_result': {
                    'command': ' '.join(cmd),
                    'output': result.stdout
                },
                'status': 'deleted'
            }
            
        except Exception as e:
            return {
                'operation': 'delete_canary',
                'target': target,
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def list_canaries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all canaries in namespace or cluster"""
        namespace = params.get('namespace', '')
        
        try:
            if namespace:
                cmd = [self.kubectl_path, 'get', 'canaries', '-n', namespace, '-o', 'json']
            else:
                cmd = [self.kubectl_path, 'get', 'canaries', '-A', '-o', 'json']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            canaries_data = json.loads(result.stdout)
            
            # Extract relevant information
            canaries_info = []
            for canary in canaries_data.get('items', []):
                canary_info = {
                    'name': canary['metadata']['name'],
                    'namespace': canary['metadata']['namespace'],
                    'target': canary['spec']['targetRef']['name'],
                    'provider': canary['spec'].get('meshProvider', 'unknown'),
                    'strategy': self._detect_strategy(canary),
                    'status': canary.get('status', {}).get('phase', 'unknown')
                }
                canaries_info.append(canary_info)
            
            return {
                'operation': 'list_canaries',
                'namespace': namespace or 'all',
                'canaries': canaries_info,
                'total_count': len(canaries_info),
                'status': 'listed'
            }
            
        except Exception as e:
            return {
                'operation': 'list_canaries',
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def _generate_canary_manifest(self, strategy: str, target: str, namespace: str, 
                                provider: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate canary custom resource manifest"""
        base_manifest = {
            'apiVersion': 'flagger.app/v1beta1',
            'kind': 'Canary',
            'metadata': {
                'name': target,
                'namespace': namespace,
                'labels': {
                    'app.kubernetes.io/name': target,
                    'app.kubernetes.io/component': 'canary'
                }
            },
            'spec': {
                'targetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': target
                },
                'service': {
                    'port': params.get('service_port', 80),
                    'targetPort': params.get('target_port', 8080),
                    'portName': params.get('port_name', 'http')
                },
                'analysis': self._generate_analysis_config(params)
            }
        }
        
        # Add strategy-specific configuration
        if strategy == 'canary':
            base_manifest['spec']['canarySteps'] = self._generate_canary_steps(params)
        elif strategy == 'abtest':
            base_manifest['spec']['canarySteps'] = self._generate_abtest_steps(params)
        elif strategy == 'bluegreen':
            base_manifest['spec']['progressDeadlineSeconds'] = params.get('progress_deadline', 600)
        elif strategy == 'mirror':
            base_manifest['spec']['canarySteps'] = self._generate_mirror_steps(params)
        
        # Add provider-specific configuration
        if provider in ['istio', 'linkerd', 'kuma']:
            base_manifest['spec']['service']['meshName'] = provider
        elif provider in ['nginx', 'contour', 'traefik', 'gloo', 'skipper', 'apisix']:
            base_manifest['spec']['ingressRef'] = self._generate_ingress_ref(provider, target, params)
        
        # Add custom analysis templates if specified
        if 'analysis_templates' in params:
            base_manifest['spec']['analysis']['templates'] = params['analysis_templates']
        
        # Add webhook configuration if specified
        if 'webhooks' in params:
            base_manifest['spec']['analysis']['webhooks'] = params['webhooks']
        
        return base_manifest
    
    def _generate_analysis_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis configuration"""
        return {
            'interval': params.get('analysis_interval', self.config['analysis_interval']),
            'threshold': params.get('success_threshold', self.config['success_threshold']),
            'iterations': params.get('max_iterations', self.config['max_iterations']),
            'metrics': self._generate_metrics_config(params),
            'webhooks': params.get('webhooks', []),
            'templates': params.get('analysis_templates', [])
        }
    
    def _generate_metrics_config(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate metrics configuration"""
        default_metrics = [
            {
                'name': 'request-success-rate',
                'threshold': params.get('success_threshold', self.config['success_threshold']),
                'interval': '1m',
                'query': 'sum(rate(http_server_requests_total{namespace!="{{ namespace }}",status!~"5.."}[2m])) / sum(rate(http_server_requests_total{namespace="{{ namespace }}"}[2m]))'
            },
            {
                'name': 'request-duration',
                'threshold': params.get('duration_threshold', 500),
                'interval': '1m',
                'query': 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{namespace="{{ namespace }}"}[2m])) by (le))'
            }
        ]
        
        # Add custom metrics if specified
        custom_metrics = params.get('custom_metrics', [])
        return default_metrics + custom_metrics
    
    def _generate_canary_steps(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate canary deployment steps"""
        traffic_increment = params.get('traffic_increment', self.config['traffic_increment'])
        pause_duration = params.get('pause_duration', '1m')
        max_weight = params.get('max_weight', 100)
        
        steps = []
        current_weight = traffic_increment
        
        while current_weight < max_weight:
            steps.append({'setWeight': current_weight})
            steps.append({'pause': {'duration': pause_duration}})
            current_weight += traffic_increment
        
        # Final step to route all traffic
        steps.append({'setWeight': 100})
        
        return steps
    
    def _generate_abtest_steps(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate A/B testing steps"""
        test_duration = params.get('test_duration', '10m')
        traffic_split = params.get('traffic_split', 50)
        
        return [
            {'setWeight': traffic_split},
            {'pause': {'duration': test_duration}}
        ]
    
    def _generate_mirror_steps(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate mirroring steps"""
        mirror_duration = params.get('mirror_duration', '5m')
        mirror_percent = params.get('mirror_percent', 100)
        
        return [
            {'mirror': {'percent': mirror_percent, 'duration': mirror_duration}}
        ]
    
    def _generate_ingress_ref(self, provider: str, target: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ingress reference for ingress controllers"""
        ingress_name = params.get('ingress_name', f'{target}-ingress')
        
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'name': ingress_name
        }
    
    def _validate_canary_manifest(self, manifest: Dict[str, Any]) -> None:
        """Validate canary manifest"""
        required_fields = ['apiVersion', 'kind', 'metadata', 'spec']
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field: {field}")
        
        if 'targetRef' not in manifest['spec']:
            raise ValueError("Missing targetRef in spec")
        
        if 'service' not in manifest['spec']:
            raise ValueError("Missing service in spec")
        
        if 'analysis' not in manifest['spec']:
            raise ValueError("Missing analysis in spec")
    
    def _apply_canary_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Apply canary manifest to cluster"""
        manifest_file = f'/tmp/canary-{self.operation_id}.yaml'
        with open(manifest_file, 'w') as f:
            yaml.dump(manifest, f)
        
        cmd = [self.kubectl_path, 'apply', '-f', manifest_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up
        Path(manifest_file).unlink(missing_ok=True)
        
        return {
            'command': ' '.join(cmd),
            'output': result.stdout,
            'stderr': result.stderr
        }
    
    def _verify_canary_creation(self, target: str, namespace: str) -> Dict[str, Any]:
        """Verify canary was created successfully"""
        try:
            cmd = [self.kubectl_path, 'get', 'canary', target, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            canary_data = json.loads(result.stdout)
            
            return {
                'name': canary_data['metadata']['name'],
                'namespace': canary_data['metadata']['namespace'],
                'created_at': canary_data['metadata']['creationTimestamp'],
                'status': canary_data.get('status', {}),
                'verified': True
            }
            
        except Exception as e:
            return {
                'verified': False,
                'error': str(e)
            }
    
    def _get_canary_config(self, target: str, namespace: str) -> Dict[str, Any]:
        """Get current canary configuration"""
        cmd = [self.kubectl_path, 'get', 'canary', target, '-n', namespace, '-o', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    
    def _update_canary_manifest(self, current: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """Update canary manifest with new parameters"""
        updated = current.copy()
        
        # Update analysis configuration
        if 'analysis' in params:
            updated['spec']['analysis'].update(params['analysis'])
        
        # Update canary steps
        if 'canary_steps' in params:
            updated['spec']['canarySteps'] = params['canary_steps']
        
        # Update thresholds
        if 'success_threshold' in params:
            updated['spec']['analysis']['threshold'] = params['success_threshold']
        
        return updated
    
    def _get_canary_status(self, target: str, namespace: str) -> Dict[str, Any]:
        """Get canary status"""
        try:
            cmd = [self.kubectl_path, 'get', 'canary', target, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            canary_data = json.loads(result.stdout)
            return canary_data.get('status', {})
        except Exception:
            return {}
    
    def _detect_strategy(self, canary: Dict[str, Any]) -> str:
        """Detect deployment strategy from canary spec"""
        spec = canary.get('spec', {})
        
        if 'canarySteps' in spec:
            steps = spec['canarySteps']
            if any('mirror' in step for step in steps):
                return 'mirror'
            elif len(steps) == 2 and 'setWeight' in steps[0] and 'pause' in steps[1]:
                return 'abtest'
            else:
                return 'canary'
        elif 'progressDeadlineSeconds' in spec:
            return 'bluegreen'
        else:
            return 'unknown'

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {
            'strategy': 'canary',
            'targetResource': 'example-app',
            'namespace': 'default',
            'provider': 'istio'
        }
    
    manager = CanaryManager()
    
    if params.get('operation') == 'list':
        result = manager.list_canaries(params)
    elif params.get('operation') == 'delete':
        result = manager.delete_canary(params)
    elif params.get('operation') == 'update':
        result = manager.update_canary(params)
    else:
        result = manager.create_canary(params)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
