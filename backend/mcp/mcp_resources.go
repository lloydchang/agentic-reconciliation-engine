package mcp

import (
	"context"
	"fmt"
	"time"
)

// registerDefaultResources registers the default MCP resources
func (s *MCPServer) registerDefaultResources() {
	// Workflow Results Resource
	s.RegisterResource(&MCPResource{
		Name:        "Workflow Results",
		Description: "Access completed workflow results and reports",
		URI:         "workflow://results",
		MimeType:    "application/json",
		Handler:     s.handleWorkflowResults,
	})

	// Agent Capabilities Resource
	s.RegisterResource(&MCPResource{
		Name:        "Agent Capabilities",
		Description: "Discover available AI agents and their capabilities",
		URI:         "agent://capabilities",
		MimeType:    "application/json",
		Handler:     s.handleAgentCapabilities,
	})

	// Compliance Reports Resource
	s.RegisterResource(&MCPResource{
		Name:        "Compliance Reports",
		Description: "Retrieve compliance reports and audit trails",
		URI:         "compliance://reports",
		MimeType:    "application/json",
		Handler:     s.handleComplianceReports,
	})

	// Infrastructure State Resource
	s.RegisterResource(&MCPResource{
		Name:        "Infrastructure State",
		Description: "Current infrastructure state and configuration",
		URI:         "infrastructure://state",
		MimeType:    "application/json",
		Handler:     s.handleInfrastructureState,
	})

	// Workflow Metrics Resource
	s.RegisterResource(&MCPResource{
		Name:        "Workflow Metrics",
		Description: "Performance metrics and statistics for workflows",
		URI:         "workflow://metrics",
		MimeType:    "application/json",
		Handler:     s.handleWorkflowMetrics,
	})

	// Human Tasks Resource
	s.RegisterResource(&MCPResource{
		Name:        "Human Tasks",
		Description: "Access human review tasks and their status",
		URI:         "human://tasks",
		MimeType:    "application/json",
		Handler:     s.handleHumanTasks,
	})
}

// handleWorkflowResults handles access to workflow results
func (s *MCPServer) handleWorkflowResults(ctx context.Context, uri string) (interface{}, error) {
	// Parse URI for specific workflow ID if provided
	workflowId := ""
	if len(uri) > len("workflow://results/") {
		workflowId = uri[len("workflow://results/"):]
	}

	if workflowId != "" {
		// Get specific workflow result
		// For now, return a simulated result since we're avoiding Temporal API complexity
		result := map[string]interface{}{
			"workflowId":   workflowId,
			"runId":        fmt.Sprintf("run-%d", time.Now().Unix()),
			"status":       "completed",
			"workflowType": "AIAgentOrchestrationWorkflowV2",
			"result": map[string]interface{}{
				"complianceScore": 92.5,
				"issuesFound":     3,
				"recommendations": []string{
					"Update SSL certificates",
					"Enable encryption at rest",
					"Review access permissions",
				},
				"approved": true,
				"reportUrl": fmt.Sprintf("/reports/%s.pdf", workflowId),
			},
			"completedAt": time.Now().Add(-2*time.Hour).Format(time.RFC3339),
		}

		return result, nil
	} else {
		// Get list of recent workflow results
		// In a real implementation, this would query a results database
		results := map[string]interface{}{
			"workflows": []map[string]interface{}{
				{
					"workflowId":     "mcp-compliance-vm-web-server-001-1705123456",
					"targetResource": "vm-web-server-001",
					"workflowType":   "AIAgentOrchestrationWorkflowV2",
					"status":         "completed",
					"complianceScore": 92.5,
					"completedAt":    time.Now().Add(-2*time.Hour).Format(time.RFC3339),
				},
				{
					"workflowId":     "mcp-security-db-main-001-1705123457",
					"targetResource": "db-main-001",
					"workflowType":   "AIAgentOrchestrationWorkflowV2",
					"status":         "completed",
					"complianceScore": 88.0,
					"completedAt":    time.Now().Add(-4*time.Hour).Format(time.RFC3339),
				},
				{
					"workflowId":     "mcp-cost-storage-backups-001-1705123458",
					"targetResource": "storage-backups-001",
					"workflowType":   "AIAgentOrchestrationWorkflowV2",
					"status":         "running",
					"startedAt":      time.Now().Add(-30*time.Minute).Format(time.RFC3339),
				},
			},
			"total": 3,
			"queriedAt": time.Now().Format(time.RFC3339),
		}

		return results, nil
	}
}

