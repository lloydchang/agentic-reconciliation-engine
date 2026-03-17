# Agent Integration and Testing Guide

## Overview

This guide documents the integration patterns, testing strategies, and validation procedures for independent AI agents, including inter-agent communication, system integration, and comprehensive testing methodologies.

## Table of Contents

1. [Integration Architecture](#integration-architecture)
2. [Agent Communication Patterns](#agent-communication-patterns)
3. [System Integration](#system-integration)
4. [Testing Strategies](#testing-strategies)
5. [Validation Procedures](#validation-procedures)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Performance Testing](#performance-testing)
8. [Troubleshooting Integration Issues](#troubleshooting-integration-issues)

## Integration Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Temporal   │  │   Memory    │  │   Independent Agents    │ │
│  │   Workers   │  │   Agents    │  │                         │ │
│  │             │  │             │  │ ┌─────────┐ ┌─────────┐ │ │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ │Cost Opt│ │Security│ │ │
│  │ │Worker 1 │ │  │ │Rust Mem│ │  │ │Agent   │ │Scanner │ │ │
│  │ │Worker 2 │ │  │ │Go Mem   │ │  │ └─────────┘ └─────────┘ │ │
│  │ │Worker N │ │  │ │Py Mem   │ │  │ ┌─────────────────────┐ │ │
│  │ └─────────┘ │  │ └─────────┘ │  │ │Swarm Coordinator    │ │ │
│  └─────────────┘  └─────────────┘  │ └─────────────────────┘ │
│                                   └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Kubernetes  │  │   Kind      │  │   Docker Registry      │ │
│  │   Cluster   │  │   Cluster   │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Monitoring & Observability                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Prometheus  │  │  Grafana    │  │   Dashboard API         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

#### 1. Memory Agent Integration
```yaml
# Environment variables for memory agent connection
env:
- name: MEMORY_AGENT_URL
  value: "http://agent-memory-rust:8080"
- name: LANGUAGE_PRIORITY
  value: "rust,go,python"
- name: BACKEND_PRIORITY
  value: "llama.cpp,ollama"
```

#### 2. Ollama Integration
```yaml
# Ollama service configuration
env:
- name: OLLAMA_URL
  value: "http://ollama-service:11434"
- name: MODEL
  value: "qwen2.5:0.5b"
```

#### 3. Temporal Integration
```yaml
# Temporal worker configuration
env:
- name: TEMPORAL_HOST_PORT
  value: "temporal-frontend:7233"
- name: TEMPORAL_NAMESPACE
  value: "default"
- name: TASK_QUEUE
  value: "gitops-temporal"
```

## Agent Communication Patterns

### 1. HTTP API Communication

#### Agent-to-Agent API Calls
```go
// Example: Cost Optimizer calling Security Scanner
func callSecurityScanner() (*SecurityScanResult, error) {
    client := &http.Client{Timeout: 30 * time.Second}
    
    req, err := http.NewRequest("POST", 
        "http://security-scanner-service:8080/scan", 
        bytes.NewBuffer(scanRequest))
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }
    
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-Agent-ID", "cost-optimizer")
    
    resp, err := client.Do(req)
    if err != nil {
        return nil, fmt.Errorf("failed to call security scanner: %w", err)
    }
    defer resp.Body.Close()
    
    var result SecurityScanResult
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }
    
    return &result, nil
}
```

#### Service Discovery
```go
// Service discovery with health checking
func discoverHealthyAgents(agentType string) ([]string, error) {
    var healthyAgents []string
    
    // Query Kubernetes API for healthy pods
    pods, err := clientset.CoreV1().Pods("ai-infrastructure").List(context.TODO(),
        metav1.ListOptions{
            LabelSelector: fmt.Sprintf("agent-type=%s", agentType),
        })
    if err != nil {
        return nil, fmt.Errorf("failed to list pods: %w", err)
    }
    
    for _, pod := range pods.Items {
        if isPodHealthy(&pod) {
            serviceName := fmt.Sprintf("%s-service", agentType)
            healthyAgents = append(healthyAgents, 
                fmt.Sprintf("http://%s.%s.svc.cluster.local:8080", 
                    serviceName, "ai-infrastructure"))
        }
    }
    
    return healthyAgents, nil
}

func isPodHealthy(pod *v1.Pod) bool {
    for _, condition := range pod.Status.Conditions {
        if condition.Type == v1.PodReady && condition.Status == v1.ConditionTrue {
            return true
        }
    }
    return false
}
```

### 2. Message Queue Communication

#### Redis-based Message Queue
```go
// Message queue implementation
type MessageQueue struct {
    client *redis.Client
    ctx    context.Context
}

func (mq *MessageQueue) Publish(topic string, message interface{}) error {
    msgBytes, err := json.Marshal(message)
    if err != nil {
        return fmt.Errorf("failed to marshal message: %w", err)
    }
    
    return mq.client.LPush(mq.ctx, topic, msgBytes).Err()
}

func (mq *MessageQueue) Subscribe(topic string, handler func([]byte) error) error {
    for {
        result, err := mq.client.BRPop(mq.ctx, 0, topic).Result()
        if err != nil {
            return fmt.Errorf("failed to pop message: %w", err)
        }
        
        if err := handler([]byte(result.Val[1])); err != nil {
            log.Printf("Error handling message: %v", err)
        }
    }
}
```

#### Message Types
```go
// Agent coordination messages
type CoordinationMessage struct {
    Type      string                 `json:"type"`
    AgentID   string                 `json:"agent_id"`
    Timestamp time.Time              `json:"timestamp"`
    Payload   map[string]interface{} `json:"payload"`
}

// Swarm registration message
type SwarmRegistration struct {
    AgentID       string    `json:"agent_id"`
    AgentType     string    `json:"agent_type"`
    Capabilities  []string  `json:"capabilities"`
    HealthURL     string    `json:"health_url"`
    LastHeartbeat time.Time `json:"last_heartbeat"`
}
```

### 3. gRPC Communication

#### gRPC Service Definition
```protobuf
syntax = "proto3";

package agent;

service AgentService {
    rpc RegisterAgent(RegisterAgentRequest) returns (RegisterAgentResponse);
    rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
    rpc CoordinateTask(CoordinateTaskRequest) returns (CoordinateTaskResponse);
    rpc GetStatus(GetStatusRequest) returns (GetStatusResponse);
}

message RegisterAgentRequest {
    string agent_id = 1;
    string agent_type = 2;
    repeated string capabilities = 3;
    string health_endpoint = 4;
}

message RegisterAgentResponse {
    bool success = 1;
    string message = 2;
    string swarm_id = 3;
}
```

#### gRPC Client Implementation
```go
// gRPC client for agent communication
type AgentClient struct {
    conn   *grpc.ClientConn
    client agentpb.AgentServiceClient
}

func NewAgentClient(address string) (*AgentClient, error) {
    conn, err := grpc.Dial(address, grpc.WithInsecure())
    if err != nil {
        return nil, fmt.Errorf("failed to connect: %w", err)
    }
    
    return &AgentClient{
        conn:   conn,
        client: agentpb.NewAgentServiceClient(conn),
    }, nil
}

func (ac *AgentClient) RegisterAgent(req *agentpb.RegisterAgentRequest) (*agentpb.RegisterAgentResponse, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    
    return ac.client.RegisterAgent(ctx, req)
}
```

## System Integration

### 1. Memory Agent Integration

#### Memory Client Implementation
```go
// Memory agent client
type MemoryClient struct {
    baseURL string
    client  *http.Client
}

func (mc *MemoryClient) StoreMemory(ctx context.Context, memory *Memory) error {
    url := fmt.Sprintf("%s/api/memory", mc.baseURL)
    
    reqBody, err := json.Marshal(memory)
    if err != nil {
        return fmt.Errorf("failed to marshal memory: %w", err)
    }
    
    req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
    if err != nil {
        return fmt.Errorf("failed to create request: %w", err)
    }
    
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := mc.client.Do(req)
    if err != nil {
        return fmt.Errorf("failed to store memory: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("memory store failed with status: %d", resp.StatusCode)
    }
    
    return nil
}

func (mc *MemoryClient) RetrieveMemories(ctx context.Context, query string) ([]*Memory, error) {
    url := fmt.Sprintf("%s/api/memory/search?q=%s", mc.baseURL, url.QueryEscape(query))
    
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }
    
    resp, err := mc.client.Do(req)
    if err != nil {
        return nil, fmt.Errorf("failed to retrieve memories: %w", err)
    }
    defer resp.Body.Close()
    
    var memories []*Memory
    if err := json.NewDecoder(resp.Body).Decode(&memories); err != nil {
        return nil, fmt.Errorf("failed to decode memories: %w", err)
    }
    
    return memories, nil
}
```

#### Memory Types
```go
// Memory structure
type Memory struct {
    ID          string                 `json:"id"`
    AgentID     string                 `json:"agent_id"`
    Type        string                 `json:"type"`
    Content     string                 `json:"content"`
    Context     map[string]interface{} `json:"context"`
    Timestamp   time.Time              `json:"timestamp"`
    ExpiresAt   *time.Time             `json:"expires_at,omitempty"`
    Tags        []string               `json:"tags"`
    Priority    int                    `json:"priority"`
}

// Memory types
const (
    MemoryTypeObservation = "observation"
    MemoryTypeDecision     = "decision"
    MemoryTypeLearning     = "learning"
    MemoryTypeCoordination = "coordination"
)
```

### 2. Ollama Integration

#### Ollama Client
```go
// Ollama client for LLM inference
type OllamaClient struct {
    baseURL string
    client  *http.Client
}

func (oc *OllamaClient) Generate(ctx context.Context, prompt string, model string) (*GenerationResponse, error) {
    url := fmt.Sprintf("%s/api/generate", oc.baseURL)
    
    request := GenerationRequest{
        Model:  model,
        Prompt: prompt,
        Stream: false,
        Options: Options{
            Temperature: 0.7,
            TopP:        0.9,
            MaxTokens:   1000,
        },
    }
    
    reqBody, err := json.Marshal(request)
    if err != nil {
        return nil, fmt.Errorf("failed to marshal request: %w", err)
    }
    
    req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }
    
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := oc.client.Do(req)
    if err != nil {
        return nil, fmt.Errorf("failed to generate response: %w", err)
    }
    defer resp.Body.Close()
    
    var generation GenerationResponse
    if err := json.NewDecoder(resp.Body).Decode(&generation); err != nil {
        return nil, fmt.Errorf("failed to decode response: %w", err)
    }
    
    return &generation, nil
}

type GenerationRequest struct {
    Model    string  `json:"model"`
    Prompt   string  `json:"prompt"`
    Stream   bool    `json:"stream"`
    Options  Options `json:"options"`
}

type GenerationResponse struct {
    Model     string `json:"model"`
    Response  string `json:"response"`
    Done      bool   `json:"done"`
    CreatedAt int64  `json:"created_at"`
}

type Options struct {
    Temperature float64 `json:"temperature"`
    TopP        float64 `json:"top_p"`
    MaxTokens   int     `json:"num_predict"`
}
```

### 3. Dashboard Integration

#### Dashboard API Client
```go
// Dashboard API client
type DashboardClient struct {
    baseURL string
    client  *http.Client
    apiKey  string
}

func (dc *DashboardClient) ReportAgentStatus(ctx context.Context, status *AgentStatus) error {
    url := fmt.Sprintf("%s/api/agents/status", dc.baseURL)
    
    reqBody, err := json.Marshal(status)
    if err != nil {
        return fmt.Errorf("failed to marshal status: %w", err)
    }
    
    req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
    if err != nil {
        return fmt.Errorf("failed to create request: %w", err)
    }
    
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", dc.apiKey))
    
    resp, err := dc.client.Do(req)
    if err != nil {
        return fmt.Errorf("failed to report status: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("status report failed with status: %d", resp.StatusCode)
    }
    
    return nil
}

type AgentStatus struct {
    AgentID      string                 `json:"agent_id"`
    AgentType    string                 `json:"agent_type"`
    Status       string                 `json:"status"`
    Health       string                 `json:"health"`
    LastSeen     time.Time              `json:"last_seen"`
    Metrics      map[string]interface{} `json:"metrics"`
    Capabilities []string               `json:"capabilities"`
}
```

## Testing Strategies

### 1. Unit Testing

#### Agent Logic Tests
```go
// Example unit test for cost optimizer
func TestCostOptimization(t *testing.T) {
    optimizer := NewCostOptimizer()
    
    testCases := []struct {
        name     string
        request  *CostOptimizationRequest
        expected *CostOptimizationResponse
        wantErr  bool
    }{
        {
            name: "valid optimization request",
            request: &CostOptimizationRequest{
                CloudProvider: "aws",
                Region:        "us-west-2",
                Services:      []string{"ec2", "s3"},
                TimeRange:     "last-30-days",
            },
            expected: &CostOptimizationResponse{
                Recommendations: "Right-size EC2 instances",
                PotentialSavings: 25.5,
                ImplementationSteps: []string{
                    "Analyze current instance usage",
                    "Recommend new instance types",
                    "Implement gradual migration",
                },
            },
            wantErr: false,
        },
        {
            name: "invalid cloud provider",
            request: &CostOptimizationRequest{
                CloudProvider: "invalid",
                Region:        "us-west-2",
                Services:      []string{"ec2"},
                TimeRange:     "last-30-days",
            },
            expected: nil,
            wantErr:  true,
        },
    }
    
    for _, tc := range testCases {
        t.Run(tc.name, func(t *testing.T) {
            result, err := optimizer.OptimizeCosts(tc.request)
            
            if tc.wantErr {
                assert.Error(t, err)
                return
            }
            
            assert.NoError(t, err)
            assert.Equal(t, tc.expected.Recommendations, result.Recommendations)
            assert.InDelta(t, tc.expected.PotentialSavings, result.PotentialSavings, 0.1)
        })
    }
}
```

#### Memory Client Tests
```go
func TestMemoryClient_StoreAndRetrieve(t *testing.T) {
    // Setup test server
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch r.URL.Path {
        case "/api/memory":
            if r.Method == "POST" {
                w.WriteHeader(http.StatusOK)
                w.Write([]byte(`{"id": "test-memory-id"}`))
            }
        case "/api/memory/search":
            if r.Method == "GET" {
                memories := []*Memory{
                    {
                        ID:      "test-memory-id",
                        AgentID: "test-agent",
                        Type:    "observation",
                        Content: "test content",
                    },
                }
                json.NewEncoder(w).Encode(memories)
            }
        default:
            w.WriteHeader(http.StatusNotFound)
        }
    }))
    defer server.Close()
    
    client := NewMemoryClient(server.URL)
    
    // Test storing memory
    memory := &Memory{
        AgentID: "test-agent",
        Type:    "observation",
        Content: "test content",
    }
    
    err := client.StoreMemory(context.Background(), memory)
    assert.NoError(t, err)
    
    // Test retrieving memories
    memories, err := client.RetrieveMemories(context.Background(), "test")
    assert.NoError(t, err)
    assert.Len(t, memories, 1)
    assert.Equal(t, "test content", memories[0].Content)
}
```

### 2. Integration Testing

#### End-to-End Agent Communication
```go
func TestAgentCommunication(t *testing.T) {
    // Setup test environment
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    // Deploy agents
    err := testEnv.DeployAgent("cost-optimizer", costOptimizerConfig)
    assert.NoError(t, err)
    
    err = testEnv.DeployAgent("security-scanner", securityScannerConfig)
    assert.NoError(t, err)
    
    // Wait for agents to be ready
    err = testEnv.WaitForAgentReady("cost-optimizer", 60*time.Second)
    assert.NoError(t, err)
    
    err = testEnv.WaitForAgentReady("security-scanner", 60*time.Second)
    assert.NoError(t, err)
    
    // Test communication
    costOptimizerURL := testEnv.GetAgentServiceURL("cost-optimizer")
    
    // Send optimization request
    req := &CostOptimizationRequest{
        CloudProvider: "aws",
        Region:        "us-west-2",
        Services:      []string{"ec2", "s3"},
        TimeRange:     "last-30-days",
    }
    
    resp, err := http.Post(costOptimizerURL+"/optimize", "application/json", bytes.NewBuffer(json.Marshal(req)))
    assert.NoError(t, err)
    defer resp.Body.Close()
    
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var result CostOptimizationResponse
    err = json.NewDecoder(resp.Body).Decode(&result)
    assert.NoError(t, err)
    
    assert.NotEmpty(t, result.Recommendations)
    assert.Greater(t, result.PotentialSavings, 0.0)
}
```

#### Memory Agent Integration
```go
func TestMemoryAgentIntegration(t *testing.T) {
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    // Deploy memory agent
    err := testEnv.DeployAgent("agent-memory-rust", memoryAgentConfig)
    assert.NoError(t, err)
    
    err = testEnv.WaitForAgentReady("agent-memory-rust", 60*time.Second)
    assert.NoError(t, err)
    
    // Test memory operations
    memoryURL := testEnv.GetAgentServiceURL("agent-memory-rust")
    client := NewMemoryClient(memoryURL)
    
    // Store memory
    memory := &Memory{
        AgentID: "test-agent",
        Type:    "observation",
        Content: "test observation",
        Context: map[string]interface{}{
            "environment": "test",
            "timestamp":   time.Now(),
        },
    }
    
    err = client.StoreMemory(context.Background(), memory)
    assert.NoError(t, err)
    
    // Retrieve memory
    memories, err := client.RetrieveMemories(context.Background(), "test")
    assert.NoError(t, err)
    assert.Len(t, memories, 1)
    assert.Equal(t, "test observation", memories[0].Content)
}
```

### 3. Performance Testing

#### Load Testing Framework
```go
// Load testing for agent endpoints
func TestAgentLoad(t *testing.T) {
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    agentURL := testEnv.GetAgentServiceURL("cost-optimizer")
    
    // Load test configuration
    config := &LoadTestConfig{
        ConcurrentRequests: 50,
        TotalRequests:     1000,
        RequestInterval:   10 * time.Millisecond,
        Timeout:           30 * time.Second,
    }
    
    // Run load test
    results := runLoadTest(agentURL+"/health", config)
    
    // Assert performance requirements
    assert.Less(t, results.AverageResponseTime, 100*time.Millisecond)
    assert.Less(t, results.P95ResponseTime, 200*time.Millisecond)
    assert.Greater(t, results.SuccessRate, 0.99)
    assert.Less(t, results.ErrorRate, 0.01)
}

type LoadTestConfig struct {
    ConcurrentRequests int
    TotalRequests     int
    RequestInterval   time.Duration
    Timeout           time.Duration
}

type LoadTestResults struct {
    TotalRequests       int
    SuccessfulRequests int
    FailedRequests     int
    AverageResponseTime time.Duration
    P95ResponseTime    time.Duration
    SuccessRate        float64
    ErrorRate          float64
}
```

#### Memory Performance Tests
```go
func TestMemoryPerformance(t *testing.T) {
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    memoryURL := testEnv.GetAgentServiceURL("agent-memory-rust")
    client := NewMemoryClient(memoryURL)
    
    // Performance test configuration
    numMemories := 1000
    batchSize := 50
    
    start := time.Now()
    
    // Store memories in batches
    for i := 0; i < numMemories; i += batchSize {
        var batch []*Memory
        for j := 0; j < batchSize && i+j < numMemories; j++ {
            memory := &Memory{
                AgentID: fmt.Sprintf("agent-%d", i+j),
                Type:    "observation",
                Content: fmt.Sprintf("memory content %d", i+j),
            }
            batch = append(batch, memory)
        }
        
        // Store batch concurrently
        var wg sync.WaitGroup
        for _, memory := range batch {
            wg.Add(1)
            go func(mem *Memory) {
                defer wg.Done()
                err := client.StoreMemory(context.Background(), mem)
                assert.NoError(t, err)
            }(memory)
        }
        wg.Wait()
    }
    
    duration := time.Since(start)
    
    // Assert performance requirements
    assert.Less(t, duration, 30*time.Second) // Should complete within 30 seconds
    
    memoriesPerSecond := float64(numMemories) / duration.Seconds()
    assert.Greater(t, memoriesPerSecond, 50.0) // At least 50 memories/second
}
```

## Validation Procedures

### 1. Health Check Validation

#### Agent Health Endpoint
```go
// Health check validation
func validateAgentHealth(agentURL string) error {
    client := &http.Client{Timeout: 10 * time.Second}
    
    resp, err := client.Get(agentURL + "/health")
    if err != nil {
        return fmt.Errorf("health check failed: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("health check returned status: %d", resp.StatusCode)
    }
    
    var health HealthResponse
    if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
        return fmt.Errorf("failed to decode health response: %w", err)
    }
    
    if health.Status != "healthy" {
        return fmt.Errorf("agent is not healthy: %s", health.Status)
    }
    
    return nil
}

type HealthResponse struct {
    Status    string                 `json:"status"`
    Version   string                 `json:"version"`
    Timestamp time.Time              `json:"timestamp"`
    Checks    map[string]interface{} `json:"checks"`
}
```

#### Comprehensive Health Validation
```go
func validateSystemHealth() error {
    // Validate all agents
    agents := []string{
        "cost-optimizer-service",
        "security-scanner-service",
        "agent-swarm-coordinator-service",
        "agent-memory-rust",
        "ollama-service",
    }
    
    for _, agent := range agents {
        agentURL := fmt.Sprintf("http://%s.ai-infrastructure.svc.cluster.local:8080", agent)
        
        if err := validateAgentHealth(agentURL); err != nil {
            return fmt.Errorf("agent %s health validation failed: %w", agent, err)
        }
    }
    
    // Validate cluster health
    if err := validateClusterHealth(); err != nil {
        return fmt.Errorf("cluster health validation failed: %w", err)
    }
    
    return nil
}

func validateClusterHealth() error {
    // Check node status
    nodes, err := clientset.CoreV1().Nodes().List(context.TODO(), metav1.ListOptions{})
    if err != nil {
        return fmt.Errorf("failed to list nodes: %w", err)
    }
    
    for _, node := range nodes.Items {
        for _, condition := range node.Status.Conditions {
            if condition.Type == v1.NodeReady && condition.Status != v1.ConditionTrue {
                return fmt.Errorf("node %s is not ready", node.Name)
            }
        }
    }
    
    return nil
}
```

### 2. Functional Validation

#### Agent Functionality Tests
```go
func validateAgentFunctionality(agentType, agentURL string) error {
    switch agentType {
    case "cost-optimizer":
        return validateCostOptimizerFunctionality(agentURL)
    case "security-scanner":
        return validateSecurityScannerFunctionality(agentURL)
    case "swarm-coordinator":
        return validateSwarmCoordinatorFunctionality(agentURL)
    default:
        return fmt.Errorf("unknown agent type: %s", agentType)
    }
}

func validateCostOptimizerFunctionality(agentURL string) error {
    // Test optimization endpoint
    req := &CostOptimizationRequest{
        CloudProvider: "aws",
        Region:        "us-west-2",
        Services:      []string{"ec2"},
        TimeRange:     "last-30-days",
    }
    
    reqBody, err := json.Marshal(req)
    if err != nil {
        return fmt.Errorf("failed to marshal request: %w", err)
    }
    
    resp, err := http.Post(agentURL+"/optimize", "application/json", bytes.NewBuffer(reqBody))
    if err != nil {
        return fmt.Errorf("failed to call optimize endpoint: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("optimize endpoint returned status: %d", resp.StatusCode)
    }
    
    var result CostOptimizationResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return fmt.Errorf("failed to decode response: %w", err)
    }
    
    // Validate response structure
    if result.Recommendations == "" {
        return fmt.Errorf("empty recommendations received")
    }
    
    if result.PotentialSavings <= 0 {
        return fmt.Errorf("invalid potential savings: %f", result.PotentialSavings)
    }
    
    return nil
}
```

### 3. Integration Validation

#### End-to-End Workflow Validation
```go
func validateEndToEndWorkflow() error {
    // Setup test scenario
    scenario := &TestScenario{
        Name: "cost-optimization-workflow",
        Steps: []TestStep{
            {
                Name:        "deploy-agents",
                Description: "Deploy all required agents",
                Action:      deployTestAgents,
            },
            {
                Name:        "validate-health",
                Description: "Validate all agents are healthy",
                Action:      validateSystemHealth,
            },
            {
                Name:        "execute-workflow",
                Description: "Execute cost optimization workflow",
                Action:      executeCostOptimizationWorkflow,
            },
            {
                Name:        "validate-results",
                Description: "Validate workflow results",
                Action:      validateWorkflowResults,
            },
        },
    }
    
    // Execute scenario
    for _, step := range scenario.Steps {
        if err := step.Action(); err != nil {
            return fmt.Errorf("step %s failed: %w", step.Name, err)
        }
    }
    
    return nil
}

func executeCostOptimizationWorkflow() error {
    // Get cost optimizer URL
    costOptimizerURL := getAgentServiceURL("cost-optimizer-service")
    
    // Execute cost optimization
    req := &CostOptimizationRequest{
        CloudProvider: "aws",
        Region:        "us-west-2",
        Services:      []string{"ec2", "s3", "rds"},
        TimeRange:     "last-30-days",
    }
    
    reqBody, err := json.Marshal(req)
    if err != nil {
        return fmt.Errorf("failed to marshal request: %w", err)
    }
    
    resp, err := http.Post(costOptimizerURL+"/optimize", "application/json", bytes.NewBuffer(reqBody))
    if err != nil {
        return fmt.Errorf("failed to execute optimization: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("optimization failed with status: %d", resp.StatusCode)
    }
    
    // Store result for validation
    var result CostOptimizationResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return fmt.Errorf("failed to decode result: %w", err)
    }
    
    return storeWorkflowResult("cost-optimization", &result)
}
```

## Monitoring and Observability

### 1. Metrics Collection

#### Prometheus Metrics
```go
// Metrics collection
var (
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "agent_http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )
    
    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "agent_http_request_duration_seconds",
            Help: "HTTP request duration in seconds",
        },
        []string{"method", "endpoint"},
    )
    
    agentOperationsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "agent_operations_total",
            Help: "Total number of agent operations",
        },
        []string{"agent_type", "operation", "status"},
    )
)

func init() {
    prometheus.MustRegister(httpRequestsTotal)
    prometheus.MustRegister(httpRequestDuration)
    prometheus.MustRegister(agentOperationsTotal)
}

// Metrics middleware
func metricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        // Wrap response writer to capture status code
        ww := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
        
        next.ServeHTTP(ww, r)
        
        duration := time.Since(start)
        
        httpRequestsTotal.WithLabelValues(r.Method, r.URL.Path, fmt.Sprintf("%d", ww.statusCode)).Inc()
        httpRequestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration.Seconds())
    })
}

type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}
```

#### Custom Agent Metrics
```go
// Agent-specific metrics
func recordAgentOperation(agentType, operation, status string) {
    agentOperationsTotal.WithLabelValues(agentType, operation, status).Inc()
}

func recordCostOptimizationMetrics(request *CostOptimizationRequest, result *CostOptimizationResponse) {
    // Record optimization metrics
    labels := prometheus.Labels{
        "cloud_provider": request.CloudProvider,
        "region":         request.Region,
    }
    
    costOptimizationSavings.With(labels).Set(result.PotentialSavings)
    costOptimizationRecommendations.With(labels).Add(float64(len(result.ImplementationSteps)))
}

var (
    costOptimizationSavings = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "agent_cost_optimization_savings_dollars",
            Help: "Potential cost optimization savings in dollars",
        },
        []string{"cloud_provider", "region"},
    )
    
    costOptimizationRecommendations = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "agent_cost_optimization_recommendations_count",
            Help: "Number of cost optimization recommendations",
        },
        []string{"cloud_provider", "region"},
    )
)
```

### 2. Distributed Tracing

#### OpenTelemetry Integration
```go
// Distributed tracing setup
func initTracing(serviceName string) (*sdktrace.TracerProvider, error) {
    exporter, err := jaeger.New(jaeger.WithCollectorEndpoint())
    if err != nil {
        return nil, fmt.Errorf("failed to create Jaeger exporter: %w", err)
    }
    
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
            semconv.ServiceVersionKey.String("1.0.0"),
        )),
    )
    
    otel.SetTracerProvider(tp)
    return tp, nil
}

// Traced HTTP handler
func tracedHandler(handler http.Handler, tracer trace.Tracer, operationName string) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx, span := tracer.Start(r.Context(), operationName)
        defer span.End()
        
        // Add span attributes
        span.SetAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("http.url", r.URL.String()),
            attribute.String("http.user_agent", r.UserAgent()),
        )
        
        // Continue with request
        r = r.WithContext(ctx)
        handler.ServeHTTP(w, r)
    })
}
```

### 3. Logging

#### Structured Logging
```go
// Structured logging with correlation IDs
type Logger struct {
    logger *logrus.Logger
}

func NewLogger() *Logger {
    logger := logrus.New()
    logger.SetFormatter(&logrus.JSONFormatter{
        TimestampFormat: time.RFC3339,
    })
    
    return &Logger{logger: logger}
}

func (l *Logger) WithRequestID(requestID string) *logrus.Entry {
    return l.logger.WithField("request_id", requestID)
}

func (l *Logger) WithAgentInfo(agentID, agentType string) *logrus.Entry {
    return l.logger.WithFields(logrus.Fields{
        "agent_id":   agentID,
        "agent_type": agentType,
    })
}

func (l *Logger) LogAgentOperation(agentID, agentType, operation string, duration time.Duration, err error) {
    entry := l.WithAgentInfo(agentID, agentType).WithFields(logrus.Fields{
        "operation": operation,
        "duration":  duration.Milliseconds(),
    })
    
    if err != nil {
        entry.WithError(err).Error("Agent operation failed")
    } else {
        entry.Info("Agent operation completed")
    }
}
```

## Performance Testing

### 1. Load Testing Framework

#### Concurrent Request Testing
```go
// Load testing framework
type LoadTester struct {
    client     *http.Client
    config     *LoadTestConfig
    results    *LoadTestResults
    resultsMux sync.Mutex
}

func (lt *LoadTester) RunLoadTest(targetURL string) (*LoadTestResults, error) {
    lt.results = &LoadTestResults{
        StartTimestamp: time.Now(),
    }
    
    // Create channel for requests
    requestCh := make(chan int, lt.config.ConcurrentRequests)
    
    // Start workers
    var wg sync.WaitGroup
    for i := 0; i < lt.config.ConcurrentRequests; i++ {
        wg.Add(1)
        go lt.worker(requestCh, &wg)
    }
    
    // Send requests
    for i := 0; i < lt.config.TotalRequests; i++ {
        requestCh <- i
        if lt.config.RequestInterval > 0 {
            time.Sleep(lt.config.RequestInterval)
        }
    }
    
    close(requestCh)
    wg.Wait()
    
    lt.results.EndTimestamp = time.Now()
    lt.results.calculateMetrics()
    
    return lt.results, nil
}

func (lt *LoadTester) worker(requestCh <-chan int, wg *sync.WaitGroup) {
    defer wg.Done()
    
    for requestID := range requestCh {
        start := time.Now()
        
        resp, err := lt.client.Get(lt.config.TargetURL)
        duration := time.Since(start)
        
        lt.resultsMux.Lock()
        lt.results.TotalRequests++
        if err != nil {
            lt.results.FailedRequests++
            lt.results.ErrorDurations = append(lt.results.ErrorDurations, duration)
        } else {
            lt.results.SuccessfulRequests++
            lt.results.SuccessDurations = append(lt.results.SuccessDurations, duration)
            resp.Body.Close()
        }
        lt.resultsMux.Unlock()
    }
}
```

### 2. Stress Testing

#### Memory Stress Testing
```go
// Memory stress testing
func TestMemoryStress(t *testing.T) {
    testEnv := setupTestEnvironment(t)
    defer testEnv.Cleanup()
    
    memoryURL := testEnv.GetAgentServiceURL("agent-memory-rust")
    client := NewMemoryClient(memoryURL)
    
    // Stress test configuration
    stressConfig := &StressTestConfig{
        Duration:           5 * time.Minute,
        ConcurrentGoroutines: 100,
        OperationsPerSecond: 1000,
        MemorySize:         1024, // 1KB per memory
    }
    
    results := runMemoryStressTest(client, stressConfig)
    
    // Assert stress test requirements
    assert.Greater(t, results.TotalOperations, 100000)
    assert.Less(t, results.AverageLatency, 100*time.Millisecond)
    assert.Greater(t, results.SuccessRate, 0.95)
}

type StressTestConfig struct {
    Duration           time.Duration
    ConcurrentGoroutines int
    OperationsPerSecond int
    MemorySize         int
}

type StressTestResults struct {
    TotalOperations   int
    SuccessfulOps     int
    FailedOps         int
    AverageLatency    time.Duration
    P95Latency        time.Duration
    SuccessRate       float64
    MemoryUsage       int64
}
```

### 3. Benchmark Testing

#### Agent Performance Benchmarks
```go
// Benchmark agent operations
func BenchmarkCostOptimization(b *testing.B) {
    optimizer := NewCostOptimizer()
    
    request := &CostOptimizationRequest{
        CloudProvider: "aws",
        Region:        "us-west-2",
        Services:      []string{"ec2", "s3"},
        TimeRange:     "last-30-days",
    }
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, err := optimizer.OptimizeCosts(request)
        if err != nil {
            b.Fatalf("Optimization failed: %v", err)
        }
    }
}

func BenchmarkMemoryOperations(b *testing.B) {
    client := setupMemoryClient(b)
    memory := &Memory{
        AgentID: "benchmark-agent",
        Type:    "observation",
        Content: strings.Repeat("x", 100), // 100 bytes
    }
    
    b.Run("Store", func(b *testing.B) {
        b.ResetTimer()
        for i := 0; i < b.N; i++ {
            memory.AgentID = fmt.Sprintf("agent-%d", i)
            err := client.StoreMemory(context.Background(), memory)
            if err != nil {
                b.Fatalf("Store failed: %v", err)
            }
        }
    })
    
    b.Run("Retrieve", func(b *testing.B) {
        b.ResetTimer()
        for i := 0; i < b.N; i++ {
            _, err := client.RetrieveMemories(context.Background(), "benchmark")
            if err != nil {
                b.Fatalf("Retrieve failed: %v", err)
            }
        }
    })
}
```

## Troubleshooting Integration Issues

### 1. Communication Issues

#### Network Connectivity Problems
```bash
# Check service connectivity
kubectl exec -it cost-optimizer-agent-xxx -n ai-infrastructure -- wget -qO- http://security-scanner-service:8080/health

# Check DNS resolution
kubectl exec -it cost-optimizer-agent-xxx -n ai-infrastructure -- nslookup security-scanner-service.ai-infrastructure.svc.cluster.local

# Check network policies
kubectl get networkpolicy -n ai-infrastructure

# Check service endpoints
kubectl get endpoints -n ai-infrastructure
```

#### Service Discovery Issues
```go
// Debug service discovery
func debugServiceDiscovery(agentType string) error {
    // List pods for agent type
    pods, err := clientset.CoreV1().Pods("ai-infrastructure").List(context.TODO(),
        metav1.ListOptions{
            LabelSelector: fmt.Sprintf("agent-type=%s", agentType),
        })
    if err != nil {
        return fmt.Errorf("failed to list pods: %w", err)
    }
    
    fmt.Printf("Found %d pods for agent type %s\n", len(pods.Items), agentType)
    
    for _, pod := range pods.Items {
        fmt.Printf("Pod: %s, Status: %s, IP: %s\n", 
            pod.Name, pod.Status.Phase, pod.Status.PodIP)
        
        // Check pod conditions
        for _, condition := range pod.Status.Conditions {
            fmt.Printf("  Condition: %s = %s\n", condition.Type, condition.Status)
        }
    }
    
    // Check service
    serviceName := fmt.Sprintf("%s-service", agentType)
    service, err := clientset.CoreV1().Services("ai-infrastructure").Get(context.TODO(), serviceName, metav1.GetOptions{})
    if err != nil {
        return fmt.Errorf("failed to get service: %w", err)
    }
    
    fmt.Printf("Service: %s, Type: %s, ClusterIP: %s\n", 
        service.Name, service.Spec.Type, service.Spec.ClusterIP)
    
    return nil
}
```

### 2. Performance Issues

#### Resource Bottlenecks
```bash
# Check resource usage
kubectl top pods -n ai-infrastructure
kubectl top nodes

# Check resource limits
kubectl describe pod cost-optimizer-agent-xxx -n ai-infrastructure | grep -A 10 "Limits:"

# Check HPA status
kubectl get hpa -n ai-infrastructure

# Check events for resource issues
kubectl get events -n ai-infrastructure --field-selector reason=FailedScheduling
```

#### Memory Leaks
```go
// Memory leak detection
func detectMemoryLeaks(agentURL string, duration time.Duration) error {
    var samples []MemorySample
    
    ticker := time.NewTicker(10 * time.Second)
    defer ticker.Stop()
    
    ctx, cancel := context.WithTimeout(context.Background(), duration)
    defer cancel()
    
    for {
        select {
        case <-ctx.Done():
            return analyzeMemorySamples(samples)
        case <-ticker.C:
            sample, err := collectMemorySample(agentURL)
            if err != nil {
                return fmt.Errorf("failed to collect memory sample: %w", err)
            }
            samples = append(samples, *sample)
        }
    }
}

type MemorySample struct {
    Timestamp time.Time
    RSS       int64
    HeapSize  int64
    Goroutines int
}

func analyzeMemorySamples(samples []MemorySample) error {
    if len(samples) < 2 {
        return fmt.Errorf("insufficient samples for analysis")
    }
    
    // Calculate memory growth rate
    firstSample := samples[0]
    lastSample := samples[len(samples)-1]
    
    duration := lastSample.Timestamp.Sub(firstSample.Timestamp)
    memoryGrowth := lastSample.RSS - firstSample.RSS
    growthRate := float64(memoryGrowth) / duration.Seconds()
    
    fmt.Printf("Memory growth rate: %.2f bytes/second\n", growthRate)
    
    // Check for potential memory leak
    if growthRate > 1024*1024 { // 1MB/second
        return fmt.Errorf("potential memory leak detected: growth rate %.2f bytes/second", growthRate)
    }
    
    return nil
}
```

## Conclusion

This comprehensive guide covers all aspects of agent integration and testing:

1. **Integration Architecture**: System components and communication patterns
2. **Communication Patterns**: HTTP, message queues, and gRPC implementations
3. **System Integration**: Memory agents, Ollama, and dashboard integration
4. **Testing Strategies**: Unit, integration, and performance testing
5. **Validation Procedures**: Health checks, functional validation, and E2E workflows
6. **Monitoring**: Metrics, tracing, and structured logging
7. **Performance Testing**: Load testing, stress testing, and benchmarks
8. **Troubleshooting**: Common issues and debugging procedures

By following these integration patterns and testing methodologies, you can ensure reliable, performant, and well-tested AI agent deployments in your Kubernetes environment.

## References

- [Kubernetes Testing Documentation](https://kubernetes.io/docs/tasks/testing/)
- [OpenTelemetry Go Documentation](https://opentelemetry.io/docs/instrumentation/go/)
- [Prometheus Go Client](https://github.com/prometheus/client_golang)
- [Go Testing Documentation](https://golang.org/pkg/testing/)
