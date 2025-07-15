#!/usr/bin/env python3
"""Test script to verify the flow metrics implementation with mock data."""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.calculator import FlowMetricsCalculator
from src.config_manager import AzureDevOpsConfig, FlowMetricsSettings, get_settings
from src.mock_data import generate_mock_azure_devops_data as generate_mock_data

console = Console()


def test_mock_data_generation():
    """Test mock data generation."""
    console.print("\n[bold cyan]Testing Mock Data Generation[/bold cyan]")

    # Generate mock data
    mock_items = generate_mock_data()  # Always generates 200 items
    console.print(f"✓ Generated {len(mock_items)} mock work items")

    # Verify structure
    if mock_items:
        sample_item = mock_items[0]
        console.print(
            f"✓ Sample item has required fields: id={sample_item['id']}, title={sample_item['title'][:30]}..."
        )
        console.print(
            f"✓ Item has {len(sample_item.get('transitions', []))} state transitions"
        )

    # Assert that we generated valid data
    assert len(mock_items) > 0, "Must generate at least one work item"
    assert all("id" in item for item in mock_items), "All items must have IDs"

    console.print(f"✅ Mock data generation test passed")


def test_metrics_calculation():
    """Test metrics calculation."""
    console.print("\n[bold cyan]Testing Metrics Calculation[/bold cyan]")

    # Generate test data
    from src.mock_data import generate_mock_azure_devops_data

    work_items = generate_mock_azure_devops_data()

    # Calculate metrics
    from src.calculator import FlowMetricsCalculator
    from src.config_manager import get_settings

    settings = get_settings()
    calculator = FlowMetricsCalculator(work_items, settings)
    report = calculator.generate_flow_metrics_report()

    # Validate results with assertions
    assert "summary" in report, "Report must contain summary section"
    assert "lead_time" in report, "Report must contain lead_time section"
    assert "cycle_time" in report, "Report must contain cycle_time section"

    summary = report["summary"]
    assert isinstance(
        summary["total_work_items"], int
    ), "total_work_items must be integer"
    assert summary["total_work_items"] > 0, "Must have work items"

    console.print(f"✓ Calculated metrics for {summary['total_work_items']} work items")

    # Display results in a table
    table = Table(title="Flow Metrics Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Items", str(summary["total_work_items"]))
    table.add_row("Completed Items", str(summary["completed_items"]))
    table.add_row("Current WIP", str(report["work_in_progress"]["total_wip"]))

    if report.get("lead_time"):
        table.add_row(
            "Average Lead Time", f"{report['lead_time']['average_days']:.1f} days"
        )
        table.add_row(
            "Median Lead Time", f"{report['lead_time']['median_days']:.1f} days"
        )

    if report.get("cycle_time"):
        table.add_row(
            "Average Cycle Time", f"{report['cycle_time']['average_days']:.1f} days"
        )
        table.add_row(
            "Median Cycle Time", f"{report['cycle_time']['median_days']:.1f} days"
        )

    if report.get("throughput"):
        table.add_row(
            "Throughput (30 days)",
            f"{report['throughput']['items_per_period']:.1f} items",
        )

    if report.get("flow_efficiency"):
        eff_pct = report["flow_efficiency"]["average_efficiency"] * 100
        table.add_row("Flow Efficiency", f"{eff_pct:.1f}%")

    if report.get("littles_law_validation"):
        variance = report["littles_law_validation"].get("variance_percentage", 0)
        table.add_row("Little's Law Variance", f"{variance:.1f}%")

    console.print(table)

    # Show team metrics
    if report.get("team_metrics"):
        team_table = Table(title="\nTeam Metrics")
        team_table.add_column("Team Member", style="cyan")
        team_table.add_column("Completed", style="green")
        team_table.add_column("Active", style="yellow")
        team_table.add_column("Avg Lead Time", style="magenta")

        for member_name, metrics in report["team_metrics"].items():
            team_table.add_row(
                member_name,
                str(metrics.get("completed_items", 0)),
                str(metrics.get("active_items", 0)),
                (
                    f"{metrics.get('average_lead_time', 0):.1f} days"
                    if metrics.get("average_lead_time")
                    else "N/A"
                ),
            )

        console.print(team_table)

    # Final assertion that everything worked
    assert isinstance(report, dict), "Report must be a dictionary"
    assert "summary" in report, "Report must have summary section"

    console.print("✅ Metrics calculation test passed")


def test_configuration():
    """Test configuration management."""
    console.print("\n[bold cyan]Testing Configuration Management[/bold cyan]")

    # Create a test configuration
    try:
        # Check if config exists
        config_path = Path("config/config.json")
        if not config_path.exists():
            console.print(
                "[yellow]⚠ config.json not found, using sample configuration[/yellow]"
            )

            # Create minimal test config
            test_config = {
                "azure_devops": {
                    "org_url": "https://dev.azure.com/test-org",
                    "default_project": "Test-Project",
                    "api_version": "7.0",
                },
                "flow_metrics": {"throughput_period_days": 30, "default_days_back": 30},
                "stage_metadata": [
                    {
                        "stage_name": "New",
                        "stage_group": "Backlog",
                        "is_active": False,
                        "is_done": False,
                    },
                    {
                        "stage_name": "In Progress",
                        "stage_group": "Development",
                        "is_active": True,
                        "is_done": False,
                    },
                    {
                        "stage_name": "Done",
                        "stage_group": "Completed",
                        "is_active": False,
                        "is_done": True,
                    },
                ],
            }

            settings = FlowMetricsSettings(**test_config)
            console.print("✓ Created test configuration")
        else:
            settings = get_settings()
            console.print("✓ Loaded configuration from config.json")

        # Test configuration structure
        console.print("✓ Configuration loaded successfully")

    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        assert False, f"Configuration test failed: {e}"

    console.print("✅ Configuration test passed")


def save_test_results(work_items, report):
    """Save test results to files."""
    console.print("\n[bold cyan]Saving Test Results[/bold cyan]")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Save mock data
    mock_file = data_dir / "test_mock_items.json"
    with open(mock_file, "w") as f:
        json.dump(work_items, f, indent=2, default=str)
    console.print(f"✓ Saved mock data to {mock_file}")

    # Save report
    report_file = data_dir / "test_metrics_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    console.print(f"✓ Saved metrics report to {report_file}")


def main():
    """Run all tests."""
    console.print("[bold green]Flow Metrics Python Implementation Test[/bold green]")
    console.print("=" * 50)

    try:
        # Test configuration
        if not test_configuration():
            console.print("[red]Configuration test failed, using defaults[/red]")

        # Test mock data generation
        work_items = test_mock_data_generation()

        # Test metrics calculation
        report = test_metrics_calculation(work_items)

        # Save results
        save_test_results(work_items, report)

        console.print("\n[bold green]✓ All tests completed successfully![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Test failed: {e}[/bold red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
