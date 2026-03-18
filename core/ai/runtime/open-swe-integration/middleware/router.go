package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"
)

// CommandRouter handles routing commands to appropriate skills
type CommandRouter struct {
	middlewareChain *MiddlewareChain
	logger          *Logger
}

func NewCommandRouter(middlewareChain *MiddlewareChain, logger *Logger) *CommandRouter {
	return &CommandRouter{
		middlewareChain: middlewareChain,
		logger:          logger,
	}
}

// RouteCommand processes incoming commands through middleware
func (cr *CommandRouter) RouteCommand(ctx context.Context, source string, rawRequest interface{}) (*Response, error) {
	// Convert raw request to Request struct
	req, err := cr.parseRequest(source, rawRequest)
	if err != nil {
		return &Response{Status: "error", Error: fmt.Sprintf("failed to parse request: %v", err)}, err
	}

	// Process through middleware chain
	resp, err := cr.middlewareChain.Process(ctx, req)
	if err != nil {
		return resp, err
	}

	// Route to appropriate handler based on enriched data
	if resp.Status == "complete" {
		return resp, nil
	}

	// Continue processing based on request type
	return cr.routeToHandler(ctx, req, resp)
}

func (cr *CommandRouter) parseRequest(source string, rawRequest interface{}) (*Request, error) {
	req := &Request{
		Source:    source,
		Timestamp: time.Now().UTC(),
		RequestID: generateRequestID(),
	}

	switch source {
	case "slack":
		return cr.parseSlackRequest(rawRequest, req)
	case "linear":
		return cr.parseLinearRequest(rawRequest, req)
	default:
		return nil, fmt.Errorf("unsupported source: %s", source)
	}
}

func (cr *CommandRouter) parseSlackRequest(rawRequest interface{}, req *Request) (*Request, error) {
	data, ok := rawRequest.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid Slack request format")
	}

	req.Type = "command"
	req.Data = data

	// Extract user and channel information
	if eventType, ok := data["type"].(string); ok {
		switch eventType {
		case "url_verification":
			req.Type = "verification"
		case "event":
			if event, ok := data["event"].(map[string]interface{}); ok {
				if eventType, ok := event["type"].(string); ok {
					switch eventType {
					case "message":
						req.Type = "message"
						if user, ok := event["user"].(string); ok {
							req.UserID = user
						}
						if channel, ok := event["channel"].(string); ok {
							req.ChannelID = channel
						}
						if text, ok := event["text"].(string); ok {
							req.Data["command"] = text
						}
					case "app_mention":
						req.Type = "mention"
						if user, ok := event["user"].(string); ok {
							req.UserID = user
						}
						if channel, ok := event["channel"].(string); ok {
							req.ChannelID = channel
						}
						if text, ok := event["text"].(string); ok {
							req.Data["command"] = text
						}
					}
				}
			}
		}
	}

	return req, nil
}

func (cr *CommandRouter) parseLinearRequest(rawRequest interface{}, req *Request) (*Request, error) {
	data, ok := rawRequest.(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid Linear request format")
	}

	req.Type = "issue"
	req.Data = data

	// Extract issue information
	if action, ok := data["action"].(string); ok {
		req.Data["action"] = action
	}

	if issueData, ok := data["data"].(map[string]interface{}); ok {
		if title, ok := issueData["title"].(string); ok {
			req.Data["command"] = title
		}
		if id, ok := issueData["id"].(string); ok {
			req.Data["issue_id"] = id
		}
		if user, ok := issueData["assignee"].(map[string]interface{}); ok {
			if userID, ok := user["id"].(string); ok {
				req.UserID = userID
			}
		}
	}

	return req, nil
}

func (cr *CommandRouter) routeToHandler(ctx context.Context, req *Request, resp *Response) (*Response, error) {
	command, ok := req.Data["command"].(string)
	if !ok {
		return &Response{Status: "error", Error: "no command found"}, fmt.Errorf("no command found")
	}

	// Parse command and route to appropriate skill
	skillName, params := cr.parseCommand(command)

	cr.logger.Info("Routing command", "command", command, "skill", skillName, "request_id", req.RequestID)

	// Create skill execution request
	skillResp, err := cr.executeSkill(ctx, skillName, params, req)
	if err != nil {
		return &Response{Status: "error", Error: fmt.Sprintf("skill execution failed: %v", err)}, err
	}

	// Merge responses
	for k, v := range skillResp.Data {
		resp.Data[k] = v
	}
	resp.ProcessedBy = append(resp.ProcessedBy, skillName)

	return resp, nil
}

