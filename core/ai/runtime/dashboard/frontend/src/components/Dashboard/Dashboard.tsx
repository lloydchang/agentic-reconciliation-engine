import React, { useState, useEffect } from 'react';
import './Dashboard.css';
import SystemOverview from './SystemOverview';
import PerformanceMetrics from './PerformanceMetrics';
import SkillsDistribution from './SkillsDistribution';
import ActiveAgents from './ActiveAgents';
import AvailableSkills from './AvailableSkills';
import RecentActivity from './RecentActivity';
import SystemControls from './SystemControls';
import { ApiService } from '../../services/api';
import { WebSocketService } from '../../services/websocket';

interface SystemMetrics {
  agentMetrics: {
    total: number;
    running: number;
    idle: number;
    errored: number;
    stopped: number;
  };
  skillMetrics: {
    total: number;
    executions24h: number;
    successRate: number;
    avgDuration: number;
  };
  performance: {
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    networkIO: number;
  };
  timestamp: string;
}

interface Agent {
  id: string;
  name: string;
  language: string;
  status: string;
  backend: string;
  skills: string[];
  lastActivity?: string;
  successRate: number;
  createdAt: string;
  updatedAt: string;
}

interface Skill {
  id: string;
  name: string;
  description: string;
  license?: string;
  compatibility?: string;
  metadata: {
    risk_level: string;
    autonomy: string;
    layer: string;
    human_gate?: string;
  };
  createdAt: string;
}

interface Activity {
  id: string;
  type: string;
  agent: string;
  agentName: string;
  message: string;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const api = new ApiService();
    const ws = new WebSocketService();

    const fetchData = async () => {
      try {
        const [metricsData, agentsData, skillsData, activitiesData] = await Promise.all([
          api.getSystemMetrics(),
          api.getAgents(),
          api.getSkills(),
          api.getActivities()
        ]);

        setMetrics(metricsData);
        setAgents(agentsData);
        setSkills(skillsData);
        setActivities(activitiesData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up WebSocket listeners
    ws.on('agent_status', (agent: Agent) => {
      setAgents(prev => prev.map(a => a.id === agent.id ? agent : a));
    });

    ws.on('activity', (activity: Activity) => {
      setActivities(prev => [activity, ...prev.slice(0, 49)]);
    });

    ws.on('metrics', (newMetrics: SystemMetrics) => {
      setMetrics(newMetrics);
    });

    return () => {
      ws.disconnect();
    };
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-grid">
        <SystemOverview metrics={metrics} />
        <PerformanceMetrics metrics={metrics} />
        <SkillsDistribution skills={skills} />
      </div>

      <div className="dashboard-grid">
        <ActiveAgents agents={agents} />
        <AvailableSkills skills={skills} />
        <RecentActivity activities={activities} />
      </div>

      <div className="dashboard-grid full-width">
        <SystemControls agents={agents} />
      </div>
    </div>
  );
};

export default Dashboard;
