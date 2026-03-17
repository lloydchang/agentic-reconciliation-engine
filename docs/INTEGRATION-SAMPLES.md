# Integration Examples

This directory contains integration examples demonstrating how to integrate with the Continuous Reconciliation Engine (CRE).

## Directory Structure

```
core/core/automation/ci-cd/scripts/
├── integration-overlay/examples/
│   ├── python-api-client/
│   ├── go-webhook-handler/
│   ├── shell-integration/
│   ├── terraform-wrapper/
│   ├── jenkins-pipeline/
│   └── kubernetes-job/
├── proprietary-extensions/
│   ├── multi-tenant-api/
│   ├── billing-integration/
│   └── compliance-monitor/
└── deployment-overlay/examples/
    ├── saas-infrastructure-platform/       # Commercial SaaS offering with billing/subscriptions
    ├── enterprise-infrastructure-console/  # Internal enterprise management tool
    └── customer-infrastructure-portal/     # Customer-facing infrastructure UI
```

These examples demonstrate safe, AGPL-compliant integration patterns that maintain clear separation between the CRE core and your proprietary business logic.

## How Samples Are Provided

**Important**: The integration samples are **intentionally incomplete patterns** embedded as code snippets in documentation. They require user adaptation and are **NOT** complete, executable implementations.

### Why Samples Are Incomplete

- **Environment-Specific Configuration**: Require user-defined variables (project IDs, credentials, endpoints)
- **Business Logic Integration**: Users must add their own authentication, monitoring, and error handling
- **Infrastructure Customization**: Platform-specific parameters must be adapted to user environments  
- **Security Requirements**: Users must implement their own security hardening and compliance checks
- **Production Readiness**: Samples demonstrate patterns, not production-deployable code

### Sample Usage Pattern

```bash
# Sample shows the pattern - user must provide actual values
deploy_gcp_network "$tenant_id" "$GCP_PROJECT_ID"  # User provides GCP_PROJECT_ID

# Sample demonstrates structure - user implements actual logic
check_deployment_status() {
    # Sample shows approach, user implements specifics
    kubectl get pods -n "$tenant_namespace" -o jsonpath='{.status.phase}'
}
```

### Licensing Justification

Since samples are **incomplete by definition** and require significant user adaptation, they can be **Apache 2.0 licensed** without triggering AGPL derivative work requirements. Users create their own complete implementations using these patterns.

## How Users Adapt Samples into Executable Code

**Important**: Samples are **NOT fully executable** - they are **patterns requiring user adaptation** into complete, production-ready implementations.

### User Workflow for Building Proprietary Layers

#### Step 1: Copy Sample Patterns

```bash
# User copies sample pattern from documentation
cp docs/INTEGRATION-SAMPLES.md ~/my-project/
# Extract code snippets and adapt them
```

#### Step 2: Create Complete Executable Scripts

```bash
#!/usr/bin/env bash
set -euo pipefail

# User's complete implementation (Apache 2.0 licensed)
# Adapted from CRE integration samples

# Add user's environment configuration
readonly GCP_PROJECT_ID="my-production-project"
readonly TENANT_PREFIX="prod"
readonly LOG_LEVEL="INFO"

# Add user's authentication/authorization
authenticate_user() {
    local user_token="$1"
    # User's proprietary auth logic
    curl -s "https://my-auth-service.com/validate?token=$user_token"
}

# Add user's monitoring and alerting
send_alert() {
    local message="$1"
    # User's proprietary alerting
    curl -X POST "https://my-alerts.com/webhook" \
         -d "{\"message\": \"$message\", \"severity\": \"info\"}"
}

# Adapted from CRE sample - now complete and executable
deploy_gcp_infrastructure() {
    local tenant_id="$1"
    local user_token="$2"
    
    # User's auth check
    if ! authenticate_user "$user_token"; then
        echo "ERROR: Authentication failed"
        send_alert "Unauthorized infrastructure deployment attempt by tenant $tenant_id"
        exit 1
    fi
    
    log "Starting GCP deployment for tenant $tenant_id"
    send_alert "Starting infrastructure deployment for $tenant_id"
    
    # Adapted sample pattern with user's specific configuration
    deploy_gcp_network "$tenant_id" "$GCP_PROJECT_ID"
    deploy_gcp_gke "$tenant_id" "$GCP_PROJECT_ID"
    
    # User's monitoring and validation
    monitor_deployment "$tenant_id"
    
    log "GCP deployment completed for tenant $tenant_id"
    send_alert "Infrastructure deployment completed for $tenant_id"
}

# User's complete monitoring implementation
monitor_deployment() {
    local tenant_id="$1"
    local max_attempts=30
    local attempt=1
    
    while (( attempt <= max_attempts )); do
        if kubectl get containercluster "${tenant_id}-gke" -n flux-system >/dev/null 2>&1; then
            log "GKE cluster ${tenant_id}-gke is ready"
            send_alert "GKE cluster ready for tenant $tenant_id"
            return 0
        fi
        
        log "Waiting for GKE cluster... (attempt $attempt/$max_attempts)"
        sleep 30
        ((attempt++))
    done
    
    log "ERROR: GKE deployment timed out for tenant $tenant_id"
    send_alert "CRITICAL: GKE deployment failed for tenant $tenant_id"
    return 1
}

# Main execution with user's CLI interface
main() {
    local tenant_id="$1"
    local user_token="${2:-$USER_TOKEN}"
    
    log "Starting proprietary infrastructure deployment service"
    
    if [[ -z "$tenant_id" ]]; then
        echo "Usage: $0 <tenant-id> [user-token]"
        exit 1
    fi
    
    deploy_gcp_infrastructure "$tenant_id" "$user_token"
}

main "$@"
```

