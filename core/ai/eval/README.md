# AI Agent Tracing Evaluation Framework

Comprehensive evaluation framework for analyzing Pi-Mono agent traces from Langfuse observability data.

## Overview

This framework provides automated evaluation of AI agent performance and behavior by analyzing trace data from Langfuse. It helps ensure agents are operating correctly, skills are being invoked properly, and performance meets expectations.

## Features

### Evaluators

1. **Skill Invocation Evaluator** (`skill_invocation_evaluator.py`)
   - Evaluates whether skills are properly invoked for GitOps operations
   - Checks timing correctness and skill coverage
   - Generates skill usage reports

2. **Performance Evaluator** (`performance_evaluator.py`)
   - Analyzes latency, throughput, and resource utilization
   - Tracks error rates and performance trends
   - Provides performance tier classification

### Core Framework

- **Multi-Evaluator Support**: Run multiple evaluators simultaneously
- **Batch Processing**: Analyze large volumes of trace data
- **Flexible Input**: Load from files or Langfuse API
- **Multiple Output Formats**: JSON, summary, detailed reports
- **Trend Analysis**: Track performance over time

## Installation

```bash
# Clone repository
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine/agent-tracing-evaluation

# Install dependencies
pip install -r requirements.txt

# Make executable
chmod +x main.py
```

## Quick Start

### Basic Usage

```bash
# Evaluate traces from JSON file
python main.py --file traces.json

# Run specific evaluators
python main.py --file traces.json --evaluators skill_invocation performance

# Generate detailed report
python main.py --file traces.json --format detailed

# Save report to file
python main.py --file traces.json --output report.txt --format summary
```

### Advanced Usage

```bash
# Load traces from Langfuse API
python main.py --langfuse --config langfuse-config.json

# Run with custom configuration
python main.py --file traces.json \
  --evaluators all \
  --format detailed \
  --output evaluation-report.json
```

## Configuration

### Langfuse Configuration

Create `langfuse-config.json`:

```json
{
  "secret_key": "sk-lf-...",
  "public_key": "pk-lf-...",
  "host": "https://us.cloud.langfuse.com",
  "project": "pi-mono-agent",
  "time_range": {
    "start": "2026-03-16T00:00:00Z",
    "end": "2026-03-17T00:00:00Z"
  }
}
```

### Trace Data Format

The framework expects trace data in the following format:

```json
{
  "traces": [
    {
      "id": "trace-123",
      "timestamp": 1678901234567,
      "duration": {"duration_ms": 800},
      "attributes": {
        "operation_type": "cost-optimization",
        "skill_invoked": true,
        "memory_usage_mb": 750,
        "cpu_usage_percent": 45
      },
      "usage": {
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150
      },
      "events": [
        {
          "name": "skill_loaded",
          "level": "info",
          "timestamp": 1000
        },
        {
          "name": "workflow_started",
          "level": "info", 
          "timestamp": 1100
        }
      ]
    }
  ]
}
```
                Alerting & Optimization
```

## Implementation

### 1. Enhanced Tracing Setup

#### Custom GitOps Metrics
```go
// temporal/workflows/gitops-tracing.go
import (
    "github.com/langfuse/langfuse-go"
    "go.temporal.io/sdk/workflow"
)

type GitOpsTraceMetrics struct {
    SkillInvoked          bool     `json:"skill_invoked"`
    RiskLevel            string   `json:"risk_level"`
    AutonomyLevel        string   `json:"autonomy_level"`
    HumanGateRequired    bool     `json:"human_gate_required"`
    StructuredOutput     bool     `json:"structured_output"`
    ExecutionTime        int64    `json:"execution_time_ms"`
    TokenUsage           int      `json:"token_usage"`
    SuccessRate          float64  `json:"success_rate"`
}

func (w *GitOpsWorkflow) Execute(ctx workflow.Context, input GitOpsRequest) error {
    // Enhanced tracing with GitOps metrics
    span := langfuse.NewSpan(ctx, "gitops-workflow", langfuse.SpanAttributes{
        "skill_name": input.SkillName,
        "risk_level": input.RiskLevel,
        "operation_type": input.OperationType,
    })

    defer span.End()

    // Execute workflow with comprehensive tracing
    result, err := w.executeWithTracing(ctx, span, input)

    // Record custom GitOps metrics
    span.SetAttributes(langfuse.SpanAttributes{
        "skill_invoked": result.SkillInvoked,
        "human_gate_required": result.HumanGateRequired,
        "structured_output": result.StructuredOutput,
        "execution_time": result.ExecutionTime,
        "token_usage": result.TokenUsage,
        "success_rate": result.SuccessRate,
    })

    return err
}
```

### 2. Custom GitOps Evaluators

#### Skill Invocation Evaluator
```python
# evaluators/skill-invocation-evaluator.py
from langfuse import LangfuseEvaluator

