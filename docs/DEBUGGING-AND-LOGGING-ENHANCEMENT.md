# Debugging and Logging Enhancement - Technical Documentation

## Overview

This document details the comprehensive debugging and logging enhancements implemented to provide full visibility into the skills discovery and loading process. The enhancements include structured logging, debug endpoints, and troubleshooting utilities.

## Logging Architecture

### Log Levels
```go
type LogLevel int

const (
    LogLevelDebug LogLevel = iota
    LogLevelInfo
    LogLevelWarn
    LogLevelError
    LogLevelFatal
)

var logLevelNames = map[LogLevel]string{
    LogLevelDebug: "DEBUG",
    LogLevelInfo:  "INFO",
    LogLevelWarn:  "WARN",
    LogLevelError: "ERROR",
    LogLevelFatal: "FATAL",
}
```

### Structured Logger
```go
type StructuredLogger struct {
    level  LogLevel
    logger *log.Logger
    output io.Writer
}

func NewStructuredLogger(level LogLevel, output io.Writer) *StructuredLogger {
    return &StructuredLogger{
        level:  level,
        logger: log.New(output, "", 0),
        output: output,
    }
}

func (l *StructuredLogger) Debug(msg string, fields ...interface{}) {
    if l.level <= LogLevelDebug {
        l.log(LogLevelDebug, msg, fields...)
    }
}

func (l *StructuredLogger) Info(msg string, fields ...interface{}) {
    if l.level <= LogLevelInfo {
        l.log(LogLevelInfo, msg, fields...)
    }
}

func (l *StructuredLogger) Error(msg string, err error, fields ...interface{}) {
    if l.level <= LogLevelError {
        l.log(LogLevelError, msg, append([]interface{}{err}, fields...)...)
    }
}
```

## Skills Discovery Logging

### 1. Service Initialization Logging
**File**: `core/ai/runtime/agents/backend/skills/service.go`

```go
func NewSkillService(workingDir, sessionID string) *SkillService {
    logger := NewStructuredLogger(LogLevelInfo, os.Stdout)
    
    logger.Info("Initializing skills service", 
        "working_dir", workingDir,
        "session_id", sessionID,
    )
    
    ss := &SkillService{
        manager:    NewSkillManager(workingDir, sessionID, logger),
        sessionID:  sessionID,
        startTime:  time.Now(),
        logger:     logger,
    }
    
    // Initialize skill discovery
    ss.initializeSkillDiscovery()
    
    logger.Info("Skills service initialization completed",
        "skills_loaded", len(ss.manager.ListSkills()),
        "initialization_time", time.Since(ss.startTime),
    )
    
    return ss
}
```

### 2. Directory Discovery Logging
```go
func (ss *SkillService) initializeSkillDiscovery() {
    currentDir, err := os.Getwd()
    if err != nil {
        ss.logger.Error("Failed to get current directory", err)
        return
    }
    
    ss.logger.Info("Starting skills discovery",
        "current_dir", currentDir,
        "session_id", ss.sessionID,
    )
    
    // Discover project skills
    ss.discoverProjectSkills(currentDir)
    
    ss.logger.Info("Skills discovery completed",
        "total_skills", len(ss.manager.ListSkills()),
        "session_id", ss.sessionID,
    )
}
```

### 3. Path Resolution Logging
```go
func (ss *SkillService) discoverProjectSkills(currentDir string) {
    // Define search paths with logging
    searchPaths := []string{
        filepath.Join(currentDir, "core", "ai", "skills"),
        filepath.Join(currentDir, "skills"),
        filepath.Join(currentDir, ".agents", "skills"),
    }
    
    ss.logger.Info("Checking skills directories", 
        "search_paths", searchPaths,
    )
    
    foundPaths := []string{}
    
    // Check each path
    for _, path := range searchPaths {
        ss.logger.Debug("Checking skills directory", "path", path)
        
        if stat, err := os.Stat(path); err == nil {
            if stat.IsDir() {
                ss.logger.Info("Found skills directory", 
                    "path", path,
                    "is_dir", true,
                )
                foundPaths = append(foundPaths, path)
                ss.manager.AddSkillDirectory(path)
            } else {
                ss.logger.Warn("Path exists but is not a directory", 
                    "path", path,
                )
            }
        } else {
            ss.logger.Debug("Skills directory not found", 
                "path", path,
                "error", err.Error(),
            )
        }
    }
    
    if len(foundPaths) == 0 {
        ss.logger.Warn("No skills directories found",
            "searched_paths", searchPaths,
        )
    } else {
        ss.logger.Info("Skills directories discovered",
            "found_count", len(foundPaths),
            "found_paths", foundPaths,
        )
    }
    
    // Load skills from discovered directories
    startTime := time.Now()
    ss.manager.LoadSkills()
    loadTime := time.Since(startTime)
    
    ss.logger.Info("Skills loading completed",
        "load_time", loadTime,
        "skills_count", len(ss.manager.ListSkills()),
    )
}
```

