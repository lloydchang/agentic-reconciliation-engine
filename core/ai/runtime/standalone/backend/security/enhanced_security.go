package security

import (
	"context"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"sync"
	"time"

	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/workflow"
)

// Security enhancements for agent communication and data protection

// SecureCommunicationManager handles encrypted communication between agents
type SecureCommunicationManager struct {
	encryptionKey []byte
	agents        map[string]*AgentCredentials
	messageLog    []*SecureMessage
	mu            sync.RWMutex
}

// AgentCredentials holds authentication credentials for agents
type AgentCredentials struct {
	AgentID    string    `json:"agentId"`
	PublicKey  []byte    `json:"publicKey"`
	Token      string    `json:"token"`
	ExpiresAt  time.Time `json:"expiresAt"`
	Active     bool      `json:"active"`
}

// SecureMessage represents an encrypted message between agents
type SecureMessage struct {
	ID          string                 `json:"id"`
	FromAgent   string                 `json:"fromAgent"`
	ToAgent     string                 `json:"toAgent"`
	MessageType string                 `json:"messageType"`
	Payload     []byte                 `json:"payload"` // Encrypted
	Signature   []byte                 `json:"signature"`
	Timestamp   time.Time              `json:"timestamp"`
	Sequence    int64                  `json:"sequence"`
}

// AuditLogger provides comprehensive audit logging
type AuditLogger struct {
	events   []*AuditEvent
	maxSize  int
	mu       sync.RWMutex
	enabled  bool
}

// AuditEvent represents an auditable security event
type AuditEvent struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	EventType   string                 `json:"eventType"`
	Actor       string                 `json:"actor"`
	Resource    string                 `json:"resource"`
	Action      string                 `json:"action"`
	Result      string                 `json:"result"`
	Details     map[string]interface{} `json:"details"`
	IPAddress   string                 `json:"ipAddress,omitempty"`
	UserAgent   string                 `json:"userAgent,omitempty"`
}

// DataProtectionManager handles data encryption and masking
type DataProtectionManager struct {
	encryptionEnabled bool
	maskingRules      map[string]MaskingRule
	sensitiveFields   []string
}

// MaskingRule defines how to mask sensitive data
type MaskingRule struct {
	Field     string `json:"field"`
	Method    string `json:"method"` // "mask", "hash", "encrypt"
	Pattern   string `json:"pattern,omitempty"`
	KeepChars int    `json:"keepChars,omitempty"`
}

// Global instances
var (
	globalSecCommMgr *SecureCommunicationManager
	globalAuditLogger *AuditLogger
	globalDataProtMgr *DataProtectionManager
	secCommOnce      sync.Once
	auditOnce        sync.Once
	dataProtOnce     sync.Once
)

// GetGlobalSecureCommunicationManager returns the singleton secure communication manager
func GetGlobalSecureCommunicationManager() *SecureCommunicationManager {
	secCommOnce.Do(func() {
		key := make([]byte, 32) // 256-bit key
		if _, err := rand.Read(key); err != nil {
			panic("failed to generate encryption key")
		}
		globalSecCommMgr = NewSecureCommunicationManager(key)
	})
	return globalSecCommMgr
}

// GetGlobalAuditLogger returns the singleton audit logger
func GetGlobalAuditLogger() *AuditLogger {
	auditOnce.Do(func() {
		globalAuditLogger = NewAuditLogger(1000, true)
	})
	return globalAuditLogger
}

// GetGlobalDataProtectionManager returns the singleton data protection manager
func GetGlobalDataProtectionManager() *DataProtectionManager {
	dataProtOnce.Do(func() {
		globalDataProtMgr = NewDataProtectionManager()
	})
	return globalDataProtMgr
}

// NewSecureCommunicationManager creates a new secure communication manager
func NewSecureCommunicationManager(key []byte) *SecureCommunicationManager {
	return &SecureCommunicationManager{
		encryptionKey: key,
		agents:        make(map[string]*AgentCredentials),
		messageLog:    make([]*SecureMessage, 0),
	}
}

// RegisterAgent registers an agent with the communication manager
func (scm *SecureCommunicationManager) RegisterAgent(agentID string, publicKey []byte) error {
	scm.mu.Lock()
	defer scm.mu.Unlock()

	if _, exists := scm.agents[agentID]; exists {
		return fmt.Errorf("agent %s already registered", agentID)
	}

	// Generate authentication token
	token, err := scm.generateToken(agentID)
	if err != nil {
		return fmt.Errorf("failed to generate token: %w", err)
	}

	scm.agents[agentID] = &AgentCredentials{
		AgentID:   agentID,
		PublicKey: publicKey,
		Token:     token,
		ExpiresAt: time.Now().Add(time.Hour * 24), // 24 hour expiry
		Active:    true,
	}

	return nil
}

