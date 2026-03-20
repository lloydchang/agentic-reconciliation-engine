## Goal
Make the portal “Skills Available” count come from real `core/ai/skills/*/SKILL.md` directories (not the hardcoded fallback list), so the UI reflects actual repository data.

## Current issue
`GET http://localhost:5000/api/skills` is served by `dashboard/services/real-data-api.js`.
That file builds `skillsDir` using `path.join(__dirname, 'core', 'ai', 'skills')`.
Because `__dirname` is `dashboard/services/`, this resolves to a non-existent folder and triggers the fallback hardcoded skills list.

## Approach
1. Fix the relative path used in `dashboard/services/real-data-api.js` (and optionally `dashboard/services/comprehensive-api.js`) so it correctly points to the repo-root `core/ai/skills` directory.
2. Keep the portal counting only `skillsPayload.skills.length` (a deterministic count), so even if other fields are placeholder/random, the count will be real.

## Files to change
- `dashboard/services/real-data-api.js`
  - `getAgentData()` and `getSkillsData()` should read skills from `../../core/ai/skills`.
- `dashboard/services/comprehensive-api.js` (optional but recommended for consistency)
  - `loadSkillsFromRepository()` should read skills from `../../core/ai/skills`.

## Acceptance criteria
1. `GET http://localhost:5000/api/skills` returns a `skills` array whose length matches the number of directories under `core/ai/skills` (no fallback list).
2. `http://localhost:9001/` shows “Skills Available” as the correct count and no longer drifts due to fallback behavior.

