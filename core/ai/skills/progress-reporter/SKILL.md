---
name: progress-reporter
description: >
  Automated progress reporting and stakeholder communication system that generates
  comprehensive project status reports, tracks milestones, and provides executive
  summaries. Integrates with project management tools and communication platforms.
metadata:
  risk_level: low
  autonomy: high
  layer: temporal
  human_gate: Executive approval required for board-level reports
---

# Progress Reporter Skill

## Overview

The Progress Reporter skill provides automated project progress reporting and stakeholder communication capabilities. It integrates with project management tools, development pipelines, and communication platforms to generate comprehensive status reports, track milestones, and provide executive summaries.

## Capabilities

### Core Functions

- **Automated Report Generation**: Creates comprehensive project status reports
- **Milestone Tracking**: Monitors project milestones and deliverables
- **Executive Summaries**: Generates high-level summaries for leadership
- **Stakeholder Communication**: Distributes reports through multiple channels
- **Trend Analysis**: Analyzes project trends and performance metrics
- **Risk Assessment**: Identifies and reports project risks and issues

### Integration Sources

- **Project Management**: Jira, Asana, Trello, Monday.com
- **Development**: GitHub, GitLab, Bitbucket, CI/CD pipelines
- **Communication**: Slack, Microsoft Teams, Email
- **Documentation**: Confluence, Notion, SharePoint
- **Metrics**: Custom dashboards, analytics platforms

### Report Types

1. **Daily Standup Reports**: Quick status updates for team alignment
2. **Weekly Progress Reports**: Detailed weekly progress and planning
3. **Monthly Executive Reports**: High-level summaries for leadership
4. **Milestone Reports**: Specific milestone achievement reports
5. **Risk Assessment Reports**: Risk analysis and mitigation strategies
6. **Performance Metrics Reports**: KPI tracking and trend analysis

## Usage

### Basic Report Generation

```bash
# Generate daily standup report
skill invoke progress-reporter generate --type daily --team backend

# Generate weekly progress report
skill invoke progress-reporter generate --type weekly --project web-platform --include-metrics

# Generate executive summary
skill invoke progress-reporter generate --type executive --time-period Q1-2024 --format PDF
```

### Milestone Tracking

```bash
# Track milestone progress
skill invoke progress-reporter track-milestone --milestone "Q1 Launch" --project web-platform

# Generate milestone report
skill invoke progress-reporter milestone-report --milestone "Q1 Launch" --include-risks

# Update milestone status
skill invoke progress-reporter update-milestone --milestone "Q1 Launch" --status completed --completion-date 2024-03-31
```

### Stakeholder Communication

```bash
# Distribute report to stakeholders
skill invoke progress-reporter distribute --report-id report-123 --channels slack,email

# Send executive summary
skill invoke progress-reporter executive-summary --period monthly --recipients exec-team@company.com

# Schedule automated reports
skill invoke progress-reporter schedule --type weekly --every monday --recipients project-team@company.com
```

### Trend Analysis

```bash
# Analyze project trends
skill invoke progress-reporter analyze-trends --project web-platform --period 90d

# Generate performance metrics
skill invoke progress-reporter metrics --project web-platform --kpi velocity,quality,cost

# Compare with previous periods
skill invoke progress-reporter compare --project web-platform --period current --vs previous
```

### Risk Assessment

```bash
# Generate risk assessment
skill invoke progress-reporter risk-assessment --project web-platform --include-mitigation

# Update risk status
skill invoke progress-reporter update-risk --risk-id risk-001 --severity high --mitigation "Added monitoring"

# Generate risk dashboard
skill invoke progress-reporter risk-dashboard --project web-platform --format HTML
```

## Configuration

### Required Environment Variables

