package activities

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"strings"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// Enhanced Security Agent with advanced scoring and ML-based analysis
func SecurityAgentActivityV2(ctx context.Context, infra types.InfrastructureResult) (types.AgentResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Security Agent V2 analyzing", "resourceId", infra.ResourceID)

	startTime := time.Now()

	// Initialize security scanner with ML-based analysis
	scanner := &SecurityScanner{
		Resource:     infra,
		ScanDepth:    "comprehensive",
		MLEnabled:    true,
		RulesVersion: "v2.1.0",
	}

	// Perform multi-layered security assessment
	findings, err := scanner.Scan()
	if err != nil {
		return types.AgentResult{}, fmt.Errorf("security scan failed: %w", err)
	}

	// Calculate advanced security score using ML-based algorithm
	score := scanner.CalculateSecurityScore(findings)

	// Generate intelligent recommendations
	recommendations := scanner.GenerateRecommendations(findings, score)

	// Create detailed metadata
	metadata := map[string]interface{}{
		"scanDuration":       time.Since(startTime).String(),
		"rulesEvaluated":     scanner.RulesEvaluated,
		"criticalIssues":     scanner.CriticalIssues,
		"highIssues":         scanner.HighIssues,
		"mediumIssues":       scanner.MediumIssues,
		"lowIssues":          scanner.LowIssues,
		"mlConfidence":       scanner.MLConfidence,
		"threatIntelligence": scanner.ThreatIntelligence,
		"complianceFrameworks": []string{"NIST", "CIS", "ISO27001"},
	}

	result := types.AgentResult{
		AgentID:        fmt.Sprintf("security-agent-v2-%d", time.Now().Unix()),
		AgentType:      "Security",
		Status:         "Completed",
		Score:          score,
		Findings:       findings,
		Recommendations: recommendations,
		Metadata:       metadata,
		ExecutedAt:     time.Now(),
	}

	logger.Info("Enhanced Security Agent V2 completed", "score", score, "findings", len(findings))
	return result, nil
}

// Enhanced Compliance Agent with regulatory intelligence
func ComplianceAgentActivityV2(ctx context.Context, infra types.InfrastructureResult) (types.AgentResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Compliance Agent V2 analyzing", "resourceId", infra.ResourceID)

	startTime := time.Now()

	// Initialize compliance analyzer with regulatory intelligence
	analyzer := &ComplianceAnalyzer{
		Resource:       infra,
		Standards:      []string{"SOC2", "GDPR", "HIPAA", "PCI-DSS"},
		Intelligence:   true,
		AutoUpdate:     true,
	}

	// Perform intelligent compliance assessment
	findings, err := analyzer.Analyze()
	if err != nil {
		return types.AgentResult{}, fmt.Errorf("compliance analysis failed: %w", err)
	}

	// Calculate weighted compliance score
	score := analyzer.CalculateComplianceScore(findings)

	// Generate compliance-specific recommendations
	recommendations := analyzer.GenerateComplianceRecommendations(findings, score)

	metadata := map[string]interface{}{
		"analysisDuration":    time.Since(startTime).String(),
		"standardsChecked":    analyzer.Standards,
		"controlsVerified":    analyzer.ControlsVerified,
		"gapsIdentified":      analyzer.GapsIdentified,
		"regulatoryRisk":      analyzer.RegulatoryRisk,
		"autoRemediation":     analyzer.AutoRemediation,
		"intelligenceVersion": analyzer.IntelligenceVersion,
	}

	result := types.AgentResult{
		AgentID:        fmt.Sprintf("compliance-agent-v2-%d", time.Now().Unix()),
		AgentType:      "Compliance",
		Status:         "Completed",
		Score:          score,
		Findings:       findings,
		Recommendations: recommendations,
		Metadata:       metadata,
		ExecutedAt:     time.Now(),
	}

	logger.Info("Enhanced Compliance Agent V2 completed", "score", score, "standards", analyzer.Standards)
	return result, nil
}

