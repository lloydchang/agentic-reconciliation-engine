# AI Agents Development Setup Guide

## Overview

This guide provides comprehensive instructions for setting up a complete development environment for the AI Agents ecosystem, including the dashboard frontend, API backend, and deployment infrastructure.

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux, or Windows (WSL2)
- **Memory**: 8GB+ RAM recommended
- **Storage**: 20GB+ free disk space
- **Network**: Internet connection for package downloads

### Required Tools

#### Core Development Tools
```bash
# Node.js (v18+ recommended)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# npm (comes with Node.js)
npm --version

# Python (3.9+)
python3 --version
pip3 --version

# Git
git --version
```

#### Container and Orchestration
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# kind (for local Kubernetes)
brew install kind  # macOS
# or
curl -Lo kind https://kind.sigs.k8s.io/dl/v0.17.0/kind-linux-amd64
chmod +x kind
sudo mv kind /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Optional Development Tools
```bash
# VS Code (recommended)
code --version

# Postman (for API testing)
# Download from https://www.postman.com/

# React Dev Tools (browser extension)
# Install from Chrome Web Store
```

## Repository Setup

### Clone Repository
```bash
# Clone the repository
git clone https://github.com/lloydchang/agentic-reconciliation-engine.git
cd agentic-reconciliation-engine

# Verify structure
ls -la
```

### Repository Structure
```
gitops-infra-core/operators/
├── dashboard-frontend/          # React dashboard application
├── api-server.py               # Flask API server
├── core/scripts/automation/                    # Deployment and utility scripts
├── docs/                       # Documentation
├── core/ai/skills/                    # Agent skill definitions
├── ai-core/ai/runtime/                  # Backend agent implementations
├── core/resources/             # Kubernetes manifests
└── core/operators/             # GitOps configurations
```

## Frontend Development Setup

### Dashboard Frontend (React)
```bash
# Navigate to frontend directory
cd dashboard-frontend

# Install dependencies
npm install

# Install additional required packages
npm install axios recharts @mui/material@^5.15.0 @mui/icons-material@^5.15.0

# Verify installation
npm list --depth=0

# Start development server
npm start

# Access at http://localhost:3000
```

### Frontend Environment Configuration
```bash
# Create environment file
cat > .env << EOF
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG=true
EOF

# For production
cat > .env.production << EOF
REACT_APP_API_URL=/api
REACT_APP_ENVIRONMENT=production
REACT_APP_DEBUG=false
EOF
```

### Frontend Development Workflow
```bash
# 1. Start development server
npm start

# 2. Run tests (if configured)
npm test

# 3. Build for production
npm run build

# 4. Lint code (if configured)
npm run lint

# 5. Type checking
npx tsc --noEmit
```

## Backend Development Setup

### API Server (FastAPI)
```bash
# Navigate to repository root
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine

# Install Python dependencies
pip3 install fastapi uvicorn[standard] pydantic

# Verify installation
python3 -c "import fastapi; print('FastAPI installed successfully')"

# Start API server
uvicorn api:app --host 0.0.0.0 --port 5000 --reload

# Access at http://localhost:5000
# Access interactive docs at http://localhost:5000/docs
```

### Backend Environment Configuration
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn[standard] pydantic python-dotenv

# Create environment file
cat > .env << EOF
FASTAPI_ENV=development
API_HOST=0.0.0.0
API_PORT=5000
EOF

# Start with environment
uvicorn api:app --host 0.0.0.0 --port 5000 --reload
```

### Backend Development Workflow
```bash
# 1. Start API server with auto-reload
uvicorn api:app --host 0.0.0.0 --port 5000 --reload

# 2. Test endpoints
curl http://localhost:5000/api/cluster-status
curl http://localhost:5000/api/core/ai/runtime/detailed

# 3. Access interactive documentation
open http://localhost:5000/docs
```

## Local Kubernetes Setup

### Create Kind Cluster
```bash
# Create kind cluster configuration
cat > kind-config.yaml << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
  - containerPort: 443
    hostPort: 443
  - containerPort: 3000
    hostPort: 3000
  - containerPort: 5000
    hostPort: 5000
  - containerPort: 7233
    hostPort: 7233
EOF

# Create cluster
kind create cluster --name gitops-hub --config kind-config.yaml

# Verify cluster
kubectl cluster-info --context kind-gitops-hub
kubectl get nodes
```

### Kubernetes Development Tools
```bash
# Install kubectx for context switching
brew install kubectx  # macOS
# or clone from GitHub for Linux

