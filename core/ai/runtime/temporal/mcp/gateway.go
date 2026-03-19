package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// MCPServer represents an MCP server instance
type MCPServer struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Endpoint    string                 `json:"endpoint"`
	Status      ServerStatus           `json:"status"`
	Health      HealthStatus           `json:"health"`
	Capabilities []string              `json:"capabilities"`
	Metadata    map[string]interface{} `json:"metadata"`
	CreatedAt   time.Time              `json:"created_at"`
	LastSeen    time.Time              `json:"last_seen"`
}

// ServerStatus represents the status of an MCP server
type ServerStatus string

const (
	ServerStatusActive   ServerStatus = "active"
	ServerStatusInactive ServerStatus = "inactive"
	ServerStatusError    ServerStatus = "error"
	ServerStatusUnknown  ServerStatus = "unknown"
)

// HealthStatus represents health check results
type HealthStatus struct {
	Healthy   bool      `json:"healthy"`
	Message   string    `json:"message"`
	CheckTime time.Time `json:"check_time"`
	Latency   int64     `json:"latency_ms"`
}

// MCPRequest represents an MCP request
type MCPRequest struct {
	ID        string                 `json:"id"`
	Method    string                 `json:"method"`
	Params    map[string]interface{} `json:"params"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	SessionID string                 `json:"session_id"`
}

// MCPResponse represents an MCP response
type MCPResponse struct {
	ID        string                 `json:"id"`
	Result    map[string]interface{} `json:"result,omitempty"`
	Error     *MCPError              `json:"error,omitempty"`
	Timestamp time.Time              `json:"timestamp"`
	Duration  int64                  `json:"duration_ms"`
}

// MCPError represents an MCP error
type MCPError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// MCPGateway manages MCP server registry and proxy
type MCPGateway struct {
	mu            sync.RWMutex
	servers       map[string]*MCPServer
	registry      *ServerRegistry
	authorizer    *Authorizer
	telemetry     *TelemetryCollector
	sandbox       *SandboxEnvironment
	config        *GatewayConfig
	httpServer    *http.Server
	metrics       *GatewayMetrics
}

// ServerRegistry manages MCP server registration and discovery
type ServerRegistry struct {
	storage    RegistryStorage
	categories map[string][]string
}

// RegistryStorage defines the interface for server registry storage
type RegistryStorage interface {
	Store(ctx context.Context, server *MCPServer) error
	Get(ctx context.Context, id string) (*MCPServer, error)
	List(ctx context.Context, filters map[string]interface{}) ([]*MCPServer, error)
	Delete(ctx context.Context, id string) error
}

// Authorizer handles MCP access control
type Authorizer struct {
	rules []AuthorizationRule
}

// AuthorizationRule defines access control rules
type AuthorizationRule struct {
	Resource   string   `json:"resource"`
	Actions    []string `json:"actions"`
	Subjects   []string `json:"subjects"`
	Conditions []string `json:"conditions"`
}

// TelemetryCollector collects usage metrics and telemetry
type TelemetryCollector struct {
	requests    chan *MCPRequest
	responses   chan *MCPResponse
	metrics     map[string]*prometheus.CounterVec
	histograms  map[string]*prometheus.HistogramVec
}

// SandboxEnvironment provides isolated execution environment
type SandboxEnvironment struct {
	enabled bool
	config  SandboxConfig
}

// SandboxConfig defines sandbox configuration
type SandboxConfig struct {
	MaxMemoryMB     int           `json:"max_memory_mb"`
	MaxCPUPercent   int           `json:"max_cpu_percent"`
	Timeout         time.Duration `json:"timeout"`
	AllowedNetworks []string      `json:"allowed_networks"`
}

// GatewayConfig defines gateway configuration
type GatewayConfig struct {
	ListenAddr         string        `json:"listen_addr"`
	RegistryStorage    string        `json:"registry_storage"`
	TelemetryEnabled   bool          `json:"telemetry_enabled"`
	SandboxEnabled     bool          `json:"sandbox_enabled"`
	DefaultTimeout     time.Duration `json:"default_timeout"`
	MaxRequestSize     int64         `json:"max_request_size"`
	RateLimitPerMinute int           `json:"rate_limit_per_minute"`
}

// GatewayMetrics tracks gateway performance metrics
type GatewayMetrics struct {
	RequestsTotal    *prometheus.CounterVec
	RequestDuration  *prometheus.HistogramVec
	ErrorsTotal      *prometheus.CounterVec
	ServerStatus     *prometheus.GaugeVec
}

// NewMCPGateway creates a new MCP gateway instance
func NewMCPGateway(config *GatewayConfig) (*MCPGateway, error) {
	gateway := &MCPGateway{
		servers:   make(map[string]*MCPServer),
		config:    config,
		telemetry: NewTelemetryCollector(),
	}

	// Initialize registry
	storage, err := NewRedisRegistryStorage(config.RegistryStorage)
	if err != nil {
		return nil, fmt.Errorf("failed to create registry storage: %w", err)
	}
	gateway.registry = &ServerRegistry{
		storage:    storage,
		categories: make(map[string][]string),
	}

	// Initialize authorizer
	gateway.authorizer = NewAuthorizer()

	// Initialize sandbox
	gateway.sandbox = &SandboxEnvironment{
		enabled: config.SandboxEnabled,
		config: SandboxConfig{
			MaxMemoryMB:     512,
			MaxCPUPercent:   50,
			Timeout:         30 * time.Second,
			AllowedNetworks: []string{},
		},
	}

	// Initialize metrics
	gateway.metrics = NewGatewayMetrics()

	// Setup HTTP server
	gateway.setupHTTPServer()

	return gateway, nil
}

// Start starts the MCP gateway
func (mg *MCPGateway) Start(ctx context.Context) error {
	log.Printf("Starting MCP gateway on %s", mg.config.ListenAddr)

	// Load existing servers from registry
	if err := mg.loadServersFromRegistry(ctx); err != nil {
		log.Printf("Warning: failed to load servers from registry: %v", err)
	}

	// Start health checks
	go mg.healthCheckRoutine(ctx)

	// Start metrics collection
	go mg.telemetryCollectionRoutine(ctx)

	// Start HTTP server
	return mg.httpServer.ListenAndServe()
}

// Stop stops the MCP gateway
func (mg *MCPGateway) Stop(ctx context.Context) error {
	log.Printf("Stopping MCP gateway")
	
	if mg.httpServer != nil {
		return mg.httpServer.Shutdown(ctx)
	}
	
	return nil
}

// RegisterServer registers a new MCP server
func (mg *MCPGateway) RegisterServer(ctx context.Context, server *MCPServer) error {
	mg.mu.Lock()
	defer mg.mu.Unlock()

	// Validate server
	if err := mg.validateServer(server); err != nil {
		return fmt.Errorf("server validation failed: %w", err)
	}

	// Store in registry
	if err := mg.registry.Store(ctx, server); err != nil {
		return fmt.Errorf("failed to store server in registry: %w", err)
	}

	// Add to memory cache
	mg.servers[server.ID] = server

	log.Printf("Registered MCP server: %s (%s)", server.ID, server.Name)
	return nil
}

// UnregisterServer unregisters an MCP server
func (mg *MCPGateway) UnregisterServer(ctx context.Context, serverID string) error {
	mg.mu.Lock()
	defer mg.mu.Unlock()

	// Remove from registry
	if err := mg.registry.Delete(ctx, serverID); err != nil {
		return fmt.Errorf("failed to delete server from registry: %w", err)
	}

	// Remove from memory cache
	delete(mg.servers, serverID)

	log.Printf("Unregistered MCP server: %s", serverID)
	return nil
}

// ListServers lists registered MCP servers
func (mg *MCPGateway) ListServers(ctx context.Context, filters map[string]interface{}) ([]*MCPServer, error) {
	mg.mu.RLock()
	defer mg.mu.RUnlock()

	if len(filters) == 0 {
		// Return all cached servers
		servers := make([]*MCPServer, 0, len(mg.servers))
		for _, server := range mg.servers {
			servers = append(servers, server)
		}
		return servers, nil
	}

	// Use registry for filtered queries
	return mg.registry.List(ctx, filters)
}

// ProxyRequest proxies an MCP request to the appropriate server
func (mg *MCPGateway) ProxyRequest(ctx context.Context, request *MCPRequest) (*MCPResponse, error) {
	startTime := time.Now()

	// Record request
	mg.telemetry.RecordRequest(request)

	// Find target server
	server, err := mg.findServerForMethod(request.Method)
	if err != nil {
		return &MCPResponse{
			ID:   request.ID,
			Error: &MCPError{Code: -32601, Message: "Method not found"},
		}, nil
	}

	// Authorize request
	if !mg.authorizer.Authorize(request, server) {
		return &MCPResponse{
			ID:   request.ID,
			Error: &MCPError{Code: -32600, Message: "Unauthorized"},
		}, nil
	}

	// Execute in sandbox if enabled
	var result map[string]interface{}
	if mg.sandbox.enabled {
		result, err = mg.executeInSandbox(ctx, server, request)
	} else {
		result, err = mg.executeDirect(ctx, server, request)
	}

	// Create response
	response := &MCPResponse{
		ID:        request.ID,
		Timestamp: time.Now(),
		Duration:  time.Since(startTime).Milliseconds(),
	}

	if err != nil {
		response.Error = &MCPError{
			Code:    -32603,
			Message: err.Error(),
		}
		mg.metrics.ErrorsTotal.WithLabelValues("execution_error").Inc()
	} else {
		response.Result = result
	}

	// Record response
	mg.telemetry.RecordResponse(response)

	return response, nil
}

// findServerForMethod finds the appropriate server for a method
func (mg *MCPGateway) findServerForMethod(method string) (*MCPServer, error) {
	mg.mu.RLock()
	defer mg.mu.RUnlock()

	for _, server := range mg.servers {
		if server.Status == ServerStatusActive {
			for _, capability := range server.Capabilities {
				if capability == method {
					return server, nil
				}
			}
		}
	}

	return nil, fmt.Errorf("no server found for method: %s", method)
}

// executeDirect executes a request directly on the server
func (mg *MCPGateway) executeDirect(ctx context.Context, server *MCPServer, request *MCPRequest) (map[string]interface{}, error) {
	// In a real implementation, this would make an HTTP request to the server endpoint
	// For now, we'll simulate execution
	log.Printf("Executing request %s on server %s", request.Method, server.ID)
	
	return map[string]interface{}{
		"result": "simulated execution",
		"server": server.ID,
		"method": request.Method,
	}, nil
}

// executeInSandbox executes a request in a sandboxed environment
func (mg *MCPGateway) executeInSandbox(ctx context.Context, server *MCPServer, request *MCPRequest) (map[string]interface{}, error) {
	// In a real implementation, this would use container-based sandboxing
	log.Printf("Executing request %s on server %s in sandbox", request.Method, server.ID)
	
	return map[string]interface{}{
		"result": "sandboxed execution",
		"server": server.ID,
		"method": request.Method,
		"sandbox": true,
	}, nil
}

// validateServer validates a server registration
func (mg *MCPGateway) validateServer(server *MCPServer) error {
	if server.ID == "" {
		return fmt.Errorf("server ID is required")
	}
	if server.Name == "" {
		return fmt.Errorf("server name is required")
	}
	if server.Endpoint == "" {
		return fmt.Errorf("server endpoint is required")
	}
	if server.Type == "" {
		return fmt.Errorf("server type is required")
	}
	return nil
}

// loadServersFromRegistry loads servers from the registry
func (mg *MCPGateway) loadServersFromRegistry(ctx context.Context) error {
	servers, err := mg.registry.List(ctx, nil)
	if err != nil {
		return err
	}

	for _, server := range servers {
		mg.servers[server.ID] = server
	}

	log.Printf("Loaded %d servers from registry", len(servers))
	return nil
}

// healthCheckRoutine performs periodic health checks
func (mg *MCPGateway) healthCheckRoutine(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		mg.performHealthChecks(ctx)
	}
}

// performHealthChecks checks the health of all registered servers
func (mg *MCPGateway) performHealthChecks(ctx context.Context) {
	mg.mu.RLock()
	servers := make([]*MCPServer, 0, len(mg.servers))
	for _, server := range mg.servers {
		servers = append(servers, server)
	}
	mg.mu.RUnlock()

	for _, server := range servers {
		health := mg.checkServerHealth(server)
		
		mg.mu.Lock()
		server.Health = health
		server.LastSeen = time.Now()
		
		// Update status based on health
		if health.Healthy {
			server.Status = ServerStatusActive
		} else {
			server.Status = ServerStatusError
		}
		mg.mu.Unlock()

		// Update metrics
		statusValue := 1.0
		if !health.Healthy {
			statusValue = 0.0
		}
		mg.metrics.ServerStatus.WithLabelValues(server.ID, string(server.Status)).Set(statusValue)
	}
}

// checkServerHealth checks the health of a single server
func (mg *MCPGateway) checkServerHealth(server *MCPServer) HealthStatus {
	startTime := time.Now()
	
	// In a real implementation, this would make an HTTP request to the server's health endpoint
	// For now, we'll simulate health checks
	healthy := true
	message := "Server is healthy"
	
	return HealthStatus{
		Healthy:   healthy,
		Message:   message,
		CheckTime: time.Now(),
		Latency:   time.Since(startTime).Milliseconds(),
	}
}

// telemetryCollectionRoutine collects and processes telemetry data
func (mg *MCPGateway) telemetryCollectionRoutine(ctx context.Context) {
	for {
		select {
		case request := <-mg.telemetry.requests:
			mg.processRequestTelemetry(request)
		case response := <-mg.telemetry.responses:
			mg.processResponseTelemetry(response)
		case <-ctx.Done():
			return
		}
	}
}

// processRequestTelemetry processes request telemetry
func (mg *MCPGateway) processRequestTelemetry(request *MCPRequest) {
	mg.metrics.RequestsTotal.WithLabelValues(request.Method, request.UserID).Inc()
}

// processResponseTelemetry processes response telemetry
func (mg *MCPGateway) processResponseTelemetry(response *MCPResponse) {
	if response.Error != nil {
		mg.metrics.ErrorsTotal.WithLabelValues(response.Error.Message).Inc()
	}
}

// setupHTTPServer sets up the HTTP server
func (mg *MCPGateway) setupHTTPServer() {
	router := mux.NewRouter()

	// API routes
	router.HandleFunc("/api/v1/servers", mg.handleListServers).Methods("GET")
	router.HandleFunc("/api/v1/servers", mg.handleRegisterServer).Methods("POST")
	router.HandleFunc("/api/v1/servers/{id}", mg.handleUnregisterServer).Methods("DELETE")
	router.HandleFunc("/api/v1/proxy", mg.handleProxyRequest).Methods("POST")
	router.HandleFunc("/api/v1/health", mg.handleHealthCheck).Methods("GET")

	// Metrics endpoint
	router.Handle("/metrics", promhttp.Handler())

	mg.httpServer = &http.Server{
		Addr:    mg.config.ListenAddr,
		Handler: router,
	}
}

// HTTP Handlers
func (mg *MCPGateway) handleListServers(w http.ResponseWriter, r *http.Request) {
	servers, err := mg.ListServers(r.Context(), nil)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(servers)
}

func (mg *MCPGateway) handleRegisterServer(w http.ResponseWriter, r *http.Request) {
	var server MCPServer
	if err := json.NewDecoder(r.Body).Decode(&server); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	if err := mg.RegisterServer(r.Context(), &server); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(server)
}

func (mg *MCPGateway) handleUnregisterServer(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	serverID := vars["id"]

	if err := mg.UnregisterServer(r.Context(), serverID); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

func (mg *MCPGateway) handleProxyRequest(w http.ResponseWriter, r *http.Request) {
	var request MCPRequest
	if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	response, err := mg.ProxyRequest(r.Context(), &request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (mg *MCPGateway) handleHealthCheck(w http.ResponseWriter, r *http.Request) {
	health := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now(),
		"servers":   len(mg.servers),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(health)
}

// Helper functions for creating components
func NewTelemetryCollector() *TelemetryCollector {
	return &TelemetryCollector{
		requests:  make(chan *MCPRequest, 1000),
		responses: make(chan *MCPResponse, 1000),
		metrics:   make(map[string]*prometheus.CounterVec),
		histograms: make(map[string]*prometheus.HistogramVec),
	}
}

func NewAuthorizer() *Authorizer {
	return &Authorizer{
		rules: []AuthorizationRule{},
	}
}

func NewGatewayMetrics() *GatewayMetrics {
	return &GatewayMetrics{
		RequestsTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "mcp_gateway_requests_total",
				Help: "Total number of MCP requests",
			},
			[]string{"method", "user_id"},
		),
		RequestDuration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name: "mcp_gateway_request_duration_seconds",
				Help: "Duration of MCP requests",
			},
			[]string{"method", "server_id"},
		),
		ErrorsTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "mcp_gateway_errors_total",
				Help: "Total number of MCP errors",
			},
			[]string{"error_type"},
		),
		ServerStatus: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "mcp_gateway_server_status",
				Help: "Status of MCP servers",
			},
			[]string{"server_id", "status"},
		),
	}
}

func (a *Authorizer) Authorize(request *MCPRequest, server *MCPServer) bool {
	// Simple authorization logic - in a real implementation, this would be more sophisticated
	return true
}

func (tc *TelemetryCollector) RecordRequest(request *MCPRequest) {
	select {
	case tc.requests <- request:
	default:
		// Channel full, drop the request
	}
}

func (tc *TelemetryCollector) RecordResponse(response *MCPResponse) {
	select {
	case tc.responses <- response:
	default:
		// Channel full, drop the response
	}
}

// Redis registry storage implementation (simplified)
func NewRedisRegistryStorage(addr string) (RegistryStorage, error) {
	// In a real implementation, this would connect to Redis
	return &mockRegistryStorage{}, nil
}

type mockRegistryStorage struct{}

func (m *mockRegistryStorage) Store(ctx context.Context, server *MCPServer) error { return nil }
func (m *mockRegistryStorage) Get(ctx context.Context, id string) (*MCPServer, error) { return nil, fmt.Errorf("not implemented") }
func (m *mockRegistryStorage) List(ctx context.Context, filters map[string]interface{}) ([]*MCPServer, error) { return nil, nil }
func (m *mockRegistryStorage) Delete(ctx context.Context, id string) error { return nil }
