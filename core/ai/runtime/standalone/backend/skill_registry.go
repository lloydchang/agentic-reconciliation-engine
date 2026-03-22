package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v2"
)

// SkillMetadata represents the frontmatter of a SKILL.md file
type SkillMetadata struct {
	Name        string   `yaml:"name"`
	Description string   `yaml:"description"`
	Tools       []string `yaml:"tools,omitempty"`
}

// Skill represents a loaded skill with metadata and content
type Skill struct {
	Metadata SkillMetadata
	Content  string
	Path     string
}

// SkillRegistry manages the loading and querying of skills
type SkillRegistry struct {
	skills     map[string]*Skill
	skillDir   string
	keywords   map[string][]string // keyword -> []skill_names
}

// NewSkillRegistry creates a new skill registry
func NewSkillRegistry(skillDir string) *SkillRegistry {
	return &SkillRegistry{
		skills:   make(map[string]*Skill),
		skillDir: skillDir,
		keywords: make(map[string][]string),
	}
}

// LoadSkills discovers and loads all SKILL.md files in the skill directory
func (sr *SkillRegistry) LoadSkills() error {
	return filepath.Walk(sr.skillDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		if strings.ToLower(filepath.Base(path)) == "skill.md" {
			skill, err := sr.loadSkill(path)
			if err != nil {
				fmt.Printf("Warning: Failed to load skill from %s: %v\n", path, err)
				return nil // Continue loading other skills
			}

			sr.skills[skill.Metadata.Name] = skill
			fmt.Printf("Loaded skill: %s from %s\n", skill.Metadata.Name, path)
		}

		return nil
	})
}

// loadSkill parses a single SKILL.md file
func (sr *SkillRegistry) loadSkill(path string) (*Skill, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	// Split frontmatter from content
	parts := strings.SplitN(string(content), "---", 3)
	if len(parts) < 3 {
		return nil, fmt.Errorf("invalid skill format: missing frontmatter")
	}

	frontmatter := parts[1]
	body := parts[2]

	var metadata SkillMetadata
	if err := yaml.Unmarshal([]byte(frontmatter), &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse frontmatter: %w", err)
	}

	skill := &Skill{
		Metadata: metadata,
		Content:  body,
		Path:     path,
	}

	return skill, nil
}

// FindSkillsByKeywords searches for skills that match the given keywords
func (sr *SkillRegistry) FindSkillsByKeywords(keywords []string) []*Skill {
	var matches []*Skill

	for _, keyword := range keywords {
		keyword = strings.ToLower(strings.TrimSpace(keyword))

		// Check if keyword is in skill descriptions
		for _, skill := range sr.skills {
			desc := strings.ToLower(skill.Metadata.Description)
			if strings.Contains(desc, keyword) {
				matches = append(matches, skill)
			}
		}
	}

	// Remove duplicates
	seen := make(map[string]bool)
	var unique []*Skill
	for _, skill := range matches {
		if !seen[skill.Metadata.Name] {
			seen[skill.Metadata.Name] = true
			unique = append(unique, skill)
		}
	}

	return unique
}

// GetSkill returns a skill by name
func (sr *SkillRegistry) GetSkill(name string) (*Skill, error) {
	skill, exists := sr.skills[name]
	if !exists {
		return nil, fmt.Errorf("skill not found: %s", name)
	}
	return skill, nil
}

// ListSkills returns all loaded skills
func (sr *SkillRegistry) ListSkills() []*Skill {
	var skills []*Skill
	for _, skill := range sr.skills {
		skills = append(skills, skill)
	}
	return skills
}

// LoadAGENTSKeywords parses AGENTS.md to extract skill trigger keywords
func (sr *SkillRegistry) LoadAGENTSKeywords(agentsPath string) error {
	content, err := os.ReadFile(agentsPath)
	if err != nil {
		return fmt.Errorf("failed to read AGENTS.md: %w", err)
	}

	// Parse the skill trigger keywords table
	lines := strings.Split(string(content), "\n")
	inTable := false

	for _, line := range lines {
		line = strings.TrimSpace(line)

		if strings.Contains(line, "| Trigger keywords | Skill to load |") {
			inTable = true
			continue
		}

		if inTable && strings.HasPrefix(line, "| ") && strings.Contains(line, " | ") {
			parts := strings.Split(line, "|")
			if len(parts) >= 4 {
				keywordsStr := strings.TrimSpace(parts[1])
				skillName := strings.TrimSpace(parts[2])

				if keywordsStr != "Trigger keywords" && keywordsStr != "---" {
					keywords := parseKeywords(keywordsStr)
					for _, keyword := range keywords {
						sr.keywords[keyword] = append(sr.keywords[keyword], skillName)
					}
				}
			}
		}

		if inTable && strings.HasPrefix(line, "|---") {
			// Table separator, continue
		}
	}

	fmt.Printf("Loaded %d keyword mappings from AGENTS.md\n", len(sr.keywords))
	return nil
}

// parseKeywords extracts individual keywords from a comma-separated string
func parseKeywords(keywordsStr string) []string {
	keywords := strings.Split(keywordsStr, ",")
	var result []string

	for _, keyword := range keywords {
		keyword = strings.TrimSpace(keyword)
		keyword = strings.ToLower(keyword)

		// Remove common prefixes/suffixes
		keyword = strings.TrimPrefix(keyword, "any request to ")
		keyword = strings.TrimPrefix(keyword, "request to ")

		if keyword != "" {
			result = append(result, keyword)
		}
	}

	return result
}

// MatchRequestToSkills uses keywords to find relevant skills for a user request
func (sr *SkillRegistry) MatchRequestToSkills(request string) []*Skill {
	request = strings.ToLower(request)
	var matchedSkills []*Skill
	seen := make(map[string]bool)

	for keyword, skillNames := range sr.keywords {
		if strings.Contains(request, keyword) {
			for _, skillName := range skillNames {
				if !seen[skillName] {
					if skill, exists := sr.skills[skillName]; exists {
						matchedSkills = append(matchedSkills, skill)
						seen[skillName] = true
					}
				}
			}
		}
	}

	return matchedSkills
}
