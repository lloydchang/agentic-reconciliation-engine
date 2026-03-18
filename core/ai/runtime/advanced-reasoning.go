package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"
	"time"

	"github.com/sashabaranov/go-openai"
	"go.temporal.io/sdk/workflow"
)

// Decision represents a reasoning decision with confidence and justification
type Decision struct {
	DecisionID   string                 `json:"decision_id"`
	TaskID       string                 `json:"task_id"`
	Options      []DecisionOption       `json:"options"`
	ChosenOption *DecisionOption        `json:"chosen_option,omitempty"`
	Confidence   float64                `json:"confidence"`
	Justification string                `json:"justification"`
	Timestamp    time.Time              `json:"timestamp"`
	Context      map[string]interface{} `json:"context,omitempty"`
}

// DecisionOption represents an option in a decision
type DecisionOption struct {
	OptionID     string                 `json:"option_id"`
	Description  string                 `json:"description"`
	Pros         []string               `json:"pros"`
	Cons         []string               `json:"cons"`
	RiskLevel    string                 `json:"risk_level"` // low, medium, high
	Impact       string                 `json:"impact"`     // low, medium, high
	Score        float64                `json:"score"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// ReasoningEngine provides advanced reasoning capabilities
type ReasoningEngine struct {
	openaiClient *openai.Client
	maxRetries   int
	timeout      time.Duration
}

// NewReasoningEngine creates a new reasoning engine
func NewReasoningEngine(apiKey string) *ReasoningEngine {
	client := openai.NewClient(apiKey)
	return &ReasoningEngine{
		openaiClient: client,
		maxRetries:   3,
		timeout:      30 * time.Second,
	}
}

// AnalyzeOptions performs advanced reasoning on decision options
func (re *ReasoningEngine) AnalyzeOptions(ctx context.Context, taskDescription string, options []DecisionOption, context map[string]interface{}) (*Decision, error) {
	decisionID := fmt.Sprintf("decision-%d", time.Now().Unix())

	// Create prompt for LLM reasoning
	prompt := re.buildReasoningPrompt(taskDescription, options, context)

	// Get LLM analysis
	llmResponse, err := re.queryLLM(ctx, prompt)
	if err != nil {
		return nil, fmt.Errorf("failed to query LLM: %v", err)
	}

	// Parse LLM response into decision
	decision, err := re.parseLLMDecision(decisionID, taskDescription, options, llmResponse)
	if err != nil {
		return nil, fmt.Errorf("failed to parse LLM decision: %v", err)
	}

	// Apply additional reasoning rules
	decision = re.applyReasoningRules(decision, context)

	// Calculate final confidence
	decision.Confidence = re.calculateConfidence(decision)

	return decision, nil
}

// buildReasoningPrompt creates a structured prompt for LLM reasoning
func (re *ReasoningEngine) buildReasoningPrompt(taskDescription string, options []DecisionOption, context map[string]interface{}) string {
	var prompt strings.Builder

	prompt.WriteString("You are an expert AI decision-making system. Analyze the following task and options, then recommend the best choice with detailed reasoning.\n\n")
	prompt.WriteString(fmt.Sprintf("TASK: %s\n\n", taskDescription))

	if len(context) > 0 {
		prompt.WriteString("CONTEXT:\n")
		for key, value := range context {
			prompt.WriteString(fmt.Sprintf("- %s: %v\n", key, value))
		}
		prompt.WriteString("\n")
	}

	prompt.WriteString("OPTIONS:\n")
	for i, option := range options {
		prompt.WriteString(fmt.Sprintf("%d. %s\n", i+1, option.Description))
		if len(option.Pros) > 0 {
			prompt.WriteString("   Pros: " + strings.Join(option.Pros, ", ") + "\n")
		}
		if len(option.Cons) > 0 {
			prompt.WriteString("   Cons: " + strings.Join(option.Cons, ", ") + "\n")
		}
		prompt.WriteString(fmt.Sprintf("   Risk Level: %s, Impact: %s\n\n", option.RiskLevel, option.Impact))
	}

	prompt.WriteString("INSTRUCTIONS:\n")
	prompt.WriteString("1. Evaluate each option based on pros, cons, risk, and impact\n")
	prompt.WriteString("2. Consider the task requirements and context\n")
	prompt.WriteString("3. Recommend the single best option with justification\n")
	prompt.WriteString("4. Provide a confidence score (0.0-1.0) for your recommendation\n")
	prompt.WriteString("5. Explain your reasoning step by step\n\n")
	prompt.WriteString("RESPONSE FORMAT:\n")
	prompt.WriteString("{\n")
	prompt.WriteString("  \"recommended_option\": <number>,\n")
	prompt.WriteString("  \"confidence\": <float>,\n")
	prompt.WriteString("  \"justification\": \"<detailed explanation>\",\n")
	prompt.WriteString("  \"reasoning_steps\": [\"step1\", \"step2\", ...]\n")
	prompt.WriteString("}")

	return prompt.String()
}

// queryLLM sends prompt to LLM and gets response
func (re *ReasoningEngine) queryLLM(ctx context.Context, prompt string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, re.timeout)
	defer cancel()

	req := openai.ChatCompletionRequest{
		Model: openai.GPT4,
		Messages: []openai.ChatCompletionMessage{
			{
				Role:    openai.ChatMessageRoleSystem,
				Content: "You are an expert decision-making AI. Provide structured, logical analysis.",
			},
			{
				Role:    openai.ChatMessageRoleUser,
				Content: prompt,
			},
		},
		Temperature: 0.3,
		MaxTokens:   1000,
	}

	resp, err := re.openaiClient.CreateChatCompletion(ctx, req)
	if err != nil {
		return "", err
	}

	if len(resp.Choices) == 0 {
		return "", fmt.Errorf("no response from LLM")
	}

	return resp.Choices[0].Message.Content, nil
}

// parseLLMDecision parses LLM response into Decision struct
func (re *ReasoningEngine) parseLLMDecision(decisionID, taskID string, options []DecisionOption, llmResponse string) (*Decision, error) {
	var llmResult struct {
		RecommendedOption int       `json:"recommended_option"`
		Confidence       float64   `json:"confidence"`
		Justification    string    `json:"justification"`
		ReasoningSteps   []string  `json:"reasoning_steps"`
	}

	if err := json.Unmarshal([]byte(llmResponse), &llmResult); err != nil {
		return nil, fmt.Errorf("failed to parse LLM response: %v", err)
	}

	if llmResult.RecommendedOption < 1 || llmResult.RecommendedOption > len(options) {
		return nil, fmt.Errorf("invalid recommended option index: %d", llmResult.RecommendedOption)
	}

	chosenOption := options[llmResult.RecommendedOption-1]

	return &Decision{
		DecisionID:    decisionID,
		TaskID:        taskID,
		Options:       options,
		ChosenOption:  &chosenOption,
		Confidence:    llmResult.Confidence,
		Justification: llmResult.Justification,
		Timestamp:     time.Now(),
		Context: map[string]interface{}{
			"reasoning_steps": llmResult.ReasoningSteps,
		},
	}, nil
}

// applyReasoningRules applies additional deterministic reasoning rules
func (re *ReasoningEngine) applyReasoningRules(decision *Decision, context map[string]interface{}) *Decision {
	// Apply risk-based filtering
	if riskThreshold, exists := context["max_risk_level"].(string); exists {
		if decision.ChosenOption.RiskLevel == "high" && riskThreshold != "high" {
			log.Printf("High-risk option chosen, applying risk mitigation")
			decision.Confidence *= 0.8 // Reduce confidence for high-risk choices
			decision.Justification += " (Note: High-risk option selected - consider additional review)"
		}
	}

	// Apply impact-based weighting
	if impactWeight, exists := context["impact_weight"].(float64); exists {
		if decision.ChosenOption.Impact == "high" {
			decision.Confidence *= impactWeight
		}
	}

	return decision
}

// calculateConfidence calculates final confidence score
func (re *ReasoningEngine) calculateConfidence(decision *Decision) float64 {
	if decision.ChosenOption == nil {
		return 0.0
	}

	// Base confidence from LLM
	baseConfidence := decision.Confidence

	// Adjust based on option scores
	if len(decision.Options) > 0 {
		// Sort options by score
		sortedOptions := make([]DecisionOption, len(decision.Options))
		copy(sortedOptions, decision.Options)
		sort.Slice(sortedOptions, func(i, j int) bool {
			return sortedOptions[i].Score > sortedOptions[j].Score
		})

		// If chosen option is not the highest scored, reduce confidence
		if sortedOptions[0].OptionID != decision.ChosenOption.OptionID {
			baseConfidence *= 0.9
		}
	}

	// Ensure confidence is between 0.0 and 1.0
	if baseConfidence > 1.0 {
		baseConfidence = 1.0
	} else if baseConfidence < 0.0 {
		baseConfidence = 0.0
	}

	return baseConfidence
}

// WorkflowReasoningActivity is a Temporal activity for reasoning
func WorkflowReasoningActivity(ctx context.Context, taskDescription string, options []DecisionOption, context map[string]interface{}) (*Decision, error) {
	// Note: In a real implementation, this would get the API key from secure config
	re := NewReasoningEngine("your-openai-api-key-here")

	return re.AnalyzeOptions(ctx, taskDescription, options, context)
}

// ReasoningWorkflow is a Temporal workflow for complex decision-making
func ReasoningWorkflow(ctx workflow.Context, taskDescription string, options []DecisionOption, context map[string]interface{}) (*Decision, error) {
	// Configure workflow options
	ao := workflow.ActivityOptions{
		StartToCloseTimeout: 60 * time.Second,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    30 * time.Second,
			MaximumAttempts:    3,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result *Decision
	err := workflow.ExecuteActivity(ctx, WorkflowReasoningActivity, taskDescription, options, context).Get(ctx, &result)
	if err != nil {
		return nil, err
	}

	// Log the decision for audit
	workflow.GetLogger(ctx).Info("Reasoning workflow completed",
		"decision_id", result.DecisionID,
		"chosen_option", result.ChosenOption.OptionID,
		"confidence", result.Confidence)

	return result, nil
}

// Global reasoning engine instance
var GlobalReasoningEngine *ReasoningEngine

// InitReasoningEngine initializes the global reasoning engine
func InitReasoningEngine(apiKey string) error {
	GlobalReasoningEngine = NewReasoningEngine(apiKey)
	return nil
}

// AnalyzeDecision provides a simple interface for decision analysis
func AnalyzeDecision(taskDescription string, options []DecisionOption, context map[string]interface{}) (*Decision, error) {
	if GlobalReasoningEngine == nil {
		return nil, fmt.Errorf("reasoning engine not initialized")
	}

	ctx := context.Background()
	return GlobalReasoningEngine.AnalyzeOptions(ctx, taskDescription, options, context)
}
