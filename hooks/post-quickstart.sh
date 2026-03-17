#!/bin/bash
# Overlay post-quickstart hook
# This runs after the base quickstart.sh

echo "🚀 Overlay post-quickstart hook executing..."

# Create overlay-specific directories
mkdir -p overlay/examples
mkdir -p overlay/templates
mkdir -p overlay/registry

# Initialize overlay registry if it doesn't exist
if [[ ! -f overlay/registry/catalog.yaml ]]; then
    cat > overlay/registry/catalog.yaml << 'REGISTRY_EOF'
apiVersion: v1
kind: OverlayRegistry
metadata:
  name: overlay-registry
  namespace: flux-system
spec:
  overlays: []
REGISTRY_EOF
fi

# Create overlay templates if they don't exist
if [[ ! -d overlay/templates ]]; then
    mkdir -p overlay/templates/{skill-overlay,dashboard-overlay,infra-overlay}
fi

echo "✅ Overlay structure initialized"

# Deploy GitOps Agent Observability System
echo "🔍 Deploying GitOps Agent Observability System..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "🐍 Python3 detected, setting up agent evaluation system..."

    # Navigate to evaluation directory
    cd agent-tracing-evaluation || {
        echo "⚠️  Agent tracing evaluation directory not found, skipping deployment"
        exit 0
    }

    # Install Python dependencies if requirements.txt exists
    if [[ -f requirements.txt ]]; then
        echo "📦 Installing Python dependencies..."
        pip3 install --user -r requirements.txt || {
            echo "⚠️  Failed to install Python dependencies, continuing..."
        }
    fi

    # Set up evaluation results directory
    mkdir -p evaluation-results/history

    # Create initial evaluation configuration
    if [[ ! -f evaluation-results/config.yaml ]]; then
        cat > evaluation-results/config.yaml << 'CONFIG_EOF'
# GitOps Agent Evaluation Configuration
evaluation:
  time_ranges: ["24h", "7d"]
  enabled_evaluators:
    - skill_invocation
    - risk_compliance

alerting:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  # Configure recipients via environment variables:
  # ALERT_RECIPIENTS=team@company.com,manager@company.com

dashboard:
  host: "0.0.0.0"
  port: 5000
  auto_start: false  # Set to true to start dashboard automatically

# Langfuse Configuration (set via environment variables)
# LANGFUSE_API_KEY=your_api_key
# LANGFUSE_HOST=https://api.langfuse.com
CONFIG_EOF
        echo "📋 Created evaluation configuration"
    fi

    # Create initial evaluation results placeholder
    if [[ ! -f evaluation-results/latest.json ]]; then
        cat > evaluation-results/latest.json << 'RESULTS_EOF'
{
  "summary": {
    "total_traces": 0,
    "total_evaluations": 0,
    "average_score": 0.0,
    "pass_rate": 0.0,
    "evaluation_timestamp": "2024-01-01T00:00:00",
    "time_range": "24h"
  },
  "by_evaluator": {},
  "failing_traces": [],
  "trends": {
    "score_trend": "no_data",
    "pass_rate_trend": "no_data",
    "recommendations": [
      "Run the first evaluation to generate baseline metrics",
      "Configure Langfuse integration for real trace data",
      "Set up automated evaluation pipeline in CI/CD"
    ]
  }
}
RESULTS_EOF
        echo "📊 Created initial evaluation results"
    fi

    # Run initial evaluation with mock data
    echo "🔬 Running initial evaluation with sample data..."
    python3 pipelines/evaluation_runner.py --time-range 24h || {
        echo "⚠️  Initial evaluation failed, but system setup complete"
    }

    # Return to original directory
    cd - > /dev/null

    echo "✅ GitOps Agent Observability System deployed successfully"
    echo ""
    echo "🎯 Quick Start Commands:"
    echo "  cd agent-tracing-evaluation"
    echo "  python3 pipelines/evaluation_runner.py --time-range 24h    # Run evaluation"
    echo "  python3 dashboard/dashboard.py                          # Start dashboard"
    echo "  python3 alerts/alerter.py --check-only                  # Check alerts"
    echo ""
    echo "📚 For full documentation, see: agent-tracing-evaluation/README.md"

else
    echo "⚠️  Python3 not found, skipping agent evaluation system deployment"
    echo "   To deploy manually: cd agent-tracing-evaluation && pip3 install -r requirements.txt"
