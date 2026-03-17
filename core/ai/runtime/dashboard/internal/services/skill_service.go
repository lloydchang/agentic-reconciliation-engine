package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

type SkillService struct {
	db     *sql.DB
	logger *zap.Logger
}

func NewSkillService(db *sql.DB, logger *zap.Logger) *SkillService {
	return &SkillService{
		db:     db,
		logger: logger,
	}
}

func (s *SkillService) GetSkills(ctx context.Context) ([]models.Skill, error) {
	query := `
		SELECT id, name, description, license, compatibility, metadata, created_at
		FROM skills
		ORDER BY name ASC
	`

	rows, err := s.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query skills: %w", err)
	}
	defer rows.Close()

	var skills []models.Skill
	for rows.Next() {
		var skill models.Skill
		var metadataJSON []byte

		err := rows.Scan(
			&skill.ID,
			&skill.Name,
			&skill.Description,
			&skill.License,
			&skill.Compatibility,
			&metadataJSON,
			&skill.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan skill: %w", err)
		}

		if len(metadataJSON) > 0 {
			if err := json.Unmarshal(metadataJSON, &skill.Metadata); err != nil {
				s.logger.Error("failed to unmarshal skill metadata", zap.Error(err))
				skill.Metadata = make(map[string]string)
			}
		} else {
			skill.Metadata = make(map[string]string)
		}

		skills = append(skills, skill)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating skills: %w", err)
	}

	return skills, nil
}

func (s *SkillService) GetSkill(ctx context.Context, name string) (*models.Skill, error) {
	query := `
		SELECT id, name, description, license, compatibility, metadata, created_at
		FROM skills
		WHERE name = $1
	`

	var skill models.Skill
	var metadataJSON []byte

	err := s.db.QueryRowContext(ctx, query, name).Scan(
		&skill.ID,
		&skill.Name,
		&skill.Description,
		&skill.License,
		&skill.Compatibility,
		&metadataJSON,
		&skill.CreatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("skill not found")
		}
		return nil, fmt.Errorf("failed to query skill: %w", err)
	}

	if len(metadataJSON) > 0 {
		if err := json.Unmarshal(metadataJSON, &skill.Metadata); err != nil {
			s.logger.Error("failed to unmarshal skill metadata", zap.Error(err))
			skill.Metadata = make(map[string]string)
		}
	} else {
		skill.Metadata = make(map[string]string)
	}

	return &skill, nil
}

func (s *SkillService) CreateSkill(ctx context.Context, skill *models.Skill) (*models.Skill, error) {
	metadataJSON, err := json.Marshal(skill.Metadata)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal metadata: %w", err)
	}

	query := `
		INSERT INTO skills (id, name, description, license, compatibility, metadata, created_at)
		VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
		RETURNING id, created_at
	`

	err = s.db.QueryRowContext(ctx, query,
		skill.Name,
		skill.Description,
		skill.License,
		skill.Compatibility,
		metadataJSON,
	).Scan(&skill.ID, &skill.CreatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to create skill: %w", err)
	}

	return skill, nil
}

func (s *SkillService) ExecuteSkill(ctx context.Context, skillName string, params map[string]interface{}) (interface{}, error) {
	// Get skill metadata to check autonomy level
	skill, err := s.GetSkill(ctx, skillName)
	if err != nil {
		return nil, fmt.Errorf("failed to get skill: %w", err)
	}

	// Check autonomy level from metadata
	autonomy := skill.Metadata["autonomy"]
	switch autonomy {
	case string(models.SkillAutonomyFullyAuto):
		return s.executeSkillDirectly(ctx, skill, params)
	case string(models.SkillAutonomyConditional):
		return s.executeSkillWithApproval(ctx, skill, params)
	case string(models.SkillAutonomyRequiresPR):
		return s.executeSkillWithPR(ctx, skill, params)
	default:
		return nil, fmt.Errorf("unknown autonomy level: %s", autonomy)
	}
}

func (s *SkillService) executeSkillDirectly(ctx context.Context, skill *models.Skill, params map[string]interface{}) (interface{}, error) {
	// TODO: Implement direct skill execution via Temporal
	s.logger.Info("Executing skill directly", zap.String("skill", skill.Name))
	return map[string]interface{}{
		"status":  "executed",
		"skill":   skill.Name,
		"message": "Skill executed directly",
	}, nil
}

func (s *SkillService) executeSkillWithApproval(ctx context.Context, skill *models.Skill, params map[string]interface{}) (interface{}, error) {
	// TODO: Implement skill execution with approval workflow
	s.logger.Info("Executing skill with approval", zap.String("skill", skill.Name))
	return map[string]interface{}{
		"status":  "pending_approval",
		"skill":   skill.Name,
		"message": "Skill execution pending approval",
	}, nil
}

func (s *SkillService) executeSkillWithPR(ctx context.Context, skill *models.Skill, params map[string]interface{}) (interface{}, error) {
	// TODO: Implement skill execution requiring PR
	s.logger.Info("Executing skill requiring PR", zap.String("skill", skill.Name))
	return map[string]interface{}{
		"status":  "requires_pr",
		"skill":   skill.Name,
		"message": "Skill execution requires PR approval",
	}, nil
}
