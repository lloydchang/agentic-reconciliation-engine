package slack

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

	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/config"
	"github.com/agentic-reconciliation-engine/openswe-orchestrator/pkg/orchestrator"
)

// SlackBot handles Slack integration for OpenSWE
type SlackBot struct {
	config         *config.Config
	orchestrator   *orchestrator.OpenSWEOrchestrator
	httpClient     *http.Client
	verificationToken string
	botToken       string
	botUserID      string
}

// SlackEvent represents a Slack event
type SlackEvent struct {
	Token       string    `json:"token"`
	TeamID      string    `json:"team_id"`
	APIAppID    string    `json:"api_app_id"`
	Event       SlackEventData `json:"event"`
	Type        string    `json:"type"`
	EventID     string    `json:"event_id"`
	EventTime   int64     `json:"event_time"`
	AuthedUsers []string  `json:"authed_users,omitempty"`
}

// SlackEventData represents the event data
type SlackEventData struct {
	Type      string `json:"type"`
	User      string `json:"user"`
	Text      string `json:"text"`
	Timestamp string `json:"ts"`
	Channel   string `json:"channel"`
	ChannelType string `json:"channel_type"`
	ThreadTS  string `json:"thread_ts,omitempty"`
	BotID     string `json:"bot_id,omitempty"`
}

// SlackMessage represents a message to send to Slack
type SlackMessage struct {
	Channel   string `json:"channel"`
	Text      string `json:"text,omitempty"`
	Blocks    []Block `json:"blocks,omitempty"`
	ThreadTS  string `json:"thread_ts,omitempty"`
	Username  string `json:"username,omitempty"`
	IconEmoji string `json:"icon_emoji,omitempty"`
}

// Block represents a Slack block
type Block struct {
	Type string    `json:"type"`
	Text *TextBlock `json:"text,omitempty"`
}

// TextBlock represents a text block
type TextBlock struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// NewSlackBot creates a new Slack bot
func NewSlackBot(cfg *config.Config, orch *orchestrator.OpenSWEOrchestrator) *SlackBot {
	return &SlackBot{
		config:       cfg,
		orchestrator: orch,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		verificationToken: cfg.Integrations.Slack.VerificationToken,
		botToken:          cfg.Integrations.Slack.BotToken,
		botUserID:         cfg.Integrations.Slack.BotUserID,
	}
}

