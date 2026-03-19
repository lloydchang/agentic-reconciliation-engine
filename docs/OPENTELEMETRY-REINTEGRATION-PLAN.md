# OpenTelemetry Reintegration Plan

## Overview

This document outlines the plan for reintegrating OpenTelemetry observability into the skills system backend. The original OpenTelemetry code was commented out during the "0 Active Skills" error fix to resolve compilation issues. This plan provides a structured approach to properly re-enable observability features.

## Current State Analysis

### What Was Disabled
- **OpenTelemetry Imports**: Commented out in `main.go`
- **Tracing Initialization**: Commented out tracer setup
- **Observability Package**: Commented out custom observability code
- **Span Creation**: Commented out tracing spans in API handlers

### Why It Was Disabled
- Missing OpenTelemetry packages in Go module
- Compilation errors preventing backend startup
- Need to prioritize fixing "0 Active Skills" error

### What Needs to Be Re-enabled
- Distributed tracing for API requests
- Metrics collection and export
- Proper span context propagation
- Integration with observability backend (Jaeger/Zipkin)

## Implementation Plan

### Phase 1: Package Installation and Dependencies

#### Required OpenTelemetry Packages
```bash
# Core OpenTelemetry packages
go get go.opentelemetry.io/otel@v1.21.0
go get go.opentelemetry.io/otel/trace@v1.21.0

# Exporters
go get go.opentelemetry.io/otel/exporters/jaeger@v1.17.0
go get go.opentelemetry.io/otel/exporters/zipkin@v1.17.0
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp@v1.21.0

# SDK and resources
go get go.opentelemetry.io/otel/sdk@v1.21.0
go get go.opentelemetry.io/otel/sdk/resource@v1.21.0
go get go.opentelemetry.io/otel/sdk/metric@v1.21.0

# Semantic conventions
go get go.opentelemetry.io/otel/semconv/v1.17.0
go get go.opentelemetry.io/otel/semconv/v1.21.0

# Prometheus metrics bridge
go get go.opentelemetry.io/otel/exporters/prometheus@v0.42.0
```

#### Updated go.mod Dependencies
```go
// go.mod additions
require (
    go.opentelemetry.io/otel v1.21.0
    go.opentelemetry.io/otel/trace v1.21.0
    go.opentelemetry.io/otel/exporters/jaeger v1.17.0
    go.opentelemetry.io/otel/exporters/zipkin v1.17.0
    go.opentelemetry.io/otel/sdk v1.21.0
    go.opentelemetry.io/otel/sdk/resource v1.21.0
    go.opentelemetry.io/otel/sdk/metric v1.21.0
    go.opentelemetry.io/otel/semconv/v1.17.0
    go.opentelemetry.io/otel/exporters/prometheus v0.42.0
)
```

### Phase 2: Observability Package Recreation

#### New Observability Package Structure
```
core/ai/runtime/agents/backend/observability/
├── tracing.go          # Tracing configuration and setup
├── metrics.go          # Metrics configuration and setup
├── resources.go        # Resource detection and attributes
├── exporters.go        # Exporter configurations
└── middleware.go       # HTTP middleware for tracing
```

