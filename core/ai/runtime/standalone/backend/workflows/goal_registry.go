package workflows

import (
	"fmt"
	"strings"
	"time"
)

// AgentGoal represents a goal that the agent can accomplish
type AgentGoal struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Category    string                 `json:"category"`
	Priority    int                    `json:"priority"` // 1-10, higher = more important
	Tools       []string               `json:"tools"`    // Required tools for this goal
	Inputs      []GoalInput            `json:"inputs"`   // Required inputs
	Outputs     []string               `json:"outputs"`  // Expected outputs
	MaxTurns    int                    `json:"maxTurns"` // Maximum conversation turns
	Timeout     time.Duration          `json:"timeout"`  // Goal timeout
	Enabled     bool                   `json:"enabled"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// GoalInput represents an input required for a goal
type GoalInput struct {
	Name        string      `json:"name"`
	Type        string      `json:"type"`        // string, number, boolean, object
	Required    bool        `json:"required"`
	Description string      `json:"description"`
	Validation  string      `json:"validation"`  // Regex or validation rule
	Default     interface{} `json:"default,omitempty"`
}

// GoalRegistry manages available agent goals
type GoalRegistry struct {
	goals map[string]*AgentGoal
}

// NewGoalRegistry creates a new goal registry
func NewGoalRegistry() *GoalRegistry {
	registry := &GoalRegistry{
		goals: make(map[string]*AgentGoal),
	}
	registry.registerDefaultGoals()
	return registry
}

// RegisterGoal registers a new goal
func (gr *GoalRegistry) RegisterGoal(goal *AgentGoal) error {
	if goal.Name == "" {
		return fmt.Errorf("goal name cannot be empty")
	}
	if _, exists := gr.goals[goal.Name]; exists {
		return fmt.Errorf("goal %s already registered", goal.Name)
	}
	gr.goals[goal.Name] = goal
	return nil
}

// GetGoal retrieves a goal by name
func (gr *GoalRegistry) GetGoal(name string) (*AgentGoal, error) {
	goal, exists := gr.goals[name]
	if !exists {
		return nil, fmt.Errorf("goal %s not found", name)
	}
	return goal, nil
}

// ListGoals returns all registered goals
func (gr *GoalRegistry) ListGoals() []*AgentGoal {
	goals := make([]*AgentGoal, 0, len(gr.goals))
	for _, goal := range gr.goals {
		goals = append(goals, goal)
	}
	return goals
}

// ListGoalsByCategory returns goals filtered by category
func (gr *GoalRegistry) ListGoalsByCategory(category string) []*AgentGoal {
	var goals []*AgentGoal
	for _, goal := range gr.goals {
		if strings.EqualFold(goal.Category, category) {
			goals = append(goals, goal)
		}
	}
	return goals
}

// ValidateGoalInputs validates inputs against goal requirements
func (gr *GoalRegistry) ValidateGoalInputs(goalName string, inputs map[string]interface{}) error {
	goal, err := gr.GetGoal(goalName)
	if err != nil {
		return err
	}

	for _, input := range goal.Inputs {
		if input.Required {
			if value, exists := inputs[input.Name]; !exists || value == nil {
				return fmt.Errorf("required input %s missing", input.Name)
			}
		}
		// Additional validation can be added here
	}

	return nil
}

// registerDefaultGoals registers the default set of agent goals
func (gr *GoalRegistry) registerDefaultGoals() {
	// Infrastructure analysis goal
	gr.RegisterGoal(&AgentGoal{
		Name:        "infrastructure_analysis",
		Description: "Analyze infrastructure components and provide insights",
		Category:    "infrastructure",
		Priority:    8,
		Tools:       []string{"infrastructure_discovery", "security_scan", "cost_analysis"},
		Inputs: []GoalInput{
			{
				Name:        "target_resource",
				Type:        "string",
				Required:    true,
				Description: "The infrastructure resource to analyze",
			},
			{
				Name:        "analysis_type",
				Type:        "string",
				Required:    false,
				Description: "Type of analysis (full, security, cost, performance)",
				Default:     "full",
			},
		},
		Outputs:  []string{"analysis_report", "recommendations", "risk_assessment"},
		MaxTurns: 15,
		Timeout:  time.Minute * 30,
		Enabled:  true,
	})

	// Compliance check goal
	gr.RegisterGoal(&AgentGoal{
		Name:        "compliance_check",
		Description: "Perform compliance checks on systems and data",
		Category:    "compliance",
		Priority:    9,
		Tools:       []string{"compliance_agent", "audit_log_analyzer", "policy_validator"},
		Inputs: []GoalInput{
			{
				Name:        "target_system",
				Type:        "string",
				Required:    true,
				Description: "The system or data to check for compliance",
			},
			{
				Name:        "compliance_standard",
				Type:        "string",
				Required:    false,
				Description: "Compliance standard (GDPR, HIPAA, SOC2, etc.)",
				Default:     "general",
			},
		},
		Outputs:  []string{"compliance_report", "violations", "remediation_steps"},
		MaxTurns: 12,
		Timeout:  time.Minute * 20,
		Enabled:  true,
	})

	// Cost optimization goal
	gr.RegisterGoal(&AgentGoal{
		Name:        "cost_optimization",
		Description: "Analyze and optimize cloud resource costs",
		Category:    "cost",
		Priority:    7,
		Tools:       []string{"cost_analyzer", "resource_optimizer", "budget_tracker"},
		Inputs: []GoalInput{
			{
				Name:        "target_account",
				Type:        "string",
				Required:    true,
				Description: "Cloud account or project to analyze",
			},
			{
				Name:        "time_period",
				Type:        "string",
				Required:    false,
				Description: "Analysis time period (30d, 90d, 1y)",
				Default:     "30d",
			},
		},
		Outputs:  []string{"cost_analysis", "optimization_recommendations", "savings_estimate"},
		MaxTurns: 10,
		Timeout:  time.Minute * 15,
		Enabled:  true,
	})

	// Research and analysis goal
	gr.RegisterGoal(&AgentGoal{
		Name:        "research_analysis",
		Description: "Perform research and provide detailed analysis",
		Category:    "research",
		Priority:    6,
		Tools:       []string{"web_search", "data_analyzer", "report_generator"},
		Inputs: []GoalInput{
			{
				Name:        "research_topic",
				Type:        "string",
				Required:    true,
				Description: "The topic or question to research",
			},
			{
				Name:        "depth",
				Type:        "string",
				Required:    false,
				Description: "Research depth (basic, detailed, comprehensive)",
				Default:     "detailed",
			},
		},
		Outputs:  []string{"research_report", "findings", "conclusions"},
		MaxTurns: 20,
		Timeout:  time.Minute * 45,
		Enabled:  true,
	})
}
