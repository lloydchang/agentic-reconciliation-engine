---
name: babysit-pr
description: Use when you need to monitor pull requests through CI/CD pipeline and handle failures automatically. Monitors PR status, retries flaky CI, resolves merge conflicts, enables auto-merge when criteria are met, and provides comprehensive PR management for development workflows.
license: AGPLv3
metadata:
  author: agentic-reconciliation-engine
  version: "1.0"
  category: cicd-automation
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: Requires approval for auto-merge to protected branches
compatibility: Requires GitHub API access, CI system integration, and repository permissions
allowed-tools: Bash Read Write Grep
---

# PR Babysitter - Automated Pull Request Management

## Purpose
Automated pull request monitoring and management system that handles CI/CD pipeline failures, retry logic, conflict resolution, and merge automation to streamline development workflows.

## When to Use
- **CI/CD Monitoring**: When you need to monitor PRs through automated testing and deployment pipelines
- **Flaky CI Handling**: When dealing with unreliable CI/CD systems that need automatic retries
- **Merge Conflict Resolution**: When automatically resolving simple merge conflicts in PRs
- **Auto-Merge Management**: When enabling automatic merging for PRs that meet all criteria
- **PR Status Notifications**: When keeping teams informed about PR progress and issues
- **Workflow Optimization**: When reducing manual intervention in the development process
- **Quality Gates**: When enforcing quality standards before automatic merging

## Core Features

### PR Status Monitoring
```python
class PRMonitor:
    def __init__(self, github_client, ci_client):
        self.github = github_client
        self.ci = ci_client
        self.active_prs = {}
    
    def monitor_pr(self, pr_number):
        """Monitor a specific PR through the pipeline"""
        pr = self.github.get_pull_request(pr_number)
        
        # Check CI status
        ci_status = self.ci.get_build_status(pr.head.sha)
        
        # Check required reviews
        reviews = self.github.get_reviews(pr_number)
        required_reviews = self._check_review_requirements(reviews)
        
        # Check merge conflicts
        conflicts = self.github.check_merge_conflicts(pr_number)
        
        return {
            'pr_number': pr_number,
            'status': pr.state,
            'ci_status': ci_status,
            'reviews': required_reviews,
            'conflicts': conflicts,
            'mergeable': pr.mergeable
        }
```

### Automatic Retry Logic
```python
class CIRetryHandler:
    def __init__(self, max_retries=3, retry_delay=300):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_history = {}
    
    def should_retry(self, pr_number, build_result):
        """Determine if a build should be retried"""
        if build_result.status == 'success':
            return False
        
        retry_count = self.retry_history.get(pr_number, 0)
        if retry_count >= self.max_retries:
            return False
        
        # Check if failure is retryable
        return self._is_retryable_failure(build_result)
    
    def _is_retryable_failure(self, build_result):
        """Check if failure type is suitable for retry"""
        retryable_patterns = [
            'timeout',
            'network error',
            'infrastructure failure',
            'flaky test',
            'resource constraint'
        ]
        
        failure_message = build_result.message.lower()
        return any(pattern in failure_message for pattern in retryable_patterns)
    
    def retry_build(self, pr_number):
        """Retry a failed build"""
        retry_count = self.retry_history.get(pr_number, 0) + 1
        self.retry_history[pr_number] = retry_count
        
        # Trigger new build
        build_id = self.ci.trigger_build(pr_number)
        
        # Schedule monitoring
        self._schedule_build_monitoring(pr_number, build_id)
        
        return {
            'retry_count': retry_count,
            'build_id': build_id,
            'max_retries': self.max_retries
        }
```

