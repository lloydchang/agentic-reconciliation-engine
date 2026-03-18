package main

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"
)

// SlackEvent represents a Slack event payload
type SlackEvent struct {
	Type      string `json:"type"`
	Event     Event  `json:"event,omitempty"`
	Challenge string `json:"challenge,omitempty"`
	Token     string `json:"token,omitempty"`
}

type Event struct {
	Type    string `json:"type"`
	Text    string `json:"text"`
	User    string `json:"user"`
	Channel string `json:"channel"`
	Ts      string `json:"ts"`
	ThreadTs string `json:"thread_ts,omitempty"`
}

// SlackCommand represents a parsed GitOps command
type SlackCommand struct {
	Action       string
	Parameters   map[string]string
	User         string
	Channel      string
	ThreadID     string
	MessageID    string
	RawText      string
}

// SlackResponse represents a response to send back to Slack
type SlackResponse struct {
	Text         string `json:"text"`
	ResponseType string `json:"response_type,omitempty"` // "in_channel" or "ephemeral"
	Attachments  []Attachment `json:"attachments,omitempty"`
}

type Attachment struct {
	Text  string `json:"text"`
	Color string `json:"color,omitempty"`
}

// SlackIntegration handles Slack webhook processing
type SlackIntegration struct {
	botToken      string
	signingSecret string
	commandRouter *CommandRouter
	memoryAgent   *MemoryAgentClient
	temporalClient *TemporalClient
}

// NewSlackIntegration creates a new Slack integration
func NewSlackIntegration(botToken, signingSecret string) *SlackIntegration {
	return &SlackIntegration{
		botToken:      botToken,
		signingSecret: signingSecret,
		commandRouter: NewCommandRouter(),
		memoryAgent:   NewMemoryAgentClient(),
		temporalClient: NewTemporalClient(),
	}
}

