package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/lloydchang/backstage-temporal/backend/mcp"
)

var (
	serverURL   string
	apiKey      string
	verbose     bool
	interactive bool
)

type CLIClient struct {
	serverURL string
	apiKey    string
	httpClient *http.Client
}

type WorkflowStatus struct {
	WorkflowID string                 `json:"workflowId"`
	RunID      string                 `json:"runId"`
	Status     string                 `json:"status"`
	StartTime  *time.Time             `json:"startTime,omitempty"`
	CloseTime  *time.Time             `json:"closeTime,omitempty"`
	Details    map[string]interface{} `json:"details,omitempty"`
}

type WorkflowResult struct {
	WorkflowID string      `json:"workflowId"`
	Status     string      `json:"status"`
	Result     interface{} `json:"result,omitempty"`
	Error      string      `json:"error,omitempty"`
}

func NewCLIClient(serverURL, apiKey string) *CLIClient {
	return &CLIClient{
		serverURL: strings.TrimSuffix(serverURL, "/"),
		apiKey:    apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *CLIClient) makeRequest(method, endpoint string, body io.Reader) (*http.Response, error) {
	url := c.serverURL + endpoint
	req, err := http.NewRequest(method, url, body)
	if err != nil {
		return nil, err
	}

	if c.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.apiKey)
	}
	req.Header.Set("Content-Type", "application/json")

	if verbose {
		log.Printf("Making %s request to %s", method, url)
	}

	return c.httpClient.Do(req)
}

func (c *CLIClient) startWorkflow(workflowType string, targetResource string, params map[string]interface{}) (*WorkflowResult, error) {
	var endpoint string
	var requestBody map[string]interface{}

	switch workflowType {
	case "compliance":
		endpoint = "/workflow/start-enhanced-compliance"
		requestBody = map[string]interface{}{
			"targetResource": targetResource,
			"parameters":     params,
			"priority":       "normal",
		}
	case "batch":
		endpoint = "/workflow/start-batch"
		requestBody = []map[string]interface{}{
			{
				"targetResource": targetResource,
				"parameters":     params,
			},
		}
	default:
		return nil, fmt.Errorf("unknown workflow type: %s", workflowType)
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return nil, err
	}

	resp, err := c.makeRequest("POST", endpoint, strings.NewReader(string(jsonBody)))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var result WorkflowResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

func (c *CLIClient) getWorkflowStatus(workflowID string) (*WorkflowStatus, error) {
	endpoint := "/workflow/status?id=" + workflowID

	resp, err := c.makeRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var status WorkflowStatus
	if err := json.NewDecoder(resp.Body).Decode(&status); err != nil {
		return nil, err
	}

	return &status, nil
}

func (c *CLIClient) listWorkflows() ([]WorkflowStatus, error) {
	// This would require a new endpoint - for now return empty
	return []WorkflowStatus{}, nil
}

func (c *CLIClient) signalWorkflow(workflowID, signalName, signalValue string) error {
	endpoint := fmt.Sprintf("/workflow/signal/%s", workflowID)

	requestBody := map[string]interface{}{
		"signal": signalName,
		"value":  signalValue,
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return err
	}

	resp, err := c.makeRequest("POST", endpoint, strings.NewReader(string(jsonBody)))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

func (c *CLIClient) getHealth() (map[string]interface{}, error) {
	resp, err := c.makeRequest("GET", "/health", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var health map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return nil, err
	}

	return health, nil
}

func (c *CLIClient) invokeSkill(skillName string, args []string) (map[string]interface{}, error) {
	endpoint := fmt.Sprintf("/api/skills/%s/execute", skillName)

	requestBody := map[string]interface{}{
		"arguments": args,
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return nil, err
	}

	resp, err := c.makeRequest("POST", endpoint, strings.NewReader(string(jsonBody)))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result, nil
}

func (c *CLIClient) listSkills() ([]map[string]interface{}, error) {
	resp, err := c.makeRequest("GET", "/api/skills", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, err
	}

	if skills, ok := response["skills"].([]interface{}); ok {
		var result []map[string]interface{}
		for _, skill := range skills {
			if skillMap, ok := skill.(map[string]interface{}); ok {
				result = append(result, skillMap)
			}
		}
		return result, nil
	}

	return nil, fmt.Errorf("invalid response format")
}

func (c *CLIClient) getSkill(name string) (map[string]interface{}, error) {
	endpoint := fmt.Sprintf("/api/skills/%s", name)

	resp, err := c.makeRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(body))
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return result, nil
}

var rootCmd = &cobra.Command{
	Use:   "temporal-agents",
	Short: "Temporal AI Agents CLI",
	Long:  `Command-line interface for managing Temporal AI agent workflows and MCP interactions.`,
}

var startCmd = &cobra.Command{
	Use:   "start [workflow-type] [target-resource]",
	Short: "Start a new workflow",
	Long:  `Start a new AI agent workflow. Supported types: compliance, security, cost-analysis`,
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		workflowType := args[0]
		targetResource := args[1]

		fmt.Printf("Starting %s workflow for %s...\n", workflowType, targetResource)

		result, err := client.startWorkflow(workflowType, targetResource, map[string]interface{}{})
		if err != nil {
			log.Fatalf("Failed to start workflow: %v", err)
		}

		fmt.Printf("Workflow started successfully!\n")
		fmt.Printf("Workflow ID: %s\n", result.WorkflowID)
		fmt.Printf("Run ID: %s\n", result.RunID)
		fmt.Printf("Status: %s\n", result.Status)
	},
}

