# Skills Hot Reloading Implementation

## Overview

This document outlines the implementation of hot reloading for the skills system in the development environment. Hot reloading allows developers to modify skill files and see changes reflected immediately without restarting the backend server.

## Requirements Analysis

### Functional Requirements
1. **File System Monitoring**: Watch for changes in skill files and directories
2. **Automatic Reloading**: Reload skills when files are modified
3. **Validation**: Validate skill files before reloading
4. **Error Handling**: Gracefully handle parsing errors without crashing
5. **API Updates**: Update in-memory skill cache automatically

### Non-Functional Requirements
1. **Performance**: Minimal impact on system performance
2. **Reliability**: No memory leaks or file handle issues
3. **Developer Experience**: Clear feedback on reload status
4. **Configuration**: Enable/disable via environment variable

## Implementation Plan

### Phase 1: File System Monitoring

#### File Watcher Implementation
```go
// skills/watcher.go
package skills

import (
    "context"
    "fmt"
    "log"
    "path/filepath"
    "sync"
    "time"

    "github.com/fsnotify/fsnotify"
)

type SkillWatcher struct {
    watcher       *fsnotify.Watcher
    manager       *SkillManager
    debounceTime  time.Duration
    debounceTimer *time.Timer
    mutex         sync.Mutex
    enabled       bool
    logger        *StructuredLogger
}

func NewSkillWatcher(manager *SkillManager, logger *StructuredLogger) (*SkillWatcher, error) {
    watcher, err := fsnotify.NewWatcher()
    if err != nil {
        return nil, fmt.Errorf("failed to create file watcher: %w", err)
    }

    return &SkillWatcher{
        watcher:      watcher,
        manager:      manager,
        debounceTime: 500 * time.Millisecond,
        enabled:      true,
        logger:       logger,
    }, nil
}

func (sw *SkillWatcher) Start(ctx context.Context) error {
    if !sw.enabled {
        sw.logger.Info("Hot reloading is disabled")
        return nil
    }

    // Add watch directories
    for _, dir := range sw.manager.SkillDirs {
        if err := sw.addWatchDirectory(dir); err != nil {
            sw.logger.Error("Failed to add watch directory", err,
                "directory", dir,
            )
            continue
        }
    }

    // Start watching
    go sw.watchLoop(ctx)

    sw.logger.Info("Hot reloading started",
        "watched_directories", sw.manager.SkillDirs,
        "debounce_time", sw.debounceTime,
    )

    return nil
}

func (sw *SkillWatcher) addWatchDirectory(dir string) error {
    // Add the directory itself
    if err := sw.watcher.Add(dir); err != nil {
        return fmt.Errorf("failed to watch directory %s: %w", dir, err)
    }

    // Add all subdirectories
    return filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return err
        }

        if info.IsDir() {
            if err := sw.watcher.Add(path); err != nil {
                sw.logger.Error("Failed to watch subdirectory", err,
                    "path", path,
                )
            }
        }

        return nil
    })
}

func (sw *SkillWatcher) watchLoop(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case event, ok := <-sw.watcher.Events:
            if !ok {
                return
            }
            sw.handleEvent(event)
        case err, ok := <-sw.watcher.Errors:
            if !ok {
                return
            }
            sw.logger.Error("File watcher error", err)
        }
    }
}

func (sw *SkillWatcher) handleEvent(event fsnotify.Event) {
    // Only process skill files
    if !sw.isSkillFile(event.Name) {
        return
    }

    sw.logger.Debug("File system event received",
        "file", event.Name,
        "operation", event.Op.String(),
    )

    // Debounce rapid file changes
    sw.mutex.Lock()
    defer sw.mutex.Unlock()

    if sw.debounceTimer != nil {
        sw.debounceTimer.Stop()
    }

    sw.debounceTimer = time.AfterFunc(sw.debounceTime, func() {
        sw.reloadSkills(event.Name)
    })
}

func (sw *SkillWatcher) isSkillFile(filename string) bool {
    return filepath.Base(filename) == "SKILL.md"
}

func (sw *SkillWatcher) reloadSkills(changedFile string) {
    sw.logger.Info("Reloading skills due to file change",
        "changed_file", changedFile,
    )

    startTime := time.Now()

    // Reload skills
    err := sw.manager.ReloadSkills()
    if err != nil {
        sw.logger.Error("Failed to reload skills", err,
            "changed_file", changedFile,
        )
        return
    }

    loadTime := time.Since(startTime)
    skills := sw.manager.ListSkills()

    sw.logger.Info("Skills reloaded successfully",
        "changed_file", changedFile,
        "load_time", loadTime,
        "skills_count", len(skills),
    )

    // Notify subscribers (WebSocket, etc.)
    sw.notifyReload(changedFile, skills)
}

func (sw *SkillWatcher) notifyReload(changedFile string, skills []*Skill) {
    // Implementation for notifying subscribers
    // Could be WebSocket events, HTTP callbacks, etc.
}

func (sw *SkillWatcher) Stop() error {
    if sw.debounceTimer != nil {
        sw.debounceTimer.Stop()
    }
    return sw.watcher.Close()
}

func (sw *SkillWatcher) SetEnabled(enabled bool) {
    sw.mutex.Lock()
    defer sw.mutex.Unlock()
    sw.enabled = enabled
}
```

