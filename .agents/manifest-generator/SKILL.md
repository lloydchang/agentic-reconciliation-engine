# Manifest Generator Skill

## Name
manifest-generator

## Purpose
Generate and validate Kubernetes manifests, Helm charts, and configuration files with policy compliance and security checks.

## When to Use
- When creating new Kubernetes resources and deployments
- When generating Helm charts for applications
- When validating manifests against policies and best practices
- When converting configurations between formats
- When generating RBAC and security policies

## Inputs
- Resource specifications and requirements
- Environment and cluster context
- Policy and compliance constraints
- Security and access control requirements
- Helm chart templates and values

## Process
1. Analyze requirements and generate manifest templates
2. Apply security policies and RBAC configurations
3. Validate against Kubernetes API schema and policies
4. Generate Helm charts and deployment configurations
5. Test manifests in dry-run mode
6. Provide validation reports and deployment guidance

## Outputs
- Generated Kubernetes manifests and Helm charts
- Policy validation results and compliance reports
- Security configurations and RBAC policies
- Deployment scripts and rollback procedures
- Configuration validation and testing results

## Environment
- Kubernetes clusters with API access
- Helm installation and repositories
- Policy engines (OPA Gatekeeper, Kyverno)
- Configuration management tools

## Dependencies
- kubectl and Kubernetes API access
- Helm binary and chart repositories
- Policy validation tools and engines
- Schema validation and testing frameworks

## Scripts
- scripts/generate_manifest.py: Python script for manifest generation
- scripts/validate_policy.py: Policy validation script
- scripts/helm_generator.py: Helm chart generation script

## Trigger Keywords
manifest, Helm, K8s config, policy validation

## Human Gate Requirements
High-risk manifests

## API Patterns

### JavaScript
```javascript
// Generate manifest
const manifest = await generate_manifest({
  resourceType: "deployment|service|configmap",
  namespace: "production",
  securityPolicy: "restricted",
  priority: "normal"
});

// Get generation results
const results = await get_manifest_results({
  workflowId: manifest.workflowId
});
```

### Rust
```rust
// Rust-based manifest generation
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ManifestRequest {
    pub resource_type: ResourceType,
    pub namespace: String,
    pub security_policy: SecurityPolicy,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum ResourceType {
    Deployment,
    Service,
    ConfigMap,
}

pub async fn generate_manifest(request: ManifestRequest) -> Result<ManifestWorkflow, ManifestError> {
    // Secure manifest generation with validation
    let workflow = ManifestWorkflow::new(request).await?;
    
    // Apply security policies and validate
    workflow.generate_secure().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "resourceType": "string (required) - type of resource to generate: deployment|service|configmap|secret|ingress",
  "namespace": "string (optional) - target namespace, defaults to 'default'",
  "securityPolicy": "string (optional) - security policy level: restricted|standard|permissive",
  "helmChart": "boolean (optional) - generate as Helm chart, defaults to false",
  "environment": "string (optional) - target environment: dev|staging|prod",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "validateOnly": "boolean (optional) - validate without generating, defaults to false",
  "policyCheck": "boolean (optional) - enforce policy validation, defaults to true"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "manifest": "object - generated Kubernetes manifest",
    "helmChart": "object - generated Helm chart if requested",
    "policyViolations": "array - any policy violations found",
    "securityScore": "number - security assessment score 1-10",
    "validationResults": "object - schema and policy validation results",
    "deploymentGuide": "string - deployment instructions and considerations"
  },
  "errors": [],
  "metadata": {
    "resourceType": "string - type of resource generated",
    "namespace": "string - target namespace",
    "securityPolicy": "string - applied security policy",
    "riskScore": "number - operation risk score 1-10",
    "policyCompliant": "boolean - whether manifest passes all policies"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|POLICY_VIOLATION|SCHEMA_INVALID|GENERATION_FAILED",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```
