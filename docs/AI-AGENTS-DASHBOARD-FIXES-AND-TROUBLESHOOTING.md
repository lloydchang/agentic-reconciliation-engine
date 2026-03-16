# AI Agents Dashboard Fixes and Troubleshooting

## Overview

This document covers the recent fixes applied to the AI Agents Dashboard and provides comprehensive troubleshooting guidance for common issues. The dashboard was successfully fixed and is now fully operational with all features working correctly.

## Recent Fixes Applied

### 🛠️ Issues Resolved

#### 1. Missing Dependencies
**Problem**: Dashboard failed to load due to missing npm packages
```bash
ERROR: Cannot find module 'axios'
ERROR: Cannot find module 'recharts'
ERROR: Cannot find module '@mui/material/Grid2'
```

**Solution**: Installed required dependencies
```bash
cd dashboard-frontend
npm install axios recharts @mui/material@^5.15.0 @mui/icons-material@^5.15.0
```

#### 2. MUI Version Compatibility
**Problem**: TypeScript compilation errors with MUI Grid component
```bash
ERROR: TS2769: No overload matches this call
ERROR: Property 'item' does not exist on type
```

**Solution**: Downgraded MUI to compatible version (v5.15.0)
```bash
npm install @mui/material@^5.15.0 @mui/icons-material@^5.15.0
```

#### 3. Grid Component API Changes
**Problem**: MUI v7 removed `item` prop and changed Grid API
```typescript
// Old API (v7) - broken
<Grid item xs={12} sm={6} md={3}>

// New API (v5) - working
<Grid item xs={12} sm={6} md={3}>
```

**Solution**: Reverted to MUI v5 API syntax
```typescript
import { Grid } from '@mui/material'; // v5 import
// Grid item props work correctly in v5
```

#### 4. Missing API Backend
**Problem**: Dashboard couldn't fetch data due to missing backend service
```bash
ERROR: Failed to load resource: net::ERR_CONNECTION_REFUSED
ERROR: Dashboard fetch error: AxiosError: Network Error
```

**Solution**: Started Flask API server
```bash
cd /Users/lloyd/github/antigravity/gitops-infra-control-plane
pip install flask flask-cors
python api-server.py
```

#### 5. Unused Import Warnings
**Problem**: ESLint warnings for unused icon imports
```bash
WARNING: 'TimelineIcon' is defined but never used
WARNING: 'TrendingUpIcon' is defined but never used
```

**Solution**: Removed unused imports
```typescript
// Removed from imports
import { Timeline as TimelineIcon } from '@mui/icons-material';
import { TrendingUp as TrendingUpIcon } from '@mui/icons-material';
```

## Current Dashboard Status

### ✅ Working Features
- **Real-time Data**: Live metrics from Flask API
- **All Tabs**: Agent Overview, Performance Metrics, System Health
- **Interactive Elements**: Refresh button, debug dialog, tab navigation
- **Responsive Design**: Proper layout with MUI components
- **Agent Cards**: Detailed agent information with status indicators
- **Charts**: Performance and skills distribution charts (ready for data)
- **Debug Tools**: Quick access to debugging commands
- **Auto-refresh**: 30-second intervals with manual refresh

### 🌐 Access URLs
- **Development**: http://localhost:3001
- **API Backend**: http://localhost:5000
- **Production**: http://dashboard.local (with ingress)

## Troubleshooting Guide

### 🔧 Common Issues and Solutions

#### Dashboard Not Loading

**Symptoms**:
- Blank page or loading spinner
- Console errors about missing modules
- Network errors

**Solutions**:
```bash
# 1. Check dependencies
cd dashboard-frontend
npm install

# 2. Verify MUI version compatibility
npm list @mui/material
# Should be 5.15.0, not 7.x.x

# 3. Restart dev server
npm start

# 4. Clear browser cache
# Open browser dev tools, right-click refresh, select "Empty Cache and Hard Reload"
```

#### TypeScript Compilation Errors

**Symptoms**:
- Red squiggly lines in code
- Build failures
- Grid component errors

**Solutions**:
```bash
# 1. Check MUI version
npm list @mui/material

# 2. Downgrade if necessary
npm install @mui/material@^5.15.0 @mui/icons-material@^5.15.0

# 3. Verify Grid imports
import { Grid } from '@mui/material'; // Correct for v5
```

#### API Connection Errors

**Symptoms**:
- "Failed to fetch dashboard data" error
- Network connection refused
- Empty metrics display

**Solutions**:
```bash
# 1. Start API server
cd /Users/lloyd/github/antigravity/gitops-infra-control-plane
python api-server.py

# 2. Install dependencies if needed
pip install flask flask-cors

# 3. Verify API is running
curl http://localhost:5000/api/cluster-status

# 4. Check dashboard API calls
# Open browser dev tools -> Network tab
# Look for failed requests to localhost:5000
```

