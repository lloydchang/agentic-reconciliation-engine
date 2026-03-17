#!/bin/bash

# PipeCD CI/CD Integration Script
# Integrates PipeCD into existing Jenkins/GitHub Actions pipelines

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PIPECD_URL="${PIPECD_URL:-http://pipecd.pipecd.svc.cluster.local:8080}"
PIPECD_TOKEN="${PIPECD_TOKEN:-}"
PIPECD_PROJECT="${PIPECD_PROJECT:-quickstart}"
PIPECD_API_VERSION="${PIPECD_API_VERSION:-v1beta1}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check PipeCD connectivity
check_pipecd_connectivity() {
    log_info "Checking PipeCD connectivity..."
    
    if [[ -z "$PIPECD_TOKEN" ]]; then
        log_error "PIPECD_TOKEN environment variable is not set"
        return 1
    fi
    
    # Test API connectivity
    if ! curl -s -f -H "Authorization: Bearer $PIPECD_TOKEN" "$PIPECD_URL/api/v1/projects" &> /dev/null; then
        log_error "Cannot connect to PipeCD API at $PIPECD_URL"
        return 1
    fi
    
    log_success "PipeCD connectivity verified"
    return 0
}

# Trigger deployment
trigger_deployment() {
    local app_name="$1"
    local commit_hash="${2:-}"
    local env="${3:-production}"
    
    log_info "Triggering deployment for app: $app_name, commit: $commit_hash, env: $env"
    
    local payload='{
        "head_commit": {
            "hash": "'"$commit_hash"'"
        },
        "sync_strategy": {
            "quick_sync": true
        },
        "force": false
    }'
    
    if [[ -n "$commit_hash" ]]; then
        payload=$(echo "$payload" | jq '.head_commit.hash = "'"$commit_hash"'"')
    fi
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $PIPECD_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/applications/$app_name/sync")
    
    if [[ $? -eq 0 ]] && echo "$response" | jq -e '.deployment_id' &> /dev/null; then
        local deployment_id
        deployment_id=$(echo "$response" | jq -r '.deployment_id')
        log_success "Deployment triggered successfully. ID: $deployment_id"
        echo "$deployment_id"
        return 0
    else
        log_error "Failed to trigger deployment: $response"
        return 1
    fi
}

# Wait for deployment completion
wait_for_deployment() {
    local deployment_id="$1"
    local timeout="${2:-300}"
    
    log_info "Waiting for deployment $deployment_id to complete (timeout: ${timeout}s)"
    
    local start_time
    start_time=$(date +%s)
    
    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if ((elapsed > timeout)); then
            log_error "Deployment timeout after ${timeout}s"
            return 1
        fi
        
        local response
        response=$(curl -s \
            -H "Authorization: Bearer $PIPECD_TOKEN" \
            "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/deployments/$deployment_id")
        
        if [[ $? -ne 0 ]]; then
            log_warning "Failed to get deployment status, retrying..."
            sleep 10
            continue
        fi
        
        local status
        status=$(echo "$response" | jq -r '.status // "UNKNOWN"')
        
        case "$status" in
            "DEPLOYMENT_SUCCESS")
                log_success "Deployment completed successfully"
                return 0
                ;;
            "DEPLOYMENT_FAILURE")
                log_error "Deployment failed"
                echo "$response" | jq -r '.summary // "No summary available"'
                return 1
                ;;
            "DEPLOYMENT_CANCELLED")
                log_warning "Deployment was cancelled"
                return 1
                ;;
            "DEPLOYMENT_PENDING"|"DEPLOYMENT_RUNNING")
                log_info "Deployment status: $status (elapsed: ${elapsed}s)"
                sleep 30
                ;;
            *)
                log_warning "Unknown deployment status: $status"
                sleep 10
                ;;
        esac
    done
}