var statusCmd = &cobra.Command{
	Use:   "status [workflow-id]",
	Short: "Get workflow status",
	Long:  `Get the current status of a running workflow.`,
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		workflowID := args[0]

		status, err := client.getWorkflowStatus(workflowID)
		if err != nil {
			log.Fatalf("Failed to get workflow status: %v", err)
		}

		fmt.Printf("Workflow Status:\n")
		fmt.Printf("ID: %s\n", status.WorkflowID)
		fmt.Printf("Run ID: %s\n", status.RunID)
		fmt.Printf("Status: %s\n", status.Status)

		if status.StartTime != nil {
			fmt.Printf("Started: %s\n", status.StartTime.Format(time.RFC3339))
		}
		if status.CloseTime != nil {
			fmt.Printf("Completed: %s\n", status.CloseTime.Format(time.RFC3339))
		}

		if status.Details != nil && verbose {
			fmt.Printf("Details: %+v\n", status.Details)
		}
	},
}

var signalCmd = &cobra.Command{
	Use:   "signal [workflow-id] [signal-name] [signal-value]",
	Short: "Send a signal to a workflow",
	Long:  `Send a signal to a running workflow to trigger state changes.`,
	Args:  cobra.ExactArgs(3),
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		workflowID := args[0]
		signalName := args[1]
		signalValue := args[2]

		fmt.Printf("Sending signal '%s' with value '%s' to workflow %s...\n",
			signalName, signalValue, workflowID)

		err := client.signalWorkflow(workflowID, signalName, signalValue)
		if err != nil {
			log.Fatalf("Failed to send signal: %v", err)
		}

		fmt.Println("Signal sent successfully!")
	},
}

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List workflows",
	Long:  `List all workflows and their current status.`,
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		workflows, err := client.listWorkflows()
		if err != nil {
			log.Fatalf("Failed to list workflows: %v", err)
		}

		if len(workflows) == 0 {
			fmt.Println("No workflows found.")
			return
		}

		fmt.Printf("%-40s %-15s %-20s\n", "Workflow ID", "Status", "Started")
		fmt.Println(strings.Repeat("-", 75))

		for _, wf := range workflows {
			startTime := "N/A"
			if wf.StartTime != nil {
				startTime = wf.StartTime.Format("2006-01-02 15:04:05")
			}
			fmt.Printf("%-40s %-15s %-20s\n", truncateString(wf.WorkflowID, 40), wf.Status, startTime)
		}
	},
}

