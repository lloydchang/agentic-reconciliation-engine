---
name: standup-post
description: Use when you need to generate and post automated daily standup updates. Aggregates ticket tracker, GitHub activity, and prior standups into formatted updates with delta-only reporting.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: business-automation
  risk_level: low
  autonomy: conditional
  layer: temporal
  human_gate: Requires initial setup of team configuration
compatibility: Requires GitHub API, ticket system access, and Slack integration
allowed-tools: Bash Read Write Grep
---

# Standup Post Automation

## Purpose
Automates daily standup reporting by aggregating ticket tracker activity, GitHub changes, and previous standups into concise, delta-only updates for team communication.

## When to Use
- **Daily standups**: When you need to generate daily team updates
- **Remote teams**: For asynchronous status communication
- **Project tracking**: When monitoring progress across multiple systems
- **Management reporting**: For stakeholder updates on team activity
- **Personal productivity**: For tracking individual contributions

## Setup Configuration

### First-Time Setup
Create `config.json` in the skill directory:
```json
{
  "team": {
    "name": "platform-team",
    "members": ["alice", "bob", "charlie"],
    "manager": "diana"
  },
  "integrations": {
    "slack": {
      "channel": "#platform-standup",
      "webhook_url": "${SLACK_WEBHOOK_URL}",
      "post_as_user": true
    },
    "github": {
      "org": "company",
      "repos": ["platform-api", "platform-ui", "platform-deploy"],
      "token": "${GITHUB_TOKEN}"
    },
    "ticket_system": {
      "type": "jira", // or "linear", "asana"
      "project": "PLAT",
      "token": "${JIRA_TOKEN}"
    }
  },
  "schedule": {
    "timezone": "America/Los_Angeles",
    "post_time": "09:00",
    "weekend_mode": "skip"
  },
  "filters": {
    "exclude_labels": ["wontfix", "duplicate"],
    "include_states": ["In Progress", "Review", "Done"],
    "min_activity_threshold": 1
  }
}
```

## Process

### 1. Data Collection
- **GitHub Activity**: Fetch commits, PRs, and issues from configured repositories
- **Ticket Updates**: Retrieve ticket status changes and assignments
- **Previous Standup**: Load yesterday's standup for delta comparison

### 2. Activity Analysis
- **Categorize Changes**: Group activities by type (features, bugs, infrastructure)
- **Identify Deltas**: Compare with previous day to highlight only new changes
- **Member Attribution**: Link activities to team members

### 3. Report Generation
- **Format Summary**: Create structured standup report
- **Prioritize Items**: Order by importance and impact
- **Add Context**: Include relevant links and details

### 4. Distribution
- **Post to Slack**: Share in configured channel
- **Store History**: Save to `standups.log` for future reference
- **Update Metrics**: Track participation and activity trends

## Inputs

### Command Line Options
```bash
# Generate and post standup
python main.py post --config config.json

# Generate only (don't post)
python main.py generate --date yesterday --output standup.md

# Custom date range
python main.py generate --from-date 2024-01-15 --to-date 2024-01-16

# Specific team members
python main.py post --members alice,bob --config config.json

# Dry run with preview
python main.py post --dry-run --preview
```

### Configuration Parameters
- **team**: Team configuration and member list
- **integrations**: External system connections
- **schedule**: Posting schedule and timezone settings
- **filters**: Activity filtering and inclusion rules

## Outputs

### Standup Report Format
```markdown
# Platform Team Standup - January 16, 2024

## 🎯 Highlights
- **Feature**: User authentication service deployed to staging (alice)
- **Bug Fix**: Fixed memory leak in API gateway (bob)
- **Infrastructure**: Database migration completed (charlie)

## 📋 Activity Summary

### Alice (@alice)
- ✅ PR #234: Add OAuth2 authentication (merged)
- 🎫 PLAT-123: Implement user login (in review)
- 📝 Updated API documentation

### Bob (@bob)  
- 🔧 PR #235: Fix memory leak in gateway (merged)
- 🐛 PLAT-125: Resolve caching issue (done)
- 📊 Performance testing completed

### Charlie (@charlie)
- 🗄️ PLAT-127: Database migration (completed)
- 📋 Infrastructure review checklist updated
- 🔍 Security audit in progress

## 📊 Metrics
- **PRs Merged**: 3
- **Tickets Completed**: 2
- **Commits**: 15
- **Team Members Active**: 3/3

## 🔗 Links
- [GitHub Activity](https://github.com/company/platform-api/pulls)
- [Jira Board](https://company.atlassian.net/secure/RapidBoard.jspa?project=PLAT)
- [Deployment Dashboard](https://deploy.company.com/platform)

## 📝 Notes
- Code review meeting scheduled for 2 PM
- Production deployment window tomorrow 10-11 AM
```

