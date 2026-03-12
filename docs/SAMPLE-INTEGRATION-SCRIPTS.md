# Sample Integration Scripts

This directory contains sample scripts demonstrating how to integrate with the Continuous Reconciliation Engine (CRE).

## Directory Structure

```
scripts/
├── integration-examples/
│   ├── python-api-client/
│   ├── go-webhook-handler/
│   ├── terraform-wrapper/
│   ├── jenkins-pipeline/
│   └── kubernetes-job/
├── proprietary-extensions/
│   ├── multi-tenant-api/
│   ├── billing-integration/
│   └── compliance-monitor/
└── deployment-examples/
    ├── saas-infrastructure-platform/       # Commercial SaaS offering with billing/subscriptions
    ├── enterprise-infrastructure-console/  # Internal enterprise management tool
    └── customer-infrastructure-portal/     # Customer-facing infrastructure UI
```

## Python API Client Example

### infrastructure_client.py
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
                    sh 'kubectl kustomize control-plane/ | kubeval --strict'
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
   cd scripts/integration-examples/python-api-client
   pip install -r requirements.txt
   python infrastructure_client.py
   ```

3. **Run Go webhook handler**
   ```bash
   cd scripts/integration-examples/go-webhook-handler
   go mod tidy
   go run webhook_handler.go
   ```

4. **Test Terraform wrapper**
   ```bash
   cd scripts/integration-examples/terraform-wrapper
   terraform init
   terraform plan -var="cre_git_repo=https://github.com/your-org/repo"
   ```

These examples demonstrate safe, AGPL-compliant integration patterns that maintain clear separation between the CRE core and your proprietary business logic.
