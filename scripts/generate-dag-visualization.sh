#!/bin/bash
# Generate DAG visualization from Flux Kustomization dependsOn relationships
# Outputs Mermaid format for documentation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "# Flux Infrastructure DAG Visualization"
echo ""
echo "Generated from Kustomization dependsOn relationships in control-plane/flux/"
echo ""

# Function to extract dependsOn from a Kustomization
get_dependencies() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        return
    fi

    # Extract name more precisely
    local name=$(grep -A2 "^metadata:" "$file" | grep "^  name:" | head -1 | sed 's/.*name: //' | tr -d ' ')

    # Extract dependsOn more precisely - only get name fields under dependsOn
    local depends_on=""
    if grep -q "dependsOn:" "$file"; then
        # Find the line number where dependsOn starts
        local depends_line=$(grep -n "dependsOn:" "$file" | head -1 | cut -d: -f1)
        if [[ -n "$depends_line" ]]; then
            # Get all lines after dependsOn until the next top-level key (same indentation as dependsOn)
            local depends_section=$(tail -n +$((depends_line + 1)) "$file" | grep -E "^\s*-\s*name:" | sed 's/.*name: //' | tr -d ' ' | tr '\n' ' ')
            depends_on="$depends_section"
        fi
    fi

    # Only output if we have a valid name
    if [[ -n "$name" ]]; then
        echo "$name|$depends_on"
    fi
}

# Collect all Kustomizations
echo "## Current Kustomization Dependencies"
echo ""

# Use indexed arrays instead of associative arrays for compatibility
declare -a names
declare -a deps_list

# Function to get dependency for a name
get_dep() {
    local target="$1"
    for i in "${!names[@]}"; do
        if [[ "${names[$i]}" == "$target" ]]; then
            echo "${deps_list[$i]}"
            return
        fi
    done
    echo ""
}

# Function to check if name exists
has_name() {
    local target="$1"
    for name in "${names[@]}"; do
        if [[ "$name" == "$target" ]]; then
            return 0
        fi
    done
    return 1
}

while IFS='|' read -r name deps; do
    if [[ -n "$name" ]]; then
        # Clean up deps (remove extra spaces)
        deps=$(echo "$deps" | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')
        # Check if name already exists to avoid duplicates
        if ! has_name "$name"; then
            names+=("$name")
            deps_list+=("$deps")
        fi
    fi
done < <(for file in "$REPO_ROOT/control-plane/flux"/*.yaml; do
    [[ "$file" == *install.yaml ]] && continue  # Skip the large install file
    get_dependencies "$file"
done)

# Print dependency table
echo "| Kustomization | Depends On |"
echo "|--------------|------------|"
for i in "${!names[@]}"; do
    name="${names[$i]}"
    deps="${deps_list[$i]}"
    if [[ -z "$deps" ]]; then
        echo "| $name | (none) |"
    else
        echo "| $name | $deps |"
    fi
done

echo ""
echo "## Mermaid DAG Diagram"
echo ""
echo "\`\`\`mermaid"
echo "graph TD"
echo "    %% Root node"
echo "    Git[Git Repository<br/>Source of Truth] --> Flux[Flux Controllers<br/>flux-system]"

# Generate Mermaid edges
for i in "${!names[@]}"; do
    name="${names[$i]}"
    deps="${deps_list[$i]}"

    if [[ -z "$deps" ]]; then
        # No dependencies - connect to Flux
        echo "    Flux --> $name[$name]"
    else
        # Has dependencies - connect each dep to this node
        for dep in $deps; do
            echo "    $dep --> $name[$name]"
        done
    fi
done

# Styling
echo ""
echo "    %% Styling"
echo "    classDef git fill:#e8f4fd,stroke:#0066cc,stroke-width:2px"
echo "    classDef flux fill:#fff2cc,stroke:#d6b656,stroke-width:2px"
echo "    classDef network fill:#d5e8d4,stroke:#82b366,stroke-width:2px"
echo "    classDef cluster fill:#ffe6cc,stroke:#d79b00,stroke-width:2px"
echo "    classDef workload fill:#f8cecc,stroke:#b85450,stroke-width:2px"
echo ""
echo "    class Git git"
echo "    class Flux flux"

# Apply styling based on naming patterns
network_nodes=""
cluster_nodes=""
workload_nodes=""

for name in "${!dependencies[@]}"; do
    if [[ "$name" == *network* ]]; then
        network_nodes="$network_nodes,$name"
    elif [[ "$name" == *cluster* ]]; then
        cluster_nodes="$cluster_nodes,$name"
    elif [[ "$name" == *workload* ]]; then
        workload_nodes="$workload_nodes,$name"
    fi
done

if [[ -n "$network_nodes" ]]; then
    echo "    class ${network_nodes#,} network"
fi
if [[ -n "$cluster_nodes" ]]; then
    echo "    class ${cluster_nodes#,} cluster"
fi
if [[ -n "$workload_nodes" ]]; then
    echo "    class ${workload_nodes#,} workload"
fi

echo "\`\`\`"

echo ""
echo "## Validation"
echo ""

# Check for cycles (basic check)
echo "### Cycle Detection"

# Simple cycle detection - check for any mutual dependencies
has_cycles=false
for name in "${!dependencies[@]}"; do
    deps="${dependencies[$name]}"

    for dep in $deps; do
        # Check if the dependency depends back on this node
        dep_deps="${dependencies[$dep]:-}"
        for dep_dep in $dep_deps; do
            if [[ "$dep_dep" == "$name" ]]; then
                echo "❌ Cycle detected: $name -> $dep -> $name"
                has_cycles=true
            fi
        done
    done
done

if [[ "$has_cycles" == "false" ]]; then
    echo "✅ No cycles detected - DAG is valid"
fi

# Check connectivity
echo ""
echo "### Connectivity Check"
root_nodes=""
leaf_nodes=""

for name in "${!dependencies[@]}"; do
    # Check if this node is depended on by others
    is_depended_on=false
    for other in "${!dependencies[@]}"; do
        deps="${dependencies[$other]}"
        for dep in $deps; do
            if [[ "$dep" == "$name" ]]; then
                is_depended_on=true
                break 2
            fi
        done
    done

    if [[ "$is_depended_on" == "false" ]]; then
        root_nodes="$root_nodes $name"
    fi

    # Check if this node depends on others
    deps="${dependencies[$name]}"
    if [[ -z "$deps" ]]; then
        leaf_nodes="$leaf_nodes $name"
    fi
done

echo "Root nodes (no dependencies):${root_nodes:- none}"
echo "Leaf nodes (no dependents):${leaf_nodes:- none}"

# Count connections
total_nodes=${#dependencies[@]}
echo "Total nodes: $total_nodes"

if [[ $total_nodes -gt 0 ]]; then
    echo "✅ DAG connectivity validated"
fi
