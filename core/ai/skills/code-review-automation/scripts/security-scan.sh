#!/bin/bash

# Code Review Automation - Security Scanning Script
# Scans code changes for security vulnerabilities and issues

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-$(mktemp -d)}"
SECURITY_REPORT="${OUTPUT_DIR}/security-report.json"
LOG_FILE="${OUTPUT_DIR}/security-scan.log"
REPO_DIR="${REPO_DIR:-/tmp/repo}"
PR_NUMBER="${PR_NUMBER:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# Security tools configuration
BANDIT_CONFIG="${BANDIT_CONFIG:-.bandit}"
SECRETS_CONFIG="${SECRETS_CONFIG:-.secrets.baseline}
OWASP_CONFIG="${OWASP_CONFIG:-owasp-dependency-check.conf"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking security scanning prerequisites..."
    
    command -v jq >/dev/null || error_exit "jq is required"
    command -v git >/dev/null || error_exit "git is required"
    
    # Check for security tools
    local tools_found=true
    
    if ! command -v bandit >/dev/null; then
        log "WARNING: bandit not found, Python security scanning disabled"
        tools_found=false
    fi
    
    if ! command -v trufflehog >/dev/null; then
        log "WARNING: trufflehog not found, secret scanning disabled"
        tools_found=false
    fi
    
    if ! command -v semgrep >/dev/null; then
        log "WARNING: semgrep not found, static analysis disabled"
        tools_found=false
    fi
    
    if [[ "$tools_found" == "false" ]]; then
        log "WARNING: Some security tools are not available"
    fi
    
    log "Prerequisites check completed"
}

# Setup repository
setup_repository() {
    log "Setting up repository for security scanning..."
    
    if [[ ! -d "$REPO_DIR" ]]; then
        error_exit "Repository directory not found: $REPO_DIR"
    fi
    
    cd "$REPO_DIR"
    
    # Ensure we're on the PR branch
    if [[ -n "$PR_NUMBER" ]]; then
        log "Fetching PR #$PR_NUMBER"
        git fetch origin "pull/$PR_NUMBER/head:pr-$PR_NUMBER"
        git checkout "pr-$PR_NUMBER"
    fi
    
    # Get changed files
    if [[ -n "$PR_NUMBER" ]]; then
        git diff --name-only HEAD~1 HEAD > "${OUTPUT_DIR}/changed_files.txt"
    else
        git diff --name-only HEAD~1 HEAD > "${OUTPUT_DIR}/changed_files.txt"
    fi
    
    local changed_files_count=$(wc -l < "${OUTPUT_DIR}/changed_files.txt")
    log "Found $changed_files_count changed files"
}

# Scan for Python security issues
scan_python_security() {
    log "Scanning Python code for security issues..."
    
    local python_files=$(grep -E '\.py$' "${OUTPUT_DIR}/changed_files.txt" || true)
    
    if [[ -z "$python_files" ]]; then
        log "No Python files to scan"
        return
    fi
    
    if command -v bandit >/dev/null; then
        local bandit_report="${OUTPUT_DIR}/bandit-report.json"
        
        # Run bandit on changed Python files
        echo "$python_files" | xargs bandit -f json -o "$bandit_report" 2>/dev/null || true
        
        if [[ -f "$bandit_report" ]]; then
            local issues=$(jq '.results | length' "$bandit_report" 2>/dev/null || echo "0")
            log "Bandit found $issues security issues"
            
            # Parse bandit results
            jq -r '.results[] | {
                file: .filename,
                line: .line_number,
                severity: .issue_severity,
                confidence: .issue_cconfidence,
                test_name: .test_name,
                test_id: .test_id,
                message: .issue_text
            }' "$bandit_report" 2>/dev/null || true
        fi
    fi
}

# Scan for secrets and credentials
scan_secrets() {
    log "Scanning for secrets and credentials..."
    
    if command -v trufflehog >/dev/null; then
        local trufflehog_report="${OUTPUT_DIR}/trufflehog-report.json"
        
        # Run trufflehog on repository
        trufflehog filesystem "$REPO_DIR" --json > "$trufflehog_report" 2>/dev/null || true
        
        if [[ -f "$trufflehog_report" ]]; then
            local secrets_found=$(jq length "$trufflehog_report" 2>/dev/null || echo "0")
            log "TruffleHog found $secrets_found potential secrets"
            
            # Parse trufflehog results
            jq -r '.[] | {
                file: .SourceMetadata.Data.Filesystem.File,
                line: .SourceMetadata.Data.Filesystem.Line,
                detector: .DetectorName,
                verified: .Verified,
                raw: .Raw
            }' "$trufflehog_report" 2>/dev/null || true
        fi
    fi
    
    # Additional secret scanning with regex patterns
    scan_secrets_regex
}