# Install stern for log tailing
brew install stern  # macOS
# or download binary

# Install lens for GUI (optional)
# Download from https://k8slens.dev/
```

### Namespace Setup
```bash
# Create development namespace
kubectl create namespace ai-infrastructure

# Set default namespace
kubectl config set-context --current --namespace=ai-infrastructure

# Verify
kubectl get namespaces
```

## Integrated Development Workflow

### Start Complete Development Environment
```bash
# Terminal 1: Start API server
cd /Users/lloyd/github/antigravity/agentic-reconciliation-engine
python api-server.py

# Terminal 2: Start frontend
cd dashboard-frontend
npm start

# Terminal 3: Kubernetes operations
kubectl get pods -n ai-infrastructure
kubectl logs -f deployment/agent-dashboard -n ai-infrastructure
```

### Development Commands Reference
```bash
# Frontend commands
cd dashboard-frontend
npm start                    # Start dev server
npm run build               # Build for production
npm test                    # Run tests
npm run lint                # Lint code

# Backend commands
python api-server.py        # Start API server
curl http://localhost:5000/api/cluster-status  # Test API

# Kubernetes commands
kubectl get pods -n ai-infrastructure
kubectl get services -n ai-infrastructure
kubectl logs -f deployment/agent-dashboard -n ai-infrastructure
kubectl port-forward svc/agent-dashboard-service 8080:80 -n ai-infrastructure
```

## Code Quality and Testing

### Frontend Testing Setup
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event

# Configure Jest (package.json)
{
  "scripts": {
    "test": "react-scripts test",
    "test:coverage": "react-scripts test --coverage --watchAll=false"
  }
}

# Run tests
npm test
npm run test:coverage
```

### Backend Testing Setup
```bash
# Install testing dependencies
pip install pytest pytest-flask

# Create test file
cat > test_api.py << EOF
import pytest
from api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_cluster_status(client):
    response = client.get('/api/cluster-status')
    assert response.status_code == 200
    assert 'status' in response.json
EOF

# Run tests
pytest test_api.py -v
```

### Code Quality Tools
```bash
# Frontend linting
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npx eslint src/

# Backend linting
pip install flake8 black
flake8 api-server.py
black api-server.py

# Pre-commit hooks
pip install pre-commit
pre-commit install
```

## Debugging Setup

### Frontend Debugging
```bash
# 1. Install React Dev Tools browser extension
# 2. Open browser dev tools
# 3. Use React Dev Tools tab for component inspection
# 4. Use Console tab for error debugging
# 5. Use Network tab for API debugging

# Debug configuration (VS Code)
cat > .vscode/launch.json << EOF
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug React App",
      "type": "node",
      "request": "launch",
      "cwd": "\${workspaceFolder}/dashboard-frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["start"]
    }
  ]
}
EOF
```

### Backend Debugging
```bash
# Python debugging with pdb
python -m pdb api-server.py

# VS Code Python debugging
cat > .vscode/launch.json << EOF
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Flask App",
      "type": "python",
      "request": "launch",
      "program": "\${workspaceFolder}/api-server.py",
      "console": "integratedTerminal",
      "env": {
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      }
    }
  ]
}
EOF
```

### Kubernetes Debugging
```bash
# Port forwarding for local debugging
kubectl port-forward svc/agent-dashboard-service 8080:80 -n ai-infrastructure
kubectl port-forward svc/dashboard-api-service 5000:5000 -n ai-infrastructure

# Log debugging
kubectl logs -f deployment/agent-dashboard -n ai-infrastructure
kubectl logs -f deployment/dashboard-api -n ai-infrastructure

# Exec into pod for debugging
kubectl exec -it deployment/agent-dashboard -n ai-infrastructure -- /bin/sh
```

## Performance Monitoring

### Frontend Performance
```bash
# Install performance monitoring tools
npm install --save-dev webpack-bundle-analyzer

# Analyze bundle size
npm run build
npx webpack-bundle-analyzer build/static/js/*.js

# Lighthouse audit
# Install Lighthouse CLI
npm install -g lighthouse
lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html
```

### Backend Performance
```bash
# Install performance monitoring
pip install flask-profiler

# Add to api-server.py
from flask_profiler import Profiler

app.config["PROFILER"] = {
    "enabled": True,
    "storage": {
        "engine": "sqlite",
        "FILE": "profiler.db"
    },
    "basicAuth": {
        "enabled": True,
        "username": "admin",
        "password": "password"
    }
}

Profiler(app)
```

