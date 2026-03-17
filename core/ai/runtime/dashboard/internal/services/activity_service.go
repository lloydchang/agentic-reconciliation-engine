package services

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

type ActivityService struct {
	db     *sql.DB
	logger *zap.Logger
}

func NewActivityService(db *sql.DB, logger *zap.Logger) *ActivityService {
	return &ActivityService{
		db:     db,
		logger: logger,
	}
}

func (s *ActivityService) GetActivities(ctx context.Context, limit int) ([]models.Activity, error) {
	if limit <= 0 {
		limit = 50 // default limit
	}

	query := `
		SELECT id, type, agent_id, agent_name, message, timestamp
		FROM activities
		ORDER BY timestamp DESC
		LIMIT $1
	`

	rows, err := s.db.QueryContext(ctx, query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query activities: %w", err)
	}
	defer rows.Close()

	var activities []models.Activity
	for rows.Next() {
		var activity models.Activity

		err := rows.Scan(
			&activity.ID,
			&activity.Type,
			&activity.AgentID,
			&activity.AgentName,
			&activity.Message,
			&activity.Timestamp,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan activity: %w", err)
		}

		activities = append(activities, activity)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating activities: %w", err)
	}

	return activities, nil
}

func (s *ActivityService) CreateActivity(ctx context.Context, activity *models.Activity) error {
	query := `
		INSERT INTO activities (id, type, agent_id, agent_name, message, timestamp)
		VALUES ($1, $2, $3, $4, $5, $6)
	`

	activity.ID = uuid.New().String()
	if activity.Timestamp.IsZero() {
		activity.Timestamp = time.Now()
	}

	_, err := s.db.ExecContext(ctx, query,
		activity.ID,
		activity.Type,
		activity.AgentID,
		activity.AgentName,
		activity.Message,
		activity.Timestamp,
	)
	if err != nil {
		return fmt.Errorf("failed to create activity: %w", err)
	}

	return nil
}

func (s *ActivityService) CreateAgentActivity(ctx context.Context, agentID, agentName, activityType, message string) error {
	activity := &models.Activity{
		Type:      activityType,
		AgentID:   agentID,
		AgentName: agentName,
		Message:   message,
		Timestamp: time.Now(),
	}

	return s.CreateActivity(ctx, activity)
}

func (s *ActivityService) GetActivitiesByAgent(ctx context.Context, agentID string, limit int) ([]models.Activity, error) {
	if limit <= 0 {
		limit = 50 // default limit
	}

	query := `
		SELECT id, type, agent_id, agent_name, message, timestamp
		FROM activities
		WHERE agent_id = $1
		ORDER BY timestamp DESC
		LIMIT $2
	`

	rows, err := s.db.QueryContext(ctx, query, agentID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query agent activities: %w", err)
	}
	defer rows.Close()

	var activities []models.Activity
	for rows.Next() {
		var activity models.Activity

		err := rows.Scan(
			&activity.ID,
			&activity.Type,
			&activity.AgentID,
			&activity.AgentName,
			&activity.Message,
			&activity.Timestamp,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan activity: %w", err)
		}

		activities = append(activities, activity)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating activities: %w", err)
	}

	return activities, nil
}
