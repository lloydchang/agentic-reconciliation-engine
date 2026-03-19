# Comprehensive AI Agents Analytics Dashboard

## Overview

The Comprehensive AI Agents Analytics Dashboard provides real-time monitoring, detailed analytics, and failure analysis for the Agentic Reconciliation Engine's AI agents ecosystem. This dashboard replaces the previous static, hardcoded metrics system with dynamic, real-time data collection and visualization.

## 🎯 Problem Statement

### Issues with Original Dashboard

1. **Hardcoded Metrics**: Static values like "99.2% success rate" in ConfigMaps
2. **Incomplete Agent Discovery**: Only counted Kubernetes pods, missing Temporal workflows and memory agents
3. **Missing Skill Details**: Showed count (64) but no individual skill descriptions
4. **No Failure Analysis**: Success rate shown without context for failures
5. **No Time-Series Data**: No historical trends or performance visualization
6. **Static ConfigMap**: Dashboard HTML served from ConfigMap with no dynamic updates

### Root Cause Analysis

- **Static ConfigMap**: Dashboard HTML served from ConfigMap with hardcoded metrics
- **Missing Dynamic Updates**: No real-time connection to agent status
- **Incomplete Agent Discovery**: Only counting Kubernetes pods, not Temporal workflows
- **No Skill Details**: Dashboard shows count (64) but no individual skill descriptions
- **No Failure Analysis**: Success rate shown without context for 0.8% failures

## 🚀 Solution Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Comprehensive Dashboard                    │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React/Chart.js)     │    Backend (FastAPI)      │
│  - Real-time UI                │    - Metrics Collection   │
│  - Interactive Charts          │    - Time-series Storage  │
│  - Dark/Light Theme            │    - Failure Analysis      │
│  - Auto-refresh (30s)          │    - API Endpoints         │
├─────────────────────────────────────────────────────────────┤
│                     Data Sources                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │   K8s Pods  │ │ Temporal    │ │Memory Agents│ │Pi-Mono  │ │
│  │             │ │ Workflows   │ │             │ │RPC      │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Storage Layer                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   SQLite    │ │  SKILL.md   │ │  Metrics    │           │
│  │ Time-series │ │   Files     │ │   Server    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Agent Discovery Methods

The dashboard implements comprehensive agent discovery across all 4 execution methods:

| Method | Purpose | Discovery Mechanism | Metrics |
|---|---|---|---|
| **Kubernetes Pods** | Container-based agents | `kubectl list pods` | CPU, Memory, Status |
| **Temporal Workflows** | Orchestration-based agents | Temporal API | Success Rate, Error Count |
| **Memory Agents** | Local inference agents | HTTP endpoints | Inference metrics |
| **Pi-Mono RPC** | Interactive AI assistance | RPC calls | Session metrics |

## 📊 Features

### 1. Real-time Agent Metrics

- **Total Agent Count**: Comprehensive counting across all execution methods
- **Agent Breakdown**: By type (Pods, Workflows, Memory, RPC)
- **Status Monitoring**: Running, Failed, Unknown states
- **Performance Metrics**: CPU usage, Memory usage, Success rates

### 2. Detailed Skill Information

- **64+ Skills**: Parsed from `SKILL.md` files
- **Full Descriptions**: Extracted from frontmatter
- **Risk Level Categorization**: Low, Medium, High risk skills
- **Autonomy Levels**: Conditional, Fully-auto skills
- **Execution Metrics**: Success/failure counts, timing data

### 3. Time-Series Visualization

- **Performance Trends**: Success rate over time
- **Skill Execution Metrics**: Bar charts for top skills
- **Historical Data**: SQLite database for persistence
- **Interactive Charts**: Zoom, filter, export capabilities
- **Auto-refresh**: 30-second intervals

### 4. Failure Analysis & Post-Mortem

