#!/usr/bin/env python3
"""
Evaluation API Server

HTTP API server for exposing agent tracing evaluation results to the dashboard.
Provides REST endpoints for monitoring, health checks, and auto-fix status.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TracingEvaluationFramework

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard integration

# Initialize evaluation framework
evaluation_framework = TracingEvaluationFramework()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for latest evaluation results
latest_results = {}
evaluation_history = []

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "evaluation-api"
    })

@app.route('/api/v1/evaluation/health', methods=['GET'])
def get_evaluation_health():
    """Get agent health evaluation results"""
    try:
        if "health_check" in latest_results:
            return jsonify({
                "status": "success",
                "data": latest_results["health_check"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Run evaluation if no cached results
            traces = load_sample_traces()
            results = evaluation_framework.evaluate_traces(traces, ["health_check"])
            latest_results["health_check"] = results["evaluator_results"]["health_check"]
            
            return jsonify({
                "status": "success", 
                "data": latest_results["health_check"],
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error getting health evaluation: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/evaluation/monitoring', methods=['GET'])
def get_evaluation_monitoring():
    """Get monitoring evaluation results"""
    try:
        if "monitoring" in latest_results:
            return jsonify({
                "status": "success",
                "data": latest_results["monitoring"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Run evaluation if no cached results
            traces = load_sample_traces()
            results = evaluation_framework.evaluate_traces(traces, ["monitoring"])
            latest_results["monitoring"] = results["evaluator_results"]["monitoring"]
            
            return jsonify({
                "status": "success",
                "data": latest_results["monitoring"],
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error getting monitoring evaluation: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/evaluation/issues', methods=['GET'])
def get_evaluation_issues():
    """Get detected issues from evaluation"""
    try:
        if "monitoring" in latest_results:
            monitoring_data = latest_results["monitoring"]
            issues = []
            
            # Extract issues from monitoring report
            if "infrastructure_health" in monitoring_data:
                issues.extend(monitoring_data["infrastructure_health"].get("issues", []))
            if "temporal_health" in monitoring_data:
                issues.extend(monitoring_data["temporal_health"].get("timeout_issues", []))
            if "agent_health" in monitoring_data:
                issues.extend(monitoring_data["agent_health"].get("issues", []))
            
            # Convert issues to serializable format
            serializable_issues = []
            for issue in issues:
                if hasattr(issue, '__dict__'):
                    serializable_issues.append(issue.__dict__)
                else:
                    serializable_issues.append(issue)
            
            return jsonify({
                "status": "success",
                "data": {
                    "issues": serializable_issues,
                    "total_count": len(serializable_issues),
                    "critical_count": len([i for i in serializable_issues if i.get("severity") == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "success",
                "data": {"issues": [], "total_count": 0, "critical_count": 0},
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"Error getting issues: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/evaluation/auto-fix', methods=['GET'])
def get_auto_fix_status():
    """Get auto-fix status and history"""
    try:
        auto_fix_manager = evaluation_framework.auto_fix_manager
        
        return jsonify({
            "status": "success",
            "data": {
                "fix_history": [
                    {
                        "timestamp": fix.timestamp.isoformat(),
                        "action": fix.action.value,
                        "target": fix.target,
                        "success": fix.success,
                        "error_message": fix.error_message
                    } for fix in auto_fix_manager.fix_history
                ],
                "backoff_periods": auto_fix_manager.backoff_periods,
                "total_fixes": len(auto_fix_manager.fix_history)
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting auto-fix status: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/evaluation/summary', methods=['GET'])
def get_evaluation_summary():
    """Get comprehensive evaluation summary"""
    try:
        # Ensure we have latest results
        traces = load_sample_traces()
        results = evaluation_framework.evaluate_traces(traces, ["monitoring", "health_check"])
        
        # Update cache
        latest_results.update(results["evaluator_results"])
        
        # Store in history
        evaluation_history.append({
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        # Keep only last 10 evaluations
        if len(evaluation_history) > 10:
            evaluation_history.pop(0)
        
        return jsonify({
            "status": "success",
            "data": {
                "summary": results["summary"],
                "evaluator_results": results["evaluator_results"],
                "trace_count": results["trace_count"],
                "evaluators_run": results["evaluators_run"]
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/evaluation/evaluate', methods=['POST'])
def run_evaluation():
    """Run evaluation on provided traces"""
    try:
        data = request.get_json()
        
        if not data or "traces" not in data:
            return jsonify({
                "status": "error",
                "error": "Missing traces in request body"
            }), 400
        
        traces = data["traces"]
        evaluator_types = data.get("evaluator_types", ["monitoring", "health_check"])
        
        results = evaluation_framework.evaluate_traces(traces, evaluator_types)
        
        # Update cache
        latest_results.update(results["evaluator_results"])
        
        return jsonify({
            "status": "success",
            "data": results,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error running evaluation: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def load_sample_traces():
    """Load sample traces for demonstration"""
    try:
        # Try to load from file
        with open("sample_traces.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return mock traces if file not found
        return [
            {
                "kubernetes": {
                    "pod_restarts": 3,
                    "pod_name": "agent-worker-1",
                    "namespace": "temporal"
                },
                "temporal": {
                    "status": "completed",
                    "workflow_type": "skill_execution",
                    "duration_ms": 1500
                },
                "agent": {
                    "conversation": [{"turn": i} for i in range(10)],
                    "tools": [{"name": "kubectl", "success": True}]
                },
                "timestamp": datetime.now().isoformat()
            }
        ]

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluation API Server")
    parser.add_argument("--port", type=int, default=8081, help="Port to run the server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Evaluation API Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
