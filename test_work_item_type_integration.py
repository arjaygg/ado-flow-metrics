#!/usr/bin/env python3
"""
Work Item Type Integration Test

Demonstrates integration of work item type configuration
with the flow metrics calculator.
"""

import json
import os
from src.work_item_type_mapper import create_type_mapper


def test_type_mapper_basic():
    """Test basic type mapper functionality"""
    print("🧪 Testing WorkItemTypeMapper Basic Functionality")
    print("-" * 60)
    
    mapper = create_type_mapper()
    
    # Test type list
    all_types = mapper.get_all_types()
    print(f"✅ Total types loaded: {len(all_types)}")
    
    # Test velocity types
    velocity_types = mapper.get_velocity_types()
    print(f"✅ Velocity types: {velocity_types}")
    
    # Test throughput types
    throughput_types = mapper.get_throughput_types()
    print(f"✅ Throughput types count: {len(throughput_types)}")
    
    # Test categorization
    categories = set(mapper.get_category(t) for t in all_types)
    print(f"✅ Categories: {sorted(categories)}")
    
    return True


def test_type_specific_behavior():
    """Test type-specific behavior rules"""
    print("\n🧪 Testing Type-Specific Behavior Rules")
    print("-" * 60)
    
    mapper = create_type_mapper()
    
    test_cases = [
        ("Task", "Development", False, "hours", 1.0),
        ("Product Backlog Item", "Requirements", True, "story_points", 1.5),
        ("Bug", "Defects", False, "hours", 1.2),
        ("Feature", "Product", True, "story_points", 3.0),
        ("Test Case", "Testing", False, "hours", 0.8)
    ]
    
    for type_name, expected_category, expected_story_points, expected_estimation, expected_complexity in test_cases:
        category = mapper.get_category(type_name)
        uses_points = mapper.uses_story_points(type_name)
        complexity = mapper.get_complexity_multiplier(type_name)
        config = mapper.get_type_config(type_name)
        
        print(f"✅ {type_name}:")
        print(f"   ├── Category: {category} (expected: {expected_category})")
        print(f"   ├── Uses story points: {uses_points} (expected: {expected_story_points})")
        print(f"   ├── Estimation method: {config.behavior.effort_estimation} (expected: {expected_estimation})")
        print(f"   └── Complexity multiplier: {complexity} (expected: {expected_complexity})")
        
        assert category == expected_category, f"Category mismatch for {type_name}"
        assert uses_points == expected_story_points, f"Story points usage mismatch for {type_name}"
        assert config.behavior.effort_estimation == expected_estimation, f"Estimation method mismatch for {type_name}"
        assert complexity == expected_complexity, f"Complexity multiplier mismatch for {type_name}"
    
    return True


def test_calculation_rules_integration():
    """Test calculation rules for metrics"""
    print("\n🧪 Testing Calculation Rules Integration")
    print("-" * 60)
    
    mapper = create_type_mapper()
    calc_rules = mapper.get_calculation_rules()
    
    # Test velocity calculation
    velocity_include = set(calc_rules['velocity_calculation']['include_types'])
    velocity_exclude = set(calc_rules['velocity_calculation']['exclude_types'])
    
    print(f"✅ Velocity calculation:")
    print(f"   ├── Include types: {len(velocity_include)} types")
    print(f"   ├── Exclude types: {len(velocity_exclude)} types")
    print(f"   └── Include list: {sorted(velocity_include)}")
    
    # Verify no overlap
    overlap = velocity_include.intersection(velocity_exclude)
    assert len(overlap) == 0, f"Velocity rules have overlapping types: {overlap}"
    
    # Test throughput calculation
    throughput_include_all = calc_rules['throughput_calculation']['include_all_types']
    throughput_exclude = set(calc_rules['throughput_calculation'].get('exclude_portfolio_items', []))
    
    print(f"✅ Throughput calculation:")
    print(f"   ├── Include all types: {throughput_include_all}")
    print(f"   └── Exclude portfolio items: {sorted(throughput_exclude)}")
    
    # Test cycle time calculation
    cycle_time_include = set(calc_rules['cycle_time_calculation']['include_types'])
    cycle_time_exclude = set(calc_rules['cycle_time_calculation']['exclude_types'])
    
    print(f"✅ Cycle time calculation:")
    print(f"   ├── Include types: {len(cycle_time_include)} types")
    print(f"   └── Exclude types: {len(cycle_time_exclude)} types")
    
    return True


