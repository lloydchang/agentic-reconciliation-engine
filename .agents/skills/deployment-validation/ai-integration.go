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

// DeploymentValidationRequest represents input for deployment validation
type DeploymentValidationRequest struct {
	ServiceName     string                 `json:"service_name"`
	ImageTag        string                 `json:"image_tag"`
	Environment     string                 `json:"environment"`
	Strategy        string                 `json:"strategy"`
	Metrics         map[string]interface{} `json:"metrics"`
	TestResults     map[string]interface{} `json:"test_results"`
	ChangeLog       []string               `json:"change_log"`
}

// DeploymentValidationResult represents AI analysis of deployment validation
type DeploymentValidationResult struct {
	GoNoGo            string                  `json:"go_nogo"` // "GO" or "NO-GO"
	Confidence        float64                 `json:"confidence"`
	RiskAssessment    DeploymentRisk          `json:"risk_assessment"`
	Recommendations   []string                `json:"recommendations"`
	GateResults       map[string]string       `json:"gate_results"`
	PredictedIssues   []PredictedIssue        `json:"predicted_issues"`
	RollbackTrigger   bool                    `json:"rollback_trigger"`
	RollbackReason    string                  `json:"rollback_reason,omitempty"`
}

// DeploymentRisk represents risk assessment
type DeploymentRisk struct {
	Level         string  `json:"level"` // "low", "medium", "high", "critical"
	Score         float64 `json:"score"` // 0-1 scale
	PrimaryRisks  []string `json:"primary_risks"`
	MitigationSteps []string `json:"mitigation_steps"`
}

// PredictedIssue represents potential deployment issues
type PredictedIssue struct {
	Issue         string  `json:"issue"`
	Probability   float64 `json:"probability"`
	Impact        string  `json:"impact"`
	DetectionGate string  `json:"detection_gate"`
}

