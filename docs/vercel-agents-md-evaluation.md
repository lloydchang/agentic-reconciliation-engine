# AGENTS.md vs Skills: Vercel Agent Evaluation Results

## Summary

Vercel's recent evaluation comparing AGENTS.md and skills-based approaches for teaching AI coding agents framework knowledge revealed that passive context (AGENTS.md) significantly outperforms on-demand retrieval (skills).

## Key Findings

### Performance Results
- **AGENTS.md docs index**: 100% pass rate
- **Skills with explicit instructions**: 79% pass rate  
- **Skills (default behavior)**: 53% pass rate (no improvement over baseline)
- **Baseline (no docs)**: 53% pass rate

### Core Issues with Skills
- **Reliability**: Skills were not triggered in 56% of eval cases
- **Fragility**: Small changes in instruction wording produced dramatically different results
- **Decision Overhead**: Agents must decide when to invoke skills, introducing failure points

### AGENTS.md Advantages
- **No Decision Point**: Information is always present in context
- **Consistent Availability**: Available on every turn without async loading
- **No Ordering Issues**: Avoids sequencing decisions that can cause failures

## Implementation Details

### Compression Strategy
- Initial docs injection: ~40KB
- Compressed format: 8KB (80% reduction)
- Pipe-delimited structure for minimal space usage

### Content Structure
```
[Next.js Docs Index]|root: ./.next-docs
|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning
|01-app/01-getting-started:{01-installation.mdx,02-project-structure.mdx,...}
```

### Retrieval Pattern
- Docs index provides file paths and locations
- Agent reads specific files as needed rather than loading everything upfront
- Enables version-matched documentation access

## Implications for Agent Architecture

### Framework Authors
- **Passive Context**: Most reliable for general framework knowledge
- **Skills**: Better suited for vertical, action-specific workflows (upgrades, migrations)
- **Compression**: Aggressive compression maintains effectiveness while preserving context window

### Agent Design
- **Retrieval-Led Reasoning**: Shift from pre-training to retrieval-based approaches
- **Context Management**: Design docs for efficient retrieval rather than upfront loading
- **Evaluation Focus**: Test against APIs not in training data to measure true doc access effectiveness

## Setup for Next.js Projects

Vercel provides an automated setup:

```bash
npx @next/codemod@canary agents-md
```

This command:
1. Detects Next.js version
2. Downloads matching documentation to `.next-docs/`
3. Injects compressed index into `AGENTS.md`

## Source
- Blog Post: https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals
- Date: January 27, 2026
- Author: Jude Gao (Software Engineer, Next.js)

## Related Research
This finding supports the agent architecture design decisions in this repository, particularly the use of persistent context files (AGENTS.md, CLAUDE.md) over on-demand skill invocation for core framework knowledge.