### Phase 2: Skill Manager Enhancements

#### Enhanced Skill Manager with Reloading
```go
// skills/manager.go - Enhanced with reloading capabilities
package skills

import (
    "sync"
    "time"
)

type SkillManager struct {
    Skills       map[string]*Skill
    SkillDirs    []string
    SessionID    string
    WorkingDir   string
    logger       *StructuredLogger
    parseErrors  int
    loadTime     time.Duration
    lastLoadTime time.Time
    mutex        sync.RWMutex
    
    // Hot reloading
    watcher      *SkillWatcher
    reloadCount  int
    lastReload   time.Time
    subscribers  []ReloadSubscriber
}

type ReloadSubscriber interface {
    OnSkillsReloaded(skills []*Skill, changedFile string)
}

func (sm *SkillManager) ReloadSkills() error {
    sm.mutex.Lock()
    defer sm.mutex.Unlock()

    startTime := time.Now()

    // Clear existing skills
    sm.Skills = make(map[string]*Skill)
    sm.parseErrors = 0

    // Reload from all directories
    for _, dir := range sm.SkillDirs {
        if err := sm.scanDirectory(dir); err != nil {
            sm.logger.Error("Failed to scan directory during reload", err,
                "directory", dir,
            )
        }
    }

    // Update metrics
    sm.loadTime = time.Since(startTime)
    sm.lastLoadTime = time.Now()
    sm.reloadCount++

    sm.logger.Info("Skills reloaded",
        "reload_count", sm.reloadCount,
        "load_time", sm.loadTime,
        "skills_count", len(sm.Skills),
        "parse_errors", sm.parseErrors,
    )

    return nil
}

func (sm *SkillManager) EnableHotReloading() error {
    if sm.watcher != nil {
        return fmt.Errorf("hot reloading already enabled")
    }

    watcher, err := NewSkillWatcher(sm, sm.logger)
    if err != nil {
        return err
    }

    sm.watcher = watcher

    // Start watcher in background
    go func() {
        ctx, cancel := context.WithCancel(context.Background())
        defer cancel()
        
        if err := watcher.Start(ctx); err != nil {
            sm.logger.Error("Failed to start hot reloading", err)
        }
    }()

    return nil
}

func (sm *SkillManager) DisableHotReloading() error {
    if sm.watcher == nil {
        return nil
    }

    err := sm.watcher.Stop()
    sm.watcher = nil
    return err
}

func (sm *SkillManager) AddReloadSubscriber(subscriber ReloadSubscriber) {
    sm.mutex.Lock()
    defer sm.mutex.Unlock()
    sm.subscribers = append(sm.subscribers, subscriber)
}

func (sm *SkillManager) notifyReload(changedFile string) {
    sm.mutex.RLock()
    skills := make([]*Skill, 0, len(sm.Skills))
    for _, skill := range sm.Skills {
        skills = append(skills, skill)
    }
    subscribers := make([]ReloadSubscriber, len(sm.subscribers))
    copy(subscribers, sm.subscribers)
    sm.mutex.RUnlock()

    for _, subscriber := range subscribers {
        subscriber.OnSkillsReloaded(skills, changedFile)
    }
}

func (sm *SkillManager) GetReloadStats() map[string]interface{} {
    sm.mutex.RLock()
    defer sm.mutex.RUnlock()

    return map[string]interface{}{
        "reload_count":   sm.reloadCount,
        "last_reload":     sm.lastLoadTime,
        "hot_reload_enabled": sm.watcher != nil,
        "watched_directories": sm.SkillDirs,
        "subscribers_count": len(sm.subscribers),
    }
}
```

