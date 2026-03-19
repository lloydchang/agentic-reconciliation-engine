#!/usr/bin/env python3
"""
Simple HTTP server for the AI Infrastructure Portal
Runs on port 9000 (common for admin consoles and enterprise tools)
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 9001
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.path = '/enhanced-index.html'
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers to allow status checking
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def start_server():
    """Start the portal server"""
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 AI Infrastructure Portal is running!")
        print(f"📍 Portal URL: http://localhost:{PORT}")
        print(f"📂 Serving from: {DIRECTORY}")
        print(f"🔄 Press Ctrl+C to stop the server")
        print()
        print("🌐 Access links to all your AI services:")
        print("   🤖 AI Dashboard: http://localhost:8080")
        print("   📊 Dashboard API: http://localhost:5003") 
        print("   🔍 Langfuse: http://localhost:3000")
        print("   📈 Comprehensive API: http://localhost:5001")
        print("   🖥️ Comprehensive Frontend: http://localhost:8082")
        print("   🧠 Memory Service: http://localhost:8081")
        print("   ⏰ Temporal UI: http://localhost:7233")
        print()
        print("💡 Real-time Status Portal: http://localhost:9000/real_portal.html")
        print()
        
        # Auto-open browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print("🌐 Portal opened in your browser!")
        except:
            print("⚠️  Could not auto-open browser")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Portal server stopped. Goodbye!")

if __name__ == "__main__":
    start_server()
