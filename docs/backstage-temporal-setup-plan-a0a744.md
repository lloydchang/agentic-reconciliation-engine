# Backstage-Temporal Repository Scaffold Plan

This plan will fully scaffold a private GitHub repository integrating Backstage (TypeScript) and Temporal (Go) with Dockerized environments, sample workflows, plugin integration, and local development scripts.

## Phase 1: Repository Setup & Structure
- **Repository Initialization**: Create GitHub repo, add README, .gitignore, LICENSE
- Create directory structure: backend/, frontend/, scripts/, docs/
- Set up initial git commit and push

## Phase 2: Temporal Worker Setup
- Initialize Go module with Temporal SDK
- **Temporal Worker Setup**: Create sample workflow and activities, Dockerfile, docker-compose.yml
- Implement HelloBackstageWorkflow with FetchDataActivity and ProcessDataActivity
- Add logging and retry policies
- Create Dockerfile for the worker
- Set up docker-compose.yml with Temporal server, UI, and PostgreSQL
- Add HTTP endpoints: POST /workflow/start, GET /workflow/status

## Phase 3: Backstage App & Plugin
- **Backstage App & Plugin**: Create Backstage app, add temporal-integration plugin with UI for triggering and viewing workflows
- Create Backstage app using @backstage/create-app
- Develop temporal-integration plugin with:
  - Workflow trigger button
  - Workflow status table
  - Optional logs view
- Configure connection to Temporal backend (REST/gRPC)

## Phase 4: Integration & Testing
- **Integration**: Implement backend endpoints and frontend calls for workflow management
- Connect frontend plugin to backend endpoints
- Implement end-to-end workflow validation
- Test complete workflow execution flow

## Phase 5: Development Tooling & Scripts
- **Scripts**: Create dev.sh and build.sh for local development and building
- Create /scripts/dev.sh for starting Temporal server and Backstage dev server
- Create /scripts/build.sh for building Docker images
- Add comprehensive documentation in README.md and /docs/

## Phase 6: Documentation & Extensions
- **Documentation**: Update README, add docs in /docs
- Update README with architecture diagram and setup instructions
- Add experimental notes and changelog to /docs/
- **Optional Extensions**: Add AI agent integration, multi-cloud hooks, GitHub Actions CI
- Prepare for optional extensions (AI agent integration, multi-cloud hooks, GitHub Actions CI)

## Technical Considerations & Notes
- Ensure Go, Node.js, Docker, Docker Compose are installed.
- Use Go 1.21-alpine for backend Docker image
- Implement proper error handling and logging
- Ensure Docker and Docker Compose compatibility
- Repo starts private; make public later if stable.
- Keep repository private initially per security best practices
- Validate end-to-end workflow functionality.
