# Agent Sandbox: Secure Isolation for AI Agents on Kubernetes and GKE

## Overview

Agent Sandbox is a Kubernetes extension designed to provide secure, isolated runtime environments for AI agents and other workloads that execute untrusted or specialized code. Introduced by Google at KubeCon NA 2025, it addresses the security challenges of running non-deterministic AI agents that can generate and execute code, use terminals, or interact with browsers without risking the host cluster or other workloads.

Built on gVisor for strong process, storage, and network isolation, Agent Sandbox is an open-source project under Kubernetes SIG Apps, enabling the creation of ephemeral, stateful, singleton workloads with VM-like characteristics on Kubernetes.

## Key Features

- **Strong Isolation**: Uses gVisor or Kata Containers to provide kernel-level isolation, preventing untrusted code from affecting the host or other pods.
- **Stable Identity**: Each sandbox maintains a consistent hostname and network identity across restarts.
- **Persistent Storage**: Supports PersistentVolumeClaims for state retention across pod lifecycles.
- **Lifecycle Management**: Includes hibernation (pausing) and resumption capabilities.
- **Rapid Provisioning**: Integrates with warm pools and snapshots for sub-second startup times.
- **Kubernetes-Native**: Implemented as CRDs (Custom Resource Definitions) for declarative management.

## Architecture

Agent Sandbox consists of core components and extensions:

### Core Components
- **Sandbox CRD**: Defines a single, stateful pod with stable identity and persistent storage.
- **Controller**: Manages the lifecycle of sandbox pods, ensuring they match the specified templates.

### Extensions
- **SandboxTemplate**: Reusable templates for creating similar sandboxes.
- **SandboxClaim**: Higher-level abstraction for requesting sandboxes from templates.
- **SandboxWarmPool**: Maintains a pool of pre-warmed pods for instant allocation.

The architecture follows the standard Kubernetes controller pattern, watching for CRD events and managing underlying pods accordingly.

## GKE Integration

Google Kubernetes Engine provides enhanced support for Agent Sandbox:

### Autopilot and Standard Clusters
- **Autopilot**: gVisor enabled by default; Agent Sandbox deploys without special node pool configuration.
- **Standard**: Requires creating node pools with `--sandbox type=gvisor` flag.

### Performance Optimizations
- **Pod Snapshots**: GKE-exclusive feature allowing checkpoint/restore of pod state, reducing startup from minutes to seconds.
- **Managed gVisor**: Optimized container runtime for horizontal scaling of sandboxes.

### Python SDK
A high-level Python library simplifies sandbox lifecycle management:

```python
from agentic_sandbox import Sandbox

with Sandbox(template_name="python3-template", namespace="ai-agents") as sandbox:
    result = sandbox.run("print('Hello from inside the sandbox!')")
```

## Use Cases

- **AI Agent Runtimes**: Isolated environments for executing LLM-generated code.
- **Development Environments**: Persistent, network-accessible cloud workspaces.
- **Research Tools**: Single-container sessions for notebooks and interactive tools.
- **Multi-Tenant Scenarios**: Secure execution of untrusted code in shared clusters.

## Installation and Setup

### Prerequisites
- Kubernetes cluster with gVisor support (enabled by default on GKE Autopilot)
- kubectl configured to access the cluster

### Installation
```bash
export VERSION="v0.1.0"
kubectl apply -f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/manifest.yaml
kubectl apply -f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/${VERSION}/extensions.yaml
```

### Basic Usage
Create a sandbox using the CRD:

```yaml
apiVersion: agents.x-k8s.io/v1alpha1
kind: Sandbox
metadata:
  name: my-sandbox
spec:
  podTemplate:
    spec:
      containers:
      - name: my-container
        image: python:3.10-slim
        command: ["python3", "-c"]
        args: ["print('Hello from sandbox!')"]
```

## Security Considerations

- Default deny network policies recommended
- Minimal IAM permissions via GKE Workload Identity
- gVisor provides additional process and network isolation
- Suitable for running untrusted code without cluster compromise

## Performance and Scaling

- Warm pools enable sub-second sandbox allocation
- Pod snapshots reduce cold start latency by up to 90%
- Horizontal scaling supported on GKE with managed gVisor
- Efficient resource utilization through hibernation and snapshot-based resumption

## Roadmap

Current development focuses on:
- Enhanced runtime support (Kata Containers, etc.)
- Improved hibernation and resume capabilities
- Rich identity and connectivity features
- Programmable APIs for agent consumption

## Resources

- [Official Blog Post](https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke)
- [GKE Documentation - Agent Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox)
- [GKE Documentation - Pod Snapshots](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox-pod-snapshots)
- [The New Stack Deep Dive](https://thenewstack.io/google-cloud-a-deep-dive-into-gke-sandbox-for-agents/)
- [GitHub Repository](https://github.com/kubernetes-sigs/agent-sandbox)
- [CNCF Project](https://www.cncf.io/projects/agent-sandbox/)

## Contributing

Agent Sandbox is an open-source project under Kubernetes SIG Apps. Contributions are welcome via the GitHub repository. Engage with the community through Slack or the mailing list.
