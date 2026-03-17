import React from 'react';

interface Activity {
  id: string;
  type: string;
  agent: string;
  agentName: string;
  message: string;
  timestamp: string;
}

interface RecentActivityProps {
  activities: Activity[];
}

const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return '🚀';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffMinutes < 60) {
      return `${diffMinutes} min ago`;
    } else if (diffMinutes < 1440) {
      return `${Math.floor(diffMinutes / 60)} min ago`;
    } else {
      return `${Math.floor(diffMinutes / 1440)} min ago`;
    }
  };

  return (
    <div className="card">
      <h2 className="section-title">📋 Recent Activity</h2>
      <div className="activity-feed">
        {activities.slice(0, 5).map((activity) => (
          <div key={activity.id} className="activity-item">
            {getActivityIcon(activity.type)} {formatTime(activity.timestamp)} - {activity.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivity;
