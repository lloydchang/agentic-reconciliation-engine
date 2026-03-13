package orchestration

import (
	"fmt"
	"strings"
	"time"

	"go.temporal.io/sdk/workflow"
)

// generateSimpleResponse generates a simple response (haiku-like for demo)
func (w *OrchestrationWorkflow) generateSimpleResponse(query string) string {
	// Simulate a simple agent that generates structured responses
	// In production, this would call an LLM with specific formatting instructions
	return fmt.Sprintf(`Here is my response to: "%s"

A simple answer flows
Like water in a gentle stream
Clarity emerges

The query has been processed with care and consideration.`, query)
}

// analyzeQueryForTools analyzes a query to determine which tools are needed
func (w *OrchestrationWorkflow) analyzeQueryForTools(query string) []string {
	query = strings.ToLower(query)
	var tools []string

	// Simple keyword-based tool detection
	if strings.Contains(query, "weather") || strings.Contains(query, "temperature") {
		tools = append(tools, "weather_api")
	}
	if strings.Contains(query, "search") || strings.Contains(query, "find") || strings.Contains(query, "information") {
		tools = append(tools, "web_search")
	}
	if strings.Contains(query, "calculate") || strings.Contains(query, "compute") || strings.Contains(query, "math") {
		tools = append(tools, "calculator")
	}
	if strings.Contains(query, "time") || strings.Contains(query, "date") {
		tools = append(tools, "datetime")
	}

	// Default to web search if no specific tools detected
	if len(tools) == 0 {
		tools = append(tools, "web_search")
	}

	return tools
}

// executeTool executes a tool using the MCP registry
func (w *OrchestrationWorkflow) executeTool(ctx workflow.Context, toolName, query string) (map[string]interface{}, error) {
	// Create tool call parameters based on tool type
	var params map[string]interface{}

	switch toolName {
	case "weather_api":
		params = map[string]interface{}{
			"location": w.extractLocationFromQuery(query),
			"units":    "celsius",
		}
	case "web_search":
		params = map[string]interface{}{
			"query":   query,
			"limit":   5,
			"engine": "duckduckgo",
		}
	case "calculator":
		params = map[string]interface{}{
			"expression": w.extractCalculationFromQuery(query),
		}
	case "datetime":
		params = map[string]interface{}{
			"timezone": "UTC",
			"format":   "RFC3339",
		}
	default:
		params = map[string]interface{}{
			"query": query,
		}
	}

	// Execute tool using MCP registry (this would be done in an activity)
	// For now, simulate tool execution
	start := time.Now()
	result := w.simulateToolExecution(toolName, params)
	duration := time.Since(start)

	return map[string]interface{}{
		"tool_name": toolName,
		"parameters": params,
		"result": result,
		"duration_ms": duration.Milliseconds(),
		"timestamp": time.Now().Format(time.RFC3339),
	}, nil
}

// synthesizeToolBasedResponse creates a response from tool execution results
func (w *OrchestrationWorkflow) synthesizeToolBasedResponse(query string, toolCalls []ToolExecution) string {
	if len(toolCalls) == 0 {
		return fmt.Sprintf("I processed your query: %s", query)
	}

	response := fmt.Sprintf("Based on your query '%s', I executed the following tools:\n\n", query)

	for i, toolCall := range toolCalls {
		response += fmt.Sprintf("%d. **%s**: ", i+1, toolCall.ToolName)
		if toolCall.Error != "" {
			response += fmt.Sprintf("Failed - %s\n", toolCall.Error)
		} else {
			response += fmt.Sprintf("Completed successfully\n")
			// Add some result summary
			if result, ok := toolCall.Result.(map[string]interface{}); ok {
				if summary, exists := result["summary"]; exists {
					response += fmt.Sprintf("   Result: %v\n", summary)
				}
			}
		}
	}

	response += "\nThis demonstrates tool-based agent orchestration where multiple tools can be executed to gather information and provide comprehensive responses."

	return response
}

// createResearchPlan creates a research plan for a query
func (w *OrchestrationWorkflow) createResearchPlan(query, depth string) map[string]interface{} {
	if depth == "" {
		depth = "moderate"
	}

	plan := map[string]interface{}{
		"query": query,
		"depth": depth,
		"searchStrategy": "comprehensive",
		"sources": []string{"web", "academic", "news"},
		"maxSources": 10,
		"focusAreas": w.extractResearchFocusAreas(query),
		"timestamp": time.Now().Format(time.RFC3339),
	}

	// Adjust plan based on depth
	switch depth {
	case "shallow":
		plan["maxSources"] = 3
		plan["sources"] = []string{"web"}
	case "deep":
		plan["maxSources"] = 20
		plan["searchStrategy"] = "exhaustive"
	case "moderate":
		// Default settings
	}

	return plan
}

// executeResearchSearches executes searches based on research plan
func (w *OrchestrationWorkflow) executeResearchSearches(ctx workflow.Context, plan map[string]interface{}, toolCalls *[]ToolExecution) []map[string]interface{} {
	query := plan["query"].(string)
	maxSources := plan["maxSources"].(int)

	results := []map[string]interface{}{}

	// Execute multiple search tools
	searchQueries := w.generateSearchQueries(query, maxSources)

	for _, searchQuery := range searchQueries {
		toolResult, err := w.executeTool(ctx, "web_search", searchQuery)
		if err != nil {
			// Continue with other searches even if one fails
			continue
		}

		results = append(results, toolResult)

		// Add to tool calls list
		*toolCalls = append(*toolCalls, ToolExecution{
			ToolName:   "web_search",
			Parameters: map[string]interface{}{"query": searchQuery},
			Result:     toolResult,
			Duration:   time.Duration(toolResult["duration_ms"].(float64)) * time.Millisecond,
		})
	}

	return results
}

