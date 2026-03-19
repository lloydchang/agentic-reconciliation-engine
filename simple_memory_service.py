#!/usr/bin/env python3
"""
Simple Memory Service
Basic memory management for the AI Infrastructure Portal
"""

import json
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Simple in-memory storage
memory_store = {
    "conversations": [],
    "entities": {},
    "skills": {},
    "metadata": {
        "created_at": datetime.now().isoformat(),
        "version": "1.0.0"
    }
}

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "memory-service"
    })

@app.route('/api/memory/status')
def memory_status():
    """Memory service status"""
    return jsonify({
        "status": "operational",
        "storage": {
            "conversations": len(memory_store["conversations"]),
            "entities": len(memory_store["entities"]),
            "skills": len(memory_store["skills"])
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/memory/search')
def memory_search():
    """Memory search endpoint"""
    return jsonify({
        "results": [],
        "total": 0,
        "query": "sample",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/memory/store')
def memory_store_endpoint():
    """Memory store endpoint"""
    return jsonify({
        "status": "success",
        "stored": True,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🧠 Starting Simple Memory Service")
    print("📍 Available endpoints:")
    print("   - Health: http://localhost:8081/health")
    print("   - Status: http://localhost:8081/api/memory/status")
    print("   - Search: http://localhost:8081/api/memory/search")
    print("   - Store: http://localhost:8081/api/memory/store")
    app.run(host='0.0.0.0', port=8081, debug=True)
