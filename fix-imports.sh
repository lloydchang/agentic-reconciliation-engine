#!/usr/bin/env bash
MOD="github.com/lloydchang/gitops-infra-control-plane"

echo "🔧 Normalizing import paths for internal packages..."

# List of internal packages you want to use
PACKAGES=("service" "activity" "notifier" "workflow")

for PKG in "${PACKAGES[@]}"; do
    # Find all .go files that use the package name
    # We replace any incorrect/dangling imports with the full correct path
    find ./ai-agents/cmd -name "*.go" -exec sed -i '' "s|import (.*\"$PKG\"|import (\"$MOD/ai-agents/internal/$PKG\"|g" {} +
done

echo "✅ Imports normalized. Running go mod tidy..."
go mod tidy

