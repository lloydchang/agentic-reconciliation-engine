# Directory Restructure Summary

## Changes Made

### Before
```
├── ai-core/ai/runtime/                    # Temporal AI orchestration code
│   ├── backend/                  # Go Temporal workflows and activities
│   ├── cli/                      # Command-line interface
│   └── tools/                    # Tool permissions and configurations
├── dashboard-frontend/           # React dashboard and WebMCP client
```

### After
```
├── core/ai/runtime/                       # Agent runtime implementation
│   ├── backend/                  # Go Temporal workflows and activities
│   ├── dashboard/                # React dashboard and WebMCP client
│   ├── cli/                      # Command-line interface
│   └── tools/                    # Tool permissions and configurations
```

## Rationale

1. **Cleaner naming**: `core/ai/runtime/` is more concise than `ai-core/ai/runtime/`
2. **Logical grouping**: All agent-related code in one directory
3. **Clear hierarchy**: `core/ai/runtime/dashboard/` shows it's the UI for agents
4. **Avoids redundancy**: Dashboard is inherently a frontend, no need for `-frontend` suffix
5. **Scalable structure**: Room for future agent components

## Updated References

- Documentation updated to use new paths
- Import statements may need updating
- Deployment configurations should reference new locations
- API proxy configuration in Vite config remains the same

## Benefits

- ✅ More intuitive directory structure
- ✅ Cleaner naming conventions
- ✅ Better organization for future growth
- ✅ Eliminates naming redundancy
- ✅ Maintains clear separation from `core/ai/skills/` (skill definitions)
