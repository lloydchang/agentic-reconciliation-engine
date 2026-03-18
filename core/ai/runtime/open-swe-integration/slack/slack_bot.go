package slack

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/slack-go/slack"
	"github.com/slack-go/slack/slackevents"
	"github.com/slack-go/slack/socketmode"

	"gitops-infra-control-plane/core/ai/runtime/open-swe-integration/shared"
)

// SlackBot handles Slack bot interactions
type SlackBot struct {
	client     *slack.Client
	socket     *socketmode.Client
	dispatcher shared.TriggerDispatcher
	botUserID  string
	repoMap    map[string]shared.RepoMapping // channel -> repo mapping
}

// NewSlackBot creates a new Slack bot instance
func NewSlackBot(botToken, appToken string, dispatcher shared.TriggerDispatcher) (*SlackBot, error) {
	client := slack.New(
		botToken,
		slack.OptionDebug(true),
		slack.OptionLog(nil), // Add proper logging later
	)

	socket := socketmode.New(
		client,
		socketmode.OptionDebug(true),
	)

	bot := &SlackBot{
		client:     client,
		socket:     socket,
		dispatcher: dispatcher,
		repoMap:    make(map[string]shared.RepoMapping),
	}

	// Get bot user ID
	auth, err := client.AuthTest()
	if err != nil {
		return nil, fmt.Errorf("failed to authenticate: %w", err)
	}
	bot.botUserID = auth.UserID

	return bot, nil
}

// Start begins the Slack bot event loop
func (b *SlackBot) Start(ctx context.Context) error {
	// Set up event handlers
	go b.handleEvents(ctx)

	// Start socket mode client
	return b.socket.Run()
}

// handleEvents processes incoming Slack events
func (b *SlackBot) handleEvents(ctx context.Context) {
	for envelope := range b.socket.Events {
		switch envelope.Type {
		case socketmode.EventTypeEventsAPI:
			eventPayload := envelope.Data.(slackevents.EventsAPIEvent)
			if err := b.handleEventAPI(ctx, eventPayload); err != nil {
				fmt.Printf("Error handling event: %v\n", err)
			}

		case socketmode.EventTypeInteractive:
			callback := envelope.Data.(slack.InteractionCallback)
			if err := b.handleInteraction(ctx, callback); err != nil {
				fmt.Printf("Error handling interaction: %v\n", err)
			}
		}

		b.socket.Ack(*envelope.EnvelopeID, nil)
	}
}

// handleEventAPI processes Events API events
func (b *SlackBot) handleEventAPI(ctx context.Context, event slackevents.EventsAPIEvent) error {
	switch ev := event.InnerEvent.Data.(type) {
	case *slackevents.AppMentionEvent:
		return b.handleAppMention(ctx, ev)
	case *slackevents.MessageEvent:
		return b.handleMessage(ctx, ev)
	default:
		// Ignore other event types
		return nil
	}
}

// handleAppMention processes @bot mentions
func (b *SlackBot) handleAppMention(ctx context.Context, event *slackevents.AppMentionEvent) error {
	// Check if this is a command for us
	text := strings.TrimSpace(strings.Replace(event.Text, fmt.Sprintf("<@%s>", b.botUserID), "", -1))

	if b.isAgentCommand(text) {
		return b.handleAgentCommand(ctx, event, text)
	}

	return nil
}

// handleMessage processes regular messages (for threads)
func (b *SlackBot) handleMessage(ctx context.Context, event *slackevents.MessageEvent) error {
	// Only process messages in threads where we've been mentioned
	if event.ThreadTimestamp == "" {
		return nil
	}

	// Check if we're mentioned in this message
	if !strings.Contains(event.Text, fmt.Sprintf("<@%s>", b.botUserID)) {
		return nil
	}

	text := strings.TrimSpace(strings.Replace(event.Text, fmt.Sprintf("<@%s>", b.botUserID), "", -1))

	if b.isAgentCommand(text) {
		return b.handleAgentCommand(ctx, &slackevents.AppMentionEvent{
			Text:            event.Text,
			User:            event.User,
			Channel:         event.Channel,
			Timestamp:       event.Timestamp,
			ThreadTimestamp: event.ThreadTimestamp,
		}, text)
	}

	return nil
}