# Get deployment logs
get_deployment_logs() {
    local deployment_id="$1"
    
    log_info "Fetching logs for deployment: $deployment_id"
    
    local response
    response=$(curl -s \
        -H "Authorization: Bearer $PIPECD_TOKEN" \
        "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/deployments/$deployment_id/logs")
    
    if [[ $? -eq 0 ]]; then
        echo "$response" | jq -r '.logs // [] | .[] | .message' 2>/dev/null || echo "$response"
    else
        log_error "Failed to fetch deployment logs"
        return 1
    fi
}

# Rollback deployment
rollback_deployment() {
    local app_name="$1"
    local to_commit="${2:-}"
    
    log_info "Rolling back application: $app_name"
    
    local payload='{
        "summary": "Automated rollback via CI/CD pipeline"
    }'
    
    if [[ -n "$to_commit" ]]; then
        payload=$(echo "$payload" | jq '.to_commit.hash = "'"$to_commit"'"')
    fi
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $PIPECD_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/applications/$app_name/rollback")
    
    if [[ $? -eq 0 ]] && echo "$response" | jq -e '.deployment_id' &> /dev/null; then
        local deployment_id
        deployment_id=$(echo "$response" | jq -r '.deployment_id')
        log_success "Rollback triggered successfully. ID: $deployment_id"
        echo "$deployment_id"
        return 0
    else
        log_error "Failed to trigger rollback: $response"
        return 1
    fi
}

# Get application status
get_app_status() {
    local app_name="$1"
    
    log_info "Getting status for application: $app_name"
    
    local response
    response=$(curl -s \
        -H "Authorization: Bearer $PIPECD_TOKEN" \
        "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/applications/$app_name")
    
    if [[ $? -eq 0 ]]; then
        local status
        status=$(echo "$response" | jq -r '.status // "UNKNOWN"')
        local version
        version=$(echo "$response" | jq -r '.version // "N/A"')
        
        log_info "Application $app_name status: $status, version: $version"
        echo "{\"status\": \"$status\", \"version\": \"$version\"}"
        return 0
    else
        log_error "Failed to get application status"
        return 1
    fi
}

# Promote deployment between environments
promote_deployment() {
    local app_name="$1"
    local from_env="$2"
    local to_env="$3"
    
    log_info "Promoting $app_name from $from_env to $to_env"
    
    local payload='{
        "from_environment": "'"$from_env"'",
        "to_environment": "'"$to_env"'",
        "summary": "Automated promotion via CI/CD pipeline"
    }'
    
    local response
    response=$(curl -s -X POST \
        -H "Authorization: Bearer $PIPECD_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/applications/$app_name/promote")
    
    if [[ $? -eq 0 ]] && echo "$response" | jq -e '.deployment_id' &> /dev/null; then
        local deployment_id
        deployment_id=$(echo "$response" | jq -r '.deployment_id')
        log_success "Promotion triggered successfully. ID: $deployment_id"
        echo "$deployment_id"
        return 0
    else
        log_error "Failed to trigger promotion: $response"
        return 1
    fi
}

# Get AI analysis for deployment
get_ai_analysis() {
    local app_name="$1"
    local deployment_id="${2:-}"
    
    log_info "Getting AI analysis for application: $app_name"
    
    # Get deployment data
    local deployment_data
    if [[ -n "$deployment_id" ]]; then
        deployment_data=$(curl -s \
            -H "Authorization: Bearer $PIPECD_TOKEN" \
            "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/deployments/$deployment_id")
    else
        # Get latest deployment
        local deployments
        deployments=$(curl -s \
            -H "Authorization: Bearer $PIPECD_TOKEN" \
            "$PIPECD_URL/api/v1/projects/$PIPECD_PROJECT/applications/$app_name/deployments?limit=1")
        deployment_data=$(echo "$deployments" | jq -r '.deployments[0] // {}')
    fi
    
    if [[ -z "$deployment_data" || "$deployment_data" == "{}" ]]; then
        log_error "No deployment data available for analysis"
        return 1
    fi
    
    # Send to AI analysis webhook
    local analysis_payload='{
        "deployment_data": '"$deployment_data"',
        "analysis_type": "deployment"
    }'
    
    local analysis_response
    analysis_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$analysis_payload" \
        "http://k8sgpt-webhook.pipecd.svc.cluster.local:8000/analyze")
    
    if [[ $? -eq 0 ]]; then
        log_info "AI Analysis Results:"
        echo "$analysis_response" | jq '.' 2>/dev/null || echo "$analysis_response"
        return 0
    else
        log_error "Failed to get AI analysis"
        return 1
    fi
}

