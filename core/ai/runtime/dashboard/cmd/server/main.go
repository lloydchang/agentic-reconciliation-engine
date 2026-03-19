package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/api"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/config"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/database"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/rag"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/services"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/ws"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/pkg/metrics"
	"go.uber.org/zap"
)

func main() {
	// Initialize logger
	logger, _ := zap.NewDevelopment()
	defer logger.Sync()

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	log.Printf("Configuration loaded: DatabaseURL = %s", cfg.DatabaseURL)

	// Initialize database
	db, err := database.NewConnection(cfg.DatabaseURL)
	if err != nil {
		logger.Fatal("Failed to connect to database", zap.Error(err))
	}
	defer db.Close()
	
	logger.Info("Connected to database", zap.String("database_url", cfg.DatabaseURL))

	// Run migrations
	if err := database.RunMigrations(db); err != nil {
		logger.Fatal("Failed to run migrations", zap.Error(err))
	}

	// Initialize services
	agentService := services.NewAgentService(db, logger)
	skillService := services.NewSkillService(db, logger)
	activityService := services.NewActivityService(db, logger)
	systemService := services.NewSystemService(db, logger)
	evaluationService := services.NewEvaluationService(logger)

	// Initialize RAG service if enabled
	var ragService *rag.RAGService
	var ragHandler *api.RAGHandler
	if os.Getenv("RAG_ENABLED") == "true" {
		qwenClient := rag.NewQwenClient(
			getEnv("QWEN_LLAMACPP_URL", "http://localhost:8080"),
			getEnv("QWEN_MODEL", "qwen2.5:0.5b"),
		)
		ragService = rag.NewRAGService(db, qwenClient)
		ragHandler = api.NewRAGHandler(ragService)
		
		// Index documentation on startup
		go func() {
			logger.Info("Indexing documentation...")
			if err := ragService.IndexDocumentation(context.Background()); err != nil {
				logger.Error("Failed to index documentation", zap.Error(err))
			} else {
				logger.Info("Documentation indexing completed")
			}
		}()
	}

	// Initialize voice handler
	var voiceHandler *api.VoiceHandler
	voiceHandler = api.NewVoiceHandler(getEnv("VOICE_UPLOAD_DIR", "/tmp/voice-uploads"))

	// Initialize WebSocket hub
	wsHub := ws.NewHub(logger)
	go wsHub.Run()

	// Initialize metrics
	metrics.Init()

	// Setup Gin router
	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// CORS middleware
	router.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Initialize API handlers
	apiHandler := api.NewHandler(agentService, skillService, activityService, systemService, evaluationService, wsHub, logger)

	// Register routes
	v1 := router.Group("/api/v1")
	{
		// Agent Management
		v1.GET("/agents", apiHandler.GetAgents)
		v1.GET("/agents/:id", apiHandler.GetAgent)
		v1.POST("/agents/:id/start", apiHandler.StartAgent)
		v1.POST("/agents/:id/stop", apiHandler.StopAgent)
		v1.POST("/agents/:id/restart", apiHandler.RestartAgent)

		// Skills Management
		v1.GET("/skills", apiHandler.GetSkills)
		v1.GET("/skills/:id", apiHandler.GetSkill)
		v1.POST("/skills/:id/execute", apiHandler.ExecuteSkill)

		// System APIs
		v1.GET("/system/status", apiHandler.GetSystemStatus)
		v1.GET("/system/metrics", apiHandler.GetSystemMetrics)
		v1.GET("/system/health", apiHandler.GetHealth)

		// Evaluation APIs
		v1.GET("/evaluation/health", apiHandler.GetEvaluationHealth)
		v1.GET("/evaluation/monitoring", apiHandler.GetEvaluationMonitoring)
		v1.GET("/evaluation/issues", apiHandler.GetEvaluationIssues)
		v1.GET("/evaluation/auto-fix", apiHandler.GetAutoFixStatus)
		v1.GET("/evaluation/summary", apiHandler.GetEvaluationSummary)

		// Activity APIs
		v1.GET("/activity", apiHandler.GetActivities)
		v1.GET("/activity/stream", apiHandler.HandleWebSocket)

		// RAG APIs (if enabled)
		if ragHandler != nil {
			v1.POST("/rag/query", func(c *gin.Context) {
				ragHandler.HandleRAGQuery(c.Writer, c.Request)
			})
			v1.POST("/rag/index", func(c *gin.Context) {
				ragHandler.HandleIndexDocumentation(c.Writer, c.Request)
			})
			v1.GET("/rag/status", func(c *gin.Context) {
				ragHandler.HandleRAGStatus(c.Writer, c.Request)
			})
		}

		// Voice APIs (if enabled)
		if voiceHandler != nil {
			voiceHandler.RegisterVoiceRoutes(router)
		}
	}

	// Health check endpoint
	router.GET("/health", apiHandler.GetHealth)

	// Metrics endpoint
	router.GET("/metrics", gin.WrapH(metrics.Handler()))

	// Create HTTP server
	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: router,
	}

	// Start server in a goroutine
	go func() {
		logger.Info("Starting server", zap.Int("port", cfg.Port))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("Shutting down server...")

	// The context is used to inform the server it has 5 seconds to finish
	// the request it is currently handling
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Fatal("Server forced to shutdown", zap.Error(err))
	}

	logger.Info("Server exited")
}

// Helper function to get environment variable
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
