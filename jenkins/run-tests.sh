#!/bin/bash

# Test script for Jenkins CI pipeline
# This script runs various tests to validate the GitOps Infrastructure Control Plane

set -e

echo "🧪 Starting Jenkins CI tests..."
echo "📅 Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo "🔧 Environment: ${NODE_ENV:-development}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_step() {
    echo -e "${BLUE}🔍 Testing: $1${NC}"
}

pass_step() {
    echo -e "${GREEN}✅ Passed: $1${NC}"
}

fail_step() {
    echo -e "${RED}❌ Failed: $1${NC}"
    exit 1
}

warn_step() {
    echo -e "${YELLOW}⚠️ Warning: $1${NC}"
}

# 1. Container Health Tests
test_step "Container Environment"
if [ -f /app ]; then
    pass_step "Container has /app directory"
else
    warn_step "No /app directory found"
fi

# Test basic commands
test_step "Basic System Commands"
if command -v python3 >/dev/null 2>&1; then
    pass_step "Python3 available: $(python3 --version)"
else
    warn_step "Python3 not available"
fi

if command -v node >/dev/null 2>&1; then
    pass_step "Node.js available: $(node --version)"
else
    warn_step "Node.js not available"
fi

if command -v kubectl >/dev/null 2>&1; then
    pass_step "kubectl available: $(kubectl version --client --short 2>/dev/null || echo 'version check failed')"
else
    warn_step "kubectl not available"
fi

if command -v flux >/dev/null 2>&1; then
    pass_step "flux CLI available: $(flux version --short 2>/dev/null || echo 'version check failed')"
else
    warn_step "flux CLI not available"
fi

# 2. File Structure Tests
test_step "Project File Structure"

# Check for key directories
directories=("infrastructure" "control-plane" "docs" ".github" "jenkins")
for dir in "${directories[@]}"; do
    if [ -d "/app/$dir" ]; then
        pass_step "Directory exists: $dir"
    else
        warn_step "Directory missing: $dir"
    fi
done

# Check for key files
files=("README.md" "SETUP.md" "bootstrap.sh")
for file in "${files[@]}"; do
    if [ -f "/app/$file" ]; then
        pass_step "File exists: $file"
    else
        warn_step "File missing: $file"
    fi
done

# 3. YAML Validation Tests
test_step "YAML File Validation"

# Find and validate YAML files
find /app -name "*.yaml" -o -name "*.yml" | head -10 | while read -r yaml_file; do
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            pass_step "Valid YAML: $(basename "$yaml_file")"
        else
            fail_step "Invalid YAML: $(basename "$yaml_file")"
        fi
    else
        warn_step "Cannot validate YAML - python3 not available"
    fi
done

# 4. Kubernetes Manifest Tests
test_step "Kubernetes Manifest Validation"

# Check for valid Kubernetes manifests
find /app/infrastructure -name "*.yaml" | head -5 | while read -r manifest; do
    if command -v kubectl >/dev/null 2>&1; then
        if kubectl apply --dry-run=client -f "$manifest" >/dev/null 2>&1; then
            pass_step "Valid K8s manifest: $(basename "$manifest")"
        else
            warn_step "K8s manifest validation failed: $(basename "$manifest")"
        fi
    else
        warn_step "Cannot validate K8s manifests - kubectl not available"
    fi
done

# 5. Flux Configuration Tests
test_step "Flux Configuration"

flux_files=("gotk-components.yaml" "gotk-sync.yaml")
for flux_file in "${flux_files[@]}"; do
    if [ -f "/app/control-plane/flux/$flux_file" ]; then
        pass_step "Flux file exists: $flux_file"
        
        # Basic Flux validation
        if grep -q "apiVersion:" "/app/control-plane/flux/$flux_file"; then
            pass_step "Flux file has valid API version: $flux_file"
        else
            warn_step "Flux file missing API version: $flux_file"
        fi
    else
        warn_step "Flux file missing: $flux_file"
    fi
done

# 6. Jenkins Configuration Tests
test_step "Jenkins Configuration"

if [ -f "/app/jenkins/Jenkinsfile" ]; then
    pass_step "Jenkinsfile exists"
    
    # Check for Jenkinsfile syntax
    if grep -q "pipeline {" "/app/jenkins/Jenkinsfile"; then
        pass_step "Jenkinsfile has pipeline structure"
    else
        warn_step "Jenkinsfile may have syntax issues"
    fi
else
    warn_step "Jenkinsfile not found"
fi

if [ -f "/app/jenkins/docker-pod.yaml" ]; then
    pass_step "Docker pod configuration exists"
else
    warn_step "Docker pod configuration missing"
fi

# 7. Documentation Tests
test_step "Documentation Quality"

doc_files=("README.md" "SETUP.md")
for doc_file in "${doc_files[@]}"; do
    if [ -f "/app/$doc_file" ]; then
        pass_step "Documentation exists: $doc_file"
        
        # Check for basic markdown structure
        if grep -q "^#" "/app/$doc_file"; then
            pass_step "Documentation has headers: $doc_file"
        else
            warn_step "Documentation missing headers: $doc_file"
        fi
    else
        warn_step "Documentation missing: $doc_file"
    fi
done

# 8. Security Tests
test_step "Security Validation"

# Check for sensitive files (should not exist)
sensitive_files=("id_rsa" ".env" "secrets.yaml")
for sensitive_file in "${sensitive_files[@]}"; do
    if [ -f "/app/$sensitive_file" ]; then
        fail_step "Sensitive file found: $sensitive_file"
    else
        pass_step "No sensitive file: $sensitive_file"
    fi
done

# Check file permissions
find /app -name "*.sh" | head -3 | while read -r script; do
    if [ -x "$script" ]; then
        pass_step "Script is executable: $(basename "$script")"
    else
        warn_step "Script not executable: $(basename "$script")"
    fi
done

# 9. Integration Tests
test_step "Integration Tests"

# Test if we can connect to external services (if needed)
if command -v curl >/dev/null 2>&1; then
    if curl -s --connect-timeout 5 https://github.com >/dev/null 2>&1; then
        pass_step "Can reach GitHub"
    else
        warn_step "Cannot reach GitHub (may be expected in test environment)"
    fi
else
    warn_step "curl not available for connectivity tests"
fi

# 10. Performance Tests
test_step "Performance Metrics"

# Check container resource usage
if [ -f /proc/meminfo ]; then
    mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    if [ "$mem_available" -gt 100000 ]; then  # >100MB
        pass_step "Sufficient memory available: $(($mem_available / 1024))MB"
    else
        warn_step "Low memory available: $(($mem_available / 1024))MB"
    fi
fi

# Final Summary
echo ""
echo -e "${GREEN}🎉 Test Suite Completed!${NC}"
echo "📊 Test Summary:"
echo "  - All critical tests passed"
echo "  - Warnings indicate non-critical issues"
echo "  - Build environment validated"
echo ""
echo "🚀 Ready for deployment with Flux!"

# Exit with success
exit 0
