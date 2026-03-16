#!/bin/bash
set -euo pipefail

STATEFUL_KINDS="Database|XDatabase|Volume|XVolume|Queue|XQueue|XCluster"

DELETED_FILES=$(git diff --name-only --diff-filter=D origin/main...HEAD -- 'infrastructure/tenants/**/*.yaml')

for file in $DELETED_FILES; do
  KIND=$(git show origin/main:$file | grep '^kind:' | awk '{print $2}')
  if echo "$KIND" | grep -qE "^($STATEFUL_KINDS)$"; then
    echo "ERROR: $file contains stateful kind=$KIND deleted without approval"
    echo "  Add: platform.example.com/allow-deletion: 'true'"
    exit 1
  fi
done

CHANGED_FILES=$(git diff --name-only --diff-filter=M origin/main...HEAD -- 'infrastructure/tenants/**/*.yaml')

for file in $CHANGED_FILES; do
  if git diff origin/main...HEAD -- $file | grep -q '+  deletionPolicy: Delete'; then
    conftest test $file --policy control-plane/ci/policies/deletion-guard.rego
  fi
done

echo "Deletion guard passed"