- **Root Cause Analysis**: Detailed failure tracking
- **Error Categorization**: By type, agent, skill
- **Post-Mortem Reports**: Resolution and diagnosis
- **Success Rate Calculation**: Real-time from actual operations
- **Failure Trends**: Pattern analysis and prevention

### 5. Modern UI/UX

- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Theme**: Toggle between themes
- **Interactive Elements**: Clickable metrics, expandable details
- **Real-time Updates**: Live connection status indicator
- **Professional Styling**: Modern charts and animations

## 🛠️ Implementation Details

### Backend API (FastAPI)

#### Core Components

```python
class MetricsCollector:
    - collect_agent_metrics()
    - collect_skill_metrics()
    - setup_kubernetes()
    - parse_skill_md()

class FailureAnalyzer:
    - analyze_failures()
    - generate_reports()
    - track_patterns()
```

#### API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v2/agents` | GET | Comprehensive agent metrics |
| `/api/v2/skills` | GET | Detailed skill information |
| `/api/v2/metrics/timeseries` | GET | Time-series data |
| `/api/v2/failures/analysis` | GET | Failure analysis |
| `/api/v2/failures/report` | POST | Report new failure |

#### Database Schema

```sql
-- Agents table for time-series metrics
CREATE TABLE agents (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    status TEXT NOT NULL,
    pod_name TEXT,
    workflow_id TEXT,
    memory_agent_id TEXT,
    cpu_usage REAL,
    memory_usage REAL,
    success_rate REAL,
    error_count INTEGER
);

-- Skills table for skill metrics
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    skill_description TEXT,
    risk_level TEXT,
    autonomy_level TEXT,
    execution_count INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    avg_execution_time REAL
);

-- Failures table for post-mortem analysis
CREATE TABLE failures (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    skill_name TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT,
    root_cause TEXT,
    resolution TEXT,
    severity TEXT,
    status TEXT DEFAULT 'open'
);
```

### Frontend (HTML/JavaScript/Chart.js)

#### Key Features

- **Chart.js Integration**: Interactive time-series and bar charts
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Responsive Grid Layout**: Adapts to screen size
- **Theme System**: Dark/Light mode toggle
- **Error Handling**: Graceful degradation on API failures

#### JavaScript Architecture

```javascript
// Core functions
- initializeCharts()
- loadAllData()
- loadAgents()
- loadSkills()
- loadMetrics()
- loadFailureAnalysis()
- createAgentCard()
- createSkillItem()
- createFailureItem()
- updatePerformanceChart()
- updateSkillsChart()
```

## 🚀 Deployment

### Kubernetes Manifests

#### 1. API Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: comprehensive-dashboard-api
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: comprehensive-dashboard-api
  template:
    spec:
      containers:
      - name: api
        image: python:3.9-slim
        ports:
        - containerPort: 5000
        volumeMounts:
        - name: api-code
          mountPath: /app
        - name: skills-data
          mountPath: /skills
```

#### 2. Frontend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: comprehensive-dashboard-frontend
  namespace: ai-infrastructure
spec:
  replicas: 1
  selector:
    matchLabels:
      app: comprehensive-dashboard-frontend
  template:
    spec:
      containers:
      - name: frontend
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: dashboard-html
          mountPath: /usr/share/nginx/html
```

#### 3. Services
```yaml
apiVersion: v1
kind: Service
metadata:
  name: comprehensive-dashboard-api
  namespace: ai-infrastructure
spec:
  selector:
    app: comprehensive-dashboard-api
  ports:
  - name: http
    port: 5000
    targetPort: 5000
```

### Deployment Script

```bash
#!/bin/bash
# deploy-comprehensive-dashboard.sh

echo "🚀 Deploying Comprehensive AI Agents Analytics Dashboard..."

# Create namespace
kubectl create namespace ai-infrastructure --dry-run=client -o yaml | kubectl apply -f -

# Deploy components
kubectl apply -f comprehensive-dashboard-api-configmap.yaml
kubectl apply -f comprehensive-dashboard-configmap.yaml
kubectl apply -f comprehensive-dashboard-deployment.yaml

# Wait for readiness
kubectl rollout status deployment/comprehensive-dashboard-api -n ai-infrastructure
kubectl rollout status deployment/comprehensive-dashboard-frontend -n ai-infrastructure

echo "✅ Deployment complete!"
echo "Access: http://localhost:8083 (after port-forward)"
```

