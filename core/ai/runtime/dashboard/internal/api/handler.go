package api

import (
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/services"
	"github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/dashboard/internal/ws"
	"go.uber.org/zap"
)

type Handler struct {
	agentService      *services.AgentService
	skillService      *services.SkillService
	activityService   *services.ActivityService
	systemService     *services.SystemService
	evaluationService *services.EvaluationService
	wsHub            *ws.Hub
	logger           *zap.Logger
}

func NewHandler(
	agentService *services.AgentService,
	skillService *services.SkillService,
	activityService *services.ActivityService,
	systemService *services.SystemService,
	evaluationService *services.EvaluationService,
	wsHub *ws.Hub,
	logger *zap.Logger,
) *Handler {
	return &Handler{
		agentService:      agentService,
		skillService:      skillService,
		activityService:   activityService,
		systemService:     systemService,
		evaluationService: evaluationService,
		wsHub:            wsHub,
		logger:           logger,
	}
}

// Agent Management Endpoints
func (h *Handler) GetAgents(c *gin.Context) {
	agents, err := h.agentService.GetAgents(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get agents", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get agents"})
		return
	}

	c.JSON(http.StatusOK, agents)
}

func (h *Handler) GetAgent(c *gin.Context) {
	id := c.Param("id")
	
	agent, err := h.agentService.GetAgent(c.Request.Context(), id)
	if err != nil {
		h.logger.Error("Failed to get agent", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusNotFound, gin.H{"error": "Agent not found"})
		return
	}

	c.JSON(http.StatusOK, agent)
}

func (h *Handler) StartAgent(c *gin.Context) {
	id := c.Param("id")
	
	err := h.agentService.StartAgent(c.Request.Context(), id)
	if err != nil {
		h.logger.Error("Failed to start agent", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to start agent"})
		return
	}

	// Broadcast agent status update
	if agent, err := h.agentService.GetAgent(c.Request.Context(), id); err == nil {
		h.wsHub.BroadcastAgentStatus(*agent)
	}

	// Create activity
	h.activityService.CreateAgentActivity(c.Request.Context(), id, "Agent", "info", "Agent started")

	c.JSON(http.StatusOK, gin.H{"status": "started"})
}

func (h *Handler) StopAgent(c *gin.Context) {
	id := c.Param("id")
	
	err := h.agentService.StopAgent(c.Request.Context(), id)
	if err != nil {
		h.logger.Error("Failed to stop agent", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to stop agent"})
		return
	}

	// Broadcast agent status update
	if agent, err := h.agentService.GetAgent(c.Request.Context(), id); err == nil {
		h.wsHub.BroadcastAgentStatus(*agent)
	}

	// Create activity
	h.activityService.CreateAgentActivity(c.Request.Context(), id, "Agent", "info", "Agent stopped")

	c.JSON(http.StatusOK, gin.H{"status": "stopped"})
}

func (h *Handler) RestartAgent(c *gin.Context) {
	id := c.Param("id")
	
	err := h.agentService.RestartAgent(c.Request.Context(), id)
	if err != nil {
		h.logger.Error("Failed to restart agent", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to restart agent"})
		return
	}

	// Broadcast agent status update
	if agent, err := h.agentService.GetAgent(c.Request.Context(), id); err == nil {
		h.wsHub.BroadcastAgentStatus(*agent)
	}

	// Create activity
	h.activityService.CreateAgentActivity(c.Request.Context(), id, "Agent", "info", "Agent restarted")

	c.JSON(http.StatusOK, gin.H{"status": "restarted"})
}

// Skills Management Endpoints
func (h *Handler) GetSkills(c *gin.Context) {
	skills, err := h.skillService.GetSkills(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get skills", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get skills"})
		return
	}

	c.JSON(http.StatusOK, skills)
}

func (h *Handler) GetSkill(c *gin.Context) {
	id := c.Param("id")
	
	skill, err := h.skillService.GetSkill(c.Request.Context(), id)
	if err != nil {
		h.logger.Error("Failed to get skill", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusNotFound, gin.H{"error": "Skill not found"})
		return
	}

	c.JSON(http.StatusOK, skill)
}

func (h *Handler) ExecuteSkill(c *gin.Context) {
	id := c.Param("id")
	
	var params map[string]interface{}
	if err := c.ShouldBindJSON(&params); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid parameters"})
		return
	}

	result, err := h.skillService.ExecuteSkill(c.Request.Context(), id, params)
	if err != nil {
		h.logger.Error("Failed to execute skill", zap.String("id", id), zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to execute skill"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// System Endpoints
func (h *Handler) GetSystemStatus(c *gin.Context) {
	status, err := h.systemService.GetSystemStatus(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get system status", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get system status"})
		return
	}

	c.JSON(http.StatusOK, status)
}

func (h *Handler) GetSystemMetrics(c *gin.Context) {
	h.logger.Info("GetSystemMetrics handler called")
	
	// Test database connection directly
	if h.systemService != nil {
		h.logger.Info("SystemService is not nil")
	} else {
		h.logger.Error("SystemService is nil")
	}
	
	metrics, err := h.systemService.GetSystemMetrics(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get system metrics", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get system metrics"})
		return
	}
	h.logger.Info("System metrics retrieved successfully", zap.Int64("total_agents", metrics.AgentMetrics.Total))
	c.JSON(http.StatusOK, metrics)
}

func (h *Handler) GetEvaluationHealth(c *gin.Context) {
	health, err := h.evaluationService.GetHealthEvaluation(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get evaluation health", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get evaluation health"})
		return
	}

	c.JSON(http.StatusOK, health)
}

func (h *Handler) GetEvaluationMonitoring(c *gin.Context) {
	monitoring, err := h.evaluationService.GetMonitoringEvaluation(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get evaluation monitoring", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get evaluation monitoring"})
		return
	}

	c.JSON(http.StatusOK, monitoring)
}

func (h *Handler) GetEvaluationIssues(c *gin.Context) {
	issues, err := h.evaluationService.GetIssues(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get evaluation issues", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get evaluation issues"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"issues": issues, "total_count": len(issues)})
}

func (h *Handler) GetAutoFixStatus(c *gin.Context) {
	autoFix, err := h.evaluationService.GetAutoFixStatus(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get auto-fix status", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get auto-fix status"})
		return
	}

	c.JSON(http.StatusOK, autoFix)
}

func (h *Handler) GetEvaluationSummary(c *gin.Context) {
	summary, err := h.evaluationService.GetSummary(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get evaluation summary", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get evaluation summary"})
		return
	}

	c.JSON(http.StatusOK, summary)
}

func (h *Handler) GetHealth(c *gin.Context) {
	health, err := h.systemService.GetHealth(c.Request.Context())
	if err != nil {
		h.logger.Error("Failed to get health", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get health"})
		return
	}

	c.JSON(http.StatusOK, health)
}

// Activity Endpoints
func (h *Handler) GetActivities(c *gin.Context) {
	limit := 50 // default limit
	if l := c.Query("limit"); l != "" {
		if parsed, err := parseInt(l); err == nil && parsed > 0 {
			limit = parsed
		}
	}

	activities, err := h.activityService.GetActivities(c.Request.Context(), limit)
	if err != nil {
		h.logger.Error("Failed to get activities", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get activities"})
		return
	}

	c.JSON(http.StatusOK, activities)
}

func (h *Handler) HandleWebSocket(c *gin.Context) {
	h.wsHub.HandleWebSocket(c.Writer, c.Request)
}

func parseInt(s string) (int, error) {
	var result int
	_, err := fmt.Sscanf(s, "%d", &result)
	return result, err
}