#### Tracing Implementation
```go
// observability/tracing.go
package observability

import (
    "context"
    "fmt"
    "os"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
    "go.opentelemetry.io/otel/exporters/zipkin"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
    "go.opentelemetry.io/otel/trace"
)

type TracingConfig struct {
    ServiceName    string
    ServiceVersion string
    Environment    string
    ExporterType   string // "jaeger", "zipkin", "otlp"
    Endpoint       string
    SampleRate     float64
}

func InitTracer(config TracingConfig) (*trace.TracerProvider, error) {
    // Create resource
    res, err := newResource(config)
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // Create exporter based on type
    exporter, err := createTraceExporter(config)
    if err != nil {
        return nil, fmt.Errorf("failed to create exporter: %w", err)
    }

    // Create batch span processor
    batchProcessor := trace.NewBatchSpanProcessor(exporter)

    // Create tracer provider
    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(res),
        trace.WithSampler(trace.TraceIDRatioBased(config.SampleRate)),
    )

    // Register globally
    otel.SetTracerProvider(tp)

    return tp, nil
}

func newResource(config TracingConfig) (*resource.Resource, error) {
    return resource.NewWithAttributes(
        semconv.SchemaURL,
        semconv.ServiceNameKey.String(config.ServiceName),
        semconv.ServiceVersionKey.String(config.ServiceVersion),
        semconv.DeploymentEnvironmentKey.String(config.Environment),
    )
}

func createTraceExporter(config TracingConfig) (trace.SpanExporter, error) {
    switch config.ExporterType {
    case "jaeger":
        return jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(config.Endpoint)))
    case "zipkin":
        return zipkin.New(config.Endpoint)
    case "otlp":
        return otlptracehttp.New(context.Background(), otlptracehttp.WithEndpoint(config.Endpoint))
    default:
        return nil, fmt.Errorf("unsupported exporter type: %s", config.ExporterType)
    }
}

func GetTracer(name string) trace.Tracer {
    return otel.Tracer(name)
}
```

#### Metrics Implementation
```go
// observability/metrics.go
package observability

import (
    "context"
    "fmt"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/prometheus"
    "go.opentelemetry.io/otel/metric"
    "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

type MetricsConfig struct {
    ServiceName    string
    ServiceVersion string
    Environment    string
    Port          int
}

type Metrics struct {
    Meter                metric.Meter
    SkillsLoadedGauge    metric.Float64Gauge
    APIDurationHistogram metric.Float64Histogram
    APIErrorCounter      metric.Int64Counter
    ParseErrorCounter    metric.Int64Counter
}

func InitMetrics(config MetricsConfig) (*metric.MeterProvider, *Metrics, error) {
    // Create resource
    res, err := resource.NewWithAttributes(
        semconv.SchemaURL,
        semconv.ServiceNameKey.String(config.ServiceName),
        semconv.ServiceVersionKey.String(config.ServiceVersion),
        semconv.DeploymentEnvironmentKey.String(config.Environment),
    )
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // Create Prometheus exporter
    exporter, err := prometheus.New(prometheus.WithAddress(fmt.Sprintf(":%d", config.Port)))
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create Prometheus exporter: %w", err)
    }

    // Create meter provider
    provider := metric.NewMeterProvider(
        metric.WithReader(exporter),
        metric.WithResource(res),
    )

    // Set globally
    otel.SetMeterProvider(provider)

    // Create metrics
    meter := provider.Meter(config.ServiceName)

    skillsLoadedGauge, err := meter.Float64Gauge("skills_loaded_count",
        metric.WithDescription("Number of skills currently loaded"))
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create skills loaded gauge: %w", err)
    }

    apiDurationHistogram, err := meter.Float64Histogram("api_duration_seconds",
        metric.WithDescription("API request duration in seconds"))
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create API duration histogram: %w", err)
    }

    apiErrorCounter, err := meter.Int64Counter("api_errors_total",
        metric.WithDescription("Total number of API errors"))
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create API error counter: %w", err)
    }

    parseErrorCounter, err := meter.Int64Counter("parse_errors_total",
        metric.WithDescription("Total number of skill parsing errors"))
    if err != nil {
        return nil, nil, fmt.Errorf("failed to create parse error counter: %w", err)
    }

    metrics := &Metrics{
        Meter:                meter,
        SkillsLoadedGauge:    skillsLoadedGauge,
        APIDurationHistogram: apiDurationHistogram,
        APIErrorCounter:      apiErrorCounter,
        ParseErrorCounter:    parseErrorCounter,
    }

    return provider, metrics, nil
}
```

