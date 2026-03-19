from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import time
import random
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# Mock data for demonstration
MOCK_AGENTS = [
    {"name": "Memory Agent (Rust)", "type": "memory", "status": "Running", "lastActivity": "2 minutes ago"},
    {"name": "Temporal Orchestrator", "type": "orchestration", "status": "Running", "lastActivity": "1 minute ago"},
    {"name": "GitOps Controller", "type": "control", "status": "Running", "lastActivity": "5 minutes ago"},
    {"name": "Pi-Mono Agent", "type": "interactive", "status": "Running", "lastActivity": "30 seconds ago"},
    {"name": "Cost Optimizer", "type": "skill", "status": "Idle", "lastActivity": "1 hour ago"},
]

MOCK_ACTIVITIES = [
    {"message": "Cost optimization workflow completed successfully", "timestamp": datetime.now() - timedelta(minutes=5)},
    {"message": "Memory agent processed context for user query", "timestamp": datetime.now() - timedelta(minutes=10)},
    {"message": "GitOps PR #123 merged for infrastructure update", "timestamp": datetime.now() - timedelta(minutes=15)},
    {"message": "Temporal workflow 'cluster-provision' started", "timestamp": datetime.now() - timedelta(minutes=20)},
    {"message": "Pi-Mono agent executed skill: optimize-costs", "timestamp": datetime.now() - timedelta(minutes=25)},
]

MOCK_LOGS = [
    {"level": "INFO", "agent": "Temporal Orchestrator", "message": "Workflow execution completed", "timestamp": datetime.now() - timedelta(minutes=2)},
    {"level": "WARN", "agent": "Memory Agent", "message": "High memory usage detected", "timestamp": datetime.now() - timedelta(minutes=5)},
    {"level": "INFO", "agent": "GitOps Controller", "message": "PR validation passed", "timestamp": datetime.now() - timedelta(minutes=8)},
    {"level": "ERROR", "agent": "Cost Optimizer", "message": "Failed to connect to cloud provider API", "timestamp": datetime.now() - timedelta(minutes=12)},
    {"level": "INFO", "agent": "Pi-Mono Agent", "message": "Skill execution started", "timestamp": datetime.now() - timedelta(minutes=15)},
]

@app.route('/')
def dashboard():
    return send_from_directory(os.path.join(app.root_path, '../dashboard/ui'), 'dashboard-index.html')

@app.route('/api/metrics')
def get_metrics():
    # Mock metrics - in real implementation, this would come from monitoring systems
    return jsonify({
        "agents": {
            "total": len(MOCK_AGENTS),
            "active": len([a for a in MOCK_AGENTS if a["status"] == "Running"]),
            "healthy": len([a for a in MOCK_AGENTS if a["status"] == "Running"]),
            "failed": len([a for a in MOCK_AGENTS if a["status"] == "Idle"])
        },
        "system": {
            "uptime": "2 days, 14 hours",
            "memory_usage": random.randint(45, 75),
            "cpu_usage": random.randint(20, 60),
            "requests_per_minute": random.randint(50, 200)
        },
        "temporal": {
            "workflows_running": random.randint(0, 5),
            "workflows_completed_today": random.randint(20, 100),
            "average_execution_time": f"{random.randint(30, 120)}s"
        }
    })

@app.route('/api/agents')
def get_agents():
    return jsonify(MOCK_AGENTS)

@app.route('/api/activity')
def get_activity():
    activities = []
    for activity in MOCK_ACTIVITIES:
        activities.append({
            "message": activity["message"],
            "timestamp": activity["timestamp"].isoformat()
        })
    return jsonify(activities)

@app.route('/api/logs')
def get_logs():
    logs = []
    for log in MOCK_LOGS:
        logs.append({
            "level": log["level"],
            "agent": log["agent"],
            "message": log["message"],
            "timestamp": log["timestamp"].isoformat()
        })
    return jsonify(logs)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').lower()

    # Simple RAG-like responses based on keywords
    responses = {
        "status": "The system is currently healthy with all core agents running. Memory usage is moderate and temporal workflows are executing normally.",
        "agents": f"There are {len(MOCK_AGENTS)} agents deployed: Memory Agent (Rust), Temporal Orchestrator, GitOps Controller, Pi-Mono Agent, and Cost Optimizer. {len([a for a in MOCK_AGENTS if a['status'] == 'Running'])} are currently active.",
        "metrics": "Current system metrics show good performance with moderate resource usage. CPU usage is around 40%, memory at 60%, and we're handling about 125 requests per minute.",
        "help": "I can help you with system status, agent information, metrics, recent activity, and logs. Try asking about 'status', 'agents', 'metrics', or 'activity'."
    }

    response = "I'm not sure about that. Try asking about status, agents, metrics, or activity."

    for keyword, resp in responses.items():
        if keyword in user_message:
            response = resp
            break

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
