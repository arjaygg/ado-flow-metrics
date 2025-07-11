#!/usr/bin/env python3
"""
Test script for Workstream Configuration Features
Tests Power BI-like CONTAINSSTRING logic and grouping functionality
"""

import json
import logging
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.calculator import FlowMetricsCalculator
from src.mock_data import generate_mock_azure_devops_data
from src.workstream_manager import WorkstreamManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_workstream_assignment():
    """Test individual team member workstream assignment"""
    logger.info("=== Testing Workstream Assignment (Power BI Logic) ===")

    manager = WorkstreamManager()

    # Test cases based on your Power BI configuration
    test_cases = [
        # Data workstream
        ("Nenissa Malibago", "Data"),
        ("Ariel Dimapilis", "Data"),
        ("Patrick Oniel Bernardo", "Data"),
        ("Christopher Jan Riños", "Data"),
        ("Ian Belmonte", "Data"),
        # QA workstream
        ("Sharon Smith", "QA"),
        ("Lorenz Johnson", "QA"),
        ("Arvin Lee", "QA"),
        # OutSystems workstream
        ("Janiel Apollo Bodiongan", "OutSystems"),
        ("Glizzel Ann Artates", "OutSystems"),
        ("Prince Joedymar Jud Barro", "OutSystems"),
        ("Rio Alyssa Venturina", "OutSystems"),
        ("Nymar Fernandez", "OutSystems"),
        # Others/Unknown
        ("Unknown Person", "Others"),
        ("Random Developer", "Others"),
        ("", "Others"),
    ]

    success_count = 0
    total_tests = len(test_cases)

    for member_name, expected_workstream in test_cases:
        actual_workstream = manager.get_workstream_for_member(member_name)
        status = "✅ PASS" if actual_workstream == expected_workstream else "❌ FAIL"

        logger.info(f"{member_name:25} -> {actual_workstream:12} {status}")

        if actual_workstream == expected_workstream:
            success_count += 1
        else:
            logger.error(f"Expected {expected_workstream}, got {actual_workstream}")

    logger.info(
        f"\nWorkstream Assignment Results: {success_count}/{total_tests} passed"
    )
    return success_count == total_tests


def test_workstream_filtering():
    """Test workstream-based filtering of metrics"""
    logger.info("=== Testing Workstream Filtering ===")

    # Generate mock data
    mock_data = generate_mock_azure_devops_data()
    calculator = FlowMetricsCalculator(mock_data)
    manager = WorkstreamManager()

    # Test 1: Get all team metrics (baseline)
    all_metrics = calculator.calculate_team_metrics()
    logger.info(f"Total team members: {len(all_metrics)}")

    # Test 2: Filter by specific workstreams
    workstreams_to_test = ["Data", "OutSystems", "QA"]

    for workstream in workstreams_to_test:
        filtered_metrics = calculator.calculate_team_metrics(workstreams=[workstream])
        logger.info(f"{workstream} workstream: {len(filtered_metrics)} members")

        # Verify all returned members belong to the workstream
        for member_name in filtered_metrics.keys():
            actual_workstream = manager.get_workstream_for_member(member_name)
            if actual_workstream != workstream:
                logger.error(
                    f"Member {member_name} in {workstream} filter but belongs to {actual_workstream}"
                )
                return False

    # Test 3: Multiple workstreams
    multi_workstream_metrics = calculator.calculate_team_metrics(
        workstreams=["Data", "QA"]
    )
    logger.info(f"Data + QA workstreams: {len(multi_workstream_metrics)} members")

    logger.info("✅ Workstream filtering test passed!")
    return True


def test_workstream_summary():
    """Test workstream summary and distribution"""
    logger.info("=== Testing Workstream Summary ===")

    mock_data = generate_mock_azure_devops_data()
    manager = WorkstreamManager()

    # Get workstream distribution
    summary = manager.get_workstream_summary(mock_data)

    logger.info("Workstream Distribution:")
    total_percentage = 0
    for workstream, stats in summary.items():
        logger.info(
            f"  {workstream:12}: {stats['count']:3} items ({stats['percentage']:5.1f}%)"
        )
        total_percentage += stats["percentage"]

    logger.info(f"Total: {total_percentage:.1f}%")

    # Verify percentages add up to ~100%
    if abs(total_percentage - 100.0) > 0.1:
        logger.error(f"Percentages don't add up to 100%: {total_percentage}%")
        return False

    logger.info("✅ Workstream summary test passed!")
    return True


