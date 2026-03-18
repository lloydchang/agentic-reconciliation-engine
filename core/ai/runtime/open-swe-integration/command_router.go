// CommandRouter handles routing of commands to appropriate GitOps skills
package main

import (
	"fmt"
	"strings"
)

// CommandRouter routes commands to GitOps skills
type CommandRouter struct {
	commandMappings map[string]string
	linearMappings  map[string]string
}

// NewCommandRouter creates a new command router
func NewCommandRouter() *CommandRouter {
	return &CommandRouter{
		commandMappings: map[string]string{
			"deploy":      "deployment-strategy",
			"deployment":  "deployment-strategy",
			"optimize":    "optimize-costs",
			"cost":        "optimize-costs",
			"secure":      "analyze-security",
			"security":    "analyze-security",
			"scale":       "scale-resources",
			"scaling":     "scale-resources",
			"backup":      "orchestrate-backups",
			"backups":     "orchestrate-backups",
			"monitor":     "check-cluster-health",
			"health":      "check-cluster-health",
			"status":      "check-cluster-health",
			"troubleshoot": "diagnose-network",
			"network":     "diagnose-network",
			"certificate": "manage-certificates",
			"certs":       "manage-certificates",
			"database":    "maintain-databases",
			"db":          "maintain-databases",
			"cluster":     "manage-kubernetes-cluster",
			"kubernetes":  "manage-kubernetes-cluster",
			"k8s":         "manage-kubernetes-cluster",
			"compliance":  "generate-compliance-report",
			"audit":       "audit-security-events",
			"secrets":     "rotate-secrets",
			"certificates": "manage-certificates",
		},
		linearMappings: map[string]string{
			// Title-based routing for Linear issues
			"deploy":        "deployment-strategy",
			"optimize":      "optimize-costs",
			"security":      "analyze-security",
			"scale":         "scale-resources",
			"backup":        "orchestrate-backups",
			"monitor":       "check-cluster-health",
			"troubleshoot":  "diagnose-network",
			"certificate":   "manage-certificates",
			"database":      "maintain-databases",
			"cluster":       "manage-kubernetes-cluster",
			"compliance":    "generate-compliance-report",
			"audit":         "audit-security-events",
			"secrets":       "rotate-secrets",
		},
	}
}

// RouteCommand routes a Slack command to a GitOps skill
func (cr *CommandRouter) RouteCommand(action string) (string, error) {
	action = strings.ToLower(strings.TrimSpace(action))

	skill, exists := cr.commandMappings[action]
	if !exists {
		return "", fmt.Errorf("unknown command: %s", action)
	}

	return skill, nil
}

// RouteLinearIssue routes a Linear issue to a GitOps skill based on content analysis
func (cr *CommandRouter) RouteLinearIssue(command *LinearCommand) (string, error) {
	// First, try to match based on title keywords
	title := strings.ToLower(command.Title)
	for keyword, skill := range cr.linearMappings {
		if strings.Contains(title, keyword) {
			return skill, nil
		}
	}

	// Then try description
	description := strings.ToLower(command.Description)
	for keyword, skill := range cr.linearMappings {
		if strings.Contains(description, keyword) {
			return skill, nil
		}
	}

	// Try labels
	for _, label := range command.Labels {
		label = strings.ToLower(label)
		for keyword, skill := range cr.linearMappings {
			if strings.Contains(label, keyword) {
				return skill, nil
			}
		}
	}

	// Try comments
	for _, comment := range command.Comments {
		comment = strings.ToLower(comment)
		for keyword, skill := range cr.linearMappings {
			if strings.Contains(comment, keyword) {
				return skill, nil
			}
		}
	}

	// Default fallback based on priority or content analysis
	if cr.isUrgentIssue(command) {
		return "check-cluster-health", nil // Quick health check for urgent issues
	}

	// Generic infrastructure management
	return "manage-infrastructure", nil
}

