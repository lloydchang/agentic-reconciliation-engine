#!/bin/bash

# TOPDIR Validation Script
# Prevents creation of files in TOPDIR that should be in subdirectories

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get TOPDIR
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPDIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Patterns that should not be in TOPDIR
FORBIDDEN_PATTERNS=(
    "*.py$"
    "*.js$"
    "*.go$"
    "*.yaml$"
    "*.yml$"
    "*.json$"
    "*.sh$"
    "*service*"
    "*dashboard*"
    "*api*"
    "*backend*"
    "*frontend*"
    "*comprehensive*"
    "*real-*"
    "*simple-*"
    "*memory-*"
    "*portal*"
)

# Allowed files in TOPDIR
ALLOWED_FILES=(
    "README.md"
    "LICENSE"
    "CONTRIBUTING.md"
    "AGENTS.md"
    "CLAUDE.md"
    "GEMINI.md"
    ".gitignore"
    ".env.template"
    "go.mod"
    "go.sum"
    ".env"
)

# Allowed directories in TOPDIR
ALLOWED_DIRS=(
    "core"
    "dashboard"
    "docs"
    "helm"
    "hooks"
    "overlay"
    "portal"
    "scripts"
    "test"
    ".git"
    ".github"
    ".agents"
    ".claude"
    ".codex"
    ".cursor"
    ".windsurf"
)

echo -e "${BLUE}🔍 TOPDIR Validation Check${NC}"
echo -e "${BLUE}=============================${NC}"
echo

# Check for forbidden files
echo -e "${YELLOW}Checking for misplaced files in TOPDIR...${NC}"
found_issues=false

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    # Find files matching the pattern
    while IFS= read -r -d '' file; do
        filename=$(basename "$file")
        
        # Skip if file is allowed
        if [[ " ${ALLOWED_FILES[*]} " =~ " ${filename} " ]]; then
            continue
        fi
        
        # Skip if file is in a subdirectory
        if [[ "$file" == */* ]]; then
            continue
        fi
        
        echo -e "${RED}❌ Misplaced file: $file${NC}"
        echo -e "${RED}   This file should be moved to an appropriate subdirectory${NC}"
        found_issues=true
    done < <(find "$TOPDIR" -maxdepth 1 -type f -name "$pattern" -print0 2>/dev/null || true)
done

# Check for unexpected directories
echo
echo -e "${YELLOW}Checking for unexpected directories in TOPDIR...${NC}"

for dir in "$TOPDIR"/*; do
    if [ -d "$dir" ]; then
        dirname=$(basename "$dir")
        
        # Skip if directory is allowed
        if [[ " ${ALLOWED_DIRS[*]} " =~ " ${dirname} " ]]; then
            continue
        fi
        
        echo -e "${RED}❌ Unexpected directory: $dirname${NC}"
        echo -e "${RED}   This directory should be documented or moved${NC}"
        found_issues=true
    fi
done

# Check for temporary files that should be gitignored
echo
echo -e "${YELLOW}Checking for temporary files that should be .gitignored...${NC}"

temp_patterns=(
    "*.pid"
    "*.log"
    "*.tmp"
    "*.bak"
    "*.swp"
    "*.swo"
    ".DS_Store"
    "memory.db"
    "*.cache"
)

for pattern in "${temp_patterns[@]}"; do
    for file in "$TOPDIR"/$pattern; do
        if [ -f "$file" ]; then
            echo -e "${RED}❌ Temporary file not ignored: $(basename "$file")${NC}"
            echo -e "${RED}   This should be covered by .gitignore${NC}"
            found_issues=true
        fi
    done
done

# Summary
echo
if [ "$found_issues" = true ]; then
    echo -e "${RED}❌ TOPDIR validation FAILED!${NC}"
    echo
    echo -e "${YELLOW}Recommended actions:${NC}"
    echo -e "1. Move misplaced files to appropriate subdirectories:"
    echo -e "   - Dashboard/Backend files → dashboard/"
    echo -e "   - Portal files → portal/"
    echo -e "   - Scripts → scripts/"
    echo -e "   - Infrastructure manifests → overlay/"
    echo -e "   - Documentation → docs/"
    echo -e "2. Add temporary files to .gitignore if needed"
    echo -e "3. Update scripts to use correct working directories"
    exit 1
else
    echo -e "${GREEN}✅ TOPDIR validation PASSED!${NC}"
    echo -e "${GREEN}   TOPDIR is clean and properly organized${NC}"
    exit 0
fi