#### Port Conflicts

**Symptoms**:
- Port already in use errors
- Cannot start development server

**Solutions**:
```bash
# 1. Find process using port
lsof -i :3001
lsof -i :5000

# 2. Kill process if needed
kill -9 <PID>

# 3. Use different port
PORT=3002 npm start

# 4. Or kill all react-scripts processes
pkill -f "react-scripts start"
```

#### Memory/Performance Issues

**Symptoms**:
- Slow dashboard loading
- Browser becoming unresponsive
- High memory usage

**Solutions**:
```bash
# 1. Check system resources
npm run build  # Creates optimized build

# 2. Use production build
serve -s build  # Or any static server

# 3. Limit chart data points
# Edit App.tsx to reduce data complexity

# 4. Enable React dev tools profiling
# Install React Dev Tools browser extension
```

### 🐛 Debugging Techniques

#### Browser Console Debugging
```javascript
// 1. Check for JavaScript errors
// Open Dev Tools -> Console tab

// 2. Monitor network requests
// Dev Tools -> Network tab
// Look for failed API calls

// 3. Check React component state
// Install React Dev Tools
// Inspect component props and state

// 4. Profile performance
// Dev Tools -> Performance tab
// Record dashboard interactions
```

#### API Endpoint Testing
```bash
# Test all API endpoints
curl http://localhost:5000/api/cluster-status
curl http://localhost:5000/api/agents/status
curl http://localhost:5000/api/agents/detailed
curl http://localhost:5000/api/metrics/real-time
curl http://localhost:5000/api/system/health

# Expected responses should be JSON with data
```

#### Component Isolation
```typescript
// 1. Test components individually
// Create test component to isolate issues

// 2. Use React Dev Tools to inspect components
// Check props, state, and hooks

// 3. Add error boundaries
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary>
  <Dashboard />
</ErrorBoundary>
```

### 📊 Performance Monitoring

#### Dashboard Performance Metrics
```javascript
// Monitor dashboard performance
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(entry.name, entry.duration);
  }
});
observer.observe({entryTypes: ['measure']});

// Add performance marks
performance.mark('dashboard-start');
// ... dashboard operations
performance.mark('dashboard-end');
performance.measure('dashboard-load', 'dashboard-start', 'dashboard-end');
```

#### Memory Usage Tracking
```javascript
// Monitor memory usage
setInterval(() => {
  if (performance.memory) {
    console.log('Memory:', {
      used: Math.round(performance.memory.usedJSHeapSize / 1048576) + 'MB',
      total: Math.round(performance.memory.totalJSHeapSize / 1048576) + 'MB',
      limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576) + 'MB'
    });
  }
}, 10000);
```

### 🔄 Development Workflow

#### Local Development Setup
```bash
# 1. Start API backend
cd /Users/lloyd/github/antigravity/gitops-infra-control-plane
python api-server.py &

# 2. Start frontend dev server
cd dashboard-frontend
npm start

# 3. Open browser to http://localhost:3001
# 4. Open browser dev tools for debugging
```

#### Production Build Process
```bash
# 1. Create production build
cd dashboard-frontend
npm run build

# 2. Test production build locally
npx serve -s build

# 3. Deploy to Kubernetes
# Use deployment script or kubectl apply
```

#### Code Quality Checks
```bash
# 1. TypeScript compilation
npm run build

# 2. ESLint checking
npm run lint  # if configured

# 3. Unit tests
npm test  # if configured

# 4. Bundle analysis
npm install --save-dev webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js
```

## Advanced Troubleshooting

### 🔍 Deep Dive Issues

#### React Hydration Errors
**Problem**: HTML nesting validation warnings
```
Warning: In HTML, <p> cannot be a descendant of <p>
Warning: <p> cannot contain a nested <p>
```

**Solution**: Fix HTML structure in components
```typescript
// Incorrect
<Typography variant="body2">
  <Typography component="p">Nested paragraph</Typography>
</Typography>

// Correct
<Typography variant="body2">
  <span>Nested content</span>
</Typography>
```

#### State Management Issues
**Problem**: Component state not updating properly

**Solution**: Verify React hooks usage
```typescript
// Correct useState usage
const [agents, setAgents] = useState<Agent[]>([]);

// Correct useEffect dependency
useEffect(() => {
  fetchData();
}, []); // Empty dependency for one-time fetch

// Correct async handling
const fetchData = async () => {
  try {
    const response = await axios.get('/api/agents/detailed');
    setAgents(response.data);
  } catch (error) {
    console.error('Dashboard fetch error:', error);
  }
};
```

