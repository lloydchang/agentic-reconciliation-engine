package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// Configuration
const (
	OllamaBaseURL = "http://localhost:11434"
	Model         = "qwen2.5:0.5b"
	MaxSearchResults = 5
	SearchTimeout     = 10 * time.Second
)

// BackendType represents different inference backends
type BackendType string

const (
	BackendLlamaCpp BackendType = "llama.cpp"
	BackendOllama   BackendType = "ollama"
)

// LanguageType represents different agent language implementations
type LanguageType string

const (
	LanguageRust   LanguageType = "rust"
	LanguageGo     LanguageType = "go"
	LanguagePython LanguageType = "python"
)

// AgentConfig holds configuration for backend and language priorities
type AgentConfig struct {
	BackendPriority  []BackendType  `json:"backend_priority"`
	LanguagePriority []LanguageType `json:"language_priority"`
	OllamaURL        string         `json:"ollama_url"`
	Model            string         `json:"model"`
	LlamaCppModelPath *string       `json:"llama_cpp_model_path,omitempty"`
}

// Memory represents a stored memory item
type Memory struct {
	ID           int       `json:"id"`
	Source       string    `json:"source"`
	RawText      string    `json:"raw_text"`
	Summary      string    `json:"summary"`
	Entities     []string  `json:"entities"`
	Topics       []string  `json:"topics"`
	Connections  []Connection `json:"connections"`
	Importance   float64   `json:"importance"`
	CreatedAt    time.Time `json:"created_at"`
	Consolidated bool      `json:"consolidated"`
}

// Connection represents a relationship between memories
type Connection struct {
	FromID       int    `json:"from_id"`
	ToID         int    `json:"to_id"`
	Relationship string `json:"relationship"`
}

// Consolidation represents a consolidated insight
type Consolidation struct {
	ID         int       `json:"id"`
	SourceIDs  []int     `json:"source_ids"`
	Summary    string    `json:"summary"`
	Insight    string    `json:"insight"`
	CreatedAt  time.Time `json:"created_at"`
}

// SearchResult represents a DuckDuckGo search result
type SearchResult struct {
	Title   string `json:"title"`
	Body    string `json:"body"`
	URL     string `json:"url"`
	Source  string `json:"source"`
}

type OllamaResponse struct {
	Response string `json:"response"`
}

// Backend interface for inference
type Backend interface {
	Generate(prompt string) (string, error)
	Name() string
}

// OllamaBackend implements Backend using Ollama
type OllamaBackend struct {
	httpClient *http.Client
	baseURL    string
	model      string
}

func NewOllamaBackend(baseURL, model string) *OllamaBackend {
	return &OllamaBackend{
		httpClient: &http.Client{Timeout: 60 * time.Second},
		baseURL:    baseURL,
		model:      model,
	}
}

func (ob *OllamaBackend) Generate(prompt string) (string, error) {
	reqBody := map[string]interface{}{
		"model":  ob.model,
		"prompt": prompt,
		"stream": false,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/api/generate", ob.baseURL), bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := ob.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("ollama API error %d: %s", resp.StatusCode, string(body))
	}

	var ollamaResp OllamaResponse
	if err := json.NewDecoder(resp.Body).Decode(&ollamaResp); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	return strings.TrimSpace(ollamaResp.Response), nil
}

func (ob *OllamaBackend) Name() string {
	return "Ollama"
}

// LlamaCppBackend implements Backend using llama.cpp (placeholder for now)
type LlamaCppBackend struct {
	modelPath string
}

func NewLlamaCppBackend(modelPath string) *LlamaCppBackend {
	return &LlamaCppBackend{modelPath: modelPath}
}

func (lb *LlamaCppBackend) Generate(prompt string) (string, error) {
	// TODO: Implement actual llama.cpp integration
	return "", fmt.Errorf("llama.cpp backend not yet implemented")
}

func (lb *LlamaCppBackend) Name() string {
	return "llama.cpp"
}

// MemoryAgent handles all memory operations
type MemoryAgent struct {
	db           *sql.DB
	backends     []Backend
	httpClient   *http.Client
	searchClient *http.Client
	inboxPath    string
	config       AgentConfig
	mu           sync.RWMutex
}

// NewMemoryAgent creates a new memory agent
func NewMemoryAgent(dbPath, inboxPath string) (*MemoryAgent, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := initDB(db); err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	httpClient := &http.Client{
		Timeout: 60 * time.Second,
	}

	searchClient := &http.Client{
		Timeout: SearchTimeout,
	}

	return &MemoryAgent{
		db:           db,
		httpClient:   httpClient,
		searchClient: searchClient,
		inboxPath:    inboxPath,
	}, nil
}

