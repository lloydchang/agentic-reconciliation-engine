package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"regexp"
	"strings"
	"time"

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/sandbox"
)

// TemplateSelector selects appropriate sandbox templates based on various criteria
type TemplateSelector struct {
	config          *config.AgentSandboxConfig
	templates       map[string]*config.TemplateSpec
	selectionRules  []*SelectionRule
	performanceData map[string]*TemplatePerformance
}

// SelectionRule defines a rule for template selection
type SelectionRule struct {
	Name        string              `yaml:"name" json:"name"`
	Priority    int                 `yaml:"priority" json:"priority"`
	Conditions  []SelectionCondition `yaml:"conditions" json:"conditions"`
	Action      SelectionAction      `yaml:"action" json:"action"`
	Enabled     bool                `yaml:"enabled" json:"enabled"`
}

// SelectionCondition defines a condition for template selection
type SelectionCondition struct {
	Field    string      `yaml:"field" json:"field"`      // skill_type, language, agent_type, etc.
	Operator string      `yaml:"operator" json:"operator"` // equals, contains, regex, in
	Value    interface{} `yaml:"value" json:"value"`
}

// SelectionAction defines the action to take when conditions are met
type SelectionAction struct {
	Type       string                 `yaml:"type" json:"type"` // set_template, set_resources, add_env
	Parameters map[string]interface{} `yaml:"parameters" json:"parameters"`
}

// TemplatePerformance tracks performance metrics for templates
type TemplatePerformance struct {
	TemplateName    string        `json:"template_name"`
	Executions      int64         `json:"executions"`
	SuccessRate     float64       `json:"success_rate"`
	AverageDuration time.Duration `json:"average_duration"`
	ResourceUsage   ResourceUsage `json:"resource_usage"`
	LastUpdated     time.Time     `json:"last_updated"`
}

// ResourceUsage tracks average resource usage
type ResourceUsage struct {
	AverageCPU    float64 `json:"average_cpu"`
	AverageMemory  int64   `json:"average_memory"`
	PeakCPU        float64 `json:"peak_cpu"`
	PeakMemory     int64   `json:"peak_memory"`
}

// SelectionContext provides context for template selection
type SelectionContext struct {
	SkillName      string
	SkillType      string
	AgentType      string
	Language       string
	CodeComplexity string
	IsolationLevel string
	NetworkAccess  bool
	UserID         string
	TenantID       string
	RequestID      string
}

// SelectionResult contains the result of template selection
type SelectionResult struct {
	Template      *config.TemplateSpec
	Resources     sandbox.ResourceSpec
	Environment   map[string]string
	Reason        string
	Confidence    float64
	Alternatives  []*config.TemplateSpec
}

// NewTemplateSelector creates a new template selector
func NewTemplateSelector(config *config.AgentSandboxConfig) *TemplateSelector {
	ts := &TemplateSelector{
		config:          config,
		templates:       make(map[string]*config.TemplateSpec),
		selectionRules:  make([]*SelectionRule, 0),
		performanceData: make(map[string]*TemplatePerformance),
	}

	// Load templates from config
	for _, template := range config.Templates {
		ts.templates[template.Name] = &template
	}

	// Initialize default selection rules
	ts.initializeDefaultRules()

	return ts
}

// initializeDefaultRules sets up default template selection rules
func (ts *TemplateSelector) initializeDefaultRules() {
	defaultRules := []*SelectionRule{
		{
			Name:     "Python Skills",
			Priority: 100,
			Conditions: []SelectionCondition{
				{Field: "language", Operator: "equals", Value: "python"},
				{Field: "skill_type", Operator: "contains", Value: "python"},
			},
			Action: SelectionAction{
				Type: "set_template",
				Parameters: map[string]interface{}{
					"template": "python-runtime-template",
				},
			},
			Enabled: true,
		},
		{
			Name:     "Bash/Shell Skills",
			Priority: 100,
			Conditions: []SelectionCondition{
				{Field: "language", Operator: "in", Value: []string{"bash", "shell"}},
				{Field: "skill_type", Operator: "contains", Value: "bash"},
			},
			Action: SelectionAction{
				Type: "set_template",
				Parameters: map[string]interface{}{
					"template": "bash-runtime-template",
				},
			},
			Enabled: true,
		},
		{
			Name:     "High Isolation",
			Priority: 200,
			Conditions: []SelectionCondition{
				{Field: "isolation_level", Operator: "equals", Value: "high"},
			},
			Action: SelectionAction{
				Type: "set_resources",
				Parameters: map[string]interface{}{
					"cpu":    "1000m",
					"memory": "2Gi",
				},
			},
			Enabled: true,
		},
		{
			Name:     "Infrastructure Skills",
			Priority: 150,
			Conditions: []SelectionCondition{
				{Field: "skill_type", Operator: "contains", Value: "infrastructure"},
				{Field: "skill_name", Operator: "regex", Value: ".*infra.*"},
			},
			Action: SelectionAction{
				Type: "set_template",
				Parameters: map[string]interface{}{
					"template": "bash-runtime-template",
				},
			},
			Enabled: true,
		},
		{
			Name:     "Security Skills",
			Priority: 150,
			Conditions: []SelectionCondition{
				{Field: "skill_type", Operator: "contains", Value: "security"},
				{Field: "skill_name", Operator: "contains", Value: "security"},
			},
			Action: SelectionAction{
				Type: "set_template",
				Parameters: map[string]interface{}{
					"template": "python-runtime-template",
				},
			},
			Enabled: true,
		},
	}

	ts.selectionRules = defaultRules
}

