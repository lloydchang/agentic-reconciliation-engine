package rag

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"
)

// Document represents a document from any data source
type Document struct {
	Content  string                 `json:"content"`
	Source   string                 `json:"source"`
	Type     string                 `json:"type"`
	Metadata map[string]interface{} `json:"metadata"`
}

// RAGResponse represents the response from RAG query
type RAGResponse struct {
	Answer   string     `json:"answer"`
	Sources  []Document `json:"sources"`
	Model    string     `json:"model"`
	Metadata map[string]interface{} `json:"metadata"`
}

// DataSource interface for all data sources
type DataSource interface {
	Search(ctx context.Context, query string) ([]Document, error)
	IsRelevant(query string) bool
}

// RAGService main service
type RAGService struct {
	db           *sql.DB
	qwenClient   *QwenClient
	dataSources  map[string]DataSource
	queryAnalyzer *QueryAnalyzer
}

// NewRAGService creates a new RAG service
func NewRAGService(db *sql.DB, qwenClient *QwenClient) *RAGService {
	service := &RAGService{
		db:          db,
		qwenClient:  qwenClient,
		dataSources: make(map[string]DataSource),
		queryAnalyzer: NewQueryAnalyzer(),
	}
	
	// Initialize data sources
	service.initializeDataSources()
	
	return service
}

// initializeDataSources sets up all available data sources
func (r *RAGService) initializeDataSources() {
	// SQLite Memory Source
	r.dataSources["sqlite_memory"] = NewSQLiteMemorySource(r.db)
	
	// Documentation Source (file system)
	r.dataSources["documentation"] = NewDocumentationSource()
	
	// Kubernetes Source
	r.dataSources["kubernetes"] = NewKubernetesSource()
	
	// Dashboard APIs Source
	r.dataSources["dashboard"] = NewDashboardSource()
	
	// K8sGPT Source (if available)
	if k8sgptURL := getEnv("K8SGPT_URL", ""); k8sgptURL != "" {
		r.dataSources["k8sgpt"] = NewK8sGPTSource(k8sgptURL)
	}
	
	// Flux CD Source
	r.dataSources["flux"] = NewFluxSource()
	
	// Argo CD Source
	if argocdURL := getEnv("ARGOCD_URL", ""); argocdURL != "" {
		r.dataSources["argocd"] = NewArgoCDSource(argocdURL)
	}
}

// Query processes a RAG query
func (r *RAGService) Query(ctx context.Context, question string) (*RAGResponse, error) {
	startTime := time.Now()
	
	// 1. Analyze query to determine needed sources
	sources := r.queryAnalyzer.Analyze(question)
	
	// 2. Build context from multiple sources
	context, err := r.buildContext(ctx, sources, question)
	if err != nil {
		return nil, fmt.Errorf("failed to build context: %w", err)
	}
	
	// 3. Generate response with Qwen
	response, err := r.qwenClient.Generate(ctx, question, context)
	if err != nil {
		return nil, fmt.Errorf("failed to generate response: %w", err)
	}
	
	// 4. Format response
	ragResponse := &RAGResponse{
		Answer:   response.Content,
		Sources:  context,
		Model:    response.Model,
		Metadata: map[string]interface{}{
			"processing_time":    time.Since(startTime).Milliseconds(),
			"sources_queried":    sources,
			"context_count":      len(context),
			"query":             question,
		},
	}
	
	return ragResponse, nil
}

// buildContext retrieves and combines documents from multiple sources
func (r *RAGService) buildContext(ctx context.Context, sources []string, query string) ([]Document, error) {
	var allDocuments []Document
	var mu sync.Mutex
	var wg sync.WaitGroup
	
	// Parallel data retrieval from all sources
	for _, source := range sources {
		if dataSource, exists := r.dataSources[source]; exists {
			wg.Add(1)
			go func(src string, ds DataSource) {
				defer wg.Done()
				
				docs, err := ds.Search(ctx, query)
				if err == nil && len(docs) > 0 {
					mu.Lock()
					allDocuments = append(allDocuments, docs...)
					mu.Unlock()
				}
			}(source, dataSource)
		}
	}
	
	wg.Wait()
	
	// Rank and limit documents
	return r.rankDocuments(query, allDocuments, 10), nil
}

// rankDocuments ranks documents by relevance and limits count
func (r *RAGService) rankDocuments(query string, documents []Document, maxCount int) []Document {
	// Simple keyword-based ranking for now
	// In production, use semantic similarity with embeddings
	queryWords := strings.Fields(strings.ToLower(query))
	
	var scoredDocs []struct {
		doc    Document
		score  int
	}
	
	for _, doc := range documents {
		score := 0
		content := strings.ToLower(doc.Content)
		
		// Count matching words
		for _, word := range queryWords {
			if strings.Contains(content, word) {
				score++
			}
		}
		
		scoredDocs = append(scoredDocs, struct {
			doc    Document
			score  int
		}{doc, score})
	}
	
	// Sort by score (descending)
	for i := 0; i < len(scoredDocs); i++ {
		for j := i + 1; j < len(scoredDocs); j++ {
			if scoredDocs[i].score < scoredDocs[j].score {
				scoredDocs[i], scoredDocs[j] = scoredDocs[j], scoredDocs[i]
			}
		}
	}
	
	// Return top documents
	var result []Document
	for i, scored := range scoredDocs {
		if i >= maxCount {
			break
		}
		result = append(result, scored.doc)
	}
	
	return result
}

// IndexDocumentation indexes documentation files
func (r *RAGService) IndexDocumentation(ctx context.Context) error {
	log.Println("Starting documentation indexing...")
	
	docSource := r.dataSources["documentation"]
	if docSource == nil {
		return fmt.Errorf("documentation source not available")
	}
	
	// Get all documentation
	docs, err := docSource.Search(ctx, "")
	if err != nil {
		return fmt.Errorf("failed to load documentation: %w", err)
	}
	
	// Clear existing documents
	_, err = r.db.ExecContext(ctx, "DELETE FROM rag_documents WHERE source_type = 'documentation'")
	if err != nil {
		return fmt.Errorf("failed to clear existing documents: %w", err)
	}
	
	// Insert new documents
	for _, doc := range docs {
		metadataJSON, _ := json.Marshal(doc.Metadata)
		
		_, err := r.db.ExecContext(ctx, 
			`INSERT INTO rag_documents (content, source_type, source_id, metadata) 
			 VALUES ($1, $2, $3, $4)`,
			doc.Content, doc.Source, doc.Type, metadataJSON)
		
		if err != nil {
			log.Printf("Failed to insert document %s: %v", doc.Source, err)
		}
	}
	
	log.Printf("Indexed %d documentation documents", len(docs))
	return nil
}

// Helper function to get environment variable
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