// isUrgentIssue determines if an issue requires immediate attention
func (cr *CommandRouter) isUrgentIssue(command *LinearCommand) bool {
	// Check priority
	if command.Priority == "high" || command.Priority == "urgent" {
		return true
	}

	// Check labels for urgency indicators
	for _, label := range command.Labels {
		label = strings.ToLower(label)
		if strings.Contains(label, "urgent") ||
		   strings.Contains(label, "critical") ||
		   strings.Contains(label, "p0") ||
		   strings.Contains(label, "emergency") {
			return true
		}
	}

	// Check content for urgency keywords
	content := strings.ToLower(command.Title + " " + command.Description)
	urgentKeywords := []string{
		"down", "broken", "critical", "emergency", "urgent",
		"failing", "unavailable", "outage", "incident",
		"security breach", "data loss", "production down",
	}

	for _, keyword := range urgentKeywords {
		if strings.Contains(content, keyword) {
			return true
		}
	}

	return false
}

// GetSkillParameters extracts skill-specific parameters from commands
func (cr *CommandRouter) GetSkillParameters(skillName string, command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch skillName {
	case "deployment-strategy":
		params = cr.extractDeploymentParams(command)
	case "optimize-costs":
		params = cr.extractCostOptimizationParams(command)
	case "analyze-security":
		params = cr.extractSecurityParams(command)
	case "scale-resources":
		params = cr.extractScalingParams(command)
	case "orchestrate-backups":
		params = cr.extractBackupParams(command)
	case "check-cluster-health":
		params = cr.extractHealthCheckParams(command)
	case "diagnose-network":
		params = cr.extractNetworkParams(command)
	case "manage-certificates":
		params = cr.extractCertificateParams(command)
	case "maintain-databases":
		params = cr.extractDatabaseParams(command)
	case "manage-kubernetes-cluster":
		params = cr.extractClusterParams(command)
	default:
		params = cr.extractGenericParams(command)
	}

	return params
}

// extractDeploymentParams extracts parameters for deployment operations
func (cr *CommandRouter) extractDeploymentParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "environment", "env":
				params["environment"] = value
			case "namespace", "ns":
				params["namespace"] = value
			case "service", "svc":
				params["service"] = value
			case "version", "tag":
				params["version"] = value
			}
		}
	case *LinearCommand:
		// Extract from title, description, and labels
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "staging") {
			params["environment"] = "staging"
		} else if strings.Contains(content, "production") {
			params["environment"] = "production"
		}

		// Look for service names in labels
		for _, label := range cmd.Labels {
			if strings.HasPrefix(strings.ToLower(label), "service:") {
				params["service"] = strings.TrimPrefix(label, "service:")
			}
		}
	}

	// Set defaults
	if _, exists := params["environment"]; !exists {
		params["environment"] = "staging"
	}

	return params
}

// extractCostOptimizationParams extracts parameters for cost optimization
func (cr *CommandRouter) extractCostOptimizationParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "budget", "limit":
				params["budget_limit"] = value
			case "aggressive":
				params["optimization_level"] = "aggressive"
			case "conservative":
				params["optimization_level"] = "conservative"
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "aggressive") {
			params["optimization_level"] = "aggressive"
		} else {
			params["optimization_level"] = "moderate"
		}
	}

	if _, exists := params["optimization_level"]; !exists {
		params["optimization_level"] = "moderate"
	}

	return params
}

// extractSecurityParams extracts parameters for security analysis
func (cr *CommandRouter) extractSecurityParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "scope", "target":
				params["scope"] = value
			case "deep":
				params["scan_depth"] = "deep"
			case "quick":
				params["scan_depth"] = "quick"
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "deep") || strings.Contains(content, "comprehensive") {
			params["scan_depth"] = "deep"
		} else {
			params["scan_depth"] = "standard"
		}
	}

	if _, exists := params["scan_depth"]; !exists {
		params["scan_depth"] = "standard"
	}

	return params
}

// extractScalingParams extracts parameters for resource scaling
func (cr *CommandRouter) extractScalingParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "target", "service":
				params["target_service"] = value
			case "amount", "scale":
				params["scale_amount"] = value
			case "replicas", "count":
				params["replica_count"] = value
			}
		}
	case *LinearCommand:
		// Extract scaling information from content
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		// This would need more sophisticated parsing
		params["scale_type"] = "horizontal"
	}

	return params
}

