package services

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

type SystemService struct {
	db     *sql.DB
	logger *zap.Logger
}

func NewSystemService(db *sql.DB, logger *zap.Logger) *SystemService {
	return &SystemService{
		db:     db,
		logger: logger,
	}
}

func (s *SystemService) GetSystemStatus(ctx context.Context) (*models.SystemStatus, error) {
	status := &models.SystemStatus{
		Status:      "healthy",
		Timestamp:   time.Now(),
		Version:     "1.0.0",
		Components:  make(map[string]string),
		Environment: "development",
	}

	// Check database health
	if s.db != nil {
		if err := s.db.Ping(); err != nil {
			status.Components["database"] = "unhealthy"
			status.Status = "degraded"
		} else {
			status.Components["database"] = "healthy"
		}
	} else {
		status.Components["database"] = "not_configured"
	}

	// TODO: Add checks for Temporal, Memory Agent, etc.
	status.Components["temporal"] = "healthy"
	status.Components["memory_agent"] = "healthy"

	return status, nil
}

func (s *SystemService) GetSystemMetrics(ctx context.Context) (*models.SystemMetrics, error) {
	metrics := &models.SystemMetrics{
		Timestamp: time.Now(),
	}

	// Get agent metrics
	if s.db != nil {
		s.logger.Info("Getting agent metrics from database")
		agentMetrics, err := s.getAgentMetrics(ctx)
		if err != nil {
			s.logger.Error("Failed to get agent metrics", zap.Error(err))
		} else {
			metrics.AgentMetrics = agentMetrics
			s.logger.Info("Agent metrics retrieved", zap.Int64("total", agentMetrics.Total))
		}

		skillMetrics, err := s.getSkillMetrics(ctx)
		if err != nil {
			s.logger.Error("Failed to get skill metrics", zap.Error(err))
		} else {
			metrics.SkillMetrics = skillMetrics
			s.logger.Info("Skill metrics retrieved", zap.Int64("total", skillMetrics.Total))
		}
	} else {
		s.logger.Error("Database connection is nil")
		// Default metrics when no database
		metrics.AgentMetrics = models.AgentMetrics{
			Total:   0,
			Running: 0,
			Idle:    0,
			Errored: 0,
			Stopped: 0,
		}
		metrics.SkillMetrics = models.SkillMetrics{
			Total:         0,
			Executions24h: 0,
			SuccessRate:   0.0,
			AvgDuration:   0.0,
		}
	}

	// Get performance metrics (mock for now)
	metrics.Performance = models.Performance{
		CPUUsage:    25.5,
		MemoryUsage: 45.2,
		DiskUsage:   60.1,
		NetworkIO:   12.3,
	}

	return metrics, nil
}

func (s *SystemService) getAgentMetrics(ctx context.Context) (models.AgentMetrics, error) {
	var metrics models.AgentMetrics

	// Test database connection
	var test int
	err := s.db.QueryRowContext(ctx, "SELECT 1").Scan(&test)
	if err != nil {
		s.logger.Error("Database connection test failed", zap.Error(err))
		return metrics, fmt.Errorf("database connection test failed: %w", err)
	}
	s.logger.Info("Database connection test passed", zap.Int("test", test))

	// Get total agents
	err = s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM agents").Scan(&metrics.Total)
	if err != nil {
		return metrics, fmt.Errorf("failed to get total agents: %w", err)
	}
	s.logger.Info("Got total agents", zap.Int64("total", metrics.Total))

	// Get agents by status
	statuses := []string{"running", "idle", "errored", "stopped"}
	counts := []*int64{&metrics.Running, &metrics.Idle, &metrics.Errored, &metrics.Stopped}

	for i, status := range statuses {
		err := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM agents WHERE status = $1", status).Scan(counts[i])
		if err != nil {
			s.logger.Error("Failed to get agent count by status", zap.String("status", status), zap.Error(err))
		} else {
			s.logger.Info("Got agent count by status", zap.String("status", status), zap.Int64("count", *counts[i]))
		}
	}

	return metrics, nil
}

func (s *SystemService) getSkillMetrics(ctx context.Context) (models.SkillMetrics, error) {
	var metrics models.SkillMetrics

	// Get total skills
	err := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM skills").Scan(&metrics.Total)
	if err != nil {
		return metrics, fmt.Errorf("failed to get total skills: %w", err)
	}

	// Get executions in last 24 hours
	err = s.db.QueryRowContext(ctx, `
		SELECT COUNT(*) FROM agent_executions 
		WHERE started_at >= NOW() - INTERVAL '24 hours'
	`).Scan(&metrics.Executions24h)
	if err != nil {
		s.logger.Error("Failed to get 24h executions", zap.Error(err))
	}

	// Get success rate
	var successful, total int64
	err = s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM agent_executions WHERE status = 'completed'").Scan(&successful)
	if err != nil {
		s.logger.Error("Failed to get successful executions", zap.Error(err))
	}

	err = s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM agent_executions").Scan(&total)
	if err != nil {
		s.logger.Error("Failed to get total executions", zap.Error(err))
	}

	if total > 0 {
		metrics.SuccessRate = float64(successful) / float64(total) * 100
	}

	// Get average duration (simplified)
	err = s.db.QueryRowContext(ctx, `
		SELECT COALESCE(AVG(EXTRACT(EPOCH FROM (completed_at - started_at))), 0) 
		FROM agent_executions 
		WHERE status = 'completed' AND completed_at IS NOT NULL
	`).Scan(&metrics.AvgDuration)
	if err != nil {
		s.logger.Error("Failed to get average duration", zap.Error(err))
	}

	return metrics, nil
}

func (s *SystemService) GetHealth(ctx context.Context) (*models.HealthCheck, error) {
	health := &models.HealthCheck{
		Status:    "healthy",
		Timestamp: time.Now(),
		Version:   "1.0.0",
		Checks:    make(map[string]string),
	}

	// Database check
	if s.db != nil {
		if err := s.db.Ping(); err != nil {
			health.Checks["database"] = "unhealthy: " + err.Error()
			health.Status = "unhealthy"
		} else {
			health.Checks["database"] = "healthy"
		}
	} else {
		health.Checks["database"] = "not_configured"
	}

	// TODO: Add checks for other components
	health.Checks["temporal"] = "healthy"
	health.Checks["memory_agent"] = "healthy"
	health.Checks["websocket"] = "healthy"

	return health, nil
}
