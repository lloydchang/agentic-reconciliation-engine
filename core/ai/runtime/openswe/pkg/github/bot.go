package github

import (
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

// GitHubBot handles GitHub integration for OpenSWE
type GitHubBot struct {
	config      *config.Config
	orchestrator *orchestrator.OpenSWEOrchestrator
	httpClient  *http.Client
	webhookSecret string
	appID       string
	privateKey  string
}

// GitHubWebhook represents a GitHub webhook payload
type GitHubWebhook struct {
	Action      string      `json:"action"`
	PullRequest *PullRequest `json:"pull_request,omitempty"`
	Issue       *Issue       `json:"issue,omitempty"`
	Comment     *Comment     `json:"comment,omitempty"`
	Repository  Repository  `json:"repository"`
	Sender      User        `json:"sender"`
}

// PullRequest represents a GitHub pull request
type PullRequest struct {
	ID     int    `json:"id"`
	Number int    `json:"number"`
	Title  string `json:"title"`
	Body   string `json:"body"`
	State  string `json:"state"`
	Head   Branch `json:"head"`
	Base   Branch `json:"base"`
	User   User   `json:"user"`
}

// Issue represents a GitHub issue
type Issue struct {
	ID     int    `json:"id"`
	Number int    `json:"number"`
	Title  string `json:"title"`
	Body   string `json:"body"`
	State  string `json:"state"`
	User   User   `json:"user"`
}

// Comment represents a GitHub comment
type Comment struct {
	ID   int    `json:"id"`
	Body string `json:"body"`
	User User   `json:"user"`
}

// Branch represents a Git branch
type Branch struct {
	Ref string     `json:"ref"`
	SHA string     `json:"sha"`
	Repo Repository `json:"repo"`
}

// Repository represents a GitHub repository
type Repository struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	FullName string `json:"full_name"`
	Owner    User   `json:"owner"`
}

// User represents a GitHub user
type User struct {
	ID    int    `json:"id"`
	Login string `json:"login"`
}

// NewGitHubBot creates a new GitHub bot
func NewGitHubBot(cfg *config.Config, orch *orchestrator.OpenSWEOrchestrator) *GitHubBot {
	return &GitHubBot{
		config:       cfg,
		orchestrator: orch,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		webhookSecret: cfg.Integrations.GitHub.WebhookSecret,
		appID:         cfg.Integrations.GitHub.AppID,
		privateKey:    cfg.Integrations.GitHub.PrivateKey,
	}
}

