# AI Infrastructure Portal - Developer Guide

## Overview

This guide provides comprehensive information for developers working with the AI Infrastructure Portal. It covers development setup, API integration, contribution guidelines, testing procedures, and best practices for extending and maintaining the platform.

## Development Environment Setup

### Prerequisites

#### System Requirements
- **Node.js**: v18.0.0 or later
- **npm**: v8.0.0 or later (comes with Node.js)
- **Git**: v2.30.0 or later
- **Docker**: v20.10.0 or later (for containerized development)
- **Kubernetes**: v1.24.0 or later (for local cluster development)

#### Operating System Support
- **Linux**: Ubuntu 20.04+, CentOS 8+, RHEL 8+
- **macOS**: 11.0+ (Big Sur or later)
- **Windows**: Windows 10 Pro/Enterprise with WSL2

### Local Development Setup

#### 1. Clone Repository
```bash
git clone https://github.com/your-org/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine
```

#### 2. Install Dependencies
```bash
# Install root-level dependencies
npm install

# Install dashboard dependencies
cd dashboard/ui
npm install

# Return to root
cd ../..
```

#### 3. Environment Configuration
```bash
# Copy environment template
cp core/config/.env.template core/config/.env.local

# Edit configuration
nano core/config/.env.local
```

**Required Environment Variables:**
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_portal
DB_USER=ai_user
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Configuration
API_PORT=5001
DASHBOARD_PORT=8081
JWT_SECRET=your_jwt_secret_key
API_KEY=your_api_key

# External Services
ARGOCD_URL=http://localhost:8080
PROMETHEUS_URL=http://localhost:9090
ELASTICSEARCH_URL=http://localhost:9200

# Development Settings
NODE_ENV=development
LOG_LEVEL=debug
ENABLE_CORS=true
```

#### 4. Start Development Services

##### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose -f docker-compose.dev.yaml up -d

# Check service status
docker-compose -f docker-compose.dev.yaml ps
```

##### Manual Service Startup
```bash
# Start API server
npm run dev:api

# Start dashboard server (in another terminal)
npm run dev:dashboard

# Start Redis (if not using Docker)
redis-server

# Start PostgreSQL (if not using Docker)
sudo systemctl start postgresql
```

#### 5. Verify Setup
```bash
# Test API health
curl http://localhost:5001/api/health

# Test dashboard
curl http://localhost:8081/health

# Run basic tests
npm test
```

### IDE Configuration

#### Visual Studio Code
**Recommended Extensions:**
- ES6 Mocha Snippets
- Prettier - Code formatter
- ESLint
- Docker
- Kubernetes
- GitLens

**Settings Configuration:**
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "eslint.validate": ["javascript", "typescript"],
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

#### IntelliJ IDEA/WebStorm
**Recommended Plugins:**
- Node.js
- Docker
- Kubernetes
- Prettier
- ESLint

## Project Structure

```
agentic-reconciliation-engine/
├── core/                          # Core AI and infrastructure components
│   ├── ai/                       # AI-related services
│   │   ├── agents/              # AI agent implementations
│   │   ├── skills/              # AI skill definitions
│   │   ├── runtime/             # AI runtime orchestration
│   │   └── AGENTS.md            # Agent architecture documentation
│   ├── automation/              # Automation scripts and tools
│   │   ├── ci-cd/              # CI/CD pipeline configurations
│   │   ├── scripts/            # Utility scripts
│   │   └── testing/            # Test automation
│   └── config/                  # Configuration files
├── dashboard/                    # Dashboard application
│   ├── ui/                      # Frontend React application
│   ├── services/                # Backend dashboard services
│   └── overlay/                 # Kubernetes deployment overlays
├── docs/                        # Documentation
├── helm/                        # Helm charts for deployment
├── scripts/                     # Utility scripts
├── test/                        # Test files and configurations
├── docker-compose*.yaml         # Docker Compose configurations
├── package.json                 # Root package configuration
└── README.md                    # Project documentation
```

### Key Directories Explained

