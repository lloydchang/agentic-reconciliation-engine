package linear

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"agentic-reconciliation-engine/core/ai/runtime/open-swe-integration/shared"
)

// LinearClient handles Linear API interactions
type LinearClient struct {
	apiKey     string
	baseURL    string
	httpClient *http.Client
}

// NewLinearClient creates a new Linear API client
func NewLinearClient(apiKey string) *LinearClient {
	return &LinearClient{
		apiKey:  apiKey,
		baseURL: "https://api.linear.app/graphql",
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// LinearIssue represents a Linear issue
type LinearIssue struct {
	ID          string    `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	State       State     `json:"state"`
	Assignee    User      `json:"assignee"`
	Creator     User      `json:"creator"`
	Team        Team      `json:"team"`
	Labels      []Label   `json:"labels"`
	Comments    []Comment `json:"comments"`
	Priority    int       `json:"priority"`
	CreatedAt   time.Time `json:"createdAt"`
	UpdatedAt   time.Time `json:"updatedAt"`
}

// State represents a Linear workflow state
type State struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Type string `json:"type"`
}

// User represents a Linear user
type User struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Email    string `json:"email"`
	AvatarURL string `json:"avatarUrl"`
}

// Team represents a Linear team
type Team struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Key  string `json:"key"`
}

// Label represents a Linear label
type Label struct {
	ID   string `json:"id"`
	Name string `json:"name"`
}

// Comment represents a Linear comment
type Comment struct {
	ID        string    `json:"id"`
	Body      string    `json:"body"`
	User      User      `json:"user"`
	CreatedAt time.Time `json:"createdAt"`
}

// GetIssue retrieves an issue by ID
func (c *LinearClient) GetIssue(issueID string) (*LinearIssue, error) {
	query := `
		query GetIssue($id: String!) {
			issue(id: $id) {
				id
				title
				description
				state {
					id
					name
					type
				}
				assignee {
					id
					name
					email
				}
				creator {
					id
					name
					email
				}
				team {
					id
					name
					key
				}
				labels {
					id
					name
				}
				comments {
					id
					body
					user {
						id
						name
						email
					}
					createdAt
				}
				priority
				createdAt
				updatedAt
			}
		}
	`

	variables := map[string]interface{}{
		"id": issueID,
	}

	var response struct {
		Data struct {
			Issue LinearIssue `json:"issue"`
		} `json:"data"`
	}

	if err := c.executeQuery(query, variables, &response); err != nil {
		return nil, fmt.Errorf("failed to get issue: %w", err)
	}

	return &response.Data.Issue, nil
}

// CreateComment adds a comment to an issue
func (c *LinearClient) CreateComment(issueID, body string) error {
	query := `
		mutation CreateComment($issueId: String!, $body: String!) {
			commentCreate(input: {
				issueId: $issueId,
				body: $body
			}) {
				success
				comment {
					id
				}
			}
		}
	`

	variables := map[string]interface{}{
		"issueId": issueID,
		"body":    body,
	}

	var response struct {
		Data struct {
			CommentCreate struct {
				Success bool `json:"success"`
				Comment struct {
					ID string `json:"id"`
				} `json:"comment"`
			} `json:"commentCreate"`
		} `json:"data"`
	}

	if err := c.executeQuery(query, variables, &response); err != nil {
		return fmt.Errorf("failed to create comment: %w", err)
	}

	if !response.Data.CommentCreate.Success {
		return fmt.Errorf("comment creation failed")
	}

	return nil
}

// UpdateIssueState changes the state of an issue
func (c *LinearClient) UpdateIssueState(issueID, stateID string) error {
	query := `
		mutation UpdateIssue($issueId: String!, $stateId: String!) {
			issueUpdate(id: $issueId, input: {
				stateId: $stateId
			}) {
				success
			}
		}
	`

	variables := map[string]interface{}{
		"issueId": issueID,
		"stateId": stateID,
	}

	var response struct {
		Data struct {
			IssueUpdate struct {
				Success bool `json:"success"`
			} `json:"issueUpdate"`
		} `json:"data"`
	}

	if err := c.executeQuery(query, variables, &response); err != nil {
		return fmt.Errorf("failed to update issue state: %w", err)
	}

	if !response.Data.IssueUpdate.Success {
		return fmt.Errorf("issue state update failed")
	}

	return nil
}

// executeQuery performs a GraphQL query against the Linear API
func (c *LinearClient) executeQuery(query string, variables map[string]interface{}, result interface{}) error {
	requestBody := map[string]interface{}{
		"query":     query,
		"variables": variables,
	}

	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", c.baseURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", c.apiKey)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(body))
	}

	if err := json.NewDecoder(resp.Body).Decode(result); err != nil {
		return fmt.Errorf("failed to decode response: %w", err)
	}

	return nil
}
