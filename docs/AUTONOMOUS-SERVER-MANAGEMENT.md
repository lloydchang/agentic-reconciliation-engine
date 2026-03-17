# Autonomous Server Management Guide

## Overview

This guide documents the autonomous server management system implemented for the Agent Tracing Evaluation Framework, addressing the requirement for non-blocking, fully automated server operations.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Server Manager  │    │   FastAPI       │    │   Process       │
│  (CLI Interface)│───▶│   Server        │───▶│   Management    │
│                 │    │   (Port 8082)   │    │   System        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PID Files     │    │   Log Files     │    │   Signal        │
│   (.pid)        │    │   (.log)        │    │   Handling      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Server Manager (`server_manager.py`)

**Purpose**: CLI interface for autonomous server management

**Key Features**:
- Background process execution
- PID file management
- Graceful shutdown handling
- Status monitoring
- Log management

### 2. Process Management

**PID File**: `api_server.pid`
- Stores server process ID
- Enables process tracking
- Supports graceful shutdown

**Log File**: `api_server.log`
- Captures all server output
- Enables debugging
- Supports log rotation

### 3. Signal Handling

**SIGTERM**: Graceful shutdown
- Allows current requests to complete
- Clean resource cleanup
- Proper connection closure

**SIGKILL**: Force shutdown (fallback)
- Immediate process termination
- Used when graceful shutdown fails
- Emergency cleanup only

## Command Reference

### 1. Start Command

```bash
python server_manager.py start [options]
```

**Options**:
- `--port <number>`: Port to run server on (default: 8081)
- `--host <address>`: Host to bind server to (default: 0.0.0.0)
- `--foreground`: Run in foreground mode (development)

**Examples**:
```bash
# Background mode (production)
python server_manager.py start --port 8082

# Foreground mode (development)
python server_manager.py start --port 8082 --foreground

# Custom host
python server_manager.py start --host 127.0.0.1 --port 8082
```

### 2. Stop Command

```bash
python server_manager.py stop
```

**Behavior**:
1. Reads PID from `api_server.pid`
2. Sends SIGTERM signal
3. Waits 2 seconds for graceful shutdown
4. Sends SIGKILL if still running
5. Removes PID file

**Output**:
```
Server stopped gracefully
```
or
```
Server forcefully stopped
```

### 3. Status Command

```bash
python server_manager.py status
```

**Output Examples**:
```
Server is running with PID: 78064
Log file: api_server.log
```
or
```
Server is not running
```

### 4. Restart Command

```bash
python server_manager.py restart [options]
```

**Behavior**:
1. Stops existing server
2. Waits 1 second
3. Starts new server with specified options

## Implementation Details

### 1. Background Process Execution

```python
def start_server(port=8081, host="0.0.0.0", background=True):
    """Start the evaluation API server"""
    
    if background:
        with open(LOG_FILE, "a") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True  # Key for background execution
            )
        
        # Write PID for process tracking
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
```

**Key Points**:
- `start_new_session=True`: Creates new process group
- `stdout=log_file`: Redirects output to log file
- `stderr=subprocess.STDOUT`: Combines stderr with stdout
- PID file enables process tracking

### 2. Graceful Shutdown

```python
def stop_server():
    """Stop the evaluation API server"""
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Wait for graceful termination
        time.sleep(2)
        
        # Check if process still exists
        try:
            os.kill(pid, 0)  # Test process existence
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            print("Server forcefully stopped")
        except ProcessLookupError:
            print("Server stopped gracefully")
        
        # Clean up PID file
        os.remove(PID_FILE)
```

**Shutdown Sequence**:
1. SIGTERM signal sent
2. 2-second grace period
3. Process existence check
4. SIGKILL if needed
5. PID file cleanup

### 3. Status Monitoring

```python
def is_server_running():
    """Check if server is running"""
    
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Test process existence
        os.kill(pid, 0)
        return True
        
    except (FileNotFoundError, ValueError, ProcessLookupError):
        # Clean up stale PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return False
```