```bash
# Project Management Systems
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token

ASANA_API_KEY=your_asana_api_key
ASANA_WORKSPACE_ID=your_workspace_id

# Development Platforms
GITHUB_TOKEN=your_github_token
GITLAB_TOKEN=your_gitlab_token

# Communication Platforms
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
TEAMS_WEBHOOK_URL=https://your-teams-webhook-url

# Email Configuration
SMTP_HOST=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=reports@company.com
SMTP_PASSWORD=your_email_password

# Analytics Platforms
ANALYTICS_API_KEY=your_analytics_api_key
DASHBOARD_URL=https://dashboards.company.com
```

### Skill Configuration

```yaml
# .claude/skills/progress-reporter/config.yaml
data_sources:
  jira:
    url: ${JIRA_URL}
    username: ${JIRA_USERNAME}
    api_token: ${JIRA_API_TOKEN}
    projects:
      - WEB
      - MOBILE
      - INFRA
    fields:
      - status
      - assignee
      - priority
      - created
      - resolved
      - story_points

  github:
    token: ${GITHUB_TOKEN}
    repositories:
      - company/web-platform
      - company/mobile-app
      - company/infrastructure
    metrics:
      - pull_requests
      - issues
      - commits
      - deployments

  slack:
    bot_token: ${SLACK_BOT_TOKEN}
    signing_secret: ${SLACK_SIGNING_SECRET}
    channels:
      - #project-updates
      - #executive-reports
      - #team-standups

report_types:
  daily:
    sections:
      - team_status
      - blockers
      - achievements
      - next_steps
    schedule: "0 9 * * *"  # Daily at 9 AM
    recipients:
      - slack: #team-standups

  weekly:
    sections:
      - executive_summary
      - progress_overview
      - milestone_status
      - risk_assessment
      - resource_allocation
      - next_week_priorities
    schedule: "0 16 * * 5"  # Friday at 4 PM
    recipients:
      - email: project-team@company.com
      - slack: #project-updates

  monthly:
    sections:
      - executive_summary
      - financial_overview
      - kpi_dashboard
      - milestone_achievements
      - risk_analysis
      - team_performance
      - strategic_initiatives
    schedule: "0 9 1 * *"  # 1st of month at 9 AM
    recipients:
      - email: executives@company.com
      - slack: #executive-reports

metrics:
  velocity:
    calculation: "completed_story_points / sprint_duration"
    target: 40
    unit: "points/sprint"
  
  quality:
    calculation: "passed_tests / total_tests"
    target: 0.95
    unit: "percentage"
  
  cost:
    calculation: "actual_cost / budgeted_cost"
    target: 1.0
    unit: "ratio"
  
  delivery:
    calculation: "on_time_deliveries / total_deliveries"
    target: 0.90
    unit: "percentage"

milestones:
  tracking:
    auto_update: true
    notification_threshold: 0.8  # Alert at 80% completion
    risk_threshold: 0.6  # Flag as risky if < 60% complete by due date
  
  categories:
    - product_launch
    - feature_release
    - infrastructure_upgrade
    - compliance_requirement
    - customer_delivery

risk_assessment:
  categories:
    - technical
    - resource
    - schedule
    - budget
    - quality
    - security
  
  severity_levels:
    - critical: immediate_action_required
    - high: mitigation_within_24h
    - medium: mitigation_within_72h
    - low: monitor_and_review
  
  auto_detection:
    - schedule_slips
    - budget_overruns
    - quality_degradation
    - resource_constraints
    - stakeholder_concerns

report_templates:
  executive_summary: |
    # {{project_name}} - {{report_period}} Executive Summary
    
    ## Key Highlights
    {{#highlights}}
    - {{.}}
    {{/highlights}}
    
    ## Progress Overview
    - **Overall Progress**: {{overall_progress}}%
    - **Milestones Completed**: {{completed_milestones}}/{{total_milestones}}
    - **Budget Status**: {{budget_status}}
    - **Team Velocity**: {{team_velocity}} points/sprint
    
    ## Critical Issues
    {{#critical_issues}}
    - **{{title}}**: {{description}} ({{severity}})
    {{/critical_issues}}
    
    ## Next Period Focus
    {{#next_focus}}
    - {{.}}
    {{/next_focus}}

  weekly_progress: |
    # {{project_name}} - Week of {{week_start}} Progress Report
    
    ## Executive Summary
    {{executive_summary}}
    
    ## This Week's Achievements
    {{#achievements}}
    - ✅ {{.}}
    {{/achievements}}
    
    ## Current Sprint Status
    - **Sprint**: {{sprint_name}}
    - **Progress**: {{sprint_progress}}%
    - **Story Points**: {{completed_points}}/{{total_points}}
    - **Days Remaining**: {{days_remaining}}
    
    ## Blockers and Issues
    {{#blockers}}
    - 🚧 **{{title}}**: {{description}} ({{assignee}})
    {{/blockers}}
    
    ## Next Week's Priorities
    {{#next_priorities}}
    - {{.}}
    {{/next_priorities}}
    
    ## Team Performance
    - **Velocity**: {{velocity}} points/sprint
    - **Quality**: {{quality_score}}% pass rate
    - **Cycle Time**: {{cycle_time}} days

notification_settings:
  channels:
    slack:
      enabled: true
      default_channel: #project-updates
      executive_channel: #executive-reports
      thread_replies: true
    
    email:
      enabled: true
      from_address: progress-reports@company.com
      template_engine: handlebars
      include_attachments: true
    
    teams:
      enabled: true
      webhook_url: ${TEAMS_WEBHOOK_URL}
      adaptive_cards: true
  
  scheduling:
    daily_reports: "0 9 * * *"
    weekly_reports: "0 16 * * 5"
    monthly_reports: "0 9 1 * *"
    milestone_alerts: "0 */6 * * *"  # Every 6 hours
  
  escalation:
    missed_deadlines:
      - level: team_lead
        delay: 4h
        channels: [slack, email]
      - level: manager
        delay: 24h
        channels: [slack, email]
      - level: executive
        delay: 48h
        channels: [slack, email]
```

