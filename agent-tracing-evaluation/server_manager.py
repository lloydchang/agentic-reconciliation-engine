#!/usr/bin/env python3
"""
Evaluation API Server Management Script

Provides utilities to start, stop, and manage the evaluation API server
without blocking the terminal.
"""

import subprocess
import sys
import os
import time
import argparse
import signal
from pathlib import Path

PID_FILE = "api_server.pid"
LOG_FILE = "api_server.log"

def start_server(port=8081, host="0.0.0.0", background=True):
    """Start the evaluation API server"""
    
    # Check if server is already running
    if is_server_running():
        print("Server is already running")
        return False
    
    cmd = [
        sys.executable, "api_server.py",
        "--port", str(port),
        "--host", host
    ]
    
    if background:
        # Start in background
        with open(LOG_FILE, "a") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
        
        # Write PID file
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
        
        print(f"Server started in background with PID: {process.pid}")
        print(f"API available at http://{host}:{port}")
        print(f"Logs: {LOG_FILE}")
        return True
    else:
        # Start in foreground
        print(f"Starting server in foreground on http://{host}:{port}")
        subprocess.run(cmd)

def stop_server():
    """Stop the evaluation API server"""
    
    if not os.path.exists(PID_FILE):
        print("Server is not running (no PID file found)")
        return False
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM signal
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        time.sleep(2)
        
        # Check if process is still running
        try:
            os.kill(pid, 0)  # Check if process exists
            # If we get here, process is still running, force kill
            os.kill(pid, signal.SIGKILL)
            print("Server forcefully stopped")
        except ProcessLookupError:
            print("Server stopped gracefully")
        
        # Remove PID file
        os.remove(PID_FILE)
        return True
        
    except (FileNotFoundError, ValueError, ProcessLookupError) as e:
        print(f"Error stopping server: {e}")
        # Clean up stale PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return False

def is_server_running():
    """Check if server is running"""
    
    if not os.path.exists(PID_FILE):
        return False
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        os.kill(pid, 0)
        return True
        
    except (FileNotFoundError, ValueError, ProcessLookupError):
        # Clean up stale PID file
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return False

def server_status():
    """Show server status"""
    
    if is_server_running():
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        print(f"Server is running with PID: {pid}")
        
        if os.path.exists(LOG_FILE):
            print(f"Log file: {LOG_FILE}")
        return True
    else:
        print("Server is not running")
        return False

def restart_server(port=8081, host="0.0.0.0"):
    """Restart the evaluation API server"""
    
    print("Stopping server...")
    stop_server()
    time.sleep(1)
    
    print("Starting server...")
    return start_server(port, host)

def main():
    parser = argparse.ArgumentParser(description="Evaluation API Server Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--port", type=int, default=8081, help="Port to run server on")
    start_parser.add_argument("--host", default="0.0.0.0", help="Host to bind server to")
    start_parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop the server")
    
    # Status command
    subparsers.add_parser("status", help="Show server status")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the server")
    restart_parser.add_argument("--port", type=int, default=8081, help="Port to run server on")
    restart_parser.add_argument("--host", default="0.0.0.0", help="Host to bind server to")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_server(args.port, args.host, background=not args.foreground)
    elif args.command == "stop":
        stop_server()
    elif args.command == "status":
        server_status()
    elif args.command == "restart":
        restart_server(args.port, args.host)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
