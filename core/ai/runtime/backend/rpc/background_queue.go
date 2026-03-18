package rpc

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"go.temporal.io/api/enums/v1"
	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/worker"
)

// BackgroundTask represents a queued background task
type BackgroundTask struct {
	ID           string                 `json:"id"`
	SkillName    string                 `json:"skill_name"`
	Input        map[string]interface{} `json:"input"`
	Priority     int                    `json:"priority"`
	UserID       string                 `json:"user_id"`
	SessionID    string                 `json:"session_id"`
	CreatedAt    time.Time              `json:"created_at"`
	ScheduledAt  time.Time              `json:"scheduled_at"`
	Status       TaskStatus             `json:"status"`
	Progress     float64                `json:"progress"`
	Result       map[string]interface{} `json:"result,omitempty"`
	Error        string                 `json:"error,omitempty"`
	Retries      int                    `json:"retries"`
	MaxRetries   int                    `json:"max_retries"`
	Timeout      time.Duration          `json:"timeout"`
	Notifications []NotificationChannel `json:"notifications"`
}

// TaskStatus represents the status of a background task
type TaskStatus string

const (
	TaskStatusPending    TaskStatus = "pending"
	TaskStatusRunning    TaskStatus = "running"
	TaskStatusCompleted  TaskStatus = "completed"
	TaskStatusFailed     TaskStatus = "failed"
	TaskStatusCancelled  TaskStatus = "cancelled"
	TaskStatusTimeout    TaskStatus = "timeout"
)

// NotificationChannel defines where to send task notifications
type NotificationChannel struct {
	Type   string                 `json:"type"` // slack, github, email
	Config map[string]interface{} `json:"config"`
}

// TaskQueue manages background task execution
type TaskQueue struct {
	mu            sync.RWMutex
	redisClient   *redis.Client
	temporalClient client.Client
	worker        worker.Worker
	pendingTasks  chan *BackgroundTask
	runningTasks  map[string]*BackgroundTask
	completedTasks map[string]*BackgroundTask
	config        *QueueConfig
}

// QueueConfig defines queue configuration
type QueueConfig struct {
	MaxConcurrentTasks    int           `json:"max_concurrent_tasks"`
	DefaultTimeout        time.Duration `json:"default_timeout"`
	DefaultRetries        int           `json:"default_retries"`
	TaskRetentionPeriod   time.Duration `json:"task_retention_period"`
	NotificationQueueSize int           `json:"notification_queue_size"`
	RedisAddr            string        `json:"redis_addr"`
	TemporalAddr         string        `json:"temporal_addr"`
}