// HandleEvent handles incoming Slack events
func (sb *SlackBot) HandleEvent(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	body, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("Error reading request body: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	// Verify Slack signature
	if !sb.verifySignature(r.Header, body) {
		log.Printf("Invalid Slack signature")
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var event SlackEvent
	if err := json.Unmarshal(body, &event); err != nil {
		log.Printf("Error parsing Slack event: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	// Handle URL verification challenge
	if event.Type == "url_verification" {
		challenge := r.FormValue("challenge")
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(challenge))
		return
	}

	// Handle events
	if event.Type == "event_callback" {
		go sb.handleEventCallback(event)
	}

	w.WriteHeader(http.StatusOK)
}

// verifySignature verifies the Slack request signature
func (sb *SlackBot) verifySignature(header http.Header, body []byte) bool {
	signature := header.Get("X-Slack-Signature")
	timestamp := header.Get("X-Slack-Request-Timestamp")

	if signature == "" || timestamp == "" {
		return false
	}

	// Check timestamp to prevent replay attacks
	ts, err := time.ParseInt(timestamp, 10, 64)
	if err != nil {
		return false
	}

	if time.Now().Unix()-ts > 300 { // 5 minutes
		return false
	}

	// Create signature base string
	baseString := fmt.Sprintf("v0:%s:%s", timestamp, string(body))

	// Create HMAC-SHA256 signature
	mac := hmac.New(sha256.New, []byte(sb.verificationToken))
	mac.Write([]byte(baseString))
	expectedSignature := "v0=" + hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// handleEventCallback handles event callbacks from Slack
func (sb *SlackBot) handleEventCallback(event SlackEvent) {
	switch event.Event.Type {
	case "app_mention":
		sb.handleAppMention(event)
	case "message":
		if event.Event.ChannelType == "im" && event.Event.BotID == "" {
			sb.handleDirectMessage(event)
		} else if event.Event.ThreadTS != "" && event.Event.BotID == "" {
			sb.handleThreadReply(event)
		}
	default:
		log.Printf("Unhandled event type: %s", event.Event.Type)
	}
}

// handleAppMention handles @mentions of the bot
func (sb *SlackBot) handleAppMention(event SlackEvent) {
	text := strings.TrimSpace(strings.Replace(event.Event.Text, fmt.Sprintf("<@%s>", sb.botUserID), "", 1))

	if strings.Contains(text, "deploy") || strings.Contains(text, "infrastructure") {
		sb.handleInfrastructureCommand(event, text)
	} else {
		sb.handleGeneralCommand(event, text)
	}
}

// handleDirectMessage handles direct messages to the bot
func (sb *SlackBot) handleDirectMessage(event SlackEvent) {
	text := strings.TrimSpace(event.Event.Text)

	if strings.Contains(text, "deploy") || strings.Contains(text, "infrastructure") {
		sb.handleInfrastructureCommand(event, text)
	} else {
		sb.handleGeneralCommand(event, text)
	}
}

// handleThreadReply handles replies in threads
func (sb *SlackBot) handleThreadReply(event SlackEvent) {
	// Handle follow-up messages in existing conversations
	log.Printf("Handling thread reply: %s", event.Event.Text)
	// TODO: Implement thread reply handling
}

// handleInfrastructureCommand handles infrastructure-related commands
func (sb *SlackBot) handleInfrastructureCommand(event SlackEvent, command string) {
	ctx := context.Background()

	// Send initial acknowledgment
	sb.sendMessage(event.Event.Channel, "🤖 Processing infrastructure command...", event.Event.ThreadTS)

	// Parse command and create task
	task, err := sb.parseInfrastructureCommand(command)
	if err != nil {
		sb.sendMessage(event.Event.Channel, fmt.Sprintf("❌ Error parsing command: %v", err), event.Event.ThreadTS)
		return
	}

	// Execute task using OpenSWE orchestrator
	result, err := sb.orchestrator.ExecuteTask(ctx, task)
	if err != nil {
		sb.sendMessage(event.Event.Channel, fmt.Sprintf("❌ Error executing task: %v", err), event.Event.ThreadTS)
		return
	}

	// Send result
	sb.sendMessage(event.Event.Channel, fmt.Sprintf("✅ Task completed: %s", result.Summary), event.Event.ThreadTS)
}

// handleGeneralCommand handles general commands
func (sb *SlackBot) handleGeneralCommand(event SlackEvent, command string) {
	ctx := context.Background()

	// Send initial acknowledgment
	sb.sendMessage(event.Event.Channel, "🤖 Processing command...", event.Event.ThreadTS)

	// Create general task
	task := &orchestrator.Task{
		Type:    "general",
		Command: command,
		Context: map[string]interface{}{
			"slack_channel": event.Event.Channel,
			"slack_user":    event.Event.User,
			"thread_ts":     event.Event.ThreadTS,
		},
	}

	// Execute task
	result, err := sb.orchestrator.ExecuteTask(ctx, task)
	if err != nil {
		sb.sendMessage(event.Event.Channel, fmt.Sprintf("❌ Error: %v", err), event.Event.ThreadTS)
		return
	}

	// Send result
	sb.sendMessage(event.Event.Channel, fmt.Sprintf("✅ %s", result.Summary), event.Event.ThreadTS)
}

// parseInfrastructureCommand parses infrastructure-related commands
func (sb *SlackBot) parseInfrastructureCommand(command string) (*orchestrator.Task, error) {
	// Simple command parsing - can be enhanced with NLP
	if strings.Contains(command, "deploy") {
		return &orchestrator.Task{
			Type: "infrastructure",
			Command: "deploy",
			Parameters: map[string]interface{}{
				"action": "deploy",
				"target": extractTarget(command),
			},
		}, nil
	}

	if strings.Contains(command, "status") {
		return &orchestrator.Task{
			Type: "infrastructure",
			Command: "status",
			Parameters: map[string]interface{}{
				"action": "status",
			},
		}, nil
	}

	return nil, fmt.Errorf("unsupported command: %s", command)
}

// extractTarget extracts the deployment target from command
func extractTarget(command string) string {
	// Simple target extraction - can be enhanced
	if strings.Contains(command, "staging") {
		return "staging"
	}
	if strings.Contains(command, "production") {
		return "production"
	}
	return "default"
}

// sendMessage sends a message to Slack
func (sb *SlackBot) sendMessage(channel, text, threadTS string) error {
	message := SlackMessage{
		Channel:  channel,
		Text:     text,
		ThreadTS: threadTS,
		Username: "OpenSWE Bot",
		IconEmoji: ":robot_face:",
	}

	jsonData, err := json.Marshal(message)
	if err != nil {
		return err
	}

	req, err := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+sb.botToken)

	resp, err := sb.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		log.Printf("Slack API error: %s", string(body))
		return fmt.Errorf("slack API error: %d", resp.StatusCode)
	}

	return nil
}
