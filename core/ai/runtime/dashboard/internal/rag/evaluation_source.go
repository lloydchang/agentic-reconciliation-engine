package rag

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// EvaluationSource provides evaluation data from the evaluation API
type EvaluationSource struct {
	client  *http.Client
	baseURL string
}

// NewEvaluationSource creates a new evaluation data source
func NewEvaluationSource(baseURL string) *EvaluationSource {
	return &EvaluationSource{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
		baseURL: strings.TrimSuffix(baseURL, "/"),
	}
}

// Search implements DataSource interface
func (e *EvaluationSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Determine which endpoint to query based on the query
	if strings.Contains(strings.ToLower(query), "health") {
		doc, err := e.getHealthData(ctx)
		if err == nil {
			documents = append(documents, doc)
		}
	}
	
	if strings.Contains(strings.ToLower(query), "monitor") || strings.Contains(strings.ToLower(query), "issue") {
		doc, err := e.getMonitoringData(ctx)
		if err == nil {
			documents = append(documents, doc)
		}
		
		issuesDoc, err := e.getIssuesData(ctx)
		if err == nil {
			documents = append(documents, issuesDoc)
		}
	}
	
	if strings.Contains(strings.ToLower(query), "fix") || strings.Contains(strings.ToLower(query), "auto") {
		doc, err := e.getAutoFixData(ctx)
		if err == nil {
			documents = append(documents, doc)
		}
	}
	
	// If no specific match, get summary
	if len(documents) == 0 {
		doc, err := e.getSummaryData(ctx)
		if err == nil {
			documents = append(documents, doc)
		}
	}
	
	return documents, nil
}

// IsRelevant checks if evaluation source is relevant for the query
func (e *EvaluationSource) IsRelevant(query string) bool {
	keywords := []string{
		"evaluation", "monitor", "health", "agent", "trace", 
		"issue", "problem", "fix", "auto-fix", "performance",
		"conversation", "workflow", "temporal", "kubernetes",
	}
	
	queryLower := strings.ToLower(query)
	for _, keyword := range keywords {
		if strings.Contains(queryLower, keyword) {
			return true
		}
	}
	return false
}

