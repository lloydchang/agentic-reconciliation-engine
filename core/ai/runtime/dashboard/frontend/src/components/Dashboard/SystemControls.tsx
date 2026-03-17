import React from 'react';

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

interface SystemControlsProps {
  agents: Agent[];
}

const SystemControls: React.FC<SystemControlsProps> = ({ agents }) => {
  const handleDeployAll = () => {
    console.log('Deploy all agents');
  };

  const handleStopAll = () => {
    console.log('Stop all agents');
  };

  const handleRestartSystem = () => {
    console.log('Restart system');
  };

  const handleExportLogs = () => {
    console.log('Export logs');
  };

  const handleSettings = () => {
    console.log('Open settings');
  };

  return (
    <div className="card">
      <h2 className="section-title">🎛️ System Controls</h2>
      <div className="controls-grid">
        <button className="btn" onClick={handleDeployAll}>
          Deploy All Agents
        </button>
        <button className="btn" onClick={handleStopAll}>
          Stop All Agents
        </button>
        <button className="btn" onClick={handleRestartSystem}>
          Restart System
        </button>
        <button className="btn" onClick={handleExportLogs}>
          Export Logs
        </button>
        <button className="btn" onClick={handleSettings}>
          Settings
        </button>
      </div>
    </div>
  );
};

export default SystemControls;
