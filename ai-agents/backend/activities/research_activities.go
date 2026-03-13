package activities

import (
	"context"
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// GenerateResearchPlanActivity generates a research plan
func GenerateResearchPlanActivity(ctx context.Context, query string, researchType string, contextData map[string]interface{}) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating research plan", "query", query, "type", researchType)

	// Mock research plan generation
	plan := map[string]interface{}{
		"query":        query,
		"researchType": researchType,
		"phases": []string{
			"planning",
			"discovery", 
			"knowledge_graph",
			"analysis",
			"synthesis",
			"streaming",
		},
		"estimatedDuration": "15-30 minutes",
		"requiredAgents": []string{
			"web-search-agent",
			"database-search-agent", 
			"content-analysis-agent",
			"pattern-analysis-agent",
			"sentiment-analysis-agent",
			"synthesis-agent",
		},
		"maxSources":     20,
		"maxDepth":       3,
		"confidence":     0.85,
		"complexity":     "medium",
		"estimatedFindings": 8,
	}

	logger.Info("Research plan generated", "phases", len(plan["phases"].([]string)))
	return plan, nil
}

// DiscoverWebSourcesActivity discovers web sources
func DiscoverWebSourcesActivity(ctx context.Context, query string, maxSources int) ([]types.ResearchSource, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Discovering web sources", "query", query, "maxSources", maxSources)

	// Mock web source discovery
	time.Sleep(time.Millisecond * 500) // Simulate API call

	sources := []types.ResearchSource{
		{
			ID:          "web_1",
			Title:       fmt.Sprintf("Research Article about %s", query),
			URL:         "https://example.com/research-article-1",
			Content:     fmt.Sprintf("This is a comprehensive research article about %s. It contains detailed analysis and findings...", query),
			Relevance:   0.9,
			Credibility: 0.85,
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"sourceType": "academic",
				"published":  "2024-01-15",
				"authors":    []string{"Dr. Smith", "Dr. Johnson"},
			},
		},
		{
			ID:          "web_2",
			Title:       fmt.Sprintf("Industry Report on %s", query),
			URL:         "https://example.com/industry-report-1",
			Content:     fmt.Sprintf("Industry analysis report covering %s with market trends and forecasts...", query),
			Relevance:   0.8,
			Credibility: 0.9,
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"sourceType": "industry",
				"published":  "2024-02-01",
				"publisher":  "Market Research Inc",
			},
		},
		{
			ID:          "web_3",
			Title:       fmt.Sprintf("News Article: Latest %s Developments", query),
			URL:         "https://example.com/news-article-1",
			Content:     fmt.Sprintf("Breaking news and recent developments in %s including expert opinions...", query),
			Relevance:   0.75,
			Credibility: 0.7,
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"sourceType": "news",
				"published":  "2024-03-10",
				"outlet":     "Tech News Daily",
			},
		},
	}

	// Limit to maxSources
	if len(sources) > maxSources {
		sources = sources[:maxSources]
	}

	logger.Info("Web sources discovered", "count", len(sources))
	return sources, nil
}

// DiscoverDatabaseSourcesActivity discovers database sources
func DiscoverDatabaseSourcesActivity(ctx context.Context, query string, maxSources int) ([]types.ResearchSource, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Discovering database sources", "query", query, "maxSources", maxSources)

	// Mock database source discovery
	time.Sleep(time.Millisecond * 300) // Simulate database query

	sources := []types.ResearchSource{
		{
			ID:          "db_1",
			Title:       fmt.Sprintf("Internal Database Entry: %s Analysis", query),
			URL:         "internal://database/entry/12345",
			Content:     fmt.Sprintf("Internal analysis data for %s including historical trends and metrics...", query),
			Relevance:   0.95,
			Credibility: 0.95,
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"sourceType": "internal",
				"database":   "analytics",
				"table":      "research_data",
				"recordId":   "12345",
			},
		},
		{
			ID:          "db_2",
			Title:       fmt.Sprintf("Customer Feedback Data: %s", query),
			URL:         "internal://database/entry/67890",
			Content:     fmt.Sprintf("Customer feedback and survey results related to %s with sentiment analysis...", query),
			Relevance:   0.85,
			Credibility: 0.9,
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"sourceType": "internal",
				"database":   "crm",
				"table":      "customer_feedback",
				"recordId":   "67890",
			},
		},
	}

	// Limit to maxSources
	if len(sources) > maxSources {
		sources = sources[:maxSources]
	}

	logger.Info("Database sources discovered", "count", len(sources))
	return sources, nil
}

