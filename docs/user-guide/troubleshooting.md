# Troubleshooting

Common issues and their solutions when working with the AI Agents Sandbox.

## Prerequisites & Setup Issues

### Docker Issues

**Problem:** Docker containers fail to start
```
docker-compose ps
docker-compose logs temporal
docker-compose logs postgres
```

**Solutions:**
- Check for port conflicts (5432, 7233, 8080, 8081, 3000)
- Ensure Docker Desktop is running
- Try restarting Docker: `docker-compose restart`

**Problem:** PostgreSQL connection issues
```
curl http://localhost:7233/health
docker-compose logs temporal | grep "Worker registered"
```

**Solutions:**
- Wait for PostgreSQL to fully initialize (can take 30-60 seconds)
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify no other PostgreSQL instances are running on port 5432

### Go/Node.js Version Issues

**Problem:** Go version not recognized
```bash
go version
# Expected: go version go1.25+ ...
```

**Solutions:**
- Install Go 1.25+ from https://golang.org/dl/
- Update PATH to include Go binary directory
- Restart terminal after installation

**Problem:** Node.js dependencies fail to install
```bash
cd frontend && rm -rf node_modules && yarn install
```

**Solutions:**
- Clear npm/yarn cache
- Check Node.js version (16+ required)
- Verify internet connection for package downloads

## Backend Issues

### Temporal Connection Problems

**Problem:** Backend can't connect to Temporal server
```
curl http://localhost:7233/health
# Should return: {"status":"SERVING"}
```

**Solutions:**
- Ensure Temporal container is running: `docker-compose ps`
- Check Temporal logs: `docker-compose logs temporal`
- Verify backend is using correct host: `TEMPORAL_HOST=localhost:7233`

### Agent Decision Tracing

**Problem:** Need to debug agent behavior
```bash
LOG_LEVEL=debug go run main.go
```

**Solutions:**
- Enable debug logging to trace agent decision-making
- Check activity execution logs in Temporal UI
- Review workflow history for failed steps

### MCP Server Issues

**Problem:** MCP server not responding
```bash
curl http://localhost:8081/mcp/resources
curl http://localhost:8081/mcp/tools
```

**Solutions:**
- Verify backend is running on port 8081
- Check MCP server logs in backend output
- Ensure proper JSON-RPC 2.0 protocol usage

## Frontend Issues

### Backstage App Won't Start

**Problem:** Frontend fails to load
```bash
cd frontend && cat frontend/app-config.yaml
cd frontend && rm -rf node_modules && yarn install
```

**Solutions:**
- Verify app-config.yaml points to correct backend URLs
- Clear node_modules and reinstall dependencies
- Check for port conflicts on 3000

### API Connection Issues

**Problem:** Frontend can't reach backend APIs
```
# Check backend health
curl http://localhost:8081/health

# Check CORS settings in backend
# Verify frontend app-config.yaml has correct API URLs
```

**Solutions:**
- Ensure backend is running and accessible
- Check CORS configuration in Go backend
- Verify API URLs in frontend configuration

## Skill Execution Issues

### Skill Not Found

**Problem:** Requested skill returns "not found"
```bash
# List available skills
./cli skill list

# Check skill directory exists
ls -la .agents/skills/
```

**Solutions:**
- Verify skill directory exists in `.agents/skills/`
- Check SKILL.md file is present and valid YAML frontmatter
- Restart backend to reload skills

### Workflow Validation Errors

**Problem:** Skill parameters are rejected
```bash
# Validate skill structure
python3 eval/run_evals.py --skill [skill-name] --verbose

# Check skill YAML schema
cat .agents/skills/[skill-name]/SKILL.md | head -20
```

**Solutions:**
- Review skill's YAML frontmatter for correct parameter definitions
- Check input validation rules in skill implementation
- Verify parameter types match expected formats

## Cloud Integration Issues

### AWS/Azure/GCP Authentication

**Problem:** Cloud operations fail with auth errors
```bash
# AWS
aws sts get-caller-identity

# Azure
az account show

# GCP
gcloud auth list
```

