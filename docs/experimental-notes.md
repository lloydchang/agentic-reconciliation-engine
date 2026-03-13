# Experimental Notes

This is an experimental sandbox for Backstage and Temporal integration.

Key points:
- Backend worker on port 8081 with /workflow/start and /workflow/status endpoints
- Temporal UI on 8080, server on 7233
- PostgreSQL for persistence
- Docker Compose for infrastructure

Future experiments:
- AI agent integration: Placeholder for orchestrating Temporal workflows via AI agents.
- Multi-cloud hooks: Placeholder for hooks to AWS Proton, Azure Foundry.
- GitHub Actions CI: Implemented basic CI workflow for linting, tests, and builds.
