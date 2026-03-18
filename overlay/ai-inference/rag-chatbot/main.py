#!/usr/bin/env python3
"""
RAG Chatbot Service
Integrates OpenAI, Ollama, Agent Memory, and Kubernetes data
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import yaml
import requests
from flask import Flask, request, jsonify
from kubernetes import client, config
from prometheus_client import Counter, Histogram, generate_latest
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('rag_chatbot_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('rag_chatbot_request_duration_seconds', 'Request duration')
INFERENCE_COUNT = Counter('rag_chatbot_inference_total', 'Total inference calls', ['provider', 'model'])

app = Flask(__name__)

class RAGChatbot:
    def __init__(self):
        self.config = self._load_config()
        self.k8s_client = self._init_kubernetes()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.agent_memory_url = os.getenv('AGENT_MEMORY_URL', 'http://agent-memory-service:8080')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://ollama-service:11434')
        self.model_name = os.getenv('MODEL_NAME', 'qwen2.5:0.5b')
        
        # Knowledge base with AI skills
        self.knowledge_base = self._load_knowledge_base()
        
        logger.info("RAG Chatbot initialized", config_version=self.config.get('chatbot', {}).get('version'))

    def _load_config(self) -> Dict:
        """Load configuration from ConfigMap"""
        try:
            with open('/app/config/config.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning("Failed to load config, using defaults", error=str(e))
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'chatbot': {'name': 'GitOps AI Assistant', 'version': '1.0.0'},
            'llm': {
                'primary': 'openai',
                'fallback': 'ollama',
                'models': {
                    'openai': {'model': 'gpt-3.5-turbo', 'max_tokens': 1000, 'temperature': 0.7},
                    'ollama': {'model': 'qwen2.5:0.5b', 'max_tokens': 800, 'temperature': 0.6}
                }
            },
            'memory': {'agent_memory_url': 'http://agent-memory-service:8080'},
            'kubernetes': {'enabled': True, 'namespace': 'ai-infrastructure'},
            'system_controls': {'enabled': True}
        }

    def _init_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
            return client.CoreV1Api()
        except:
            logger.warning("Failed to load in-cluster config, trying default")
            try:
                config.load_kube_config()
                return client.CoreV1Api()
            except:
                logger.error("Failed to initialize Kubernetes client")
                return None

    def _load_knowledge_base(self) -> Dict:
        """Load AI skills knowledge base"""
        return {
            "cost_analysis": {
                "description": "Analyzes cloud spend and recommends cost reductions across AWS, Azure, and GCP",
                "capabilities": ["Cost monitoring", "Resource optimization", "Billing analysis", "Savings recommendations"],
                "usage": "Automatically runs daily cost analysis and generates optimization reports"
            },
            "security_audit": {
                "description": "Performs comprehensive security assessments including CIS, NIST, PCI-DSS compliance",
                "capabilities": ["Vulnerability scanning", "Compliance checking", "Security recommendations", "Remediation"],
                "usage": "Continuous security monitoring with automated remediation"
            },
            "log_analysis": {
                "description": "Aggregates and analyzes logs from multiple sources with anomaly detection",
                "capabilities": ["Log aggregation", "Anomaly detection", "Pattern recognition", "Alert generation"],
                "usage": "Real-time log analysis with intelligent alerting"
            },
            "performance_tuning": {
                "description": "Monitors resource usage and provides auto-scaling recommendations",
                "capabilities": ["Resource monitoring", "Performance metrics", "Auto-scaling", "Optimization"],
                "usage": "Continuous performance monitoring with automatic optimization"
            },
            "certificate_rotation": {
                "description": "Automated SSL/TLS certificate lifecycle management",
                "capabilities": ["Certificate monitoring", "Auto-renewal", "Expiry alerts", "Deployment"],
                "usage": "Automated certificate management with zero downtime"
            },
            "dependency_updates": {
                "description": "Vulnerability scanning and automated dependency patching",
                "capabilities": ["Vulnerability scanning", "Automated patching", "Version management", "Security updates"],
                "usage": "Continuous dependency monitoring with automated security updates"
            }
        }

    async def get_cluster_data(self) -> Dict:
        """Get real Kubernetes cluster data"""
        if not self.k8s_client:
            return {"error": "Kubernetes client not available"}

        try:
            namespace = self.config.get('kubernetes', {}).get('namespace', 'ai-infrastructure')
            
            # Get pods
            pods = self.k8s_client.list_namespaced_pod(namespace)
            pod_data = []
            for pod in pods.items:
                pod_data.append({
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": sum(1 for c in pod.status.container_statuses if c.ready) if pod.status.container_statuses else 0,
                    "total": len(pod.spec.containers),
                    "restarts": pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0,
                    "age": str(datetime.now(pod.metadata.creation_timestamp.timestamp()).replace(microsecond=0, second=0)) if pod.metadata.creation_timestamp else "Unknown"
                })

            # Get nodes
            nodes = self.k8s_client.list_node()
            node_count = len(nodes.items)

            return {
                "namespace": namespace,
                "pods": pod_data,
                "node_count": node_count,
                "total_pods": len(pod_data)
            }

        except Exception as e:
            logger.error("Failed to get cluster data", error=str(e))
            return {"error": str(e)}

    def retrieve_knowledge(self, query: str) -> List[Dict]:
        """Retrieve relevant knowledge from knowledge base"""
        query_lower = query.lower()
        relevant = []
        
        for skill_name, skill_info in self.knowledge_base.items():
            score = 0
            if any(word in query_lower for word in skill_name.split('_')):
                score += 10
            if any(word in query_lower for word in skill_info['description'].lower().split()):
                score += 5
            if any(word in query_lower for word in ' '.join(skill_info['capabilities']).lower().split()):
                score += 3
            
            if score > 0:
                relevant.append({
                    "skill": skill_name,
                    "info": skill_info,
                    "relevance_score": score
                })
        
        return sorted(relevant, key=lambda x: x['relevance_score'], reverse=True)[:3]

    async def get_memory_context(self, query: str) -> Optional[str]:
        """Get conversation context from agent memory"""
        try:
            response = requests.get(f"{self.agent_memory_url}/api/retrieve", 
                                  params={"query": query, "limit": 5},
                                  timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return " ".join([item['content'] for item in data['results']])
        except Exception as e:
            logger.warning("Failed to get memory context", error=str(e))
        return None

    async def generate_openai_response(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            model_config = self.config['llm']['models']['openai']
            response = client.chat.completions.create(
                model=model_config['model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=model_config['max_tokens'],
                temperature=model_config['temperature']
            )
            
            INFERENCE_COUNT.labels(provider='openai', model=model_config['model']).inc()
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("OpenAI inference failed", error=str(e))
            raise

    async def generate_ollama_response(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            response = requests.post(f"{self.ollama_url}/api/generate",
                                  json={
                                      "model": self.model_name,
                                      "prompt": prompt,
                                      "stream": False
                                  },
                                  timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                INFERENCE_COUNT.labels(provider='ollama', model=self.model_name).inc()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error("Ollama inference failed", error=str(e))
            raise

    async def generate_response(self, query: str) -> Dict:
        """Generate RAG response"""
        try:
            # Get cluster data
            cluster_data = await self.get_cluster_data()
            
            # Retrieve relevant knowledge
            knowledge = self.retrieve_knowledge(query)
            
            # Get memory context
            memory_context = await self.get_memory_context(query)
            
            # Build enhanced prompt
            prompt_parts = [
                "You are a helpful GitOps infrastructure assistant.",
                "Here is the current cluster status:",
                json.dumps(cluster_data, indent=2),
            ]
            
            if knowledge:
                prompt_parts.append("\nRelevant knowledge:")
                for item in knowledge:
                    prompt_parts.append(f"- {item['skill']}: {item['info']['description']}")
            
            if memory_context:
                prompt_parts.append(f"\nPrevious context: {memory_context}")
            
            prompt_parts.append(f"\nUser question: {query}")
            prompt_parts.append("\nProvide a helpful response based on the available information.")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Try OpenAI first, then fallback to Ollama
            try:
                response = await self.generate_openai_response(full_prompt)
                provider = "openai"
            except:
                response = await self.generate_ollama_response(full_prompt)
                provider = "ollama"
            
            # Store in memory if available
            try:
                requests.post(f"{self.agent_memory_url}/api/store",
                            json={"query": query, "response": response, "context": str(cluster_data)},
                            timeout=5)
            except:
                pass  # Memory storage is optional
            
            return {
                "query": query,
                "response": response,
                "provider": provider,
                "cluster_data": cluster_data,
                "relevant_knowledge": knowledge,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return {
                "query": query,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "provider": "error",
                "timestamp": datetime.utcnow().isoformat()
            }

# Initialize chatbot
chatbot = RAGChatbot()

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/ready')
def ready():
    """Readiness check endpoint"""
    return jsonify({"status": "ready", "chatbot": chatbot.config.get('chatbot', {}).get('name')})

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.route('/chat', methods=['POST'])
@REQUEST_DURATION.time()
def chat():
    """Main chat endpoint"""
    REQUEST_COUNT.labels(method='POST', endpoint='/chat').inc()
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' field"}), 400
        
        query = data['query']
        logger.info("Chat request received", query=query[:100])
        
        # Generate response asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(chatbot.generate_response(query))
        finally:
            loop.close()
        
        logger.info("Chat response generated", provider=result.get('provider'))
        return jsonify(result)
        
    except Exception as e:
        logger.error("Chat endpoint error", error=str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/cluster')
def cluster():
    """Get cluster information"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(chatbot.get_cluster_data())
        return jsonify(result)
    finally:
        loop.close()

@app.route('/knowledge')
def knowledge():
    """Get knowledge base information"""
    return jsonify(chatbot.knowledge_base)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
