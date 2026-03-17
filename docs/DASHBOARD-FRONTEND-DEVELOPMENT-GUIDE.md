# AI Agents Dashboard - Complete Development Guide

## Overview

This document covers the complete development lifecycle of the AI agents dashboard, including frontend development, branding updates, API integration, and deployment strategies.

## Frontend Architecture

### Technology Stack
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **HTTP Client**: Axios for API communication
- **Build Tool**: Create React App with custom configuration
- **Styling**: Material-UI themes and custom CSS

### Project Structure
```
dashboard-frontend/
├── public/
│   ├── index.html          # Main HTML template
│   ├── manifest.json       # PWA configuration
│   ├── favicon.ico         # Custom AI-themed favicon
│   └── robots.txt          # SEO configuration
├── src/
│   ├── App.tsx             # Main application component
│   ├── index.tsx           # Application entry point
│   └── components/         # Reusable UI components
└── package.json            # Dependencies and scripts
```

## Branding and Professional Updates

### Title and Metadata Updates

#### HTML Template Changes
**File**: `public/index.html`

```html
<!-- Before -->
<title>React App</title>
<meta name="description" content="Web site created using create-react-app">

<!-- After -->
<title>AI Agents Dashboard</title>
<meta name="description" content="AI Agents Dashboard - Real-time monitoring and orchestration of AI agents in Kubernetes infrastructure">
```

#### PWA Manifest Updates
**File**: `public/manifest.json`

```json
{
  "short_name": "AI Dashboard",
  "name": "AI Agents Dashboard",
  "theme_color": "#1976d2",
  "background_color": "#ffffff"
}
```

### Favicon Development

#### Custom Favicon Creation
**Script**: `create-favicon.py`

```python
from PIL import Image, ImageDraw
import math

# Create AI-themed favicon
size = 32
img = Image.new('RGBA', (size, size), (25, 118, 210, 255))  # Material-UI blue
draw = ImageDraw.Draw(img)

# Draw AI brain/network icon
center = size // 2
circle_size = size // 3
draw.ellipse([center - circle_size, center - circle_size, center + circle_size, center + circle_size], 
             fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=1)

# Add network nodes
for i in range(3):
    angle = i * 120  # 120 degrees apart
    x = center + int(circle_size * 1.5 * math.cos(math.radians(angle)))
    y = center + int(circle_size * 1.5 * math.sin(math.radians(angle)))
    draw.ellipse([x-2, y-2, x+2, y+2], fill=(255, 255, 255, 255))

img.save('public/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32)])
```

