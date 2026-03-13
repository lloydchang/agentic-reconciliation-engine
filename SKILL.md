# Temporal AI Agents - Claude/Codex Skills Interface

## Overview

The Temporal AI Agents system provides a comprehensive set of skills for managing and orchestrating AI agent workflows. This skill interface allows Claude and Codex to interact with the system through structured tool calls, enabling automated compliance checking, security analysis, cost optimization, and workflow management.

## System Architecture

The system consists of:
- **Temporal Workflow Engine**: Durable orchestration of AI agent workflows
- **Multi-Agent Framework**: Specialized agents for compliance, security, and cost analysis
- **REST APIs**: Programmatic access to workflow management
- **MCP Server**: Standardized agent-tool communication protocol
- **Infrastructure Emulator**: Safe simulation environment for cloud resources

## Available Skills

### 1. Compliance Management Skills

#### `start_compliance_check`
Starts a compliance check workflow for a target resource.

**Parameters:**
- `targetResource` (string, required): The resource to check (e.g., "vm-web-server-001")
- `complianceType` (string, optional): Type of compliance check - "SOC2", "GDPR", "HIPAA", "full-scan" (default: "full-scan")
- `priority` (string, optional): Priority level - "low", "normal", "high", "critical" (default: "normal")

**Returns:**
- `workflowId` (string): Unique identifier for the started workflow
- `status` (string): Initial status ("started")
- `targetResource` (string): Resource being checked
- `complianceType` (string): Type of compliance check
- `startedAt` (string): ISO timestamp when workflow started

**Example:**
```json
{
  "targetResource": "vm-web-server-001",
  "complianceType": "SOC2",
  "priority": "high"
}
```

#### `get_compliance_status`
Retrieves the current status of a compliance workflow.

**Parameters:**
- `workflowId` (string, required): The workflow ID to check

**Returns:**
- `workflowId` (string): Workflow identifier
- `status` (string): Current status ("running", "completed", "failed")
- `complianceScore` (number): Compliance score (0-100)
- `issuesFound` (number): Number of issues identified
- `recommendations` (array): List of remediation recommendations
- `approved` (boolean): Whether the resource passed compliance checks

### 2. Security Analysis Skills

#### `start_security_scan`
Initiates a security analysis workflow.

**Parameters:**
- `targetResource` (string, required): Resource to scan
- `scanType` (string, optional): Scan type - "vulnerability", "malware", "configuration", "full" (default: "full")
- `priority` (string, optional): Priority level (default: "normal")

**Returns:**
- `workflowId` (string): Workflow identifier
- `status` (string): Initial status
- `targetResource` (string): Resource being scanned
- `scanType` (string): Type of security scan
- `startedAt` (string): Start timestamp

#### `get_security_report`
Retrieves security analysis results.

**Parameters:**
- `workflowId` (string, required): Security workflow ID

**Returns:**
- `vulnerabilities` (array): List of identified vulnerabilities
- `riskLevel` (string): Overall risk assessment ("low", "medium", "high", "critical")
- `recommendations` (array): Security remediation steps
- `scanCoverage` (number): Percentage of resource scanned

### 3. Cost Optimization Skills

#### `start_cost_analysis`
Begins cost optimization analysis.

**Parameters:**
- `targetResource` (string, required): Resource to analyze
- `analysisType` (string, optional): Analysis type - "usage", "optimization", "forecast", "full" (default: "full")
- `timeframe` (string, optional): Analysis period - "7d", "30d", "90d" (default: "30d")

**Returns:**
- `workflowId` (string): Analysis workflow ID
- `targetResource` (string): Resource analyzed
- `analysisType` (string): Type of cost analysis
- `timeframe` (string): Analysis period

#### `get_cost_recommendations`
Retrieves cost optimization recommendations.

**Parameters:**
- `workflowId` (string, required): Cost analysis workflow ID

**Returns:**
- `currentCost` (number): Current monthly cost
- `projectedSavings` (number): Potential monthly savings
- `recommendations` (array): Specific cost optimization actions
- `roi` (number): Return on investment percentage

### 4. Workflow Management Skills

#### `list_active_workflows`
Lists all currently running workflows.

**Parameters:**
- `workflowType` (string, optional): Filter by type ("compliance", "security", "cost-analysis")

**Returns:**
- `workflows` (array): List of active workflows with IDs, types, and start times

#### `get_workflow_details`
Gets detailed information about a specific workflow.

**Parameters:**
- `workflowId` (string, required): Workflow identifier

