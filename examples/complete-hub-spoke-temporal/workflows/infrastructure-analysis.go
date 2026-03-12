package workflows

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

// InfrastructureAnalysisInput represents input for infrastructure analysis
type InfrastructureAnalysisInput struct {
	ResourceType    string            `json:"resourceType"`
	CloudProviders  []string          `json:"cloudProviders"`
	AnalysisDepth   string            `json:"analysisDepth"` // "basic", "detailed", "comprehensive"
	Parameters      map[string]string `json:"parameters"`
}

// InfrastructureAnalysisOutput represents the result of infrastructure analysis
type InfrastructureAnalysisOutput struct {
	AnalysisID      string                    `json:"analysisId"`
	Timestamp       time.Time                 `json:"timestamp"`
	ResourceType    string                    `json:"resourceType"`
	Findings        []InfrastructureFinding     `json:"findings"`
	Recommendations []InfrastructureRecommendation `json:"recommendations"`
	RiskScore       float64                   `json:"riskScore"`
	CostImpact      float64                   `json:"costImpact"`
	Summary        string                    `json:"summary"`
}

// InfrastructureFinding represents a single finding from analysis
type InfrastructureFinding struct {
	ID          string                 `json:"id"`
	Severity    string                 `json:"severity"` // "low", "medium", "high", "critical"
	Category    string                 `json:"category"` // "security", "performance", "cost", "compliance"
	ResourceID  string                 `json:"resourceId"`
	Description string                 `json:"description"`
	Impact     string                 `json:"impact"`
	Remediation string                 `json:"remediation"`
	Metadata    map[string]interface{}  `json:"metadata"`
}

// InfrastructureRecommendation represents an optimization recommendation
type InfrastructureRecommendation struct {
	ID          string  `json:"id"`
	Priority    string  `json:"priority"` // "low", "medium", "high", "urgent"`
	Category    string  `json:"category"`
	Title       string  `json:"title"`
	Description string  `json:"description"`
	Savings     float64 `json:"savings"`
	Impact      string  `json:"impact"`
	Effort      string  `json:"effort"` // "low", "medium", "high"
}

// InfrastructureAnalysisWorkflow implements durable infrastructure analysis with AI
func InfrastructureAnalysisWorkflow(ctx workflow.Context, input InfrastructureAnalysisInput) (*InfrastructureAnalysisOutput, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting infrastructure analysis workflow", "resourceType", input.ResourceType)

	// Generate unique analysis ID
	analysisID := fmt.Sprintf("infra-analysis-%d", workflow.Now(ctx).Unix())
	
	output := &InfrastructureAnalysisOutput{
		AnalysisID:   analysisID,
		Timestamp:    workflow.Now(ctx),
		ResourceType: input.ResourceType,
		Findings:     []InfrastructureFinding{},
		Recommendations: []InfrastructureRecommendation{},
	}

	// Phase 1: Multi-cloud scatter/gather analysis
	logger.Info("Starting multi-cloud scatter/gather analysis")
	
	// Scatter: Query all cloud providers in parallel
	var cloudFutures []workflow.Future
	for _, provider := range input.CloudProviders {
		provider := provider // Capture for closure
		future := workflow.ExecuteActivity(ctx, activities.QueryCloudProviderActivity, CloudQueryInput{
			Provider:     provider,
			ResourceType: input.ResourceType,
			AnalysisDepth: input.AnalysisDepth,
			Parameters:   input.Parameters,
		})
		cloudFutures = append(cloudFutures, future)
	}

	// Gather: Collect results from all providers
	var cloudResults []CloudQueryResult
	for _, future := range cloudFutures {
		var result CloudQueryResult
		if err := future.Get(ctx, &result); err != nil {
			logger.Error("Cloud provider query failed", "provider", result.Provider, "error", err)
			// Continue with other providers - fault tolerance
			continue
		}
		cloudResults = append(cloudResults, result)
	}

	// Phase 2: AI-enhanced analysis of collected data
	logger.Info("Starting AI-enhanced analysis")
	
	aiAnalysisInput := AIAnalysisInput{
		CloudResults:   cloudResults,
		ResourceType:   input.ResourceType,
		AnalysisDepth:   input.AnalysisDepth,
		AnalysisID:     analysisID,
	}
	
	var aiAnalysis AIAnalysisResult
	err := workflow.ExecuteActivity(ctx, activities.AIAnalysisActivity, aiAnalysisInput).Get(ctx, &aiAnalysis)
	if err != nil {
		logger.Error("AI analysis failed", "error", err)
		return nil, fmt.Errorf("AI analysis failed: %w", err)
	}

	// Phase 3: Risk assessment and scoring
	logger.Info("Performing risk assessment")
	
	riskAssessmentInput := RiskAssessmentInput{
		Findings:     aiAnalysis.Findings,
		CloudResults:  cloudResults,
		ResourceType: input.ResourceType,
	}
	
	var riskAssessment RiskAssessmentResult
	err = workflow.ExecuteActivity(ctx, activities.RiskAssessmentActivity, riskAssessmentInput).Get(ctx, &riskAssessment)
	if err != nil {
		logger.Error("Risk assessment failed", "error", err)
		return nil, fmt.Errorf("risk assessment failed: %w", err)
	}

	// Phase 4: Generate optimization recommendations
	logger.Info("Generating optimization recommendations")
	
	recommendationInput := RecommendationInput{
		Findings:       aiAnalysis.Findings,
		RiskAssessment: riskAssessment,
		CostData:       aggregateCostData(cloudResults),
		ResourceType:    input.ResourceType,
	}
	
	var recommendations []InfrastructureRecommendation
	err = workflow.ExecuteActivity(ctx, activities.GenerateRecommendationsActivity, recommendationInput).Get(ctx, &recommendations)
	if err != nil {
		logger.Error("Recommendation generation failed", "error", err)
		return nil, fmt.Errorf("recommendation generation failed: %w", err)
	}

	// Phase 5: Human approval for high-risk changes
	if riskAssessment.OverallRiskScore > 7.0 {
		logger.Info("High risk detected, requiring human approval")
		
		approvalInput := HumanApprovalInput{
			AnalysisID:     analysisID,
			RiskScore:      riskAssessment.OverallRiskScore,
			Findings:       aiAnalysis.Findings,
			Recommendations: recommendations,
			Timeout:        24 * time.Hour, // 24 hour approval window
		}
		
		var approved bool
		err = workflow.ExecuteActivity(ctx, activities.RequestHumanApprovalActivity, approvalInput).Get(ctx, &approved)
		if err != nil {
			return nil, fmt.Errorf("human approval process failed: %w", err)
		}
		
		if !approved {
			logger.Info("Human approval denied, terminating workflow")
			return nil, fmt.Errorf("analysis rejected by human approver")
		}
	}

	// Compile final output
	output.Findings = aiAnalysis.Findings
	output.Recommendations = recommendations
	output.RiskScore = riskAssessment.OverallRiskScore
	output.CostImpact = calculateCostImpact(recommendations)
	output.Summary = generateSummary(aiAnalysis, riskAssessment, recommendations)

	logger.Info("Infrastructure analysis completed", 
		"analysisID", analysisID,
		"findingsCount", len(output.Findings),
		"recommendationsCount", len(output.Recommendations),
		"riskScore", output.RiskScore)

	return output, nil
}

