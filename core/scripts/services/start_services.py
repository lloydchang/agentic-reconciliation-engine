#!/usr/bin/env python3
"""
Service Startup Script
Starts all required services for the Portal
"""

import subprocess
import time
import os
import signal
import sys

def start_service(name, command, port):
    """Start a service and check if it's running"""
    print(f"🚀 Starting {name} on port {port}...")
    
    # Kill any existing process on the port
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
            time.sleep(1)
    except:
        pass
    
    # Start the service
    try:
        process = subprocess.Popen(command, shell=True, 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        time.sleep(2)  # Give it time to start
        
        # Check if it's running
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✅ {name} started successfully on port {port}")
            return process
        else:
            print(f"❌ {name} failed to start")
            return None
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    print("🎯 Starting AI Infrastructure Services")
    print("=" * 50)
    
    services = [
        {
            "name": "Dashboard API",
            "command": "python3 simple_dashboard_api.py",
            "port": 5000
        },
        {
            "name": "Memory Service", 
            "command": "python3 simple_memory_service.py",
            "port": 8081
        }
    ]
    
    processes = []
    
    for service in services:
        # Update the port in the service files
        if service["name"] == "Dashboard API":
            # Update port to 5000 in the dashboard API
            with open('simple_dashboard_api.py', 'r') as f:
                content = f.read()
            content = content.replace('app.run(host=\'0.0.0.0\', port=5002', 
                                       'app.run(host=\'0.0.0.0\', port=5000')
            with open('simple_dashboard_api.py', 'w') as f:
                f.write(content)
        
        process = start_service(service["name"], service["command"], service["port"])
        if process:
            processes.append(process)
    
    print("\n🎉 Services started!")
    print("📍 Access your services:")
    print("   🌐 Portal: http://localhost:9000")
    print("   📊 Dashboard API: http://localhost:5000")
    print("   🧠 Memory Service: http://localhost:8081")
    print("   ⏰ Temporal UI: http://localhost:7233")
    print("\n💡 Press Ctrl+C to stop all services")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        for process in processes:
            if process:
                process.terminate()
        print("👋 All services stopped")

if __name__ == "__main__":
    main()
