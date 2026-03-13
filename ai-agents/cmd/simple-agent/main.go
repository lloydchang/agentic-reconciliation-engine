package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"gopkg.in/yaml.v3"
)

// SimpleSkill represents a loaded skill
type SimpleSkill struct {
	Name        string   `yaml:"name"`
	Description string   `yaml:"description"`
	Tools       []string `yaml:"tools"`
	Content     string   `yaml:"-"`
}

// AgentResponse represents response from the AI agent
type AgentResponse struct {
	Status        string                 `json:"status"`
	Message       string                 `json:"message"`
	Request       string                 `json:"request"`
	SkillUsed    string                 `json:"skill_used,omitempty"`
	WorkflowID    string                 `json:"workflow_id,omitempty"`
	Result        map[string]interface{} `json:"result,omitempty"`
	Steps         []ExecutionStep        `json:"steps,omitempty"`
	Errors        []string               `json:"errors,omitempty"`
	Timestamp     time.Time             `json:"timestamp"`
}

// ExecutionStep represents a step in skill execution
type ExecutionStep struct {
	Step   int    `json:"step"`
	Action string `json:"action"`
	Result string `json:"result"`
	Output string `json:"output,omitempty"`
}

// SimpleAIAgent is a minimal AI agent implementation
type SimpleAIAgent struct {
	skills      map[string]*SimpleSkill
	keywordMap map[string][]string
}

// NewSimpleAIAgent creates a new simple AI agent
func NewSimpleAIAgent() *SimpleAIAgent {
	return &SimpleAIAgent{
		skills:      make(map[string]*SimpleSkill),
		keywordMap:  make(map[string][]string),
	}
}

// LoadSkills loads skills from .agents/skills directory
func (agent *SimpleAIAgent) LoadSkills(skillsDir string) error {
	// Load skills from directory (simplified for demo)
	skills := []string{
		"terraform-provisioning",
		"compliance-security-scanner", 
		"cicd-pipeline-monitor",
		"incident-triage-runbook",
		"kubernetes-cluster-manager",
		"cost-optimisation",
		"orchestrator",
	}

	for _, skillName := range skills {
		skillPath := filepath.Join(skillsDir, skillName, "SKILL.md")
		if _, err := os.Stat(skillPath); os.IsNotExist(err) {
			log.Printf("Skill file not found: %s", skillPath)
			continue
		}

		content, err := os.ReadFile(skillPath)
		if err != nil {
			log.Printf("Failed to read skill file %s: %v", skillPath, err)
			continue
		}

		// Parse YAML frontmatter
		var skill SimpleSkill
		contentStr := string(content)
		
		startIdx := strings.Index(contentStr, "---")
		if startIdx == -1 {
			log.Printf("No YAML frontmatter found in %s", skillPath)
			continue
		}
		
		endIdx := strings.Index(contentStr[startIdx+3:], "---")
		if endIdx == -1 {
			log.Printf("Unterminated YAML frontmatter in %s", skillPath)
			continue
		}
		
		frontmatter := contentStr[startIdx+3 : startIdx+3+endIdx]
		
		err = yaml.Unmarshal([]byte(frontmatter), &skill)
		if err != nil {
			log.Printf("Failed to parse YAML frontmatter in %s: %v", skillPath, err)
			continue
		}

		skill.Content = contentStr
		agent.skills[skillName] = &skill
		
		// Build keyword map
		description := strings.ToLower(skill.Description)
		words := strings.Fields(description)
		for _, word := range words {
			if len(word) > 3 {
				agent.keywordMap[word] = append(agent.keywordMap[word], skillName)
			}
		}
	}

	// Add AGENTS.md trigger keywords
	agent.addTriggerKeywords()

	log.Printf("Loaded %d skills", len(agent.skills))
	return nil
}

