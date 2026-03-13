package orchestration

import (
	"time"

	"go.temporal.io/sdk/workflow"
)

// executeSimpleAgent implements a simple agent (like the Hello World haiku demo)
func (w *OrchestrationWorkflow) executeSimpleAgent(ctx workflow.Context, req OrchestrationWorkflowRequest, steps *[]OrchestrationStep, toolCalls *[]ToolExecution) (string, error) {
	logger := workflow.GetLogger(ctx)

	step := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "SimpleAgent",
		Action:     "GenerateResponse",
		Input:      req.Query,
		Timestamp:  workflow.Now(ctx),
	}
	stepStart := workflow.Now(ctx)

	// Simulate a simple agent that generates a haiku-like response
	// In a real implementation, this would call an LLM with specific instructions
	response := w.generateSimpleResponse(req.Query)

	step.Duration = workflow.Now(ctx).Sub(stepStart)
	step.Output = response
	*steps = append(*steps, step)

	logger.Info("Simple agent completed",
		"query", req.Query,
		"response", response)

	return response, nil
}

// executeToolBasedAgent implements a tool-based agent (like the weather tool demo)
func (w *OrchestrationWorkflow) executeToolBasedAgent(ctx workflow.Context, req OrchestrationWorkflowRequest, steps *[]OrchestrationStep, toolCalls *[]ToolExecution) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Step 1: Analyze query and determine needed tools
	analysisStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "ToolAnalyzer",
		Action:     "AnalyzeQuery",
		Input:      req.Query,
		Timestamp:  workflow.Now(ctx),
	}
	analysisStart := workflow.Now(ctx)

	neededTools := w.analyzeQueryForTools(req.Query)

	analysisStep.Duration = workflow.Now(ctx).Sub(analysisStart)
	analysisStep.Output = map[string]interface{}{
		"neededTools": neededTools,
		"reasoning":   "Analyzed query to determine required tools",
	}
	*steps = append(*steps, analysisStep)

	// Step 2: Execute tools
	for _, toolName := range neededTools {
		toolStep := OrchestrationStep{
			StepNumber: len(*steps) + 1,
			AgentName:  "ToolExecutor",
			Action:     "ExecuteTool",
			Input:      map[string]string{"tool": toolName},
			Timestamp:  workflow.Now(ctx),
		}
		toolStart := workflow.Now(ctx)

		// Execute the tool using MCP registry
		toolResult, err := w.executeTool(ctx, toolName, req.Query)
		if err != nil {
			logger.Warn("Tool execution failed", "tool", toolName, "error", err)
			toolResult = map[string]interface{}{
				"error": err.Error(),
				"tool":  toolName,
			}
		}

		toolStep.Duration = workflow.Now(ctx).Sub(toolStart)
		toolStep.Output = toolResult
		toolStep.ToolCalls = []ToolExecution{{
			ToolName:   toolName,
			Parameters: map[string]interface{}{"query": req.Query},
			Result:     toolResult,
			Duration:   toolStep.Duration,
		}}
		*steps = append(*steps, toolStep)
		*toolCalls = append(*toolCalls, toolStep.ToolCalls[0])
	}

	// Step 3: Synthesize response from tool results
	synthesisStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "ResponseSynthesizer",
		Action:     "SynthesizeResponse",
		Input:      map[string]interface{}{
			"query":     req.Query,
			"toolCalls": *toolCalls,
		},
		Timestamp: workflow.Now(ctx),
	}
	synthesisStart := workflow.Now(ctx)

	response := w.synthesizeToolBasedResponse(req.Query, *toolCalls)

	synthesisStep.Duration = workflow.Now(ctx).Sub(synthesisStart)
	synthesisStep.Output = response
	*steps = append(*steps, synthesisStep)

	logger.Info("Tool-based agent completed",
		"query", req.Query,
		"toolsExecuted", len(*toolCalls),
		"responseLength", len(response))

	return response, nil
}

