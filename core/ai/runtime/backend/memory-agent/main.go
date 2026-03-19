package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	_ "github.com/mattn/go-sqlite3"
)

type MemoryAgent struct {
	db     *sql.DB
	server *http.Server
}

type MemoryType string

const (
	Episodic  MemoryType = "episodic"
	Semantic  MemoryType = "semantic"
	Procedural MemoryType = "procedural"
	Working   MemoryType = "working"
)

type MemoryEntry struct {
	ID          int         `json:"id"`
	Type        MemoryType  `json:"type"`
	Key         string      `json:"key"`
	Value       string      `json:"value"`
	Timestamp   time.Time   `json:"timestamp"`
	Metadata    string      `json:"metadata"`
}

type EventPayload struct {
	CorrelationID string                 `json:"correlation_id"`
	Resource      ResourceContext        `json:"resource"`
	Alert         AlertInfo             `json:"alert"`
	Metadata      map[string]interface{} `json:"metadata"`
}

type ResourceContext struct {
	Namespace string `json:"namespace"`
	Kind      string `json:"kind"`
	Name      string `json:"name"`
	UID       string `json:"uid,omitempty"`
}

type AlertInfo struct {
	Name        string            `json:"name"`
	Severity    string            `json:"severity"`
	Description string            `json:"description"`
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
}

type QueryRequest struct {
	Type    MemoryType `json:"type"`
	Key     string     `json:"key,omitempty"`
	Limit   int        `json:"limit,omitempty"`
	Pattern string     `json:"pattern,omitempty"`
}

func NewMemoryAgent(dbPath string) (*MemoryAgent, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	agent := &MemoryAgent{db: db}
	if err := agent.initSchema(); err != nil {
		return nil, fmt.Errorf("failed to initialize schema: %w", err)
	}

	return agent, nil
}

func (ma *MemoryAgent) initSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS memories (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		type TEXT NOT NULL,
		key TEXT NOT NULL,
		value TEXT NOT NULL,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
		metadata TEXT,
		UNIQUE(type, key)
	);

	CREATE INDEX IF NOT EXISTS idx_memories_type_key ON memories(type, key);
	CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);

	CREATE TABLE IF NOT EXISTS events (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		correlation_id TEXT NOT NULL,
		resource_namespace TEXT,
		resource_kind TEXT,
		resource_name TEXT,
		resource_uid TEXT,
		alert_name TEXT,
		alert_severity TEXT,
		alert_description TEXT,
		alert_labels TEXT,
		alert_annotations TEXT,
		metadata TEXT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	);

	CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);
	CREATE INDEX IF NOT EXISTS idx_events_resource ON events(resource_namespace, resource_kind, resource_name);
	CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
	`

	_, err := ma.db.Exec(schema)
	return err
}

func (ma *MemoryAgent) Store(ctx context.Context, memType MemoryType, key, value string, metadata map[string]interface{}) error {
	metaJSON, _ := json.Marshal(metadata)

	_, err := ma.db.ExecContext(ctx,
		`INSERT OR REPLACE INTO memories (type, key, value, metadata) VALUES (?, ?, ?, ?)`,
		memType, key, value, string(metaJSON),
	)
	return err
}

func (ma *MemoryAgent) Retrieve(ctx context.Context, memType MemoryType, key string) (*MemoryEntry, error) {
	row := ma.db.QueryRowContext(ctx,
		`SELECT id, type, key, value, timestamp, metadata FROM memories WHERE type = ? AND key = ?`,
		memType, key,
	)

	var entry MemoryEntry
	var timestampStr, metaStr string

	err := row.Scan(&entry.ID, &entry.Type, &entry.Key, &entry.Value, &timestampStr, &metaStr)
	if err != nil {
		return nil, err
	}

	entry.Timestamp, _ = time.Parse(time.RFC3339, timestampStr)
	json.Unmarshal([]byte(metaStr), &entry.Metadata)

	return &entry, nil
}

func (ma *MemoryAgent) Query(ctx context.Context, req QueryRequest) ([]MemoryEntry, error) {
	query := `SELECT id, type, key, value, timestamp, metadata FROM memories WHERE type = ?`
	args := []interface{}{req.Type}

	if req.Key != "" {
		query += " AND key = ?"
		args = append(args, req.Key)
	}

	if req.Pattern != "" {
		query += " AND key LIKE ?"
		args = append(args, "%"+req.Pattern+"%")
	}

	query += " ORDER BY timestamp DESC"

	if req.Limit > 0 {
		query += " LIMIT ?"
		args = append(args, req.Limit)
	}

	rows, err := ma.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []MemoryEntry
	for rows.Next() {
		var entry MemoryEntry
		var timestampStr, metaStr string

		err := rows.Scan(&entry.ID, &entry.Type, &entry.Key, &entry.Value, &timestampStr, &metaStr)
		if err != nil {
			return nil, err
		}

		entry.Timestamp, _ = time.Parse(time.RFC3339, timestampStr)
		json.Unmarshal([]byte(metaStr), &entry.Metadata)
		entries = append(entries, entry)
	}

	return entries, nil
}

func (ma *MemoryAgent) IngestEvent(ctx context.Context, payload EventPayload) error {
	alertLabels, _ := json.Marshal(payload.Alert.Labels)
	alertAnnotations, _ := json.Marshal(payload.Alert.Annotations)
	metadata, _ := json.Marshal(payload.Metadata)

	_, err := ma.db.ExecContext(ctx, `
		INSERT INTO events (
			correlation_id, resource_namespace, resource_kind, resource_name, resource_uid,
			alert_name, alert_severity, alert_description, alert_labels, alert_annotations, metadata
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		payload.CorrelationID, payload.Resource.Namespace, payload.Resource.Kind, payload.Resource.Name, payload.Resource.UID,
		payload.Alert.Name, payload.Alert.Severity, payload.Alert.Description, string(alertLabels), string(alertAnnotations), string(metadata),
	)

	if err != nil {
		return err
	}

	// Store in episodic memory for pattern recognition
	eventKey := fmt.Sprintf("event:%s:%s", payload.Resource.Kind, payload.Resource.Name)
	eventData, _ := json.Marshal(payload)
	return ma.Store(ctx, Episodic, eventKey, string(eventData), map[string]interface{}{
		"correlation_id": payload.CorrelationID,
		"type":          "alert_event",
	})
}

