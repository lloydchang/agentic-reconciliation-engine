package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/joho/godotenv"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
)

// AutonomousDecisionEngine enables fully autonomous AI operations
// with learning capabilities and reconciliation safety nets
type AutonomousDecisionEngine struct {
	temporalClient  client.Client
	redisClient    *redis.Client
	learningStore  map[string]LearningData
	riskThreshold  float64
	experience     int
}

// LearningData captures trial-and-error learning
type LearningData struct {
	Operation     string                 `json:"operation"`
	Outcome       string                 `json:"outcome"`
	Success       bool                   `json:"success"`
	Cost          float64                `json:"cost"`
	TimeTaken     time.Duration          `json:"time_taken"`
	ErrorRate     float64                `json:"error_rate"`
	RecoveryTime  time.Duration          `json:"recovery_time"`
	LearnedFrom   string                 `json:"learned_from"`
	Context       map[string]interface{} `json:"context"`
	Timestamp     time.Time              `json:"timestamp"`
}

// AutonomousOperation represents a fully autonomous operation
type AutonomousOperation struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Priority    string                 `json:"priority"`
	Risk        string                 `json:"risk"`
	Plan        map[string]interface{} `json:"plan"`
	Confidence  float64                `json:"confidence"`
	Learned     bool                   `json:"learned"`
	CreatedAt   time.Time              `json:"created_at"`
	ExecutedAt  *time.Time            `json:"executed_at,omitempty"`
}

// ReconciliationGuard provides safety net for autonomous operations
type ReconciliationGuard struct {
	MaxCostPerHour    float64 `json:"max_cost_per_hour"`
	MaxFailureRate    float64 `json:"max_failure_rate"`
	RequireApproval  bool    `json:"require_approval"`
	RollbackEnabled  bool    `json:"rollback_enabled"`
}

func main() {
	// Load configuration
	if err := godotenv.Load(); err != nil {
		log.Printf("Warning: Could not load .env file: %v", err)
	}

	// Initialize autonomous decision engine
	engine := &AutonomousDecisionEngine{
		riskThreshold: 0.3, // Increased risk tolerance for learning
		learningStore: make(map[string]LearningData),
		experience:    0,
	}

	// Setup Redis for learning persistence
	engine.setupRedis()
	
	// Setup Temporal client
	engine.setupTemporal()

	// Start autonomous decision worker
	engine.startAutonomousWorker()
}

func (e *AutonomousDecisionEngine) setupRedis() {
	// Connect to Redis for learning data persistence
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "", // no password set
		DB:       0,  // use default DB
	})

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		log.Printf("Warning: Redis not available, learning will be in-memory only: %v", err)
		e.redisClient = nil
		return
	}

	e.redisClient = rdb
	log.Println("Connected to Redis for learning persistence")
}

func (e *AutonomousDecisionEngine) setupTemporal() {
	// Connect to Temporal for workflow orchestration
	clientOptions := client.Options{
		HostPort:  os.Getenv("TEMPORAL_ADDRESS"),
		Namespace:  os.Getenv("TEMPORAL_NAMESPACE"),
	}

	if clientOptions.HostPort == "" {
		clientOptions.HostPort = "temporal-frontend:7233"
	}
	if clientOptions.Namespace == "" {
		clientOptions.Namespace = "default"
	}

	c, err := client.Dial(clientOptions)
	if err != nil {
		log.Printf("Warning: Failed to connect to Temporal: %v. Continuing for local development...", err)
		return
	}

	e.temporalClient = c
	log.Println("Connected to Temporal for autonomous orchestration")
}

func (e *AutonomousDecisionEngine) startAutonomousWorker() {
	if e.temporalClient == nil || (fmt.Sprintf("%T", e.temporalClient) != "<nil>" && fmt.Sprintf("%v", e.temporalClient) == "<nil>") {
		log.Printf("Warning: Temporal client is nil or invalid, skipping autonomous worker start")
		return
	}
	// Create worker for autonomous operations
	taskQueue := os.Getenv("TEMPORAL_WORKER_TASK_QUEUE")
	if taskQueue == "" {
		taskQueue = "autonomous-decision-engine"
	}
	options := worker.Options{}
	w := worker.New(e.temporalClient, taskQueue, options)
	
	// Register autonomous workflows
	w.RegisterWorkflow(e.AutonomousOperationWorkflow)
	w.RegisterActivity(e.ExecuteAutonomousOperation)
	w.RegisterActivity(e.LearnFromOutcome)
	w.RegisterActivity(e.ApplyReconciliationGuard)

	// Start worker
	err := w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalf("Failed to start autonomous worker: %v", err)
	}
}