**Solutions:**
- Configure cloud CLI credentials
- Set appropriate environment variables
- Check IAM permissions for required operations

### Resource Access Issues

**Problem:** Agent can't access cloud resources
```
# Check environment variables are set
echo $AWS_ACCOUNT_ID
echo $AZURE_SUBSCRIPTION_ID
echo $GCP_PROJECT_ID
```

**Solutions:**
- Verify environment variables are exported
- Check resource permissions in cloud console
- Ensure agent has appropriate IAM roles

## Performance Issues

### Slow Workflow Execution

**Problem:** Workflows take too long to complete
```
# Check Temporal UI for bottlenecks
open http://localhost:8080

# Monitor resource usage
docker stats
```

**Solutions:**
- Check for resource constraints (CPU/memory)
- Review workflow parallelism settings
- Optimize activity timeouts and retry policies

### Memory/CPU Usage

**Problem:** High resource consumption
```bash
# Monitor Docker containers
docker stats

# Check backend logs for memory issues
docker-compose logs backend | grep -i memory
```

**Solutions:**
- Increase Docker resource limits
- Review Go garbage collection settings
- Optimize concurrent workflow limits

## Network & Connectivity

### Port Conflicts

**Problem:** Services can't bind to ports
```bash
# Check what's using ports
lsof -i :8080
lsof -i :8081
lsof -i :7233
lsof -i :5432
lsof -i :3000

# Find available ports
netstat -tulpn | grep LISTEN
```

**Solutions:**
- Stop conflicting services
- Change default ports in configuration
- Use port forwarding if needed

### Firewall Issues

**Problem:** External connections blocked
```bash
# Test local connectivity
curl http://localhost:8081/health

# Check firewall rules
sudo ufw status
sudo iptables -L
```

**Solutions:**
- Configure firewall to allow required ports
- Use host networking mode for Docker if needed
- Check VPN/proxy interference

## Development & Testing

### Test Failures

**Problem:** Unit/integration tests failing
```bash
# Run backend tests
cd backend && go test ./...

# Run integration tests
cd backend && go test -tags=integration ./...

# Run frontend tests
cd frontend && yarn test
```

**Solutions:**
- Check test dependencies and setup
- Review test logs for specific failures
- Update test data and mock objects

### Hot Reload Issues

**Problem:** Code changes not reflected
```bash
# Backend
go run main.go

# Frontend
cd frontend && yarn start
```

**Solutions:**
- Ensure files are saved and compiled
- Check for syntax errors preventing compilation
- Restart development servers if needed

## Advanced Troubleshooting

### Complete Environment Validation

```bash
# Run comprehensive validation
./scripts/validate.sh

# Check all prerequisites
./bootstrap.sh
```

### Skill Evaluation

```bash
# Evaluate all skills
python3 eval/run_evals.py

# Evaluate specific skill
python3 eval/run_evals.py --skill incident-triage-runbook --verbose
```

### Log Analysis

```bash
# Backend logs
docker-compose logs backend

# Temporal logs
docker-compose logs temporal

# Frontend logs (in browser dev tools)
# Network tab for API calls
# Console tab for JavaScript errors
```

## Getting Help

If these solutions don't resolve your issue:

1. Check the **[Agent Behavior](../developer-guide/agent-behavior.md)** guide for operational constraints
2. Review **[Configuration](../reference/configuration.md)** for setup options
3. Check existing GitHub issues for similar problems
4. Create a new issue with:
   - Full error messages and logs
   - Steps to reproduce
   - Environment details (OS, Docker versions, etc.)
   - Configuration files (redact sensitive data)

## Common Error Patterns

- **"Connection refused"**: Check if services are running and ports are accessible
- **"Permission denied"**: Verify file permissions and user access rights
- **"Timeout"**: Increase timeout values or check for resource constraints
- **"Invalid input"**: Review API documentation and parameter formats
- **"Out of memory"**: Increase Docker memory limits or optimize resource usage
