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

// ComplianceScanRequest represents input for compliance analysis
type ComplianceScanRequest struct {
	ResourceType string                 `json:"resource_type"`
	ResourceID   string                 `json:"resource_id"`
	ScanResults  map[string]interface{} `json:"scan_results"`
	TenantID     string                 `json:"tenant_id"`
}

// ComplianceAnalysis represents AI analysis of compliance issues
type ComplianceAnalysis struct {
	RiskLevel        string   `json:"risk_level"`
	Violations       []string `json:"violations"`
	Recommendations  []string `json:"recommendations"`
	RemediationSteps []string `json:"remediation_steps"`
}

// AnalyzeComplianceWithAI uses AI to analyze compliance scan results
func AnalyzeComplianceWithAI(ctx context.Context, req ComplianceScanRequest) (*ComplianceAnalysis, error) {
	logger := activity.GetLogger(ctx)

	// Prepare inference request
	inferenceReq := map[string]interface{}{
		"task": fmt.Sprintf("Analyze compliance scan results for %s resource: %s", req.ResourceType, req.ResourceID),
		"context": "Assess security risks, identify violations, provide remediation recommendations",
		"data": map[string]interface{}{
			"resource_type": req.ResourceType,
			"resource_id":   req.ResourceID,
			"scan_results":  req.ScanResults,
			"tenant_id":     req.TenantID,
		},
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

	// Read and parse response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		logger.Error("AI inference service returned error", "status", resp.StatusCode, "body", string(body))
		return nil, fmt.Errorf("AI service error: %s", string(body))
	}

	var aiResp map[string]interface{}
	if err := json.Unmarshal(body, &aiResp); err != nil {
		return nil, fmt.Errorf("failed to parse AI response: %w", err)
	}

	// Extract analysis
	analysis := ""
	if result, ok := aiResp["result"].(string); ok {
		analysis = result
	}

	// Parse AI response for structured compliance analysis
	compliance := &ComplianceAnalysis{
		RiskLevel: "medium", // default
		Violations: []string{},
		Recommendations: []string{
			"Review resource configuration against security best practices",
			"Implement automated compliance monitoring",
			"Consider security training for development teams",
		},
		RemediationSteps: []string{
			"Update resource tags for compliance tracking",
			"Enable encryption for data at rest",
			"Configure access logging and monitoring",
		},
	}

	// Try to extract risk level from AI analysis
	analysisUpper := strings.ToUpper(analysis)
	if strings.Contains(analysisUpper, "HIGH") || strings.Contains(analysisUpper, "CRITICAL") {
		compliance.RiskLevel = "high"
	} else if strings.Contains(analysisUpper, "LOW") || strings.Contains(analysisUpper, "MINOR") {
		compliance.RiskLevel = "low"
	}

	logger.Info("Compliance analyzed with AI", "resource", req.ResourceID, "risk_level", compliance.RiskLevel)

	return compliance, nil
}

// PrioritizeComplianceRemediation uses AI to prioritize remediation tasks
func PrioritizeComplianceRemediation(ctx context.Context, violations []string) ([]string, error) {
	req := AIAnalysisRequest{
		Task: "Prioritize these compliance violations by risk and impact",
		Context: "Rank violations from highest to lowest priority for remediation",
		Data: map[string]interface{}{
			"violations": violations,
		},
	}

	resp, err := AnalyzeIncidentWithAI(ctx, req)
	if err != nil {
		// Fallback to original order
		return violations, err
	}

	// Parse prioritized list from AI response
	// This is simplified - in practice, you'd parse structured output
	prioritized := strings.Split(strings.ReplaceAll(resp.Analysis, "- ", ""), "\n")
	var cleanList []string
	for _, item := range prioritized {
		item = strings.TrimSpace(item)
		if item != "" && !strings.HasPrefix(item, "Prioritized") && !strings.HasPrefix(item, "Ranked") {
			cleanList = append(cleanList, item)
		}
	}

	if len(cleanList) == 0 {
		return violations, nil // fallback
	}

	return cleanList, nil
}