// BuildKnowledgeGraphActivity builds a knowledge graph
func BuildKnowledgeGraphActivity(ctx context.Context, sources []types.ResearchSource, maxDepth int) ([]types.KnowledgeNode, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Building knowledge graph", "sources", len(sources), "maxDepth", maxDepth)

	// Mock knowledge graph construction
	time.Sleep(time.Millisecond * 800) // Simulate graph processing

	nodes := []types.KnowledgeNode{
		{
			ID:    "node_1",
			Label: "Main Topic",
			Type:  "concept",
			Properties: map[string]interface{}{
				"importance": 0.9,
				"category":   "primary",
			},
			Relationships: []types.KnowledgeEdge{
				{
					ID:     "edge_1",
					Source: "node_1",
					Target: "node_2",
					Type:   "relates_to",
					Weight: 0.8,
					Properties: map[string]interface{}{
						"strength": "strong",
					},
				},
			},
			CreatedAt: time.Now(),
		},
		{
			ID:    "node_2",
			Label: "Related Concept",
			Type:  "concept",
			Properties: map[string]interface{}{
				"importance": 0.7,
				"category":   "secondary",
			},
			Relationships: []types.KnowledgeEdge{
				{
					ID:     "edge_2",
					Source: "node_2",
					Target: "node_3",
					Type:   "influences",
					Weight: 0.6,
				},
			},
			CreatedAt: time.Now(),
		},
		{
			ID:    "node_3",
			Label: "Supporting Evidence",
			Type:  "evidence",
			Properties: map[string]interface{}{
				"importance": 0.6,
				"category":   "supporting",
			},
			Relationships: []types.KnowledgeEdge{},
			CreatedAt:    time.Now(),
		},
	}

	logger.Info("Knowledge graph built", "nodes", len(nodes), "edges", countEdges(nodes))
	return nodes, nil
}

// AnalyzeContentActivity analyzes content from sources
func AnalyzeContentActivity(ctx context.Context, sources []types.ResearchSource, query string) ([]types.ResearchFinding, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing content", "sources", len(sources))

	// Mock content analysis
	time.Sleep(time.Millisecond * 600)

	findings := []types.ResearchFinding{
		{
			ID:          "finding_1",
			Title:       "Key Trend Identified",
			Description: fmt.Sprintf("Analysis of sources reveals a significant trend related to %s", query),
			Confidence:  0.85,
			Sources:     []string{"web_1", "db_1"},
			Category:    "trends",
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"analysisType": "content",
				"method":       "semantic_analysis",
			},
		},
		{
			ID:          "finding_2",
			Title:       "Statistical Correlation",
			Description: fmt.Sprintf("Strong statistical correlation found between %s and business outcomes", query),
			Confidence:  0.9,
			Sources:     []string{"db_1", "db_2"},
			Category:    "statistics",
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"analysisType": "content",
				"method":       "statistical_analysis",
			},
		},
	}

	logger.Info("Content analysis completed", "findings", len(findings))
	return findings, nil
}

// AnalyzePatternsActivity analyzes patterns in data
func AnalyzePatternsActivity(ctx context.Context, sources []types.ResearchSource, knowledgeGraph []types.KnowledgeNode) ([]types.ResearchFinding, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing patterns", "sources", len(sources), "nodes", len(knowledgeGraph))

	// Mock pattern analysis
	time.Sleep(time.Millisecond * 700)

	findings := []types.ResearchFinding{
		{
			ID:          "pattern_1",
			Title:       "Recurring Pattern Detected",
			Description: "Analysis reveals a recurring pattern across multiple data sources",
			Confidence:  0.8,
			Sources:     []string{"web_1", "web_2"},
			Category:    "patterns",
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"analysisType": "pattern",
				"method":       "time_series_analysis",
			},
		},
		{
			ID:          "pattern_2",
			Title:       "Network Pattern Identified",
			Description: "Knowledge graph analysis reveals significant network patterns",
			Confidence:  0.75,
			Sources:     []string{"db_1"},
			Category:    "network",
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"analysisType": "pattern",
				"method":       "graph_analysis",
			},
		},
	}

	logger.Info("Pattern analysis completed", "findings", len(findings))
	return findings, nil
}

