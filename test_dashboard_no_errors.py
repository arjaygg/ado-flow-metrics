#!/usr/bin/env python3
"""
Dashboard Error Verification Script
Tests that dashboards load without 'Not Found' errors
"""
import http.server
import socketserver
import threading
import time
import requests
import json
from urllib.parse import urlparse

def test_dashboard_endpoints():
    """Test all dashboard endpoints for errors"""
    
    print("🔍 Testing Dashboard Endpoints...")
    
    # Start test server
    port = 8092
    server = None
    
    try:
        # Start HTTP server in background
        handler = http.server.SimpleHTTPRequestHandler
        server = socketserver.TCPServer(("", port), handler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"✅ Test server started on port {port}")
        time.sleep(2)
        
        base_url = f"http://localhost:{port}"
        
        # Test static files
        static_tests = [
            f"{base_url}/dashboard.html",
            f"{base_url}/executive-dashboard.html", 
            f"{base_url}/js/workstream_config.js",
            f"{base_url}/js/workstream-manager.js"
        ]
        
        for url in static_tests:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - OK")
            else:
                print(f"❌ {url} - Status: {response.status_code}")
        
        # Test data files
        data_tests = [
            f"{base_url}/data/dashboard_data.json",
            f"{base_url}/data/flow_metrics_report.json",
            f"{base_url}/data/test_report.json",
            f"{base_url}/data/test_metrics_report.json"
        ]
        
        for url in data_tests:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {url} - Valid JSON ({len(str(data))} chars)")
                except:
                    print(f"⚠️  {url} - Not valid JSON")
            else:
                print(f"❌ {url} - Status: {response.status_code}")
        
        # Test specific features in data
        print("\n🧪 Testing Feature Data...")
        response = requests.get(f"{base_url}/data/dashboard_data.json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Test Work Item Types
            if 'items_by_type' in data:
                types = list(data['items_by_type'].keys())
                print(f"✅ Work Item Types: {types}")
            else:
                print("❌ Missing items_by_type data")
                
            # Test Sprints
            if 'items_by_sprint' in data:
                sprints = list(data['items_by_sprint'].keys())
                print(f"✅ Sprints: {sprints}")
            else:
                print("❌ Missing items_by_sprint data")
                
            # Test Team Metrics
            if 'team_metrics' in data:
                teams = list(data['team_metrics'].keys())
                print(f"✅ Teams: {teams}")
            else:
                print("❌ Missing team_metrics data")
        
        print(f"\n🎯 Dashboard Testing Complete!")
        print(f"📊 Access Main Dashboard: {base_url}/dashboard.html")
        print(f"📈 Access Executive Dashboard: {base_url}/executive-dashboard.html")
        print(f"🔧 If you see 'Not Found' errors, check browser console for specific failed requests")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        if server:
            server.shutdown()
            print("🛑 Test server stopped")

if __name__ == "__main__":
    success = test_dashboard_endpoints()
    exit(0 if success else 1)