#!/usr/bin/env bash

# Set TOPDIR to the project root of the agentic-reconciliation-engine repository

# This script finds the project root by looking for go.mod, starting from the script's directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TOPDIR="$SCRIPT_DIR"

while [ ! -f "$TOPDIR/go.mod" ] && [ "$TOPDIR" != "/" ]; do

  TOPDIR="$(dirname "$TOPDIR")"

done

if [ ! -f "$TOPDIR/go.mod" ]; then

  echo "Could not find project root with go.mod" >&2

  exit 1

fi

export TOPDIR