class GitOpsSkillEvaluator(LangfuseEvaluator):
    """Evaluates whether skills are properly invoked for GitOps tasks"""

    def evaluate(self, trace):
        """Evaluate skill invocation effectiveness"""
        # Check if skill was invoked
        skill_invoked = trace.attributes.get("skill_invoked", False)

        # Check if operation was skill-appropriate
        operation_type = trace.attributes.get("operation_type", "")
        should_use_skill = self._should_use_skill(operation_type)

        # Check timing - skill loaded before execution
        timing_correct = self._check_invocation_timing(trace)

        score = 0.0
        if skill_invoked and should_use_skill and timing_correct:
            score = 1.0
        elif not should_use_skill and not skill_invoked:
            score = 1.0  # Correctly didn't invoke for non-skill operations
        elif skill_invoked and not should_use_skill:
            score = 0.5  # Wrongly invoked skill
        elif should_use_skill and not skill_invoked:
            score = 0.3  # Failed to invoke when should have

        return {
            "score": score,
            "passed": score >= 0.8,
            "details": {
                "skill_invoked": skill_invoked,
                "should_use_skill": should_use_skill,
                "timing_correct": timing_correct
            }
        }

    def _should_use_skill(self, operation_type):
        """Determine if operation should use skills vs direct execution"""
        skill_operations = [
            "cost-optimization", "security-scan", "deployment-strategy",
            "infrastructure-provisioning", "database-maintenance"
        ]
        return operation_type in skill_operations

    def _check_invocation_timing(self, trace):
        """Check if skill was invoked at the right time"""
        events = trace.events
        skill_load_events = [e for e in events if e.name == "skill_loaded"]
        execution_events = [e for e in events if e.name == "workflow_started"]

        if not skill_load_events or not execution_events:
            return False

        skill_load_time = skill_load_events[0].timestamp
        execution_time = execution_events[0].timestamp

        # Skill should be loaded before execution starts
        return skill_load_time < execution_time
```

#### Risk Compliance Evaluator
```python
# evaluators/risk-compliance-evaluator.py
from langfuse import LangfuseEvaluator

class GitOpsRiskEvaluator(LangfuseEvaluator):
    """Evaluates risk compliance in GitOps operations"""

    def evaluate(self, trace):
        """Evaluate risk assessment and compliance"""
        risk_level = trace.attributes.get("risk_level", "unknown")
        autonomy_level = trace.attributes.get("autonomy_level", "unknown")
        human_gate_used = trace.attributes.get("human_gate_required", False)

        # Risk level compliance
        risk_compliant = self._check_risk_compliance(risk_level, autonomy_level)

        # Human gate compliance
        gate_compliant = self._check_gate_compliance(risk_level, human_gate_used)

        # Structured output compliance
        output_compliant = trace.attributes.get("structured_output", False)

        score = 0.0
        if risk_compliant and gate_compliant and output_compliant:
            score = 1.0
        else:
            score = 0.7  # Partial compliance

        return {
            "score": score,
            "passed": score >= 0.8,
            "details": {
                "risk_compliant": risk_compliant,
                "gate_compliant": gate_compliant,
                "output_compliant": output_compliant,
                "risk_level": risk_level,
                "autonomy_level": autonomy_level
            }
        }

    def _check_risk_compliance(self, risk_level, autonomy_level):
        """Check if autonomy level matches risk assessment"""
        risk_matrix = {
            "low": ["fully_auto"],
            "medium": ["conditional"],
            "high": ["requires_PR"]
        }
        allowed_autonomies = risk_matrix.get(risk_level, [])
        return autonomy_level in allowed_autonomies

    def _check_gate_compliance(self, risk_level, human_gate_used):
        """Check if human gate is used appropriately"""
        requires_gate = risk_level in ["medium", "high"]
        return requires_gate == human_gate_used
```

### 3. Evaluation Pipeline Setup

#### Automated Evaluation Runner
```python
# pipelines/evaluation-runner.py
import asyncio
from langfuse import Langfuse
from evaluators.skill-invocation-evaluator import GitOpsSkillEvaluator
from evaluators.risk-compliance-evaluator import GitOpsRiskEvaluator
import pandas as pd