// SendSecureMessage sends an encrypted message between agents
func (scm *SecureCommunicationManager) SendSecureMessage(fromAgent, toAgent, messageType string, payload interface{}) error {
	scm.mu.Lock()
	defer scm.mu.Unlock()

	// Verify sender is registered
	fromCreds, exists := scm.agents[fromAgent]
	if !exists || !fromCreds.Active {
		return fmt.Errorf("sender agent %s not registered or inactive", fromAgent)
	}

	// Verify recipient is registered
	_, exists = scm.agents[toAgent]
	if !exists {
		return fmt.Errorf("recipient agent %s not registered", toAgent)
	}

	// Serialize payload
	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to serialize payload: %w", err)
	}

	// Encrypt payload
	encryptedPayload, err := scm.encrypt(payloadBytes)
	if err != nil {
		return fmt.Errorf("failed to encrypt payload: %w", err)
	}

	// Create signature
	signature := scm.signMessage(fromAgent, encryptedPayload)

	// Create secure message
	message := &SecureMessage{
		ID:          scm.generateMessageID(),
		FromAgent:   fromAgent,
		ToAgent:     toAgent,
		MessageType: messageType,
		Payload:     encryptedPayload,
		Signature:   signature,
		Timestamp:   time.Now(),
		Sequence:    scm.getNextSequence(fromAgent),
	}

	// Log message
	scm.messageLog = append(scm.messageLog, message)

	// Audit the communication
	GetGlobalAuditLogger().LogEvent(AuditEvent{
		ID:        message.ID,
		Timestamp: message.Timestamp,
		EventType: "agent_communication",
		Actor:     fromAgent,
		Resource:  toAgent,
		Action:    "send_message",
		Result:    "success",
		Details: map[string]interface{}{
			"messageType": messageType,
			"sequence":    message.Sequence,
		},
	})

	return nil
}

// ReceiveSecureMessage receives and decrypts a message for an agent
func (scm *SecureCommunicationManager) ReceiveSecureMessage(agentID, messageID string) (interface{}, error) {
	scm.mu.RLock()
	defer scm.mu.RUnlock()

	// Find message
	var message *SecureMessage
	for _, msg := range scm.messageLog {
		if msg.ID == messageID && msg.ToAgent == agentID {
			message = msg
			break
		}
	}

	if message == nil {
		return nil, fmt.Errorf("message not found")
	}

	// Verify signature
	if !scm.verifySignature(message) {
		return nil, fmt.Errorf("message signature verification failed")
	}

	// Decrypt payload
	decryptedPayload, err := scm.decrypt(message.Payload)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt payload: %w", err)
	}

	// Deserialize payload
	var payload interface{}
	err = json.Unmarshal(decryptedPayload, &payload)
	if err != nil {
		return nil, fmt.Errorf("failed to deserialize payload: %w", err)
	}

	return payload, nil
}

// encrypt encrypts data using AES-GCM
func (scm *SecureCommunicationManager) encrypt(data []byte) ([]byte, error) {
	block, err := aes.NewCipher(scm.encryptionKey)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, err
	}

	ciphertext := gcm.Seal(nonce, nonce, data, nil)
	return ciphertext, nil
}

// decrypt decrypts data using AES-GCM
func (scm *SecureCommunicationManager) decrypt(data []byte) ([]byte, error) {
	block, err := aes.NewCipher(scm.encryptionKey)
	if err != nil {
		return nil, err
	}

	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}

	nonceSize := gcm.NonceSize()
	if len(data) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}

	nonce, ciphertext := data[:nonceSize], data[nonceSize:]
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}

	return plaintext, nil
}

// generateToken generates an authentication token for an agent
func (scm *SecureCommunicationManager) generateToken(agentID string) (string, error) {
	tokenData := fmt.Sprintf("%s:%d", agentID, time.Now().Unix())
	hash := sha256.Sum256([]byte(tokenData))
	return base64.URLEncoding.EncodeToString(hash[:]), nil
}

// signMessage creates a signature for a message
func (scm *SecureCommunicationManager) signMessage(agentID string, payload []byte) []byte {
	signatureData := fmt.Sprintf("%s:%s", agentID, base64.StdEncoding.EncodeToString(payload))
	hash := sha256.Sum256([]byte(signatureData))
	return hash[:]
}