# Main CI/CD integration functions
ci_deploy() {
    local app_name="$1"
    local commit_hash="${2:-$GIT_COMMIT}"
    local wait_for_completion="${3:-true}"
    
    log_info "Starting CI/CD deployment for $app_name at commit $commit_hash"
    
    # Check connectivity
    check_pipecd_connectivity || return 1
    
    # Trigger deployment
    local deployment_id
    deployment_id=$(trigger_deployment "$app_name" "$commit_hash") || return 1
    
    # Wait for completion if requested
    if [[ "$wait_for_completion" == "true" ]]; then
        wait_for_deployment "$deployment_id" || {
            log_error "Deployment failed. Fetching logs..."
            get_deployment_logs "$deployment_id"
            return 1
        }
    fi
    
    # Get AI analysis
    get_ai_analysis "$app_name" "$deployment_id" || log_warning "AI analysis failed, but deployment succeeded"
    
    log_success "CI/CD deployment completed successfully"
    return 0
}

ci_rollback() {
    local app_name="$1"
    local to_commit="${2:-}"
    
    log_info "Starting CI/CD rollback for $app_name"
    
    check_pipecd_connectivity || return 1
    
    local deployment_id
    deployment_id=$(rollback_deployment "$app_name" "$to_commit") || return 1
    
    wait_for_deployment "$deployment_id" || {
        log_error "Rollback failed. Fetching logs..."
        get_deployment_logs "$deployment_id"
        return 1
    }
    
    log_success "CI/CD rollback completed successfully"
    return 0
}

ci_promote() {
    local app_name="$1"
    local from_env="$2"
    local to_env="$3"
    
    log_info "Starting CI/CD promotion for $app_name from $from_env to $to_env"
    
    check_pipecd_connectivity || return 1
    
    local deployment_id
    deployment_id=$(promote_deployment "$app_name" "$from_env" "$to_env") || return 1
    
    wait_for_deployment "$deployment_id" || {
        log_error "Promotion failed. Fetching logs..."
        get_deployment_logs "$deployment_id"
        return 1
    }
    
    log_success "CI/CD promotion completed successfully"
    return 0
}

# Jenkins pipeline integration
jenkins_pipeline_example() {
    cat << 'EOF'
pipeline {
    agent any
    
    environment {
        PIPECD_TOKEN = credentials('pipecd-token')
        PIPECD_URL = 'http://pipecd.pipecd.svc.cluster.local:8080'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t my-app:${BUILD_NUMBER} .'
                sh 'docker push my-app:${BUILD_NUMBER}'
            }
        }
        
        stage('Deploy to Staging') {
            steps {
                sh '''
                export PATH=$PATH:/path/to/pipecd/scripts
                ci_deploy my-app-staging ${GIT_COMMIT}
                '''
            }
        }
        
        stage('AI Analysis') {
            steps {
                sh '''
                export PATH=$PATH:/path/to/pipecd/scripts
                get_ai_analysis my-app-staging
                '''
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    input message: 'Deploy to production?'
                }
                sh '''
                export PATH=$PATH:/path/to/pipecd/scripts
                ci_promote my-app staging production
                '''
            }
        }
        
        stage('Rollback') {
            when {
                expression { currentBuild.result == 'FAILURE' }
            }
            steps {
                sh '''
                export PATH=$PATH:/path/to/pipecd/scripts
                ci_rollback my-app
                '''
            }
        }
    }
    
    post {
        always {
            sh '''
            export PATH=$PATH:/path/to/pipecd/scripts
            get_deployment_logs $(cat /tmp/last_deployment_id 2>/dev/null || echo "")
            ''' || true
        }
    }
}
EOF
}

