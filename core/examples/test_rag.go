package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"os"

	_ "github.com/lib/pq"
	"agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/rag"
)

func main() {
	// Test database connection
	db, err := sql.Open("postgres", "postgres://temporal:temporal@localhost:5432/temporal?sslmode=disable")
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Test database connection
	if err := db.Ping(); err != nil {
		log.Fatalf("Failed to ping database: %v", err)
	}
	log.Println("Database connection successful")

	// Create Qwen client using centralized service
	qwenClient := rag.NewQwenClient(
		"http://agent-memory-service.ai-infrastructure.svc.cluster.local:8080", // centralized Qwen service
		"qwen2.5-7b-instruct",
	)

	// Create RAG service
	ragService := rag.NewRAGService(db, qwenClient)

	// Index documentation
	log.Println("Indexing documentation...")
	if err := ragService.IndexDocumentation(context.Background()); err != nil {
		log.Printf("Failed to index documentation: %v", err)
	} else {
		log.Println("Documentation indexing completed")
	}

	// Test RAG query
	log.Println("Testing RAG query...")
	response, err := ragService.Query(context.Background(), "What is the status of our Agentic Reconciliation Engine?")
	if err != nil {
		log.Printf("RAG query failed: %v", err)
		return
	}

	fmt.Printf("RAG Response:\n")
	fmt.Printf("Question: What is the status of our Agentic Reconciliation Engine?\n")
	fmt.Printf("Answer: %s\n", response.Answer)
	fmt.Printf("Sources: %d\n", len(response.Sources))
	fmt.Printf("Model: %s\n", response.Model)
	fmt.Printf("Processing Time: %v ms\n", response.Metadata["processing_time"])

	// Test with different queries
	queries := []string{
		"Why are my pods failing?",
		"Show me the deployment status",
		"What skills are available?",
		"How can I optimize costs?",
	}

	for _, query := range queries {
		fmt.Printf("\n---\nQuestion: %s\n", query)
		response, err := ragService.Query(context.Background(), query)
		if err != nil {
			log.Printf("Query failed: %v", err)
			continue
		}
		fmt.Printf("Answer: %s\n", response.Answer)
		fmt.Printf("Sources Queried: %v\n", response.Metadata["sources_queried"])
	}
}
