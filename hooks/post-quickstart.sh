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
