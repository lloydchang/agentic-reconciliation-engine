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

interface PerformanceMetricsProps {
  metrics: SystemMetrics | null;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics }) => {
  return (
    <div className="card">
      <h2 className="section-title">⚡ Performance Metrics</h2>
      <div className="chart-container">
        Performance Chart
      </div>
    </div>
  );
};

export default PerformanceMetrics;
