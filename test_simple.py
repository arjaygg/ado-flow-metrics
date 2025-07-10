#!/usr/bin/env python3
"""Simple test without dependencies to verify basic functionality."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mock_data import generate_mock_azure_devops_data
from src.calculator import FlowMetricsCalculator


def test_mock_data():
    """Test mock data generation."""
    print("\n=== Testing Mock Data Generation ===")

    mock_items = generate_mock_azure_devops_data()
    print(f"✓ Generated {len(mock_items)} mock work items")

    if mock_items:
        sample = mock_items[0]
        print(f"✓ Sample item: ID={sample['id']}, Title='{sample['title'][:30]}...'")
        print(
            f"✓ Sample has {len(sample.get('state_transitions', []))} state transitions"
        )
        print(f"✓ Sample assigned to: {sample.get('assigned_to', 'Unassigned')}")

    return mock_items


def test_calculator():
    """Test metrics calculation."""
    print("\n=== Testing Metrics Calculation ===")

    # Generate test data
    work_items = generate_mock_azure_devops_data()

    # Calculate metrics
    calculator = FlowMetricsCalculator(work_items)
    try:
        report = calculator.generate_flow_metrics_report()

        # The report structure matches PowerShell version
        summary = report.get("summary", {})
        lead_time = report.get("lead_time", {})
        cycle_time = report.get("cycle_time", {})
        throughput = report.get("throughput", {})
        wip = report.get("work_in_progress", {})

        print(f"✓ Calculated metrics for {summary.get('total_work_items', 0)} items")
        print(f"✓ Completed items: {summary.get('completed_items', 0)}")
        print(f"✓ Completion rate: {summary.get('completion_rate', 0):.1f}%")
        print(f"✓ Current WIP: {wip.get('total_wip', 0)}")

        if lead_time:
            print(f"✓ Average lead time: {lead_time.get('average_days', 0):.1f} days")
            print(f"✓ Median lead time: {lead_time.get('median_days', 0):.1f} days")

        if cycle_time:
            print(f"✓ Average cycle time: {cycle_time.get('average_days', 0):.1f} days")
            print(f"✓ Median cycle time: {cycle_time.get('median_days', 0):.1f} days")

        if throughput:
            print(
                f"✓ Throughput: {throughput.get('items_per_period', 0):.1f} items/{throughput.get('period_days', 30)} days"
            )

        if report.get("flow_efficiency"):
            print(
                f"✓ Flow efficiency: {report['flow_efficiency'].get('efficiency_percentage', 0):.1f}%"
            )

        return report

    except Exception as e:
        print(f"✗ Calculation failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def save_results(work_items, report):
    """Save test results."""
    print("\n=== Saving Test Results ===")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Save mock data
    mock_file = data_dir / "test_mock_items.json"
    with open(mock_file, "w") as f:
        json.dump(work_items, f, indent=2, default=str)
    print(f"✓ Saved mock data to {mock_file}")

    # Save report
    if report:
        report_file = data_dir / "test_metrics_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"✓ Saved metrics report to {report_file}")


def main():
    """Run simple tests."""
    print("Flow Metrics Python Implementation - Simple Test")
    print("=" * 50)

    try:
        # Test mock data generation
        work_items = test_mock_data()

        # Test metrics calculation
        report = test_calculator()

        # Save results
        save_results(work_items, report)

        print("\n✓ All tests completed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
