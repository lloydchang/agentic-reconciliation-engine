# Portal - User Guide

## Overview

The Portal is a comprehensive web-based platform for monitoring, managing, and optimizing AI infrastructure. This guide provides detailed instructions for using the portal's dashboard, APIs, and configuration options.

## Getting Started

### Accessing the Portal

#### Dashboard Access
- **URL**: `https://dashboard.ai-infrastructure-portal.com`
- **Authentication**: Required for all access
- **Supported Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

#### API Access
- **Base URL**: `https://api.ai-infrastructure-portal.com/api`
- **Authentication**: JWT token required
- **Rate Limits**: 100 requests per minute per user

### Initial Login

1. Navigate to the dashboard URL
2. Click "Login" in the top-right corner
3. Enter your credentials:
   - Username: Your assigned username
   - Password: Your password
   - MFA Code: If enabled, enter the code from your authenticator app
4. Click "Sign In"

### Dashboard Layout

The dashboard consists of several main sections:

#### Header
- **Navigation Menu**: Access to different sections
- **User Menu**: Account settings, theme selection, logout
- **Search Bar**: Global search across all data
- **Notifications**: Real-time alerts and system messages

#### Main Content Area
- **Overview Dashboard**: High-level metrics and status
- **Services Section**: Infrastructure service monitoring
- **Agents Section**: AI agent status and performance
- **Activity Feed**: Recent system activities and events

#### Sidebar
- **Quick Actions**: Common tasks and shortcuts
- **Filters**: Data filtering and search options
- **Settings**: Dashboard customization options

## Dashboard Features

### Overview Dashboard

#### System Metrics
- **CPU Usage**: Real-time CPU utilization across all services
- **Memory Usage**: Memory consumption and trends
- **Network I/O**: Network traffic and throughput
- **Disk Usage**: Storage utilization and I/O operations

#### Service Health
- **Service Status**: Online/offline status of all services
- **Response Times**: API response times and latency
- **Error Rates**: Error rates and failure patterns
- **Uptime**: Service availability percentages

#### AI Agent Status
- **Active Agents**: Currently running AI agents
- **Agent Performance**: Response times and success rates
- **Skill Execution**: Recent skill usage and outcomes
- **Resource Usage**: Agent-specific resource consumption

### Real-Time Updates

#### WebSocket Connection
The dashboard uses WebSocket connections for real-time updates:
- **Connection Status**: Green indicator when connected
- **Auto-Reconnection**: Automatic reconnection on network issues
- **Update Frequency**: Data refreshes every 5 seconds

#### Live Charts
- **Interactive Charts**: Click and drag to zoom, hover for details
- **Time Range Selection**: Choose from 1h, 6h, 24h, 7d, 30d
- **Export Options**: Download charts as PNG, SVG, or PDF
- **Data Export**: Export underlying data as CSV or JSON

### Interactive Widgets

#### Widget Types
- **Metric Cards**: Key performance indicators
- **Line Charts**: Time-series data visualization
- **Bar Charts**: Categorical data comparison
- **Pie Charts**: Proportional data representation
- **Tables**: Detailed data with sorting and filtering
- **Gauges**: Progress indicators and thresholds

#### Widget Customization
- **Drag and Drop**: Rearrange widgets on the dashboard
- **Resize**: Adjust widget dimensions
- **Configuration**: Modify widget settings and data sources
- **Save Layouts**: Save custom dashboard layouts

### Advanced Filtering

#### Global Search
- **Search Bar**: Search across all dashboard data
- **Filters**: Filter by service, agent, time range, status
- **Saved Searches**: Save frequently used search queries
- **Search History**: Access recent searches

#### Data Filtering
- **Time Filters**: Filter data by time ranges
- **Status Filters**: Filter by operational status
- **Type Filters**: Filter by service type or agent category
- **Custom Filters**: Create custom filter combinations

## API Usage

### Authentication

#### JWT Token Authentication
```bash
# Login to get JWT token
curl -X POST https://api.ai-infrastructure-portal.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.ai-infrastructure-portal.com/api/services
```

#### API Key Authentication (for integrations)
```bash
# Use API key in header
curl -H "X-API-Key: YOUR_API_KEY" \
  https://api.ai-infrastructure-portal.com/api/metrics
```

### Core API Endpoints

