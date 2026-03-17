# MCP Server Implementation Guide

## Overview

This document provides detailed implementation guidance for the Model Context Protocol (MCP) servers that power the AI Agent Skills. MCP servers enable AI agents to interact with external tools, services, and data sources through standardized interfaces.

## Table of Contents

1. [MCP Protocol Overview](#mcp-protocol-overview)
2. [Server Architecture](#server-architecture)
3. [Implementation Patterns](#implementation-patterns)
4. [Tool Development](#tool-development)
5. [Resource Management](#resource-management)
6. [Prompt Templates](#prompt-templates)
7. [Error Handling](#error-handling)
8. [Security Implementation](#security-implementation)
9. [Testing and Validation](#testing-and-validation)
10. [Performance Optimization](#performance-optimization)

## MCP Protocol Overview

### Protocol Basics

The Model Context Protocol (MCP) defines a standardized way for AI models to interact with external systems. It provides:

- **Tools**: Callable functions that perform specific actions
- **Resources**: Data sources and state management
- **Prompts**: Structured templates for AI interactions

### Protocol Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   AI Model  │───▶│   MCP       │───▶│   External  │───▶│   Response  │
│   (Client)  │    │   Server    │    │   Service   │    │   (Result)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
         │                │                │                │
         ▼                ▼                ▼                ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Request   │    │   Tool      │    │   API Call  │    │   Data      │
│   JSON      │    │   Execution │    │   HTTP/SDK  │    │   Processing│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Message Types

1. **initialize**: Establish connection and capabilities
2. **tools/list**: List available tools
3. **tools/call**: Execute a specific tool
4. **resources/list**: List available resources
5. **resources/read**: Read resource data
6. **prompts/list**: List available prompts
7. **prompts/get**: Get prompt template

## Server Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                           │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Server    │  │   Tool      │  │   Resource  │    │
│  │   Core      │  │   Registry  │  │   Manager   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Request   │  │   Skill     │  │   Data       │    │
│  │   Handler   │  │   Logic     │  │   Access     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │             │
│         ▼                ▼                ▼             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   External  │  │   Business  │  │   Storage    │    │
│  │   APIs      │  │   Logic     │  │   Layer      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Server Implementation Template

```javascript
#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
  ListResourcesRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

// Server initialization
const server = new Server(
  {
    name: "skill-name",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {}
    },
  }
);

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "tool-name",
        description: "Tool description",
        inputSchema: {
          type: "object",
          properties: {
            parameter1: {
              type: "string",
              description: "Parameter description"
            }
          },
          required: ["parameter1"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case "tool-name":
        return await handleToolName(args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Resource handlers
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "resource://example/data",
        name: "Example Resource",
        description: "Resource description",
        mimeType: "application/json"
      }
    ]
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  switch (uri) {
    case "resource://example/data":
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify({ data: "example" })
          }
        ]
      };
    default:
      throw new Error(`Unknown resource: ${uri}`);
  }
});

// Prompt handlers
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "example-prompt",
        description: "Example prompt template",
        arguments: [
          {
            name: "topic",
            description: "Topic for the prompt",
            required: true
          }
        ]
      }
    ]
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case "example-prompt":
      return {
        description: "Generated prompt for {topic}",
        messages: [
          {
            role: "user",
            content: {
              type: "text",
              text: `Please provide information about ${args.topic}`
            }
          }
        ]
      };
    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

## Implementation Patterns

### Error Handling Pattern

```javascript
// Standardized error handling
class SkillError extends Error {
  constructor(message, code, details = {}) {
    super(message);
    this.name = 'SkillError';
    this.code = code;
    this.details = details;
  }
}

// Error response format
const createErrorResponse = (error) => {
  return {
    content: [
      {
        type: "text",
        text: `Error: ${error.message}`
      }
    ],
    isError: true,
    error: {
      code: error.code || 'UNKNOWN_ERROR',
      message: error.message,
      details: error.details
    }
  };
};

// Usage in tool handlers
try {
  const result = await riskyOperation(args);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result, null, 2)
      }
    ]
  };
} catch (error) {
  return createErrorResponse(error);
}
```

### Validation Pattern

```javascript
// Input validation
const validateInput = (schema, input) => {
  const errors = [];
  
  for (const [field, rules] of Object.entries(schema)) {
    const value = input[field];
    
    if (rules.required && (value === undefined || value === null)) {
      errors.push(`${field} is required`);
      continue;
    }
    
    if (rules.type && typeof value !== rules.type) {
      errors.push(`${field} must be of type ${rules.type}`);
    }
    
    if (rules.pattern && !rules.pattern.test(value)) {
      errors.push(`${field} does not match required pattern`);
    }
  }
  
  if (errors.length > 0) {
    throw new SkillError('Validation failed', 'VALIDATION_ERROR', { errors });
  }
};

// Usage
const inputSchema = {
  accountId: { required: true, type: 'string', pattern: /^\d{12}$/ },
  region: { required: false, type: 'string', default: 'us-east-1' }
};

validateInput(inputSchema, args);
```

### Async Operation Pattern

```javascript
// Async operation handling
class AsyncOperation {
  constructor(id, operation, timeout = 30000) {
    this.id = id;
    this.operation = operation;
    this.timeout = timeout;
    this.startTime = Date.now();
    this.status = 'pending';
    this.result = null;
    this.error = null;
  }
  
  async execute() {
    try {
      this.status = 'running';
      this.result = await Promise.race([
        this.operation(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Operation timeout')), this.timeout)
        )
      ]);
      this.status = 'completed';
      return this.result;
    } catch (error) {
      this.error = error;
      this.status = 'failed';
      throw error;
    }
  }
  
  getStatus() {
    return {
      id: this.id,
      status: this.status,
      startTime: this.startTime,
      duration: Date.now() - this.startTime,
      result: this.result,
      error: this.error
    };
  }
}

// Usage in tool handlers
const operationId = generateOperationId();
const operation = new AsyncOperation(operationId, async () => {
  return await performComplexOperation(args);
});

// For long-running operations, return operation ID
return {
  content: [
    {
      type: "text",
      text: JSON.stringify({
        operationId: operation.id,
        status: 'started',
        message: 'Operation started. Use check-status tool to monitor progress.'
      })
    }
  ]
};
```

## Tool Development

### Tool Design Principles

1. **Single Responsibility**: Each tool should do one thing well
2. **Idempotency**: Tools should be safe to call multiple times
3. **Validation**: Validate all inputs before processing
4. **Error Handling**: Provide clear error messages and recovery options
5. **Documentation**: Include comprehensive descriptions and examples

### Tool Implementation Example

```javascript
// Cloud Compliance Auditor - Compliance Scan Tool
const handleComplianceScan = async (args) => {
  const {
    scope = 'all',
    framework = 'CIS',
    severityThreshold = 'medium',
    remediationMode = 'dry_run',
    accounts = [],
    subscriptions = [],
    projects = []
  } = args;
  
  // Validate inputs
  const schema = {
    scope: { type: 'string', enum: ['all', 'production', 'staging', 'development'] },
    framework: { type: 'string', enum: ['CIS', 'NIST', 'SOC2', 'PCI-DSS', 'HIPAA'] },
    severityThreshold: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
    remediationMode: { type: 'string', enum: ['dry_run', 'auto', 'manual'] }
  };
  
  validateInput(schema, args);
  
  // Initialize scan
  const scanId = generateScanId();
  const scan = {
    id: scanId,
    startTime: new Date().toISOString(),
    status: 'running',
    scope,
    framework,
    severityThreshold,
    remediationMode,
    accounts,
    subscriptions,
    projects,
    findings: []
  };
  
  try {
    // Execute compliance scan
    if (scope === 'all' || scope.includes('aws')) {
      const awsFindings = await scanAWSCompliance({
        accounts,
        framework,
        severityThreshold
      });
      scan.findings.push(...awsFindings);
    }
    
    if (scope === 'all' || scope.includes('azure')) {
      const azureFindings = await scanAzureCompliance({
        subscriptions,
        framework,
        severityThreshold
      });
      scan.findings.push(...azureFindings);
    }
    
    if (scope === 'all' || scope.includes('gcp')) {
      const gcpFindings = await scanGCPCompliance({
        projects,
        framework,
        severityThreshold
      });
      scan.findings.push(...gcpFindings);
    }
    
    // Process findings
    scan.findings = processFindings(scan.findings, severityThreshold);
    
    // Generate remediation plan if requested
    if (remediationMode !== 'dry_run') {
      scan.remediationPlan = generateRemediationPlan(scan.findings);
    }
    
    scan.status = 'completed';
    scan.endTime = new Date().toISOString();
    scan.duration = calculateDuration(scan.startTime, scan.endTime);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(scan, null, 2)
        }
      ]
    };
    
  } catch (error) {
    scan.status = 'failed';
    scan.error = error.message;
    scan.endTime = new Date().toISOString();
    
    return createErrorResponse(error);
  }
};

// AWS Compliance Scan Implementation
const scanAWSCompliance = async ({ accounts, framework, severityThreshold }) => {
  const findings = [];
  
  for (const account of accounts) {
    try {
      // Initialize AWS SDK
      const awsClient = new AWSClient(account);
      
      // Scan based on framework
      switch (framework) {
        case 'CIS':
          const cisFindings = await scanCISControls(awsClient);
          findings.push(...cisFindings);
          break;
        case 'NIST':
          const nistFindings = await scanNISTControls(awsClient);
          findings.push(...nistFindings);
          break;
        // Add other frameworks
      }
      
    } catch (error) {
      findings.push({
        account,
        framework,
        severity: 'high',
        title: 'AWS Scan Failed',
        description: `Failed to scan account: ${error.message}`,
        recommendation: 'Check AWS credentials and permissions'
      });
    }
  }
  
  return findings;
};
```

### Tool Registration Pattern

```javascript
// Tool registry system
class ToolRegistry {
  constructor() {
    this.tools = new Map();
  }
  
  register(name, handler, schema) {
    this.tools.set(name, {
      name,
      handler,
      schema,
      description: schema.description || `Tool: ${name}`
    });
  }
  
  list() {
    return Array.from(this.tools.values()).map(tool => ({
      name: tool.name,
      description: tool.description,
      inputSchema: tool.schema
    }));
  }
  
  async call(name, args) {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new SkillError(`Tool not found: ${name}`, 'TOOL_NOT_FOUND');
    }
    
    return await tool.handler(args);
  }
}

// Usage
const toolRegistry = new ToolRegistry();

toolRegistry.register('compliance-scan', handleComplianceScan, {
  name: 'compliance-scan',
  description: 'Perform comprehensive compliance scan across cloud environments',
  inputSchema: {
    type: 'object',
    properties: {
      scope: {
        type: 'string',
        enum: ['all', 'production', 'staging', 'development'],
        description: 'Scope of the compliance scan'
      },
      framework: {
        type: 'string',
        enum: ['CIS', 'NIST', 'SOC2', 'PCI-DSS', 'HIPAA'],
        description: 'Compliance framework to use'
      },
      severityThreshold: {
        type: 'string',
        enum: ['low', 'medium', 'high', 'critical'],
        description: 'Minimum severity level for findings'
      },
      remediationMode: {
        type: 'string',
        enum: ['dry_run', 'auto', 'manual'],
        description: 'Remediation mode'
      },
      accounts: {
        type: 'array',
        items: { type: 'string' },
        description: 'AWS accounts to scan'
      },
      subscriptions: {
        type: 'array',
        items: { type: 'string' },
        description: 'Azure subscriptions to scan'
      },
      projects: {
        type: 'array',
        items: { type: 'string' },
        description: 'GCP projects to scan'
      }
    },
    required: ['framework']
  }
});

// MCP server integration
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    return await toolRegistry.call(name, args);
  } catch (error) {
    return createErrorResponse(error);
  }
});
```

## Resource Management

### Resource Types

1. **Configuration Resources**: Settings and preferences
2. **Data Resources**: Static or dynamic data
3. **State Resources**: Current system state
4. **Log Resources**: Historical operation logs

### Resource Implementation Example

```javascript
// Resource manager
class ResourceManager {
  constructor() {
    this.resources = new Map();
    this.cache = new Map();
    this.cacheTimeout = 300000; // 5 minutes
  }
  
