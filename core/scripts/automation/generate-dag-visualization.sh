#!/bin/bash
# Generate DAG visualization from Flux Kustomization dependsOn relationships
# Outputs Mermaid format for documentation
# Supports variant and ecosystem visualization

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "# Flux Infrastructure DAG Visualization"
echo ""
echo "Generated from Kustomization dependsOn relationships across the repository"
echo ""

# Function to extract dependsOn from a Kustomization
get_dependencies() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        return
    fi

    # Extract name more precisely
    local name=$(grep -A2 "^metadata:" "$file" | grep "^  name:" | head -1 | sed 's/.*name: //' | tr -d ' ')

    # Extract variant from labels
    local variant=$(grep -A10 "labels:" "$file" | grep "variant:" | sed 's/.*variant: //' | tr -d ' ' | head -1 || echo "unknown")
    
    # Extract ecosystem from labels
    local ecosystem=$(grep -A10 "labels:" "$file" | grep "ecosystem:" | sed 's/.*ecosystem: //' | tr -d ' ' | head -1 || echo "unknown")

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
        echo "$name|$depends_on|$variant|$ecosystem"
    fi
}

# Collect all Kustomizations
echo "## Current Kustomization Dependencies"
echo ""

# Use indexed arrays instead of associative arrays for compatibility
declare -a names
declare -a deps_list
declare -a variants
declare -a ecosystems

