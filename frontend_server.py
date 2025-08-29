#!/usr/bin/env python3
"""
Frontend Server for AnwaltsAI
Serves the complete frontend with all dependencies, routing, and assets
"""

import http.server
import socketserver
import os
from pathlib import Path
import webbrowser
import time
import threading

class AnwaltsAIHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for AnwaltsAI frontend"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="Client", **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests with proper routing"""
        if self.path == '/':
            self.path = '/anwalts-ai-app.html'
        elif self.path == '/dashboard':
            self.path = '/anwalts-ai-dashboard.html'
        elif self.path == '/generator':
            self.path = '/generator-replacement.html'
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"Frontend: {format % args}")

def start_frontend_server(port=3000):
    """Start the frontend server"""
    os.chdir(Path(__file__).parent)
    
    if not os.path.exists("Client"):
        print("❌ Client folder not found!")
        return False
    
    try:
        with socketserver.TCPServer(("", port), AnwaltsAIHTTPRequestHandler) as httpd:
            print(f"🌐 AnwaltsAI Frontend Server")
            print(f"📡 Serving at: http://localhost:{port}")
            print(f"📁 Directory: {os.path.abspath('Client')}")
            print(f"🎯 Main App: http://localhost:{port}/")
            print(f"📊 Dashboard: http://localhost:{port}/dashboard") 
            print(f"📝 Generator: http://localhost:{port}/generator")
            print("=" * 50)
            
            # Auto-open browser after short delay
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{port}/')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} already in use. Trying port {port + 1}...")
            return start_frontend_server(port + 1)
        else:
            print(f"❌ Failed to start frontend server: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Starting AnwaltsAI Frontend Server...")
    start_frontend_server()