def test_validation_functions():
    """Test validation functions"""
    print("\n🧪 Testing Validation Functions")
    print("-" * 60)
    
    mapper = create_type_mapper()
    
    # Test effort validation
    test_cases = [
        ("Product Backlog Item", 8, True),  # Valid Fibonacci
        ("Product Backlog Item", 7, False),  # Invalid Fibonacci
        ("Task", 16, True),  # Valid hours
        ("Task", -5, False),  # Invalid negative
        ("Feature", 21, True),  # Valid large Fibonacci
        ("Bug", 2.5, True),  # Valid decimal hours
    ]
    
    for type_name, effort_value, expected_valid in test_cases:
        is_valid = mapper.validate_effort(type_name, effort_value)
        validation_type = mapper.get_type_config(type_name).validation['effort_validation']
        
        print(f"✅ {type_name} effort {effort_value} ({validation_type}): {is_valid} (expected: {expected_valid})")
        assert is_valid == expected_valid, f"Validation mismatch for {type_name} effort {effort_value}"
    
    return True


def test_volume_statistics():
    """Test volume statistics"""
    print("\n🧪 Testing Volume Statistics")
    print("-" * 60)
    
    mapper = create_type_mapper()
    stats = mapper.get_volume_stats()
    
    print(f"✅ Volume statistics:")
    print(f"   ├── Total analyzed: {stats['total_analyzed']:,}")
    print(f"   ├── Unique types: {stats['unique_types']}")
    print(f"   └── Categories: {len(stats['by_category'])}")
    
    # Test top types by volume
    top_types = sorted(
        [(name, data['count']) for name, data in stats['by_type'].items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    print(f"✅ Top 5 types by volume:")
    for rank, (type_name, count) in enumerate(top_types, 1):
        percentage = (count / stats['total_analyzed']) * 100
        print(f"   {rank}. {type_name}: {count:,} ({percentage:.1f}%)")
    
    # Verify totals
    total_by_type = sum(data['count'] for data in stats['by_type'].values())
    assert total_by_type == stats['total_analyzed'], "Type volume totals don't match"
    
    return True


def test_calculator_integration_example():
    """Demonstrate calculator integration example"""
    print("\n🧪 Calculator Integration Example")
    print("-" * 60)
    
    mapper = create_type_mapper()
    
    # Example work items
    example_items = [
        {"type": "Task", "effort_hours": 8, "state": "Done"},
        {"type": "Product Backlog Item", "story_points": 5, "state": "Done"},
        {"type": "Bug", "effort_hours": 4, "state": "Done"},
        {"type": "Test Case", "effort_hours": 2, "state": "Done"},
        {"type": "Feature", "story_points": 21, "state": "Done"}
    ]
    
    # Calculate velocity (story points only)
    velocity_points = 0
    velocity_hours = 0
    
    print("✅ Processing work items for velocity calculation:")
    for item in example_items:
        item_type = item["type"]
        
        if mapper.get_velocity_types() and item_type in mapper.get_velocity_types():
            complexity_multiplier = mapper.get_complexity_multiplier(item_type)
            
            if mapper.uses_story_points(item_type) and "story_points" in item:
                weighted_points = item["story_points"] * complexity_multiplier
                velocity_points += weighted_points
                print(f"   ├── {item_type}: {item['story_points']} SP × {complexity_multiplier} = {weighted_points}")
            
            elif not mapper.uses_story_points(item_type) and "effort_hours" in item:
                weighted_hours = item["effort_hours"] * complexity_multiplier
                velocity_hours += weighted_hours
                print(f"   ├── {item_type}: {item['effort_hours']} hrs × {complexity_multiplier} = {weighted_hours}")
        else:
            print(f"   ├── {item_type}: Excluded from velocity calculation")
    
    print(f"✅ Velocity calculation result:")
    print(f"   ├── Story points: {velocity_points}")
    print(f"   ├── Effort hours: {velocity_hours}")
    print(f"   └── Combined metric: {velocity_points + (velocity_hours / 8):.1f} story point equivalents")
    
    # Calculate throughput (all completed items)
    throughput_count = len([
        item for item in example_items
        if item["state"] == "Done" and item["type"] != "Product"  # Exclude portfolio items
    ])
    
    print(f"✅ Throughput calculation:")
    print(f"   └── Completed items: {throughput_count}")
    
    return True


def main():
    """Run all integration tests"""
    print("=" * 80)
    print("WORK ITEM TYPE INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        test_type_mapper_basic,
        test_type_specific_behavior,
        test_calculation_rules_integration,
        test_validation_functions,
        test_volume_statistics,
        test_calculator_integration_example
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
                print("✅ PASSED")
            else:
                failed += 1
                print("❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED")
    print("=" * 80)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Integration ready for production!")
        return 0
    else:
        print("💥 SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    exit(main())