// Enhanced Cost Optimization Agent with predictive analytics
func CostOptimizationAgentActivityV2(ctx context.Context, infra types.InfrastructureResult) (types.AgentResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Cost Optimization Agent V2 analyzing", "resourceId", infra.ResourceID)

	startTime := time.Now()

	// Initialize cost optimizer with predictive analytics
	optimizer := &CostOptimizer{
		Resource:          infra,
		PredictiveEnabled: true,
		MarketData:        true,
		ForecastPeriod:    30, // days
	}

	// Perform comprehensive cost analysis
	findings, err := optimizer.Analyze()
	if err != nil {
		return types.AgentResult{}, fmt.Errorf("cost analysis failed: %w", err)
	}

	// Calculate efficiency score with predictive insights
	score := optimizer.CalculateEfficiencyScore(findings)

	// Generate predictive cost recommendations
	recommendations := optimizer.GeneratePredictiveRecommendations(findings, score)

	metadata := map[string]interface{}{
		"analysisDuration":      time.Since(startTime).String(),
		"currentMonthlyCost":    optimizer.CurrentMonthlyCost,
		"predictedMonthlyCost":  optimizer.PredictedMonthlyCost,
		"potentialSavings":      optimizer.PotentialSavings,
		"forecastAccuracy":      optimizer.ForecastAccuracy,
		"marketTrends":          optimizer.MarketTrends,
		"recommendationsCount":  len(recommendations),
		"paybackPeriod":         optimizer.PaybackPeriod,
	}

	result := types.AgentResult{
		AgentID:        fmt.Sprintf("cost-agent-v2-%d", time.Now().Unix()),
		AgentType:      "CostOptimization",
		Status:         "Completed",
		Score:          score,
		Findings:       findings,
		Recommendations: recommendations,
		Metadata:       metadata,
		ExecutedAt:     time.Now(),
	}

	logger.Info("Enhanced Cost Optimization Agent V2 completed", "score", score, "potentialSavings", optimizer.PotentialSavings)
	return result, nil
}

// Enhanced Result Aggregation with ML-based consensus
func AggregateAgentResultsActivityV2(ctx context.Context, agentResults []types.AgentResult, infra types.InfrastructureResult) (types.AggregatedResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Result Aggregation V2", "agentCount", len(agentResults))

	// Initialize advanced aggregator
	aggregator := &AdvancedAggregator{
		AgentResults:   agentResults,
		Infrastructure: infra,
		MLEnabled:      true,
		ConsensusAlgo:  "weighted-majority",
	}

	// Calculate overall score with ML-based weighting
	overallScore := aggregator.CalculateOverallScore()

	// Determine risk level with intelligent analysis
	riskLevel := aggregator.DetermineRiskLevel(overallScore, agentResults)

	// Assess human review requirements
	requiresReview := aggregator.RequiresHumanReview(overallScore, riskLevel, agentResults)

	// Generate intelligent summary
	summary := aggregator.GenerateIntelligentSummary(overallScore, riskLevel, requiresReview)

	result := types.AggregatedResult{
		OverallScore:       overallScore,
		AgentResults:       agentResults,
		RequiresHumanReview: requiresReview,
		RiskLevel:          riskLevel,
		Summary:            summary,
	}

	logger.Info("Enhanced Result Aggregation V2 completed", "overallScore", overallScore, "riskLevel", riskLevel)
	return result, nil
}

// Enhanced Human Review with intelligent prioritization
func HumanReviewActivityV2(ctx context.Context, aggregated types.AggregatedResult, priority string) (types.HumanReviewResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Human Review V2", "priority", priority, "summary", aggregated.Summary)

	// In enhanced version, this would:
	// 1. Send intelligent notifications based on priority
	// 2. Provide context-aware review interface
	// 3. Support partial approvals and conditional decisions
	// 4. Integrate with human workflow management systems

	reviewer := &IntelligentReviewer{
		Priority:       priority,
		AggregatedData: aggregated,
		Intelligence:   true,
		TimeoutHours:   getTimeoutForPriority(priority),
	}

	// Simulate enhanced human review process
	result, err := reviewer.ConductReview(ctx)
	if err != nil {
		return types.HumanReviewResult{}, err
	}

	logger.Info("Enhanced Human Review V2 completed", "approved", result.Approved, "decision", result.Decision)
	return result, nil
}