### Phase 3: WebSocket Integration

#### WebSocket Handler for Real-time Updates
```go
// skills/websocket.go
package skills

import (
    "encoding/json"
    "log"
    "net/http"
    "sync"

    "github.com/gorilla/websocket"
)

type WebSocketManager struct {
    clients    map[*websocket.Conn]bool
    mutex      sync.Mutex
    upgrader   websocket.Upgrader
    manager    *SkillManager
}

type WebSocketMessage struct {
    Type      string      `json:"type"`
    Data      interface{} `json:"data"`
    Timestamp time.Time   `json:"timestamp"`
}

type SkillsReloadMessage struct {
    ChangedFile string  `json:"changed_file"`
    Skills      []*Skill `json:"skills"`
    Count       int     `json:"count"`
}

func NewWebSocketManager(manager *SkillManager) *WebSocketManager {
    return &WebSocketManager{
        clients: make(map[*websocket.Conn]bool),
        upgrader: websocket.Upgrader{
            CheckOrigin: func(r *http.Request) bool {
                return true // Allow all origins in development
            },
        },
        manager: manager,
    }
}

func (wsm *WebSocketManager) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
    conn, err := wsm.upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Printf("WebSocket upgrade failed: %v", err)
        return
    }
    defer conn.Close()

    // Add client
    wsm.mutex.Lock()
    wsm.clients[conn] = true
    wsm.mutex.Unlock()

    // Send initial skills data
    skills := wsm.manager.ListSkills()
    message := WebSocketMessage{
        Type:      "initial_skills",
        Data:      skills,
        Timestamp: time.Now(),
    }
    conn.WriteJSON(message)

    // Handle messages
    for {
        var msg WebSocketMessage
        if err := conn.ReadJSON(&msg); err != nil {
            log.Printf("WebSocket read error: %v", err)
            break
        }

        // Handle different message types
        switch msg.Type {
        case "ping":
            conn.WriteJSON(WebSocketMessage{
                Type:      "pong",
                Timestamp: time.Now(),
            })
        }
    }

    // Remove client
    wsm.mutex.Lock()
    delete(wsm.clients, conn)
    wsm.mutex.Unlock()
}

func (wsm *WebSocketManager) BroadcastSkillsReload(changedFile string, skills []*Skill) {
    message := WebSocketMessage{
        Type: "skills_reload",
        Data: SkillsReloadMessage{
            ChangedFile: changedFile,
            Skills:      skills,
            Count:       len(skills),
        },
        Timestamp: time.Now(),
    }

    wsm.mutex.Lock()
    defer wsm.mutex.Unlock()

    for client := range wsm.clients {
        if err := client.WriteJSON(message); err != nil {
            log.Printf("WebSocket write error: %v", err)
            client.Close()
            delete(wsm.clients, client)
        }
    }
}

// Implement ReloadSubscriber interface
func (wsm *WebSocketManager) OnSkillsReloaded(skills []*Skill, changedFile string) {
    wsm.BroadcastSkillsReload(changedFile, skills)
}
```

### Phase 4: Frontend Integration

#### Frontend Hot Reloading Client
```typescript
// src/services/hotReload.ts
class HotReloadService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private subscribers: Set<(skills: Skill[]) => void> = new Set();

    constructor() {
        this.connect();
    }

    private connect() {
        const wsUrl = `ws://localhost:8081/ws/skills`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('Hot reload WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('Hot reload WebSocket disconnected');
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('Hot reload WebSocket error:', error);
        };
    }

    private handleMessage(message: any) {
        switch (message.type) {
            case 'initial_skills':
                console.log('Received initial skills:', message.data);
                this.notifySubscribers(message.data);
                break;
            case 'skills_reload':
                console.log('Skills reloaded:', message.data);
                this.notifySubscribers(message.data.skills);
                this.showReloadNotification(message.data.changedFile);
                break;
            case 'pong':
                // Ping/pong for connection health
                break;
        }
    }

    private notifySubscribers(skills: Skill[]) {
        this.subscribers.forEach(callback => callback(skills));
    }

    private showReloadNotification(changedFile: string) {
        // Show browser notification
        if (Notification.permission === 'granted') {
            new Notification('Skills Reloaded', {
                body: `Skills reloaded due to change in ${changedFile}`,
                icon: '/favicon.ico'
            });
        }

        // Show in-app notification
        this.showInAppNotification(`Skills reloaded: ${changedFile}`);
    }

    private showInAppNotification(message: string) {
        // Implementation for in-app notification
        const notification = document.createElement('div');
        notification.className = 'hot-reload-notification';
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    private scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
            
            this.reconnectDelay *= 2; // Exponential backoff
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    public subscribe(callback: (skills: Skill[]) => void) {
        this.subscribers.add(callback);
        return () => this.subscribers.delete(callback);
    }

    public ping() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }

    public disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Singleton instance
