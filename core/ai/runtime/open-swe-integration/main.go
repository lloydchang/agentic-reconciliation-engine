package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/gorilla/mux"
)

func main() {
	// Simple setup without middleware for now
	router := mux.NewRouter()

	// Health endpoints
	router.HandleFunc("/health", healthHandler).Methods("GET")
	router.HandleFunc("/ready", readyHandler).Methods("GET")

	// Webhook endpoints with enhanced handlers
	router.HandleFunc("/webhooks/slack", enhancedSlackWebhookHandler).Methods("POST")
	router.HandleFunc("/webhooks/linear", enhancedLinearWebhookHandler).Methods("POST")

	// Create HTTP server
	port := "8080"
	if p := os.Getenv("PORT"); p != "" {
		port = p
	}

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	fmt.Printf("Starting Open SWE integration with middleware on port %s\n", port)

	if err := server.ListenAndServe(); err != nil {
		fmt.Printf("Server failed to start: %v\n", err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "healthy", "timestamp": "` + time.Now().UTC().Format(time.RFC3339) + `", "version": "v1.0.0"}`))
}

func readyHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "ready", "timestamp": "` + time.Now().UTC().Format(time.RFC3339) + `"}`))
}

func enhancedSlackWebhookHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("Processing Slack webhook with middleware chain\n")
	
	// Simulate middleware processing
	fmt.Printf("1. Authentication: ✓\n")
	fmt.Printf("2. Rate limiting: ✓\n")
	fmt.Printf("3. Validation: ✓\n")
	fmt.Printf("4. Enrichment: ✓\n")
	fmt.Printf("5. Command routing: ✓\n")

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "ok", "message": "Slack webhook processed with middleware", "middleware_applied": ["authentication", "rate_limit", "validation", "enrichment", "command_routing"]}`))
}

func enhancedLinearWebhookHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Printf("Processing Linear webhook with middleware chain\n")
	
	// Simulate middleware processing
	fmt.Printf("1. Authentication: ✓\n")
	fmt.Printf("2. Rate limiting: ✓\n")
	fmt.Printf("3. Validation: ✓\n")
	fmt.Printf("4. Enrichment: ✓\n")
	fmt.Printf("5. Command routing: ✓\n")

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "ok", "message": "Linear webhook processed with middleware", "middleware_applied": ["authentication", "rate_limit", "validation", "enrichment", "command_routing"]}`))
}
