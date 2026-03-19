package agent_sandbox

import (
	"context"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/sandbox"
)

// SkillIntegration handles skill-specific Agent Sandbox execution
type SkillIntegration struct {
	integrator   *AgentIntegrator
	config       *config.AgentSandboxConfig
	templateMap  map[string]string // Maps skill patterns to templates
	resourceMap  map[string]sandbox.ResourceSpec // Maps skill types to default resources
}

// SkillMetadata represents extended skill metadata for Agent Sandbox
type SkillMetadata struct {
	ExecutionMode    string                 `yaml:"execution_mode" json:"execution_mode"`
	SandboxConfig    SandboxSkillConfig     `yaml:"sandbox_config" json:"sandbox_config"`
	IsolationLevel   string                 `yaml:"isolation_level" json:"isolation_level"`
	NetworkAccess    bool                   `yaml:"network_access" json:"network_access"`
	AllowedTools     []string               `yaml:"allowed_tools" json:"allowed_tools"`
	ResourceLimits   sandbox.ResourceSpec   `yaml:"resource_limits" json:"resource_limits"`
	Timeout          string                 `yaml:"timeout" json:"timeout"`
	Environment      map[string]string      `yaml:"environment" json:"environment"`
	SecurityPolicies []SecurityPolicy       `yaml:"security_policies" json:"security_policies"`
}

// SandboxSkillConfig defines sandbox-specific configuration for skills
type SandboxSkillConfig struct {
	Template         string                 `yaml:"template" json:"template"`
	WarmPool         string                 `yaml:"warm_pool" json:"warm_pool"`
	EnableSnapshots  bool                   `yaml:"enable_snapshots" json:"enable_snapshots"`
	SnapshotPolicy   string                 `yaml:"snapshot_policy" json:"snapshot_policy"`
	AutoCleanup      bool                   `yaml:"auto_cleanup" json:"auto_cleanup"`
	MaxConcurrent    int                    `yaml:"max_concurrent" json:"max_concurrent"`
	PreWarmCount     int                    `yaml:"pre_warm_count" json:"pre_warm_count"`
	CustomResources  map[string]interface{} `yaml:"custom_resources" json:"custom_resources"`
}

// SecurityPolicy defines security policies for sandbox execution
type SecurityPolicy struct {
	Name        string            `yaml:"name" json:"name"`
	Type        string            `yaml:"type" json:"type"` // network, filesystem, process
	Rule        string            `yaml:"rule" json:"rule"`
	Action      string            `yaml:"action" json:"action"` // allow, deny, log
	Parameters  map[string]string `yaml:"parameters" json:"parameters"`
}

// SkillExecutionContext represents the context for skill execution
type SkillExecutionContext struct {
	SkillName       string
	SkillType       string
	AgentType       string
	Metadata        *SkillMetadata
	RequestID       string
	UserID          string
	TenantID        string
	ExecutionID     string
	StartTime       string
}

// NewSkillIntegration creates a new skill integration
func NewSkillIntegration(integrator *AgentIntegrator, config *config.AgentSandboxConfig) *SkillIntegration {
	si := &SkillIntegration{
		integrator:  integrator,
		config:     config,
		templateMap: make(map[string]string),
		resourceMap: make(map[string]sandbox.ResourceSpec),
	}

	// Initialize default mappings
	si.initializeDefaultMappings()

	return si
}

// initializeDefaultMappings sets up default template and resource mappings
func (si *SkillIntegration) initializeDefaultMappings() {
	// Template mappings based on skill patterns
	si.templateMap["python"] = "python-runtime-template"
	si.templateMap["bash"] = "bash-runtime-template"
	si.templateMap["shell"] = "bash-runtime-template"
	si.templateMap["infrastructure"] = "bash-runtime-template"
	si.templateMap["security"] = "python-runtime-template"
	si.templateMap["monitoring"] = "python-runtime-template"
	si.templateMap["cost-optimization"] = "python-runtime-template"
	si.templateMap["database"] = "python-runtime-template"

	// Resource mappings based on skill types
	si.resourceMap["lightweight"] = sandbox.ResourceSpec{
		CPU:    "250m",
		Memory: "512Mi",
		Disk:   "1Gi",
	}
	si.resourceMap["standard"] = sandbox.ResourceSpec{
		CPU:    "500m",
		Memory: "1Gi",
		Disk:   "2Gi",
	}
	si.resourceMap["compute-intensive"] = sandbox.ResourceSpec{
		CPU:    "1000m",
		Memory: "2Gi",
		Disk:   "4Gi",
	}
	si.resourceMap["memory-intensive"] = sandbox.ResourceSpec{
		CPU:    "500m",
		Memory: "4Gi",
		Disk:   "2Gi",
	}
}

