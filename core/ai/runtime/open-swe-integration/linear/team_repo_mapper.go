package linear

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sync"

	"gitops-infra-control-plane/core/ai/runtime/open-swe-integration/shared"
)

// TeamRepoMapper manages the mapping between Linear teams and GitHub repositories
type TeamRepoMapper struct {
	mappings map[string]shared.RepoMapping
	mutex    sync.RWMutex
	configFile string
}

// NewTeamRepoMapper creates a new team repository mapper
func NewTeamRepoMapper(configFile string) *TeamRepoMapper {
	mapper := &TeamRepoMapper{
		mappings:   make(map[string]shared.RepoMapping),
		configFile: configFile,
	}
	
	// Load existing mappings
	if err := mapper.loadMappings(); err != nil {
		// Log error but don't fail - start with empty mappings
		fmt.Printf("Warning: Failed to load team mappings: %v\n", err)
	}
	
	return mapper
}

// GetMapping returns the repository mapping for a given team ID
func (m *TeamRepoMapper) GetMapping(teamID string) (shared.RepoMapping, bool) {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	mapping, exists := m.mappings[teamID]
	return mapping, exists
}

// SetMapping sets the repository mapping for a given team ID
func (m *TeamRepoMapper) SetMapping(teamID string, mapping shared.RepoMapping) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	m.mappings[teamID] = mapping
	return m.saveMappings()
}

// RemoveMapping removes the repository mapping for a given team ID
func (m *TeamRepoMapper) RemoveMapping(teamID string) error {
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	delete(m.mappings, teamID)
	return m.saveMappings()
}

// GetAllMappings returns all team mappings
func (m *TeamRepoMapper) GetAllMappings() map[string]shared.RepoMapping {
	m.mutex.RLock()
	defer m.mutex.RUnlock()
	
	// Return a copy to prevent external modification
	result := make(map[string]shared.RepoMapping)
	for k, v := range m.mappings {
		result[k] = v
	}
	return result
}

// loadMappings loads team mappings from the configuration file
func (m *TeamRepoMapper) loadMappings() error {
	file, err := os.Open(m.configFile)
	if err != nil {
		if os.IsNotExist(err) {
			// File doesn't exist, start with empty mappings
			return nil
		}
		return fmt.Errorf("failed to open config file: %w", err)
	}
	defer file.Close()

	var config struct {
		Teams map[string]shared.RepoMapping `json:"teams"`
	}

	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&config); err != nil {
		return fmt.Errorf("failed to decode config file: %w", err)
	}

	m.mappings = config.Teams
	return nil
}

// saveMappings saves team mappings to the configuration file
func (m *TeamRepoMapper) saveMappings() error {
	config := struct {
		Teams map[string]shared.RepoMapping `json:"teams"`
	}{
		Teams: m.mappings,
	}

	file, err := os.Create(m.configFile)
	if err != nil {
		return fmt.Errorf("failed to create config file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(config); err != nil {
		return fmt.Errorf("failed to encode config: %w", err)
	}

	return nil
}

// ValidateMapping validates a repository mapping
func ValidateMapping(mapping shared.RepoMapping) error {
	if mapping.Owner == "" {
		return fmt.Errorf("repository owner is required")
	}
	if mapping.Name == "" {
		return fmt.Errorf("repository name is required")
	}
	if mapping.Token == "" {
		return fmt.Errorf("GitHub token is required")
	}
	return nil
}

// DefaultMappings provides sensible default mappings for common team structures
func DefaultMappings() map[string]shared.RepoMapping {
	return map[string]shared.RepoMapping{
		"engineering": {
			Owner:    "my-org",
			Name:     "backend",
			Token:    "${GITHUB_TOKEN}", // Use environment variable
			BasePath: ".",
		},
		"product": {
			Owner:    "my-org", 
			Name:     "frontend",
			Token:    "${GITHUB_TOKEN}",
			BasePath: ".",
		},
		"platform": {
			Owner:    "my-org",
			Name:     "infrastructure",
			Token:    "${GITHUB_TOKEN}",
			BasePath: ".",
		},
	}
}