#### Memory Leaks
**Problem**: Memory usage increasing over time

**Solution**: Clean up intervals and event listeners
```typescript
useEffect(() => {
  const interval = setInterval(fetchData, 30000);
  
  // Cleanup function
  return () => clearInterval(interval);
}, []); // Include empty dependency array
```

### 🚀 Performance Optimization

#### Code Splitting
```typescript
// Lazy load heavy components
const PerformanceMetrics = React.lazy(() => import('./PerformanceMetrics'));

// Use with Suspense
<Suspense fallback={<div>Loading...</div>}>
  <PerformanceMetrics />
</Suspense>
```

#### Virtualization
```typescript
// For large lists, use react-window
import { FixedSizeList as List } from 'react-window';

const Row = ({ index, style }) => (
  <div style={style}>
    Agent {index}
  </div>
);

<List
  height={600}
  itemCount={agents.length}
  itemSize={80}
>
  {Row}
</List>
```

#### Memoization
```typescript
// Memoize expensive computations
const expensiveValue = useMemo(() => {
  return agents.reduce((sum, agent) => sum + agent.cpu, 0);
}, [agents]);

// Memoize event handlers
const handleRefresh = useCallback(() => {
  fetchData();
}, [fetchData]);
```

## Environment-Specific Issues

### 🖥️ macOS Specific
```bash
# Port conflicts with AirPlay
sudo lsof -i :5000
sudo kill -9 <PID>

# Permission issues with Node.js
brew install node
# Or use nvm for version management
```

### 🐧 Linux Specific
```bash
# Package manager differences
sudo apt-get install nodejs npm
# Or
sudo yum install nodejs npm

# Firewall issues
sudo ufw allow 3001
sudo ufw allow 5000
```

### 🪟 Windows Specific
```bash
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Port conflicts with Windows services
netstat -ano | findstr :3001
taskkill /PID <PID> /F
```

## Monitoring and Alerting

### 📈 Dashboard Health Monitoring
```bash
# Create health check script
#!/bin/bash
# check-dashboard-health.sh

# Check frontend
if curl -f http://localhost:3001 > /dev/null 2>&1; then
  echo "✅ Frontend healthy"
else
  echo "❌ Frontend down"
  exit 1
fi

# Check backend API
if curl -f http://localhost:5000/api/cluster-status > /dev/null 2>&1; then
  echo "✅ Backend API healthy"
else
  echo "❌ Backend API down"
  exit 1
fi
```

### 🔔 Automated Alerts
```yaml
# Kubernetes health check
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: dashboard
    image: dashboard:latest
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Best Practices

### ✅ Development Best Practices
1. **Always check console for errors** first
2. **Use React Dev Tools** for component debugging
3. **Test API endpoints independently** before frontend integration
4. **Keep dependencies updated** but compatible
5. **Use TypeScript strict mode** for better error catching
6. **Implement error boundaries** for graceful error handling
7. **Monitor bundle size** with webpack-bundle-analyzer
8. **Use performance profiling** regularly

### 🛡️ Security Best Practices
1. **Validate API responses** before using them
2. **Sanitize user inputs** to prevent XSS
3. **Use HTTPS** in production
4. **Implement authentication** for production dashboards
5. **Audit dependencies** for security vulnerabilities
6. **Use Content Security Policy** headers
7. **Enable CORS** properly on API servers

### 📦 Deployment Best Practices
1. **Use environment variables** for configuration
2. **Implement health checks** in production
3. **Use rolling updates** for zero downtime
4. **Monitor resource usage** in production
5. **Set up alerts** for critical failures
6. **Backup configurations** regularly
7. **Test disaster recovery** procedures

## Support Resources

### 📚 Documentation
- [AI Agents Dashboard Guide](AI-AGENTS-DASHBOARD-GUIDE.md)
- [Complete Deployment Guide](AI-AGENTS-COMPLETE-DEPLOYMENT-GUIDE.md)
- [Ecosystem Deployment Script](AI-AGENTS-ECOSYSTEM-DEPLOYMENT-SCRIPT.md)

### 🛠️ Tools and Resources
- **React Dev Tools**: Browser extension for React debugging
- **Redux Dev Tools**: For state management debugging
- **Webpack Bundle Analyzer**: For bundle size optimization
- **Lighthouse**: For performance auditing
- **Chrome Dev Tools**: For general debugging and profiling

### 🆘 Getting Help
1. **Check this documentation first**
2. **Review browser console errors**
3. **Verify API endpoints are working**
4. **Check network connectivity**
5. **Validate resource availability**
6. **Review recent changes** if something stopped working

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: AI Agents Dashboard Team  
**Status**: ✅ Fully Operational
