#!/usr/bin/env python3
"""
K8sGPT Analyzer - AI-Powered Kubernetes Intelligence
Integrates K8sGPT with Qwen LLM for intelligent cluster analysis
"""

import json
import sys
import uuid
import logging
import subprocess
import yaml
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class K8sGPTAnalyzer:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.config = self._load_config()
        self.k8sgpt_path = self._find_k8sgpt()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or defaults"""
        config_path = Path.home() / '.k8sgpt' / 'config.yaml'
        default_config = {
            'backend': 'qwen',
            'model': 'qwen2.5-7b-instruct',
            'baseurl': 'http://localhost:8000/v1',
            'max_tokens': 4096,
            'temperature': 0.7,
            'namespace': 'default',
            'output_format': 'json',
            'api_key': os.getenv('QWEN_API_KEY', ''),
            'timeout': 300
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                    default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _find_k8sgpt(self) -> str:
        """Find K8sGPT binary in PATH"""
        try:
            result = subprocess.run(['which', 'k8sgpt'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("K8sGPT CLI not found. Please install K8sGPT first.")
    
    def execute_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main operation execution"""
        try:
            validated_params = self._validate_inputs(params)
            self._setup_k8sgpt_backend(validated_params)
            results = self._perform_analysis(validated_params)
            return self._format_output(results, "completed")
        except Exception as e:
            return self._handle_error(e, params)
    
    def _validate_inputs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Input validation"""
        required_fields = ['operation', 'targetResource']
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
        
        valid_operations = ['analyze', 'diagnose', 'optimize', 'monitor', 'report']
        if params['operation'] not in valid_operations:
            raise ValueError(f"Invalid operation: {params['operation']}")
        
        valid_backends = ['qwen', 'openai', 'localai', 'ollama']
        backend = params.get('backend', self.config['backend'])
        if backend not in valid_backends:
            raise ValueError(f"Invalid backend: {backend}")
        
        return params
    
    def _setup_k8sgpt_backend(self, params: Dict[str, Any]) -> None:
        """Configure K8sGPT backend (Qwen by default)"""
        backend = params.get('backend', self.config['backend'])
        
        try:
            if backend == 'qwen':
                # Configure Qwen backend via LocalAI/OpenAI compatible API
                cmd = [
                    'k8sgpt', 'auth', 'add',
                    '--backend', 'localai',
                    '--model', self.config['model'],
                    '--baseurl', self.config['baseurl']
                ]
                if self.config.get('api_key'):
                    cmd.extend(['--password', self.config['api_key']])
                
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            
            elif backend == 'openai':
                # Configure OpenAI backend
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable required")
                
                cmd = [
                    'k8sgpt', 'auth', 'add',
                    '--backend', 'openai',
                    '--model', params.get('model', 'gpt-4o-mini'),
                    '--password', api_key
                ]
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            
            elif backend == 'ollama':
                # Configure Ollama backend
                cmd = [
                    'k8sgpt', 'auth', 'add',
                    '--backend', 'localai',
                    '--model', params.get('model', 'llama3.1'),
                    '--baseurl', 'http://localhost:11434/v1'
                ]
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            
            logging.info(f"K8sGPT backend configured: {backend}")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Backend configuration timeout for {backend}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Backend configuration failed: {e.stderr}")
    
    def _perform_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute K8sGPT analysis"""
        operation = params['operation']
        target = params['targetResource']
        scope = params.get('scope', 'cluster')
        explain = params.get('explain', True)
        backend = params.get('backend', self.config['backend'])
        
        # Build K8sGPT command
        cmd = ['k8sgpt', 'analyze']
        
        # Add scope/namespace if specified
        if scope != 'cluster' and scope != 'all':
            cmd.extend(['--namespace', scope])
        
        # Add target filter if not cluster-wide
        if target != 'cluster':
            cmd.extend(['--filter', target])
        
        # Add explanation flag
        if explain:
            cmd.append('--explain')
        
        # Add output format
        output_format = params.get('output', self.config['output_format'])
        if output_format != 'json':
            cmd.extend(['--output', output_format])
        
        # Add backend specification
        cmd.extend(['--backend', backend])
        
        # Add additional filters based on operation type
        if operation == 'diagnose':
            cmd.extend(['--filter', 'problems'])
        elif operation == 'optimize':
            cmd.extend(['--filter', 'resources'])
        elif operation == 'monitor':
            cmd.extend(['--filter', 'events'])
        
        logging.info(f"Executing K8sGPT command: {' '.join(cmd)}")
        
        try:
            # Execute analysis with timeout
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=self.config.get('timeout', 300)
            )
            
            # Parse and enhance results
            analysis_data = self._parse_k8sgpt_output(result.stdout)
            
            # Add metadata
            enhanced_results = {
                'operation': operation,
                'target': target,
                'scope': scope,
                'analysis': analysis_data,
                'timestamp': datetime.utcnow().isoformat(),
                'backend': backend,
                'command': ' '.join(cmd),
                'execution_time': 0  # Will be filled by format_output
            }
            
            # Add cluster context if available
            try:
                cluster_info = self._get_cluster_info()
                enhanced_results['cluster_context'] = cluster_info
            except Exception as e:
                logging.warning(f"Failed to get cluster info: {e}")
            
            return enhanced_results
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Analysis timeout after {self.config.get('timeout', 300)} seconds")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"K8sGPT analysis failed: {e.stderr}")
    
    def _parse_k8sgpt_output(self, output: str) -> Dict[str, Any]:
        """Parse K8sGPT output into structured format"""
        try:
            # Try JSON first
            return json.loads(output)
        except json.JSONDecodeError:
            # Parse text output into structured format
            lines = output.strip().split('\n')
            
            # Try to identify sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                        current_content = []
                        current_section = None
                    continue
                
                # Check if this looks like a section header
                if line.endswith(':') and len(line) < 50:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = line.rstrip(':')
                    current_content = []
                else:
                    if not current_section:
                        current_section = "analysis"
                    current_content.append(line)
            
            # Add final section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            
            return {
                'format': 'text',
                'sections': sections,
                'raw_output': output,
                'summary': lines[0] if lines else "No analysis available",
                'line_count': len(lines)
            }
    
    def _get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information"""
        try:
            # Get cluster context
            result = subprocess.run(
                ['kubectl', 'config', 'current-context'],
                capture_output=True, text=True, check=True
            )
            context = result.stdout.strip()
            
            # Get cluster info
            result = subprocess.run(
                ['kubectl', 'cluster-info'],
                capture_output=True, text=True, check=True
            )
            cluster_info = result.stdout.strip()
            
            # Get node count
            result = subprocess.run(
                ['kubectl', 'get', 'nodes', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            node_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get namespace count
            result = subprocess.run(
                ['kubectl', 'get', 'namespaces', '--no-headers'],
                capture_output=True, text=True, check=True
            )
            namespace_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            return {
                'context': context,
                'cluster_info': cluster_info,
                'node_count': node_count,
                'namespace_count': namespace_count
            }
            
        except subprocess.CalledProcessError:
            return {'error': 'Failed to get cluster information'}
    
    def _format_output(self, results: Dict[str, Any], status: str) -> Dict[str, Any]:
        """Format output according to enterprise schema"""
        # Calculate execution time (simplified)
        start_time = datetime.fromisoformat(results['timestamp'].replace('Z', '+00:00'))
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "operationId": self.operation_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "result": results,
            "metadata": {
                "execution_time": execution_time,
                "risk_score": self._calculate_risk_score(results),
                "agent_version": "1.0.0",
                "k8sgpt_version": "latest",
                "backend": self.config['backend'],
                "model": self.config['model']
            }
        }
    
    def _calculate_risk_score(self, results: Dict[str, Any]) -> int:
        """Calculate risk score based on analysis results"""
        base_score = 3
        
        # Check for critical issues in analysis
        analysis = results.get('analysis', {})
        if isinstance(analysis, dict):
            sections = analysis.get('sections', {})
            for section_name, section_content in sections:
                # Look for risk indicators
                content_lower = section_content.lower()
                if any(keyword in content_lower for keyword in ['critical', 'error', 'failed', 'security']):
                    base_score = min(10, base_score + 2)
                elif any(keyword in content_lower for keyword in ['warning', 'caution', 'attention']):
                    base_score = min(8, base_score + 1)
        
        return base_score
    
    def _handle_error(self, error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive error handling"""
        return {
            "operationId": self.operation_id,
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "code": "ANALYSIS_ERROR",
                "message": str(error),
                "details": {
                    "parameters": params,
                    "error_type": type(error).__name__,
                    "config": {
                        'backend': self.config['backend'],
                        'model': self.config['model'],
                        'baseurl': self.config['baseurl']
                    }
                }
            }
        }

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        if len(sys.argv) > 1:
            params = json.loads(sys.argv[1])
        else:
            params = {
                'operation': 'analyze',
                'targetResource': 'cluster',
                'scope': 'cluster',
                'backend': 'qwen',
                'explain': True,
                'output': 'json'
            }
        
        analyzer = K8sGPTAnalyzer()
        result = analyzer.execute_operation(params)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = {
            "status": "failed",
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e),
                "type": type(e).__name__
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
