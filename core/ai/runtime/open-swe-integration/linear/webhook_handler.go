package linear

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"agentic-reconciliation-engine/core/ai/runtime/open-swe-integration/shared"
)

// WebhookHandler handles Linear webhook events
type WebhookHandler struct {
	client      *LinearClient
	mapper      *TeamRepoMapper
	dispatcher  shared.TriggerDispatcher
	webhookSecret string
}

// NewWebhookHandler creates a new Linear webhook handler
func NewWebhookHandler(client *LinearClient, mapper *TeamRepoMapper, dispatcher shared.TriggerDispatcher, webhookSecret string) *WebhookHandler {
	return &WebhookHandler{
		client:        client,
		mapper:        mapper,
		dispatcher:    dispatcher,
		webhookSecret: webhookSecret,
	}
}

// HandleWebhook processes incoming Linear webhook events
func (h *WebhookHandler) HandleWebhook(w http.ResponseWriter, r *http.Request) {
	// Verify webhook signature
	if !h.verifySignature(r) {
		http.Error(w, "Invalid signature", http.StatusUnauthorized)
		return
	}

	// Read request body
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read request body", http.StatusBadRequest)
		return
	}

	// Parse webhook payload
	var payload WebhookPayload
	if err := json.Unmarshal(body, &payload); err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	// Process the webhook event
	if err := h.processEvent(r.Context(), &payload); err != nil {
		fmt.Printf("Error processing webhook event: %v\n", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

// WebhookPayload represents the structure of a Linear webhook payload
type WebhookPayload struct {
	Action string      `json:"action"`
	Type   string      `json:"type"`
	Data   interface{} `json:"data"`
}

// processEvent handles different types of Linear webhook events
func (h *WebhookHandler) processEvent(ctx context.Context, payload *WebhookPayload) error {
	switch payload.Type {
	case "Issue":
		return h.handleIssueEvent(ctx, payload)
	case "Comment":
		return h.handleCommentEvent(ctx, payload)
	case "Project":
		return h.handleProjectEvent(ctx, payload)
	default:
		// Log unknown event type but don't fail
		fmt.Printf("Received unknown webhook event type: %s\n", payload.Type)
		return nil
	}
}

// handleIssueEvent processes issue-related webhook events
func (h *WebhookHandler) handleIssueEvent(ctx context.Context, payload *WebhookPayload) error {
	// Extract issue data
	issueData, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid issue data format")
	}

	issueID, ok := issueData["id"].(string)
	if !ok {
		return fmt.Errorf("missing issue ID")
	}

	teamID, ok := issueData["teamId"].(string)
	if !ok {
		return fmt.Errorf("missing team ID")
	}

	// Get repository mapping for the team
	repoMapping, exists := h.mapper.GetMapping(teamID)
	if !exists {
		// No mapping found, skip processing
		fmt.Printf("No repository mapping found for team %s, skipping issue %s\n", teamID, issueID)
		return nil
	}

	// Get full issue details
	issue, err := h.client.GetIssue(issueID)
	if err != nil {
		return fmt.Errorf("failed to get issue details: %w", err)
	}

	// Create trigger event
	triggerEvent := shared.TriggerEvent{
		ID:          fmt.Sprintf("linear-issue-%s-%d", issueID, time.Now().Unix()),
		Platform:    "linear",
		Type:        "issue",
		Action:      payload.Action,
		UserID:      issue.Creator.ID,
		UserEmail:   issue.Creator.Email,
		Repository:  repoMapping,
		Timestamp:   time.Now(),
		Data: map[string]interface{}{
			"issue_id":    issue.ID,
			"title":       issue.Title,
			"description": issue.Description,
			"state":       issue.State.Name,
			"priority":    issue.Priority,
			"team":        issue.Team.Name,
			"labels":      h.extractLabelNames(issue.Labels),
		},
	}

	// Dispatch the event
	return h.dispatcher.Dispatch(ctx, triggerEvent)
}

// handleCommentEvent processes comment-related webhook events
func (h *WebhookHandler) handleCommentEvent(ctx context.Context, payload *WebhookPayload) error {
	// Extract comment data
	commentData, ok := payload.Data.(map[string]interface{})
	if !ok {
		return fmt.Errorf("invalid comment data format")
	}

	commentID, ok := commentData["id"].(string)
	if !ok {
		return fmt.Errorf("missing comment ID")
	}

	issueID, ok := commentData["issueId"].(string)
	if !ok {
		return fmt.Errorf("missing issue ID")
	}

	userID, ok := commentData["userId"].(string)
	if !ok {
		return fmt.Errorf("missing user ID")
	}

	body, ok := commentData["body"].(string)
	if !ok {
		return fmt.Errorf("missing comment body")
	}

	// Get issue details to find team mapping
	issue, err := h.client.GetIssue(issueID)
	if err != nil {
		return fmt.Errorf("failed to get issue details for comment: %w", err)
	}

	// Get repository mapping for the team
	repoMapping, exists := h.mapper.GetMapping(issue.Team.ID)
	if !exists {
		// No mapping found, skip processing
		fmt.Printf("No repository mapping found for team %s, skipping comment %s\n", issue.Team.ID, commentID)
		return nil
	}

	// Check if this is a command for the agent
	if h.isAgentCommand(body) {
		// Create trigger event for agent command
		triggerEvent := shared.TriggerEvent{
			ID:          fmt.Sprintf("linear-comment-%s-%d", commentID, time.Now().Unix()),
			Platform:    "linear",
			Type:        "comment",
			Action:      "command",
			UserID:      userID,
			UserEmail:   issue.Creator.Email, // Use issue creator as fallback
			Repository:  repoMapping,
			Timestamp:   time.Now(),
			Data: map[string]interface{}{
				"comment_id":  commentID,
				"issue_id":    issueID,
				"issue_title": issue.Title,
				"body":        body,
				"command":     h.extractCommand(body),
			},
		}

		return h.dispatcher.Dispatch(ctx, triggerEvent)
	}

	return nil
}

// handleProjectEvent processes project-related webhook events
func (h *WebhookHandler) handleProjectEvent(ctx context.Context, payload *WebhookPayload) error {
	// For now, we mainly care about issues and comments
	// Project events could be used for team mapping updates in the future
	fmt.Printf("Received project event: %s\n", payload.Action)
	return nil
}

// verifySignature verifies the webhook signature using HMAC-SHA256
func (h *WebhookHandler) verifySignature(r *http.Request) bool {
	signature := r.Header.Get("X-Linear-Signature")
	if signature == "" {
		return false
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		return false
	}

	// Restore body for later use
	r.Body = io.NopCloser(strings.NewReader(string(body)))

	mac := hmac.New(sha256.New, []byte(h.webhookSecret))
	mac.Write(body)
	expectedSignature := "sha256=" + hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// isAgentCommand checks if a comment body contains an agent command
func (h *WebhookHandler) isAgentCommand(body string) bool {
	// Check for common agent command prefixes
	commandPrefixes := []string{
		"@gitops-agent",
		"@agent",
		"/agent",
	}

	body = strings.ToLower(body)
	for _, prefix := range commandPrefixes {
		if strings.Contains(body, prefix) {
			return true
		}
	}

	return false
}

// extractCommand extracts the command text from a comment body
func (h *WebhookHandler) extractCommand(body string) string {
	// Remove the agent mention and return the rest
	commandPrefixes := []string{
		"@gitops-agent",
		"@agent",
		"/agent",
	}

	for _, prefix := range commandPrefixes {
		if idx := strings.Index(strings.ToLower(body), prefix); idx >= 0 {
			return strings.TrimSpace(body[idx+len(prefix):])
		}
	}

	return body
}

// extractLabelNames extracts label names from a slice of labels
func (h *WebhookHandler) extractLabelNames(labels []Label) []string {
	names := make([]string, len(labels))
	for i, label := range labels {
		names[i] = label.Name
	}
	return names
}