// AnalyzeSentimentActivity analyzes sentiment in sources
func AnalyzeSentimentActivity(ctx context.Context, sources []types.ResearchSource) ([]types.ResearchFinding, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Analyzing sentiment", "sources", len(sources))

	// Mock sentiment analysis
	time.Sleep(time.Millisecond * 400)

	findings := []types.ResearchFinding{
		{
			ID:          "sentiment_1",
			Title:       "Overall Sentiment Analysis",
			Description: "Sentiment analysis across sources shows predominantly positive outlook",
			Confidence:  0.7,
			Sources:     []string{"web_3", "db_2"},
			Category:    "sentiment",
			Timestamp:   time.Now(),
			Metadata: map[string]interface{}{
				"analysisType": "sentiment",
				"method":       "nlp_sentiment",
				"sentiment":    "positive",
			},
		},
	}

	logger.Info("Sentiment analysis completed", "findings", len(findings))
	return findings, nil
}

// GenerateSynthesisActivity generates final synthesis
func GenerateSynthesisActivity(ctx context.Context, query string, sources []types.ResearchSource, findings []types.ResearchFinding, knowledgeGraph []types.KnowledgeNode, llmProvider string, llmModel string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Generating synthesis", "query", query, "sources", len(sources), "findings", len(findings))

	// Mock synthesis generation
	time.Sleep(time.Millisecond * 1000)

	synthesis := fmt.Sprintf(`# Research Synthesis: %s

## Executive Summary
Based on comprehensive analysis of %d sources and %d key findings, this research provides valuable insights into %s.

## Key Findings
1. **Primary Trend**: Analysis reveals significant patterns and trends related to the research topic
2. **Statistical Evidence**: Strong correlations and statistical evidence support the conclusions
3. **Pattern Recognition**: Recurring patterns identified across multiple data sources
4. **Sentiment Analysis**: Overall sentiment analysis indicates positive outlook

## Data Sources
The research utilized %d high-quality sources including:
- Academic research articles
- Industry reports and analysis
- Internal database records
- Customer feedback data

## Knowledge Graph Insights
Analysis of the knowledge graph reveals %d interconnected concepts and relationships, providing a comprehensive understanding of the topic landscape.

## Conclusion
This comprehensive research analysis provides actionable insights into %s, supported by robust data analysis and multiple analytical approaches. The findings suggest clear opportunities for further investigation and practical application.

## Confidence Level
Overall confidence in these findings: 85%%
`, query, len(sources), len(findings), query, len(sources), len(knowledgeGraph), query)

	logger.Info("Synthesis generated", "length", len(synthesis))
	return synthesis, nil
}

// StreamResearchEventsActivity streams research events
func StreamResearchEventsActivity(ctx context.Context, events []types.ResearchEvent, query string) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Streaming research events", "eventCount", len(events), "query", query)

	// Mock event streaming (in real implementation would stream to event bus)
	for _, event := range events {
		logger.Info("Streaming event", "type", event.Type, "message", event.Message)
		
		// Simulate streaming delay
		time.Sleep(time.Millisecond * 100)
	}

	logger.Info("Event streaming completed", "totalEvents", len(events))
	return nil
}

