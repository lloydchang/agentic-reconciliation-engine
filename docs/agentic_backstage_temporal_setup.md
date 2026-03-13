# Agentic AI Implementation Instructions for Backstage-Temporal Sandbox

**Goal**: Fully scaffold a private/public GitHub repository integrating Backstage (TypeScript) and Temporal (Go) for experimentation. Includes Dockerized environments, sample workflows, Backstage plugin integration, and local dev scripts.

## Repository Initialization

Create GitHub repo: `backstage-temporal`

- Private initially (can be made public later)

Initialize with:

- README.md describing project purpose
- .gitignore for Go and Node.js/TypeScript
- LICENSE Apache 2.0

### Commands

```bash
gh repo create backstage-temporal --private
echo "# Backstage + Temporal Sandbox" > README.md
curl -o LICENSE https://www.apache.org/licenses/LICENSE-2.0.txt
npx gitignore node,go > .gitignore
git add .
git commit -m "Initial repo setup with README, license, and .gitignore"
git push -u origin main
```

## Directory Structure

```
/backend        # Temporal worker code (Go)
/frontend       # Backstage app + plugin (TypeScript)
/scripts        # Dev and build automation scripts
/docs           # Architecture, notes, diagrams
```

### Commands

```bash
mkdir backend frontend scripts docs
```

## Temporal Worker Setup (Go)

Initialize Go module:

```bash
cd backend
go mod init github.com/yourusername/backstage-temporal/backend
go get go.temporal.io/sdk
```

Create sample workflow: `HelloBackstageWorkflow`

Create sample activities: `FetchDataActivity`, `ProcessDataActivity`

- Logging enabled, basic retry policy implemented

### Dockerfile

```dockerfile
FROM golang:1.21-alpine
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o worker .
CMD ["./worker"]
```

Add docker-compose.yml for Temporal server + UI + Postgres/MySQL

## Backstage App & Plugin (TypeScript)

Create Backstage app:

```bash
cd ../frontend
npx @backstage/create-app
```

Add plugin: `temporal-integration`

Implement:

- Button to trigger workflows
- Table for workflow status
- Optional logs view

Connect to Temporal backend via REST or gRPC

## Integration

Backend exposes workflow endpoints:

- POST `/workflow/start`
- GET `/workflow/status`

Frontend plugin calls these endpoints

Validate end-to-end sample workflow

## Local Development Scripts (/scripts)

### dev.sh

```bash
#!/bin/bash
# Start Temporal server & Backstage dev server
docker-compose -f ../backend/docker-compose.yml up -d
cd ../frontend
yarn dev
```

### build.sh

```bash
#!/bin/bash
# Build Docker images for backend and frontend
docker build -t backstage-temporal-backend ./backend
docker build -t backstage-temporal-frontend ./frontend
```

## Documentation

README.md includes:

- Purpose and architecture diagram
- Local development instructions
- Example workflow triggers

/docs/ contains:

- Experimental notes
- Changelog

## Optional Extensions

- AI agent integration for orchestrating Temporal workflows
- Multi-cloud hooks (AWS Proton, Azure Foundry) for future testing
- GitHub Actions for CI: linting, tests, build verification

## Execution Notes

- Ensure Go and Node.js are installed
- Docker and Docker Compose are required
- Plugin communication with Temporal can use either REST gateway or Temporal SDK
- Keep initial repo private until integration experiments are stable

---

*This instruction set is ready for feeding into an agentic AI coding agent to scaffold a working prototype.*
