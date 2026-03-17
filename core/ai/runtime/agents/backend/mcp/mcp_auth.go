package mcp

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"
)

// AuthManager handles authentication and authorization
type AuthManager struct {
	config     *MCPConfig
	logger     *log.Logger
	apiKeys    map[string]*APIKey
	tokens     map[string]*Token
	mu         sync.RWMutex
}

// APIKey represents an API key configuration
type APIKey struct {
	Key        string            `json:"key"`
	Name       string            `json:"name"`
	Permissions []string         `json:"permissions"`
	CreatedAt  time.Time         `json:"createdAt"`
	ExpiresAt  *time.Time        `json:"expiresAt,omitempty"`
	Metadata   map[string]string `json:"metadata"`
}

// Token represents a JWT-like token
type Token struct {
	Token       string            `json:"token"`
	UserID      string            `json:"userId"`
	Permissions []string         `json:"permissions"`
	CreatedAt   time.Time         `json:"createdAt"`
	ExpiresAt   time.Time         `json:"expiresAt"`
	Metadata    map[string]string `json:"metadata"`
}

// NewAuthManager creates a new authentication manager
func NewAuthManager(config *MCPConfig) *AuthManager {
	return &AuthManager{
		config:  config,
		logger:  log.New(os.Stderr, "[AUTH] ", log.LstdFlags),
		apiKeys: make(map[string]*APIKey),
		tokens:  make(map[string]*Token),
	}
}

// InitializeDefaultAuth sets up default authentication
func (am *AuthManager) InitializeDefaultAuth() error {
	if !am.config.EnableAuth {
		return nil
	}

	// Add default API key if configured
	if am.config.APIKey != "" {
		defaultKey := &APIKey{
			Key:         am.config.APIKey,
			Name:        "default-api-key",
			Permissions: []string{"*"}, // All permissions
			CreatedAt:   time.Now(),
			Metadata: map[string]string{
				"created_by": "system",
				"purpose":    "default_mcp_access",
			},
		}
		am.apiKeys[am.config.APIKey] = defaultKey
		am.logger.Printf("Added default API key")
	}

	// Add some example API keys for development
	if os.Getenv("MCP_DEV_MODE") == "true" {
		devKey := &APIKey{
			Key:         "dev-api-key-12345",
			Name:        "development-key",
			Permissions: []string{"tools:*", "resources:read"},
			CreatedAt:   time.Now(),
			ExpiresAt:   &[]time.Time{time.Now().Add(24 * time.Hour)}[0],
			Metadata: map[string]string{
				"created_by": "system",
				"purpose":    "development",
			},
		}
		am.apiKeys[devKey.Key] = devKey

		limitedKey := &APIKey{
			Key:         "limited-api-key-67890",
			Name:        "limited-key",
			Permissions: []string{"tools:start_compliance_workflow", "resources:read"},
			CreatedAt:   time.Now(),
			ExpiresAt:   &[]time.Time{time.Now().Add(12 * time.Hour)}[0],
			Metadata: map[string]string{
				"created_by": "system",
				"purpose":    "limited_access",
			},
		}
		am.apiKeys[limitedKey.Key] = limitedKey

		am.logger.Printf("Added development API keys")
	}

	return nil
}

// AuthenticateRequest authenticates an incoming request
func (am *AuthManager) AuthenticateRequest(ctx context.Context, headers map[string]string) (*AuthContext, error) {
	if !am.config.EnableAuth {
		return &AuthContext{
			Authenticated: true,
			Permissions:  []string{"*"},
			UserID:       "anonymous",
		}, nil
	}

	// Check API key in Authorization header
	authHeader := headers["Authorization"]
	if authHeader == "" {
		authHeader = headers["X-API-Key"] // Alternative header
	}

	if authHeader == "" {
		return nil, fmt.Errorf("missing authentication credentials")
	}

	// Extract API key (support Bearer token format)
	var apiKey string
	if strings.HasPrefix(authHeader, "Bearer ") {
		apiKey = strings.TrimPrefix(authHeader, "Bearer ")
	} else {
		apiKey = authHeader
	}

	// Validate API key
	keyInfo, exists := am.getAPIKey(apiKey)
	if !exists {
		return nil, fmt.Errorf("invalid API key")
	}

	// Check if key has expired
	if keyInfo.ExpiresAt != nil && time.Now().After(*keyInfo.ExpiresAt) {
		return nil, fmt.Errorf("API key has expired")
	}

	return &AuthContext{
		Authenticated: true,
		Permissions:  keyInfo.Permissions,
		UserID:       keyInfo.Name,
		Metadata:     keyInfo.Metadata,
	}, nil
}

// AuthorizeAction checks if the auth context has permission for a specific action
func (am *AuthManager) AuthorizeAction(authCtx *AuthContext, action string) error {
	if !am.config.EnableAuth {
		return nil
	}

	if !authCtx.Authenticated {
		return fmt.Errorf("not authenticated")
	}

	// Check for wildcard permission
	for _, permission := range authCtx.Permissions {
		if permission == "*" {
			return nil
		}
	}

	// Check for exact match or wildcard action
	for _, permission := range authCtx.Permissions {
		if permission == action {
			return nil
		}
		if strings.HasSuffix(permission, ":*") {
			prefix := strings.TrimSuffix(permission, ":*")
			if strings.HasPrefix(action, prefix+":") {
				return nil
			}
		}
	}

	return fmt.Errorf("insufficient permissions for action: %s", action)
}

// getAPIKey retrieves API key information
func (am *AuthManager) getAPIKey(key string) (*APIKey, bool) {
	am.mu.RLock()
	defer am.mu.RUnlock()

	keyInfo, exists := am.apiKeys[key]
	return keyInfo, exists
}