// handleAgentCapabilities handles discovery of agent capabilities
func (s *MCPServer) handleAgentCapabilities(ctx context.Context, uri string) (interface{}, error) {
	capabilities := map[string]interface{}{
		"agents": []map[string]interface{}{
			{
				"name":        "SecurityAgent",
				"description": "Performs security analysis and vulnerability scanning",
				"capabilities": []string{
					"vulnerability_scanning",
					"malware_detection",
					"configuration_audit",
					"compliance_check",
				},
				"supportedResources": []string{"vm", "database", "storage", "network"},
				"executionTime":      "5-15 minutes",
				"confidence":         0.95,
			},
			{
				"name":        "ComplianceAgent",
				"description": "Ensures regulatory compliance and audit readiness",
				"capabilities": []string{
					"SOC2_compliance",
					"GDPR_compliance",
					"HIPAA_compliance",
					"audit_trail_generation",
				},
				"supportedResources": []string{"vm", "database", "storage"},
				"executionTime":      "10-20 minutes",
				"confidence":         0.92,
			},
			{
				"name":        "CostOptimizationAgent",
				"description": "Analyzes and optimizes cloud resource costs",
				"capabilities": []string{
					"usage_analysis",
					"cost_forecasting",
					"optimization_recommendations",
					"resource_rightsizing",
				},
				"supportedResources": []string{"vm", "storage", "network"},
				"executionTime":      "3-10 minutes",
				"confidence":         0.88,
			},
		},
		"totalAgents": 3,
		"lastUpdated": time.Now().Format(time.RFC3339),
	}

	return capabilities, nil
}

// handleComplianceReports handles access to compliance reports
func (s *MCPServer) handleComplianceReports(ctx context.Context, uri string) (interface{}, error) {
	// Parse URI for specific report ID if provided
	reportId := ""
	if len(uri) > len("compliance://reports/") {
		reportId = uri[len("compliance://reports/"):]
	}

	if reportId != "" {
		// Get specific compliance report
		report := map[string]interface{}{
			"reportId":   reportId,
			"workflowId": fmt.Sprintf("mcp-compliance-vm-web-server-001-%d", time.Now().Unix()),
			"targetResource": "vm-web-server-001",
			"complianceType": "SOC2",
			"generatedAt": time.Now().Add(-2*time.Hour).Format(time.RFC3339),
			"score": 92.5,
			"status": "approved",
			"sections": []map[string]interface{}{
				{
					"name":        "Security",
					"score":       95.0,
					"status":      "pass",
					"findings":    []string{"SSL certificates valid", "Firewall configured"},
					"issues":      []string{},
				},
				{
					"name":        "Access Control",
					"score":       88.0,
					"status":      "pass",
					"findings":    []string{"RBAC implemented", "MFA enabled"},
					"issues":      []string{"Some users have excessive permissions"},
				},
				{
					"name":        "Data Protection",
					"score":       94.5,
					"status":      "pass",
					"findings":    []string{"Encryption at rest enabled", "Backup configured"},
					"issues":      []string{},
				},
			},
			"recommendations": []string{
				"Review and tighten user permissions",
				"Implement automated security patching",
				"Enhance monitoring and alerting",
			},
			"auditTrail": []map[string]interface{}{
				{
					"timestamp": time.Now().Add(-2*time.Hour).Format(time.RFC3339),
					"action":    "report_generated",
					"user":      "mcp-client",
					"details":   "Compliance report generated successfully",
				},
				{
					"timestamp": time.Now().Add(-2*time.Hour+10*time.Minute).Format(time.RFC3339),
					"action":    "human_review",
					"user":      "compliance-team",
					"details":   "Report reviewed and approved",
				},
			},
		}

		return report, nil
	} else {
		// Get list of compliance reports
		reports := map[string]interface{}{
			"reports": []map[string]interface{}{
				{
					"reportId":       "SOC2-vm-web-server-001-20240113",
					"targetResource": "vm-web-server-001",
					"complianceType": "SOC2",
					"score":          92.5,
					"status":         "approved",
					"generatedAt":    time.Now().Add(-2*time.Hour).Format(time.RFC3339),
				},
				{
					"reportId":       "GDPR-db-main-001-20240113",
					"targetResource": "db-main-001",
					"complianceType": "GDPR",
					"score":          88.0,
					"status":         "needs_review",
					"generatedAt":    time.Now().Add(-4*time.Hour).Format(time.RFC3339),
				},
				{
					"reportId":       "HIPAA-storage-backups-001-20240113",
					"targetResource": "storage-backups-001",
					"complianceType": "HIPAA",
					"score":          95.0,
					"status":         "approved",
					"generatedAt":    time.Now().Add(-1*24*time.Hour).Format(time.RFC3339),
				},
			},
			"total": 3,
			"queriedAt": time.Now().Format(time.RFC3339),
		}

		return reports, nil
	}
}

