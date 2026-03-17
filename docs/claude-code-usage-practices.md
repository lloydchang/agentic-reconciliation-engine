# Claude Code Usage Practices: 13 Practical Moves

## Overview

This document summarizes the practical workflow patterns shared by Boris Cherny, creator of Claude Code, for effective AI-assisted development. These "vanilla" but disciplined approaches emphasize consistency, verification, and systematic automation over raw speed.

## Target Audience

- Teams already using Claude Code seeking more consistent results
- Workflow managers wanting shared team guardrails
- Developers comfortable with basic automation setup

## Core Principles

- **Consistency over speed**: Choose one model and stick with it
- **Verification loops**: Build systems for Claude to validate its own work
- **Progressive automation**: Start small, add hooks and commands iteratively
- **Parallel workflows**: Run multiple sessions simultaneously for throughput

## The 13 Practical Moves

### 1. Run Multiple Claudes in Parallel — and Label Them

Maintain 5+ terminal sessions simultaneously with numbered tabs for easy tracking. Use system notifications to monitor background sessions.

**Why it works**: Enables momentum across independent tasks without waiting.

**Implementation**: Start with two sessions ("refactor" and "tests"), keep them separate through commit.

### 2. Mix Local and Web Sessions Purposefully

Run browser sessions alongside local terminals (5-10 total). Use web UI at claude.ai/code for cleaner views or mobile work.

**Why it works**: Match interface to task requirements.

**Implementation**: Reserve web sessions for "review and reasoning", local for "edit execution".

### 3. Pick a Model, Then Stick With It for Coding

Use a single model (e.g., Opus 4.5 with thinking) consistently for all coding tasks.

**Why it works**: Reduced back-and-forth often makes end-to-end work faster despite slower individual responses.

**Implementation**: Commit to one model for a week, measure re-prompting frequency before changing.

### 4. Treat CLAUDE.md as Living Team Memory

Maintain a shared CLAUDE.md file in git with:
- Command patterns and shortcuts
- Code style guidelines
- Workflow rules
- Common mistake corrections

Keep it concise (<2000 tokens) and update via PRs.

**Example structure**:
```markdown
# Bash commands
- pnpm test --filter <name>: run focused test
- pnpm lint: run lint before pushing

# Code style
- Prefer early returns over nested ifs
- Use named exports

# Workflow
- Write tests first for non-trivial changes
- Update docs when behavior changes
```

### 5. Start in Plan Mode, Then Switch to Auto-Accept Edits

Begin PR work in Plan mode (Shift+Tab twice) to iterate on approach. Once plan solidifies, switch to auto-accept for rapid execution.

**Why it works**: Plan provides safety rails, auto-accept accelerates implementation.

**Implementation**: Focus on plan quality rather than rushing to code.

### 6. Turn Inner-Loop Prompts into Slash Commands

Convert repetitive prompts into reusable slash commands with inline bash for context.

**Example**:
```yaml
---
description: Prep a clean commit and push a PR
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git commit:*), Bash(git push:*)
---

# Context
- Status: !`git status -sb`
- Diff: !`git diff --stat`

# Task
Draft a commit message, commit, and push the current branch.
```

### 7. Promote Recurring Roles into Subagents

Create specialized subagents for repeatable tasks like code simplification or end-to-end verification.

**Template**:
```yaml
---
name: verify-app
description: Runs the app, checks key flows, reports issues.
tools: Bash, Read
model: inherit
---

Verify the app changes using the project's standard commands.
Report failures with exact error output and reproduction steps.
```

### 8. Use Hooks to Make the Last 10% Deterministic

Automate formatting and other consistent post-edit tasks via hooks.

**Example hook config**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "npm run format" }
        ]
      }
    ]
  }
}
```

### 9. Pre-Allow Safe Tools, Don't Default to YOLO

Create allowlists of trusted tools via `/permissions` and `.claude/settings.json` rather than blanket permission skipping.

**Implementation**: Review and update safe allowlist monthly, keep risky operations prompted.

### 10. Plug Claude into Real Systems via MCP

Connect Claude to external tools (Slack, BigQuery, Sentry) using MCP servers, sharing config in `.mcp.json`.

**Implementation**: Start with one system that eliminates a daily pain point, expand gradually.

### 11. For Long-Running Work, Add Background Verification

Set up automated verification for lengthy tasks using background agents, Stop hooks, or plugins like ralph-wiggum.

**Implementation**: Add Stop hook that runs smoke tests and posts summary to transcript.

### 12. Give Claude a Verification Loop (The Multiplier)

Build systems for Claude to validate its own outputs through:
- Single commands (e.g., `pnpm test --filter ...`)
- Test suites
- Browser UI checks
- Review passes by subagents

**Why it works**: Self-verification dramatically improves quality.

### 13. Share Team Skills and Conventions Intentionally

Use shared skills/settings for team-critical elements while allowing personal preferences. Leverage multiple skills directories for separation.

**Implementation**: Keep project skills in git, personal skills in home directory with clear naming.

## Starter Kit

Four artifacts providing 80% of the value:

1. **Minimal CLAUDE.md** with 2-3 "do/don't" rules
2. **One slash command** for your most common workflow loop
3. **One subagent** for verification or review
4. **One formatting hook** to eliminate CI noise

## One-Week Adoption Plan

- **Day 1**: Create minimal CLAUDE.md with core rules
- **Day 2**: Build one slash command for repetitive tasks
- **Day 3**: Add verification subagent for post-change checks
- **Day 4**: Implement formatting hook
- **Day 5**: Audit and tighten tool permissions
- **Day 6**: Connect first MCP tool
- **Day 7**: Review and refine based on time savings

## Common Pitfalls to Avoid

- **Over-automation**: Start with one command/hook, not ten
- **Skipping verification**: Without validation, you're gambling
- **Messy parallelism**: Label sessions, keep tasks independent
- **Bloat**: Keep CLAUDE.md concise, review regularly

## Conclusion

These practices transform Claude Code from a code editor into a workflow hub. The key is starting small, focusing on verification, and building habits that compound over time. Consistency and systematic automation deliver more reliable results than chasing the fastest individual response.
