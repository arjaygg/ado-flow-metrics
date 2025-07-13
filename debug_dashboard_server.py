#!/usr/bin/env python3
"""
Debug Dashboard Server
Simple HTTP server to test dashboard loading issues
"""

import http.server
import socketserver
import webbrowser
import sys
from pathlib import Path

def start_debug_server(port=8080):
    """Start a debug server to troubleshoot dashboard issues"""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    dashboard_file = project_root / "dashboard.html"
    
    print(f"Debug Dashboard Server")
    print(f"======================")
    print(f"Project root: {project_root}")
    print(f"Dashboard file: {dashboard_file}")
    print(f"Dashboard exists: {dashboard_file.exists()}")
    
    if not dashboard_file.exists():
        print("❌ ERROR: dashboard.html not found!")
        sys.exit(1)
    
    # List key files
    key_files = [
        "dashboard.html",
        "executive-dashboard.html", 
        "data/dashboard_data.json",
        "js/workstream_config.js",
        "js/predictive-analytics.js",
        "manifest.json"
    ]
    
    print(f"\nChecking key files:")
    for file_path in key_files:
        full_path = project_root / file_path
        status = "✅" if full_path.exists() else "❌"
        print(f"  {status} {file_path}")
    
    # Create enhanced HTTP handler
    class DebugHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(project_root), **kwargs)
        
        def log_message(self, format, *args):
            print(f"[{self.address_string()}] {format % args}")
        
        def do_GET(self):
            print(f"GET request for: {self.path}")
            return super().do_GET()
        
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Cache-Control', 'no-cache')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", port), DebugHandler) as httpd:
            httpd.allow_reuse_address = True
            
            print(f"\n🚀 Debug server started on http://localhost:{port}")
            print(f"📊 Dashboard URL: http://localhost:{port}/dashboard.html")
            print(f"👔 Executive Dashboard: http://localhost:{port}/executive-dashboard.html")
            print(f"📁 Files served from: {project_root}")
            print(f"\nPress Ctrl+C to stop the server")
            
            # Try to open browser
            try:
                dashboard_url = f"http://localhost:{port}/dashboard.html"
                webbrowser.open(dashboard_url)
                print(f"✅ Opened browser to {dashboard_url}")
            except Exception as e:
                print(f"⚠️  Could not open browser: {e}")
                print(f"   Please manually open: http://localhost:{port}/dashboard.html")
            
            httpd.serve_forever()
            
    except OSError as e:
        print(f"❌ Server error: {e}")
        print(f"💡 Try a different port: python debug_dashboard_server.py {port + 1}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n✅ Debug server stopped")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_debug_server(port)