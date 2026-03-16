# AI Agent Debugging Scripts Collection

This directory contains all debugging scripts for AI agents in Kubernetes distributed systems.

## Scripts Overview

### 1. main.py
**Purpose**: Main Python debugging engine with PEP 723 dependencies
**Usage**: Core debugging operations and LLM-to-LLM collaboration
```bash
python main.py '{"operation": "diagnose", "targetAgent": "memory-agent"}'
```

### 2. debug-ai-agents-k8s.sh
**Purpose**: Interactive Kubernetes debugging with tight feedback loops
**Usage**: Real-time debugging and health monitoring
```bash
./debug-ai-agents-k8s.sh memory-agent DEBUG_LEVEL=detailed
```

### 3. llm-debug-automation.sh
**Purpose**: LLM-to-LLM collaborative debugging automation
**Usage**: Automated analysis and session management
```bash
./llm-debug-automation.sh ai-inference-gateway ANALYSIS_DEPTH=deep
```

## Script Integration

### Combined Debugging Workflow
```bash
# 1. Quick health assessment
./debug-ai-agents-k8s.sh all DEBUG_LEVEL=basic

# 2. Deep behavioral analysis
python main.py '{"operation": "analyze", "targetAgent": "all", "debugLevel": "deep"}'

# 3. LLM collaborative debugging
./llm-debug-automation.sh all ANALYSIS_DEPTH=deep AUTO_FIX=true

# 4. Automated fixes
python main.py '{"operation": "automate", "targetAgent": "memory-agent"}'
```

### Script Dependencies
- `main.py`: Core debugging logic and state collection
- `debug-ai-agents-k8s.sh`: Kubernetes-specific debugging utilities
- `llm-debug-automation.sh`: LLM collaboration and session management

### Shared Configuration
All scripts use consistent environment variables:
- `NAMESPACE`: Kubernetes namespace (default: ai-infrastructure)
- `DEBUG_LEVEL`: Analysis depth (basic, detailed, deep)
- `CORRELATION_ID`: Request tracing identifier
- `OUTPUT_FORMAT`: Output format (interactive, json, yaml)

## Usage Patterns

### Basic Debugging
```bash
# Quick health check
./debug-ai-agents-k8s.sh memory-agent

# Interactive session
./debug-ai-agents-k8s.sh all OUTPUT_FORMAT=interactive
```

### Advanced Analysis
```bash
# Deep analysis with LLM collaboration
python main.py '{"operation": "llm-analyze", "targetAgent": "all"}'

# Automated debugging session
./llm-debug-automation.sh all ANALYSIS_DEPTH=deep
```

### Prevention and Monitoring
```bash
# Generate prevention strategies
python main.py '{"operation": "prevent", "targetAgent": "all"}'

# Automated fixes with validation
python main.py '{"operation": "automate", "targetAgent": "memory-agent"}'
```

## Script Features

### debug-ai-agents-k8s.sh
- Interactive debugging mode
- Multi-level debugging (basic, detailed, deep)
- Real-time log following
- Health endpoint checking
- Resource usage monitoring
- Model status verification

### llm-debug-automation.sh
- LLM-to-LLM collaborative debugging
- Comprehensive state collection
- Behavioral pattern analysis
- Automated fix execution
- Session artifact management
- Knowledge base integration

### main.py
- agentskills.io compliant execution
- Comprehensive input validation
- Multi-agent type support
- Error handling and recovery
- Session management
- Output formatting

## Integration Examples

### Full Debugging Session
```bash
#!/bin/bash
# Complete AI agent debugging session

echo "=== Starting AI Agent Debugging Session ==="

# 1. Initial health assessment
echo "Step 1: Basic health check"
./debug-ai-agents-k8s.sh all DEBUG_LEVEL=basic

# 2. Deep analysis
echo "Step 2: Deep behavioral analysis"
python main.py '{"operation": "analyze", "targetAgent": "all", "debugLevel": "detailed"}'

# 3. LLM collaboration
echo "Step 3: LLM-to-LLM collaborative debugging"
./llm-debug-automation.sh all ANALYSIS_DEPTH=deep

# 4. Prevention strategies
echo "Step 4: Generate prevention strategies"
python main.py '{"operation": "prevent", "targetAgent": "all"}'

# 5. Automated fixes
echo "Step 5: Apply automated fixes"
python main.py '{"operation": "automate", "targetAgent": "memory-agent"}'

echo "=== Debugging session completed ==="
```

### Emergency Response
```bash
#!/bin/bash
# Emergency debugging for critical issues

# Quick diagnosis
./debug-ai-agents-k8s.sh all DEBUG_LEVEL=basic FOLLOW_LOGS=true

# Automated recovery
python main.py '{"operation": "automate", "targetAgent": "all"}'

# LLM analysis for complex issues
./llm-debug-automation.sh all ANALYSIS_DEPTH=deep AUTO_FIX=true
```

This script collection provides comprehensive debugging capabilities for AI agents in distributed Kubernetes environments, with both immediate debugging and long-term prevention strategies.
