# AI Agent Deployment & Crossplane Resolution

This walkthrough demonstrates the fixes for the AI agent deployments.

## Changes Made

### 🛠️ Common Fixes
- **Resource Optimization**: Reduced CPU/memory for all agents to fit the Kind cluster.
- **Image Load**: Built Docker images locally and loaded into the `kind-agentic-test` cluster.
- **ConfigMap Size**: Applied `agent-skills-configmap` with `--server-side` for 100+ skills.

### 🧠 Memory Selector [READY]
- **Status**: `Running` (1/1)
- **Fixes**: Fixed Kustomization, reduced replicas to 1, loaded image.

### 🏗️ Standalone Backend [READY]
- **Status**: `Running` (1/1)
- **Fixes**: Fixed import paths, aligned port (8081), fixed `SKILLS_PATH`/`PORT` env vars.

### 🤖 Autonomous Decision Engine (ADE) [FIXED ✅]
- **Root Cause**: `panic: open /root/autonomous-decision-engine: permission denied`
  - The Temporal SDK's `getBinaryChecksum()` reads the running binary to compute a SHA256 checksum used for worker versioning.
  - The binary was in `/root/` (owned by `root`) but the process ran as `autonomous` (uid 1001), so it could not read the file.
- **Fix** (in [Dockerfile](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/runtime/standalone/backend/Dockerfile)):
  - Changed `WORKDIR` from `/root/` to `/app/`
  - Used `COPY --chown=autonomous:autonomous` to give the non-root user ownership
  - Created the user _before_ the `COPY` instruction so `--chown` resolves correctly
  - Used absolute path `/app/autonomous-decision-engine` in `CMD`

## Verification

```bash
kubectl get pods -n ai-infrastructure -l layer=ai-agents
```

| Agent | Status |
|---|---|
| Memory Selector | ✅ Running (1/1) |
| Standalone Backend | ✅ Running (1/1) |
| ADE | ✅ Worker started (`INFO Started Worker`) |

**ADE Worker log:**
```
INFO Started Worker Namespace default TaskQueue autonomous-decision-engine WorkerID 1@autonomous-decision-engine-84f94b575d-kr59t@
```

## Next Steps
- Configure Crossplane with actual cloud credentials when available.
- Clean up debug `DEBUG:` print statements from [main.go](file:///Users/lloyd/github/claude-code/agentic-reconciliation-engine/core/ai/runtime/standalone/backend/main.go) (added during panic investigation).
