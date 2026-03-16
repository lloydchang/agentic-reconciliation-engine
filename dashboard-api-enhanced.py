#!/usr/bin/env python3

# Enhanced Dashboard API with Real Metrics Integration
# This Flask app can serve either mock data or real metrics from the Go server

import os
import json
import time
import random
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Configuration
USE_REAL_METRICS = os.environ.get('USE_REAL_METRICS', 'false').lower() == 'true'
METRICS_SERVER_URL = os.environ.get('METRICS_SERVER_URL', 'http://ai-metrics-service.ai-infrastructure.svc.cluster.local:8080')

# Mock data generator (fallback)
def generate_mock_agent_data():
    """Generate mock agent data for fallback"""
    agents = [
        {
            "name": "memory-agent-rust",
            "status": "active",
            "language": "Rust",
            "currentActivity": "Processing memory consolidation for active workflows",
            "skills": ["memory-consolidation", "context-retention", "inference-caching", "data-persistence"],
            "cpu": 45 + random.randint(-5, 5),
            "memory": 128 + random.randint(-16, 16),
            "uptime": "2h 15m",
            "errorRate": 0.02,
            "score": 85.5
        },
        {
            "name": "orchestration-agent-temporal",
            "status": "active",
            "language": "Go",
            "currentActivity": f"Coordinating {random.randint(1, 5)} active workflows across {random.randint(3, 7)} skills",
            "skills": ["workflow-orchestration", "skill-coordination", "task-scheduling", "error-handling"],
            "cpu": 32 + random.randint(-8, 8),
            "memory": 96 + random.randint(-12, 12),
            "uptime": "3h 42m",
            "errorRate": 0.01,
            "score": 92.3
        },
        {
            "name": "inference-gateway-python",
            "status": "idle",
            "language": "Python",
            "currentActivity": "Ready for inference requests - Ollama backend active",
            "skills": ["ai-inference", "model-serving", "request-routing", "load-balancing"],
            "cpu": 12 + random.randint(-3, 3),
            "memory": 64 + random.randint(-8, 8),
            "uptime": "1h 8m",
            "errorRate": 0.00,
            "score": 78.9
        }
    ]
    return agents

def fetch_real_metrics(endpoint):
    """Fetch real metrics from the Go metrics server"""
    try:
        response = requests.get(f"{METRICS_SERVER_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching metrics: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to metrics server: {e}")
        return None

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/agents/status')
def agents_status():
    """Basic agent status endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/agents/status')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    agents = generate_mock_agent_data()
    active_count = sum(1 for agent in agents if agent['status'] == 'active')
    
    return jsonify({
        "agent_count": len(agents),
        "active_agents": active_count,
        "skills_executed": random.randint(40, 50),
        "avg_response_time": random.randint(70, 90),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/agents/detailed')
def agents_detailed():
    """Detailed agent information endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/agents/detailed')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    agents = generate_mock_agent_data()
    return jsonify(agents)

@app.route('/api/workflows/status')
def workflows_status():
    """Workflow status endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/workflows/status')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    return jsonify({
        "active_workflows": random.randint(1, 3),
        "total_workflows": random.randint(10, 20),
        "skills_executed": random.randint(40, 50),
        "avg_response_time": random.randint(70, 90),
        "success_rate": random.uniform(0.85, 0.95),
        "error_rate": random.uniform(0.01, 0.05)
    })

@app.route('/api/metrics/real-time')
def metrics_real_time():
    """Real-time metrics endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/metrics/real-time')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    return jsonify({
        "agent_count": 3,
        "skills_executed": random.randint(40, 50),
        "errors_last_24h": random.randint(0, 3),
        "avg_response_time": random.randint(70, 90),
        "temporal_workflows_active": random.randint(1, 3),
        "memory_usage_mb": random.randint(256, 512),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/system/health')
def system_health():
    """System health endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/system/health')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    return jsonify({
        "status": "healthy",
        "uptime": "4h 23m",
        "agents": 3,
        "workflows": 2,
        "alerts": 0,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/alerts')
def alerts():
    """Alerts endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/alerts')
        if data:
            return jsonify(data)
    
    # Fallback to mock data
    return jsonify([])

@app.route('/api/config')
def config():
    """Configuration endpoint"""
    return jsonify({
        "use_real_metrics": USE_REAL_METRICS,
        "metrics_server_url": METRICS_SERVER_URL,
        "metrics_server_status": "connected" if USE_REAL_METRICS else "mock_mode"
    })

if __name__ == '__main__':
    print(f"Starting Dashboard API...")
    print(f"Real Metrics: {'ENABLED' if USE_REAL_METRICS else 'DISABLED (mock mode)'}")
    if USE_REAL_METRICS:
        print(f"Metrics Server: {METRICS_SERVER_URL}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
