#!/usr/bin/env bash
set -ex

# --- Configuration ---
REPO_ROOT=$(pwd)
SKILLS_DIR="core/ai/skills/skills"
INFRA_DIR="infrastructure"

echo "🚀 Deploying GitOps Control Plane architecture to: $REPO_ROOT"

# 1. Directory Structure
mkdir -p "$SKILLS_DIR/security-audit/cmd" "$SKILLS_DIR/security-audit/internal"
mkdir -p "ai-core/ai/runtime/cmd/worker" "ai-core/ai/runtime/internal/workflow" "ai-core/ai/runtime/internal/activity" "ai-core/ai/runtime/internal/notifier"
mkdir -p "$INFRA_DIR"/{temporal,crossplane,flux}

# 2. Recursive Makefile
cat <<EOF > Makefile
SKILLS := \$(wildcard core/ai/skills/skills/*)

.PHONY: all build test \$(SKILLS)

all: build

build: \$(SKILLS)
	@go build -o bin/cloud-ai-worker ./ai-core/ai/runtime/cmd/worker/main.go
	@for dir in \$(SKILLS); do \$(MAKE) -C \$\$dir build; done

test: \$(SKILLS)
	@go test -v ./ai-core/ai/runtime/...
	@for dir in \$(SKILLS); do \$(MAKE) -C \$\$dir test; done

\$(SKILLS):
	@\$(MAKE) -C \$@ \$(MAKECMDGOALS)
EOF

# 3. Main AI Worker
cat <<EOF > ai-core/ai/runtime/cmd/worker/main.go
package main
import (
	"log"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
	"github.com/lloydchang/gitops-infra-core/operators/ai-core/ai/runtime/internal/workflow"
)
func main() {
	c, _ := client.Dial(client.Options{})
	defer c.Close()
	w := worker.New(c, "cloud-ai-task-queue", worker.Options{})
	w.RegisterWorkflow(workflow.SecurityDriftWorkflow)
	err := w.Run(worker.InterruptCh())
	if err != nil { log.Fatalln("Unable to start worker", err) }
}
EOF

# 4. Security Workflow
cat <<EOF > ai-core/ai/runtime/internal/workflow/security_drift.go
package workflow
import "go.temporal.io/sdk/workflow"
func SecurityDriftWorkflow(ctx workflow.Context, resourceID string) error {
	return nil
}
EOF

# 5. Teams Notifier with Adaptive Card Template
cat <<EOF > ai-core/ai/runtime/internal/notifier/teams_template.go
package notifier
import ("encoding/json"; "fmt")

func GenerateTeamsApprovalCard(workflowID string, resourceID string) string {
	card := map[string]interface{}{
		"type": "AdaptiveCard",
		"version": "1.4",
		"body": []map[string]interface{}{
			{"type": "TextBlock", "text": "⚠️ Security Drift Detected", "weight": "bolder"},
			{"type": "TextBlock", "text": fmt.Sprintf("Resource: %s", resourceID)},
		},
		"actions": []map[string]interface{}{
			{"type": "Action.Submit", "title": "Approve", "data": map[string]interface{}{"action": "approve"}},
		},
	}
	payload, _ := json.Marshal(card)
	return string(payload)
}
EOF

# 6. Dockerfile
cat <<EOF > Dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /cloud-ai-worker ./ai-core/ai/runtime/cmd/worker/main.go
FROM gcr.io/distroless/static-debian12:latest
COPY --from=builder /cloud-ai-worker .
ENTRYPOINT ["./cloud-ai-worker"]
EOF

# 7. Initialize Git & First Commit
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "chore: full deployment of autonomous gitops control plane"
fi

echo "✅ Deployment complete. Repository is staged and ready to push."
