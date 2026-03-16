# File: remove_age_key_and_reencrypt.sh

set -euo pipefail
set -x   # optional, only if you want debug output

REPO_URL=git@github.com:lloydchang/gitops-infra-control-plane.git
WORKDIR=$(mktemp -d -t gitops-infra-clean-XXXX)
SOPS_KEY_DIR=.sops-keys
AGE_KEY_FILE=$SOPS_KEY_DIR/age.agekey
SECRETS_DIR=infrastructure/tenants
SCRIPT_NAME=$(basename "$0")
SCRIPT_DEST_DIR=scripts

echo "Using temporary working directory: $WORKDIR"

# Clean up any previous temp clone
rm -rf "$WORKDIR"

# Clone repo
git clone "$REPO_URL" "$WORKDIR"
cd "$WORKDIR"

# Remove age keys from git history
git filter-repo --force --path age.agekey --path .sops-keys/age.agekey --invert-paths

# Re-add remote
git remote add origin "$REPO_URL"

# Verify removal
git log --all -- age.agekey || true
git log --all -- .sops-keys/age.agekey || true

# Force push cleaned history
git push --force --all origin
git push --force --tags origin

# Ensure SOPS key directory exists
mkdir -p "$SOPS_KEY_DIR"

# Generate new age key
age-keygen -o "$AGE_KEY_FILE"
AGE_PUBLIC_KEY=$(age-keygen -y "$AGE_KEY_FILE")

shopt -s nullglob
ENCRYPTED=false

# Encrypt secret files if they exist
if compgen -G "$SECRETS_DIR/*.secret.yaml" > /dev/null; then
  for secret in "$SECRETS_DIR"/*.secret.yaml; do
    sops --encrypt --in-place "$secret"
  done
  ENCRYPTED=true
else
  echo "No secret files found, skipping encryption."
fi

# Ensure .gitignore rules
grep -qxF "$SOPS_KEY_DIR/" .gitignore || echo "$SOPS_KEY_DIR/" >> .gitignore
grep -qxF '*.agekey' .gitignore || echo '*.agekey' >> .gitignore

# Add the cleanup script to scripts/ if it doesn't exist or has changed
mkdir -p "$SCRIPT_DEST_DIR"
cp "$OLDPWD/$SCRIPT_NAME" "$SCRIPT_DEST_DIR/$SCRIPT_NAME"

# Stage changes
git add .gitignore .sops.yaml "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
git diff --cached --quiet || git commit -m 'Add .gitignore rules, encrypt new secrets, add/update cleanup script'

# Push changes
git push origin main

# Final safety check
FOUND_KEYS=$(git ls-files | grep -E 'age.agekey|\.sops-keys/age.agekey' || true)
if [ -n "$FOUND_KEYS" ]; then
  echo "Warning: Sensitive Age key files still tracked!"
  echo "$FOUND_KEYS"
  exit 1
fi

echo "Cleanup complete. All collaborators must delete old clones and reclone."
echo "Old Age key is invalid. Secrets are now encrypted with a new key and tracked as templates."
echo "Working directory used: $WORKDIR"
