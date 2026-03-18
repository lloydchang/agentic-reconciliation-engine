#!/usr/bin/env node

const express = require('express');
const path = require('path');
const fs = require('fs');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Enable CORS
app.use(cors());
app.use(express.json());

// Serve static files
app.use(express.static(path.join(__dirname)));

// API endpoint for AI agents metrics
app.get('/api/metrics', async (req, res) => {
  try {
    // Simulate real AI agents metrics
    const metrics = {
      agents: {
        total: 72,
        active: 68,
        healthy: 65,
        failed: 3
      },
      skills: {
        'cost-optimizer': { status: 'healthy', executions: 1247, success_rate: 98.4 },
        'debug-system': { status: 'healthy', executions: 892, success_rate: 96.1 },
        'incident-triage': { status: 'healthy', executions: 445, success_rate: 94.2 },
        'cloud-compliance': { status: 'failed', executions: 0, success_rate: 0 },
        'knowledge-base': { status: 'healthy', executions: 2341, success_rate: 99.1 }
      },
      system: {
        uptime: '2d 14h 32m',
        memory_usage: 67.8,
        cpu_usage: 42.3,
        requests_per_minute: 147
      },
      temporal: {
        workflows_running: 12,
        workflows_completed_today: 1847,
        average_execution_time: '2.3s'
      }
    };
    
    res.json(metrics);
  } catch (error) {
    console.error('Error fetching metrics:', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

// API endpoint for RAG chatbot (supporting both endpoints)
app.post('/api/chat', async (req, res) => {
  await handleChatRequest(req, res);
});

app.post('/api/v1/rag/query', async (req, res) => {
  await handleChatRequest(req, res);
});

async function handleChatRequest(req, res) {
  try {
    const { message, query } = req.body;
    const userMessage = message || query || '';
    
    // Simulate RAG response with system data
    const responses = {
      'agents': 'There are currently 72 AI agents deployed in the system. 68 are active, 65 are healthy, and 3 have failed. The agents include cost-optimizer, debug-system, incident-triage, and knowledge-base skills.',
      'metrics': 'Current system metrics show 67.8% memory usage and 42.3% CPU usage. The system is processing 147 requests per minute with an average workflow execution time of 2.3 seconds.',
      'skills': 'The system supports 72+ different skills across categories like debugging, cost optimization, incident triage, and knowledge management. Each skill is designed to handle specific infrastructure operations.',
      'temporal': 'Temporal orchestration is currently running 12 workflows and has completed 1,847 workflows today. The system maintains high availability with automated workflow retry logic.',
      'hi': 'Hello! I\'m your AI assistant powered by RAG (Retrieval-Augmented Generation). I can help you with information about the AI agents, cluster status, skills, and system performance. What would you like to know?',
      'hello': 'Hello! I\'m your AI assistant powered by RAG (Retrieval-Augmented Generation). I can help you with information about the AI agents, cluster status, skills, and system performance. What would you like to know?',
      'bye': 'Goodbye! Feel free to ask me anything about your GitOps infrastructure when you return.',
      'default': 'I can help you with information about AI agents, system metrics, available skills, and Temporal orchestration. What would you like to know?'
    };
    
    // Simple keyword matching for demo
    let response = responses.default;
    for (const [key, value] of Object.entries(responses)) {
      if (userMessage.toLowerCase().includes(key)) {
        response = value;
        break;
      }
    }
    
    res.json({
      response,
      sources: [
        { type: 'system-metrics', confidence: 0.95 },
        { type: 'agent-status', confidence: 0.98 },
        { type: 'skill-registry', confidence: 0.92 }
      ]
    });
  } catch (error) {
    console.error('Error processing chat:', error);
    res.status(500).json({ error: 'Failed to process message' });
  }
}

// API endpoint for agent logs
app.get('/api/logs', (req, res) => {
  try {
    const logs = [
      { timestamp: new Date().toISOString(), level: 'INFO', agent: 'cost-optimizer', message: 'Successfully analyzed AWS spend patterns' },
      { timestamp: new Date(Date.now() - 60000).toISOString(), level: 'WARN', agent: 'debug-system', message: 'High memory usage detected in pod memory-optimizer-xyz' },
      { timestamp: new Date(Date.now() - 120000).toISOString(), level: 'INFO', agent: 'incident-triage', message: 'New incident created: POD-2024-001' },
      { timestamp: new Date(Date.now() - 180000).toISOString(), level: 'ERROR', agent: 'cloud-compliance', message: 'Failed to connect to compliance database' },
      { timestamp: new Date(Date.now() - 240000).toISOString(), level: 'INFO', agent: 'knowledge-base', message: 'Indexed 245 new infrastructure documents' }
    ];
    
    res.json(logs);
  } catch (error) {
    console.error('Error fetching logs:', error);
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
});

// Serve the main dashboard
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'dashboard-index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 AI Agents Dashboard running at http://localhost:${PORT}`);
  console.log(`📊 Metrics API available at http://localhost:${PORT}/api/metrics`);
  console.log(`💬 Chat API available at http://localhost:${PORT}/api/chat`);
  console.log(`📋 Logs API available at http://localhost:${PORT}/api/logs`);
});
