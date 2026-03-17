package models

import (
	"time"
)

// Skill reflects the agentskills.io standard fields plus
// project-specific metadata stored under the metadata key.
type Skill struct {
	ID            string            `json:"id" db:"id"`
	Name          string            `json:"name" db:"name"`
	Description   string            `json:"description" db:"description"`
	License       string            `json:"license,omitempty" db:"license"`
	Compatibility string            `json:"compatibility,omitempty" db:"compatibility"`
	// Project-specific metadata (stored under metadata: in SKILL.md frontmatter)
	Metadata      map[string]string `json:"metadata" db:"metadata"`
	CreatedAt     time.Time         `json:"createdAt" db:"created_at"`
}

// SkillMetadata are project-specific keys stored under metadata: in SKILL.md
type SkillMetadata struct {
	RiskLevel  string `json:"risk_level"`   // low, medium, high
	Autonomy   string `json:"autonomy"`     // fully_auto, conditional, requires_PR
	Layer      string `json:"layer"`        // temporal, gitops
	HumanGate  string `json:"human_gate,omitempty"`
}

type SkillRiskLevel string

const (
	SkillRiskLevelLow    SkillRiskLevel = "low"
	SkillRiskLevelMedium SkillRiskLevel = "medium"
	SkillRiskLevelHigh   SkillRiskLevel = "high"
)

type SkillAutonomy string

const (
	SkillAutonomyFullyAuto  SkillAutonomy = "fully_auto"
	SkillAutonomyConditional SkillAutonomy = "conditional"
	SkillAutonomyRequiresPR SkillAutonomy = "requires_PR"
)

type SkillLayer string

const (
	SkillLayerTemporal SkillLayer = "temporal"
	SkillLayerGitOps   SkillLayer = "gitops"
)
