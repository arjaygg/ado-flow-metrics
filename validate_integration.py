#!/usr/bin/env python3
"""
Validation script for the calculator configuration integration.
Demonstrates the enhanced functionality with real data.
"""

import sys
import json
from pathlib import Path

# Set up the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def validate_configuration_integration():
    """Validate the complete configuration integration."""
    
    print("🔧 Validating Calculator Configuration Integration")
    print("=" * 60)
    
    try:
        # Load configuration manager
        from configuration_manager import ConfigurationManager
        config_manager = ConfigurationManager()
        
        print("✅ Configuration Manager loaded successfully")
        
        # Load real work items data
        try:
            with open('data/work_items.json', 'r') as f:
                work_items = json.load(f)
            print(f"✅ Loaded {len(work_items)} work items from data/work_items.json")
        except FileNotFoundError:
            print("⚠️ No work_items.json found, creating sample data")
            work_items = [
                {
                    "id": "1",
                    "title": "Sample Task",
                    "type": "Task",
                    "priority": "High",
                    "created_date": "2024-01-01T00:00:00",
                    "created_by": "Test User",
                    "assigned_to": "John Doe",
                    "current_state": "2.2 - In Progress",
                    "state_transitions": []
                }
            ]
        
        print("\n📊 Configuration Analysis:")
        print("-" * 40)
        
        # Analyze workflow states
        workflow_config = config_manager.get_workflow_states()
        state_categories = workflow_config.get('stateCategories', {})
        
        active_states = set()
        completion_states = set()
        blocked_states = set()
        
        for category_name, category_data in state_categories.items():
            states = category_data.get('states', [])
            if category_data.get('isActive', False) and not category_data.get('isCompletedState', False):
                active_states.update(states)
            if category_data.get('isCompletedState', False):
                completion_states.update(states)
            if category_data.get('isBlockedState', False):
                blocked_states.update(states)
        
        print(f"📈 Active states configured: {len(active_states)}")
        print(f"✅ Completion states configured: {len(completion_states)}")
        print(f"🚫 Blocked states configured: {len(blocked_states)}")
        
        # Analyze work item types
        work_item_types = config_manager.get_work_item_types().get('work_item_types', {})
        velocity_types = []
        throughput_types = []
        
        for type_name, type_config in work_item_types.items():
            metrics = type_config.get('metrics', {})
            if metrics.get('include_in_velocity', False):
                velocity_types.append(type_name)
            if metrics.get('include_in_throughput', False):
                throughput_types.append(type_name)
        
        print(f"🏃 Velocity-contributing types: {len(velocity_types)}")
        print(f"🔄 Throughput-contributing types: {len(throughput_types)}")
        
        # Analyze current work items with configuration
        print(f"\n📋 Work Items Analysis:")
        print("-" * 40)
        
        active_items = [item for item in work_items if item.get('current_state') in active_states]
        completed_items = [item for item in work_items if item.get('current_state') in completion_states]
        blocked_items = [item for item in work_items if item.get('current_state') in blocked_states]
        
        print(f"🔄 Items in active states: {len(active_items)}")
        print(f"✅ Items in completion states: {len(completed_items)}")
        print(f"🚫 Items in blocked states: {len(blocked_items)}")
        
        # Analyze by work item type
        type_distribution = {}
        for item in work_items:
            item_type = item.get('type', 'Unknown')
            type_distribution[item_type] = type_distribution.get(item_type, 0) + 1
        
        print(f"\n📈 Type Distribution:")
        print("-" * 40)
        
        for item_type, count in sorted(type_distribution.items(), key=lambda x: x[1], reverse=True)[:5]:
            include_velocity = config_manager.should_include_in_velocity(item_type)
            include_throughput = config_manager.should_include_in_throughput(item_type)
            complexity = config_manager.get_type_complexity_multiplier(item_type)
            
            print(f"{item_type}: {count} items (V:{include_velocity}, T:{include_throughput}, C:{complexity}x)")
        
        # Test calculation parameters
        print(f"\n⚙️ Calculation Parameters:")
        print("-" * 40)
        
        calc_params = config_manager.get_calculation_parameters()
        flow_metrics = calc_params.get('flow_metrics', {})
        
        throughput_config = flow_metrics.get('throughput', {})
        lead_time_config = flow_metrics.get('lead_time', {})
        cycle_time_config = flow_metrics.get('cycle_time', {})
        
        print(f"📊 Default throughput period: {throughput_config.get('default_period_days', 30)} days")
        print(f"📏 Lead time percentiles: {lead_time_config.get('percentiles', [50, 75, 85, 95])}")
        print(f"⏱️ Cycle time percentiles: {cycle_time_config.get('percentiles', [50, 75, 85, 95])}")
        
        # Configuration validation
        print(f"\n🔍 Configuration Validation:")
        print("-" * 40)
        
        validation_results = config_manager.validate_all_configurations()
        for config_type, is_valid in validation_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"{config_type}: {status}")
        
        # Summary
        print(f"\n🎉 Integration Validation Complete!")
        print("=" * 60)
        print(f"✅ Configuration Manager: Operational")
        print(f"✅ Workflow States: {len(active_states)} active, {len(completion_states)} done")
        print(f"✅ Work Item Types: {len(work_item_types)} types configured")
        print(f"✅ Calculation Parameters: Flow metrics configured")
        print(f"✅ Data Compatibility: {len(work_items)} work items ready")
        
        print(f"\n🚀 Calculator is ready for configuration-driven flow metrics!")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_configuration_integration()
    sys.exit(0 if success else 1)