// handleAgentCommand processes agent commands from Slack
func (b *SlackBot) handleAgentCommand(ctx context.Context, event interface{}, commandText string) error {
	var channelID, userID, timestamp, threadTS string

	// Extract common fields based on event type
	switch e := event.(type) {
	case *slackevents.AppMentionEvent:
		channelID = e.Channel
		userID = e.User
		timestamp = e.Timestamp
		if e.ThreadTimestamp != "" {
			threadTS = e.ThreadTimestamp
		} else {
			threadTS = e.Timestamp
		}
	case *slackevents.MessageEvent:
		channelID = e.Channel
		userID = e.User
		timestamp = e.Timestamp
		if e.ThreadTimestamp != "" {
			threadTS = e.ThreadTimestamp
		} else {
			threadTS = e.Timestamp
		}
	}

	// Get repository mapping for this channel
	repoMapping, exists := b.repoMap[channelID]
	if !exists {
		// Try to extract repo from command text (e.g., "repo:owner/name")
		if extractedRepo := b.extractRepoFromCommand(commandText); extractedRepo.Owner != "" {
			repoMapping = extractedRepo
		} else {
			// Use default repository
			repoMapping = shared.RepoMapping{
				Owner:    "my-org",
				Name:     "default-repo",
				Token:    "${GITHUB_TOKEN}",
				BasePath: ".",
			}
		}
	}

	// Get user info
	user, err := b.client.GetUserInfo(userID)
	if err != nil {
		fmt.Printf("Failed to get user info: %v\n", err)
	}

	userEmail := ""
	if user != nil {
		userEmail = user.Profile.Email
	}

	// Create trigger event
	triggerEvent := shared.TriggerEvent{
		ID:         fmt.Sprintf("slack-command-%s-%d", timestamp, time.Now().Unix()),
		Platform:   "slack",
		Type:       "command",
		Action:     "execute",
		UserID:     userID,
		UserEmail:  userEmail,
		Repository: repoMapping,
		Timestamp:  time.Now(),
		Data: map[string]interface{}{
			"channel_id":      channelID,
			"thread_ts":       threadTS,
			"command_text":    commandText,
			"command":         b.parseCommand(commandText),
			"slack_user_id":   userID,
			"slack_timestamp": timestamp,
		},
	}

	// Send initial response
	b.sendThreadResponse(channelID, threadTS, "🤖 Processing your request...")

	// Dispatch the event
	if err := b.dispatcher.Dispatch(ctx, triggerEvent); err != nil {
		b.sendThreadResponse(channelID, threadTS, fmt.Sprintf("❌ Error: %v", err))
		return err
	}

	return nil
}

// handleInteraction processes interactive components (buttons, etc.)
func (b *SlackBot) handleInteraction(ctx context.Context, callback slack.InteractionCallback) error {
	// Handle approval/rejection buttons
	action := callback.ActionCallback.AttachmentActions[0]

	switch action.Name {
	case "approve":
		return b.handleApproval(ctx, callback, true)
	case "reject":
		return b.handleApproval(ctx, callback, false)
	case "status":
		return b.handleStatusRequest(ctx, callback)
	}

	return nil
}

// handleApproval processes approval/rejection actions
func (b *SlackBot) handleApproval(ctx context.Context, callback slack.InteractionCallback, approved bool) error {
	// Extract workflow ID from callback value
	workflowID := callback.ActionCallback.AttachmentActions[0].Value

	// Create approval event
	triggerEvent := shared.TriggerEvent{
		ID:         fmt.Sprintf("slack-approval-%s-%d", workflowID, time.Now().Unix()),
		Platform:   "slack",
		Type:       "approval",
		Action:     map[bool]string{true: "approve", false: "reject"}[approved],
		UserID:     callback.User.ID,
		UserEmail:  callback.User.Name, // Slack doesn't provide email in callback
		Timestamp:  time.Now(),
		Data: map[string]interface{}{
			"workflow_id": workflowID,
			"approved":    approved,
			"channel_id":  callback.Channel.ID,
			"message_ts":  callback.MessageTs,
		},
	}

	return b.dispatcher.Dispatch(ctx, triggerEvent)
}

