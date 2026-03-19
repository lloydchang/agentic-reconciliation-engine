package cost

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"
)

// CostTracker tracks token usage and costs for AI agent executions
type CostTracker struct {
	mu               sync.RWMutex
	modelPricing     map[string]ModelPricing
	usage            map[string]*UsageRecord
	dailyLimits      map[string]float64
	monthlyLimits    map[string]float64
	notificationHook string
}

// ModelPricing defines pricing for different AI models
type ModelPricing struct {
	InputTokenPrice  float64 `json:"input_token_price"`  // Price per 1K input tokens
	OutputTokenPrice float64 `json:"output_token_price"` // Price per 1K output tokens
	ModelProvider    string  `json:"model_provider"`
	ModelName        string  `json:"model_name"`
}

// UsageRecord tracks usage for a skill execution
type UsageRecord struct {
	SkillName        string    `json:"skill_name"`
	ModelUsed        string    `json:"model_used"`
	InputTokens      int       `json:"input_tokens"`
	OutputTokens     int       `json:"output_tokens"`
	ExecutionTime    time.Time `json:"execution_time"`
	Cost             float64   `json:"cost"`
	UserID           string    `json:"user_id"`
	SessionID        string    `json:"session_id"`
	Success          bool      `json:"success"`
	ErrorMessage     string    `json:"error_message,omitempty"`
}

// CostSummary provides cost analysis
type CostSummary struct {
	TotalCost         float64            `json:"total_cost"`
	TotalTokens       int                `json:"total_tokens"`
	SkillCosts        map[string]float64 `json:"skill_costs"`
	ModelCosts        map[string]float64 `json:"model_costs"`
	DailyCost         float64            `json:"daily_cost"`
	MonthlyCost       float64            `json:"monthly_cost"`
	CostSavings       float64            `json:"cost_savings"`
	ExecutionCount    int                `json:"execution_count"`
	SuccessRate       float64            `json:"success_rate"`
}

// NewCostTracker creates a new cost tracker instance
func NewCostTracker() *CostTracker {
	return &CostTracker{
		modelPricing: make(map[string]ModelPricing),
		usage:        make(map[string]*UsageRecord),
		dailyLimits:  make(map[string]float64),
		monthlyLimits: make(map[string]float64),
	}
}

// LoadModelPricing loads model pricing configuration
func (ct *CostTracker) LoadModelPricing(pricingConfig map[string]ModelPricing) {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	
	ct.modelPricing = pricingConfig
	
	// Set default pricing for common models if not provided
	defaults := map[string]ModelPricing{
		"local:llama.cpp": {
			InputTokenPrice:  0.0001, // $0.0001 per 1K tokens (essentially free)
			OutputTokenPrice: 0.0001,
			ModelProvider:    "local",
			ModelName:        "llama.cpp",
		},
		"external:claude-3-sonnet": {
			InputTokenPrice:  0.003, // $3.00 per 1M input tokens
			OutputTokenPrice: 0.015, // $15.00 per 1M output tokens
			ModelProvider:    "anthropic",
			ModelName:        "claude-3-sonnet",
		},
		"external:claude-3-opus": {
			InputTokenPrice:  0.015, // $15.00 per 1M input tokens
			OutputTokenPrice: 0.075, // $75.00 per 1M output tokens
			ModelProvider:    "anthropic",
			ModelName:        "claude-3-opus",
		},
		"external:gpt-4": {
			InputTokenPrice:  0.03, // $30.00 per 1M input tokens
			OutputTokenPrice: 0.06, // $60.00 per 1M output tokens
			ModelProvider:    "openai",
			ModelName:        "gpt-4",
		},
	}
	
	for model, pricing := range defaults {
		if _, exists := ct.modelPricing[model]; !exists {
			ct.modelPricing[model] = pricing
		}
	}
}