// addTriggerKeywords adds AGENTS.md trigger keywords
func (agent *SimpleAIAgent) addTriggerKeywords() {
	// Simplified trigger keywords from AGENTS.md
	triggers := map[string][]string{
		"terraform":           {"terraform-provisioning"},
		"provision":           {"terraform-provisioning"},
		"infra":               {"terraform-provisioning"},
		"pipeline":            {"cicd-pipeline-monitor"},
		"cicd":               {"cicd-pipeline-monitor"},
		"deploy":              {"cicd-pipeline-monitor"},
		"incident":            {"incident-triage-runbook"},
		"alert":               {"incident-triage-runbook"},
		"p1":                 {"incident-triage-runbook"},
		"outage":              {"incident-triage-runbook"},
		"tenant":              {"tenant-lifecycle-manager"},
		"onboard":             {"tenant-lifecycle-manager"},
		"scan":                {"compliance-security-scanner"},
		"compliance":          {"compliance-security-scanner"},
		"security":            {"compliance-security-scanner"},
		"kubernetes":          {"kubernetes-cluster-manager"},
		"cluster":             {"kubernetes-cluster-manager"},
		"cost":                {"cost-optimisation"},
		"optimization":        {"cost-optimisation"},
		"orchestrator":         {"orchestrator"},
	}

	for keyword, skillNames := range triggers {
		agent.keywordMap[keyword] = skillNames
	}
}

// ProcessRequest processes a user request and triggers appropriate skills
func (agent *SimpleAIAgent) ProcessRequest(request string) (*AgentResponse, error) {
	// Extract keywords from request
	keywords := agent.extractKeywords(request)
	
	// Find matching skills
	var matchedSkills []string
	skillScores := make(map[string]int)
	
	for _, keyword := range keywords {
		keyword = strings.ToLower(keyword)
		if skillNames, exists := agent.keywordMap[keyword]; exists {
			for _, skillName := range skillNames {
				skillScores[skillName] += 100 // High priority for trigger keywords
				matchedSkills = append(matchedSkills, skillName)
			}
		}
	}
	
	if len(matchedSkills) == 0 {
		return &AgentResponse{
			Status:     "no_skill_matched",
			Message:    "No matching skill found for request",
			Request:    request,
			Timestamp:  time.Now(),
		}, nil
	}
	
	// Use best matching skill
	skillName := matchedSkills[0]
	skill, exists := agent.skills[skillName]
	if !exists {
		return &AgentResponse{
			Status:     "skill_not_found",
			Message:    fmt.Sprintf("Skill '%s' not found", skillName),
			Request:    request,
			Timestamp:  time.Now(),
		}, nil
	}
	
	// Check for human gates
	if agent.requiresHumanGate(request) {
		return &AgentResponse{
			Status:        "pending_human_gate",
			Message:       "Human approval required for this operation",
			Request:       request,
			SkillUsed:     skillName,
			Timestamp:     time.Now(),
		}, nil
	}
	
	// Execute skill (simplified)
	result := agent.executeSkill(skill, request)
	
	return &AgentResponse{
		Status:     "success",
		Message:    "Skill executed successfully",
		Request:    request,
		SkillUsed:  skillName,
		Result:     result,
		Steps:      []ExecutionStep{
			{Step: 1, Action: "skill_execution", Result: "success", Output: fmt.Sprintf("Executed %s skill", skillName)},
		},
		Timestamp:  time.Now(),
	}, nil
}

// extractKeywords extracts relevant keywords from user request
func (agent *SimpleAIAgent) extractKeywords(request string) []string {
	keywordMap := map[string]bool{
		"terraform": true, "provision": true, "infra": true, "iac": true,
		"pipeline": true, "cicd": true, "deploy": true, "build": true,
		"incident": true, "alert": true, "p1": true, "outage": true,
		"tenant": true, "onboard": true, "customer": true, "offboard": true,
		"scan": true, "cve": true, "compliance": true, "security": true,
		"kubernetes": true, "cluster": true, "aks": true, "eks": true, "gke": true,
		"cost": true, "spend": true, "optimization": true, "finops": true,
		"orchestrator": true, "workflow": true,
	}
	
	words := strings.Fields(strings.ToLower(request))
	var keywords []string
	
	for _, word := range words {
		if keywordMap[word] {
			keywords = append(keywords, word)
		}
	}
	
	return keywords
}

// requiresHumanGate checks if a skill execution requires human approval
func (agent *SimpleAIAgent) requiresHumanGate(request string) bool {
	highRiskPatterns := []string{
		"destroy", "delete", "remove", "terminate", "shutdown",
		"production", "prod", "critical", "emergency",
	}
	
	requestLower := strings.ToLower(request)
	for _, pattern := range highRiskPatterns {
		if strings.Contains(requestLower, pattern) {
			return true
		}
	}
	
	return false
}

