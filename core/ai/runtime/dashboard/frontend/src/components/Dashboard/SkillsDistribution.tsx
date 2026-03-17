import React from 'react';

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

interface SkillsDistributionProps {
  skills: Skill[];
}

const SkillsDistribution: React.FC<SkillsDistributionProps> = ({ skills }) => {
  return (
    <div className="card">
      <h2 className="section-title">🎯 Skills Distribution</h2>
      <div className="chart-container">
        Skills Chart
      </div>
    </div>
  );
};

export default SkillsDistribution;
