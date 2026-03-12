# gitops-infra-control-plane

Continuous Reconciliation Engine for Multi-Cloud Infra

## The Core Advantage
Traditional IaC tools (Terraform, CDK, CloudFormation, Bicep, ARM) run once and exit - they cannot continuously maintain infrastructure state. We provide **24/7 continuous reconciliation** that automatically detects and repairs configuration drift, something push-based tools fundamentally cannot achieve without complex external orchestration.

| Approach | Traditional IaC | Continuous Reconciliation |
|----------|----------------|---------------------------|
| **Operation** | Run once → Exit | Monitor 24/7 → Auto-heal |
| **Drift Detection** | Manual `plan` runs | Automatic within minutes |
| **Emergency Fix** | Manual process | Git commit → Auto-deploy |
| **State Management** | State files (corruption risk) | Live cloud API (no files) |
| **Human Error** | Manual corrections needed | Automatic reverts |

* **Continuous Reconciliation**: Native Kubernetes controllers (AWS ACK, Azure ASO, GCP KCC) monitor Cloud APIs 24/7. They actively repair configuration drift without human intervention.
* **Self-Healing Infrastructure**: Unlike traditional IaC that requires manual re-runs, our approach automatically maintains desired state continuously.
* **Zero State Files**: There is no Terraform State to corrupt, lock, or lose. The live Cloud API is the only source of truth.
* **Hybrid Setup**: Industry-standard CLIs (eksctl, az, gcloud) for initial Hub cluster creation, then continuous reconciliation for all ongoing infrastructure management.

**👉 See [Continuous Reconciliation Value Proposition](./docs/CONTINUOUS-RECONCILIATION-VALUE-PROP.md) for detailed comparison and real-world scenarios.**

## Architectural Topology
We use a hub-and-spoke model where a single Hub Cluster acts as the control plane for all cloud environments:

```text
                       GIT REPOSITORY
                     (Source of Truth)
                             |
                    Flux Pulls Manifests
                             |
                             v
      +------------------------------------------+
      |                HUB CLUSTER               |
      |------------------------------------------|
      | Flux | ACK        | ASO           | KCC  |
      +------------------------------------------+
             |               |               |
   Provisions/Manages Provisions/Manages Provisions/Manages
             |               |               |
      +-------------+ +-------------+ +-------------+
      |   SPOKE 1   | |   SPOKE 2   | |   SPOKE 3   |
      |   (EKS)     | |   (AKS)     | |   (GKE)     |
      |   CLUSTER   | |   CLUSTER   | |   CLUSTER   |
      +-------------+ +-------------+ +-------------+
```

## Getting Started
To understand the technical design, architectural mandates, and step-by-step implementation phases, refer to:
[implementation_plan.md](./docs/implementation_plan.md)

## Why Flux?
We utilize Flux over Argo CD because Flux is architecturally optimized for infrastructure lifecycle management:
- Controller-Native: Flux is a set of Kubernetes controllers, not an external UI overlay.
- Dependency Chaining: Flux dependency chaining enables a true Directed Acyclic Graph (DAG) for complex infrastructure dependencies, whereas Argo CD relies on linear Sync Waves.
- Headless & Reliable: Flux is designed for cluster-to-cluster management, which is essential for our hub-and-spoke Hub vs. Spoke Clusters strategy.

