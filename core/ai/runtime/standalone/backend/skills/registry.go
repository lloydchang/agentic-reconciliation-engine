package skills

import (
	"context"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

// SkillRegistry manages loading and accessing AI agent skills
type SkillRegistry struct {
	skills       map[string]*Skill
	keywordMap   map[string][]string // keywords -> skill names
	triggerMap   map[string]string    // AGENTS.md trigger keywords -> skill names
	initialized  bool
	agentsConfig  *AgentsConfig
}

// Skill represents a loaded AI agent skill
type Skill struct {
	Name        string            `yaml:"name"`
	Description string            `yaml:"description"`
	Tools       []string          `yaml:"tools"`
	Arguments   string            `yaml:"argument-hint,omitempty"`
	UserInvocable bool            `yaml:"user-invocable,omitempty"`
	DisableModel bool            `yaml:"disable-model-invocation,omitempty"`
	AllowedTools []string         `yaml:"allowed-tools,omitempty"`
	Context     string           `yaml:"context,omitempty"`
	Agent       string           `yaml:"agent,omitempty"`
	Content     string            `yaml:"-"` // Full skill content
	FilePath    string            `yaml:"-"` // Path to SKILL.md
	LastModified time.Time         `yaml:"-"`
	
	// Additional fields from the actual skill format
	Version     string            `yaml:"version,omitempty"`
	RiskLevel   string            `yaml:"risk_level,omitempty"`
	Autonomy    string            `yaml:"autonomy,omitempty"`
	ActionName  string            `yaml:"action_name,omitempty"`
}

// AgentsConfig represents the AGENTS.md configuration
type AgentsConfig struct {
	SkillIndex []SkillIndexEntry `yaml:"skill_index"`
	Workflows  []WorkflowEntry   `yaml:"workflows"`
	Schedules  []ScheduleEntry   `yaml:"schedules"`
}

// SkillIndexEntry represents the skill index from AGENTS.md
type SkillIndexEntry struct {
	TriggerKeywords   []string `yaml:"trigger_keywords"`
	SkillToLoad      string   `yaml:"skill_to_load"`
	HumanGateRequired bool     `yaml:"human_gate_required"`
}

// WorkflowEntry represents composite workflows
type WorkflowEntry struct {
	ID          string   `yaml:"id"`
	Name        string   `yaml:"name"`
	Trigger     string   `yaml:"trigger"`
	Steps       []string `yaml:"steps"`
	Description string   `yaml:"description"`
}

// ScheduleEntry represents automated schedules
type ScheduleEntry struct {
	Task      string `yaml:"task"`
	Schedule  string `yaml:"schedule"`
	Skill     string `yaml:"skill"`
}

// NewSkillRegistry creates a new skill registry
func NewSkillRegistry() *SkillRegistry {
	return &SkillRegistry{
		skills:     make(map[string]*Skill),
		keywordMap:  make(map[string][]string),
		triggerMap:  make(map[string]string),
		initialized: false,
	}
}

// LoadSkills loads all skills from the .agents/skills directory
func (sr *SkillRegistry) LoadSkills(ctx context.Context, skillsDir string) error {
	sr.skills = make(map[string]*Skill)
	sr.keywordMap = make(map[string][]string)

	// Walk the skills directory
	err := filepath.WalkDir(skillsDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Only process SKILL.md files
		if d.IsDir() || filepath.Base(path) != "SKILL.md" {
			return nil
		}

		// Extract skill name from directory
		skillDir := filepath.Dir(path)
		skillName := filepath.Base(skillDir)

		// Load the skill
		skill, err := sr.loadSkill(path)
		if err != nil {
			fmt.Printf("Warning: Failed to load skill %s: %v\n", skillName, err)
			return nil // Continue loading other skills
		}

		sr.skills[skillName] = skill
		sr.buildKeywordMap(skillName, skill)

		return nil
	})

	if err != nil {
		return fmt.Errorf("failed to walk skills directory: %w", err)
	}

	// Load AGENTS.md configuration
	err = sr.loadAgentsConfig(ctx)
	if err != nil {
		return fmt.Errorf("failed to load AGENTS.md: %w", err)
	}

	sr.initialized = true
	return nil
}

// loadSkill loads a single skill from its SKILL.md file
func (sr *SkillRegistry) loadSkill(filePath string) (*Skill, error) {
	content, err := os.ReadFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read skill file: %w", err)
	}

	// Get file info for modification time
	info, err := os.Stat(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to get skill file info: %w", err)
	}

	// Parse YAML frontmatter
	contentStr := string(content)
	var skill Skill
	
	// Find frontmatter boundaries
	startIdx := strings.Index(contentStr, "---")
	if startIdx == -1 {
		return nil, fmt.Errorf("no YAML frontmatter found in %s", filePath)
	}
	
	endIdx := strings.Index(contentStr[startIdx+3:], "---")
	if endIdx == -1 {
		return nil, fmt.Errorf("unterminated YAML frontmatter in %s", filePath)
	}
	
	frontmatter := contentStr[startIdx+3 : startIdx+3+endIdx]
	
	err = yaml.Unmarshal([]byte(frontmatter), &skill)
	if err != nil {
		return nil, fmt.Errorf("failed to parse YAML frontmatter: %w", err)
	}

	// Store additional metadata
	skill.Content = contentStr
	skill.FilePath = filePath
	skill.LastModified = info.ModTime()

	return &skill, nil
}

