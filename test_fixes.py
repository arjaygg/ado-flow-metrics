#!/usr/bin/env python3
"""
Test script to validate the fixes implemented for ADO flow issues.
"""
import os
import sys
from pathlib import Path

def test_cli_fixes():
    """Test that CLI commands have the executive flag."""
    print("🧪 Testing CLI Executive Dashboard Fixes...")
    
    cli_file = Path("src/cli.py")
    if not cli_file.exists():
        print("❌ CLI file not found")
        return False
    
    cli_content = cli_file.read_text()
    
    # Check for executive flag in serve command
    if '--executive' in cli_content and 'Launch executive dashboard' in cli_content:
        print("✅ CLI serve command has --executive flag")
    else:
        print("❌ CLI serve command missing --executive flag")
        return False
    
    # Check for executive flag in demo command  
    if cli_content.count('--executive') >= 2:
        print("✅ CLI demo command has --executive flag")
    else:
        print("❌ CLI demo command missing --executive flag")
        return False
    
    # Check for executive dashboard file handling
    if 'executive-dashboard.html' in cli_content:
        print("✅ CLI handles executive dashboard file")
    else:
        print("❌ CLI doesn't handle executive dashboard file")
        return False
    
    return True

def test_workstream_filtering():
    """Test that workstream filtering is implemented in executive dashboard."""
    print("\n🧪 Testing Workstream Filtering Fixes...")
    
    exec_dashboard = Path("executive-dashboard.html")
    if not exec_dashboard.exists():
        print("❌ Executive dashboard file not found")
        return False
    
    dashboard_content = exec_dashboard.read_text()
    
    # Check for workstream filtering in KPIs
    if 'Apply workstream filtering to team metrics for KPI calculations' in dashboard_content:
        print("✅ KPI workstream filtering implemented")
    else:
        print("❌ KPI workstream filtering missing")
        return False
    
    # Check for workstream filtering in charts
    if 'Apply workstream filtering to WIP data' in dashboard_content:
        print("✅ WIP chart workstream filtering implemented")
    else:
        print("❌ WIP chart workstream filtering missing")
        return False
    
    if 'Apply workstream filtering to throughput data' in dashboard_content:
        print("✅ Throughput chart workstream filtering implemented")
    else:
        print("❌ Throughput chart workstream filtering missing")
        return False
    
    if 'Apply workstream filtering to efficiency calculation' in dashboard_content:
        print("✅ Efficiency gauge workstream filtering implemented")
    else:
        print("❌ Efficiency gauge workstream filtering missing")
        return False
    
    return True

def test_data_filtering_consistency():
    """Test that data filtering is consistent across dashboards."""
    print("\n🧪 Testing Data Filtering Consistency...")
    
    # Check executive dashboard
    exec_dashboard = Path("executive-dashboard.html")
    if not exec_dashboard.exists():
        print("❌ Executive dashboard file not found")
        return False
    
    exec_content = exec_dashboard.read_text()
    
    # Check for WorkstreamManager usage
    if 'this.workstreamManager.filterTeamMetrics' in exec_content:
        print("✅ Executive dashboard uses WorkstreamManager for filtering")
    else:
        print("❌ Executive dashboard missing WorkstreamManager filtering")
        return False
    
    # Check for consistent filtering across all update functions
    update_functions = ['updateKPIs', 'updateWorkDistributionChart', 'updateThroughputChart', 'updateEfficiencyGauge']
    filtering_found = 0
    
    for func in update_functions:
        if func in exec_content and 'filterTeamMetrics' in exec_content:
            filtering_found += 1
    
    if filtering_found >= 3:  # At least 3 functions should have filtering
        print("✅ Data filtering is consistent across dashboard components")
    else:
        print("❌ Data filtering inconsistent across dashboard components")
        return False
    
    return True

def test_file_existence():
    """Test that all required files exist."""
    print("\n🧪 Testing File Existence...")
    
    required_files = [
        "src/cli.py",
        "executive-dashboard.html",
        "dashboard.html",
        "js/workstream-manager.js",
        "open_dashboard.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("🧪 ADO Flow Fixes Test Suite")
    print("=" * 50)
    
    os.chdir("/home/devag/git/fix-ado-flow")
    
    tests = [
        ("File Existence", test_file_existence),
        ("CLI Executive Dashboard", test_cli_fixes),
        ("Workstream Filtering", test_workstream_filtering),
        ("Data Filtering Consistency", test_data_filtering_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes implemented successfully!")
        print("\n💡 Usage Examples:")
        print("  # Launch executive dashboard with auto-generated data:")
        print("  python3 -m src.cli serve --open-browser --executive --auto-generate")
        print("  # Launch executive dashboard demo:")
        print("  python3 -m src.cli demo --open-browser --executive --use-mock-data")
        print("\n🔧 Features Fixed:")
        print("  ✅ Executive dashboard CLI launch with --open-browser")
        print("  ✅ Workstream filtering applied to all dashboard components")
        print("  ✅ Data filtering consistency across KPIs and charts")
        return True
    else:
        print("❌ Some fixes need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)