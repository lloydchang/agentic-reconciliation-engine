package workflows

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)



// DeepResearchWorkflow orchestrates multi-agent deep research
func DeepResearchWorkflow(ctx workflow.Context, request types.ResearchRequest) (*types.ResearchState, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Deep Research Workflow", "query", request.Query, "type", request.ResearchType)

	// Set activity options with retry policy
	activityOptions := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute * 15,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second * 3,
			BackoffCoefficient: 1.5,
			MaximumInterval:    time.Minute * 2,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, activityOptions)

	// Initialize research state
	state := &types.ResearchState{
		Query:              request.Query,
		ResearchType:       request.ResearchType,
		CurrentPhase:       "initialization",
		Status:             "running",
		Sources:            []types.ResearchSource{},
		KnowledgeGraph:     []types.KnowledgeNode{},
		Findings:           []types.ResearchFinding{},
		StartTime:          workflow.Now(ctx),
		LLMProvider:        request.LLMProvider,
		LLMModel:           request.LLMModel,
		Context:            request.Context,
		EventStream:        []types.ResearchEvent{},
		AgentCollaboration: []types.AgentContribution{},
	}

	// Phase 1: Query Analysis and Planning
	state.CurrentPhase = "planning"
	if err := executeResearchPlanning(ctx, state, request); err != nil {
		logger.Error("Research planning failed", "error", err)
		state.Status = "failed"
		return state, err
	}

	// Phase 2: Multi-Agent Source Discovery
	state.CurrentPhase = "discovery"
	if err := executeSourceDiscovery(ctx, state, request); err != nil {
		logger.Error("Source discovery failed", "error", err)
		state.Status = "failed"
		return state, err
	}

	// Phase 3: Knowledge Graph Construction (if enabled)
	if request.IncludeKnowledgeGraph {
		state.CurrentPhase = "knowledge_graph"
		if err := executeKnowledgeGraphConstruction(ctx, state, request); err != nil {
			logger.Error("Knowledge graph construction failed", "error", err)
			// Continue without knowledge graph
		}
	}

	// Phase 4: Multi-Agent Analysis
	state.CurrentPhase = "analysis"
	if err := executeMultiAgentAnalysis(ctx, state, request); err != nil {
		logger.Error("Multi-agent analysis failed", "error", err)
		state.Status = "failed"
		return state, err
	}

	// Phase 5: Synthesis and Report Generation
	state.CurrentPhase = "synthesis"
	if err := executeSynthesis(ctx, state, request); err != nil {
		logger.Error("Synthesis failed", "error", err)
		state.Status = "failed"
		return state, err
	}

	// Phase 6: Event Streaming (if enabled)
	if request.StreamEvents {
		state.CurrentPhase = "streaming"
		if err := executeEventStreaming(ctx, state, request); err != nil {
			logger.Error("Event streaming failed", "error", err)
			// Continue without streaming
		}
	}

	state.Status = "completed"
	state.EndTime = workflow.Now(ctx)
	
	logger.Info("Deep Research Workflow completed successfully", 
		"sources", len(state.Sources), 
		"findings", len(state.Findings),
		"duration", state.EndTime.Sub(state.StartTime))

	return state, nil
}

// executeResearchPlanning plans the research approach
func executeResearchPlanning(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting research planning phase",
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"query": request.Query,
			"type":  request.ResearchType,
		},
	}
	state.EventStream = append(state.EventStream, event)

	// Generate research plan
	var plan map[string]interface{}
	err := workflow.ExecuteActivity(ctx, activities.GenerateResearchPlanActivity, 
		request.Query, request.ResearchType, request.Context).Get(ctx, &plan)
	if err != nil {
		return fmt.Errorf("failed to generate research plan: %w", err)
	}

	// Store plan in context
	if state.Context == nil {
		state.Context = make(map[string]interface{})
	}
	state.Context["researchPlan"] = plan

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   "Research planning completed",
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"plan": plan,
		},
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Research planning completed", "planKeys", len(plan))
	return nil
}

