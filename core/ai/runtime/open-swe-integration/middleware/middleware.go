package main

import (
	"context"
	"fmt"
	"net/http"
	"time"
)

// Middleware interface for request processing
type Middleware interface {
	Process(ctx context.Context, req *Request) (*Response, error)
	Name() string
}

// Request represents an incoming request
type Request struct {
	Source      string            `json:"source"`      // "slack" or "linear"
	Type        string            `json:"type"`        // "command", "issue", "event"
	Data        map[string]interface{} `json:"data"`
	Headers     map[string]string `json:"headers"`
	Timestamp   time.Time         `json:"timestamp"`
	RequestID   string            `json:"request_id"`
	UserID      string            `json:"user_id"`
	ChannelID   string            `json:"channel_id"`
}

// Response represents a middleware response
type Response struct {
	Status      string            `json:"status"`
	Data        map[string]interface{} `json:"data"`
	Headers     map[string]string `json:"headers"`
	ProcessedBy []string          `json:"processed_by"`
	Error       string            `json:"error,omitempty"`
}

// MiddlewareChain manages middleware execution
type MiddlewareChain struct {
	middleware []Middleware
	logger     *Logger
}

// NewMiddlewareChain creates a new middleware chain
func NewMiddlewareChain(logger *Logger) *MiddlewareChain {
	return &MiddlewareChain{
		middleware: []Middleware{},
		logger:     logger,
	}
}

// Add adds middleware to the chain
func (mc *MiddlewareChain) Add(middleware Middleware) {
	mc.middleware = append(mc.middleware, middleware)
	mc.logger.Info("Added middleware", "name", middleware.Name())
}

// Process executes the middleware chain
func (mc *MiddlewareChain) Process(ctx context.Context, req *Request) (*Response, error) {
	resp := &Response{
		Status:      "processing",
		Data:        make(map[string]interface{}),
		Headers:     make(map[string]string),
		ProcessedBy: []string{},
	}

	for _, middleware := range mc.middleware {
		start := time.Now()
		
		mc.logger.Info("Processing middleware", "name", middleware.Name(), "request_id", req.RequestID)
		
		result, err := middleware.Process(ctx, req)
		if err != nil {
			mc.logger.Error("Middleware failed", "name", middleware.Name(), "error", err, "request_id", req.RequestID)
			resp.Status = "error"
			resp.Error = err.Error()
			return resp, err
		}

		// Merge response data
		for k, v := range result.Data {
			resp.Data[k] = v
		}
		for k, v := range result.Headers {
			resp.Headers[k] = v
		}
		resp.ProcessedBy = append(resp.ProcessedBy, middleware.Name())

		duration := time.Since(start)
		mc.logger.Info("Middleware completed", "name", middleware.Name(), "duration", duration, "request_id", req.RequestID)

		// Stop processing if middleware indicates completion
		if result.Status == "complete" {
			resp.Status = "complete"
			break
		}
	}

	if resp.Status == "processing" {
		resp.Status = "complete"
	}

	return resp, nil
}

// AuthenticationMiddleware handles request authentication
type AuthenticationMiddleware struct {
	secretManager *SecretManager
	logger        *Logger
}

func NewAuthenticationMiddleware(secretManager *SecretManager, logger *Logger) *AuthenticationMiddleware {
	return &AuthenticationMiddleware{
		secretManager: secretManager,
		logger:        logger,
	}
}

func (am *AuthenticationMiddleware) Name() string {
	return "authentication"
}

func (am *AuthenticationMiddleware) Process(ctx context.Context, req *Request) (*Response, error) {
	am.logger.Info("Authenticating request", "source", req.Source, "request_id", req.RequestID)

	// Verify webhook signature based on source
	var valid bool
	var err error

	switch req.Source {
	case "slack":
		valid, err = am.verifySlackSignature(req)
	case "linear":
		valid, err = am.verifyLinearSignature(req)
	default:
		return &Response{Status: "error", Error: "unknown source"}, fmt.Errorf("unknown source: %s", req.Source)
	}

	if err != nil {
		return &Response{Status: "error", Error: "signature verification failed"}, err
	}

	if !valid {
		return &Response{Status: "error", Error: "invalid signature"}, fmt.Errorf("invalid signature")
	}

	am.logger.Info("Request authenticated successfully", "request_id", req.RequestID)
	return &Response{Status: "continue", Data: map[string]interface{}{"authenticated": true}}, nil
}

func (am *AuthenticationMiddleware) verifySlackSignature(req *Request) (bool, error) {
	// Placeholder for Slack signature verification
	// Implementation would verify X-Slack-Signature and X-Slack-Request-Timestamp
	return true, nil
}

func (am *AuthenticationMiddleware) verifyLinearSignature(req *Request) (bool, error) {
	// Placeholder for Linear signature verification
	// Implementation would verify Linear webhook signature
	return true, nil
}

// ValidationMiddleware handles request validation
type ValidationMiddleware struct {
	logger *Logger
}

func NewValidationMiddleware(logger *Logger) *ValidationMiddleware {
	return &ValidationMiddleware{
		logger: logger,
	}
}

func (vm *ValidationMiddleware) Name() string {
	return "validation"
}

