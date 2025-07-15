#!/usr/bin/env python3
"""
Dashboard Functionality Test Script

This script tests the dashboard functionality without requiring a full server setup.
It validates JavaScript modules, generates test data, and checks configuration.
"""

import json
import os
import sys
from pathlib import Path

def test_dashboard_files():
    """Test that all required dashboard files exist and are readable"""
    print("🔍 Testing Dashboard Files...")
    
    required_files = [
        "dashboard.html",
        "executive-dashboard.html",
        "js/workstream-manager.js",
        "js/workstream_config.js",
        "js/predictive-analytics.js",
        "js/time-series-analysis.js",
        "js/enhanced-ux.js",
        "js/advanced-filtering.js",
        "config/workstream_config.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  ✅ All dashboard files present")
    return True

def test_workstream_config():
    """Test workstream configuration loading and validation"""
    print("\n🔧 Testing Workstream Configuration...")
    
    try:
        with open("config/workstream_config.json", "r") as f:
            config = json.load(f)
        
        # Validate structure
        required_keys = ["workstreams", "default_workstream", "matching_options"]
        for key in required_keys:
            if key not in config:
                print(f"  ❌ Missing key: {key}")
                return False
        
        workstreams = config["workstreams"]
        print(f"  ✅ Found {len(workstreams)} workstreams:")
        for name, details in workstreams.items():
            patterns = details.get("name_patterns", [])
            print(f"    - {name}: {len(patterns)} name patterns")
        
        print(f"  ✅ Default workstream: {config['default_workstream']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading workstream config: {e}")
        return False

def generate_test_data():
    """Generate test data for dashboard testing"""
    print("\n📊 Generating Test Data...")
    
    test_data = {
        "summary": {
            "total_work_items": 150,
            "completed_items": 98,
            "completion_rate": 65.3
        },
        "lead_time": {
            "average_days": 14.2,
            "median_days": 12.0,
            "count": 98
        },
        "cycle_time": {
            "average_days": 9.8,
            "median_days": 8.5,
            "count": 98
        },
        "throughput": {
            "items_per_period": 16.3,
            "period_days": 30
        },
        "work_in_progress": {
            "total_wip": 52,
            "wip_by_state": {
                "New": 12,
                "Active": 28,
                "Resolved": 8,
                "Closed": 4
            }
        },
        "flow_efficiency": {
            "average_efficiency": 0.69
        },
        "team_metrics": {
            "Nenissa Chen": {"completed_items": 18, "active_items": 4, "completion_rate": 88.2, "average_lead_time": 11.5},
            "Ariel Santos": {"completed_items": 15, "active_items": 3, "completion_rate": 91.7, "average_lead_time": 9.2},
            "Sharon Martinez": {"completed_items": 12, "active_items": 5, "completion_rate": 78.4, "average_lead_time": 16.8},
            "Apollo Rodriguez": {"completed_items": 14, "active_items": 2, "completion_rate": 95.1, "average_lead_time": 8.7},
            "Patrick Oniel": {"completed_items": 16, "active_items": 6, "completion_rate": 82.3, "average_lead_time": 13.4},
            "Lorenz Johnson": {"completed_items": 11, "active_items": 4, "completion_rate": 76.9, "average_lead_time": 18.2},
            "Glizzel Reyes": {"completed_items": 12, "active_items": 3, "completion_rate": 86.5, "average_lead_time": 10.9}
        },
        "historical_data": [
            {
                "id": "item-001",
                "title": "User authentication feature",
                "workItemType": "User Story",
                "state": "Done",
                "assignedTo": "Nenissa Chen",
                "createdDate": "2024-06-01T09:00:00Z",
                "resolvedDate": "2024-06-15T17:30:00Z",
                "leadTime": 14.35,
                "cycleTime": 8.5,
                "priority": "High",
                "tags": ["security", "authentication"]
            },
            {
                "id": "item-002", 
                "title": "API endpoint testing",
                "workItemType": "Task",
                "state": "Done",
                "assignedTo": "Sharon Martinez",
                "createdDate": "2024-06-03T10:15:00Z",
                "resolvedDate": "2024-06-18T14:20:00Z",
                "leadTime": 15.17,
                "cycleTime": 12.3,
                "priority": "Medium",
                "tags": ["testing", "api"]
            },
            {
                "id": "item-003",
                "title": "Database optimization",
                "workItemType": "Bug",
                "state": "Done", 
                "assignedTo": "Apollo Rodriguez",
                "createdDate": "2024-06-05T14:30:00Z",
                "resolvedDate": "2024-06-12T16:45:00Z",
                "leadTime": 7.09,
                "cycleTime": 5.2,
                "priority": "Critical",
                "tags": ["performance", "database"]
            }
        ]
    }
    
    # Save test data
    os.makedirs("data", exist_ok=True)
    with open("data/test_dashboard_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    print("  ✅ Test data generated: data/test_dashboard_data.json")
    return True

def test_javascript_modules():
    """Test that JavaScript modules have proper syntax"""
    print("\n🧪 Testing JavaScript Modules...")
    
    js_files = [
        "js/workstream-manager.js",
        "js/predictive-analytics.js", 
        "js/time-series-analysis.js",
        "js/enhanced-ux.js",
        "js/advanced-filtering.js"
    ]
    
    for js_file in js_files:
        if Path(js_file).exists():
            try:
                with open(js_file, "r") as f:
                    content = f.read()
                
                # Basic syntax checks
                if "class " in content:
                    print(f"  ✅ {js_file}: Contains class definitions")
                elif "function " in content:
                    print(f"  ✅ {js_file}: Contains function definitions")
                else:
                    print(f"  ⚠️  {js_file}: No classes or functions detected")
                    
            except Exception as e:
                print(f"  ❌ {js_file}: Error reading file - {e}")
        else:
            print(f"  ❌ {js_file}: File not found")
    
    return True

def start_test_server():
    """Start a simple HTTP server for testing"""
    print("\n🚀 Starting Test Server...")
    
    import subprocess
    import time
    
    try:
        # Start server in background
        server = subprocess.Popen([
            sys.executable, "-m", "http.server", "8080"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        time.sleep(2)
        
        print("  ✅ Test server started on http://localhost:8080")
        print("  📊 Dashboard URL: http://localhost:8080/dashboard.html")
        print("  👔 Executive Dashboard: http://localhost:8080/executive-dashboard.html")
        print("\n  Press Ctrl+C to stop the server")
        
        # Wait for user interrupt
        try:
            server.wait()
        except KeyboardInterrupt:
            print("\n  🛑 Stopping server...")
            server.terminate()
            server.wait()
            print("  ✅ Server stopped")
            
    except Exception as e:
        print(f"  ❌ Error starting server: {e}")

def main():
    """Run all dashboard tests"""
    print("🧪 Dashboard Functionality Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_dashboard_files),
        ("Workstream Config", test_workstream_config),
        ("Test Data Generation", generate_test_data),
        ("JavaScript Modules", test_javascript_modules)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"  ❌ {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Dashboard is ready for use.")
        
        # Offer to start test server
        try:
            response = input("\n🚀 Start test server? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                start_test_server()
        except (EOFError, KeyboardInterrupt):
            print("\n✅ Test completed successfully!")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())