#### Favicon Features
- **Design**: AI brain/network theme
- **Colors**: Material-UI blue (#1976d2) with white accents
- **Sizes**: 16x16 and 32x32 for browser compatibility
- **Format**: ICO with multiple resolutions

## Application Architecture

### Main Component Structure

#### App.tsx - Core Application
```typescript
import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Grid, Card, CardContent, Typography, Box, Chip } from '@mui/material';
import axios from 'axios';

// Define Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Material-UI blue
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Types
interface Agent {
  name: string;
  status: string;
  language: string;
  currentActivity: string;
  skills: string[];
  cpu: number;
  memory: number;
  uptime: string;
}

interface Metrics {
  activeAgents: number;
  skillsExecuted: number;
  avgResponseTime: number;
  activeWorkflows: number;
  errorsLast24h: number;
}

// Main App Component
const App: () => JSX.Element = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data fetching logic
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch agents and metrics in parallel
      const [agentsResponse, metricsResponse] = await Promise.all([
        axios.get('/api/core/ai/runtime/detailed'),
        axios.get('/api/metrics/real-time')
      ]);

      if (agentsResponse.data.error) {
        setError(agentsResponse.data.message);
        return;
      }

      setAgents(agentsResponse.data.agents || []);
      setMetrics(metricsResponse.data);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 504) {
        setError('Real metrics server unavailable. Run: ./setup-real-connection.sh');
      } else {
        setError('Failed to fetch dashboard data');
      }
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Render logic...
};
```

### Component Architecture

#### Dashboard Layout
```typescript
const Dashboard: () => JSX.Element = () => {
  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Typography variant="h4" component="h1" gutterBottom>
          🚀 AI Agents Dashboard
        </Typography>
        
        {/* Metrics Overview */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">Active Agents</Typography>
                <Typography variant="h4">{metrics?.activeAgents || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          {/* Additional metric cards... */}
        </Grid>

        {/* Agents Grid */}
        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} md={6} key={agent.name}>
              <AgentCard agent={agent} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  );
};
```

#### Agent Card Component
```typescript
const AgentCard: React.FC<{ agent: Agent }> = ({ agent }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'success';
      case 'idle': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">{agent.name}</Typography>
          <Chip 
            label={agent.status} 
            color={getStatusColor(agent.status) as any}
            size="small"
          />
        </Box>
        
        <Typography variant="body2" color="textSecondary" gutterBottom>
          Language: {agent.language}
        </Typography>
        
        <Typography variant="body2" gutterBottom>
          Current Activity: {agent.currentActivity}
        </Typography>
        
        {/* Skills */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" component="span">
            Skills ({agent.skills.length}):
          </Typography>
          {agent.skills.slice(0, 3).map((skill, index) => (
            <Chip key={index} label={skill} size="small" sx={{ ml: 0.5 }} />
          ))}
          {agent.skills.length > 3 && (
            <Chip label={`+${agent.skills.length - 3} more`} size="small" sx={{ ml: 0.5 }} />
          )}
        </Box>
        
        {/* Resource Usage */}
        <Typography variant="body2" color="textSecondary">
          CPU: {agent.cpu}% | Memory: {agent.memory}MB
        </Typography>
        
        <Typography variant="body2" color="textSecondary">
          Uptime: {agent.uptime}
        </Typography>
      </CardContent>
    </Card>
  );
};
```

## API Integration

### HTTP Client Configuration

#### Axios Setup
```typescript
import axios from 'axios';

// Configure base URL for API calls
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5002',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 504) {
      console.error('Gateway Timeout - Real metrics server unavailable');
    }
    return Promise.reject(error);
  }
);
```

### Data Fetching Patterns

#### Parallel Data Loading
```typescript
const fetchDashboardData = async () => {
  try {
    const [agentsResponse, metricsResponse, workflowsResponse] = await Promise.all([
      api.get('/api/core/ai/runtime/detailed'),
      api.get('/api/metrics/real-time'),
      api.get('/api/workflows/status')
    ]);

    return {
      agents: agentsResponse.data.agents || [],
      metrics: metricsResponse.data,
      workflows: workflowsResponse.data
    };
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error);
    throw error;
  }
};
```

#### Error Handling Strategy
```typescript
const handleApiError = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 504) {
      return {
        type: 'gateway_timeout',
        message: 'Real metrics server unavailable',
        action: 'Run: ./setup-real-connection.sh'
      };
    } else if (error.code === 'ECONNREFUSED') {
      return {
        type: 'connection_refused',
        message: 'API server not running',
        action: 'Start the real data API'
      };
    }
  }
  
  return {
    type: 'unknown_error',
    message: 'Unknown error occurred',
    action: 'Check system logs'
  };
};
```

## State Management

### React State Patterns

#### Local State Management
```typescript
const useDashboardState = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const refreshData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await fetchDashboardData();
      setAgents(data.agents);
      setMetrics(data.metrics);
      setLastUpdated(new Date());
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, [refreshData]);

  return {
    agents,
    metrics,
    loading,
    error,
    lastUpdated,
    refreshData
  };
};
```

### Performance Optimization

#### Memoization
```typescript
import { memo, useMemo } from 'react';

// Memoized agent card to prevent unnecessary re-renders
const AgentCard = memo<AgentCardProps>(({ agent }) => {
  const skillsDisplay = useMemo(() => {
    return agent.skills.slice(0, 3).map((skill, index) => (
      <Chip key={index} label={skill} size="small" sx={{ ml: 0.5 }} />
    ));
  }, [agent.skills]);

  const statusColor = useMemo(() => {
    return getStatusColor(agent.status);
  }, [agent.status]);

  return (
    <Card sx={{ height: '100%' }}>
      {/* Card content using memoized values */}
    </Card>
  );
});
```

#### Virtual Scrolling (for large datasets)
```typescript
import { FixedSizeList as List } from 'react-window';

const AgentList: React.FC<{ agents: Agent[] }> = ({ agents }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <AgentCard agent={agents[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={agents.length}
      itemSize={200}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

## Responsive Design

### Material-UI Breakpoints
```typescript
const useResponsiveStyles = () => {
  return useMemo(() => ({
    container: {
      py: { xs: 2, md: 4 },
      px: { xs: 1, md: 2 }
    },
    metricsGrid: {
      spacing: { xs: 2, md: 3 }
    },
    agentCard: {
      height: { xs: 'auto', md: '100%' }
    }
  }), []);
};
```

### Mobile-First Design
```typescript
const Dashboard: React.FC = () => {
  const isMobile = useMediaQuery('(max-width:600px)');
  const styles = useResponsiveStyles();

  return (
    <Container maxWidth="xl" sx={styles.container}>
      <Grid container spacing={isMobile ? 2 : 3}>
        {/* Responsive layout */}
        <Grid item xs={12} md={6} lg={4}>
          <MetricCard />
        </Grid>
      </Grid>
    </Container>
  );
};
```

## Accessibility Features

### ARIA Labels and Semantic HTML
```typescript
const MetricCard: React.FC<{ title: string; value: number; description: string }> = ({ 
  title, value, description 
}) => (
  <Card>
    <CardContent>
      <Typography 
        variant="h6" 
        component="h2"
        aria-label={`${title}: ${value}`}
      >
        {title}
      </Typography>
      <Typography 
        variant="h4" 
        aria-describedby={`${title}-description`}
        role="img"
        aria-label={`Current value: ${value}`}
      >
        {value}
      </Typography>
      <Typography 
        id={`${title}-description`}
        variant="body2" 
        color="textSecondary"
      >
        {description}
      </Typography>
    </CardContent>
  </Card>
);
```

### Keyboard Navigation
```typescript
const InteractiveAgentCard: React.FC<{ agent: Agent }> = ({ agent }) => {
  const [selected, setSelected] = useState(false);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      setSelected(!selected);
    }
  };

  return (
    <Card
      tabIndex={0}
      role="button"
      aria-pressed={selected}
      onKeyDown={handleKeyDown}
      onClick={() => setSelected(!selected)}
      sx={{
        cursor: 'pointer',
        '&:focus': {
          outline: '2px solid #1976d2',
          outlineOffset: 2
        }
      }}
    >
      {/* Card content */}
    </Card>
  );
};
```

## Development Workflow

### Local Development Setup
```bash
# Start backend services
./setup-real-connection.sh
python3 real-data-api.py &

