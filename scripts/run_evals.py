#!/usr/bin/env python3
"""
Cloud AI Agent — Skill Eval Harness
=====================================================
Tests that each skill:
  1. Has a valid SKILL.md with correct frontmatter
  2. Triggers on the right input phrases
  3. Produces correctly structured output schemas
  4. Has required sections (examples, output format, commands)

Usage:
  python3 eval/run_evals.py                    # Run all evals
  python3 eval/run_evals.py --skill gitops     # Run one skill
  python3 eval/run_evals.py --verbose          # Show details
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── ANSI colours ─────────────────────────────────────────────────────────────
GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"
CYAN = "\033[96m"; BOLD = "\033[1m"; RESET = "\033[0m"

# ── Test case schema ──────────────────────────────────────────────────────────
@dataclass
class EvalCase:
    """One test case for one skill."""
    skill: str
    input_phrase: str
    expected_trigger: bool        # Should this skill activate?
    required_output_keys: list[str] = field(default_factory=list)
    description: str = ""

@dataclass
class EvalResult:
    skill: str
    case: EvalCase
    passed: bool
    checks: list[tuple[str, bool, str]] = field(default_factory=list)
    duration_ms: float = 0.0

# ── Skill structure validator ─────────────────────────────────────────────────
REQUIRED_SECTIONS = [
    "## Examples",
    "## Output Format",
]
REQUIRED_FRONTMATTER_KEYS = ["name", "description", "tools"]

def validate_skill_structure(skill_path: Path) -> tuple[bool, list[str]]:
    """Validate a SKILL.md has the required sections and frontmatter."""
    issues = []
    content = skill_path.read_text()

    # Check frontmatter
    if not content.startswith("---"):
        issues.append("Missing YAML frontmatter (must start with ---)")
        return False, issues

    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        issues.append("Malformed YAML frontmatter (no closing ---)")
        return False, issues

    fm = fm_match.group(1)
    for key in REQUIRED_FRONTMATTER_KEYS:
        if f"{key}:" not in fm:
            issues.append(f"Missing frontmatter key: {key}")

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            issues.append(f"Missing section: {section}")

    # Check for at least one code block
    if "```" not in content:
        issues.append("No code blocks found — skill must include commands")

    # Check output format is JSON
    output_idx = content.find("## Output Format")
    if output_idx > 0:
        output_section = content[output_idx:output_idx + 400]
        if "```json" not in output_section:
            issues.append("Output Format section must include a ```json block")

    # Check skill name in frontmatter matches directory name
    dir_name = skill_path.parent.name
    name_match = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
    if name_match:
        declared_name = name_match.group(1).strip()
        if declared_name != dir_name:
            issues.append(
                f"Skill name mismatch: frontmatter declares '{declared_name}' "
                f"but directory is '{dir_name}'"
            )

    return len(issues) == 0, issues


def extract_trigger_keywords(skill_path: Path) -> list[str]:
    """Extract trigger keywords from the skill's description field."""
    content = skill_path.read_text()
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return []
    fm = fm_match.group(1)
    desc_match = re.search(r'description:\s*>\n(.*?)(?=\n\w|\ntools:)', fm, re.DOTALL)
    if not desc_match:
        return []
    desc = desc_match.group(1).strip()
    # Extract words after "Triggers:" in description
    triggers_match = re.search(r'Triggers?:(.*)', desc, re.DOTALL | re.IGNORECASE)
    if triggers_match:
        return [w.lower() for w in re.findall(r'\b\w{4,}\b', triggers_match.group(1))]
    return [w.lower() for w in re.findall(r'\b\w{4,}\b', desc)]


def phrase_matches_skill(phrase: str, skill_keywords: list[str]) -> bool:
    """Check whether an input phrase would trigger a skill."""
    phrase_words = set(phrase.lower().split())
    return bool(phrase_words.intersection(set(skill_keywords)))


