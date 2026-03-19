package api

import (
	"encoding/json"
	"net/http"
	"os"

	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/rag"
)

// RAGHandler handles RAG API requests
type RAGHandler struct {
	ragService *rag.RAGService
}

// NewRAGHandler creates a new RAG handler
func NewRAGHandler(ragService *rag.RAGService) *RAGHandler {
	return &RAGHandler{
		ragService: ragService,
	}
}

// RAGQuery represents a RAG query request
type RAGQuery struct {
	Question string   `json:"question"`
	Sources  []string `json:"sources,omitempty"`
}

// RegisterRAGRoutes registers RAG API routes
func (h *RAGHandler) RegisterRAGRoutes(router *http.ServeMux) {
	router.HandleFunc("/api/v1/rag/query", h.HandleRAGQuery)
	router.HandleFunc("/api/v1/rag/index", h.HandleIndexDocumentation)
	router.HandleFunc("/api/v1/rag/status", h.HandleRAGStatus)
}

// handleRAGQuery handles RAG query requests
func (h *RAGHandler) HandleRAGQuery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var query RAGQuery
	if err := json.NewDecoder(r.Body).Decode(&query); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if query.Question == "" {
		http.Error(w, "Question is required", http.StatusBadRequest)
		return
	}

	// Process RAG query
	response, err := h.ragService.Query(r.Context(), query.Question)
	if err != nil {
		http.Error(w, "Failed to process query: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Set response headers
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	// Send response
	if err := json.NewEncoder(w).Encode(response); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
}

// handleIndexDocumentation handles documentation indexing requests
func (h *RAGHandler) HandleIndexDocumentation(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Index documentation
	err := h.ragService.IndexDocumentation(r.Context())
	if err != nil {
		http.Error(w, "Failed to index documentation: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Return success response
	response := map[string]interface{}{
		"message": "Documentation indexed successfully",
		"timestamp": "2026-03-17T08:00:00Z",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// handleRAGStatus handles RAG status requests
func (h *RAGHandler) HandleRAGStatus(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Get RAG service status
	status := map[string]interface{}{
		"enabled": true,
		"model":   "qwen2.5:0.5b",
		"sources": []string{
			"documentation",
			"sqlite_memory", 
			"kubernetes",
			"dashboard",
			"k8sgpt",
			"flux",
			"argocd",
		},
		"environment": os.Getenv("ENVIRONMENT"),
		"version": "1.0.0",
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(status)
}
