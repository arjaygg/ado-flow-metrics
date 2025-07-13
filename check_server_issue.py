#!/usr/bin/env python3
"""
Check Server Issue
Diagnose why the CLI server returns "detail not found"
"""

import http.client
import json
from pathlib import Path

def check_server_issue(host='localhost', port=8000):
    """Check what's wrong with the server"""
    
    print(f"Checking server issue at {host}:{port}")
    print("=" * 40)
    
    # Test various endpoints
    endpoints = [
        '/',
        '/dashboard.html',
        '/data/dashboard_data.json',
        '/js/workstream_config.js',
        '/config/workstream_config.json'
    ]
    
    for endpoint in endpoints:
        try:
            conn = http.client.HTTPConnection(host, port, timeout=5)
            conn.request("GET", endpoint)
            response = conn.getresponse()
            
            print(f"GET {endpoint}")
            print(f"  Status: {response.status} {response.reason}")
            print(f"  Headers: {dict(response.getheaders())}")
            
            if response.status == 200:
                content = response.read()
                print(f"  Content-Length: {len(content)} bytes")
                print(f"  Content-Type: {response.getheader('Content-Type')}")
                
                # Show first 100 chars for HTML/JSON
                if endpoint.endswith('.html') or endpoint.endswith('.json'):
                    preview = content.decode('utf-8', errors='ignore')[:100]
                    print(f"  Preview: {preview}...")
            
            elif response.status == 404:
                print(f"  ❌ File not found!")
            else:
                error_content = response.read().decode('utf-8', errors='ignore')
                print(f"  Error content: {error_content[:200]}...")
            
            conn.close()
            print()
            
        except ConnectionRefusedError:
            print(f"❌ Cannot connect to server at {host}:{port}")
            print("Make sure the server is running first:")
            print("  python -m src.cli serve --port 8000")
            break
        except Exception as e:
            print(f"❌ Error checking {endpoint}: {e}")
            print()

def check_local_files():
    """Check if files exist locally"""
    print("\\nChecking local files:")
    print("-" * 20)
    
    project_root = Path(__file__).parent
    files_to_check = [
        'dashboard.html',
        'data/dashboard_data.json',
        'js/workstream_config.js',
        'config/workstream_config.json',
        'manifest.json'
    ]
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} - {size} bytes")
        else:
            print(f"❌ {file_path} - Missing")

if __name__ == "__main__":
    import sys
    
    # Check local files first
    check_local_files()
    
    # Then check server if running
    print("\\n" + "=" * 40)
    print("Now checking server (make sure it's running)...")
    print("If you get connection errors, start the server first:")
    print("  python -m src.cli serve --port 8000")
    print("=" * 40)
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    check_server_issue(port=port)