## Repository Standards
- Refer to .gitignore to ensure no local secrets or state artifacts are ever committed.
- All code is subject to the GNU Affero General Public License v3.0 (AGPL-3.0) (see [LICENSE](https://github.com/lloydchang/gitops-infra-control-plane/blob/main/LICENSE) file).

## Dual Licensing for Commercial Use

This repository uses dual licensing to enable both open-source contributions and commercial usage:

- **AGPL-3.0**: Core Continuous Reconciliation Engine (CRE) - infrastructure manifests, Flux configurations, and core logic
- **Apache 2.0**: Code samples and example snippets within documentation - allows commercial use and proprietary derivatives
- **LLM Usage and Generated Content**: Large Language Models (LLMs) may be trained on or used to generate code/infrastructure based on this repository's content. Outputs derived from Apache 2.0 licensed examples (e.g., documentation snippets) can be used commercially. However, any code that replicates or extends AGPL-3.0 core logic (e.g., Flux configurations, reconciliation engine components) must remain AGPL-licensed. Always validate AI-generated manifests against Kubernetes schemas to avoid hallucinations (see `docs/AI-INTEGRATION-ANALYSIS.md` for safe integration patterns).

## 🚀 Multi-Language Consensus-Based Agent Orchestration

The GitOps Infrastructure Control Plane now supports **comprehensive multi-language consensus-based agent orchestration**, enabling autonomous, self-organizing agent swarms with tight feedback loops across all major programming paradigms.

### 🎯 **Supported Languages & Runtimes**

| Language | Performance | Feedback Loop Speed | Best Use Case |
|-----------|------------|---------------------|-------------|
| **Rust** | **Highest** | **10-15 seconds** | Performance-critical consensus |
| **Go** | High | 30 seconds | Kubernetes integration |
| **Python** | Medium | 30 seconds | AI/ML analytics |
| **TypeScript** | Medium | 30 seconds | Real-time coordination |
| **C#/.NET** | High | 30 seconds | Enterprise integration |
| **Java** | Medium | 30 seconds | Large-scale systems |

### 🔄 **Consensus Protocol: Raft-Based Coordination**

- **Raft over Paxos**: Chosen for simplicity, performance, and understandability
- **Leader-Based Coordination**: Natural fit for agent swarm architecture
- **Tight Feedback Loops**: 10-30 second optimization cycles
- **Fault Tolerance**: Automatic leader election and log replication
- **Production Proven**: Used in etcd, Consul, and enterprise systems

### 🛠 **Integration Options**

#### **Temporal-Based Orchestration**
- **Multi-Language SDKs**: Go, Python, TypeScript, C#, Java support
- **Durable Workflows**: Persistent consensus state across failures
- **Go-Based Performance**: Native Kubernetes integration
- **Enterprise Features**: Advanced error handling and monitoring

#### **Kubernetes-Native Workflows**
- **Resolute**: Pure Kubernetes-native workflow management
- **Zero External Dependencies**: Runs entirely within Kubernetes
- **GitOps-Friendly**: Declarative workflow definitions in Git
- **Resource Efficiency**: Shared cluster resources

#### **Hybrid Architecture**
- **Performance-Critical**: Rust components for ultra-fast loops
- **AI/ML Processing**: Python for machine learning and analytics
- **Enterprise Integration**: C#/Java for large-scale systems
- **Real-Time Coordination**: TypeScript for event-driven monitoring

### 📊 **Key Capabilities**

#### **Autonomous Agent Swarms**
- **Self-Organization**: Emergent intelligence from local interactions
- **Distributed Consensus**: Raft-based coordination without single points of failure
- **Local Optimization**: Agents make decisions based on local state
- **Global Coherence**: Lightweight consensus protocols maintain system-wide optimization

#### **Ultra-Tight Feedback Loops**
- **Micro-Loops**: 10-15 seconds (Rust) for performance-critical decisions
- **Standard Loops**: 30 seconds for most agent coordination
- **Hierarchical Consensus**: Multi-level coordination (local → regional → global)
- **Byzantine Tolerance**: Optional PBFT for high-security environments

#### **Multi-Cloud Coordination**
- **Cross-Cloud Consensus**: Global optimization across providers
- **Dynamic Membership**: Add/remove agents without system disruption
- **Load Balancing**: Distributed decision making across all agents
- **Fault Recovery**: Automatic failover and state recovery

### �️ Modular Architecture & DAG

This control plane is built with **explicit dependency management** using Flux's `dependsOn` feature, creating a true Directed Acyclic Graph (DAG) for infrastructure deployment.

### Core DAG Structure
```
Level 0: flux-system (GitRepository)
Level 1: infrastructure-controllers, monitoring-alerts
Level 2: aws/azure/gcp-network
Level 3: aws/azure/gcp-clusters  
Level 4: aws/azure/gcp-workloads
Level 5: Enhanced services (AI, auth, certificates)
```

### 📋 Quick Start

#### 1. **Open Source Deployment**
```bash
./scripts/variant-swapper.sh opensource
```

#### 2. **Enterprise Deployment**
```bash
./scripts/variant-swapper.sh enterprise
```

#### 3. **Language Ecosystem Variants**
```bash
# Python/ML Stack
./scripts/variant-swapper.sh languages python

# Go/Cloud Native Stack
./scripts/variant-swapper.sh languages go

# Rust/WasmCloud Stack
./scripts/variant-swapper.sh languages rust

# TypeScript/Node.js Stack
./scripts/variant-swapper.sh languages typescript

# C#/.NET Stack
./scripts/variant-swapper.sh languages csharp

# Java/JVM Stack
./scripts/variant-swapper.sh languages java
```

### 🔧 DAG Visualization
```bash
# Generate dependency graph
python3 scripts/dag-visualizer.py . --format mermaid --output docs/diagrams/current-dag.md

# Check for circular dependencies
python3 scripts/dag-visualizer.py . --format report
```

### 📚 Documentation
- **[DAG Architecture](docs/DAG-ARCHITECTURE.md)** - Complete dependency management guide
- **[Variant Management](variants/)** - Deployment variant configurations
- **[Examples](examples/)** - Complete deployment scenarios
- **[AI Integration Analysis](docs/AI-INTEGRATION-ANALYSIS.md)**: Comprehensive multi-language runtime support
- **[Agent Architecture](docs/ARCHITECTURE.md)**: Consensus-based orchestration design
- **[Agent Skills](docs/AGENT-SKILLS-NEXT-LEVEL.md)**: Self-organizing swarm patterns

---

## Open-source Software
https://github.com/lloydchang/gitops-infra-control-plane

<img width="1024" height="1024" alt="Image" src="https://github.com/user-attachments/assets/e6b4bec7-3855-4532-a06c-daadffed4911" />
