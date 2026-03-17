import React from 'react';

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

interface SystemOverviewProps {
  metrics: SystemMetrics | null;
}

const SystemOverview: React.FC<SystemOverviewProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="card">
        <h2 className="section-title">📊 System Overview</h2>
        <div className="metrics-grid">
          <div className="metric">
            <div className="metric-value">-</div>
            <div className="metric-label">Total Agents</div>
          </div>
          <div className="metric">
            <div className="metric-value">-</div>
            <div className="metric-label">Active Skills</div>
          </div>
          <div className="metric">
            <div className="metric-value">-</div>
            <div className="metric-label">Success Rate</div>
          </div>
        </div>
      </div>
    );
  }

  const agentChange = metrics.agentMetrics.running > 2 ? "+2 this hour" : "+1 this hour";
  const skillChange = "+15% today";
  const successChange = "+5% today";

  return (
    <div className="card">
      <h2 className="section-title">📊 System Overview</h2>
      <div className="metrics-grid">
        <div className="metric">
          <div className="metric-value">{metrics.agentMetrics.total}</div>
          <div className="metric-label">Total Agents</div>
          <div className="metric-change">{agentChange}</div>
        </div>
        <div className="metric">
          <div className="metric-value">{metrics.skillMetrics.total}</div>
          <div className="metric-label">Active Skills</div>
          <div className="metric-change">{skillChange}</div>
        </div>
        <div className="metric">
          <div className="metric-value">{metrics.skillMetrics.successRate.toFixed(1)}%</div>
          <div className="metric-label">Success Rate</div>
          <div className="metric-change">{successChange}</div>
        </div>
      </div>
    </div>
  );
};

export default SystemOverview;