## Skill Manager Logging

### 1. Manager Initialization
**File**: `core/ai/runtime/agents/backend/skills/skill.go`

```go
func NewSkillManager(workingDir, sessionID string, logger *StructuredLogger) *SkillManager {
    sm := &SkillManager{
        Skills:       make(map[string]*Skill),
        SkillDirs:    []string{},
        SessionID:    sessionID,
        WorkingDir:   workingDir,
        logger:       logger,
        parseErrors:  0,
        loadTime:     0,
    }
    
    logger.Info("Skill manager initialized",
        "working_dir", workingDir,
        "session_id", sessionID,
    )
    
    return sm
}
```

### 2. Directory Scanning with Detailed Logging
```go
func (sm *SkillManager) scanDirectory(dirPath string) error {
    startTime := time.Now()
    
    sm.logger.Info("Starting directory scan",
        "directory", dirPath,
        "session_id", sm.SessionID,
    )
    
    entries, err := os.ReadDir(dirPath)
    if err != nil {
        sm.logger.Error("Failed to read directory", err,
            "directory", dirPath,
        )
        return err
    }
    
    sm.logger.Debug("Directory entries found",
        "directory", dirPath,
        "entry_count", len(entries),
    )
    
    skillCount := 0
    parseErrors := 0
    
    for _, entry := range entries {
        if !entry.IsDir() {
            sm.logger.Debug("Skipping non-directory entry",
                "entry", entry.Name(),
                "directory", dirPath,
            )
            continue
        }
        
        skillPath := filepath.Join(dirPath, entry.Name(), "SKILL.md")
        sm.logger.Debug("Checking for skill file",
            "skill_path", skillPath,
            "skill_name", entry.Name(),
        )
        
        if stat, err := os.Stat(skillPath); err == nil {
            sm.logger.Debug("Found skill file",
                "skill_path", skillPath,
                "file_size", stat.Size(),
                "modified_time", stat.ModTime(),
            )
            
            skill, err := parseSkill(skillPath, sm.logger)
            if err != nil {
                sm.logger.Error("Failed to parse skill", err,
                    "skill_path", skillPath,
                    "skill_name", entry.Name(),
                )
                parseErrors++
                sm.parseErrors++
                continue
            }
            
            if err := sm.addSkill(skill); err != nil {
                sm.logger.Error("Failed to add skill", err,
                    "skill_name", skill.Name,
                    "skill_path", skillPath,
                )
                parseErrors++
                sm.parseErrors++
                continue
            }
            
            skillCount++
            sm.logger.Info("Skill loaded successfully",
                "skill_name", skill.Name,
                "skill_path", skillPath,
                "version", skill.Version,
                "risk_level", skill.RiskLevel,
            )
        } else {
            sm.logger.Debug("No SKILL.md file found",
                "skill_directory", entry.Name(),
                "parent_directory", dirPath,
                "error", err.Error(),
            )
        }
    }
    
    scanTime := time.Since(startTime)
    sm.logger.Info("Directory scan completed",
        "directory", dirPath,
        "skills_found", skillCount,
        "parse_errors", parseErrors,
        "scan_time", scanTime,
        "session_id", sm.SessionID,
    )
    
    return nil
}
```