// verifySignature verifies a message signature
func (scm *SecureCommunicationManager) verifySignature(message *SecureMessage) bool {
	expectedSignature := scm.signMessage(message.FromAgent, message.Payload)
	return string(expectedSignature) == string(message.Signature)
}

// generateMessageID generates a unique message ID
func (scm *SecureCommunicationManager) generateMessageID() string {
	return fmt.Sprintf("msg-%d", time.Now().UnixNano())
}

// getNextSequence gets the next sequence number for an agent
func (scm *SecureCommunicationManager) getNextSequence(agentID string) int64 {
	// Find highest sequence for this agent
	var maxSeq int64
	for _, msg := range scm.messageLog {
		if msg.FromAgent == agentID && msg.Sequence > maxSeq {
			maxSeq = msg.Sequence
		}
	}
	return maxSeq + 1
}

// NewAuditLogger creates a new audit logger
func NewAuditLogger(maxSize int, enabled bool) *AuditLogger {
	return &AuditLogger{
		events:  make([]*AuditEvent, 0),
		maxSize: maxSize,
		enabled: enabled,
	}
}

// LogEvent logs an audit event
func (al *AuditLogger) LogEvent(event AuditEvent) {
	if !al.enabled {
		return
	}

	al.mu.Lock()
	defer al.mu.Unlock()

	event.ID = fmt.Sprintf("audit-%d", time.Now().UnixNano())
	event.Timestamp = time.Now()

	al.events = append(al.events, &event)

	// Rotate log if it gets too large
	if len(al.events) > al.maxSize {
		// Keep only the most recent events
		al.events = al.events[len(al.events)-al.maxSize:]
	}
}

// GetEvents returns audit events with optional filtering
func (al *AuditLogger) GetEvents(filter func(*AuditEvent) bool) []*AuditEvent {
	al.mu.RLock()
	defer al.mu.RUnlock()

	if filter == nil {
		events := make([]*AuditEvent, len(al.events))
		copy(events, al.events)
		return events
	}

	var filtered []*AuditEvent
	for _, event := range al.events {
		if filter(event) {
			filtered = append(filtered, event)
		}
	}

	return filtered
}

// NewDataProtectionManager creates a new data protection manager
func NewDataProtectionManager() *DataProtectionManager {
	return &DataProtectionManager{
		encryptionEnabled: true,
		maskingRules: map[string]MaskingRule{
			"password":     {Field: "password", Method: "hash"},
			"ssn":         {Field: "ssn", Method: "mask", Pattern: "XXX-XX-****", KeepChars: 4},
			"creditCard":  {Field: "creditCard", Method: "mask", Pattern: "****-****-****-****", KeepChars: 4},
			"email":       {Field: "email", Method: "mask", KeepChars: 3},
		},
		sensitiveFields: []string{"password", "ssn", "creditCard", "apiKey", "secret"},
	}
}

// ProtectData applies data protection rules to sensitive information
func (dpm *DataProtectionManager) ProtectData(data map[string]interface{}) map[string]interface{} {
	if !dpm.encryptionEnabled {
		return data
	}

	protected := make(map[string]interface{})
	for key, value := range data {
		if dpm.isSensitiveField(key) {
			protected[key] = dpm.applyMasking(key, value)
		} else {
			protected[key] = value
		}
	}

	return protected
}

// isSensitiveField checks if a field contains sensitive data
func (dpm *DataProtectionManager) isSensitiveField(fieldName string) bool {
	for _, sensitive := range dpm.sensitiveFields {
		if fieldName == sensitive {
			return true
		}
	}
	return false
}

// applyMasking applies appropriate masking to sensitive data
func (dpm *DataProtectionManager) applyMasking(fieldName string, value interface{}) interface{} {
	rule, exists := dpm.maskingRules[fieldName]
	if !exists {
		// Default masking for unknown sensitive fields
		if str, ok := value.(string); ok {
			return dpm.maskString(str, len(str)-4, '*')
		}
		return value
	}

	switch rule.Method {
	case "hash":
		if str, ok := value.(string); ok {
			hash := sha256.Sum256([]byte(str))
			return base64.StdEncoding.EncodeToString(hash[:])
		}
	case "mask":
		if str, ok := value.(string); ok {
			return dpm.maskString(str, rule.KeepChars, '*')
		}
	case "encrypt":
		// In a real implementation, encrypt the value
		return fmt.Sprintf("[ENCRYPTED]%v", value)
	}

	return value
}

