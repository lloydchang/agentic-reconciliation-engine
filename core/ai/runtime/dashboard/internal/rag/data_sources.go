package rag

import (
	"context"
	"database/sql"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// SQLiteMemorySource implements DataSource for SQLite agent memory
type SQLiteMemorySource struct {
	db *sql.DB
}

// NewSQLiteMemorySource creates a new SQLite memory source
func NewSQLiteMemorySource(db *sql.DB) *SQLiteMemorySource {
	return &SQLiteMemorySource{db: db}
}

// Search searches SQLite for relevant conversations
func (s *SQLiteMemorySource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Query conversations table (assuming it exists)
	rows, err := s.db.QueryContext(ctx, 
		`SELECT content, timestamp, metadata FROM conversations 
		 WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 10`, 
		"%"+query+"%")
	if err != nil {
		log.Printf("SQLite query failed: %v", err)
		return documents, nil
	}
	defer rows.Close()
	
	for rows.Next() {
		var content, timestamp string
		var metadata sql.NullString
		
		if err := rows.Scan(&content, &timestamp, &metadata); err != nil {
			continue
		}
		
		doc := Document{
			Content: content,
			Source:  "sqlite_memory",
			Type:    "conversation",
			Metadata: map[string]interface{}{
				"timestamp": timestamp,
			},
		}
		
		if metadata.Valid {
			doc.Metadata["raw_metadata"] = metadata.String
		}
		
		documents = append(documents, doc)
	}
	
	return documents, nil
}

// IsRelevant checks if SQLite memory is relevant for the query
func (s *SQLiteMemorySource) IsRelevant(query string) bool {
	keywords := []string{"agent", "memory", "conversation", "history", "previous", "past"}
	return containsAny(strings.ToLower(query), keywords)
}

// DocumentationSource implements DataSource for file system documentation
type DocumentationSource struct {
	basePath string
}

// NewDocumentationSource creates a new documentation source
func NewDocumentationSource() *DocumentationSource {
	return &DocumentationSource{
		basePath: "/app/docs", // Adjust based on actual path in container
	}
}

// Search searches documentation files
func (d *DocumentationSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Define documentation files to index
	docFiles := []string{
		"AGENTS.md",
		"README.md", 
		"RAG-QWEN-INTEGRATION-PLAN.md",
		"COMPREHENSIVE-RAG-IMPLEMENTATION-PLAN.md",
	}
	
	for _, file := range docFiles {
		content, err := d.readDocumentationFile(file)
		if err != nil {
			log.Printf("Failed to read %s: %v", file, err)
			continue
		}
		
		documents = append(documents, Document{
			Content: content,
			Source:  file,
			Type:    "documentation",
			Metadata: map[string]interface{}{
				"file":     file,
				"indexed":  time.Now().Format(time.RFC3339),
			},
		})
	}
	
	return documents, nil
}

// readDocumentationFile reads a documentation file
func (d *DocumentationSource) readDocumentationFile(filename string) (string, error) {
	// Try multiple possible paths
	paths := []string{
		filepath.Join(d.basePath, filename),
		filepath.Join("/app", filename),
		filepath.Join("/workspace", filename),
		filename,
	}
	
	for _, path := range paths {
		content, err := ioutil.ReadFile(path)
		if err == nil {
			return string(content), nil
		}
	}
	
	return "", fmt.Errorf("documentation file %s not found", filename)
}

// IsRelevant checks if documentation is relevant (always true for now)
func (d *DocumentationSource) IsRelevant(query string) bool {
	return true // Documentation is always relevant
}

// KubernetesSource implements DataSource for Kubernetes API
type KubernetesSource struct {
	// In production, this would use the Kubernetes client
}

// NewKubernetesSource creates a new Kubernetes source
func NewKubernetesSource() *KubernetesSource {
	return &KubernetesSource{}
}

// Search searches Kubernetes for relevant information
func (k *KubernetesSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Mock Kubernetes data for now
	// In production, this would query the actual Kubernetes API
	mockData := []struct {
		content string
		source  string
	}{
		{
			"Cluster Status: All nodes are ready. CPU usage: 45%. Memory usage: 62%. Storage: 78% used.",
			"cluster_status",
		},
		{
			"Pod Status: 15 pods running, 2 pods pending, 0 pods failed. Recent restarts: cost-optimizer-agent (3 times).",
			"pod_status",
		},
		{
			"Deployment Status: All deployments are healthy. Latest deployments: agent-dashboard (v1.2.0), dashboard-api (v1.1.0).",
			"deployment_status",
		},
	}
	
	for _, data := range mockData {
		if strings.Contains(strings.ToLower(query), strings.ToLower(data.source)) {
			documents = append(documents, Document{
				Content: data.content,
				Source:  "kubernetes",
				Type:    data.source,
				Metadata: map[string]interface{}{
					"timestamp": time.Now().Format(time.RFC3339),
					"namespace": "ai-infrastructure",
				},
			})
		}
	}
	
	return documents, nil
}

// IsRelevant checks if Kubernetes is relevant for the query
func (k *KubernetesSource) IsRelevant(query string) bool {
	keywords := []string{"cluster", "pod", "deployment", "service", "namespace", "node", "k8s", "kube"}
	return containsAny(strings.ToLower(query), keywords)
}

// DashboardSource implements DataSource for dashboard APIs
type DashboardSource struct {
	// In production, this would query the actual dashboard APIs
}

// NewDashboardSource creates a new dashboard source
func NewDashboardSource() *DashboardSource {
	return &DashboardSource{}
}

// Search searches dashboard for relevant metrics and status
func (d *DashboardSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Mock dashboard data
	mockData := []struct {
		content string
		source  string
	}{
		{
			"System Metrics: CPU usage 45%, Memory 62%, Disk 78%. Response time: 120ms. Error rate: 0.1%.",
			"system_metrics",
		},
		{
			"Agent Status: 5 agents running, 1 agent failing (cost-optimizer). Recent errors: ImagePullBackOff.",
			"agent_status",
		},
		{
			"Activity Log: 23 skill executions in last hour. Success rate: 95.6%. Average execution time: 2.3s.",
			"activity_log",
		},
	}
	
	for _, data := range mockData {
		if strings.Contains(strings.ToLower(query), strings.ToLower(data.source)) {
			documents = append(documents, Document{
				Content: data.content,
				Source:  "dashboard",
				Type:    data.source,
				Metadata: map[string]interface{}{
					"timestamp": time.Now().Format(time.RFC3339),
				},
			})
		}
	}
	
	return documents, nil
}

// IsRelevant checks if dashboard is relevant for the query
func (d *DashboardSource) IsRelevant(query string) bool {
	keywords := []string{"metric", "monitor", "dashboard", "status", "performance", "analytics"}
	return containsAny(strings.ToLower(query), keywords)
}

// K8sGPTSource implements DataSource for K8sGPT analysis
type K8sGPTSource struct {
	client  *http.Client
	baseURL string
}

// NewK8sGPTSource creates a new K8sGPT source
func NewK8sGPTSource(baseURL string) *K8sGPTSource {
	return &K8sGPTSource{
		client:  &http.Client{Timeout: 30 * time.Second},
		baseURL: baseURL,
	}
}

// Search searches K8sGPT for cluster analysis
func (k *K8sGPTSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Mock K8sGPT analysis
	// In production, this would call the actual K8sGPT API
	mockAnalysis := Document{
		Content: "K8sGPT Analysis: Identified 3 issues in the cluster:\n1. Pod 'cost-optimizer-agent' is in ImagePullBackOff state - likely container image not available\n2. High memory usage on node 'worker-1' (85%) - consider scaling or optimizing workloads\n3. Service 'agent-dashboard' has no endpoints - check pod selector configuration",
		Source:  "k8sgpt",
		Type:    "cluster_analysis",
		Metadata: map[string]interface{}{
			"issues_found": 3,
			"severity":     "medium",
			"timestamp":    time.Now().Format(time.RFC3339),
		},
	}
	
	documents = append(documents, mockAnalysis)
	return documents, nil
}

// IsRelevant checks if K8sGPT is relevant for the query
func (k *K8sGPTSource) IsRelevant(query string) bool {
	keywords := []string{"problem", "issue", "error", "troubleshoot", "analyze", "diagnose", "health"}
	return containsAny(strings.ToLower(query), keywords)
}

// FluxSource implements DataSource for Flux CD
type FluxSource struct {
	// In production, this would query Flux Kubernetes resources
}

// NewFluxSource creates a new Flux source
func NewFluxSource() *FluxSource {
	return &FluxSource{}
}

// Search searches Flux for GitOps status
func (f *FluxSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Mock Flux data
	mockData := Document{
		Content: "Flux CD Status: All Kustomizations are healthy.\n- gitops-system: Last applied revision main@sha1:abc123\n- ai-infrastructure: Sync status Ready\n- monitoring: Sync status Ready\n\nRecent commits:\n- Update dashboard deployment (2 hours ago)\n- Add new agent skill (5 hours ago)\n- Fix memory leak (1 day ago)",
		Source:  "flux",
		Type:    "gitops_status",
		Metadata: map[string]interface{}{
			"kustomizations": 3,
			"healthy":        true,
			"last_sync":      time.Now().Add(-2 * time.Hour).Format(time.RFC3339),
		},
	}
	
	documents = append(documents, mockData)
	return documents, nil
}

// IsRelevant checks if Flux is relevant for the query
func (f *FluxSource) IsRelevant(query string) bool {
	keywords := []string{"flux", "gitops", "deployment", "sync", "manifest", "kustomize", "git"}
	return containsAny(strings.ToLower(query), keywords)
}

// ArgoCDSource implements DataSource for Argo CD
type ArgoCDSource struct {
	baseURL string
}

// NewArgoCDSource creates a new Argo CD source
func NewArgoCDSource(baseURL string) *ArgoCDSource {
	return &ArgoCDSource{baseURL: baseURL}
}

// Search searches Argo CD for application status
func (a *ArgoCDSource) Search(ctx context.Context, query string) ([]Document, error) {
	var documents []Document
	
	// Mock Argo CD data
	mockData := Document{
		Content: "Argo CD Status: All applications are healthy.\n- agent-dashboard: Synced, Healthy (v1.2.0)\n- dashboard-api: Synced, Healthy (v1.1.0)\n- monitoring-stack: Synced, Healthy (latest)\n\nRecent deployments:\n- agent-dashboard rolled out successfully (2 hours ago)\n- dashboard-api updated (6 hours ago)",
		Source:  "argocd",
		Type:    "application_status",
		Metadata: map[string]interface{}{
			"applications": 3,
			"healthy":      true,
			"last_deploy":  time.Now().Add(-2 * time.Hour).Format(time.RFC3339),
		},
	}
	
	documents = append(documents, mockData)
	return documents, nil
}

// IsRelevant checks if Argo CD is relevant for the query
func (a *ArgoCDSource) IsRelevant(query string) bool {
	keywords := []string{"argo", "application", "app", "rollout", "canary", "blue-green", "progressive"}
	return containsAny(strings.ToLower(query), keywords)
}

// Helper function
func containsAny(query string, keywords []string) bool {
	for _, keyword := range keywords {
		if strings.Contains(query, keyword) {
			return true
		}
	}
	return false
}

// InitDataSources initializes all available data sources
func InitDataSources(db *sql.DB) []DataSource {
	var sources []DataSource
	
	// Add SQLite memory source if database is available
	if db != nil {
		sources = append(sources, NewSQLiteMemorySource(db))
	}
	
	// Add static documentation sources
	sources = append(sources, 
		NewStaticSource("static"),
		NewK8sGPTSource("k8sgpt"),
		NewFluxSource("flux"),
		NewArgoCDSource("argocd"),
	)
	
	// Add evaluation source if API is available
	if evaluationURL := getEvaluationAPIURL(); evaluationURL != "" {
		sources = append(sources, NewEvaluationSource(evaluationURL))
	}
	
	return sources
}

// getEvaluationAPIURL gets the evaluation API URL from environment or default
func getEvaluationAPIURL() string {
	// Check environment variable first
	if url := os.Getenv("EVALUATION_API_URL"); url != "" {
		return url
	}
	
	// Default to localhost:8081 for development
	return "http://localhost:8081"
}
