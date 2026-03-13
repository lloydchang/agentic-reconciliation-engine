package activities

import (
	"context"
	"fmt"
	"os/exec"
	"regexp"
	"strings"

	"go.temporal.io/sdk/activity"
	"github.com/lloydchang/ai-agents-sandbox/backend/skills"
	"github.com/lloydchang/ai-agents-sandbox/backend/emulators"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
)

// SkillExecutionActivities provides activities for executing skills
type SkillExecutionActivities struct {
	SkillManager *skills.SkillManager
	Emulator     *emulators.InfrastructureEmulator
}

// GetSkillContentActivity retrieves and processes the skill content
func (a *SkillExecutionActivities) GetSkillContentActivity(ctx context.Context, skillName string, args []string) (string, error) {
	execution, err := a.SkillManager.ExecuteSkill(skillName, args)
	if err != nil {
		return "", err
	}
	return execution.GetProcessedContent(), nil
}

// ParseSkillStepsActivity parses steps from the markdown content
func (a *SkillExecutionActivities) ParseSkillStepsActivity(ctx context.Context, content string) ([]types.SkillStep, error) {
	var steps []types.SkillStep
	
	lines := strings.Split(content, "\n")
	inStepsSection := false
	inCodeBlock := false
	var currentStep *types.SkillStep
	
	// More flexible regex for steps: supports 1. 1) - [ ] etc.
	stepRegex := regexp.MustCompile(`^(?:\d+\.|\d+\)|- \[ \])\s+(.*)`)
	codeBlockStartRegex := regexp.MustCompile("^```(bash|terraform|curl|kubectl|sh|shell)?")
	
	// Headings that might contain steps
	stepsHeadings := []string{"steps", "instructions", "process", "workflow", "plan"}
	
	for _, line := range lines {
		trimmedLine := strings.TrimSpace(line)
		if trimmedLine == "" {
			continue
		}
		
		lowerLine := strings.ToLower(trimmedLine)
		
		// Detect Steps section (any header containing our keywords)
		if strings.HasPrefix(trimmedLine, "#") {
			isStepsHeader := false
			for _, h := range stepsHeadings {
				if strings.Contains(lowerLine, h) {
					isStepsHeader = true
					break
				}
			}
			
			if isStepsHeader {
				inStepsSection = true
				continue
			}
		}
		
		if !inStepsSection {
			continue
		}

		// Detect new step (either a header with a number or a numbered list item)
		// e.g., #### 1. Parse Input Arguments  OR  1. Validate inputs
		if matches := stepRegex.FindStringSubmatch(trimmedLine); matches != nil {
			if currentStep != nil {
				steps = append(steps, *currentStep)
			}
			
			currentStep = &types.SkillStep{
				Number:      len(steps) + 1,
				Description: matches[1],
				Commands:    []string{},
			}
			// Check for human gate keywords in description
			desc := strings.ToLower(matches[1])
			if strings.Contains(desc, "human gate") || strings.Contains(desc, "confirm") || strings.Contains(desc, "approve") {
				currentStep.IsHumanGate = true
			}
			continue
		} else if strings.HasPrefix(trimmedLine, "#") && regexp.MustCompile(`\d+[\.:]\s+`).MatchString(trimmedLine) {
			// Handle headings like "#### 1. Parse Input Arguments"
			parts := regexp.MustCompile(`\d+[\.:]\s+`).Split(trimmedLine, 2)
			if len(parts) > 1 {
				if currentStep != nil {
					steps = append(steps, *currentStep)
				}
				currentStep = &types.SkillStep{
					Number:      len(steps) + 1,
					Description: strings.TrimSpace(parts[1]),
					Commands:    []string{},
				}
				continue
			}
		}

		if currentStep == nil {
			continue
		}

		// Detect code block start/end
		if codeBlockStartRegex.MatchString(trimmedLine) && !inCodeBlock {
			inCodeBlock = true
			continue
		} else if strings.HasPrefix(trimmedLine, "```") && inCodeBlock {
			inCodeBlock = false
			continue
		}

		// Collect commands
		if inCodeBlock {
			// Extract commands (lines starting with $ or everything in certain blocks)
			if strings.HasPrefix(trimmedLine, "$ ") {
				currentStep.Commands = append(currentStep.Commands, trimmedLine[2:])
			} else if !strings.HasPrefix(trimmedLine, "#") {
				// If no $ prefix but in a bash block, take the whole line
				currentStep.Commands = append(currentStep.Commands, trimmedLine)
			}
		} else if strings.HasPrefix(trimmedLine, "$ ") {
			currentStep.Commands = append(currentStep.Commands, trimmedLine[2:])
		}
	}

	if currentStep != nil {
		steps = append(steps, *currentStep)
	}

	// fallback: if we failed to parse with regex, let's try a simpler split
	if len(steps) == 0 {
		steps = append(steps, types.SkillStep{
			Number: 1,
			Description: "Execute skill instructions",
			Commands: []string{"bash"}, // generic
		})
	}

	return steps, nil
}

// ExecuteSkillStepActivity runs the commands for a step using os/exec
func (a *SkillExecutionActivities) ExecuteSkillStepActivity(ctx context.Context, step types.SkillStep) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing skill step", "number", step.Number, "description", step.Description)

	var outputs []string
	
	if len(step.Commands) == 0 {
		return fmt.Sprintf("Step %d: No commands to execute", step.Number), nil
	}

	for _, cmdStr := range step.Commands {
		outputs = append(outputs, fmt.Sprintf("$ %s", cmdStr))
		
		// In a real sandbox, we use /bin/bash -c for safety and flexibility
		cmd := exec.CommandContext(ctx, "bash", "-c", cmdStr)
		
		// Run in the working directory
		// cmd.Dir = a.SkillManager.WorkingDir // This might be too restrictive if we need to run in repo root
		
		combinedOutput, err := cmd.CombinedOutput()
		outputStr := string(combinedOutput)
		
		if outputStr != "" {
			outputs = append(outputs, outputStr)
		}
		
		if err != nil {
			outputs = append(outputs, fmt.Sprintf("Error: %v", err))
			return strings.Join(outputs, "\n"), err
		}
	}

	return strings.Join(outputs, "\n"), nil
}