### 3. Skill Parsing with Validation Logging
```go
func parseSkill(filePath string, logger *StructuredLogger) (*Skill, error) {
    startTime := time.Now()
    
    logger.Debug("Starting skill parsing",
        "file_path", filePath,
    )
    
    // Read file content
    content, err := os.ReadFile(filePath)
    if err != nil {
        logger.Error("Failed to read skill file", err,
            "file_path", filePath,
        )
        return nil, fmt.Errorf("failed to read file: %w", err)
    }
    
    logger.Debug("Skill file read successfully",
        "file_path", filePath,
        "file_size", len(content),
    )
    
    // Extract YAML frontmatter
    yamlContent := extractYAMLFrontmatter(content)
    if yamlContent == "" {
        logger.Error("No YAML frontmatter found in skill file", nil,
            "file_path", filePath,
        )
        return nil, fmt.Errorf("no YAML frontmatter found")
    }
    
    logger.Debug("YAML frontmatter extracted",
        "file_path", filePath,
        "yaml_length", len(yamlContent),
    )
    
    // Parse YAML
    var skill Skill
    err = yaml.Unmarshal([]byte(yamlContent), &skill)
    if err != nil {
        logger.Error("Failed to parse YAML frontmatter", err,
            "file_path", filePath,
            "yaml_preview", yamlContent[:min(100, len(yamlContent))],
        )
        return nil, fmt.Errorf("failed to parse YAML: %w", err)
    }
    
    // Validate required fields
    if err := validateSkill(&skill, logger); err != nil {
        logger.Error("Skill validation failed", err,
            "file_path", filePath,
            "skill_name", skill.Name,
        )
        return nil, err
    }
    
    // Set additional fields
    skill.FilePath = filePath
    skill.Content = string(content)
    skill.LastModified = getFileModTime(filePath)
    
    parseTime := time.Since(startTime)
    
    logger.Info("Skill parsed successfully",
        "skill_name", skill.Name,
        "file_path", filePath,
        "version", skill.Version,
        "risk_level", skill.RiskLevel,
        "autonomy", skill.Autonomy,
        "parse_time", parseTime,
    )
    
    return &skill, nil
}
```

### 4. Skill Validation with Detailed Logging
```go
func validateSkill(skill *Skill, logger *StructuredLogger) error {
    logger.Debug("Starting skill validation",
        "skill_name", skill.Name,
    )
    
    validationErrors := []string{}
    
    // Check required fields
    if skill.Name == "" {
        validationErrors = append(validationErrors, "name is required")
        logger.Error("Skill name is missing", nil,
            "skill_file", skill.FilePath,
        )
    } else {
        // Validate name format
        if !isValidSkillName(skill.Name) {
            validationErrors = append(validationErrors, "invalid name format")
            logger.Error("Skill name format is invalid", nil,
                "skill_name", skill.Name,
                "expected_format", "lowercase-hyphen-separated",
            )
        }
    }
    
    if skill.Description == "" {
        validationErrors = append(validationErrors, "description is required")
        logger.Error("Skill description is missing", nil,
            "skill_name", skill.Name,
        )
    }
    
    // Validate metadata fields
    if skill.RiskLevel != "" {
        validRiskLevels := []string{"low", "medium", "high", "critical"}
        if !contains(validRiskLevels, skill.RiskLevel) {
            validationErrors = append(validationErrors, "invalid risk level")
            logger.Error("Invalid risk level", nil,
                "skill_name", skill.Name,
                "risk_level", skill.RiskLevel,
                "valid_levels", validRiskLevels,
            )
        }
    }
    
    if skill.Autonomy != "" {
        validAutonomyLevels := []string{"manual", "conditional", "auto", "fully_auto"}
        if !contains(validAutonomyLevels, skill.Autonomy) {
            validationErrors = append(validationErrors, "invalid autonomy level")
            logger.Error("Invalid autonomy level", nil,
                "skill_name", skill.Name,
                "autonomy", skill.Autonomy,
                "valid_levels", validAutonomyLevels,
            )
        }
    }
    
    if len(validationErrors) > 0 {
        logger.Error("Skill validation failed with multiple errors", nil,
            "skill_name", skill.Name,
            "validation_errors", validationErrors,
        )
        return fmt.Errorf("validation failed: %s", strings.Join(validationErrors, ", "))
    }
    
    logger.Debug("Skill validation passed",
        "skill_name", skill.Name,
        "risk_level", skill.RiskLevel,
        "autonomy", skill.Autonomy,
    )
    
    return nil
}
```

