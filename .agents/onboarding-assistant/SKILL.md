# Onboarding Assistant Skill

## Name
onboarding-assistant

## Purpose
Guide new team members and services through the platform onboarding process, including access setup, resource provisioning, and best practice education.

## When to Use
- When new team members join the organization
- When onboarding new services or applications
- When setting up development environments
- When provisioning access and permissions
- When providing platform training and documentation

## Inputs
- User or service profile information
- Required access levels and permissions
- Environment and resource requirements
- Training and documentation needs
- Timeline and milestone expectations

## Process
1. Assess onboarding requirements and scope
2. Provision necessary accounts and access
3. Set up development environments and tools
4. Provide training materials and documentation
5. Configure monitoring and alerting
6. Validate successful onboarding completion

## Outputs
- User accounts and access credentials
- Development environment configurations
- Training materials and documentation
- Access and permission reports
- Onboarding completion verification

## Environment
- Identity and access management systems
- Development environment provisioning
- Documentation and training platforms
- Monitoring and alerting systems

## Dependencies
- IAM systems and directory services
- Environment provisioning tools
- Documentation management systems
- Training and learning platforms

## Scripts
- scripts/onboard_user.py: Python script for user onboarding
- scripts/setup_environment.py: Environment provisioning script
- scripts/generate_credentials.py: Access credential generation script

## Trigger Keywords
onboarding, scaffold, catalog, portal, templates

## Human Gate Requirements
Enterprise resource prep

## API Patterns

### JavaScript
```javascript
// Onboard new user or service
const onboarding = await onboard_entity({
  entityType: "user|service|team",
  entityName: "john.doe|web-service",
  accessLevel: "developer|admin|read-only",
  priority: "normal"
});

// Get onboarding results
const results = await get_onboarding_results({
  workflowId: onboarding.workflowId
});
```

### Rust
```rust
// Rust-based onboarding automation
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct OnboardingRequest {
    pub entity_type: EntityType,
    pub entity_name: String,
    pub access_level: AccessLevel,
    pub priority: Priority,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum EntityType {
    User,
    Service,
    Team,
}

pub async fn onboard_entity(request: OnboardingRequest) -> Result<OnboardingWorkflow, OnboardingError> {
    // Comprehensive onboarding automation
    let workflow = OnboardingWorkflow::new(request).await?;
    
    // Execute complete onboarding process
    workflow.onboard_comprehensive().await?;
    
    Ok(workflow)
}
```

## Parameter Schema
```json
{
  "entityType": "string (required) - type of entity to onboard: user|service|team",
  "entityName": "string (required) - name of the entity to onboard",
  "accessLevel": "string (required) - required access level: developer|admin|read-only|operator",
  "environment": "string (optional) - target environment: dev|staging|prod|all",
  "resources": "array (optional) - specific resources to provision",
  "trainingRequired": "boolean (optional) - provide training materials, defaults to true",
  "timeline": "string (optional) - onboarding timeline: immediate|1day|1week",
  "priority": "string (optional) - operation priority: low|normal|high|critical",
  "notifications": "boolean (optional) - send completion notifications, defaults to true"
}
```

## Return Schema
```json
{
  "workflowId": "uuid",
  "status": "started|running|completed|failed",
  "startedAt": "ISO8601 timestamp",
  "result": {
    "entityType": "string - type of entity onboarded",
    "entityName": "string - name of the onboarded entity",
    "accounts": "array - provisioned accounts and credentials",
    "accessGrants": "array - granted permissions and access levels",
    "environments": "array - set up development environments",
    "trainingMaterials": "array - provided documentation and training",
    "completionChecklist": "array - onboarding completion verification items"
  },
  "errors": [],
  "metadata": {
    "onboardingDuration": "string - total time for onboarding process",
    "resourcesProvisioned": "number - number of resources created",
    "accessLevelGranted": "string - final access level assigned",
    "trainingCompleted": "boolean - whether training was provided",
    "riskScore": "number - operation risk score 1-10"
  }
}
```

## Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR|ACCESS_DENIED|PROVISIONING_FAILED|TRAINING_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format",
      "actual": "provided_value"
    }
  }
}
```