// HandleWebhook handles incoming GitHub webhooks
func (gb *GitHubBot) HandleWebhook(w http.ResponseWriter, r *http.Request) {
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

	// Verify GitHub signature
	if !gb.verifySignature(r.Header, body) {
		log.Printf("Invalid GitHub signature")
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var webhook GitHubWebhook
	if err := json.Unmarshal(body, &webhook); err != nil {
		log.Printf("Error parsing GitHub webhook: %v", err)
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}

	// Handle webhook based on type
	switch {
	case webhook.PullRequest != nil:
		go gb.handlePullRequest(webhook)
	case webhook.Issue != nil && webhook.Comment != nil:
		go gb.handleIssueComment(webhook)
	default:
		log.Printf("Unhandled webhook type")
	}

	w.WriteHeader(http.StatusOK)
}

// verifySignature verifies the GitHub webhook signature
func (gb *GitHubBot) verifySignature(header http.Header, body []byte) bool {
	signature := header.Get("X-Hub-Signature-256")
	if signature == "" {
		return false
	}

	// Remove "sha256=" prefix
	if !strings.HasPrefix(signature, "sha256=") {
		return false
	}
	signature = strings.TrimPrefix(signature, "sha256=")

	// Create HMAC-SHA256 signature
	mac := hmac.New(sha256.New, []byte(gb.webhookSecret))
	mac.Write(body)
	expectedSignature := hex.EncodeToString(mac.Sum(nil))

	return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

// handlePullRequest handles pull request events
func (gb *GitHubBot) handlePullRequest(webhook GitHubWebhook) {
	pr := webhook.PullRequest
	ctx := context.Background()

	log.Printf("Handling PR %d: %s", pr.Number, pr.Title)

	switch webhook.Action {
	case "opened", "synchronize", "reopened":
		gb.handlePROpened(ctx, webhook.Repository, pr)
	case "closed":
		if pr.Merged {
			gb.handlePRMerged(ctx, webhook.Repository, pr)
		}
	}
}

// handlePROpened handles when a PR is opened or updated
func (gb *GitHubBot) handlePROpened(ctx context.Context, repo Repository, pr *PullRequest) {
	// Create code review task
	task := &orchestrator.Task{
		Type: "code-review",
		Command: "review",
		Parameters: map[string]interface{}{
			"repository": repo.FullName,
			"pull_request": pr.Number,
			"title": pr.Title,
			"body": pr.Body,
			"head_sha": pr.Head.SHA,
			"base_sha": pr.Base.SHA,
		},
		Context: map[string]interface{}{
			"github_repo": repo.FullName,
			"pr_number": pr.Number,
			"pr_title": pr.Title,
		},
	}

	// Execute code review
	result, err := gb.orchestrator.ExecuteTask(ctx, task)
	if err != nil {
		log.Printf("Error executing code review: %v", err)
		gb.postComment(repo.FullName, pr.Number, fmt.Sprintf("❌ Code review failed: %v", err))
		return
	}

	// Post review comments
	if result.Comments != nil {
		for _, comment := range result.Comments {
			gb.postComment(repo.FullName, pr.Number, comment)
		}
	}

	// Update PR status
	if result.Status == "approved" {
		gb.postComment(repo.FullName, pr.Number, "✅ Code review passed!")
	} else {
		gb.postComment(repo.FullName, pr.Number, "⚠️ Code review completed with suggestions")
	}
}

// handlePRMerged handles when a PR is merged
func (gb *GitHubBot) handlePRMerged(ctx context.Context, repo Repository, pr *PullRequest) {
	// Create deployment task if needed
	if gb.shouldDeploy(pr.Body) {
		task := &orchestrator.Task{
			Type: "deployment",
			Command: "deploy",
			Parameters: map[string]interface{}{
				"repository": repo.FullName,
				"pull_request": pr.Number,
				"merge_commit": pr.Head.SHA,
			},
		}

		result, err := gb.orchestrator.ExecuteTask(ctx, task)
		if err != nil {
			log.Printf("Error executing deployment: %v", err)
			// Could create an issue or send notification here
		} else {
			log.Printf("Deployment completed: %s", result.Summary)
		}
	}
}

// handleIssueComment handles comments on issues/PRs
func (gb *GitHubBot) handleIssueComment(webhook GitHubWebhook) {
	comment := webhook.Comment
	issue := webhook.Issue

	// Check if comment mentions the bot
	if !strings.Contains(comment.Body, "@openswe") {
		return
	}

	ctx := context.Background()
	log.Printf("Handling issue comment on %s #%d", webhook.Repository.FullName, issue.Number)

	// Clean the comment text
	cleanComment := strings.Replace(comment.Body, "@openswe", "", 1)
	cleanComment = strings.TrimSpace(cleanComment)

	// Create task from comment
	task := &orchestrator.Task{
		Type: "general",
		Command: cleanComment,
		Parameters: map[string]interface{}{
			"repository": webhook.Repository.FullName,
			"issue_number": issue.Number,
			"comment_id": comment.ID,
			"user": comment.User.Login,
		},
		Context: map[string]interface{}{
			"github_repo": webhook.Repository.FullName,
			"issue_number": issue.Number,
			"comment": cleanComment,
		},
	}

	// Execute task
	result, err := gb.orchestrator.ExecuteTask(ctx, task)
	if err != nil {
		log.Printf("Error executing task from comment: %v", err)
		gb.postComment(webhook.Repository.FullName, issue.Number, fmt.Sprintf("❌ Error: %v", err))
		return
	}

	// Post result as comment
	gb.postComment(webhook.Repository.FullName, issue.Number, fmt.Sprintf("🤖 %s", result.Summary))
}

// shouldDeploy determines if a PR should trigger deployment
func (gb *GitHubBot) shouldDeploy(prBody string) bool {
	// Simple heuristic - can be enhanced
	return strings.Contains(strings.ToLower(prBody), "deploy") ||
		   strings.Contains(strings.ToLower(prBody), "release")
}

// postComment posts a comment to a GitHub issue/PR
func (gb *GitHubBot) postComment(repoFullName string, issueNumber int, body string) error {
	// TODO: Implement GitHub API call to post comment
	// This would require GitHub App authentication and API token

	// For now, just log the comment
	log.Printf("Would post comment to %s #%d: %s", repoFullName, issueNumber, body)

	// Placeholder for actual GitHub API implementation
	// comment := &github.IssueComment{
	//     Body: &body,
	// }
	// _, _, err := gb.githubClient.Issues.CreateComment(ctx, owner, repo, issueNumber, comment)

	return nil
}

// createPR creates a pull request
func (gb *GitHubBot) createPR(repoFullName, title, body, head, base string) error {
	// TODO: Implement GitHub API call to create PR
	log.Printf("Would create PR in %s: %s (%s -> %s)", repoFullName, title, head, base)

	// Placeholder for actual GitHub API implementation
	// pr := &github.NewPullRequest{
	//     Title: &title,
	//     Body:  &body,
	//     Head:  &head,
	//     Base:  &base,
	// }
	// _, _, err := gb.githubClient.PullRequests.Create(ctx, owner, repo, pr)

	return nil
}