# GitHub Actions integration
github_actions_example() {
    cat << 'EOF'
name: Deploy with PipeCD
on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    env:
      PIPECD_TOKEN: ${{ secrets.PIPECD_TOKEN }}
      PIPECD_URL: ${{ secrets.PIPECD_URL }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup PipeCD CLI
        run: |
          curl -L https://github.com/pipe-cd/pipecd/releases/latest/download/pipecd_linux_amd64.tar.gz | tar xz
          sudo mv pipecd /usr/local/bin/
      
      - name: Build and Push
        run: |
          docker build -t my-app:${{ github.sha }} .
          docker push my-app:${{ github.sha }}
      
      - name: Deploy to Staging
        if: github.ref == 'refs/heads/staging'
        run: |
          chmod +x core/ai/skills/manage-pipecd/scripts/ci-integration.sh
          ./core/ai/skills/manage-pipecd/scripts/ci-integration.sh deploy my-app-staging ${{ github.sha }}
      
      - name: AI Analysis
        run: |
          ./core/ai/skills/manage-pipecd/scripts/ci-integration.sh analyze my-app-staging
      
      - name: Deploy to Production
        if: github.ref == 'refs/heads/main'
        environment: production
        run: |
          ./core/ai/skills/manage-pipecd/scripts/ci-integration.sh promote my-app staging production
      
      - name: Rollback on Failure
        if: failure()
        run: |
          ./core/ai/skills/manage-pipecd/scripts/ci-integration.sh rollback my-app
EOF
}

# Main execution
main() {
    case "${1:-}" in
        "deploy")
            shift
            ci_deploy "$@" || exit 1
            ;;
        "rollback")
            shift
            ci_rollback "$@" || exit 1
            ;;
        "promote")
            shift
            ci_promote "$@" || exit 1
            ;;
        "analyze")
            shift
            get_ai_analysis "$@" || exit 1
            ;;
        "status")
            shift
            get_app_status "$@" || exit 1
            ;;
        "jenkins-example")
            jenkins_pipeline_example
            ;;
        "github-example")
            github_actions_example
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 <command> [options]"
            echo
            echo "PipeCD CI/CD Integration Script"
            echo
            echo "Commands:"
            echo "  deploy <app-name> [commit-hash] [wait=true]  - Deploy application"
            echo "  rollback <app-name> [to-commit]              - Rollback application"
            echo "  promote <app-name> <from-env> <to-env>       - Promote between environments"
            echo "  analyze <app-name> [deployment-id]           - Get AI analysis"
            echo "  status <app-name>                            - Get application status"
            echo "  jenkins-example                              - Show Jenkins pipeline example"
            echo "  github-example                               - Show GitHub Actions example"
            echo "  help                                         - Show this help"
            echo
            echo "Environment variables:"
            echo "  PIPECD_URL         - PipeCD API URL (default: http://pipecd.pipecd.svc.cluster.local:8080)"
            echo "  PIPECD_TOKEN       - PipeCD API token (required)"
            echo "  PIPECD_PROJECT     - PipeCD project name (default: quickstart)"
            echo "  PIPECD_API_VERSION - API version (default: v1beta1)"
            echo
            echo "Examples:"
            echo "  $0 deploy my-app abc123"
            echo "  $0 rollback my-app"
            echo "  $0 promote my-app staging production"
            echo "  $0 analyze my-app"
            exit 0
            ;;
        *)
            log_error "Unknown command: ${1:-}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
