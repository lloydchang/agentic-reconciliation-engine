# API Integration Fixes - Technical Documentation

## Overview

This document details the API integration fixes implemented to resolve connectivity issues between the frontend dashboard and the backend skills service. The fixes include port configuration, CORS handling, and API endpoint verification.

## Architecture Overview

### Service Communication
```
Frontend (React)     Backend (Go)        Skills Service
     │                    │                     │
     │ HTTP Requests      │                     │
     ├────────────────────►│                     │
     │                    │                     │
     │                    │ Skills API Calls    │
     │                    ├─────────────────────►│
     │                    │                     │
     │ JSON Response      │ Skills Data         │
     │◄───────────────────┤◄─────────────────────┤
```

### Port Configuration
- **Frontend**: Port 8080 (served by dashboard server)
- **Backend**: Port 8081 (Go API server)
- **Skills API**: `/api/skills` endpoint on backend

## Frontend API Configuration

### API Service Implementation
**File**: `core/ai/runtime/dashboard/frontend/src/services/api.ts`

#### Configuration
```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8081';

class ApiService {
  private baseURL = `${API_BASE_URL}/api`;

  // Skills Management
  async getSkills() {
    const response = await axios.get(`${this.baseURL}/skills`);
    return response.data;
  }

  async getSkill(id: string) {
    const response = await axios.get(`${this.baseURL}/skills/${id}`);
    return response.data;
  }

  // System APIs
  async getSystemStatus() {
    const response = await axios.get(`${this.baseURL}/system/status`);
    return response.data;
  }

  async getHealth() {
    const response = await axios.get(`${this.baseURL}/system/health`);
    return response.data;
  }
}
```

#### Environment Variables
```typescript
// Development
const API_BASE_URL = 'http://localhost:8081';

// Production (can be overridden)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8081';
```

### Frontend Integration Points

#### Dashboard Component
**File**: `core/ai/runtime/dashboard/frontend/src/components/Dashboard/Dashboard.tsx`

#### Skills Data Fetching
```typescript
const Dashboard: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        setLoading(true);
        const response = await apiService.getSkills();
        setSkills(response.skills || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch skills:', err);
        setError('Failed to load skills');
      } finally {
        setLoading(false);
      }
    };

    fetchSkills();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSkills, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <SkillsOverview skills={skills} loading={loading} error={error} />
      {/* Other dashboard components */}
    </div>
  );
};
```

#### Skills Overview Component
```typescript
const SkillsOverview: React.FC<SkillsOverviewProps> = ({ skills, loading, error }) => {
  if (loading) return <div>Loading skills...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="skills-overview">
      <div className="skills-count">
        <h3>{skills.length} Active Skills</h3>
      </div>
      <div className="skills-list">
        {skills.map(skill => (
          <SkillCard key={skill.name} skill={skill} />
        ))}
      </div>
    </div>
  );
};
```

## Backend API Implementation

### HTTP Server Configuration
**File**: `core/ai/runtime/agents/backend/main.go`

#### Server Setup
```go
func main() {
    // Initialize router
    r := mux.NewRouter()
    
    // Apply CORS middleware
    r.Use(corsMiddleware)
    
    // Register API routes
    registerAPIRoutes(r, skillService)
    
    // Start server
    log.Printf("Starting enhanced HTTP server on :8081")
    log.Fatal(http.ListenAndServe(":8081", r))
}
```

#### CORS Middleware
```go
func corsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
        
        if r.Method == "OPTIONS" {
            w.WriteHeader(http.StatusOK)
            return
        }
        
        next.ServeHTTP(w, r)
    })
}
```

### Skills API Routes

#### Route Registration
```go
func registerAPIRoutes(router *mux.Router, skillService *skills.SkillService) {
    // Skills endpoints
    router.HandleFunc("/api/skills", skillService.ListSkillsHandler).Methods("GET", "OPTIONS")
    router.HandleFunc("/api/skills/{name}", skillService.GetSkillHandler).Methods("GET", "OPTIONS")
    router.HandleFunc("/api/skills/{name}/execute", skillService.ExecuteSkillHandler).Methods("POST", "OPTIONS")
    router.HandleFunc("/api/skills/invocable", skillService.ListInvocableSkillsHandler).Methods("GET", "OPTIONS")
    router.HandleFunc("/api/skills/discover", skillService.DiscoverSkillsHandler).Methods("POST", "OPTIONS")
    
    // System endpoints
    router.HandleFunc("/api/system/status", systemStatusHandler).Methods("GET", "OPTIONS")
    router.HandleFunc("/api/system/health", healthCheckHandler).Methods("GET", "OPTIONS")
    router.HandleFunc("/api/system/metrics", metricsHandler).Methods("GET", "OPTIONS")
    
    // Health check endpoint
    router.HandleFunc("/health", healthCheckHandler).Methods("GET", "OPTIONS")
}
```