// TrackUsage records token usage for a skill execution
func (ct *CostTracker) TrackUsage(ctx context.Context, record *UsageRecord) error {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	
	// Calculate cost
	pricing, exists := ct.modelPricing[record.ModelUsed]
	if !exists {
		return fmt.Errorf("no pricing found for model: %s", record.ModelUsed)
	}
	
	inputCost := float64(record.InputTokens) / 1000.0 * pricing.InputTokenPrice
	outputCost := float64(record.OutputTokens) / 1000.0 * pricing.OutputTokenPrice
	record.Cost = inputCost + outputCost
	
	// Store usage record
	recordID := fmt.Sprintf("%s-%s-%d", record.SkillName, record.SessionID, time.Now().Unix())
	ct.usage[recordID] = record
	
	// Check limits and send notifications if needed
	if err := ct.checkLimits(ctx, record); err != nil {
		log.Printf("Warning: %v", err)
	}
	
	log.Printf("Tracked usage: %s used %d input/%d output tokens with %s, cost: $%.4f",
		record.SkillName, record.InputTokens, record.OutputTokens, record.ModelUsed, record.Cost)
	
	return nil
}

// checkLimits checks if usage exceeds configured limits
func (ct *CostTracker) checkLimits(ctx context.Context, record *UsageRecord) error {
	// Check daily limit
	if dailyLimit, exists := ct.dailyLimits[record.SkillName]; exists {
		dailyCost := ct.getDailyCost(record.SkillName)
		if dailyCost+record.Cost > dailyLimit {
			ct.sendNotification(ctx, "warning", 
				fmt.Sprintf("Daily cost limit exceeded for %s: $%.2f + $%.4f > $%.2f",
					record.SkillName, dailyCost, record.Cost, dailyLimit))
		}
	}
	
	// Check monthly limit
	if monthlyLimit, exists := ct.monthlyLimits[record.SkillName]; exists {
		monthlyCost := ct.getMonthlyCost(record.SkillName)
		if monthlyCost+record.Cost > monthlyLimit {
			ct.sendNotification(ctx, "critical",
				fmt.Sprintf("Monthly cost limit exceeded for %s: $%.2f + $%.4f > $%.2f",
					record.SkillName, monthlyCost, record.Cost, monthlyLimit))
		}
	}
	
	return nil
}

// GetCostSummary returns cost summary for a time period
func (ct *CostTracker) GetCostSummary(ctx context.Context, skillName string, days int) (*CostSummary, error) {
	ct.mu.RLock()
	defer ct.mu.RUnlock()
	
	summary := &CostSummary{
		SkillCosts: make(map[string]float64),
		ModelCosts: make(map[string]float64),
	}
	
	cutoff := time.Now().AddDate(0, 0, -days)
	executionCount := 0
	successCount := 0
	
	for _, record := range ct.usage {
		if record.ExecutionTime.Before(cutoff) {
			continue
		}
		
		if skillName != "" && record.SkillName != skillName {
			continue
		}
		
		summary.TotalCost += record.Cost
		summary.TotalTokens += record.InputTokens + record.OutputTokens
		executionCount++
		
		if record.Success {
			successCount++
		}
		
		summary.SkillCosts[record.SkillName] += record.Cost
		summary.ModelCosts[record.ModelUsed] += record.Cost
	}
	
	summary.ExecutionCount = executionCount
	if executionCount > 0 {
		summary.SuccessRate = float64(successCount) / float64(executionCount)
	}
	
	summary.DailyCost = ct.getDailyCost(skillName)
	summary.MonthlyCost = ct.getMonthlyCost(skillName)
	
	// Calculate cost savings (assuming local model vs external)
	localCost := ct.getLocalModelCost(skillName, days)
	externalCost := ct.getExternalModelCost(skillName, days)
	summary.CostSavings = externalCost - localCost
	
	return summary, nil
}

// getDailyCost calculates cost for today
func (ct *CostTracker) getDailyCost(skillName string) float64 {
	today := time.Now().Truncate(24 * time.Hour)
	dailyCost := 0.0
	
	for _, record := range ct.usage {
		if record.ExecutionTime.Before(today) {
			continue
		}
		
		if skillName != "" && record.SkillName != skillName {
			continue
		}
		
		dailyCost += record.Cost
	}
	
	return dailyCost
}

