# AI Agents Dashboard Guide

## Overview

The AI Agents Dashboard is a comprehensive web-based control center that provides real-time monitoring, management, and control capabilities for the Cloud AI Agents ecosystem. It offers a modern, responsive interface comparable to commercial AI agent platforms.

## Features

### 📊 Real-time Monitoring
- **System Overview**: Live metrics for total agents, active skills, and success rates
- **Performance Metrics**: Response time trends and system performance charts
- **Skills Distribution**: Visual breakdown of skill categories and usage
- **Activity Feed**: Real-time timeline of agent activities and events

### 🤖 Agent Management
- **Visual Agent Cards**: Display agent status, type, performance metrics
- **Multi-language Support**: Shows Rust, Go, and Python agents
- **Performance Tracking**: Success rates, skill counts, last activity
- **Agent Controls**: Add, deploy, stop, and restart agents

### 🛠️ Interactive Skills Grid
- **16+ Available Skills**: Cost Analysis, Security Audit, Cluster Health, etc.
- **Click-to-Execute**: Direct skill execution from dashboard
- **Visual Categories**: Color-coded skill types
- **Real-time Updates**: Live skill status and availability

### 🎛️ System Controls
- **Deploy All Agents**: One-click deployment of entire agent fleet
- **Stop All Agents**: Emergency stop capability
- **System Restart**: Full system reboot with confirmation
- **Log Export**: Download system logs for analysis
- **Settings Panel**: Configuration and preferences

## Architecture

### Frontend Components
- **React-based UI**: Modern component architecture
- **Chart.js Integration**: Interactive data visualization
- **Feather Icons**: Consistent icon system
- **Responsive Design**: Mobile and desktop optimized

### Backend Services
- **Dashboard API**: Flask-based REST API (`dashboard-api-service`)
- **Metrics Collection**: Real-time data aggregation
- **Agent Communication**: Direct integration with AI agents
- **WebSocket Updates**: Live data streaming (planned)

### Kubernetes Integration
- **Deployment**: `agent-dashboard` deployment with nginx
- **Service**: `agent-dashboard-service` for internal access
- **ConfigMap**: `agent-dashboard-config` for HTML/CSS/JS
- **Ingress**: External access routing

## Installation and Deployment

### Prerequisites
- Kubernetes cluster with `ai-infrastructure` namespace
- Deployed AI agents ecosystem
- NGINX ingress controller (for external access)

### Deploy Dashboard
```bash
# Deploy using the ecosystem script
./core/core/automation/ci-cd/scripts/deploy-ai-agents-ecosystem.sh

# Or deploy dashboard only
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-dashboard
  namespace: ai-infrastructure
spec:
  # ... deployment config
EOF
```

### Access Dashboard

#### Port Forward (Development)
```bash
kubectl port-forward svc/agent-dashboard-service 8888:80 -n ai-infrastructure
# Access at http://localhost:8888
```

#### Ingress (Production)
```bash
# Add to /etc/hosts
echo "127.0.0.1 dashboard.local" >> /etc/hosts

# Access at http://dashboard.local
```

## User Interface Guide

### Dashboard Layout

#### Header Section
- **Logo**: "🚀 Cloud AI Agents Control Center"
- **System Status**: Online/Offline indicator with real-time status

#### Metrics Cards
- **System Overview**: Total agents, active skills, success rate
- **Performance Charts**: Response time trends
- **Skills Distribution**: Doughnut chart of skill categories

#### Agent Management Panel
- **Agent List**: Individual agent cards with avatars
- **Status Indicators**: Running (green), Idle (yellow), Error (red)
- **Performance Metrics**: Success rates and activity timestamps

#### Skills Grid
- **Interactive Tiles**: Clickable skill buttons
- **Hover Effects**: Visual feedback on interaction
- **Categories**: Organized by function (Cost, Security, Monitoring, etc.)

#### Activity Feed
- **Timeline View**: Chronological activity display
- **Event Types**: Success (✅), Warning (⚠️), Error (❌), Info (📊)
- **Timestamps**: Relative time display (e.g., "2 min ago")

#### Control Panel
- **Deploy Controls**: System-wide agent management
- **Maintenance Tools**: Restart, log export, settings
- **Confirmation Dialogs**: Safety confirmations for destructive actions

## API Integration

### Dashboard API Endpoints

#### Cluster Status
```http
GET /api/cluster-status
Response: {"status": "healthy", "message": "Cluster is operational"}
```

#### Agent Status
```http
GET /api/core/ai/runtime/status
Response: {"agent_count": 3, "skills_executed": 42}
```