// initDB initializes the database schema
func initDB(db *sql.DB) error {
	schema := `
		CREATE TABLE IF NOT EXISTS memories (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			source TEXT NOT NULL DEFAULT '',
			raw_text TEXT NOT NULL,
			summary TEXT NOT NULL,
			entities TEXT NOT NULL DEFAULT '[]',
			topics TEXT NOT NULL DEFAULT '[]',
			connections TEXT NOT NULL DEFAULT '[]',
			importance REAL NOT NULL DEFAULT 0.5,
			created_at DATETIME NOT NULL,
			consolidated INTEGER NOT NULL DEFAULT 0
		);
		CREATE TABLE IF NOT EXISTS consolidations (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			source_ids TEXT NOT NULL,
			summary TEXT NOT NULL,
			insight TEXT NOT NULL,
			created_at DATETIME NOT NULL
		);
		CREATE TABLE IF NOT EXISTS processed_files (
			path TEXT PRIMARY KEY,
			processed_at DATETIME NOT NULL
		);
	`
	_, err := db.Exec(schema)
	return err
}

// generate uses configured backends with automatic fallback
func (ma *MemoryAgent) generate(prompt string) (string, error) {
	for _, backend := range ma.backends {
		if response, err := backend.Generate(prompt); err == nil {
			log.Printf("✅ Generated response using %s", backend.Name())
			return response, nil
		} else {
			log.Printf("❌ %s backend failed: %v", backend.Name(), err)
		}
	}
	return "", fmt.Errorf("all inference backends failed")
}

// ollamaGenerate generates text using Ollama
func (ma *MemoryAgent) ollamaGenerate(prompt string) (string, error) {
	reqBody := map[string]interface{}{
		"model":  Model,
		"prompt": prompt,
		"stream": false,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/api/generate", OllamaBaseURL), bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := ma.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to make request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("ollama API error %d: %s", resp.StatusCode, string(body))
	}

	var ollamaResp OllamaResponse
	if err := json.NewDecoder(resp.Body).Decode(&ollamaResp); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	return strings.TrimSpace(ollamaResp.Response), nil
}