### Port Forwarding

```bash
# Frontend
kubectl port-forward svc/comprehensive-dashboard-frontend 8083:80 -n ai-infrastructure &

# API
kubectl port-forward svc/comprehensive-dashboard-api 5001:5000 -n ai-infrastructure &
```

## 📊 Usage Guide

### Accessing the Dashboard

1. **Deploy the dashboard**: `./deploy-comprehensive-dashboard.sh`
2. **Start port forwards**: Run the port-forward commands
3. **Access frontend**: http://localhost:8083
4. **API documentation**: http://localhost:5001/docs

### Dashboard Navigation

#### Main Metrics Grid
- **Total Agents**: Real-time count across all execution methods
- **Active Skills**: Number of available skills with risk breakdown
- **Success Rate**: Calculated from actual operations
- **Recent Failures**: Count from last 24 hours

#### Performance Trends Chart
- **Success Rate Line**: Shows success rate over time
- **Error Count Line**: Shows error count trends
- **Time Range**: Last 24 hours (configurable)
- **Interactive**: Hover for details, zoom for closer inspection

#### Skills Metrics Chart
- **Top 10 Skills**: By execution count
- **Success vs Execution**: Compare success and total executions
- **Risk Level Color Coding**: Visual risk indicators

#### Active Agents Grid
- **Agent Cards**: Individual agent status and metrics
- **Type Indicators**: Pod, Workflow, Memory, RPC
- **Status Badges**: Running, Failed states
- **Performance Metrics**: Success rates, error counts

#### Skills List
- **Skill Cards**: Detailed skill information
- **Descriptions**: Full skill descriptions from SKILL.md
- **Metadata Tags**: Risk level, autonomy level
- **Execution Stats**: Success/failure counts

#### Failure Analysis Section
- **Recent Failures**: Last 10 failures with details
- **Root Cause Analysis**: Investigation and resolution
- **Error Patterns**: Categorized by type and agent
- **Post-Mortem**: Complete failure lifecycle

### API Usage

#### Get All Agents
```bash
curl http://localhost:5001/api/v2/agents
```

#### Get All Skills
```bash
curl http://localhost:5001/api/v2/skills
```

#### Get Time-Series Metrics
```bash
curl "http://localhost:5001/api/v2/metrics/timeseries?metric_type=agents&time_range_hours=24"
```

#### Get Failure Analysis
```bash
curl "http://localhost:5001/api/v2/failures/analysis?time_range_hours=24"
```

#### Report Failure
```bash
curl -X POST http://localhost:5001/api/v2/failures/report \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "test-agent",
    "error_type": "timeout",
    "error_message": "Operation timed out",
    "severity": "medium"
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `METRICS_SERVER_URL` | `http://temporal-worker.temporal.svc.cluster.local:8080` | Temporal metrics server |
| `PYTHONPATH` | `/app` | Python path for API |
| `DB_PATH` | `/tmp/agents_metrics.db` | SQLite database path |

### Customization

#### Adding New Agent Types

1. **Update MetricsCollector**: Add new collection method
2. **Update Database Schema**: Add new columns if needed
3. **Update Frontend**: Add new agent type handling
4. **Update API**: Add new endpoints if needed

#### Adding New Metrics

1. **Database Schema**: Add new tables/columns
2. **Collection Logic**: Implement metric gathering
3. **API Endpoints**: Add new metric endpoints
4. **Frontend Charts**: Add new visualizations

#### Custom Themes