#### Skills List Handler
```go
func (ss *SkillService) ListSkillsHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    // Get skills from manager
    skills := ss.manager.ListSkills()
    
    // Build response
    response := SkillsResponse{
        Skills: skills,
        Count:  len(skills),
        Timestamp: time.Now().Format(time.RFC3339),
    }
    
    // Encode response
    if err := json.NewEncoder(w).Encode(response); err != nil {
        log.Printf("Failed to encode skills response: %v", err)
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }
    
    log.Printf("Returned %d skills via API", len(skills))
}
```

#### Response Structures
```go
type SkillsResponse struct {
    Skills    []*Skill `json:"skills"`
    Count     int      `json:"count"`
    Timestamp string   `json:"timestamp"`
}

type SkillResponse struct {
    Skill     *Skill   `json:"skill"`
    Timestamp string   `json:"timestamp"`
}

type ErrorResponse struct {
    Error     string   `json:"error"`
    Message   string   `json:"message"`
    Timestamp string   `json:"timestamp"`
}
```

## Port Conflict Resolution

### Problem Identification
```bash
# Check port usage
lsof -i :8081

# Sample output showing conflict
COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
main     86498 lloyd  12u  IPv6 0x123456789abcdef0      0t0  TCP *:8081 (LISTEN)
```

### Resolution Process
```bash
# Kill conflicting process
kill -9 86498

# Verify port is free
lsof -i :8081
# Should return no output

# Start backend server
cd core/ai/runtime/agents/backend
go run main.go
```

### Port Configuration Validation
```go
// Verify port is available
func isPortAvailable(port int) bool {
    addr := fmt.Sprintf(":%d", port)
    listener, err := net.Listen("tcp", addr)
    if err != nil {
        return false
    }
    listener.Close()
    return true
}

// Main function with port check
func main() {
    port := 8081
    if !isPortAvailable(port) {
        log.Fatalf("Port %d is already in use", port)
    }
    
    // Continue with server startup
    log.Printf("Starting server on port %d", port)
}
```

## API Testing and Verification

### Manual Testing
```bash
# Test skills endpoint
curl -v http://localhost:8081/api/skills

# Expected response
{
  "skills": [...],
  "count": 5,
  "timestamp": "2026-03-17T03:46:25Z"
}

# Test health endpoint
curl -v http://localhost:8081/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2026-03-17T03:46:25Z"
}

# Test CORS preflight
curl -X OPTIONS -H "Origin: http://localhost:8080" \
     -H "Access-Control-Request-Method: GET" \
     http://localhost:8081/api/skills

# Expected headers
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Automated Testing
```go
func TestSkillsAPI(t *testing.T) {
    // Setup test server
    skillService := NewSkillService("../../../", "test-session")
    router := mux.NewRouter()
    skillService.RegisterRoutes(router)
    
    server := httptest.NewServer(router)
    defer server.Close()
    
    // Test GET /api/skills
    resp, err := http.Get(server.URL + "/api/skills")
    assert.NoError(t, err)
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var response SkillsResponse
    err = json.NewDecoder(resp.Body).Decode(&response)
    assert.NoError(t, err)
    assert.Greater(t, response.Count, 0)
    
    // Test CORS headers
    assert.Equal(t, "*", resp.Header.Get("Access-Control-Allow-Origin"))
}

func TestHealthEndpoint(t *testing.T) {
    router := mux.NewRouter()
    router.HandleFunc("/health", healthCheckHandler).Methods("GET")
    
    server := httptest.NewServer(router)
    defer server.Close()
    
    resp, err := http.Get(server.URL + "/health")
    assert.NoError(t, err)
    assert.Equal(t, http.StatusOK, resp.StatusCode)
    
    var health map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&health)
    assert.NoError(t, err)
    assert.Equal(t, "healthy", health["status"])
}
```

## Error Handling and Resilience

### Request Timeout Handling
```go
func (ss *SkillService) ListSkillsHandler(w http.ResponseWriter, r *http.Request) {
    // Set timeout context
    ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
    defer cancel()
    
    // Process request
    select {
    case <-ctx.Done():
        http.Error(w, "Request timeout", http.StatusRequestTimeout)
        return
    default:
        // Continue processing
        skills := ss.manager.ListSkills()
        // ... rest of handler
    }
}
```

### Retry Logic in Frontend
```typescript
class ApiService {
  private async retryRequest<T>(
    request: () => Promise<T>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: Error;
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await request();
      } catch (error) {
        lastError = error as Error;
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay));
          delay *= 2; // Exponential backoff
        }
      }
    }
    
    throw lastError!;
  }
  
  async getSkills(): Promise<SkillsResponse> {
    return this.retryRequest(async () => {
      const response = await axios.get(`${this.baseURL}/skills`);
      return response.data;
    });
  }
}
```

### Circuit Breaker Pattern
```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  
  constructor(
    private threshold = 5,
    private timeout = 60000
  ) {}
  
  async execute<T>(request: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    
    try {
      const result = await request();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }
  
  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}
