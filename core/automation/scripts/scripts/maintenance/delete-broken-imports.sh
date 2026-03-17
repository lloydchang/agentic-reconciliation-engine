#!/usr/bin/env bash
# Remove the non-existent service and mcp imports
find . -name "*.go" -exec sed -i '' '/internal\/service/d' {} +
find . -name "*.go" -exec sed -i '' '/internal\/mcp/d' {} +

# Clean up now that the bad imports are gone
go mod tidy