var healthCmd = &cobra.Command{
	Use:   "health",
	Short: "Check server health",
	Long:  `Check the health status of the Temporal AI Agents server.`,
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		health, err := client.getHealth()
		if err != nil {
			log.Fatalf("Failed to get health status: %v", err)
		}

		fmt.Println("Server Health:")
		if status, ok := health["status"].(string); ok {
			fmt.Printf("Status: %s\n", status)
		}
		if version, ok := health["version"].(string); ok {
			fmt.Printf("Version: %s\n", version)
		}
		if uptime, ok := health["uptime"].(float64); ok {
			fmt.Printf("Uptime: %.2f seconds\n", uptime)
		}
		if goroutines, ok := health["goroutines"].(float64); ok {
			fmt.Printf("Goroutines: %.0f\n", goroutines)
		}

		if verbose {
			fmt.Printf("Full health info: %+v\n", health)
		}
	},
}

var skillCmd = &cobra.Command{
	Use:   "skill",
	Short: "Manage and invoke skills",
	Long:  `Manage and invoke AI agent skills. Skills are reusable capabilities that can be executed with specific parameters.`,
}

var skillInvokeCmd = &cobra.Command{
	Use:   "invoke [skill-name] [args...]",
	Short: "Invoke a skill",
	Long:  `Invoke a skill with optional arguments. Use /skill-name syntax or just skill-name.`,
	Args:  cobra.MinimumNArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		skillName := args[0]
		skillArgs := args[1:]

		// Handle /skill-name syntax
		if strings.HasPrefix(skillName, "/") {
			skillName = skillName[1:]
		}

		fmt.Printf("Invoking skill '%s' with arguments: %v\n", skillName, skillArgs)

		result, err := client.invokeSkill(skillName, skillArgs)
		if err != nil {
			log.Fatalf("Failed to invoke skill: %v", err)
		}

		fmt.Printf("Skill executed successfully!\n")
		if executionId, ok := result["executionId"].(string); ok {
			fmt.Printf("Execution ID: %s\n", executionId)
		}
		if forkRequired, ok := result["forkRequired"].(bool); ok && forkRequired {
			if agentType, ok := result["agentType"].(string); ok {
				fmt.Printf("Running in forked context with agent: %s\n", agentType)
			}
		}
		if content, ok := result["content"].(string); ok && verbose {
			fmt.Printf("Content: %s\n", content)
		}
	},
}

var skillListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available skills",
	Long:  `List all available skills with their descriptions and capabilities.`,
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		skills, err := client.listSkills()
		if err != nil {
			log.Fatalf("Failed to list skills: %v", err)
		}

		if len(skills) == 0 {
			fmt.Println("No skills available.")
			return
		}

		fmt.Printf("%-20s %-50s %-10s\n", "Name", "Description", "Scope")
		fmt.Println(strings.Repeat("-", 80))

		for _, skill := range skills {
			name := ""
			if n, ok := skill["name"].(string); ok {
				name = n
			}
			description := ""
			if d, ok := skill["description"].(string); ok {
				description = d
			}
			scope := ""
			if s, ok := skill["scope"].(string); ok {
				scope = s
			}

			fmt.Printf("%-20s %-50s %-10s\n",
				truncateString(name, 20),
				truncateString(description, 50),
				scope)
		}
	},
}

var skillInfoCmd = &cobra.Command{
	Use:   "info [skill-name]",
	Short: "Get detailed information about a skill",
	Long:  `Get detailed information about a specific skill including parameters and usage.`,
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)

		skillName := args[0]

		skill, err := client.getSkill(skillName)
		if err != nil {
			log.Fatalf("Failed to get skill info: %v", err)
		}

		fmt.Printf("Skill: %s\n", skillName)
		if desc, ok := skill["description"].(string); ok {
			fmt.Printf("Description: %s\n", desc)
		}
		if scope, ok := skill["scope"].(string); ok {
			fmt.Printf("Scope: %s\n", scope)
		}
		if argHint, ok := skill["argumentHint"].(string); ok && argHint != "" {
			fmt.Printf("Arguments: %s\n", argHint)
		}
		if model, ok := skill["model"].(string); ok && model != "" {
			fmt.Printf("Model: %s\n", model)
		}
		if context, ok := skill["context"].(string); ok && context != "" {
			fmt.Printf("Context: %s\n", context)
		}

		fmt.Printf("User Invocable: ")
		if userInvocable, ok := skill["userInvocable"].(bool); ok && userInvocable {
			fmt.Printf("Yes\n")
		} else {
			fmt.Printf("No\n")
		}

		if allowedTools, ok := skill["allowedTools"].([]interface{}); ok && len(allowedTools) > 0 {
			fmt.Printf("Allowed Tools: ")
			for i, tool := range allowedTools {
				if i > 0 {
					fmt.Printf(", ")
				}
				fmt.Printf("%v", tool)
			}
			fmt.Printf("\n")
		}
	},
}