// ExecuteSkill executes a skill in Agent Sandbox with enhanced metadata support
func (si *SkillIntegration) ExecuteSkill(ctx context.Context, skillCtx *SkillExecutionContext, code string) (*ExecutionResult, error) {
	log.Printf("Executing skill %s in Agent Sandbox with metadata", skillCtx.SkillName)

	// Parse and validate skill metadata
	if err := si.validateSkillMetadata(skillCtx.Metadata); err != nil {
		return nil, fmt.Errorf("invalid skill metadata: %w", err)
	}

	// Determine template
	template := si.selectTemplate(skillCtx)

	// Determine resources
	resources := si.selectResources(skillCtx)

	// Create execution request
	request := &ExecutionRequest{
		AgentID:       fmt.Sprintf("%s-%s", skillCtx.AgentType, skillCtx.SkillName),
		AgentType:     skillCtx.AgentType,
		Code:          code,
		Language:      si.detectLanguageFromSkill(skillCtx),
		Template:      template,
		Resources:     resources,
		Environment:   si.buildEnvironment(skillCtx),
		Timeout:       si.parseTimeout(skillCtx.Metadata.Timeout),
		NetworkAccess: skillCtx.Metadata.NetworkAccess,
		Metadata: map[string]interface{}{
			"skill_name":       skillCtx.SkillName,
			"skill_type":       skillCtx.SkillType,
			"execution_mode":    skillCtx.Metadata.ExecutionMode,
			"isolation_level":   skillCtx.Metadata.IsolationLevel,
			"request_id":        skillCtx.RequestID,
			"user_id":           skillCtx.UserID,
			"tenant_id":         skillCtx.TenantID,
			"execution_id":      skillCtx.ExecutionID,
			"start_time":        skillCtx.StartTime,
		},
	}

	// Apply security policies
	if err := si.applySecurityPolicies(ctx, request, skillCtx.Metadata.SecurityPolicies); err != nil {
		return nil, fmt.Errorf("security policy violation: %w", err)
	}

	// Execute the skill
	result, err := si.integrator.executor.Execute(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("failed to execute skill: %w", err)
	}

	// Apply post-execution security checks
	if err := si.postExecutionSecurityCheck(ctx, result, skillCtx.Metadata.SecurityPolicies); err != nil {
		log.Printf("Post-execution security check failed: %v", err)
		// Don't fail the execution, just log it
	}

	return result, nil
}

// validateSkillMetadata validates skill metadata
func (si *SkillIntegration) validateSkillMetadata(metadata *SkillMetadata) error {
	if metadata == nil {
		return fmt.Errorf("skill metadata is required")
	}

	if metadata.ExecutionMode != "agent_sandbox" {
		return fmt.Errorf("execution mode must be 'agent_sandbox'")
	}

	if metadata.SandboxConfig.Template == "" {
		return fmt.Errorf("sandbox template is required")
	}

	// Validate isolation level
	validLevels := []string{"low", "medium", "high"}
	if !contains(validLevels, metadata.IsolationLevel) {
		return fmt.Errorf("invalid isolation level: %s", metadata.IsolationLevel)
	}

	return nil
}

// selectTemplate selects the appropriate template for the skill
func (si *SkillIntegration) selectTemplate(skillCtx *SkillExecutionContext) string {
	// Use explicitly specified template if available
	if skillCtx.Metadata.SandboxConfig.Template != "" {
		return skillCtx.Metadata.SandboxConfig.Template
	}

	// Use template mapping based on skill type
	for pattern, template := range si.templateMap {
		if strings.Contains(strings.ToLower(skillCtx.SkillName), pattern) ||
		   strings.Contains(strings.ToLower(skillCtx.SkillType), pattern) {
			return template
		}
	}

	// Fall back to default template
	return si.config.DefaultTemplate
}

// selectResources selects appropriate resources for the skill
func (si *SkillIntegration) selectResources(skillCtx *SkillExecutionContext) sandbox.ResourceSpec {
	// Use explicitly specified resources if available
	if skillCtx.Metadata.ResourceLimits.CPU != "" || skillCtx.Metadata.ResourceLimits.Memory != "" {
		return skillCtx.Metadata.ResourceLimits
	}

	// Select resources based on isolation level
	switch skillCtx.Metadata.IsolationLevel {
	case "high":
		return si.resourceMap["compute-intensive"]
	case "medium":
		return si.resourceMap["standard"]
	case "low":
		return si.resourceMap["lightweight"]
	default:
		return si.resourceMap["standard"]
	}
}

// buildEnvironment builds environment variables for the skill
func (si *SkillIntegration) buildEnvironment(skillCtx *SkillExecutionContext) map[string]string {
	env := make(map[string]string)

	// Add skill metadata environment variables
	env["SKILL_NAME"] = skillCtx.SkillName
	env["SKILL_TYPE"] = skillCtx.SkillType
	env["AGENT_TYPE"] = skillCtx.AgentType
	env["EXECUTION_MODE"] = skillCtx.Metadata.ExecutionMode
	env["ISOLATION_LEVEL"] = skillCtx.Metadata.IsolationLevel
	env["REQUEST_ID"] = skillCtx.RequestID
	env["EXECUTION_ID"] = skillCtx.ExecutionID

	// Add custom environment variables
	if skillCtx.Metadata.Environment != nil {
		for k, v := range skillCtx.Metadata.Environment {
			env[k] = v
		}
	}

	return env
}

