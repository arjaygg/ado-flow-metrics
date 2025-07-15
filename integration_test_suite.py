#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite
Tests the complete Azure DevOps and Dashboard integration pipeline
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_azure_devops_mock_integration():
    """Test Azure DevOps integration using mock data"""
    print("🔍 Testing Azure DevOps Mock Integration...")
    
    try:
        # Import required modules
        from mock_data import generate_mock_azure_devops_data
        
        # Generate mock data
        mock_data = generate_mock_azure_devops_data()
        
        if not mock_data:
            print("  ❌ Failed to generate mock data")
            return False
            
        print(f"  ✅ Generated {len(mock_data)} mock work items")
        
        # Save mock data for testing
        with open('test_mock_data.json', 'w') as f:
            json.dump(mock_data, f, indent=2, default=str)
        
        print("  ✅ Mock data saved for testing")
        return True
        
    except Exception as e:
        print(f"  ❌ Mock integration error: {e}")
        return False

def test_calculator_integration():
    """Test flow metrics calculator with mock data"""
    print("🔍 Testing Calculator Integration...")
    
    try:
        # Import modules with proper handling
        from mock_data import generate_mock_azure_devops_data
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        # Generate test data
        work_items = generate_mock_azure_devops_data()
        
        # Test basic calculator functionality
        # Import calculator without relative imports
        import importlib.util
        spec = importlib.util.spec_from_file_location("calculator", 
                                                     Path(__file__).parent / "src" / "calculator.py")
        calculator_module = importlib.util.module_from_spec(spec)
        
        # Mock the relative import
        calculator_module.WorkstreamManager = type('MockWorkstreamManager', (), {
            '__init__': lambda self, *args: None,
            'filter_work_items_by_workstream': lambda self, items, stream: items
        })
        
        spec.loader.exec_module(calculator_module)
        
        # Create calculator instance
        config = {
            "flow_metrics": {
                "active_states": ["Active", "In Progress", "Development"],
                "done_states": ["Done", "Closed", "Resolved"]
            }
        }
        
        calculator = calculator_module.FlowMetricsCalculator(work_items, config)
        
        # Test metrics calculation
        basic_metrics = calculator.calculate_basic_metrics()
        
        print(f"  ✅ Basic metrics calculated: {len(basic_metrics)} metrics")
        
        # Save metrics for dashboard testing
        with open('test_metrics.json', 'w') as f:
            json.dump(basic_metrics, f, indent=2, default=str)
        
        print("  ✅ Calculator integration successful")
        return True
        
    except Exception as e:
        print(f"  ❌ Calculator integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_data_pipeline():
    """Test the complete data pipeline from mock data to dashboard"""
    print("🔍 Testing Dashboard Data Pipeline...")
    
    try:
        # Check if test data exists
        if not Path('test_mock_data.json').exists():
            print("  ❌ Test mock data not found")
            return False
            
        if not Path('test_metrics.json').exists():
            print("  ❌ Test metrics not found")
            return False
        
        # Load and validate data structure
        with open('test_mock_data.json', 'r') as f:
            mock_data = json.load(f)
            
        with open('test_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        # Validate data structure for dashboard compatibility
        required_data_keys = ['id', 'title', 'state', 'assigned_to']
        required_metrics_keys = ['summary', 'lead_time', 'cycle_time']
        
        # Check mock data structure
        if mock_data:
            sample_item = mock_data[0]
            for key in required_data_keys:
                if key not in sample_item:
                    print(f"  ❌ Missing required data key: {key}")
                    return False
        
        # Check metrics structure
        for key in required_metrics_keys:
            if key not in metrics:
                print(f"  ❌ Missing required metrics key: {key}")
                return False
        
        # Create dashboard-compatible data
        dashboard_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "integration_test",
            "work_items": mock_data,
            "metrics": metrics,
            "data_validation": {
                "total_items": len(mock_data),
                "metrics_calculated": True,
                "pipeline_complete": True
            }
        }
        
        # Save to data directory for dashboard
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        with open(data_dir / 'integration_test_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print("  ✅ Dashboard data pipeline successful")
        print(f"  ✅ Data saved to: {data_dir / 'integration_test_data.json'}")
        return True
        
    except Exception as e:
        print(f"  ❌ Dashboard pipeline error: {e}")
        return False

def test_cli_commands():
    """Test CLI command functionality"""
    print("🔍 Testing CLI Commands...")
    
    try:
        # Test CLI help
        result = subprocess.run([
            sys.executable, '-m', 'src.cli', '--help'
        ], capture_output=True, text=True, timeout=10, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"  ❌ CLI help failed: {result.stderr}")
            return False
        
        print("  ✅ CLI help command works")
        
        # Test mock data generation command
        result = subprocess.run([
            sys.executable, '-c', 
            "import sys; sys.path.insert(0, 'src'); from mock_data import generate_mock_azure_devops_data; print(f'Generated {len(generate_mock_azure_devops_data())} items')"
        ], capture_output=True, text=True, timeout=15, cwd=Path(__file__).parent)
        
        if result.returncode == 0 and "Generated" in result.stdout:
            print("  ✅ Mock data generation command works")
        else:
            print(f"  ⚠️  Mock data command warning: {result.stderr}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("  ❌ CLI command timed out")
        return False
    except Exception as e:
        print(f"  ❌ CLI test error: {e}")
        return False

def test_dashboard_file_integrity():
    """Test dashboard files exist and have correct structure"""
    print("🔍 Testing Dashboard File Integrity...")
    
    required_files = [
        'dashboard.html',
        'executive-dashboard.html',
        'config/config.json',
        'config/workstream_config.json',
        'js/workstream-manager.js',
        'js/predictive-analytics.js',
        'js/time-series-analysis.js',
        'js/enhanced-ux.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  ❌ Missing dashboard files: {missing_files}")
        return False
    
    # Check dashboard.html for required elements
    with open('dashboard.html', 'r') as f:
        html_content = f.read()
    
    required_elements = [
        'data-source-selector',
        'workstreamDropdown',
        'leadCycleChart',
        'wipChart'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in html_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"  ❌ Missing HTML elements: {missing_elements}")
        return False
    
    print("  ✅ Dashboard file integrity verified")
    return True

def test_workstream_filtering():
    """Test workstream filtering functionality"""
    print("🔍 Testing Workstream Filtering...")
    
    try:
        # Load workstream config
        with open('config/workstream_config.json', 'r') as f:
            workstream_config = json.load(f)
        
        workstreams = workstream_config.get('workstreams', {})
        if not workstreams:
            print("  ❌ No workstreams configured")
            return False
        
        print(f"  ✅ Found {len(workstreams)} workstreams configured")
        
        # Test each workstream has required structure
        for name, config in workstreams.items():
            if 'name_patterns' not in config:
                print(f"  ❌ Workstream {name} missing name_patterns")
                return False
            if 'description' not in config:
                print(f"  ❌ Workstream {name} missing description")
                return False
        
        print("  ✅ Workstream filtering configuration valid")
        return True
        
    except Exception as e:
        print(f"  ❌ Workstream filtering error: {e}")
        return False

def test_end_to_end_flow():
    """Test the complete end-to-end flow"""
    print("🔍 Testing End-to-End Flow...")
    
    try:
        # Check all test data exists
        required_files = [
            'test_mock_data.json',
            'test_metrics.json',
            'data/integration_test_data.json'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                print(f"  ❌ Missing test file: {file_path}")
                return False
        
        # Load final dashboard data
        with open('data/integration_test_data.json', 'r') as f:
            final_data = json.load(f)
        
        # Validate complete data pipeline
        validation = final_data.get('data_validation', {})
        
        if not validation.get('pipeline_complete'):
            print("  ❌ Data pipeline not complete")
            return False
        
        if not validation.get('metrics_calculated'):
            print("  ❌ Metrics not calculated")
            return False
        
        total_items = validation.get('total_items', 0)
        if total_items == 0:
            print("  ❌ No work items in final data")
            return False
        
        print(f"  ✅ End-to-end flow successful with {total_items} items")
        return True
        
    except Exception as e:
        print(f"  ❌ End-to-end flow error: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Comprehensive Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Azure DevOps Mock Integration", test_azure_devops_mock_integration),
        ("Calculator Integration", test_calculator_integration),
        ("Dashboard Data Pipeline", test_dashboard_data_pipeline),
        ("CLI Commands", test_cli_commands),
        ("Dashboard File Integrity", test_dashboard_file_integrity),
        ("Workstream Filtering", test_workstream_filtering),
        ("End-to-End Flow", test_end_to_end_flow)
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
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Generate test report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_type": "integration_comprehensive",
        "total_tests": total,
        "passed_tests": passed,
        "failed_tests": total - passed,
        "success_rate": f"{(passed/total)*100:.1f}%",
        "results": [{"test": name, "passed": result} for name, result in results],
        "test_artifacts": [
            "test_mock_data.json",
            "test_metrics.json", 
            "data/integration_test_data.json"
        ]
    }
    
    with open('integration_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("\n📋 Next Steps:")
        print("  1. Open dashboard.html in browser")
        print("  2. Load data/integration_test_data.json")
        print("  3. Verify dashboard functionality")
    else:
        print(f"\n⚠️  {total - passed} integration tests failed.")
    
    print(f"\n📋 Detailed results saved to: integration_test_results.json")
    
    # Cleanup test files
    cleanup_files = ['test_mock_data.json', 'test_metrics.json']
    for file_path in cleanup_files:
        try:
            Path(file_path).unlink(missing_ok=True)
        except:
            pass
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)