// executeResearchAgent implements a research agent (like the research workflow demo)
func (w *OrchestrationWorkflow) executeResearchAgent(ctx workflow.Context, req OrchestrationWorkflowRequest, steps *[]OrchestrationStep, toolCalls *[]ToolExecution) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Step 1: Planning phase
	planningStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "ResearchPlanner",
		Action:     "CreateResearchPlan",
		Input:      req.Query,
		Timestamp:  workflow.Now(ctx),
	}
	planningStart := workflow.Now(ctx)

	researchPlan := w.createResearchPlan(req.Query, req.ResearchDepth)

	planningStep.Duration = workflow.Now(ctx).Sub(planningStart)
	planningStep.Output = researchPlan
	*steps = append(*steps, planningStep)

	// Step 2: Search execution phase
	searchStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "ResearchSearcher",
		Action:     "ExecuteSearches",
		Input:      researchPlan,
		Timestamp:  workflow.Now(ctx),
	}
	searchStart := workflow.Now(ctx)

	searchResults := w.executeResearchSearches(ctx, researchPlan, toolCalls)

	searchStep.Duration = workflow.Now(ctx).Sub(searchStart)
	searchStep.Output = searchResults
	searchStep.ToolCalls = *toolCalls
	*steps = append(*steps, searchStep)

	// Step 3: Synthesis phase
	synthesisStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "ResearchSynthesizer",
		Action:     "SynthesizeReport",
		Input:      map[string]interface{}{
			"query":         req.Query,
			"researchPlan":  researchPlan,
			"searchResults": searchResults,
		},
		Timestamp: workflow.Now(ctx),
	}
	synthesisStart := workflow.Now(ctx)

	report := w.synthesizeResearchReport(req.Query, researchPlan, searchResults)

	synthesisStep.Duration = workflow.Now(ctx).Sub(synthesisStart)
	synthesisStep.Output = report
	*steps = append(*steps, synthesisStep)

	logger.Info("Research agent completed",
		"query", req.Query,
		"searchesExecuted", len(*toolCalls),
		"reportLength", len(report))

	return report, nil
}

// executeMultiAgent implements a multi-agent system (like the interactive research demo)
func (w *OrchestrationWorkflow) executeMultiAgent(ctx workflow.Context, req OrchestrationWorkflowRequest, steps *[]OrchestrationStep, toolCalls *[]ToolExecution) (string, error) {
	logger := workflow.GetLogger(ctx)

	// Step 1: Triage agent - analyze query and determine if clarification needed
	triageStep := OrchestrationStep{
		StepNumber: len(*steps) + 1,
		AgentName:  "TriageAgent",
		Action:     "AnalyzeQuery",
		Input:      req.Query,
		Timestamp:  workflow.Now(ctx),
	}
	triageStart := workflow.Now(ctx)

	triageResult := w.analyzeQueryForClarification(req.Query)

	triageStep.Duration = workflow.Now(ctx).Sub(triageStart)
	triageStep.Output = triageResult
	*steps = append(*steps, triageStep)

	// If clarification needed and interactive mode enabled, wait for human input
	if triageResult["needsClarification"].(bool) && req.InteractiveMode {
		logger.Info("Waiting for clarification", "query", req.Query)

		// Add clarification request to steps
		clarifyStep := OrchestrationStep{
			StepNumber: len(*steps) + 1,
			AgentName:  "ClarifyingAgent",
			Action:     "GenerateQuestions",
			Input:      triageResult,
			Timestamp:  workflow.Now(ctx),
		}
		clarifyStart := workflow.Now(ctx)

		questions := w.generateClarificationQuestions(triageResult)

		clarifyStep.Duration = workflow.Now(ctx).Sub(clarifyStart)
		clarifyStep.Output = questions
		*steps = append(*steps, clarifyStep)

		// Wait for human signal with clarification
		signalChan := workflow.GetSignalChannel(ctx, "clarification-response")
		var clarification string
		signalChan.ReceiveAsync(&clarification)

		// Timeout after 10 minutes for clarification
		selector := workflow.NewSelector(ctx)
		selector.AddReceive(signalChan, func(c workflow.ReceiveChannel, more bool) {
			if clarification != "" {
				logger.Info("Received clarification", "clarification", clarification)
			}
		})
		selector.AddFuture(workflow.NewTimer(ctx, 10*time.Minute), func(f workflow.Future) {
			logger.Info("Clarification timeout, proceeding without additional input")
		})
		selector.Select(ctx)

		// Refine query with clarification
		if clarification != "" {
			refineStep := OrchestrationStep{
				StepNumber: len(*steps) + 1,
				AgentName:  "InstructionAgent",
				Action:     "RefineQuery",
				Input:      map[string]interface{}{
					"originalQuery":  req.Query,
					"clarification":  clarification,
					"triageResult":   triageResult,
				},
				Timestamp: workflow.Now(ctx),
			}
			refineStart := workflow.Now(ctx)

			req.Query = w.refineQueryWithClarification(req.Query, clarification, triageResult)

			refineStep.Duration = workflow.Now(ctx).Sub(refineStart)
			refineStep.Output = req.Query
			*steps = append(*steps, refineStep)
		}
	}

	// Execute research with refined query
	return w.executeResearchAgent(ctx, req, steps, toolCalls)
}
