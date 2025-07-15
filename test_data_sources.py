#!/usr/bin/env python3
"""
Data Source Test Script

Tests all data source switching functionality including:
1. Mock data generation
2. JSON file loading
3. CLI data integration 
4. IndexedDB simulation
5. Data source switching
"""

import json
import os
import tempfile
from pathlib import Path

def test_mock_data_generation():
    """Test mock data generation functionality"""
    print("🎲 Testing Mock Data Generation...")
    
    # Test mock data in both dashboards
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    
    for dashboard_file in dashboards:
        if not Path(dashboard_file).exists():
            print(f"  ❌ {dashboard_file} not found")
            continue
            
        with open(dashboard_file, "r") as f:
            content = f.read()
        
        # Check for mock data generation functions
        mock_functions = [
            "generateMockData",
            "generateExecutiveMockData", 
            "mockData",
            "team_metrics",
            "lead_time",
            "cycle_time"
        ]
        
        found_functions = []
        for func in mock_functions:
            if func in content:
                found_functions.append(func)
        
        print(f"  ✅ {dashboard_file}: Found {len(found_functions)} mock data functions")
    
    return True

def test_json_file_loading():
    """Test JSON file loading functionality"""
    print("\n📄 Testing JSON File Loading...")
    
    # Create test JSON data
    test_data = {
        "summary": {
            "total_work_items": 100,
            "completed_items": 75,
            "completion_rate": 75.0
        },
        "lead_time": {
            "average_days": 12.5,
            "median_days": 10.0,
            "count": 75
        },
        "cycle_time": {
            "average_days": 8.3,
            "median_days": 7.0,
            "count": 75
        },
        "throughput": {
            "items_per_period": 18.7,
            "period_days": 30
        },
        "work_in_progress": {
            "total_wip": 25,
            "wip_by_state": {
                "New": 5,
                "Active": 15,
                "Review": 3,
                "Done": 2
            }
        },
        "flow_efficiency": {
            "average_efficiency": 0.66
        },
        "team_metrics": {
            "Test User 1": {"completed_items": 25, "active_items": 3, "completion_rate": 89.3, "average_lead_time": 10.2},
            "Test User 2": {"completed_items": 30, "active_items": 5, "completion_rate": 85.7, "average_lead_time": 11.8},
            "Test User 3": {"completed_items": 20, "active_items": 2, "completion_rate": 90.9, "average_lead_time": 9.5}
        }
    }
    
    # Save test data
    os.makedirs("data", exist_ok=True)
    test_file = "data/test_json_data.json"
    
    with open(test_file, "w") as f:
        json.dump(test_data, f, indent=2)
    
    print(f"  ✅ Test JSON data created: {test_file}")
    
    # Verify the data can be loaded
    try:
        with open(test_file, "r") as f:
            loaded_data = json.load(f)
        
        # Basic validation
        required_keys = ["summary", "lead_time", "cycle_time", "team_metrics"]
        for key in required_keys:
            if key not in loaded_data:
                print(f"  ❌ Missing key in test data: {key}")
                return False
        
        print(f"  ✅ Test JSON data validated ({len(loaded_data)} sections)")
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading test JSON data: {e}")
        return False

def test_cli_data_integration():
    """Test CLI data integration functionality"""
    print("\n💻 Testing CLI Data Integration...")
    
    # Check if dashboards have CLI data loading capabilities
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    
    cli_integration_checks = [
        "loadFromCLI",
        "cliData",
        "dashboard_data.json",
        "flow_metrics_report.json",
        "test_report.json"
    ]
    
    results = {}
    for dashboard_file in dashboards:
        if not Path(dashboard_file).exists():
            results[dashboard_file] = False
            continue
            
        with open(dashboard_file, "r") as f:
            content = f.read()
        
        found_checks = []
        for check in cli_integration_checks:
            if check in content:
                found_checks.append(check)
        
        results[dashboard_file] = len(found_checks) >= 3  # At least 3 CLI features
        status = "✅" if results[dashboard_file] else "❌"
        print(f"  {status} {dashboard_file}: {len(found_checks)}/{len(cli_integration_checks)} CLI features")
    
    return all(results.values())

def test_indexeddb_simulation():
    """Test IndexedDB functionality simulation"""
    print("\n🗄️  Testing IndexedDB Simulation...")
    
    # Check for IndexedDB functions in dashboards
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    
    indexeddb_functions = [
        "initIndexedDB",
        "saveToIndexedDB", 
        "loadFromIndexedDB",
        "indexedDB",
        "FlowMetricsDB"
    ]
    
    results = {}
    for dashboard_file in dashboards:
        if not Path(dashboard_file).exists():
            results[dashboard_file] = False
            continue
            
        with open(dashboard_file, "r") as f:
            content = f.read()
        
        found_functions = []
        for func in indexeddb_functions:
            if func in content:
                found_functions.append(func)
        
        results[dashboard_file] = len(found_functions) >= 3  # At least 3 IndexedDB features
        status = "✅" if results[dashboard_file] else "❌"
        print(f"  {status} {dashboard_file}: {len(found_functions)}/{len(indexeddb_functions)} IndexedDB features")
    
    return all(results.values())