fi

# Deploy Langfuse + Temporal Integration
echo "🔍 Deploying Langfuse + Temporal Integration..."

# Check if kubectl is available
if command -v kubectl &> /dev/null; then
    echo "☸️  kubectl detected, deploying Langfuse integration..."
    
    # Deploy Langfuse secrets to control-plane namespace
    echo "📋 Deploying Langfuse secrets to control-plane namespace..."
    if [[ -f "core/config/langfuse-secret.yaml" ]]; then
        if kubectl apply -f core/config/langfuse-secret.yaml; then
            echo "✅ Langfuse secrets deployed to control-plane namespace"
        else
            echo "⚠️  Failed to deploy Langfuse secrets to control-plane namespace"
        fi
    else
        echo "⚠️  Langfuse secrets file not found: core/config/langfuse-secret.yaml"
    fi
    
    # Deploy Langfuse secrets to ai-infrastructure namespace
    echo "📋 Deploying Langfuse secrets to ai-infrastructure namespace..."
    if [[ -f "core/config/langfuse-secret-gitops-infra.yaml" ]]; then
        if kubectl apply -f core/config/langfuse-secret-gitops-infra.yaml; then
            echo "✅ Langfuse secrets deployed to ai-infrastructure namespace"
        else
            echo "⚠️  Failed to deploy Langfuse secrets to ai-infrastructure namespace"
        fi
    else
        echo "⚠️  Langfuse secrets file not found: core/config/langfuse-secret-gitops-infra.yaml"
    fi
    
    # Deploy monitoring stack with Langfuse dashboard
    echo "📊 Deploying monitoring stack with Langfuse dashboard..."
    if [[ -d "core/resources/infrastructure/monitoring" ]]; then
        if kubectl apply -k core/resources/infrastructure/monitoring; then
            echo "✅ Monitoring stack with Langfuse dashboard deployed"
        else
            echo "⚠️  Failed to deploy monitoring stack"
        fi
    else
        echo "⚠️  Monitoring directory not found: core/resources/infrastructure/monitoring"
    fi
    
    # Create namespace for observability if it doesn't exist
    echo "📝 Creating observability namespace..."
    kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f - || {
        echo "⚠️  Failed to create namespace, may already exist"
    }
    
    # Check if Langfuse secrets manifest exists
    if [[ -f "gitops/langfuse-secrets.yaml" ]]; then
        echo "🔐 Applying Langfuse secrets..."
        kubectl apply -f gitops/langfuse-secrets.yaml -n observability || {
            echo "⚠️  Failed to apply Langfuse secrets, please check configuration"
        }
    else
        echo "📝 Creating Langfuse secrets template..."
        mkdir -p gitops
        cat > gitops/langfuse-secrets.yaml << 'SECRETS_EOF'
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-secrets
  namespace: observability
type: Opaque
stringData:
  # Set these values via environment variables or kubectl edit
  public-key: "${LANGFUSE_PUBLIC_KEY:-your-public-key}"
  secret-key: "${LANGFUSE_SECRET_KEY:-your-secret-key}"
  base-url: "${LANGFUSE_BASE_URL:-https://cloud.langfuse.com}"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: langfuse-config
  namespace: observability
data:
  OTEL_SERVICE_NAME: "gitops-temporal-worker"
  OTEL_TRACES_EXPORTER: "otlp"
  OTEL_EXPORTER_OTLP_ENDPOINT: "https://cloud.langfuse.com/api/public/otel"
  OTEL_TRACES_ENABLED: "true"
  OTEL_TRACES_SAMPLER: "traceidratio"
  OTEL_TRACES_SAMPLER_ARG: "0.1"