// parseTimeout parses timeout from metadata
func (si *SkillIntegration) parseTimeout(timeoutStr string) time.Duration {
	if timeoutStr == "" {
		return si.config.Timeout
	}

	duration, err := time.ParseDuration(timeoutStr)
	if err != nil {
		log.Printf("Invalid timeout format '%s', using default: %v", timeoutStr, err)
		return si.config.Timeout
	}

	return duration
}

// detectLanguageFromSkill detects programming language from skill context
func (si *SkillIntegration) detectLanguageFromSkill(skillCtx *SkillExecutionContext) string {
	// Use language hints from skill metadata if available
	if skillCtx.Metadata.Environment != nil {
		if lang, exists := skillCtx.Metadata.Environment["LANGUAGE"]; exists {
			return lang
		}
	}

	// Detect based on skill type and name
	skillName := strings.ToLower(skillCtx.SkillName)
	skillType := strings.ToLower(skillCtx.SkillType)

	if strings.Contains(skillName, "python") || strings.Contains(skillType, "python") {
		return "python"
	}
	if strings.Contains(skillName, "bash") || strings.Contains(skillName, "shell") || strings.Contains(skillType, "bash") {
		return "bash"
	}
	if strings.Contains(skillName, "go") || strings.Contains(skillType, "go") {
		return "go"
	}
	if strings.Contains(skillName, "javascript") || strings.Contains(skillName, "js") || strings.Contains(skillType, "javascript") {
		return "javascript"
	}

	// Default to python
	return "python"
}

// applySecurityPolicies applies security policies before execution
func (si *SkillIntegration) applySecurityPolicies(ctx context.Context, request *ExecutionRequest, policies []SecurityPolicy) error {
	for _, policy := range policies {
		switch policy.Type {
		case "network":
			if err := si.applyNetworkPolicy(request, policy); err != nil {
				return err
			}
		case "filesystem":
			if err := si.applyFilesystemPolicy(request, policy); err != nil {
				return err
			}
		case "process":
			if err := si.applyProcessPolicy(request, policy); err != nil {
				return err
			}
		}
	}
	return nil
}

// applyNetworkPolicy applies network security policy
func (si *SkillIntegration) applyNetworkPolicy(request *ExecutionRequest, policy SecurityPolicy) error {
	if policy.Action == "deny" && policy.Rule == "all" {
		request.NetworkAccess = false
	}
	return nil
}

// applyFilesystemPolicy applies filesystem security policy
func (si *SkillIntegration) applyFilesystemPolicy(request *ExecutionRequest, policy SecurityPolicy) error {
	// Filesystem policies would be implemented at the container level
	// For now, we log the policy
	log.Printf("Applying filesystem policy: %s - %s", policy.Name, policy.Rule)
	return nil
}

// applyProcessPolicy applies process security policy
func (si *SkillIntegration) applyProcessPolicy(request *ExecutionRequest, policy SecurityPolicy) error {
	// Process policies would be implemented at the container level
	// For now, we log the policy
	log.Printf("Applying process policy: %s - %s", policy.Name, policy.Rule)
	return nil
}

// postExecutionSecurityCheck performs security checks after execution
func (si *SkillIntegration) postExecutionSecurityCheck(ctx context.Context, result *ExecutionResult, policies []SecurityPolicy) error {
	// Check for security violations in execution output
	for _, policy := range policies {
		if policy.Type == "output" && policy.Action == "scan" {
			if err := si.scanOutputForViolations(result.Stdout, policy); err != nil {
				return err
			}
		}
	}
	return nil
}

// scanOutputForViolations scans output for security violations
func (si *SkillIntegration) scanOutputForViolations(output string, policy SecurityPolicy) error {
	// Simple keyword-based scanning
	// In a real implementation, this would be more sophisticated
	violations := []string{"password", "secret", "token", "key"}
	
	for _, violation := range violations {
		if strings.Contains(strings.ToLower(output), violation) {
			return fmt.Errorf("potential security violation detected: %s", violation)
		}
	}
	
	return nil
}

// GetSkillTemplateMapping returns the skill-to-template mapping
func (si *SkillIntegration) GetSkillTemplateMapping() map[string]string {
	return si.templateMap
}

// UpdateSkillTemplateMapping updates the skill-to-template mapping
func (si *SkillIntegration) UpdateSkillTemplateMapping(skillPattern, template string) {
	si.templateMap[skillPattern] = template
	log.Printf("Updated skill template mapping: %s -> %s", skillPattern, template)
}

// GetResourceMapping returns the skill-type-to-resource mapping
func (si *SkillIntegration) GetResourceMapping() map[string]sandbox.ResourceSpec {
	return si.resourceMap
}

// UpdateResourceMapping updates the resource mapping
func (si *SkillIntegration) UpdateResourceMapping(skillType string, resources sandbox.ResourceSpec) {
	si.resourceMap[skillType] = resources
	log.Printf("Updated resource mapping: %s", skillType)
}