#### Step 3: Test in Tight Feedback Loops

```bash
# User's development workflow
chmod +x deploy-gcp.sh

# Test with development environment
./deploy-gcp.sh "test-tenant-123"

# Monitor CRE status in real-time
kubectl get containerclusters -n flux-system -w

# Validate deployment
kubectl get pods -n tenant-test-tenant-123

# Iterate quickly with tight feedback
# Make changes, re-deploy, validate - all within minutes
```

#### Step 4: Build Proprietary Layers

```python
# User's proprietary SaaS API built on CRE samples
# Complete implementation using adapted patterns

from flask import Flask, request, jsonify
from cre_client import CREInfrastructureClient  # Adapted from sample

app = Flask(__name__)

class ProprietaryInfrastructureAPI:
    def __init__(self):
        self.cre_client = CREInfrastructureClient()
        self.billing_service = ProprietaryBillingService()
        self.audit_logger = ProprietaryAuditLogger()
    
    def deploy_tenant_infrastructure(self, tenant_id, user_id, config):
        # User's business logic
        self.audit_logger.log(user_id, f"Deploying infrastructure for tenant {tenant_id}")
        
        # Check billing/quota
        if not self.billing_service.check_quota(tenant_id, config):
            raise Exception("Billing quota exceeded")
        
        # Use adapted CRE sample patterns
        deployment_id = self.cre_client.deploy_infrastructure(tenant_id, config)
        
        # User's post-deployment processing
        self.billing_service.charge_for_deployment(tenant_id, config)
        
        return deployment_id

# REST API for proprietary SaaS offering
@app.route('/api/v1/core/resources/deploy', methods=['POST'])
def deploy_infrastructure():
    data = request.get_json()
    
    # User's proprietary validation
    tenant_id = data.get('tenant_id')
    user_id = get_current_user()  # User's auth
    
    # Use adapted CRE patterns
    api = ProprietaryInfrastructureAPI()
    deployment_id = api.deploy_tenant_infrastructure(tenant_id, user_id, data['config'])
    
    return jsonify({'deployment_id': deployment_id, 'status': 'deploying'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Key Differences: Samples vs. User's Executable Code

| Aspect | CRE Samples (Apache 2.0) | User's Code (Proprietary) |
|--------|-------------------------|---------------------------|
| **Completeness** | Incomplete patterns | Complete, executable implementations |
| **Configuration** | Placeholder variables | Real environment values |
| **Business Logic** | Missing | User's proprietary logic |
| **Authentication** | Not implemented | User's auth systems |
| **Monitoring** | Basic logging | Full observability stack |
| **Error Handling** | Basic patterns | Comprehensive recovery |
| **Testing** | Not executable | Tested in tight feedback loops |
| **Licensing** | Apache 2.0 (permissive) | User's license choice |

### Tight Feedback Loop Development

Users develop proprietary layers using **rapid iteration cycles**:

1. **Copy Sample Pattern** → Adapt to user's environment
2. **Add Business Logic** → Authentication, billing, monitoring
3. **Test Integration** → Deploy to CRE and validate
4. **Iterate Quickly** → Make changes, redeploy, retest (minutes)
5. **Scale Up** → Move from development to production environments

This enables building sophisticated proprietary infrastructure platforms while leveraging the CRE's continuous reconciliation capabilities.

**Important**: All integration examples in this documentation are provided under the **Apache License 2.0** (permissive open-source license). This allows you to:

- Use the code commercially
- Modify and distribute
- Use privately without restrictions
- Include in proprietary software
- Patent protection for contributors

The examples are **NOT** licensed under AGPL-3.0 because they demonstrate integration patterns, not modifications of the CRE core. You can adapt these examples into your proprietary applications while maintaining AGPL compliance.

## Multi-Cloud Integration Samples

The following samples demonstrate how to integrate with the CRE across all supported platforms. Each sample shows safe, AGPL-compliant integration patterns using network communication only.

### AWS Integration Sample

```bash
#!/usr/bin/env bash
set -euo pipefail

