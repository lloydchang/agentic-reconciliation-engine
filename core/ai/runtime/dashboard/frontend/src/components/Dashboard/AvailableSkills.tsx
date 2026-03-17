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

interface AvailableSkillsProps {
  skills: Skill[];
}

const AvailableSkills: React.FC<AvailableSkillsProps> = ({ skills }) => {
  const getDisplayName = (name: string) => {
    return name.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <div className="card">
      <h2 className="section-title">🛠️ Available Skills</h2>
      <div className="skills-grid">
        {skills.slice(0, 12).map((skill) => (
          <div key={skill.id} className="skill-item">
            {getDisplayName(skill.name)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AvailableSkills;