  register(uri, handler, options = {}) {
    this.resources.set(uri, {
      uri,
      handler,
      mimeType: options.mimeType || 'application/json',
      cacheable: options.cacheable !== false,
      description: options.description || `Resource: ${uri}`
    });
  }
  
  list() {
    return Array.from(this.resources.values()).map(resource => ({
      uri: resource.uri,
      name: resource.uri.split('/').pop(),
      description: resource.description,
      mimeType: resource.mimeType
    }));
  }
  
  async read(uri) {
    const resource = this.resources.get(uri);
    if (!resource) {
      throw new SkillError(`Resource not found: ${uri}`, 'RESOURCE_NOT_FOUND');
    }
    
    // Check cache
    if (resource.cacheable && this.cache.has(uri)) {
      const cached = this.cache.get(uri);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }
    }
    
    // Fetch fresh data
    const data = await resource.handler();
    
    // Cache if cacheable
    if (resource.cacheable) {
      this.cache.set(uri, {
        data,
        timestamp: Date.now()
      });
    }
    
    return {
      contents: [
        {
          uri,
          mimeType: resource.mimeType,
          text: typeof data === 'string' ? data : JSON.stringify(data, null, 2)
        }
      ]
    };
  }
  
  invalidate(uri) {
    this.cache.delete(uri);
  }
  
  clearCache() {
    this.cache.clear();
  }
}