# Initialize arrays
names=()
deps_list=()
variants=()
ecosystems=()

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
    if [[ ${#names[@]} -eq 0 ]]; then
        return 1
    fi
    for name in "${names[@]}"; do
        if [[ "$name" == "$target" ]]; then
            return 0
        fi
    done
    return 1
}

while IFS='|' read -r name deps variant ecosystem; do
    if [[ -n "$name" ]]; then
        # Clean up deps (remove extra spaces)
        deps=$(echo "$deps" | sed 's/  */ /g' | sed 's/^ *//;s/ *$//')
        # Check if name already exists to avoid duplicates
        if ! has_name "$name"; then
            names+=("$name")
            deps_list+=("$deps")
            variants+=("$variant")
            ecosystems+=("$ecosystem")
        fi
    fi
done < <(for file in "$REPO_ROOT"/core/operators/flux/*.yaml "$REPO_ROOT"/core/resources/tenants/*/kustomization.yaml "$REPO_ROOT"/overlay/examples/*/kustomization.yaml; do
    [[ "$file" == *install.yaml ]] && continue  # Skip the large install file
    get_dependencies "$file"
done)

# Print dependency table with variant and ecosystem info
echo "| Kustomization | Depends On | Variant | Ecosystem |"
echo "|--------------|------------|---------|-----------|"
for i in "${!names[@]}"; do
    name="${names[$i]}"
    deps="${deps_list[$i]}"
    variant="${variants[$i]}"
    ecosystem="${ecosystems[$i]}"
    if [[ -z "$deps" ]]; then
        echo "| $name | (none) | $variant | $ecosystem |"
    else
        echo "| $name | $deps | $variant | $ecosystem |"
    fi
done

echo ""
echo "## Mermaid DAG Diagram"
echo ""
echo "\`\`\`mermaid"
echo "graph TD"
echo "    %% Root node"
echo "    Git[Git Repository<br/>Source of Truth] --> Flux[Flux Controllers<br/>flux-system]"

# Generate Mermaid edges with variant/ecosystem styling
for i in "${!names[@]}"; do
    name="${names[$i]}"
    deps="${deps_list[$i]}"
    variant="${variants[$i]}"
    ecosystem="${ecosystems[$i]}"

    # Create node with variant/ecosystem info
    node_label="$name"
    if [[ "$variant" != "unknown" ]]; then
        node_label="$node_label<br/><small>variant: $variant</small>"
    fi
    if [[ "$ecosystem" != "unknown" ]]; then
        node_label="$node_label<br/><small>ecosystem: $ecosystem</small>"
    fi

    if [[ -z "$deps" ]]; then
        # No dependencies - connect to Flux
        echo "    Flux --> $name[\"$node_label\"]"
    else
        # Has dependencies - connect each dep to this node
        for dep in $deps; do
            echo "    $dep --> $name[\"$node_label\"]"
        done
    fi
done

# Enhanced styling for variants and ecosystems
echo ""
echo "    %% Styling"
echo "    classDef git fill:#e8f4fd,stroke:#0066cc,stroke-width:2px"
echo "    classDef flux fill:#fff2cc,stroke:#d6b656,stroke-width:2px"
echo "    classDef network fill:#d5e8d4,stroke:#82b366,stroke-width:2px"
echo "    classDef cluster fill:#ffe6cc,stroke:#d79b00,stroke-width:2px"
echo "    classDef workload fill:#f8cecc,stroke:#b85450,stroke-width:2px"
echo "    classDef opensource fill:#e8f5e8,stroke:#4caf50,stroke-width:2px"
echo "    classDef smallbusiness fill:#fff3e0,stroke:#ff9800,stroke-width:2px"
echo "    classDef enterprise fill:#fce4ec,stroke:#e91e63,stroke-width:2px"
echo "    classDef rust fill:#fff8e1,stroke:#ffc107,stroke-width:2px"
echo "    classDef go fill:#e3f2fd,stroke:#2196f3,stroke-width:2px"
echo "    classDef python fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px"
echo "    classDef typescript fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px"
echo "    classDef dotnet fill:#fce4ec,stroke:#e91e63,stroke-width:2px"
echo "    classDef java fill:#ffebee,stroke:#f44336,stroke-width:2px"
echo "    classDef shell fill:#f1f8e9,stroke:#4caf50,stroke-width:2px"
echo ""
echo "    class Git git"
echo "    class Flux flux"

# Apply styling based on naming patterns, variants, and ecosystems
for i in "${!names[@]}"; do
    name="${names[$i]}"
    variant="${variants[$i]}"
    ecosystem="${ecosystems[$i]}"
    
    # Apply variant styling
    if [[ "$variant" == "opensource" ]]; then
        echo "    class $name opensource"
    elif [[ "$variant" == "small-business" ]]; then
        echo "    class $name smallbusiness"
    elif [[ "$variant" == "enterprise" ]]; then
        echo "    class $name enterprise"
    # Apply ecosystem styling if no variant
    elif [[ "$ecosystem" == "rust" ]]; then
        echo "    class $name rust"
    elif [[ "$ecosystem" == "go" ]]; then
        echo "    class $name go"
    elif [[ "$ecosystem" == "python" ]]; then
        echo "    class $name python"
    elif [[ "$ecosystem" == "typescript" ]]; then
        echo "    class $name typescript"
    elif [[ "$ecosystem" == "dotnet" ]]; then
        echo "    class $name dotnet"
    elif [[ "$ecosystem" == "java" ]]; then
        echo "    class $name java"
    elif [[ "$ecosystem" == "shell" ]]; then
        echo "    class $name shell"
    # Apply tier-based styling
    elif [[ "$name" == *network* ]]; then
        echo "    class $name network"
    elif [[ "$name" == *cluster* ]]; then
        echo "    class $name cluster"
    elif [[ "$name" == *workload* ]]; then
        echo "    class $name workload"
    fi
done

echo "\`\`\`"

echo ""
echo "## Validation"
echo ""

# Check for cycles (basic check)
echo "### Cycle Detection"

# Simple cycle detection - check for any mutual dependencies
has_cycles=false
for i in "${!names[@]}"; do
    name="${names[$i]}"
    deps="${deps_list[$i]}"

    for dep in $deps; do
        # Check if the dependency depends back on this node
        for j in "${!names[@]}"; do
            if [[ "${names[$j]}" == "$dep" ]]; then
                dep_deps="${deps_list[$j]}"
                for dep_dep in $dep_deps; do
                    if [[ "$dep_dep" == "$name" ]]; then
                        echo "❌ Cycle detected: $name -> $dep -> $name"
                        has_cycles=true
                    fi
                done
                break
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

for i in "${!names[@]}"; do
    name="${names[$i]}"
    # Check if this node is depended on by others
    is_depended_on=false
    for j in "${!names[@]}"; do
        deps="${deps_list[$j]}"
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
    deps="${deps_list[$i]}"
    if [[ -z "$deps" ]]; then
        leaf_nodes="$leaf_nodes $name"
    fi
done

echo "Root nodes (no dependencies):${root_nodes:- none}"
echo "Leaf nodes (no dependents):${leaf_nodes:- none}"

# Count connections
total_nodes=${#names[@]}
echo "Total nodes: $total_nodes"

if [[ $total_nodes -gt 0 ]]; then
    echo "✅ DAG connectivity validated"
fi
