# Claude Code with Local Llama Model Example

This example demonstrates using Claude Code with a local Llama-3.2-3B-Instruct-q4f16_1-MLC model deployment, providing offline AI infrastructure automation without external API dependencies.

## Architecture

```
[Local Kubernetes Cluster]
├── llama-model-service (Pod with Web-LLM)
│   └── Exposes /v1/chat/completions API
├── claude-code-cronjobs
│   ├── Drift Analysis (every 4 hours)
│   ├── Manifest Validation (daily)
│   └── Uses local model endpoint
└── validation-pipeline
    └── GitOps-driven AI validation
```

## Prerequisites

- Kubernetes cluster with GPU support (optional but recommended for performance)
- 20Gi+ storage for model weights
- 8Gi+ RAM for model inference
- kubectl access

## Quick Start

### 1. Deploy Local Model
```bash
kubectl apply -f examples/local-llama-integration/model-deployment/
```

### 2. Set Environment Variables
```bash
export ANTHROPIC_BASE_URL="http://llama-model-service.control-plane.svc.cluster.local:8080"
export ANTHROPIC_MODEL="meta-llama/Llama-3.2-3B-Instruct-q4f16_1-MLC"
export ANTHROPIC_API_KEY=""  # No key needed for local
```

### 3. Install Claude Code (if not already installed)
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### 4. Launch Claude Code
```bash
cd /your/project
claude
```

## Deployment Guide

### Model Deployment
The model runs in a Pod with Web-LLM serving the Llama model. Supports GPU acceleration via CUDA.

- **Image**: Custom container with Web-LLM and pre-downloaded model weights
- **Resources**: 8Gi RAM, 4 CPU cores, optional GPU
- **Storage**: 20Gi PVC for model weights
- **Endpoint**: `http://llama-model-service:8080/v1/chat/completions`

### AI CronJobs
Automated jobs for infrastructure monitoring using local AI:

- **Drift Analysis**: Runs every 4 hours, analyzes infrastructure state
- **Validation**: Daily manifest validation with schema and security checks
- **Persistence**: 10Gi PVC for reports, 5Gi PVC for validation data

### Validation Pipeline
Flux-driven pipeline that triggers AI validation on Git commits:

- **Source**: Watches repository for changes
- **Automation**: Deploys validation job when manifests are updated
- **Reporting**: Stores results in persistent volumes

## Security Benefits

- **Offline Operation**: No external API calls or data exfiltration
- **Local Control**: Complete isolation from cloud providers
- **Cost-Free**: No API usage costs after initial setup
- **Compliance**: Suitable for air-gapped or highly regulated environments

## Performance Considerations

- **Inference Speed**: ~10-30 tokens/second on CPU, faster with GPU
- **Context Window**: 4K tokens (limited compared to cloud models)
- **Model Size**: 3B parameters quantized for efficiency
- **Resource Usage**: High memory requirements during inference

## Scaling

For production use:
- Add horizontal pod autoscaling based on inference requests
- Implement model caching for frequently used contexts
- Consider model sharding for larger deployments
- Use persistent volumes for model warm-up

## Troubleshooting

### Model Not Loading
- Check PVC has sufficient storage (20Gi minimum)
- Verify GPU drivers if using CUDA
- Check pod logs for Web-LLM initialization errors

### Claude Code Connection Issues
- Ensure ANTHROPIC_BASE_URL points to correct service
- Verify model name matches deployed model
- Check network policies allow communication

### Performance Issues
- Monitor resource usage with kubectl top
- Consider GPU-enabled nodes for better performance
- Reduce context window in prompts to improve speed

## Integration with CRE

This example demonstrates AI integration on top of the Continuous Reconciliation Engine:

1. **CRE manages infrastructure** (Flux, ACK, ASO, KCC)
2. **Local AI monitors and validates** changes
3. **GitOps workflow** ensures all changes are versioned
4. **Offline operation** maintains security boundaries

See [docs/AI-INTEGRATION-ANALYSIS.md](docs/AI-INTEGRATION-ANALYSIS.md) for detailed integration patterns and security considerations.
