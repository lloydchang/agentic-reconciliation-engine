package dispatcher

import (
	"context"
	"fmt"
	"sync"

	"agentic-reconciliation-engine/core/ai/runtime/open-swe-integration/shared"
)

// UnifiedDispatcher routes events from all platforms to appropriate handlers
type UnifiedDispatcher struct {
	handlers map[string]map[string]shared.TriggerHandler // platform -> eventType -> handler
	mutex    sync.RWMutex
}

// NewUnifiedDispatcher creates a new unified event dispatcher
func NewUnifiedDispatcher() *UnifiedDispatcher {
	return &UnifiedDispatcher{
		handlers: make(map[string]map[string]shared.TriggerHandler),
	}
}

// RegisterHandler registers a handler for a specific platform and event type
func (d *UnifiedDispatcher) RegisterHandler(platform, eventType string, handler shared.TriggerHandler) error {
	d.mutex.Lock()
	defer d.mutex.Unlock()

	if d.handlers[platform] == nil {
		d.handlers[platform] = make(map[string]shared.TriggerHandler)
	}

	if _, exists := d.handlers[platform][eventType]; exists {
		return fmt.Errorf("handler already registered for %s/%s", platform, eventType)
	}

	d.handlers[platform][eventType] = handler
	return nil
}

// Dispatch routes an event to the appropriate handler
func (d *UnifiedDispatcher) Dispatch(ctx context.Context, event shared.TriggerEvent) error {
	d.mutex.RLock()
	defer d.mutex.RUnlock()

	// Set correlation ID if not provided
	if event.CorrelationID == "" {
		event.CorrelationID = fmt.Sprintf("%s-%s-%d", event.Platform, event.ID, event.Timestamp.Unix())
	}

	platformHandlers, platformExists := d.handlers[event.Platform]
	if !platformExists {
		return fmt.Errorf("no handlers registered for platform: %s", event.Platform)
	}

	handler, handlerExists := platformHandlers[event.Type]
	if !handlerExists {
		// Try wildcard handler for the platform
		if wildcardHandler, hasWildcard := platformHandlers["*"]; hasWildcard {
			handler = wildcardHandler
		} else {
			return fmt.Errorf("no handler registered for %s/%s", event.Platform, event.Type)
		}
	}

	// Add correlation context
	ctx = context.WithValue(ctx, "correlation_id", event.CorrelationID)
	ctx = context.WithValue(ctx, "platform", event.Platform)
	ctx = context.WithValue(ctx, "user_id", event.UserID)

	return handler.HandleEvent(ctx, event)
}

// ListHandlers returns all registered handlers
func (d *UnifiedDispatcher) ListHandlers() map[string]map[string]bool {
	d.mutex.RLock()
	defer d.mutex.RUnlock()

	result := make(map[string]map[string]bool)
	for platform, handlers := range d.handlers {
		result[platform] = make(map[string]bool)
		for eventType := range handlers {
			result[platform][eventType] = true
		}
	}
	return result
}

// UnregisterHandler removes a handler registration
func (d *UnifiedDispatcher) UnregisterHandler(platform, eventType string) error {
	d.mutex.Lock()
	defer d.mutex.Unlock()

	if platformHandlers, exists := d.handlers[platform]; exists {
		if _, handlerExists := platformHandlers[eventType]; handlerExists {
			delete(platformHandlers, eventType)
			// Clean up empty platform maps
			if len(platformHandlers) == 0 {
				delete(d.handlers, platform)
			}
			return nil
		}
	}
	return fmt.Errorf("handler not found for %s/%s", platform, eventType)
}