#### Agent List
```http
GET /api/agents
Response: {
  "agents": [
    {
      "id": "agent-1",
      "name": "Cost Optimizer",
      "type": "Rust",
      "status": "running",
      "skills": 12,
      "successRate": 98.5
    }
  ]
}
```

#### Skills List
```http
GET /api/skills
Response: {
  "skills": ["Cost Analysis", "Security Audit", "Cluster Health", ...]
}
```

#### Activity Feed
```http
GET /api/activity
Response: {
  "activities": [
    {
      "time": "2 min ago",
      "type": "success",
      "icon": "🚀",
      "message": "Cost Optimizer completed analysis"
    }
  ]
}
```

## Customization

### Adding New Skills
```javascript
// In dashboard HTML
function generateMockSkills() {
  return [
    'Cost Analysis', 'Security Audit', 'Cluster Health',
    'New Custom Skill', // Add new skill here
    // ... other skills
  ];
}
```

### Custom Metrics
```javascript
// Add new metric cards
<div class="metric">
  <div>
    <div class="metric-value" id="custom-metric">0</div>
    <div class="metric-label">Custom Metric</div>
  </div>
</div>
```

### Theme Customization
```css
:root {
  --primary: #6366f1;     /* Change primary color */
  --secondary: #8b5cf6;   /* Change secondary color */
  --success: #10b981;     /* Change success color */
  /* ... other color variables */
}
```

## Monitoring and Troubleshooting

### Dashboard Logs
```bash
# View dashboard pod logs
kubectl logs -n ai-infrastructure deployment/agent-dashboard

# View API service logs
kubectl logs -n ai-infrastructure deployment/dashboard-api
```

### Common Issues

#### Dashboard Not Loading
```bash
# Check pod status
kubectl get pods -n ai-infrastructure -l component=agent-dashboard

# Check service
kubectl get svc -n ai-infrastructure agent-dashboard-service

# Restart dashboard
kubectl rollout restart deployment/agent-dashboard -n ai-infrastructure
```

#### API Not Responding
```bash
# Check API pod
kubectl get pods -n ai-infrastructure -l component=dashboard-api

# Test API endpoint
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure
curl http://localhost:5000/api/cluster-status
```

#### Metrics Not Updating
```bash
# Check agent connectivity
kubectl get pods -n ai-infrastructure -l component=memory-agent

# Verify agent API endpoints
kubectl port-forward svc/memory-agent-service 8080:80 -n ai-infrastructure
curl http://localhost:8080/health
```

## Security Considerations

### Authentication (Future Enhancement)
- OAuth 2.0 integration planned
- Role-based access control
- API key authentication

### Network Security
- Internal cluster communication only
- Ingress TLS termination
- Network policies for isolation

### Data Protection
- No sensitive data in browser storage
- Encrypted API communications
- Audit logging for all actions

## Performance Optimization

### Frontend Optimization
- Lazy loading for large datasets
- Debounced API calls
- Efficient chart rendering
- Minimal bundle size

### Backend Optimization
- Cached API responses
- Efficient database queries
- Connection pooling
- Horizontal scaling support

### Resource Limits
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

## Future Enhancements

### Planned Features
- **Real-time WebSocket Updates**: Live data streaming
- **Advanced Analytics**: Historical data analysis
- **Custom Dashboards**: User-configurable layouts
- **Alert Management**: Integration with monitoring system
- **Multi-cluster Support**: Cross-cluster dashboard
- **Mobile App**: Native mobile application

### API Enhancements
- GraphQL endpoint for complex queries
- Streaming API for real-time updates
- Authentication and authorization
- Rate limiting and throttling

### UI/UX Improvements
- Dark mode support
- Accessibility improvements
- Internationalization (i18n)
- Customizable themes

## Integration with Other Systems

### Monitoring Integration
- Prometheus metrics export
- Grafana dashboard templates
- Alertmanager integration

### CI/CD Integration
- Deployment status display
- Pipeline triggers
- Automated testing results

### External APIs
- Cloud provider integrations
- Third-party monitoring tools
- Custom webhook endpoints

## Support and Contributing

### Getting Help
- Check troubleshooting section
- Review pod logs for errors
- Verify network connectivity
- Check resource availability

### Contributing
- UI improvements welcome
- New metric suggestions
- API endpoint additions
- Documentation updates

### Reporting Issues
- Include browser console errors
- Provide Kubernetes pod logs
- Share network configuration
- Include reproduction steps

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: Cloud AI Agents Team