// AnalyzeDeploymentWithAI uses AI to validate deployment quality and predict issues
func AnalyzeDeploymentWithAI(ctx context.Context, req DeploymentValidationRequest) (*DeploymentValidationResult, error) {
	logger := activity.GetLogger(ctx)

	// Prepare comprehensive inference request
	inferenceReq := map[string]interface{}{
		"task": fmt.Sprintf("Validate deployment of %s:%s to %s environment using %s strategy", req.ServiceName, req.ImageTag, req.Environment, req.Strategy),
		"context": "Analyze metrics, test results, and changes to determine GO/NO-GO decision, assess risks, predict potential issues, and provide deployment recommendations",
		"data": map[string]interface{}{
			"service_name":  req.ServiceName,
			"image_tag":     req.ImageTag,
			"environment":   req.Environment,
			"strategy":      req.Strategy,
			"metrics":       req.Metrics,
			"test_results":  req.TestResults,
			"change_log":    req.ChangeLog,
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

	// Extract AI analysis
	analysis := ""
	if result, ok := aiResp["result"].(string); ok {
		analysis = result
	}

	// Generate structured validation result
	result := &DeploymentValidationResult{
		GoNoGo:         "GO",
		Confidence:     0.9,
		RollbackTrigger: false,
		GateResults: map[string]string{
			"smoke":           "pass",
			"health":          "pass",
			"golden_signals":  "pass",
			"business_metrics": "pass",
		},
		Recommendations: []string{
			"Monitor error rates closely for the first 15 minutes",
			"Ensure rollback procedures are tested and ready",
			"Have on-call engineer prepared for potential issues",
		},
		RiskAssessment: DeploymentRisk{
			Level:  "low",
			Score:  0.2,
			PrimaryRisks: []string{
				"Minor performance regression possible",
			},
			MitigationSteps: []string{
				"Monitor latency metrics",
				"Have rollback plan ready",
			},
		},
		PredictedIssues: []PredictedIssue{},
	}

	// Analyze AI response for deployment decision
	analysisUpper := strings.ToUpper(analysis)

	// Determine GO/NO-GO based on AI analysis
	if strings.Contains(analysisUpper, "BLOCK") || strings.Contains(analysisUpper, "FAIL") ||
	   strings.Contains(analysisUpper, "CRITICAL") || strings.Contains(analysisUpper, "NO-GO") {
		result.GoNoGo = "NO-GO"
		result.RollbackTrigger = true
		result.RollbackReason = "AI analysis detected critical issues"
		result.Confidence = 0.3
		result.RiskAssessment.Level = "critical"
		result.RiskAssessment.Score = 0.9
	} else if strings.Contains(analysisUpper, "CAUTION") || strings.Contains(analysisUpper, "WARNING") ||
	          strings.Contains(analysisUpper, "RISK") {
		result.GoNoGo = "GO"
		result.Confidence = 0.7
		result.RiskAssessment.Level = "medium"
		result.RiskAssessment.Score = 0.5
		result.Recommendations = append(result.Recommendations,
			"Close monitoring required during rollout",
			"Consider canary deployment strategy")
	}

	// Extract predicted issues from AI analysis
	result.PredictedIssues = extractPredictedIssues(analysis)

	// Update gate results based on AI analysis
	updateGateResults(result, analysis)

	logger.Info("Deployment validated with AI",
		"service", req.ServiceName,
		"go_nogo", result.GoNoGo,
		"confidence", result.Confidence,
		"risk_level", result.RiskAssessment.Level)

	return result, nil
}

// extractPredictedIssues parses AI analysis for potential deployment issues
func extractPredictedIssues(analysis string) []PredictedIssue {
	issues := []PredictedIssue{}

	analysisLower := strings.ToLower(analysis)

	// Look for common deployment issue patterns
	if strings.Contains(analysisLower, "latency") || strings.Contains(analysisLower, "slow") {
		issues = append(issues, PredictedIssue{
			Issue:         "Performance degradation",
			Probability:   0.3,
			Impact:        "medium",
			DetectionGate: "golden_signals",
		})
	}

	if strings.Contains(analysisLower, "error") || strings.Contains(analysisLower, "fail") {
		issues = append(issues, PredictedIssue{
			Issue:         "Increased error rates",
			Probability:   0.4,
			Impact:        "high",
			DetectionGate: "golden_signals",
		})
	}

	if strings.Contains(analysisLower, "resource") || strings.Contains(analysisLower, "cpu") || strings.Contains(analysisLower, "memory") {
		issues = append(issues, PredictedIssue{
			Issue:         "Resource exhaustion",
			Probability:   0.2,
			Impact:        "high",
			DetectionGate: "health",
		})
	}

	if strings.Contains(analysisLower, "database") || strings.Contains(analysisLower, "connection") {
		issues = append(issues, PredictedIssue{
			Issue:         "Database connectivity issues",
			Probability:   0.3,
			Impact:        "critical",
			DetectionGate: "business_metrics",
		})
	}

	return issues
}

// updateGateResults updates validation gates based on AI analysis
func updateGateResults(result *DeploymentValidationResult, analysis string) {
	analysisLower := strings.ToLower(analysis)

	// Update gate results based on analysis content
	if strings.Contains(analysisLower, "smoke fail") || strings.Contains(analysisLower, "test fail") {
		result.GateResults["smoke"] = "fail"
		if result.GoNoGo == "GO" {
			result.GoNoGo = "NO-GO"
			result.RollbackTrigger = true
			result.RollbackReason = "Smoke tests predicted to fail"
		}
	}

	if strings.Contains(analysisLower, "health fail") || strings.Contains(analysisLower, "unhealthy") {
		result.GateResults["health"] = "fail"
		if result.GoNoGo == "GO" {
			result.GoNoGo = "NO-GO"
			result.RollbackTrigger = true
			result.RollbackReason = "Health checks predicted to fail"
		}
	}

	if strings.Contains(analysisLower, "latency") || strings.Contains(analysisLower, "performance") {
		if strings.Contains(analysisLower, "high") || strings.Contains(analysisLower, "increase") {
			result.GateResults["golden_signals"] = "caution"
		}
	}
}

// ValidateCanaryPromotion uses AI to analyze canary deployment metrics and recommend promotion
func ValidateCanaryPromotion(ctx context.Context, canaryMetrics map[string]interface{}, baselineMetrics map[string]interface{}) (bool, error) {
	req := AIAnalysisRequest{
		Task: "Analyze canary deployment metrics and recommend whether to promote or rollback",
		Context: "Compare canary metrics against baseline, assess stability, and provide GO/NO-GO recommendation for full rollout",
		Data: map[string]interface{}{
			"canary_metrics":  canaryMetrics,
			"baseline_metrics": baselineMetrics,
		},
	}

	resp, err := AnalyzeIncidentWithAI(ctx, req)
	if err != nil {
		return false, err // Default to no promotion on error
	}

	// Determine promotion recommendation from AI analysis
	analysis := strings.ToLower(resp.Analysis)

	if strings.Contains(analysis, "promote") || strings.Contains(analysis, "go") || strings.Contains(analysis, "proceed") {
		return true, nil
	}

	return false, nil
}

// PredictDeploymentSuccess uses AI to predict deployment outcome before execution
func PredictDeploymentSuccess(ctx context.Context, preDeployData map[string]interface{}) (float64, error) {
	req := AIAnalysisRequest{
		Task: "Predict the success probability of this deployment based on historical data and current conditions",
		Context: "Analyze code changes, test results, infrastructure health, and historical patterns to predict deployment success rate",
		Data: preDeployData,
	}

	resp, err := AnalyzeIncidentWithAI(ctx, req)
	if err != nil {
		return 0.5, err // Default 50% confidence
	}

	// Extract success probability from AI response
	analysis := resp.Analysis

	// Simple parsing - look for percentage or confidence indicators
	if strings.Contains(analysis, "90%") || strings.Contains(analysis, "high confidence") {
		return 0.9, nil
	} else if strings.Contains(analysis, "80%") || strings.Contains(analysis, "good chance") {
		return 0.8, nil
	} else if strings.Contains(analysis, "70%") || strings.Contains(analysis, "moderate") {
		return 0.7, nil
	} else if strings.Contains(analysis, "60%") || strings.Contains(analysis, "fair") {
		return 0.6, nil
	} else if strings.Contains(analysis, "50%") || strings.Contains(analysis, "uncertain") {
		return 0.5, nil
	} else if strings.Contains(analysis, "40%") || strings.Contains(analysis, "low") {
		return 0.4, nil
	} else if strings.Contains(analysis, "30%") || strings.Contains(analysis, "poor") {
		return 0.3, nil
	} else if strings.Contains(analysis, "20%") || strings.Contains(analysis, "very low") {
		return 0.2, nil
	} else if strings.Contains(analysis, "10%") || strings.Contains(analysis, "critical") {
		return 0.1, nil
	}

	// Default based on sentiment
	if strings.Contains(strings.ToLower(analysis), "successful") || strings.Contains(strings.ToLower(analysis), "success") {
		return 0.8, nil
	} else if strings.Contains(strings.ToLower(analysis), "risky") || strings.Contains(strings.ToLower(analysis), "concern") {
		return 0.4, nil
	}

	return 0.7, nil // Default moderate confidence
}