# AWS Infrastructure Deployment via CRE
# Uses network communication (kubectl/git) - AGPL compliant

deploy_aws_vpc() {
    local tenant_id="$1"
    local region="${2:-us-east-1}"
    local cidr="${3:-10.0.0.0/16}"
    
    log "Deploying VPC for tenant ${tenant_id} in ${region}"
    
    # Generate AWS-specific VPC manifest
    local manifest
    manifest=$(cat << EOF
apiVersion: ec2.aws.crossplane.io/v1beta1
kind: VPC
metadata:
  name: "${tenant_id}-vpc"
  namespace: flux-system
  labels:
    tenant: "${tenant_id}"
    cloud: aws
spec:
  forProvider:
    region: "${region}"
    cidrBlock: "${cidr}"
    enableDnsHostnames: true
    enableDnsSupport: true
    tags:
    - key: Name
      value: "${tenant_id}-vpc"
    - key: Environment
      value: tenant-${tenant_id}
EOF
)
    
    # Safe: Use GitOps to communicate with CRE (network protocol)
    echo "$manifest" > "tenants/${tenant_id}/aws-vpc.yaml"
    git add "tenants/${tenant_id}/aws-vpc.yaml"
    git commit -m "Deploy AWS VPC for tenant ${tenant_id}"
    git push origin main
}

deploy_aws_eks() {
    local tenant_id="$1"
    local cluster_name="${2:-${tenant_id}-cluster}"
    local vpc_id="${3:-${tenant_id}-vpc}"
    
    log "Deploying EKS cluster ${cluster_name}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: eks.aws.crossplane.io/v1beta1
kind: Cluster
metadata:
  name: "${cluster_name}"
  namespace: flux-system
spec:
  forProvider:
    region: us-east-1
    roleARN: "arn:aws:iam::123456789012:role/eks-service-role"
    vpcConfig:
    - subnetIdsRef:
        name: "${vpc_id}"
      securityGroupIds:
      - sg-default
    version: "1.28"
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/aws-eks.yaml"
    git add "tenants/${tenant_id}/aws-eks.yaml"
    git commit -m "Deploy AWS EKS cluster for tenant ${tenant_id}"
    git push origin main
}
```

### Azure Integration Sample

```bash
# Licensed under Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env bash
set -euo pipefail

# Azure Infrastructure Deployment via CRE
# Uses network communication (kubectl/git) - AGPL compliant

deploy_azure_resource_group() {
    local tenant_id="$1"
    local location="${2:-eastus}"
    
    log "Deploying Azure Resource Group for tenant ${tenant_id}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: azure.crossplane.io/v1alpha1
kind: ResourceGroup
metadata:
  name: "${tenant_id}-rg"
  namespace: flux-system
spec:
  forProvider:
    location: "${location}"
    tags:
      environment: "tenant-${tenant_id}"
      managed-by: cre
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/azure-rg.yaml"
    git add "tenants/${tenant_id}/azure-rg.yaml"
    git commit -m "Deploy Azure Resource Group for tenant ${tenant_id}"
    git push origin main
}

