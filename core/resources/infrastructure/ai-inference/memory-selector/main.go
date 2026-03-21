package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/mux"
)

type MemoryBackend struct {
	URL      string
	Language string
	Healthy  bool
	LastCheck time.Time
}

type MemorySelector struct {
	mu             sync.RWMutex
	backends       []MemoryBackend
	priorityOrder  []string // e.g., ["rust", "go", "python"]
	activeBackend  *MemoryBackend
	httpClient     *http.Client
}

type QueryRequest struct {
	Type    string `json:"type"`
	Key     string `json:"key,omitempty"`
	Limit   int    `json:"limit,omitempty"`
	Pattern string `json:"pattern,omitempty"`
}

type StoreRequest struct {
	Type    string                 `json:"type"`
	Key     string                 `json:"key"`
	Value   string                 `json:"value"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

type InsightsRequest struct {
	Query string `json:"query"`
}

type HealthResponse struct {
	Status    string            `json:"status"`
	Backends  []BackendHealth   `json:"backends"`
	Active    string            `json:"active,omitempty"`
	Timestamp string            `json:"timestamp"`
}

type BackendHealth struct {
	Language string `json:"language"`
	URL      string `json:"url"`
	Healthy  bool   `json:"healthy"`
	LastSeen string `json:"last_seen,omitempty"`
}

func NewMemorySelector() (*MemorySelector, error) {
	priority := strings.Split(os.Getenv("LANGUAGE_PRIORITY"), ",")
	if len(priority) == 0 {
		priority = []string{"rust", "go", "python"}
	}

	selector := &MemorySelector{
		priorityOrder: priority,
		backends:      make([]MemoryBackend, 0, len(priority)),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}

	// Initialize backends from environment
	for _, lang := range priority {
		urlEnv := fmt.Sprintf("MEMORY_AGENT_%s_URL", strings.ToUpper(lang))
		url := os.Getenv(urlEnv)
		if url == "" {
			// Default URLs based on language
			switch lang {
			case "rust":
				url = "http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080"
			case "go":
				url = "http://agent-memory-go.ai-infrastructure.svc.cluster.local:8080"
			case "python":
				url = "http://agent-memory-python.ai-infrastructure.svc.cluster.local:8080"
			}
		}

		if url != "" {
			backend := MemoryBackend{
				URL:      url,
				Language: lang,
				Healthy:  false,
			}
			selector.backends = append(selector.backends, backend)
		}
	}

	// Perform initial health check
	if err := selector.checkAllBackends(); err != nil {
		log.Printf("Warning: initial health check failed: %v", err)
	}

	return selector, nil
}

func (s *MemorySelector) checkAllBackends() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	for i := range s.backends {
		healthy := s.checkBackend(&s.backends[i])
		s.backends[i].Healthy = healthy
		s.backends[i].LastCheck = now

		if healthy && s.activeBackend == nil {
			s.activeBackend = &s.backends[i]
		}
	}

	// If active backend is unhealthy, find next healthy
	if s.activeBackend != nil && !s.activeBackend.Healthy {
		s.selectActiveBackend()
	}

	return nil
}

func (s *MemorySelector) checkBackend(backend *MemoryBackend) bool {
	healthURL := fmt.Sprintf("%s/api/health", backend.URL)
	req, err := http.NewRequest("GET", healthURL, nil)
	if err != nil {
		return false
	}

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}

func (s *MemorySelector) selectActiveBackend() {
	for i := range s.backends {
		if s.backends[i].Healthy {
			s.activeBackend = &s.backends[i]
			log.Printf("Selected active backend: %s at %s", s.backends[i].Language, s.backends[i].URL)
			return
		}
	}
	s.activeBackend = nil // No healthy backends
}

func (s *MemorySelector) getActiveBackend() *MemoryBackend {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.activeBackend
}

func (s *MemorySelector) proxyRequest(w http.ResponseWriter, r *http.Request, method string, path string, body interface{}) {
	backend := s.getActiveBackend()
	if backend == nil {
		http.Error(w, "No healthy memory backends available", http.StatusServiceUnavailable)
		return
	}

	targetURL := fmt.Sprintf("%s%s", backend.URL, path)
	var reqBody []byte
	var err error

	if body != nil {
		reqBody, err = json.Marshal(body)
		if err != nil {
			http.Error(w, fmt.Sprintf("Failed to marshal request: %v", err), http.StatusBadRequest)
			return
		}
	}

	req, err := http.NewRequestWithContext(r.Context(), method, targetURL, bytes.NewReader(reqBody))
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to create request: %v", err), http.StatusBadRequest)
		return
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		// Backend failed – mark unhealthy and retry with next
		s.mu.Lock()
		backend.Healthy = false
		s.selectActiveBackend()
		s.mu.Unlock()

		if s.getActiveBackend() != nil {
			// Retry once with new active backend
			http.Error(w, "Backend failed, retrying with next available", http.StatusBadGateway)
			return
		}
		http.Error(w, fmt.Sprintf("All backends failed: %v", err), http.StatusServiceUnavailable)
		return
	}
	defer resp.Body.Close()

	// Copy response
	w.WriteHeader(resp.StatusCode)
	if resp.Body != nil {
		io.Copy(w, resp.Body)
	}
}

func (s *MemorySelector) handleHealth(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	backends := make([]BackendHealth, len(s.backends))
	for i, b := range s.backends {
		backends[i] = BackendHealth{
			Language: b.Language,
			URL:      b.URL,
			Healthy:  b.Healthy,
			LastSeen: b.LastCheck.Format(time.RFC3339),
		}
	}
	activeLang := ""
	if s.activeBackend != nil {
		activeLang = s.activeBackend.Language
	}
	s.mu.RUnlock()

	response := HealthResponse{
		Status:    "healthy",
		Backends:  backends,
		Active:    activeLang,
		Timestamp: time.Now().Format(time.RFC3339),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (s *MemorySelector) handleQuery(w http.ResponseWriter, r *http.Request) {
	var req QueryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	s.proxyRequest(w, r, "POST", "/api/query", req)
}

func (s *MemorySelector) handleStore(w http.ResponseWriter, r *http.Request) {
	var req StoreRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	s.proxyRequest(w, r, "POST", "/api/store", req)
}

func (s *MemorySelector) handleEvents(w http.ResponseWriter, r *http.Request) {
	var payload map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	s.proxyRequest(w, r, "POST", "/api/events", payload)
}

func (s *MemorySelector) handleInsights(w http.ResponseWriter, r *http.Request) {
	var req InsightsRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
		return
	}

	s.proxyRequest(w, r, "POST", "/api/insights", req)
}

func (s *MemorySelector) startHealthTicker() {
	ticker := time.NewTicker(30 * time.Second)
	go func() {
		for range ticker.C {
			s.checkAllBackends()
		}
	}()
}

func main() {
	selector, err := NewMemorySelector()
	if err != nil {
		log.Fatalf("Failed to create memory selector: %v", err)
	}

	selector.startHealthTicker()

	r := mux.NewRouter()
	r.HandleFunc("/health", selector.handleHealth).Methods("GET")
	r.HandleFunc("/api/query", selector.handleQuery).Methods("POST")
	r.HandleFunc("/api/store", selector.handleStore).Methods("POST")
	r.HandleFunc("/api/events", selector.handleEvents).Methods("POST")
	r.HandleFunc("/api/insights", selector.handleInsights).Methods("POST")

	port := os.Getenv("MEMORY_SELECTOR_PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Memory selector service starting on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}
