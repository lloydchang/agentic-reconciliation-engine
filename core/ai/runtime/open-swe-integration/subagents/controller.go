package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/gorilla/mux"
)

// SubagentController manages HTTP endpoints for subagent operations
type SubagentController struct {
	manager *SubagentManager
	logger  *Logger
}

func NewSubagentController(manager *SubagentManager, logger *Logger) *SubagentController {
	return &SubagentController{
		manager: manager,
		logger:  logger,
	}
}

// SubmitTaskHandler handles task submission
func (sc *SubagentController) SubmitTaskHandler(w http.ResponseWriter, r *http.Request) {
	var task Task
	if err := json.NewDecoder(r.Body).Decode(&task); err != nil {
		sc.logger.Error("Failed to decode task", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Generate task ID if not provided
	if task.ID == "" {
		task.ID = generateTaskID()
	}

	// Set default timeout if not provided
	if task.Timeout == 0 {
		task.Timeout = 5 * time.Minute
	}

	if err := sc.manager.SubmitTask(&task); err != nil {
		sc.logger.Error("Failed to submit task", "error", err, "task_id", task.ID)
		http.Error(w, fmt.Sprintf("Failed to submit task: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{
		"task_id": task.ID,
		"status":  "submitted",
	})
}

// GetResultHandler handles result retrieval
func (sc *SubagentController) GetResultHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	taskID := vars["task_id"]

	if taskID == "" {
		http.Error(w, "Missing task_id", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
	defer cancel()

	result, err := sc.manager.GetResult(ctx)
	if err != nil {
		sc.logger.Error("Failed to get result", "error", err, "task_id", taskID)
		http.Error(w, fmt.Sprintf("Failed to get result: %v", err), http.StatusInternalServerError)
		return
	}

	if result.TaskID != taskID {
		http.Error(w, "Result not found for task_id", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

// GetStatusHandler handles status requests
func (sc *SubagentController) GetStatusHandler(w http.ResponseWriter, r *http.Request) {
	status := sc.manager.GetStatus()
	queueStatus := sc.manager.GetQueueStatus()

	response := map[string]interface{}{
		"subagents": status,
		"queue":     queueStatus,
		"timestamp": time.Now().UTC(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// ParallelTaskHandler handles parallel task submission
func (sc *SubagentController) ParallelTaskHandler(w http.ResponseWriter, r *http.Request) {
	var request struct {
		Tasks    []Task `json:"tasks"`
		Parallel bool   `json:"parallel"`
	}

	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		sc.logger.Error("Failed to decode parallel task request", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	results := make([]map[string]interface{}, 0, len(request.Tasks))

	if request.Parallel {
		// Submit tasks in parallel
		for _, task := range request.Tasks {
			if task.ID == "" {
				task.ID = generateTaskID()
			}
			if task.Timeout == 0 {
				task.Timeout = 5 * time.Minute
			}

			if err := sc.manager.SubmitTask(&task); err != nil {
				results = append(results, map[string]interface{}{
					"task_id": task.ID,
					"status":  "failed",
					"error":   err.Error(),
				})
			} else {
				results = append(results, map[string]interface{}{
					"task_id": task.ID,
					"status":  "submitted",
				})
			}
		}
	} else {
		// Submit tasks sequentially
		for _, task := range request.Tasks {
			if task.ID == "" {
				task.ID = generateTaskID()
			}
			if task.Timeout == 0 {
				task.Timeout = 5 * time.Minute
			}

			if err := sc.manager.SubmitTask(&task); err != nil {
				results = append(results, map[string]interface{}{
					"task_id": task.ID,
					"status":  "failed",
					"error":   err.Error(),
				})
				break // Stop on first error in sequential mode
			} else {
				results = append(results, map[string]interface{}{
					"task_id": task.ID,
					"status":  "submitted",
				})
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"tasks":    results,
		"parallel": request.Parallel,
		"count":    len(results),
	})
}

// SubagentIntegration integrates subagents with the main webhook handlers
type SubagentIntegration struct {
	controller *SubagentController
	manager    *SubagentManager
	logger     *Logger
}

func NewSubagentIntegration(parallelism int, logger *Logger) *SubagentIntegration {
	manager := NewSubagentManager(parallelism, logger)
	controller := NewSubagentController(manager, logger)

	return &SubagentIntegration{
		controller: controller,
		manager:    manager,
		logger:     logger,
	}
}

// Start starts the subagent integration
func (si *SubagentIntegration) Start(ctx context.Context) error {
	// Register built-in subagents
	si.manager.RegisterSubagent(NewDeploymentSubagent(si.logger))
	si.manager.RegisterSubagent(NewSecuritySubagent(si.logger))

	// Start the manager
	if err := si.manager.Start(ctx); err != nil {
		return fmt.Errorf("failed to start subagent manager: %w", err)
	}

	si.logger.Info("Subagent integration started", "subagents", len(si.manager.GetStatus()))
	return nil
}

// Stop stops the subagent integration
func (si *SubagentIntegration) Stop() {
	si.manager.Stop()
	si.logger.Info("Subagent integration stopped")
}

// ProcessWebhookWithSubagents processes webhook requests using subagents
func (si *SubagentIntegration) ProcessWebhookWithSubagents(source string, data map[string]interface{}) (*Result, error) {
	// Convert webhook to task
	task, err := si.webhookToTask(source, data)
	if err != nil {
		return nil, fmt.Errorf("failed to convert webhook to task: %w", err)
	}

	// Submit task to subagent manager
	if err := si.manager.SubmitTask(task); err != nil {
		return nil, fmt.Errorf("failed to submit task: %w", err)
	}

	// Wait for result (with timeout)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	result, err := si.manager.GetResult(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get result: %w", err)
	}

	return result, nil
}

// webhookToTask converts webhook data to a task
func (si *SubagentIntegration) webhookToTask(source string, data map[string]interface{}) (*Task, error) {
	task := &Task{
		ID:       generateTaskID(),
		Type:     "unknown",
		Priority: 5,
		Data:     data,
		Context: map[string]interface{}{
			"source": source,
		},
		Timeout:   5 * time.Minute,
		CreatedAt: time.Now(),
	}

	// Extract task type from webhook data
	switch source {
	case "slack":
		task = si.parseSlackWebhook(task, data)
	case "linear":
		task = si.parseLinearWebhook(task, data)
	}

	return task, nil
}

// parseSlackWebhook parses Slack webhook data
func (si *SubagentIntegration) parseSlackWebhook(task *Task, data map[string]interface{}) *Task {
	if eventType, ok := data["type"].(string); ok {
		switch eventType {
		case "event":
			if event, ok := data["event"].(map[string]interface{}); ok {
				if eventType, ok := event["type"].(string); ok {
					switch eventType {
					case "message":
						if text, ok := event["text"].(string); ok {
							task.Type = si.extractTaskType(text)
							task.Data["command"] = text
							if user, ok := event["user"].(string); ok {
								task.Context["user_id"] = user
							}
							if channel, ok := event["channel"].(string); ok {
								task.Context["channel_id"] = channel
							}
						}
					}
				}
			}
		}
	}
	return task
}

// parseLinearWebhook parses Linear webhook data
func (si *SubagentIntegration) parseLinearWebhook(task *Task, data map[string]interface{}) *Task {
	if action, ok := data["action"].(string); ok {
		task.Context["action"] = action
	}

	if issueData, ok := data["data"].(map[string]interface{}); ok {
		if title, ok := issueData["title"].(string); ok {
			task.Type = si.extractTaskType(title)
			task.Data["command"] = title
			task.Data["issue_id"] = issueData["id"]
		}
	}

	return task
}

// extractTaskType extracts task type from command text
func (si *SubagentIntegration) extractTaskType(text string) string {
	text = text // Simple implementation - would use NLP in production
	
	taskTypes := map[string]string{
		"deploy":   "deploy",
		"scale":    "scale",
		"security": "security",
		"audit":    "audit",
		"scan":     "security",
		"check":    "security",
		"test":     "security",
	}

	for keyword, taskType := range taskTypes {
		if contains(text, keyword) {
			return taskType
		}
	}

	return "general"
}

// SetupSubagentRoutes sets up HTTP routes for subagent operations
func SetupSubagentRoutes(router *mux.Router, integration *SubagentIntegration) {
	// API routes
	router.HandleFunc("/api/v1/tasks", integration.controller.SubmitTaskHandler).Methods("POST")
	router.HandleFunc("/api/v1/tasks/{task_id}/result", integration.controller.GetResultHandler).Methods("GET")
	router.HandleFunc("/api/v1/tasks/parallel", integration.controller.ParallelTaskHandler).Methods("POST")
	router.HandleFunc("/api/v1/status", integration.controller.GetStatusHandler).Methods("GET")

	// Enhanced webhook handlers with subagent integration
	router.HandleFunc("/webhooks/slack", func(w http.ResponseWriter, r *http.Request) {
		si.handleSlackWebhookWithSubagents(w, r)
	}).Methods("POST")

	router.HandleFunc("/webhooks/linear", func(w http.ResponseWriter, r *http.Request) {
		si.handleLinearWebhookWithSubagents(w, r)
	}).Methods("POST")
}

// handleSlackWebhookWithSubagents handles Slack webhooks with subagent processing
func (si *SubagentIntegration) handleSlackWebhookWithSubagents(w http.ResponseWriter, r *http.Request) {
	si.logger.Info("Processing Slack webhook with subagents")

	var data map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		si.logger.Error("Failed to decode Slack webhook", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := si.ProcessWebhookWithSubagents("slack", data)
	if err != nil {
		si.logger.Error("Failed to process Slack webhook with subagents", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok",
		"message": "Slack webhook processed with subagents",
		"result": result,
		"subagent": result.Subagent,
	})
}

// handleLinearWebhookWithSubagents handles Linear webhooks with subagent processing
func (si *SubagentIntegration) handleLinearWebhookWithSubagents(w http.ResponseWriter, r *http.Request) {
	si.logger.Info("Processing Linear webhook with subagents")

	var data map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		si.logger.Error("Failed to decode Linear webhook", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	result, err := si.ProcessWebhookWithSubagents("linear", data)
	if err != nil {
		si.logger.Error("Failed to process Linear webhook with subagents", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok",
		"message": "Linear webhook processed with subagents",
		"result": result,
		"subagent": result.Subagent,
	})
}

// Utility functions
func generateTaskID() string {
	return fmt.Sprintf("task_%d", time.Now().UnixNano())
}

func contains(text, keyword string) bool {
	return len(text) >= len(keyword) && text[:len(keyword)] == keyword
}

// Enhanced main function with subagent integration
func setupOpenSWEIntegrationWithSubagents() (*SubagentIntegration, *mux.Router) {
	logger := &Logger{}
	
	// Initialize subagent integration
	integration := NewSubagentIntegration(5, logger) // 5 parallel workers
	
	// Setup HTTP routes
	router := mux.NewRouter()
	
	// Health endpoints
	router.HandleFunc("/health", healthHandler).Methods("GET")
	router.HandleFunc("/ready", readyHandler).Methods("GET")
	
	// Setup subagent routes
	SetupSubagentRoutes(router, integration)
	
	return integration, router
}
