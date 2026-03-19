# Dashboard Quick Reference Guide

## Quick Start

### 1. Start All Services
```bash
# Terminal 1: Start Backend
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/ai/runtime/dashboard
DATABASE_URL="/tmp/dashboard.db" ./main

# Terminal 2: Start Agent Simulator (for real-time data)
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/ai/runtime/dashboard
./bin/agent-simulator

# Terminal 3: Start Frontend
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine/core/ai/runtime/dashboard/frontend
python3 -m http.server 8080
```

### 2. Access Dashboard
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8081
- **Health Check**: http://localhost:8081/health

### 3. Verify Real-Time Data
```bash
# Check system metrics
curl -s http://localhost:8081/api/v1/system/metrics | jq

# Expected output:
{
  "agentMetrics": {
    "total": 3,
    "running": 1,
    "idle": 1,
    "errored": 1,
    "stopped": 0
  },
  "skillMetrics": {
    "total": 5,
    "executions24h": 12,
    "successRate": 91.7,
    "avgDuration": 2.3
  }
}
```

## Key Files

### Backend Configuration
- **Main Server**: `core/ai/runtime/dashboard/cmd/server/main.go`
- **Database**: `core/ai/runtime/dashboard/internal/database/database.go`
- **System Service**: `core/ai/runtime/dashboard/internal/services/system_service.go`
- **API Handler**: `core/ai/runtime/dashboard/internal/api/handler.go`

### Frontend Configuration
- **API Service**: `core/ai/runtime/dashboard/frontend/src/services/api.ts`
- **Dashboard Component**: `core/ai/runtime/dashboard/frontend/src/components/Dashboard/`

### Real-Time Data
- **Agent Simulator**: `core/ai/runtime/dashboard/cmd/agent-simulator/main.go`
- **Database File**: `/tmp/dashboard.db`

## Common Commands

### Database Operations
```bash
# Check agent status distribution
sqlite3 /tmp/dashboard.db "SELECT status, COUNT(*) FROM agents GROUP BY status;"

# Check recent skill executions
sqlite3 /tmp/dashboard.db "SELECT skill_name, status, started_at FROM agent_executions ORDER BY started_at DESC LIMIT 10;"

# Add sample data
sqlite3 /tmp/dashboard.db < /tmp/insert_simple.sql
```

### Service Management
```bash
# Kill processes on ports
lsof -ti:8081 | xargs kill -9  # Backend
lsof -ti:8080 | xargs kill -9  # Frontend

# Rebuild backend
cd core/ai/runtime/dashboard && go build -o main ./cmd/server

# Rebuild simulator
cd core/ai/runtime/dashboard && go build -o bin/agent-simulator ./cmd/agent-simulator
```

### Testing
```bash
# Test API endpoints
curl -s http://localhost:8081/api/v1/agents
curl -s http://localhost:8081/api/v1/skills
curl -s http://localhost:8081/api/v1/system/status
curl -s http://localhost:8081/health

# Test frontend
open http://localhost:8080
```

## Troubleshooting

### Issue: "0 Total Agents"
**Solution**: 
1. Check backend is running: `lsof -i:8081`
2. Check database connection: `sqlite3 /tmp/dashboard.db "SELECT COUNT(*) FROM agents;"`
3. Restart backend with correct DATABASE_URL

### Issue: Frontend Not Loading
**Solution**:
1. Check frontend is running: `lsof -i:8080`
2. Check API configuration in `frontend/src/services/api.ts`
3. Verify backend API responds: `curl -s http://localhost:8081/api/v1/system/metrics`

### Issue: No Real-Time Updates
**Solution**:
1. Start agent simulator: `./bin/agent-simulator`
2. Check database updates: `sqlite3 /tmp/dashboard.db "SELECT status, COUNT(*) FROM agents GROUP BY status;"`
3. Verify simulator logs for activity

## Environment Variables

### Backend
```bash
DATABASE_URL="/tmp/dashboard.db"          # SQLite database path
PORT="8081"                              # Backend port
RAG_ENABLED="false"                       # RAG service disabled
GIN_MODE="debug"                          # Gin framework mode
```

### Frontend
```bash
REACT_APP_API_URL="http://localhost:8081" # Backend API URL
PORT="8080"                               # Frontend port
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (Go/Gin)      │◄──►│   (SQLite)      │
│   Port: 8080    │    │   Port: 8081    │    │   /tmp/db       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌─────────────────┐
                       │ Agent Simulator │
                       │ (Real-time data)│
                       └─────────────────┘
```

## Performance Metrics

### Current Status
- **Response Time**: < 100ms
- **Update Frequency**: 5-60 seconds
- **Data Freshness**: Real-time
- **Memory Usage**: < 100MB
- **CPU Usage**: < 5%

### Monitoring
```bash
# Check system resources
top -p $(lsof -ti:8081)  # Backend
top -p $(lsof -ti:8080)  # Frontend

# Check database size
ls -lh /tmp/dashboard.db

# Monitor API calls
tail -f /var/log/system.log | grep "dashboard"
```

---

**For detailed documentation**, see: `docs/DASHBOARD-REALTIME-DATA-SYSTEM.md`
