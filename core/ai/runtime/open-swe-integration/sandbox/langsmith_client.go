package sandbox

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hasura/go-graphql-client"
)

// LangSmithClient handles sandbox execution via LangSmith
type LangSmithClient struct {
	client   *graphql.Client
	apiKey   string
	baseURL  string
	timeout  time.Duration
}

// SandboxExecution represents a sandbox execution request
type SandboxExecution struct {
	ID          string                 `json:"id"`
	Code        string                 `json:"code"`
	Language    string                 `json:"language"`
	Environment map[string]string      `json:"environment,omitempty"`
	Timeout     time.Duration          `json:"timeout"`
	MemoryLimit int64                  `json:"memory_limit_mb"`
	CPULimit    string                 `json:"cpu_limit"`
	Inputs      map[string]interface{} `json:"inputs,omitempty"`
	CorrelationID string               `json:"correlation_id"`
}

// SandboxResult represents the result of a sandbox execution
type SandboxResult struct {
	ID            string                 `json:"id"`
	Status        string                 `json:"status"` // "success", "error", "timeout"
	Output        string                 `json:"output,omitempty"`
	Error         string                 `json:"error,omitempty"`
	ExecutionTime time.Duration          `json:"execution_time"`
	MemoryUsed    int64                  `json:"memory_used_mb"`
	ExitCode      int                    `json:"exit_code"`
	Data          map[string]interface{} `json:"data,omitempty"`
}

// NewLangSmithClient creates a new LangSmith sandbox client
func NewLangSmithClient(apiKey, baseURL string) *LangSmithClient {
	return &LangSmithClient{
		client:  graphql.NewClient(baseURL+"/graphql", nil),
		apiKey:  apiKey,
		baseURL: baseURL,
		timeout: 5 * time.Minute,
	}
}

// ExecuteCode executes code in a secure sandbox environment
func (c *LangSmithClient) ExecuteCode(ctx context.Context, execution SandboxExecution) (*SandboxResult, error) {
	if execution.Timeout == 0 {
		execution.Timeout = c.timeout
	}

	ctx, cancel := context.WithTimeout(ctx, execution.Timeout)
	defer cancel()

	// Prepare GraphQL mutation
	var mutation struct {
		ExecuteCode struct {
			ID            graphql.String
			Status        graphql.String
			Output        graphql.String
			Error         graphql.String
			ExecutionTime graphql.Int
			MemoryUsed    graphql.Int
			ExitCode      graphql.Int
		} `graphql:"executeCode(input: $input)"`
	}

	input := map[string]interface{}{
		"code":         execution.Code,
		"language":     execution.Language,
		"environment":  execution.Environment,
		"timeout":      int(execution.Timeout.Seconds()),
		"memoryLimit":  execution.MemoryLimit,
		"cpuLimit":     execution.CPULimit,
		"inputs":       execution.Inputs,
		"correlationId": execution.CorrelationID,
	}

	err := c.client.WithRequestModifier(func(r *http.Request) {
		r.Header.Set("Authorization", "Bearer "+c.apiKey)
		r.Header.Set("Content-Type", "application/json")
	}).Mutate(ctx, &mutation, input)

	if err != nil {
		return nil, fmt.Errorf("sandbox execution failed: %w", err)
	}

	result := &SandboxResult{
		ID:            string(mutation.ExecuteCode.ID),
		Status:        string(mutation.ExecuteCode.Status),
		Output:        string(mutation.ExecuteCode.Output),
		Error:         string(mutation.ExecuteCode.Error),
		ExecutionTime: time.Duration(mutation.ExecuteCode.ExecutionTime) * time.Millisecond,
		MemoryUsed:    int64(mutation.ExecuteCode.MemoryUsed),
		ExitCode:      int(mutation.ExecuteCode.ExitCode),
	}

	return result, nil
}

// ValidateCode performs static analysis on code before execution
func (c *LangSmithClient) ValidateCode(ctx context.Context, code, language string) (*ValidationResult, error) {
	var query struct {
		ValidateCode struct {
			Valid   graphql.Boolean
			Issues  []struct {
				Type        graphql.String
				Message     graphql.String
				Line        graphql.Int
				Column      graphql.Int
				Severity    graphql.String
			}
			SecurityScore graphql.Float
		} `graphql:"validateCode(code: $code, language: $language)"`
	}

	err := c.client.WithRequestModifier(func(r *http.Request) {
		r.Header.Set("Authorization", "Bearer "+c.apiKey)
	}).Query(ctx, &query, map[string]interface{}{
		"code":     code,
		"language": language,
	})

	if err != nil {
		return nil, fmt.Errorf("code validation failed: %w", err)
	}

	result := &ValidationResult{
		Valid:         bool(query.ValidateCode.Valid),
		SecurityScore: float64(query.ValidateCode.SecurityScore),
	}

	for _, issue := range query.ValidateCode.Issues {
		result.Issues = append(result.Issues, ValidationIssue{
			Type:     string(issue.Type),
			Message:  string(issue.Message),
			Line:     int(issue.Line),
			Column:  int(issue.Column),
			Severity: string(issue.Severity),
		})
	}

	return result, nil
}

// ValidationResult represents code validation results
type ValidationResult struct {
	Valid         bool              `json:"valid"`
	Issues        []ValidationIssue `json:"issues,omitempty"`
	SecurityScore float64           `json:"security_score"`
}

// ValidationIssue represents a code validation issue
type ValidationIssue struct {
	Type     string `json:"type"`
	Message  string `json:"message"`
	Line     int    `json:"line"`
	Column  int    `json:"column"`
	Severity string `json:"severity"`
}