func (vm *ValidationMiddleware) Process(ctx context.Context, req *Request) (*Response, error) {
	vm.logger.Info("Validating request", "source", req.Source, "type", req.Type, "request_id", req.RequestID)

	// Validate required fields
	if req.RequestID == "" {
		return &Response{Status: "error", Error: "missing request_id"}, fmt.Errorf("missing request_id")
	}

	if req.Source == "" {
		return &Response{Status: "error", Error: "missing source"}, fmt.Errorf("missing source")
	}

	if req.Type == "" {
		return &Response{Status: "error", Error: "missing type"}, fmt.Errorf("missing type")
	}

	// Validate source-specific requirements
	switch req.Source {
	case "slack":
		if err := vm.validateSlackRequest(req); err != nil {
			return &Response{Status: "error", Error: err.Error()}, err
		}
	case "linear":
		if err := vm.validateLinearRequest(req); err != nil {
			return &Response{Status: "error", Error: err.Error()}, err
		}
	}

	vm.logger.Info("Request validated successfully", "request_id", req.RequestID)
	return &Response{Status: "continue", Data: map[string]interface{}{"validated": true}}, nil
}

func (vm *ValidationMiddleware) validateSlackRequest(req *Request) error {
	if req.UserID == "" {
		return fmt.Errorf("missing user_id for Slack request")
	}
	if req.ChannelID == "" {
		return fmt.Errorf("missing channel_id for Slack request")
	}
	return nil
}

func (vm *ValidationMiddleware) validateLinearRequest(req *Request) error {
	// Add Linear-specific validation
	return nil
}

// EnrichmentMiddleware enhances request data
type EnrichmentMiddleware struct {
	memoryAgent *MemoryAgent
	logger      *Logger
}

func NewEnrichmentMiddleware(memoryAgent *MemoryAgent, logger *Logger) *EnrichmentMiddleware {
	return &EnrichmentMiddleware{
		memoryAgent: memoryAgent,
		logger:      logger,
	}
}

func (em *EnrichmentMiddleware) Name() string {
	return "enrichment"
}

func (em *EnrichmentMiddleware) Process(ctx context.Context, req *Request) (*Response, error) {
	em.logger.Info("Enriching request", "request_id", req.RequestID)

	// Add context from memory agent
	context, err := em.memoryAgent.GetContext(ctx, req.UserID)
	if err != nil {
		em.logger.Warn("Failed to get context from memory agent", "error", err, "request_id", req.RequestID)
		// Continue without enrichment
	}

	enrichedData := map[string]interface{}{
		"enriched": true,
		"context": context,
	}

	// Add timestamp enrichment
	enrichedData["processed_at"] = time.Now().UTC()

	em.logger.Info("Request enriched successfully", "request_id", req.RequestID)
	return &Response{Status: "continue", Data: enrichedData}, nil
}

// RateLimitMiddleware handles rate limiting
type RateLimitMiddleware struct {
	limiter *RateLimiter
	logger  *Logger
}

func NewRateLimitMiddleware(limiter *RateLimiter, logger *Logger) *RateLimitMiddleware {
	return &RateLimitMiddleware{
		limiter: limiter,
		logger:  logger,
	}
}

func (rlm *RateLimitMiddleware) Name() string {
	return "rate_limit"
}

func (rlm *RateLimitMiddleware) Process(ctx context.Context, req *Request) (*Response, error) {
	rlm.logger.Info("Checking rate limit", "user_id", req.UserID, "request_id", req.RequestID)

	allowed, resetTime, err := rlm.limiter.Allow(ctx, req.UserID)
	if err != nil {
		return &Response{Status: "error", Error: "rate limit check failed"}, err
	}

	if !allowed {
		rlm.logger.Warn("Rate limit exceeded", "user_id", req.UserID, "request_id", req.RequestID)
		return &Response{
			Status: "error",
			Error:  "rate limit exceeded",
			Data:   map[string]interface{}{"reset_time": resetTime},
		}, fmt.Errorf("rate limit exceeded")
	}

	rlm.logger.Info("Rate limit check passed", "user_id", req.UserID, "request_id", req.RequestID)
	return &Response{Status: "continue", Data: map[string]interface{}{"rate_limited": false}}, nil
}

// Logger placeholder
type Logger struct{}

func (l *Logger) Info(msg string, args ...interface{}) {
	fmt.Printf("[INFO] %s %v\n", msg, args)
}

func (l *Logger) Warn(msg string, args ...interface{}) {
	fmt.Printf("[WARN] %s %v\n", msg, args)
}

func (l *Logger) Error(msg string, args ...interface{}) {
	fmt.Printf("[ERROR] %s %v\n", msg, args)
}

// SecretManager placeholder
type SecretManager struct{}

func (sm *SecretManager) GetSecret(key string) (string, error) {
	return "", nil
}

// MemoryAgent placeholder
type MemoryAgent struct{}

func (ma *MemoryAgent) GetContext(ctx context.Context, userID string) (map[string]interface{}, error) {
	return map[string]interface{}{}, nil
}

// RateLimiter placeholder
type RateLimiter struct{}

func (rl *RateLimiter) Allow(ctx context.Context, userID string) (bool, time.Time, error) {
	return true, time.Time{}, nil
}
