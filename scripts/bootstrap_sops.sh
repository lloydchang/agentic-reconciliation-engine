# bootstrap_sops.sh
# Minimal SOPS bootstrap for a fresh clone

set -euo pipefail
set -x   # optional, enable for debug output

# Directories and files
SOPS_KEY_DIR=.sops-keys
AGE_KEY_FILE=$SOPS_KEY_DIR/age.agekey
SCRIPT_NAME=remove_age_key_and_reencrypt.sh
SCRIPT_DEST_DIR=scripts

# Create SOPS key directory if it doesn't exist
mkdir -p $SOPS_KEY_DIR

# Generate a new Age key if missing
if [ ! -f "$AGE_KEY_FILE" ]; then
    echo "Generating new Age key..."
    age-keygen -o "$AGE_KEY_FILE"
    AGE_PUBLIC_KEY=$(age-keygen -y "$AGE_KEY_FILE")
    echo "Public key: $AGE_PUBLIC_KEY"
else
    echo "Age key already exists at $AGE_KEY_FILE"
fi

# Ensure scripts directory exists
mkdir -p $SCRIPT_DEST_DIR

# Copy the cleanup/encryption script if missing or updated
if [ ! -f "$SCRIPT_DEST_DIR/$SCRIPT_NAME" ] || ! cmp -s "$SCRIPT_NAME" "$SCRIPT_DEST_DIR/$SCRIPT_NAME"; then
    echo "Adding/updating $SCRIPT_NAME in $SCRIPT_DEST_DIR"
    cp "$SCRIPT_NAME" "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
    chmod +x "$SCRIPT_DEST_DIR/$SCRIPT_NAME"
fi

echo "Bootstrap complete. You can now run: $SCRIPT_DEST_DIR/$SCRIPT_NAME"
