#!/usr/bin/env bash

set -xe

# The specific module we want to eradicate
TARGET="github.com/lloydchang/ai-agents-sandbox"

echo "☢️ Purging legacy imports from $TARGET..."

# 1. Find all files containing the target string
FILES=$(grep -rl "$TARGET" .)

# 2. For each file, remove lines containing the target string
for FILE in $FILES; do
    echo "Cleaning $FILE"
    # This deletes the entire line if it contains the target
    sed -i '' "/$TARGET/d" "$FILE"
done

echo "✅ Purge complete. Running final tidy..."
go mod tidy