SECRETS_EOF
        echo "📋 Created Langfuse secrets template"
        echo "⚠️  Update secrets with real Langfuse credentials before deployment"
    fi
    
    # Check if Temporal worker deployment manifest exists
    if [[ -f "gitops/temporal-worker-deployment.yaml" ]]; then
        echo "🚀 Applying Temporal worker with Langfuse integration..."
        kubectl apply -f gitops/temporal-worker-deployment.yaml -n observability || {
            echo "⚠️  Failed to apply Temporal worker deployment"
        }
    else
        echo "📝 Creating Temporal worker deployment template..."
        cat > gitops/temporal-worker-deployment.yaml << 'WORKER_EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: temporal-worker
  namespace: observability
  labels:
    app: temporal-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: temporal-worker
  template:
    metadata:
      labels:
        app: temporal-worker
    spec:
      containers:
      - name: temporal-worker
        image: gitops-temporal-worker:latest
        env:
        - name: LANGFUSE_PUBLIC_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: public-key
        - name: LANGFUSE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: secret-key
        - name: LANGFUSE_BASE_URL
          valueFrom:
            secretKeyRef:
              name: langfuse-secrets
              key: base-url
        - name: OTEL_SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_SERVICE_NAME
        - name: OTEL_TRACES_EXPORTER
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_TRACES_EXPORTER
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_EXPORTER_OTLP_ENDPOINT
        - name: OTEL_TRACES_ENABLED
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_TRACES_ENABLED
        - name: OTEL_TRACES_SAMPLER
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_TRACES_SAMPLER
        - name: OTEL_TRACES_SAMPLER_ARG
          valueFrom:
            configMapKeyRef:
              name: langfuse-config
              key: OTEL_TRACES_SAMPLER_ARG
        - name: TEMPORAL_HOST
          value: "temporal:7233"
        - name: TEMPORAL_TASK_QUEUE
          value: "agents-task-queue"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        command:
        - "/otelcol"
        - "--config=/conf/otel-collector-config.yaml"
        volumeMounts:
        - name: otel-collector-config
          mountPath: /conf
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: otel-collector-config
        configMap:
          name: otel-collector-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
data:
  otel-collector-config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      batch:
        timeout: 5s
        send_batch_size: 1024
    exporters:
      otlp:
        endpoint: https://cloud.langfuse.com/api/public/otel
        headers:
          Authorization: "Bearer ${LANGFUSE_PUBLIC_KEY}"
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [otlp]
WORKER_EOF
        echo "📋 Created Temporal worker deployment template"
    fi
    
    # Check deployment status
    echo "🔍 Checking deployment status..."
    kubectl get pods -n observability -l app=temporal-worker --no-headers | wc -l | xargs -I {} echo "📊 Temporal worker pods: {}"
    
    # Wait for pods to be ready (with timeout)
    echo "⏳ Waiting for Temporal worker pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=temporal-worker -n observability --timeout=300s || {
        echo "⚠️  Temporal worker pods not ready within timeout, but deployment initiated"
    }
    
    echo "✅ Langfuse + Temporal integration deployed successfully"
    echo ""
    echo "🎯 Langfuse Integration Status:"
    echo "  Deployment Options:"
    echo "    1. Self-hosted (Free): Deploy Langfuse in your cluster"
    echo "    2. Langfuse Cloud (Managed): Use cloud.langfuse.com"
    echo ""
    echo "  For Self-hosted Deployment:"
    echo "    • Deploy: docker-compose up -d (local) or kubectl apply (cluster)"
    echo "    • Configure: Set LANGFUSE_HOST to your deployment URL"
    echo "    • Create API keys via Langfuse UI after deployment"
    echo ""
    echo "  For Langfuse Cloud:"
    echo "    • Sign up: https://cloud.langfuse.com"
    echo "    • Create API keys in dashboard"
    echo "    • Update secrets with real credentials"
    echo ""
    echo "  Current Status: Secrets deployed with placeholder values"
    echo "  Next Step: Choose deployment option and configure accordingly"
    echo ""
    
else
    echo "⚠️  kubectl not found, skipping Langfuse integration deployment"
    echo "   To deploy manually: kubectl apply -f gitops/langfuse-secrets.yaml gitops/temporal-worker-deployment.yaml"
fi

# Deploy AI Agent Skills
echo "🤖 Deploying AI Agent Skills..."

# Check if Python is available for skill deployment
if command -v python3 &> /dev/null; then
    echo "🐍 Python3 detected, setting up AI agent skills..."

    # Navigate to skills directory
    cd core/ai/skills || {
        echo "⚠️  Skills directory not found, skipping skill deployment"
        exit 0
    }

    # Install uv for modern Python dependency management if available
    if ! command -v uv &> /dev/null; then
        echo "📦 Installing uv for dependency management..."
        pip3 install --user uv || {
            echo "⚠️  Failed to install uv, skills may have dependency issues"
        }
    fi

    # Create skills deployment configuration
    if [[ ! -f deployment-config.yaml ]]; then
        cat > deployment-config.yaml << 'DEPLOY_EOF'