// AutonomousOperationWorkflow - Main workflow for autonomous operations
func (e *AutonomousDecisionEngine) AutonomousOperationWorkflow(ctx workflow.Context, operation AutonomousOperation) error {
	ao := workflow.ActivityOptions{
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    3,
		},
		StartToCloseTimeout: 10 * time.Minute,
	}
	
	// Step 1: Apply reconciliation guard
	var guardPassed bool
	guardCtx := workflow.WithActivityOptions(ctx, workflow.ActivityOptions{
		ActivityID: "apply-guard",
		StartToCloseTimeout: 1 * time.Minute,
	})
	err := workflow.ExecuteActivity(guardCtx, e.ApplyReconciliationGuard, operation).Get(ctx, &guardPassed)
	if err != nil {
		return fmt.Errorf("reconciliation guard failed: %w", err)
	}

	if !guardPassed {
		return fmt.Errorf("operation blocked by reconciliation guard: %s", operation.ID)
	}

	// Step 2: Execute autonomous operation
	var outcome LearningData
	ctx = workflow.WithActivityOptions(ctx, ao)
	err = workflow.ExecuteActivity(ctx, e.ExecuteAutonomousOperation, operation).Get(ctx, &outcome)
	if err != nil {
		return fmt.Errorf("autonomous operation failed: %w", err)
	}

	// Step 3: Learn from outcome
	var learned bool
	err = workflow.ExecuteActivity(ctx, e.LearnFromOutcome, outcome).Get(ctx, &learned)
	if err != nil {
		log.Printf("Warning: Failed to learn from outcome: %v", err)
	}

	// Step 4: Update experience counter
	e.experience++
	log.Printf("Autonomous operation %s completed. Experience count: %d, Learned: %v", operation.ID, e.experience, learned)

	return nil
}

// ExecuteAutonomousOperation - Execute operation with full autonomy
func (e *AutonomousDecisionEngine) ExecuteAutonomousOperation(ctx context.Context, operation AutonomousOperation) (LearningData, error) {
	startTime := time.Now()
	
	log.Printf("🚀 Executing autonomous operation: %s (Type: %s, Risk: %s)", operation.ID, operation.Type, operation.Risk)

	// Simulate autonomous execution based on operation type
	var outcome LearningData
	outcome.Operation = operation.ID
	outcome.Context = operation.Plan
	outcome.Timestamp = startTime

	switch operation.Type {
	case "cost_optimization":
		outcome = e.executeCostOptimization(ctx, operation)
	case "security_fix":
		outcome = e.executeSecurityFix(ctx, operation)
	case "scaling_decision":
		outcome = e.executeScalingDecision(ctx, operation)
	case "deployment_update":
		outcome = e.executeDeploymentUpdate(ctx, operation)
	case "performance_tuning":
		outcome = e.executePerformanceTuning(ctx, operation)
	default:
		outcome = e.executeGenericOperation(ctx, operation)
	}

	// Calculate execution metrics
	outcome.TimeTaken = time.Since(startTime)
	outcome.LearnedFrom = "autonomous_execution"

	log.Printf("✅ Autonomous operation %s completed in %v (Success: %v)", operation.ID, outcome.TimeTaken, outcome.Success)

	return outcome, nil
}

// ApplyReconciliationGuard - Safety net using reconciliation engines
func (e *AutonomousDecisionEngine) ApplyReconciliationGuard(ctx context.Context, operation AutonomousOperation) (bool, error) {
	guard := ReconciliationGuard{
		MaxCostPerHour:   1000.0, // Increased for learning
		MaxFailureRate:   0.15,    // 15% failure rate threshold
		RequireApproval:  false,      // Full autonomy enabled
		RollbackEnabled:  true,       // Always enable rollback
	}

	// Check recent failure rate for this operation type
	failureRate := e.calculateFailureRate(operation.Type)
	if failureRate > guard.MaxFailureRate {
		log.Printf("🛡️ Reconciliation guard blocked operation %s: failure rate %.2f > %.2f", 
			operation.ID, failureRate, guard.MaxFailureRate)
		return false, nil
	}

	// Check cost impact
	costImpact := e.estimateCostImpact(operation)
	if costImpact > guard.MaxCostPerHour {
		log.Printf("🛡️ Reconciliation guard blocked operation %s: cost impact $%.2f > $%.2f", 
			operation.ID, costImpact, guard.MaxCostPerHour)
		return false, nil
	}

	// Check if reconciliation loops can handle this
	if !e.canReconcile(operation) {
		log.Printf("🛡️ Reconciliation guard blocked operation %s: cannot be safely reconciled", operation.ID)
		return false, nil
	}

	log.Printf("✅ Reconciliation guard approved operation %s", operation.ID)
	return true, nil
}

