package services

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

type AgentService struct {
	db     *sql.DB
	logger *zap.Logger
}

func NewAgentService(db *sql.DB, logger *zap.Logger) *AgentService {
	return &AgentService{
		db:     db,
		logger: logger,
	}
}

func (s *AgentService) GetAgents(ctx context.Context) ([]models.Agent, error) {
	query := `
		SELECT id, name, language, status, backend, skills, last_activity, success_rate, created_at, updated_at
		FROM agents
		ORDER BY created_at DESC
	`

	rows, err := s.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query agents: %w", err)
	}
	defer rows.Close()

	var agents []models.Agent
	for rows.Next() {
		var agent models.Agent
		var skillsJSON []byte
		var lastActivity sql.NullTime

		err := rows.Scan(
			&agent.ID,
			&agent.Name,
			&agent.Language,
			&agent.Status,
			&agent.Backend,
			&skillsJSON,
			&lastActivity,
			&agent.SuccessRate,
			&agent.CreatedAt,
			&agent.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan agent: %w", err)
		}

		if len(skillsJSON) > 0 {
			if err := json.Unmarshal(skillsJSON, &agent.Skills); err != nil {
				s.logger.Error("failed to unmarshal skills", zap.Error(err))
				agent.Skills = []string{}
			}
		}

		if lastActivity.Valid {
			agent.LastActivity = &lastActivity.Time
		}

		agents = append(agents, agent)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating agents: %w", err)
	}

	return agents, nil
}

func (s *AgentService) GetAgent(ctx context.Context, id string) (*models.Agent, error) {
	query := `
		SELECT id, name, language, status, backend, skills, last_activity, success_rate, created_at, updated_at
		FROM agents
		WHERE id = $1
	`

	var agent models.Agent
	var skillsJSON []byte
	var lastActivity sql.NullTime

	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&agent.ID,
		&agent.Name,
		&agent.Language,
		&agent.Status,
		&agent.Backend,
		&skillsJSON,
		&lastActivity,
		&agent.SuccessRate,
		&agent.CreatedAt,
		&agent.UpdatedAt,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("agent not found")
		}
		return nil, fmt.Errorf("failed to query agent: %w", err)
	}

	if len(skillsJSON) > 0 {
		if err := json.Unmarshal(skillsJSON, &agent.Skills); err != nil {
			s.logger.Error("failed to unmarshal skills", zap.Error(err))
			agent.Skills = []string{}
		}
	}

	if lastActivity.Valid {
		agent.LastActivity = &lastActivity.Time
	}

	return &agent, nil
}

func (s *AgentService) CreateAgent(ctx context.Context, agent *models.Agent) (*models.Agent, error) {
	skillsJSON, err := json.Marshal(agent.Skills)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal skills: %w", err)
	}

	query := `
		INSERT INTO agents (id, name, language, status, backend, skills, last_activity, success_rate, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING created_at, updated_at
	`

	agent.ID = uuid.New().String()
	agent.CreatedAt = time.Now()
	agent.UpdatedAt = time.Now()

	err = s.db.QueryRowContext(ctx, query,
		agent.ID,
		agent.Name,
		agent.Language,
		agent.Status,
		agent.Backend,
		skillsJSON,
		agent.LastActivity,
		agent.SuccessRate,
	).Scan(&agent.CreatedAt, &agent.UpdatedAt)
	if err != nil {
		return nil, fmt.Errorf("failed to create agent: %w", err)
	}

	return agent, nil
}

func (s *AgentService) UpdateAgentStatus(ctx context.Context, id string, status string) error {
	query := `
		UPDATE agents
		SET status = $1, last_activity = NOW(), updated_at = NOW()
		WHERE id = $2
	`

	result, err := s.db.ExecContext(ctx, query, status, id)
	if err != nil {
		return fmt.Errorf("failed to update agent status: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("agent not found")
	}

	return nil
}

func (s *AgentService) StartAgent(ctx context.Context, id string) error {
	return s.UpdateAgentStatus(ctx, id, string(models.AgentStatusRunning))
}

func (s *AgentService) StopAgent(ctx context.Context, id string) error {
	return s.UpdateAgentStatus(ctx, id, string(models.AgentStatusStopped))
}

func (s *AgentService) RestartAgent(ctx context.Context, id string) error {
	// First stop, then start
	if err := s.StopAgent(ctx, id); err != nil {
		return err
	}
	return s.StartAgent(ctx, id)
}
