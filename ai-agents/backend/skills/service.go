package skills

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/gorilla/mux"
)

// SkillService provides HTTP endpoints for skill management
type SkillService struct {
	manager *SkillManager
}

// NewSkillService creates a new skill service
func NewSkillService(workingDir, sessionID string) *SkillService {
	manager := NewSkillManager(workingDir, sessionID)

	// Initialize skill discovery
	manager.initializeSkillDiscovery(workingDir)

	return &SkillService{
		manager: manager,
	}
}

// initializeSkillDiscovery sets up skill directory scanning
func (sm *SkillManager) initializeSkillDiscovery(workingDir string) {
	// Priority order: enterprise (highest) > personal > project > system (lowest)

	// 1. Enterprise skills (if applicable)
	// This would typically come from managed settings

	// 2. Personal skills (~/.agents/skills and ~/.claude/skills)
	if homeDir, err := os.UserHomeDir(); err == nil {
		personalSkillsDir := filepath.Join(homeDir, ".agents", "skills")
		sm.AddSkillDir(personalSkillsDir, "user", 20)
		
		claudeSkillsDir := filepath.Join(homeDir, ".claude", "skills")
		sm.AddSkillDir(claudeSkillsDir, "claude-user", 20)
	}

	// 3. Project skills (.agents/skills and .claude/skills from current directory up to repo root)
	sm.discoverProjectSkills(workingDir)

	// 4. System skills (bundled with the application)
	// These would be in the application directory
}

// discoverProjectSkills discovers skills from .agents/skills and .claude/skills directories
func (sm *SkillManager) discoverProjectSkills(startDir string) {
	currentDir := startDir
	repoRootFound := false

	for {
		// Check for .agents/skills in current directory
		skillDir := filepath.Join(currentDir, ".agents", "skills")
		if _, err := os.Stat(skillDir); err == nil {
			priority := 10 // Default project priority
			if repoRootFound {
				priority = 15 // Higher priority for repo root
			}
			sm.AddSkillDir(skillDir, "repo", priority)
		}

		// Also check for .agents/skills (common pattern)
		agentsSkillDir := filepath.Join(currentDir, ".agents", "skills")
		if _, err := os.Stat(agentsSkillDir); err == nil {
			sm.AddSkillDir(agentsSkillDir, "agents-repo", 15)
		}

		// Also check for discovered_skills (manual sync)
		discoveredSkillDir := filepath.Join(currentDir, "discovered_skills")
		if _, err := os.Stat(discoveredSkillDir); err == nil {
			sm.AddSkillDir(discoveredSkillDir, "discovered", 25)
		}

		// Check for .claude/skills in current directory (additional support)
		claudeSkillDir := filepath.Join(currentDir, ".claude", "skills")
		if _, err := os.Stat(claudeSkillDir); err == nil {
			priority := 10 // Default project priority
			if repoRootFound {
				priority = 15 // Higher priority for repo root
			}
			sm.AddSkillDir(claudeSkillDir, "claude", priority)
		}

		// Check if this is a git repository root
		if !repoRootFound {
			if _, err := os.Stat(filepath.Join(currentDir, ".git")); err == nil {
				repoRootFound = true
			}
		}

		// Move up one directory
		parentDir := filepath.Dir(currentDir)
		if parentDir == currentDir {
			// Reached filesystem root
			break
		}
		currentDir = parentDir

		// Prevent infinite loops and limit search depth
		if strings.Count(startDir, string(os.PathSeparator))-strings.Count(currentDir, string(os.PathSeparator)) > 10 {
			break
		}
	}
}

// RegisterRoutes registers skill management routes
func (ss *SkillService) RegisterRoutes(router *mux.Router) {
	// List all skills
	router.HandleFunc("/api/skills", ss.ListSkillsHandler).Methods("GET", "OPTIONS")

	// Get specific skill
	router.HandleFunc("/api/skills/{name}", ss.GetSkillHandler).Methods("GET", "OPTIONS")

	// Execute skill
	router.HandleFunc("/api/skills/{name}/execute", ss.ExecuteSkillHandler).Methods("POST", "OPTIONS")

	// List user-invocable skills (for UI dropdowns)
	router.HandleFunc("/api/skills/invocable", ss.ListInvocableSkillsHandler).Methods("GET", "OPTIONS")

	// Skill discovery endpoint
	router.HandleFunc("/api/skills/discover", ss.DiscoverSkillsHandler).Methods("POST", "OPTIONS")
}

// ListSkillsHandler returns all available skills
func (ss *SkillService) ListSkillsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	skills := ss.manager.ListSkills()

	response := map[string]interface{}{
		"skills": skills,
		"count":  len(skills),
	}

	json.NewEncoder(w).Encode(response)
}

// GetSkillHandler returns a specific skill by name
func (ss *SkillService) GetSkillHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	vars := mux.Vars(r)
	name := vars["name"]

	skill, exists := ss.manager.GetSkill(name)
	if !exists {
		http.Error(w, fmt.Sprintf("Skill '%s' not found", name), http.StatusNotFound)
		return
	}

	json.NewEncoder(w).Encode(skill)
}

// ExecuteSkillHandler executes a skill with provided arguments
func (ss *SkillService) ExecuteSkillHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	vars := mux.Vars(r)
	name := vars["name"]

	var req struct {
		Arguments []string `json:"arguments"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	execution, err := ss.manager.ExecuteSkill(name, req.Arguments)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	response := map[string]interface{}{
		"skillName":     execution.Skill.Name,
		"executionId":   fmt.Sprintf("%s-%s", execution.Skill.Name, execution.SessionID),
		"forkRequired":  execution.ShouldFork(),
		"agentType":     execution.GetAgentType(),
		"content":       execution.GetProcessedContent(),
		"arguments":     execution.Arguments,
	}

	json.NewEncoder(w).Encode(response)
}

// ListInvocableSkillsHandler returns skills that can be invoked by users
func (ss *SkillService) ListInvocableSkillsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	skills := ss.manager.ListUserInvocableSkills()

	response := map[string]interface{}{
		"skills": skills,
		"count":  len(skills),
	}

	json.NewEncoder(w).Encode(response)
}

// DiscoverSkillsHandler triggers skill discovery
func (ss *SkillService) DiscoverSkillsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Re-initialize skill discovery
	ss.manager.Skills = make(map[string]*Skill)
	ss.manager.initializeSkillDiscovery(ss.manager.WorkingDir)

	skills := ss.manager.ListSkills()

	response := map[string]interface{}{
		"message": "Skills discovered successfully",
		"skills":  skills,
		"count":   len(skills),
	}

	json.NewEncoder(w).Encode(response)
}

// GetManager returns the underlying skill manager
func (ss *SkillService) GetManager() *SkillManager {
	return ss.manager
}