deploy_azure_aks() {
    local tenant_id="$1"
    local cluster_name="${2:-${tenant_id}-aks}"
    local rg_name="${3:-${tenant_id}-rg}"
    
    log "Deploying AKS cluster ${cluster_name}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: containerservice.azure.crossplane.io/v1beta1
kind: KubernetesCluster
metadata:
  name: "${cluster_name}"
  namespace: flux-system
spec:
  forProvider:
    resourceGroupNameRef:
      name: "${rg_name}"
    location: eastus
    kubernetesVersion: "1.28.0"
    dnsPrefix: "${tenant_id}"
    agentPools:
    - name: default
      count: 3
      vmSize: Standard_DS2_v2
      osType: Linux
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/azure-aks.yaml"
    git add "tenants/${tenant_id}/azure-aks.yaml"
    git commit -m "Deploy Azure AKS cluster for tenant ${tenant_id}"
    git push origin main
}
```

### GCP Integration Sample

```bash
# Licensed under Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env bash
set -euo pipefail

# GCP Infrastructure Deployment via CRE
# Uses network communication (kubectl/git) - AGPL compliant

deploy_gcp_network() {
    local tenant_id="$1"
    local project_id="$2"
    
    log "Deploying GCP VPC network for tenant ${tenant_id}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: compute.cnrm.cloud.google.com/v1beta1
kind: ComputeNetwork
metadata:
  name: "${tenant_id}-network"
  namespace: flux-system
  annotations:
    cnrm.cloud.google.com/project-id: "${project_id}"
spec:
  description: "VPC network for tenant ${tenant_id}"
  autoCreateSubnetworks: false
  routingConfig:
    routingMode: REGIONAL
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/gcp-network.yaml"
    git add "tenants/${tenant_id}/gcp-network.yaml"
    git commit -m "Deploy GCP VPC network for tenant ${tenant_id}"
    git push origin main
}

deploy_gcp_gke() {
    local tenant_id="$1"
    local cluster_name="${2:-${tenant_id}-gke}"
    local project_id="$2"
    local network_name="${3:-${tenant_id}-network}"
    
    log "Deploying GKE cluster ${cluster_name}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: container.cnrm.cloud.google.com/v1beta1
kind: ContainerCluster
metadata:
  name: "${cluster_name}"
  namespace: flux-system
  annotations:
    cnrm.cloud.google.com/project-id: "${project_id}"
spec:
  location: us-central1
  initialNodeCount: 3
  networkRef:
    name: "${network_name}"
  nodeConfig:
    machineType: n1-standard-1
    diskSizeGb: 100
    oauthScopes:
    - https://www.googleapis.com/auth/cloud-platform
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/gcp-gke.yaml"
    git add "tenants/${tenant_id}/gcp-gke.yaml"
    git commit -m "Deploy GCP GKE cluster for tenant ${tenant_id}"
    git push origin main
}
```

### Local/Kubernetes Integration Sample

```bash
# Licensed under Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env bash
set -euo pipefail

# Local Kubernetes Infrastructure Deployment via CRE
# Uses network communication (kubectl/git) - AGPL compliant

deploy_local_namespace() {
    local tenant_id="$1"
    
    log "Deploying local Kubernetes namespace for tenant ${tenant_id}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: "tenant-${tenant_id}"
  labels:
    tenant: "${tenant_id}"
    environment: local
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/local-namespace.yaml"
    git add "tenants/${tenant_id}/local-namespace.yaml"
    git commit -m "Deploy local namespace for tenant ${tenant_id}"
    git push origin main
}

deploy_local_deployment() {
    local tenant_id="$1"
    local app_name="${2:-tenant-app}"
    local image="${3:-nginx:latest}"
    
    log "Deploying local Kubernetes deployment ${app_name}"
    
    local manifest
    manifest=$(cat << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: "${app_name}"
  namespace: "tenant-${tenant_id}"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: "${app_name}"
  template:
    metadata:
      labels:
        app: "${app_name}"
        tenant: "${tenant_id}"
    spec:
      containers:
      - name: app
        image: "${image}"
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
EOF
)
    
    echo "$manifest" > "tenants/${tenant_id}/local-deployment.yaml"
    git add "tenants/${tenant_id}/local-deployment.yaml"
    git commit -m "Deploy local Kubernetes app for tenant ${tenant_id}"
    git push origin main
}
```

## Usage Examples for Each Platform

### AWS Usage

```bash
# Deploy complete AWS infrastructure stack
deploy_aws_vpc "tenant-123"
deploy_aws_eks "tenant-123"

# Monitor via CRE
kubectl get vpc tenant-123-vpc -w
kubectl get cluster tenant-123-cluster -w
```

### Azure Usage  

```bash
# Deploy complete Azure infrastructure stack
deploy_azure_resource_group "tenant-456"
deploy_azure_aks "tenant-456"