// LearnFromOutcome - Learn from trial and error
func (e *AutonomousDecisionEngine) LearnFromOutcome(ctx context.Context, outcome LearningData) (bool, error) {
	// Store learning data
	operationKey := fmt.Sprintf("%s:%s", outcome.Operation, outcome.Context["type"])
	
	// Update in-memory store
	e.learningStore[operationKey] = outcome
	
	// Persist to Redis if available
	if e.redisClient != nil {
		learningJSON, _ := json.Marshal(outcome)
		err := e.redisClient.Set(ctx, operationKey, learningJSON, 24*time.Hour).Err()
		if err != nil {
			log.Printf("Warning: Failed to persist learning data to Redis: %v", err)
		}
	}

	// Update decision models based on outcome
	e.updateDecisionModels(outcome)

	// Check if we learned something significant
	learned := e.isSignificantLearning(outcome)
	
	log.Printf("🧠 Learned from operation %s: %v (Significant: %v)", outcome.Operation, learned, learned)
	
	return learned, nil
}

// Operation-specific execution methods with learning
func (e *AutonomousDecisionEngine) executeCostOptimization(ctx context.Context, operation AutonomousOperation) LearningData {
	// Simulate cost optimization with learning
	outcome := LearningData{Success: true}
	
	// Use learned patterns to make better decisions
	previousOutcomes := e.getPreviousOutcomes("cost_optimization")
	if len(previousOutcomes) > 0 {
		// Apply learned optimizations
		avgSuccess := e.calculateAverageSuccess(previousOutcomes)
		outcome.Success = avgSuccess > 0.7 // Use learned success rate
		outcome.Cost = e.calculateOptimizedCost(operation, previousOutcomes)
	} else {
		// First-time optimization with conservative approach
		outcome.Cost = 50.0 // Conservative cost estimate
	}

	outcome.Outcome = "cost_optimized"
	outcome.LearnedFrom = "trial_and_error"
	
	return outcome
}

func (e *AutonomousDecisionEngine) executeSecurityFix(ctx context.Context, operation AutonomousOperation) LearningData {
	outcome := LearningData{Success: true}
	
	// Learn from previous security operations
	previousOutcomes := e.getPreviousOutcomes("security_fix")
	if len(previousOutcomes) > 0 {
		// Apply learned security patterns
		riskReduction := e.calculateRiskReduction(previousOutcomes)
		outcome.Success = riskReduction > 0.8
		outcome.ErrorRate = 1.0 - riskReduction
	} else {
		// Conservative security fix
		outcome.ErrorRate = 0.1
	}

	outcome.Outcome = "security_fixed"
	outcome.LearnedFrom = "security_learning"
	
	return outcome
}

func (e *AutonomousDecisionEngine) executeScalingDecision(ctx context.Context, operation AutonomousOperation) LearningData {
	outcome := LearningData{Success: true}
	
	// Use learned scaling patterns
	previousOutcomes := e.getPreviousOutcomes("scaling_decision")
	if len(previousOutcomes) > 0 {
		// Apply learned scaling models
		optimalScale := e.calculateOptimalScaling(operation, previousOutcomes)
		outcome.Success = true
		outcome.Cost = optimalScale.Cost
		outcome.Context = map[string]interface{}{
			"optimal_replicas": optimalScale.Replicas,
			"learned_scaling":  true,
		}
	} else {
		// Conservative scaling
		outcome.Context = map[string]interface{}{
			"optimal_replicas": 2,
			"learned_scaling":  false,
		}
		outcome.Cost = 100.0
	}

	outcome.Outcome = "scaling_applied"
	outcome.LearnedFrom = "scaling_learning"
	
	return outcome
}

