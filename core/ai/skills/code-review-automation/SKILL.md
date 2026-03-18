---
name: code-review-automation
description: >
  Automates code review processes using AI to analyze pull requests, suggest improvements,
  check for security vulnerabilities, and enforce coding standards. Provides intelligent
  code analysis and automated feedback on code changes.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for automated merges
  cost_limit: 120
  execution_model: "local:llama.cpp"
  planning_model: "local:llama.cpp"
  cost_management:
    token_limit: 120
    cost_threshold: 0.12 # USD
    model_preference: "local:llama.cpp"
  execution:
    background_enabled: true
    parallel_capable: true
    notification_channels: ["github", "slack"]
  dependencies:
    required_skills: []
    conflicts_with: []
    order_constraints: []
---

# Code Review Automation Skill

This skill automates the code review process using AI to provide intelligent analysis, security checks, and quality feedback on pull requests.

## When to Use

Use this skill when:
- Pull requests need automated code review
- Security vulnerability scanning is required
- Code quality and style enforcement is needed
- Performance analysis should be automated
- Documentation and testing completeness checks are needed

## What This Skill Does

### 1. Code Analysis
- Analyzes code changes in pull requests
- Identifies potential bugs and issues
- Checks for code style and formatting violations
- Evaluates code complexity and maintainability
- Reviews architectural decisions and patterns

### 2. Security Scanning
- Scans for common security vulnerabilities
- Checks for hardcoded secrets and credentials
- Validates input sanitization and output encoding
- Reviews authentication and authorization logic
- Identifies dependency security issues

### 3. Performance Analysis
- Identifies performance bottlenecks
- Reviews algorithm efficiency
- Checks resource usage patterns
- Analyzes database query optimization
- Evaluates caching strategies

### 4. Testing Validation
- Checks test coverage for changed code
- Validates test quality and effectiveness
- Reviews test structure and organization
- Identifies missing edge case tests
- Suggests additional test scenarios

### 5. Documentation Review
- Validates code documentation completeness
- Checks API documentation accuracy
- Reviews inline comments and explanations
- Validates README and guide updates
- Ensures changelog entries are present

### 6. Integration Checks
- Validates integration with existing systems
- Checks API compatibility and breaking changes
- Reviews configuration and deployment changes
- Validates monitoring and logging additions
- Checks backward compatibility

## Implementation Details

### Required Tools and Access
- GitHub API access for pull request analysis
- Code analysis tools (SonarQube, ESLint, etc.)
- Security scanning tools (Bandit, Snyk, etc.)
- Test coverage tools (Coverage.py, Jest, etc.)
- Documentation generation tools

### Configuration Requirements
```yaml
code_review_automation:
  enabled_checks:
    - security_scan
    - code_quality
    - performance_analysis
    - test_coverage
    - documentation
  thresholds:
    security_score: 8.0
    quality_score: 7.5
    coverage_threshold: 80
    complexity_limit: 10
  notification_settings:
    github_comments: true
    slack_alerts: true
    email_reports: false
  exclusions:
    - "test/**"
    - "docs/**"
    - "*.md"
  custom_rules:
    - "no_hardcoded_secrets"
    - "proper_error_handling"
    - "api_versioning"
```

### Execution Steps

1. **Pre-flight Checks**
   - Validate GitHub API access
   - Check pull request permissions
   - Verify analysis tools availability

2. **Code Discovery**
   - Run: `scripts/discover-changes.sh`
   - Output: `code-changes.json`

3. **Security Analysis**
   - Run: `scripts/security-scan.sh`
   - Output: `security-report.json`

4. **Quality Analysis**
   - Run: `scripts/quality-check.sh`
   - Output: `quality-report.json`

5. **Performance Analysis**
   - Run: `scripts/performance-analysis.sh`
   - Output: `performance-report.json`

6. **Testing Analysis**
   - Run: `scripts/test-analysis.sh`
   - Output: `test-report.json`

7. **Documentation Review**
   - Run: `scripts/documentation-check.sh`
   - Output: `documentation-report.json`

8. **Report Generation**
   - Run: `scripts/generate-report.sh`
   - Output: `review-summary.md`

9. **Comment Posting**
   - Run: `scripts/post-comments.sh`
   - Output: GitHub PR comments

## Success Criteria

- All security vulnerabilities are identified and reported
- Code quality meets defined thresholds
- Test coverage meets minimum requirements
- Performance issues are highlighted
- Documentation is complete and accurate
- Review comments are helpful and actionable

## Error Handling

### Common Issues
- GitHub API rate limiting
- Analysis tool failures
- Large code base timeouts
- Missing test files
- Documentation parsing errors

### Recovery Procedures
- API rate limiting: Implement exponential backoff
- Tool failures: Fall back to alternative analysis methods
- Timeouts: Split analysis into smaller chunks
- Missing tests: Flag for manual review
- Parsing errors: Log warnings and continue

## Monitoring and Observability

### Metrics to Track
- Number of PRs reviewed
- Security issues found
- Quality scores distribution
- Test coverage improvements
- Review completion time
- Developer satisfaction scores

### Logging Requirements
- Detailed analysis logs
- Security vulnerability reports
- Quality assessment details
- Performance bottleneck identification
- Error and warning messages

## Security Considerations

- Secure handling of sensitive code
- Protection of API credentials
- Secure storage of analysis results
- Audit trail for all reviews
- Compliance with security policies

## Integration Points

- **Version Control**: GitHub, GitLab, Bitbucket
- **CI/CD**: Jenkins, GitHub Actions, GitLab CI
- **Code Analysis**: SonarQube, CodeClimate, Codacy
- **Security Tools**: Snyk, OWASP ZAP, Bandit
- **Testing**: Jest, PyTest, Coverage.py

## References

Load these files when needed:
- `scripts/discover-changes.sh` - Code discovery script
- `scripts/security-scan.sh` - Security scanning script
- `scripts/quality-check.sh` - Code quality analysis script
- `scripts/performance-analysis.sh` - Performance analysis script
- `references/coding-standards.md` - Coding standards documentation
- `references/security-policies.md` - Security policy requirements
