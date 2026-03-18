#!/usr/bin/env python3

# Enhanced Dashboard API with Real Metrics Integration
# This Flask app can serve either mock data or real metrics from the Go server

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Configuration
USE_REAL_METRICS = os.environ.get('USE_REAL_METRICS', 'false').lower() == 'true'
METRICS_SERVER_URL = os.environ.get('METRICS_SERVER_URL', 'http://ai-metrics-service.ai-infrastructure.svc.cluster.local:8080')

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

@app.route('/api/core/ai/runtime/status')
def agents_status():
    """Basic agent status endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/core/ai/runtime/status')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

@app.route('/api/core/ai/runtime/detailed')
def agents_detailed():
    """Detailed agent information endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/core/ai/runtime/detailed')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

@app.route('/api/workflows/status')
def workflows_status():
    """Workflow status endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/workflows/status')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

@app.route('/api/metrics/real-time')
def metrics_real_time():
    """Real-time metrics endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/metrics/real-time')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

@app.route('/api/system/health')
def system_health():
    """System health endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/system/health')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

@app.route('/api/alerts')
def alerts():
    """Alerts endpoint"""
    if USE_REAL_METRICS:
        data = fetch_real_metrics('/api/alerts')
        if data:
            return jsonify(data)
        else:
            return jsonify({
                "error": "Metrics server unavailable",
                "message": "Real metrics service is not responding",
                "timestamp": datetime.now().isoformat()
            }), 504
    
    # Mock data removed - API should fail when real metrics disabled
    return jsonify({
        "error": "Real metrics not enabled",
        "message": "Set USE_REAL_METRICS=true to enable real monitoring",
        "timestamp": datetime.now().isoformat()
    }), 503

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
