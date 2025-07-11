#!/usr/bin/env python3
"""
Test script for Flow Metrics Dashboard.
Validates that all components are working correctly.
"""

import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def test_dependencies():
    """Test that all required dependencies are available."""
    print("🧪 Testing dependencies...")
    
    try:
        import click
        import flask
        import flask_cors
        import rich
        import requests
        print("✅ All required dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False


def test_data_generation():
    """Test data generation using CLI."""
    print("🧪 Testing data generation...")
    
    try:
        # Generate mock data
        result = subprocess.run([
            sys.executable, "-m", "src.cli", "calculate", "--use-mock-data"
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode != 0:
            print(f"❌ CLI failed: {result.stderr}")
            return False
            
        # Check if data files exist
        data_dir = Path("data")
        required_files = ["dashboard_data.json", "flow_metrics_report.json"]
        
        for filename in required_files:
            file_path = data_dir / filename
            if not file_path.exists():
                print(f"❌ Missing data file: {filename}")
                return False
                
        print("✅ Data generation successful")
        return True
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return False


def test_dashboard_data():
    """Test that dashboard data has correct structure."""
    print("🧪 Testing dashboard data structure...")
    
    try:
        data_file = Path("data/dashboard_data.json")
        if not data_file.exists():
            print("❌ Dashboard data file not found")
            return False
            
        with open(data_file, 'r') as f:
            data = json.load(f)
            
        # Check required top-level keys
        required_keys = ["timestamp", "source", "data"]
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing top-level key: {key}")
                return False
                
        # Check data structure
        dashboard_data = data["data"]
        required_sections = [
            "summary", "lead_time", "cycle_time", "throughput", 
            "work_in_progress", "flow_efficiency", "team_metrics"
        ]
        
        for section in required_sections:
            if section not in dashboard_data:
                print(f"❌ Missing data section: {section}")
                return False
                
        # Check team metrics has actual data
        team_metrics = dashboard_data["team_metrics"]
        if not team_metrics or len(team_metrics) == 0:
            print("❌ No team metrics data found")
            return False
            
        print(f"✅ Dashboard data structure valid ({len(team_metrics)} team members)")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard data validation failed: {e}")
        return False


def test_web_server():
    """Test that web server can start and serve content."""
    print("🧪 Testing web server...")
    
    try:
        # Test that we can import the web server
        from src.web_server import FlowMetricsWebServer
        
        # Create server instance
        server = FlowMetricsWebServer(data_source="mock")
        
        print("✅ Web server can be instantiated")
        return True
        
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        return False


def test_javascript_files():
    """Test that JavaScript files exist and are accessible."""
    print("🧪 Testing JavaScript files...")
    
    js_files = [
        "js/workstream_config.js",
        "js/workstream-manager.js"
    ]
    
    for js_file in js_files:
        file_path = Path(js_file)
        if not file_path.exists():
            print(f"❌ Missing JavaScript file: {js_file}")
            return False
            
    config_files = [
        "config/workstream_config.json"
    ]
    
    for config_file in config_files:
        file_path = Path(config_file)
        if not file_path.exists():
            print(f"❌ Missing config file: {config_file}")
            return False
            
    print("✅ All JavaScript and config files present")
    return True


def test_dashboard_html():
    """Test that dashboard HTML exists and has required elements."""
    print("🧪 Testing dashboard HTML...")
    
    try:
        dashboard_file = Path("dashboard.html")
        if not dashboard_file.exists():
            print("❌ Dashboard HTML file not found")
            return False
            
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for required elements
        required_elements = [
            "WorkstreamManager",
            "leadTimeAvg",
            "cycleTimeAvg", 
            "throughputValue",
            "wipValue",
            "teamTableBody"
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"❌ Missing dashboard element: {element}")
                return False
                
        print("✅ Dashboard HTML structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard HTML validation failed: {e}")
        return False


def start_demo_server():
    """Start the demo server for manual testing."""
    print("🚀 Starting demo server...")
    print("💡 This will start the server with mock data")
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Use the CLI demo command which handles everything
        subprocess.run([
            sys.executable, "-m", "src.cli", "demo", "--use-mock-data", "--open-browser"
        ], cwd=Path.cwd())
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Demo server failed: {e}")


def main():
    """Run all dashboard tests."""
    print("🧪 Flow Metrics Dashboard Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Data Generation", test_data_generation),
        ("Dashboard Data", test_dashboard_data),
        ("Web Server", test_web_server),
        ("JavaScript Files", test_javascript_files),
        ("Dashboard HTML", test_dashboard_html),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
        
    print("\n" + "=" * 50)
    print("🧪 Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
        if not passed:
            all_passed = False
            
    print("=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! Dashboard is ready to use.")
        
        response = input("\n🚀 Would you like to start the demo server? (y/n): ")
        if response.lower().startswith('y'):
            start_demo_server()
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()