// Ingest processes new information into structured memory
func (ma *MemoryAgent) Ingest(text, source string) (*Memory, error) {
	prompt := fmt.Sprintf(`You are a Memory Ingest Agent. Process this information into structured memory.

Input: %s

Extract and return ONLY a JSON object with these fields:
{
    "summary": "1-2 sentence summary",
    "entities": ["key people/companies/products/concepts"],
    "topics": ["2-4 topic tags"],
    "importance": 0.0-1.0
}

Be concise and accurate.`, text)

	response, err := ma.ollamaGenerate(prompt)
	if err != nil {
		return nil, fmt.Errorf("failed to generate memory: %w", err)
	}

	var data struct {
		Summary    string   `json:"summary"`
		Entities   []string `json:"entities"`
		Topics     []string `json:"topics"`
		Importance float64  `json:"importance"`
	}

	if err := json.Unmarshal([]byte(response), &data); err != nil {
		// Fallback: store raw text
		data.Summary = text[:200] + "..."
		data.Entities = []string{}
		data.Topics = []string{}
		data.Importance = 0.5
	}

	ma.mu.Lock()
	defer ma.mu.Unlock()

	result, err := ma.db.Exec(
		`INSERT INTO memories (source, raw_text, summary, entities, topics, importance, created_at)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		source, text, data.Summary,
		mustMarshal(data.Entities),
		mustMarshal(data.Topics),
		data.Importance,
		time.Now(),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to insert memory: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("failed to get insert ID: %w", err)
	}

	memory := &Memory{
		ID:           int(id),
		Source:       source,
		RawText:      text,
		Summary:      data.Summary,
		Entities:     data.Entities,
		Topics:       data.Topics,
		Importance:   data.Importance,
		CreatedAt:    time.Now(),
		Consolidated: false,
	}

	log.Printf("📥 Stored memory #%d: %s...", memory.ID, memory.Summary[:60])
	return memory, nil
}

// Consolidate finds connections and patterns in unconsolidated memories
func (ma *MemoryAgent) Consolidate() error {
	ma.mu.RLock()
	rows, err := ma.db.Query(`
		SELECT id, summary, entities, topics, importance
		FROM memories
		WHERE consolidated = 0
		ORDER BY created_at DESC LIMIT 10
	`)
	if err != nil {
		ma.mu.RUnlock()
		return fmt.Errorf("failed to query memories: %w", err)
	}

	var memories []map[string]interface{}
	for rows.Next() {
		var id int
		var summary string
		var entitiesStr, topicsStr string
		var importance float64

		if err := rows.Scan(&id, &summary, &entitiesStr, &topicsStr, &importance); err != nil {
			rows.Close()
			ma.mu.RUnlock()
			return fmt.Errorf("failed to scan memory: %w", err)
		}

		var entities, topics []string
		json.Unmarshal([]byte(entitiesStr), &entities)
		json.Unmarshal([]byte(topicsStr), &topics)

		memories = append(memories, map[string]interface{}{
			"id":        id,
			"summary":   summary,
			"entities":  entities,
			"topics":    topics,
			"importance": importance,
		})
	}
	rows.Close()
	ma.mu.RUnlock()

	if len(memories) < 2 {
		return fmt.Errorf("need at least 2 unconsolidated memories for consolidation")
	}

	context := "Memories:\n"
	sourceIDs := make([]int, len(memories))
	for i, m := range memories {
		sourceIDs[i] = m["id"].(int)
		context += fmt.Sprintf("Memory %d: %s (Entities: %v) (Topics: %v)\n",
			m["id"], m["summary"], m["entities"], m["topics"])
	}

	prompt := fmt.Sprintf(`You are a Memory Consolidation Agent. Analyze these memories and find connections/patterns.

%s

Return ONLY a JSON object with:
{
    "source_ids": %v,
    "summary": "synthesized summary across memories",
    "insight": "one key pattern/insight discovered",
    "connections": [{"from_id": id, "to_id": id, "relationship": "description"}]
}

Be thorough but concise.`, context, sourceIDs)

	response, err := ma.ollamaGenerate(prompt)
	if err != nil {
		return fmt.Errorf("failed to generate consolidation: %w", err)
	}

	var data struct {
		SourceIDs  []int `json:"source_ids"`
		Summary    string `json:"summary"`
		Insight    string `json:"insight"`
		Connections []Connection `json:"connections"`
	}

	if err := json.Unmarshal([]byte(response), &data); err != nil {
		return fmt.Errorf("failed to parse consolidation response: %w", err)
	}

	if len(data.SourceIDs) == 0 {
		return fmt.Errorf("no consolidation needed")
	}

	ma.mu.Lock()
	defer ma.mu.Unlock()

	// Store consolidation
	result, err := ma.db.Exec(
		`INSERT INTO consolidations (source_ids, summary, insight, created_at) VALUES (?, ?, ?, ?)`,
		mustMarshal(data.SourceIDs), data.Summary, data.Insight, time.Now(),
	)
	if err != nil {
		return fmt.Errorf("failed to insert consolidation: %w", err)
	}

	consolidationID, _ := result.LastInsertId()

	// Update connections and mark as consolidated
	for _, conn := range data.Connections {
		for _, mid := range []int{conn.FromID, conn.ToID} {
			var connectionsStr string
			ma.db.QueryRow(`SELECT connections FROM memories WHERE id = ?`, mid).Scan(&connectionsStr)

			var connections []Connection
			json.Unmarshal([]byte(connectionsStr), &connections)

			connections = append(connections, Connection{
				FromID:       conn.FromID,
				ToID:         conn.ToID,
				Relationship: conn.Relationship,
			})

			ma.db.Exec(`UPDATE memories SET connections = ? WHERE id = ?`,
				mustMarshal(connections), mid)
		}
	}

	// Mark source memories as consolidated
	for _, id := range data.SourceIDs {
		ma.db.Exec(`UPDATE memories SET consolidated = 1 WHERE id = ?`, id)
	}

	log.Printf("🔄 Consolidated %d memories. Insight: %s", len(data.SourceIDs), data.Insight[:80])
	return nil
}

// Query answers questions using stored memories and optional search
func (ma *MemoryAgent) Query(question string, useSearch bool) (string, error) {
	ma.mu.RLock()
	rows, err := ma.db.Query(`
		SELECT summary, source FROM memories ORDER BY created_at DESC LIMIT 20
	`)
	if err != nil {
		ma.mu.RUnlock()
		return "", fmt.Errorf("failed to query memories: %w", err)
	}

	context := "Stored Memories:\n"
	for rows.Next() {
		var summary, source string
		rows.Scan(&summary, &source)
		context += fmt.Sprintf("[%s] %s\n", source, summary)
	}
	rows.Close()

	// Get recent consolidations
	rows, err = ma.db.Query(`
		SELECT insight FROM consolidations ORDER BY created_at DESC LIMIT 5
	`)
	if err != nil {
		ma.mu.RUnlock()
		return "", fmt.Errorf("failed to query consolidations: %w", err)
	}

	if rows.Next() {
		context += "\nConsolidation Insights:\n"
		var insight string
		for rows.Next() {
			rows.Scan(&insight)
			context += fmt.Sprintf("- %s\n", insight)
		}
	}
	rows.Close()
	ma.mu.RUnlock()

	// Decide if we need to search
	searchNeeded := false
	if useSearch {
		searchPrompt := fmt.Sprintf(`Based on this question and available memories, do we need current web information?

Question: %s

Available memories cover: %s

Should we search the internet for additional grounding? Answer only YES or NO.`, question, context[:200])

		searchDecision, err := ma.ollamaGenerate(searchPrompt)
		if err != nil {
			return "", fmt.Errorf("failed to decide on search: %w", err)
		}
		searchNeeded = strings.Contains(strings.ToUpper(searchDecision), "YES")
	}

	searchResults := ""
	if searchNeeded {
		log.Printf("🔍 Searching web for: %s", question)
		results, err := ma.searchWeb(question)
		if err != nil {
			log.Printf("Search error: %v", err)
		} else if len(results) > 0 {
			searchResults = "\n\nWeb Search Results:\n"
			for _, r := range results {
				searchResults += fmt.Sprintf("- %s: %s... (%s)\n",
					r.Title, r.Body[:200], r.URL)
			}
			log.Printf("📊 Found %d search results", len(results))
		}
	}

	prompt := fmt.Sprintf(`You are a Memory Query Agent. Answer this question using stored memories and web search results if available.

Question: %s

%s%s

Provide a comprehensive answer. Reference sources when using web search. Be thorough but concise.`, question, context, searchResults)

	return ma.ollamaGenerate(prompt)
}

// searchWeb performs DuckDuckGo search
func (ma *MemoryAgent) searchWeb(query string) ([]SearchResult, error) {
	// Note: This is a simplified implementation. In production, you'd want a proper DDGS library
	// For now, we'll use a basic approach
	url := fmt.Sprintf("https://duckduckgo.com/html/?q=%s", query)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (compatible; MemoryAgent/1.0)")

	resp, err := ma.searchClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("search request failed with status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	// Very basic HTML parsing - in production, use a proper HTML parser
	html := string(body)
	var results []SearchResult

	// Extract titles and snippets (simplified)
	lines := strings.Split(html, "\n")
	for _, line := range lines {
		if strings.Contains(line, "<a class=\"result__a\"") {
			// Extract title
			start := strings.Index(line, ">")
			end := strings.Index(line, "</a>")
			if start != -1 && end != -1 && end > start {
				title := line[start+1 : end]
				results = append(results, SearchResult{
					Title:  title,
					Body:   "Search result snippet",
					URL:    "#",
					Source: "DuckDuckGo",
				})
			}
		}
		if len(results) >= MaxSearchResults {
			break
		}
	}

	return results, nil
}

// mustMarshal is a helper for JSON marshaling
func mustMarshal(v interface{}) string {
	data, _ := json.Marshal(v)
	return string(data)
}

// GetStatus returns memory system status
func (ma *MemoryAgent) GetStatus() (map[string]interface{}, error) {
	ma.mu.RLock()
	defer ma.mu.RUnlock()

	var total, unconsolidated, consolidations int

	ma.db.QueryRow(`SELECT COUNT(*) FROM memories`).Scan(&total)
	ma.db.QueryRow(`SELECT COUNT(*) FROM memories WHERE consolidated = 0`).Scan(&unconsolidated)
	ma.db.QueryRow(`SELECT COUNT(*) FROM consolidations`).Scan(&consolidations)

	return map[string]interface{}{
		"total_memories":  total,
		"unconsolidated":  unconsolidated,
		"consolidations":  consolidations,
		"model":           Model,
		"ollama_url":      OllamaBaseURL,
	}, nil
}

// GetMemories returns all stored memories
func (ma *MemoryAgent) GetMemories() ([]Memory, error) {
	ma.mu.RLock()
	defer ma.mu.RUnlock()

	rows, err := ma.db.Query(`
		SELECT id, source, summary, entities, topics, connections, importance, created_at, consolidated
		FROM memories ORDER BY created_at DESC LIMIT 50
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var memories []Memory
	for rows.Next() {
		var m Memory
		var entitiesStr, topicsStr, connectionsStr string
		var createdAtStr string

		err := rows.Scan(&m.ID, &m.Source, &m.Summary, &entitiesStr, &topicsStr,
			&connectionsStr, &m.Importance, &createdAtStr, &m.Consolidated)
		if err != nil {
			return nil, err
		}

		json.Unmarshal([]byte(entitiesStr), &m.Entities)
		json.Unmarshal([]byte(topicsStr), &m.Topics)
		json.Unmarshal([]byte(connectionsStr), &m.Connections)
		m.CreatedAt, _ = time.Parse(time.RFC3339, createdAtStr)

		memories = append(memories, m)
	}

	return memories, nil
}

// Close closes the database connection
func (ma *MemoryAgent) Close() error {
	return ma.db.Close()
}