#### `core/ai/`
Contains all AI-related functionality:
- **agents/**: Individual AI agent implementations
- **skills/**: Reusable AI skills and capabilities
- **runtime/**: Orchestration and workflow management

#### `dashboard/`
Frontend and backend dashboard components:
- **ui/**: React-based frontend application
- **services/**: Node.js backend services for dashboard
- **overlay/**: Kubernetes deployment configurations

#### `core/automation/`
Infrastructure automation tools:
- **ci-cd/**: GitHub Actions and deployment pipelines
- **scripts/**: Utility scripts for various tasks
- **testing/**: Automated testing frameworks

## API Integration

### Authentication

#### JWT Token Generation
```javascript
const jwt = require('jsonwebtoken');

function generateToken(user) {
  return jwt.sign(
    {
      userId: user.id,
      username: user.username,
      role: user.role
    },
    process.env.JWT_SECRET,
    { expiresIn: '24h' }
  );
}
```

#### API Request with Authentication
```javascript
const axios = require('axios');

async function makeAuthenticatedRequest(endpoint, method = 'GET', data = null) {
  const token = await getStoredToken();

  const config = {
    method,
    url: `${process.env.API_BASE_URL}${endpoint}`,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  };

  if (data) {
    config.data = data;
  }

  try {
    const response = await axios(config);
    return response.data;
  } catch (error) {
    handleApiError(error);
    throw error;
  }
}
```

### Service Integration Patterns

#### External Service Integration
```javascript
class ExternalServiceIntegration {
  constructor(baseUrl, timeout = 30000) {
    this.baseUrl = baseUrl;
    this.timeout = timeout;
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: {
        'User-Agent': 'AI-Infrastructure-Portal/1.0'
      }
    });
  }

  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return {
        status: response.status === 200 ? 'healthy' : 'unhealthy',
        responseTime: response.config.metadata?.endTime - response.config.metadata?.startTime,
        version: response.data?.version
      };
    } catch (error) {
      return {
        status: 'unreachable',
        error: error.message
      };
    }
  }

  async getMetrics() {
    try {
      const response = await this.client.get('/metrics');
      return this.normalizeMetrics(response.data);
    } catch (error) {
      console.error(`Failed to fetch metrics from ${this.baseUrl}:`, error);
      return {};
    }
  }

  normalizeMetrics(rawMetrics) {
    // Normalize different metric formats to standard schema
    return {
      cpu: rawMetrics.cpu || 0,
      memory: rawMetrics.memory || 0,
      responseTime: rawMetrics.response_time || 0,
      errorRate: rawMetrics.error_rate || 0
    };
  }
}
```

#### Custom Service Implementation
```javascript
class CustomAIService extends ExternalServiceIntegration {
  constructor() {
    super(process.env.CUSTOM_AI_URL);
  }

  async analyzeInfrastructure(data) {
    const response = await this.client.post('/analyze', {
      infrastructure: data,
      analysisType: 'comprehensive'
    });

    return {
      recommendations: response.data.recommendations || [],
      riskScore: response.data.risk_score || 0,
      costSavings: response.data.cost_savings || 0
    };
  }

  async optimizeCosts(currentConfig) {
    const response = await this.client.post('/optimize', {
      configuration: currentConfig,
      constraints: {
        maxDowntime: '4h',
        budgetLimit: 10000
      }
    });

    return response.data.optimization_plan || {};
  }
}
```

### WebSocket Integration

#### Client-Side WebSocket Connection
```javascript
class RealtimeClient {
  constructor(apiUrl) {
    this.apiUrl = apiUrl;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
  }

  connect() {
    try {
      this.ws = new WebSocket(`${this.apiUrl.replace('http', 'ws')}/ws`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.subscribeToUpdates();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      this.handleReconnect();
    }
  }

  subscribeToUpdates() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['metrics', 'alerts', 'agents', 'services']
      }));
    }
  }

  handleMessage(data) {
    switch (data.type) {
      case 'metric_update':
        this.handleMetricUpdate(data.payload);
        break;
      case 'alert':
        this.handleAlert(data.payload);
        break;
      case 'agent_status':
        this.handleAgentUpdate(data.payload);
        break;
      case 'service_status':
        this.handleServiceUpdate(data.payload);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
      // Notify user of connection failure
      this.onConnectionFailed();
    }
  }

  // Override these methods in subclasses
  handleMetricUpdate(metrics) {}
  handleAlert(alert) {}
  handleAgentUpdate(agent) {}
  handleServiceUpdate(service) {}
  onConnectionFailed() {}
}
```

## Testing

### Unit Testing

#### Test Structure
```
test/
├── unit/                    # Unit tests
│   ├── api/                # API endpoint tests
│   ├── services/           # Service integration tests
│   └── utils/              # Utility function tests
├── integration/            # Integration tests
├── e2e/                    # End-to-end tests
└── fixtures/               # Test data fixtures
```

#### Example Unit Test
```javascript
const { expect } = require('chai');
const sinon = require('sinon');
const { HealthService } = require('../src/services/health.service');

describe('HealthService', () => {
  let healthService;
  let mockAxios;

  beforeEach(() => {
    mockAxios = sinon.stub();
    healthService = new HealthService({ axios: mockAxios });
  });

  afterEach(() => {
    sinon.restore();
  });

  describe('checkHealth()', () => {
    it('should return healthy status for successful response', async () => {
      mockAxios.get.resolves({
        status: 200,
        data: { status: 'ok' },
        config: { metadata: { startTime: 1000, endTime: 1050 } }
      });

      const result = await healthService.checkHealth('http://test-service.com');

      expect(result).to.deep.equal({
        status: 'healthy',
        responseTime: 50,
        service: 'test-service'
      });
    });

    it('should return unhealthy status for error response', async () => {
      mockAxios.get.rejects(new Error('Connection refused'));

      const result = await healthService.checkHealth('http://test-service.com');

      expect(result.status).to.equal('unhealthy');
      expect(result.error).to.include('Connection refused');
    });

    it('should handle timeout errors appropriately', async () => {
      mockAxios.get.rejects({ code: 'ECONNABORTED' });

      const result = await healthService.checkHealth('http://test-service.com');

      expect(result.status).to.equal('timeout');
    });
  });
});
```

### Integration Testing

#### API Integration Test
```javascript
const request = require('supertest');
const { expect } = require('chai');
const app = require('../src/app');

describe('API Integration Tests', () => {
  let server;
  let authToken;

  before(async () => {
    server = app.listen(0);

    // Get auth token for tests
    const authResponse = await request(app)
      .post('/auth/login')
      .send({ username: 'testuser', password: 'testpass' });

    authToken = authResponse.body.token;
  });

  after(() => {
    server.close();
  });

  describe('GET /api/health', () => {
    it('should return system health status', async () => {
      const response = await request(app)
        .get('/api/health')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body).to.have.property('status');
      expect(response.body).to.have.property('timestamp');
      expect(response.body.status).to.equal('healthy');
    });
  });

  describe('GET /api/services', () => {
    it('should return list of services', async () => {
      const response = await request(app)
        .get('/api/services')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body).to.be.an('array');
      expect(response.body.length).to.be.greaterThan(0);

      const service = response.body[0];
      expect(service).to.have.property('name');
      expect(service).to.have.property('status');
    });

    it('should support filtering by status', async () => {
      const response = await request(app)
        .get('/api/services?status=healthy')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      response.body.forEach(service => {
        expect(service.status).to.equal('healthy');
      });
    });
  });
});
```

### End-to-End Testing

#### E2E Test Example
```javascript
const puppeteer = require('puppeteer');
const { expect } = require('chai');

describe('Dashboard E2E Tests', () => {
  let browser;
  let page;

  before(async () => {
    browser = await puppeteer.launch();
    page = await browser.newPage();
  });

  after(async () => {
    await browser.close();
  });

  it('should load dashboard and display metrics', async () => {
    await page.goto('http://localhost:8081');

    // Wait for dashboard to load
    await page.waitForSelector('.dashboard-container');

    // Check if metrics are displayed
    const cpuMetric = await page.$('.metric-cpu');
    expect(cpuMetric).to.not.be.null;

    // Verify real-time updates
    const initialValue = await page.$eval('.metric-cpu .value', el => el.textContent);

    // Wait for update (assuming 5-second interval)
    await page.waitForTimeout(6000);

    const updatedValue = await page.$eval('.metric-cpu .value', el => el.textContent);
    expect(updatedValue).to.not.equal(initialValue);
  });

  it('should handle user authentication', async () => {
    await page.goto('http://localhost:8081/login');

    // Fill login form
    await page.type('#username', 'testuser');
    await page.type('#password', 'testpass');
    await page.click('#login-button');

    // Wait for redirect to dashboard
    await page.waitForNavigation();
    expect(page.url()).to.include('/dashboard');
  });

  it('should support real-time WebSocket updates', async () => {
    await page.goto('http://localhost:8081');

    // Listen for WebSocket messages
    let wsMessageReceived = false;
    page.on('response', response => {
      if (response.url().includes('/ws')) {
        wsMessageReceived = true;
      }
    });

    // Wait for WebSocket connection and message
    await page.waitForTimeout(10000);
    expect(wsMessageReceived).to.be.true;
  });
});
```

### Running Tests

#### Test Commands
```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- test/unit/api/health.test.js
```

#### Test Configuration
```javascript
// jest.config.js or mocha.opts
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/test/**/*.test.js'],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/test/setup.js']
};
```

## Contributing Guidelines

### Code Style

#### JavaScript Style Guide
```javascript
// Use ES6+ features
const arrowFunction = (param) => {
  return param * 2;
};

