package services

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/lloydchang/gitops-infra-control-plane/core/ai/runtime/dashboard/internal/models"
	"go.uber.org/zap"
)

type EvaluationService struct {
	client  *http.Client
	baseURL string
	logger  *zap.Logger
}

func NewEvaluationService(logger *zap.Logger) *EvaluationService {
	return &EvaluationService{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
		baseURL: "http://localhost:8081", // Default evaluation API URL
		logger:  logger,
	}
}

// SetBaseURL updates the evaluation API base URL
func (s *EvaluationService) SetBaseURL(url string) {
	s.baseURL = url
}

// GetHealthEvaluation fetches health evaluation results
func (s *EvaluationService) GetHealthEvaluation(ctx context.Context) (*models.EvaluationHealth, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/health", s.baseURL)
	
	resp, err := s.client.Get(url)
	if err != nil {
		s.logger.Error("Failed to fetch health evaluation", zap.Error(err))
		return nil, fmt.Errorf("failed to fetch health evaluation: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		s.logger.Error("Failed to read response body", zap.Error(err))
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		s.logger.Error("Failed to unmarshal health response", zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	return s.parseHealthResponse(response), nil
}

// GetMonitoringEvaluation fetches monitoring evaluation results
func (s *EvaluationService) GetMonitoringEvaluation(ctx context.Context) (*models.EvaluationMonitoring, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/monitoring", s.baseURL)
	
	resp, err := s.client.Get(url)
	if err != nil {
		s.logger.Error("Failed to fetch monitoring evaluation", zap.Error(err))
		return nil, fmt.Errorf("failed to fetch monitoring evaluation: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		s.logger.Error("Failed to read response body", zap.Error(err))
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		s.logger.Error("Failed to unmarshal monitoring response", zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	return s.parseMonitoringResponse(response), nil
}

// GetIssues fetches detected issues
func (s *EvaluationService) GetIssues(ctx context.Context) ([]models.EvaluationIssue, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/issues", s.baseURL)
	
	resp, err := s.client.Get(url)
	if err != nil {
		s.logger.Error("Failed to fetch issues", zap.Error(err))
		return nil, fmt.Errorf("failed to fetch issues: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		s.logger.Error("Failed to read response body", zap.Error(err))
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		s.logger.Error("Failed to unmarshal issues response", zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	return s.parseIssuesResponse(response), nil
}

// GetAutoFixStatus fetches auto-fix status
func (s *EvaluationService) GetAutoFixStatus(ctx context.Context) (*models.AutoFixStatus, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/auto-fix", s.baseURL)
	
	resp, err := s.client.Get(url)
	if err != nil {
		s.logger.Error("Failed to fetch auto-fix status", zap.Error(err))
		return nil, fmt.Errorf("failed to fetch auto-fix status: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		s.logger.Error("Failed to read response body", zap.Error(err))
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		s.logger.Error("Failed to unmarshal auto-fix response", zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	return s.parseAutoFixResponse(response), nil
}

// GetSummary fetches comprehensive evaluation summary
func (s *EvaluationService) GetSummary(ctx context.Context) (*models.EvaluationSummary, error) {
	url := fmt.Sprintf("%s/api/v1/evaluation/summary", s.baseURL)
	
	resp, err := s.client.Get(url)
	if err != nil {
		s.logger.Error("Failed to fetch evaluation summary", zap.Error(err))
		return nil, fmt.Errorf("failed to fetch evaluation summary: %w", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		s.logger.Error("Failed to read response body", zap.Error(err))
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		s.logger.Error("Failed to unmarshal summary response", zap.Error(err))
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}
	
	return s.parseSummaryResponse(response), nil
}

// Helper methods for parsing responses

func (s *EvaluationService) parseHealthResponse(response map[string]interface{}) *models.EvaluationHealth {
	health := &models.EvaluationHealth{
		Timestamp: time.Now(),
	}
	
	if data, ok := response["data"].(map[string]interface{}); ok {
		if workerHealth, exists := data["worker_health"]; exists {
			if workerMap, ok := workerHealth.(map[string]interface{}); ok {
				health.WorkerHealth = workerMap
			}
		}
		
		if conversationHealth, exists := data["conversation_health"]; exists {
			if convMap, ok := conversationHealth.(map[string]interface{}); ok {
				health.ConversationHealth = convMap
			}
		}
		
		if overallHealth, exists := data["overall_health_status"]; exists {
			if overallStr, ok := overallHealth.(string); ok {
				health.OverallHealth = overallStr
			}
		}
		
		if recommendations, exists := data["recommendations"]; exists {
			if recList, ok := recommendations.([]interface{}); ok {
				for _, rec := range recList {
					if recStr, ok := rec.(string); ok {
						health.Recommendations = append(health.Recommendations, recStr)
					}
				}
			}
		}
	}
	
	return health
}

func (s *EvaluationService) parseMonitoringResponse(response map[string]interface{}) *models.EvaluationMonitoring {
	monitoring := &models.EvaluationMonitoring{
		Timestamp: time.Now(),
	}
	
	if data, ok := response["data"].(map[string]interface{}); ok {
		if infraHealth, exists := data["infrastructure_health"]; exists {
			if infraMap, ok := infraHealth.(map[string]interface{}); ok {
				monitoring.InfrastructureHealth = infraMap
			}
		}
		
		if temporalHealth, exists := data["temporal_health"]; exists {
			if temporalMap, ok := temporalHealth.(map[string]interface{}); ok {
				monitoring.TemporalHealth = temporalMap
			}
		}
		
		if agentHealth, exists := data["agent_health"]; exists {
			if agentMap, ok := agentHealth.(map[string]interface{}); ok {
				monitoring.AgentHealth = agentMap
			}
		}
		
		if correlationID, exists := data["correlation_id"]; exists {
			if corrStr, ok := correlationID.(string); ok {
				monitoring.CorrelationID = corrStr
			}
		}
		
		if totalIssues, exists := data["total_issues"]; exists {
			if totalInt, ok := totalIssues.(float64); ok {
				monitoring.TotalIssues = int(totalInt)
			}
		}
	}
	
	return monitoring
}

func (s *EvaluationService) parseIssuesResponse(response map[string]interface{}) []models.EvaluationIssue {
	var issues []models.EvaluationIssue
	
	if data, ok := response["data"].(map[string]interface{}); ok {
		if issueList, exists := data["issues"]; exists {
			if issueSlice, ok := issueList.([]interface{}); ok {
				for _, issue := range issueSlice {
					if issueMap, ok := issue.(map[string]interface{}); ok {
						evalIssue := models.EvaluationIssue{
							Timestamp: time.Now(),
						}
						
						if id, exists := issueMap["id"]; exists {
							if idStr, ok := id.(string); ok {
								evalIssue.ID = idStr
							}
						}
						
						if issueType, exists := issueMap["type"]; exists {
							if typeStr, ok := issueType.(string); ok {
								evalIssue.Type = typeStr
							}
						}
						
						if severity, exists := issueMap["severity"]; exists {
							if severityStr, ok := severity.(string); ok {
								evalIssue.Severity = severityStr
							}
						}
						
						if description, exists := issueMap["description"]; exists {
							if descStr, ok := description.(string); ok {
								evalIssue.Description = descStr
							}
						}
						
						if target, exists := issueMap["target"]; exists {
							if targetStr, ok := target.(string); ok {
								evalIssue.Target = targetStr
							}
						}
						
						if metrics, exists := issueMap["metrics"]; exists {
							if metricsMap, ok := metrics.(map[string]interface{}); ok {
								evalIssue.Metrics = metricsMap
							}
						}
						
						issues = append(issues, evalIssue)
					}
				}
			}
		}
	}
	
	return issues
}

func (s *EvaluationService) parseAutoFixResponse(response map[string]interface{}) *models.AutoFixStatus {
	autoFix := &models.AutoFixStatus{
		Timestamp: time.Now(),
	}
	
	if data, ok := response["data"].(map[string]interface{}); ok {
		if totalFixes, exists := data["total_fixes"]; exists {
			if totalInt, ok := totalFixes.(float64); ok {
				autoFix.TotalFixes = int(totalInt)
			}
		}
		
		if fixHistory, exists := data["fix_history"]; exists {
			if historySlice, ok := fixHistory.([]interface{}); ok {
				for _, fix := range historySlice {
					if fixMap, ok := fix.(map[string]interface{}); ok {
						attempt := models.AutoFixAttempt{
							Timestamp: time.Now(),
						}
						
						if timestamp, exists := fixMap["timestamp"]; exists {
							if timeStr, ok := timestamp.(string); ok {
								if parsedTime, err := time.Parse(time.RFC3339, timeStr); err == nil {
									attempt.Timestamp = parsedTime
								}
							}
						}
						
						if action, exists := fixMap["action"]; exists {
							if actionStr, ok := action.(string); ok {
								attempt.Action = actionStr
							}
						}
						
						if target, exists := fixMap["target"]; exists {
							if targetStr, ok := target.(string); ok {
								attempt.Target = targetStr
							}
						}
						
						if success, exists := fixMap["success"]; exists {
							if successBool, ok := success.(bool); ok {
								attempt.Success = successBool
							}
						}
						
						if errorMessage, exists := fixMap["error_message"]; exists {
							if errorStr, ok := errorMessage.(string); ok {
								attempt.ErrorMessage = errorStr
							}
						}
						
						autoFix.FixHistory = append(autoFix.FixHistory, attempt)
					}
				}
			}
		}
		
		if backoffPeriods, exists := data["backoff_periods"]; exists {
			if backoffMap, ok := backoffPeriods.(map[string]interface{}); ok {
				autoFix.BackoffPeriods = backoffMap
			}
		}
	}
	
	return autoFix
}

func (s *EvaluationService) parseSummaryResponse(response map[string]interface{}) *models.EvaluationSummary {
	summary := &models.EvaluationSummary{
		Timestamp: time.Now(),
	}
	
	if data, ok := response["data"].(map[string]interface{}); ok {
		if summaryData, exists := data["summary"]; exists {
			if summaryMap, ok := summaryData.(map[string]interface{}); ok {
				summary.Summary = summaryMap
			}
		}
		
		if evaluatorResults, exists := data["evaluator_results"]; exists {
			if resultsMap, ok := evaluatorResults.(map[string]interface{}); ok {
				summary.EvaluatorResults = resultsMap
			}
		}
		
		if traceCount, exists := data["trace_count"]; exists {
			if traceInt, ok := traceCount.(float64); ok {
				summary.TraceCount = int(traceInt)
			}
		}
		
		if evaluatorsRun, exists := data["evaluators_run"]; exists {
			if evaluatorList, ok := evaluatorsRun.([]interface{}); ok {
				for _, evaluator := range evaluatorList {
					if evalStr, ok := evaluator.(string); ok {
						summary.EvaluatorsRun = append(summary.EvaluatorsRun, evalStr)
					}
				}
			}
		}
	}
	
	return summary
}