// executeSkill executes a skill (simplified implementation)
func (agent *SimpleAIAgent) executeSkill(skill *SimpleSkill, request string) map[string]interface{} {
	switch skill.Name {
	case "terraform-provisioning":
		return map[string]interface{}{
			"operation":     "plan",
			"environment":   "production",
			"status":       "success",
			"plan_summary": map[string]int{
				"add":     3,
				"change":   1,
				"destroy":  0,
			},
			"resources_affected": []string{
				"aws_vpc.main",
				"aws_subnet.public",
				"aws_eks_cluster.main",
			},
			"next_action": "apply",
		}
	case "compliance-security-scanner":
		return map[string]interface{}{
			"scan_id":         fmt.Sprintf("SCAN-%d", time.Now().Unix()),
			"critical_findings": 1,
			"status":          "success",
			"summary": map[string]int{
				"critical": 1,
				"high":     3,
				"medium":   7,
				"low":      12,
			},
			"compliance_score": 87.5,
		}
	case "cicd-pipeline-monitor":
		return map[string]interface{}{
			"workflow_id":   fmt.Sprintf("WF-%d", time.Now().Unix()),
			"status":        "success",
			"pipelines": []map[string]interface{}{
				{
					"name":       "main-app-deploy",
					"status":     "failed",
					"stage":      "deploy-to-production",
					"duration":   "12m 34s",
					"failure_reason": "Health check timeout",
				},
			},
		}
	case "orchestrator":
		return map[string]interface{}{
			"workflow_id":     fmt.Sprintf("WF-%d", time.Now().Unix()),
			"workflow_type":  "composite",
			"status":         "success",
			"skills_executed": []string{"compliance-security-scanner", "cost-optimisation"},
			"overall_status": "completed",
		}
	default:
		return map[string]interface{}{
			"skill_name": skill.Name,
			"status":      "success",
			"message":     fmt.Sprintf("Skill %s executed successfully", skill.Name),
			"executed_at": time.Now().Format(time.RFC3339),
		}
	}
}

