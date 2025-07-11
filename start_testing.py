#!/usr/bin/env python3
"""
Simple testing server for Flow Metrics Dashboard features
"""
import http.server
import socketserver
import webbrowser
import threading
import time
import os

def start_server(port=8090):
    """Start a simple HTTP server for testing"""
    
    # Change to project directory
    os.chdir('/home/devag/git/feat-ado-flow')
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers for local testing
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            print("🚀 Flow Metrics Dashboard Testing Server")
            print("=" * 50)
            print(f"📊 Main Dashboard: http://localhost:{port}/dashboard.html")
            print(f"📈 Executive Dashboard: http://localhost:{port}/executive-dashboard.html") 
            print(f"🧪 Testing Guide: http://localhost:{port}/LIVE_TESTING_GUIDE.md")
            print(f"🧩 Run Tests: python3 test_new_features.py")
            print()
            print("✨ NEW FEATURES TO TEST:")
            print("  1. Work Item Type filtering (multi-select)")
            print("  2. Sprint-based filtering (dynamic)")
            print("  3. Defect ratio chart (configurable)")
            print()
            print(f"Server running on port {port}. Press Ctrl+C to stop.")
            print("=" * 50)
            
            # Try to open browser
            try:
                time.sleep(1)
                webbrowser.open(f'http://localhost:{port}/dashboard.html')
                print("✅ Browser opened automatically")
            except:
                print("ℹ️  Please open the URLs manually in your browser")
            
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying port {port + 1}...")
            start_server(port + 1)
        else:
            raise

if __name__ == "__main__":
    start_server()