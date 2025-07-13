#!/usr/bin/env python3
"""
Comprehensive Post-Rebase Test Suite
Tests all dashboard functionality after successful rebase of advanced filtering with predictive analytics
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

def test_file_structure():
    """Test that all required files exist after rebase"""
    print("🔍 Testing file structure...")
    
    required_files = [
        'dashboard.html',
        'executive-dashboard.html',
        'config/config.json',
        'config/workstream_config.json',
        'src/azure_devops_client.py',
        'src/cli.py',
        'src/calculator.py',
        'js/workstream-manager.js',
        'js/predictive-analytics.js',
        'js/time-series-analysis.js',
        'js/enhanced-ux.js',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_javascript_modules():
    """Test that new JavaScript modules are properly integrated"""
    print("🔍 Testing JavaScript module integration...")
    
    with open('dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for predictive analytics modules
    required_scripts = [
        'js/predictive-analytics.js',
        'js/time-series-analysis.js', 
        'js/enhanced-ux.js',
        'js/workstream-manager.js'
    ]
    
    missing_scripts = []
    for script in required_scripts:
        if f'src="{script}"' not in content:
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Missing script references: {missing_scripts}")
        return False
    
    # Check for class instantiations
    required_classes = [
        'new PredictiveAnalytics()',
        'new TimeSeriesAnalyzer()',
        'new EnhancedUX()',
        'new WorkstreamManager()'
    ]
    
    missing_classes = []
    for class_ref in required_classes:
        if class_ref not in content:
            missing_classes.append(class_ref)
    
    if missing_classes:
        print(f"❌ Missing class instantiations: {missing_classes}")
        return False
    
    print("✅ JavaScript modules properly integrated")
    return True

def test_configuration():
    """Test configuration files are valid and updated"""
    print("🔍 Testing configuration...")
    
    try:
        # Test main config
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        
        # Check for Azure DevOps config
        if 'azure_devops' not in config:
            print("❌ Missing azure_devops configuration")
            return False
        
        azure_config = config['azure_devops']
        required_keys = ['org_url', 'default_project', 'pat_token']
        for key in required_keys:
            if key not in azure_config:
                print(f"❌ Missing Azure DevOps config key: {key}")
                return False
        
        # Test workstream config
        with open('config/workstream_config.json', 'r') as f:
            workstream_config = json.load(f)
        
        if 'workstreams' not in workstream_config:
            print("❌ Missing workstreams configuration in workstream_config.json")
            return False
        
        print("✅ Configuration files valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

def test_dashboard_html_structure():
    """Test dashboard HTML structure contains all required elements"""
    print("🔍 Testing dashboard HTML structure...")
    
    with open('dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for key HTML elements (actual IDs from dashboard)
    required_elements = [
        'data-source-selector',
        'workstreamDropdown',
        'leadCycleChart',
        'wipChart', 
        'teamChart',
        'efficiencyChart',
        'forecastChart',
        'velocityTrendChart',
        'movingAveragesChart',
        'periodComparisonChart'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing HTML elements: {missing_elements}")
        return False
    
    print("✅ Dashboard HTML structure complete")
    return True

def test_executive_dashboard():
    """Test executive dashboard exists and has required structure"""
    print("🔍 Testing executive dashboard...")
    
    if not os.path.exists('executive-dashboard.html'):
        print("❌ Executive dashboard file missing")
        return False
    
    with open('executive-dashboard.html', 'r') as f:
        content = f.read()
    
    # Check for executive-specific elements (actual elements from executive dashboard)
    required_elements = [
        'nav-overview',
        'nav-workitems',
        'dataSourceInfo',
        'refreshBtn',
        'loadDataBtn'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Missing executive dashboard elements: {missing_elements}")
        return False
    
    print("✅ Executive dashboard structure complete")
    return True

def test_python_modules():
    """Test Python modules are present and syntactically correct"""
    print("🔍 Testing Python modules...")
    
    python_files = [
        'src/azure_devops_client.py',
        'src/cli.py',
        'src/calculator.py',
        'src/mock_data.py'
    ]
    
    for py_file in python_files:
        if not os.path.exists(py_file):
            print(f"❌ Missing Python file: {py_file}")
            return False
        
        # Test syntax
        try:
            with open(py_file, 'r') as f:
                code = f.read()
            compile(code, py_file, 'exec')
        except SyntaxError as e:
            print(f"❌ Syntax error in {py_file}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking {py_file}: {e}")
            return False
    
    print("✅ Python modules syntax valid")
    return True

def test_cli_functionality():
    """Test CLI commands are available"""
    print("🔍 Testing CLI functionality...")
    
    try:
        # Test CLI help command
        result = subprocess.run([
            sys.executable, '-m', 'src.cli', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ CLI help command failed: {result.stderr}")
            return False
        
        # Check if basic commands are listed
        if 'data' not in result.stdout:
            print("❌ CLI missing 'data' command")
            return False
        
        print("✅ CLI functionality available")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ CLI command timed out")
        return False
    except Exception as e:
        print(f"❌ CLI test error: {e}")
        return False

def test_workstream_filtering():
    """Test workstream filtering configuration"""
    print("🔍 Testing workstream filtering...")
    
    try:
        with open('config/workstream_config.json', 'r') as f:
            config = json.load(f)
        
        workstreams = config.get('workstreams', {})
        if not workstreams:
            print("❌ No workstreams configured")
            return False
        
        # Test each workstream has required structure
        for workstream_name, workstream_config in workstreams.items():
            if 'name_patterns' not in workstream_config:
                print(f"❌ Workstream {workstream_name} missing name_patterns")
                return False
            
            if 'description' not in workstream_config:
                print(f"❌ Workstream {workstream_name} missing description")
                return False
        
        print(f"✅ Workstream filtering configured for {len(workstreams)} workstreams")
        return True
        
    except Exception as e:
        print(f"❌ Workstream filtering test error: {e}")
        return False

def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("🚀 Starting Post-Rebase Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("JavaScript Modules", test_javascript_modules),
        ("Configuration", test_configuration),
        ("Dashboard HTML", test_dashboard_html_structure),
        ("Executive Dashboard", test_executive_dashboard),
        ("Python Modules", test_python_modules),
        ("CLI Functionality", test_cli_functionality),
        ("Workstream Filtering", test_workstream_filtering)
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Rebase integration successful!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Review issues above.")
    
    # Generate test report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_type": "post_rebase_comprehensive",
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": total - passed,
        "success_rate": f"{(passed/total)*100:.1f}%",
        "results": [{"test": name, "passed": result} for name, result in results]
    }
    
    with open('post_rebase_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📋 Detailed results saved to: post_rebase_test_results.json")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)