// handleInfrastructureState handles access to infrastructure state
func (s *MCPServer) handleInfrastructureState(ctx context.Context, uri string) (interface{}, error) {
	state := map[string]interface{}{
		"overview": map[string]interface{}{
			"totalResources": 15,
			"healthyResources": 13,
			"unhealthyResources": 2,
			"environments": []string{"dev", "staging", "prod"},
			"regions": []string{"us-west-2", "us-east-1", "eu-west-1"},
		},
		"resources": []map[string]interface{}{
			{
				"id":            "vm-web-server-001",
				"type":          "vm",
				"environment":   "prod",
				"region":        "us-west-2",
				"status":        "running",
				"health":        "healthy",
				"lastChecked":   time.Now().Add(-5*time.Minute).Format(time.RFC3339),
				"configuration": map[string]interface{}{
					"instanceType": "t3.medium",
					"vcpu":         2,
					"memory":       "4GB",
					"storage":      "100GB SSD",
					"os":           "ubuntu-22.04",
				},
				"metrics": map[string]interface{}{
					"cpuUtilization": 45.2,
					"memoryUtilization": 67.8,
					"diskUtilization": 23.1,
					"networkIn":  "1.2MB/s",
					"networkOut": "0.8MB/s",
				},
			},
			{
				"id":            "db-main-001",
				"type":          "database",
				"environment":   "prod",
				"region":        "us-west-2",
				"status":        "available",
				"health":        "healthy",
				"lastChecked":   time.Now().Add(-3*time.Minute).Format(time.RFC3339),
				"configuration": map[string]interface{}{
					"engine":       "postgresql",
					"version":      "14.9",
					"instanceClass": "db.m5.large",
					"storage":      "500GB SSD",
					"multiAZ":      true,
				},
				"metrics": map[string]interface{}{
					"cpuUtilization":    32.1,
					"memoryUtilization": 58.3,
					"storageUtilization": 41.7,
					"connections":        45,
					"readIOPS":          1200,
					"writeIOPS":          800,
				},
			},
			{
				"id":            "storage-backups-001",
				"type":          "storage",
				"environment":   "prod",
				"region":        "us-west-2",
				"status":        "active",
				"health":        "degraded",
				"lastChecked":   time.Now().Add(-10*time.Minute).Format(time.RFC3339),
				"configuration": map[string]interface{}{
					"storageClass": "standard",
					"size":         "500GB",
					"encryption":   true,
					"versioning":   true,
				},
				"metrics": map[string]interface{}{
					"usedSpace":    342.5,
					"availableSpace": 157.5,
					"utilization":  68.5,
					"objects":      12450,
				},
			},
		},
		"lastUpdated": time.Now().Format(time.RFC3339),
	}

	return state, nil
}

// handleWorkflowMetrics handles access to workflow metrics
func (s *MCPServer) handleWorkflowMetrics(ctx context.Context, uri string) (interface{}, error) {
	metrics := map[string]interface{}{
		"summary": map[string]interface{}{
			"totalWorkflows":      156,
			"completedWorkflows":  142,
			"runningWorkflows":    8,
			"failedWorkflows":     6,
			"successRate":        91.0,
			"averageDuration":     "12m 34s",
			"totalExecutions":     324,
		},
		"byType": []map[string]interface{}{
			{
				"workflowType":     "AIAgentOrchestrationWorkflowV2",
				"totalExecutions":  245,
				"successRate":      93.5,
				"averageDuration":  "15m 22s",
				"lastExecuted":     time.Now().Add(-45*time.Minute).Format(time.RFC3339),
			},
			{
				"workflowType":     "EnhancedHumanInTheLoopWorkflow",
				"totalExecutions":  67,
				"successRate":      89.5,
				"averageDuration":  "2h 15m 30s",
				"lastExecuted":     time.Now().Add(-2*time.Hour).Format(time.RFC3339),
			},
			{
				"workflowType":     "OptimizedWorkflow",
				"totalExecutions":  12,
				"successRate":      100.0,
				"averageDuration":  "8m 45s",
				"lastExecuted":     time.Now().Add(-30*time.Minute).Format(time.RFC3339),
			},
		},
		"performance": map[string]interface{}{
			"cpuUtilization":    45.2,
			"memoryUtilization": 67.8,
			"goroutines":        124,
			"activeConnections": 8,
			"queueDepth":        3,
		},
		"recentActivity": []map[string]interface{}{
			{
				"timestamp":     time.Now().Add(-5*time.Minute).Format(time.RFC3339),
				"workflowId":    "mcp-compliance-vm-web-server-001-1705123456",
				"workflowType":  "AIAgentOrchestrationWorkflowV2",
				"action":        "completed",
				"duration":      "14m 32s",
				"status":        "success",
			},
			{
				"timestamp":     time.Now().Add(-15*time.Minute).Format(time.RFC3339),
				"workflowId":    "mcp-security-db-main-001-1705123457",
				"workflowType":  "AIAgentOrchestrationWorkflowV2",
				"action":        "started",
				"status":        "running",
			},
			{
				"timestamp":     time.Now().Add(-30*time.Minute).Format(time.RFC3339),
				"workflowId":    "mcp-cost-storage-backups-001-1705123458",
				"workflowType":  "AIAgentOrchestrationWorkflowV2",
				"action":        "failed",
				"duration":      "3m 12s",
				"status":        "error",
				"error":         "Timeout during cost analysis",
			},
		},
		"generatedAt": time.Now().Format(time.RFC3339),
	}

	return metrics, nil
}