# Monitor via CRE
kubectl get resourcegroup tenant-456-rg -w
kubectl get kubernetescluster tenant-456-aks -w
```

### GCP Usage

```bash
# Deploy complete GCP infrastructure stack
deploy_gcp_network "tenant-789" "my-gcp-project"
deploy_gcp_gke "tenant-789" "my-gcp-project"

# Monitor via CRE
kubectl get computenetwork tenant-789-network -w
kubectl get containercluster tenant-789-gke -w
```

### Local Usage

```bash
# Deploy local Kubernetes resources
deploy_local_namespace "tenant-local"
deploy_local_deployment "tenant-local"

# Monitor via CRE
kubectl get deployments -n tenant-tenant-local -w
kubectl get pods -n tenant-tenant-local -w
```

## Multi-Cloud Deployment Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# Multi-Cloud Infrastructure Deployment
# Demonstrates CRE's ability to manage infrastructure across all platforms

deploy_multi_cloud() {
    local tenant_id="$1"
    local cloud_provider="$2"  # aws, azure, gcp, local
    
    case "$cloud_provider" in
        aws)
            deploy_aws_vpc "$tenant_id"
            deploy_aws_eks "$tenant_id"
            ;;
        azure)
            deploy_azure_resource_group "$tenant_id"
            deploy_azure_aks "$tenant_id"
            ;;
        gcp)
            deploy_gcp_network "$tenant_id" "$GCP_PROJECT"
            deploy_gcp_gke "$tenant_id" "$GCP_PROJECT"
            ;;
        local)
            deploy_local_namespace "$tenant_id"
            deploy_local_deployment "$tenant_id"
            ;;
        *)
            echo "Unsupported cloud provider: $cloud_provider"
            exit 1
            ;;
    esac
    
    log "Successfully deployed ${cloud_provider} infrastructure for tenant ${tenant_id}"
}

# Usage: ./deploy.sh tenant-123 aws
deploy_multi_cloud "$1" "$2"
```

These samples demonstrate how the CRE provides unified infrastructure management across AWS, Azure, GCP, and local Kubernetes environments using consistent GitOps patterns and network-based communication.

```python
#!/usr/bin/env python3
"""
CRE Infrastructure Management Client
Example of building proprietary API on top of CRE
"""

import requests
import yaml
import json
from typing import Dict, Any
import os

class CREClient:
    def __init__(self, git_repo_url: str, git_token: str = None):
        self.git_repo = git_repo_url
        self.git_token = git_token or os.getenv('GIT_TOKEN')
        self.session = requests.Session()
        if self.git_token:
            self.session.headers.update({'Authorization': f'token {self.git_token}'})

    def deploy_infrastructure(self, tenant_id: str, manifest: Dict[str, Any]) -> str:
        """
        Deploy infrastructure via GitOps (triggers CRE reconciliation)
        """
        # Create tenant-specific manifest
        tenant_manifest = self._add_tenant_prefix(manifest, tenant_id)

        # Write to Git repository
        file_path = f"tenants/{tenant_id}/infrastructure.yaml"
        content = yaml.dump(tenant_manifest)

        # GitHub API integration
        self._create_or_update_file(file_path, content, f"Deploy infrastructure for {tenant_id}")

        return f"deployment-{tenant_id}-{hash(str(manifest))}"

    def get_infrastructure_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get current infrastructure status from CRE
        """
        # This would integrate with Flux APIs or kubectl
        # For demo, return mock status
        return {
            "tenant_id": tenant_id,
            "status": "reconciling",
            "resources": [
                {"name": "vpc", "status": "ready"},
                {"name": "cluster", "status": "reconciling"}
            ]
        }

    def _add_tenant_prefix(self, manifest: Dict, tenant_id: str) -> Dict:
        """Add tenant isolation prefix to all resources"""
        if isinstance(manifest, dict):
            prefixed = {}
            for key, value in manifest.items():
                prefixed[f"{tenant_id}-{key}"] = self._add_tenant_prefix(value, tenant_id)
            return prefixed
        elif isinstance(manifest, list):
            return [self._add_tenant_prefix(item, tenant_id) for item in manifest]
        else:
            return manifest

    def _create_or_update_file(self, path: str, content: str, message: str):
        """GitHub API file operations"""
        url = f"{self.git_repo}/contents/{path}"

        # Check if file exists
        response = self.session.get(url)
        sha = response.json().get('sha') if response.status_code == 200 else None

        data = {
            "message": message,
            "content": content.encode('utf-8').decode('base64'),
            "branch": "main"
        }
        if sha:
            data["sha"] = sha

        response = self.session.put(url, json=data)
        response.raise_for_status()

# Usage example
if __name__ == "__main__":
    client = CREClient("https://api.github.com/repos/your-org/infra-repo")

    # Deploy VPC for tenant
    manifest = {
        "vpc": {
            "cidr": "10.0.0.0/16",
            "region": "us-east-1"
        },
        "subnet": {
            "cidr": "10.0.1.0/24",
            "az": "us-east-1a"
        }
    }

    deployment_id = client.deploy_infrastructure("tenant-123", manifest)
    print(f"Deployment initiated: {deployment_id}")

    # Check status
    status = client.get_infrastructure_status("tenant-123")
    print(f"Status: {status}")
```