// HandleWebhook processes incoming Slack webhooks
func (s *SlackIntegration) HandleWebhook(w http.ResponseWriter, r *http.Request) {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Failed to read request body", http.StatusBadRequest)
		return
	}

	// Verify Slack request signature
	if !s.verifySignature(r.Header, body) {
		http.Error(w, "Invalid signature", http.StatusUnauthorized)
		return
	}

	var event SlackEvent
	if err := json.Unmarshal(body, &event); err != nil {
		http.Error(w, "Failed to parse JSON", http.StatusBadRequest)
		return
	}

	// Handle Slack URL verification challenge
	if event.Challenge != "" {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"challenge": event.Challenge})
		return
	}

	// Handle Slack events
	if event.Type == "event_callback" {
		go s.handleEvent(event.Event)
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

// handleEvent processes individual Slack events
func (s *SlackIntegration) handleEvent(event Event) {
	if event.Type != "app_mention" {
		return
	}

	// Parse the command from the message text
	command, err := s.parseCommand(event)
	if err != nil {
		log.Printf("Failed to parse command: %v", err)
		s.sendResponse(event.Channel, &SlackResponse{
			Text:         fmt.Sprintf("Sorry, I couldn't understand that command. Error: %v", err),
			ResponseType: "ephemeral",
		})
		return
	}

	// Acknowledge receipt
	s.sendResponse(event.Channel, &SlackResponse{
		Text:         fmt.Sprintf("Processing your request: `%s`", command.RawText),
		ResponseType: "in_channel",
	})

	// Route the command to appropriate GitOps skill
	go s.routeCommand(command)
}

// parseCommand extracts GitOps commands from Slack messages
func (s *SlackIntegration) parseCommand(event Event) (*SlackCommand, error) {
	// Remove the bot mention from the text
	text := strings.TrimSpace(event.Text)
	text = strings.TrimPrefix(text, "<@"+event.User+">") // Remove user mention if present
	text = strings.TrimSpace(text)

	if text == "" {
		return nil, fmt.Errorf("empty command")
	}

	// Basic command parsing - can be enhanced with NLP later
	parts := strings.Fields(text)
	if len(parts) == 0 {
		return nil, fmt.Errorf("no command provided")
	}

	action := strings.ToLower(parts[0])
	parameters := make(map[string]string)

	// Simple parameter extraction
	for i := 1; i < len(parts); i++ {
		part := parts[i]
		if strings.Contains(part, ":") {
			kv := strings.SplitN(part, ":", 2)
			if len(kv) == 2 {
				parameters[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
			}
		}
	}

	return &SlackCommand{
		Action:     action,
		Parameters: parameters,
		User:       event.User,
		Channel:    event.Channel,
		ThreadID:   event.ThreadTs,
		MessageID:  event.Ts,
		RawText:    text,
	}, nil
}

// routeCommand routes parsed commands to GitOps skills
func (s *SlackIntegration) routeCommand(command *SlackCommand) {
	ctx := context.Background()

	// Create a unique thread ID for this conversation
	threadID := s.generateThreadID(command)

	// Get context from memory agent
	memoryContext, err := s.memoryAgent.GetContext(ctx, threadID)
	if err != nil {
		log.Printf("Failed to get memory context: %v", err)
	}

	// Route to appropriate skill based on command
	skillName, err := s.commandRouter.RouteCommand(command.Action)
	if err != nil {
		s.sendResponse(command.Channel, &SlackResponse{
			Text:         fmt.Sprintf("Unknown command: %s", command.Action),
			ResponseType: "ephemeral",
		})
		return
	}

	// Create Temporal workflow for the GitOps operation
	workflowID := fmt.Sprintf("slack-%s-%d", threadID, time.Now().Unix())

	err = s.temporalClient.StartWorkflow(ctx, workflowID, skillName, map[string]interface{}{
		"command":       command,
		"memoryContext": memoryContext,
		"threadID":      threadID,
	})

	if err != nil {
		s.sendResponse(command.Channel, &SlackResponse{
			Text:         fmt.Sprintf("Failed to start workflow: %v", err),
			ResponseType: "ephemeral",
		})
		return
	}

	// Send initial response
	s.sendResponse(command.Channel, &SlackResponse{
		Text:         fmt.Sprintf("✅ Started GitOps workflow for: `%s`\nWorkflow ID: `%s`", command.RawText, workflowID),
		ResponseType: "in_channel",
	})
}

// sendResponse sends a message back to Slack
func (s *SlackIntegration) sendResponse(channel string, response *SlackResponse) {
	payload := map[string]interface{}{
		"channel": channel,
		"text":    response.Text,
	}

	if response.ResponseType != "" {
		payload["response_type"] = response.ResponseType
	}

	if len(response.Attachments) > 0 {
		payload["attachments"] = response.Attachments
	}

	jsonPayload, _ := json.Marshal(payload)

	req, _ := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewBuffer(jsonPayload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+s.botToken)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Failed to send Slack response: %v", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Slack API error: %d", resp.StatusCode)
	}
}

// verifySignature verifies Slack request signatures
func (s *SlackIntegration) verifySignature(header http.Header, body []byte) bool {
	timestamp := header.Get("X-Slack-Request-Timestamp")
	signature := header.Get("X-Slack-Signature")

	if timestamp == "" || signature == "" {
		return false
	}

	// Check timestamp to prevent replay attacks
	ts, err := time.ParseInt(timestamp, 10, 64)
	if err != nil {
		return false
	}

	now := time.Now().Unix()
	if now-ts > 300 { // 5 minutes
		return false
	}

	// Create signature
	baseString := fmt.Sprintf("v0:%s:%s", timestamp, string(body))
	hash := hmac.New(sha256.New, []byte(s.signingSecret))
	hash.Write([]byte(baseString))
	expectedSignature := "v0=" + hex.EncodeToString(hash.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// generateThreadID creates a unique thread identifier
func (s *SlackIntegration) generateThreadID(command *SlackCommand) string {
	if command.ThreadID != "" {
		return fmt.Sprintf("slack-thread-%s", command.ThreadID)
	}
	return fmt.Sprintf("slack-msg-%s", command.MessageID)
}

// Start starts the Slack integration server
func (s *SlackIntegration) Start(port string) error {
	r := mux.NewRouter()
	r.HandleFunc("/webhooks/slack", s.HandleWebhook).Methods("POST")

	log.Printf("Starting Slack integration on port %s", port)
	return http.ListenAndServe(":"+port, r)
}