# Start frontend development server
cd dashboard-frontend
npm start

# Application will be available at http://localhost:3000
```

### Environment Configuration
```bash
# .env.local file
REACT_APP_API_URL=http://localhost:5002
REACT_APP_WS_URL=ws://localhost:5002
REACT_APP_REFRESH_INTERVAL=30000
```

### Build Process
```bash
# Development build
npm run build

# Production build with optimization
npm run build --production

# Analyze bundle size
npm run analyze
```

## Testing Strategy

### Unit Testing
```typescript
// AgentCard.test.tsx
import { render, screen } from '@testing-library/react';
import { AgentCard } from './AgentCard';
import { mockAgent } from '../test-utils';

describe('AgentCard', () => {
  it('renders agent information correctly', () => {
    render(<AgentCard agent={mockAgent} />);
    
    expect(screen.getByText(mockAgent.name)).toBeInTheDocument();
    expect(screen.getByText(mockAgent.language)).toBeInTheDocument();
    expect(screen.getByText(mockAgent.status)).toBeInTheDocument();
  });

  it('displays correct status color', () => {
    render(<AgentCard agent={mockAgent} />);
    
    const statusChip = screen.getByText(mockAgent.status);
    expect(statusChip).toHaveClass('MuiChip-colorSuccess');
  });
});
```

### Integration Testing
```typescript
// Dashboard.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import { server } from '../mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Dashboard Integration', () => {
  it('loads and displays dashboard data', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Active Agents')).toBeInTheDocument();
    });
    
    expect(screen.getByText('3')).toBeInTheDocument(); // Mock agent count
  });

  it('handles API errors gracefully', async () => {
    server.use(
      rest.get('/api/core/ai/runtime/detailed', (req, res, ctx) => {
        return res(ctx.status(504));
      })
    );

    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Real metrics server unavailable/)).toBeInTheDocument();
    });
  });
});
```

### E2E Testing
```typescript
// dashboard.e2e.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard E2E', () => {
  test('displays real agent data', async ({ page }) => {
    await page.goto('http://localhost:3001');
    
    // Wait for data to load
    await expect(page.locator('[data-testid="agent-count"]')).toContainText(/\d+/);
    
    // Check for agent cards
    await expect(page.locator('[data-testid="agent-card"]')).toHaveCount.greaterThan(0);
    
    // Verify real data indicators
    await expect(page.locator('text=Real Data Only')).toBeVisible();
  });

  test('handles connection errors', async ({ page }) => {
    // Simulate connection loss
    await page.route('**/api/core/ai/runtime/detailed', route => route.abort());
    
    await page.goto('http://localhost:3001');
    
    // Should display error message
    await expect(page.locator('text=Real metrics server unavailable')).toBeVisible();
  });
});
```

## Performance Optimization

### Bundle Optimization
```javascript
// webpack.config.js (custom webpack config)
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        mui: {
          test: /[\\/]node_modules[\\/]@mui[\\/]/,
          name: 'mui',
          chunks: 'all',
        },
      },
    },
  },
};
```

### Code Splitting
```typescript
// Lazy loading for heavy components
const AgentDetails = React.lazy(() => import('./AgentDetails'));

const Dashboard: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  return (
    <div>
      {/* Main dashboard */}
      {selectedAgent && (
        <React.Suspense fallback={<div>Loading...</div>}>
          <AgentDetails agentId={selectedAgent} />
        </React.Suspense>
      )}
    </div>
  );
};
```

## Deployment Configuration

### Docker Configuration
```dockerfile
# Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Kubernetes Deployment
```yaml
# dashboard-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard-frontend
  namespace: ai-infrastructure
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dashboard-frontend
  template:
    metadata:
      labels:
        app: dashboard-frontend
    spec:
      containers:
      - name: frontend
        image: dashboard-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        env:
        - name: REACT_APP_API_URL
          value: "http://real-data-api-service:5002"
```

This comprehensive development guide covers all aspects of the AI agents dashboard frontend, from initial setup and branding to production deployment and optimization.