class GitOpsEvaluationPipeline:
    """Automated evaluation pipeline for GitOps agents"""

    def __init__(self):
        self.langfuse = Langfuse()
        self.evaluators = [
            GitOpsSkillEvaluator(),
            GitOpsRiskEvaluator()
        ]

    async def run_evaluation(self, time_range="24h"):
        """Run evaluation on recent traces"""
        # Get traces from last time period
        traces = self.langfuse.get_traces(
            from_timestamp=f"now-{time_range}",
            tags=["gitops-workflow"]
        )

        results = []
        for trace in traces:
            trace_results = await self.evaluate_trace(trace)
            results.extend(trace_results)

        # Generate report
        report = self.generate_evaluation_report(results)

        # Store results for dashboard
        self.store_evaluation_results(report)

        return report

    async def evaluate_trace(self, trace):
        """Evaluate a single trace with all evaluators"""
        results = []

        for evaluator in self.evaluators:
            try:
                result = evaluator.evaluate(trace)
                result["trace_id"] = trace.id
                result["timestamp"] = trace.timestamp
                result["evaluator"] = evaluator.__class__.__name__
                results.append(result)
            except Exception as e:
                # Log evaluation errors
                results.append({
                    "trace_id": trace.id,
                    "evaluator": evaluator.__class__.__name__,
                    "error": str(e),
                    "score": 0.0,
                    "passed": False
                })

        return results

    def generate_evaluation_report(self, results):
        """Generate comprehensive evaluation report"""
        df = pd.DataFrame(results)

        report = {
            "summary": {
                "total_traces": len(df),
                "average_score": df["score"].mean(),
                "pass_rate": (df["passed"] == True).mean(),
                "evaluation_timestamp": pd.Timestamp.now()
            },
            "by_evaluator": df.groupby("evaluator").agg({
                "score": ["mean", "std"],
                "passed": "mean",
                "trace_id": "count"
            }).to_dict(),
            "failing_traces": df[~df["passed"]].to_dict("records"),
            "trends": self.calculate_trends(df)
        }

        return report

    def calculate_trends(self, df):
        """Calculate performance trends"""
        df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour

        trends = df.groupby("hour").agg({
            "score": "mean",
            "passed": "mean"
        }).to_dict()

        return trends

    def store_evaluation_results(self, report):
        """Store results for dashboard consumption"""
        # Store in database or file system for dashboard access
        with open("evaluation-results/latest.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
```

### 4. CI/CD Integration

#### GitHub Actions Workflow
```yaml
# .github/workflows/agent-evaluation.yml
name: Agent Evaluation Pipeline

on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install langfuse pandas

    - name: Run evaluation pipeline
      run: |
        cd agent-tracing-evaluation
        python pipelines/evaluation-runner.py --time-range 24h

    - name: Upload evaluation results
      uses: actions/upload-artifact@v3
      with:
        name: evaluation-report
        path: agent-tracing-evaluation/evaluation-results/

    - name: Check evaluation thresholds
      run: |
        python scripts/check-evaluation-thresholds.py

    - name: Send notifications
      if: failure()
      run: |
        python scripts/send-evaluation-alert.py
```

## Usage

### Running Evaluations
```bash
# Run evaluation on recent traces
cd agent-tracing-evaluation
python pipelines/evaluation-runner.py --time-range 24h

# Evaluate specific trace
python pipelines/evaluation-runner.py --trace-id abc-123-def

# Generate performance report
python scripts/generate-performance-report.py
```

### Custom Evaluator Development
```python
# evaluators/custom-evaluator.py
from langfuse import LangfuseEvaluator

class CustomGitOpsEvaluator(LangfuseEvaluator):
    """Your custom GitOps evaluator"""

    def evaluate(self, trace):
        # Implement your evaluation logic
        return {
            "score": calculated_score,
            "passed": score >= threshold,
            "details": evaluation_details
        }
```

## Metrics and Alerts

### Key Metrics Tracked
- **Skill Invocation Rate**: Percentage of operations correctly using skills
- **Risk Compliance**: Proper risk assessment and human gating
- **Structured Output Rate**: JSON plan generation compliance
- **Execution Success Rate**: End-to-end workflow success
- **Performance Trends**: Response times and resource usage

### Alerting Rules
- Skill invocation rate drops below 80%
- Risk compliance failures in production
- Structured output rate below 95%
- Evaluation pipeline failures

## Integration with Existing Systems

This evaluation framework integrates seamlessly with:

- **Langfuse**: Leverages existing Temporal tracing
- **AGENTS.md**: Compressed context for better agent performance
- **GitOps Pipeline**: Validates structured outputs and PR workflows
- **Monitoring Stack**: Prometheus metrics and Grafana dashboards

## Results Storage

Evaluation results are stored in:
- `evaluation-results/latest.json`: Most recent evaluation
- `evaluation-results/history/`: Historical results by date
- Database integration for dashboard consumption

This provides comprehensive observability and systematic improvement capabilities for your GitOps agent system.