// Use async/await for asynchronous code
async function fetchData() {
  try {
    const response = await axios.get('/api/data');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch data:', error);
    throw error;
  }
}

// Use destructuring
const { data, status } = await apiCall();

// Use template literals
const message = `User ${user.name} has ${user.points} points`;

// Use const/let instead of var
const PI = 3.14159;
let counter = 0;
```

#### Naming Conventions
- **Files**: kebab-case (e.g., `health-service.js`)
- **Classes**: PascalCase (e.g., `HealthService`)
- **Functions/Methods**: camelCase (e.g., `checkHealth()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)
- **Variables**: camelCase (e.g., `userData`)

### Commit Guidelines

#### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

#### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes
- **refactor**: Code refactoring
- **test**: Test additions/modifications
- **chore**: Maintenance tasks

#### Examples
```bash
feat(auth): add JWT token refresh functionality

fix(api): resolve memory leak in metrics endpoint

docs(readme): update installation instructions

test(metrics): add unit tests for CPU monitoring

refactor(services): extract common functionality to base class
```

### Pull Request Process

#### PR Checklist
- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Reviewed by at least one maintainer

#### PR Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No breaking changes
```

### Code Review Guidelines

#### For Reviewers
- Focus on code quality, not personal preferences
- Provide constructive feedback
- Suggest improvements, don't dictate
- Approve when requirements are met

#### For Contributors
- Address all review comments
- Explain reasoning for controversial changes
- Keep discussions professional
- Don't take feedback personally

## Deployment

### Development Deployment
```bash
# Deploy to dev environment
npm run deploy:dev