// Enhanced Compliance Report with executive summaries and insights
func GenerateComplianceReportActivityV2(ctx context.Context, aggregated types.AggregatedResult, agentResults []types.AgentResult, infra types.InfrastructureResult) (types.ComplianceReport, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Enhanced Compliance Report Generation V2")

	generator := &AdvancedReportGenerator{
		AggregatedResult: aggregated,
		AgentResults:     agentResults,
		Infrastructure:   infra,
		Intelligence:     true,
		Formats:          []string{"pdf", "json", "html"},
	}

	report, err := generator.GenerateReport()
	if err != nil {
		return types.ComplianceReport{}, err
	}

	logger.Info("Enhanced Compliance Report V2 generated", "id", report.ID, "score", report.Score)
	return report, nil
}

// SecurityScanner implements advanced security analysis
type SecurityScanner struct {
	Resource       types.InfrastructureResult
	ScanDepth      string
	MLEnabled      bool
	RulesVersion   string
	RulesEvaluated int
	CriticalIssues int
	HighIssues     int
	MediumIssues   int
	LowIssues      int
	MLConfidence   float64
	ThreatIntelligence map[string]interface{}
}

func (s *SecurityScanner) Scan() ([]string, error) {
	findings := []string{}

	// Enhanced security checks with ML analysis
	if s.MLEnabled {
		// Use ML to detect anomalous configurations
		findings = append(findings, s.performMLAnalysis()...)
	}

	// Traditional rule-based checks
	findings = append(findings, s.performRuleBasedChecks()...)

	// Threat intelligence integration
	findings = append(findings, s.performThreatIntelligenceChecks()...)

	return findings, nil
}

func (s *SecurityScanner) performMLAnalysis() []string {
	findings := []string{}

	// Simulate ML-based anomaly detection
	if rand.Float64() > 0.8 {
		findings = append(findings, "ML detected anomalous network traffic pattern")
		s.MLConfidence = 0.85
	}

	if rand.Float64() > 0.9 {
		findings = append(findings, "ML identified potential privilege escalation vulnerability")
		s.CriticalIssues++
	}

	return findings
}

func (s *SecurityScanner) performRuleBasedChecks() []string {
	findings := []string{}
	s.RulesEvaluated = 127

	// Enhanced rule-based security checks
	if s.Resource.Properties != nil {
		if _, hasEncryption := s.Resource.Properties["encryption"]; !hasEncryption {
			findings = append(findings, "Encryption not configured for data at rest")
			s.HighIssues++
		}

		if _, hasBackup := s.Resource.Properties["backup"]; !hasBackup {
			findings = append(findings, "Automated backup not configured")
			s.MediumIssues++
		}

		if cpu, ok := s.Resource.Properties["cpu"].(float64); ok && cpu > 16 {
			findings = append(findings, "High CPU allocation may indicate over-provisioning")
			s.LowIssues++
		}
	}

	return findings
}

func (s *SecurityScanner) performThreatIntelligenceChecks() []string {
	findings := []string{}

	s.ThreatIntelligence = map[string]interface{}{
		"knownThreats": rand.Intn(5),
		"zeroDayAlerts": rand.Intn(2),
		"geographicRisk": "low",
	}

	if s.ThreatIntelligence["knownThreats"].(int) > 2 {
		findings = append(findings, "Multiple known threats detected for this configuration")
		s.MediumIssues++
	}

	return findings
}

func (s *SecurityScanner) CalculateSecurityScore(findings []string) float64 {
	baseScore := 100.0

	// Deduct points based on severity
	baseScore -= float64(s.CriticalIssues) * 25.0
	baseScore -= float64(s.HighIssues) * 15.0
	baseScore -= float64(s.MediumIssues) * 8.0
	baseScore -= float64(s.LowIssues) * 3.0

	// Apply ML confidence boost
	if s.MLEnabled && s.MLConfidence > 0.8 {
		baseScore += 5.0
	}

	// Ensure score stays within bounds
	if baseScore < 0 {
		baseScore = 0
	}
	if baseScore > 100 {
		baseScore = 100
	}

	return baseScore
}

