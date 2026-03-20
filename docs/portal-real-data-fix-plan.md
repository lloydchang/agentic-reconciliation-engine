## Portal real-data fix plan (no fake metrics)

### What’s wrong today
1. `core/ai/portal/server.py` serves `enhanced-index.html` at `http://localhost:9001/`.
2. `core/ai/portal/enhanced-index.html` checks each service by doing `fetch(..., { method: "HEAD" })` against the service root URL (e.g. `http://localhost:8080/`), which fails because many services:
   - don’t implement `HEAD` (405 Method Not Allowed)
   - don’t have a root route (404 Not Found)
   - may not be running (connection refused)
3. The portal then displays metrics (“Success Rate”, “Skills Executed”, “Avg Response Time”) using `Math.random()` and a static activity feed, so it can’t be “real data”.

### Implementation approach
Update only the frontend portal page to:
1. Stop issuing `HEAD` probes to service roots.
2. Fetch real status + metrics from the already-existing “real backend” service on port `8080`:
   - `GET http://localhost:8080/api/core/ai/runtime/status` (for `active_agents`)
   - `GET http://localhost:8080/api/system/health` (for per-service `running/offline` plus computed `issues`)
3. Compute “Success Rate” deterministically from real service status:
   - `success_rate = online_services / total_services * 100`
4. Remove `Math.random()` from the portal entirely.
5. Replace the “Recent Activity” list with items derived from real health `issues` (so activity is not hardcoded).
6. If the real backend endpoints fail, show `N/A` (or `offline`) rather than fake values.

### Files to change
1. `core/ai/portal/enhanced-index.html`

### Acceptance criteria
1. Browser console should no longer show `HEAD http://localhost:<port>/` failures.
2. “Online/Offline/Health %” and “Active Agents” should reflect backend responses.
3. No random/fake metrics are generated client-side.