## Debug Endpoints

### 1. Skills Debug Endpoint
```go
func (ss *SkillService) DebugSkillsHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    debugInfo := map[string]interface{}{
        "session_id": ss.sessionID,
        "start_time": ss.startTime,
        "uptime": time.Since(ss.startTime).String(),
        "manager": ss.manager.GetDebugInfo(),
    }
    
    json.NewEncoder(w).Encode(debugInfo)
}
```

### 2. Manager Debug Information
```go
func (sm *SkillManager) GetDebugInfo() map[string]interface{} {
    skills := sm.ListSkills()
    
    // Categorize skills
    categories := map[string]int{
        "compliance": 0,
        "security":   0,
        "automation": 0,
        "other":      0,
    }
    
    riskLevels := map[string]int{
        "low":      0,
        "medium":   0,
        "high":     0,
        "critical": 0,
        "":         0, // unspecified
    }
    
    autonomyLevels := map[string]int{
        "manual":     0,
        "conditional": 0,
        "auto":       0,
        "fully_auto": 0,
        "":           0, // unspecified
    }
    
    for _, skill := range skills {
        // Categorize by name
        if strings.Contains(skill.Name, "compliance") {
            categories["compliance"]++
        } else if strings.Contains(skill.Name, "security") {
            categories["security"]++
        } else if strings.Contains(skill.Name, "automation") || strings.Contains(skill.Name, "optimize") {
            categories["automation"]++
        } else {
            categories["other"]++
        }
        
        // Count risk levels
        riskLevels[skill.RiskLevel]++
        
        // Count autonomy levels
        autonomyLevels[skill.Autonomy]++
    }
    
    return map[string]interface{}{
        "total_skills":      len(skills),
        "skill_directories": sm.SkillDirs,
        "parse_errors":      sm.parseErrors,
        "load_time":         sm.loadTime.String(),
        "categories":        categories,
        "risk_levels":       riskLevels,
        "autonomy_levels":   autonomyLevels,
        "session_id":        sm.SessionID,
        "working_dir":       sm.WorkingDir,
        "skills":            skills,
    }
}
```

### 3. Detailed Skill Information
```go
func (ss *SkillService) DebugSkillHandler(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    skillName := vars["name"]
    
    w.Header().Set("Content-Type", "application/json")
    
    skill := ss.manager.GetSkill(skillName)
    if skill == nil {
        http.Error(w, "Skill not found", http.StatusNotFound)
        return
    }
    
    debugInfo := map[string]interface{}{
        "skill": skill,
        "file_info": map[string]interface{}{
            "exists": fileExists(skill.FilePath),
            "size":    getFileSize(skill.FilePath),
            "modified": getFileModTime(skill.FilePath),
        },
        "validation": map[string]interface{}{
            "name_valid":       isValidSkillName(skill.Name),
            "risk_level_valid": contains([]string{"low", "medium", "high", "critical"}, skill.RiskLevel),
            "autonomy_valid":   contains([]string{"manual", "conditional", "auto", "fully_auto"}, skill.Autonomy),
        },
    }
    
    json.NewEncoder(w).Encode(debugInfo)
}
```

## Performance Monitoring

### 1. Metrics Collection
```go
type SkillsMetrics struct {
    TotalSkills        int           `json:"total_skills"`
    LoadTime          time.Duration `json:"load_time"`
    ParseErrors        int           `json:"parse_errors"`
    DirectoriesScanned int          `json:"directories_scanned"`
    LastLoadTime       time.Time     `json:"last_load_time"`
    SkillsByCategory   map[string]int `json:"skills_by_category"`
    SkillsByRisk       map[string]int `json:"skills_by_risk"`
    SkillsByAutonomy   map[string]int `json:"skills_by_autonomy"`
}

func (sm *SkillManager) GetMetrics() SkillsMetrics {
    skills := sm.ListSkills()
    
    metrics := SkillsMetrics{
        TotalSkills:        len(skills),
        LoadTime:          sm.loadTime,
        ParseErrors:        sm.parseErrors,
        DirectoriesScanned: len(sm.SkillDirs),
        LastLoadTime:       sm.lastLoadTime,
        SkillsByCategory:   make(map[string]int),
        SkillsByRisk:       make(map[string]int),
        SkillsByAutonomy:   make(map[string]int),
    }
    
    // Categorize skills
    for _, skill := range skills {
        // Category
        category := "other"
        if strings.Contains(skill.Name, "compliance") {
            category = "compliance"
        } else if strings.Contains(skill.Name, "security") {
            category = "security"
        } else if strings.Contains(skill.Name, "automation") || strings.Contains(skill.Name, "optimize") {
            category = "automation"
        }
        metrics.SkillsByCategory[category]++
        
        // Risk level
        metrics.SkillsByRisk[skill.RiskLevel]++
        
        // Autonomy
        metrics.SkillsByAutonomy[skill.Autonomy]++
    }
    
    return metrics
}
```

