package types

import (
	"time"
)

// ResearchRequest represents a research request
type ResearchRequest struct {
	Query              string                 `json:"query"`
	ResearchType       string                 `json:"researchType"` // "deep", "quick", "comparative"
	MaxSources         int                    `json:"maxSources"`
	MaxDepth           int                    `json:"maxDepth"`
	IncludeKnowledgeGraph bool              `json:"includeKnowledgeGraph"`
	StreamEvents       bool                   `json:"streamEvents"`
	LLMProvider        string                 `json:"llmProvider"`
	LLMModel           string                 `json:"llmModel"`
	Context            map[string]interface{} `json:"context"`
}

// ResearchState represents the state of a research workflow
type ResearchState struct {
	Query              string                 `json:"query"`
	ResearchType       string                 `json:"researchType"`
	CurrentPhase       string                 `json:"currentPhase"`
	Status             string                 `json:"status"`
	Sources            []ResearchSource       `json:"sources"`
	KnowledgeGraph     []KnowledgeNode        `json:"knowledgeGraph"`
	Findings           []ResearchFinding      `json:"findings"`
	Synthesis          string                 `json:"synthesis"`
	StartTime          time.Time              `json:"startTime"`
	EndTime            time.Time              `json:"endTime"`
	LLMProvider        string                 `json:"llmProvider"`
	LLMModel           string                 `json:"llmModel"`
	Context            map[string]interface{} `json:"context"`
	EventStream        []ResearchEvent        `json:"eventStream"`
	AgentCollaboration []AgentContribution    `json:"agentCollaboration"`
}

// ResearchSource represents a research source
type ResearchSource struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	URL         string                 `json:"url"`
	Content     string                 `json:"content"`
	Relevance   float64                `json:"relevance"`
	Credibility float64                `json:"credibility"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// KnowledgeNode represents a node in the knowledge graph
type KnowledgeNode struct {
	ID          string                 `json:"id"`
	Label       string                 `json:"label"`
	Type        string                 `json:"type"`
	Properties  map[string]interface{} `json:"properties"`
	Relationships []KnowledgeEdge      `json:"relationships"`
	CreatedAt   time.Time              `json:"createdAt"`
}

// KnowledgeEdge represents a relationship in the knowledge graph
type KnowledgeEdge struct {
	ID         string                 `json:"id"`
	Source     string                 `json:"source"`
	Target     string                 `json:"target"`
	Type       string                 `json:"type"`
	Weight     float64                `json:"weight"`
	Properties map[string]interface{} `json:"properties"`
}

// ResearchFinding represents a research finding
type ResearchFinding struct {
	ID          string                 `json:"id"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Confidence  float64                `json:"confidence"`
	Sources     []string               `json:"sources"`
	Category    string                 `json:"category"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ResearchEvent represents an event in the research process
type ResearchEvent struct {
	ID        string                 `json:"id"`
	Type      string                 `json:"type"`
	Message   string                 `json:"message"`
	Timestamp time.Time              `json:"timestamp"`
	Data      map[string]interface{} `json:"data"`
}

// AgentContribution represents an agent's contribution to research
type AgentContribution struct {
	AgentID    string                 `json:"agentId"`
	AgentType  string                 `json:"agentType"`
	Contribution string               `json:"contribution"`
	Confidence float64                `json:"confidence"`
	Timestamp  time.Time              `json:"timestamp"`
	Sources    []string               `json:"sources"`
}