def test_power_bi_equivalence():
    """Test equivalence with Power BI SWITCH logic"""
    logger.info("=== Testing Power BI SWITCH Logic Equivalence ===")

    manager = WorkstreamManager()

    # Test the exact patterns from your Power BI config
    power_bi_tests = [
        # Data team patterns
        ("Nenissa", "Data"),
        ("Ariel", "Data"),
        ("Patrick Oniel", "Data"),
        ("Kennedy Oliveira", "Data"),
        ("Christopher Jan", "Data"),
        ("Jegs", "Data"),
        ("Ian Belmonte", "Data"),
        # QA team patterns
        ("Sharon", "QA"),
        ("Lorenz", "QA"),
        ("Arvin", "QA"),
        # OutSystems team patterns
        ("Apollo", "OutSystems"),
        ("Glizzel", "OutSystems"),
        ("Prince", "OutSystems"),
        ("Patrick Russel", "OutSystems"),
        ("Rio", "OutSystems"),
        ("Nymar", "OutSystems"),
    ]

    success_count = 0
    for partial_name, expected_workstream in power_bi_tests:
        # Test with full names that contain the partial
        test_full_name = f"John {partial_name} Smith"  # Simulate full name
        actual_workstream = manager.get_workstream_for_member(test_full_name)

        status = "✅ PASS" if actual_workstream == expected_workstream else "❌ FAIL"
        logger.info(
            f"'{partial_name}' in '{test_full_name}' -> {actual_workstream} {status}"
        )

        if actual_workstream == expected_workstream:
            success_count += 1

    logger.info(f"Power BI Equivalence: {success_count}/{len(power_bi_tests)} passed")
    return success_count == len(power_bi_tests)


def test_configuration_validation():
    """Test workstream configuration validation"""
    logger.info("=== Testing Configuration Validation ===")

    manager = WorkstreamManager()
    validation_results = manager.validate_config()

    logger.info("Configuration Validation Results:")
    for level, messages in validation_results.items():
        if messages:
            logger.info(f"{level.upper()}:")
            for msg in messages:
                logger.info(f"  - {msg}")

    # Check for critical errors
    has_errors = len(validation_results.get("errors", [])) > 0
    if has_errors:
        logger.error("Configuration has errors!")
        return False

    logger.info("✅ Configuration validation passed!")
    return True


def demonstrate_usage():
    """Demonstrate real-world usage scenarios"""
    logger.info("=== Usage Demonstration ===")

    # Generate sample data
    mock_data = generate_mock_azure_devops_data()
    calculator = FlowMetricsCalculator(mock_data)
    manager = WorkstreamManager()

    logger.info("📊 Scenario 1: Cross-workstream comparison")
    workstreams = ["Data", "OutSystems", "QA"]

    comparison_results = {}
    for workstream in workstreams:
        metrics = calculator.calculate_team_metrics(workstreams=[workstream])

        # Calculate workstream-level aggregates
        total_items = sum(m["total_items"] for m in metrics.values())
        completed_items = sum(m["completed_items"] for m in metrics.values())
        avg_lead_time = (
            sum(m["average_lead_time"] for m in metrics.values()) / len(metrics)
            if metrics
            else 0
        )

        comparison_results[workstream] = {
            "members": len(metrics),
            "total_items": total_items,
            "completed_items": completed_items,
            "completion_rate": (completed_items / total_items * 100)
            if total_items > 0
            else 0,
            "avg_lead_time": avg_lead_time,
        }

    logger.info("Cross-workstream Performance:")
    for workstream, stats in comparison_results.items():
        logger.info(
            f"  {workstream:12}: {stats['members']} members, "
            f"{stats['completion_rate']:5.1f}% completion, "
            f"{stats['avg_lead_time']:5.1f}d avg lead time"
        )

    logger.info("\n📊 Scenario 2: Individual workstream deep-dive")
    data_metrics = calculator.calculate_team_metrics(workstreams=["Data"])
    logger.info(f"Data Team Details ({len(data_metrics)} members):")
    for member, stats in data_metrics.items():
        logger.info(
            f"  {member:25}: {stats['completed_items']:2} completed, "
            f"{stats['average_lead_time']:5.1f}d lead time"
        )

    return True


def main():
    """Run all workstream feature tests"""
    logger.info("🚀 Starting Workstream Features Test Suite")

    tests = [
        ("Workstream Assignment", test_workstream_assignment),
        ("Workstream Filtering", test_workstream_filtering),
        ("Workstream Summary", test_workstream_summary),
        ("Power BI Equivalence", test_power_bi_equivalence),
        ("Configuration Validation", test_configuration_validation),
    ]

    results = {}
    passed_tests = 0

    for test_name, test_func in tests:
        try:
            logger.info(f"\n" + "=" * 50)
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False

    # Run usage demonstration
    logger.info(f"\n" + "=" * 50)
    demonstrate_usage()

    # Save results
    with open("/home/devag/git/feature-new-dev/workstream_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n" + "=" * 50)
    logger.info("🎯 WORKSTREAM TEST SUMMARY")
    logger.info(f"Tests Passed: {passed_tests}/{len(tests)}")

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")

    if passed_tests == len(tests):
        logger.info("🎉 ALL WORKSTREAM TESTS PASSED!")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