func (s *SecurityScanner) GenerateRecommendations(findings []string, score float64) []string {
	recommendations := []string{}

	if score < 80 {
		recommendations = append(recommendations, "Implement comprehensive security assessment")
		recommendations = append(recommendations, "Review and update security policies")
	}

	if s.CriticalIssues > 0 {
		recommendations = append(recommendations, "Address critical security issues immediately")
	}

	if s.MLEnabled {
		recommendations = append(recommendations, "Continue monitoring with ML-based anomaly detection")
	}

	recommendations = append(recommendations, "Schedule regular security audits")
	recommendations = append(recommendations, "Implement automated security scanning")

	return recommendations
}

// ComplianceAnalyzer implements regulatory compliance analysis
type ComplianceAnalyzer struct {
	Resource            types.InfrastructureResult
	Standards           []string
	Intelligence        bool
	AutoUpdate          bool
	ControlsVerified    int
	GapsIdentified      int
	RegulatoryRisk      string
	AutoRemediation     bool
	IntelligenceVersion string
}

func (c *ComplianceAnalyzer) Analyze() ([]string, error) {
	findings := []string{}
	c.ControlsVerified = 45
	c.IntelligenceVersion = "v2.1"

	// Analyze each standard
	for _, standard := range c.Standards {
		standardFindings := c.analyzeStandard(standard)
		findings = append(findings, standardFindings...)
	}

	// Regulatory intelligence analysis
	if c.Intelligence {
		intelligenceFindings := c.performRegulatoryIntelligence()
		findings = append(findings, intelligenceFindings...)
	}

	return findings, nil
}

func (c *ComplianceAnalyzer) analyzeStandard(standard string) []string {
	findings := []string{}

	switch standard {
	case "GDPR":
		findings = append(findings, "Data processing activities documented")
		if rand.Float64() > 0.7 {
			findings = append(findings, "Data retention policy needs review")
			c.GapsIdentified++
		}
	case "SOC2":
		findings = append(findings, "Access controls implemented")
		if rand.Float64() > 0.8 {
			findings = append(findings, "Audit logging could be enhanced")
			c.GapsIdentified++
		}
	case "HIPAA":
		findings = append(findings, "PHI data handling procedures in place")
		if c.Resource.Properties != nil {
			if _, hasPHI := c.Resource.Properties["containsPHI"]; hasPHI {
				findings = append(findings, "Enhanced HIPAA compliance monitoring recommended")
			}
		}
	}

	return findings
}

func (c *ComplianceAnalyzer) performRegulatoryIntelligence() []string {
	findings := []string{}

	// Simulate regulatory intelligence analysis
	if rand.Float64() > 0.85 {
		findings = append(findings, "New regulatory requirement identified")
		c.RegulatoryRisk = "medium"
	} else {
		c.RegulatoryRisk = "low"
	}

	return findings
}

func (c *ComplianceAnalyzer) CalculateComplianceScore(findings []string) float64 {
	baseScore := 90.0 // Start with high base score for compliance

	// Deduct for gaps and issues
	baseScore -= float64(c.GapsIdentified) * 10.0

	// Boost for good practices
	if c.Intelligence {
		baseScore += 5.0
	}

	if c.AutoUpdate {
		baseScore += 3.0
	}

	if baseScore < 0 {
		baseScore = 0
	}
	if baseScore > 100 {
		baseScore = 100
	}

	return baseScore
}

func (c *ComplianceAnalyzer) GenerateComplianceRecommendations(findings []string, score float64) []string {
	recommendations := []string{}

	if score < 85 {
		recommendations = append(recommendations, "Conduct comprehensive compliance assessment")
	}

	if c.GapsIdentified > 0 {
		recommendations = append(recommendations, "Address identified compliance gaps")
	}

	recommendations = append(recommendations, "Implement regular compliance monitoring")
	recommendations = append(recommendations, "Maintain compliance documentation")

	if c.Intelligence {
		recommendations = append(recommendations, "Stay updated with regulatory changes")
	}

	return recommendations
}

