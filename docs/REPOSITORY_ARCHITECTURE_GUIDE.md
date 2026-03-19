# Repository Architecture Guide

This document explains the current repository structure and the rationale behind the organization decisions.

## High-Level Architecture

The repository follows a clear separation of concerns with three main layers:

```
├── core/ai/skills/          # Skill definitions (agentskills.io)
├── core/ai/runtime/           # Runtime implementation
├── core/operators/    # Kubernetes infrastructure
├── core/resources/   # Cloud resources
└── docs/            # Documentation
```

## Directory Structure

### Core Components

#### `core/ai/skills/` - Skill Definitions
```
core/ai/skills/
├── [skill_name]/
│   ├── SKILL.md          # Skill definition with YAML frontmatter
│   ├── scripts/          # Optional executable code
│   ├── references/       # Documentation
│   └── assets/           # Templates/resources
└── README.md             # Skills framework overview
```

**Purpose**: Contains agent skill definitions following the [agentskills.io specification](https://agentskills.io/specification).

#### `core/ai/runtime/` - Runtime Implementation
```
core/ai/runtime/
├── backend/              # Go Temporal workflows and activities
├── dashboard/            # React dashboard UI
├── cli/                  # Command-line interface
├── tools/                # Tool permissions and configurations
└── docs/                 # Implementation documentation
```

**Purpose**: Runtime code for the agent system, including backend services and user interface.

#### `core/operators/` - Kubernetes Infrastructure
```
core/operators/
├── bootstrap/            # Cluster bootstrap configuration
├── capi/                 # Cluster API resources
├── consensus/            # A2A consensus implementation
└── monitoring/           # Infrastructure monitoring
```

**Purpose**: Kubernetes manifests and infrastructure for running the agent system.

#### `core/resources/` - Cloud Resources
```
core/resources/
├── ai-inference/         # AI model serving
├── flux/                 # GitOps configurations
├── monitoring/           # Application monitoring
└── fallback/             # Backup configurations
```

**Purpose**: Cloud provider resources and services.

### Supporting Directories

#### `docs/` - Documentation
```
docs/
├── developer-guide/      # Development documentation
├── user-guide/          # User documentation
├── legacy-configs/      # Historical configurations
└── [various guides].md  # Topic-specific documentation
```

#### `core/scripts/automation/` - Automation
```
core/scripts/automation/
├── debug/               # Debugging utilities
├── helpers/             # Helper functions
├── hub-clusters/        # Cluster setup scripts
└── maintenance/         # Maintenance automation
```

#### `overlay/examples/` - Reference Implementations
```
overlay/examples/
├── complete-hub-spoke/          # Full deployment example
├── complete-hub-spoke-temporal/ # Temporal integration
├── complete-hub-spoke-kagent/  # Kubernetes agent
└── complete-hub-spoke-consensus/ # Consensus layer
```

## Naming Conventions

### Directory Naming

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `kebab-case` | `dashboard-frontend` (old) | ❌ Avoided |
| `kebab-case` | `control-plane` | ✅ Infrastructure components |
| `singular` | `agents` | ✅ Logical groupings |
| `plural` | `scripts` | ✅ Collections of items |
| `dot-prefix` | `.agents` | ✅ Configuration/special directories |

### File Naming

| Type | Pattern | Example |
|------|---------|---------|
| Documentation | [TITLE.md](TITLE.md) | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) |
| Configuration | `config.yaml` | `cluster-config.yaml` |
| Scripts | `action.sh` | `setup-cluster.sh` |
| Components | `ComponentName.tsx` | `Dashboard.tsx` |

## Historical Evolution

### March 2026 Restructure

**Before**:
```
├── ai-core/ai/runtime/                    # Verbose naming
│   ├── backend/
│   ├── cli/
│   └── tools/
├── dashboard-frontend/           # Redundant suffix
```

**After**:
```
├── core/ai/runtime/                       # Clean naming
│   ├── backend/
│   ├── dashboard/                # Logical grouping
│   ├── cli/
│   └── tools/
```