def extract_output_keys(skill_path: Path) -> list[str]:
    """Extract expected JSON keys from the Output Format section.

    Handles nested objects by finding the outermost ``{...}`` block inside
    the ```json fence, then extracting top-level keys only.
    """
    content = skill_path.read_text()
    output_idx = content.find("## Output Format")
    if output_idx < 0:
        return []
    output_section = content[output_idx:output_idx + 1200]

    # Find the start of the JSON block
    fence_match = re.search(r'```json\n', output_section)
    if not fence_match:
        return []

    block_start = fence_match.end()
    # Walk forward tracking brace depth to find the outermost closing brace
    depth = 0
    block_end = block_start
    for i, ch in enumerate(output_section[block_start:], start=block_start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                block_end = i + 1
                break

    json_str = output_section[block_start:block_end]
    if not json_str.strip():
        return []

    # Try full JSON parse first (strip JS comments)
    try:
        clean = re.sub(r'//[^\n]*', '', json_str)
        obj = json.loads(clean)
        return list(obj.keys())
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract top-level keys using indentation heuristic
    # Top-level keys are at the root object level (indented by 2 spaces, not 4+)
    top_keys = re.findall(r'^\s{2}"(\w+)":', json_str, re.MULTILINE)
    if top_keys:
        return top_keys

    # Last resort: all quoted keys
    return re.findall(r'"(\w+)":', json_str)


# ── Eval cases ────────────────────────────────────────────────────────────────
EVAL_CASES: list[EvalCase] = [
    # Terraform provisioning
    EvalCase("terraform-provisioning",
             "run terraform plan on the staging environment",
             True, ["operation", "environment", "status"],
             "Standard terraform trigger"),
    EvalCase("terraform-provisioning",
             "check for infrastructure drift in prod",
             True, ["operation", "status"],
             "Drift detection trigger"),

    # CI/CD
    EvalCase("cicd-pipeline-monitor",
             "why did the payments-api build fail in GitHub Actions?",
             True, ["pipeline_tool", "status", "failure_reason"],
             "Pipeline failure investigation"),
    EvalCase("cicd-pipeline-monitor",
             "show DORA metrics for last month",
             True, ["dora"],
             "DORA metrics trigger"),

    # Incident
    EvalCase("incident-triage-runbook",
             "we have a P1 — the AKS cluster is returning 503s",
             True, ["severity", "runbook_applied", "status"],
             "P1 incident trigger"),
    EvalCase("incident-triage-runbook",
             "PagerDuty alert: high error rate on payments namespace",
             True, ["severity"],
             "Alert-based incident trigger"),

    # Tenant lifecycle
    EvalCase("tenant-lifecycle-manager",
             "onboard new enterprise tenant Acme Corp in East US",
             True, ["tenant_id", "tier", "status"],
             "New tenant onboarding"),
    EvalCase("tenant-lifecycle-manager",
             "offboard tenant-42 — they've churned",
             True, ["tenant_id", "status"],
             "Tenant offboard"),

    # Compliance
    EvalCase("compliance-security-scanner",
             "run a CVE scan on all images in prod",
             True, ["critical_findings", "status"],
             "Vulnerability scan"),
    EvalCase("compliance-security-scanner",
             "generate a SOC2 compliance report",
             True, ["status"],
             "Compliance report trigger"),

    # SLA
    EvalCase("sla-monitoring-alerting",
             "what is our current error budget for the enterprise tier?",
             True, ["tier", "budget_remaining_pct", "status"],
             "Error budget query"),

    # Deployment
    EvalCase("deployment-validation",
             "validate the payments-api v2.3.1 deploy before it goes to prod",
             True, ["service", "gate_results", "go_nogo"],
             "Pre-deployment validation"),

    # KPI
    EvalCase("kpi-report-generator",
             "prepare the monthly exec report for leadership",
             True, ["report_type", "status"],
             "Monthly report trigger"),

    # Networking
    EvalCase("multi-cloud-networking",
             "provision a spoke VNet for tenant-53 and peer it to the hub",
             True, ["operation", "resource", "status"],
             "VNet provisioning"),
    EvalCase("multi-cloud-networking",
             "why can't the payments-api pod reach the database?",
             True, ["connectivity", "status"],
             "Connectivity diagnosis"),

    # Database
    EvalCase("database-operations",
             "restore tenant-42 database to 3 hours ago",
             True, ["operation", "tenant_id", "status"],
             "PITR restore"),
    EvalCase("database-operations",
             "scale up the enterprise database for tenant-91",
             True, ["operation", "tenant_id", "status"],
             "DB scaling"),

    # DR
    EvalCase("disaster-recovery",
             "execute region failover for tenant-42 — East US is down",
             True, ["operation", "rto_achieved_minutes", "status"],
             "Failover execution"),
    EvalCase("disaster-recovery",
             "run a DR drill for all enterprise tenants",
             True, ["drill_result", "status"],
             "DR drill"),

    # GitOps
    EvalCase("gitops-workflow",
             "why is the payments-api out of sync in ArgoCD?",
             True, ["sync_status", "status"],
             "Sync investigation"),
    EvalCase("gitops-workflow",
             "promote tenant-app v2.3.1 from staging to prod",
             True, ["operation", "target_revision", "status"],
             "Image promotion"),

    # Service mesh
    EvalCase("service-mesh",
             "enable strict mTLS for the tenant-42 namespace",
             True, ["mtls_mode", "status"],
             "mTLS enforcement"),
    EvalCase("service-mesh",
             "set up a 10% canary split for payments-api v2",
             True, ["canary_weight", "status"],
             "Canary configuration"),

    # Container registry
    EvalCase("container-registry",
             "scan the payments-api:v2.3.1 image for critical CVEs",
             True, ["scan_result", "status"],
             "Image CVE scan"),
    EvalCase("container-registry",
             "promote tenant-app:v1.5.0 from staging to prod registry",
             True, ["promotion_status", "status"],
             "Image promotion"),

    # Developer self-service
    EvalCase("developer-self-service",
             "onboard the checkout engineering team to the platform",
             True, ["team", "status"],
             "Team onboarding"),
    EvalCase("developer-self-service",
             "create a Backstage template for a new Python microservice",
             True, ["template", "status"],
             "Template creation"),

    # Audit SIEM
    EvalCase("audit-siem",
             "who accessed the payments-api secrets in Key Vault this week?",
             True, ["results_count", "status"],
             "Audit query"),
    EvalCase("audit-siem",
             "generate a SOC2 evidence package for the Q2 audit",
             True, ["evidence_files", "status"],
             "Evidence package"),

    # Change management
    EvalCase("change-management",
             "score the risk of deploying a new database schema to 45 tenants",
             True, ["risk_score", "change_type", "approval_status"],
             "Risk scoring"),
    EvalCase("change-management",
             "is there a change freeze next week?",
             True, ["frozen"],
             "Change freeze check"),

    # Chaos/load testing
    EvalCase("chaos-load-testing",
             "run the pod-kill experiment on payments-api in staging",
             True, ["type", "status", "slo_breached"],
             "Chaos experiment"),
    EvalCase("chaos-load-testing",
             "load test tenant-42 environment to find the breaking point",
             True, ["type", "metrics", "status"],
             "Load test"),

    # Negative cases — should NOT trigger wrong skills
    EvalCase("terraform-provisioning",
             "show me slow queries on the database",
             False, [],
             "Should NOT trigger terraform for DB query"),
    EvalCase("incident-triage-runbook",
             "what is our monthly cloud spend?",
             False, [],
             "Should NOT trigger incident skill for cost query"),
]
def run_evals(
    skills_dir: Path,
    filter_skill: Optional[str] = None,
    verbose: bool = False,
) -> list[EvalResult]:
    results = []
    cases = [c for c in EVAL_CASES if not filter_skill or filter_skill in c.skill]

    print(f"\n{BOLD}Running {len(cases)} eval cases across "
          f"{len(set(c.skill for c in cases))} skills{RESET}\n")

    for case in cases:
        start = time.perf_counter()
        skill_path = skills_dir / case.skill / "SKILL.md"
        checks: list[tuple[str, bool, str]] = []

        # Check 1: skill file exists
        exists = skill_path.exists()
        checks.append(("SKILL.md exists", exists,
                        str(skill_path) if not exists else ""))

        if exists:
            # Check 2: structure valid
            struct_ok, struct_issues = validate_skill_structure(skill_path)
            checks.append((
                "Structure valid",
                struct_ok,
                "; ".join(struct_issues) if not struct_ok else "",
            ))

            # Check 3: trigger matching
            keywords = extract_trigger_keywords(skill_path)
            triggered = phrase_matches_skill(case.input_phrase, keywords)
            trigger_ok = triggered == case.expected_trigger
            checks.append((
                f"Trigger {'fires' if case.expected_trigger else 'silent'} on phrase",
                trigger_ok,
                f"Got trigger={triggered}, expected={case.expected_trigger}. "
                f"Keywords: {', '.join(keywords[:10])}" if not trigger_ok else "",
            ))

            # Check 4: output keys present
            if case.required_output_keys:
                actual_keys = extract_output_keys(skill_path)
                missing_keys = [k for k in case.required_output_keys
                                if k not in actual_keys]
                keys_ok = len(missing_keys) == 0
                checks.append((
                    f"Output schema has required keys",
                    keys_ok,
                    f"Missing: {missing_keys}" if not keys_ok else "",
                ))

        passed = all(ok for _, ok, _ in checks)
        duration_ms = (time.perf_counter() - start) * 1000
        result = EvalResult(case.skill, case, passed, checks, duration_ms)
        results.append(result)

        # Print inline result
        icon = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"  {icon} [{status}] {case.skill:<35} {case.description}")

        if verbose or not passed:
            for check_name, ok, detail in checks:
                sub_icon = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
                line = f"         {sub_icon} {check_name}"
                if detail:
                    line += f"\n           {YELLOW}→ {detail}{RESET}"
                print(line)

    return results


