package workflows

import (
	"context"
	"fmt"
	"time"

	"go.temporal.io/sdk/workflow"
)

// ConsensusDecisionInput represents input for consensus-based decision making
type ConsensusDecisionInput struct {
	DecisionType     string                 `json:"decisionType"` // "infrastructure-change", "security-policy", "cost-optimization", "resource-allocation"
	ProposalID       string                 `json:"proposalId"`
	ProposerAgent    string                 `json:"proposerAgent"`
	Proposal         Proposal               `json:"proposal"`
	RequiredVotes    int                    `json:"requiredVotes"` // Quorum size
	VotingTimeout    time.Duration           `json:"votingTimeout"`
	EmergencyMode    bool                   `json:"emergencyMode"` // Skip some checks for urgent decisions
	Parameters       map[string]interface{}  `json:"parameters"`
}

// Proposal represents a proposal for consensus decision
type Proposal struct {
	ID              string                 `json:"id"`
	Type            string                 `json:"type"`
	Title           string                 `json:"title"`
	Description     string                 `json:"description"`
	Impact          string                 `json:"impact"`
	RiskAssessment  RiskAssessment         `json:"riskAssessment"`
	CompensationPlan CompensationPlan      `json:"compensationPlan"`
	EstimatedCost    float64                `json:"estimatedCost"`
	EstimatedTime    time.Duration         `json:"estimatedTime"`
	Dependencies    []string               `json:"dependencies"`
	Metadata        map[string]interface{}  `json:"metadata"`
}

// ConsensusDecisionOutput represents the result of consensus decision making
type ConsensusDecisionOutput struct {
	DecisionID       string               `json:"decisionId"`
	ProposalID        string               `json:"proposalId"`
	Decision          DecisionResult       `json:"decision"`
	VotingResults     []VoteResult        `json:"votingResults"`
	ConsensusReached  bool                 `json:"consensusReached"`
	ExecutionPlan     ExecutionPlan        `json:"executionPlan"`
	CompensationPlan  CompensationPlan     `json:"compensationPlan"`
	Timestamp         time.Time            `json:"timestamp"`
	ExecutionStatus   string               `json:"executionStatus"` // "pending", "approved", "rejected", "executing", "completed", "failed"
}

// DecisionResult represents the final consensus decision
type DecisionResult struct {
	Outcome        string    `json:"outcome"` // "approve", "reject", "modify", "escalate"
	Confidence     float64   `json:"confidence"`
	Rationale      string    `json:"rationale"`
	Conditions     []string   `json:"conditions"`
	RequiredActions []string   `json:"requiredActions"`
	NextSteps      []string   `json:"nextSteps"`
}

// VoteResult represents a single vote from an agent
type VoteResult struct {
	AgentID      string    `json:"agentId"`
	Vote         string    `json:"vote"` // "approve", "reject", "abstain"
	Reasoning     string    `json:"reasoning"`
	Confidence    float64   `json:"confidence"`
	Timestamp     time.Time `json:"timestamp"`
	VetoPower    bool      `json:"vetoPower"` // Some agents have veto authority
}

// ExecutionPlan represents the plan for executing the decision
type ExecutionPlan struct {
	Steps           []ExecutionStep      `json:"steps"`
	EstimatedTime    time.Duration        `json:"estimatedTime"`
	RequiredResources []ResourceRequirement `json:"requiredResources"`
	RiskMitigation  []RiskMitigation     `json:"riskMitigation"`
	RollbackPlan    RollbackPlan         `json:"rollbackPlan"`
}

// ExecutionStep represents a single step in the execution plan
type ExecutionStep struct {
	ID              string        `json:"id"`
	Name            string        `json:"name"`
	Type            string        `json:"type"` // "sequential", "parallel", "conditional"
	Description     string        `json:"description"`
	Command         string        `json:"command"`
	Dependencies    []string      `json:"dependencies"`
	Timeout         time.Duration `json:"timeout"`
	RetryPolicy     RetryPolicy   `json:"retryPolicy"`
	ExpectedOutcome  string        `json:"expectedOutcome"`
}

// ResourceRequirement represents resources needed for execution
type ResourceRequirement struct {
	Type        string  `json:"type"` // "cpu", "memory", "storage", "network", "custom"
	Amount      float64 `json:"amount"`
	Unit        string  `json:"unit"`
	Priority    string  `json:"priority"` // "critical", "high", "medium", "low"
	Allocatable  bool    `json:"allocatable"`
}

// RiskMitigation represents a risk mitigation strategy
type RiskMitigation struct {
	RiskID       string `json:"riskId"`
	RiskType     string `json:"riskType"`
	Strategy     string `json:"strategy"`
	Probability  float64 `json:"probability"`
	Impact       string `json:"impact"`
	Mitigation   string `json:"mitigation"`
	Contingency  string `json:"contingency"`
}