### 2. Performance Endpoint
```go
func (ss *SkillService) PerformanceHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    metrics := ss.manager.GetMetrics()
    
    performance := map[string]interface{}{
        "skills_metrics": metrics,
        "system_metrics": map[string]interface{}{
            "uptime":          time.Since(ss.startTime),
            "memory_usage":    getMemoryUsage(),
            "goroutines":      runtime.NumGoroutine(),
            "heap_size":       getHeapSize(),
        },
        "timestamp": time.Now().Format(time.RFC3339),
    }
    
    json.NewEncoder(w).Encode(performance)
}
```

## Troubleshooting Utilities

### 1. Health Check with Debug Info
```go
func (ss *SkillService) HealthHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    skills := ss.manager.ListSkills()
    metrics := ss.manager.GetMetrics()
    
    health := map[string]interface{}{
        "status": "healthy",
        "timestamp": time.Now().Format(time.RFC3339),
        "version": "1.0.0",
        "uptime": time.Since(ss.startTime).String(),
        "skills": map[string]interface{}{
            "total":     len(skills),
            "loaded":    len(skills),
            "errors":    metrics.ParseErrors,
            "load_time": metrics.LoadTime.String(),
        },
        "directories": map[string]interface{}{
            "scanned": metrics.DirectoriesScanned,
            "paths":   ss.manager.SkillDirs,
        },
        "session": map[string]interface{}{
            "id":   ss.sessionID,
            "start": ss.startTime,
        },
    }
    
    // Add warnings if there are issues
    warnings := []string{}
    
    if len(skills) == 0 {
        warnings = append(warnings, "No skills loaded")
    }
    
    if metrics.ParseErrors > 0 {
        warnings = append(warnings, fmt.Sprintf("%d parse errors", metrics.ParseErrors))
    }
    
    if metrics.DirectoriesScanned == 0 {
        warnings = append(warnings, "No skill directories found")
    }
    
    if len(warnings) > 0 {
        health["warnings"] = warnings
        health["status"] = "degraded"
    }
    
    json.NewEncoder(w).Encode(health)
}
```

### 2. Diagnostic Commands
```go
func (ss *SkillService) DiagnosticsHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    diagnostics := map[string]interface{}{
        "file_system": ss.getFileSystemDiagnostics(),
        "skills":     ss.getSkillsDiagnostics(),
        "system":      ss.getSystemDiagnostics(),
        "timestamp":   time.Now().Format(time.RFC3339),
    }
    
    json.NewEncoder(w).Encode(diagnostics)
}

func (ss *SkillService) getFileSystemDiagnostics() map[string]interface{} {
    diagnostics := map[string]interface{}{
        "current_directory": "",
        "skill_directories": []map[string]interface{}{},
        "permissions":      map[string]interface{}{},
    }
    
    // Current directory
    if wd, err := os.Getwd(); err == nil {
        diagnostics["current_directory"] = wd
    }
    
    // Check each skill directory
    for _, dir := range ss.manager.SkillDirs {
        dirInfo := map[string]interface{}{
            "path":     dir,
            "exists":   false,
            "readable": false,
            "writable": false,
            "skills":   0,
        }
        
        if stat, err := os.Stat(dir); err == nil {
            dirInfo["exists"] = true
            dirInfo["readable"] = stat.Mode().Perm()&0400 != 0
            dirInfo["writable"] = stat.Mode().Perm()&0200 != 0
            
            if stat.IsDir() {
                if entries, err := os.ReadDir(dir); err == nil {
                    dirInfo["skills"] = len(entries)
                }
            }
        }
        
        diagnostics["skill_directories"] = append(
            diagnostics["skill_directories"].([]map[string]interface{}),
            dirInfo,
        )
    }
    
    return diagnostics
}
```