**Status Logic**:
1. Check PID file existence
2. Read PID from file
3. Test process with signal 0
4. Clean up stale PID files
5. Return boolean status

## Usage Patterns

### 1. Development Workflow

```bash
# Start server in background
python server_manager.py start --port 8082

# Work on code changes
# Server runs independently

# Check status periodically
python server_manager.py status

# View logs if needed
tail -f api_server.log

# Stop when done
python server_manager.py stop
```

### 2. Production Deployment

```bash
# Start production server
python server_manager.py start --port 8082

# Verify running
python server_manager.py status

# Monitor logs
tail -f api_server.log

# Restart for updates
python server_manager.py restart --port 8082
```

### 3. CI/CD Integration

```bash
#!/bin/bash
# ci-deploy.sh

# Start evaluation server
python server_manager.py start --port 8082

# Wait for server to be ready
sleep 5

# Run integration tests
python tests/integration.py

# Cleanup
python server_manager.py stop
```

### 4. Automation Scripts

```bash
#!/bin/bash
# automated-monitoring.sh

while true; do
    if ! python server_manager.py status > /dev/null 2>&1; then
        echo "Server not running, restarting..."
        python server_manager.py start --port 8082
    fi
    
    sleep 30
done
```

## Troubleshooting

### 1. Server Won't Start

**Symptoms**:
- "Server is already running" but it's not
- Port already in use error
- Permission denied

**Solutions**:
```bash
# Check for stale PID file
rm -f api_server.pid

# Check port usage
lsof -i :8082

# Kill existing process
pkill -f api_server.py

# Try different port
python server_manager.py start --port 8083
```

### 2. Server Won't Stop

**Symptoms**:
- "Server is not running" but process exists
- PID file corruption
- Process ignoring signals

**Solutions**:
```bash
# Force cleanup
rm -f api_server.pid

# Find and kill process
ps aux | grep api_server
kill -9 <PID>

# Verify cleanup
python server_manager.py status
```

### 3. Status Inconsistency

**Symptoms**:
- Status shows running but API not responding
- PID file exists but process dead
- Multiple processes running

**Solutions**:
```bash
# Check actual processes
ps aux | grep api_server

# Clean up everything
pkill -f api_server.py
rm -f api_server.pid

# Fresh start
python server_manager.py start --port 8082
```

### 4. Log Issues

**Symptoms**:
- No log file created
- Permission denied writing logs
- Log file too large

**Solutions**:
```bash
# Check permissions
ls -la api_server.log

# Create log directory
mkdir -p logs
chmod 755 logs

# Rotate logs
mv api_server.log api_server.log.old
python server_manager.py restart
```

## Advanced Configuration

### 1. Custom PID and Log Locations

```python
# Environment variables
PID_FILE = os.environ.get("API_SERVER_PID", "api_server.pid")
LOG_FILE = os.environ.get("API_SERVER_LOG", "api_server.log")
```

**Usage**:
```bash
export API_SERVER_PID="/var/run/api-server.pid"
export API_SERVER_LOG="/var/log/api-server.log"
python server_manager.py start
```

### 2. Systemd Service

Create `/etc/systemd/system/evaluation-api.service`:

```ini
[Unit]
Description=Evaluation API Server
After=network.target

[Service]
Type=forking
User=evaluation
Group=evaluation
WorkingDirectory=/opt/evaluation
ExecStart=/usr/bin/python3 server_manager.py start --port 8082
ExecStop=/usr/bin/python3 server_manager.py stop
ExecReload=/usr/bin/python3 server_manager.py restart
PIDFile=/opt/evaluation/api_server.pid
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
# Enable service
sudo systemctl enable evaluation-api

# Start service
sudo systemctl start evaluation-api

# Check status
sudo systemctl status evaluation-api

# View logs
sudo journalctl -u evaluation-api
```

### 3. Docker Integration

**Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create startup script
RUN echo '#!/bin/bash\npython server_manager.py start --port 8082\ntail -f api_server.log' > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8082
CMD ["/app/entrypoint.sh"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  evaluation-api:
    build: .
    ports:
      - "8082:8082"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## Monitoring and Observability

### 1. Health Monitoring

```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash

if python server_manager.py status > /dev/null 2>&1; then
    if curl -s http://localhost:8082/health > /dev/null; then
        echo "HEALTHY"
        exit 0
    else
        echo "UNHEALTHY: API not responding"
        exit 1
    fi
else
    echo "UNHEALTHY: Server not running"
    exit 1
fi
EOF

chmod +x health_check.sh
```

### 2. Performance Monitoring

```bash
# Monitor process resources
while true; do
    if python server_manager.py status > /dev/null 2>&1; then
        PID=$(cat api_server.pid)
        ps -p $PID -o %cpu,%mem,etime,cmd
    fi
    sleep 5
done
```

### 3. Log Monitoring

```bash
# Monitor for errors
tail -f api_server.log | grep -i error

# Monitor API requests
tail -f api_server.log | grep "GET\|POST"

# Alert on critical errors
tail -f api_server.log | grep -i "critical\|fatal" | while read line; do
    echo "ALERT: $line"
    # Send alert notification
done
```

## Best Practices

### 1. Process Management

- **Always use server_manager**: Never start server directly
- **Check status first**: Verify server state before operations
- **Use graceful shutdown**: Allow proper cleanup
- **Monitor logs**: Regularly check for issues

### 2. Security

- **Restrict permissions**: Run as non-root user
- **Secure PID files**: Proper file permissions
- **Log rotation**: Prevent disk space issues
- **Network isolation**: Bind to appropriate interfaces

### 3. Reliability

- **Automatic restart**: Use systemd or supervisor
- **Health checks**: Regular monitoring
- **Backup processes**: Multiple instance support
- **Graceful degradation**: Handle failures gracefully

### 4. Performance

- **Resource limits**: Set appropriate limits
- **Connection pooling**: Reuse connections
- **Caching**: Cache frequent requests
- **Load balancing**: Distribute load

## Integration Examples

### 1. CI/CD Pipeline

```yaml
# .github/workflows/evaluation-tests.yml
name: Evaluation Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Start evaluation server
        run: |
          python server_manager.py start --port 8082
      
      - name: Wait for server
        run: sleep 10
      
      - name: Run tests
        run: |
          python tests/integration.py
      
      - name: Stop server
        run: |
          python server_manager.py stop
```

### 2. Monitoring Integration

```python
# monitoring.py
import subprocess
import time
import requests

def monitor_server():
    while True:
        try:
            # Check server status
            result = subprocess.run(
                ["python", "server_manager.py", "status"],
                capture_output=True, text=True
            )
            
            if "Server is running" not in result.stdout:
                print("Server not running, restarting...")
                subprocess.run(["python", "server_manager.py", "restart"])
            
            # Check API health
            response = requests.get("http://localhost:8082/health", timeout=5)
            if response.status_code != 200:
                print("API unhealthy, restarting...")
                subprocess.run(["python", "server_manager.py", "restart"])
            
        except Exception as e:
            print(f"Monitoring error: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_server()
```

### 3. Backup and Recovery

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/evaluation"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp server_manager.py "$BACKUP_DIR/server_manager_$DATE.py"
cp api_server.py "$BACKUP_DIR/api_server_$DATE.py"

# Backup logs
cp api_server.log "$BACKUP_DIR/api_server_$DATE.log"

# Backup PID file (if exists)
if [ -f api_server.pid ]; then
    cp api_server.pid "$BACKUP_DIR/api_server_$DATE.pid"
fi

echo "Backup completed: $BACKUP_DIR"
```

## Conclusion

The autonomous server management system provides:

1. **Non-blocking Operation**: Server runs independently without terminal interference
2. **Process Lifecycle Management**: Complete control over server startup, shutdown, and monitoring
3. **Graceful Error Handling**: Robust error recovery and cleanup mechanisms
4. **Production Readiness**: Suitable for production deployment with monitoring
5. **Automation Friendly**: Designed for CI/CD and automated workflows

This system eliminates the need for manual server management and enables fully autonomous operation of the evaluation framework.