// SelectTemplate selects the best template based on context and rules
func (ts *TemplateSelector) SelectTemplate(ctx context.Context, context *SelectionContext) (*SelectionResult, error) {
	log.Printf("Selecting template for skill %s (type: %s, agent: %s)", 
		context.SkillName, context.SkillType, context.AgentType)

	result := &SelectionResult{
		Environment: make(map[string]string),
		Alternatives: make([]*config.TemplateSpec, 0),
	}

	// Start with default template
	defaultTemplate, exists := ts.templates[ts.config.DefaultTemplate]
	if !exists {
		return nil, fmt.Errorf("default template %s not found", ts.config.DefaultTemplate)
	}
	result.Template = defaultTemplate
	result.Reason = "Default template selected"

	// Apply selection rules in priority order
	sortedRules := ts.getSortedRules()
	for _, rule := range sortedRules {
		if !rule.Enabled {
			continue
		}

		if ts.evaluateConditions(rule.Conditions, context) {
			if err := ts.applyAction(rule.Action, result, context); err != nil {
				log.Printf("Failed to apply action for rule %s: %v", rule.Name, err)
				continue
			}
			result.Reason = fmt.Sprintf("Rule matched: %s", rule.Name)
			log.Printf("Applied selection rule: %s", rule.Name)
			break // Apply first matching rule by priority
		}
	}

	// Set default resources if not specified
	if result.Resources.CPU == "" {
		result.Resources = ts.config.ResourceDefaults
	}

	// Calculate confidence based on rule matching and performance
	result.Confidence = ts.calculateConfidence(result.Template.Name, context)

	// Find alternative templates
	ts.findAlternatives(result, context)

	log.Printf("Template selection completed: %s (confidence: %.2f, reason: %s)", 
		result.Template.Name, result.Confidence, result.Reason)

	return result, nil
}

// evaluateConditions evaluates if all conditions are met
func (ts *TemplateSelector) evaluateConditions(conditions []SelectionCondition, context *SelectionContext) bool {
	for _, condition := range conditions {
		if !ts.evaluateCondition(condition, context) {
			return false
		}
	}
	return true
}

// evaluateCondition evaluates a single condition
func (ts *TemplateSelector) evaluateCondition(condition SelectionCondition, context *SelectionContext) bool {
	fieldValue := ts.getFieldValue(condition.Field, context)

	switch condition.Operator {
	case "equals":
		return fmt.Sprintf("%v", fieldValue) == fmt.Sprintf("%v", condition.Value)
	case "contains":
		return strings.Contains(strings.ToLower(fmt.Sprintf("%v", fieldValue)), 
			strings.ToLower(fmt.Sprintf("%v", condition.Value)))
	case "regex":
		pattern, err := regexp.Compile(fmt.Sprintf("%v", condition.Value))
		if err != nil {
			log.Printf("Invalid regex pattern: %v", err)
			return false
		}
		return pattern.MatchString(fmt.Sprintf("%v", fieldValue))
	case "in":
		values, ok := condition.Value.([]interface{})
		if !ok {
			return false
		}
		for _, v := range values {
			if fmt.Sprintf("%v", fieldValue) == fmt.Sprintf("%v", v) {
				return true
			}
		}
		return false
	default:
		log.Printf("Unknown operator: %s", condition.Operator)
		return false
	}
}

// getFieldValue gets the value of a field from context
func (ts *TemplateSelector) getFieldValue(field string, context *SelectionContext) interface{} {
	switch field {
	case "skill_name":
		return context.SkillName
	case "skill_type":
		return context.SkillType
	case "agent_type":
		return context.AgentType
	case "language":
		return context.Language
	case "isolation_level":
		return context.IsolationLevel
	case "network_access":
		return context.NetworkAccess
	case "user_id":
		return context.UserID
	case "tenant_id":
		return context.TenantID
	case "request_id":
		return context.RequestID
	default:
		return ""
	}
}

