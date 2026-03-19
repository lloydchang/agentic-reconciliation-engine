#!/bin/bash

# set_topdir.sh
# Set TOPDIR to the project root of agentic-reconciliation-engine repository
# relative to $(dirname $0)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Set TOPDIR to the project root (assuming this script is in the root)
TOPDIR="$SCRIPT_DIR"

# Export the variable so it can be used by other scripts
export TOPDIR

echo "TOPDIR set to: $TOPDIR"