### Merge Conflict Resolution
```python
class ConflictResolver:
    def __init__(self, github_client):
        self.github = github_client
    
    def resolve_conflicts(self, pr_number):
        """Attempt to resolve merge conflicts"""
        pr = self.github.get_pull_request(pr_number)
        
        if not pr.mergeable:
            conflicts = self._detect_conflicts(pr)
            resolution_attempts = []
            
            for conflict in conflicts:
                resolution = self._attempt_resolution(conflict)
                if resolution.success:
                    resolution_attempts.append(resolution)
            
            if resolution_attempts:
                # Create commit with resolutions
                commit_sha = self._commit_resolutions(pr_number, resolution_attempts)
                return {
                    'resolved': True,
                    'commit_sha': commit_sha,
                    'resolutions': resolution_attempts
                }
        
        return {'resolved': False, 'reason': 'No conflicts or unresolvable'}
    
    def _detect_conflicts(self, pr):
        """Detect specific conflict types"""
        # Implementation for detecting common conflict patterns
        return []
    
    def _attempt_resolution(self, conflict):
        """Attempt to resolve a specific conflict"""
        # Implementation for conflict resolution logic
        return ConflictResolution(success=False)
```

## Configuration

### Repository Settings
```yaml
# pr-babysitter-config.yaml
repository: "company/product"
protected_branches:
  - main
  - production
  - staging

auto_merge_rules:
  require_tests_pass: true
  require_code_review: true
  require_approval_count: 2
  max_age_hours: 72
  exclude_labels: ["wip", "do-not-merge"]

retry_configuration:
  max_retries: 3
  retry_delay_seconds: 300
  flaky_test_patterns:
    - "integration_test_*"
    - "e2e_test_*"
    - "performance_test_*"

notification_settings:
  slack:
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#pr-updates"
    notify_on_failure: true
    notify_on_merge: true
  
  github:
    comment_on_retry: true
    comment_on_conflict_resolution: true
    comment_on_auto_merge: true
```

### Quality Gates
```python
class QualityGates:
    def __init__(self, config):
        self.config = config
    
    def check_merge_eligibility(self, pr):
        """Check if PR is eligible for auto-merge"""
        checks = {
            'ci_status': self._check_ci_status(pr),
            'code_review': self._check_code_review(pr),
            'age_check': self._check_pr_age(pr),
            'label_check': self._check_labels(pr),
            'conflict_check': self._check_conflicts(pr)
        }
        
        return all(checks.values()), checks
    
    def _check_ci_status(self, pr):
        """Check if all CI checks are passing"""
        required_checks = self.config.get('required_ci_checks', [])
        for check in required_checks:
            status = self.github.get_commit_status(pr.head.sha, check)
            if status.state != 'success':
                return False
        return True
    
    def _check_code_review(self, pr):
        """Check code review requirements"""
        required_approvals = self.config.get('required_approvals', 1)
        approvals = [r for r in pr.reviews if r.state == 'APPROVED']
        return len(approvals) >= required_approvals
    
    def _check_pr_age(self, pr):
        """Check PR age requirements"""
        max_age_hours = self.config.get('max_age_hours', 72)
        age_hours = (datetime.now() - pr.created_at).total_seconds() / 3600
        return age_hours <= max_age_hours
    
    def _check_labels(self, pr):
        """Check for blocking labels"""
        blocking_labels = self.config.get('blocking_labels', [])
        pr_labels = [label.name for label in pr.labels]
        return not any(label in pr_labels for label in blocking_labels)
```

## Gotchas

### Common Pitfalls
- **False Positives**: Auto-merge may trigger for PRs that shouldn't be merged
- **Merge Conflicts**: Automatic conflict resolution may introduce bugs
- **CI Retry Logic**: Excessive retries can waste CI resources and delay feedback
- **Permission Issues**: Service accounts may lack necessary permissions for operations

### Edge Cases
- **Large PRs**: Very large PRs may timeout during conflict resolution
- **Protected Branches**: Some branches may have additional protection rules
- **External Dependencies**: CI failures due to external services may not be retryable
- **Concurrent Operations**: Multiple operations on the same PR may conflict