# Scan for secrets using regex patterns
scan_secrets_regex() {
    log "Scanning for secrets using regex patterns..."
    
    local secrets_report="${OUTPUT_DIR}/regex-secrets.json"
    local patterns=(
        "AKIA[0-9A-Z]{16}" # AWS Access Key
        "[0-9a-zA-Z/+]{40}" # Possible secret token
        "ghp_[a-zA-Z0-9]{36}" # GitHub Personal Access Token
        "xoxb-[0-9]{10}-[0-9]{10}-[a-zA-Z0-9]{24}" # Slack Bot Token
        "sk-[a-zA-Z0-9]{24,}" # Stripe API Key
        "AIza[0-9A-Za-z_-]{35}" # Google API Key
    )
    
    echo "[]" > "$secrets_report"
    
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            for pattern in "${patterns[@]}"; do
                local matches=$(grep -n "$pattern" "$file" 2>/dev/null || true)
                if [[ -n "$matches" ]]; then
                    while IFS= read -r match; do
                        local line=$(echo "$match" | cut -d: -f1)
                        local content=$(echo "$match" | cut -d: -f2-)
                        
                        jq --arg file "$file" \
                           --arg line "$line" \
                           --arg pattern "$pattern" \
                           --arg content "$content" \
                           '. + [{
                               file: $file,
                               line: ($line | tonumber),
                               pattern: $pattern,
                               content: $content,
                               severity: "high"
                           }]' "$secrets_report" > "${secrets_report}.tmp" && mv "${secrets_report}.tmp" "$secrets_report"
                    done <<< "$matches"
                fi
            done
        fi
    done < "${OUTPUT_DIR}/changed_files.txt"
    
    local regex_secrets=$(jq length "$secrets_report" 2>/dev/null || echo "0")
    log "Regex scanning found $regex_secrets potential secrets"
}

# Run static analysis with semgrep
run_static_analysis() {
    log "Running static analysis with semgrep..."
    
    if command -v semgrep >/dev/null; then
        local semgrep_report="${OUTPUT_DIR}/semgrep-report.json"
        
        # Run semgrep on changed files
        local changed_files=$(cat "${OUTPUT_DIR}/changed_files.txt" | tr '\n' ' ')
        
        if [[ -n "$changed_files" ]]; then
            semgrep --config=auto --json --output="$semgrep_report" $changed_files 2>/dev/null || true
            
            if [[ -f "$semgrep_report" ]]; then
                local findings=$(jq '.results | length' "$semgrep_report" 2>/dev/null || echo "0")
                log "Semgrep found $findings security findings"
                
                # Parse semgrep results
                jq -r '.results[] | {
                    file: .path,
                    line: .start.line,
                    end_line: .end.line,
                    rule_id: .check_id,
                    message: .message,
                    severity: .metadata.severity,
                    confidence: .metadata.confidence,
                    cwe: .metadata.cwe
                }' "$semgrep_report" 2>/dev/null || true
            fi
        fi
    fi
}

# Check dependency security
check_dependencies() {
    log "Checking dependency security..."
    
    local deps_report="${OUTPUT_DIR}/dependency-security.json"
    echo "[]" > "$deps_report"
    
    # Check Python dependencies
    if [[ -f "requirements.txt" ]]; then
        if command -v safety >/dev/null; then
            local safety_report="${OUTPUT_DIR}/safety-report.json"
            safety check --json --output "$safety_report" 2>/dev/null || true
            
            if [[ -f "$safety_report" ]]; then
                local vulns=$(jq length "$safety_report" 2>/dev/null || echo "0")
                log "Safety found $vulns Python dependency vulnerabilities"
                
                jq --arg source "requirements.txt" \
                   --arg vulns "$vulns" \
                   '. + [{
                       source: $source,
                       vulnerabilities: ($vulns | tonumber),
                       tool: "safety"
                   }]' "$deps_report" > "${deps_report}.tmp" && mv "${deps_report}.tmp" "$deps_report"
            fi
        fi
    fi
    
    # Check Node.js dependencies
    if [[ -f "package.json" ]]; then
        if command -v npm >/dev/null; then
            local npm_audit="${OUTPUT_DIR}/npm-audit.json"
            npm audit --json > "$npm_audit" 2>/dev/null || true
            
            if [[ -f "$npm_audit" ]]; then
                local vulns=$(jq '.vulnerabilities | length' "$npm_audit" 2>/dev/null || echo "0")
                log "NPM audit found $vulns Node.js dependency vulnerabilities"
                
                jq --arg source "package.json" \
                   --arg vulns "$vulns" \
                   '. + [{
                       source: $source,
                       vulnerabilities: ($vulns | tonumber),
                       tool: "npm-audit"
                   }]' "$deps_report" > "${deps_report}.tmp" && mv "${deps_report}.tmp" "$deps_report"
            fi
        fi
    fi
}