**Returns:**
- `workflowId` (string): Workflow ID
- `type` (string): Workflow type
- `status` (string): Current status
- `startTime` (string): When workflow started
- `endTime` (string, optional): When workflow completed
- `progress` (number): Completion percentage (0-100)
- `result` (object): Workflow results (varies by type)

#### `cancel_workflow`
Cancels a running workflow.

**Parameters:**
- `workflowId` (string, required): Workflow to cancel
- `reason` (string, optional): Reason for cancellation

**Returns:**
- `success` (boolean): Whether cancellation was successful
- `message` (string): Confirmation message

### 5. Infrastructure Discovery Skills

#### `discover_resources`
Discovers available infrastructure resources.

**Parameters:**
- `resourceType` (string, optional): Filter by type - "vm", "database", "storage", "network", "all" (default: "all")
- `environment` (string, optional): Filter by environment - "dev", "staging", "prod", "all" (default: "all")

**Returns:**
- `resources` (array): List of discovered resources with metadata
- `totalCount` (number): Total number of resources found

#### `get_resource_details`
Gets detailed information about a specific resource.

**Parameters:**
- `resourceId` (string, required): Resource identifier

**Returns:**
- `resourceId` (string): Resource identifier
- `type` (string): Resource type
- `environment` (string): Deployment environment
- `status` (string): Current operational status
- `configuration` (object): Resource configuration details

### 6. Human-in-the-Loop Skills

#### `request_human_review`
Initiates a human review workflow for agent decisions.

**Parameters:**
- `workflowId` (string, required): Workflow requiring human review
- `reviewType` (string, required): Type of review needed
- `priority` (string, optional): Review priority ("low", "normal", "high", "critical")
- `context` (object, optional): Additional context for reviewers

**Returns:**
- `reviewId` (string): Human review task identifier
- `assignedTo` (string): Team or person assigned for review
- `estimatedCompletion` (string): Expected completion time

#### `get_review_status`
Checks the status of a human review task.

**Parameters:**
- `reviewId` (string, required): Review task identifier

**Returns:**
- `status` (string): Review status ("pending", "in-progress", "completed")
- `decision` (string, optional): Final decision if completed
- `comments` (string, optional): Review comments
- `reviewedBy` (string, optional): Who performed the review

## Usage Examples

### Compliance Automation Workflow
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
// Detect and respond to security incident
const securityScan = await start_security_scan({
  targetResource: "compromised-server-001",
  scanType: "full",
  priority: "critical"
});

// Wait for completion and get report
const report = await get_security_report({ workflowId: securityScan.workflowId });

// Take automated actions based on findings
if (report.riskLevel === "critical") {
  // Trigger emergency response workflows
  await request_human_review({
    workflowId: securityScan.workflowId,
    reviewType: "security-incident",
    priority: "critical"
  });
}
```

### Cost Optimization Analysis
```javascript
// Monthly cost review
const costAnalysis = await start_cost_analysis({
  targetResource: "all-production-resources",
  analysisType: "full",
  timeframe: "30d"
});

// Get optimization recommendations
const recommendations = await get_cost_recommendations({
  workflowId: costAnalysis.workflowId
});

console.log(`Current Cost: $${recommendations.currentCost}/month`);
console.log(`Potential Savings: $${recommendations.projectedSavings}/month`);

// Implement high-ROI recommendations automatically
recommendations.recommendations
  .filter(rec => rec.roi > 50)
  .forEach(rec => {
    console.log(`High ROI Recommendation: ${rec.description}`);
    // Trigger implementation workflow
  });
```

## Integration Guidelines

### Authentication
All skill calls require API key authentication:
```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting
- 100 requests per minute per API key
- 1000 requests per hour per API key
- Batch operations encouraged for bulk actions

### Error Handling
All skills return consistent error responses:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid workflow ID format",
    "details": { "field": "workflowId", "expected": "uuid-format" }
  }
}
```

### Timeouts
- Workflow operations: 15 minutes
- Status queries: 30 seconds
- Resource discovery: 2 minutes

## System Requirements

- **Backend API**: `http://localhost:8081` (configurable)
- **MCP Server**: `localhost:8082` (stdio/websocket/http)
- **Authentication**: API key required
- **Data Format**: JSON for all requests/responses

## Monitoring and Logging

All skill executions are logged with:
- Timestamp and duration
- User/API key identification
- Success/failure status
- Performance metrics
- Audit trail for compliance

This skill interface enables Claude and Codex to seamlessly integrate with the Temporal AI Agents system for automated infrastructure management, compliance monitoring, and intelligent workflow orchestration.
