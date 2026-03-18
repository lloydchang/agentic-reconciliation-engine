#!/usr/bin/env python3

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Configuration - ONLY REAL DATA ALLOWED
METRICS_SERVER_URL = os.environ.get('METRICS_SERVER_URL', 'http://localhost:8080')

def fetch_real_metrics(endpoint):
    """Fetch REAL metrics from the Go metrics server - NO FALLBACKS"""
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
    """Basic agent status endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/core/ai/runtime/status')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/core/ai/runtime/detailed')
def agents_detailed():
    """Detailed agent information endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/core/ai/runtime/detailed')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/workflows/status')
def workflows_status():
    """Workflow status endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/workflows/status')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/metrics/real-time')
def metrics_real_time():
    """Real-time metrics endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/metrics/real-time')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/system/health')
def system_health():
    """System health endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/system/health')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/alerts')
def alerts():
    """Alerts endpoint - REAL DATA ONLY"""
    data = fetch_real_metrics('/api/alerts')
    if data:
        return jsonify(data)
    else:
        return jsonify({
            "error": "Real metrics server unavailable",
            "message": "Go metrics server at http://localhost:8080 is not responding",
            "action_required": "Run: ./setup-real-connection.sh",
            "timestamp": datetime.now().isoformat()
        }), 504

@app.route('/api/config')
def config():
    """Configuration endpoint"""
    return jsonify({
        "data_source": "REAL_METRICS_ONLY",
        "metrics_server_url": METRICS_SERVER_URL,
        "no_fake_data": True,
        "no_simulation": True,
        "real_data_only": True
    })

if __name__ == '__main__':
    print("🔥 REAL DATA ONLY API - NO FAKING, NO SIMULATION")
    print(f"📡 Metrics Server: {METRICS_SERVER_URL}")
    print("⚠️  Will fail if Go metrics server is not available")
    print("🚀 NO FALLBACKS - REAL DATA OR NOTHING!")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