#### Health Check
```bash
GET /api/health
```
Returns overall system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": "7d 4h 23m"
}
```

#### Services
```bash
GET /api/services
```
Returns status of all infrastructure services.

**Parameters:**
- `status`: Filter by status (healthy, warning, critical)
- `type`: Filter by service type

**Response:**
```json
[
  {
    "name": "api-server",
    "status": "healthy",
    "type": "api",
    "url": "http://api-server:5001",
    "responseTime": 45,
    "uptime": "99.9%",
    "lastChecked": "2024-01-15T10:30:00Z"
  }
]
```

#### Metrics
```bash
GET /api/metrics
```
Returns system performance metrics.

**Parameters:**
- `period`: Time period (1h, 6h, 24h, 7d)

**Response:**
```json
{
  "cpu": {
    "usage": 65.5,
    "cores": 8,
    "loadAverage": [1.2, 1.1, 1.0]
  },
  "memory": {
    "used": 8192,
    "total": 16384,
    "percentage": 50.0
  },
  "disk": {
    "used": 256,
    "total": 512,
    "percentage": 50.0
  }
}
```

#### Agents
```bash
GET /api/agents
```
Returns AI agent status and information.

**Parameters:**
- `status`: Filter by agent status
- `type`: Filter by agent type

**Response:**
```json
[
  {
    "id": "memory-agent-rust",
    "name": "Memory Agent (Rust)",
    "type": "Memory Agent",
    "status": "active",
    "skills": 8,
    "successRate": 99.2,
    "lastActivity": "2024-01-15T10:25:00Z",
    "responseTime": 0.8
  }
]
```

#### Skills
```bash
GET /api/skills
```
Returns available AI skills and their status.

**Response:**
```json
[
  {
    "name": "optimize-costs",
    "description": "Multi-cloud cost optimization automation",
    "category": "infrastructure",
    "risk_level": "medium",
    "autonomy": "conditional",
    "executions": 1250,
    "successRate": 94.5,
    "avgResponseTime": 2.1
  }
]
```

#### Activity Feed
```bash
GET /api/activity
```
Returns recent system activities and events.

**Parameters:**
- `limit`: Number of activities to return (default: 50)
- `type`: Filter by activity type

**Response:**
```json
[
  {
    "id": "activity_12345",
    "type": "agent_execution",
    "description": "Cost optimization skill executed",
    "timestamp": "2024-01-15T10:30:00Z",
    "user": "system",
    "status": "success",
    "details": {
      "skill": "optimize-costs",
      "savings": "$1250.00",
      "duration": 2.1
    }
  }
]
```

### Advanced API Features

#### RAG Queries
```bash
POST /api/rag/query
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN

{
  "query": "What is the current system status?",
  "context": "infrastructure monitoring",
  "maxResults": 5
}
```

**Response:**
```json
{
  "response": "The system is currently operating normally with 99.9% uptime...",
  "confidence": 0.92,
  "sources": [
    {
      "type": "metric",
      "content": "All services reporting healthy status",
      "relevance": 0.95
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### WebSocket Integration
```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('wss://api.ai-infrastructure-portal.com/ws');

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'metric_update':
      updateMetrics(data.payload);
      break;
    case 'alert':
      showAlert(data.payload);
      break;
    case 'agent_status':
      updateAgentStatus(data.payload);
      break;
  }
};

// Send subscription request
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['metrics', 'alerts', 'agents']
  }));
};
```

### Rate Limiting

#### Rate Limit Headers
All API responses include rate limiting headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642156800
X-RateLimit-Retry-After: 60 (only present when limit exceeded)
```

#### Rate Limit Exceeded Response
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retryAfter": 60,
  "limit": 100,
  "remaining": 0,
  "reset": 1642156800
}
```

## Configuration

### User Preferences

#### Theme Settings
- **Light Theme**: Clean, bright interface
- **Dark Theme**: Easy on the eyes for extended use
- **Auto Theme**: Follows system preference
- **Custom Theme**: Personalize colors and fonts

#### Dashboard Customization
- **Widget Layout**: Arrange widgets as preferred
- **Default Time Range**: Set default time periods
- **Refresh Interval**: Configure auto-refresh frequency
- **Notification Settings**: Choose notification preferences

### API Configuration

#### Webhook Configuration
```bash
POST /api/webhooks
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["alerts", "metrics", "agents"],
  "secret": "your-webhook-secret"
}
```

#### Integration Settings
- **Slack Integration**: Receive notifications in Slack
- **Email Notifications**: Configure email alerts
- **PagerDuty**: Connect with incident management
- **Custom Integrations**: Webhook-based integrations

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
**Symptoms:** Blank page or loading errors
**Solutions:**
1. Clear browser cache and cookies
2. Check network connectivity
3. Verify browser compatibility
4. Contact support if issue persists

#### Authentication Issues
**Symptoms:** Unable to login or token expired
**Solutions:**
1. Verify username and password
2. Check MFA code if enabled
3. Clear browser cache
4. Reset password if needed

#### WebSocket Disconnection
**Symptoms:** Real-time updates not working
**Solutions:**
1. Check network firewall settings
2. Verify WebSocket URL configuration
3. Restart browser session
4. Contact IT support for proxy issues

#### API Rate Limiting
**Symptoms:** 429 Too Many Requests errors
**Solutions:**
1. Implement request throttling in your application
2. Use batch requests where possible
3. Upgrade to higher rate limit tier if available
4. Implement exponential backoff for retries

#### Slow Performance
**Symptoms:** Dashboard slow to load or update
**Solutions:**
1. Reduce time range for queries
2. Use filters to limit data volume
3. Close unused browser tabs
4. Check network connection speed
5. Contact support for performance optimization

### Error Codes

#### HTTP Status Codes
- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

#### WebSocket Error Codes
- **1000**: Normal closure
- **1001**: Going away
- **1006**: Abnormal closure
- **1011**: Server error
- **4000**: Authentication failed
- **4001**: Rate limit exceeded

### Getting Help

#### Support Resources
- **Documentation**: This user guide and API reference
- **Knowledge Base**: Searchable FAQ and troubleshooting guides
- **Community Forum**: User-to-user support and discussions
- **Video Tutorials**: Step-by-step video guides

#### Contact Support
- **Email**: support@ai-infrastructure-portal.com
- **Phone**: 1-800-AI-PORTAL (available 9 AM - 5 PM PST)
- **Live Chat**: Available in dashboard for logged-in users
- **Emergency**: 1-800-AI-EMERGENCY (24/7 for critical issues)

## Best Practices

### Dashboard Usage
- Regularly review system health metrics
- Set up appropriate alert thresholds
- Use saved searches for frequently monitored items
- Customize dashboard layout for your workflow
- Export important data regularly

### API Integration
- Implement proper error handling and retries
- Use WebSocket connections for real-time data
- Respect rate limits and implement backoff strategies
- Validate API responses before processing
- Keep API keys secure and rotate regularly

### Security
- Use strong, unique passwords
- Enable multi-factor authentication
- Log out when not using the portal
- Be cautious with shared devices
- Report any suspicious activity immediately

### Performance
- Use appropriate time ranges for queries
- Implement caching where possible
- Monitor your application's resource usage
- Optimize queries to reduce data transfer
- Use batch operations for multiple requests

## Appendices

### Appendix A: Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open global search |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+R` | Refresh dashboard |
| `Ctrl+S` | Save dashboard layout |
| `Esc` | Close modals/dialogs |
| `F11` | Toggle fullscreen |
| `Ctrl+Shift+F` | Toggle filters panel |

### Appendix B: API Response Codes

#### Success Codes (2xx)
- **200 OK**: Standard success response
- **201 Created**: Resource created successfully
- **204 No Content**: Request processed, no content returned

#### Client Error Codes (4xx)
- **400 Bad Request**: Malformed request
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limit exceeded

#### Server Error Codes (5xx)
- **500 Internal Server Error**: Unexpected server error
- **502 Bad Gateway**: Invalid response from upstream server
- **503 Service Unavailable**: Service temporarily unavailable
- **504 Gateway Timeout**: Request timed out

### Appendix C: Webhook Event Types

- **alerts**: System alerts and notifications
- **metrics**: Performance metrics updates
- **agents**: AI agent status changes
- **services**: Service health updates
- **activities**: System activity events
- **incidents**: Incident creation and updates

### Appendix D: Browser Compatibility

| Browser | Minimum Version | Recommended |
|---------|----------------|-------------|
| Chrome | 90 | 110+ |
| Firefox | 88 | 105+ |
| Safari | 14 | 16+ |
| Edge | 90 | 110+ |
| Mobile Safari | 14 | 16+ |

### Appendix E: System Requirements

#### Hardware Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: Dual-core processor or better
- **Storage**: 100MB for application, plus data storage
- **Network**: Broadband internet connection

#### Software Requirements
- **Operating System**: Windows 10+, macOS 10.15+, Linux distributions
- **Browser**: See browser compatibility table
- **Network**: HTTPS support required

---

## Feedback and Support

We value your feedback! Please help us improve the Portal by:

- **Reporting Issues**: Use the feedback button in the dashboard
- **Suggesting Features**: Share your ideas for new functionality
- **Participating in Surveys**: Help us understand your needs
- **Contributing**: Submit pull requests for improvements

For support, please visit our [support portal](https://support.ai-infrastructure-portal.com) or contact us using the information in the Getting Help section.

---

**Version**: 1.0.0
**Last Updated**: January 15, 2024
**Document ID**: UG-AIP-2024-001