```css
/* Add custom theme variables */
:root {
    --primary-color: #2563eb;
    --secondary-color: #7c3aed;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Dashboard Shows "Error"
- **Check API Health**: `curl http://localhost:5001/health`
- **Check Pod Status**: `kubectl get pods -n ai-infrastructure`
- **Check Logs**: `kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure`

#### 2. Agent Count is 0
- **Check Kubernetes Connection**: `kubectl cluster-info`
- **Check Labels**: `kubectl get pods -n ai-infrastructure --show-labels`
- **Check API Endpoints**: Verify temporal and memory agent endpoints

#### 3. Skills Not Loading
- **Check Skills Directory**: Verify `/skills` mount path
- **Check File Permissions**: Ensure SKILL.md files are readable
- **Check YAML Parsing**: Verify SKILL.md frontmatter format

#### 4. Charts Not Updating
- **Check API Response**: Verify metrics endpoints return data
- **Check JavaScript Console**: Look for frontend errors
- **Check Database**: Verify SQLite database has data

### Debug Commands

```bash
# Check all dashboard components
kubectl get all -n ai-infrastructure -l component=analytics

# Check API logs
kubectl logs deployment/comprehensive-dashboard-api -n ai-infrastructure -f

# Check frontend logs
kubectl logs deployment/comprehensive-dashboard-frontend -n ai-infrastructure -f

# Test API endpoints
curl http://localhost:5001/health
curl http://localhost:5001/api/v2/agents
curl http://localhost:5001/api/v2/skills

# Check database
kubectl exec deployment/comprehensive-dashboard-api -n ai-infrastructure \
  -- sqlite3 /tmp/agents_metrics.db ".tables"
```

## 📈 Performance Considerations

### Database Optimization

- **Indexing**: Add indexes on timestamp columns for faster queries
- **Cleanup**: Implement data retention policies (e.g., 30 days)
- **Partitioning**: Consider partitioning by date for large datasets

### API Performance

- **Caching**: Implement Redis caching for frequent queries
- **Pagination**: Add pagination for large skill/agent lists
- **Rate Limiting**: Implement rate limiting for API endpoints

### Frontend Optimization

- **Lazy Loading**: Load agent/skill details on demand
- **Chart Updates**: Optimize chart redraw frequency
- **Bundle Size**: Minimize JavaScript bundle size

## 🔮 Future Enhancements

### Planned Features

1. **Real-time WebSockets**: Replace polling with WebSocket connections
2. **Advanced Filtering**: Filter by agent type, skill, time range
3. **Export Functionality**: Export metrics to CSV/JSON
4. **Alerting Integration**: Integrate with Prometheus/Alertmanager
5. **Multi-cluster Support**: Monitor across multiple Kubernetes clusters
6. **Custom Dashboards**: User-configurable dashboard layouts
7. **ML Anomaly Detection**: Machine learning for anomaly detection
8. **Mobile App**: Native mobile application

### Integration Opportunities

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Advanced visualization and dashboards
- **ELK Stack**: Log aggregation and analysis
- **Jaeger**: Distributed tracing
- **Fluentd**: Log collection and processing

## 📚 References

### Related Documentation

- [AGENTS.md](../core/ai/AGENTS.md) - Agent architecture overview
- [SKILL_TEMPLATE.md](../core/ai/skills/SKILL_TEMPLATE.md) - Skill definition format
- [DASHBOARD-API-DEVELOPMENT-GUIDE.md](../docs/DASHBOARD-API-DEVELOPMENT-GUIDE.md) - API development guide
- [OVERLAY-QUICK-START.md](../docs/OVERLAY-QUICK-START.md) - Overlay system documentation

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Temporal Documentation](https://docs.temporal.io/)

---

## 📝 License

This comprehensive dashboard is part of the Agentic Reconciliation Engine project and follows the same licensing terms.

## 🤝 Contributing

Contributions to the comprehensive dashboard are welcome! Please refer to the main project's contribution guidelines.

---

**Last Updated**: 2025-03-17  
**Version**: 2.0.0  
**Status**: Production Ready ✅