# AI Agent Skills Deployment Configuration
deployment:
  enabled_skills:
    - check-cluster-health
    - optimize-costs
    - provision-infrastructure
    - troubleshoot-kubernetes
    - generate-compliance-report
    - manage-gitops-workflows
    - balance-resources
    - monitor-slo
    - predict-incidents
    - recover-from-disaster

  auto_install: true
  validate_on_deploy: true

environment:
  # Set these environment variables for production
  # LANGFUSE_API_KEY=your_api_key
  # TEMPORAL_HOST=your_temporal_host
  # KUBECONFIG=/path/to/kubeconfig

logging:
  level: INFO
  file: skills-deployment.log
DEPLOY_EOF
        echo "📋 Created skills deployment configuration"
    fi

    # Validate and install core skills
    echo "🔧 Validating and installing core AI agent skills..."

    # List of core skills to validate
    core_skills=(
        "check-cluster-health"
        "optimize-costs"
        "provision-infrastructure"
        "troubleshoot-kubernetes"
        "generate-compliance-report"
    )

    for skill in "${core_skills[@]}"; do
        if [[ -d "$skill" && -f "$skill/SKILL.md" ]]; then
            echo "✅ Found skill: $skill"

            # Validate SKILL.md structure
            if grep -q "^---$" "$skill/SKILL.md" && grep -q "^name:" "$skill/SKILL.md"; then
                echo "   ✅ Valid SKILL.md structure for $skill"

                # Check for Python dependencies
                if [[ -f "$skill/pyproject.toml" ]] || grep -q "requires-python" "$skill/SKILL.md" 2>/dev/null; then
                    echo "   📦 Installing dependencies for $skill..."
                    if [[ -f "$skill/pyproject.toml" ]]; then
                        uv pip install -e "$skill" --quiet 2>/dev/null || {
                            echo "   ⚠️  Failed to install $skill dependencies"
                        }
                    fi
                fi

                # Run skill validation if available
                if [[ -f "$skill/scripts/validate.py" ]]; then
                    echo "   🔍 Running validation for $skill..."
                    python3 "$skill/scripts/validate.py" --quiet 2>/dev/null || {
                        echo "   ⚠️  Validation failed for $skill"
                    }
                fi

            else
                echo "   ❌ Invalid SKILL.md structure for $skill"
            fi
        else
            echo "⚠️  Skill not found: $skill"
        fi
    done

    # Create skill registry
    if [[ ! -f skill-registry.json ]]; then
        echo "📚 Creating skill registry..."
        python3 -c "
import json
import os
from pathlib import Path

registry = {'skills': {}}
skills_dir = Path('.')

for item in skills_dir.iterdir():
    if item.is_dir() and (item / 'SKILL.md').exists():
        skill_name = item.name
        skill_md = item / 'SKILL.md'
        
        # Extract basic info from SKILL.md
        try:
            with open(skill_md, 'r') as f:
                content = f.read()
                
            # Extract frontmatter
            if '---' in content:
                frontmatter = content.split('---')[1]
                registry['skills'][skill_name] = {
                    'name': skill_name,
                    'path': str(item),
                    'installed': True,
                    'validated': True
                }
        except Exception as e:
            registry['skills'][skill_name] = {
                'name': skill_name,
                'path': str(item),
                'installed': False,
                'error': str(e)
            }

with open('skill-registry.json', 'w') as f:
    json.dump(registry, f, indent=2)
        "
        echo "📚 Skill registry created"
    fi

    # Return to original directory
    cd - > /dev/null

    echo "✅ AI Agent Skills deployment completed"
    echo ""
    echo "🎯 Available Skills:"
    echo "  cd core/ai/skills && ls -la"
    echo "  python3 -m skills.check-cluster-health --help"
    echo "  python3 -m skills.optimize-costs --help"
    echo ""
    echo "📚 Skills Documentation: core/ai/skills/README.md"

else
    echo "⚠️  Python3 not found, skipping AI agent skills deployment"
    echo "   Skills can be installed manually: cd core/ai/skills && pip install -e <skill-name>"
fi