# Analyze authentication and authorization
analyze_auth() {
    log "Analyzing authentication and authorization patterns..."
    
    local auth_report="${OUTPUT_DIR}/auth-analysis.json"
    
    # Look for common auth patterns and issues
    local auth_patterns=(
        "password.*hash"
        "bcrypt"
        "jwt.*decode"
        "session.*cookie"
        "oauth.*token"
        "api.*key"
        "authentication"
        "authorization"
    )
    
    echo "[]" > "$auth_report"
    
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            for pattern in "${auth_patterns[@]}"; do
                local matches=$(grep -n -i "$pattern" "$file" 2>/dev/null || true)
                if [[ -n "$matches" ]]; then
                    while IFS= read -r match; do
                        local line=$(echo "$match" | cut -d: -f1)
                        local content=$(echo "$match" | cut -d: -f2-)
                        
                        jq --arg file "$file" \
                           --arg line "$line" \
                           --arg pattern "$pattern" \
                           --arg content "$content" \
                           '. + [{
                               file: $file,
                               line: ($line | tonumber),
                               pattern: $pattern,
                               content: $content,
                               category: "authentication"
                           }]' "$auth_report" > "${auth_report}.tmp" && mv "${auth_report}.tmp" "$auth_report"
                    done <<< "$matches"
                fi
            done
        fi
    done < "${OUTPUT_DIR}/changed_files.txt"
    
    local auth_findings=$(jq length "$auth_report" 2>/dev/null || echo "0")
    log "Found $auth_findings authentication-related code patterns"
}

# Generate security report
generate_security_report() {
    log "Generating comprehensive security report..."
    
    local report="${OUTPUT_DIR}/security-report.json"
    
    # Combine all security analysis results
    jq -n \
        --arg scan_time "$(date -Iseconds)" \
        --arg pr_number "$PR_NUMBER" \
        --arg repo_dir "$REPO_DIR" \
        '{
            scan_metadata: {
                timestamp: $scan_time,
                pr_number: $pr_number,
                repository: $repo_dir,
                scanner_version: "1.0.0"
            },
            summary: {},
            findings: []
        }' > "$report"
    
    # Add bandit results if available
    local bandit_report="${OUTPUT_DIR}/bandit-report.json"
    if [[ -f "$bandit_report" ]]; then
        jq --argjson bandit "$(cat "$bandit_report" 2>/dev/null || echo 'null')" \
           '.findings += ($bandit.results // [])' "$report" > "${report}.tmp" && mv "${report}.tmp" "$report"
    fi
    
    # Add trufflehog results if available
    local trufflehog_report="${OUTPUT_DIR}/trufflehog-report.json"
    if [[ -f "$trufflehog_report" ]]; then
        jq --argjson trufflehog "$(cat "$trufflehog_report" 2>/dev/null || echo 'null')" \
           '.findings += ($trufflehog // [])' "$report" > "${report}.tmp" && mv "${report}.tmp" "$report"
    fi
    
    # Add semgrep results if available
    local semgrep_report="${OUTPUT_DIR}/semgrep-report.json"
    if [[ -f "$semgrep_report" ]]; then
        jq --argjson semgrep "$(cat "$semgrep_report" 2>/dev/null || echo 'null')" \
           '.findings += ($semgrep.results // [])' "$report" > "${report}.tmp" && mv "${report}.tmp" "$report"
    fi
    
    # Add regex secrets results
    local regex_secrets="${OUTPUT_DIR}/regex-secrets.json"
    if [[ -f "$regex_secrets" ]]; then
        jq --argjson secrets "$(cat "$regex_secrets" 2>/dev/null || echo 'null')" \
           '.findings += ($secrets // [])' "$report" > "${report}.tmp" && mv "${report}.tmp" "$report"
    fi
    
    # Calculate summary statistics
    local total_findings=$(jq '.findings | length' "$report" 2>/dev/null || echo "0")
    local high_severity=$(jq '.findings | map(select(.severity == "high" or .issue_severity == "high")) | length' "$report" 2>/dev/null || echo "0")
    local medium_severity=$(jq '.findings | map(select(.severity == "medium" or .issue_severity == "medium")) | length' "$report" 2>/dev/null || echo "0")
    local low_severity=$(jq '.findings | map(select(.severity == "low" or .issue_severity == "low")) | length' "$report" 2>/dev/null || echo "0")
    
    jq --arg total "$total_findings" \
       --arg high "$high_severity" \
       --arg medium "$medium_severity" \
       --arg low "$low_severity" \
       '.summary = {
           total_findings: ($total | tonumber),
           high_severity: ($high | tonumber),
           medium_severity: ($medium | tonumber),
           low_severity: ($low | tonumber),
           security_score: (if ($total | tonumber) > 0 then (10 - ($high | tonumber) * 2 - ($medium | tonumber) * 0.5) else 10 end)
       }' "$report" > "${report}.tmp" && mv "${report}.tmp" "$report"
    
    log "Security report generated: $report"
    log "Summary: $total_findings findings ($high_severity high, $medium_severity medium, $low_severity low)"
}

