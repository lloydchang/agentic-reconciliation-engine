#!/bin/bash

# Set TOPDIR to the project root relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TOPDIR="$SCRIPT_DIR"

echo "TOPDIR set to: $TOPDIR"
