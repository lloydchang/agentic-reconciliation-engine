package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/standalone/backend/monitoring"
)

func main() {
	// Get metrics collector
	collector := monitoring.GetGlobalMetricsCollector()
	
	// Create HTTP metrics server
	server := monitoring.NewHTTPMetricsServer(collector, 8080)
	
	// Create context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	
	// Start metrics collection
	go func() {
		log.Println("Starting metrics collection...")
		collector.Start(ctx, 10*time.Second)
	}()
	
	// Start HTTP server
	log.Println("Starting HTTP metrics server on port 8080...")
	if err := server.Start(ctx); err != nil {
		log.Fatalf("Failed to start HTTP server: %v", err)
	}
	
	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan
	
	log.Println("Shutting down...")
	
	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()
	
	if err := server.Stop(shutdownCtx); err != nil {
		log.Printf("Error during server shutdown: %v", err)
	}
	
	collector.Stop()
	log.Println("Shutdown complete")
}
