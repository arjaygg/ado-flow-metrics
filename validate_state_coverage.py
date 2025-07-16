#!/usr/bin/env python3
"""
Validate State Coverage - Verify all states from work_items.json are covered in configuration

This script validates that the workflow_states.json configuration covers all states
found in the actual work_items.json data.
"""

import json
import sys
from pathlib import Path
from src.state_mapper import StateMapper


def extract_states_from_data(data_file: Path) -> set:
    """Extract all unique states from work_items.json data."""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    states = set()
    
    for item in data:
        # Add current_state
        if 'current_state' in item and item['current_state']:
            states.add(item['current_state'])
        
        # Add states from state_transitions
        if 'state_transitions' in item:
            for transition in item['state_transitions']:
                if 'state' in transition and transition['state']:
                    states.add(transition['state'])
    
    return states


def main():
    """Main validation function."""
    print("State Coverage Validation")
    print("=" * 50)
    
    # Paths
    data_file = Path("data/work_items.json")
    config_file = Path("config/workflow_states.json")
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False
    
    # Extract states from data
    print("📊 Extracting states from data...")
    data_states = extract_states_from_data(data_file)
    print(f"   Found {len(data_states)} unique states in data")
    
    # Load configured states
    print("🔧 Loading configured states...")
    mapper = StateMapper(str(config_file))
    configured_states = set(mapper.state_to_category.keys())
    print(f"   Found {len(configured_states)} states in configuration")
    
    # Find missing states
    missing_from_config = data_states - configured_states
    extra_in_config = configured_states - data_states
    
    # Report results
    print("\n📋 Validation Results:")
    print("-" * 30)
    
    if not missing_from_config:
        print("✅ All data states are covered in configuration")
    else:
        print(f"❌ {len(missing_from_config)} states found in data but missing from config:")
        for state in sorted(missing_from_config):
            print(f"   - '{state}'")
    
    if extra_in_config:
        print(f"\n⚠️  {len(extra_in_config)} states in config but not found in data:")
        for state in sorted(extra_in_config):
            print(f"   - '{state}'")
    
    # Coverage statistics
    coverage_pct = (len(data_states & configured_states) / len(data_states)) * 100
    print(f"\n📈 Coverage Statistics:")
    print(f"   Coverage: {coverage_pct:.1f}% ({len(data_states & configured_states)}/{len(data_states)})")
    print(f"   Data states: {len(data_states)}")
    print(f"   Configured states: {len(configured_states)}")
    print(f"   Overlap: {len(data_states & configured_states)}")
    
    # Test state mapping for sample data states
    print(f"\n🧪 Testing state mapping for sample states:")
    sample_states = list(data_states)[:5]
    for state in sample_states:
        category = mapper.get_state_category(state)
        is_active = mapper.is_active_state(state)
        is_blocked = mapper.is_blocked_state(state)
        print(f"   '{state}' → {category} (active: {is_active}, blocked: {is_blocked})")
    
    # Return success status
    success = len(missing_from_config) == 0
    print(f"\n{'✅ VALIDATION PASSED' if success else '❌ VALIDATION FAILED'}")
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)