func (e *AutonomousDecisionEngine) executeDeploymentUpdate(ctx context.Context, operation AutonomousOperation) LearningData {
	outcome := LearningData{Success: true}
	
	// Learn from previous deployments
	previousOutcomes := e.getPreviousOutcomes("deployment_update")
	if len(previousOutcomes) > 0 {
		// Apply learned deployment strategies
		successRate := e.calculateDeploymentSuccessRate(previousOutcomes)
		outcome.Success = successRate > 0.85
		outcome.RecoveryTime = e.calculateAverageRecoveryTime(previousOutcomes)
	} else {
		// Conservative deployment
		outcome.Success = true
		outcome.RecoveryTime = 5 * time.Minute
	}

	outcome.Outcome = "deployment_updated"
	outcome.LearnedFrom = "deployment_learning"
	
	return outcome
}

func (e *AutonomousDecisionEngine) executePerformanceTuning(ctx context.Context, operation AutonomousOperation) LearningData {
	outcome := LearningData{Success: true}
	
	// Use learned performance patterns
	previousOutcomes := e.getPreviousOutcomes("performance_tuning")
	if len(previousOutcomes) > 0 {
		// Apply learned optimizations
		improvement := e.calculatePerformanceImprovement(previousOutcomes)
		outcome.Success = improvement > 0.1 // 10% improvement threshold
		outcome.Context = map[string]interface{}{
			"performance_improvement": improvement,
			"learned_optimization":   true,
		}
	} else {
		// Conservative tuning
		outcome.Context = map[string]interface{}{
			"performance_improvement": 0.05,
			"learned_optimization":   false,
		}
	}

	outcome.Outcome = "performance_tuned"
	outcome.LearnedFrom = "performance_learning"
	
	return outcome
}

func (e *AutonomousDecisionEngine) executeGenericOperation(ctx context.Context, operation AutonomousOperation) LearningData {
	// Generic autonomous operation with basic learning
	return LearningData{
		Operation:    operation.ID,
		Outcome:      "completed",
		Success:      true,
		Cost:         100.0,
		ErrorRate:    0.05,
		LearnedFrom:   "generic_learning",
		Context:      operation.Plan,
		Timestamp:    time.Now(),
	}
}

// Learning and decision support methods
func (e *AutonomousDecisionEngine) getPreviousOutcomes(operationType string) []LearningData {
	var outcomes []LearningData
	
	// Check Redis first
	if e.redisClient != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		
		keys, err := e.redisClient.Keys(ctx, fmt.Sprintf("%s:*", operationType)).Result()
		if err == nil {
			for _, key := range keys {
				data, err := e.redisClient.Get(ctx, key).Result()
				if err == nil {
					var outcome LearningData
					if err := json.Unmarshal([]byte(data), &outcome); err == nil {
						outcomes = append(outcomes, outcome)
					}
				}
			}
		}
	}
	
	// Supplement with in-memory data
	for _, outcome := range e.learningStore {
		if outcome.Context["type"] == operationType {
			outcomes = append(outcomes, outcome)
		}
	}
	
	return outcomes
}

func (e *AutonomousDecisionEngine) calculateAverageSuccess(outcomes []LearningData) float64 {
	if len(outcomes) == 0 {
		return 0.5
	}
	
	total := 0.0
	for _, outcome := range outcomes {
		if outcome.Success {
			total += 1.0
		}
	}
	
	return total / float64(len(outcomes))
}

func (e *AutonomousDecisionEngine) calculateOptimizedCost(operation AutonomousOperation, outcomes []LearningData) float64 {
	if len(outcomes) == 0 {
		return 100.0
	}
	
	// Learn from previous cost optimizations
	totalCost := 0.0
	for _, outcome := range outcomes {
		totalCost += outcome.Cost
	}
	
	avgCost := totalCost / float64(len(outcomes))
	
	// Apply learning factor (reduce cost over time)
	learningFactor := 1.0 - (float64(e.experience) * 0.01)
	if learningFactor < 0.7 {
		learningFactor = 0.7
	}
	
	return avgCost * learningFactor
}

func (e *AutonomousDecisionEngine) calculateRiskReduction(outcomes []LearningData) float64 {
	if len(outcomes) == 0 {
		return 0.5
	}
	
	totalRisk := 0.0
	for _, outcome := range outcomes {
		totalRisk += (1.0 - outcome.ErrorRate)
	}
	
	return totalRisk / float64(len(outcomes))
}