# Post security comments to PR
post_security_comments() {
    log "Posting security comments to pull request..."
    
    if [[ -z "$GITHUB_TOKEN" || -z "$PR_NUMBER" ]]; then
        log "GitHub token or PR number not provided, skipping comment posting"
        return
    fi
    
    local report="${OUTPUT_DIR}/security-report.json"
    if [[ ! -f "$report" ]]; then
        log "Security report not found, skipping comment posting"
        return
    fi
    
    # Generate comment content
    local comment_file="${OUTPUT_DIR}/security-comment.md"
    
    cat > "$comment_file" << EOF
## 🔒 Security Analysis Report

**Scan completed:** $(date -Iseconds)

### Summary
- **Total Findings:** $(jq '.summary.total_findings' "$report")
- **High Severity:** $(jq '.summary.high_severity' "$report")
- **Medium Severity:** $(jq '.summary.medium_severity' "$report")
- **Low Severity:** $(jq '.summary.low_severity' "$report")
- **Security Score:** $(jq '.summary.security_score' "$report" | cut -d. -f1)/10

EOF

    # Add high severity findings
    local high_findings=$(jq '.findings | map(select(.severity == "high" or .issue_severity == "high")) | length' "$report")
    if [[ "$high_findings" -gt 0 ]]; then
        cat >> "$comment_file" << EOF
### 🚨 High Severity Issues

EOF
        jq -r '.findings | map(select(.severity == "high" or .issue_severity == "high"))[] | "- **\(.file // "Unknown"):\(try .line catch "N/A")** - \(.message // .issue_text // "No message")"' "$report" >> "$comment_file"
        echo "" >> "$comment_file"
    fi
    
    # Add medium severity findings
    local medium_findings=$(jq '.findings | map(select(.severity == "medium" or .issue_severity == "medium")) | length' "$report")
    if [[ "$medium_findings" -gt 0 ]]; then
        cat >> "$comment_file" << EOF
### ⚠️ Medium Severity Issues

EOF
        jq -r '.findings | map(select(.severity == "medium" or .issue_severity == "medium"))[] | "- **\(.file // "Unknown"):\(try .line catch "N/A")** - \(.message // .issue_text // "No message")"' "$report" >> "$comment_file"
        echo "" >> "$comment_file"
    fi
    
    cat >> "$comment_file" << EOF
### Recommendations

EOF

    # Add recommendations based on findings
    local total_findings=$(jq '.summary.total_findings' "$report")
    if [[ "$total_findings" -eq 0 ]]; then
        echo "✅ No security issues found! Great job keeping the code secure." >> "$comment_file"
    else
        echo "Please review and address the security issues above before merging." >> "$comment_file"
        echo "" >> "$comment_file"
        echo "🔧 **Recommended actions:**" >> "$comment_file"
        echo "- Fix all high severity issues" >> "$comment_file"
        echo "- Review and address medium severity issues" >> "$comment_file"
        echo "- Consider addressing low severity issues for better security posture" >> "$comment_file"
    fi
    
    # Post comment to GitHub
    local comment_body=$(cat "$comment_file")
    local comment_url="https://api.github.com/repos/$(basename "$REPO_DIR")/issues/$PR_NUMBER/comments"
    
    curl -s -X POST \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"body\": $(echo "$comment_body" | jq -Rs .)}" \
        "$comment_url" > /dev/null || log "Failed to post security comment"
    
    log "Security comment posted to PR #$PR_NUMBER"
}

# Main execution
main() {
    log "Starting security scanning for code review..."
    
    check_prerequisites
    setup_repository
    scan_python_security
    scan_secrets
    run_static_analysis
    check_dependencies
    analyze_auth
    generate_security_report
    post_security_comments
    
    log "Security scanning completed"
    log "Report saved to: $SECURITY_REPORT"
    log "Log file: $LOG_FILE"
}

# Execute main function
main "$@"