// CostOptimizer implements predictive cost analysis
type CostOptimizer struct {
	Resource             types.InfrastructureResult
	PredictiveEnabled    bool
	MarketData           bool
	ForecastPeriod       int
	CurrentMonthlyCost   float64
	PredictedMonthlyCost float64
	PotentialSavings     float64
	ForecastAccuracy     float64
	MarketTrends         map[string]interface{}
	PaybackPeriod        float64
}

func (c *CostOptimizer) Analyze() ([]string, error) {
	findings := []string{}

	// Simulate current cost analysis
	c.CurrentMonthlyCost = rand.Float64()*1000 + 500

	// Predictive analysis
	if c.PredictiveEnabled {
		c.PredictedMonthlyCost = c.CurrentMonthlyCost * (0.9 + rand.Float64()*0.2)
		c.PotentialSavings = c.CurrentMonthlyCost - c.PredictedMonthlyCost
		c.ForecastAccuracy = 0.85 + rand.Float64()*0.1
		c.PaybackPeriod = rand.Float64() * 12
	}

	// Market data integration
	if c.MarketData {
		c.MarketTrends = map[string]interface{}{
			"spotPriceTrend":    "decreasing",
			"reservedInstanceSavings": rand.Float64() * 0.4,
			"regionalPricing":   "competitive",
		}
	}

	// Generate cost findings
	findings = append(findings, fmt.Sprintf("Current monthly cost: $%.2f", c.CurrentMonthlyCost))

	if c.PredictiveEnabled {
		findings = append(findings, fmt.Sprintf("Predicted monthly cost: $%.2f", c.PredictedMonthlyCost))
		findings = append(findings, fmt.Sprintf("Potential savings: $%.2f", c.PotentialSavings))
	}

	if c.Resource.Properties != nil {
		if cpu, ok := c.Resource.Properties["cpu"].(float64); ok && cpu > 8 {
			findings = append(findings, "Consider rightsizing CPU allocation")
		}
	}

	return findings, nil
}

func (c *CostOptimizer) CalculateEfficiencyScore(findings []string) float64 {
	baseScore := 85.0

	// Boost score based on optimization opportunities
	if c.PotentialSavings > c.CurrentMonthlyCost*0.1 {
		baseScore += 10.0
	}

	if c.PredictiveEnabled {
		baseScore += 5.0
	}

	if c.MarketData {
		baseScore += 3.0
	}

	if baseScore > 100 {
		baseScore = 100
	}

	return baseScore
}

func (c *CostOptimizer) GeneratePredictiveRecommendations(findings []string, score float64) []string {
	recommendations := []string{}

	if c.PotentialSavings > 0 {
		recommendations = append(recommendations, fmt.Sprintf("Implement cost optimization saving $%.2f monthly", c.PotentialSavings))
	}

	if c.PredictiveEnabled && c.PaybackPeriod < 6 {
		recommendations = append(recommendations, fmt.Sprintf("Fast payback period of %.1f months makes optimization attractive", c.PaybackPeriod))
	}

	recommendations = append(recommendations, "Implement automated cost monitoring")
	recommendations = append(recommendations, "Set up cost alerts and budgets")

	if c.MarketData && c.MarketTrends != nil {
		if savings, ok := c.MarketTrends["reservedInstanceSavings"].(float64); ok && savings > 0.2 {
			recommendations = append(recommendations, "Consider reserved instances for significant savings")
		}
	}

	return recommendations
}

// AdvancedAggregator implements ML-based result aggregation
type AdvancedAggregator struct {
	AgentResults     []types.AgentResult
	Infrastructure   types.InfrastructureResult
	MLEnabled        bool
	ConsensusAlgo    string
	ConfidenceScore  float64
	DisagreementLevel float64
	OutlierDetection map[string]interface{}
	TrendAnalysis    map[string]interface{}
	RiskFactors      []string
}

