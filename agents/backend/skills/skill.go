package skills

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v2"
)

// Skill represents a parsed skill with its metadata and content
type Skill struct {
	Name                     string            `yaml:"name" json:"name"`
	Description              string            `yaml:"description" json:"description"`
	ArgumentHint             string            `yaml:"argument-hint,omitempty" json:"argumentHint,omitempty"`
	DisableModelInvocation   bool              `yaml:"disable-model-invocation,omitempty" json:"disableModelInvocation,omitempty"`
	UserInvocable            bool              `yaml:"user-invocable,omitempty" json:"userInvocable,omitempty"`
	AllowedTools             []string          `yaml:"allowed-tools,omitempty" json:"allowedTools,omitempty"`
	Model                    string            `yaml:"model,omitempty" json:"model,omitempty"`
	Context                  string            `yaml:"context,omitempty" json:"context,omitempty"`
	Agent                    string            `yaml:"agent,omitempty" json:"agent,omitempty"`
	Hooks                    map[string]interface{} `yaml:"hooks,omitempty" json:"hooks,omitempty"`

	// Parsed content
	Content         string `json:"content"`
	Path            string `json:"path"`
	Directory       string `json:"directory"`
	SupportingFiles map[string]string `json:"supportingFiles"`

	// Metadata
	Scope           string `json:"scope"`    // "repo", "user", "admin", "system"
	Priority        int    `json:"priority"` // For conflict resolution
}

// SkillMetadata represents the optional agents/openai.yaml metadata
type SkillMetadata struct {
	Interface struct {
		DisplayName      string `yaml:"display_name,omitempty" json:"displayName,omitempty"`
		ShortDescription string `yaml:"short_description,omitempty" json:"shortDescription,omitempty"`
		IconSmall        string `yaml:"icon_small,omitempty" json:"iconSmall,omitempty"`
		IconLarge        string `yaml:"icon_large,omitempty" json:"iconLarge,omitempty"`
		BrandColor       string `yaml:"brand_color,omitempty" json:"brandColor,omitempty"`
		DefaultPrompt    string `yaml:"default_prompt,omitempty" json:"defaultPrompt,omitempty"`
	} `yaml:"interface,omitempty" json:"interface,omitempty"`

	Policy struct {
		AllowImplicitInvocation bool `yaml:"allow_implicit_invocation" json:"allowImplicitInvocation"`
	} `yaml:"policy,omitempty" json:"policy,omitempty"`

	Dependencies struct {
		Tools []struct {
			Type        string `yaml:"type" json:"type"`
			Value       string `yaml:"value" json:"value"`
			Description string `yaml:"description,omitempty" json:"description,omitempty"`
			Transport   string `yaml:"transport,omitempty" json:"transport,omitempty"`
			URL         string `yaml:"url,omitempty" json:"url,omitempty"`
		} `yaml:"tools,omitempty" json:"tools,omitempty"`
	} `yaml:"dependencies,omitempty" json:"dependencies,omitempty"`
}

// SkillManager manages skill discovery and execution
type SkillManager struct {
	Skills       map[string]*Skill
	SkillDirs    []string
	SessionID    string
	WorkingDir   string
}

// NewSkillManager creates a new skill manager
func NewSkillManager(workingDir, sessionID string) *SkillManager {
	return &SkillManager{
		Skills:     make(map[string]*Skill),
		SkillDirs:  []string{},
		SessionID:  sessionID,
		WorkingDir: workingDir,
	}
}

// AddSkillDir adds a directory to scan for skills
func (sm *SkillManager) AddSkillDir(dir string, scope string, priority int) error {
	absDir, err := filepath.Abs(dir)
	if err != nil {
		return err
	}

	sm.SkillDirs = append(sm.SkillDirs, absDir)

	// Scan for skills in this directory
	return sm.scanDirectory(absDir, scope, priority)
}

// scanDirectory scans a directory for skills
func (sm *SkillManager) scanDirectory(dir, scope string, priority int) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		skillPath := filepath.Join(dir, entry.Name(), "SKILL.md")
		if _, err := os.Stat(skillPath); os.IsNotExist(err) {
			continue
		}

		skill, err := sm.parseSkill(skillPath, scope, priority)
		if err != nil {
			continue // Skip invalid skills
		}

		// Handle naming conflicts with priority
		if existing, exists := sm.Skills[skill.Name]; exists {
			if skill.Priority > existing.Priority {
				sm.Skills[skill.Name] = skill
			}
		} else {
			sm.Skills[skill.Name] = skill
		}
	}

	return nil
}

// parseSkill parses a SKILL.md file
func (sm *SkillManager) parseSkill(skillPath, scope string, priority int) (*Skill, error) {
	content, err := ioutil.ReadFile(skillPath)
	if err != nil {
		return nil, err
	}

	skill := &Skill{
		Path:            skillPath,
		Directory:       filepath.Dir(skillPath),
		Scope:           scope,
		Priority:        priority,
		SupportingFiles: make(map[string]string),
		UserInvocable:   true, // Default to true
	}

	// Parse frontmatter and content
	frontmatter, markdownContent, err := sm.parseFrontmatter(string(content))
	if err != nil {
		return nil, err
	}

	// Parse YAML frontmatter
	if err := yaml.Unmarshal([]byte(frontmatter), skill); err != nil {
		return nil, err
	}

	// Set defaults
	if skill.Name == "" {
		skill.Name = strings.ToLower(filepath.Base(filepath.Dir(skillPath)))
	}

	if skill.Description == "" {
		// Use first paragraph of markdown as description
		lines := strings.Split(markdownContent, "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			if line != "" && !strings.HasPrefix(line, "#") {
				skill.Description = line
				break
			}
		}
	}

	skill.Content = markdownContent

	// Load supporting files
	sm.loadSupportingFiles(skill)

	return skill, nil
}

