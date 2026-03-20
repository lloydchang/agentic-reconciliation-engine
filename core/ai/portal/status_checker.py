#!/usr/bin/env python3
"""
Real-time service status checker for Portal
Checks actual service availability and updates status indicators
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import threading

class ServiceStatusChecker:
    def __init__(self):
        self.services = {
            "AI Dashboard": {"url": "http://localhost:8080", "port": 8080, "type": "web"},
            "Dashboard API": {"url": "http://localhost:5000", "port": 5000, "type": "api"},
            "Langfuse": {"url": "http://localhost:3000", "port": 3000, "type": "web"},
            "Comprehensive API": {"url": "http://localhost:5001", "port": 5001, "type": "api"},
            "Comprehensive Frontend": {"url": "http://localhost:8082", "port": 8082, "type": "web"},
            "Memory Service": {"url": "http://localhost:8081/health", "port": 8081, "type": "api"},
            "Temporal UI": {"url": "http://localhost:7233", "port": 7233, "type": "web"}
        }
        self.status_cache = {}
        self.last_check = None
        
    def check_service(self, name: str, config: Dict) -> Dict:
        """Check individual service status"""
        url = config["url"]
        timeout = 3
        
        try:
            if config["type"] == "api":
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return {"status": "online", "response_time": response.elapsed.total_seconds()}
                else:
                    return {"status": "error", "code": response.status_code}
            else:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return {"status": "online", "response_time": response.elapsed.total_seconds()}
                else:
                    return {"status": "error", "code": response.status_code}
                    
        except requests.exceptions.ConnectionError:
            return {"status": "offline"}
        except requests.exceptions.Timeout:
            return {"status": "timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def check_all_services(self) -> Dict:
        """Check all services and return status"""
        results = {}
        for name, config in self.services.items():
            results[name] = self.check_service(name, config)
        
        self.status_cache = results
        self.last_check = datetime.now()
        return results
    
    def get_status_json(self) -> str:
        """Get status as JSON for API endpoint"""
        status = self.check_all_services()
        return json.dumps({
            "timestamp": self.last_check.isoformat() if self.last_check else None,
            "services": status
        })
    
    def get_service_count_summary(self) -> Dict:
        """Get summary counts of service statuses"""
        if not self.status_cache:
            self.check_all_services()
        
        counts = {"online": 0, "offline": 0, "error": 0, "timeout": 0}
        for service_status in self.status_cache.values():
            status = service_status.get("status", "offline")
            if status in counts:
                counts[status] += 1
        
        return counts

# Global checker instance
status_checker = ServiceStatusChecker()

if __name__ == "__main__":
    # Test the checker
    status = status_checker.check_all_services()
    print("Service Status:")
    for name, result in status.items():
        print(f"  {name}: {result['status']}")