// Resource registration
const resourceManager = new ResourceManager();

// Configuration resource
resourceManager.register('config://compliance/settings', async () => {
  return {
    frameworks: ['CIS', 'NIST', 'SOC2', 'PCI-DSS', 'HIPAA'],
    severityLevels: ['low', 'medium', 'high', 'critical'],
    remediationModes: ['dry_run', 'auto', 'manual'],
    defaultTimeout: 300000,
    maxConcurrentScans: 5
  };
}, {
  mimeType: 'application/json',
  description: 'Compliance scanner configuration settings'
});

// Data resource
resourceManager.register('data://compliance/findings', async () => {
  const findings = await loadRecentFindings();
  return findings;
}, {
  mimeType: 'application/json',
  description: 'Recent compliance findings',
  cacheable: true
});

// State resource
resourceManager.register('state://compliance/scanner', async () => {
  const state = await getScannerState();
  return state;
}, {
  mimeType: 'application/json',
  description: 'Current scanner state and status',
  cacheable: false
});

// MCP server integration
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return { resources: resourceManager.list() };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  return await resourceManager.read(uri);
});
```

## Prompt Templates

### Prompt Design Principles

1. **Context Awareness**: Provide relevant context for the AI model
2. **Structured Output**: Define expected response formats
3. **Parameterization**: Use variables for dynamic content
4. **Clarity**: Be specific and unambiguous
5. **Reusability**: Design prompts for multiple use cases

### Prompt Implementation Example

```javascript
// Prompt manager
class PromptManager {
  constructor() {
    this.prompts = new Map();
  }
  
