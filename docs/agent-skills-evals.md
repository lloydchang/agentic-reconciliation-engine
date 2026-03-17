# Agent Skills Evaluation Framework

This document adapts the OpenAI Codex evaluation methodology to the gitops-infra-control-plane skills system, providing systematic testing and improvement tracking for AI agent skills.

**Source**: [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills) (OpenAI, Jan 22, 2026)

## Overview

Building on the [OpenAI Evals for Agent Skills](https://developers.openai.com/blog/eval-skills) approach, we implement structured evaluation for our skills following the [agentskills.io specification](https://agentskills.io/specification). Instead of relying on subjective "feels better" assessments, we use concrete, measurable criteria to track skill performance over time.

## Core Evaluation Concept

An eval consists of:
- **Prompt** → **Captured Run** (trace + artifacts) → **Checks** → **Score**

For our skills, this translates to:
- Natural language prompt triggering the skill
- JSONL trace from Temporal workflow execution
- Deterministic checks against expected behavior
- Structured scoring for comparison over time

## Success Criteria Categories

### 1. Outcome Goals
- Did the task complete successfully?
- Do resulting artifacts work as intended?
- Are all required outputs present?

### 2. Process Goals
- Did the agent invoke the correct skill?
- Were expected Temporal activities executed?
- Did the workflow follow intended steps?

### 3. Style Goals
- Do outputs follow our conventions?
- Is code structure consistent with project standards?
- Are naming conventions adhered to?

### 4. Efficiency Goals
- No unnecessary workflow executions
- Reasonable token usage
- Minimal thrashing or retries

## Skills Structure

Our skills follow the agentskills.io format:
```
core/ai/skills/[skill-name]/
├── SKILL.md          # Required: name, description, metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates/resources
```

### SKILL.md Frontmatter
```yaml
---
name: cost-optimizer
description: >
  Analyses cloud spend and recommends cost reductions. Use when asked to reduce
  costs, right-size resources, or analyse billing across AWS, Azure, or GCP.
metadata:
  risk_level: medium
  autonomy: conditional
  layer: temporal
  human_gate: PR approval required for changes > $100/day savings
---
```

## Evaluation Implementation

### 1. Define Success Before Implementation

For each skill, establish clear success criteria:

**Example for cost-optimizer skill:**
- **Outcome**: Cost analysis report generated with savings recommendations
- **Process**: AWS/Azure/GCP APIs queried, Temporal activities executed
- **Style**: Report follows JSON schema, recommendations prioritized by impact
- **Efficiency**: Single workflow execution, <5 API calls per provider

### 2. Create Eval Dataset

Use CSV format for test cases: `evals/[skill-name].prompts.csv`

```csv
id,should_trigger,prompt,expected_outcome
test-01,true,"Analyze AWS costs and find savings opportunities",cost_report_generated
test-02,true,"Optimize GCP spend for production environment",cost_report_generated
test-03,false,"Set up a new Kubernetes cluster",no_action
test-04,true,"Show me Azure billing analysis",cost_report_generated
```

### 3. Deterministic Checks

Implement checks against Temporal workflow traces:

```javascript
// evals/check-cost-optimizer.mjs
function checkApiCallsExecuted(events) {
  return events.some(e =>
    e.type === 'activity.completed' &&
    e.activity.name.includes('query_aws_costs')
  );
}

function checkReportGenerated(workflowResult) {
  return workflowResult.output &&
         workflowResult.output.savings_recommendations?.length > 0;
}

function checkHumanGateApplied(events, riskLevel) {
  if (riskLevel === 'high') {
    return events.some(e => e.type === 'human_approval_requested');
  }
  return true;
}
```

### 4. Structured Rubric Evaluation

For qualitative aspects, use schema-constrained evaluation:

```json
// evals/cost-optimizer-rubric.schema.json
{
  "type": "object",
  "properties": {
    "overall_pass": { "type": "boolean" },
    "score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "pass": { "type": "boolean" },
          "notes": { "type": "string" }
        },
        "required": ["id", "pass", "notes"]
      }
    }
  },
  "required": ["overall_pass", "score", "checks"]
}
```

### 5. Integration with Temporal Orchestration

Our evaluation framework integrates with the existing Temporal layer:

- **Workflow Discovery**: Agent loads skill based on description match
- **Context Retrieval**: Memory agent provides historical performance data
- **Plan Generation**: Structured JSON plan from skill instructions
- **Risk Assessment**: Plan tagged with risk level and autonomy settings
- **GitOps Execution**: Changes flow through PR validation
- **Results Recording**: Success/failure stored in memory for future context

### 6. Evaluation Runner

```javascript
// evals/run-skill-evals.mjs
import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";

async function runSkillEval(skillName, testCase) {
  const tracePath = path.join('evals', 'artifacts', `${testCase.id}.jsonl`);

  // Execute via Temporal workflow
  const result = await executeTemporalWorkflow(skillName, testCase.prompt);

  // Save trace
  writeFileSync(tracePath, JSON.stringify(result.trace, null, 2));

  // Run deterministic checks
  const checks = {
    triggeredCorrectly: checkSkillTriggered(result, skillName),
    completedSuccessfully: checkWorkflowCompleted(result),
    followedProcess: checkProcessCompliance(result, skillName),
    meetsStyleGuidelines: checkStyleCompliance(result)
  };

  // Run qualitative rubric if needed
  if (testCase.needsRubric) {
    const rubricResult = await runRubricEval(skillName, result);
    checks.rubricScore = rubricResult.score;
  }

  return {
    testCase: testCase.id,
    passed: Object.values(checks).every(c => c === true || (typeof c === 'number' && c >= 80)),
    checks,
    tracePath
  };
}
```

### 7. Risk-Based Evaluation

Evaluation adapts based on skill risk level:

- **Low Risk**: Basic checks, no human gate
- **Medium Risk**: Process verification, optional human review
- **High Risk**: Full audit trail, mandatory human approval

### 8. Continuous Improvement

- **Regression Detection**: Automated runs catch behavior changes
- **Performance Tracking**: Token usage, execution time monitoring
- **Coverage Expansion**: Add test cases for discovered edge cases
- **Model Updates**: Use eval results to refine skill prompts and logic

## Integration Points

### CI/CD Integration
- GitHub Actions workflow runs evals on skill changes
- Results posted as PR comments
- Blocking checks for high-risk skills

### Monitoring Integration
- Eval metrics feed into Prometheus/Grafana dashboards
- Alert on eval failures or performance regressions
- Historical trend analysis

### Memory Agent Integration
- Successful eval runs stored as episodic memory
- Failed cases used to improve skill descriptions
- Performance patterns inform workflow optimization

## Best Practices

1. **Start Small**: Begin with 5-10 test cases per skill
2. **Automate Early**: Integrate evals into CI from day one
3. **Measure What Matters**: Focus on user-facing outcomes first
4. **Fail Fast**: Use deterministic checks for quick feedback
5. **Evolve Gradually**: Add complexity only when it reduces risk

## Example: Cost Optimizer Eval

**Test Case**: "Find ways to reduce AWS costs for our production environment"

**Deterministic Checks**:
- ✅ Workflow triggered for cost-optimizer skill
- ✅ AWS Cost Explorer API called
- ✅ Report generated with savings > $1000/month
- ✅ No destructive actions taken

**Rubric Evaluation**:
- ✅ Recommendations prioritized by impact
- ✅ Clear implementation steps provided
- ✅ Risk assessment included
- ✅ Score: 95/100

This framework ensures our skills remain reliable, efficient, and aligned with our GitOps principles as they evolve over time.