// AddAPIKey adds a new API key
func (am *AuthManager) AddAPIKey(key *APIKey) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	if _, exists := am.apiKeys[key.Key]; exists {
		return fmt.Errorf("API key already exists")
	}

	am.apiKeys[key.Key] = key
	am.logger.Printf("Added API key: %s", key.Name)
	return nil
}

// RemoveAPIKey removes an API key
func (am *AuthManager) RemoveAPIKey(key string) error {
	am.mu.Lock()
	defer am.mu.Unlock()

	if _, exists := am.apiKeys[key]; !exists {
		return fmt.Errorf("API key not found")
	}

	delete(am.apiKeys, key)
	am.logger.Printf("Removed API key: %s", key)
	return nil
}

// ListAPIKeys returns all API keys
func (am *AuthManager) ListAPIKeys() []*APIKey {
	am.mu.RLock()
	defer am.mu.RUnlock()

	keys := make([]*APIKey, 0, len(am.apiKeys))
	for _, key := range am.apiKeys {
		keys = append(keys, key)
	}
	return keys
}

// AuthContext represents authentication context
type AuthContext struct {
	Authenticated bool              `json:"authenticated"`
	Permissions   []string          `json:"permissions"`
	UserID        string            `json:"userId"`
	Metadata      map[string]string `json:"metadata"`
}

// SecurityMiddleware provides security middleware for MCP requests
type SecurityMiddleware struct {
	authManager *AuthManager
	logger      *log.Logger
}

// NewSecurityMiddleware creates a new security middleware
func NewSecurityMiddleware(authManager *AuthManager) *SecurityMiddleware {
	return &SecurityMiddleware{
		authManager: authManager,
		logger:      log.New(os.Stderr, "[SECURITY] ", log.LstdFlags),
	}
}

// SecureRequest secures an MCP request
func (sm *SecurityMiddleware) SecureRequest(ctx context.Context, message MCPMessage, headers map[string]string) (*MCPMessage, error) {
	// Authenticate the request
	authCtx, err := sm.authManager.AuthenticateRequest(ctx, headers)
	if err != nil {
		sm.logger.Printf("Authentication failed: %v", err)
		return &MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32000,
				Message: "Authentication failed",
				Data:    err.Error(),
			},
		}, nil
	}

	// Authorize the specific action
	action := sm.getActionForMethod(message.Method)
	if err := sm.authManager.AuthorizeAction(authCtx, action); err != nil {
		sm.logger.Printf("Authorization failed for action %s: %v", action, err)
		return &MCPMessage{
			JSONRPC: "2.0",
			ID:      message.ID,
			Error: &MCPError{
				Code:    -32001,
				Message: "Authorization failed",
				Data:    err.Error(),
			},
		}, nil
	}

	// Log the authorized request
	sm.logger.Printf("Authorized request: %s by user %s", message.Method, authCtx.UserID)

	// Return nil to allow the request to proceed
	return nil, nil
}

// getActionForMethod maps MCP methods to security actions
func (sm *SecurityMiddleware) getActionForMethod(method string) string {
	switch method {
	case "initialize":
		return "mcp:initialize"
	case "tools/list":
		return "tools:list"
	case "tools/call":
		return "tools:call"
	case "resources/list":
		return "resources:list"
	case "resources/read":
		return "resources:read"
	default:
		return fmt.Sprintf("mcp:%s", method)
	}
}

// AuditLogger provides audit logging for MCP operations
type AuditLogger struct {
	logger *log.Logger
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger() *AuditLogger {
	return &AuditLogger{
		logger: log.New(os.Stderr, "[AUDIT] ", log.LstdFlags),
	}
}

// LogRequest logs an MCP request for audit purposes
func (al *AuditLogger) LogRequest(authCtx *AuthContext, message MCPMessage, headers map[string]string) {
	auditEntry := map[string]interface{}{
		"timestamp":   time.Now().Format(time.RFC3339),
		"userId":      authCtx.UserID,
		"method":      message.Method,
		"requestId":   message.ID,
		"userAgent":   headers["User-Agent"],
		"remoteAddr":  headers["X-Forwarded-For"],
		"permissions": authCtx.Permissions,
	}

	// Log as JSON for structured logging
	if jsonData, err := json.Marshal(auditEntry); err == nil {
		al.logger.Printf("REQUEST: %s", string(jsonData))
	} else {
		al.logger.Printf("REQUEST: %s %s by %s", message.Method, message.ID, authCtx.UserID)
	}
}

// LogResponse logs an MCP response for audit purposes
func (al *AuditLogger) LogResponse(authCtx *AuthContext, message MCPMessage, duration time.Duration) {
	auditEntry := map[string]interface{}{
		"timestamp": time.Now().Format(time.RFC3339),
		"userId":    authCtx.UserID,
		"method":    message.Method,
		"requestId": message.ID,
		"success":   message.Error == nil,
		"duration":  duration.String(),
	}

	if message.Error != nil {
		auditEntry["error"] = message.Error.Message
		auditEntry["errorCode"] = message.Error.Code
	}

	// Log as JSON for structured logging
	if jsonData, err := json.Marshal(auditEntry); err == nil {
		al.logger.Printf("RESPONSE: %s", string(jsonData))
	} else {
		status := "SUCCESS"
		if message.Error != nil {
			status = fmt.Sprintf("ERROR (%d)", message.Error.Code)
		}
		al.logger.Printf("RESPONSE: %s %s by %s - %s (took %s)", 
			message.Method, message.ID, authCtx.UserID, status, duration)
	}
}
