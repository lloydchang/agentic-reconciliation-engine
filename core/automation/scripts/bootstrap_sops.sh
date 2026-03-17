#!/usr/bin/env bash

# bootstrap_sops.sh
# Minimal SOPS bootstrap for a fresh clone

set -euo pipefail
set -x   # optional, only if you want debug output

SOPS_KEY_DIR=".sops-keys"
AGE_KEY_FILE="$SOPS_KEY_DIR/age.agekey"
SCRIPT_NAME="remove_age_key_and_reencrypt.sh"
SCRIPT_DEST_DIR="scripts"

# Ensure directories exist
mkdir -p "$SOPS_KEY_DIR"
mkdir -p "$SCRIPT_DEST_DIR"

# Generate Age key if missing
if [ ! -f "$AGE_KEY_FILE" ]; then
    echo "Generating new Age key..."
    age-keygen -o "$AGE_KEY_FILE"
    AGE_PUBLIC_KEY=$(age-keygen -y "$AGE_KEY_FILE")
    echo "Public key: $AGE_PUBLIC_KEY"
else
    echo "Age key already exists at $AGE_KEY_FILE"
fi

# Ensure remove_age_key_and_reencrypt.sh exists in core/automation/scripts/
if [ ! -f "$SCRIPT_DEST_DIR/$SCRIPT_NAME" ]; then
    echo "$SCRIPT_NAME not found in $SCRIPT_DEST_DIR, downloading from GitHub..."
    curl -sL "https://raw.githubusercontent.com/lloydchang/gitops-infra-core/operators/main/core/automation/scripts/$SCRIPT_NAME" -o "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
    chmod +x "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
else
    echo "$SCRIPT_NAME already present in $SCRIPT_DEST_DIR, updating..."
    curl -sL "https://raw.githubusercontent.com/lloydchang/gitops-infra-core/operators/main/core/automation/scripts/$SCRIPT_NAME" -o "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
    chmod +x "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
fi

echo "Bootstrap complete. Age key in $AGE_KEY_FILE, cleanup script in $SCRIPT_DEST_DIR/$SCRIPT_NAME"
