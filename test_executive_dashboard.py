#!/usr/bin/env python3
"""
Test script for Executive Dashboard.
Validates executive dashboard functionality and CLI data integration.
"""

import subprocess
import sys
import time
from pathlib import Path


def test_executive_dashboard_html():
    """Test that executive dashboard HTML exists and has required elements."""
    print("🧪 Testing executive dashboard HTML...")
    
    try:
        dashboard_file = Path("executive-dashboard.html")
        if not dashboard_file.exists():
            print("❌ Executive dashboard HTML file not found")
            return False
            
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for required executive dashboard elements
        required_elements = [
            "ExecutiveDashboard",
            "deliverySpeed",
            "flowEfficiency", 
            "wipItems",
            "teamVelocity",
            "summaryText",
            "keyInsights",
            "cliData"  # CLI Data option we added
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"❌ Missing executive dashboard element: {element}")
                return False
                
        print("✅ Executive dashboard HTML structure valid")
        return True
        
    except Exception as e:
        print(f"❌ Executive dashboard HTML validation failed: {e}")
        return False


def test_executive_cli_data_integration():
    """Test that executive dashboard can load CLI data."""
    print("🧪 Testing executive dashboard CLI data integration...")
    
    try:
        dashboard_file = Path("executive-dashboard.html")
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for CLI data loading function
        required_functions = [
            "loadFromCLI",
            "case 'cliData':",
            "data/dashboard_data.json"
        ]
        
        for func in required_functions:
            if func not in content:
                print(f"❌ Missing CLI integration: {func}")
                return False
                
        print("✅ Executive dashboard CLI data integration present")
        return True
        
    except Exception as e:
        print(f"❌ Executive dashboard CLI integration test failed: {e}")
        return False


def main():
    """Run executive dashboard tests."""
    print("🧪 Executive Dashboard Test Suite")
    print("=" * 40)
    
    tests = [
        ("Executive HTML", test_executive_dashboard_html),
        ("CLI Integration", test_executive_cli_data_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
        
    print("\n" + "=" * 40)
    print("🧪 Executive Dashboard Test Results:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
        if not passed:
            all_passed = False
            
    print("=" * 40)
    
    if all_passed:
        print("🎉 Executive dashboard tests passed!")
        print("💡 The executive dashboard now has CLI data integration")
        print("💡 Use 'CLI Data' option to load generated metrics")
    else:
        print("❌ Some executive dashboard tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()