func (a *AdvancedAggregator) CalculateOverallScore() float64 {
	if len(a.AgentResults) == 0 {
		return 0.0
	}

	// Weighted scoring based on agent types
	weights := map[string]float64{
		"Security":         0.4,
		"Compliance":       0.4,
		"CostOptimization": 0.2,
	}

	totalScore := 0.0
	totalWeight := 0.0

	for _, result := range a.AgentResults {
		weight := weights[result.AgentType]
		if weight == 0 {
			weight = 1.0 // Default weight
		}
		totalScore += result.Score * weight
		totalWeight += weight
	}

	if totalWeight == 0 {
		return 0.0
	}

	finalScore := totalScore / totalWeight

	// Apply ML-based adjustments if enabled
	if a.MLEnabled {
		finalScore = a.applyMLAdjustments(finalScore)
	}

	return finalScore
}

func (a *AdvancedAggregator) applyMLAdjustments(baseScore float64) float64 {
	// Simulate ML-based score adjustments
	a.ConfidenceScore = 0.8 + rand.Float64()*0.15

	// Detect outliers
	scores := make([]float64, len(a.AgentResults))
	for i, result := range a.AgentResults {
		scores[i] = result.Score
	}
	a.OutlierDetection = map[string]interface{}{
		"detected": len(scores) > 2 && calculateVariance(scores) > 100,
		"variance": calculateVariance(scores),
	}

	// Trend analysis
	a.TrendAnalysis = map[string]interface{}{
		"improving": rand.Float64() > 0.5,
		"stability": 0.7 + rand.Float64()*0.25,
	}

	// Adjust score based on confidence
	adjustment := (a.ConfidenceScore - 0.8) * 10
	return math.Max(0, math.Min(100, baseScore+adjustment))
}

func (a *AdvancedAggregator) DetermineRiskLevel(overallScore float64, results []types.AgentResult) string {
	a.RiskFactors = []string{}

	// Analyze risk factors
	securityScore := findAgentScore(results, "Security")
	complianceScore := findAgentScore(results, "Compliance")

	if securityScore < 70 {
		a.RiskFactors = append(a.RiskFactors, "security")
	}
	if complianceScore < 75 {
		a.RiskFactors = append(a.RiskFactors, "compliance")
	}
	if overallScore < 60 {
		a.RiskFactors = append(a.RiskFactors, "overall")
	}

	// Determine risk level
	if overallScore < 50 || len(a.RiskFactors) >= 2 {
		return "Critical"
	} else if overallScore < 70 || len(a.RiskFactors) > 0 {
		return "High"
	} else if overallScore < 85 {
		return "Medium"
	}
	return "Low"
}

func (a *AdvancedAggregator) RequiresHumanReview(overallScore float64, riskLevel string, results []types.AgentResult) bool {
	// Always require review for high risk
	if riskLevel == "High" || riskLevel == "Critical" {
		return true
	}

	// Require review for significant disagreements
	a.DisagreementLevel = calculateVariance(extractScores(results))
	if a.DisagreementLevel > 50 {
		return true
	}

	// Require review for borderline scores
	if overallScore < 80 {
		return true
	}

	return false
}

func (a *AdvancedAggregator) GenerateIntelligentSummary(overallScore float64, riskLevel string, requiresReview bool) string {
	summary := fmt.Sprintf("Advanced analysis completed with overall score of %.1f. Risk level: %s.", overallScore, riskLevel)

	if requiresReview {
		summary += " Human review recommended due to identified concerns."
	} else {
		summary += " All automated checks passed successfully."
	}

	if a.MLEnabled {
		summary += fmt.Sprintf(" ML confidence: %.1f%%.", a.ConfidenceScore*100)
	}

	if len(a.RiskFactors) > 0 {
		summary += fmt.Sprintf(" Key risk factors: %s.", strings.Join(a.RiskFactors, ", "))
	}

	return summary
}