var interactiveCmd = &cobra.Command{
	Use:   "interactive",
	Short: "Start interactive mode",
	Long:  `Start an interactive shell for managing workflows.`,
	Run: func(cmd *cobra.Command, args []string) {
		client := NewCLIClient(serverURL, apiKey)
		runInteractiveMode(client)
	},
}

func runInteractiveMode(client *CLIClient) {
	fmt.Println("Temporal AI Agents Interactive Mode")
	fmt.Println("Type 'help' for available commands, 'quit' to exit")
	fmt.Println()

	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("> ")
		if !scanner.Scan() {
			break
		}

		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		args := strings.Fields(line)
		command := args[0]

		switch command {
		case "help":
			printInteractiveHelp()
		case "start":
			handleInteractiveStart(client, args[1:])
		case "status":
			handleInteractiveStatus(client, args[1:])
		case "signal":
			handleInteractiveSignal(client, args[1:])
		case "list":
			handleInteractiveList(client)
		case "health":
			handleInteractiveHealth(client)
		case "skill":
			handleInteractiveSkill(client, args[1:])
		case "skills":
			handleInteractiveSkills(client, args[1:])
		default:
			fmt.Printf("Unknown command: %s. Type 'help' for available commands.\n", command)
		}
		fmt.Println()
	}
}

func printInteractiveHelp() {
	fmt.Println("Available commands:")
	fmt.Println("  start <type> <resource>     - Start a workflow")
	fmt.Println("  status <workflow-id>        - Get workflow status")
	fmt.Println("  signal <id> <name> <value>  - Send signal to workflow")
	fmt.Println("  list                        - List workflows")
	fmt.Println("  skill <name> [args...]      - Invoke a skill (/name syntax also works)")
	fmt.Println("  skills list                 - List available skills")
	fmt.Println("  skills info <name>          - Get skill information")
	fmt.Println("  health                      - Check server health")
	fmt.Println("  metrics                     - Get server metrics")
	fmt.Println("  help                        - Show this help")
	fmt.Println("  quit                        - Exit interactive mode")
}

func handleInteractiveSkill(client *CLIClient, args []string) {
	if len(args) < 1 {
		fmt.Println("Usage: skill <skill-name> [args...]")
		fmt.Println("Or use: /skill-name [args...]")
		return
	}

	skillName := args[0]
	skillArgs := args[1:]

	// Handle /skill-name syntax
	if strings.HasPrefix(skillName, "/") {
		skillName = skillName[1:]
	}

	fmt.Printf("Invoking skill '%s'...\n", skillName)

	result, err := client.invokeSkill(skillName, skillArgs)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Skill executed successfully!\n")
	if executionId, ok := result["executionId"].(string); ok {
		fmt.Printf("Execution ID: %s\n", executionId)
	}
	if forkRequired, ok := result["forkRequired"].(bool); ok && forkRequired {
		if agentType, ok := result["agentType"].(string); ok {
			fmt.Printf("Running in forked context with agent: %s\n", agentType)
		}
	}
}

func handleInteractiveSkills(client *CLIClient, args []string) {
	if len(args) == 0 {
		// Default to list
		handleInteractiveSkillList(client)
		return
	}

	subcommand := args[0]
	subargs := args[1:]

	switch subcommand {
	case "list":
		handleInteractiveSkillList(client)
	case "info":
		if len(subargs) < 1 {
			fmt.Println("Usage: skills info <skill-name>")
			return
		}
		handleInteractiveSkillInfo(client, subargs[0])
	default:
		fmt.Printf("Unknown skills subcommand: %s\n", subcommand)
		fmt.Println("Available subcommands: list, info")
	}
}