## Environment-Specific Setup

### macOS Setup
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install tools with Homebrew
brew install node python3 kubectl helm kind docker

# Set up shell environment
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Linux Setup (Ubuntu/Debian)
```bash
# Update package manager
sudo apt update

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python
sudo apt-get install python3 python3-pip python3-venv

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Windows Setup (WSL2)
```powershell
# Enable WSL2
wsl --install

# Install Ubuntu from Microsoft Store
wsl --set-default-version Ubuntu

# Inside WSL2 Ubuntu terminal
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip

# Install Docker Desktop for Windows
# Download from https://www.docker.com/products/docker-desktop

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/windows/amd64/kubectl.exe"
```

## IDE Configuration

### VS Code Setup
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension ms-kubernetes-tools.vscode-kubernetes-tools

# Create workspace settings
cat > .vscode/settings.json << EOF
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/node_modules": true,
    "**/build": true,
    "**/.git": true
  }
}
EOF
```

### VS Code Tasks
```bash
# Create tasks configuration
cat > .vscode/tasks.json << EOF
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Frontend",
      "type": "shell",
      "command": "npm",
      "args": ["start"],
      "options": {
        "cwd": "\${workspaceFolder}/dashboard-frontend"
      },
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    },
    {
      "label": "Start Backend",
      "type": "shell",
      "command": "python",
      "args": ["api-server.py"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "new"
      }
    }
  ]
}
EOF
```

## Git Configuration

### Git Hooks Setup
```bash
# Install pre-commit hooks
pip install pre-commit
npm install --save-dev husky

# Configure pre-commit
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        files: ^.*\.py$

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.30.0
    hooks:
      - id: eslint
        files: ^dashboard-frontend/.*\.(js|ts|tsx)$
        additional_dependencies:
          - eslint@8.30.0
          - "@typescript-eslint/eslint-plugin@5.48.1"
EOF

pre-commit install
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/dashboard-improvements

# Make changes
git add .
git commit -m "feat: improve dashboard performance"

# Push and create PR
git push origin feature/dashboard-improvements
```

## Troubleshooting Development Issues

### Common Frontend Issues
```bash
# Module not found errors
npm install <missing-package>

# Port already in use
lsof -ti:3000 | xargs kill -9
npm start

# TypeScript errors
npx tsc --noEmit
# Fix type errors in code

# Build failures
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Common Backend Issues
```bash
# Python module not found
pip install <missing-package>

# Port conflicts
lsof -ti:5000 | xargs kill -9
python api-server.py

# Flask debug mode not working
export FLASK_ENV=development
export FLASK_DEBUG=1
python api-server.py
```

### Common Kubernetes Issues
```bash
# Cluster not accessible
kubectl config view
kubectl config use-context kind-gitops-hub

# Pod not starting
kubectl describe pod <pod-name> -n ai-infrastructure
kubectl logs <pod-name> -n ai-infrastructure

# Service not accessible
kubectl get endpoints -n ai-infrastructure
kubectl port-forward svc/<service-name> 8080:80 -n ai-infrastructure
```

## Best Practices

### Development Best Practices
1. **Use version control** for all code changes
2. **Write tests** for new features
3. **Follow code style** guidelines
4. **Document changes** in commit messages
5. **Use environment variables** for configuration
6. **Keep dependencies updated** but stable
7. **Monitor performance** regularly
8. **Use debugging tools** effectively

### Security Best Practices
1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Validate inputs** in both frontend and backend
4. **Use HTTPS** in production
5. **Keep dependencies updated** for security patches
6. **Use CORS** properly on API servers
7. **Implement authentication** for production systems

### Performance Best Practices
1. **Optimize bundle size** for frontend
2. **Use caching** strategies appropriately
3. **Monitor resource usage** in development
4. **Profile performance** bottlenecks
5. **Use lazy loading** for large components
6. **Implement efficient data fetching**
7. **Minimize re-renders** in React components

## Next Steps

After completing the development setup:

1. **Explore the codebase** to understand the architecture
2. **Run the complete ecosystem** using the deployment script
3. **Make your first changes** to the dashboard or API
4. **Test your changes** locally before deployment
5. **Contribute back** to the project with improvements

---

**Last Updated**: 2026-03-16  
**Version**: 1.0.0  
**Maintainer**: AI Agents Development Team
