package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/lloydchang/gitops-infra-control-plane/backend/service"
)

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

	// Create and initialize skill service
	skillService, err := service.NewSkillService()
	if err != nil {
		log.Fatalf("Failed to create skill service: %v", err)
	}

	// Initialize the service
	ctx := context.Background()
	err = skillService.Initialize(ctx)
	if err != nil {
		log.Fatalf("Failed to initialize skill service: %v", err)
	}

	fmt.Println("🤖 Cloud AI Agent Skills Service")
	fmt.Println("=================================")
	fmt.Printf("📡 Starting AI agent service on port %s\n", *port)
	fmt.Printf("📋 Skills loaded from .agents/skills/\n")
	fmt.Printf("🔗 AGENTS.md integration enabled\n")
	fmt.Printf("⚡ agentskills.io specification compliant\n")
	fmt.Println()

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start service in goroutine
	go func() {
		if err := skillService.Start(ctx, *port); err != nil {
			log.Fatalf("AI agent service failed: %v", err)
		}
	}()

	// Wait for shutdown signal
	<-sigChan
	fmt.Println("\n🛑 Shutdown signal received")

	// Graceful shutdown
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30)
	defer cancel()

	if err := skillService.Stop(shutdownCtx); err != nil {
		log.Printf("Error during shutdown: %v", err)
	}

	fmt.Println("✅ AI agent service stopped gracefully")
}

func showHelp() {
	fmt.Println("Cloud AI Agent Skills Service - agentskills.io Compliant")
	fmt.Println("======================================================")
	fmt.Println()
	fmt.Println("This service provides HTTP API endpoints for executing AI agent skills")
	fmt.Println("that are defined in AGENTS.md and .agents/skills/ SKILL.md files.")
	fmt.Println("Fully compliant with agentskills.io specification.")
	fmt.Println()
	fmt.Println("Usage:")
	fmt.Println("  ai-agent [options]")
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
	fmt.Println("  GET  /api/v1/skills/{name}")
	fmt.Println("        Get details for a specific skill")
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
	fmt.Println("AGENTS.md Integration:")
	fmt.Println("  ✅ Parses trigger keyword table")
	fmt.Println("  ✅ Maps keywords to skills")
	fmt.Println("  ✅ Implements human gates")
	fmt.Println("  ✅ Supports composite workflows")
	fmt.Println("  ✅ Returns structured JSON responses")
	fmt.Println()
	fmt.Println("Examples:")
	fmt.Println("  # Start the service")
	fmt.Println("  ai-agent -port 8081")
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
	fmt.Println()
	fmt.Println("  # Check service health")
	fmt.Println("  curl http://localhost:8081/api/v1/health")
	fmt.Println()
	fmt.Println("Supported Skills (from AGENTS.md):")
	fmt.Println("  infrastructure-provisioning, cicd-pipeline-monitor, incident-triage-runbook")
	fmt.Println("  tenant-lifecycle-manager, compliance-security-scanner, sla-monitoring-alerting")
	fmt.Println("  deployment-validation, kpi-report-generator, runbook-documentation-gen")
	fmt.Println("  kubernetes-cluster-manager, cost-optimisation, secrets-certificate-manager")
	fmt.Println("  And 25+ more specialized skills...")
	fmt.Println()
	fmt.Println("Supported Workflows (from AGENTS.md):")
	fmt.Println("  WORKFLOW-01: Full Tenant Onboarding")
	fmt.Println("  WORKFLOW-02: P1 Incident Response")
	fmt.Println("  WORKFLOW-03: Weekly Compliance Scan")
	fmt.Println("  And 7+ more composite workflows...")
}