func (e *AutonomousDecisionEngine) calculateOptimalScaling(operation AutonomousOperation, outcomes []LearningData) struct {
	Replicas int
	Cost      float64
} {
	// Simple learning-based scaling optimization
	if len(outcomes) == 0 {
		return struct{Replicas int; Cost float64}{2, 100.0}
	}
	
	// Find most successful scaling outcome
	bestOutcome := outcomes[0]
	for _, outcome := range outcomes {
		if outcome.Success && outcome.Cost < bestOutcome.Cost {
			bestOutcome = outcome
		}
	}
	
	// Extract learned optimal replicas
	if replicas, ok := bestOutcome.Context["optimal_replicas"].(float64); ok {
		return struct{Replicas int; Cost float64}{int(replicas), bestOutcome.Cost}
	}
	
	return struct{Replicas int; Cost float64}{2, 100.0}
}

func (e *AutonomousDecisionEngine) calculateDeploymentSuccessRate(outcomes []LearningData) float64 {
	return e.calculateAverageSuccess(outcomes)
}

func (e *AutonomousDecisionEngine) calculateAverageRecoveryTime(outcomes []LearningData) time.Duration {
	if len(outcomes) == 0 {
		return 5 * time.Minute
	}
	
	totalTime := time.Duration(0)
	for _, outcome := range outcomes {
		totalTime += outcome.RecoveryTime
	}
	
	return totalTime / time.Duration(len(outcomes))
}

func (e *AutonomousDecisionEngine) calculatePerformanceImprovement(outcomes []LearningData) float64 {
	if len(outcomes) == 0 {
		return 0.05
	}
	
	totalImprovement := 0.0
	for _, outcome := range outcomes {
		if improvement, ok := outcome.Context["performance_improvement"].(float64); ok {
			totalImprovement += improvement
		}
	}
	
	return totalImprovement / float64(len(outcomes))
}

// Safety and reconciliation methods
func (e *AutonomousDecisionEngine) calculateFailureRate(operationType string) float64 {
	outcomes := e.getPreviousOutcomes(operationType)
	if len(outcomes) == 0 {
		return 0.05 // Default 5% failure rate
	}
	
	failures := 0
	for _, outcome := range outcomes {
		if !outcome.Success {
			failures++
		}
	}
	
	return float64(failures) / float64(len(outcomes))
}

func (e *AutonomousDecisionEngine) estimateCostImpact(operation AutonomousOperation) float64 {
	// Simple cost estimation based on operation type and risk
	baseCost := 100.0
	
	riskMultiplier := 1.0
	switch operation.Risk {
	case "low":
		riskMultiplier = 0.5
	case "medium":
		riskMultiplier = 1.0
	case "high":
		riskMultiplier = 2.0
	case "critical":
		riskMultiplier = 5.0
	}
	
	return baseCost * riskMultiplier
}

func (e *AutonomousDecisionEngine) canReconcile(operation AutonomousOperation) bool {
	// Check if Kubernetes reconciliation loops can handle this operation
	reconcilableOps := map[string]bool{
		"cost_optimization": true,
		"scaling_decision": true,
		"performance_tuning": true,
		"deployment_update": true,
		"security_fix": true,
	}
	
	return reconcilableOps[operation.Type]
}

func (e *AutonomousDecisionEngine) updateDecisionModels(outcome LearningData) {
	// Update internal decision models based on learned outcomes
	log.Printf("🧠 Updating decision models based on outcome from %s", outcome.Operation)
	
	// This would integrate with more sophisticated ML models
	// For now, we store the learning data for future decisions
}

func (e *AutonomousDecisionEngine) isSignificantLearning(outcome LearningData) bool {
	// Determine if this outcome provides significant learning
	significanceFactors := 0
	
	// Success rate improvement
	if outcome.Success {
		significanceFactors++
	}
	
	// Cost efficiency
	if outcome.Cost < 100.0 {
		significanceFactors++
	}
	
	// Error rate reduction
	if outcome.ErrorRate < 0.1 {
		significanceFactors++
	}
	
	// Recovery time improvement
	if outcome.RecoveryTime < 5*time.Minute {
		significanceFactors++
	}
	
	return significanceFactors >= 3
}