**Rationale**:
1. **Eliminated redundancy** - Dashboard is inherently frontend
2. **Cleaner naming** - `agents` vs `ai-agents`
3. **Better organization** - Dashboard grouped with its backend
4. **Scalability** - Room for future agent components

### Vite Migration

The dashboard migrated from Create React App to Vite for:
- **Performance** - Faster development and builds
- **Modern tooling** - Latest ES features
- **Better DX** - Hot module replacement

## Design Principles

### 1. Clear Separation of Concerns

Each directory has a single, well-defined purpose:
- `core/ai/skills/` = Skill specifications
- `core/ai/runtime/` = Runtime implementation
- `core/operators/` = Kubernetes infrastructure
- `core/resources/` = Cloud resources

### 2. Logical Grouping

Related components are grouped together:
- `core/ai/runtime/dashboard/` with `core/ai/runtime/backend/`
- `core/operators/` with `core/resources/`

### 3. Scalability

Structure accommodates future growth:
- Room for new agent components in `core/ai/runtime/`
- Extensible infrastructure in `core/operators/`
- Modular documentation in `docs/`

### 4. Minimal Redundancy

Avoid unnecessary suffixes and prefixes:
- `dashboard` not `dashboard-frontend`
- `agents` not `ai-agents`
- `monitoring` not `monitoring-system`

## Integration Points

### API Connections

```
core/ai/runtime/dashboard (React UI)
    ↓ HTTP/WebSocket
core/ai/runtime/backend (Go API)
    ↓ gRPC/Protocol
Temporal Workflows
    ↓ Kubernetes API
core/operators/ (K8s resources)
```

### Data Flow

1. **User Interface** - `core/ai/runtime/dashboard/` provides web UI
2. **API Layer** - `core/ai/runtime/backend/` handles business logic
3. **Orchestration** - Temporal workflows coordinate agents
4. **Infrastructure** - Kubernetes manages deployment
5. **Skills** - `core/ai/skills/` defines agent capabilities

### Configuration Management

- **GitOps** - `flux/` manages infrastructure state
- **Skills** - `core/ai/skills/` defines agent behaviors
- **Environment** - `core/resources/` handles cloud-specific configs

## Best Practices

### Adding New Components

1. **Determine the layer** - Is it UI, backend, infrastructure, or docs?
2. **Choose appropriate directory** - Follow existing patterns
3. **Use consistent naming** - Follow conventions above
4. **Update documentation** - Keep docs in sync
5. **Consider dependencies** - Minimize cross-directory dependencies

### File Organization

1. **Group by feature** - Not by file type
2. **Keep related files together** - Components, tests, docs
3. **Use index files** - For clean imports
4. **Avoid deep nesting** - Keep structure flat

### Documentation

1. **Document decisions** - Explain architectural choices
2. **Keep guides current** - Update when structure changes
3. **Use examples** - Show how to use components
4. **Maintain CHANGELOG** - Track breaking changes

## Migration Guidelines

When restructuring:

1. **Plan carefully** - Consider all impacts
2. **Update references** - Fix all imports and links
3. **Test thoroughly** - Ensure nothing breaks
4. **Document changes** - Explain the rationale
5. **Communicate** - Let team know what changed

## Future Considerations

### Potential Improvements

1. **Monorepo tools** - Consider Nx or Lerna for large scale
2. **Package boundaries** - Define clear API contracts
3. **Automated testing** - Cross-directory integration tests
4. **Documentation generation** - Auto-generate from code

### Scalability

The current structure supports:
- **Multiple teams** working on different components
- **Independent deployment** of UI and backend
- **Cloud-agnostic** infrastructure
- **Extensible skill system**

## Conclusion

This architecture provides:

- ✅ **Clear organization** - Easy to understand and navigate
- ✅ **Scalable structure** - Room for growth
- ✅ **Minimal complexity** - No unnecessary abstractions
- ✅ **Good separation** - Clear boundaries between components
- ✅ **Future-proof** - Adaptable to changing requirements

The structure balances simplicity with scalability, making it easy for new developers to understand while accommodating complex requirements.
