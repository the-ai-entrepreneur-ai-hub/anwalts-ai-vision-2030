#!/usr/bin/env python3
"""
AnwaltsAI Frontend Startup Script
Starts the HTTP server for the client application
"""

import http.server
import socketserver
import webbrowser
import os
import time
from threading import Timer

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    """Open the browser after a short delay"""
    time.sleep(2)
    print("🌐 Opening browser...")
    webbrowser.open(f'http://localhost:{PORT}/anwalts-ai-app.html')

if __name__ == "__main__":
    print("=" * 60)
    print("🖥️  AnwaltsAI Frontend Server")
    print("=" * 60)
    print(f"📡 Starting server on port {PORT}...")
    print(f"🏠 Main App: http://localhost:{PORT}/anwalts-ai-app.html")
    print(f"📊 Dashboard: http://localhost:{PORT}/anwalts-ai-dashboard.html")
    print("=" * 60)
    print("💡 Make sure the backend is running on port 8008")
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start browser opening timer
        Timer(3.0, open_browser).start()
        
        # Start the server
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Frontend server started successfully!")
            print(f"🌐 Serving at http://localhost:{PORT}")
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use!")
            print("Try stopping any existing servers or use a different port.")
        else:
            print(f"❌ Server Error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")