## MCP Server Integration

This skill integrates with the `engagement-sync` MCP server for enhanced stakeholder communication:

### Available MCP Tools

- `schedule_meeting`: Schedule stakeholder meetings for report discussions
- `track_communication`: Track report distribution and engagement
- `disseminate_decision`: Share report findings and decisions
- `collect_feedback`: Gather feedback on reports and recommendations
- `generate_engagement_report`: Analyze stakeholder engagement with reports

### MCP Usage Example

```javascript
// Using the MCP server directly
const reportDistribution = await mcp.call('track_communication', {
  communication_id: `report-${reportId}`,
  type: 'email',
  participants: stakeholders,
  content: reportSummary,
  sentiment: 'neutral',
  engagement_level: 'high'
});

const feedbackCollection = await mcp.call('collect_feedback', {
  feedback_id: `feedback-${reportId}`,
  topic: 'Q1 Progress Report',
  stakeholders: executives,
  feedback_type: 'survey',
  questions: [
    'How useful was this report?',
    'What additional information would you like?',
    'Rate the clarity of the executive summary'
  ],
  deadline: '2024-04-07T17:00:00Z'
});
```

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Data Sources    │    │ Report Engine    │    │ Distribution    │
│                 │    │                  │    │                 │
│ • Jira API      │───▶│ • Data Aggregation│───▶│ • Email Sender  │
│ • GitHub API    │    │ • Metric Calc    │    │ • Slack Bot     │
│ • Analytics API │    │ • Template Engine│    │ • Teams Webhook │
│ • Custom APIs   │    │ • Chart Generation│    │ • PDF Export   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Analytics       │    │ Risk Assessment  │    │ Scheduling     │
│                 │    │                  │    │                 │
│ • Trend Analysis│    │ • Risk Detection │    │ • Cron Jobs     │
│ • KPI Tracking  │    │ • Impact Scoring │    │ • Event Triggers│
│ • Forecasting   │    │ • Mitigation     │    │ • Reminders     │
│ • Dashboards    │    │ • Escalation     │    │ • Calendar Sync │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Report Generation Pipeline