// extractBackupParams extracts parameters for backup operations
func (cr *CommandRouter) extractBackupParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "type", "kind":
				params["backup_type"] = value
			case "retention", "keep":
				params["retention_days"] = value
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "database") {
			params["backup_type"] = "database"
		} else if strings.Contains(content, "volume") || strings.Contains(content, "pv") {
			params["backup_type"] = "volume"
		} else {
			params["backup_type"] = "full"
		}
	}

	if _, exists := params["backup_type"]; !exists {
		params["backup_type"] = "full"
	}

	return params
}

// extractHealthCheckParams extracts parameters for health checks
func (cr *CommandRouter) extractHealthCheckParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "scope", "target":
				params["check_scope"] = value
			case "detailed", "verbose":
				params["detailed_output"] = true
			}
		}
	case *LinearCommand:
		// Health checks are usually comprehensive for urgent issues
		if cr.isUrgentIssue(cmd) {
			params["check_scope"] = "full"
			params["detailed_output"] = true
		}
	}

	return params
}

// extractNetworkParams extracts parameters for network diagnostics
func (cr *CommandRouter) extractNetworkParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "target", "service":
				params["target_service"] = value
			case "namespace", "ns":
				params["namespace"] = value
			case "deep":
				params["diagnostic_level"] = "deep"
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "connectivity") {
			params["diagnostic_type"] = "connectivity"
		} else if strings.Contains(content, "dns") {
			params["diagnostic_type"] = "dns"
		} else {
			params["diagnostic_type"] = "general"
		}
	}

	return params
}

// extractCertificateParams extracts parameters for certificate management
func (cr *CommandRouter) extractCertificateParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "service", "domain":
				params["certificate_domain"] = value
			case "type", "kind":
				params["certificate_type"] = value
			}
		}
	case *LinearCommand:
		// Extract domain/service from content
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		// This would need more sophisticated parsing to extract domains
		params["certificate_type"] = "tls"
	}

	return params
}

// extractDatabaseParams extracts parameters for database maintenance
func (cr *CommandRouter) extractDatabaseParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "database", "db":
				params["database_name"] = value
			case "operation", "action":
				params["maintenance_operation"] = value
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "backup") {
			params["maintenance_operation"] = "backup"
		} else if strings.Contains(content, "optimize") || strings.Contains(content, "tune") {
			params["maintenance_operation"] = "optimize"
		} else {
			params["maintenance_operation"] = "maintenance"
		}
	}

	return params
}

// extractClusterParams extracts parameters for cluster management
func (cr *CommandRouter) extractClusterParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	switch cmd := command.(type) {
	case *SlackCommand:
		for key, value := range cmd.Parameters {
			switch key {
			case "operation", "action":
				params["cluster_operation"] = value
			case "nodes", "count":
				params["node_count"] = value
			}
		}
	case *LinearCommand:
		content := strings.ToLower(cmd.Title + " " + cmd.Description)
		if strings.Contains(content, "upgrade") {
			params["cluster_operation"] = "upgrade"
		} else if strings.Contains(content, "scale") {
			params["cluster_operation"] = "scale"
		} else {
			params["cluster_operation"] = "maintenance"
		}
	}

	return params
}

// extractGenericParams provides default parameters for unmapped skills
func (cr *CommandRouter) extractGenericParams(command interface{}) map[string]interface{} {
	params := make(map[string]interface{})

	// Add basic metadata
	switch cmd := command.(type) {
	case *SlackCommand:
		params["source"] = "slack"
		params["user"] = cmd.User
		params["channel"] = cmd.Channel
	case *LinearCommand:
		params["source"] = "linear"
		params["issue_id"] = cmd.IssueID
		params["assignee"] = cmd.Assignee
		params["priority"] = cmd.Priority
	}

	params["timestamp"] = time.Now().Unix()
	params["execution_mode"] = "automated"

	return params
}
