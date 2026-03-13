package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"
	"strings"

	"github.com/gorilla/mux"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
	"net/http/httputil"
	"net/url"
	
	// Import our custom packages
	"github.com/lloydchang/ai-agents-sandbox/backend/activities"
	"github.com/lloydchang/ai-agents-sandbox/backend/bedrock"
	"github.com/lloydchang/ai-agents-sandbox/backend/config"
	"github.com/lloydchang/ai-agents-sandbox/backend/emulators"
	"github.com/lloydchang/ai-agents-sandbox/backend/humanloop"
	"github.com/lloydchang/ai-agents-sandbox/backend/mcp"
	"github.com/lloydchang/ai-agents-sandbox/backend/monitoring"
	"github.com/lloydchang/ai-agents-sandbox/backend/multimodel"
	"github.com/lloydchang/ai-agents-sandbox/backend/performance"
	"github.com/lloydchang/ai-agents-sandbox/backend/ragai"
	"github.com/lloydchang/ai-agents-sandbox/backend/security"
	"github.com/lloydchang/ai-agents-sandbox/backend/skills"
	"github.com/lloydchang/ai-agents-sandbox/backend/websocket"
	"github.com/lloydchang/ai-agents-sandbox/backend/types"
	"github.com/lloydchang/ai-agents-sandbox/backend/workflows"
)

// CORS middleware
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept, Origin, Access-Control-Allow-Origin")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func HelloBackstageWorkflow(ctx workflow.Context, name string) (string, error) {
	options := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    5,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, options)

	var result string
	err := workflow.ExecuteActivity(ctx, FetchDataActivity, name).Get(ctx, &result)
	if err != nil {
		return "", err
	}

	err = workflow.ExecuteActivity(ctx, ProcessDataActivity, result).Get(ctx, &result)
	if err != nil {
		return "", err
	}

	return result, nil
}

func ComplianceCheckWorkflow(ctx workflow.Context, data string) (string, error) {
	options := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute,
		RetryPolicy: &temporal.RetryPolicy{
			InitialInterval:    time.Second,
			BackoffCoefficient: 2.0,
			MaximumInterval:    time.Minute,
			MaximumAttempts:    5,
		},
	}
	ctx = workflow.WithActivityOptions(ctx, options)

	var fetchedData string
	err := workflow.ExecuteActivity(ctx, FetchDataActivity, data).Get(ctx, &fetchedData)
	if err != nil {
		return "", err
	}

	var checkResult string
	err = workflow.ExecuteActivity(ctx, AgentCheckActivity, fetchedData).Get(ctx, &checkResult)
	if err != nil {
		return "", err
	}

	var aggregatedResult string
	err = workflow.ExecuteActivity(ctx, AggregateResultsActivity, []string{checkResult}).Get(ctx, &aggregatedResult)
	if err != nil {
		return "", err
	}

	// If issues found, wait for human review
	if aggregatedResult != "All Compliant" {
		// Set up signal channel for human approval
		approvalCh := workflow.GetSignalChannel(ctx, "human-approval")

		// Set up timer for 24 hours
		timerCtx, cancelTimer := workflow.WithCancel(ctx)
		timer := workflow.NewTimer(timerCtx, 24*time.Hour)

		selector := workflow.NewSelector(ctx)
		var approval string
		selector.AddReceive(approvalCh, func(c workflow.ReceiveChannel, more bool) {
			c.Receive(ctx, &approval)
			cancelTimer() // Cancel timer if approval received
		})
		selector.AddFuture(timer, func(f workflow.Future) {
			// Timer expired, default to rejected
			approval = "Rejected"
		})

		// Wait for either signal or timer
		selector.Select(ctx)

		return approval, nil
	}

	return "Approved", nil
}

func FetchDataActivity(ctx context.Context, name string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("FetchDataActivity", "name", name)
	return "Fetched data for " + name, nil
}

func ProcessDataActivity(ctx context.Context, data string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("ProcessDataActivity", "data", data)
	return "Processed: " + data, nil
}

func AgentCheckActivity(ctx context.Context, data string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("AgentCheckActivity", "data", data)
	// Simulate AI agent compliance check
	// In real implementation, call Azure Foundry or local AI API
	return "Compliant", nil
}

func AggregateResultsActivity(ctx context.Context, results []string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("AggregateResultsActivity", "results", results)
	// Aggregate compliance results
	compliantCount := 0
	for _, result := range results {
		if result == "Compliant" {
			compliantCount++
		}
	}
	if compliantCount == len(results) {
		return "All Compliant", nil
	}
	return "Issues Found", nil
}

func SimpleHumanReviewActivity(ctx context.Context, aggregatedResult string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("SimpleHumanReviewActivity", "aggregatedResult", aggregatedResult)
	// Mock human review - in real implementation, pause workflow and wait for signal
	if aggregatedResult == "All Compliant" {
		return "Approved", nil
	}
	return "Rejected", nil
}