// RollbackPlan represents the plan for rolling back changes
type RollbackPlan struct {
	TriggerConditions []string      `json:"triggerConditions"`
	RollbackSteps    []RollbackStep `json:"rollbackSteps"`
	MaxRollbackTime  time.Duration `json:"maxRollbackTime"`
	DataBackup       bool          `json:"dataBackup"`
	VerificationPlan  VerificationPlan `json:"verificationPlan"`
}

// RollbackStep represents a single rollback step
type RollbackStep struct {
	ID          string        `json:"id"`
	Name        string        `json:"name"`
	Description string        `json:"description"`
	Command     string        `json:"command"`
	Timeout     time.Duration `json:"timeout"`
	Verification bool          `json:"verification"`
}

// VerificationPlan represents verification steps after rollback
type VerificationPlan struct {
	Checks       []VerificationCheck `json:"checks"`
	SuccessCriteria []string       `json:"successCriteria"`
	FallbackAction string           `json:"fallbackAction"`
}

// VerificationCheck represents a single verification check
type VerificationCheck struct {
	Name        string `json:"name"`
	Type        string `json:"type"` // "automated", "manual", "api-call"
	Command     string `json:"command"`
	Expected    string `json:"expected"`
	Timeout     time.Duration `json:"timeout"`
	Critical    bool   `json:"critical"`
}

// ConsensusDecisionWorkflow implements durable consensus-based decision making
func ConsensusDecisionWorkflow(ctx workflow.Context, input ConsensusDecisionInput) (*ConsensusDecisionOutput, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting consensus decision workflow", 
		"decisionType", input.DecisionType,
		"proposalId", input.ProposalID)

	// Generate unique decision ID
	decisionID := fmt.Sprintf("consensus-%s-%d", input.DecisionType, workflow.Now(ctx).Unix())
	
	output := &ConsensusDecisionOutput{
		DecisionID:      decisionID,
		ProposalID:       input.ProposalID,
		VotingResults:    []VoteResult{},
		ConsensusReached: false,
		Timestamp:       workflow.Now(ctx),
		ExecutionStatus:  "pending",
	}

	// Phase 1: Proposal Validation
	logger.Info("Phase 1: Validating proposal")
	
	validationInput := ProposalValidationInput{
		Proposal:      input.Proposal,
		DecisionType:  input.DecisionType,
		EmergencyMode: input.EmergencyMode,
	}
	
	var validation ProposalValidationResult
	err := workflow.ExecuteActivity(ctx, activities.ValidateProposalActivity, validationInput).Get(ctx, &validation)
	if err != nil {
		logger.Error("Proposal validation failed", "error", err)
		return nil, fmt.Errorf("proposal validation failed: %w", err)
	}

	if !validation.IsValid {
		output.Decision = DecisionResult{
			Outcome:   "reject",
			Confidence: 1.0,
			Rationale:  validation.RejectionReason,
		}
		output.ExecutionStatus = "rejected"
		return output, nil
	}

	// Phase 2: Agent Notification and Voting
	logger.Info("Phase 2: Notifying agents and collecting votes")
	
	// Create voting selector with timeout
	votingCtx, cancelVoting := workflow.WithCancel(ctx)
	defer cancelVoting()
	
	votingSelector := workflow.NewSelector(votingCtx)
	
	// Start voting activity
	votingFuture := workflow.ExecuteActivity(votingCtx, activities.CollectVotesActivity, VotingInput{
		ProposalID:    input.ProposalID,
		RequiredVotes:  input.RequiredVotes,
		VotingTimeout:  input.VotingTimeout,
		Agents:        []string{"agent-1", "agent-2", "agent-3"}, // From agent registry
	})
	
	votingSelector.AddFuture(votingFuture, func(f workflow.Future) {
		var votes []VoteResult
		if err := f.Get(votingCtx, &votes); err != nil {
			logger.Error("Vote collection failed", "error", err)
			return
		}
		
		output.VotingResults = votes
		logger.Info("Votes collected", "voteCount", len(votes))
	})

	// Wait for voting to complete or timeout
	votingSelector.Select(votingCtx)

	// Phase 3: Consensus Calculation
	logger.Info("Phase 3: Calculating consensus")
	
	consensusInput := ConsensusCalculationInput{
		Votes:          output.VotingResults,
		RequiredVotes:   input.RequiredVotes,
		DecisionType:    input.DecisionType,
		Proposal:        input.Proposal,
	}
	
	var consensusCalculation ConsensusCalculationResult
	err = workflow.ExecuteActivity(ctx, activities.CalculateConsensusActivity, consensusInput).Get(ctx, &consensusCalculation)
	if err != nil {
		logger.Error("Consensus calculation failed", "error", err)
		return nil, fmt.Errorf("consensus calculation failed: %w", err)
	}

	output.ConsensusReached = consensusCalculation.Reached
	output.Decision = consensusCalculation.Decision

	// Phase 4: Execution Plan Generation (if approved)
	if output.ConsensusReached && output.Decision.Outcome == "approve" {
		logger.Info("Phase 4: Generating execution plan")
		
		planningInput := ExecutionPlanInput{
			Proposal:      input.Proposal,
			Decision:      output.Decision,
			Consensus:     consensusCalculation,
			Parameters:    input.Parameters,
		}
		
		var executionPlan ExecutionPlan
		err = workflow.ExecuteActivity(ctx, activities.GenerateExecutionPlanActivity, planningInput).Get(ctx, &executionPlan)
		if err != nil {
			logger.Error("Execution plan generation failed", "error", err)
			return nil, fmt.Errorf("execution plan generation failed: %w", err)
		}
		
		output.ExecutionPlan = executionPlan
		output.CompensationPlan = input.Proposal.CompensationPlan
		output.ExecutionStatus = "approved"
	} else {
		output.ExecutionStatus = "rejected"
	}

	// Phase 5: Decision Recording and Notification
	logger.Info("Phase 5: Recording decision and notifying agents")
	
	recordingInput := DecisionRecordingInput{
		DecisionID:      decisionID,
		ProposalID:       input.ProposalID,
		Decision:         output.Decision,
		ConsensusReached: output.ConsensusReached,
		VotingResults:    output.VotingResults,
		Timestamp:        workflow.Now(ctx),
	}
	
	err = workflow.ExecuteActivity(ctx, activities.RecordDecisionActivity, recordingInput).Get(ctx, nil)
	if err != nil {
		logger.Error("Decision recording failed", "error", err)
		// Non-fatal error, continue workflow
	}

	// Phase 6: Execute Decision (if approved)
	if output.ConsensusReached && output.Decision.Outcome == "approve" {
		logger.Info("Phase 6: Executing approved decision")
		
		output.ExecutionStatus = "executing"
		
		executionInput := DecisionExecutionInput{
			DecisionID:     decisionID,
			ExecutionPlan:  output.ExecutionPlan,
			Proposal:       input.Proposal,
		}
		
		var executionResult DecisionExecutionResult
		err = workflow.ExecuteActivity(ctx, activities.ExecuteDecisionActivity, executionInput).Get(ctx, &executionResult)
		if err != nil {
			logger.Error("Decision execution failed", "error", err)
			output.ExecutionStatus = "failed"
			// Initiate compensation
			workflow.ExecuteActivity(ctx, activities.InitiateCompensationActivity, InitiateCompensationInput{
				DecisionID:      decisionID,
				CompensationPlan: output.CompensationPlan,
				FailureReason:   err.Error(),
			})
		} else {
			output.ExecutionStatus = "completed"
		}
	}

	logger.Info("Consensus decision workflow completed",
		"decisionID", decisionID,
		"consensusReached", output.ConsensusReached,
		"executionStatus", output.ExecutionStatus)

	return output, nil
}