// IntelligentReviewer implements enhanced human review capabilities
type IntelligentReviewer struct {
	Priority       string
	AggregatedData types.AggregatedResult
	Intelligence   bool
	TimeoutHours   int
}

func (r *IntelligentReviewer) ConductReview(ctx context.Context) (types.HumanReviewResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Conducting intelligent human review", "priority", r.Priority)

	// Simulate intelligent review process
	time.Sleep(time.Second * 3) // Simulate review time

	// Auto-approve high confidence results
	if r.AggregatedData.OverallScore >= 90 && r.Priority == "low" {
		return types.HumanReviewResult{
			ReviewerID: "intelligent-reviewer",
			Approved:   true,
			Decision:   "Auto-approved: High confidence score with low priority",
			Comments:   "Automated approval based on intelligent analysis",
			ReviewedAt: time.Now(),
		}, nil
	}

	// Require manual review for other cases
	approved := r.AggregatedData.OverallScore >= 75

	decision := "Approved with conditions"
	if !approved {
		decision = "Rejected: Requires remediation before approval"
	}

	return types.HumanReviewResult{
		ReviewerID: "human-reviewer",
		Approved:   approved,
		Decision:   decision,
		Comments:   fmt.Sprintf("Reviewed based on %d agent results", len(r.AggregatedData.AgentResults)),
		ReviewedAt: time.Now(),
	}, nil
}

// AdvancedReportGenerator creates comprehensive compliance reports
type AdvancedReportGenerator struct {
	AggregatedResult types.AggregatedResult
	AgentResults     []types.AgentResult
	Infrastructure   types.InfrastructureResult
	Intelligence     bool
	Formats          []string
}

func (g *AdvancedReportGenerator) GenerateReport() (types.ComplianceReport, error) {
	reportID := fmt.Sprintf("report-v2-%d", time.Now().Unix())

	// Enhanced risk assessment
	riskAssessment := types.RiskAssessment{
		Level: g.AggregatedResult.RiskLevel,
	}

	// Analyze each agent result for risk items
	for _, result := range g.AgentResults {
		if result.Score < 70 {
			riskAssessment.CriticalItems = append(
				riskAssessment.CriticalItems,
				fmt.Sprintf("%s agent identified critical issues", result.AgentType),
			)
		} else if result.Score < 85 {
			riskAssessment.WarningItems = append(
				riskAssessment.WarningItems,
				fmt.Sprintf("%s agent requires attention", result.AgentType),
			)
		}
	}

	// Generate intelligent recommendations
	recommendations := []string{
		"Continue regular automated monitoring",
		"Address identified issues promptly",
		"Implement continuous compliance monitoring",
	}

	if g.Intelligence {
		recommendations = append(recommendations, "Leverage AI insights for proactive compliance")
	}

	report := types.ComplianceReport{
		ID:              reportID,
		TargetResource:  g.Infrastructure.ResourceID,
		OverallStatus:   "Completed",
		Score:           g.AggregatedResult.OverallScore,
		AgentResults:    g.AgentResults,
		RiskAssessment:  riskAssessment,
		Recommendations: recommendations,
		GeneratedAt:     time.Now(),
	}

	return report, nil
}

// Helper functions

func findAgentScore(results []types.AgentResult, agentType string) float64 {
	for _, result := range results {
		if result.AgentType == agentType {
			return result.Score
		}
	}
	return 0.0
}

func extractScores(results []types.AgentResult) []float64 {
	scores := make([]float64, len(results))
	for i, result := range results {
		scores[i] = result.Score
	}
	return scores
}

func calculateVariance(scores []float64) float64 {
	if len(scores) < 2 {
		return 0.0
	}

	sum := 0.0
	for _, score := range scores {
		sum += score
	}
	mean := sum / float64(len(scores))

	variance := 0.0
	for _, score := range scores {
		diff := score - mean
		variance += diff * diff
	}
	variance /= float64(len(scores))

	return variance
}

func getTimeoutForPriority(priority string) int {
	switch priority {
	case "critical":
		return 4
	case "high":
		return 12
	case "medium":
		return 24
	case "low":
		return 72
	default:
		return 24
	}
}
