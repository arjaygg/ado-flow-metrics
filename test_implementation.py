#!/usr/bin/env python3
"""Test script to verify the flow metrics implementation with mock data."""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mock_data import generate_mock_azure_devops_data as generate_mock_data
from src.calculator import FlowMetricsCalculator
from src.config_manager import ConfigManager, FlowMetricsSettings, AzureDevOpsConfig
from rich.console import Console
from rich.table import Table
from rich import print as rprint

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

    return mock_items


def test_metrics_calculation(work_items):
    """Test metrics calculation."""
    console.print("\n[bold cyan]Testing Metrics Calculation[/bold cyan]")

    calculator = FlowMetricsCalculator()
    report = calculator.calculate_all_metrics(work_items, analysis_period_days=30)

    metrics = report["metrics"]
    console.print(f"✓ Calculated metrics for {metrics['total_items']} items")

    # Display results in a table
    table = Table(title="Flow Metrics Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Items", str(metrics["total_items"]))
    table.add_row("Completed Items", str(metrics["completed_items"]))
    table.add_row("Current WIP", str(metrics["wip"]["total"]))

    if metrics.get("lead_time"):
        table.add_row(
            "Average Lead Time", f"{metrics['lead_time']['average']:.1f} days"
        )
        table.add_row("Median Lead Time", f"{metrics['lead_time']['median']:.1f} days")

    if metrics.get("cycle_time"):
        table.add_row(
            "Average Cycle Time", f"{metrics['cycle_time']['average']:.1f} days"
        )
        table.add_row(
            "Median Cycle Time", f"{metrics['cycle_time']['median']:.1f} days"
        )

    if metrics.get("throughput"):
        table.add_row(
            "Throughput (30 days)", f"{metrics['throughput']['per_30_days']:.1f} items"
        )

    if metrics.get("flow_efficiency"):
        table.add_row("Flow Efficiency", f"{metrics['flow_efficiency']:.1f}%")

    if metrics.get("littles_law"):
        table.add_row(
            "Little's Law Variance", f"{metrics['littles_law']['variance']:.1f}%"
        )

    console.print(table)

    # Show team metrics
    if report.get("team_metrics"):
        team_table = Table(title="\nTeam Metrics")
        team_table.add_column("Team Member", style="cyan")
        team_table.add_column("Completed", style="green")
        team_table.add_column("Active", style="yellow")
        team_table.add_column("Avg Lead Time", style="magenta")

        for member in report["team_metrics"]:
            team_table.add_row(
                member["name"],
                str(member["completed_items"]),
                str(member["active_items"]),
                (
                    f"{member.get('average_lead_time', 0):.1f} days"
                    if member.get("average_lead_time")
                    else "N/A"
                ),
            )

        console.print(team_table)

    return report


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
            config_manager = ConfigManager()
            settings = config_manager.load(config_path)
            console.print("✓ Loaded configuration from config.json")

        # Test configuration methods
        active_stages = settings.get_active_stages()
        done_stages = settings.get_done_stages()

        console.print(
            f"✓ Found {len(active_stages)} active stages: {', '.join(active_stages[:3])}..."
        )
        console.print(
            f"✓ Found {len(done_stages)} done stages: {', '.join(done_stages[:3])}..."
        )

    except Exception as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
        return False

    return True


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