// executeSourceDiscovery discovers relevant sources
func executeSourceDiscovery(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting source discovery phase",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	// Discover sources using multiple agents
	var sources []types.ResearchSource
	
	// Web search agent
	var webSources []types.ResearchSource
	err := workflow.ExecuteActivity(ctx, activities.DiscoverWebSourcesActivity, 
		request.Query, request.MaxSources/2).Get(ctx, &webSources)
	if err != nil {
		logger.Warn("Web source discovery failed", "error", err)
	} else {
		sources = append(sources, webSources...)
		
		// Record agent contribution
		contribution := types.AgentContribution{
			AgentID:       "web-search-agent",
			AgentType:     "web-search",
			Contribution:  fmt.Sprintf("Discovered %d web sources", len(webSources)),
			Confidence:    0.8,
			Timestamp:     workflow.Now(ctx),
			Sources:       extractSourceIDs(webSources),
		}
		state.AgentCollaboration = append(state.AgentCollaboration, contribution)
	}

	// Database search agent
	var dbSources []types.ResearchSource
	err = workflow.ExecuteActivity(ctx, activities.DiscoverDatabaseSourcesActivity, 
		request.Query, request.MaxSources/2).Get(ctx, &dbSources)
	if err != nil {
		logger.Warn("Database source discovery failed", "error", err)
	} else {
		sources = append(sources, dbSources...)
		
		// Record agent contribution
		contribution := types.AgentContribution{
			AgentID:       "database-search-agent",
			AgentType:     "database-search",
			Contribution:  fmt.Sprintf("Discovered %d database sources", len(dbSources)),
			Confidence:    0.9,
			Timestamp:     workflow.Now(ctx),
			Sources:       extractSourceIDs(dbSources),
		}
		state.AgentCollaboration = append(state.AgentCollaboration, contribution)
	}

	// Deduplicate and rank sources
	sources = deduplicateSources(sources)
	sources = rankSources(sources, request.Query)
	
	// Limit to max sources
	if len(sources) > request.MaxSources {
		sources = sources[:request.MaxSources]
	}

	state.Sources = sources

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   fmt.Sprintf("Source discovery completed with %d sources", len(sources)),
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"sourceCount": len(sources),
		},
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Source discovery completed", "sources", len(sources))
	return nil
}

// executeKnowledgeGraphConstruction builds a knowledge graph
func executeKnowledgeGraphConstruction(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting knowledge graph construction",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	// Build knowledge graph from sources
	var knowledgeGraph []types.KnowledgeNode
	err := workflow.ExecuteActivity(ctx, activities.BuildKnowledgeGraphActivity, 
		state.Sources, request.MaxDepth).Get(ctx, &knowledgeGraph)
	if err != nil {
		return fmt.Errorf("failed to build knowledge graph: %w", err)
	}

	state.KnowledgeGraph = knowledgeGraph

	// Record agent contribution
	contribution := types.AgentContribution{
		AgentID:       "knowledge-graph-agent",
		AgentType:     "knowledge-graph",
		Contribution:  fmt.Sprintf("Built knowledge graph with %d nodes", len(knowledgeGraph)),
		Confidence:    0.85,
		Timestamp:     workflow.Now(ctx),
		Sources:       extractSourceIDs(state.Sources),
	}
	state.AgentCollaboration = append(state.AgentCollaboration, contribution)

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   fmt.Sprintf("Knowledge graph construction completed with %d nodes", len(knowledgeGraph)),
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"nodeCount": len(knowledgeGraph),
		},
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Knowledge graph construction completed", "nodes", len(knowledgeGraph))
	return nil
}

// executeMultiAgentAnalysis performs multi-agent analysis
func executeMultiAgentAnalysis(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting multi-agent analysis",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	// Analyze sources with different agent types
	var findings []types.ResearchFinding

	// Content analysis agent
	var contentFindings []types.ResearchFinding
	err := workflow.ExecuteActivity(ctx, activities.AnalyzeContentActivity, 
		state.Sources, request.Query).Get(ctx, &contentFindings)
	if err != nil {
		logger.Warn("Content analysis failed", "error", err)
	} else {
		findings = append(findings, contentFindings...)
		
		// Record agent contribution
		contribution := types.AgentContribution{
			AgentID:       "content-analysis-agent",
			AgentType:     "content-analysis",
			Contribution:  fmt.Sprintf("Generated %d content findings", len(contentFindings)),
			Confidence:    0.85,
			Timestamp:     workflow.Now(ctx),
			Sources:       extractSourceIDs(state.Sources),
		}
		state.AgentCollaboration = append(state.AgentCollaboration, contribution)
	}

	// Pattern analysis agent
	var patternFindings []types.ResearchFinding
	err = workflow.ExecuteActivity(ctx, activities.AnalyzePatternsActivity, 
		state.Sources, state.KnowledgeGraph).Get(ctx, &patternFindings)
	if err != nil {
		logger.Warn("Pattern analysis failed", "error", err)
	} else {
		findings = append(findings, patternFindings...)
		
		// Record agent contribution
		contribution := types.AgentContribution{
			AgentID:       "pattern-analysis-agent",
			AgentType:     "pattern-analysis",
			Contribution:  fmt.Sprintf("Generated %d pattern findings", len(patternFindings)),
			Confidence:    0.75,
			Timestamp:     workflow.Now(ctx),
			Sources:       extractSourceIDs(state.Sources),
		}
		state.AgentCollaboration = append(state.AgentCollaboration, contribution)
	}

	// Sentiment analysis agent
	var sentimentFindings []types.ResearchFinding
	err = workflow.ExecuteActivity(ctx, activities.AnalyzeSentimentActivity, 
		state.Sources).Get(ctx, &sentimentFindings)
	if err != nil {
		logger.Warn("Sentiment analysis failed", "error", err)
	} else {
		findings = append(findings, sentimentFindings...)
		
		// Record agent contribution
		contribution := types.AgentContribution{
			AgentID:       "sentiment-analysis-agent",
			AgentType:     "sentiment-analysis",
			Contribution:  fmt.Sprintf("Generated %d sentiment findings", len(sentimentFindings)),
			Confidence:    0.7,
			Timestamp:     workflow.Now(ctx),
			Sources:       extractSourceIDs(state.Sources),
		}
		state.AgentCollaboration = append(state.AgentCollaboration, contribution)
	}

	// Deduplicate and rank findings
	findings = deduplicateFindings(findings)
	findings = rankFindings(findings, request.Query)

	state.Findings = findings

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   fmt.Sprintf("Multi-agent analysis completed with %d findings", len(findings)),
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"findingCount": len(findings),
		},
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Multi-agent analysis completed", "findings", len(findings))
	return nil
}