1. **Data Collection**: Gather data from all configured sources
2. **Data Processing**: Clean, normalize, and aggregate data
3. **Metric Calculation**: Compute KPIs and performance metrics
4. **Template Rendering**: Apply report templates with data
5. **Format Generation**: Create reports in requested formats
6. **Distribution**: Send reports through configured channels
7. **Feedback Collection**: Gather stakeholder feedback
8. **Analytics**: Track engagement and effectiveness

### Metric Calculations

#### Velocity Metrics
```python
def calculate_velocity(team_data, time_period):
    """
    Calculate team velocity based on completed story points
    """
    completed_points = sum(
        issue.story_points 
        for issue in team_data.issues 
        if issue.status == 'done' and 
           issue.completed_date >= time_period.start
    )
    
    sprint_count = len(time_period.sprints)
    return completed_points / sprint_count if sprint_count > 0 else 0
```

#### Quality Metrics
```python
def calculate_quality_score(build_data, deployments):
    """
    Calculate quality score based on test results and deployment success
    """
    test_pass_rate = sum(
        build.passed_tests / build.total_tests 
        for build in build_data
    ) / len(build_data)
    
    deployment_success_rate = sum(
        1 for deployment in deployments 
        if deployment.status == 'success'
    ) / len(deployments)
    
    return (test_pass_rate * 0.7 + deployment_success_rate * 0.3)
```

#### Budget Metrics
```python
def calculate_budget_variance(actual_costs, planned_costs):
    """
    Calculate budget variance as percentage
    """
    total_actual = sum(actual_costs.values())
    total_planned = sum(planned_costs.values())
    
    if total_planned == 0:
        return 0
    
    variance = (total_actual - total_planned) / total_planned
    return variance * 100  # Return as percentage
```

### Risk Assessment Algorithm

The risk assessment uses a multi-factor scoring system:

```python
def calculate_risk_score(risk_factors):
    """
    Calculate overall risk score based on multiple factors
    """
    weights = {
        'schedule_variance': 0.3,
        'budget_variance': 0.25,
        'quality_score': 0.2,
        'resource_availability': 0.15,
        'stakeholder_satisfaction': 0.1
    }
    
    weighted_score = sum(
        weights[factor] * normalize_score(risk_factors[factor])
        for factor in weights
    )
    
    return weighted_score * 100  # Convert to 0-100 scale
```

## Best Practices

### 1. Report Design
- Keep executive summaries concise (1-2 pages max)
- Use visualizations for complex data
- Include actionable insights and recommendations
- Maintain consistent formatting and branding

### 2. Data Quality
- Ensure data sources are reliable and up-to-date
- Validate data integrity before report generation
- Handle missing or incomplete data gracefully
- Document data sources and calculations

### 3. Stakeholder Engagement
- Tailor reports to audience needs and preferences
- Provide multiple distribution channels
- Collect and act on feedback
- Maintain communication schedules

### 4. Continuous Improvement
- Monitor report effectiveness and engagement
- Regularly update templates and metrics
- Incorporate new data sources and insights
- Adapt to changing business requirements

## Troubleshooting

### Common Issues

**Data Source Connection Failures**
```bash
# Test data source connectivity
skill invoke progress-reporter test-connection --source jira
skill invoke progress-reporter test-connection --source github
skill invoke progress-reporter test-connection --source analytics

# Verify API credentials
skill invoke progress-reporter verify-credentials --source jira
skill invoke progress-reporter verify-credentials --source github
```

**Report Generation Failures**
```bash
# Check template syntax
skill invoke progress-reporter validate-template --template executive_summary

# Test data processing
skill invoke progress-reporter test-data-processing --project web-platform

# Debug report generation
export PROGRESS_REPORTER_DEBUG=true
skill invoke progress-reporter generate --type weekly --debug --verbose
```

