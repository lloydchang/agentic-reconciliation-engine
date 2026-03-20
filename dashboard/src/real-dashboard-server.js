#!/usr/bin/env node

/**
 * Real AI Infrastructure Dashboard Server
 * Serves the dashboard with real data from the API
 */

const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const PORT = 8081;

// Serve static files
app.use(express.static(path.join(__dirname)));

// Dashboard HTML with real data integration
const dashboardHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 AI Infrastructure Portal - Real Data</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #667eea;
        }
        
        .header p {
            color: #666;
            font-size: 1.2em;
        }
        
        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .services-section {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .service-card {
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .service-card:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .service-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .service-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }
        
        .service-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        
        .status-offline {
            background: #f8d7da;
            color: #721c24;
        }
        
        .service-url {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
        }
        
        .service-url:hover {
            text-decoration: underline;
        }
        
        .agents-section {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .agent-card {
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
        }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }
        
        .agent-type {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .agent-metrics {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 0.9em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
        }
        
        .metric-label {
            color: #666;
        }
        
        .metric-value {
            font-weight: bold;
            color: #333;
        }
        
        .activity-section {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .activity-feed {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .activity-item {
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-icon {
            font-size: 1.5em;
            margin-right: 15px;
        }
        
        .activity-content {
            flex: 1;
        }
        
        .activity-message {
            color: #333;
            margin-bottom: 5px;
        }
        
        .activity-time {
            color: #666;
            font-size: 0.9em;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: white;
            font-size: 0.9em;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Infrastructure Portal</h1>
            <p>Real-time monitoring and control of your AI services</p>
            <p style="font-size: 0.9em; color: #999; margin-top: 10px;">Last updated: <span id="lastUpdated">Loading...</span></p>
        </div>
        
        <div class="stats-overview">
            <div class="stat-card">
                <div class="stat-value" id="activeAgents">-</div>
                <div class="stat-label">Active Agents</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="successRate">-</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="skillsExecuted">-</div>
                <div class="stat-label">Skills Available</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="responseTime">-</div>
                <div class="stat-label">Avg Response Time</div>
            </div>
        </div>
        
        <div class="services-section">
            <div class="section-title">
                🔄 Service Status
                <button class="refresh-btn" onclick="loadServices()">Refresh</button>
            </div>
            <div id="servicesContainer" class="services-grid">
                <div class="loading">Loading services...</div>
            </div>
        </div>
        
        <div class="agents-section">
            <div class="section-title">
                🤖 Active Agents
                <button class="refresh-btn" onclick="loadAgents()">Refresh</button>
            </div>
            <div id="agentsContainer" class="agents-grid">
                <div class="loading">Loading agents...</div>
            </div>
        </div>
        
        <div class="activity-section">
            <div class="section-title">
                📊 Recent Activity
                <button class="refresh-btn" onclick="loadActivity()">Refresh</button>
            </div>
            <div id="activityContainer" class="activity-feed">
                <div class="loading">Loading activity...</div>
            </div>
        </div>
        
        <div class="footer">
            <p>🔧 Managed by Agentic Reconciliation Engine | Real Data API Connected</p>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:5000/api';
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(API_BASE + endpoint);
                if (!response.ok) throw new Error('Network response was not ok');
                return await response.json();
            } catch (error) {
                console.error('Error fetching data:', error);
                return null;
            }
        }
        
        function updateTimestamp() {
            document.getElementById('lastUpdated').textContent = new Date().toLocaleString();
        }
        
        async function loadServices() {
            const container = document.getElementById('servicesContainer');
            container.innerHTML = '<div class="loading">Loading services...</div>';
            
            const data = await fetchData('/services');
            if (!data) {
                container.innerHTML = '<div class="error">Failed to load services</div>';
                return;
            }
            
            const servicesHTML = Object.entries(data.services).map(([name, service]) => {
                return \`
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-name">\${name}</div>
                        <div class="service-status status-\${service.status}">\${service.status}</div>
                    </div>
                    <div>
                        <a href="\${service.url}" target="_blank" class="service-url">\${service.url}</a>
                    </div>
                </div>
            \`}).join('');
            
            container.innerHTML = servicesHTML;
        }
        
        async function loadAgents() {
            const container = document.getElementById('agentsContainer');
            container.innerHTML = '<div class="loading">Loading agents...</div>';
            
            const data = await fetchData('/agents');
            if (!data) {
                container.innerHTML = '<div class="error">Failed to load agents</div>';
                return;
            }
            
            const agentsHTML = data.agents.map(agent => {
                return \`
                <div class="agent-card">
                    <div class="agent-header">
                        <div class="agent-name">\${agent.name}</div>
                        <div class="service-status status-running">Running</div>
                    </div>
                    <div class="agent-type">\${agent.type}</div>
                    <div class="agent-metrics">
                        <div class="metric">
                            <span class="metric-label">Skills:</span>
                            <span class="metric-value">\${agent.skills}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Success Rate:</span>
                            <span class="metric-value">\${agent.successRate}%</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Memory:</span>
                            <span class="metric-value">\${agent.memoryUsage}MB</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Response Time:</span>
                            <span class="metric-value">\${agent.responseTime}s</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Last Activity:</span>
                            <span class="metric-value">\${agent.lastActivity}</span>
                        </div>
                    </div>
                </div>
            \`}).join('');
            
            container.innerHTML = agentsHTML;
            
            // Update overview stats
            document.getElementById('activeAgents').textContent = data.agents.length;
            const avgSuccessRate = (data.agents.reduce((sum, agent) => sum + agent.successRate, 0) / data.agents.length).toFixed(1);
            document.getElementById('successRate').textContent = avgSuccessRate + '%';
            const avgResponseTime = (data.agents.reduce((sum, agent) => sum + parseFloat(agent.responseTime), 0) / data.agents.length).toFixed(1);
            document.getElementById('responseTime').textContent = avgResponseTime + 's';
        }
        
        async function loadActivity() {
            const container = document.getElementById('activityContainer');
            container.innerHTML = '<div class="loading">Loading activity...</div>';
            
            const data = await fetchData('/activity');
            if (!data) {
                container.innerHTML = '<div class="error">Failed to load activity</div>';
                return;
            }
            
            const activityHTML = data.activities.map(activity => \`
                <div class="activity-item">
                    <div class="activity-icon">\${activity.icon}</div>
                    <div class="activity-content">
                        <div class="activity-message">\${activity.message}</div>
                        <div class="activity-time">\${activity.time}</div>
                    </div>
                </div>
            \`).join('');
            
            container.innerHTML = activityHTML;
        }
        
        async function loadSkills() {
            const data = await fetchData('/skills');
            if (data) {
                document.getElementById('skillsExecuted').textContent = data.skills.length;
            }
        }
        
        // Load all data
        async function loadAllData() {
            updateTimestamp();
            await Promise.all([
                loadServices(),
                loadAgents(),
                loadActivity(),
                loadSkills()
            ]);
        }
        
        // Initial load
        loadAllData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
`;

// Serve the dashboard
app.get('/', (req, res) => {
  res.send(dashboardHTML);
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Real AI Infrastructure Dashboard running on port ${PORT}`);
  console.log(`🌐 Dashboard URL: http://localhost:${PORT}`);
  console.log(`📊 Connected to Real Data API: http://localhost:5000`);
  console.log(`\n✨ This dashboard now shows REAL data instead of fake data!`);
});