## Log Analysis Tools

### 1. Log Parser
```go
type LogEntry struct {
    Timestamp time.Time `json:"timestamp"`
    Level     string    `json:"level"`
    Message   string    `json:"message"`
    Fields    map[string]interface{} `json:"fields,omitempty"`
}

type LogParser struct {
    entries []LogEntry
}

func NewLogParser() *LogParser {
    return &LogParser{
        entries: []LogEntry{},
    }
}

func (p *LogParser) ParseLogFile(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer file.Close()
    
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        line := scanner.Text()
        if entry := p.parseLogLine(line); entry != nil {
            p.entries = append(p.entries, *entry)
        }
    }
    
    return scanner.Err()
}

func (p *LogParser) parseLogLine(line string) *LogEntry {
    // Parse structured log format
    // Example: 2026/03/17 03:46:25 INFO Initializing skills service session_id=test-123
    parts := strings.SplitN(line, " ", 4)
    if len(parts) < 4 {
        return nil
    }
    
    timestamp, err := time.Parse("2006/01/02 15:04:05", parts[0]+" "+parts[1])
    if err != nil {
        return nil
    }
    
    level := parts[2]
    message := parts[3]
    
    return &LogEntry{
        Timestamp: timestamp,
        Level:     level,
        Message:   message,
    }
}
```

### 2. Log Analyzer
```go
type LogAnalyzer struct {
    parser *LogParser
}

func NewLogAnalyzer() *LogAnalyzer {
    return &LogAnalyzer{
        parser: NewLogParser(),
    }
}

func (a *LogAnalyzer) AnalyzeSkillsLoading() map[string]interface{} {
    analysis := map[string]interface{}{
        "total_entries":    len(a.parser.entries),
        "skill_events":     []LogEntry{},
        "error_events":     []LogEntry{},
        "timeline":         []map[string]interface{}{},
        "summary":          map[string]interface{}{},
    }
    
    skillEvents := []LogEntry{}
    errorEvents := []LogEntry{}
    
    for _, entry := range a.parser.entries {
        // Filter skill-related events
        if strings.Contains(entry.Message, "skill") || 
           strings.Contains(entry.Message, "directory") {
            skillEvents = append(skillEvents, entry)
        }
        
        // Filter error events
        if entry.Level == "ERROR" {
            errorEvents = append(errorEvents, entry)
        }
    }
    
    analysis["skill_events"] = skillEvents
    analysis["error_events"] = errorEvents
    
    // Create timeline
    timeline := []map[string]interface{}{}
    for _, entry := range skillEvents {
        timeline = append(timeline, map[string]interface{}{
            "timestamp": entry.Timestamp,
            "level":     entry.Level,
            "message":   entry.Message,
        })
    }
    
    analysis["timeline"] = timeline
    
    // Summary
    summary := map[string]interface{}{
        "skill_events_count": len(skillEvents),
        "error_events_count": len(errorEvents),
        "first_event":       time.Time{},
        "last_event":        time.Time{},
    }
    
    if len(skillEvents) > 0 {
        summary["first_event"] = skillEvents[0].Timestamp
        summary["last_event"] = skillEvents[len(skillEvents)-1].Timestamp
    }
    
    analysis["summary"] = summary
    
    return analysis
}
```

## Configuration

### 1. Environment Variables
```go
type LoggingConfig struct {
    Level        string `env:"LOG_LEVEL" envDefault:"INFO"`
    Format       string `env:"LOG_FORMAT" envDefault:"text"`
    Output       string `env:"LOG_OUTPUT" envDefault:"stdout"`
    File         string `env:"LOG_FILE"`
    MaxSize      int    `env:"LOG_MAX_SIZE" envDefault:"100"`
    MaxBackups   int    `env:"LOG_MAX_BACKUPS" envDefault:"3"`
    DebugEnabled bool   `env:"DEBUG_ENABLED" envDefault:"false"`
}

func LoadLoggingConfig() LoggingConfig {
    cfg := LoggingConfig{}
    
    if level := os.Getenv("LOG_LEVEL"); level != "" {
        cfg.Level = level
    }
    
    if debug := os.Getenv("DEBUG_ENABLED"); debug == "true" {
        cfg.DebugEnabled = true
        cfg.Level = "DEBUG"
    }
    
    return cfg
}
```

