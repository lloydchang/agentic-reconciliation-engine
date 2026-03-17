#!/usr/bin/env python3
"""
Evaluation API Server

FastAPI server for exposing agent tracing evaluation results to the dashboard.
Provides REST endpoints for monitoring, health checks, and auto-fix status.
"""

import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import TracingEvaluationFramework

# Initialize FastAPI app
app = FastAPI(
    title="Evaluation API",
    description="Agent Tracing Evaluation Framework API",
    version="1.0.0"
)

# Enable CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize evaluation framework
evaluation_framework = TracingEvaluationFramework()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for latest evaluation results
latest_results = {}
evaluation_history = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "evaluation-api"
    }

@app.get("/api/v1/evaluation/health")
async def get_evaluation_health():
    """Get agent health evaluation results"""
    try:
        if "health_check" in latest_results:
            return {
                "status": "success",
                "data": latest_results["health_check"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Run evaluation if no cached results
            traces = load_sample_traces()
            results = evaluation_framework.evaluate_traces(traces, ["health_check"])
            latest_results["health_check"] = results["evaluator_results"]["health_check"]
            
            return {
                "status": "success", 
                "data": latest_results["health_check"],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting health evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/evaluation/monitoring")
async def get_evaluation_monitoring():
    """Get monitoring evaluation results"""
    try:
        if "monitoring" in latest_results:
            return {
                "status": "success",
                "data": latest_results["monitoring"],
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Run evaluation if no cached results
            traces = load_sample_traces()
            results = evaluation_framework.evaluate_traces(traces, ["monitoring"])
            latest_results["monitoring"] = results["evaluator_results"]["monitoring"]
            
            return {
                "status": "success",
                "data": latest_results["monitoring"],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting monitoring evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/evaluation/issues")
async def get_evaluation_issues():
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
            
            return {
                "status": "success",
                "data": {
                    "issues": serializable_issues,
                    "total_count": len(serializable_issues),
                    "critical_count": len([i for i in serializable_issues if i.get("severity") == "critical"])
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "success",
                "data": {"issues": [], "total_count": 0, "critical_count": 0},
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting issues: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/evaluation/auto-fix")
async def get_auto_fix_status():
    """Get auto-fix status and history"""
    try:
        auto_fix_manager = evaluation_framework.auto_fix_manager
        
        return {
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
        }
    except Exception as e:
        logger.error(f"Error getting auto-fix status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/evaluation/summary")
async def get_evaluation_summary():
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
        
        return {
            "status": "success",
            "data": {
                "summary": results["summary"],
                "evaluator_results": results["evaluator_results"],
                "trace_count": results["trace_count"],
                "evaluators_run": results["evaluators_run"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/evaluation/evaluate")
async def run_evaluation(request: Dict[str, Any]):
    """Run evaluation on provided traces"""
    try:
        if not request or "traces" not in request:
            raise HTTPException(status_code=400, detail="Missing traces in request body")
        
        traces = request["traces"]
        evaluator_types = request.get("evaluator_types", ["monitoring", "health_check"])
        
        results = evaluation_framework.evaluate_traces(traces, evaluator_types)
        
        # Update cache
        latest_results.update(results["evaluator_results"])
        
        return {
            "status": "success",
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error running evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    parser = argparse.ArgumentParser(description="Evaluation API Server")
    parser.add_argument("--port", type=int, default=8081, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--background", action="store_true", help="Run server in background and exit")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload for production")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Evaluation API Server on {args.host}:{args.port}")
    
    if args.background:
        # Run in background mode
        import subprocess
        import sys
        import os
        
        # Start server in background
        cmd = [
            sys.executable, "api_server.py",
            "--port", str(args.port),
            "--host", args.host,
            "--no-reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info(f"Server started in background with PID: {process.pid}")
        logger.info(f"API available at http://{args.host}:{args.port}")
        
        # Write PID file for management
        with open("api_server.pid", "w") as f:
            f.write(str(process.pid))
        
        # Exit immediately after starting background process
        sys.exit(0)
    else:
        # Run in foreground (development mode)
        uvicorn.run(
            "api_server:app",
            host=args.host,
            port=args.port,
            reload=not args.no_reload,
            log_level="info"
        )