```

## Monitoring and Observability

### Request Metrics
```go
type RequestMetrics struct {
    TotalRequests    int64
    SuccessfulReqs   int64
    FailedReqs       int64
    AvgResponseTime  time.Duration
    LastRequest      time.Time
}

var metrics = &RequestMetrics{}

func metricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        // Wrap response writer to capture status
        wrapped := &responseWriter{ResponseWriter: w}
        
        // Process request
        next.ServeHTTP(wrapped, r)
        
        // Update metrics
        duration := time.Since(start)
        metrics.TotalRequests++
        metrics.LastRequest = time.Now()
        
        if wrapped.statusCode < 400 {
            metrics.SuccessfulReqs++
        } else {
            metrics.FailedReqs++
        }
        
        // Update average response time
        metrics.AvgResponseTime = time.Duration(
            (int64(metrics.AvgResponseTime) + int64(duration)) / 2,
        )
    })
}
```

### Health Check Implementation
```go
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    health := map[string]interface{}{
        "status": "healthy",
        "timestamp": time.Now().Format(time.RFC3339),
        "version": "1.0.0",
        "uptime": time.Since(startTime).String(),
        "metrics": map[string]interface{}{
            "total_requests": metrics.TotalRequests,
            "success_rate": float64(metrics.SuccessfulReqs) / float64(metrics.TotalRequests) * 100,
            "avg_response_time": metrics.AvgResponseTime.String(),
        },
    }
    
    json.NewEncoder(w).Encode(health)
}
```

## Security Considerations

### API Security
```go
func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Skip auth for health checks
        if r.URL.Path == "/health" {
            next.ServeHTTP(w, r)
            return
        }
        
        // Validate API key
        apiKey := r.Header.Get("X-API-Key")
        if apiKey != os.Getenv("API_KEY") {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        
        next.ServeHTTP(w, r)
    })
}
```

### Rate Limiting
```go
type RateLimiter struct {
    requests map[string][]time.Time
    limit    int
    window   time.Duration
    mutex    sync.Mutex
}

func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
    return &RateLimiter{
        requests: make(map[string][]time.Time),
        limit:    limit,
        window:   window,
    }
}

func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        clientIP := r.RemoteAddr
        
        rl.mutex.Lock()
        defer rl.mutex.Unlock()
        
        now := time.Now()
        requests := rl.requests[clientIP]
        
        // Remove old requests outside window
        validRequests := make([]time.Time, 0)
        for _, reqTime := range requests {
            if now.Sub(reqTime) < rl.window {
                validRequests = append(validRequests, reqTime)
            }
        }
        
        // Check limit
        if len(validRequests) >= rl.limit {
            http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
            return
        }
        
        // Add current request
        validRequests = append(validRequests, now)
        rl.requests[clientIP] = validRequests
        
        next.ServeHTTP(w, r)
    })
}
```

## Deployment Configuration

### Docker Configuration
```dockerfile
# Backend Dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .
COPY --from=builder /app/core/ai/skills ./core/ai/skills

EXPOSE 8081
CMD ["./main"]
```

### Kubernetes Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: skills-api
spec:
  selector:
    app: skills-api
  ports:
  - port: 8081
    targetPort: 8081
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: skills-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: skills-api
  template:
    metadata:
      labels:
        app: skills-api
    spec:
      containers:
      - name: skills-api
        image: skills-api:latest
        ports:
        - containerPort: 8081
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: api-key
```

## Troubleshooting Guide

### Common Issues

#### 1. Connection Refused
**Symptoms**: Frontend cannot connect to backend
**Solutions**:
```bash
# Check if backend is running
curl http://localhost:8081/health

# Check port conflicts
lsof -i :8081

# Restart backend
cd core/ai/runtime/agents/backend
go run main.go
```

#### 2. CORS Errors
**Symptoms**: Browser console shows CORS errors
**Solutions**:
```bash
# Test CORS preflight
curl -X OPTIONS -H "Origin: http://localhost:8080" \
     http://localhost:8081/api/skills

# Check CORS headers
curl -I http://localhost:8081/api/skills
```

#### 3. API Returns 404
**Symptoms**: API endpoints return 404 errors
**Solutions**:
```bash
# Check registered routes
curl http://localhost:8081/api/skills

# Verify route registration
grep -r "HandleFunc" core/ai/runtime/agents/backend/main.go
```

### Debug Commands
```bash
# Enable debug logging
export DEBUG=true
go run main.go

# Test all endpoints
for endpoint in /health /api/skills /api/system/status; do
    echo "Testing $endpoint"
    curl -v http://localhost:8081$endpoint
    echo
done

# Monitor API requests
tail -f /var/log/skills-api.log
```

---

**Last Updated**: March 17, 2026  
**Author**: AI Assistant  
**Version**: 1.0
