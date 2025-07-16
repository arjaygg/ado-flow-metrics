#!/usr/bin/env python3
"""
Dependency Fix Validation Script
Validates that all critical dependency issues have been resolved.
"""

import sys
import importlib
from pathlib import Path

def test_critical_imports():
    """Test that all critical modules can be imported."""
    print("🔍 Testing Critical Imports...")
    
    critical_modules = [
        'pydantic',
        'pydantic_settings', 
        'src.config_manager',
        'src.calculator',
        'src.azure_devops_client',
        'src.data_storage',
        'src.models'
    ]
    
    for module in critical_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            return False
    
    return True

def test_pydantic_settings_functionality():
    """Test that pydantic_settings works correctly."""
    print("\n🔍 Testing Pydantic Settings Functionality...")
    
    try:
        from src.config_manager import FlowMetricsSettings, AzureDevOpsConfig
        
        # Test basic instantiation
        settings = FlowMetricsSettings()
        print("  ✅ FlowMetricsSettings instantiation")
        
        # Test environment variable override
        import os
        os.environ['AZURE_DEVOPS_PAT'] = 'test-token'
        ado_config = AzureDevOpsConfig(pat_token='original-token')
        assert ado_config.pat_token == 'test-token'
        print("  ✅ Environment variable override")
        
        # Clean up
        del os.environ['AZURE_DEVOPS_PAT']
        
        return True
    except Exception as e:
        print(f"  ❌ Pydantic settings test failed: {e}")
        return False

def test_configuration_loading():
    """Test that configuration loading works."""
    print("\n🔍 Testing Configuration Loading...")
    
    try:
        from src.config_manager import get_settings
        
        settings = get_settings()
        print(f"  ✅ Settings loaded: {type(settings).__name__}")
        
        # Test that stage definitions work
        assert 'active_states' in settings.stage_definitions
        assert len(settings.stage_definitions['active_states']) > 0
        print(f"  ✅ Stage definitions: {len(settings.stage_definitions['active_states'])} active states")
        
        return True
    except Exception as e:
        print(f"  ❌ Configuration loading failed: {e}")
        return False

def test_core_functionality():
    """Test that core application functionality works."""
    print("\n🔍 Testing Core Functionality...")
    
    try:
        from src.calculator import FlowMetricsCalculator
        from src.models import WorkItem
        from datetime import datetime
        
        # Test calculator instantiation with empty data
        calculator = FlowMetricsCalculator([])
        print("  ✅ FlowMetricsCalculator instantiation")
        
        # Test model creation
        work_item = WorkItem(
            id=1,
            title="Test Item",
            type="User Story",
            state="Active",
            assigned_to="test@example.com",
            created_date=datetime.now(),
            area_path="Test\\Area"
        )
        print("  ✅ WorkItem model creation")
        
        return True
    except Exception as e:
        print(f"  ❌ Core functionality test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Dependency Fix Validation")
    print("=" * 50)
    
    tests = [
        test_critical_imports,
        test_pydantic_settings_functionality, 
        test_configuration_loading,
        test_core_functionality
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 ALL DEPENDENCY FIXES VALIDATED!")
        print("✨ The project is ready for development and testing.")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())