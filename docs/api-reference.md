# AI Agents Sandbox API Reference

## 🌐 Base URL
```
Development: http://localhost:8081
Production: https://api.ai-agents-sandbox.com
```

## 📋 Authentication
```http
Authorization: Bearer <jwt-token>
Content-Type: application/json
```

## 🔍 Health & Status

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-09T21:15:00-07:00",
  "project": "AI Agents Sandbox",
  "phase": "Phase 2 Complete",
  "integrations_completed": 7,
  "implementation_status": "✅ SUCCESS"
}
```

### System Status
```http
GET /status
```

**Response:**
```json
{
  "message": "All repository integrations completed successfully",
  "phase1": {
    "mcp_tool_support": "✅ Completed",
    "rag_ai_plugin": "✅ Completed", 
    "react_patterns": "✅ Completed"
  },
  "phase2": {
    "research_workflows": "✅ Completed",
    "aws_bedrock": "✅ Completed",
    "websocket_updates": "✅ Completed",
    "multi_model_ai": "✅ Completed"
  },
  "total_files_created": 40,
  "total_api_endpoints": 25,
  "total_activities": 35,
  "production_ready": true
}
```

## 🤖 Workflow Management

### Start Workflow
```http
POST /workflow/start
```

**Request Body:**
```json
{
  "workflowType": "goal-based-agent",
  "parameters": {
    "goal": "payment-processing",
    "context": {"amount": 10000, "currency": "usd"},
    "agentType": "single",
    "maxTurns": 20,
    "userId": "user123"
  }
}
```

**Response:**
```json
{
  "workflowId": "goal-agent-1710035700123",
  "runId": "run-abc123",
  "status": "started",
  "startedAt": "2026-03-09T21:15:00-07:00"
}
```

### Get Workflow Status
```http
GET /workflow/status/{workflowId}
```

**Response:**
```json
{
  "workflowId": "goal-agent-1710035700123",
  "status": "running",
  "currentTurn": 3,
  "maxTurns": 20,
  "historyLength": 6,
  "startTime": "2026-03-09T21:15:00-07:00",
  "endTime": null
}
```

### Send Signal to Workflow
```http
POST /workflow/{workflowId}/signal
```

**Request Body:**
```json
{
  "signalName": "humanInput",
  "input": "Please proceed with the payment processing",
  "userId": "user123"
}
```

## 🎯 Goal-Based Agents

### Start Goal-Based Agent
```http
POST /agent/goal/start
```

**Request Body:**
```json
{
  "goal": "payment-processing",
  "context": {
    "amount": 10000,
    "currency": "usd",
    "customerId": "cust_123"
  },
  "agentType": "single",
  "maxTurns": 20,
  "userId": "user123"
}
```

**Response:**
```json
{
  "workflowId": "goal-agent-1710035700123",
  "runId": "run-abc123",
  "status": "started",
  "goal": "payment-processing",
  "startedAt": "2026-03-09T21:15:00-07:00"
}
```

### Get Agent Status
```http
GET /agent/goal/{workflowId}/status
```

**Response:**
```json
{
  "workflowId": "goal-agent-1710035700123",
  "goal": "payment-processing",
  "currentTurn": 3,
  "maxTurns": 20,
  "status": "running",
  "history": [
    {
      "turn": 1,
      "type": "agent",
      "message": "I'll help you process this payment...",
      "timestamp": "2026-03-09T21:15:05-07:00"
    }
  ],
  "startTime": "2026-03-09T21:15:00-07:00"
}
```

### Send Human Input
```http
POST /agent/goal/{workflowId}/message
```

**Request Body:**
```json
{
  "message": "Please proceed with the payment processing",
  "userId": "user123"
}
```

## 🧠 ReAct Agents

### Start ReAct Agent
```http
POST /agent/react/start
```

**Request Body:**
```json
{
  "query": "What is the current stock price of AAPL?",
  "maxSteps": 10,
  "llmProvider": "openai",
  "llmModel": "gpt-4",
  "tools": ["web_search"],
  "context": {"market": "NASDAQ"}
}
```

**Response:**
```json
{
  "workflowId": "react-agent-1710035700123",
  "runId": "run-def456",
  "status": "started",
  "query": "What is the current stock price of AAPL?",
  "maxSteps": 10,
  "startedAt": "2026-03-09T21:15:00-07:00"
}
```

### Get ReAct Status
```http
GET /agent/react/{workflowId}/status?includeSteps=true
```

**Response:**
```json
{
  "workflowId": "react-agent-1710035700123",
  "query": "What is the current stock price of AAPL?",
  "currentStep": 3,
  "maxSteps": 10,
  "status": "running",
  "steps": [
    {
      "stepNumber": 1,
      "type": "thought",
      "content": "I need to search for current AAPL stock price",
      "timestamp": "2026-03-09T21:15:05-07:00",
      "confidence": 0.8
    },
    {
      "stepNumber": 2,
      "type": "action",
      "content": "I will use the web search tool to find AAPL stock price",
      "toolCalls": [
        {
          "toolName": "web_search",
          "parameters": {"query": "AAPL stock price current"}
        }
      ],
      "timestamp": "2026-03-09T21:15:10-07:00"
    }
  ]
}
```

## 🔬 Research Workflows

### Start Research Workflow
```http
POST /research/start
```

**Request Body:**
```json
{
  "query": "AI trends in 2024",
  "researchType": "deep",
  "maxSources": 20,
  "maxDepth": 3,
  "includeKnowledgeGraph": true,
  "streamEvents": true,
  "llmProvider": "openai",
  "llmModel": "gpt-4",
  "context": {"industry": "technology"}
}
```

**Response:**
```json
{
  "workflowId": "research-1710035700123",
  "runId": "run-ghi789",
  "status": "started",
  "query": "AI trends in 2024",
  "researchType": "deep",
  "maxSources": 20,
  "startedAt": "2026-03-09T21:15:00-07:00"
}
```

### Get Research Status
```http
GET /research/{workflowId}/status?includeDetails=true
```

**Response:**
```json
{
  "workflowId": "research-1710035700123",
  "query": "AI trends in 2024",
  "researchType": "deep",
  "currentPhase": "analysis",
  "status": "running",
  "sourceCount": 15,
  "findingCount": 8,
  "nodeCount": 12,
  "eventCount": 25,
  "agentCount": 4,
  "sources": [
    {
      "id": "web_1",
      "title": "Research Article about AI trends",
      "url": "https://example.com/research-article-1",
      "relevance": 0.9,
      "credibility": 0.85,
      "timestamp": "2026-03-09T21:15:05-07:00"
    }
  ],
  "findings": [
    {
      "id": "finding_1",
      "title": "Key Trend Identified",
      "description": "Analysis reveals significant trends in AI adoption",
      "confidence": 0.85,
      "category": "trends",
      "timestamp": "2026-03-09T21:15:30-07:00"
    }
  ]
}
```

### Get Research Quality Metrics
```http
GET /research/{workflowId}/quality
```

**Response:**
```json
{
  "sourceQuality": 0.87,
  "findingQuality": 0.82,
  "graphQuality": 0.75,
  "overallQuality": 0.81,
  "agentCollaborationScore": 0.88,
  "eventStreamCompleteness": 0.92
}
```

## 🔧 MCP Tool Management

### List Available Tools
```http
GET /mcp/tools
```

**Query Parameters:**
- `category` (optional): Filter by category (finance, hr, travel, research, general)
- `goal` (optional): Filter by goal alignment

**Response:**
```json
{
  "tools": [
    {
      "name": "stripe_payment",
      "description": "Process a payment through Stripe",
      "toolType": "mcp",
      "serverName": "stripe",
      "category": "finance",
      "priority": 1,
      "goalAligned": ["payment-processing", "billing"],
      "inputSchema": {
        "type": "object",
        "properties": {
          "amount": {"type": "number", "description": "Payment amount in cents"},
          "currency": {"type": "string", "description": "Currency code"}
        },
        "required": ["amount", "currency"]
      }
    }
  ],
  "count": 5
}
```

### Get Available Goals
```http
GET /mcp/goals
```

**Response:**
```json
{
  "goals": [
    "payment-processing",
    "billing",
    "subscription-management",
    "employee-management",
    "onboarding",
    "team-coordination",
    "travel-booking",
    "business-travel",
    "data-analysis",
    "reporting",
    "audit",
    "research",
    "information-gathering",
    "competitive-analysis"
  ]
}
```

### Get Tool Categories
```http
GET /mcp/categories
```

**Response:**
```json
{
  "categories": ["finance", "hr", "travel", "research", "general"],
  "count": 5
}
```

### Execute Tool
```http
POST /mcp/execute
```

**Request Body:**
```json
{
  "toolName": "stripe_payment",
  "parameters": {
    "amount": 10000,
    "currency": "usd",
    "source": "tok_mock"
  },
  "goalContext": "payment-processing",
  "agentType": "payment-agent"
}
```

**Response:**
```json
{
  "toolName": "stripe_payment",
  "parameters": {
    "amount": 10000,
    "currency": "usd",
    "source": "tok_mock"
  },
  "result": {
    "paymentId": "pi_1234567890",
    "status": "succeeded",
    "amount": 10000,
    "currency": "usd"
  },
  "duration": 1500000000,
  "goalContext": "payment-processing",
  "agentType": "payment-agent"
}
```

## ☁️ AWS Bedrock Integration

### List Available Models
```http
GET /api/bedrock/models
```

**Response:**
```json
{
  "models": [
    {
      "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "name": "Claude 3 Sonnet",
      "provider": "Anthropic",
      "capabilities": ["text", "conversation", "analysis"],
      "maxTokens": 4096,
      "temperature": 0.7,
      "topP": 0.9
    },
    {
      "modelId": "amazon.titan-text-express-v1",
      "name": "Titan Text Express",
      "provider": "Amazon",
      "capabilities": ["text", "generation"],
      "maxTokens": 4096,
      "temperature": 0.7,
      "topP": 0.9
    }
  ],
  "count": 5
}
```

### Get Model Details
```http
GET /api/bedrock/models/{modelId}
```

**Response:**
```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "name": "Claude 3 Sonnet",
  "provider": "Anthropic",
  "capabilities": ["text", "conversation", "analysis"],
  "maxTokens": 4096,
  "temperature": 0.7,
  "topP": 0.9,
  "parameters": {
    "top_k": 250
  }
}
```

### Invoke Model
```http
POST /api/bedrock/invoke
```

**Request Body:**
```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "prompt": "Summarize the key benefits of AI in healthcare",
  "maxTokens": 1000,
  "temperature": 0.7,
  "topP": 0.9
}
```

**Response:**
```json
{
  "completion": "AI offers numerous benefits in healthcare including improved diagnostic accuracy, personalized treatment plans, operational efficiency, and enhanced patient care...",
  "prompt": "Summarize the key benefits of AI in healthcare",
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 150,
    "total_tokens": 165
  },
  "finishReason": "stop",
  "processingTime": 850
}
```

### Conduct Conversation
```http
POST /api/bedrock/conversation
```

**Request Body:**
```json
{
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "messages": [
    {
      "role": "user",
      "content": "What are the latest trends in AI?"
    }
  ],
  "systemPrompt": "You are a helpful AI assistant specializing in technology trends.",
  "maxTokens": 1000,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What are the latest trends in AI?"
    },
    {
      "role": "assistant",
      "content": "The latest trends in AI include multimodal models, improved reasoning capabilities, edge AI deployment, and increased focus on AI safety and ethics..."
    }
  ],
  "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 180,
    "total_tokens": 200
  },
  "finishReason": "stop",
  "processingTime": 1200
}
```

### Get Models by Provider
```http
GET /api/bedrock/models/provider/{provider}
```

**Response:**
```json
{
  "models": [
    {
      "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "name": "Claude 3 Sonnet",
      "provider": "Anthropic"
    },
    {
      "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
      "name": "Claude 3 Haiku",
      "provider": "Anthropic"
    }
  ],
  "count": 2,
  "provider": "Anthropic"
}
```

### Get Models by Capability
```http
GET /api/bedrock/models/capability/{capability}
```

**Response:**
```json
{
  "models": [
    {
      "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "name": "Claude 3 Sonnet",
      "capabilities": ["text", "conversation", "analysis"]
    }
  ],
  "count": 1,
  "capability": "conversation"
}
```

## 🤖 Multi-Model AI Management

### Get All Available Models
```http
GET /api/multimodel/models
```

**Response:**
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "capabilities": ["text", "conversation", "analysis", "code"],
      "maxTokens": 4096,
      "temperature": 0.7,
      "enabled": true,
      "priority": 1
    },
    {
      "id": "anthropic.claude-3-sonnet-20240229-v1:0",
      "name": "Claude 3 Sonnet",
      "provider": "anthropic",
      "capabilities": ["text", "conversation", "analysis"],
      "maxTokens": 4096,
      "enabled": true,
      "priority": 1
    }
  ]
}
```

