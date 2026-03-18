---
name: pr-analysis
description: >
  Analyzes GitHub pull requests for code quality, security vulnerabilities, performance implications, and best practices. Provides automated code review insights and recommendations.
metadata:
  risk_level: low
  autonomy: fully_auto
  layer: temporal
  human_gate: None - informational only
  cost_management:
    token_limit: 500
    cost_threshold: 0.10
    model_preference: "local:llama.cpp"
---

# Pull Request Analysis Automation

This skill automates the analysis of GitHub pull requests, providing comprehensive code review insights including:

## Analysis Capabilities

### 1. Code Quality Assessment
- **Complexity Analysis**: Identifies overly complex functions and classes
- **Code Smells**: Detects common anti-patterns and poor practices
- **Readability Metrics**: Assesses code clarity and maintainability
- **Best Practices**: Validates adherence to coding standards

### 2. Security Review
- **Vulnerability Detection**: Scans for known security vulnerabilities
- **Input Validation**: Checks for proper sanitization of user inputs
- **Authentication/Authorization**: Reviews access control implementations
- **Data Exposure**: Identifies potential data leakage points

### 3. Performance Impact
- **Algorithm Complexity**: Analyzes time/space complexity changes
- **Resource Usage**: Evaluates memory and CPU usage implications
- **Database Queries**: Reviews query efficiency and optimization
- **Caching Strategy**: Assesses caching implementations

### 4. Architectural Impact
- **Dependency Changes**: Evaluates impact of new dependencies
- **API Changes**: Reviews breaking changes to public interfaces
- **Data Model Changes**: Assesses database schema modifications
- **System Integration**: Evaluates integration points and coupling

## Integration Points

- **GitHub Webhooks**: Automatically triggered on PR creation/updates
- **CI/CD Pipeline**: Integrated into existing build workflows
- **Temporal Orchestration**: Durable execution for long-running analyses
- **Dashboard Integration**: Results displayed in PR comments and dashboards

## Usage

```yaml
# Example workflow trigger
workflows:
  pr-analysis:
    on: pull_request
    skills:
      - pr-analysis
    inputs:
      repository: "owner/repo"
      pr_number: 123
      analysis_scope: ["security", "performance", "quality"]
```

## Output Format

Results are provided in structured JSON format:

```json
{
  "summary": {
    "overall_score": 8.5,
    "severity": "medium",
    "recommendations_count": 12
  },
  "issues": [
    {
      "type": "security",
      "severity": "high",
      "file": "src/auth.go",
      "line": 45,
      "description": "Potential SQL injection vulnerability",
      "recommendation": "Use parameterized queries"
    }
  ],
  "metrics": {
    "complexity_increase": "+15%",
    "test_coverage": "92%",
    "security_score": 7.8
  }
}
```

## Configuration

The skill supports customization through environment variables:

- `ANALYSIS_DEPTH`: Basic, standard, comprehensive
- `SECURITY_RULES`: Custom security rules file
- `QUALITY_THRESHOLDS`: Code quality thresholds
- `EXCLUDE_PATTERNS`: Files/patterns to exclude from analysis
