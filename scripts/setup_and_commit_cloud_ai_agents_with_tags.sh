#!/bin/bash
# File: setup_and_commit_cloud_ai_agents_with_tags.sh
# macOS-compatible script to create .agents Cloud AI skills, git commit, and tag each skill

set -e

# Root directory of your local repo
REPO_DIR="$(dirname $0)/.."  # <-- update this path
AGENTS_DIR="$REPO_DIR/.agents"

mkdir -p "$AGENTS_DIR"

# Ensure repo is git initialized
cd "$REPO_DIR"
if [ ! -d ".git" ]; then
    git init
fi

# List of 40 Cloud AI skills
SKILLS=(
incident-summary
k8s-troubleshoot
runbook-planner
manifest-generator
gitops-pr
log-classifier
doc-generator
kubectl-assistant
policy-explainer
platform-chat
autoscaler-advisor
cost-optimizer
deployment-strategy
security-audit
backup-validator
compliance-reporter
dependency-checker
incident-predictor
alert-router
remediation-bot
observability-aggregator
onboarding-assistant
config-validator
incident-history
resource-balancer
troubleshooting-playbook
cluster-health-check
node-maintenance
service-mesh-manager
ci-cd-integrator
feature-flag-manager
secret-rotation
load-balancer-tuner
network-diagnostics
database-maintenance
alert-prioritizer
release-manager
rollback-assistant
capacity-planner
slo-monitor
runbook-suggester
)

# Templates
GO_TEMPLATE='package main

import (
    "fmt"
    "os"
)

func main() {
    if len(os.Args) < 2 {
        fmt.Println("Usage: <skill> <input>")
        os.Exit(1)
    }
    input := os.Args[1]
    fmt.Println("__SKILL__ Go Skill Output for input:", input)
}
'

RUST_TEMPLATE='fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: <skill> <input>");
        std::process::exit(1);
    }
    let input = &args[1];
    println!("__SKILL__ Rust Skill Output for input: {}", input);
}
'

SKILL_MD_TEMPLATE='Name: __SKILL__
Purpose: Placeholder for __SKILL__ skill in Cloud AI
Inputs: Input payload or event
Process: Analyze input and perform placeholder logic
Outputs: Example output or action
Optional scripts: scripts/run.sh
Optional manifests: manifests/example.yaml
'

SHELL_SCRIPT_TEMPLATE='#!/bin/bash
echo "Running __SKILL__ skill script with argument: $1"
'

YAML_TEMPLATE='apiVersion: v1
kind: ConfigMap
metadata:
  name: __SKILL__-config
data:
  example: "placeholder for __SKILL__"
'

echo "Creating Cloud AI .agents workspace inside $AGENTS_DIR..."

SKILL_INDEX=1

for skill in "${SKILLS[@]}"; do
    SKILL_DIR="$AGENTS_DIR/$skill"
    mkdir -p "$SKILL_DIR/cmd/go/$skill"
    mkdir -p "$SKILL_DIR/cmd/rust/$skill/src"
    mkdir -p "$SKILL_DIR/scripts"
    mkdir -p "$SKILL_DIR/manifests"

    # Initialize Go module
    (cd "$SKILL_DIR/cmd/go/$skill" && go mod init "cloudai/$skill")

    # Create Go main.go
    echo "${GO_TEMPLATE//__SKILL__/$skill}" > "$SKILL_DIR/cmd/go/$skill/main.go"

    # Initialize Rust project
    (cd "$SKILL_DIR/cmd/rust/$skill" && cargo init --bin --quiet)

    # Replace Rust main.rs with template
    echo "${RUST_TEMPLATE//__SKILL__/$skill}" > "$SKILL_DIR/cmd/rust/$skill/src/main.rs"

    # Create SKILL.md
    echo "${SKILL_MD_TEMPLATE//__SKILL__/$skill}" > "$SKILL_DIR/SKILL.md"

    # Create shell script
    echo "${SHELL_SCRIPT_TEMPLATE//__SKILL__/$skill}" > "$SKILL_DIR/scripts/run.sh"
    chmod +x "$SKILL_DIR/scripts/run.sh"

    # Create YAML manifest
    echo "${YAML_TEMPLATE//__SKILL__/$skill}" > "$SKILL_DIR/manifests/example.yaml"

    # Git add & commit
    git add "$SKILL_DIR"
    git commit -m "Add Cloud AI skill #$SKILL_INDEX: $skill"

    # Tag the commit
    git tag -a "skill-$SKILL_INDEX" -m "Skill #$SKILL_INDEX: $skill"

    echo "Created, committed, and tagged skill #$SKILL_INDEX: '$skill'"

    SKILL_INDEX=$((SKILL_INDEX+1))
done

echo "All 40 Cloud AI skills created, committed, and tagged in $AGENTS_DIR"
echo "Go skills ready for Temporal, Rust skills ready for high-performance Kubernetes execution."