// executeSynthesis generates final synthesis
func executeSynthesis(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting synthesis phase",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	// Generate synthesis
	var synthesis string
	err := workflow.ExecuteActivity(ctx, activities.GenerateSynthesisActivity, 
		request.Query, state.Sources, state.Findings, state.KnowledgeGraph, 
		request.LLMProvider, request.LLMModel).Get(ctx, &synthesis)
	if err != nil {
		return fmt.Errorf("failed to generate synthesis: %w", err)
	}

	state.Synthesis = synthesis

	// Record agent contribution
	contribution := types.AgentContribution{
		AgentID:       "synthesis-agent",
		AgentType:     "synthesis",
		Contribution:  "Generated comprehensive research synthesis",
		Confidence:    0.9,
		Timestamp:     workflow.Now(ctx),
		Sources:       extractSourceIDs(state.Sources),
	}
	state.AgentCollaboration = append(state.AgentCollaboration, contribution)

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   "Synthesis phase completed",
		Timestamp: workflow.Now(ctx),
		Data: map[string]interface{}{
			"synthesisLength": len(synthesis),
		},
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Synthesis completed", "synthesisLength", len(synthesis))
	return nil
}

// executeEventStreaming streams research events
func executeEventStreaming(ctx workflow.Context, state *types.ResearchState, request types.ResearchRequest) error {
	logger := workflow.GetLogger(ctx)

	// Add event
	event := types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_start",
		Message:   "Starting event streaming",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	// Stream events (mock implementation)
	err := workflow.ExecuteActivity(ctx, activities.StreamResearchEventsActivity, 
		state.EventStream, request.Query).Get(ctx, nil)
	if err != nil {
		logger.Warn("Event streaming failed", "error", err)
		// Continue without streaming
	}

	// Add completion event
	event = types.ResearchEvent{
		ID:        generateEventID(),
		Type:      "phase_complete",
		Message:   "Event streaming completed",
		Timestamp: workflow.Now(ctx),
	}
	state.EventStream = append(state.EventStream, event)

	logger.Info("Event streaming completed", "eventCount", len(state.EventStream))
	return nil
}

// Helper functions

func generateEventID() string {
	return fmt.Sprintf("event_%d", time.Now().UnixNano())
}

func extractSourceIDs(sources []types.ResearchSource) []string {
	var ids []string
	for _, source := range sources {
		ids = append(ids, source.ID)
	}
	return ids
}

func deduplicateSources(sources []types.ResearchSource) []types.ResearchSource {
	seen := make(map[string]bool)
	var result []types.ResearchSource
	
	for _, source := range sources {
		if !seen[source.URL] {
			seen[source.URL] = true
			result = append(result, source)
		}
	}
	
	return result
}

func rankSources(sources []types.ResearchSource, query string) []types.ResearchSource {
	// Simple ranking by relevance (in real implementation would use more sophisticated algorithms)
	// For now, just return as-is
	return sources
}

func deduplicateFindings(findings []types.ResearchFinding) []types.ResearchFinding {
	seen := make(map[string]bool)
	var result []types.ResearchFinding
	
	for _, finding := range findings {
		key := fmt.Sprintf("%s-%s", finding.Category, finding.Title)
		if !seen[key] {
			seen[key] = true
			result = append(result, finding)
		}
	}
	
	return result
}

func rankFindings(findings []types.ResearchFinding, query string) []types.ResearchFinding {
	// Simple ranking by confidence (in real implementation would use more sophisticated algorithms)
	// Sort by confidence descending
	for i := 0; i < len(findings)-1; i++ {
		for j := 0; j < len(findings)-i-1; j++ {
			if findings[j].Confidence < findings[j+1].Confidence {
				findings[j], findings[j+1] = findings[j+1], findings[j]
			}
		}
	}
	
	return findings
}

// GetResearchStateQuery returns the current state of the research workflow
func GetResearchStateQuery(ctx workflow.Context, state *types.ResearchState) (*types.ResearchState, error) {
	return state, nil
}