#### HTTP Middleware
```go
// observability/middleware.go
package observability

import (
    "net/http"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

// TracingMiddleware adds OpenTelemetry tracing to HTTP requests
func TracingMiddleware(tracerName string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            tracer := otel.Tracer(tracerName)
            
            ctx, span := tracer.Start(r.Context(), r.Method+" "+r.URL.Path,
                trace.WithAttributes(
                    semconv.HTTPMethodKey.String(r.Method),
                    semconv.HTTPURLKey.String(r.URL.String()),
                    semconv.HTTPUserAgentKey.String(r.UserAgent()),
                ),
            )
            defer span.End()

            // Update request context
            r = r.WithContext(ctx)

            // Call next handler
            next.ServeHTTP(w, r)
        })
    }
}

// MetricsMiddleware adds OpenTelemetry metrics to HTTP requests
func MetricsMiddleware(metrics *Metrics) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()

            // Wrap response writer to capture status code
            wrapped := &responseWriter{ResponseWriter: w, statusCode: 200}

            // Call next handler
            next.ServeHTTP(wrapped, r)

            // Record metrics
            duration := time.Since(start).Seconds()
            metrics.APIDurationHistogram.Record(r.Context(), duration)

            if wrapped.statusCode >= 400 {
                metrics.APIErrorCounter.Add(r.Context(), 1)
            }

            // Add span attributes
            span := trace.SpanFromContext(r.Context())
            span.SetAttributes(
                semconv.HTTPStatusCodeKey.Int(wrapped.statusCode),
            )
        })
    }
}

type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}
```

### Phase 3: Backend Integration

#### Updated Main Function
```go
// main.go - Updated with OpenTelemetry
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "time"

    "github.com/gorilla/mux"
    "github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/agents/backend/observability"
    "github.com/lloydchang/agentic-reconciliation-engine/core/ai/runtime/agents/backend/skills"
    "go.opentelemetry.io/otel"
)

func main() {
    // Load configuration
    config := loadConfig()

    // Initialize OpenTelemetry
    tp, err := initObservability(config)
    if err != nil {
        log.Fatalf("Failed to initialize observability: %v", err)
    }
    defer tp.Shutdown(context.Background())

    // Initialize skills service
    skillService := skills.NewSkillService("../../../../../", "session-"+time.Now().Format("20060102150405"))
    log.Printf("Skills service initialized with %d skills", len(skillService.GetManager().ListSkills()))

    // Setup router with middleware
    r := mux.NewRouter()
    
    // Add observability middleware
    r.Use(observability.TracingMiddleware("skills-backend"))
    r.Use(observability.MetricsMiddleware(metrics))
    r.Use(corsMiddleware)

    // Register routes
    registerAPIRoutes(r, skillService)

    // Start server
    log.Printf("Starting enhanced HTTP server on :8081")
    log.Fatal(http.ListenAndServe(":8081", r))
}

func initObservability(config Config) (*trace.TracerProvider, error) {
    // Initialize tracing
    tracingConfig := observability.TracingConfig{
        ServiceName:    "skills-backend",
        ServiceVersion: "1.0.0",
        Environment:    config.Environment,
        ExporterType:   config.TracingExporter,
        Endpoint:       config.TracingEndpoint,
        SampleRate:     config.TracingSampleRate,
    }

    tp, err := observability.InitTracer(tracingConfig)
    if err != nil {
        return nil, fmt.Errorf("failed to initialize tracing: %w", err)
    }

    // Initialize metrics
    metricsConfig := observability.MetricsConfig{
        ServiceName:    "skills-backend",
        ServiceVersion: "1.0.0",
        Environment:    config.Environment,
        Port:          config.MetricsPort,
    }

    _, metrics, err := observability.InitMetrics(metricsConfig)
    if err != nil {
        return nil, fmt.Errorf("failed to initialize metrics: %w", err)
    }

    return tp, nil
}

type Config struct {
    Environment        string
    TracingExporter    string
    TracingEndpoint    string
    TracingSampleRate  float64
    MetricsPort        int
}

func loadConfig() Config {
    config := Config{
        Environment:       getEnv("ENVIRONMENT", "development"),
        TracingExporter:   getEnv("TRACING_EXPORTER", "jaeger"),
        TracingEndpoint:   getEnv("TRACING_ENDPOINT", "http://localhost:14268/api/traces"),
        TracingSampleRate:  getFloatEnv("TRACING_SAMPLE_RATE", 1.0),
        MetricsPort:       getIntEnv("METRICS_PORT", 9090),
    }

    return config
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getFloatEnv(key string, defaultValue float64) float64 {
    if value := os.Getenv(key); value != "" {
        if f, err := strconv.ParseFloat(value, 64); err == nil {
            return f
        }
    }
    return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
    if value := os.Getenv(key); value != "" {
        if i, err := strconv.Atoi(value); err == nil {
            return i
        }
    }
    return defaultValue
}
```