### Log File Format (`standups.log`)
```json
{
  "date": "2024-01-16",
  "timestamp": "2024-01-16T09:00:00Z",
  "team": "platform-team",
  "summary": {
    "prs_merged": 3,
    "tickets_completed": 2,
    "commits": 15,
    "active_members": 3
  },
  "activities": [
    {
      "member": "alice",
      "type": "pull_request",
      "action": "merged",
      "title": "Add OAuth2 authentication",
      "url": "https://github.com/company/platform-api/pull/234"
    }
  ],
  "posted_to_slack": true,
  "slack_message_id": "1234567890.123456"
}
```

## Scripts

### `main.py` - Main orchestration script
```python
#!/usr/bin/env python3
"""
Standup Post Automation
Aggregates team activity and posts daily standup updates
"""

# /// script
# dependencies = [
#   "requests>=2.28.0",
#   "PyYAML>=6.0",
#   "python-dateutil>=2.8.0",
#   "slack-sdk>=3.19.0",
#   "PyGithub>=1.58.0"
# ]
# ///

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from slack_sdk import WebClient
from github import Github
import requests

class StandupGenerator:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.slack_client = WebClient(token=self.config["integrations"]["slack"]["webhook_url"])
        self.github_client = Github(self.config["integrations"]["github"]["token"])
        self.standup_log = Path("standups.log")
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def generate_standup(self, date: datetime = None) -> dict:
        """Generate standup report for specified date"""
        if date is None:
            date = datetime.now() - timedelta(days=1)
            
        # Collect activities from all sources
        github_activities = self._fetch_github_activity(date)
        ticket_activities = self._fetch_ticket_activity(date)
        
        # Combine and analyze activities
        all_activities = github_activities + ticket_activities
        activities_by_member = self._group_by_member(all_activities)
        
        # Generate report
        report = self._generate_report(date, activities_by_member)
        
        return report
    
    def post_to_slack(self, report: dict) -> str:
        """Post standup report to Slack channel"""
        message = self._format_slack_message(report)
        
        response = self.slack_client.chat_postMessage(
            channel=self.config["integrations"]["slack"]["channel"],
            text=message,
            username="Standup Bot"
        )
        
        return response["ts"]
    
    def save_to_log(self, report: dict, slack_message_id: str = None):
        """Save standup to historical log"""
        log_entry = {
            "date": report["date"],
            "timestamp": datetime.now().isoformat(),
            "team": self.config["team"]["name"],
            "summary": report["summary"],
            "activities": report["activities"],
            "posted_to_slack": slack_message_id is not None,
            "slack_message_id": slack_message_id
        }
        
        with open(self.standup_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _fetch_github_activity(self, date: datetime) -> list:
        """Fetch GitHub activity for the date"""
        activities = []
        
        for repo_name in self.config["integrations"]["github"]["repos"]:
            repo = self.github_client.get_repo(
                f"{self.config['integrations']['github']['org']}/{repo_name}"
            )
            
            # Fetch commits
            commits = repo.get_commits(since=date, until=date + timedelta(days=1))
            for commit in commits:
                activities.append({
                    "member": commit.author.login if commit.author else "unknown",
                    "type": "commit",
                    "action": "pushed",
                    "title": commit.commit.message.split('\n')[0],
                    "url": commit.html_url,
                    "timestamp": commit.commit.author.date
                })
            
            # Fetch pull requests
            pulls = repo.get_pulls(state="all", sort="updated", direction="desc")
            for pr in pulls:
                if pr.updated_at.date() == date.date():
                    activities.append({
                        "member": pr.user.login,
                        "type": "pull_request",
                        "action": pr.state,
                        "title": pr.title,
                        "url": pr.html_url,
                        "timestamp": pr.updated_at
                    })
        
        return activities
    
    def _fetch_ticket_activity(self, date: datetime) -> list:
        """Fetch ticket system activity for the date"""
        # Implementation varies by ticket system type
        if self.config["integrations"]["ticket_system"]["type"] == "jira":
            return self._fetch_jira_activity(date)
        # Add other ticket systems as needed
        return []
    
    def _group_by_member(self, activities: list) -> dict:
        """Group activities by team member"""
        members = self.config["team"]["members"]
        grouped = {member: [] for member in members}
        grouped["other"] = []
        
        for activity in activities:
            member = activity.get("member", "other")
            if member in grouped:
                grouped[member].append(activity)
            else:
                grouped["other"].append(activity)
        
        return grouped
    
    def _generate_report(self, date: datetime, activities_by_member: dict) -> dict:
        """Generate the standup report"""
        report = {
            "date": date.strftime("%Y-%m-%d"),
            "team": self.config["team"]["name"],
            "activities": [],
            "summary": self._calculate_summary(activities_by_member)
        }
        
        # Process activities for each member
        for member, activities in activities_by_member.items():
            if activities and member != "other":
                member_activities = self._process_member_activities(member, activities)
                report["activities"].extend(member_activities)
        
        return report
    
    def _format_slack_message(self, report: dict) -> str:
        """Format report for Slack posting"""
        lines = [
            f"📋 **{report['team'].title()} Standup - {report['date']}**",
            ""
        ]
        
        # Add highlights
        highlights = [a for a in report["activities"] if a.get("priority") == "high"]
        if highlights:
            lines.append("🎯 **Highlights**")
            for activity in highlights[:5]:  # Limit to top 5
                lines.append(f"• {activity['title']} ({activity['member']})")
            lines.append("")
        
        # Add member activities
        current_member = None
        for activity in report["activities"]:
            if activity["member"] != current_member:
                current_member = activity["member"]
                lines.append(f"**{current_member.title()}**")
            
            emoji = self._get_activity_emoji(activity["type"], activity["action"])
            lines.append(f"{emoji} {activity['title']}")
        
        # Add metrics
        summary = report["summary"]
        lines.extend([
            "",
            f"📊 **Metrics**: {summary['prs_merged']} PRs, {summary['tickets_completed']} tickets, {summary['commits']} commits",
            f"👥 **Active**: {summary['active_members']}/{len(self.config['team']['members'])} members"
        ])
        
        return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and post standup updates")
    parser.add_argument("--config", required=True, help="Configuration file path")
    parser.add_argument("--date", help="Date for standup (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't post")
    parser.add_argument("--preview", action="store_true", help="Preview output")
    
    args = parser.parse_args()
    
    generator = StandupGenerator(args.config)
    
    # Parse date if provided
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now() - timedelta(days=1)
    
    # Generate standup
    report = generator.generate_standup(target_date)
    
    if args.preview or args.dry_run:
        print(json.dumps(report, indent=2))
    
    if not args.dry_run:
        # Post to Slack
        message_id = generator.post_to_slack(report)
        generator.save_to_log(report, message_id)
        print(f"Standup posted to Slack (message ID: {message_id})")

if __name__ == "__main__":
    main()
```