// getMonthlyCost calculates cost for this month
func (ct *CostTracker) getMonthlyCost(skillName string) float64 {
	now := time.Now()
	monthStart := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
	monthlyCost := 0.0
	
	for _, record := range ct.usage {
		if record.ExecutionTime.Before(monthStart) {
			continue
		}
		
		if skillName != "" && record.SkillName != skillName {
			continue
		}
		
		monthlyCost += record.Cost
	}
	
	return monthlyCost
}

// getLocalModelCost calculates what the cost would have been with local models
func (ct *CostTracker) getLocalModelCost(skillName string, days int) float64 {
	localCost := 0.0
	cutoff := time.Now().AddDate(0, 0, -days)
	
	for _, record := range ct.usage {
		if record.ExecutionTime.Before(cutoff) {
			continue
		}
		
		if skillName != "" && record.SkillName != skillName {
			continue
		}
		
		// Calculate cost as if using local llama.cpp
		localCost += float64(record.InputTokens+record.OutputTokens) / 1000.0 * 0.0001
	}
	
	return localCost
}

// getExternalModelCost calculates what the cost would have been with external models
func (ct *CostTracker) getExternalModelCost(skillName string, days int) float64 {
	externalCost := 0.0
	cutoff := time.Now().AddDate(0, 0, -days)
	
	for _, record := range ct.usage {
		if record.ExecutionTime.Before(cutoff) {
			continue
		}
		
		if skillName != "" && record.SkillName != skillName {
			continue
		}
		
		// Calculate cost as if using claude-3-sonnet
		inputCost := float64(record.InputTokens) / 1000.0 * 0.003
		outputCost := float64(record.OutputTokens) / 1000.0 * 0.015
		externalCost += inputCost + outputCost
	}
	
	return externalCost
}

// sendNotification sends cost alerts
func (ct *CostTracker) sendNotification(ctx context.Context, level, message string) {
	if ct.notificationHook == "" {
		return
	}
	
	notification := map[string]interface{}{
		"level":   level,
		"message": message,
		"time":    time.Now().Format(time.RFC3339),
	}
	
	data, _ := json.Marshal(notification)
	log.Printf("Cost notification: %s", string(data))
	
	// In a real implementation, this would send to Slack, email, etc.
	// For now, we just log it
}

// SetDailyLimit sets daily cost limit for a skill
func (ct *CostTracker) SetDailyLimit(skillName string, limit float64) {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	ct.dailyLimits[skillName] = limit
}

// SetMonthlyLimit sets monthly cost limit for a skill
func (ct *CostTracker) SetMonthlyLimit(skillName string, limit float64) {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	ct.monthlyLimits[skillName] = limit
}

// SetNotificationHook sets webhook URL for cost notifications
func (ct *CostTracker) SetNotificationHook(hookURL string) {
	ct.mu.Lock()
	defer ct.mu.Unlock()
	ct.notificationHook = hookURL
}

// GetOptimalModel suggests the most cost-effective model for a task
func (ct *CostTracker) GetOptimalModel(taskComplexity string, privacyRequired bool, accuracyRequired float64) string {
	if privacyRequired {
		return "local:llama.cpp"
	}
	
	switch taskComplexity {
	case "simple":
		return "local:llama.cpp"
	case "medium":
		if accuracyRequired > 0.9 {
			return "external:claude-3-sonnet"
		}
		return "local:llama.cpp"
	case "complex":
		if accuracyRequired > 0.95 {
			return "external:claude-3-opus"
		}
		return "external:claude-3-sonnet"
	default:
		return "local:llama.cpp"
	}
}

// ExportUsage exports usage data for analysis
func (ct *CostTracker) ExportUsage(ctx context.Context, format string) ([]byte, error) {
	ct.mu.RLock()
	defer ct.mu.RUnlock()
	
	switch format {
	case "json":
		return json.MarshalIndent(ct.usage, "", "  ")
	case "csv":
		// CSV export implementation
		return []byte("skill_name,model_used,input_tokens,output_tokens,cost,execution_time,success\n"), nil
	default:
		return nil, fmt.Errorf("unsupported format: %s", format)
	}
}
