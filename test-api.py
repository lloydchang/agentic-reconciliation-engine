#!/usr/bin/env python3

from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/agents/detailed')
def agents_detailed():
    return jsonify([
        {
            "name": "test-agent",
            "status": "active", 
            "language": "Go",
            "skills": ["test-skill"],
            "currentActivity": "Testing API connection",
            "cpu": 25,
            "memory": 64,
            "uptime": "1m"
        }
    ])

@app.route('/api/metrics/real-time')
def metrics_real_time():
    return jsonify({
        "agent_count": 1,
        "skills_executed": 1,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("Starting test API on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)
