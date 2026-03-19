package rag

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// QwenClient implements Qwen LLM interface
type QwenClient struct {
	baseURL string
	model   string
	client  *http.Client
}

// QwenRequest represents a request to Qwen API
type QwenRequest struct {
	Message string `json:"message"`
	MaxTokens *int `json:"max_tokens,omitempty"`
	Temperature *float64 `json:"temperature,omitempty"`
}

// QwenResponse represents a response from Qwen API
type QwenResponse struct {
	Content string `json:"content"`
	Model   string `json:"model"`
	Done    bool   `json:"done"`
}

// LLMResponse represents the response from Qwen
type LLMResponse struct {
	Content string `json:"content"`
	Model   string `json:"model"`
}

// NewQwenClient creates a new Qwen client using centralized service
func NewQwenClient(baseURL, model string) *QwenClient {
	return &QwenClient{
		baseURL: "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080",
		model:   "qwen2.5-7b-instruct",
		client:  &http.Client{Timeout: 60 * time.Second},
	}
}

// Generate generates a response using Qwen with RAG context
func (q *QwenClient) Generate(ctx context.Context, prompt string, context []Document) (*LLMResponse, error) {
	// Build RAG-enhanced prompt
	ragPrompt := q.buildRAGPrompt(prompt, context)
	
	// Prepare request payload
	maxTokens := 2048
	temperature := 0.1
	payload := QwenRequest{
		Message: ragPrompt,
		MaxTokens: &maxTokens,
		Temperature: &temperature,
	}
	
	// Convert to JSON
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}
	
	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", q.baseURL+"/api/v1/chat", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", "k8sgpt-api-key")
	
	// Send request
	resp, err := q.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()
	
	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}
	
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}
	
	// Parse response
	var apiResponse struct {
		Success bool   `json:"success"`
		Data    *struct {
			Message string `json:"message"`
			Usage  *struct {
				PromptTokens int `json:"prompt_tokens"`
				CompletionTokens int `json:"completion_tokens"`
				TotalTokens int `json:"total_tokens"`
			} `json:"usage"`
		} `json:"data"`
		Error    string `json:"error"`
	}
	
	if err := json.Unmarshal(body, &apiResponse); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}
	
	if !apiResponse.Success {
		return nil, fmt.Errorf("API error: %s", apiResponse.Error)
	}
	
	if apiResponse.Data == nil {
		return nil, fmt.Errorf("no data in response")
	}
	
	return &LLMResponse{
		Content: apiResponse.Data.Message,
		Model:   q.model,
	}, nil
}

// CreateEmbedding creates an embedding for text (simplified version)
func (q *QwenClient) CreateEmbedding(ctx context.Context, text string) ([]float32, error) {
	// For now, return a simple hash-based embedding
	// In production, this would call a proper embedding model
	embedding := make([]float32, 1536)
	
	// Simple hash-based embedding generation
	hash := q.simpleHash(text)
	for i := range embedding {
		embedding[i] = float32((hash >> (i % 32)) & 0xFF) / 255.0
	}
	
	return embedding, nil
}

// buildRAGPrompt constructs a RAG-enhanced prompt
func (q *QwenClient) buildRAGPrompt(question string, context []Document) string {
	var contextStr strings.Builder
	
	if len(context) > 0 {
		contextStr.WriteString("Context:\n")
		for i, doc := range context {
			contextStr.WriteString(fmt.Sprintf("[%d] Source: %s\n", i+1, doc.Source))
			contextStr.WriteString(fmt.Sprintf("Content: %s\n\n", doc.Content))
		}
		contextStr.WriteString("---\n\n")
	}
	
	prompt := fmt.Sprintf(`You are Qwen, an AI assistant helping with Agentic Reconciliation Engine management.

%sQuestion: %s

Instructions:
- Use the provided context to answer accurately
- If context doesn't contain the answer, say so clearly
- Provide specific, actionable guidance
- Reference sources when possible
- Focus on practical solutions for GitOps operations

Answer:`, contextStr.String(), question)
	
	return prompt
}

// simpleHash creates a simple hash for embedding generation
func (q *QwenClient) simpleHash(text string) uint64 {
	hash := uint64(5381)
	for _, c := range text {
		hash = ((hash << 5) + hash) + uint64(c)
	}
	return hash
}
