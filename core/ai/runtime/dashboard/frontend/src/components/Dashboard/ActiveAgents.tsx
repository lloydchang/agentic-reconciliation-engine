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

interface ActiveAgentsProps {
  agents: Agent[];
}

const ActiveAgents: React.FC<ActiveAgentsProps> = ({ agents }) => {
  const getLanguageColor = (language: string) => {
    switch (language.toLowerCase()) {
      case 'rust': return 'rust';
      case 'go': return 'go';
      case 'python': return 'python';
      default: return 'rust';
    }
  };

  const getLanguageLetter = (language: string) => {
    switch (language.toLowerCase()) {
      case 'rust': return 'R';
      case 'go': return 'G';
      case 'python': return 'P';
      default: return 'R';
    }
  };

  const formatLastActivity = (lastActivity?: string) => {
    if (!lastActivity) return 'Never';
    const date = new Date(lastActivity);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffMinutes < 60) {
      return `${diffMinutes} min ago`;
    } else if (diffMinutes < 1440) {
      return `${Math.floor(diffMinutes / 60)} hours ago`;
    } else {
      return `${Math.floor(diffMinutes / 1440)} days ago`;
    }
  };

  return (
    <div className="card">
      <h2 className="section-title">🤖 Active Agents</h2>
      <div className="agents-list">
        {agents.map((agent) => (
          <div key={agent.id} className="agent-item">
            <div className={`agent-avatar ${getLanguageColor(agent.language)}`}>
              {getLanguageLetter(agent.language)}
            </div>
            <div className="agent-info">
              <div className="agent-name">{agent.name}</div>
              <div className="agent-details">
                {agent.language} • {agent.skills.length} skills • Last: {formatLastActivity(agent.lastActivity)}
              </div>
            </div>
            <div className="agent-success-rate">{agent.successRate.toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActiveAgents;
