# Skills API

This document provides the technical API specification for interacting with AI agent skills in the Temporal AI Agents system. Skills are the core building blocks that enable automated infrastructure management, compliance monitoring, and intelligent workflow orchestration.

## Overview

The Skills API allows programmatic access to 28 specialized AI agent capabilities through structured REST API calls and MCP server integration. Each skill follows the Anthropic Agent Skills specification with standardized input/output schemas and error handling.

## System Architecture

The skills system consists of:
- **Temporal Workflow Engine**: Durable orchestration of AI agent workflows
- **Multi-Agent Framework**: Specialized agents for compliance, security, and cost analysis
- **REST APIs**: Programmatic access to workflow management
- **MCP Server**: Standardized agent-tool communication protocol
- **Infrastructure Emulator**: Safe simulation environment for cloud resources

## API Authentication

All skill calls require API key authentication:

```
Authorization: Bearer YOUR_API_KEY
```

Configure your API key:
```bash
export AI_AGENTS_API_KEY="your-production-api-key"
export AI_AGENTS_API_URL="http://localhost:8081"
```

## Available Skills

### Compliance Management Skills

#### `start_compliance_check`
Starts a compliance check workflow for a target resource.

**Endpoint:** `POST /api/skills/compliance-check/execute`

**Parameters:**
- `targetResource` (string, required): The resource to check (e.g., "vm-web-server-001")
- `complianceType` (string, optional): Type of compliance check - "SOC2", "GDPR", "HIPAA", "full-scan" (default: "full-scan")
- `priority` (string, optional): Priority level - "low", "normal", "high", "critical" (default: "normal")

**Returns:**
```json
{
  "workflowId": "uuid",
  "status": "started",
  "targetResource": "vm-web-server-001",
  "complianceType": "SOC2",
  "startedAt": "2025-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8081/api/skills/compliance-check/execute \
  -H "Authorization: Bearer $AI_AGENTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"targetResource": "vm-web-server-001", "complianceType": "SOC2", "priority": "high"}'
```

#### `get_compliance_status`
Retrieves the current status of a compliance workflow.

**Endpoint:** `GET /workflow/status?id={workflowId}`

**Parameters:**
- `workflowId` (string, required): The workflow ID to check

**Returns:**
```json
{
  "workflowId": "uuid",
  "status": "completed",
  "complianceScore": 94.2,
  "issuesFound": 3,
  "recommendations": ["Enable MFA", "Update SSL cert", "Configure backup"],
  "approved": true
}
```

### Security Analysis Skills

#### `start_security_scan`
Initiates a security analysis workflow.

**Endpoint:** `POST /api/skills/security-scan/execute`

**Parameters:**
- `targetResource` (string, required): Resource to scan
- `scanType` (string, optional): Scan type - "vulnerability", "malware", "configuration", "full" (default: "full")
- `priority` (string, optional): Priority level (default: "normal")

**Returns:**
```json
{
  "workflowId": "uuid",
  "status": "started",
  "targetResource": "prod-server-001",
  "scanType": "full",
  "startedAt": "2025-01-15T10:30:00Z"
}
```

#### `get_security_report`
Retrieves security analysis results.

**Endpoint:** `GET /workflow/status?id={workflowId}`

**Parameters:**
- `workflowId` (string, required): Security workflow ID

**Returns:**
```json
{
  "vulnerabilities": [
    {"id": "CVE-2023-12345", "severity": "HIGH", "description": "..."}
  ],
  "riskLevel": "medium",
  "recommendations": ["Apply security patch", "Update configuration"],
  "scanCoverage": 98.5
}
```

### Cost Optimization Skills

#### `start_cost_analysis`
Begins cost optimization analysis.

**Endpoint:** `POST /api/skills/cost-analysis/execute`

**Parameters:**
- `targetResource` (string, required): Resource to analyze
- `analysisType` (string, optional): Analysis type - "usage", "optimization", "forecast", "full" (default: "full")
- `timeframe` (string, optional): Analysis period - "7d", "30d", "90d" (default: "30d")

**Returns:**
```json
{
  "workflowId": "uuid",
  "targetResource": "all-production-resources",
  "analysisType": "full",
  "timeframe": "30d"
}
```

#### `get_cost_recommendations`
Retrieves cost optimization recommendations.

**Endpoint:** `GET /workflow/status?id={workflowId}`

**Parameters:**
- `workflowId` (string, required): Cost analysis workflow ID

**Returns:**
```json
{
  "currentCost": 12500.00,
  "projectedSavings": 1875.00,
  "recommendations": [
    {"description": "Rightsize EC2 instances", "savings": 1200.00, "roi": 75}
  ]
}
```

### Workflow Management Skills

#### `list_active_workflows`
Lists all currently running workflows.

**Endpoint:** `GET /workflows/active?type={workflowType}`

**Parameters:**
- `workflowType` (string, optional): Filter by type ("compliance", "security", "cost-analysis")

**Returns:**
```json
{
  "workflows": [
    {"id": "wf-123", "type": "compliance", "startTime": "2025-01-15T10:00:00Z"}
  ]
}
```

#### `get_workflow_details`
Gets detailed information about a specific workflow.

