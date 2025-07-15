#!/usr/bin/env python3
"""
Simple test to verify calculator configuration integration.
"""

import sys
import os
from pathlib import Path

# Set up the path
sys.path.insert(0, str(Path(__file__).parent / "src"))
os.chdir(Path(__file__).parent)

try:
    # Test configuration manager
    from configuration_manager import ConfigurationManager
    config_manager = ConfigurationManager()
    
    print("✅ Configuration Manager loaded successfully")
    
    # Test workflow states
    workflow_states = config_manager.get_workflow_states()
    print(f"✅ Workflow states loaded: {len(workflow_states.get('stateCategories', {}))} categories")
    
    # Test work item types
    work_item_types = config_manager.get_work_item_types()
    print(f"✅ Work item types loaded: {len(work_item_types.get('work_item_types', {}))} types")
    
    # Test calculation parameters
    calc_params = config_manager.get_calculation_parameters()
    print(f"✅ Calculation parameters loaded: {bool(calc_params.get('flow_metrics'))}")
    
    # Test specific configurations
    active_states = []
    completion_states = []
    
    # Extract states manually to test the configuration structure
    state_categories = workflow_states.get('stateCategories', {})
    for category_name, category_data in state_categories.items():
        if category_data.get('isActive', False) and not category_data.get('isCompletedState', False):
            active_states.extend(category_data.get('states', []))
        if category_data.get('isCompletedState', False):
            completion_states.extend(category_data.get('states', []))
    
    print(f"✅ Active states extracted: {len(active_states)}")
    print(f"✅ Completion states extracted: {len(completion_states)}")
    
    # Test work item type behavior
    for item_type in ["Task", "Bug", "Product Backlog Item"]:
        include_velocity = config_manager.should_include_in_velocity(item_type)
        include_throughput = config_manager.should_include_in_throughput(item_type)
        complexity = config_manager.get_type_complexity_multiplier(item_type)
        
        print(f"✅ {item_type}: velocity={include_velocity}, throughput={include_throughput}, complexity={complexity}")
    
    print(f"\n🎉 Configuration integration tests completed successfully!")
    print(f"📊 Ready for calculator integration")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)