// loadAgentsConfig loads the AGENTS.md configuration
func (sr *SkillRegistry) loadAgentsConfig(ctx context.Context) error {
	agentsPath := filepath.Join(".", "AGENTS.md")
	if _, err := os.Stat(agentsPath); os.IsNotExist(err) {
		return fmt.Errorf("AGENTS.md not found at %s", agentsPath)
	}

	content, err := os.ReadFile(agentsPath)
	if err != nil {
		return fmt.Errorf("failed to read AGENTS.md: %w", err)
	}

	// For now, we'll parse the skill index table manually
	// In a full implementation, this would be more sophisticated
	sr.parseSkillIndexTable(string(content))
	
	return nil
}

// parseSkillIndexTable parses the skill index table from AGENTS.md
func (sr *SkillRegistry) parseSkillIndexTable(content string) {
	lines := strings.Split(content, "\n")
	inTable := false
	
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		
		// Look for table start
		if strings.Contains(trimmed, "Trigger keywords") && strings.Contains(trimmed, "Skill to load") {
			inTable = true
			continue
		}
		
		// Look for table end
		if inTable && (strings.HasPrefix(trimmed, "---") || strings.HasPrefix(trimmed, "For any request")) {
			break
		}
		
		// Parse table rows
		if inTable && strings.Contains(trimmed, "|") {
			parts := strings.Split(trimmed, "|")
			if len(parts) >= 3 {
				keywords := strings.TrimSpace(parts[1])
				skillName := strings.TrimSpace(parts[2])
				
				if keywords != "" && skillName != "" && !strings.Contains(keywords, "Trigger keywords") {
					// Clean up skill name
					skillName = strings.ReplaceAll(skillName, "`", "")
					
					// Parse keywords (comma-separated)
					keywordList := strings.Split(keywords, ",")
					for i, kw := range keywordList {
						keywordList[i] = strings.TrimSpace(kw)
					}
					
					// Map each keyword to the skill
					for _, kw := range keywordList {
						if kw != "" {
							sr.triggerMap[strings.ToLower(kw)] = skillName
						}
					}
				}
			}
		}
	}
}

// buildKeywordMap builds the keyword map for a skill
func (sr *SkillRegistry) buildKeywordMap(skillName string, skill *Skill) {
	// Extract keywords from description
	description := strings.ToLower(skill.Description)
	words := strings.Fields(description)
	
	for _, word := range words {
		if len(word) > 3 { // Only use words longer than 3 characters
			sr.keywordMap[word] = append(sr.keywordMap[word], skillName)
		}
	}
}

// GetSkill returns a skill by name
func (sr *SkillRegistry) GetSkill(name string) (*Skill, error) {
	if !sr.initialized {
		return nil, fmt.Errorf("skill registry not initialized")
	}
	
	skill, exists := sr.skills[name]
	if !exists {
		return nil, fmt.Errorf("skill '%s' not found", name)
	}
	
	return skill, nil
}

// FindSkillsByKeywords finds skills that match the given keywords
func (sr *SkillRegistry) FindSkillsByKeywords(keywords []string) []*Skill {
	if !sr.initialized {
		return []*Skill{}
	}
	
	var matchedSkills []*Skill
	skillScores := make(map[string]int)
	
	// Check AGENTS.md trigger keywords first
	for _, keyword := range keywords {
		keyword = strings.ToLower(keyword)
		if skillName, exists := sr.triggerMap[keyword]; exists {
			skillScores[skillName] += 100 // High priority for AGENTS.md keywords
		}
	}
	
	// Then check skill descriptions
	for _, keyword := range keywords {
		keyword = strings.ToLower(keyword)
		if skillNames, exists := sr.keywordMap[keyword]; exists {
			for _, skillName := range skillNames {
				skillScores[skillName] += 10 // Lower priority for description keywords
			}
		}
	}
	
	// Get unique skills sorted by score
	for skillName, score := range skillScores {
		if skill, exists := sr.skills[skillName]; exists && score > 0 {
			matchedSkills = append(matchedSkills, skill)
		}
	}
	
	return matchedSkills
}

// ListSkills returns all loaded skills
func (sr *SkillRegistry) ListSkills() map[string]*Skill {
	if !sr.initialized {
		return make(map[string]*Skill)
	}
	
	// Return a copy to prevent modification
	result := make(map[string]*Skill)
	for name, skill := range sr.skills {
		result[name] = skill
	}
	
	return result
}

// IsInitialized returns whether the registry is initialized
func (sr *SkillRegistry) IsInitialized() bool {
	return sr.initialized
}

// ReloadSkills reloads all skills from disk
func (sr *SkillRegistry) ReloadSkills(ctx context.Context, skillsDir string) error {
	sr.initialized = false
	return sr.LoadSkills(ctx, skillsDir)
}