// applyAction applies a selection action
func (ts *TemplateSelector) applyAction(action SelectionAction, result *SelectionResult, context *SelectionContext) error {
	switch action.Type {
	case "set_template":
		templateName, ok := action.Parameters["template"].(string)
		if !ok {
			return fmt.Errorf("template parameter not found or not a string")
		}
		template, exists := ts.templates[templateName]
		if !exists {
			return fmt.Errorf("template %s not found", templateName)
		}
		result.Template = template

	case "set_resources":
		resources := sandbox.ResourceSpec{}
		if cpu, ok := action.Parameters["cpu"].(string); ok {
			resources.CPU = cpu
		}
		if memory, ok := action.Parameters["memory"].(string); ok {
			resources.Memory = memory
		}
		if gpu, ok := action.Parameters["gpu"].(string); ok {
			resources.GPU = gpu
		}
		if disk, ok := action.Parameters["disk"].(string); ok {
			resources.Disk = disk
		}
		result.Resources = resources

	case "add_env":
		if result.Environment == nil {
			result.Environment = make(map[string]string)
		}
		for key, value := range action.Parameters {
			if strValue, ok := value.(string); ok {
				result.Environment[key] = strValue
			}
		}

	default:
		return fmt.Errorf("unknown action type: %s", action.Type)
	}

	return nil
}

// getSortedRules returns rules sorted by priority (highest first)
func (ts *TemplateSelector) getSortedRules() []*SelectionRule {
	rules := make([]*SelectionRule, len(ts.selectionRules))
	copy(rules, ts.selectionRules)

	// Simple bubble sort by priority (descending)
	for i := 0; i < len(rules); i++ {
		for j := i + 1; j < len(rules); j++ {
			if rules[j].Priority > rules[i].Priority {
				rules[i], rules[j] = rules[j], rules[i]
			}
		}
	}

	return rules
}

// calculateConfidence calculates confidence score for template selection
func (ts *TemplateSelector) calculateConfidence(templateName string, context *SelectionContext) float64 {
	confidence := 0.5 // Base confidence

	// Boost confidence based on performance data
	if perf, exists := ts.performanceData[templateName]; exists {
		confidence += perf.SuccessRate * 0.3
		if perf.AverageDuration < 30*time.Second {
			confidence += 0.1 // Fast execution bonus
		}
	}

	// Boost confidence based on exact matches
	if strings.Contains(strings.ToLower(context.SkillName), strings.ToLower(templateName)) {
		confidence += 0.2
	}

	// Ensure confidence is within [0, 1]
	if confidence > 1.0 {
		confidence = 1.0
	}
	if confidence < 0.0 {
		confidence = 0.0
	}

	return confidence
}

// findAlternatives finds alternative templates
func (ts *TemplateSelector) findAlternatives(result *SelectionResult, context *SelectionContext) {
	for _, template := range ts.templates {
		if template.Name != result.Template.Name {
			// Simple heuristic: add templates with similar resource requirements
			if ts.areResourcesCompatible(result.Resources, template.Resources) {
				result.Alternatives = append(result.Alternatives, template)
				if len(result.Alternatives) >= 3 { // Limit to 3 alternatives
					break
				}
			}
		}
	}
}

// areResourcesCompatible checks if resource requirements are compatible
func (ts *TemplateSelector) areResourcesCompatible(req1, req2 sandbox.ResourceSpec) bool {
	// Simple compatibility check
	return req1.CPU == req2.CPU && req1.Memory == req2.Memory
}

// UpdatePerformanceData updates performance data for a template
func (ts *TemplateSelector) UpdatePerformanceData(templateName string, duration time.Duration, success bool, resourceUsage ResourceUsage) {
	perf, exists := ts.performanceData[templateName]
	if !exists {
		perf = &TemplatePerformance{
			TemplateName: templateName,
		}
		ts.performanceData[templateName] = perf
	}

	// Update metrics (simplified rolling average)
	perf.Executions++
	if success {
		perf.SuccessRate = (perf.SuccessRate*float64(perf.Executions-1) + 1.0) / float64(perf.Executions)
	} else {
		perf.SuccessRate = (perf.SuccessRate * float64(perf.Executions-1)) / float64(perf.Executions)
	}

	perf.AverageDuration = (perf.AverageDuration*time.Duration(perf.Executions-1) + duration) / time.Duration(perf.Executions)
	perf.ResourceUsage = resourceUsage
	perf.LastUpdated = time.Now()
}

// GetPerformanceData returns performance data for all templates
func (ts *TemplateSelector) GetPerformanceData() map[string]*TemplatePerformance {
	return ts.performanceData
}

// AddRule adds a new selection rule
func (ts *TemplateSelector) AddRule(rule *SelectionRule) {
	ts.selectionRules = append(ts.selectionRules, rule)
	log.Printf("Added selection rule: %s", rule.Name)
}

// RemoveRule removes a selection rule by name
func (ts *TemplateSelector) RemoveRule(name string) {
	for i, rule := range ts.selectionRules {
		if rule.Name == name {
			ts.selectionRules = append(ts.selectionRules[:i], ts.selectionRules[i+1:]...)
			log.Printf("Removed selection rule: %s", name)
			break
		}
	}
}

// GetRules returns all selection rules
func (ts *TemplateSelector) GetRules() []*SelectionRule {
	return ts.selectionRules
}
