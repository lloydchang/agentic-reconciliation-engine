# AI Infrastructure Portal - Developer Setup Guide

This guide helps developers set up their environment for contributing to the AI Infrastructure Portal.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Project Structure](#project-structure)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Contributing](#contributing)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Node.js**: v16.0+ (v18+ recommended)
- **npm**: v7+ (comes with Node.js)
- **Git**: v2.25+
- **Docker**: v20.10+ (optional, for containerized development)
- **Docker Compose**: v2.0+ (optional)

### System Requirements

- **OS**: macOS, Linux, or Windows (WSL2)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 5GB free space
- **Network**: Internet connection for dependencies

### Installation

#### macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node

# Install Docker (optional)
brew install --cask docker
```

#### Ubuntu/Debian

```bash
# Update package index
sudo apt update

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Docker (optional)
sudo apt install docker.io docker-compose
```

#### Windows

```powershell
# Install Node.js from https://nodejs.org/
# Or use Chocolatey
choco install nodejs

# Install Docker Desktop from https://www.docker.com/products/docker-desktop
```

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine
```

### 2. Install Dependencies

```bash
# Install all dependencies
npm install

# Verify installation
node --version
npm --version
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your settings
# For development, defaults should work
```

### 4. Start Development Services

#### Option A: Bare Metal (Recommended for development)

```bash
# Start the API server
npm run dev:api

# In another terminal, start the dashboard
npm run dev:dashboard
```

#### Option B: Docker Compose

```bash
# Start all services with Docker Compose
docker-compose -f docker-compose-portal.yaml up -d

# View logs
docker-compose -f docker-compose-portal.yaml logs -f
```

### 5. Verify Setup

```bash
# Test API health
curl http://localhost:5001/api/health

# Test dashboard
open http://localhost:8081

# Run tests
npm test
```

## Project Structure

```
agentic-reconciliation-engine/
├── core/                          # Core ARE components
│   ├── ai/
│   │   ├── skills/               # SKILL.md definitions
│   │   ├── AGENTS.md             # Agent specifications
│   │   └── runtime/              # Agent runtime
│   └── scripts/automation/       # Quickstart scripts
├── dashboard/                     # Dashboard components
│   ├── ui/                       # Frontend React/Vue
│   └── services/                 # Dashboard backend
├── docs/                         # Documentation
├── helm/                         # Kubernetes Helm charts
├── overlay/                      # K8s overlays for environments
├── core/                         # Core AI and infrastructure components
│   ├── ai/                       # AI-related services and tools
│   │   ├── portal/               # Portal-specific files
│   │   └── skills/               # AI skill definitions
│   └── automation/               # Automation scripts and tools
├── scripts/                      # Utility scripts
├── test/                         # Test files
├── real-data-api.js             # Main API server
├── real-dashboard-server.js     # Dashboard server
├── service-integrator.js        # External service integrations
├── test-suite.js                # Comprehensive testing suite
├── docker-compose-portal.yaml   # Docker Compose config
└── package.json                 # Node.js dependencies
```

### Key Files

- **`real-data-api.js`**: Main API server with all endpoints
- **`real-dashboard-server.js`**: Dashboard web server
- **`service-integrator.js`**: External service integration framework
- **`test-suite.js`**: Comprehensive testing suite
- **`AGENTS.md`**: Agent architecture specifications
- **`docs/`**: All documentation

## Development Workflow

### 1. Create a Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Push the branch
git push -u origin feature/your-feature-name
```

### 2. Make Changes

```bash
# Start development servers
npm run dev

# Make your changes...
# Test your changes...
```

### 3. Run Tests

```bash
# Run all tests
npm test

# Run specific test suite
npm run test:api
npm run test:integration

# Run linting
npm run lint
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new endpoint for service metrics

- Added GET /api/services/{id}/metrics endpoint
- Updated service-integrator.js to include metrics collection
- Added tests for new endpoint
- Updated API documentation"

# Push changes
git push
```

### 5. Create Pull Request

1. Go to GitHub and create a PR
2. Fill out the PR template
3. Request review from maintainers
4. Address review feedback

### Development Scripts

```json
{
  "scripts": {
    "dev": "concurrently \"npm run dev:api\" \"npm run dev:dashboard\"",
    "dev:api": "nodemon real-data-api.js",
    "dev:dashboard": "nodemon real-dashboard-server.js",
    "test": "node test-suite.js",
    "test:api": "node test-suite.js --api-only",
    "test:integration": "node test-suite.js --integration-only",
    "lint": "eslint *.js **/*.js",
    "format": "prettier --write *.js **/*.js",
    "build": "npm run build:api && npm run build:dashboard",
    "start": "npm run start:api & npm run start:dashboard"
  }
}
```

## Testing

### Running Tests

```bash
# Run full test suite
node test-suite.js

# Run with verbose output
node test-suite.js --verbose

# Run specific test categories
node test-suite.js --only api
node test-suite.js --only integration
node test-suite.js --only security
```

### Test Structure

The test suite includes:

- **API Tests**: All REST endpoints
- **Data Validation**: Response structure validation
- **Integration Tests**: External service connections
- **Security Tests**: Input validation and basic security
- **Performance Tests**: Response times and load testing
- **End-to-End Tests**: Complete data flow validation

### Writing Tests

Tests are written in the `test-suite.js` file. Add new test methods following the existing pattern:

```javascript
async runYourNewTest() {
  this.log('🧪 Starting Your New Test', 'info');

  // Your test logic here
  const result = await this.testEndpoint('/api/your-endpoint', 200, 'Test description');

  if (result) {
    this.log('✓ Your test passed', 'success');
    this.results.passed++;
  } else {
    this.log('✗ Your test failed', 'error');
    this.results.failed++;
  }

  this.log('✅ Your New Test Completed', 'info');
}
```

### Test Coverage

Current test coverage includes:
- ✅ API endpoint availability
- ✅ Data structure validation
- ✅ Service integration mocking
- ✅ Security input validation
- ✅ Performance benchmarking
- ✅ End-to-end data flow

## Contributing

### Code Style

We use ESLint and Prettier for code formatting:

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format
```

### Commit Convention

We follow conventional commits:

```bash
# Feature commits
git commit -m "feat: add new dashboard widget"

# Bug fixes
git commit -m "fix: resolve memory leak in metrics collection"

# Documentation
git commit -m "docs: update API reference for new endpoints"

# Refactoring
git commit -m "refactor: simplify agent status logic"
```

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Update** documentation if needed
6. **Commit** with conventional format
7. **Push** to your fork
8. **Create** a Pull Request
9. **Address** review feedback
10. **Merge** when approved

### Issue Reporting

When reporting bugs:

1. Use the bug report template
2. Include steps to reproduce
3. Provide environment details
4. Include relevant logs
5. Suggest a fix if possible

### Feature Requests

For new features:

1. Check existing issues first
2. Use the feature request template
3. Describe the problem it solves
4. Provide mockups or examples if applicable
5. Discuss implementation approach

## Troubleshooting

### Common Issues

#### Port Conflicts

```bash
# Check what's using the ports
sudo lsof -i :5001
sudo lsof -i :8081

# Change ports in .env
PORT=5002
DASHBOARD_PORT=8082
```

#### Dependencies Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Database Connection Issues

```bash
# For Temporal/PostgreSQL issues
docker-compose -f docker-compose-portal.yaml down
docker-compose -f docker-compose-portal.yaml up -d postgres

# Check database logs
docker-compose -f docker-compose-portal.yaml logs postgres
```

#### Permission Issues

```bash
# Fix npm permissions (Linux/Mac)
sudo chown -R $(whoami) ~/.npm

# Or use nvm for Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### Getting Help

- **Documentation**: Check `docs/` directory first
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Slack**: Join our community Slack (if available)

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variable
export DEBUG=ai-portal:*

# Or in .env
DEBUG=ai-portal:*

# Run with debug output
npm run dev:api
```

### Performance Profiling

```bash
# Use Node.js built-in profiler
node --prof real-data-api.js

# Analyze the output
node --prof-process isolate-*.log > profile.txt
```

### Logs Location

- **Application logs**: Console output when running directly
- **Docker logs**: `docker-compose logs -f ai-infrastructure-portal`
- **System logs**: `/var/log/syslog` or journalctl
- **Test results**: `test-results.json`

---

Happy coding! 🚀

For more information, see the main [README.md](../README.md) or visit our [documentation site](https://docs.ai-infrastructure-portal.dev).