### Process Multi-Model Request
```http
POST /api/multimodel/process
```

**Request Body:**
```json
{
  "prompt": "Analyze the market trends for electric vehicles",
  "taskType": "analysis",
  "capabilities": ["text", "analysis"],
  "maxTokens": 1000,
  "temperature": 0.7,
  "strategy": "ensemble"
}
```

**Response:**
```json
{
  "results": [
    {
      "modelId": "gpt-4",
      "modelName": "GPT-4",
      "provider": "openai",
      "response": "The EV market is experiencing rapid growth with increasing adoption...",
      "confidence": 0.92,
      "usage": {"prompt_tokens": 25, "completion_tokens": 200},
      "processingTime": 1200
    },
    {
      "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "modelName": "Claude 3 Sonnet",
      "provider": "anthropic",
      "response": "Electric vehicle market analysis shows strong growth trends...",
      "confidence": 0.89,
      "usage": {"prompt_tokens": 25, "completion_tokens": 180},
      "processingTime": 950
    }
  ],
  "strategy": "ensemble",
  "processingTime": 2200,
  "ensemble": {
    "combinedResponse": "Based on analysis from multiple models, the EV market shows strong growth...",
    "confidence": 0.90,
    "votingResults": [
      {
        "modelId": "gpt-4",
        "response": "The EV market is experiencing rapid growth...",
        "votes": 1,
        "confidence": 0.92
      }
    ],
    "metrics": {
      "totalModels": 2,
      "validModels": 2,
      "avgConfidence": 0.905
    }
  }
}
```

