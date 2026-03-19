#!/usr/bin/env python3

import os
import json
import yaml
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import kubernetes
from kubernetes import client, config
import redis
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agents Analytics Dashboard API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup for time-series data
DB_PATH = "/tmp/agents_metrics.db"

class MetricsCollector:
    def __init__(self):
        self.db_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.init_database()
        self.setup_kubernetes()
        
    def init_database(self):
        """Initialize SQLite database for metrics storage"""
        cursor = self.db_conn.cursor()
        
        # Agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                status TEXT NOT NULL,
                pod_name TEXT,
                workflow_id TEXT,
                memory_agent_id TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                success_rate REAL,
                error_count INTEGER
            )
        ''')
        
        # Skills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                skill_description TEXT,
                risk_level TEXT,
                autonomy_level TEXT,
                execution_count INTEGER,
                success_count INTEGER,
                failure_count INTEGER,
                avg_execution_time REAL
            )
        ''')
        
        # Failures table for post-mortem analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                skill_name TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT,
                root_cause TEXT,
                resolution TEXT,
                severity TEXT,
                status TEXT DEFAULT 'open'
            )
        ''')
        
        self.db_conn.commit()
        
    def setup_kubernetes(self):
        """Setup Kubernetes client"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        self.k8s_client = client.CoreV1Api()
        self.apps_client = client.AppsV1Api()
        
    def collect_agent_metrics(self) -> List[Dict]:
        """Collect metrics from all agent types"""
        agents = []
        timestamp = datetime.now().isoformat()
        
        # 1. Kubernetes Pods (Container-based agents)
        try:
            pods = self.k8s_client.list_namespaced_pod("ai-infrastructure", label_selector="app in (agent-dashboard,dashboard-api)")
            for pod in pods.items:
                cpu_usage = self._get_pod_cpu_usage(pod.metadata.name)
                memory_usage = self._get_pod_memory_usage(pod.metadata.name)
                
                agents.append({
                    "timestamp": timestamp,
                    "agent_name": pod.metadata.name,
                    "agent_type": "kubernetes_pod",
                    "status": "running" if pod.status.phase == "Running" else "failed",
                    "pod_name": pod.metadata.name,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "success_rate": 100.0,  # Placeholder - would be calculated from actual metrics
                    "error_count": 0
                })
        except Exception as e:
            logger.error(f"Error collecting pod metrics: {e}")
            
        # 2. Temporal Workflows (Orchestration-based agents)
        try:
            # This would connect to Temporal API
            workflows = self._get_temporal_workflows()
            for workflow in workflows:
                agents.append({
                    "timestamp": timestamp,
                    "agent_name": workflow.get("workflow_id"),
                    "agent_type": "temporal_workflow",
                    "status": workflow.get("status", "unknown"),
                    "workflow_id": workflow.get("workflow_id"),
                    "success_rate": workflow.get("success_rate", 0.0),
                    "error_count": workflow.get("error_count", 0)
                })
        except Exception as e:
            logger.error(f"Error collecting workflow metrics: {e}")
            
        # 3. Memory Agents (Local inference agents)
        try:
            memory_agents = self._get_memory_agents()
            for agent in memory_agents:
                agents.append({
                    "timestamp": timestamp,
                    "agent_name": agent.get("name"),
                    "agent_type": "memory_agent",
                    "status": agent.get("status", "unknown"),
                    "memory_agent_id": agent.get("id"),
                    "success_rate": agent.get("success_rate", 0.0),
                    "error_count": agent.get("error_count", 0)
                })
        except Exception as e:
            logger.error(f"Error collecting memory agent metrics: {e}")
            
        return agents
        
    def collect_skill_metrics(self) -> List[Dict]:
        """Collect metrics from all skills"""
        skills = []
        timestamp = datetime.now().isoformat()
        
        skills_dir = Path("/Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/ai/skills")
        
        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                skill_data = self._parse_skill_md(skill_path / "SKILL.md")
                if skill_data:
                    skills.append({
                        "timestamp": timestamp,
                        "skill_name": skill_data.get("name"),
                        "skill_description": skill_data.get("description"),
                        "risk_level": skill_data.get("metadata", {}).get("risk_level"),
                        "autonomy_level": skill_data.get("metadata", {}).get("autonomy"),
                        "execution_count": skill_data.get("execution_count", 0),
                        "success_count": skill_data.get("success_count", 0),
                        "failure_count": skill_data.get("failure_count", 0),
                        "avg_execution_time": skill_data.get("avg_execution_time", 0.0)
                    })
                    
        return skills
        
    def _parse_skill_md(self, file_path: Path) -> Optional[Dict]:
        """Parse SKILL.md file and extract metadata"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    return frontmatter
                    
        except Exception as e:
            logger.error(f"Error parsing skill file {file_path}: {e}")
            
        return None
        
    def _get_pod_cpu_usage(self, pod_name: str) -> float:
        """Get CPU usage for a pod (placeholder implementation)"""
        # In real implementation, this would query metrics server
        return 0.0
        
    def _get_pod_memory_usage(self, pod_name: str) -> float:
        """Get memory usage for a pod (placeholder implementation)"""
        # In real implementation, this would query metrics server
        return 0.0
        
    def _get_temporal_workflows(self) -> List[Dict]:
        """Get Temporal workflow metrics (placeholder implementation)"""
        # In real implementation, this would query Temporal API
        return []
        
    def _get_memory_agents(self) -> List[Dict]:
        """Get memory agent metrics (placeholder implementation)"""
        # In real implementation, this would query memory agent endpoints
        return []

class FailureAnalyzer:
    def __init__(self, db_conn):
        self.db_conn = db_conn
        
    def analyze_failures(self, time_range_hours: int = 24) -> Dict:
        """Analyze failures and provide root cause analysis"""
        cursor = self.db_conn.cursor()
        
        # Get recent failures
        since_time = (datetime.now() - timedelta(hours=time_range_hours)).isoformat()
        cursor.execute('''
            SELECT * FROM failures 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC
        ''', (since_time,))
        
        failures = cursor.fetchall()
        
        # Analyze patterns
        error_types = {}
        agents_with_failures = {}
        
        for failure in failures:
            error_type = failure[4]  # error_type column
            agent_name = failure[2]   # agent_name column
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            agents_with_failures[agent_name] = agents_with_failures.get(agent_name, 0) + 1
            
        return {
            "total_failures": len(failures),
            "error_types": error_types,
            "agents_with_failures": agents_with_failures,
            "recent_failures": failures[:10]  # Last 10 failures
        }

# Initialize components
metrics_collector = MetricsCollector()
failure_analyzer = FailureAnalyzer(metrics_collector.db_conn)

# API Models
class AgentMetrics(BaseModel):
    timestamp: str
    agent_name: str
    agent_type: str
    status: str
    pod_name: Optional[str] = None
    workflow_id: Optional[str] = None
    memory_agent_id: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    success_rate: Optional[float] = None
    error_count: Optional[int] = None

class SkillMetrics(BaseModel):
    timestamp: str
    skill_name: str
    skill_description: Optional[str] = None
    risk_level: Optional[str] = None
    autonomy_level: Optional[str] = None
    execution_count: Optional[int] = None
    success_count: Optional[int] = None
    failure_count: Optional[int] = None
    avg_execution_time: Optional[float] = None

# API Endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v2/agents")
async def get_agents():
    """Get comprehensive agent metrics from all sources"""
    try:
        agents = metrics_collector.collect_agent_metrics()
        
        # Store in database for time-series
        cursor = metrics_collector.db_conn.cursor()
        for agent in agents:
            cursor.execute('''
                INSERT INTO agents 
                (timestamp, agent_name, agent_type, status, pod_name, workflow_id, 
                 memory_agent_id, cpu_usage, memory_usage, success_rate, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                agent["timestamp"], agent["agent_name"], agent["agent_type"], 
                agent["status"], agent.get("pod_name"), agent.get("workflow_id"),
                agent.get("memory_agent_id"), agent.get("cpu_usage"), 
                agent.get("memory_usage"), agent.get("success_rate"), 
                agent.get("error_count")
            ))
        metrics_collector.db_conn.commit()
        
        return {
            "agents": agents,
            "total_count": len(agents),
            "by_type": {
                "kubernetes_pods": len([a for a in agents if a["agent_type"] == "kubernetes_pod"]),
                "temporal_workflows": len([a for a in agents if a["agent_type"] == "temporal_workflow"]),
                "memory_agents": len([a for a in agents if a["agent_type"] == "memory_agent"])
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/skills")
async def get_skills():
    """Get detailed skill information with descriptions"""
    try:
        skills = metrics_collector.collect_skill_metrics()
        
        # Store in database
        cursor = metrics_collector.db_conn.cursor()
        for skill in skills:
            cursor.execute('''
                INSERT OR REPLACE INTO skills 
                (timestamp, skill_name, skill_description, risk_level, autonomy_level,
                 execution_count, success_count, failure_count, avg_execution_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill["timestamp"], skill["skill_name"], skill["skill_description"],
                skill["risk_level"], skill["autonomy_level"], skill["execution_count"],
                skill["success_count"], skill["failure_count"], skill["avg_execution_time"]
            ))
        metrics_collector.db_conn.commit()
        
        return {
            "skills": skills,
            "total_count": len(skills),
            "by_risk_level": {
                level: len([s for s in skills if s["risk_level"] == level])
                for level in set(s["risk_level"] for s in skills if s["risk_level"])
            },
            "by_autonomy_level": {
                level: len([s for s in skills if s["autonomy_level"] == level])
                for level in set(s["autonomy_level"] for s in skills if s["autonomy_level"])
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/metrics/timeseries")
async def get_timeseries_metrics(
    metric_type: str = "agents",
    time_range_hours: int = 24,
    interval_minutes: int = 60
):
    """Get time-series metrics data"""
    try:
        cursor = metrics_collector.db_conn.cursor()
        since_time = (datetime.now() - timedelta(hours=time_range_hours)).isoformat()
        
        if metric_type == "agents":
            cursor.execute('''
                SELECT timestamp, agent_type, status, COUNT(*) as count, AVG(success_rate) as avg_success_rate
                FROM agents 
                WHERE timestamp > ?
                GROUP BY timestamp, agent_type, status
                ORDER BY timestamp
            ''', (since_time,))
            
        elif metric_type == "skills":
            cursor.execute('''
                SELECT timestamp, risk_level, SUM(execution_count) as total_executions,
                       AVG(avg_execution_time) as avg_time
                FROM skills 
                WHERE timestamp > ?
                GROUP BY timestamp, risk_level
                ORDER BY timestamp
            ''', (since_time,))
            
        results = cursor.fetchall()
        
        return {
            "metric_type": metric_type,
            "time_range_hours": time_range_hours,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting timeseries metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/failures/analysis")
async def get_failure_analysis(time_range_hours: int = 24):
    """Get comprehensive failure analysis with root cause"""
    try:
        analysis = failure_analyzer.analyze_failures(time_range_hours)
        
        # Calculate success rate
        cursor = metrics_collector.db_conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as total_operations, SUM(error_count) as total_errors
            FROM agents 
            WHERE timestamp > ?
        ''', ((datetime.now() - timedelta(hours=time_range_hours)).isoformat(),))
        
        result = cursor.fetchone()
        total_operations = result[0] or 1
        total_errors = result[1] or 0
        
        success_rate = ((total_operations - total_errors) / total_operations) * 100
        
        return {
            "success_rate": round(success_rate, 2),
            "total_operations": total_operations,
            "total_errors": total_errors,
            "failure_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting failure analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/failures/report")
async def report_failure(
    agent_name: str,
    error_type: str,
    error_message: str,
    severity: str = "medium",
    skill_name: Optional[str] = None
):
    """Report a new failure for analysis"""
    try:
        cursor = metrics_collector.db_conn.cursor()
        cursor.execute('''
            INSERT INTO failures 
            (timestamp, agent_name, skill_name, error_type, error_message, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(), agent_name, skill_name, 
            error_type, error_message, severity
        ))
        metrics_collector.db_conn.commit()
        
        return {"status": "recorded", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error reporting failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
