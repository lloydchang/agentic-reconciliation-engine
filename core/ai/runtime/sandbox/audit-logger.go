package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"
)

type AuditEventType string

const (
	EventTypeSandboxCreated   AuditEventType = "sandbox_created"
	EventTypeSandboxDestroyed AuditEventType = "sandbox_destroyed"
	EventTypeSandboxActivity  AuditEventType = "sandbox_activity"
	EventTypeSecurityViolation AuditEventType = "security_violation"
	EventTypeResourceLimitHit AuditEventType = "resource_limit_hit"
)

type AuditEvent struct {
	Timestamp   time.Time      `json:"timestamp"`
	EventType   AuditEventType `json:"event_type"`
	SandboxID   string         `json:"sandbox_id"`
	TaskID      string         `json:"task_id,omitempty"`
	UserID      string         `json:"user_id,omitempty"`
	Resource    string         `json:"resource,omitempty"`
	Action      string         `json:"action"`
	Details     map[string]interface{} `json:"details,omitempty"`
	IPAddress   string         `json:"ip_address,omitempty"`
	UserAgent   string         `json:"user_agent,omitempty"`
	SessionID   string         `json:"session_id,omitempty"`
}

type AuditLogger struct {
	logFile *os.File
	encoder *json.Encoder
}

func NewAuditLogger(logPath string) (*AuditLogger, error) {
	file, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open audit log file: %v", err)
	}

	return &AuditLogger{
		logFile: file,
		encoder: json.NewEncoder(file),
	}, nil
}

func (al *AuditLogger) LogSandboxCreated(sandboxID, taskID string, resources map[string]interface{}) error {
	event := AuditEvent{
		Timestamp: time.Now(),
		EventType: EventTypeSandboxCreated,
		SandboxID: sandboxID,
		TaskID:    taskID,
		Resource:  "sandbox",
		Action:    "create",
		Details: map[string]interface{}{
			"resources": resources,
		},
	}

	return al.logEvent(event)
}

func (al *AuditLogger) LogSandboxDestroyed(sandboxID, taskID string) error {
	event := AuditEvent{
		Timestamp: time.Now(),
		EventType: EventTypeSandboxDestroyed,
		SandboxID: sandboxID,
		TaskID:    taskID,
		Resource:  "sandbox",
		Action:    "destroy",
	}

	return al.logEvent(event)
}

func (al *AuditLogger) LogSandboxActivity(sandboxID, taskID, activity string, details map[string]interface{}) error {
	event := AuditEvent{
		Timestamp: time.Now(),
		EventType: EventTypeSandboxActivity,
		SandboxID: sandboxID,
		TaskID:    taskID,
		Resource:  "sandbox",
		Action:    activity,
		Details:   details,
	}

	return al.logEvent(event)
}

func (al *AuditLogger) LogSecurityViolation(sandboxID, violationType string, details map[string]interface{}) error {
	event := AuditEvent{
		Timestamp: time.Now(),
		EventType: EventTypeSecurityViolation,
		SandboxID: sandboxID,
		Resource:  "security",
		Action:    violationType,
		Details:   details,
	}

	return al.logEvent(event)
}

func (al *AuditLogger) LogResourceLimitHit(sandboxID, resourceType, limit string) error {
	event := AuditEvent{
		Timestamp: time.Now(),
		EventType: EventTypeResourceLimitHit,
		SandboxID: sandboxID,
		Resource:  resourceType,
		Action:    "limit_hit",
		Details: map[string]interface{}{
			"limit": limit,
		},
	}

	return al.logEvent(event)
}

func (al *AuditLogger) logEvent(event AuditEvent) error {
	if err := al.encoder.Encode(event); err != nil {
		log.Printf("Failed to write audit event: %v", err)
		return err
	}

	// Ensure immediate write to disk
	if err := al.logFile.Sync(); err != nil {
		log.Printf("Failed to sync audit log: %v", err)
		return err
	}

	log.Printf("Audit event logged: %s for sandbox %s", event.EventType, event.SandboxID)
	return nil
}

func (al *AuditLogger) Close() error {
	if al.logFile != nil {
		return al.logFile.Close()
	}
	return nil
}

// Global audit logger instance
var GlobalAuditLogger *AuditLogger

func InitAuditLogger(logPath string) error {
	logger, err := NewAuditLogger(logPath)
	if err != nil {
		return err
	}
	GlobalAuditLogger = logger
	return nil
}

func LogSandboxCreated(sandboxID, taskID string, resources map[string]interface{}) {
	if GlobalAuditLogger != nil {
		GlobalAuditLogger.LogSandboxCreated(sandboxID, taskID, resources)
	}
}

func LogSandboxDestroyed(sandboxID, taskID string) {
	if GlobalAuditLogger != nil {
		GlobalAuditLogger.LogSandboxDestroyed(sandboxID, taskID)
	}
}

func LogSandboxActivity(sandboxID, taskID, activity string, details map[string]interface{}) {
	if GlobalAuditLogger != nil {
		GlobalAuditLogger.LogSandboxActivity(sandboxID, taskID, activity, details)
	}
}

func LogSecurityViolation(sandboxID, violationType string, details map[string]interface{}) {
	if GlobalAuditLogger != nil {
		GlobalAuditLogger.LogSecurityViolation(sandboxID, violationType, details)
	}
}

func LogResourceLimitHit(sandboxID, resourceType, limit string) {
	if GlobalAuditLogger != nil {
		GlobalAuditLogger.LogResourceLimitHit(sandboxID, resourceType, limit)
	}
}