  register(name, template, options = {}) {
    this.prompts.set(name, {
      name,
      template,
      arguments: options.arguments || [],
      description: options.description || `Prompt: ${name}`
    });
  }
  
  list() {
    return Array.from(this.prompts.values()).map(prompt => ({
      name: prompt.name,
      description: prompt.description,
      arguments: prompt.arguments
    }));
  }
  
  get(name, args = {}) {
    const prompt = this.prompts.get(name);
    if (!prompt) {
      throw new SkillError(`Prompt not found: ${name}`, 'PROMPT_NOT_FOUND');
    }
    
    // Validate arguments
    for (const arg of prompt.arguments) {
      if (arg.required && !args[arg.name]) {
        throw new SkillError(`Required argument missing: ${arg.name}`, 'MISSING_ARGUMENT');
      }
    }
    
    // Render template
    let rendered = prompt.template;
    for (const [key, value] of Object.entries(args)) {
      rendered = rendered.replace(new RegExp(`{${key}}`, 'g'), value);
    }
    
    return {
      description: `Generated ${name} prompt`,
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: rendered
          }
        }
      ]
    };
  }
}

// Prompt registration
const promptManager = new PromptManager();

// Compliance analysis prompt
promptManager.register('compliance-analysis', `
Please analyze the following compliance findings and provide recommendations:

## Findings Summary
{findings_summary}

## Compliance Framework
{framework}

## Severity Threshold
{severity_threshold}

## Analysis Requirements
1. Identify patterns and trends in the findings
2. Prioritize remediation actions based on risk
3. Provide specific, actionable recommendations
4. Suggest preventive measures for future compliance

## Expected Output Format
- Executive Summary (2-3 sentences)
- Key Findings (bullet points)
- Risk Assessment (High/Medium/Low)
- Recommendations (numbered list)
- Preventive Measures (bullet points)

Please provide a comprehensive analysis that can be used for compliance reporting and remediation planning.
`, {
  arguments: [
    {
      name: 'findings_summary',
      description: 'Summary of compliance findings',
      required: true
    },
    {
      name: 'framework',
      description: 'Compliance framework used',
      required: true
    },
    {
      name: 'severity_threshold',
      description: 'Severity threshold applied',
      required: false
    }
  ],
  description: 'Analyze compliance findings and provide recommendations'
});

// Incident response prompt
promptManager.register('incident-response', `
Please provide incident response guidance for the following situation:

## Incident Details
{incident_details}

## Alert Information
{alert_information}

## System Impact
{system_impact}

## Response Requirements
1. Assess incident severity and priority
2. Provide immediate containment steps
3. Suggest investigation procedures
4. Recommend communication strategy
5. Outline recovery plan

## Expected Output Format
- Severity Assessment (P0/P1/P2/P3)
- Immediate Actions (numbered list)
- Investigation Steps (numbered list)
- Communication Plan (who/what/when)
- Recovery Strategy (numbered list)
- Prevention Measures (bullet points)

Please provide actionable guidance that can be immediately implemented by the incident response team.
`, {
  arguments: [
    {
      name: 'incident_details',
      description: 'Detailed incident information',
      required: true
    },
    {
      name: 'alert_information',
      description: 'Alert data and metrics',
      required: true
    },
    {
      name: 'system_impact',
      description: 'Current system impact assessment',
      required: true
    }
  ],
  description: 'Provide incident response guidance and procedures'
});

// MCP server integration
server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return { prompts: promptManager.list() };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  return promptManager.get(name, args);
});
```

## Error Handling

### Error Classification

```javascript
// Error types and codes
const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  RATE_LIMIT_ERROR: 'RATE_LIMIT_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  API_ERROR: 'API_ERROR',
  CONFIGURATION_ERROR: 'CONFIGURATION_ERROR',
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  TOOL_NOT_FOUND: 'TOOL_NOT_FOUND',
  PROMPT_NOT_FOUND: 'PROMPT_NOT_FOUND',
  MISSING_ARGUMENT: 'MISSING_ARGUMENT',
  INVALID_ARGUMENT: 'INVALID_ARGUMENT',
  OPERATION_FAILED: 'OPERATION_FAILED',
  INTERNAL_ERROR: 'INTERNAL_ERROR'
};

// Error hierarchy
class SkillError extends Error {
  constructor(message, code, details = {}) {
    super(message);
    this.name = 'SkillError';
    this.code = code;
    this.details = details;
    this.timestamp = new Date().toISOString();
  }
}

class ValidationError extends SkillError {
  constructor(message, details = {}) {
    super(message, ERROR_CODES.VALIDATION_ERROR, details);
    this.name = 'ValidationError';
  }
}

class AuthenticationError extends SkillError {
  constructor(message, details = {}) {
    super(message, ERROR_CODES.AUTHENTICATION_ERROR, details);
    this.name = 'AuthenticationError';
  }
}

