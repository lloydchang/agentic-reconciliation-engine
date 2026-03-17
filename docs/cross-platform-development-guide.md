# Cross-Platform Development Guide

## Overview

This guide documents cross-platform development practices and tools for maintaining consistent behavior across macOS, Linux, and Windows environments. It covers command-line tools, scripting patterns, and platform-specific considerations.

## Table of Contents

1. [Sed Command Usage](#sed-command-usage)
2. [Cross-Platform Scripting](#cross-platform-scripting)
3. [File Path Handling](#file-path-handling)
4. [Tool Installation](#tool-installation)
5. [Testing Strategies](#testing-strategies)

## Sed Command Usage

### The Problem

Standard `sed` command has different syntax and behavior across platforms:

- **macOS (BSD sed)**: Uses `sed -i ''` for in-place editing
- **Linux (GNU sed)**: Uses `sed -i` for in-place editing
- **BSD vs GNU**: Different flag behaviors and regex syntax

### Solution: Use GNU sed (gsed)

Always use `gsed` (GNU sed) instead of `sed` for consistent cross-platform behavior.

#### Installation

```bash
# macOS
brew install gnu-sed

# Linux (usually pre-installed)
which sed  # Check if GNU sed is available

# CI/CD Environments
# Ensure gsed is available or use platform-specific logic
```

#### Usage Examples

```bash
# Instead of platform-specific sed:
sed -i '' 's/old/new/g' file.txt  # macOS only
sed -i 's/old/new/g' file.txt    # Linux only

# Use gsed for consistency:
gsed -i 's/old/new/g' file.txt   # Works everywhere

# Complex patterns with delimiters:
gsed -i 's|pattern|replacement|g' file.txt
gsed -i 's@/old/path@/new/path@g' file.txt
```

#### Benefits

- **Consistent behavior** across macOS and Linux
- **Better regex support** and advanced features
- **Standardized flag syntax** (`-i` works the same way)
- **Fewer platform-specific bugs** in scripts

### Common Patterns

#### Variable Expansion in Files

```bash
# Replace placeholders with environment variables
gsed -i "s|{{API_URL}}|$API_URL|g" config.yaml
gsed -i "s|{{NAMESPACE}}|$NAMESPACE|g" deployment.yaml
```

#### Multi-line Replacements

```bash
# Use different delimiters for complex strings
gsed -i 's|<old-block>|new content here|g' file.xml
```

#### Backup and Edit

```bash
# Create backup before editing
gsed -i.bak 's/old/new/g' file.txt
```

### Verification

Always test sed operations on both platforms:

```bash
# Test command availability
gsed --version | head -1

# Test basic functionality
echo "test string" | gsed 's/test/replace/'
```

## Cross-Platform Scripting

### Shell Script Considerations

#### Shebang Lines
```bash
#!/bin/bash  # Use bash for better compatibility
#!/usr/bin/env bash  # Portable shebang
```

#### Command Detection
```bash
# Check for command availability
if command -v gsed >/dev/null 2>&1; then
    SED_CMD="gsed"
elif command -v sed >/dev/null 2>&1; then
    SED_CMD="sed"
    # Handle macOS sed quirks here
else
    echo "sed not found"
    exit 1
fi
```

#### Platform Detection
```bash
# Detect operating system
case "$(uname -s)" in
    Darwin)
        OS="macOS"
        ;;
    Linux)
        OS="Linux"
        ;;
    CYGWIN*|MINGW*|MSYS*)
        OS="Windows"
        ;;
    *)
        OS="Unknown"
        ;;
esac
```

### File and Path Handling

#### Path Separators

```bash
# Use forward slashes for cross-platform compatibility
CONFIG_DIR="/etc/myapp"  # Works on all platforms
DATA_DIR="./data"        # Relative paths work everywhere

# Avoid backslashes in scripts
# ❌ WRONG: C:\Program Files\app
# ✅ RIGHT: /c/Program\ Files/app (in scripts)
```

#### Temporary Files

```bash
# Use mktemp for cross-platform temporary files
TEMP_FILE=$(mktemp)
TEMP_DIR=$(mktemp -d)

# Clean up on exit
trap "rm -f $TEMP_FILE" EXIT
trap "rm -rf $TEMP_DIR" EXIT
```

#### File Permissions

```bash
# Set executable permissions consistently
chmod +x script.sh

# Check permissions
if [[ -x "$file" ]]; then
    echo "File is executable"
fi
```

### Tool Compatibility Matrix

| Tool | macOS | Linux | Windows | Notes |
|------|-------|-------|---------|-------|
| `gsed` | ✅ (brew) | ✅ | ❌ | GNU sed required |
| `bash` | ✅ | ✅ | ✅ (WSL/Git Bash) | Use bash 4+ |
| `grep` | ✅ | ✅ | ✅ | GNU grep preferred |
| `awk` | ✅ | ✅ | ✅ | GNU awk for advanced features |
| `curl` | ✅ | ✅ | ✅ | Use for HTTP requests |
| `jq` | ✅ (brew) | ✅ | ✅ (binaries) | JSON processing |

## File Path Handling

### Absolute vs Relative Paths

```bash
# Get script directory (cross-platform)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Construct paths
CONFIG_FILE="$SCRIPT_DIR/../config/app.yaml"
DATA_DIR="$SCRIPT_DIR/../data"
```

### Path Normalization

```bash
# Normalize paths
normalize_path() {
    local path="$1"
    # Remove double slashes, resolve . and ..
    echo "$path" | sed 's|//|/|g' | sed 's|/\./|/|g'
}
```

### Windows Path Conversion

```bash
# Convert Unix paths to Windows (when needed)
unix_to_windows() {
    local path="$1"
    if [[ "$OS" == "Windows" ]]; then
        echo "$path" | sed 's|^/c/|C:/|g' | sed 's|/|\\|g'
    else
        echo "$path"
    fi
}
```

## Tool Installation

### Package Managers by Platform

```bash
# macOS
if command -v brew >/dev/null 2>&1; then
    brew install gnu-sed jq curl
fi

# Ubuntu/Debian
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y sed jq curl
fi

# CentOS/RHEL
if command -v yum >/dev/null 2>&1; then
    sudo yum install -y sed jq curl
fi

# Alpine
if command -v apk >/dev/null 2>&1; then
    apk add sed jq curl
fi
```

### Version Checking

```bash
# Verify tool versions
check_versions() {
    echo "bash: $(bash --version | head -1)"
    echo "gsed: $(gsed --version | head -1 2>/dev/null || echo 'not found')"
    echo "jq: $(jq --version 2>/dev/null || echo 'not found')"
}
```

## Testing Strategies

### Platform-Specific Testing

#### CI/CD Pipeline Setup

```yaml
# GitHub Actions example
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - name: Install dependencies
        run: |
          if [[ "$RUNNER_OS" == "macOS" ]]; then
            brew install gnu-sed jq
          else
            sudo apt-get install -y sed jq
          fi
      - name: Run tests
        run: ./test.sh
```

### Script Testing Checklist

- [ ] Test on macOS with bash
- [ ] Test on Linux with bash
- [ ] Test on Windows with Git Bash/WSL
- [ ] Verify all external commands exist
- [ ] Check path handling with spaces
- [ ] Test with different file permissions
- [ ] Verify error handling works

### Common Pitfalls to Avoid

1. **Hardcoded Paths**
   ```bash
   # ❌ WRONG
   CONFIG_FILE="/usr/local/etc/app.conf"

   # ✅ RIGHT
   CONFIG_FILE="${CONFIG_DIR:-/usr/local/etc}/app.conf"
   ```

2. **Platform-Specific Commands**
   ```bash
   # ❌ WRONG
   ls -la  # May behave differently

   # ✅ RIGHT
   ls -la 2>/dev/null || ls -l  # Graceful fallback
   ```

3. **Case Sensitivity**
   ```bash
   # ❌ WRONG (Windows is case-insensitive)
   if [[ "$var" == "Value" ]]; then

   # ✅ RIGHT
   if [[ "${var,,}" == "value" ]]; then  # Convert to lowercase
   ```

## Best Practices

### Script Template

```bash
#!/usr/bin/env bash
set -euo pipefail  # Strict error handling

# Detect OS
case "$(uname -s)" in
    Darwin) OS="macOS" ;;
    Linux) OS="Linux" ;;
    *) OS="Unknown" ;;
esac

# Setup tools
setup_tools() {
    if [[ "$OS" == "macOS" ]]; then
        # macOS-specific setup
        export PATH="/usr/local/bin:$PATH"
    fi
}

# Main logic with error handling
main() {
    setup_tools
    
    # Use gsed for consistency
    if command -v gsed >/dev/null 2>&1; then
        SED_CMD="gsed"
    else
        SED_CMD="sed"
    fi
    
    # Your script logic here
    echo "Running on $OS with $SED_CMD"
}

main "$@"
```

### Error Handling

```bash
# Robust error handling
trap 'echo "Error on line $LINENO"' ERR
set -e  # Exit on error

# Check command availability
require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Required command '$1' not found"
        exit 1
    fi
}

require_command gsed
require_command jq
```

### Documentation

Always document platform requirements:

```bash
# REQUIREMENTS:
# - bash 4.0+
# - gsed (GNU sed)
# - jq 1.5+
# - curl
#
# INSTALLATION:
# macOS: brew install gnu-sed jq curl
# Ubuntu: sudo apt-get install sed jq curl
```

---

This guide ensures consistent development practices across all supported platforms, reducing bugs and maintenance overhead.
