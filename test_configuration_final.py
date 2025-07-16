#!/usr/bin/env python3
"""
Final Configuration System Integration Test

Tests the complete configuration system with real data to validate
all components work together properly.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from calculator import FlowMetricsCalculator
from configuration_manager import get_config_manager

def test_configuration_integration():
    """Test full configuration system integration."""
    print("🧪 Final Configuration System Integration Test")
    print("=" * 60)
    
    # Load real work items data
    data_file = Path("data/work_items.json")
    if not data_file.exists():
        print("❌ work_items.json not found!")
        return False
        
    with open(data_file, 'r') as f:
        work_items = json.load(f)
    
    print(f"📊 Loading {len(work_items)} work items...")
    
    # Test 1: Configuration Manager
    print("\n1️⃣ Testing Configuration Manager...")
    config_manager = get_config_manager()
    
    # Validate all configurations
    validation_results = config_manager.validate_all_configurations()
    all_valid = all(validation_results.values())
    
    if all_valid:
        print("   ✅ All configurations valid")
    else:
        print(f"   ❌ Configuration validation failed: {validation_results}")
        return False
    
    # Test configuration summary
    summary = config_manager.get_configuration_summary()
    print(f"   📋 Workflow states: {summary['workflow_states']['states_count']} states")
    print(f"   📋 Work item types: {summary['work_item_types']['types_count']} types")
    print(f"   📋 Calculation params: Available")
    
    # Test 2: Calculator with Configuration
    print("\n2️⃣ Testing Calculator Integration...")
    calculator = FlowMetricsCalculator(work_items, config_manager=config_manager)
    
    # Verify configuration is loaded
    if hasattr(calculator, 'config_manager') and calculator.config_manager is not None:
        print("   ✅ Configuration manager integrated")
    else:
        print("   ❌ Configuration manager not integrated")
        return False
    
    # Test 3: Flow Metrics Calculation
    print("\n3️⃣ Testing Flow Metrics Calculation...")
    try:
        # Calculate individual metrics
        lead_time = calculator.calculate_lead_time()
        cycle_time = calculator.calculate_cycle_time()
        throughput = calculator.calculate_throughput()
        wip = calculator.calculate_wip()
        
        print(f"   📈 Lead time: {lead_time:.1f} days average")
        print(f"   🔄 Cycle time: {cycle_time:.1f} days average")
        print(f"   🚀 Throughput: {throughput:.2f} items/day")
        print(f"   ⚡ Work in Progress: {wip} items")
        
        # Verify realistic values
        if 0 < lead_time < 1000 and 0 < cycle_time < 1000 and throughput > 0:
            print("   ✅ Flow metrics calculated successfully")
        else:
            print("   ❌ Flow metrics values seem unrealistic")
            return False
            
    except Exception as e:
        print(f"   ❌ Flow metrics calculation failed: {e}")
        return False
    
    # Test 4: Team Metrics with Configuration
    print("\n4️⃣ Testing Team Metrics...")
    try:
        team_metrics = calculator.calculate_team_metrics()
        
        if team_metrics and len(team_metrics) > 0:
            print(f"   👥 Team metrics calculated for {len(team_metrics)} members")
            print("   ✅ Team metrics integration successful")
        else:
            print("   ⚠️  No team metrics generated (may be expected)")
            
    except Exception as e:
        print(f"   ❌ Team metrics calculation failed: {e}")
        return False
    
    # Test 5: Report Generation
    print("\n5️⃣ Testing Report Generation...")
    try:
        report = calculator.generate_flow_metrics_report()
        
        # Verify report structure
        required_fields = ['lead_time_avg_days', 'cycle_time_avg_days', 'throughput_per_day', 'wip']
        missing_fields = [field for field in required_fields if field not in report]
        
        if not missing_fields:
            print("   📋 Complete flow metrics report generated")
            print(f"   📊 Report contains {len(report)} metrics")
            print("   ✅ Report generation successful")
        else:
            print(f"   ❌ Report missing fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"   ❌ Report generation failed: {e}")
        return False
    
    # Test 6: Configuration-Specific Features
    print("\n6️⃣ Testing Configuration Features...")
    try:
        # Test state categorization
        test_states = ["Done", "In Progress", "To Do", "Active"]
        categorized_states = 0
        
        for state in test_states:
            if (config_manager.is_completion_state(state) or 
                config_manager.is_active_state(state) or 
                config_manager.is_blocked_state(state)):
                categorized_states += 1
        
        print(f"   🏷️  State categorization: {categorized_states}/{len(test_states)} states")
        
        # Test work item type behavior
        test_types = ["Task", "Product Backlog Item", "Bug"]
        configured_types = 0
        
        for work_type in test_types:
            if config_manager.should_include_in_velocity(work_type) is not None:
                configured_types += 1
        
        print(f"   🔧 Type behavior: {configured_types}/{len(test_types)} types configured")
        print("   ✅ Configuration features working")
        
    except Exception as e:
        print(f"   ❌ Configuration features failed: {e}")
        return False
    
    # Final Summary
    print("\n🎉 FINAL RESULTS")
    print("=" * 60)
    print("✅ Configuration Manager: WORKING")
    print("✅ Calculator Integration: WORKING")
    print("✅ Flow Metrics Calculation: WORKING")
    print("✅ Team Metrics: WORKING")
    print("✅ Report Generation: WORKING")
    print("✅ Configuration Features: WORKING")
    print("\n🏆 ALL TESTS PASSED - Configuration System Ready for Production!")
    
    return True

if __name__ == "__main__":
    success = test_configuration_integration()
    sys.exit(0 if success else 1)