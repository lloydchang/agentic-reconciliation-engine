package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/mux"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/worker"
	"go.temporal.io/sdk/workflow"
	
	// Import our custom packages
	"github.com/lloydchang/backstage-temporal/backend/activities"
	"github.com/lloydchang/backstage-temporal/backend/config"
	"github.com/lloydchang/backstage-temporal/backend/emulators"
	"github.com/lloydchang/backstage-temporal/backend/humanloop"
	"github.com/lloydchang/backstage-temporal/backend/monitoring"
	"github.com/lloydchang/backstage-temporal/backend/performance"
	"github.com/lloydchang/backstage-temporal/backend/security"
	"github.com/lloydchang/backstage-temporal/backend/skills"
	"github.com/lloydchang/backstage-temporal/backend/types"
	"github.com/lloydchang/backstage-temporal/backend/workflows"
)

// CORS middleware
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

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

func HumanReviewActivity(ctx context.Context, aggregatedResult string) (string, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("HumanReviewActivity", "aggregatedResult", aggregatedResult)
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
	skillService := skills.NewSkillService(".", "session-"+time.Now().Format("20060102150405"))
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

	c, err := client.NewClient(client.Options{})
	if err != nil {
		log.Fatal("Unable to create client", err)
	}
	defer c.Close()

	w := worker.New(c, "ai-agent-task-queue", worker.Options{})

	// Register enhanced workflows
	// w.RegisterWorkflow(workflows.AIOrchestrationWorkflowV2) // Function doesn't exist
	// w.RegisterWorkflow(workflows.EnhancedWorkflowMetricsWorkflow) // Function doesn't exist
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

	// Register monitoring activities
	w.RegisterActivity(monitoring.RecordWorkflowMetricsActivity)
	w.RegisterActivity(monitoring.RecordAgentMetricsActivity)
	w.RegisterActivity(monitoring.GetMetricsActivity)
	// w.RegisterActivity(monitoring.HealthCheckActivity) // Function doesn't exist
	// w.RegisterActivity(monitoring.PerformanceMetricsActivity) // Function doesn't exist

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

	err = w.Start()
	if err != nil {
		log.Fatal("Unable to start worker", err)
	}

	// HTTP server for endpoints
	r := mux.NewRouter()

	// Apply CORS middleware
	r.Use(corsMiddleware)

	// Register skill service routes
	skillService.RegisterRoutes(r)

	// Add explicit OPTIONS handlers for CORS preflight
	r.HandleFunc("/workflow/start", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}).Methods("OPTIONS")

	r.HandleFunc("/workflow/status", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}).Methods("OPTIONS")

	// Enhanced workflow endpoints
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
		w.Write([]byte(we.GetID()))
	}).Methods("POST")

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
		w.Write([]byte(we.GetID()))
	}).Methods("POST")

	r.HandleFunc("/workflow/start-optimized", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "optimized-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, performance.OptimizedWorkflow, map[string]interface{}{"optimized": true})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write([]byte(we.GetID()))
	}).Methods("POST")

	r.HandleFunc("/workflow/start-secure", func(w http.ResponseWriter, r *http.Request) {
		we, err := c.ExecuteWorkflow(context.Background(), client.StartWorkflowOptions{
			ID:        "secure-workflow-" + time.Now().Format("20060102150405"),
			TaskQueue: "ai-agent-task-queue",
		}, security.SecureWorkflow, map[string]interface{}{"secure": true})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write([]byte(we.GetID()))
	}).Methods("POST")

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
		w.Write([]byte(resp.WorkflowExecutionInfo.Status.String()))
	}).Methods("GET")

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
	}).Methods("POST")

	// Enhanced monitoring endpoints
	r.HandleFunc("/monitoring/metrics", func(w http.ResponseWriter, r *http.Request) {
		metrics := metricsCollector.GetMetrics()

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(metrics)
	}).Methods("GET")

	r.HandleFunc("/monitoring/alerts", func(w http.ResponseWriter, r *http.Request) {
		_ = metricsCollector.GetAlerts()

		w.Header().Set("Content-Type", "application/json")
	}).Methods("GET")

	// Enhanced audit endpoints
	r.HandleFunc("/audit/events", func(w http.ResponseWriter, r *http.Request) {
		events := auditLogger.GetEvents(nil)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(events)
	}).Methods("GET")

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
	}).Methods("GET")

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
	}).Methods("GET")

	r.HandleFunc("/emulator/resources/{id}", func(w http.ResponseWriter, r *http.Request) {
		resourceID := mux.Vars(r)["id"]
		resource, err := emulator.GetResource(context.Background(), resourceID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resource)
	}).Methods("GET")

	r.HandleFunc("/emulator/resources/{id}/security", func(w http.ResponseWriter, r *http.Request) {
		resourceID := mux.Vars(r)["id"]
		posture, err := emulator.GetSecurityPosture(context.Background(), resourceID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(posture)
	}).Methods("GET")

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
	}).Methods("GET")

	log.Printf("Starting enhanced HTTP server on :8081")
	log.Fatal(http.ListenAndServe(":8081", r))
}
