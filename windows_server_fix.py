#!/usr/bin/env python3
"""
Windows Server Fix for Flow Metrics Dashboard
Addresses the "detail not found" error on Windows
"""

import http.server
import socketserver
import webbrowser
import sys
import os
from pathlib import Path

def start_windows_server(port=8000):
    """Start a Windows-compatible server for the dashboard"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    dashboard_file = project_root / "dashboard.html"
    
    print(f"Windows Server Fix for Flow Metrics Dashboard")
    print(f"=" * 50)
    print(f"Project root: {project_root}")
    print(f"Dashboard file: {dashboard_file}")
    print(f"Dashboard exists: {dashboard_file.exists()}")
    
    if not dashboard_file.exists():
        print("❌ ERROR: dashboard.html not found!")
        print("Make sure you're running from the project root directory")
        sys.exit(1)
    
    # Windows-specific HTTP handler
    class WindowsHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # Use the project root explicitly
            super().__init__(*args, directory=str(project_root), **kwargs)
        
        def log_message(self, format, *args):
            print(f"[{self.address_string()}] {format % args}")
        
        def do_GET(self):
            print(f"GET request for: {self.path}")
            
            # Special handling for common paths
            if self.path == '/':
                self.path = '/dashboard.html'
            elif self.path == '/dashboard':
                self.path = '/dashboard.html'
            elif self.path == '/executive':
                self.path = '/executive-dashboard.html'
            
            # Ensure path doesn't start with double slash
            if self.path.startswith('//'):
                self.path = self.path[1:]
            
            try:
                return super().do_GET()
            except Exception as e:
                print(f"Error serving {self.path}: {e}")
                self.send_error(404, f"File not found: {self.path}")
        
        def end_headers(self):
            # Add headers for Windows compatibility
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            
            # Set proper content types
            if self.path.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript; charset=utf-8')
            elif self.path.endswith('.json'):
                self.send_header('Content-Type', 'application/json; charset=utf-8')
            elif self.path.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            elif self.path.endswith('.css'):
                self.send_header('Content-Type', 'text/css; charset=utf-8')
            
            super().end_headers()
    
    try:
        # Create server with Windows handler
        with socketserver.TCPServer(("", port), WindowsHandler) as httpd:
            httpd.allow_reuse_address = True
            
            print(f"\\n🚀 Windows-compatible server started!")
            print(f"📊 Dashboard URL: http://localhost:{port}/dashboard.html")
            print(f"👔 Executive Dashboard: http://localhost:{port}/executive-dashboard.html") 
            print(f"🌐 Server: http://localhost:{port}")
            print(f"📁 Serving from: {project_root}")
            print(f"\\nPress Ctrl+C to stop the server")
            
            # Open browser
            try:
                dashboard_url = f"http://localhost:{port}/dashboard.html"
                webbrowser.open(dashboard_url)
                print(f"✅ Opened browser to {dashboard_url}")
            except Exception as e:
                print(f"⚠️  Could not open browser: {e}")
                print(f"   Please manually open: http://localhost:{port}/dashboard.html")
            
            # Keep server running
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\\n✅ Server stopped")
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use!")
            print(f"💡 Try a different port: python windows_server_fix.py {port + 1}")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_windows_server(port)