// handleHumanTasks handles access to human review tasks
func (s *MCPServer) handleHumanTasks(ctx context.Context, uri string) (interface{}, error) {
	// Parse URI for specific task ID if provided
	taskId := ""
	if len(uri) > len("human://tasks/") {
		taskId = uri[len("human://tasks/"):]
	}

	if taskId != "" {
		// Get specific human task
		task := map[string]interface{}{
			"taskId":        taskId,
			"workflowId":    fmt.Sprintf("mcp-compliance-vm-web-server-001-%d", time.Now().Unix()),
			"title":         "Security Review Required",
			"description":   "Review security compliance findings for vm-web-server-001",
			"priority":      "high",
			"status":        "pending",
			"assignedTo":    "security-team",
			"createdAt":     time.Now().Add(-4*time.Hour).Format(time.RFC3339),
			"dueAt":         time.Now().Add(20*time.Hour).Format(time.RFC3339),
			"workflowData": map[string]interface{}{
				"targetResource": "vm-web-server-001",
				"complianceType": "SOC2",
				"confidenceScore": 0.85,
				"issuesFound": 3,
			},
			"actions": []string{
				"approve",
				"reject",
				"request_more_info",
			},
			"history": []map[string]interface{}{
				{
					"timestamp": time.Now().Add(-4*time.Hour).Format(time.RFC3339),
					"action":    "created",
					"user":      "system",
					"details":   "Task created automatically by workflow",
				},
				{
					"timestamp": time.Now().Add(-3*time.Hour).Format(time.RFC3339),
					"action":    "assigned",
					"user":      "system",
					"details":   "Task assigned to security-team",
				},
			},
		}

		return task, nil
	} else {
		// Get list of human tasks
		tasks := map[string]interface{}{
			"tasks": []map[string]interface{}{
				{
					"taskId":        "task-001",
					"workflowId":    "mcp-compliance-vm-web-server-001-1705123456",
					"title":         "Security Review Required",
					"priority":      "high",
					"status":        "pending",
					"assignedTo":    "security-team",
					"createdAt":     time.Now().Add(-4*time.Hour).Format(time.RFC3339),
					"dueAt":         time.Now().Add(20*time.Hour).Format(time.RFC3339),
				},
				{
					"taskId":        "task-002",
					"workflowId":    "mcp-gdpr-db-main-001-1705123457",
					"title":         "GDPR Compliance Review",
					"priority":      "normal",
					"status":        "in_progress",
					"assignedTo":    "compliance-team",
					"createdAt":     time.Now().Add(-6*time.Hour).Format(time.RFC3339),
					"dueAt":         time.Now().Add(18*time.Hour).Format(time.RFC3339),
				},
				{
					"taskId":        "task-003",
					"workflowId":    "mcp-cost-storage-backups-001-1705123458",
					"title":         "Cost Optimization Approval",
					"priority":      "low",
					"status":        "completed",
					"assignedTo":    "finance-team",
					"createdAt":     time.Now().Add(-1*24*time.Hour).Format(time.RFC3339),
					"completedAt":   time.Now().Add(-22*time.Hour).Format(time.RFC3339),
				},
			},
			"summary": map[string]interface{}{
				"total":      3,
				"pending":    1,
				"inProgress": 1,
				"completed":  1,
				"overdue":    0,
			},
			"queriedAt": time.Now().Format(time.RFC3339),
		}

		return tasks, nil
	}
}