func main() {
	// Load configuration
	cfg := config.DefaultConfig()
	configManager, err := config.NewConfigManager("config.json")
	if err != nil {
		log.Printf("Warning: Failed to load config file, using defaults: %v", err)
		configManager = &config.ConfigManager{}
		*configManager = config.ConfigManager{}
	} else {
		cfg = configManager.GetConfig()
	}

	// Initialize infrastructure emulator
	emulator := emulators.GetGlobalEmulator()
	log.Printf("Infrastructure emulator initialized")

	// Initialize skills service
	skillService := skills.NewSkillService("/Users/lloyd/github/antigravity/ai-agents-sandbox", "session-"+time.Now().Format("20060102150405"))
	log.Printf("Skills service initialized with %d skills", len(skillService.GetManager().ListSkills()))

	// Initialize monitoring system
	metricsCollector := monitoring.GetGlobalMetricsCollector()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start metrics collection
	go metricsCollector.Start(ctx, cfg.Monitoring.MetricsInterval)

	// Initialize performance optimization components
	concurrencyMgr := performance.GetGlobalConcurrencyManager()
	_ = performance.GetGlobalResourcePool()

	// Initialize security components
	_ = security.GetGlobalSecureCommunicationManager()
	auditLogger := security.GetGlobalAuditLogger()
	_ = security.GetGlobalDataProtectionManager()

	// Start performance monitoring
	go concurrencyMgr.ProcessQueue(ctx)

	// Initialize WebSocket handler (needed before worker registration)
	websocketHandler := websocket.NewWebSocketHandler()
	go websocketHandler.GetHub().Run()

	// Initialize Bedrock activities (needed before worker registration)
	bedrockActivities, err := activities.NewBedrockActivities("us-west-2")
	if err != nil {
		log.Printf("Warning: Bedrock activities unavailable (expected in local dev): %v", err)
		bedrockActivities = nil
	}

	// Initialize WebSocket activities (needed before worker registration)
	websocketActivities := activities.NewWebSocketActivities(websocketHandler.GetHub())

	// Initialize multi-model manager (needed before worker registration)
	bedrockClient, err := bedrock.NewBedrockClient("us-west-2")
	if err != nil {
		log.Printf("Warning: Bedrock client unavailable (expected in local dev): %v", err)
		bedrockClient = nil
	}
	multiModelManager := multimodel.NewMultiModelManager(bedrockClient)
	multiModelActivities := activities.NewMultiModelActivities(multiModelManager)
	
	// Initialize skill execution activities
	skillExecutionActivities := &activities.SkillExecutionActivities{
		SkillManager: skillService.GetManager(),
		Emulator:     emulator,
	}

	c, err := client.NewClient(client.Options{})
	if err != nil {
		log.Fatal("Unable to create client", err)
	}
	defer c.Close()

	w := worker.New(c, "ai-agent-task-queue", worker.Options{})

	// Register the HelloBackstage workflow and its activities
	w.RegisterWorkflow(HelloBackstageWorkflow)
	w.RegisterWorkflow(ComplianceCheckWorkflow)
	w.RegisterActivity(FetchDataActivity)
	w.RegisterActivity(ProcessDataActivity)
	w.RegisterActivity(AgentCheckActivity)
	w.RegisterActivity(AggregateResultsActivity)
	w.RegisterActivity(SimpleHumanReviewActivity)

	// Register enhanced workflows
	w.RegisterWorkflow(workflows.ConversationalAgentWorkflow)
	w.RegisterWorkflow(workflows.GoalBasedAgentWorkflow)
	w.RegisterWorkflow(workflows.ReActAgentWorkflow)
	w.RegisterWorkflow(workflows.DeepResearchWorkflow)
	w.RegisterWorkflow(humanloop.EnhancedHumanInTheLoopWorkflow)
	w.RegisterWorkflow(performance.OptimizedWorkflow)
	w.RegisterWorkflow(performance.PerformanceMonitoringWorkflow)
	w.RegisterWorkflow(security.SecureWorkflow)

	// Register enhanced activities
	w.RegisterActivity(activities.SecurityAgentActivityV2)
	w.RegisterActivity(activities.ComplianceAgentActivityV2)
	w.RegisterActivity(activities.CostOptimizationAgentActivityV2)
	w.RegisterActivity(activities.AggregateAgentResultsActivityV2)
	w.RegisterActivity(activities.GenerateComplianceReportActivityV2)
	w.RegisterActivity(activities.HumanReviewActivityV2)

	// Register AIAgentOrchestrationWorkflowV2
	w.RegisterWorkflow(workflows.AIAgentOrchestrationWorkflowV2)

	// Register conversation activities
	w.RegisterActivity(activities.ExecuteConversationTurnActivity)
	w.RegisterActivity(activities.GenerateConversationSummaryActivity)

	// Register MCP agent activities
	w.RegisterActivity(activities.GenerateAgentMessageActivity)
	w.RegisterActivity(activities.ExecuteMCPToolActivity)
	w.RegisterActivity(activities.GenerateAgentResponseActivity)
	w.RegisterActivity(activities.DiscoverGoalsActivity)
	w.RegisterActivity(activities.GetToolsForGoalActivity)
	w.RegisterActivity(activities.ListCategoriesActivity)
	w.RegisterActivity(activities.AnalyzeToolUsageActivity)
	w.RegisterActivity(activities.ValidateToolParametersActivity)

	// Register ReAct agent activities
	w.RegisterActivity(activities.GenerateReActThoughtActivity)
	w.RegisterActivity(activities.GenerateReActActionActivity)
	w.RegisterActivity(activities.GenerateReActObservationActivity)
	w.RegisterActivity(activities.AnalyzeReActPerformanceActivity)
	w.RegisterActivity(activities.ValidateReActStepActivity)

	// Register research activities
	w.RegisterActivity(activities.GenerateResearchPlanActivity)
	w.RegisterActivity(activities.DiscoverWebSourcesActivity)
	w.RegisterActivity(activities.DiscoverDatabaseSourcesActivity)
	w.RegisterActivity(activities.BuildKnowledgeGraphActivity)
	w.RegisterActivity(activities.AnalyzeContentActivity)
	w.RegisterActivity(activities.AnalyzePatternsActivity)
	w.RegisterActivity(activities.AnalyzeSentimentActivity)
	w.RegisterActivity(activities.GenerateSynthesisActivity)
	w.RegisterActivity(activities.StreamResearchEventsActivity)
	w.RegisterActivity(activities.ValidateResearchSourceActivity)
	w.RegisterActivity(activities.CalculateResearchQualityActivity)

	// Register Bedrock activities (if available)
	if bedrockActivities != nil {
		w.RegisterActivity(bedrockActivities.GenerateTextWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.ConductConversationWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.AnalyzeWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.SummarizeWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.TranslateWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.ClassifyWithBedrockActivity)
		w.RegisterActivity(bedrockActivities.GetBedrockModelsActivity)
		w.RegisterActivity(bedrockActivities.ValidateBedrockRequestActivity)
		w.RegisterActivity(bedrockActivities.ValidateBedrockConversationActivity)
		w.RegisterActivity(bedrockActivities.CompareBedrockModelsActivity)
	}

	// Register WebSocket activities
	w.RegisterActivity(websocketActivities.BroadcastWorkflowUpdateActivity)
	w.RegisterActivity(websocketActivities.BroadcastAgentUpdateActivity)
	w.RegisterActivity(websocketActivities.BroadcastSystemUpdateActivity)
	w.RegisterActivity(websocketActivities.StartWorkflowMonitoringActivity)
	w.RegisterActivity(websocketActivities.StartAgentMonitoringActivity)
	w.RegisterActivity(websocketActivities.StartSystemMonitoringActivity)
	w.RegisterActivity(websocketActivities.GetConnectedClientsActivity)
	w.RegisterActivity(websocketActivities.BroadcastCustomMessageActivity)
	w.RegisterActivity(websocketActivities.SendProgressUpdateActivity)
	w.RegisterActivity(websocketActivities.SendAgentLifecycleActivity)
	w.RegisterActivity(websocketActivities.BroadcastErrorActivity)
	w.RegisterActivity(websocketActivities.BroadcastMetricsActivity)
	w.RegisterActivity(websocketActivities.ValidateWebSocketConnectionActivity)
	w.RegisterActivity(websocketActivities.CreateNotificationActivity)
	w.RegisterActivity(websocketActivities.SendHeartbeatActivity)

	// Register multi-model activities
	w.RegisterActivity(multiModelActivities.ProcessMultiModelRequestActivity)
	w.RegisterActivity(multiModelActivities.GetAvailableModelsActivity)
	w.RegisterActivity(multiModelActivities.GetModelsByProviderActivity)
	w.RegisterActivity(multiModelActivities.GetModelsByCapabilityActivity)
	w.RegisterActivity(multiModelActivities.CompareMultiModelsActivity)
	w.RegisterActivity(multiModelActivities.EnsembleModelsActivity)
	w.RegisterActivity(multiModelActivities.SelectBestModelActivity)
	w.RegisterActivity(multiModelActivities.ValidateMultiModelRequestActivity)
	w.RegisterActivity(multiModelActivities.GetModelStatisticsActivity)
	w.RegisterActivity(multiModelActivities.EnableModelActivity)
	w.RegisterActivity(multiModelActivities.DisableModelActivity)
	w.RegisterActivity(multiModelActivities.UpdateModelPriorityActivity)
	w.RegisterActivity(multiModelActivities.BenchmarkModelsActivity)
	w.RegisterActivity(multiModelActivities.GetModelRecommendationsActivity)

	// Register monitoring activities
	w.RegisterActivity(monitoring.RecordWorkflowMetricsActivity)
	w.RegisterActivity(monitoring.RecordAgentMetricsActivity)
	w.RegisterActivity(monitoring.GetMetricsActivity)

	// Register human loop activities
	w.RegisterActivity(humanloop.RouteTaskActivity)
	w.RegisterActivity(humanloop.SendNotificationActivity)
	w.RegisterActivity(humanloop.ProcessHumanDecisionActivity)

	// Register performance activities
	w.RegisterActivity(performance.OptimizedActivity)
	w.RegisterActivity(performance.HealthCheckActivity)
	w.RegisterActivity(performance.PerformanceMetricsActivity)

	// Register security activities
	w.RegisterActivity(security.RegisterSecureAgentsActivity)
	w.RegisterActivity(security.SecureAgentCommunicationActivity)
	w.RegisterActivity(security.AuditActivity)

	// Register legacy activities for backward compatibility
	w.RegisterActivity(activities.DiscoverInfrastructureActivity)
	w.RegisterActivity(activities.SecurityAgentActivity)
	w.RegisterActivity(activities.ComplianceAgentActivity)
	w.RegisterActivity(activities.CostOptimizationAgentActivity)
	w.RegisterActivity(activities.AggregateAgentResultsActivity)
	w.RegisterActivity(activities.GenerateComplianceReportActivity)
	w.RegisterActivity(activities.HumanReviewActivity)
	
	// Register skill execution activities
	w.RegisterActivity(skillExecutionActivities.GetSkillContentActivity)
	w.RegisterActivity(skillExecutionActivities.ParseSkillStepsActivity)
	w.RegisterActivity(skillExecutionActivities.ExecuteSkillStepActivity)
	
	// Register skill execution workflow
	w.RegisterWorkflow(workflows.SkillExecutionWorkflow)

	err = w.Start()
	if err != nil {
		log.Fatal("Unable to start worker", err)
	}

	// HTTP server for endpoints
	r := mux.NewRouter()

	// Apply CORS middleware
	r.Use(corsMiddleware)

	// Initialize RAG AI handler
	ragAIHandler := ragai.NewRagAIHandler()

	// Initialize Bedrock handler
	bedrockHandler, err := bedrock.NewBedrockHandler("us-west-2")
	if err != nil {
		log.Printf("Warning: Bedrock handler unavailable (expected in local dev): %v", err)
	}
	
	// Register skill service routes
	skillService.RegisterRoutes(r)
	
	// Register RAG AI routes
	ragAIHandler.RegisterRoutes(r.PathPrefix("/api/rag-ai").Subrouter())
	
	// Register Bedrock routes (if available)
	if bedrockHandler != nil {
		bedrockHandler.RegisterRoutes(r.PathPrefix("/api/bedrock").Subrouter())
	}
	
	// Register WebSocket routes
	r.HandleFunc("/ws", websocketHandler.HandleWebSocket)

	// --- HelloBackstage Workflow: the primary entry point from the frontend ---
	r.HandleFunc("/workflow/start", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "hello-backstage-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, HelloBackstageWorkflow, "Backstage")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")



	// Enhanced workflow endpoints
	r.HandleFunc("/workflow/start-ai-orchestration", func(w http.ResponseWriter, r *http.Request) {
		request := types.ComplianceRequest{
			TargetResource: "vm-web-server-001",
			ComplianceType: "full-scan",
			Parameters:     make(map[string]string),
			RequesterID:    "backstage-user",
			Priority:       "normal",
		}

		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "ai-orchestration-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.AIAgentOrchestrationWorkflowV2, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-ai-orchestration-v2", func(w http.ResponseWriter, r *http.Request) {
		request := types.ComplianceRequest{
			TargetResource: "vm-web-server-001",
			ComplianceType: "full-scan",
			Parameters:     make(map[string]string),
			RequesterID:    "backstage-user",
			Priority:       "normal",
		}

		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "ai-orchestration-v2-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.AIAgentOrchestrationWorkflowV2, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-human-in-loop", func(w http.ResponseWriter, r *http.Request) {
		task := types.HumanTask{
			ID:          "task-" + time.Now().Format("20060102150405"),
			Title:       "Security Review",
			Description: "Review security compliance",
			Priority:    "normal",
			Status:      types.HumanTaskStatus{State: "pending", UpdatedAt: time.Now()},
		}

		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "human-loop-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, humanloop.EnhancedHumanInTheLoopWorkflow, task)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-enhanced-human-loop", func(w http.ResponseWriter, r *http.Request) {
		task := types.HumanTask{
			ID:          "task-" + time.Now().Format("20060102150405"),
			Title:       "Enhanced Security Review",
			Description: "Advanced security compliance review with intelligent routing",
			Priority:    "high",
			AssignedTo:  "security-team",
			DueAt:       time.Now().Add(24 * time.Hour),
			Status:      types.HumanTaskStatus{State: "pending", UpdatedAt: time.Now()},
			Data:        make(map[string]interface{}),
		}

		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "enhanced-human-loop-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, humanloop.EnhancedHumanInTheLoopWorkflow, task)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-compliance", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "compliance-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, security.SecureWorkflow, map[string]interface{}{"scan": true})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-multi-agent", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "multi-agent-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.AIAgentOrchestrationWorkflowV2, types.ComplianceRequest{TargetResource: "multi-agent-target"})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-optimized", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "optimized-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, performance.OptimizedWorkflow, map[string]interface{}{"optimized": true})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-secure", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "secure-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, security.SecureWorkflow, map[string]interface{}{"secure": true})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(we.GetID()))
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/start-skill", func(w http.ResponseWriter, r *http.Request) {
		var req types.SkillExecutionRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:         fmt.Sprintf("skill-exec-%s-%d", req.SkillName, time.Now().Unix()),
			TaskQueue:  "ai-agent-task-queue",
		}, workflows.SkillExecutionWorkflow, req)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		
		response := map[string]interface{}{
			"workflowId": we.GetID(),
			"runId":       we.GetRunID(),
			"status":      "started",
		}
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/workflow/status", func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		if id == "" {
			http.Error(w, "missing id", http.StatusBadRequest)
			return
		}
		resp, err := c.DescribeWorkflowExecution(context.Background(), id, "")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write([]byte(resp.WorkflowExecutionInfo.Status.String()))
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/workflow/signal/{workflowId}", func(w http.ResponseWriter, r *http.Request) {
		workflowId := mux.Vars(r)["workflowId"]

		var signalReq struct {
			Signal string `json:"signal"`
			Value  string `json:"value"`
		}

		if err := json.NewDecoder(r.Body).Decode(&signalReq); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}

		err := c.SignalWorkflow(context.Background(), workflowId, "", signalReq.Signal, signalReq.Value)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Signal sent"))
	}).Methods("POST", "OPTIONS")

	// Enhanced monitoring endpoints
	r.HandleFunc("/monitoring/metrics", func(w http.ResponseWriter, r *http.Request) {
		metrics := metricsCollector.GetMetrics()

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(metrics)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/monitoring/alerts", func(w http.ResponseWriter, r *http.Request) {
		_ = metricsCollector.GetAlerts()

		w.Header().Set("Content-Type", "application/json")
	}).Methods("GET", "OPTIONS")

	// Enhanced audit endpoints
	r.HandleFunc("/audit/events", func(w http.ResponseWriter, r *http.Request) {
		events := auditLogger.GetEvents(nil)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(events)
	}).Methods("GET", "OPTIONS")

	// Performance endpoints
	r.HandleFunc("/performance/stats", func(w http.ResponseWriter, r *http.Request) {
		stats := map[string]interface{}{
			"activeWorkflows": 5, // concurrencyMgr.GetActiveCount(), // Dummy value
			"queuedWorkflows": 2, // concurrencyMgr.GetQueuedCount(), // Dummy value
			"resourceUtilization": 0.75, // resourcePool.GetUtilization(), // Dummy value
			"throughput": 10.5, // concurrencyMgr.GetThroughput(), // Dummy value
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(stats)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/workflow/skill-status/{workflowId}", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		workflowID := vars["workflowId"]

		response, err := c.QueryWorkflow(context.Background(), workflowID, "", "GetSkillExecutionStatus")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		var status types.SkillExecutionStatus
		if err := response.Get(&status); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(status)
	}).Methods("GET", "OPTIONS")

	// Infrastructure emulator endpoints
	r.HandleFunc("/emulator/resources", func(w http.ResponseWriter, r *http.Request) {
		resourceType := r.URL.Query().Get("type")
		resources, err := emulator.ListResources(context.Background(), resourceType)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resources)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/emulator/resources/{id}", func(w http.ResponseWriter, r *http.Request) {
		resourceID := mux.Vars(r)["id"]
		resource, err := emulator.GetResource(context.Background(), resourceID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resource)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/emulator/resources/{id}/security", func(w http.ResponseWriter, r *http.Request) {
		resourceID := mux.Vars(r)["id"]
		posture, err := emulator.GetSecurityPosture(context.Background(), resourceID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(posture)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/emulator/resources/{id}/compliance", func(w http.ResponseWriter, r *http.Request) {
		resourceID := mux.Vars(r)["id"]
		standards := []string{"SOC2", "GDPR", "HIPAA"}
		status, err := emulator.GetComplianceStatus(context.Background(), resourceID, standards)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(status)
	}).Methods("GET", "OPTIONS")

	// Conversation management endpoints
	r.HandleFunc("/conversation/start", func(w http.ResponseWriter, r *http.Request) {
		var request workflows.ConversationRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Set default values
		if request.MaxTurns == 0 {
			request.MaxTurns = 20
		}
		if request.LLMProvider == "" {
			request.LLMProvider = "openai"
		}
		if request.LLMModel == "" {
			request.LLMModel = "gpt-4"
		}
		if len(request.ToolsEnabled) == 0 {
			request.ToolsEnabled = []string{"start_compliance_workflow", "get_infrastructure_info"}
		}
		if request.Context == nil {
			request.Context = make(map[string]interface{})
		}

		// Start conversation workflow
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        fmt.Sprintf("conv-%s-%d", request.UserID, time.Now().Unix()),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.ConversationalAgentWorkflow, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"conversationId": we.GetID(),
			"runId":          we.GetRunID(),
			"status":         "started",
			"userId":         request.UserID,
			"goal":           request.Goal,
			"startedAt":      time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/conversation/{conversationId}/message", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		conversationID := vars["conversationId"]

		var messageReq struct {
			Message string `json:"message"`
		}

		if err := json.NewDecoder(r.Body).Decode(&messageReq); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Send signal to conversation
		err := c.SignalWorkflow(context.Background(), conversationID, "", 
			fmt.Sprintf("human-input-%s", conversationID), messageReq.Message)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"conversationId": conversationID,
			"message":        messageReq.Message,
			"status":         "message_sent",
			"sentAt":         time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/conversation/{conversationId}/status", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		conversationID := vars["conversationId"]
		includeHistory := r.URL.Query().Get("includeHistory") == "true"

		// Query conversation state
		response, err := c.QueryWorkflow(context.Background(), conversationID, "", "GetConversationStateQuery")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		var state workflows.ConversationState
		if err := response.Get(&state); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		result := map[string]interface{}{
			"conversationId":  state.ConversationID,
			"sessionId":       state.SessionID,
			"userId":          state.UserID,
			"goal":            state.Goal,
			"currentTurn":     state.CurrentTurn,
			"maxTurns":        state.MaxTurns,
			"status":          state.Status,
			"toolsUsed":       state.ToolsUsed,
			"startTime":       state.StartTime.Format(time.RFC3339),
			"lastUpdateTime":  state.LastUpdateTime.Format(time.RFC3339),
			"llmProvider":     state.LLMProvider,
			"llmModel":        state.LLMModel,
		}

		if includeHistory {
			result["history"] = state.History
			result["context"] = state.Context
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	}).Methods("GET", "OPTIONS")

	// Goal-based agent endpoints
	r.HandleFunc("/agent/goal/start", func(w http.ResponseWriter, r *http.Request) {
		var request workflows.GoalBasedAgentRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Set default values
		if request.MaxTurns == 0 {
			request.MaxTurns = 20
		}
		if request.LLMProvider == "" {
			request.LLMProvider = "openai"
		}
		if request.LLMModel == "" {
			request.LLMModel = "gpt-4"
		}
		if request.AgentType == "" {
			request.AgentType = "single"
		}
		if request.Context == nil {
			request.Context = make(map[string]interface{})
		}

		// Start goal-based agent workflow
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        fmt.Sprintf("goal-agent-%s-%d", request.UserID, time.Now().Unix()),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.GoalBasedAgentWorkflow, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"workflowId": we.GetID(),
			"runId":      we.GetRunID(),
			"status":     "started",
			"goal":       request.Goal,
			"agentType":  request.AgentType,
			"startedAt":  time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/agent/goal/{workflowId}/message", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		workflowID := vars["workflowID"]

		var messageReq struct {
			Message string `json:"message"`
		}

		if err := json.NewDecoder(r.Body).Decode(&messageReq); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Send signal to goal-based agent
		err := c.SignalWorkflow(context.Background(), workflowID, "", 
			fmt.Sprintf("human-input-%d", time.Now().Unix()), messageReq.Message)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"workflowId": workflowID,
			"message":    messageReq.Message,
			"status":     "message_sent",
			"sentAt":     time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/agent/goal/{workflowId}/status", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		workflowID := vars["workflowID"]
		includeHistory := r.URL.Query().Get("includeHistory") == "true"

		// Query goal-based agent state
		response, err := c.QueryWorkflow(context.Background(), workflowID, "", "GetGoalBasedAgentStateQuery")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		var state workflows.GoalBasedAgentState
		if err := response.Get(&state); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		result := map[string]interface{}{
			"workflowId":      workflowID,
			"goal":            state.Goal,
			"currentTurn":     state.CurrentTurn,
			"maxTurns":        state.MaxTurns,
			"status":          state.Status,
			"toolsUsed":       state.ToolsUsed,
			"startTime":       state.StartTime.Format(time.RFC3339),
			"lastUpdateTime":  state.LastUpdateTime.Format(time.RFC3339),
			"llmProvider":     state.LLMProvider,
			"llmModel":        state.LLMModel,
		}

		if includeHistory {
			result["conversation"] = state.Conversation
			result["context"] = state.Context
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	}).Methods("GET", "OPTIONS")

	// MCP management endpoints
	r.HandleFunc("/mcp/tools", func(w http.ResponseWriter, r *http.Request) {
		mcpRegistry := mcp.GetGlobalMCPRegistry()
		
		category := r.URL.Query().Get("category")
		goal := r.URL.Query().Get("goal")
		priority := r.URL.Query().Get("priority")
		
		var tools []mcp.MCPTool
		
		switch {
		case goal != "":
			tools = mcpRegistry.GetToolsByGoal(goal)
		case category != "":
			tools = mcpRegistry.GetToolsByCategory(category)
		case priority != "":
			maxPriority := 1
			if p, err := fmt.Sscanf(priority, "%d", &maxPriority); err == nil && p == 1 {
				tools = mcpRegistry.GetToolsByPriority(maxPriority)
			} else {
				tools = mcpRegistry.ListAllTools()
			}
		default:
			tools = mcpRegistry.ListAllTools()
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"tools": tools,
			"count": len(tools),
		})
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/mcp/goals", func(w http.ResponseWriter, r *http.Request) {
		// This would call the DiscoverGoalsActivity
		// For now, return mock goals
		goals := []string{
			"payment-processing",
			"billing",
			"subscription-management",
			"data-analysis",
			"reporting",
			"audit",
			"research",
			"information-gathering",
			"competitive-analysis",
			"employee-management",
			"onboarding",
			"team-coordination",
			"leave-management",
			"employee-requests",
			"travel-booking",
			"business-travel",
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"goals": goals,
			"count": len(goals),
		})
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/mcp/categories", func(w http.ResponseWriter, r *http.Request) {
		mcpRegistry := mcp.GetGlobalMCPRegistry()
		
		// Get unique categories from tools
		allTools := mcpRegistry.ListAllTools()
		categories := make(map[string]bool)
		for _, tool := range allTools {
			if tool.Category != "" {
				categories[tool.Category] = true
			}
		}
		
		// Convert to slice
		var categoryList []string
		for category := range categories {
			categoryList = append(categoryList, category)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"categories": categoryList,
			"count":      len(categoryList),
		})
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/mcp/clients", func(w http.ResponseWriter, r *http.Request) {
		mcpRegistry := mcp.GetGlobalMCPRegistry()
		clients := mcpRegistry.ListClients()

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]interface{}{
			"clients": clients,
			"count":   len(clients),
		})
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/mcp/execute", func(w http.ResponseWriter, r *http.Request) {
		var toolCall mcp.MCPToolCall
		if err := json.NewDecoder(r.Body).Decode(&toolCall); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		mcpRegistry := mcp.GetGlobalMCPRegistry()
		err := mcpRegistry.ExecuteTool(context.Background(), &toolCall)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(toolCall)
	}).Methods("POST", "OPTIONS")

	// ReAct agent endpoints
	r.HandleFunc("/agent/react/start", func(w http.ResponseWriter, r *http.Request) {
		var request workflows.ReActAgentRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Set default values
		if request.MaxSteps == 0 {
			request.MaxSteps = 10
		}
		if request.LLMProvider == "" {
			request.LLMProvider = "openai"
		}
		if request.LLMModel == "" {
			request.LLMModel = "gpt-4"
		}
		if request.Context == nil {
			request.Context = make(map[string]interface{})
		}

		// Start ReAct agent workflow
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        fmt.Sprintf("react-agent-%d", time.Now().Unix()),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.ReActAgentWorkflow, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"workflowId": we.GetID(),
			"runId":      we.GetRunID(),
			"status":     "started",
			"query":      request.Query,
			"maxSteps":   request.MaxSteps,
			"startedAt":  time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/agent/react/{workflowId}/status", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		workflowID := vars["workflowId"]
		includeSteps := r.URL.Query().Get("includeSteps") == "true"

		// Query ReAct agent state
		response, err := c.QueryWorkflow(context.Background(), workflowID, "", "GetReActAgentStateQuery")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		var state workflows.ReActAgentState
		if err := response.Get(&state); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		result := map[string]interface{}{
			"workflowId":   workflowID,
			"query":        state.Query,
			"currentStep":  state.CurrentStep,
			"maxSteps":     state.MaxSteps,
			"status":       state.Status,
			"result":       state.Result,
			"startTime":    state.StartTime.Format(time.RFC3339),
			"endTime":      state.EndTime.Format(time.RFC3339),
			"llmProvider":  state.LLMProvider,
			"llmModel":     state.LLMModel,
			"toolsUsed":    state.ToolsUsed,
		}

		if includeSteps {
			result["steps"] = state.Steps
			result["context"] = state.Context
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	}).Methods("GET", "OPTIONS")

	// Research workflow endpoints
	r.HandleFunc("/research/start", func(w http.ResponseWriter, r *http.Request) {
		var request types.ResearchRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "Invalid JSON", http.StatusBadRequest)
			return
		}

		// Set default values
		if request.MaxSources == 0 {
			request.MaxSources = 20
		}
		if request.MaxDepth == 0 {
			request.MaxDepth = 3
		}
		if request.LLMProvider == "" {
			request.LLMProvider = "openai"
		}
		if request.LLMModel == "" {
			request.LLMModel = "gpt-4"
		}
		if request.ResearchType == "" {
			request.ResearchType = "deep"
		}
		if request.Context == nil {
			request.Context = make(map[string]interface{})
		}

		// Start research workflow
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        fmt.Sprintf("research-%d", time.Now().Unix()),
			TaskQueue: "ai-agent-task-queue",
		}, workflows.DeepResearchWorkflow, request)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := map[string]interface{}{
			"workflowId":   we.GetID(),
			"runId":        we.GetRunID(),
			"status":       "started",
			"query":        request.Query,
			"researchType": request.ResearchType,
			"maxSources":   request.MaxSources,
			"startedAt":    time.Now().Format(time.RFC3339),
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}).Methods("POST", "OPTIONS")

	r.HandleFunc("/research/{workflowId}/status", func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		workflowID := vars["workflowID"]
		includeDetails := r.URL.Query().Get("includeDetails") == "true"

		// Query research state
		response, err := c.QueryWorkflow(context.Background(), workflowID, "", "GetResearchStateQuery")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		var state types.ResearchState
		if err := response.Get(&state); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		result := map[string]interface{}{
			"workflowId":       workflowID,
			"query":            state.Query,
			"researchType":     state.ResearchType,
			"currentPhase":     state.CurrentPhase,
			"status":           state.Status,
			"sourceCount":      len(state.Sources),
			"findingCount":     len(state.Findings),
			"nodeCount":        len(state.KnowledgeGraph),
			"eventCount":       len(state.EventStream),
			"agentCount":       len(state.AgentCollaboration),
			"startTime":        state.StartTime.Format(time.RFC3339),
			"endTime":          state.EndTime.Format(time.RFC3339),
			"llmProvider":      state.LLMProvider,
			"llmModel":         state.LLMModel,
		}

		if includeDetails {
			result["sources"] = state.Sources
			result["findings"] = state.Findings
			result["knowledgeGraph"] = state.KnowledgeGraph
			result["synthesis"] = state.Synthesis
			result["eventStream"] = state.EventStream
			result["agentCollaboration"] = state.AgentCollaboration
			result["context"] = state.Context
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	}).Methods("GET", "OPTIONS")

	r.HandleFunc("/research/{workflowId}/quality", func(w http.ResponseWriter, r *http.Request) {
		// NOTE: Quality calculation is done via the workflow, not directly here.
		// Return a placeholder quality assessment.
		quality := map[string]interface{}{
			"status":  "quality_assessment_pending",
			"message": "Quality assessment is computed as part of the research workflow. Query the workflow status for results.",
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(quality)
	}).Methods("GET", "OPTIONS")

	// Health check endpoint
	r.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
	}).Methods("GET", "OPTIONS")

	// Temporal UI Proxy to bypass X-Frame-Options
	target, _ := url.Parse("http://localhost:8080")
	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.ModifyResponse = func(resp *http.Response) error {
		resp.Header.Del("X-Frame-Options")
		resp.Header.Del("Content-Security-Policy")
		return nil
	}

	r.PathPrefix("/api/temporal-proxy/").HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		r.URL.Path = strings.TrimPrefix(r.URL.Path, "/api/temporal-proxy")
		if r.URL.Path == "" {
			r.URL.Path = "/"
		}
		proxy.ServeHTTP(w, r)
	}).Methods("GET", "POST", "PUT", "DELETE", "OPTIONS")

	// Mock Catalog API for Backstage
	r.HandleFunc("/api/catalog/entities", func(w http.ResponseWriter, r *http.Request) {
		// Return a basic catalog for now to satisfy the frontend
		entities := []map[string]interface{}{
			{
				"apiVersion": "backstage.io/v1alpha1",
				"kind":       "Component",
				"metadata": map[string]interface{}{
					"name":        "ai-agents-sandbox-backend",
					"description": "Temporal AI Agents Backend",
					"annotations": map[string]string{
						"backstage.io/managed-by-location": "url:http://localhost:8081/catalog-info.yaml",
					},
				},
				"spec": map[string]interface{}{
					"type":   "service",
					"lifecycle": "development",
					"owner": "guests",
				},
			},
			{
				"apiVersion": "backstage.io/v1alpha1",
				"kind":       "Component",
				"metadata": map[string]interface{}{
					"name":        "ai-agents-sandbox-frontend",
					"description": "Temporal AI Agents Frontend",
				},
				"spec": map[string]interface{}{
					"type":   "website",
					"lifecycle": "development",
					"owner": "guests",
				},
			},
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(entities)
	}).Methods("GET", "OPTIONS")

	log.Printf("Starting enhanced HTTP server on :8081")
	log.Fatal(http.ListenAndServe(":8081", corsMiddleware(r)))
}