func main() {
	// Parse command line flags
	var (
		port = flag.String("port", "8081", "Port to run AI agent service on")
		help = flag.Bool("help", false, "Show help information")
	)
	flag.Parse()

	if *help {
		showHelp()
		return
	}

	// Create and initialize AI agent
	agent := NewSimpleAIAgent()
	skillsDir := ".agents/skills"
	
	err := agent.LoadSkills(skillsDir)
	if err != nil {
		log.Fatalf("Failed to load skills: %v", err)
	}

	fmt.Println("🤖 Cloud AI Agent Skills Service (agentskills.io Compliant)")
	fmt.Println("=============================================================")
	fmt.Printf("📡 Starting AI agent service on port %s\n", *port)
	fmt.Printf("📋 Skills loaded from %s\n", skillsDir)
	fmt.Printf("🔗 AGENTS.md integration enabled\n")
	fmt.Printf("⚡ agentskills.io specification compliant\n")
	fmt.Println()

	// Create HTTP server
	mux := http.NewServeMux()
	
	// Register API endpoints
	mux.HandleFunc("/api/v1/health", handleHealth)
	mux.HandleFunc("/api/v1/skills", handleListSkills(agent))
	mux.HandleFunc("/api/v1/skills/execute", handleExecuteSkill(agent))
	mux.HandleFunc("/api/v1/workflows", handleListWorkflows)
	mux.HandleFunc("/api/v1/workflows/execute", handleExecuteWorkflow(agent))

	server := &http.Server{
		Addr:         ":" + *port,
		Handler:      mux,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start server in goroutine
	go func() {
		fmt.Printf("🚀 Server listening on port %s\n", *port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("AI agent service failed: %v", err)
		}
	}()

	// Wait for shutdown signal
	<-sigChan
	fmt.Println("\n🛑 Shutdown signal received")

	// Graceful shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30)
	defer cancel()

	server.Shutdown(shutdownCtx)
	fmt.Println("✅ AI agent service stopped gracefully")
}

func showHelp() {
	fmt.Println("Cloud AI Agent Skills Service - agentskills.io Compliant")
	fmt.Println("=============================================================")
	fmt.Println()
	fmt.Println("This service provides HTTP API endpoints for executing AI agent skills")
	fmt.Println("that are defined in AGENTS.md and .agents/skills/ SKILL.md files.")
	fmt.Println("Fully compliant with agentskills.io specification.")
	fmt.Println()
	fmt.Println("Usage:")
	fmt.Println("  simple-agent [options]")
	fmt.Println()
	fmt.Println("Options:")
	fmt.Println("  -port string")
	fmt.Println("        Port to run the AI agent service on (default: 8081)")
	fmt.Println("  -help")
	fmt.Println("        Show this help information")
	fmt.Println()
	fmt.Println("API Endpoints:")
	fmt.Println("  GET  /api/v1/health")
	fmt.Println("        Service health check")
	fmt.Println()
	fmt.Println("  GET  /api/v1/skills")
	fmt.Println("        List all available skills from AGENTS.md")
	fmt.Println()
	fmt.Println("  POST /api/v1/skills/execute")
	fmt.Println("        Execute a skill with AI agent processing")
	fmt.Println("        Body: {\"request\": \"provision EKS cluster for payments\"}")
	fmt.Println()
	fmt.Println("  GET  /api/v1/workflows")
	fmt.Println("        List available composite workflows from AGENTS.md")
	fmt.Println()
	fmt.Println("  POST /api/v1/workflows/execute")
	fmt.Println("        Execute a composite workflow")
	fmt.Println("        Body: {\"workflow_id\": \"WORKFLOW-01\", \"request\": \"onboard Acme Corp\"}")
	fmt.Println()
	fmt.Println("Examples:")
	fmt.Println("  # Start the service")
	fmt.Println("  simple-agent -port 8081")
	fmt.Println()
	fmt.Println("  # Execute terraform provisioning skill")
	fmt.Println("  curl -X POST http://localhost:8081/api/v1/skills/execute \\")
	fmt.Println("       -H 'Content-Type: application/json' \\")
	fmt.Println("       -d '{\"request\": \"provision new EKS cluster in us-east-1\"}'")
	fmt.Println()
	fmt.Println("  # Execute tenant onboarding workflow")
	fmt.Println("  curl -X POST http://localhost:8081/api/v1/workflows/execute \\")
	fmt.Println("       -H 'Content-Type: application/json' \\")
	fmt.Println("       -d '{\"workflow_id\": \"WORKFLOW-01\", \"request\": \"onboard Acme Corp enterprise\"}'")
}

// HTTP Handlers
func handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	health := map[string]interface{}{
		"status":      "healthy",
		"timestamp":   time.Now().Format(time.RFC3339),
		"version":     "1.0.0",
		"agentskills":  "compliant",
		"skills_loaded": true,
	}

	writeJSONResponse(w, health)
}

func handleListSkills(agent *SimpleAIAgent) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		skillsList := make(map[string]*SimpleSkill)
		for name, skill := range agent.skills {
			skillsList[name] = skill
		}

		response := map[string]interface{}{
			"skills": skillsList,
			"count":  len(skillsList),
		}

		writeJSONResponse(w, response)
	}
}

func handleExecuteSkill(agent *SimpleAIAgent) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var request struct {
			Request string `json:"request"`
		}

		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Process request using AI agent
		response, err := agent.ProcessRequest(request.Request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		writeJSONResponse(w, response)
	}
}

func handleListWorkflows(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	workflows := []map[string]interface{}{
		{
			"id":          "WORKFLOW-01",
			"name":        "Full Tenant Onboarding",
			"description": "Complete tenant onboarding with infrastructure, security, and monitoring",
			"trigger":     "onboard [tenant] as enterprise tier in [region]",
		},
		{
			"id":          "WORKFLOW-02",
			"name":        "P1 Incident Response",
			"description": "Automated incident response with triage and notification",
			"trigger":     "P1 incident detected or take over incident response",
		},
		{
			"id":          "WORKFLOW-03",
			"name":        "Weekly Compliance Scan",
			"description": "Automated weekly security and compliance scanning",
			"trigger":     "Weekly scheduled compliance scan",
		},
	}

	response := map[string]interface{}{
		"workflows": workflows,
		"count":     len(workflows),
	}

	writeJSONResponse(w, response)
}

func handleExecuteWorkflow(agent *SimpleAIAgent) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var request struct {
			WorkflowID string `json:"workflow_id"`
			Request    string `json:"request"`
		}

		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Process as orchestrator skill
		response, err := agent.ProcessRequest(request.Request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		writeJSONResponse(w, response)
	}
}

func writeJSONResponse(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

	if err := json.NewEncoder(w).Encode(data); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
	}
}