// synthesizeResearchReport creates a comprehensive research report
func (w *OrchestrationWorkflow) synthesizeResearchReport(query string, plan map[string]interface{}, searchResults []map[string]interface{}) string {
	report := fmt.Sprintf("# Research Report: %s\n\n", query)
	report += fmt.Sprintf("**Research Plan:** %s depth analysis\n", plan["depth"])
	report += fmt.Sprintf("**Sources Analyzed:** %d\n", len(searchResults))
	report += fmt.Sprintf("**Generated:** %s\n\n", time.Now().Format(time.RFC3339))

	report += "## Executive Summary\n\n"
	report += fmt.Sprintf("This report provides comprehensive analysis of: %s\n\n", query)

	report += "## Methodology\n\n"
	report += "Research was conducted using multiple sources and analytical tools:\n"
	report += "- Web search across multiple engines\n"
	report += "- Content analysis and summarization\n"
	report += "- Cross-referencing and validation\n\n"

	report += "## Key Findings\n\n"

	// Simulate synthesis of findings
	findings := []string{
		"Primary research areas identified and explored",
		"Multiple perspectives and data points collected",
		"Comprehensive analysis of available information",
		"Future research directions identified",
	}

	for i, finding := range findings {
		report += fmt.Sprintf("%d. %s\n", i+1, finding)
	}

	report += "\n## Detailed Analysis\n\n"
	report += "The research process involved systematic investigation using advanced AI orchestration:\n\n"
	report += "### Agent Coordination\n"
	report += "- **Planning Agent**: Developed research strategy and methodology\n"
	report += "- **Search Agent**: Executed multi-source information gathering\n"
	report += "- **Analysis Agent**: Processed and synthesized findings\n"
	report += "- **Reporting Agent**: Generated comprehensive documentation\n\n"

	report += "### Tool Integration\n"
	report += "- Web search capabilities for information gathering\n"
	report += "- Content analysis tools for insight extraction\n"
	report += "- Validation mechanisms for result quality assurance\n\n"

	report += "## Conclusions\n\n"
	report += "This research demonstrates the power of orchestrated AI agents working together to provide comprehensive, well-structured analysis of complex topics.\n\n"

	report += "## References\n\n"
	for i, result := range searchResults {
		if resultMap, ok := result["result"].(map[string]interface{}); ok {
			report += fmt.Sprintf("%d. %s\n", i+1, resultMap["summary"])
		}
	}

	return report
}

// analyzeQueryForClarification determines if a query needs clarification
func (w *OrchestrationWorkflow) analyzeQueryForClarification(query string) map[string]interface{} {
	result := map[string]interface{}{
		"needsClarification": false,
		"confidence":         0.8,
		"missingInfo":        []string{},
		"reasoning":          "Query appears sufficiently specific",
	}

	query = strings.ToLower(query)

	// Check for ambiguous terms that might need clarification
	if strings.Contains(query, "best") && !strings.Contains(query, "criteria") {
		result["needsClarification"] = true
		result["missingInfo"] = append(result["missingInfo"].([]string), "evaluation criteria")
		result["reasoning"] = "Query uses 'best' but doesn't specify evaluation criteria"
	}

	if strings.Contains(query, "recent") && !strings.Contains(query, "timeframe") {
		result["needsClarification"] = true
		result["missingInfo"] = append(result["missingInfo"].([]string), "timeframe specification")
		result["reasoning"] = "Query mentions 'recent' but doesn't specify timeframe"
	}

	if strings.Contains(query, "around") || strings.Contains(query, "near") {
		if !strings.Contains(query, "location") && !strings.Contains(query, "area") {
			result["needsClarification"] = true
			result["missingInfo"] = append(result["missingInfo"].([]string), "specific location")
			result["reasoning"] = "Query mentions location-relative terms but lacks specific location"
		}
	}

	return result
}

// generateClarificationQuestions creates questions for clarification
func (w *OrchestrationWorkflow) generateClarificationQuestions(analysis map[string]interface{}) []string {
	missingInfo := analysis["missingInfo"].([]string)
	questions := make([]string, len(missingInfo))

	for i, info := range missingInfo {
		switch info {
		case "evaluation criteria":
			questions[i] = "What criteria should I use to determine the 'best' option?"
		case "timeframe specification":
			questions[i] = "What timeframe are you considering for 'recent' information?"
		case "specific location":
			questions[i] = "Could you provide a more specific location or area?"
		default:
			questions[i] = fmt.Sprintf("Could you clarify what you mean by '%s'?", info)
		}
	}

	return questions
}

// refineQueryWithClarification refines the query using clarification responses
func (w *OrchestrationWorkflow) refineQueryWithClarification(originalQuery, clarification string, analysis map[string]interface{}) string {
	// Simple refinement logic - in production, this would use an LLM
	refinedQuery := originalQuery

	if strings.Contains(clarification, "criteria") || strings.Contains(clarification, "factors") {
		refinedQuery += fmt.Sprintf(" (evaluation criteria: %s)", clarification)
	}

	if strings.Contains(clarification, "timeframe") || strings.Contains(clarification, "period") {
		refinedQuery += fmt.Sprintf(" (timeframe: %s)", clarification)
	}

	if strings.Contains(clarification, "location") || strings.Contains(clarification, "area") {
		refinedQuery += fmt.Sprintf(" (location: %s)", clarification)
	}

	return refinedQuery
}
