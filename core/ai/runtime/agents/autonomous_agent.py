#!/usr/bin/env python3
"""
Autonomous Agent Implementation for Agentic Reconciliation Engine
This agent operates autonomously, reading K8s cluster info, AGENTS.md, and SKILL.md files
"""

import os
import sys
import json
import yaml
import sqlite3
import subprocess
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AutonomousAgent')


class AutonomousAgent:
    """
    Autonomous agent that:
    1. Reads Kubernetes cluster information
    2. Parses AGENTS.md for policies and behavior rules
    3. Loads SKILL.md files for capabilities
    4. Executes escalation and non-escalation workflows
    5. Maintains persistent memory via SQLite
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.namespace = self.config.get('namespace', 'ai-infrastructure')
        self.memory_db_path = self.config.get('memory_db', '/data/memory.db')
        self.skills_dir = self.config.get('skills_dir', '/app/skills')
        self.agents_md_path = self.config.get('agents_md', '/app/agents/AGENTS.md')
        
        # Initialize memory storage
        self._init_memory_db()
        
        # Load configuration
        self.agents_config = self._load_agents_md()
        self.skills = self._load_skills()
        
        # Runtime state
        self.running = False
        self.escalation_queue = []
        self.activity_log = []
        
        logger.info(f"Autonomous Agent initialized with {len(self.skills)} skills")
    
    def _init_memory_db(self):
        """Initialize SQLite memory database"""
        os.makedirs(os.path.dirname(self.memory_db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.memory_db_path)
        cursor = conn.cursor()
        
        # Create memory tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                context TEXT,
                outcome TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT NOT NULL,
                entity_type TEXT,
                properties TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS procedural_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                parameters TEXT,
                execution_time TEXT,
                success BOOLEAN,
                outcome TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                key TEXT,
                value TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Memory database initialized at {self.memory_db_path}")
    
    def _load_agents_md(self) -> Dict[str, Any]:
        """Load and parse AGENTS.md configuration"""
        config = {
            'layers': ['memory', 'temporal', 'gitops', 'pi-mono'],
            'autonomy_levels': ['fully_auto', 'conditional', 'human_gate'],
            'risk_levels': ['low', 'medium', 'high'],
            'escalation_loop': {
                'observe': True,
                'recall': True,
                'select': True,
                'execute': True,
                'commit': True
            }
        }
        
        if os.path.exists(self.agents_md_path):
            try:
                with open(self.agents_md_path, 'r') as f:
                    content = f.read()
                    # Parse YAML frontmatter if present
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            if frontmatter:
                                config.update(frontmatter)
                logger.info(f"Loaded AGENTS.md from {self.agents_md_path}")
            except Exception as e:
                logger.warning(f"Failed to parse AGENTS.md: {e}")
        else:
            logger.warning(f"AGENTS.md not found at {self.agents_md_path}")
        
        return config
    
    def _load_skills(self) -> List[Dict[str, Any]]:
        """Load all SKILL.md files from skills directory"""
        skills = []
        
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return skills
        
        for skill_dir in Path(self.skills_dir).iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / 'SKILL.md'
                if skill_md.exists():
                    try:
                        with open(skill_md, 'r') as f:
                            content = f.read()
                            skill = self._parse_skill_md(content, skill_dir.name)
                            if skill:
                                skills.append(skill)
                    except Exception as e:
                        logger.warning(f"Failed to load skill {skill_dir.name}: {e}")
        
        logger.info(f"Loaded {len(skills)} skills from {self.skills_dir}")
        return skills
    
    def _parse_skill_md(self, content: str, skill_name: str) -> Optional[Dict[str, Any]]:
        """Parse SKILL.md frontmatter and content"""
        skill = {'name': skill_name}
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    if frontmatter:
                        skill.update(frontmatter)
                        # Determine if escalation skill
                        skill['escalation'] = self._is_escalation_skill(skill)
                except yaml.YAMLError as e:
                    logger.warning(f"YAML parse error in {skill_name}: {e}")
        
        return skill
    
    def _is_escalation_skill(self, skill: Dict[str, Any]) -> bool:
        """Determine if a skill is escalation-based"""
        escalation_keywords = [
            'troubleshoot', 'remediate', 'incident', 'escalation',
            'security', 'audit', 'predict', 'disaster', 'recover'
        ]
        
        # Check description and name for keywords
        text = f"{skill.get('name', '')} {skill.get('description', '')}".lower()
        return any(kw in text for kw in escalation_keywords)
    
    def run_kubectl(self, command: str, timeout: int = 30) -> tuple:
        """Execute kubectl command safely"""
        try:
            result = subprocess.run(
                f"kubectl {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip(), result.returncode == 0
        except subprocess.TimeoutExpired:
            return "", False
        except Exception as e:
            logger.error(f"kubectl error: {e}")
            return "", False
    
    def observe_cluster(self) -> Dict[str, Any]:
        """Observe Kubernetes cluster state (Escalation Loop Step 1)"""
        observations = {
            'timestamp': datetime.now().isoformat(),
            'nodes': [],
            'pods': [],
            'events': [],
            'errors': [],
            'warnings': []
        }
        
        # Get nodes
        output, success = self.run_kubectl("get nodes -o json")
        if success and output:
            try:
                data = json.loads(output)
                for node in data.get('items', []):
                    observations['nodes'].append({
                        'name': node['metadata']['name'],
                        'status': node['status']['conditions'][-1]['type'] if node['status']['conditions'] else 'Unknown',
                        'ready': any(c['type'] == 'Ready' and c['status'] == 'True' for c in node['status'].get('conditions', []))
                    })
            except json.JSONDecodeError:
                pass
        
        # Get pods in namespace
        output, success = self.run_kubectl(f"get pods -n {self.namespace} -o json")
        if success and output:
            try:
                data = json.loads(output)
                for pod in data.get('items', []):
                    pod_info = {
                        'name': pod['metadata']['name'],
                        'namespace': pod['metadata']['namespace'],
                        'phase': pod['status']['phase'],
                        'ready': False
                    }
                    
                    # Check ready status
                    for container_status in pod['status'].get('containerStatuses', []):
                        if container_status.get('ready'):
                            pod_info['ready'] = True
                            break
                    
                    observations['pods'].append(pod_info)
                    
                    # Track errors
                    if pod_info['phase'] not in ['Running', 'Succeeded']:
                        observations['errors'].append(f"Pod {pod_info['name']} in {pod_info['phase']} state")
            except json.JSONDecodeError:
                pass
        
        # Get recent events
        output, success = self.run_kubectl(f"get events -n {self.namespace} --sort-by='.lastTimestamp' --limit=20 -o json")
        if success and output:
            try:
                data = json.loads(output)
                for event in data.get('items', []):
                    event_info = {
                        'type': event.get('type', 'Normal'),
                        'reason': event.get('reason', ''),
                        'message': event.get('message', ''),
                        'count': event.get('count', 1),
                        'source': event.get('source', {}).get('component', 'unknown')
                    }
                    observations['events'].append(event_info)
                    
                    if event_info['type'] == 'Warning':
                        observations['warnings'].append(event_info['message'])
            except json.JSONDecodeError:
                pass
        
        # Store observation in episodic memory
        self._store_memory('episodic', {
            'event_type': 'cluster_observation',
            'description': f"Observed {len(observations['nodes'])} nodes, {len(observations['pods'])} pods",
            'context': json.dumps(observations),
            'outcome': 'success' if not observations['errors'] else 'issues_detected'
        })
        
        return observations
    
    def recall_context(self, query: str) -> List[Dict[str, Any]]:
        """Recall historical context from memory (Escalation Loop Step 2)"""
        results = []
        
        conn = sqlite3.connect(self.memory_db_path)
        cursor = conn.cursor()
        
        # Search episodic memory
        cursor.execute('''
            SELECT * FROM episodic_memory 
            WHERE description LIKE ? OR context LIKE ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append({
                'type': 'episodic',
                'id': row[0],
                'timestamp': row[1],
                'event_type': row[2],
                'description': row[3],
                'context': row[4]
            })
        
        # Search procedural memory for skill outcomes
        cursor.execute('''
            SELECT * FROM procedural_memory 
            WHERE skill_name LIKE ? OR outcome LIKE ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append({
                'type': 'procedural',
                'id': row[0],
                'skill_name': row[1],
                'success': row[4],
                'outcome': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        
        logger.info(f"Recalled {len(results)} memories for query: {query}")
        return results
    
    def select_skill(self, error_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Select appropriate skill based on error context (Escalation Loop Step 3)"""
        # Extract error characteristics
        error_type = error_context.get('type', 'unknown')
        error_message = error_context.get('message', '').lower()
        
        # Score skills based on relevance
        scored_skills = []
        for skill in self.skills:
            score = 0
            
            # Check trigger keywords
            keywords = skill.get('trigger_keywords', [])
            if isinstance(keywords, list):
                for kw in keywords:
                    if kw.lower() in error_message:
                        score += 10
            
            # Check risk level appropriateness
            risk = skill.get('risk_level', 'medium')
            if error_type in ['critical', 'error'] and risk in ['medium', 'high']:
                score += 5
            elif error_type in ['warning'] and risk == 'low':
                score += 5
            
            # Prefer escalation skills for errors
            if skill.get('escalation') and error_type in ['error', 'critical']:
                score += 8
            
            # Check autonomy level
            autonomy = skill.get('autonomy', 'conditional')
            if autonomy == 'fully_auto':
                score += 3  # Prefer autonomous skills
            
            scored_skills.append((skill, score))
        
        # Sort by score and return best match
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        
        if scored_skills and scored_skills[0][1] > 0:
            selected = scored_skills[0][0]
            logger.info(f"Selected skill: {selected.get('name')} (score: {scored_skills[0][1]})")
            return selected
        
        return None
    
    def execute_skill(self, skill: Dict[str, Any], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a skill via Temporal workflow (Escalation Loop Step 4)"""
        result = {
            'skill': skill.get('name'),
            'status': 'initiated',
            'timestamp': datetime.now().isoformat(),
            'workflow_id': None,
            'outcome': None
        }
        
        params = params or {}
        
        # In production, this would trigger a Temporal workflow
        # For now, we simulate execution
        
        # Check autonomy level
        autonomy = skill.get('autonomy', 'conditional')
        if autonomy == 'human_gate':
            result['status'] = 'awaiting_approval'
            result['message'] = 'Human approval required for this skill'
            logger.warning(f"Skill {skill.get('name')} requires human approval")
        else:
            result['status'] = 'executing'
            result['workflow_id'] = f"wf-{int(time.time())}"
            
            # Simulate skill execution
            if skill.get('name') == 'debug':
                result['outcome'] = self._execute_debug_skill(params)
            elif skill.get('name') == 'check-cluster-health':
                result['outcome'] = self._execute_health_check(params)
            else:
                result['outcome'] = {'message': 'Skill executed successfully'}
            
            result['status'] = 'completed'
        
        # Store execution in procedural memory
        self._store_memory('procedural', {
            'skill_name': skill.get('name'),
            'parameters': json.dumps(params),
            'success': result['status'] == 'completed',
            'outcome': json.dumps(result['outcome'])
        })
        
        return result
    
    def commit_result(self, result: Dict[str, Any]) -> bool:
        """Commit result to memory (Escalation Loop Step 5)"""
        try:
            # Store in episodic memory
            self._store_memory('episodic', {
                'event_type': 'skill_execution',
                'description': f"Executed {result.get('skill', 'unknown')} skill",
                'context': json.dumps(result),
                'outcome': result.get('status', 'unknown')
            })
            
            # Update semantic memory with learned concepts
            if result.get('outcome'):
                self._update_semantic_memory(result)
            
            logger.info(f"Committed result for skill {result.get('skill')}")
            return True
        except Exception as e:
            logger.error(f"Failed to commit result: {e}")
            return False
    
    def _store_memory(self, memory_type: str, data: Dict[str, Any]):
        """Store data in specified memory type"""
        conn = sqlite3.connect(self.memory_db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        if memory_type == 'episodic':
            cursor.execute('''
                INSERT INTO episodic_memory (timestamp, event_type, description, context, outcome)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, data.get('event_type', ''), data.get('description', ''),
                  data.get('context', ''), data.get('outcome', '')))
        
        elif memory_type == 'procedural':
            cursor.execute('''
                INSERT INTO procedural_memory (skill_name, parameters, execution_time, success, outcome, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data.get('skill_name', ''), data.get('parameters', ''),
                  data.get('execution_time', ''), data.get('success', False),
                  data.get('outcome', ''), timestamp))
        
        elif memory_type == 'semantic':
            cursor.execute('''
                INSERT OR REPLACE INTO semantic_memory (concept, entity_type, properties, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (data.get('concept', ''), data.get('entity_type', ''),
                  json.dumps(data.get('properties', {})), timestamp, timestamp))
        
        conn.commit()
        conn.close()
    
    def _update_semantic_memory(self, result: Dict[str, Any]):
        """Update semantic memory with learned concepts"""
        skill = result.get('skill', 'unknown')
        outcome = result.get('outcome', {})
        
        # Extract concepts from outcome
        if isinstance(outcome, dict):
            for key, value in outcome.items():
                self._store_memory('semantic', {
                    'concept': f"{skill}:{key}",
                    'entity_type': 'skill_outcome',
                    'properties': {'value': value}
                })
    
    def _execute_debug_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute debug skill"""
        observations = self.observe_cluster()
        return {
            'findings': observations.get('errors', []),
            'warnings': observations.get('warnings', []),
            'recommendations': ['Check pod logs', 'Review events', 'Verify resource limits']
        }
    
    def _execute_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute health check skill"""
        observations = self.observe_cluster()
        
        health_score = 100
        if observations['errors']:
            health_score -= len(observations['errors']) * 10
        if observations['warnings']:
            health_score -= len(observations['warnings']) * 5
        
        return {
            'health_score': max(0, health_score),
            'nodes_healthy': sum(1 for n in observations['nodes'] if n['ready']),
            'pods_running': sum(1 for p in observations['pods'] if p['phase'] == 'Running'),
            'issues': observations['errors'] + observations['warnings']
        }
    
    def run_escalation_loop(self):
        """Run the complete escalation loop"""
        logger.info("Starting escalation loop...")
        
        # Step 1: Observe
        observations = self.observe_cluster()
        
        if not observations['errors'] and not observations['warnings']:
            logger.info("No issues detected in observation phase")
            return None
        
        # Step 2: Recall
        context = self.recall_context(' '.join(observations['errors'][:3]))
        logger.info(f"Recalled {len(context)} relevant memories")
        
        # Step 3: Select
        error_context = {
            'type': 'error' if observations['errors'] else 'warning',
            'message': ' '.join(observations['errors'] + observations['warnings'])
        }
        skill = self.select_skill(error_context)
        
        if not skill:
            logger.warning("No suitable skill found for error context")
            return None
        
        # Step 4: Execute
        result = self.execute_skill(skill, {'observations': observations})
        
        # Step 5: Commit
        self.commit_result(result)
        
        logger.info(f"Escalation loop completed: {result['status']}")
        return result
    
    def run_continuous(self, interval: int = 60):
        """Run agent continuously with periodic checks"""
        self.running = True
        
        def loop():
            while self.running:
                try:
                    # Run escalation loop
                    self.run_escalation_loop()
                    
                    # Log activity
                    self.activity_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': 'escalation_check',
                        'status': 'completed'
                    })
                    
                except Exception as e:
                    logger.error(f"Error in continuous loop: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=loop, daemon=True)
        thread.start()
        logger.info(f"Started continuous operation with {interval}s interval")
    
    def stop(self):
        """Stop continuous operation"""
        self.running = False
        logger.info("Agent stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'running': self.running,
            'skills_loaded': len(self.skills),
            'escalation_skills': sum(1 for s in self.skills if s.get('escalation')),
            'memory_db': self.memory_db_path,
            'namespace': self.namespace,
            'recent_activities': self.activity_log[-10:],
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Main entry point for autonomous agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous Agent for Agentic Reconciliation Engine')
    parser.add_argument('--namespace', default='ai-infrastructure', help='Kubernetes namespace')
    parser.add_argument('--memory-db', default='/data/memory.db', help='Path to memory database')
    parser.add_argument('--skills-dir', default='/app/skills', help='Directory containing skills')
    parser.add_argument('--agents-md', default='/app/agents/AGENTS.md', help='Path to AGENTS.md')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    config = {
        'namespace': args.namespace,
        'memory_db': args.memory_db,
        'skills_dir': args.skills_dir,
        'agents_md': args.agents_md
    }
    
    agent = AutonomousAgent(config)
    
    if args.once:
        # Run single escalation loop
        result = agent.run_escalation_loop()
        print(json.dumps(result or {'status': 'no_issues'}, indent=2))
    else:
        # Run continuously
        agent.run_continuous(args.interval)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.stop()
            print("\nAgent stopped")


if __name__ == '__main__':
    main()
