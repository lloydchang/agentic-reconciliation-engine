#!/usr/bin/env python3
"""
Qwen LLM Integration with K8sGPT for Flagger Progressive Delivery
Integrates Qwen LLM with K8sGPT to provide AI-powered analysis for Flagger deployments
"""

import json
import sys
import uuid
import logging
import subprocess
import yaml
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class QwenK8sGPTIntegration:
    def __init__(self):
        self.operation_id = str(uuid.uuid4())
        self.config = self._load_config()
        self.kubectl_path = self._find_kubectl()
        self.k8sgpt_path = self._find_k8sgpt()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Qwen and K8sGPT configuration"""
        config_path = Path.home() / '.flagger' / 'qwen-config.yaml'
        default_config = {
            'qwen': {
                'model': 'qwen2.5-7b-instruct',
                'base_url': 'http://localhost:8000/v1',
                'api_key': 'not-required-for-local',
                'max_tokens': 4096,
                'temperature': 0.7,
                'timeout': 30
            },
            'k8sgpt': {
                'backend': 'localai',
                'model': 'qwen2.5-7b-instruct',
                'namespace': 'default',
                'output_format': 'json',
                'analysis': True,
                'explain': True
            },
            'flagger': {
                'analysis_interval': '30s',
                'max_analysis_time': '10m',
                'cache_results': True,
                'cache_duration': '1h'
            }
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
    
    def _find_k8sgpt(self) -> str:
        """Find K8sGPT binary in PATH"""
        try:
            result = subprocess.run(['which', 'k8sgpt'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise RuntimeError("K8sGPT not found. Please install K8sGPT first.")
    
    def setup_qwen_backend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Qwen LLM backend for K8sGPT"""
        qwen_config = self.config['qwen']
        
        try:
            # Configure K8sGPT to use Qwen backend
            cmd = [
                self.k8sgpt_path, 'auth', 'add',
                '--backend', qwen_config['backend'],
                '--model', qwen_config['model'],
                '--baseurl', qwen_config['base_url']
            ]
            
            if qwen_config.get('api_key'):
                cmd.extend(['--password', qwen_config['api_key']])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Verify configuration
            verify_result = self._verify_qwen_configuration()
            
            return {
                'operation': 'setup_qwen_backend',
                'backend': qwen_config['backend'],
                'model': qwen_config['model'],
                'base_url': qwen_config['base_url'],
                'setup_result': result.stdout,
                'verification': verify_result,
                'status': 'configured'
            }
            
        except Exception as e:
            return {
                'operation': 'setup_qwen_backend',
                'status': 'failed',
                'error': str(e)
            }
    
    def _verify_qwen_configuration(self) -> Dict[str, Any]:
        """Verify Qwen configuration in K8sGPT"""
        try:
            # Test K8sGPT with Qwen backend
            cmd = [
                self.k8sgpt_path, 'analyze',
                '--backend', self.config['qwen']['backend'],
                '--explain',
                '--output', 'json',
                '--filter', 'namespace=default'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    analysis_result = json.loads(result.stdout)
                    return {
                        'status': 'verified',
                        'analysis_result': analysis_result
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'verified',
                        'analysis_result': result.stdout
                    }
            else:
                return {
                    'status': 'failed',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'error': 'K8sGPT analysis timed out'
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def analyze_flagger_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Flagger deployment using K8sGPT with Qwen"""
        deployment_name = params.get('deployment_name', 'unknown')
        namespace = params.get('namespace', 'default')
        analysis_type = params.get('analysis_type', 'comprehensive')
        
        try:
            # Get Flagger canary status
            canary_status = self._get_canary_status(deployment_name, namespace)
            
            # Get deployment information
            deployment_info = self._get_deployment_info(deployment_name, namespace)
            
            # Get service information
            service_info = self._get_service_info(deployment_name, namespace)
            
            # Get events
            events = self._get_deployment_events(deployment_name, namespace)
            
            # Analyze with K8sGPT
            k8sgpt_analysis = self._run_k8sgpt_analysis(deployment_name, namespace, analysis_type)
            
            # Generate AI insights using Qwen
            ai_insights = self._generate_ai_insights(
                canary_status, deployment_info, service_info, events, k8sgpt_analysis
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(ai_insights, canary_status)
            
            return {
                'operation': 'analyze_flagger_deployment',
                'deployment_name': deployment_name,
                'namespace': namespace,
                'analysis_type': analysis_type,
                'canary_status': canary_status,
                'deployment_info': deployment_info,
                'service_info': service_info,
                'events': events,
                'k8sgpt_analysis': k8sgpt_analysis,
                'ai_insights': ai_insights,
                'recommendations': recommendations,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'operation': 'analyze_flagger_deployment',
                'deployment_name': deployment_name,
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def _get_canary_status(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """Get Flagger canary status"""
        try:
            cmd = [self.kubectl_path, 'get', 'canary', deployment_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return {'error': 'Canary not found'}
    
    def _get_deployment_info(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """Get deployment information"""
        try:
            cmd = [self.kubectl_path, 'get', 'deployment', deployment_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return {'error': 'Deployment not found'}
    
    def _get_service_info(self, deployment_name: str, namespace: str) -> Dict[str, Any]:
        """Get service information"""
        try:
            cmd = [self.kubectl_path, 'get', 'svc', deployment_name, '-n', namespace, '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError:
            return {'error': 'Service not found'}
    
    def _get_deployment_events(self, deployment_name: str, namespace: str) -> List[Dict[str, Any]]:
        """Get deployment events"""
        try:
            cmd = [self.kubectl_path, 'get', 'events', '-n', namespace, 
                   '--field-selector', f'involvedObject.name={deployment_name}', '-o', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            events_data = json.loads(result.stdout)
            return events_data.get('items', [])
        except subprocess.CalledProcessError:
            return []
    
    def _run_k8sgpt_analysis(self, deployment_name: str, namespace: str, analysis_type: str) -> Dict[str, Any]:
        """Run K8sGPT analysis"""
        try:
            cmd = [
                self.k8sgpt_path, 'analyze',
                '--backend', self.config['qwen']['backend'],
                '--explain',
                '--output', 'json',
                '--namespace', namespace,
                '--filter', f'deployment={deployment_name}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'raw_output': result.stdout}
            else:
                return {'error': result.stderr}
                
        except subprocess.TimeoutExpired:
            return {'error': 'K8sGPT analysis timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_ai_insights(self, canary_status: Dict[str, Any], deployment_info: Dict[str, Any],
                             service_info: Dict[str, Any], events: List[Dict[str, Any]], 
                             k8sgpt_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI insights using Qwen LLM"""
        try:
            # Prepare context for Qwen
            context = {
                'canary_status': canary_status,
                'deployment_info': deployment_info,
                'service_info': service_info,
                'events': events[-10:],  # Last 10 events
                'k8sgpt_analysis': k8sgpt_analysis
            }
            
            # Generate prompt for Qwen
            prompt = self._generate_analysis_prompt(context)
            
            # Call Qwen API
            qwen_response = self._call_qwen_api(prompt)
            
            # Parse response
            insights = self._parse_qwen_response(qwen_response)
            
            return insights
            
        except Exception as e:
            return {'error': f'AI insights generation failed: {str(e)}'}
    
    def _generate_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Generate analysis prompt for Qwen"""
        prompt = f"""
As an expert Kubernetes and progressive delivery specialist, analyze the following Flagger deployment:

**Canary Status:**
{json.dumps(context['canary_status'], indent=2)}

**Deployment Information:**
{json.dumps(context['deployment_info'], indent=2)}

**Service Information:**
{json.dumps(context['service_info'], indent=2)}

**Recent Events:**
{json.dumps(context['events'], indent=2)}

**K8sGPT Analysis:**
{json.dumps(context['k8sgpt_analysis'], indent=2)}

Please provide:
1. **Deployment Health Assessment**: Overall health status and key metrics
2. **Risk Analysis**: Potential risks and issues identified
3. **Performance Analysis**: Performance bottlenecks or optimization opportunities
4. **Configuration Issues**: Any misconfigurations or best practice violations
5. **Traffic Analysis**: Traffic routing and canary deployment progress
6. **Security Assessment**: Security considerations and recommendations

Focus on actionable insights and specific recommendations for improving the progressive delivery process.
"""
        return prompt
    
    def _call_qwen_api(self, prompt: str) -> str:
        """Call Qwen API for analysis"""
        qwen_config = self.config['qwen']
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {qwen_config["api_key"]}'
            }
            
            data = {
                'model': qwen_config['model'],
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert Kubernetes and progressive delivery specialist. Provide detailed, actionable analysis.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': qwen_config['max_tokens'],
                'temperature': qwen_config['temperature']
            }
            
            response = requests.post(
                f"{qwen_config['base_url']}/chat/completions",
                headers=headers,
                json=data,
                timeout=qwen_config['timeout']
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            raise Exception(f"Qwen API call failed: {str(e)}")
    
    def _parse_qwen_response(self, response: str) -> Dict[str, Any]:
        """Parse Qwen response into structured insights"""
        try:
            # Try to parse as JSON first
            insights = json.loads(response)
        except json.JSONDecodeError:
            # If not JSON, parse text response
            insights = {
                'raw_response': response,
                'structured_insights': self._extract_structured_insights(response)
            }
        
        return insights
    
    def _extract_structured_insights(self, response: str) -> Dict[str, Any]:
        """Extract structured insights from text response"""
        insights = {
            'health_assessment': '',
            'risk_analysis': '',
            'performance_analysis': '',
            'configuration_issues': '',
            'traffic_analysis': '',
            'security_assessment': ''
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if 'health' in line.lower() and 'assessment' in line.lower():
                current_section = 'health_assessment'
            elif 'risk' in line.lower() and 'analysis' in line.lower():
                current_section = 'risk_analysis'
            elif 'performance' in line.lower():
                current_section = 'performance_analysis'
            elif 'configuration' in line.lower():
                current_section = 'configuration_issues'
            elif 'traffic' in line.lower():
                current_section = 'traffic_analysis'
            elif 'security' in line.lower():
                current_section = 'security_assessment'
            elif current_section and line.startswith(('-', '*', '•')):
                # Add bullet point to current section
                insights[current_section] += line + '\n'
        
        return insights
    
    def _generate_recommendations(self, ai_insights: Dict[str, Any], canary_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Extract insights
        structured_insights = ai_insights.get('structured_insights', {})
        
        # Health-based recommendations
        if structured_insights.get('health_assessment'):
            health_text = structured_insights['health_assessment'].lower()
            if 'unhealthy' in health_text or 'failed' in health_text:
                recommendations.append({
                    'category': 'health',
                    'priority': 'high',
                    'action': 'Investigate deployment health issues',
                    'description': 'Deployment shows unhealthy status, review logs and events'
                })
        
        # Risk-based recommendations
        if structured_insights.get('risk_analysis'):
            risk_text = structured_insights['risk_analysis'].lower()
            if 'timeout' in risk_text or 'slow' in risk_text:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'medium',
                    'action': 'Optimize deployment timeouts',
                    'description': 'Consider increasing analysis timeout or optimizing application startup time'
                })
        
        # Performance-based recommendations
        if structured_insights.get('performance_analysis'):
            perf_text = structured_insights['performance_analysis'].lower()
            if 'resource' in perf_text and 'limit' in perf_text:
                recommendations.append({
                    'category': 'resources',
                    'priority': 'medium',
                    'action': 'Review resource limits',
                    'description': 'Consider adjusting CPU/memory limits based on performance analysis'
                })
        
        # Configuration-based recommendations
        if structured_insights.get('configuration_issues'):
            config_text = structured_insights['configuration_issues'].lower()
            if 'threshold' in config_text:
                recommendations.append({
                    'category': 'configuration',
                    'priority': 'low',
                    'action': 'Review analysis thresholds',
                    'description': 'Consider adjusting success rate or latency thresholds based on application behavior'
                })
        
        # Canary-specific recommendations
        canary_phase = canary_status.get('status', {}).get('phase', 'unknown')
        if canary_phase == 'progressing':
            recommendations.append({
                'category': 'deployment',
                'priority': 'info',
                'action': 'Monitor canary progress',
                'description': 'Canary deployment is in progress, continue monitoring'
            })
        elif canary_phase == 'failed':
            recommendations.append({
                'category': 'deployment',
                'priority': 'high',
                'action': 'Investigate canary failure',
                'description': 'Canary deployment failed, review logs and consider rollback'
            })
        
        return recommendations
    
    def setup_automated_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automated analysis for Flagger deployments"""
        namespace = params.get('namespace', 'default')
        schedule = params.get('schedule', '*/5 * * * *')  # Every 5 minutes
        
        try:
            # Create analysis cron job
            cron_job = {
                'apiVersion': 'batch/v1',
                'kind': 'CronJob',
                'metadata': {
                    'name': 'flagger-qwen-analysis',
                    'namespace': namespace
                },
                'spec': {
                    'schedule': schedule,
                    'jobTemplate': {
                        'spec': {
                            'template': {
                                'spec': {
                                    'restartPolicy': 'OnFailure',
                                    'containers': [{
                                        'name': 'qwen-analysis',
                                        'image': 'python:3.9-slim',
                                        'command': ['python3', '/scripts/analyze_flagger.py'],
                                        'env': [
                                            {'name': 'NAMESPACE', 'value': namespace},
                                            {'name': 'QWEN_MODEL', 'value': self.config['qwen']['model']},
                                            {'name': 'QWEN_BASE_URL', 'value': self.config['qwen']['base_url']}
                                        ],
                                        'volumeMounts': [{
                                            'name': 'scripts',
                                            'mountPath': '/scripts'
                                        }]
                                    }],
                                    'volumes': [{
                                        'name': 'scripts',
                                        'configMap': {
                                            'name': 'flagger-analysis-scripts'
                                        }
                                    }]
                                }
                            }
                        }
                    }
                }
            }
            
            # Apply cron job
            cron_file = f'/tmp/flagger-cron-{self.operation_id}.yaml'
            with open(cron_file, 'w') as f:
                yaml.dump(cron_job, f)
            
            cmd = [self.kubectl_path, 'apply', '-f', cron_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            Path(cron_file).unlink(missing_ok=True)
            
            return {
                'operation': 'setup_automated_analysis',
                'namespace': namespace,
                'schedule': schedule,
                'cron_job': 'flagger-qwen-analysis',
                'setup_result': result.stdout,
                'status': 'created'
            }
            
        except Exception as e:
            return {
                'operation': 'setup_automated_analysis',
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_deployment_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        deployment_name = params.get('deployment_name', 'unknown')
        namespace = params.get('namespace', 'default')
        report_format = params.get('format', 'json')
        
        try:
            # Run comprehensive analysis
            analysis_result = self.analyze_flagger_deployment(params)
            
            # Generate report
            report = {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'deployment_name': deployment_name,
                    'namespace': namespace,
                    'analysis_version': '1.0',
                    'llm_model': self.config['qwen']['model']
                },
                'executive_summary': self._generate_executive_summary(analysis_result),
                'detailed_analysis': analysis_result,
                'recommendations': analysis_result.get('recommendations', []),
                'next_steps': self._generate_next_steps(analysis_result),
                'appendix': {
                    'k8sgpt_version': self._get_k8sgpt_version(),
                    'flagger_version': self._get_flagger_version(),
                    'qwen_model': self.config['qwen']['model']
                }
            }
            
            if report_format == 'markdown':
                report['markdown_content'] = self._generate_markdown_report(report)
            
            return {
                'operation': 'generate_deployment_report',
                'deployment_name': deployment_name,
                'namespace': namespace,
                'format': report_format,
                'report': report,
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'operation': 'generate_deployment_report',
                'deployment_name': deployment_name,
                'namespace': namespace,
                'status': 'failed',
                'error': str(e)
            }
    
    def _generate_executive_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        canary_status = analysis_result.get('canary_status', {})
        ai_insights = analysis_result.get('ai_insights', {})
        
        phase = canary_status.get('status', {}).get('phase', 'unknown')
        
        summary = {
            'overall_status': phase,
            'health_score': self._calculate_health_score(analysis_result),
            'key_findings': [],
            'critical_issues': [],
            'recommendations_count': len(analysis_result.get('recommendations', []))
        }
        
        # Extract key findings from AI insights
        structured_insights = ai_insights.get('structured_insights', {})
        for category, content in structured_insights.items():
            if content and len(content.strip()) > 0:
                summary['key_findings'].append({
                    'category': category,
                    'finding': content.strip()
                })
        
        return summary
    
    def _calculate_health_score(self, analysis_result: Dict[str, Any]) -> int:
        """Calculate deployment health score (0-100)"""
        score = 100
        
        # Deduct points for issues
        recommendations = analysis_result.get('recommendations', [])
        for rec in recommendations:
            if rec.get('priority') == 'high':
                score -= 20
            elif rec.get('priority') == 'medium':
                score -= 10
            elif rec.get('priority') == 'low':
                score -= 5
        
        return max(0, score)
    
    def _generate_next_steps(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate next steps based on analysis"""
        next_steps = []
        
        recommendations = analysis_result.get('recommendations', [])
        high_priority = [r for r in recommendations if r.get('priority') == 'high']
        medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
        
        if high_priority:
            next_steps.append({
                'priority': 'immediate',
                'action': 'Address high-priority issues',
                'description': f'{len(high_priority)} high-priority issues require immediate attention',
                'estimated_time': '1-2 hours'
            })
        
        if medium_priority:
            next_steps.append({
                'priority': 'short-term',
                'action': 'Review medium-priority recommendations',
                'description': f'{len(medium_priority)} medium-priority improvements identified',
                'estimated_time': '1-2 days'
            })
        
        next_steps.append({
            'priority': 'ongoing',
            'action': 'Monitor deployment progress',
            'description': 'Continue monitoring canary deployment and automated analysis',
            'estimated_time': 'continuous'
        })
        
        return next_steps
    
    def _get_k8sgpt_version(self) -> str:
        """Get K8sGPT version"""
        try:
            cmd = [self.k8sgpt_path, 'version']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return 'unknown'
    
    def _get_flagger_version(self) -> str:
        """Get Flagger version"""
        try:
            cmd = [self.kubectl_path, 'get', 'deployment', 'flagger', '-n', 'flagger-system', '-o', 'jsonpath={.spec.template.spec.containers[0].image}']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return 'unknown'
    
    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown version of the report"""
        metadata = report['report_metadata']
        summary = report['executive_summary']
        
        markdown = f"""# Flagger Deployment Analysis Report

## Executive Summary

- **Deployment**: {metadata['deployment_name']}
- **Namespace**: {metadata['namespace']}
- **Analysis Date**: {metadata['generated_at']}
- **Overall Status**: {summary['overall_status']}
- **Health Score**: {summary['health_score']}/100

## Key Findings

"""
        
        for finding in summary['key_findings']:
            markdown += f"### {finding['category'].replace('_', ' ').title()}\n"
            markdown += f"{finding['finding']}\n\n"
        
        markdown += "## Recommendations\n\n"
        
        for rec in report['recommendations']:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢', 'info': 'ℹ️'}.get(rec['priority'], '•')
            markdown += f"{priority_emoji} **{rec['action']}** ({rec['priority']})\n"
            markdown += f"{rec['description']}\n\n"
        
        markdown += "## Next Steps\n\n"
        
        for step in report['next_steps']:
            priority_emoji = {'immediate': '🚀', 'short-term': '📋', 'ongoing': '🔄'}.get(step['priority'], '•')
            markdown += f"{priority_emoji} **{step['action']}** ({step['priority']})\n"
            markdown += f"{step['description']} - Estimated: {step['estimated_time']}\n\n"
        
        return markdown

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if len(sys.argv) > 1:
        params = json.loads(sys.argv[1])
    else:
        params = {
            'operation': 'setup_qwen_backend',
            'deployment_name': 'example-app',
            'namespace': 'default'
        }
    
    integration = QwenK8sGPTIntegration()
    
    operation = params.get('operation', 'setup_qwen_backend')
    
    if operation == 'setup_qwen_backend':
        result = integration.setup_qwen_backend(params)
    elif operation == 'analyze_flagger_deployment':
        result = integration.analyze_flagger_deployment(params)
    elif operation == 'setup_automated_analysis':
        result = integration.setup_automated_analysis(params)
    elif operation == 'generate_deployment_report':
        result = integration.generate_deployment_report(params)
    else:
        result = {
            'operation': operation,
            'status': 'failed',
            'error': f'Unknown operation: {operation}'
        }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