class RateLimitError extends SkillError {
  constructor(message, details = {}) {
    super(message, ERROR_CODES.RATE_LIMIT_ERROR, details);
    this.name = 'RateLimitError';
  }
}
```

### Error Response Format

```javascript
// Standardized error response
const createErrorResponse = (error, context = {}) => {
  const response = {
    content: [
      {
        type: "text",
        text: `Error: ${error.message}`
      }
    ],
    isError: true,
    error: {
      code: error.code || ERROR_CODES.INTERNAL_ERROR,
      message: error.message,
      timestamp: error.timestamp || new Date().toISOString(),
      context: context
    }
  };
  
  // Add details if available
  if (error.details) {
    response.error.details = error.details;
  }
  
  // Add stack trace in development
  if (process.env.NODE_ENV === 'development') {
    response.error.stack = error.stack;
  }
  
  return response;
};

// Error logging
const logError = (error, context = {}) => {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level: 'error',
    code: error.code,
    message: error.message,
    context: context,
    stack: error.stack
  };
  
  console.error(JSON.stringify(logEntry, null, 2));
  
  // Send to external logging service if configured
  if (process.env.LOGGING_ENDPOINT) {
    sendToLoggingService(logEntry);
  }
};
```

### Error Recovery Strategies

```javascript
// Retry mechanism
class RetryHandler {
  constructor(maxRetries = 3, baseDelay = 1000, maxDelay = 10000) {
    this.maxRetries = maxRetries;
    this.baseDelay = baseDelay;
    this.maxDelay = maxDelay;
  }
  
  async execute(operation, context = {}) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        
        // Don't retry certain errors
        if (error.code === ERROR_CODES.VALIDATION_ERROR ||
            error.code === ERROR_CODES.AUTHENTICATION_ERROR ||
            error.code === ERROR_CODES.AUTHORIZATION_ERROR) {
          throw error;
        }
        
        if (attempt === this.maxRetries) {
          throw new SkillError(
            `Operation failed after ${this.maxRetries} attempts: ${error.message}`,
            ERROR_CODES.OPERATION_FAILED,
            { originalError: error, attempts: attempt }
          );
        }
        
        // Calculate delay with exponential backoff
        const delay = Math.min(this.baseDelay * Math.pow(2, attempt - 1), this.maxDelay);
        
        logError(error, { attempt, delay, context });
        
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }
}

// Circuit breaker pattern
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.threshold = threshold;
    this.timeout = timeout;
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
  }
  
  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new SkillError('Circuit breaker is OPEN', ERROR_CODES.RATE_LIMIT_ERROR);
      }
    }
    
    try {
      const result = await operation();
      
      if (this.state === 'HALF_OPEN') {
        this.state = 'CLOSED';
        this.failureCount = 0;
      }
      
      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();
      
      if (this.failureCount >= this.threshold) {
        this.state = 'OPEN';
      }
      
      throw error;
    }
  }
}
```

## Security Implementation

### Authentication and Authorization

```javascript
// Security manager
class SecurityManager {
  constructor() {
    this.apiKeys = new Map();
    this.rateLimits = new Map();
    this.auditLog = [];
  }
  
  // API key management
  addApiKey(key, permissions = []) {
    this.apiKeys.set(key, {
      key,
      permissions,
      createdAt: new Date().toISOString(),
      lastUsed: null,
      usageCount: 0
    });
  }
  
  validateApiKey(key) {
    const apiKey = this.apiKeys.get(key);
    if (!apiKey) {
      throw new AuthenticationError('Invalid API key');
    }
    
    apiKey.lastUsed = new Date().toISOString();
    apiKey.usageCount++;
    
    return apiKey;
  }
  
  // Permission checking
  checkPermission(apiKey, permission) {
    const keyData = this.validateApiKey(apiKey);
    
    if (!keyData.permissions.includes(permission) && !keyData.permissions.includes('*')) {
      throw new AuthenticationError('Insufficient permissions');
    }
    
    return true;
  }
  
  // Rate limiting
  checkRateLimit(apiKey, limit = 100, window = 60000) {
    const now = Date.now();
    const key = `rate_limit:${apiKey}`;
    
    if (!this.rateLimits.has(key)) {
      this.rateLimits.set(key, { count: 0, resetTime: now + window });
    }
    
    const rateLimit = this.rateLimits.get(key);
    
    if (now > rateLimit.resetTime) {
      rateLimit.count = 0;
      rateLimit.resetTime = now + window;
    }
    
    if (rateLimit.count >= limit) {
      throw new RateLimitError('Rate limit exceeded');
    }
    
    rateLimit.count++;
  }
  
  // Audit logging
  log(action, apiKey, details = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      action,
      apiKey: apiKey.substring(0, 8) + '...', // Partial key for privacy
      details
    };
    
    this.auditLog.push(entry);
    
    // Keep only last 1000 entries
    if (this.auditLog.length > 1000) {
      this.auditLog = this.auditLog.slice(-1000);
    }
  }
}