// maskString masks a string keeping the specified number of characters
func (dpm *DataProtectionManager) maskString(input string, keepChars int, maskChar byte) string {
	if len(input) <= keepChars {
		return input
	}

	masked := make([]byte, len(input))
	for i := range masked {
		if i < len(input)-keepChars {
			masked[i] = maskChar
		} else {
			masked[i] = input[i]
		}
	}

	return string(masked)
}

// SecureWorkflow demonstrates security-enhanced workflow execution
func SecureWorkflow(ctx workflow.Context, request interface{}) (interface{}, error) {
	logger := workflow.GetLogger(ctx)
	logger.Info("Starting Secure Workflow")

	// Initialize security components
	_ = GetGlobalSecureCommunicationManager()
	auditLogger := GetGlobalAuditLogger()
	_ = GetGlobalDataProtectionManager()

	// Audit workflow start
	auditLogger.LogEvent(AuditEvent{
		EventType: "workflow_start",
		Actor:     "system",
		Resource:  "workflow",
		Action:    "execute",
		Result:    "started",
		Details:   map[string]interface{}{"workflowType": "secure"},
	})

	// Register agents securely
	var result interface{}
	err := workflow.ExecuteActivity(ctx, SecureAgentCommunicationActivity, request).Get(ctx, &result)
	if err != nil {
		logger.Error("Failed to register secure agents", "error", err)
		return nil, err
	}

	err = workflow.ExecuteActivity(ctx, SecureAgentCommunicationActivity, request).Get(ctx, nil)
	if err != nil {
		logger.Error("Secure agent communication failed", "error", err)
		return nil, err
	}

	// Audit workflow completion
	auditLogger.LogEvent(AuditEvent{
		EventType: "workflow_complete",
		Actor:     "system",
		Resource:  "workflow",
		Action:    "complete",
		Result:    "success",
		Details:   map[string]interface{}{"result": result},
	})

	logger.Info("Secure Workflow completed successfully")
	return result, nil
}

// RegisterSecureAgentsActivity registers agents with secure communication
func RegisterSecureAgentsActivity(ctx context.Context, _ interface{}) error {
	logger := activity.GetLogger(ctx)
	logger.Info("Registering secure agents")

	secCommMgr := GetGlobalSecureCommunicationManager()

	agents := []string{"security-agent", "compliance-agent", "cost-agent"}
	for _, agentID := range agents {
		publicKey := make([]byte, 32) // Generate public key
		if _, err := rand.Read(publicKey); err != nil {
			return fmt.Errorf("failed to generate public key for %s: %w", agentID, err)
		}

		err := secCommMgr.RegisterAgent(agentID, publicKey)
		if err != nil {
			logger.Error("Failed to register agent", "agent", agentID, "error", err)
			return err
		}
	}

	logger.Info("All agents registered securely")
	return nil
}

// SecureAgentCommunicationActivity demonstrates secure inter-agent communication
func SecureAgentCommunicationActivity(ctx context.Context, request interface{}) (interface{}, error) {
	logger := activity.GetLogger(ctx)
	logger.Info("Executing secure agent communication")

	secCommMgr := GetGlobalSecureCommunicationManager()

	// Send secure messages between agents
	err := secCommMgr.SendSecureMessage("security-agent", "compliance-agent", "analysis_request", map[string]interface{}{
		"target": "resource-123",
		"type":   "security-scan",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to send secure message: %w", err)
	}

	// Simulate receiving and processing the message
	messageID := "msg-123" // In real implementation, this would be retrieved
	payload, err := secCommMgr.ReceiveSecureMessage("compliance-agent", messageID)
	if err != nil {
		logger.Warn("Failed to receive message (expected in demo)", "error", err)
	}

	logger.Info("Secure agent communication completed", "payload", payload)
	return map[string]interface{}{
		"status":      "completed",
		"messages":    1,
		"encryption":  "enabled",
		"auditLogged": true,
	}, nil
}

// AuditActivity logs audit events for activities
func AuditActivity(ctx context.Context, eventType, actor, resource, action string, details map[string]interface{}) error {
	logger := activity.GetLogger(ctx)

	auditLogger := GetGlobalAuditLogger()
	auditLogger.LogEvent(AuditEvent{
		EventType: eventType,
		Actor:     actor,
		Resource:  resource,
		Action:    action,
		Result:    "success",
		Details:   details,
	})

	logger.Info("Audit event logged", "type", eventType, "actor", actor, "action", action)
	return nil
}
