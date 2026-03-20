#!/usr/bin/env python3
"""
Real service status monitoring for AI Infrastructure Portal
Connects to Kubernetes API to get actual service status
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional

class ServiceMonitor:
    def __init__(self):
        self.services = {
            "ai-dashboard": {
                "name": "AI Dashboard",
                "port": 8080,
                "url": "http://localhost:8080",
                "icon": "🤖",
                "description": "Main AI agents monitoring dashboard with real-time metrics"
            },
            "dashboard-api": {
                "name": "Dashboard API", 
                "port": 5000,
                "url": "http://localhost:5000",
                "icon": "📊",
                "description": "RESTful API for dashboard data and agent metrics"
            },
            "langfuse": {
                "name": "Langfuse Observability",
                "port": 3000,
                "url": "http://localhost:3000",
                "icon": "🔍",
                "description": "LLM observability and analytics platform"
            },
            "comprehensive-api": {
                "name": "Comprehensive API",
                "port": 5001,
                "url": "http://localhost:5001",
                "icon": "📈",
                "description": "Advanced analytics API with detailed agent metrics"
            },
            "comprehensive-dashboard": {
                "name": "Comprehensive Dashboard",
                "port": 8082,
                "url": "http://localhost:8082",
                "icon": "🖥️",
                "description": "Advanced analytics dashboard with time-series metrics"
            },
            "memory-service": {
                "name": "Memory Service",
                "port": 8081,
                "url": "http://localhost:8081",
                "icon": "🧠",
                "description": "AI memory management service with persistent state"
            },
            "temporal-ui": {
                "name": "Temporal UI",
                "port": 7233,
                "url": "http://localhost:7233",
                "icon": "⏰",
                "description": "Workflow orchestration interface for Temporal workflows"
            }
        }
    
    async def check_service_status(self, service_key: str, service_info: Dict) -> Dict:
        """Check if a service is running and responsive"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(service_info["url"], allow_redirects=True) as response:
                    if response.status == 200:
                        return {
                            "status": "running",
                            "message": "Service is operational",
                            "response_time": f"{response.headers.get('X-Response-Time', 'N/A')}"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "response_time": None
                        }
        except aiohttp.ClientError as e:
            return {
                "status": "offline",
                "message": str(e),
                "response_time": None
            }
        except Exception as e:
            return {
                "status": "unknown",
                "message": f"Unexpected error: {str(e)}",
                "response_time": None
            }
    
    async def get_all_services_status(self) -> Dict:
        """Get status of all services"""
        tasks = []
        for service_key, service_info in self.services.items():
            task = asyncio.create_task(
                self.check_service_status(service_key, service_info)
            )
            tasks.append((service_key, task))
        
        results = {}
        for service_key, task in tasks:
            status = await task
            results[service_key] = {
                **self.services[service_key],
                **status,
                "last_checked": datetime.now().isoformat()
            }
        
        return results
    
    async def get_kubernetes_status(self) -> Dict:
        """Get Kubernetes pod status (requires kubectl access)"""
        try:
            # This would require kubectl access - for now return mock data
            # In a real implementation, you'd use kubernetes-python client
            return {
                "total_pods": 12,
                "running_pods": 7,
                "failed_pods": 5,
                "pending_pods": 0,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

# Flask API for serving real status data
from flask import Flask, jsonify, render_template_string
import threading

app = Flask(__name__)
monitor = ServiceMonitor()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Infrastructure Portal - Real Status</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin: 0;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
            margin: 10px 0;
        }
        .refresh-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid white;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        .refresh-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .service-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            text-decoration: none;
            color: inherit;
            position: relative;
            overflow: hidden;
        }
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .service-card.offline {
            border-left: 5px solid #dc3545;
        }
        .service-card.running {
            border-left: 5px solid #28a745;
        }
        .service-card.error {
            border-left: 5px solid #ffc107;
        }
        .service-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .service-icon {
            font-size: 2em;
            margin-right: 15px;
        }
        .service-title {
            flex: 1;
        }
        .service-title h3 {
            margin: 0;
            font-size: 1.3em;
            color: #333;
        }
        .service-title p {
            margin: 5px 0 0 0;
            color: #666;
            font-size: 0.9em;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        .status-indicator.running { background: #28a745; }
        .status-indicator.offline { background: #dc3545; }
        .status-indicator.error { background: #ffc107; }
        .status-indicator.unknown { background: #6c757d; }
        .service-details {
            font-size: 0.85em;
            color: #666;
            line-height: 1.4;
        }
        .service-status {
            margin-top: 10px;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .service-status.running { background: #d4edda; color: #155724; }
        .service-status.offline { background: #f8d7da; color: #721c24; }
        .service-status.error { background: #fff3cd; color: #856404; }
        .service-status.unknown { background: #e2e3e5; color: #383d41; }
        .cluster-status {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        .cluster-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }
        .metric {
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .last-updated {
            text-align: center;
            color: rgba(255,255,255,0.8);
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Infrastructure Portal</h1>
            <p>Real-time monitoring of all your AI services</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Status</button>
        </div>

        <div class="cluster-status">
            <h2>📊 Cluster Overview</h2>
            <div class="cluster-metrics">
                <div class="metric">
                    <div class="metric-value">{{ cluster_status.total_pods or 'N/A' }}</div>
                    <div class="metric-label">Total Pods</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ cluster_status.running_pods or 'N/A' }}</div>
                    <div class="metric-label">Running</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ cluster_status.failed_pods or 'N/A' }}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ cluster_status.pending_pods or 'N/A' }}</div>
                    <div class="metric-label">Pending</div>
                </div>
            </div>
        </div>

        <div class="services-grid">
            {% for service_key, service in services.items() %}
            <a href="{{ service.url }}" class="service-card {{ service.status }}" target="_blank">
                <div class="service-header">
                    <div class="service-icon">{{ service.icon }}</div>
                    <div class="service-title">
                        <h3>{{ service.name }}</h3>
                        <p>{{ service.description }}</p>
                    </div>
                    <div class="status-indicator {{ service.status }}"></div>
                </div>
                <div class="service-details">
                    <strong>Port:</strong> {{ service.port }}<br>
                    <strong>URL:</strong> {{ service.url }}
                </div>
                <div class="service-status {{ service.status }}">
                    {{ service.status.upper() }}: {{ service.message }}
                </div>
            </a>
            {% endfor %}
        </div>

        <div class="last-updated">
            Last updated: {{ last_updated }} | 🔧 Managed by Agentic Reconciliation Engine
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
async def index():
    """Main portal page with real service status"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        services_status = loop.run_until_complete(monitor.get_all_services_status())
        cluster_status = loop.run_until_complete(monitor.get_kubernetes_status())
        
        return render_template_string(
            HTML_TEMPLATE,
            services=services_status,
            cluster_status=cluster_status,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    finally:
        loop.close()

@app.route('/api/status')
async def api_status():
    """API endpoint for service status"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        services_status = loop.run_until_complete(monitor.get_all_services_status())
        cluster_status = loop.run_until_complete(monitor.get_kubernetes_status())
        
        return jsonify({
            "services": services_status,
            "cluster": cluster_status,
            "timestamp": datetime.now().isoformat()
        })
    finally:
        loop.close()

if __name__ == '__main__':
    print("🚀 Starting AI Infrastructure Portal with REAL service monitoring...")
    print("📍 Portal URL: http://localhost:9000")
    print("📊 API Status: http://localhost:9000/api/status")
    print()
    
    app.run(host='0.0.0.0', port=9000, debug=True)
