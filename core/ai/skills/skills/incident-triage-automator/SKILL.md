---
name: incident-triage-automator
description: >
  Automated incident triage and management system that aggregates alerts, assesses severity,
  creates incidents, notifies stakeholders, and tracks resolution progress. Integrates with
  monitoring systems to provide comprehensive incident lifecycle management.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: Escalation approval required for P0 incidents
---

# Incident Triage Automator Skill

## Overview

The Incident Triage Automator skill provides intelligent incident management capabilities, automatically triaging alerts, assessing severity, and coordinating incident response across multiple monitoring systems. It reduces incident response time and ensures consistent handling of operational issues.

## Capabilities

### Core Functions

- **Alert Aggregation**: Correlates alerts from Prometheus, Datadog, PagerDuty, and other monitoring systems
- **Severity Assessment**: Uses ML-driven analysis to assess incident severity and impact
- **Automated Incident Creation**: Creates structured incidents in incident management systems
- **Stakeholder Notification**: Automatically notifies relevant stakeholders based on escalation policies
- **Runbook Recommendation**: Suggests relevant runbooks based on incident patterns
- **Status Tracking**: Tracks incident resolution progress and generates post-mortem reports

### Supported Monitoring Systems

- **Prometheus**: Alertmanager alerts and metrics
- **Datadog**: Monitors, events, and alerts
- **PagerDuty**: Incidents and on-call schedules
- **Grafana**: Dashboard alerts and annotations
- **Custom**: REST API integration for custom monitoring tools

### Notification Channels

- **Slack**: Channel notifications and DM alerts
- **Email**: Rich HTML email notifications
- **Microsoft Teams**: Channel and personal messages
- **PagerDuty**: Escalation and on-call notifications

## Usage

### Basic Incident Triage

```bash
# Aggregate and triage alerts from all sources
skill invoke incident-triage-automator triage --time-window 1h --severity-threshold HIGH

# Triage specific monitoring source
skill invoke incident-triage-automator triage --source prometheus --time-window 30m

# Create incident from alerts
skill invoke incident-triage-automator create-incident --title "Database Degradation" --severity P1
```

### Stakeholder Notification

```bash
# Notify stakeholders for P0 incident
skill invoke incident-triage-automator notify --incident-id INC-001 --escalation-level executive

# Send custom notification
skill invoke incident-triage-automator notify --incident-id INC-002 --channels slack,email --message-template custom
```

### Runbook Recommendations

```bash
# Get runbook recommendations for incident
skill invoke incident-triage-automator recommend-runbook --incident-id INC-001 --symptoms "high_cpu,slow_queries"

# Search runbooks by service
skill invoke incident-triage-automator recommend-runbook --service database --category performance
```

### Status Tracking

```bash
# Update incident status
skill invoke incident-triage-automator update-status --incident-id INC-001 --status investigating

# Add resolution notes
skill invoke incident-triage-automator update-status --incident-id INC-001 --status resolved --resolution-notes "Fixed database connection pool"
```

## Configuration

### Required Environment Variables

```bash
# Monitoring System Credentials
PROMETHEUS_URL=https://prometheus.company.com
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key
PAGERDUTY_API_KEY=your_pagerduty_api_key

# Notification System Credentials
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
EMAIL_SMTP_HOST=smtp.company.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=alerts@company.com
EMAIL_PASSWORD=your_email_password

# Incident Management System
INCIDENT_SYSTEM_URL=https://incidents.company.com
INCIDENT_API_KEY=your_incident_api_key
```

### Skill Configuration

```yaml
# .claude/skills/incident-triage-automator/config.yaml
alert_sources:
  prometheus:
    url: https://prometheus.company.com
    enabled: true
    alertmanager_url: https://alertmanager.company.com
  datadog:
    api_key: ${DATADOG_API_KEY}
    app_key: ${DATADOG_APP_KEY}
    enabled: true
  pagerduty:
    api_key: ${PAGERDUTY_API_KEY}
    enabled: true

severity_assessment:
  weights:
    user_impact: 0.4
    business_impact: 0.3
    affected_users: 0.2
    affected_services: 0.1
  thresholds:
    P0: 80
    P1: 60
    P2: 40
    P3: 20

escalation_policy:
  P0:
    - level: executive
      delay: 0m
      channels: [slack, email, pagerduty]
  P1:
    - level: director
      delay: 15m
      channels: [slack, email]
    - level: executive
      delay: 1h
      channels: [slack, email, pagerduty]
  P2:
    - level: manager
      delay: 1h
      channels: [slack, email]
  P3:
    - level: team
      delay: 4h
      channels: [slack]

notification_templates:
  slack: |
    🚨 **{{severity}} Incident** 🚨
    
    *Title*: {{title}}
    *Status*: {{status}}
    *Services*: {{affected_services}}
    
    {{description}}
    
    🔗 View Incident: {{incident_url}}
  
  email: |
    <h2>🚨 {{severity}} Incident Alert</h2>
    <p><strong>Title:</strong> {{title}}</p>
    <p><strong>Status:</strong> {{status}}</p>
    <p><strong>Affected Services:</strong> {{affected_services}}</p>
    <p><strong>Description:</strong> {{description}}</p>
    <p><a href="{{incident_url}}">View Incident Details</a></p>
```