func (ma *MemoryAgent) handleEvents(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var payload EventPayload
	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	if err := ma.IngestEvent(r.Context(), payload); err != nil {
		log.Printf("Failed to ingest event: %v", err)
		http.Error(w, "Failed to process event", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "accepted",
		"correlation_id": payload.CorrelationID,
	})
}

func (ma *MemoryAgent) handleQuery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req QueryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	entries, err := ma.Query(r.Context(), req)
	if err != nil {
		log.Printf("Failed to query memory: %v", err)
		http.Error(w, "Query failed", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"entries": entries,
		"count":   len(entries),
	})
}

func (ma *MemoryAgent) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status": "healthy",
		"timestamp": time.Now().Format(time.RFC3339),
	})
}

func (ma *MemoryAgent) Start(port int) error {
	r := mux.NewRouter()

	r.HandleFunc("/api/events", ma.handleEvents).Methods("POST")
	r.HandleFunc("/api/query", ma.handleQuery).Methods("POST")
	r.HandleFunc("/api/health", ma.handleHealth).Methods("GET")

	ma.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: r,
	}

	log.Printf("Memory agent starting on port %d", port)
	return ma.server.ListenAndServe()
}

func (ma *MemoryAgent) Stop(ctx context.Context) error {
	return ma.server.Shutdown(ctx)
}

func main() {
	dbPath := os.Getenv("MEMORY_DB_PATH")
	if dbPath == "" {
		dbPath = "/data/memory.db"
	}

	portStr := os.Getenv("MEMORY_AGENT_PORT")
	port := 8080
	if portStr != "" {
		if p, err := strconv.Atoi(portStr); err == nil {
			port = p
		}
	}

	agent, err := NewMemoryAgent(dbPath)
	if err != nil {
		log.Fatalf("Failed to create memory agent: %v", err)
	}

	log.Fatal(agent.Start(port))
}