### requirements.txt

```txt
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=0.19.0
```

## Go Webhook Handler Example

### webhook_handler.go

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"

    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

// FluxWebhookPayload represents webhook from CRE/Flux
type FluxWebhookPayload struct {
    InvolvedObject struct {
        Kind string `json:"kind"`
        Name string `json:"name"`
    } `json:"involvedObject"`
    Severity string `json:"severity"`
    Message  string `json:"message"`
    Reason   string `json:"reason"`
}

// ProprietaryService represents your business logic
type ProprietaryService struct {
    // Add your database connections, etc.
}

func (s *ProprietaryService) handleCREWebhook(w http.ResponseWriter, r *http.Request) {
    var payload FluxWebhookPayload
    if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }

    // Extract tenant from resource name (assuming naming convention)
    tenantID := extractTenantFromName(payload.InvolvedObject.Name)

    // Update proprietary database
    switch payload.Reason {
    case "ReconciliationSucceeded":
        s.updateDeploymentStatus(tenantID, payload.InvolvedObject.Name, "ready")
        s.notifyUser(tenantID, "Infrastructure deployed successfully")
    case "ReconciliationFailed":
        s.updateDeploymentStatus(tenantID, payload.InvolvedObject.Name, "failed")
        s.alertOpsTeam(tenantID, payload.Message)
    }

    w.WriteHeader(http.StatusOK)
}

func (s *ProprietaryService) updateDeploymentStatus(tenantID, resourceName, status string) {
    // Update your database
    log.Printf("Updated %s status to %s for tenant %s", resourceName, status, tenantID)
}

func (s *ProprietaryService) notifyUser(tenantID, message string) {
    // Send email, Slack, etc.
    log.Printf("Notifying tenant %s: %s", tenantID, message)
}

func (s *ProprietaryService) alertOpsTeam(tenantID, errorMsg string) {
    // PagerDuty, OpsGenie, etc.
    log.Printf("Alerting ops team for tenant %s: %s", tenantID, errorMsg)
}

func extractTenantFromName(name string) string {
    // Assuming naming convention: tenant-123-resource-name
    if len(name) > 7 && name[:7] == "tenant-" {
        for i := 7; i < len(name); i++ {
            if name[i] == '-' {
                return name[7:i]
            }
        }
    }
    return "default"
}

func main() {
    service := &ProprietaryService{}

    r := chi.NewRouter()
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)

    r.Post("/webhooks/cre", service.handleCREWebhook)

    port := os.Getenv("PORT")
    if port == "" {
        port = "8080"
    }

    log.Printf("Starting webhook handler on port %s", port)
    http.ListenAndServe(":"+port, r)
}
```

### go.mod

```go
module github.com/your-org/cre-webhook-handler

go 1.19

require (
    github.com/go-chi/chi/v5 v5.0.8
)
```

## Terraform Wrapper Example

### cre_terraform_wrapper.tf

```hcl
# Example of wrapping CRE with Terraform for brownfield migration

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    git = {
      source  = "innovationnorway/git"
      version = "0.1.4"
    }
  }
}

variable "cre_git_repo" {
  description = "Git repository URL for CRE manifests"
  type        = string
}

variable "tenant_id" {
  description = "Tenant identifier for multi-tenancy"
  type        = string
}

# Traditional Terraform resources (for initial setup)
resource "aws_vpc" "hub" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "cre-hub-vpc"
  }
}

