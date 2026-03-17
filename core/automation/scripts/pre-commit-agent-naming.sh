#!/bin/bash

# Pre-commit hook for agent naming validation
# This hook prevents commits that violate agent naming conventions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local status="$1"
    local message="$2"
    case $status in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        *) echo -e "[INFO] $message" ;;
    esac
}

# Function to check if a name follows verb-first pattern
is_verb_first() {
    local name="$1"
    [[ "$name" =~ ^[a-z]+-[a-z-]+$ ]]
}

# Function to validate agent naming in staged changes
validate_staged_agents() {
    local violations=0
    
    print_status "INFO" "Validating agent naming in staged changes..."
    
    # Get list of modified/added directories
    local changed_dirs=$(git diff --cached --name-only --diff-filter=d | grep -E "^[^/]+\core/ai/skills/[^/]+/$" | sed 's|/||' | sed 's|/$||')
    
    for dir in $changed_dirs; do
        if [ -d "$dir" ]; then
            local agent_name=$(basename "$dir")
            
            # Skip non-agent directories
            if [[ "$agent_name" == "SKILL.md" ]] || [[ "$agent_name" == "scripts" ]] || [[ "$agent_name" == "shared" ]] || [[ "$agent_name" == "examples" ]]; then
                continue
            fi
            
            # Check naming convention
            if ! is_verb_first "$agent_name"; then
                print_status "ERROR" "Agent '$agent_name' does not follow verb-first pattern [verb]-[qualifier]"
                echo "Expected pattern: analyze-backstage-catalog, manage-infrastructure, optimize-costs"
                echo "Found pattern: $agent_name"
                ((violations++))
            fi
            
            # Check SKILL.md compliance if it exists
            local skill_file="$dir/SKILL.md"
            if [ -f "$skill_file" ]; then
                local name_in_file=$(grep "^name:" "$skill_file" | sed 's/name: //' | sed 's/^ *//')
                if [ "$name_in_file" != "$agent_name" ]; then
                    print_status "ERROR" "SKILL.md name field '$name_in_file' does not match directory name '$agent_name'"
                    ((violations++))
                fi
            fi
        fi
    done
    
    if [ $violations -gt 0 ]; then
        print_status "ERROR" "Found $violations naming convention violations. Commit blocked."
        print_status "INFO" "Run './core/automation/scripts/ensure-agent-naming-standards.sh fix' to correct issues."
        exit 1
    else
        print_status "SUCCESS" "All agent naming conventions validated successfully!"
        exit 0
    fi
}

# Main execution
validate_staged_agents