#### Enhanced Skills Service with Tracing
```go
// skills/service.go - Updated with tracing
package skills

import (
    "context"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

func (ss *SkillService) ListSkillsHandler(w http.ResponseWriter, r *http.Request) {
    tracer := otel.Tracer("skills-service")
    ctx, span := tracer.Start(r.Context(), "ListSkills")
    defer span.End()

    w.Header().Set("Content-Type", "application/json")

    // Add span attributes
    span.SetAttributes(
        attribute.String("service", "skills"),
        attribute.String("operation", "list"),
    )

    // Get skills with tracing
    skills := ss.manager.ListSkillsWithTracing(ctx)

    response := map[string]interface{}{
        "skills": skills,
        "count":  len(skills),
    }

    if err := json.NewEncoder(w).Encode(response); err != nil {
        span.SetAttributes(
            attribute.String("error", err.Error()),
            attribute.Bool("success", false),
        )
        log.Printf("Failed to encode skills response: %v", err)
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }

    span.SetAttributes(
        attribute.Int("skills_count", len(skills)),
        attribute.Bool("success", true),
    )

    log.Printf("Returned %d skills via API", len(skills))
}

func (sm *SkillManager) ListSkillsWithTracing(ctx context.Context) []*Skill {
    tracer := otel.Tracer("skill-manager")
    _, span := tracer.Start(ctx, "ListSkills")
    defer span.End()

    skills := sm.ListSkills()

    span.SetAttributes(
        attribute.Int("skills_loaded", len(skills)),
        attribute.String("session_id", sm.SessionID),
    )

    return skills
}
```

### Phase 4: Configuration Management

#### Environment Configuration
```bash
# .env file for development
ENVIRONMENT=development
TRACING_EXPORTER=jaeger
TRACING_ENDPOINT=http://localhost:14268/api/traces
TRACING_SAMPLE_RATE=1.0
METRICS_PORT=9090

# Production environment
ENVIRONMENT=production
TRACING_EXPORTER=otlp
TRACING_ENDPOINT=http://otel-collector:4318/v1/traces
TRACING_SAMPLE_RATE=0.1
METRICS_PORT=9090
```

#### Docker Compose for Observability Stack
```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Jaeger collector
      - "14250:14250"  # gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP http receiver
      - "8888:8888"   # Prometheus metrics
      - "8889:8889"   # Prometheus exporter

volumes:
  prometheus_data:
  grafana_data:
```

#### OpenTelemetry Collector Configuration
```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

  memory_limiter:
    limit_mib: 512

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"

  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus, logging]
```

### Phase 5: Testing and Validation

#### Unit Tests for Tracing
```go
// observability/tracing_test.go
package observability

import (
    "context"
    "testing"
    "time"

    "go.opentelemetry.io/otel/sdk/trace/tracetest"
    "go.opentelemetry.io/otel/trace"
)

func TestTracerInitialization(t *testing.T) {
    config := TracingConfig{
        ServiceName:    "test-service",
        ServiceVersion: "1.0.0",
        Environment:    "test",
        ExporterType:   "jaeger",
        Endpoint:       "http://localhost:14268/api/traces",
        SampleRate:     1.0,
    }

    tp, err := InitTracer(config)
    if err != nil {
        t.Fatalf("Failed to initialize tracer: %v", err)
    }
    defer tp.Shutdown(context.Background())

    tracer := tp.Tracer("test-tracer")
    _, span := tracer.Start(context.Background(), "test-span")
    span.End()

    // Allow some time for span to be processed
    time.Sleep(100 * time.Millisecond)
}

func TestMetricsInitialization(t *testing.T) {
    config := MetricsConfig{
        ServiceName:    "test-service",
        ServiceVersion: "1.0.0",
        Environment:    "test",
        Port:          9090,
    }

    provider, metrics, err := InitMetrics(config)
    if err != nil {
        t.Fatalf("Failed to initialize metrics: %v", err)
    }
    defer provider.Shutdown(context.Background())

    if metrics == nil {
        t.Fatal("Metrics object is nil")
    }

    // Test metric recording
    metrics.SkillsLoadedGauge.Record(context.Background(), 5.0)
    metrics.APIErrorCounter.Add(context.Background(), 1)
}
```