export const hotReloadService = new HotReloadService();
```

#### React Hook for Hot Reloading
```typescript
// src/hooks/useHotReload.ts
import { useEffect, useState } from 'react';
import { hotReloadService } from '../services/hotReload';
import { Skill } from '../types/skill';

export const useHotReload = () => {
    const [skills, setSkills] = useState<Skill[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [lastReload, setLastReload] = useState<Date | null>(null);

    useEffect(() => {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Subscribe to hot reload updates
        const unsubscribe = hotReloadService.subscribe((updatedSkills) => {
            setSkills(updatedSkills);
            setLastReload(new Date());
        });

        // Set up connection monitoring
        const checkConnection = () => {
            setIsConnected(hotReloadService.isConnected());
        };

        const interval = setInterval(checkConnection, 1000);

        return () => {
            unsubscribe();
            clearInterval(interval);
        };
    }, []);

    return {
        skills,
        isConnected,
        lastReload,
        reconnect: () => hotReloadService.connect(),
        disconnect: () => hotReloadService.disconnect()
    };
};
```

### Phase 5: Configuration and Environment

#### Environment Configuration
```go
// config/hot_reload.go
package config

type HotReloadConfig struct {
    Enabled       bool          `env:"HOT_RELOAD_ENABLED" envDefault:"true"`
    DebounceTime  time.Duration `env:"HOT_RELOAD_DEBOUNCE" envDefault:"500ms"`
    WebSocketPath string        `env:"HOT_RELOAD_WS_PATH" envDefault:"/ws/skills"`
    MaxFileSize   int64         `env:"HOT_RELOAD_MAX_FILE_SIZE" envDefault:"1048576"` // 1MB
    WatchPatterns []string      `env:"HOT_RELOAD_PATTERNS" envDefault:"*.md,*.yaml,*.yml"`
}

func LoadHotReloadConfig() HotReloadConfig {
    return HotReloadConfig{
        Enabled:       getBoolEnv("HOT_RELOAD_ENABLED", true),
        DebounceTime:  getDurationEnv("HOT_RELOAD_DEBOUNCE", 500*time.Millisecond),
        WebSocketPath: getStringEnv("HOT_RELOAD_WS_PATH", "/ws/skills"),
        MaxFileSize:   getInt64Env("HOT_RELOAD_MAX_FILE_SIZE", 1048576),
        WatchPatterns: getStringSliceEnv("HOT_RELOAD_PATTERNS", []string{"*.md", "*.yaml", "*.yml"}),
    }
}
```

#### Main Integration
```go
// main.go - Updated with hot reloading
func main() {
    // Load configuration
    config := loadConfig()
    hotReloadConfig := config.LoadHotReloadConfig()

    // Initialize skills service
    skillService := skills.NewSkillService("../../../../../", "session-"+time.Now().Format("20060102150405"))
    
    // Enable hot reloading if configured
    if hotReloadConfig.Enabled {
        if err := skillService.GetManager().EnableHotReloading(); err != nil {
            log.Printf("Failed to enable hot reloading: %v", err)
        } else {
            log.Printf("Hot reloading enabled")
        }
    }

    // Setup WebSocket manager
    wsManager := skills.NewWebSocketManager(skillService.GetManager())
    skillService.GetManager().AddReloadSubscriber(wsManager)

    // Setup router
    r := mux.NewRouter()
    registerAPIRoutes(r, skillService)
    
    // Add WebSocket endpoint
    r.HandleFunc(hotReloadConfig.WebSocketPath, wsManager.HandleWebSocket)

    // Start server
    log.Printf("Starting enhanced HTTP server on :8081")
    log.Printf("Hot reloading: %s", map[bool]string{true: "enabled", false: "disabled"}[hotReloadConfig.Enabled])
    log.Fatal(http.ListenAndServe(":8081", r))
}
```

## Testing Strategy

### Unit Tests
```go
// skills/watcher_test.go
package skills

import (
    "os"
    "path/filepath"
    "testing"
    "time"
)

func TestSkillWatcher(t *testing.T) {
    // Create temporary directory
    tempDir := t.TempDir()
    
    // Create skill manager
    manager := NewSkillManager(tempDir, "test-session", NewStructuredLogger(LogLevelDebug, os.Stdout))
    
    // Create watcher
    watcher, err := NewSkillWatcher(manager, NewStructuredLogger(LogLevelDebug, os.Stdout))
    require.NoError(t, err)
    defer watcher.Stop()

    // Add watch directory
    err = watcher.addWatchDirectory(tempDir)
    require.NoError(t, err)

    // Create test skill file
    skillFile := filepath.Join(tempDir, "test-skill", "SKILL.md")
    err = os.MkdirAll(filepath.Dir(skillFile), 0755)
    require.NoError(t, err)

    // Write initial skill file
    initialContent := `---
name: test-skill
description: Test skill for hot reloading
version: 1.0.0
---
`
    err = os.WriteFile(skillFile, []byte(initialContent), 0644)
    require.NoError(t, err)

    // Wait for file to be processed
    time.Sleep(1 * time.Second)

    // Verify skill was loaded
    skills := manager.ListSkills()
    assert.Len(t, skills, 1)
    assert.Equal(t, "test-skill", skills[0].Name)

    // Modify skill file
    modifiedContent := `---
name: test-skill
description: Modified test skill for hot reloading
version: 1.1.0
---
`
    err = os.WriteFile(skillFile, []byte(modifiedContent), 0644)
    require.NoError(t, err)

    // Wait for reload
    time.Sleep(1 * time.Second)

    // Verify skill was updated
    skills = manager.ListSkills()
    assert.Len(t, skills, 1)
    assert.Equal(t, "test-skill", skills[0].Name)
    assert.Equal(t, "Modified test skill for hot reloading", skills[0].Description)
    assert.Equal(t, "1.1.0", skills[0].Version)
}
```

### Integration Tests
```go
// integration_test.go
func TestHotReloadingIntegration(t *testing.T) {
    // Setup test server with hot reloading
    skillService := NewSkillService("../../../", "test-session")
    hotReloadConfig := HotReloadConfig{Enabled: true}
    
    err := skillService.GetManager().EnableHotReloading()
    require.NoError(t, err)

    router := setupRouterWithHotReloading(skillService, hotReloadConfig)
    server := httptest.NewServer(router)
    defer server.Close()

    // Connect WebSocket
    wsURL := "ws" + server.URL[4:] + "/ws/skills"
    ws, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
    require.NoError(t, err)
    defer ws.Close()

    // Wait for initial message
    _, _, err = ws.ReadMessage()
    require.NoError(t, err)

    // Modify a skill file
    skillFile := "../../../core/ai/skills/skills/cloud-compliance-auditor/SKILL.md"
    content, err := os.ReadFile(skillFile)
    require.NoError(t, err)

    modifiedContent := string(content) + "\n# Modified for test\n"
    err = os.WriteFile(skillFile, []byte(modifiedContent), 0644)
    require.NoError(t, err)

    // Wait for reload message
    _, message, err := ws.ReadMessage()
    require.NoError(t, err)

    var wsMessage WebSocketMessage
    err = json.Unmarshal(message, &wsMessage)
    require.NoError(t, err)

    assert.Equal(t, "skills_reload", wsMessage.Type)
    
    // Restore original file
    err = os.WriteFile(skillFile, content, 0644)
    require.NoError(t, err)
}
```

## Performance Considerations

### Debouncing Strategy
```go
// Enhanced debouncing with file size limits
func (sw *SkillWatcher) handleEvent(event fsnotify.Event) {
    // Check file size limit
    if stat, err := os.Stat(event.Name); err == nil {
        if stat.Size() > sw.maxFileSize {
            sw.logger.Warn("File too large for hot reloading",
                "file", event.Name,
                "size", stat.Size,
                "max_size", sw.maxFileSize,
            )
            return
        }
    }

    // Enhanced debouncing with file pattern matching
    if !sw.matchesWatchPatterns(event.Name) {
        return
    }

    // Existing debouncing logic...
}

func (sw *SkillWatcher) matchesWatchPatterns(filename string) bool {
    for _, pattern := range sw.watchPatterns {
        if matched, _ := filepath.Match(pattern, filepath.Base(filename)); matched {
            return true
        }
    }
    return false
}
```

### Memory Management
```go
// Memory-efficient skill reloading
func (sm *SkillManager) ReloadSkills() error {
    sm.mutex.Lock()
    defer sm.mutex.Unlock()

    // Create new skills map to avoid memory issues
    newSkills := make(map[string]*Skill)
    
    // Load into new map first
    for _, dir := range sm.SkillDirs {
        if err := sm.scanDirectoryToMap(dir, newSkills); err != nil {
            sm.logger.Error("Failed to scan directory during reload", err,
                "directory", dir,
            )
        }
    }

    // Replace atomically
    sm.Skills = newSkills
    
    return nil
}
```

## Security Considerations

### File System Access Control
```go
// Security checks for hot reloading
func (sw *SkillWatcher) validateFile(filename string) error {
    // Check if file is in allowed directory
    absPath, err := filepath.Abs(filename)
    if err != nil {
        return err
    }

    for _, allowedDir := range sw.allowedDirs {
        if strings.HasPrefix(absPath, allowedDir) {
            return nil
        }
    }

    return fmt.Errorf("file outside allowed directories: %s", filename)
}
```

### Input Validation
```go
// Validate skill content before reloading
func (sm *SkillManager) validateSkillContent(content []byte) error {
    // Check for malicious content
    if containsSuspiciousPatterns(content) {
        return fmt.Errorf("suspicious content detected")
    }

    // Validate YAML structure
    if !isValidYAML(content) {
        return fmt.Errorf("invalid YAML structure")
    }

    return nil
}
```

## Troubleshooting Guide

### Common Issues

#### 1. File Watcher Not Detecting Changes
**Symptoms**: Skills not reloading when files are modified
**Solutions**:
```bash
# Check file permissions
ls -la core/ai/skills/skills/

# Check if file system supports notifications
inotifywatch -v core/ai/skills/skills/

# Restart with debug logging
HOT_RELOAD_ENABLED=true DEBUG=true go run main.go
```

#### 2. WebSocket Connection Issues
**Symptoms**: Frontend not receiving reload notifications
**Solutions**:
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8081/ws/skills

# Check CORS configuration
curl -I -H "Origin: http://localhost:8080" http://localhost:8081/ws/skills

# Check browser console for WebSocket errors
```

#### 3. Performance Issues
**Symptoms**: High CPU usage during file watching
**Solutions**:
```bash
# Monitor file watcher activity
top -p $(pgrep -f "go run main.go")

# Check for excessive file events
inotifywatch -v -t 60 core/ai/skills/skills/

# Increase debounce time
HOT_RELOAD_DEBOUNCE=2000ms go run main.go
```

### Debug Commands
```bash
# Enable hot reloading debug
export HOT_RELOAD_ENABLED=true
export DEBUG=true
export LOG_LEVEL=DEBUG

# Test file watching
inotifywait -m -r core/ai/skills/skills/

# Monitor WebSocket traffic
wscat -c ws://localhost:8081/ws/skills

# Check reload statistics
curl http://localhost:8081/debug/skills | jq '.manager.reload_stats'
```

## Future Enhancements

### Advanced Features
1. **Selective Reloading**: Only reload changed skills instead of all
2. **Dependency Tracking**: Reload dependent skills when prerequisites change
3. **Validation Pipeline**: Multi-stage validation with detailed error reporting
4. **Performance Monitoring**: Track reload times and file system performance

### Integration Enhancements
1. **IDE Integration**: VS Code and JetBrains plugin support
2. **Git Integration**: Automatic reloading on git checkout/merge
3. **CI/CD Integration**: Test hot reloading in automated pipelines
4. **Multi-environment Support**: Different configurations for dev/staging/prod

---

**Implementation Start**: March 31, 2026  
**Target Completion**: April 14, 2026  
**Owner**: Frontend Team  
**Status**: Ready for Implementation