### Performance Issues
- **API Rate Limits**: GitHub API has strict rate limits for PR operations
- **CI Queue Delays**: High CI queue times can delay PR processing
- **Database Locks**: Concurrent PR updates may cause database contention
- **Memory Usage**: Monitoring many PRs simultaneously can consume significant memory

### Security Considerations
- **Credential Management**: Service account credentials must be securely stored
- **Access Control**: PR babysitter needs appropriate but limited permissions
- **Audit Trail**: All automated actions must be logged for security compliance
- **Code Review**: Automated merges should not bypass required code review processes

### Troubleshooting
- **Stuck PRs**: PRs may get stuck in processing state due to API failures
- **Merge Failures**: Auto-merge may fail due to race conditions or conflicts
- **CI Integration**: CI system integration may fail due to API changes
- **Notification Failures**: External notifications may fail due to network issues

## Integration Examples

### GitHub Actions Integration
```yaml
# .github/workflows/pr-babysitter.yml
name: PR Babysitter

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  babysit-pr:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout PR
        uses: actions/checkout@v3
        with:
          token: ${{ secrets.BABYSITTER_TOKEN }}
      
      - name: Run PR Babysitter
        run: |
          python -m pr_babysitter monitor \
            --pr-number ${{ github.event.number }} \
            --repo ${{ github.repository }} \
            --token ${{ secrets.BABYSITTER_TOKEN }}
```

### Slack Integration
```python
class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def notify_pr_update(self, pr, event_type, details):
        """Send PR update notification to Slack"""
        message = {
            "text": f"PR #{pr.number}: {event_type}",
            "attachments": [{
                "color": self._get_color_for_event(event_type),
                "fields": [
                    {"title": "Title", "value": pr.title, "short": True},
                    {"title": "Author", "value": pr.user.login, "short": True},
                    {"title": "Details", "value": details, "short": False}
                ],
                "actions": [
                    {
                        "type": "button",
                        "text": "View PR",
                        "url": pr.html_url
                    }
                ]
            }]
        }
        
        requests.post(self.webhook_url, json=message)
    
    def _get_color_for_event(self, event_type):
        colors = {
            'retry_triggered': 'warning',
            'conflict_resolved': 'good',
            'auto_merged': 'good',
            'merge_failed': 'danger'
        }
        return colors.get(event_type, 'gray')
```

## Monitoring and Analytics

### PR Metrics Dashboard
```python
class PRMetrics:
    def __init__(self, analytics_db):
        self.db = analytics_db
    
    def get_pr_statistics(self, time_period_days=30):
        """Get PR statistics for dashboard"""
        query = """
        SELECT 
            COUNT(*) as total_prs,
            COUNT(CASE WHEN auto_merged = true THEN 1 END) as auto_merged_prs,
            COUNT(CASE WHEN retries_attempted > 0 THEN 1 END) as retried_prs,
            COUNT(CASE WHEN conflicts_resolved > 0 THEN 1 END) as conflict_resolved_prs,
            AVG(time_to_merge_hours) as avg_time_to_merge,
            AVG(ci_execution_time_minutes) as avg_ci_time
        FROM pr_metrics 
        WHERE created_at >= NOW() - INTERVAL '%s days'
        """ % time_period_days
        
        return self.db.execute(query).fetchone()
    
    def get_failure_patterns(self):
        """Analyze common failure patterns"""
        query = """
        SELECT 
            failure_type,
            COUNT(*) as occurrences,
            AVG(retry_success_rate) as avg_retry_success
        FROM ci_failures 
        WHERE timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY failure_type
        ORDER BY occurrences DESC
        """
        
        return self.db.execute(query).fetchall()
```

## References

Load these files when needed:
- `scripts/pr-monitor.py` - Core PR monitoring and status tracking
- `scripts/conflict-resolver.py` - Merge conflict detection and resolution
- `scripts/quality-gates.py` - Quality gate validation and enforcement
- `references/github-api-patterns.md` - GitHub API integration patterns
- `examples/notification-templates/` - Slack and email notification templates