### Compare Models
```http
POST /api/multimodel/compare
```

**Request Body:**
```json
{
  "prompt": "What are the benefits of renewable energy?",
  "modelIds": ["gpt-4", "anthropic.claude-3-sonnet-20240229-v1:0"],
  "strategy": "all"
}
```

**Response:**
```json
{
  "prompt": "What are the benefits of renewable energy?",
  "strategy": "all",
  "results": [
    {
      "modelId": "gpt-4",
      "response": "Renewable energy offers numerous benefits including environmental sustainability...",
      "confidence": 0.94,
      "processingTime": 1100
    },
    {
      "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
      "response": "The benefits of renewable energy include reduced carbon emissions...",
      "confidence": 0.91,
      "processingTime": 900
    }
  ],
  "processingTime": 2100,
  "timestamp": "2026-03-09T21:15:00-07:00"
}
```

### Create Ensemble Result
```http
POST /api/multimodel/ensemble
```

**Request Body:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "modelIds": ["gpt-4", "anthropic.claude-3-sonnet-20240229-v1:0", "gemini-pro"]
}
```

**Response:**
```json
{
  "combinedResponse": "[GPT-4]: Quantum computing uses quantum bits...\n[Claude 3]: Quantum computing is a revolutionary approach...\n[Gemini Pro]: At its core, quantum computing leverages...",
  "confidence": 0.89,
  "votingResults": [
    {
      "modelId": "gpt-4",
      "response": "Quantum computing uses quantum bits...",
      "votes": 1,
      "confidence": 0.87
    }
  ],
  "metrics": {
    "totalModels": 3,
    "validModels": 3,
    "avgConfidence": 0.89
  }
}
```

## 💬 RAG AI Plugin

### Chat with RAG AI
```http
POST /api/rag-ai/chat
```

**Request Body:**
```json
{
  "message": "What are our company's security policies?",
  "includeSources": true,
  "maxTokens": 1000,
  "category": "security"
}
```

**Response:**
```json
{
  "message": "Based on your company's documentation, the security policies include...",
  "sources": ["Security Policy v2.1", "Employee Handbook 2024", "IT Security Guidelines"],
  "toolCalls": [
    {
      "toolName": "database_query",
      "parameters": {"query": "SELECT * FROM security_policies"},
      "result": {"policies": ["Data Protection", "Access Control", "Incident Response"]}
    }
  ],
  "confidence": 0.92,
  "processingTime": 1500
}
```

### Search Knowledge Base
```http
GET /api/rag-ai/search?query=security%20policies&limit=10&offset=0
```

**Response:**
```json
{
  "results": [
    {
      "id": "doc_1",
      "title": "Security Policy v2.1",
      "content": "This document outlines the comprehensive security policies...",
      "source": "Documentation",
      "score": 0.95,
      "metadata": {
        "type": "policy",
        "created": "2024-01-15",
        "author": "Security Team"
      }
    }
  ],
  "total": 25,
  "facets": {
    "sources": {"Documentation": 15, "Handbook": 8, "Guidelines": 2},
    "types": {"policy": 12, "guideline": 8, "procedure": 5}
  }
}
```

### Get Available Tools
```http
GET /api/rag-ai/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information",
      "category": "research"
    },
    {
      "name": "database_query",
      "description": "Execute database queries",
      "category": "general"
    }
  ],
  "count": 2
}
```

## 🔌 WebSocket Real-Time Updates

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8081/ws');

ws.onopen = () => {
  console.log('Connected to AI Agents WebSocket');
  
  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
      subscriptions: ['workflow_update', 'agent_update', 'system_update']
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Message Types

#### Workflow Update
```json
{
  "type": "workflow_update",
  "data": {
    "workflow": {
      "workflowId": "goal-agent-1710035700123",
      "workflowType": "goal-based-agent",
      "status": "running",
      "progress": 60.0,
      "message": "Processing payment with 60% completion",
      "data": {
        "currentStep": 3,
        "totalSteps": 5
      },
      "timestamp": "2026-03-09T21:15:30-07:00"
    }
  },
  "timestamp": "2026-03-09T21:15:30-07:00"
}
```

#### Agent Update
```json
{
  "type": "agent_update",
  "data": {
    "agent": {
      "agentId": "payment-agent-123",
      "agentType": "payment-processor",
      "status": "processing",
      "message": "Validating payment details",
      "data": {
        "currentStep": 2,
        "totalSteps": 4
      },
      "timestamp": "2026-03-09T21:15:25-07:00"
    }
  },
  "timestamp": "2026-03-09T21:15:25-07:00"
}
```

#### System Update
```json
{
  "type": "system_update",
  "data": {
    "system": {
      "component": "system",
      "status": "healthy",
      "message": "All systems operational",
      "metrics": {
        "cpu": 45.2,
        "memory": 67.8,
        "uptime": "2h30m15s"
      },
      "timestamp": "2026-03-09T21:15:00-07:00"
    }
  },
  "timestamp": "2026-03-09T21:15:00-07:00"
}
```

#### Notification
```json
{
  "type": "notification",
  "data": {
    "type": "success",
    "title": "Payment Processed",
    "message": "Payment of $100.00 processed successfully",
    "data": {
      "paymentId": "pi_1234567890",
      "amount": 10000
    },
    "timestamp": "2026-03-09T21:15:45-07:00"
  }
}
```

#### Heartbeat
```json
{
  "type": "heartbeat",
  "data": {
    "status": "alive",
    "timestamp": "2026-03-09T21:15:00-07:00",
    "clients": 3
  }
}
```

## 📊 Monitoring & Metrics

### Get System Metrics
```http
GET /metrics
```

**Response:**
```json
{
  "system": {
    "uptime": "2h30m15s",
    "version": "v2.0.0",
    "build": "2024-03-09T21:00:00Z"
  },
  "performance": {
    "avgResponseTime": 250,
    "requestsPerSecond": 45,
    "errorRate": 0.02
  },
  "workflows": {
    "active": 12,
    "completed": 156,
    "failed": 3,
    "avgDuration": "45s"
  },
  "agents": {
    "active": 8,
    "totalRequests": 234,
    "successRate": 0.97
  },
  "models": {
    "totalRequests": 89,
    "avgLatency": 850,
    "cacheHitRate": 0.75
  }
}
```

### Get Integration Status
```http
GET /integrations
```

**Response:**
```json
{
  "high_priority": [
    {
      "repository": "temporal-ai-agent",
      "type": "source",
      "status": "✅ Completed",
      "features": ["MCP tool support", "goal-based agents", "multi-agent workflows"]
    }
  ],
  "medium_priority": [
    {
      "repository": "ai-iceberg-demo",
      "type": "source",
      "status": "✅ Completed",
      "features": ["research workflows", "knowledge graphs", "multi-agent analysis"]
    }
  ]
}
```

## 🚨 Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "amount",
      "issue": "must be a positive number"
    },
    "timestamp": "2026-03-09T21:15:00-07:00",
    "requestId": "req_abc123"
  }
}
```