// getHealthData fetches health evaluation data
func (e *EvaluationSource) getHealthData(ctx context.Context) (Document, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/health", e.baseURL)
	
	resp, err := e.client.Get(url)
	if err != nil {
		return Document{}, fmt.Errorf("failed to fetch health data: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Document{}, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return Document{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	content := e.formatHealthContent(response)
	
	return Document{
		Content:  content,
		Source:   "evaluation-api",
		Type:     "agent_health",
		Metadata: map[string]interface{}{
			"endpoint":    "/api/v1/evaluation/health",
			"timestamp":   time.Now().Format(time.RFC3339),
			"status":      getNestedValue(response, "status"),
			"data_source": "evaluation_framework",
		},
	}, nil
}

// getMonitoringData fetches monitoring evaluation data
func (e *EvaluationSource) getMonitoringData(ctx context.Context) (Document, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/monitoring", e.baseURL)
	
	resp, err := e.client.Get(url)
	if err != nil {
		return Document{}, fmt.Errorf("failed to fetch monitoring data: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Document{}, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return Document{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	content := e.formatMonitoringContent(response)
	
	return Document{
		Content:  content,
		Source:   "evaluation-api",
		Type:     "agent_monitoring",
		Metadata: map[string]interface{}{
			"endpoint":    "/api/v1/evaluation/monitoring",
			"timestamp":   time.Now().Format(time.RFC3339),
			"status":      getNestedValue(response, "status"),
			"data_source": "evaluation_framework",
		},
	}, nil
}

// getIssuesData fetches issues data
func (e *EvaluationSource) getIssuesData(ctx context.Context) (Document, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/issues", e.baseURL)
	
	resp, err := e.client.Get(url)
	if err != nil {
		return Document{}, fmt.Errorf("failed to fetch issues data: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Document{}, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return Document{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	content := e.formatIssuesContent(response)
	
	return Document{
		Content:  content,
		Source:   "evaluation-api",
		Type:     "agent_issues",
		Metadata: map[string]interface{}{
			"endpoint":    "/api/v1/evaluation/issues",
			"timestamp":   time.Now().Format(time.RFC3339),
			"status":      getNestedValue(response, "status"),
			"data_source": "evaluation_framework",
		},
	}, nil
}

// getAutoFixData fetches auto-fix data
func (e *EvaluationSource) getAutoFixData(ctx context.Context) (Document, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/auto-fix", e.baseURL)
	
	resp, err := e.client.Get(url)
	if err != nil {
		return Document{}, fmt.Errorf("failed to fetch auto-fix data: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Document{}, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return Document{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	content := e.formatAutoFixContent(response)
	
	return Document{
		Content:  content,
		Source:   "evaluation-api",
		Type:     "auto_fix_status",
		Metadata: map[string]interface{}{
			"endpoint":    "/api/v1/evaluation/auto-fix",
			"timestamp":   time.Now().Format(time.RFC3339),
			"status":      getNestedValue(response, "status"),
			"data_source": "evaluation_framework",
		},
	}, nil
}

// getSummaryData fetches comprehensive evaluation summary
func (e *EvaluationSource) getSummaryData(ctx context.Context) (Document, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/summary", e.baseURL)
	
	resp, err := e.client.Get(url)
	if err != nil {
		return Document{}, fmt.Errorf("failed to fetch summary data: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return Document{}, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return Document{}, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	content := e.formatSummaryContent(response)
	
	return Document{
		Content:  content,
		Source:   "evaluation-api",
		Type:     "evaluation_summary",
		Metadata: map[string]interface{}{
			"endpoint":    "/api/v1/evaluation/summary",
			"timestamp":   time.Now().Format(time.RFC3339),
			"status":      getNestedValue(response, "status"),
			"data_source": "evaluation_framework",
		},
	}, nil
}

// Helper methods for formatting content

func (e *EvaluationSource) formatHealthContent(response map[string]interface{}) string {
	data, ok := response["data"].(map[string]interface{})
	if !ok {
		return "No health data available"
	}
	
	var content strings.Builder
	content.WriteString("## Agent Health Evaluation\n\n")
	
	if workerHealth, exists := data["worker_health"]; exists {
		content.WriteString("### Worker Health\n")
		if workerMap, ok := workerHealth.(map[string]interface{}); ok {
			for key, value := range workerMap {
				content.WriteString(fmt.Sprintf("- **%s**: %v\n", key, value))
			}
		}
		content.WriteString("\n")
	}
	
	if conversationHealth, exists := data["conversation_health"]; exists {
		content.WriteString("### Conversation Health\n")
		if convMap, ok := conversationHealth.(map[string]interface{}); ok {
			for key, value := range convMap {
				content.WriteString(fmt.Sprintf("- **%s**: %v\n", key, value))
			}
		}
		content.WriteString("\n")
	}
	
	if overallHealth, exists := data["overall_health_status"]; exists {
		content.WriteString(fmt.Sprintf("### Overall Status: %v\n", overallHealth))
	}
	
	return content.String()
}

func (e *EvaluationSource) formatMonitoringContent(response map[string]interface{}) string {
	data, ok := response["data"].(map[string]interface{})
	if !ok {
		return "No monitoring data available"
	}
	
	var content strings.Builder
	content.WriteString("## Agent Monitoring Report\n\n")
	
	if infraHealth, exists := data["infrastructure_health"]; exists {
		content.WriteString("### Infrastructure Health\n")
		if infraMap, ok := infraHealth.(map[string]interface{}); ok {
			if issues, issueExists := infraMap["issues"]; issueExists {
				if issueList, ok := issues.([]interface{}); ok {
					content.WriteString(fmt.Sprintf("- **Issues Detected**: %d\n", len(issueList)))
				}
			}
			if status, statusExists := infraMap["status"]; statusExists {
				content.WriteString(fmt.Sprintf("- **Status**: %v\n", status))
			}
		}
		content.WriteString("\n")
	}
	
	if temporalHealth, exists := data["temporal_health"]; exists {
		content.WriteString("### Temporal Health\n")
		if temporalMap, ok := temporalHealth.(map[string]interface{}); ok {
			if timeouts, timeoutExists := temporalMap["timeout_issues"]; timeoutExists {
				if timeoutList, ok := timeouts.([]interface{}); ok {
					content.WriteString(fmt.Sprintf("- **Timeout Issues**: %d\n", len(timeoutList)))
				}
			}
			if status, statusExists := temporalMap["status"]; statusExists {
				content.WriteString(fmt.Sprintf("- **Status**: %v\n", status))
			}
		}
		content.WriteString("\n")
	}
	
	if agentHealth, exists := data["agent_health"]; exists {
		content.WriteString("### Agent Health\n")
		if agentMap, ok := agentHealth.(map[string]interface{}); ok {
			if issues, issueExists := agentMap["issues"]; issueExists {
				if issueList, ok := issues.([]interface{}); ok {
					content.WriteString(fmt.Sprintf("- **Issues Detected**: %d\n", len(issueList)))
				}
			}
			if status, statusExists := agentMap["status"]; statusExists {
				content.WriteString(fmt.Sprintf("- **Status**: %v\n", status))
			}
		}
	}
	
	return content.String()
}

func (e *EvaluationSource) formatIssuesContent(response map[string]interface{}) string {
	data, ok := response["data"].(map[string]interface{})
	if !ok {
		return "No issues data available"
	}
	
	var content strings.Builder
	content.WriteString("## Agent Issues Report\n\n")
	
	if totalCount, exists := data["total_count"]; exists {
		content.WriteString(fmt.Sprintf("### Total Issues: %v\n", totalCount))
	}
	
	if criticalCount, exists := data["critical_count"]; exists {
		content.WriteString(fmt.Sprintf("### Critical Issues: %v\n", criticalCount))
	}
	
	if issues, exists := data["issues"]; exists {
		content.WriteString("\n### Issue Details\n")
		if issueList, ok := issues.([]interface{}); ok {
			for i, issue := range issueList {
				if issueMap, ok := issue.(map[string]interface{}); ok {
					content.WriteString(fmt.Sprintf("#### Issue %d\n", i+1))
					for key, value := range issueMap {
						content.WriteString(fmt.Sprintf("- **%s**: %v\n", key, value))
					}
					content.WriteString("\n")
				}
			}
		}
	}
	
	return content.String()
}

func (e *EvaluationSource) formatAutoFixContent(response map[string]interface{}) string {
	data, ok := response["data"].(map[string]interface{})
	if !ok {
		return "No auto-fix data available"
	}
	
	var content strings.Builder
	content.WriteString("## Auto-Fix Status Report\n\n")
	
	if totalFixes, exists := data["total_fixes"]; exists {
		content.WriteString(fmt.Sprintf("### Total Fixes Applied: %v\n", totalFixes))
	}
	
	if fixHistory, exists := data["fix_history"]; exists {
		content.WriteString("\n### Recent Fix History\n")
		if historyList, ok := fixHistory.([]interface{}); ok {
			for i, fix := range historyList {
				if fixMap, ok := fix.(map[string]interface{}); ok {
					content.WriteString(fmt.Sprintf("#### Fix %d\n", i+1))
					for key, value := range fixMap {
						content.WriteString(fmt.Sprintf("- **%s**: %v\n", key, value))
					}
					content.WriteString("\n")
				}
			}
		}
	}
	
	return content.String()
}

func (e *EvaluationSource) formatSummaryContent(response map[string]interface{}) string {
	data, ok := response["data"].(map[string]interface{})
	if !ok {
		return "No summary data available"
	}
	
	var content strings.Builder
	content.WriteString("## Evaluation Summary\n\n")
	
	if summary, exists := data["summary"]; exists {
		content.WriteString("### Summary\n")
		if summaryMap, ok := summary.(map[string]interface{}); ok {
			for key, value := range summaryMap {
				content.WriteString(fmt.Sprintf("- **%s**: %v\n", key, value))
			}
		}
		content.WriteString("\n")
	}
	
	if traceCount, exists := data["trace_count"]; exists {
		content.WriteString(fmt.Sprintf("### Traces Analyzed: %v\n", traceCount))
	}
	
	if evaluatorsRun, exists := data["evaluators_run"]; exists {
		content.WriteString("### Evaluators Run\n")
		if evaluatorList, ok := evaluatorsRun.([]interface{}); ok {
			for _, evaluator := range evaluatorList {
				content.WriteString(fmt.Sprintf("- %v\n", evaluator))
			}
		}
	}
	
	return content.String()
}

// Helper function to safely get nested values
func getNestedValue(data map[string]interface{}, key string) interface{} {
	if value, exists := data[key]; exists {
		return value
	}
	return nil
}