# CRE integration via Git
resource "git_commit" "infrastructure" {
  repository = var.cre_git_repo
  branch     = "main"

  files = {
    "tenants/${var.tenant_id}/vpc.yaml" = yamlencode({
      apiVersion = "ec2.aws.crossplane.io/v1beta1"
      kind       = "VPC"

      metadata = {
        name = "${var.tenant_id}-vpc"
      }

      spec = {
        forProvider = {
          region = "us-east-1"
          cidrBlock = "10.1.0.0/16"
        }
      }
    })
  }

  message = "Deploy VPC for tenant ${var.tenant_id}"
}

# Output CRE deployment status
output "cre_deployment_commit" {
  value = git_commit.infrastructure.sha
  description = "Git commit SHA that triggered CRE deployment"
}
```

## Jenkins Pipeline Example

### Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        CRE_GIT_REPO = 'https://github.com/your-org/infra-repo.git'
        CRE_BRANCH = 'main'
    }

    stages {
        stage('Setup') {
            steps {
                script {
                    // Checkout CRE repository
                    checkout([$class: 'GitSCM',
                        branches: [[name: env.CRE_BRANCH]],
                        userRemoteConfigs: [[url: env.CRE_GIT_REPO]]
                    ])
                }
            }
        }

        stage('Validate Manifests') {
            steps {
                script {
                    // Validate Kubernetes manifests
                    sh 'kubectl kustomize core/operators/ | kubeval --strict'
                }
            }
        }

        stage('Deploy to CRE') {
            steps {
                script {
                    // Generate tenant-specific manifests
                    def tenantId = env.BRANCH_NAME.replace('feature/', '').replace('/', '-')
                    def manifestPath = "tenants/${tenantId}/deployment.yaml"

                    writeYaml file: manifestPath, data: [
                        apiVersion: 'apps/v1',
                        kind: 'Deployment',
                        metadata: [
                            name: "${tenantId}-app",
                            namespace: 'default'
                        ],
                        spec: [
                            replicas: 3,
                            selector: [matchLabels: [app: tenantId]],
                            template: [
                                metadata: [labels: [app: tenantId]],
                                spec: [
                                    containers: [[
                                        name: 'app',
                                        image: env.DOCKER_IMAGE,
                                        ports: [[containerPort: 8080]]
                                    ]]
                                ]
                            ]
                        ]
                    ]

                    // Commit and push (triggers CRE)
                    sh """
                        git add ${manifestPath}
                        git commit -m "Deploy ${tenantId} application via Jenkins"
                        git push origin ${env.CRE_BRANCH}
                    """
                }
            }
        }

        stage('Monitor Deployment') {
            steps {
                script {
                    // Wait for CRE reconciliation
                    timeout(time: 10, unit: 'MINUTES') {
                        waitUntil {
                            def status = sh(script: 'kubectl get deployments -l app=${BRANCH_NAME} -o jsonpath="{.items[0].status.readyReplicas}"', returnStdout: true).trim()
                            return status == "3"
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                // Notify proprietary dashboard
                httpRequest url: 'https://your-api.com/webhooks/jenkins',
                    httpMode: 'POST',
                    contentType: 'APPLICATION_JSON',
                    requestBody: """{
                        "status": "success",
                        "tenant": "${env.BRANCH_NAME}",
                        "commit": "${env.GIT_COMMIT}"
                    }"""
            }
        }
        failure {
            // Alert on failure
            echo 'Deployment failed'
        }
    }
}
```

## Usage Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/lloydchang/gitops-infra-control-plane.git
   cd gitops-infra-control-plane
   ```

2. **Run Python example**

   ```bash
   cd core/core/automation/ci-cd/scripts/integration-overlay/examples/python-api-client
   pip install -r requirements.txt
   python infrastructure_client.py
   ```

3. **Run Go webhook handler**

   ```bash
   cd core/core/automation/ci-cd/scripts/integration-overlay/examples/go-webhook-handler
   go mod tidy
   go run webhook_handler.go
   ```

4. **Test Terraform wrapper**

   ```bash
   cd core/core/automation/ci-cd/scripts/integration-overlay/examples/terraform-wrapper
   terraform init
   terraform plan -var="cre_git_repo=https://github.com/your-org/repo"
   ```

These examples demonstrate safe, AGPL-compliant integration patterns that maintain clear separation between the CRE core and your proprietary business logic.