// parseFrontmatter extracts YAML frontmatter and markdown content
func (sm *SkillManager) parseFrontmatter(content string) (string, string, error) {
	scanner := bufio.NewScanner(strings.NewReader(content))

	// Check for frontmatter start
	if !scanner.Scan() || strings.TrimSpace(scanner.Text()) != "---" {
		// No frontmatter, return empty frontmatter and full content
		return "", content, nil
	}

	var frontmatter strings.Builder
	for scanner.Scan() {
		line := scanner.Text()
		if strings.TrimSpace(line) == "---" {
			break
		}
		frontmatter.WriteString(line + "\n")
	}

	// Read remaining content
	var remaining strings.Builder
	for scanner.Scan() {
		remaining.WriteString(scanner.Text() + "\n")
	}

	return frontmatter.String(), remaining.String(), nil
}

// loadSupportingFiles loads supporting files for a skill
func (sm *SkillManager) loadSupportingFiles(skill *Skill) {
	supportingFiles := []string{
		"template.md",
		"examples.md",
		"reference.md",
	}

	for _, filename := range supportingFiles {
		path := filepath.Join(skill.Directory, filename)
		if content, err := ioutil.ReadFile(path); err == nil {
			skill.SupportingFiles[filename] = string(content)
		}
	}
}

// GetSkill returns a skill by name
func (sm *SkillManager) GetSkill(name string) (*Skill, bool) {
	skill, exists := sm.Skills[name]
	return skill, exists
}

// ListSkills returns all available skills
func (sm *SkillManager) ListSkills() []*Skill {
	var skills []*Skill
	for _, skill := range sm.Skills {
		skills = append(skills, skill)
	}
	return skills
}

// ListUserInvocableSkills returns skills that can be invoked by users
func (sm *SkillManager) ListUserInvocableSkills() []*Skill {
	var skills []*Skill
	for _, skill := range sm.Skills {
		if skill.UserInvocable && !skill.DisableModelInvocation {
			skills = append(skills, skill)
		}
	}
	return skills
}

// ExecuteSkill prepares a skill for execution with arguments
func (sm *SkillManager) ExecuteSkill(name string, args []string) (*SkillExecution, error) {
	skill, exists := sm.Skills[name]
	if !exists {
		return nil, fmt.Errorf("skill '%s' not found", name)
	}

	execution := &SkillExecution{
		Skill:      skill,
		Arguments:  args,
		SessionID:  sm.SessionID,
		WorkingDir: sm.WorkingDir,
	}

	// Process dynamic context injection
	content, err := sm.processDynamicContext(skill.Content, execution)
	if err != nil {
		return nil, err
	}

	// Apply string substitutions
	content = sm.applySubstitutions(content, execution)

	execution.ProcessedContent = content

	return execution, nil
}

// processDynamicContext processes !`command` syntax for dynamic context injection
func (sm *SkillManager) processDynamicContext(content string, execution *SkillExecution) (string, error) {
	// TODO: Implement dynamic context injection with !`command` syntax
	// For now, return content as-is - this is a safety-first implementation
	// Dynamic command execution would need security review
	return content, nil
}

// applySubstitutions applies string substitutions to skill content
func (sm *SkillManager) applySubstitutions(content string, execution *SkillExecution) string {
	// Apply argument substitutions
	argsStr := strings.Join(execution.Arguments, " ")

	content = strings.ReplaceAll(content, "$ARGUMENTS", argsStr)

	// Apply positional arguments
	for i, arg := range execution.Arguments {
		placeholder := fmt.Sprintf("$%d", i)
		content = strings.ReplaceAll(content, placeholder, arg)

		// Also support $ARGUMENTS[N] syntax
		argIndex := fmt.Sprintf("$ARGUMENTS[%d]", i)
		content = strings.ReplaceAll(content, argIndex, arg)
	}

	// Apply session and directory substitutions
	content = strings.ReplaceAll(content, "${CLAUDE_SESSION_ID}", execution.SessionID)
	content = strings.ReplaceAll(content, "${CLAUDE_SKILL_DIR}", execution.Skill.Directory)

	return content
}

// SkillExecution represents a skill execution instance
type SkillExecution struct {
	Skill           *Skill
	Arguments       []string
	SessionID       string
	WorkingDir      string
	ProcessedContent string
}

// GetProcessedContent returns the processed skill content ready for execution
func (se *SkillExecution) GetProcessedContent() string {
	return se.ProcessedContent
}

// ShouldFork returns whether this skill should run in a forked context
func (se *SkillExecution) ShouldFork() bool {
	return se.Skill.Context == "fork"
}

// GetAgentType returns the agent type for forked execution
func (se *SkillExecution) GetAgentType() string {
	if se.Skill.Agent != "" {
		return se.Skill.Agent
	}
	return "general-purpose"
}