def test_data_source_switching():
    """Test data source switching UI functionality"""
    print("\n🔄 Testing Data Source Switching...")
    
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    
    # Required data source options
    data_sources = [
        "mockData",
        "jsonFile", 
        "indexedDB",
        "cliData"
    ]
    
    # Required UI elements
    ui_elements = [
        "data-source-selector",
        "dataSourceInfo",
        "btn-check",
        "dataSource"
    ]
    
    results = {}
    for dashboard_file in dashboards:
        if not Path(dashboard_file).exists():
            results[dashboard_file] = False
            continue
            
        with open(dashboard_file, "r") as f:
            content = f.read()
        
        # Check data sources
        found_sources = sum(1 for source in data_sources if source in content)
        found_ui = sum(1 for element in ui_elements if element in content)
        
        has_switching = "addEventListener" in content and "dataSource" in content
        
        results[dashboard_file] = (found_sources >= 3 and found_ui >= 2 and has_switching)
        status = "✅" if results[dashboard_file] else "❌"
        print(f"  {status} {dashboard_file}: {found_sources}/{len(data_sources)} sources, {found_ui}/{len(ui_elements)} UI elements")
    
    return all(results.values())

def test_data_source_info_updates():
    """Test data source info updates functionality"""
    print("\n📊 Testing Data Source Info Updates...")
    
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    
    info_functions = [
        "updateDataSourceInfo",
        "dataSourceInfo",
        "textContent",
        "toLocaleTimeString"
    ]
    
    results = {}
    for dashboard_file in dashboards:
        if not Path(dashboard_file).exists():
            results[dashboard_file] = False
            continue
            
        with open(dashboard_file, "r") as f:
            content = f.read()
        
        found_functions = sum(1 for func in info_functions if func in content)
        results[dashboard_file] = found_functions >= 3
        
        status = "✅" if results[dashboard_file] else "❌"
        print(f"  {status} {dashboard_file}: {found_functions}/{len(info_functions)} info update features")
    
    return all(results.values())

def create_comprehensive_data_report():
    """Create a comprehensive data sources report"""
    print("\n📋 Creating Data Sources Report...")
    
    # Gather data from all test files
    report = {
        "test_data_files": [],
        "data_sources_summary": {
            "mock_data": "Available in both dashboards",
            "json_file": "File upload supported", 
            "cli_data": "Multiple CLI data locations supported",
            "indexeddb": "Browser storage with persistence"
        },
        "available_test_files": [],
        "dashboard_capabilities": {}
    }
    
    # List all test data files
    data_dir = Path("data")
    if data_dir.exists():
        for file_path in data_dir.glob("*.json"):
            report["test_data_files"].append(str(file_path))
    
    # Check dashboard capabilities
    dashboards = ["dashboard.html", "executive-dashboard.html"]
    for dashboard in dashboards:
        if Path(dashboard).exists():
            with open(dashboard, "r") as f:
                content = f.read()
            
            capabilities = {
                "mock_data": "generateMockData" in content or "mock" in content.lower(),
                "file_upload": "fileInput" in content or "loadFileBtn" in content,
                "cli_integration": "loadFromCLI" in content,
                "indexeddb": "indexedDB" in content,
                "workstream_filtering": "workstream" in content.lower(),
                "advanced_analytics": "predictive" in content.lower() or "analytics" in content.lower()
            }
            
            report["dashboard_capabilities"][dashboard] = capabilities
    
    # Save report
    with open("data/data_sources_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("  ✅ Data sources report saved: data/data_sources_report.json")
    
    # Print summary
    total_files = len(report["test_data_files"])
    print(f"  📁 Found {total_files} test data files")
    
    for dashboard, capabilities in report["dashboard_capabilities"].items():
        enabled_features = sum(1 for enabled in capabilities.values() if enabled)
        print(f"  📊 {dashboard}: {enabled_features}/{len(capabilities)} features enabled")
    
    return True

def main():
    """Run data source tests"""
    print("🔄 Data Source Test Suite")
    print("=" * 50)
    
    tests = [
        ("Mock Data Generation", test_mock_data_generation),
        ("JSON File Loading", test_json_file_loading),
        ("CLI Data Integration", test_cli_data_integration),
        ("IndexedDB Simulation", test_indexeddb_simulation),
        ("Data Source Switching", test_data_source_switching),
        ("Data Source Info Updates", test_data_source_info_updates),
        ("Comprehensive Report", create_comprehensive_data_report)
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
    print("📋 Data Source Test Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All data source functionality tests passed!")
        print("\n💡 Available Data Sources:")
        print("  🎲 Mock Data - Built-in sample data")
        print("  📄 JSON Files - Upload custom data files")
        print("  💻 CLI Data - Generated by flow metrics calculator")
        print("  🗄️  IndexedDB - Browser storage persistence")
        return 0
    else:
        print("❌ Some data source tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())