func (cr *CommandRouter) parseCommand(command string) (string, map[string]interface{}) {
	command = strings.ToLower(strings.TrimSpace(command))

	// Simple command parsing - in production, this would be more sophisticated
	commandMap := map[string]string{
		"deploy":      "deployment-strategy",
		"optimize":    "optimize-costs",
		"security":    "analyze-security",
		"secure":      "analyze-security",
		"scale":       "scale-resources",
		"monitor":     "check-cluster-health",
		"health":      "check-cluster-health",
		"troubleshoot": "diagnose-network",
		"debug":       "diagnose-network",
		"certificate": "manage-certificates",
		"cert":        "manage-certificates",
		"database":    "maintain-databases",
		"db":          "maintain-databases",
		"cluster":     "manage-kubernetes-cluster",
		"compliance":  "generate-compliance-report",
		"audit":       "audit-security-events",
		"secrets":     "rotate-secrets",
		"secret":      "rotate-secrets",
	}

	for keyword, skill := range commandMap {
		if strings.Contains(command, keyword) {
			return skill, cr.extractParameters(command, keyword)
		}
	}

	return "unknown", map[string]interface{}{"command": command}
}

func (cr *CommandRouter) extractParameters(command, keyword string) map[string]interface{} {
	params := make(map[string]interface{})
	
	// Extract environment for deploy commands
	if strings.Contains(command, "deploy") {
		if strings.Contains(command, "production") || strings.Contains(command, "prod") {
			params["environment"] = "production"
		} else if strings.Contains(command, "staging") {
			params["environment"] = "staging"
		} else if strings.Contains(command, "development") || strings.Contains(command, "dev") {
			params["environment"] = "development"
		}
	}

	// Extract service names
	services := []string{"frontend", "backend", "api", "database", "cache"}
	for _, service := range services {
		if strings.Contains(command, service) {
			params["service"] = service
			break
		}
	}

	return params
}

func (cr *CommandRouter) executeSkill(ctx context.Context, skillName string, params map[string]interface{}, req *Request) (*Response, error) {
	// Placeholder for skill execution
	// In production, this would invoke the actual skill via Temporal
	
	cr.logger.Info("Executing skill", "skill", skillName, "params", params, "request_id", req.RequestID)

	return &Response{
		Status: "complete",
		Data: map[string]interface{}{
			"skill_executed": skillName,
			"parameters":     params,
			"execution_id":   generateExecutionID(),
		},
	}, nil
}

// HTTP Handler for webhooks
type WebhookHandler struct {
	router *CommandRouter
	logger *Logger
}

func NewWebhookHandler(router *CommandRouter, logger *Logger) *WebhookHandler {
	return &WebhookHandler{
		router: router,
		logger: logger,
	}
}

func (wh *WebhookHandler) HandleSlackWebhook(w http.ResponseWriter, r *http.Request) {
	wh.logger.Info("Received Slack webhook")

	var rawRequest map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&rawRequest); err != nil {
		wh.logger.Error("Failed to decode Slack webhook", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	resp, err := wh.router.RouteCommand(ctx, "slack", rawRequest)
	if err != nil {
		wh.logger.Error("Failed to route Slack command", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (wh *WebhookHandler) HandleLinearWebhook(w http.ResponseWriter, r *http.Request) {
	wh.logger.Info("Received Linear webhook")

	var rawRequest map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&rawRequest); err != nil {
		wh.logger.Error("Failed to decode Linear webhook", "error", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	resp, err := wh.router.RouteCommand(ctx, "linear", rawRequest)
	if err != nil {
		wh.logger.Error("Failed to route Linear command", "error", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

// Utility functions
func generateRequestID() string {
	return fmt.Sprintf("req_%d", time.Now().UnixNano())
}

func generateExecutionID() string {
	return fmt.Sprintf("exec_%d", time.Now().UnixNano())
}

// SetupRoutes configures HTTP routes with middleware
func SetupRoutes(router *CommandRouter, logger *Logger) *mux.Router {
	r := mux.NewRouter()
	
	webhookHandler := NewWebhookHandler(router, logger)

	// Webhook endpoints
	r.HandleFunc("/webhooks/slack", webhookHandler.HandleSlackWebhook).Methods("POST")
	r.HandleFunc("/webhooks/linear", webhookHandler.HandleLinearWebhook).Methods("POST")

	// Health endpoints
	r.HandleFunc("/health", healthHandler).Methods("GET")
	r.HandleFunc("/ready", readyHandler).Methods("GET")

	return r
}