# Check deployment status
kubectl get pods -n ai-infrastructure-dev
```

### Staging Deployment
```bash
# Deploy to staging
npm run deploy:staging

# Run smoke tests
npm run test:smoke
```

### Production Deployment
```bash
# Deploy to production (requires approval)
npm run deploy:prod

# Monitor deployment
kubectl rollout status deployment/ai-infrastructure-portal -n ai-infrastructure
```

## Troubleshooting

### Common Development Issues

#### Port Conflicts
```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 <PID>

# Or use different port
export API_PORT=5002
```

#### Dependency Issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear npm cache
npm cache clean --force
```

#### Database Connection Issues
```bash
# Test database connection
npm run db:test

# Reset database
npm run db:reset

# Check database logs
kubectl logs -l app=postgres -n ai-infrastructure
```

### Debugging Techniques

#### Debug Logging
```javascript
// Enable debug logging
process.env.DEBUG = 'ai-portal:*';

// Use debug library
const debug = require('debug')('ai-portal:api');

debug('Processing request for user %s', userId);
```

#### Remote Debugging
```bash
# Start application with debug port
node --inspect=0.0.0.0:9229 app.js

# Connect with Chrome DevTools
# Open chrome://inspect and click "Open dedicated DevTools for Node"
```

#### Performance Profiling
```bash
# Generate CPU profile
node --prof app.js

# Analyze profile
node --prof-process isolate-*.log > profile.txt
```

## Security Best Practices

### Code Security
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Secure headers implementation

### Infrastructure Security
- Least privilege access
- Network segmentation
- Regular security updates
- Secret management
- Audit logging

### Development Security
- Dependency vulnerability scanning
- Code security analysis
- Secret detection in CI/CD
- Secure coding practices
- Regular security training

## Performance Optimization

### Code Optimization
- Efficient algorithms and data structures
- Memory management
- Caching strategies
- Database query optimization
- Async/await best practices

### Infrastructure Optimization
- Load balancing
- Auto-scaling
- Resource limits and requests
- CDN usage
- Database indexing

### Monitoring and Profiling
- Performance metrics collection
- Memory leak detection
- Slow query identification
- Bottleneck analysis
- Capacity planning

---

## Support and Resources

### Getting Help
- **Documentation**: Comprehensive guides and API references
- **Community**: GitHub discussions and community forums
- **Support**: Dedicated support channels for enterprise customers
- **Training**: Video tutorials and workshops

### Additional Resources
- [API Reference](API_REFERENCE.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT_RUNBOOK.md)
- [Security Guide](SECURITY_GUIDE.md)

---

**Version**: 1.0.0
**Last Updated**: January 15, 2024
**Document ID**: DG-AIP-2024-001