#### Integration Tests
```go
// integration_test.go
package main

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestTracingIntegration(t *testing.T) {
    // Setup test server with tracing
    skillService := skills.NewSkillService("../../../", "test-session")
    router := setupRouterWithTracing(skillService)

    server := httptest.NewServer(router)
    defer server.Close()

    // Make request
    resp, err := http.Get(server.URL + "/api/skills")
    if err != nil {
        t.Fatalf("Failed to make request: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("Expected status 200, got %d", resp.StatusCode)
    }

    // Verify tracing headers are present (if using propagation)
    // This would require checking with the actual tracing backend
}
```

## Implementation Timeline

### Week 1: Foundation
- **Day 1-2**: Install OpenTelemetry packages and update dependencies
- **Day 3-4**: Create observability package structure
- **Day 5**: Basic tracing implementation and testing

### Week 2: Integration
- **Day 1-2**: Integrate tracing into main application
- **Day 3-4**: Add metrics implementation
- **Day 5**: Update skills service with tracing

### Week 3: Configuration and Deployment
- **Day 1-2**: Set up observability infrastructure (Jaeger, Prometheus)
- **Day 3-4**: Configuration management and environment setup
- **Day 5**: Integration testing and validation

### Week 4: Testing and Documentation
- **Day 1-2**: Comprehensive testing (unit, integration, load)
- **Day 3-4**: Performance testing and optimization
- **Day 5**: Documentation and deployment preparation

## Success Criteria

### Technical Success
- [ ] All OpenTelemetry packages successfully installed
- [ ] Tracing spans created for all API endpoints
- [ ] Metrics collected and exported to Prometheus
- [ ] Jaeger receiving and displaying traces
- [ ] No performance degradation (>5% impact)

### Operational Success
- [ ] Observability stack running in development
- [ ] Dashboards created in Grafana
- [ ] Alert rules configured
- [ ] Documentation completed
- [ ] Team trained on new observability tools

### Business Success
- [ ] Improved debugging capabilities
- [ ] Faster issue resolution
- [ ] Better system visibility
- [ ] Enhanced user experience

## Risk Mitigation

### Technical Risks
- **Package Conflicts**: Use specific versions and test in isolated environment
- **Performance Impact**: Implement sampling and monitor performance closely
- **Configuration Complexity**: Use environment variables and provide defaults

### Operational Risks
- **Infrastructure Overhead**: Start with minimal setup and scale as needed
- **Team Adoption**: Provide training and clear documentation
- **Maintenance Burden**: Automate deployment and monitoring of observability stack

## Monitoring the Reintegration

### Key Metrics to Track
- **Tracing Overhead**: Request latency with/without tracing
- **Metrics Storage**: Prometheus storage usage
- **Jaeger Performance**: Trace ingestion and query performance
- **System Resources**: CPU and memory usage of observability components

### Success Indicators
- **Trace Coverage**: >90% of API endpoints traced
- **Metrics Availability**: 99.9% uptime for metrics endpoint
- **Dashboard Usage**: Regular team engagement with observability tools
- **Issue Resolution**: Reduced mean time to resolution (MTTR)

---

**Implementation Start**: March 24, 2026  
**Target Completion**: April 21, 2026  
**Owner**: Backend Team  
**Status**: Ready for Implementation