// handleStatusRequest processes status check requests
func (b *SlackBot) handleStatusRequest(ctx context.Context, callback slack.InteractionCallback) error {
	workflowID := callback.ActionCallback.AttachmentActions[0].Value

	// Create status request event
	triggerEvent := shared.TriggerEvent{
		ID:         fmt.Sprintf("slack-status-%s-%d", workflowID, time.Now().Unix()),
		Platform:   "slack",
		Type:       "status",
		Action:     "check",
		UserID:     callback.User.ID,
		UserEmail:  callback.User.Name,
		Timestamp:  time.Now(),
		Data: map[string]interface{}{
			"workflow_id": workflowID,
			"channel_id":  callback.Channel.ID,
			"message_ts":  callback.MessageTs,
		},
	}

	return b.dispatcher.Dispatch(ctx, triggerEvent)
}

// SetChannelMapping sets the repository mapping for a Slack channel
func (b *SlackBot) SetChannelMapping(channelID string, mapping shared.RepoMapping) {
	b.repoMap[channelID] = mapping
}

// SendStatusUpdate sends a status update to a Slack thread
func (b *SlackBot) SendStatusUpdate(channelID, threadTS, status string) error {
	return b.sendThreadResponse(channelID, threadTS, status)
}

// SendApprovalRequest sends an approval request with buttons
func (b *SlackBot) SendApprovalRequest(channelID, threadTS, workflowID, message string) error {
	attachment := slack.Attachment{
		Text:       message,
		CallbackID: fmt.Sprintf("approval-%s", workflowID),
		Actions: []slack.AttachmentAction{
			{
				Name:  "approve",
				Text:  "✅ Approve",
				Type:  "button",
				Value: workflowID,
				Style: "primary",
			},
			{
				Name:  "reject",
				Text:  "❌ Reject",
				Type:  "button",
				Value: workflowID,
				Style: "danger",
			},
			{
				Name:  "status",
				Text:  "📊 Status",
				Type:  "button",
				Value: workflowID,
			},
		},
	}

	_, _, err := b.client.PostMessage(
		channelID,
		slack.MsgOptionTS(threadTS),
		slack.MsgOptionAttachments(attachment),
	)

	return err
}

// Helper methods

func (b *SlackBot) isAgentCommand(text string) bool {
	// Check for common agent command patterns
	commandPrefixes := []string{
		"help",
		"deploy",
		"status",
		"analyze",
		"review",
		"create",
		"update",
		"fix",
		"optimize",
	}

	text = strings.ToLower(text)
	for _, prefix := range commandPrefixes {
		if strings.HasPrefix(text, prefix) {
			return true
		}
	}

	return false
}

func (b *SlackBot) parseCommand(text string) map[string]interface{} {
	// Simple command parsing - can be enhanced
	return map[string]interface{}{
		"text": text,
		"type": "general",
	}
}

func (b *SlackBot) extractRepoFromCommand(text string) shared.RepoMapping {
	// Look for repo:owner/name pattern
	if idx := strings.Index(text, "repo:"); idx >= 0 {
		repoStr := text[idx+5:]
		if slashIdx := strings.Index(repoStr, "/"); slashIdx > 0 {
			owner := strings.TrimSpace(repoStr[:slashIdx])
			name := strings.TrimSpace(repoStr[slashIdx+1:])
			if spaceIdx := strings.Index(name, " "); spaceIdx > 0 {
				name = name[:spaceIdx]
			}

			return shared.RepoMapping{
				Owner:    owner,
				Name:     name,
				Token:    "${GITHUB_TOKEN}",
				BasePath: ".",
			}
		}
	}

	return shared.RepoMapping{}
}

func (b *SlackBot) sendThreadResponse(channelID, threadTS, message string) error {
	_, _, err := b.client.PostMessage(
		channelID,
		slack.MsgOptionTS(threadTS),
		slack.MsgOptionText(message, false),
	)
	return err
}