// NewTaskQueue creates a new task queue instance
func NewTaskQueue(config *QueueConfig) (*TaskQueue, error) {
	// Initialize Redis client
	redisClient := redis.NewClient(&redis.Options{
		Addr: config.RedisAddr,
	})

	// Initialize Temporal client
	temporalClient, err := client.Dial(client.Options{
		HostPort: config.TemporalAddr,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create temporal client: %w", err)
	}

	queue := &TaskQueue{
		redisClient:    redisClient,
		temporalClient: temporalClient,
		pendingTasks:   make(chan *BackgroundTask, 1000),
		runningTasks:   make(map[string]*BackgroundTask),
		completedTasks: make(map[string]*BackgroundTask),
		config:         config,
	}

	// Start worker
	if err := queue.startWorker(); err != nil {
		return nil, fmt.Errorf("failed to start worker: %w", err)
	}

	// Start task processor
	go queue.processTasks()

	// Start cleanup routine
	go queue.cleanupRoutine()

	return queue, nil
}

// SubmitTask submits a new background task
func (tq *TaskQueue) SubmitTask(ctx context.Context, task *BackgroundTask) error {
	tq.mu.Lock()
	defer tq.mu.Unlock()

	// Set defaults
	if task.ID == "" {
		task.ID = generateTaskID()
	}
	if task.CreatedAt.IsZero() {
		task.CreatedAt = time.Now()
	}
	if task.ScheduledAt.IsZero() {
		task.ScheduledAt = time.Now()
	}
	if task.Status == "" {
		task.Status = TaskStatusPending
	}
	if task.MaxRetries == 0 {
		task.MaxRetries = tq.config.DefaultRetries
	}
	if task.Timeout == 0 {
		task.Timeout = tq.config.DefaultTimeout
	}

	// Store in Redis
	taskJSON, err := json.Marshal(task)
	if err != nil {
		return fmt.Errorf("failed to marshal task: %w", err)
	}

	key := fmt.Sprintf("task:%s", task.ID)
	if err := tq.redisClient.Set(ctx, key, taskJSON, tq.config.TaskRetentionPeriod).Err(); err != nil {
		return fmt.Errorf("failed to store task in redis: %w", err)
	}

	// Add to pending queue
	select {
	case tq.pendingTasks <- task:
		log.Printf("Task %s submitted for skill %s", task.ID, task.SkillName)
		return nil
	default:
		return fmt.Errorf("task queue is full")
	}
}

// GetTaskStatus retrieves the status of a task
func (tq *TaskQueue) GetTaskStatus(ctx context.Context, taskID string) (*BackgroundTask, error) {
	tq.mu.RLock()
	defer tq.mu.RUnlock()

	// Check running tasks first
	if task, exists := tq.runningTasks[taskID]; exists {
		return task, nil
	}

	// Check completed tasks
	if task, exists := tq.completedTasks[taskID]; exists {
		return task, nil
	}

	// Check Redis
	key := fmt.Sprintf("task:%s", taskID)
	taskJSON, err := tq.redisClient.Get(ctx, key).Result()
	if err != nil {
		return nil, fmt.Errorf("task not found: %w", err)
	}

	var task BackgroundTask
	if err := json.Unmarshal([]byte(taskJSON), &task); err != nil {
		return nil, fmt.Errorf("failed to unmarshal task: %w", err)
	}

	return &task, nil
}

// CancelTask cancels a running or pending task
func (tq *TaskQueue) CancelTask(ctx context.Context, taskID string) error {
	tq.mu.Lock()
	defer tq.mu.Unlock()

	// Check if task is running
	if task, exists := tq.runningTasks[taskID]; exists {
		task.Status = TaskStatusCancelled
		// Update Redis
		tq.updateTaskInRedis(ctx, task)
		log.Printf("Task %s cancelled", taskID)
		return nil
	}

	// Check Redis for pending task
	key := fmt.Sprintf("task:%s", taskID)
	taskJSON, err := tq.redisClient.Get(ctx, key).Result()
	if err != nil {
		return fmt.Errorf("task not found: %w", err)
	}

	var task BackgroundTask
	if err := json.Unmarshal([]byte(taskJSON), &task); err != nil {
		return fmt.Errorf("failed to unmarshal task: %w", err)
	}

	if task.Status == TaskStatusPending {
		task.Status = TaskStatusCancelled
		tq.updateTaskInRedis(ctx, task)
		log.Printf("Task %s cancelled", taskID)
		return nil
	}

	return fmt.Errorf("task cannot be cancelled (current status: %s)", task.Status)
}

// ListTasks lists tasks with optional filtering
func (tq *TaskQueue) ListTasks(ctx context.Context, status TaskStatus, limit int) ([]*BackgroundTask, error) {
	tq.mu.RLock()
	defer tq.mu.RUnlock()

	var tasks []*BackgroundTask

	// Collect from running tasks
	for _, task := range tq.runningTasks {
		if status == "" || task.Status == status {
			tasks = append(tasks, task)
		}
	}

	// Collect from completed tasks
	for _, task := range tq.completedTasks {
		if status == "" || task.Status == status {
			tasks = append(tasks, task)
		}
	}

	// If we need more tasks, check Redis
	if len(tasks) < limit {
		pattern := "task:*"
		keys, err := tq.redisClient.Keys(ctx, pattern).Result()
		if err != nil {
			return nil, fmt.Errorf("failed to get task keys: %w", err)
		}

		for _, key := range keys {
			if len(tasks) >= limit {
				break
			}

			taskJSON, err := tq.redisClient.Get(ctx, key).Result()
			if err != nil {
				continue
			}

			var task BackgroundTask
			if err := json.Unmarshal([]byte(taskJSON), &task); err != nil {
				continue
			}

			if status == "" || task.Status == status {
				tasks = append(tasks, &task)
			}
		}
	}

	// Apply limit
	if limit > 0 && len(tasks) > limit {
		tasks = tasks[:limit]
	}

	return tasks, nil
}

// processTasks processes pending tasks
func (tq *TaskQueue) processTasks() {
	for task := range tq.pendingTasks {
		// Check if we can run this task
		if len(tq.runningTasks) >= tq.config.MaxConcurrentTasks {
			// Re-queue the task
			go func() {
				time.Sleep(time.Second)
				tq.pendingTasks <- task
			}()
			continue
		}

		// Run the task
		go tq.executeTask(task)
	}
}

// executeTask executes a single task
func (tq *TaskQueue) executeTask(task *BackgroundTask) {
	ctx := context.Background()
	
	tq.mu.Lock()
	tq.runningTasks[task.ID] = task
	tq.mu.Unlock()

	// Update status
	task.Status = TaskStatusRunning
	tq.updateTaskInRedis(ctx, task)

	// Send notification
	tq.sendNotification(ctx, task, "started", fmt.Sprintf("Task %s started", task.ID))

	// Execute with timeout
	timeoutCtx, cancel := context.WithTimeout(ctx, task.Timeout)
	defer cancel()

	result, err := tq.runSkill(timeoutCtx, task)

	tq.mu.Lock()
	delete(tq.runningTasks, task.ID)
	tq.mu.Unlock()

	if err != nil {
		task.Error = err.Error()
		if task.Retries < task.MaxRetries {
			task.Status = TaskStatusPending
			task.Retries++
			task.ScheduledAt = time.Now().Add(time.Minute * time.Duration(task.Retries))
			
			// Re-queue for retry
			go func() {
				time.Sleep(time.Minute * time.Duration(task.Retries))
				tq.pendingTasks <- task
			}()
			
			tq.sendNotification(ctx, task, "retrying", fmt.Sprintf("Task %s failed, retrying (%d/%d)", task.ID, task.Retries, task.MaxRetries))
		} else {
			task.Status = TaskStatusFailed
			tq.completedTasks[task.ID] = task
			tq.sendNotification(ctx, task, "failed", fmt.Sprintf("Task %s failed: %s", task.ID, err.Error()))
		}
	} else {
		task.Status = TaskStatusCompleted
		task.Result = result
		task.Progress = 100.0
		tq.completedTasks[task.ID] = task
		tq.sendNotification(ctx, task, "completed", fmt.Sprintf("Task %s completed successfully", task.ID))
	}

	tq.updateTaskInRedis(ctx, task)
	log.Printf("Task %s completed with status: %s", task.ID, task.Status)
}

// runSkill executes the skill using Temporal
func (tq *TaskQueue) runSkill(ctx context.Context, task *BackgroundTask) (map[string]interface{}, error) {
	workflowOptions := client.StartWorkflowOptions{
		ID:        fmt.Sprintf("skill-%s-%s", task.SkillName, task.ID),
		TaskQueue: "skill-queue",
	}

	// Start workflow
	we, err := tq.temporalClient.ExecuteWorkflow(ctx, workflowOptions, task.SkillName, task.Input)
	if err != nil {
		return nil, fmt.Errorf("failed to execute workflow: %w", err)
	}

	// Wait for result
	var result map[string]interface{}
	err = we.Get(ctx, &result)
	if err != nil {
		return nil, fmt.Errorf("workflow execution failed: %w", err)
	}

	return result, nil
}

// sendNotification sends task notifications
func (tq *TaskQueue) sendNotification(ctx context.Context, task *BackgroundTask, eventType, message string) {
	for _, channel := range task.Notifications {
		switch channel.Type {
		case "slack":
			tq.sendSlackNotification(ctx, channel, task, eventType, message)
		case "github":
			tq.sendGitHubNotification(ctx, channel, task, eventType, message)
		case "email":
			tq.sendEmailNotification(ctx, channel, task, eventType, message)
		}
	}
}

// sendSlackNotification sends a Slack notification
func (tq *TaskQueue) sendSlackNotification(ctx context.Context, channel NotificationChannel, task *BackgroundTask, eventType, message string) {
	webhook, ok := channel.Config["webhook"].(string)
	if !ok {
		log.Printf("Slack webhook not configured for task %s", task.ID)
		return
	}

	payload := map[string]interface{}{
		"text": fmt.Sprintf("AI Agent Task Update: %s", message),
		"attachments": []map[string]interface{}{
			{
				"color": tq.getNotificationColor(eventType),
				"fields": []map[string]interface{}{
					{"title": "Task ID", "value": task.ID, "short": true},
					{"title": "Skill", "value": task.SkillName, "short": true},
					{"title": "Status", "value": string(task.Status), "short": true},
					{"title": "Progress", "value": fmt.Sprintf("%.1f%%", task.Progress), "short": true},
				},
				"ts": task.CreatedAt.Unix(),
			},
		},
	}

	payloadJSON, _ := json.Marshal(payload)
	// In a real implementation, send to Slack webhook
	log.Printf("Slack notification: %s", string(payloadJSON))
}

// sendGitHubNotification sends a GitHub notification
func (tq *TaskQueue) sendGitHubNotification(ctx context.Context, channel NotificationChannel, task *BackgroundTask, eventType, message string) {
	// Implementation for GitHub notifications (comments, status updates)
	log.Printf("GitHub notification for task %s: %s", task.ID, message)
}

// sendEmailNotification sends an email notification
func (tq *TaskQueue) sendEmailNotification(ctx context.Context, channel NotificationChannel, task *BackgroundTask, eventType, message string) {
	// Implementation for email notifications
	log.Printf("Email notification for task %s: %s", task.ID, message)
}

// getNotificationColor returns appropriate color for notification type
func (tq *TaskQueue) getNotificationColor(eventType string) string {
	switch eventType {
	case "started":
		return "good"
	case "completed":
		return "good"
	case "failed":
		return "danger"
	case "retrying":
		return "warning"
	default:
		return "#808080"
	}
}

// updateTaskInRedis updates task in Redis
func (tq *TaskQueue) updateTaskInRedis(ctx context.Context, task *BackgroundTask) error {
	taskJSON, err := json.Marshal(task)
	if err != nil {
		return fmt.Errorf("failed to marshal task: %w", err)
	}

	key := fmt.Sprintf("task:%s", task.ID)
	return tq.redisClient.Set(ctx, key, taskJSON, tq.config.TaskRetentionPeriod).Err()
}

// startWorker starts the Temporal worker
func (tq *TaskQueue) startWorker() error {
	worker := worker.New(tq.temporalClient, "skill-queue", worker.Options{})
	
	// Register skill workflows here
	// worker.RegisterWorkflow(skillWorkflows...)
	
	tq.worker = worker
	return nil
}

// cleanupRoutine cleans up old completed tasks
func (tq *TaskQueue) cleanupRoutine() {
	ticker := time.NewTicker(time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		tq.mu.Lock()
		
		// Remove old completed tasks
		cutoff := time.Now().Add(-tq.config.TaskRetentionPeriod)
		for id, task := range tq.completedTasks {
			if task.CreatedAt.Before(cutoff) {
				delete(tq.completedTasks, id)
			}
		}
		
		tq.mu.Unlock()
	}
}

// generateTaskID generates a unique task ID
func generateTaskID() string {
	return fmt.Sprintf("task-%d-%s", time.Now().UnixNano(), randomString(8))
}

// randomString generates a random string
func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[time.Now().UnixNano()%int64(len(charset))]
	}
	return string(b)
}

// Close closes the task queue
func (tq *TaskQueue) Close() error {
	if tq.worker != nil {
		tq.Stop()
	}
	
	if tq.temporalClient != nil {
		tq.temporalClient.Close()
	}
	
	if tq.redisClient != nil {
		return tq.redisClient.Close()
	}
	
	return nil
}
