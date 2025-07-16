#!/usr/bin/env python3
"""
Test script to validate the calculator integration with the configuration system.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import with absolute imports
import calculator
import configuration_manager

# Use the classes
FlowMetricsCalculator = calculator.FlowMetricsCalculator
ConfigurationManager = configuration_manager.ConfigurationManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_work_items():
    """Create sample work items for testing."""
    return [
        {
            "id": "1",
            "title": "Test Task 1",
            "type": "Task", 
            "priority": "High",
            "created_date": "2024-01-01T00:00:00",
            "created_by": "Test User",
            "assigned_to": "John Doe",
            "current_state": "2.2 - In Progress",
            "story_points": None,
            "effort_hours": 8,
            "tags": ["test"],
            "state_transitions": [
                {"to_state": "0 - New", "transition_date": "2024-01-01T00:00:00"},
                {"to_state": "2.2 - In Progress", "transition_date": "2024-01-02T00:00:00"}
            ]
        },
        {
            "id": "2", 
            "title": "Test Bug Fix",
            "type": "Bug",
            "priority": "Critical",
            "created_date": "2024-01-03T00:00:00",
            "created_by": "Test User",
            "assigned_to": "Jane Smith",
            "current_state": "5 - Done",
            "story_points": None,
            "effort_hours": 4,
            "tags": ["bug", "hotfix"],
            "state_transitions": [
                {"to_state": "0 - New", "transition_date": "2024-01-03T00:00:00"},
                {"to_state": "2.2 - In Progress", "transition_date": "2024-01-03T08:00:00"},
                {"to_state": "5 - Done", "transition_date": "2024-01-04T16:00:00"}
            ]
        },
        {
            "id": "3",
            "title": "Test Story",
            "type": "Product Backlog Item",
            "priority": "Medium", 
            "created_date": "2024-01-05T00:00:00",
            "created_by": "Product Owner",
            "assigned_to": "Development Team",
            "current_state": "3.2 - QA in Progress",
            "story_points": 5,
            "effort_hours": None,
            "tags": ["story", "feature"],
            "state_transitions": [
                {"to_state": "0 - New", "transition_date": "2024-01-05T00:00:00"},
                {"to_state": "2.2 - In Progress", "transition_date": "2024-01-08T00:00:00"},
                {"to_state": "3.2 - QA in Progress", "transition_date": "2024-01-10T00:00:00"}
            ]
        }
    ]

def test_configuration_loading():
    """Test configuration manager loading."""
    logger.info("=== Testing Configuration Loading ===")
    
    try:
        config_manager = ConfigurationManager()
        
        # Test workflow states
        workflow_states = config_manager.get_workflow_states()
        logger.info(f"Workflow states loaded: {bool(workflow_states)}")
        
        # Test work item types
        work_item_types = config_manager.get_work_item_types()
        logger.info(f"Work item types loaded: {bool(work_item_types)}")
        
        # Test calculation parameters
        calc_params = config_manager.get_calculation_parameters()
        logger.info(f"Calculation parameters loaded: {bool(calc_params)}")
        
        # Test specific methods
        active_states = config_manager.get_active_states()
        completion_states = config_manager.get_completion_states()
        logger.info(f"Active states: {len(active_states)}")
        logger.info(f"Completion states: {len(completion_states)}")
        
        # Test work item type behavior
        task_behavior = config_manager.get_type_behavior("Task")
        bug_behavior = config_manager.get_type_behavior("Bug")
        logger.info(f"Task behavior configured: {bool(task_behavior)}")
        logger.info(f"Bug behavior configured: {bool(bug_behavior)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        return False

def test_calculator_integration():
    """Test calculator with configuration integration."""
    logger.info("=== Testing Calculator Integration ===")
    
    try:
        # Create test data
        work_items = create_sample_work_items()
        
        # Create configuration manager
        config_manager = ConfigurationManager()
        
        # Create calculator with configuration manager
        calculator = FlowMetricsCalculator(work_items, config_manager=config_manager)
        
        # Test state configuration
        logger.info(f"Active states configured: {calculator.active_states}")
        logger.info(f"Done states configured: {calculator.done_states}")
        logger.info(f"Blocked states configured: {calculator.blocked_states}")
        
        # Test metric calculations
        lead_time = calculator.calculate_lead_time()
        logger.info(f"Lead time calculation: {lead_time}")
        
        cycle_time = calculator.calculate_cycle_time()
        logger.info(f"Cycle time calculation: {cycle_time}")
        
        throughput = calculator.calculate_throughput()
        logger.info(f"Throughput calculation: {throughput}")
        
        wip = calculator.calculate_wip()
        logger.info(f"WIP calculation: {wip}")
        
        # Test comprehensive report
        report = calculator.generate_flow_metrics_report()
        logger.info(f"Report generated with configuration summary: {bool(report.get('summary', {}).get('configuration_summary'))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Calculator integration failed: {e}")
        return False

def test_type_specific_behavior():
    """Test work item type specific behavior."""
    logger.info("=== Testing Type-Specific Behavior ===")
    
    try:
        work_items = create_sample_work_items()
        config_manager = ConfigurationManager()
        calculator = FlowMetricsCalculator(work_items, config_manager=config_manager)
        
        # Test type inclusion checks
        for item_type in ["Task", "Bug", "Product Backlog Item", "Test Case"]:
            throughput_inclusion = calculator._should_include_in_throughput(item_type)
            velocity_inclusion = calculator._should_include_in_velocity(item_type)
            complexity_multiplier = calculator._get_complexity_multiplier(item_type)
            
            logger.info(f"{item_type}: throughput={throughput_inclusion}, velocity={velocity_inclusion}, complexity={complexity_multiplier}")
        
        return True
        
    except Exception as e:
        logger.error(f"Type-specific behavior test failed: {e}")
        return False

def test_thresholds_and_parameters():
    """Test configuration-driven thresholds and parameters."""
    logger.info("=== Testing Thresholds and Parameters ===")
    
    try:
        work_items = create_sample_work_items()
        config_manager = ConfigurationManager()
        calculator = FlowMetricsCalculator(work_items, config_manager=config_manager)
        
        # Test thresholds for different work item types
        for item_type in ["Task", "Bug", "Product Backlog Item"]:
            lead_time_thresholds = calculator._get_lead_time_thresholds(item_type)
            cycle_time_thresholds = calculator._get_cycle_time_thresholds(item_type)
            
            logger.info(f"{item_type} lead time thresholds: {lead_time_thresholds}")
            logger.info(f"{item_type} cycle time thresholds: {cycle_time_thresholds}")
        
        return True
        
    except Exception as e:
        logger.error(f"Thresholds and parameters test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    logger.info("Starting Calculator Configuration Integration Tests")
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Calculator Integration", test_calculator_integration),
        ("Type-Specific Behavior", test_type_specific_behavior),
        ("Thresholds and Parameters", test_thresholds_and_parameters)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("Test Results Summary:")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All integration tests passed!")
        return 0
    else:
        logger.error("❌ Some integration tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())