def print_summary(results: list[EvalResult]) -> int:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    skills_tested = sorted(set(r.skill for r in results))
    skill_pass = {s: all(r.passed for r in results if r.skill == s)
                  for s in skills_tested}

    print(f"\n{BOLD}{'═' * 58}{RESET}")
    print(f"{BOLD}  Eval Summary{RESET}")
    print(f"{'═' * 58}")
    print(f"  Total cases:   {total}")
    print(f"  {GREEN}Passed:{RESET}        {passed}")
    if failed:
        print(f"  {RED}Failed:{RESET}        {failed}")
    print(f"  Pass rate:     {100 * passed / total:.1f}%")
    print()

    print(f"  {BOLD}Per-skill results:{RESET}")
    for skill in skills_tested:
        icon = f"{GREEN}✓{RESET}" if skill_pass[skill] else f"{RED}✗{RESET}"
        print(f"    {icon} {skill}")

    if failed == 0:
        print(f"\n  {GREEN}{BOLD}All evals passed ✓{RESET}")
    else:
        print(f"\n  {RED}{BOLD}{failed} eval(s) failed ✗{RESET}")

    print(f"{'═' * 58}\n")
    return failed


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cloud AI Agent — Skill Eval Runner"
    )
    parser.add_argument(
        "--skills-dir",
        default=str(Path(__file__).parent / "../.agents/skills"),
        help="Path to the skills directory",
    )
    parser.add_argument("--skill", help="Run evals for a single skill only")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show all check details")
    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.exists():
        print(f"{RED}Skills directory not found: {skills_dir}{RESET}")
        sys.exit(1)

    results = run_evals(skills_dir, filter_skill=args.skill, verbose=args.verbose)
    failures = print_summary(results)
    sys.exit(failures > 0)