// Security middleware
const securityMiddleware = (securityManager) => {
  return (req, res, next) => {
    try {
      // Extract API key from headers
      const apiKey = req.headers['x-api-key'];
      
      if (!apiKey) {
        throw new AuthenticationError('API key required');
      }
      
      // Validate API key
      securityManager.validateApiKey(apiKey);
      
      // Check rate limits
      securityManager.checkRateLimit(apiKey);
      
      // Log access
      securityManager.log('access', apiKey, {
        method: req.method,
        path: req.path,
        ip: req.ip
      });
      
      next();
    } catch (error) {
      res.status(401).json({
        error: error.message,
        code: error.code
      });
    }
  };
};
```

### Data Protection

```javascript
// Data encryption
class DataProtection {
  constructor(encryptionKey) {
    this.algorithm = 'aes-256-gcm';
    this.key = crypto.createHash('sha256').update(encryptionKey).digest();
  }
  
  encrypt(data) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipher(this.algorithm, this.key);
    cipher.setAAD(Buffer.from('mcp-server-data'));
    
    let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }
  
  decrypt(encryptedData) {
    const decipher = crypto.createDecipher(this.algorithm, this.key);
    decipher.setAAD(Buffer.from('mcp-server-data'));
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return JSON.parse(decrypted);
  }
  
  // Sanitize sensitive data
  sanitize(data) {
    const sensitiveFields = ['password', 'token', 'key', 'secret', 'credential'];
    
    const sanitizeObject = (obj) => {
      if (typeof obj !== 'object' || obj === null) {
        return obj;
      }
      
      const sanitized = {};
      for (const [key, value] of Object.entries(obj)) {
        const lowerKey = key.toLowerCase();
        
        if (sensitiveFields.some(field => lowerKey.includes(field))) {
          sanitized[key] = '[REDACTED]';
        } else if (typeof value === 'object') {
          sanitized[key] = sanitizeObject(value);
        } else {
          sanitized[key] = value;
        }
      }
      
      return sanitized;
    };
    
    return sanitizeObject(data);
  }
}
```

## Testing and Validation

### Unit Testing

```javascript
// Test framework
class MCPTestRunner {
  constructor(server) {
    this.server = server;
    this.tests = [];
    this.results = [];
  }
  
  addTest(name, testFunction) {
    this.tests.push({ name, testFunction });
  }
  
  async runTests() {
    console.log('Running MCP Server Tests...\n');
    
    for (const test of this.tests) {
      try {
        console.log(`Running test: ${test.name}`);
        const result = await test.function();
        
        this.results.push({
          name: test.name,
          status: 'passed',
          result,
          error: null
        });
        
        console.log(`✅ ${test.name} - PASSED\n`);
      } catch (error) {
        this.results.push({
          name: test.name,
          status: 'failed',
          result: null,
          error: error.message
        });
        
        console.log(`❌ ${test.name} - FAILED: ${error.message}\n`);
      }
    }
    
    this.printSummary();
  }
  
