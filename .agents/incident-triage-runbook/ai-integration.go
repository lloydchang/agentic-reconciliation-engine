package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"go.temporal.io/sdk/activity"
)

// AIAnalysisRequest represents the input for AI analysis
type AIAnalysisRequest struct {
	Task     string            `json:"task"`
	Context  string            `json:"context"`
	Data     map[string]interface{} `json:"data,omitempty"`
	Priority string            `json:"priority,omitempty"`
}

// AIAnalysisResponse represents the output from AI analysis
type AIAnalysisResponse struct {
	Analysis     string `json:"analysis"`
	Confidence   float64 `json:"confidence"`
	Recommendations []string `json:"recommendations,omitempty"`
	Severity     string `json:"severity,omitempty"`
}

// AnalyzeIncidentWithAI is a Temporal activity that uses AI memory agents for incident analysis
func AnalyzeIncidentWithAI(ctx context.Context, req AIAnalysisRequest) (*AIAnalysisResponse, error) {
	logger := activity.GetLogger(ctx)

	// Prepare the inference request
	inferenceReq := map[string]interface{}{
		"task": fmt.Sprintf("Analyze this incident: %s", req.Task),
		"context": req.Context,
		"data": req.Data,
	}

	// Convert to JSON
	reqBody, err := json.Marshal(inferenceReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Call AI inference gateway
	resp, err := http.Post("http://ai-inference-service.ai-infrastructure.svc.cluster.local:8080/api/infer",
		"application/json", strings.NewReader(string(reqBody)))
	if err != nil {
		logger.Error("Failed to call AI inference service", "error", err)
		return nil, fmt.Errorf("AI inference call failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		logger.Error("AI inference service returned error", "status", resp.StatusCode, "body", string(body))
		return nil, fmt.Errorf("AI service error: %s", string(body))
	}

	// Parse AI response
	var aiResp map[string]interface{}
	if err := json.Unmarshal(body, &aiResp); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w", err)
	}

	// Extract analysis from AI response
	analysis := ""
	if result, ok := aiResp["result"].(string); ok {
		analysis = result
	}

	// Create structured response
	response := &AIAnalysisResponse{
		Analysis:   analysis,
		Confidence: 0.8, // Default confidence
		Recommendations: []string{
			"Review system logs for additional context",
			"Check recent deployments for changes",
			"Monitor affected services for recovery",
		},
	}

	// Try to extract severity if present in AI response
	if severity, ok := aiResp["severity"].(string); ok {
		response.Severity = severity
	}

	logger.Info("Incident analyzed with AI", "analysis_length", len(analysis))

	return response, nil
}

// ClassifyIncidentSeverity uses AI to classify incident severity
func ClassifyIncidentSeverity(ctx context.Context, alertData map[string]interface{}) (string, error) {
	req := AIAnalysisRequest{
		Task: "Classify the severity of this incident alert",
		Context: "Determine if this is P1 (critical), P2 (major), P3 (minor), or P4 (cosmetic) based on impact and symptoms",
		Data: alertData,
	}

	resp, err := AnalyzeIncidentWithAI(ctx, req)
	if err != nil {
		return "P3", err // Default to P3 on error
	}

	// Extract severity from AI response
	if resp.Severity != "" {
		return resp.Severity, nil
	}

	// Fallback: parse severity from analysis text
	analysis := strings.ToUpper(resp.Analysis)
	if strings.Contains(analysis, "P1") || strings.Contains(analysis, "CRITICAL") {
		return "P1", nil
	} else if strings.Contains(analysis, "P2") || strings.Contains(analysis, "MAJOR") {
		return "P2", nil
	} else if strings.Contains(analysis, "P4") || strings.Contains(analysis, "COSMETIC") {
		return "P4", nil
	}

	return "P3", nil // Default
}

// GeneratePostMortem uses AI to generate incident post-mortem
func GeneratePostMortem(ctx context.Context, incidentData map[string]interface{}) (string, error) {
	req := AIAnalysisRequest{
		Task: "Generate a comprehensive post-mortem report for this incident",
		Context: "Include what happened, impact, root cause, action items, and lessons learned",
		Data: incidentData,
	}

	resp, err := AnalyzeIncidentWithAI(ctx, req)
	if err != nil {
		return "", err
	}

	return resp.Analysis, nil
}
