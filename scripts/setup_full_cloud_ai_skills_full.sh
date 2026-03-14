#!/bin/bash
# File: setup_full_cloud_ai_skills_full.sh
# Purpose: All-in-one script to scaffold 400 Cloud AI skills × 4 platforms (1600 entries)
# Includes SKILL.md, PR-ready GitOps scripts, references, and agent metadata

REPO_DIR="${1:-.}"  # Default to current directory
SKILLS_DIR="$REPO_DIR/.agents/skills"

# Generate 400 placeholder skill names
SKILLS=()
for i in $(seq 1 400); do
  SKILLS+=("cloud-ai-skill-$i")
done

PLATFORMS=("aws" "azure" "gcp" "on-prem")

# Advisory vs Actionable: even-numbered skills are actionable
is_actionable() {
  local n=$1
  if (( n % 2 == 0 )); then
    echo "true"
  else
    echo "false"
  fi
}

# Populate SKILL_COMMANDS for all 400 skills by category
declare -A SKILL_COMMANDS
for i in {1..40};   do SKILL_COMMANDS["cloud-ai-skill-$i"]="kubectl get nodes; kubectl get pods --all-namespaces"; done
for i in {41..80};  do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Generating manifests; mkdir -p generated; echo '# Kubernetes YAML' > generated/deploy.yaml"; done
for i in {81..120}; do SKILL_COMMANDS["cloud-ai-skill-$i"]="helm upgrade --install mychart ./charts/mychart"; done
for i in {121..160};do SKILL_COMMANDS["cloud-ai-skill-$i"]="kubectl diff -f generated/deploy.yaml"; done
for i in {161..200};do SKILL_COMMANDS["cloud-ai-skill-$i"]="kubectl create rolebinding example --clusterrole=edit --user=dev@example.com"; done
for i in {201..230};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Building dashboards...; grafana-cli admin reset-admin-password"; done
for i in {231..250};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Analyzing costs; aws ce get-cost-and-usage --time-period Start=2026-03-01,End=2026-03-31"; done
for i in {251..270};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Verifying backups; restic snapshots"; done
for i in {271..300};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Reviewing GitOps repo structure..."; done
for i in {301..320};do SKILL_COMMANDS["cloud-ai-skill-$i"]="kubectl get roles --all-namespaces; vault policy read default"; done
for i in {321..340};do SKILL_COMMANDS["cloud-ai-skill-$i"]="terraform init; terraform plan -out=tfplan; terraform apply tfplan"; done
for i in {341..360};do SKILL_COMMANDS["cloud-ai-skill-$i"]="kubectl apply -f compositions/"; done
for i in {361..370};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Prioritizing alerts..."; done
for i in {371..390};do SKILL_COMMANDS["cloud-ai-skill-$i"]="git checkout -b fix/\$skill; git add .; git commit -m 'Auto PR by \$skill'; git push origin fix/\$skill"; done
for i in {391..400};do SKILL_COMMANDS["cloud-ai-skill-$i"]="echo Applying automated fixes; ./scripts/run.sh"; done

# Helper to create SKILL.md
create_skill_md() {
  local path=$1
  local skill=$2
  local platform=$3
  local advisory=$4
  local actionable=$5
  cat > "$path" <<EOF
name: $skill-$platform
description: Cloud AI skill "$skill" for platform "$platform".
instructions: |
  This skill is $( [[ $advisory == "true" ]] && echo "Advisory (read-only)" || echo "Actionable (can generate PRs or run fixes)" ).
metadata:
  advisory: $advisory
  actionable: $actionable
EOF
}

# Helper to create run script with example GitOps commands
create_run_script() {
  local path=$1
  local skill=$2
  local platform=$3
  local actionable=$4
  cat > "$path" <<EOF
#!/bin/bash
echo "Running $skill on $platform"
EOF

  if [[ $actionable == "true" ]]; then
    cmds="${SKILL_COMMANDS[$skill]}"
    if [[ -n "$cmds" ]]; then
      while IFS= read -r line; do
        echo "$line" >> "$path"
      done <<< "$cmds"
    else
      echo "echo Placeholder actionable commands for $skill" >> "$path"
    fi
    cat >> "$path" <<'EOF'

# Example PR workflow
# git checkout -b fix/$skill
# git add .
# git commit -m "Automated changes by $skill"
# git push origin fix/$skill
EOF
  fi
  chmod +x "$path"
}

# Loop through all skills × platforms
for idx in "${!SKILLS[@]}"; do
  skill="${SKILLS[$idx]}"
  actionable=$(is_actionable $idx)
  advisory="true"

  for platform in "${PLATFORMS[@]}"; do
    BASE_PATH="$SKILLS_DIR/$skill/$platform"
    mkdir -p "$BASE_PATH/scripts" "$BASE_PATH/references" "$BASE_PATH/agents"

    # SKILL.md
    create_skill_md "$BASE_PATH/SKILL.md" "$skill" "$platform" "$advisory" "$actionable"

    # Run script
    create_run_script "$BASE_PATH/scripts/run.sh" "$skill" "$platform" "$actionable"

    # Reference
    cat > "$BASE_PATH/references/ref.md" <<EOF
# Reference for $skill on $platform
Add cloud provider docs, runbooks, or GitOps workflow references here.
EOF

    # Agent metadata
    cat > "$BASE_PATH/agents/openai.yaml" <<EOF
name: $skill-$platform
version: 1.0
dependencies: []
EOF

    echo "Created $skill on $platform (Advisory=$advisory, Actionable=$actionable)"
  done
done

# Validation
echo
echo "Validation Report:"
missing_dirs=0
for skill in "${SKILLS[@]}"; do
  for platform in "${PLATFORMS[@]}"; do
    BASE_PATH="$SKILLS_DIR/$skill/$platform"
    for sub in SKILL.md scripts references agents; do
      if [[ ! -e "$BASE_PATH/$sub" && ! -d "$BASE_PATH/$sub" ]]; then
        echo "Missing: $BASE_PATH/$sub"
        ((missing_dirs++))
      fi
    done
  done
done

if [[ $missing_dirs -eq 0 ]]; then
  echo "All 1600 skill entries successfully created with example GitOps commands."
else
  echo "Warning: $missing_dirs files/folders missing."
fi