// ValidateResearchSourceActivity validates a research source
func ValidateResearchSourceActivity(ctx context.Context, source types.ResearchSource) (*types.ValidationResult, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Validating research source", "sourceId", source.ID)

	var errors []string
	isValid := true

	// Validate source fields
	if source.ID == "" {
		errors = append(errors, "source ID is required")
		isValid = false
	}

	if source.Title == "" {
		errors = append(errors, "source title is required")
		isValid = false
	}

	if source.URL == "" {
		errors = append(errors, "source URL is required")
		isValid = false
	}

	if source.Relevance < 0 || source.Relevance > 1 {
		errors = append(errors, "relevance must be between 0 and 1")
		isValid = false
	}

	if source.Credibility < 0 || source.Credibility > 1 {
		errors = append(errors, "credibility must be between 0 and 1")
		isValid = false
	}

	logger.Info("Source validation completed", "valid", isValid, "errors", len(errors))
	return &types.ValidationResult{
		IsValid: isValid,
		Errors:  errors,
	}, nil
}

// CalculateResearchQualityActivity calculates research quality metrics
func CalculateResearchQualityActivity(ctx context.Context, state types.ResearchState) (map[string]interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Calculating research quality metrics")

	quality := map[string]interface{}{
		"sourceQuality": calculateSourceQuality(state.Sources),
		"findingQuality": calculateFindingQuality(state.Findings),
		"graphQuality": calculateGraphQuality(state.KnowledgeGraph),
		"overallQuality": calculateOverallQuality(state),
		"agentCollaborationScore": calculateCollaborationScore(state.AgentCollaboration),
		"eventStreamCompleteness": calculateEventCompleteness(state.EventStream),
	}

	logger.Info("Research quality calculated", "overallQuality", quality["overallQuality"])
	return quality, nil
}

// Helper functions

func countEdges(nodes []types.KnowledgeNode) int {
	count := 0
	for _, node := range nodes {
		count += len(node.Relationships)
	}
	return count
}

func calculateSourceQuality(sources []types.ResearchSource) float64 {
	if len(sources) == 0 {
		return 0
	}

	totalRelevance := 0.0
	totalCredibility := 0.0

	for _, source := range sources {
		totalRelevance += source.Relevance
		totalCredibility += source.Credibility
	}

	avgRelevance := totalRelevance / float64(len(sources))
	avgCredibility := totalCredibility / float64(len(sources))

	return (avgRelevance + avgCredibility) / 2
}

func calculateFindingQuality(findings []types.ResearchFinding) float64 {
	if len(findings) == 0 {
		return 0
	}

	totalConfidence := 0.0
	for _, finding := range findings {
		totalConfidence += finding.Confidence
	}

	return totalConfidence / float64(len(findings))
}

func calculateGraphQuality(nodes []types.KnowledgeNode) float64 {
	if len(nodes) == 0 {
		return 0
	}

	// Simple quality metric based on node count and connectivity
	nodeScore := float64(len(nodes)) / 10.0 // Normalize to 0-1 range
	edgeScore := float64(countEdges(nodes)) / 20.0 // Normalize to 0-1 range

	quality := (nodeScore + edgeScore) / 2
	if quality > 1 {
		quality = 1
	}

	return quality
}

func calculateOverallQuality(state types.ResearchState) float64 {
	sourceQuality := calculateSourceQuality(state.Sources)
	findingQuality := calculateFindingQuality(state.Findings)
	graphQuality := calculateGraphQuality(state.KnowledgeGraph)

	return (sourceQuality + findingQuality + graphQuality) / 3
}

func calculateCollaborationScore(contributions []types.AgentContribution) float64 {
	if len(contributions) == 0 {
		return 0
	}

	totalConfidence := 0.0
	for _, contribution := range contributions {
		totalConfidence += contribution.Confidence
	}

	return totalConfidence / float64(len(contributions))
}

func calculateEventCompleteness(events []types.ResearchEvent) float64 {
	expectedPhases := []string{"planning", "discovery", "knowledge_graph", "analysis", "synthesis", "streaming"}
	completedPhases := make(map[string]bool)

	for _, event := range events {
		if event.Type == "phase_complete" {
			completedPhases[event.Message] = true
		}
	}

	completedCount := 0
	for _, phase := range expectedPhases {
		for eventMessage := range completedPhases {
			if strings.Contains(eventMessage, phase) {
				completedCount++
				break
			}
		}
	}

	return float64(completedCount) / float64(len(expectedPhases))
}