  printSummary() {
    const passed = this.results.filter(r => r.status === 'passed').length;
    const failed = this.results.filter(r => r.status === 'failed').length;
    
    console.log('Test Summary:');
    console.log(`Total: ${this.results.length}`);
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Success Rate: ${((passed / this.results.length) * 100).toFixed(2)}%`);
  }
}

// Test examples
const testRunner = new MCPTestRunner(server);

// Tool tests
testRunner.addTest('List Tools', async () => {
  const request = { method: 'tools/list' };
  const response = await server.request(request);
  
  if (!response.tools || !Array.isArray(response.tools)) {
    throw new Error('Invalid tools response');
  }
  
  return { toolCount: response.tools.length };
});

testRunner.addTest('Call Compliance Scan Tool', async () => {
  const request = {
    method: 'tools/call',
    params: {
      name: 'compliance-scan',
      arguments: {
        framework: 'CIS',
        scope: 'all',
        severityThreshold: 'medium'
      }
    }
  };
  
  const response = await server.request(request);
  
  if (response.isError) {
    throw new Error(`Tool call failed: ${response.error.message}`);
  }
  
  return { success: true };
});

// Resource tests
testRunner.addTest('List Resources', async () => {
  const request = { method: 'resources/list' };
  const response = await server.request(request);
  
  if (!response.resources || !Array.isArray(response.resources)) {
    throw new Error('Invalid resources response');
  }
  
  return { resourceCount: response.resources.length };
});

// Prompt tests
testRunner.addTest('List Prompts', async () => {
  const request = { method: 'prompts/list' };
  const response = await server.request(request);
  
  if (!response.prompts || !Array.isArray(response.prompts)) {
    throw new Error('Invalid prompts response');
  }
  
  return { promptCount: response.prompts.length };
});

// Run tests
testRunner.runTests();
```

### Integration Testing

```javascript
// Integration test suite
class IntegrationTestSuite {
  constructor(server) {
    this.server = server;
    this.testData = {};
  }
  
  async setup() {
    // Setup test environment
    console.log('Setting up integration test environment...');
    
    // Create test data
    this.testData = {
      testAccount: '123456789012',
      testRegion: 'us-east-1',
      testFramework: 'CIS'
    };
    
    console.log('Integration test environment ready');
  }
  
  async teardown() {
    // Cleanup test environment
    console.log('Cleaning up integration test environment...');
    
    // Clean up test data
    this.testData = {};
    
    console.log('Integration test environment cleaned up');
  }
  
  async runIntegrationTests() {
    await this.setup();
    
    try {
      await this.testComplianceWorkflow();
      await this.testResourceWorkflow();
      await this.testPromptWorkflow();
      
      console.log('All integration tests passed');
    } finally {
      await this.teardown();
    }
  }
  
  async testComplianceWorkflow() {
    console.log('Testing compliance workflow...');
    
    // Step 1: List available tools
    const toolsResponse = await this.server.request({
      method: 'tools/list'
    });
    
    // Step 2: Call compliance scan
    const scanResponse = await this.server.request({
      method: 'tools/call',
      params: {
        name: 'compliance-scan',
        arguments: {
          framework: this.testData.testFramework,
          scope: 'aws',
          accounts: [this.testData.testAccount],
          severityThreshold: 'medium'
        }
      }
    });
    
    if (scanResponse.isError) {
      throw new Error(`Compliance scan failed: ${scanResponse.error.message}`);
    }
    
    // Step 3: Verify scan results
    const scanResult = JSON.parse(scanResponse.content[0].text);
    
    if (!scanResult.id || !scanResult.findings) {
      throw new Error('Invalid scan result format');
    }
    
    console.log('✅ Compliance workflow test passed');
  }
  
  async testResourceWorkflow() {
    console.log('Testing resource workflow...');
    
    // Step 1: List available resources
    const resourcesResponse = await this.server.request({
      method: 'resources/list'
    });
    
    // Step 2: Read configuration resource
    const configResponse = await this.server.request({
      method: 'resources/read',
      params: {
        uri: 'config://compliance/settings'
      }
    });
    
    if (!configResponse.contents || configResponse.contents.length === 0) {
      throw new Error('No resource content returned');
    }
    
    const config = JSON.parse(configResponse.contents[0].text);
    
    if (!config.frameworks || !Array.isArray(config.frameworks)) {
      throw new Error('Invalid configuration format');
    }
    
    console.log('✅ Resource workflow test passed');
  }
  
  async testPromptWorkflow() {
    console.log('Testing prompt workflow...');
    
    // Step 1: List available prompts
    const promptsResponse = await this.server.request({
      method: 'prompts/list'
    });
    
    // Step 2: Get compliance analysis prompt
    const promptResponse = await this.server.request({
      method: 'prompts/get',
      params: {
        name: 'compliance-analysis',
        arguments: {
          findings_summary: 'Test findings summary',
          framework: 'CIS',
          severity_threshold: 'medium'
        }
      }
    });
    
    if (!promptResponse.messages || promptResponse.messages.length === 0) {
      throw new Error('No prompt messages returned');
    }
    
    const message = promptResponse.messages[0];
    
    if (!message.content || !message.content.text) {
      throw new Error('Invalid prompt message format');
    }
    
    console.log('✅ Prompt workflow test passed');
  }
}

// Run integration tests
const integrationSuite = new IntegrationTestSuite(server);
integrationSuite.runIntegrationTests();
```

## Performance Optimization

### Caching Strategy

```javascript
// Advanced caching system
class CacheManager {
  constructor(options = {}) {
    this.cache = new Map();
    this.ttl = options.ttl || 300000; // 5 minutes default
    this.maxSize = options.maxSize || 1000;
    this.stats = {
      hits: 0,
      misses: 0,
      evictions: 0
    };
  }
  
  set(key, value, ttl = this.ttl) {
    // Check if eviction is needed
    if (this.cache.size >= this.maxSize) {
      this.evictOldest();
    }
    
    const item = {
      value,
      timestamp: Date.now(),
      ttl,
      accessCount: 0,
      lastAccessed: Date.now()
    };
    
    this.cache.set(key, item);
  }
  
  get(key) {
    const item = this.cache.get(key);
    
    if (!item) {
      this.stats.misses++;
      return null;
    }
    
    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }
    
    // Update access statistics
    item.accessCount++;
    item.lastAccessed = Date.now();
    this.stats.hits++;
    
    return item.value;
  }
  
  evictOldest() {
    let oldestKey = null;
    let oldestTime = Date.now();
    
    for (const [key, item] of this.cache.entries()) {
      if (item.lastAccessed < oldestTime) {
        oldestTime = item.lastAccessed;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.stats.evictions++;
    }
  }
  
  clear() {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, evictions: 0 };
  }
  
  getStats() {
    const total = this.stats.hits + this.stats.misses;
    return {
      ...this.stats,
      hitRate: total > 0 ? (this.stats.hits / total) * 100 : 0,
      size: this.cache.size
    };
  }
}

// Cache middleware
const cacheMiddleware = (cacheManager, ttl) => {
  return async (operation, ...args) => {
    const cacheKey = `${operation.name}:${JSON.stringify(args)}`;
    
    // Try cache first
    const cached = cacheManager.get(cacheKey);
    if (cached !== null) {
      return cached;
    }
    
    // Execute operation
    const result = await operation(...args);
    
    // Cache result
    cacheManager.set(cacheKey, result, ttl);
    
    return result;
  };
};
```

### Connection Pooling

```javascript
// Connection pool for external APIs
class ConnectionPool {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 10;
    this.minSize = options.minSize || 2;
    this.idleTimeout = options.idleTimeout || 30000;
    this.createConnection = options.createConnection;
    this.destroyConnection = options.destroyConnection;
    
    this.pool = [];
    this.activeConnections = 0;
    this.waitingQueue = [];
  }
  
  async acquire() {
    // Try to get from pool
    if (this.pool.length > 0) {
      const connection = this.pool.pop();
      this.activeConnections++;
      return connection;
    }
    
    // Create new connection if under limit
    if (this.activeConnections < this.maxSize) {
      const connection = await this.createConnection();
      this.activeConnections++;
      return connection;
    }
    
    // Wait for available connection
    return new Promise((resolve, reject) => {
      this.waitingQueue.push({ resolve, reject });
    });
  }
  
  release(connection) {
    this.activeConnections--;
    
    // Check if someone is waiting
    if (this.waitingQueue.length > 0) {
      const waiter = this.waitingQueue.shift();
      this.activeConnections++;
      waiter.resolve(connection);
      return;
    }
    
    // Return to pool if under max size
    if (this.pool.length < this.maxSize - this.minSize) {
      this.pool.push(connection);
      return;
    }
    
    // Destroy excess connection
    this.destroyConnection(connection);
  }
  
  async destroy() {
    // Destroy all connections
    for (const connection of this.pool) {
      await this.destroyConnection(connection);
    }
    
    this.pool = [];
    this.activeConnections = 0;
    this.waitingQueue = [];
  }
}

// Usage with AWS SDK
const awsPool = new ConnectionPool({
  maxSize: 5,
  minSize: 1,
  createConnection: async () => {
    return new AWS.CloudWatch({
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      region: process.env.AWS_DEFAULT_REGION
    });
  },
  destroyConnection: async (connection) => {
    // AWS SDK doesn't need explicit cleanup
  }
});
```

### Performance Monitoring

```javascript
// Performance monitor
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      requestCount: 0,
      responseTime: [],
      errorCount: 0,
      activeConnections: 0,
      queueSize: 0
    };
    
    this.startMonitoring();
  }
  
  startMonitoring() {
    setInterval(() => {
      this.collectMetrics();
      this.reportMetrics();
    }, 60000); // Every minute
  }
  
  recordRequest(duration, isError = false) {
    this.metrics.requestCount++;
    this.metrics.responseTime.push(duration);
    
    if (isError) {
      this.metrics.errorCount++;
    }
    
    // Keep only last 1000 response times
    if (this.metrics.responseTime.length > 1000) {
      this.metrics.responseTime = this.metrics.responseTime.slice(-1000);
    }
  }
  
  collectMetrics() {
    const now = Date.now();
    
    // Calculate statistics
    const responseTimes = this.metrics.responseTime;
    const avgResponseTime = responseTimes.length > 0 
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length 
      : 0;
    
    const sortedTimes = responseTimes.sort((a, b) => a - b);
    const p95 = sortedTimes[Math.floor(sortedTimes.length * 0.95)] || 0;
    const p99 = sortedTimes[Math.floor(sortedTimes.length * 0.99)] || 0;
    
    return {
      timestamp: now,
      requestCount: this.metrics.requestCount,
      errorCount: this.metrics.errorCount,
      errorRate: this.metrics.requestCount > 0 
        ? (this.metrics.errorCount / this.metrics.requestCount) * 100 
        : 0,
      avgResponseTime,
      p95ResponseTime: p95,
      p99ResponseTime: p99,
      activeConnections: this.metrics.activeConnections,
      queueSize: this.metrics.queueSize
    };
  }
  
  reportMetrics() {
    const metrics = this.collectMetrics();
    
    console.log('Performance Metrics:', JSON.stringify(metrics, null, 2));
    
    // Send to monitoring system
    if (process.env.METRICS_ENDPOINT) {
      this.sendMetrics(metrics);
    }
  }
  
  sendMetrics(metrics) {
    // Send to external monitoring system
    fetch(process.env.METRICS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(metrics)
    }).catch(error => {
      console.error('Failed to send metrics:', error);
    });
  }
}

// Performance middleware
const performanceMiddleware = (monitor) => {
  return async (operation, ...args) => {
    const startTime = Date.now();
    let isError = false;
    
    try {
      const result = await operation(...args);
      return result;
    } catch (error) {
      isError = true;
      throw error;
    } finally {
      const duration = Date.now() - startTime;
      monitor.recordRequest(duration, isError);
    }
  };
};
```

---

## Conclusion

This comprehensive MCP Server Implementation Guide provides the foundation for building robust, secure, and performant MCP servers that power the AI Agent Skills. The patterns and examples shown here can be adapted and extended to create custom MCP servers for specific use cases.

Key takeaways:
1. Follow standardized patterns for consistency
2. Implement comprehensive error handling and logging
3. Use security best practices for authentication and data protection
4. Optimize performance with caching and connection pooling
5. Test thoroughly with unit and integration tests
6. Monitor performance and health metrics continuously

For specific implementation details, refer to the individual MCP server source code in the `.claude/mcp-servers/` directory.