**Endpoint:** `GET /workflow/status?id={workflowId}`

**Parameters:**
- `workflowId` (string, required): Workflow identifier

**Returns:**
```json
{
  "workflowId": "wf-123",
  "type": "compliance",
  "status": "completed",
  "startTime": "2025-01-15T10:00:00Z",
  "progress": 100,
  "result": {"complianceScore": 94.2}
}
```

#### `cancel_workflow`
Cancels a running workflow.

**Endpoint:** `POST /workflow/signal/{workflowId}`

**Parameters:**
- `workflowId` (string, required): Workflow to cancel
- `reason` (string, optional): Reason for cancellation

**Returns:**
```json
{
  "success": true,
  "message": "Workflow cancelled successfully"
}
```

### Infrastructure Discovery Skills

#### `discover_resources`
Discovers available infrastructure resources.

**Endpoint:** `GET /emulator/resources?type={resourceType}&env={environment}`

**Parameters:**
- `resourceType` (string, optional): Filter by type - "vm", "database", "storage", "network", "all" (default: "all")
- `environment` (string, optional): Filter by environment - "dev", "staging", "prod", "all" (default: "all")

**Returns:**
```json
{
  "resources": [
    {"id": "vm-001", "type": "vm", "environment": "prod", "status": "running"}
  ],
  "totalCount": 25
}
```

#### `get_resource_details`
Gets detailed information about a specific resource.

**Endpoint:** `GET /emulator/resources/{resourceId}`

**Parameters:**
- `resourceId` (string, required): Resource identifier

**Returns:**
```json
{
  "resourceId": "vm-001",
  "type": "vm",
  "environment": "prod",
  "status": "running",
  "configuration": {"cpu": 4, "memory": "16GB", "disk": "100GB"}
}
```

### Human-in-the-Loop Skills

#### `request_human_review`
Initiates a human review workflow for agent decisions.

**Endpoint:** `POST /workflow/human-review`

**Parameters:**
- `workflowId` (string, required): Workflow requiring human review
- `reviewType` (string, required): Type of review needed
- `priority` (string, optional): Review priority ("low", "normal", "high", "critical")
- `context` (object, optional): Additional context for reviewers

**Returns:**
```json
{
  "reviewId": "review-123",
  "assignedTo": "security-team",
  "estimatedCompletion": "2 hours"
}
```

#### `get_review_status`
Checks the status of a human review task.

**Endpoint:** `GET /workflow/review/{reviewId}`

**Parameters:**
- `reviewId` (string, required): Review task identifier

**Returns:**
```json
{
  "status": "completed",
  "decision": "approved",
  "comments": "All security checks passed",
  "reviewedBy": "alice@company.com"
}
```

## Rate Limiting

- **Per minute**: 100 requests per API key
- **Per hour**: 1000 requests per API key
- Batch operations are encouraged for bulk actions

## Error Handling

All skills return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR|TIMEOUT|RATE_LIMITED|INFRASTRUCTURE_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "parameter_name",
      "expected": "expected_format"
    }
  }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input parameters
- `TIMEOUT`: Operation exceeded time limits
- `RATE_LIMITED`: Too many requests
- `INFRASTRUCTURE_ERROR`: Cloud provider or system issues

## Timeouts

- **Workflow operations**: 15 minutes
- **Status queries**: 30 seconds
- **Resource discovery**: 2 minutes

## MCP Server Integration

The MCP server exposes standardized tools for AI assistants:

**Endpoint:** `POST /mcp`

**Transport modes**: stdio, websocket, http

**Available tools**:
- `start_compliance_workflow`: Start compliance checks
- `get_workflow_status`: Monitor workflow progress
- `signal_workflow`: Send signals to workflows
- `get_infrastructure_info`: Discover resources

## Usage Examples

### Complete Compliance Workflow
```javascript
// Start compliance check
const complianceWorkflow = await start_compliance_check({
  targetResource: "prod-web-server-001",
  complianceType: "SOC2",
  priority: "high"
});

// Monitor progress
let status;
do {
  status = await get_workflow_details({ workflowId: complianceWorkflow.workflowId });
  await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
} while (status.status === "running");

// Get results
if (status.status === "completed") {
  console.log(`Compliance Score: ${status.result.complianceScore}%`);
  console.log(`Issues Found: ${status.result.issuesFound}`);
  if (!status.result.approved) {
    console.log("Recommendations:", status.result.recommendations);
  }
}
```

### Security Incident Response
```javascript
// Start security scan
const securityScan = await start_security_scan({
  targetResource: "compromised-server-001",
  scanType: "full",
  priority: "critical"
});

// Get report
const report = await get_security_report({ workflowId: securityScan.workflowId });

// Escalate if critical
if (report.riskLevel === "critical") {
  await request_human_review({
    workflowId: securityScan.workflowId,
    reviewType: "security-incident",
    priority: "critical"
  });
}
```

## Monitoring and Logging

All skill executions generate comprehensive logs including:
- Execution timestamps and duration
- User/API key identification
- Success/failure status and error details
- Performance metrics (CPU, memory, network usage)
- Audit trails for compliance reporting

This API specification enables seamless integration with AI assistants and automated systems for intelligent infrastructure management and workflow orchestration.
