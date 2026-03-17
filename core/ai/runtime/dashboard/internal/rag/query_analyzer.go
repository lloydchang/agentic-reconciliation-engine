package rag

import (
	"strings"
)

// QueryAnalyzer determines which data sources are relevant for a query
type QueryAnalyzer struct {
	patterns map[string][]string
}

// NewQueryAnalyzer creates a new query analyzer
func NewQueryAnalyzer() *QueryAnalyzer {
	return &QueryAnalyzer{
		patterns: map[string][]string{
			"k8sgpt": {
				"problem", "issue", "error", "troubleshoot",
				"analyze", "diagnose", "health check",
				"resource", "pod", "deployment", "service",
				"why", "what's wrong", "fix", "optimize",
				"cluster", "node", "performance", "bottleneck",
			},
			"flux": {
				"flux", "gitops", "deployment", "sync",
				"manifest", "kustomize", "helm",
				"repository", "branch", "commit",
				"drift", "reconciliation", "status",
				"git", "source", "kustomization",
			},
			"argocd": {
				"argo", "application", "app", "rollout",
				"canary", "blue-green", "progressive",
				"health", "sync status", "deployment strategy",
				"argocd", "cd", "continuous deployment",
			},
			"sqlite_memory": {
				"agent", "memory", "conversation", "history",
				"previous", "past", "learned", "experience",
				"remember", "recall", "pattern", "before",
			},
			"kubernetes": {
				"cluster", "pod", "deployment", "service",
				"namespace", "node", "resource", "status",
				"health", "running", "failed", "crash",
				"k8s", "kube", "container", "ingress",
			},
			"temporal": {
				"workflow", "history", "execution", "run",
				"skill", "activity", "task", "process",
				"orchestration", "temporal", "job", "step",
			},
			"dashboard": {
				"metric", "monitor", "alert", "performance",
				"dashboard", "ui", "interface", "view",
				"statistics", "analytics", "report", "status",
			},
		},
	}
}

// Analyze determines which data sources are relevant for a query
func (qa *QueryAnalyzer) Analyze(query string) []string {
	var neededSources []string
	queryLower := strings.ToLower(query)
	
	// Check each source pattern
	for source, keywords := range qa.patterns {
		if qa.containsAny(queryLower, keywords) {
			neededSources = append(neededSources, source)
		}
	}
	
	// Always include documentation for static knowledge
	neededSources = append(neededSources, "documentation")
	
	return neededSources
}

// containsAny checks if the query contains any of the keywords
func (qa *QueryAnalyzer) containsAny(query string, keywords []string) bool {
	for _, keyword := range keywords {
		if strings.Contains(query, keyword) {
			return true
		}
	}
	return false
}