## MCP Server Integration

This skill integrates with the `incident-triage` MCP server for enhanced capabilities:

### Available MCP Tools

- `aggregate_alerts`: Aggregate and correlate alerts from multiple sources
- `assess_incident_severity`: Assess incident severity based on impact
- `create_incident`: Create incidents in incident management systems
- `notify_stakeholders`: Notify relevant stakeholders
- `recommend_runbook`: Recommend relevant runbooks
- `track_incident_status`: Track incident resolution progress

### MCP Usage Example

```javascript
// Using the MCP server directly
const alerts = await mcp.call('aggregate_alerts', {
  time_window: '1h',
  alert_sources: ['prometheus', 'datadog'],
  correlation_threshold: 0.7
});

const severity = await mcp.call('assess_incident_severity', {
  incident_data: {
    title: 'Database Performance Degradation',
    affected_services: ['database', 'api'],
    user_impact: 'major',
    business_impact: 'medium'
  },
  auto_create_incident: true
});
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Alert Sources   │    │ Triage Engine    │    │ Incident Mgmt   │
│                 │    │                  │    │                 │
│ • Prometheus    │───▶│ • Correlation     │───▶│ • Incident CRUD │
│ • Datadog       │    │ • Severity Calc  │    │ • Status Tracking│
│ • PagerDuty     │    │ • Pattern Match  │    │ • Assignment    │
│ • Custom APIs   │    │ • ML Assessment  │    │ • Escalation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Notification     │    │ Runbook Engine   │    │ Reporting       │
│                 │    │                  │    │                 │
│ • Slack Bot     │    │ • Search         │    │ • MTTR Metrics  │
│ • Email Sender  │    │ • Ranking        │    │ • Incident Report│
│ • Teams Webhook │    │ • Context Match  │    │ • Post-mortem    │
│ • PagerDuty API │    │ • Success Rate   │    │ • Trend Analysis │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Alert Correlation Algorithm

The skill uses a sophisticated correlation algorithm:

1. **Time-based Correlation**: Groups alerts occurring within a specified time window
2. **Service-based Correlation**: Groups alerts affecting the same services
3. **Pattern-based Correlation**: Uses ML to identify similar alert patterns
4. **Impact-based Correlation**: Groups alerts with similar business impact

### Severity Assessment Model

The severity assessment considers multiple factors:

```python
def calculate_severity_score(incident_data):
    score = 0
    
    # User impact (40% weight)
    user_impact_scores = {
        'none': 0, 'minor': 25, 'major': 50, 'critical': 100
    }
    score += user_impact_scores[incident_data.user_impact] * 0.4
    
    # Business impact (30% weight)
    business_impact_scores = {
        'none': 0, 'minor': 25, 'major': 50, 'critical': 100
    }
    score += business_impact_scores[incident_data.business_impact] * 0.3
    
    # Affected users (20% weight)
    if incident_data.affected_users > 10000:
        score += 100 * 0.2
    elif incident_data.affected_users > 1000:
        score += 75 * 0.2
    elif incident_data.affected_users > 100:
        score += 50 * 0.2
    elif incident_data.affected_users > 10:
        score += 25 * 0.2
    
    # Affected services (10% weight)
    score += min(incident_data.affected_services.length * 10, 100) * 0.1
    
    return min(score, 100)