### 2. Logger Factory
```go
func CreateLogger(cfg LoggingConfig) *StructuredLogger {
    var output io.Writer
    
    switch cfg.Output {
    case "file":
        if cfg.File != "" {
            file, err := os.OpenFile(cfg.File, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
            if err != nil {
                log.Printf("Failed to open log file: %v", err)
                output = os.Stdout
            } else {
                output = file
            }
        } else {
            output = os.Stdout
        }
    case "stderr":
        output = os.Stderr
    default:
        output = os.Stdout
    }
    
    level := LogLevelInfo
    switch cfg.Level {
    case "DEBUG":
        level = LogLevelDebug
    case "WARN":
        level = LogLevelWarn
    case "ERROR":
        level = LogLevelError
    case "FATAL":
        level = LogLevelFatal
    }
    
    return NewStructuredLogger(level, output)
}
```

## Testing and Validation

### 1. Logging Tests
```go
func TestSkillsLogging(t *testing.T) {
    // Create logger with buffer for testing
    var buf bytes.Buffer
    logger := NewStructuredLogger(LogLevelDebug, &buf)
    
    // Create skill manager with test logger
    manager := NewSkillManager("/tmp", "test-session", logger)
    
    // Test directory scanning
    tempDir := t.TempDir()
    createTestSkill(t, tempDir, "test-skill", SKILL_YAML)
    
    err := manager.scanDirectory(tempDir)
    assert.NoError(t, err)
    
    // Check log output
    logs := buf.String()
    assert.Contains(t, logs, "Starting directory scan")
    assert.Contains(t, logs, "test-skill")
    assert.Contains(t, logs, "Skill loaded successfully")
}
```

### 2. Debug Endpoint Tests
```go
func TestDebugEndpoints(t *testing.T) {
    // Setup test service
    skillService := NewSkillService("../../../", "test-session")
    router := mux.NewRouter()
    
    // Register debug endpoints
    router.HandleFunc("/debug/skills", skillService.DebugSkillsHandler).Methods("GET")
    router.HandleFunc("/debug/skills/{name}", skillService.DebugSkillHandler).Methods("GET")
    
    server := httptest.NewServer(router)
    defer server.Close()
    
    // Test debug skills endpoint
    resp, err := http.Get(server.URL + "/debug/skills")
    assert.NoError(t, err)
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var debugInfo map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&debugInfo)
    assert.NoError(t, err)
    
    assert.Contains(t, debugInfo, "session_id")
    assert.Contains(t, debugInfo, "manager")
}
```

## Future Enhancements

### 1. Distributed Tracing
```go
type TracingLogger struct {
    logger    *StructuredLogger
    tracer    trace.Tracer
    span      trace.Span
}

func (tl *TracingLogger) Debug(msg string, fields ...interface{}) {
    tl.logger.Debug(msg, fields...)
    tl.span.AddEvent(msg, trace.WithAttributes(toAttributes(fields...)...))
}

func (tl *TracingLogger) Error(msg string, err error, fields ...interface{}) {
    tl.logger.Error(msg, err, fields...)
    tl.span.SetStatus(codes.Error, msg)
    tl.span.RecordError(err)
}
```

### 2. Log Aggregation
```go
type LogAggregator struct {
    buffer    chan LogEntry
    batchSize int
    flushTime time.Duration
    storage   LogStorage
}

func (la *LogAggregator) Start() {
    ticker := time.NewTicker(la.flushTime)
    batch := make([]LogEntry, 0, la.batchSize)
    
    for {
        select {
        case entry := <-la.buffer:
            batch = append(batch, entry)
            if len(batch) >= la.batchSize {
                la.flush(batch)
                batch = batch[:0]
            }
        case <-ticker.C:
            if len(batch) > 0 {
                la.flush(batch)
                batch = batch[:0]
            }
        }
    }
}
```

---

**Last Updated**: March 17, 2026  
**Author**: AI Assistant  
**Version**: 1.0