// CloudQueryInput represents input for cloud provider queries
type CloudQueryInput struct {
	Provider     string            `json:"provider"`
	ResourceType string            `json:"resourceType"`
	AnalysisDepth string            `json:"analysisDepth"`
	Parameters   map[string]string `json:"parameters"`
}

// CloudQueryResult represents results from a single cloud provider
type CloudQueryResult struct {
	Provider      string                 `json:"provider"`
	ResourceType  string                 `json:"resourceType"`
	Resources     []CloudResource         `json:"resources"`
	Metrics       CloudMetrics            `json:"metrics"`
	QueryTime     time.Time               `json:"queryTime"`
	Error         string                  `json:"error,omitempty"`
}

// CloudResource represents a cloud infrastructure resource
type CloudResource struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Type         string                 `json:"type"`
	Region       string                 `json:"region"`
	Status       string                 `json:"status"`
	Cost         float64                `json:"cost"`
	Tags         map[string]string      `json:"tags"`
	Configuration map[string]interface{} `json:"configuration"`
}

// CloudMetrics represents metrics for cloud resources
type CloudMetrics struct {
	TotalResources int     `json:"totalResources"`
	TotalCost     float64 `json:"totalCost"`
	Uptime        float64 `json:"uptime"`
	Performance   float64 `json:"performance"`
	SecurityScore float64 `json:"securityScore"`
}

// AIAnalysisInput represents input for AI analysis
type AIAnalysisInput struct {
	CloudResults   []CloudQueryResult `json:"cloudResults"`
	ResourceType   string           `json:"resourceType"`
	AnalysisDepth   string           `json:"analysisDepth"`
	AnalysisID     string           `json:"analysisId"`
}

// AIAnalysisResult represents AI analysis output
type AIAnalysisResult struct {
	AnalysisID     string                    `json:"analysisId"`
	Findings        []InfrastructureFinding    `json:"findings"`
	Anomalies       []Anomaly                `json:"anomalies"`
	Patterns        []Pattern                `json:"patterns"`
	Confidence      float64                  `json:"confidence"`
	ModelUsed       string                   `json:"modelUsed"`
	ProcessingTime  time.Duration            `json:"processingTime"`
}

// RiskAssessmentInput represents input for risk assessment
type RiskAssessmentInput struct {
	Findings     []InfrastructureFinding `json:"findings"`
	CloudResults  []CloudQueryResult     `json:"cloudResults"`
	ResourceType string                 `json:"resourceType"`
}

// RiskAssessmentResult represents risk assessment output
type RiskAssessmentResult struct {
	OverallRiskScore    float64                  `json:"overallRiskScore"`
	SecurityRisk       float64                  `json:"securityRisk"`
	PerformanceRisk    float64                  `json:"performanceRisk"`
	CostRisk          float64                  `json:"costRisk"`
	ComplianceRisk     float64                  `json:"complianceRisk"`
	RiskFactors        []RiskFactor             `json:"riskFactors"`
	MitigationStrategies []MitigationStrategy   `json:"mitigationStrategies"`
}

// Helper functions
func aggregateCostData(results []CloudQueryResult) map[string]float64 {
	costData := make(map[string]float64)
	for _, result := range results {
		costData[result.Provider] = result.Metrics.TotalCost
	}
	return costData
}

func calculateCostImpact(recommendations []InfrastructureRecommendation) float64 {
	var totalImpact float64
	for _, rec := range recommendations {
		totalImpact += rec.Savings
	}
	return totalImpact
}

func generateSummary(aiAnalysis AIAnalysisResult, riskAssessment RiskAssessmentResult, recommendations []InfrastructureRecommendation) string {
	return fmt.Sprintf("Analysis completed with %d findings, %.2f risk score, and %d recommendations. %s",
		len(aiAnalysis.Findings),
		riskAssessment.OverallRiskScore,
		len(recommendations),
		aiAnalysis.ModelUsed)
}
