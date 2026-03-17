#!/usr/bin/env python3
"""
Flagger Installer - Progressive Delivery Automation
Main installation and orchestration engine for Flagger progressive delivery
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

class FlaggerInstaller:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.config = self._load_config()
        self.kubectl_path = self._find_kubectl()
        self.helm_path = self._find_helm()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        config_path = Path.home() / '.flagger' / 'config.yaml'
        default_config = {
            'namespace': 'flagger-system',
            'provider': 'istio',
            'metrics_backend': 'prometheus',
            'analysis_interval': '10s',
            'success_threshold': 99,
            'failure_threshold': 1,
            'traffic_increment': 10,
            'timeout': '10m',
            'enable_webhook': True,
            'enable_monitoring': True,
            'log_level': 'info'
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
    
    def _find_helm(self) -> str:
        """Find helm binary in PATH"""
        try:
            result = subprocess.run(['which', 'helm'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("Helm not found. Please install Helm first.")
    
    def install_flagger(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install Flagger operator with specified configuration"""
        namespace = params.get('namespace', self.config['namespace'])
        provider = params.get('provider', self.config['provider'])
        version = params.get('version', 'latest')
        
        logging.info(f"Installing Flagger in namespace {namespace} with provider {provider}")
        
        try:
            # Create namespace if it doesn't exist
            self._create_namespace(namespace)
            
            # Add Flagger Helm repository
            self._add_helm_repo()
            
            # Install Flagger using Helm
            install_result = self._helm_install_flagger(namespace, provider, version, params)
            
            # Verify installation
            verification_result = self._verify_installation(namespace)
            
            # Setup monitoring if enabled
            if params.get('enable_monitoring', self.config['enable_monitoring']):
                monitoring_result = self._setup_monitoring(namespace, provider)
            else:
                monitoring_result = {"status": "skipped", "message": "Monitoring disabled"}
            
            return {
                'operation': 'install',
                'namespace': namespace,
                'provider': provider,
                'version': version,
                'install_result': install_result,
                'verification': verification_result,
                'monitoring': monitoring_result,
                'status': 'completed'
            }
            
        except Exception as e:
            logging.error(f"Flagger installation failed: {e}")
            return {
                'operation': 'install',
                'namespace': namespace,
                'provider': provider,
                'status': 'failed',
                'error': str(e)
            }
    
    def _create_namespace(self, namespace: str) -> None:
        """Create namespace if it doesn't exist"""
        try:
            subprocess.run([self.kubectl_path, 'create', 'namespace', namespace], 
                         check=True, capture_output=True)
            logging.info(f"Created namespace: {namespace}")
        except subprocess.CalledProcessError:
            # Namespace likely exists
            logging.info(f"Namespace {namespace} already exists")
    
    def _add_helm_repo(self) -> None:
        """Add Flagger Helm repository"""
        subprocess.run([self.helm_path, 'repo', 'add', 'flagger', 
                      'https://flagger.app'], check=True, capture_output=True)
        subprocess.run([self.helm_path, 'repo', 'update'], check=True, capture_output=True)
        logging.info("Added Flagger Helm repository")
    
    def _helm_install_flagger(self, namespace: str, provider: str, 
                              version: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Install Flagger using Helm"""
        helm_values = self._generate_helm_values(provider, params)
        
        # Write values to temporary file
        values_file = f'/tmp/flagger-values-{self.operation_id}.yaml'
        with open(values_file, 'w') as f:
            yaml.dump(helm_values, f)
        
        # Build Helm command
        cmd = [
            self.helm_path, 'upgrade', '--install', 'flagger', 'flagger/flagger',
            '--namespace', namespace,
            '--values', values_file,
            '--wait',
            '--timeout', params.get('timeout', self.config['timeout'])
        ]
        
        if version != 'latest':
            cmd.extend(['--version', version])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up values file
        Path(values_file).unlink(missing_ok=True)
        
        return {
            'command': ' '.join(cmd),
            'output': result.stdout,
            'stderr': result.stderr
        }
    
    def _generate_helm_values(self, provider: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Helm values based on provider and parameters"""
        base_values = {
            'meshProvider': provider,
            'crds': {'install': True},
            'logLevel': params.get('log_level', self.config['log_level']),
            'namespace': params.get('namespace', self.config['namespace'])
        }
        
        # Provider-specific configuration
        if provider == 'istio':
            base_values.update({
                'istio': {
                    'enabled': True,
                    'revision': params.get('istio_revision', '')
                }
            })
        elif provider == 'linkerd':
            base_values.update({
                'linkerd': {
                    'enabled': True,
                    'namespace': params.get('linkerd_namespace', 'linkerd')
                }
            })
        elif provider == 'nginx':
            base_values.update({
                'nginx': {
                    'enabled': True,
                    'ingress': params.get('nginx_ingress_class', 'nginx')
                }
            })
        elif provider == 'contour':
            base_values.update({
                'contour': {
                    'enabled': True,
                    'namespace': params.get('contour_namespace', 'contour')
                }
            })
        
        # Metrics backend configuration
        metrics_backend = params.get('metrics_backend', self.config['metrics_backend'])
        if metrics_backend == 'prometheus':
            base_values.update({
                'prometheus': {
                    'enabled': True,
                    'namespace': params.get('prometheus_namespace', 'monitoring')
                }
            })
        
        # Webhook configuration
        if params.get('enable_webhook', self.config['enable_webhook']):
            base_values.update({
                'webhook': {
                    'enabled': True,
                    'timeout': '30s'
                }
            })
        
        # Resource limits
        if 'resources' in params:
            base_values['resources'] = params['resources']
        
        return base_values
    
    def _verify_installation(self, namespace: str) -> Dict[str, Any]:
        """Verify Flagger installation"""
        try:
            # Check Flagger pods
            pods_cmd = [self.kubectl_path, 'get', 'pods', '-n', namespace, 
                       '-l', 'app=flagger', '-o', 'json']
            pods_result = subprocess.run(pods_cmd, capture_output=True, text=True, check=True)
            pods_data = json.loads(pods_result.stdout)
            
            # Check CRDs
            crds_cmd = [self.kubectl_path, 'get', 'crd', '-l', 'app.kubernetes.io/name=flagger', '-o', 'json']
            crds_result = subprocess.run(crds_cmd, capture_output=True, text=True, check=True)
            crds_data = json.loads(crds_result.stdout)
            
            # Check Flagger version
            version_cmd = [self.kubectl_path, 'get', 'deployment', 'flagger', '-n', namespace, 
                          '-o', 'jsonpath={.spec.template.spec.containers[0].image}']
            version_result = subprocess.run(version_cmd, capture_output=True, text=True, check=True)
            
            return {
                'pods': {
                    'count': len(pods_data['items']),
                    'ready': sum(1 for pod in pods_data['items'] 
                                if pod['status']['phase'] == 'Running'),
                    'details': pods_data['items']
                },
                'crds': {
                    'count': len(crds_data['items']),
                    'names': [crd['metadata']['name'] for crd in crds_data['items']]
                },
                'version': version_result.stdout.strip(),
                'status': 'verified'
            }
            
        except Exception as e:
            return {
                'status': 'verification_failed',
                'error': str(e)
            }
    
    def _setup_monitoring(self, namespace: str, provider: str) -> Dict[str, Any]:
        """Setup monitoring and alerting for Flagger"""
        try:
            # Create ServiceMonitor for Prometheus
            servicemonitor = {
                'apiVersion': 'monitoring.coreos.com/v1',
                'kind': 'ServiceMonitor',
                'metadata': {
                    'name': 'flagger',
                    'namespace': namespace,
                    'labels': {
                        'app.kubernetes.io/name': 'flagger',
                        'app.kubernetes.io/component': 'monitoring'
                    }
                },
                'spec': {
                    'selector': {
                        'matchLabels': {
                            'app': 'flagger'
                        }
                    },
                    'endpoints': [
                        {
                            'port': 'http',
                            'path': '/metrics',
                            'interval': '30s'
                        }
                    ]
                }
            }
            
            # Apply ServiceMonitor
            servicemonitor_file = f'/tmp/flagger-servicemonitor-{self.operation_id}.yaml'
            with open(servicemonitor_file, 'w') as f:
                yaml.dump(servicemonitor, f)
            
            cmd = [self.kubectl_path, 'apply', '-f', servicemonitor_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Create Grafana dashboard
            dashboard_result = self._create_grafana_dashboard(namespace, provider)
            
            # Clean up
            Path(servicemonitor_file).unlink(missing_ok=True)
            
            return {
                'servicemonitor': {
                    'command': ' '.join(cmd),
                    'output': result.stdout
                },
                'grafana_dashboard': dashboard_result,
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _create_grafana_dashboard(self, namespace: str, provider: str) -> Dict[str, Any]:
        """Create Grafana dashboard for Flagger monitoring"""
        dashboard_config = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': 'flagger-dashboard',
                'namespace': namespace,
                'labels': {
                    'grafana_dashboard': '1'
                }
            },
            'data': {
                'flagger-dashboard.json': json.dumps({
                    "dashboard": {
                        "title": f"Flagger - {provider.title()} Provider",
                        "panels": [
                            {
                                "title": "Canary Deployments",
                                "type": "stat",
                                "targets": [
                                    {
                                        "expr": "sum(flagger_canary_total)",
                                        "legendFormat": "Total Canaries"
                                    }
                                ]
                            },
                            {
                                "title": "Deployment Success Rate",
                                "type": "stat",
                                "targets": [
                                    {
                                        "expr": "sum(rate(flagger_canary_success_total[5m])) / sum(rate(flagger_canary_total[5m])) * 100",
                                        "legendFormat": "Success Rate %"
                                    }
                                ]
                            }
                        ]
                    }
                })
            }
        }
        
        # Apply dashboard
        dashboard_file = f'/tmp/flagger-dashboard-{self.operation_id}.yaml'
        with open(dashboard_file, 'w') as f:
            yaml.dump(dashboard_config, f)
        
        cmd = [self.kubectl_path, 'apply', '-f', dashboard_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Clean up
        Path(dashboard_file).unlink(missing_ok=True)
        
        return {
            'command': ' '.join(cmd),
            'output': result.stdout
        }

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {
            'namespace': 'flagger-system',
            'provider': 'istio',
            'version': 'latest',
            'enable_monitoring': True
        }
    
    installer = FlaggerInstaller()
    result = installer.install_flagger(params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