// Supporting types

type ProposalValidationInput struct {
	Proposal      Proposal `json:"proposal"`
	DecisionType  string   `json:"decisionType"`
	EmergencyMode bool     `json:"emergencyMode"`
}

type ProposalValidationResult struct {
	IsValid         bool   `json:"isValid"`
	RejectionReason string `json:"rejectionReason,omitempty"`
	Warnings       []string `json:"warnings"`
}

type VotingInput struct {
	ProposalID   string   `json:"proposalId"`
	RequiredVotes int      `json:"requiredVotes"`
	VotingTimeout time.Duration `json:"votingTimeout"`
	Agents       []string `json:"agents"`
}

type ConsensusCalculationInput struct {
	Votes        []VoteResult `json:"votes"`
	RequiredVotes int          `json:"requiredVotes"`
	DecisionType string       `json:"decisionType"`
	Proposal     Proposal     `json:"proposal"`
}

type ConsensusCalculationResult struct {
	Reached bool           `json:"reached"`
	Decision DecisionResult `json:"decision"`
	QuorumMet bool          `json:"quorumMet"`
	Majority  bool          `json:"majority"`
}

type ExecutionPlanInput struct {
	Proposal   Proposal             `json:"proposal"`
	Decision   DecisionResult       `json:"decision"`
	Consensus  ConsensusCalculationResult `json:"consensus"`
	Parameters map[string]interface{} `json:"parameters"`
}

type DecisionRecordingInput struct {
	DecisionID      string        `json:"decisionId"`
	ProposalID       string        `json:"proposalId"`
	Decision         DecisionResult `json:"decision"`
	ConsensusReached bool          `json:"consensusReached"`
	VotingResults    []VoteResult  `json:"votingResults"`
	Timestamp        time.Time     `json:"timestamp"`
}

type DecisionExecutionInput struct {
	DecisionID    string        `json:"decisionId"`
	ExecutionPlan ExecutionPlan `json:"executionPlan"`
	Proposal      Proposal      `json:"proposal"`
}

type DecisionExecutionResult struct {
	Success       bool          `json:"success"`
	ExecutionTime time.Duration `json:"executionTime"`
	Output        string        `json:"output"`
	Errors        []string      `json:"errors"`
	CompletedSteps []string      `json:"completedSteps"`
}

type InitiateCompensationInput struct {
	DecisionID       string          `json:"decisionId"`
	CompensationPlan CompensationPlan `json:"compensationPlan"`
	FailureReason    string          `json:"failureReason"`
}
