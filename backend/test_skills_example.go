package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/lloydchang/ai-agents-sandbox/backend/skills"
)

func testSkillsMain() {
	// Test skills discovery
	workingDir := ".."
	if len(os.Args) > 1 {
		workingDir = os.Args[1]
	}

	// Convert to absolute path
	absWorkingDir, err := filepath.Abs(workingDir)
	if err != nil {
		log.Fatalf("Failed to get absolute path: %v", err)
	}

	fmt.Printf("Testing skills discovery with working directory: %s\n", absWorkingDir)

	// Create skill service
	skillService := skills.NewSkillService(workingDir, "test-session")
	manager := skillService.GetManager()

	// List discovered skills
	skills := manager.ListSkills()
	fmt.Printf("Discovered %d skills:\n", len(skills))

	for _, skill := range skills {
		fmt.Printf("  - %s: %s (scope: %s, priority: %d)\n",
			skill.Name, skill.Description, skill.Scope, skill.Priority)
	}

	// Test skill execution
	if len(skills) > 0 {
		skill := skills[0]
		fmt.Printf("\nTesting execution of skill: %s\n", skill.Name)

		execution, err := manager.ExecuteSkill(skill.Name, []string{"test-arg"})
		if err != nil {
			fmt.Printf("Execution failed: %v\n", err)
		} else {
			fmt.Printf("Execution successful!\n")
			fmt.Printf("  Fork required: %v\n", execution.ShouldFork())
			fmt.Printf("  Agent type: %s\n", execution.GetAgentType())
			fmt.Printf("  Content length: %d\n", len(execution.GetProcessedContent()))
		}
	}

	fmt.Println("\nSkills discovery test completed.")
}