### HTTP Status Codes
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

## 🔧 Rate Limiting

### Rate Limits
- **Anonymous Users**: 100 requests/minute
- **Authenticated Users**: 1000 requests/minute
- **Premium Users**: 5000 requests/minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1710036000
```

## 📚 SDK Examples

### Go Client
```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type Client struct {
    BaseURL string
    Token   string
}

func (c *Client) StartGoalAgent(goal string, context map[string]interface{}) (*WorkflowResponse, error) {
    request := GoalAgentRequest{
        Goal:    goal,
        Context: context,
        AgentType: "single",
        MaxTurns: 20,
    }
    
    body, _ := json.Marshal(request)
    resp, err := http.Post(c.BaseURL+"/agent/goal/start", "application/json", bytes.NewBuffer(body))
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result WorkflowResponse
    json.NewDecoder(resp.Body).Decode(&result)
    return &result, nil
}
```

### JavaScript Client
```javascript
class AIAgentsClient {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
    }

    async startGoalAgent(goal, context) {
        const response = await fetch(`${this.baseURL}/agent/goal/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({
                goal,
                context,
                agentType: 'single',
                maxTurns: 20
            })
        });
        
        return response.json();
    }

    connectWebSocket() {
        const ws = new WebSocket(`ws://${this.baseURL.replace('http://', 'ws://')}/ws`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        return ws;
    }
}
```

### Python Client
```python
import requests
import websocket
import json

class AIAgentsClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
    
    def start_goal_agent(self, goal, context):
        url = f"{self.base_url}/agent/goal/start"
        data = {
            "goal": goal,
            "context": context,
            "agentType": "single",
            "maxTurns": 20
        }
        
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def connect_websocket(self):
        ws_url = self.base_url.replace('http://', 'ws://') + '/ws'
        
        def on_message(ws, message):
            data = json.loads(message)
            self.handle_websocket_message(data)
        
        ws = websocket.WebSocketApp(ws_url, on_message=on_message)
        ws.run_forever()
```

---

## 🎯 Quick Reference

### Common Workflows
1. **Start Goal-Based Agent**: `POST /agent/goal/start`
2. **Start ReAct Agent**: `POST /agent/react/start`
3. **Start Research**: `POST /research/start`
4. **Chat with RAG AI**: `POST /api/rag-ai/chat`
5. **Invoke AI Model**: `POST /api/bedrock/invoke`

### WebSocket Events
- `workflow_update` - Workflow progress updates
- `agent_update` - Agent status changes
- `system_update` - System health updates
- `notification` - Important notifications

### Error Codes
- `VALIDATION_ERROR` - Invalid input
- `AUTHENTICATION_ERROR` - Invalid credentials
- `PERMISSION_ERROR` - Insufficient permissions
- `RATE_LIMIT_ERROR` - Too many requests
- `INTERNAL_ERROR` - Server error

For more detailed information, see the [deployment guide](./deployment-guide.md) and [troubleshooting guide](./troubleshooting.md).