func handleInteractiveSkillList(client *CLIClient) {
	skills, err := client.listSkills()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	if len(skills) == 0 {
		fmt.Println("No skills available")
		return
	}

	fmt.Println("Available skills:")
	for _, skill := range skills {
		name := ""
		if n, ok := skill["name"].(string); ok {
			name = n
		}
		description := ""
		if d, ok := skill["description"].(string); ok {
			description = d
		}
		fmt.Printf("  /%s - %s\n", name, description)
	}
}

func handleInteractiveSkillInfo(client *CLIClient, skillName string) {
	skill, err := client.getSkill(skillName)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Skill: %s\n", skillName)
	if desc, ok := skill["description"].(string); ok {
		fmt.Printf("Description: %s\n", desc)
	}
	if scope, ok := skill["scope"].(string); ok {
		fmt.Printf("Scope: %s\n", scope)
	}
	if argHint, ok := skill["argumentHint"].(string); ok && argHint != "" {
		fmt.Printf("Arguments: %s\n", argHint)
	}
}

func handleInteractiveStart(client *CLIClient, args []string) {
	if len(args) < 2 {
		fmt.Println("Usage: start <type> <resource>")
		return
	}

	workflowType := args[0]
	targetResource := args[1]

	fmt.Printf("Starting %s workflow for %s...\n", workflowType, targetResource)

	result, err := client.startWorkflow(workflowType, targetResource, map[string]interface{}{})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Workflow started: %s\n", result.WorkflowID)
}

func handleInteractiveStatus(client *CLIClient, args []string) {
	if len(args) < 1 {
		fmt.Println("Usage: status <workflow-id>")
		return
	}

	workflowID := args[0]

	status, err := client.getWorkflowStatus(workflowID)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Status: %s\n", status.Status)
	if status.StartTime != nil {
		fmt.Printf("Started: %s\n", status.StartTime.Format(time.RFC3339))
	}
}

func handleInteractiveSignal(client *CLIClient, args []string) {
	if len(args) < 3 {
		fmt.Println("Usage: signal <workflow-id> <signal-name> <signal-value>")
		return
	}

	workflowID := args[0]
	signalName := args[1]
	signalValue := args[2]

	err := client.signalWorkflow(workflowID, signalName, signalValue)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Println("Signal sent successfully")
}

func handleInteractiveList(client *CLIClient) {
	workflows, err := client.listWorkflows()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	if len(workflows) == 0 {
		fmt.Println("No workflows found")
		return
	}

	for _, wf := range workflows {
		fmt.Printf("%s - %s\n", wf.WorkflowID, wf.Status)
	}
}

func handleInteractiveHealth(client *CLIClient) {
	health, err := client.getHealth()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	if status, ok := health["status"].(string); ok {
		fmt.Printf("Status: %s\n", status)
	}
}

func handleInteractiveMetrics(client *CLIClient) {
	metrics, err := client.getMetrics()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	for key, value := range metrics {
		fmt.Printf("%s: %v\n", key, value)
	}
}

func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func init() {
	rootCmd.PersistentFlags().StringVarP(&serverURL, "server", "s", "http://localhost:8081", "Server URL")
	rootCmd.PersistentFlags().StringVarP(&apiKey, "api-key", "k", "", "API key for authentication")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose output")
	rootCmd.PersistentFlags().BoolVarP(&interactive, "interactive", "i", false, "Start in interactive mode")

	rootCmd.AddCommand(startCmd)
	rootCmd.AddCommand(statusCmd)
	rootCmd.AddCommand(signalCmd)
	rootCmd.AddCommand(listCmd)
	rootCmd.AddCommand(healthCmd)
	rootCmd.AddCommand(metricsCmd)
	rootCmd.AddCommand(interactiveCmd)
	rootCmd.AddCommand(skillCmd)

	// Add skill subcommands
	skillCmd.AddCommand(skillInvokeCmd)
	skillCmd.AddCommand(skillListCmd)
	skillCmd.AddCommand(skillInfoCmd)
}

func main() {
	if interactive {
		client := NewCLIClient(serverURL, apiKey)
		runInteractiveMode(client)
	} else {
		if err := rootCmd.Execute(); err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}
}
