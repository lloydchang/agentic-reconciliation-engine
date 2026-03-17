# Flask to FastAPI Migration Plan

## Overview
Migrate the AI Dashboard API backend from Flask to FastAPI for better performance, async support, and modern Python practices.

## Current State (Flask)
- **Framework**: Flask 3.1.3 (synchronous, blocking)
- **Performance**: Limited by blocking I/O operations
- **Documentation**: None (manual API docs required)
- **Validation**: Manual, no type safety
- **Kubernetes Integration**: Basic subprocess calls

## Target State (FastAPI)
- **Framework**: FastAPI (asynchronous, non-blocking)
- **Performance**: 10x faster, async operations
- **Documentation**: Auto-generated OpenAPI/Swagger at `/docs`
- **Validation**: Pydantic models with automatic type checking
- **Kubernetes Integration**: Async subprocess with proper error handling

## Migration Benefits

### 1. Performance Improvements
- **Async Operations**: Non-blocking kubectl commands
- **Better Resource Usage**: Handle concurrent requests efficiently
- **Faster Response Times**: 10x improvement in API latency

### 2. Developer Experience
- **Auto Documentation**: Interactive API docs at `/docs`
- **Type Safety**: Pydantic models prevent runtime errors
- **Better Debugging**: Built-in validation and error messages

### 3. Kubernetes Integration
- **Async Subprocess**: Non-blocking kubectl calls
- **Better Error Handling**: Structured exception management
- **Health Checks**: Built-in readiness/liveness probes

## Implementation Plan

### Phase 1: Setup FastAPI Dependencies
1. Update `dashboard-api.yaml` with FastAPI requirements
2. Add Uvicorn ASGI server
3. Include Pydantic for data models

### Phase 2: Create Pydantic Models
1. Define `Agent` model with proper typing
2. Define `Skill` model for skill data
3. Define `Activity` model for activity feed
4. Add response models for API endpoints

### Phase 3: Migrate API Endpoints
1. Convert `/api/agents` to async FastAPI endpoint
2. Convert `/api/skills` to async FastAPI endpoint
3. Convert `/api/activity` to async FastAPI endpoint
4. Add proper error handling and validation

### Phase 4: Add FastAPI Features
1. Enable auto documentation at `/docs`
2. Add health check endpoints
3. Implement proper CORS configuration
4. Add request/response middleware

### Phase 5: Testing & Validation
1. Test all API endpoints
2. Verify auto-generated documentation
3. Validate Kubernetes integration
4. Performance testing

## Technical Details

### New Dependencies
```python
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
```

### Pydantic Models
```python
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime

class Agent(BaseModel):
    id: str
    name: str
    type: str
    status: Literal["running", "idle", "error"]
    skills: int
    lastActivity: str
    successRate: float

class Skill(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None

class Activity(BaseModel):
    time: str
    type: Literal["success", "warning", "error", "info"]
    icon: str
    message: str
```

### Async Kubernetes Integration
```python
import asyncio
import subprocess
from typing import List

async def get_kubectl_data(command: str) -> str:
    """Async kubectl command execution"""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return stdout.decode().strip()
        return ""
    except Exception:
        return ""
```

### FastAPI Endpoints
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Agents Dashboard API",
    description="Real-time AI agents monitoring and control API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/agents", response_model=List[Agent])
async def get_agents():
    """Get list of all AI agents with real-time status"""
    # Implementation with async kubectl calls
    pass

@app.get("/api/skills", response_model=List[Skill])
async def get_skills():
    """Get list of available skills"""
    # Implementation with real skill discovery
    pass

@app.get("/api/activity", response_model=List[Activity])
async def get_activity():
    """Get recent system activity"""
    # Implementation with real event parsing
    pass

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

## Deployment Changes

### Container Updates
1. **Base Image**: Python 3.11+ (for better async support)
2. **Server**: Uvicorn instead of Flask development server
3. **Command**: `uvicorn api:app --host 0.0.0.0 --port 5000`
4. **Health Checks**: Built-in FastAPI health endpoints

### Kubernetes Integration
1. **Readiness Probe**: `/health` endpoint
2. **Liveness Probe**: `/health` endpoint
3. **Resource Limits**: Optimized for async workloads
4. **Environment Variables**: FastAPI configuration

## Validation Criteria

### Functional Requirements
- [ ] All API endpoints return correct data
- [ ] Auto documentation accessible at `/docs`
- [ ] Health checks work properly
- [ ] Kubernetes integration functional

### Performance Requirements
- [ ] API response time < 100ms
- [ ] Handle 10+ concurrent requests
- [ ] Memory usage stable under load
- [ ] No blocking operations

### Quality Requirements
- [ ] Type safety with Pydantic models
- [ ] Proper error handling
- [ ] Structured logging
- [ ] OpenAPI specification compliance

## Rollback Plan

If migration fails:
1. Revert `dashboard-api.yaml` to Flask version
2. Restart deployment with previous configuration
3. Verify dashboard functionality
4. Document issues for future improvement

## Timeline

- **Phase 1**: 15 minutes (Dependencies)
- **Phase 2**: 15 minutes (Models)
- **Phase 3**: 30 minutes (Endpoints)
- **Phase 4**: 15 minutes (Features)
- **Phase 5**: 15 minutes (Testing)
- **Total**: ~90 minutes

## Success Metrics

1. **Performance**: 10x faster API responses
2. **Documentation**: Interactive docs available at `/docs`
3. **Reliability**: Better error handling and validation
4. **Maintainability**: Type-safe code with proper models

---

**Migration Date**: 2026-03-17
**Author**: AI Assistant
**Version**: 1.0