## Gotchas

### Common Pitfalls
- **API Rate Limits**: GitHub and Jira have rate limits. Use pagination and respect retry-after headers.
- **Time Zone Issues**: Always use UTC for internal timestamps, convert to team timezone for display.
- **Member Name Matching**: GitHub usernames might not match team member names. Maintain mapping in config.

### Edge Cases
- **Weekend Activity**: Configure weekend_mode to handle or skip non-working days.
- **Holidays**: Add holiday calendar to skip standups on company holidays.
- **New Team Members**: Update config when team members join or leave.

### Performance Issues
- **Large Repositories**: Limit commit fetching to relevant branches and time windows.
- **Network Timeouts**: Set appropriate timeouts for API calls (30-60 seconds).
- **Log File Growth**: Rotate standups.log monthly to prevent large file sizes.

### Security Considerations
- **API Tokens**: Store tokens in environment variables, not in config files.
- **Private Repositories**: Ensure GitHub token has access to all configured repositories.
- **PII Protection**: Avoid including sensitive information in standup summaries.

### Troubleshooting
- **Missing Activities**: Check if team members' GitHub emails match their accounts.
- **Slack Posting Failures**: Verify webhook URL permissions and channel access.
- **Time Zone Conflicts**: Confirm schedule timezone matches team's working hours.

## Memory and Data Storage

### Historical Data
The skill maintains `standups.log` with:
- Daily activity summaries
- Team participation metrics
- Slack posting history
- Performance trends over time

### Analytics
Use historical data to:
- Track team velocity and productivity
- Identify patterns in work distribution
- Generate weekly/monthly reports
- Forecast completion based on trends

## Integration Points

- **Version Control**: GitHub, GitLab, Bitbucket
- **Project Management**: Jira, Linear, Asana, Trello
- **Communication**: Slack, Microsoft Teams, Discord
- **Documentation**: Confluence, Notion, GitHub Wiki

## References

Load these files when needed:
- `scripts/jira-client.py` - Jira API integration helper
- `scripts/github-client.py` - GitHub API wrapper
- `templates/standup-template.md` - Custom report templates
- `examples/team-configs/` - Example team configurations