**Distribution Issues**
```bash
# Test notification channels
skill invoke progress-reporter test-notification --channel slack
skill invoke progress-reporter test-notification --channel email

# Verify recipient configuration
skill invoke progress-reporter test-recipients --report-type weekly

# Check scheduling configuration
skill invoke progress-reporter test-schedule --report-type daily
```

### Debug Mode

```bash
# Enable comprehensive debugging
export PROGRESS_REPORTER_DEBUG=true
export PROGRESS_REPORTER_TRACE=true
skill invoke progress-reporter generate --type weekly --debug --trace --verbose
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/progress-report.yml
name: Progress Report Generation
on:
  schedule:
    - cron: '0 16 * * 5'  # Friday at 4 PM
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Generate Weekly Report
        run: |
          skill invoke progress-reporter generate \
            --type weekly \
            --project web-platform \
            --format JSON,PDF,HTML
      - name: Distribute Report
        run: |
          skill invoke progress-reporter distribute \
            --report-id latest \
            --channels slack,email
      - name: Upload Artifacts
        uses: actions/upload-artifact@v2
        with:
          name: weekly-progress-report
          path: reports/
```

### Slack Integration

```javascript
// Slack bot for interactive reports
app.command('/report', async ({ command, ack, say }) => {
  await ack();
  
  const parts = command.text.split(' ');
  const reportType = parts[0];
  const project = parts[1] || 'web-platform';
  
  try {
    const report = await skill.invoke('progress-reporter', {
      action: 'generate',
      type: reportType,
      project: project,
      format: 'slack'
    });
    
    await say({
      text: `📊 ${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report for ${project}`,
      blocks: report.blocks
    });
  } catch (error) {
    await say(`❌ Error generating report: ${error.message}`);
  }
});
```

### Dashboard Integration

```javascript
// Real-time dashboard data
app.get('/api/progress/:project', async (req, res) => {
  const { project } = req.params;
  
  try {
    const progress = await skill.invoke('progress-reporter', {
      action: 'get-real-time-data',
      project: project,
      metrics: ['velocity', 'quality', 'budget', 'milestones']
    });
    
    res.json(progress);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Performance Considerations

### Optimization Tips

1. **Data Caching**: Cache frequently accessed data to reduce API calls
2. **Parallel Processing**: Process multiple data sources concurrently
3. **Incremental Updates**: Only update changed data since last report
4. **Background Processing**: Generate reports asynchronously for large projects

### Resource Usage

- **Memory**: ~1GB for processing large project datasets
- **CPU**: Moderate usage during data aggregation and metric calculation
- **Network**: High usage during API calls to data sources
- **Storage**: ~500MB for report cache and historical data

## Security Considerations

### Data Protection

- All API credentials are encrypted at rest
- Report data is stored in secure, access-controlled storage
- Sensitive information is redacted in reports
- Audit logging for all data access

### Access Control

- Role-based access for report generation and distribution
- Secure API key management
- Network segmentation for report processing
- Compliance with data protection regulations

## Version History

### v1.0.0
- Initial release with Jira and GitHub integration
- Basic report templates and distribution
- Daily and weekly report generation

### v1.1.0
- Added analytics platform integration
- Enhanced template system with Handlebars
- Risk assessment and milestone tracking

### v1.2.0
- Executive summary generation
- Advanced metrics and trend analysis
- Multi-channel distribution improvements

### v1.3.0
- Real-time dashboard integration
- Automated scheduling and escalation
- Comprehensive feedback collection

## Support and Contributing

### Getting Help

- Documentation: `/docs/progress-reporter.md`
- Examples: `/examples/progress-reporting/`
- Community: `#progress-reporting` Slack channel

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### License

This skill is licensed under the MIT License. See LICENSE file for details.