```

### Runbook Recommendation System

The runbook recommendation uses multiple signals:

1. **Incident Type Matching**: Matches incident type to runbook categories
2. **Service Matching**: Prioritizes runbooks for affected services
3. **Symptom Matching**: Uses NLP to match symptoms to runbook content
4. **Success Rate**: Prioritizes runbooks with higher success rates
5. **Recency**: Considers recently used and effective runbooks

## Best Practices

### 1. Alert Configuration
- Configure alerts with meaningful titles and descriptions
- Include relevant labels and annotations
- Set appropriate severity levels in monitoring systems
- Use consistent naming conventions

### 2. Escalation Policies
- Define clear escalation paths for each severity level
- Include on-call schedules and backup contacts
- Set appropriate escalation delays
- Test escalation policies regularly

### 3. Runbook Management
- Keep runbooks up-to-date with latest procedures
- Include clear step-by-step instructions
- Add expected timeframes for each step
- Document common pitfalls and solutions

### 4. Incident Documentation
- Capture all incident timeline events
- Document root cause analysis
- Include lessons learned
- Track improvement actions

## Troubleshooting

### Common Issues

**Alert Aggregation Failures**
```bash
# Check monitoring system connectivity
skill invoke incident-triage-automator check-connection --source prometheus
skill invoke incident-triage-automator check-connection --source datadog

# Verify alert format
skill invoke incident-triage-automator validate-alerts --source prometheus
```

**Severity Assessment Issues**
```bash
# Test severity calculation
skill invoke incident-triage-automator test-severity --incident-data test-incident.json

# Review assessment weights
skill invoke incident-triage-automator show-config --section severity_assessment
```

**Notification Failures**
```bash
# Test notification channels
skill invoke incident-triage-automator test-notification --channel slack
skill invoke incident-triage-automator test-notification --channel email

# Verify escalation policies
skill invoke incident-triage-automator test-escalation --severity P0
```

### Debug Mode

```bash
# Enable debug logging
export INCIDENT_TRIAGE_DEBUG=true
skill invoke incident-triage-automator triage --debug --verbose
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/incident-response.yml
name: Incident Response Test
on: [push]

jobs:
  test-incident-response:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test Alert Processing
        run: |
          skill invoke incident-triage-automator test-alerts \
            --test-data test-alerts.json \
            --expected-severity P1
      - name: Test Notification Flow
        run: |
          skill invoke incident-triage-automator test-notification \
            --channel slack \
            --test-incident-id TEST-001
```

### Slack Bot Integration

```javascript
// Slack bot command handler
app.command('/incident', async ({ command, ack, say }) => {
  await ack();
  
  const parts = command.text.split(' ');
  const action = parts[0];
  const incidentId = parts[1];
  
  switch (action) {
    case 'status':
      const status = await skill.invoke('incident-triage-automator', {
        action: 'get-status',
        incident_id: incidentId
      });
      await say(`Incident ${incidentId} status: ${status.status}`);
      break;
      
    case 'escalate':
      await skill.invoke('incident-triage-automator', {
        action: 'escalate',
        incident_id: incidentId,
        level: 'manager'
      });
      await say(`Incident ${incidentId} escalated to manager`);
      break;
  }
});
```

## Performance Considerations

### Optimization Tips

1. **Alert Batching**: Process alerts in batches to reduce API calls
2. **Caching**: Cache incident data and runbook recommendations
3. **Parallel Processing**: Process multiple alert sources in parallel
4. **Rate Limiting**: Respect API rate limits for monitoring systems

### Resource Usage

- **Memory**: ~1GB for processing large alert volumes
- **CPU**: High usage during correlation and ML assessment
- **Network**: High usage during alert aggregation
- **Storage**: ~500MB for incident history and runbooks

## Security Considerations

### Data Protection

- All monitoring credentials are encrypted at rest
- Incident data is stored in secure, access-controlled storage
- Sensitive information is redacted in notifications

### Access Control

- Role-based access for incident management
- Audit logging for all incident activities
- Secure webhook validation for monitoring systems

## Version History

### v1.0.0
- Initial release with Prometheus and PagerDuty integration
- Basic severity assessment and notification capabilities
- Slack and email notification support

### v1.1.0
- Added Datadog integration
- Enhanced correlation algorithms
- Runbook recommendation system

### v1.2.0
- ML-based severity assessment
- Multi-channel notification improvements
- Comprehensive reporting and analytics

### v1.3.0
- Teams integration
- Advanced escalation policies
- Post-mortem automation

## Support and Contributing

### Getting Help

- Documentation: `/docs/incident-triage-automator.md`
- Examples: `/examples/incident-triage/`
- Community: `#incident-response` Slack channel

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### License

This skill is licensed under the MIT License. See LICENSE file for details.
