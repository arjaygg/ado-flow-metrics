"""Output formatting and display logic for Flow Metrics CLI."""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich import print as rprint


class OutputFormatter:
    """Handles all output formatting and display operations."""
    
    def __init__(self):
        self.console = self._create_console()
        self.symbols = self._get_platform_symbols()
    
    def _create_console(self) -> Console:
        """Create a Rich console with Windows compatibility."""
        try:
            if os.name == "nt":  # Windows
                try:
                    # Try to enable UTF-8 support
                    import subprocess
                    subprocess.run("chcp 65001", shell=True, capture_output=True)
                    return Console(legacy_windows=False, force_terminal=True)
                except Exception:
                    # Fallback to safe mode for Windows
                    return Console(
                        legacy_windows=True, no_color=True, force_terminal=True
                    )
            else:
                return Console()
        except Exception:
            # Ultimate fallback
            return Console(no_color=True, force_terminal=True)
    
    def _get_platform_symbols(self) -> Dict[str, str]:
        """Get appropriate symbols for the current platform."""
        if os.name == "nt":  # Windows
            return {
                "check": "OK",
                "error": "ERROR",
                "info": "INFO",
                "warning": "WARN",
                "arrow": "->",
                "bullet": "*",
            }
        else:  # Unix/Linux/Mac
            return {
                "check": "✓",
                "error": "✗",
                "info": "ℹ",
                "warning": "⚠",
                "arrow": "→",
                "bullet": "•",
            }
    
    def safe_print(self, message: str, style: Optional[str] = None) -> None:
        """Print with Windows-safe encoding."""
        try:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        except UnicodeEncodeError:
            # Fallback to plain print for Windows encoding issues
            plain_message = message
            if hasattr(message, "plain"):
                plain_message = message.plain
            print(str(plain_message).encode("ascii", "replace").decode("ascii"))
    
    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.safe_print(f"[green]{self.symbols['check']} {message}[/green]")
    
    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.safe_print(f"[red]{self.symbols['error']} {message}[/red]")
    
    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.safe_print(f"[yellow]{self.symbols['warning']} {message}[/yellow]")
    
    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.safe_print(f"[cyan]{self.symbols['info']} {message}[/cyan]")
    
    def print_arrow(self, message: str) -> None:
        """Print a message with an arrow symbol."""
        self.safe_print(f"[cyan]{self.symbols['arrow']} {message}[/cyan]")
    
    def display_metrics_summary(self, report: Dict[str, Any]) -> None:
        """Display metrics summary in a nice table."""
        # Create summary table
        table = Table(title="Flow Metrics Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        # Handle the report format from FlowMetricsCalculator
        summary = report.get("summary", {})
        lead_time = report.get("lead_time", {})
        cycle_time = report.get("cycle_time", {})
        throughput = report.get("throughput", {})
        wip = report.get("work_in_progress", {})
        flow_efficiency = report.get("flow_efficiency", {})

        # Add rows
        table.add_row("Total Items", str(summary.get("total_work_items", 0)))
        table.add_row("Completed Items", str(summary.get("completed_items", 0)))
        table.add_row("Completion Rate", f"{summary.get('completion_rate', 0):.1f}%")
        table.add_row("Current WIP", str(wip.get("total_wip", 0)))

        if lead_time:
            table.add_row("Avg Lead Time", f"{lead_time.get('average_days', 0):.1f} days")
            table.add_row("Median Lead Time", f"{lead_time.get('median_days', 0):.1f} days")

        if cycle_time:
            table.add_row("Avg Cycle Time", f"{cycle_time.get('average_days', 0):.1f} days")
            table.add_row(
                "Median Cycle Time", f"{cycle_time.get('median_days', 0):.1f} days"
            )

        if throughput:
            table.add_row(
                "Throughput",
                f"{throughput.get('items_per_period', 0):.1f} items/{throughput.get('period_days', 30)} days",
            )

        if flow_efficiency:
            table.add_row(
                "Flow Efficiency", f"{flow_efficiency.get('average_efficiency', 0):.1%}"
            )

        self.console.print(table)
    
    def display_execution_history(self, executions: List[Dict[str, Any]], detailed: bool = False) -> None:
        """Display execution history in a table."""
        if not executions:
            self.console.print("[yellow]No execution history found[/yellow]")
            return

        # Create history table
        table = Table(title=f"Recent Executions (Last {len(executions)})")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="yellow")
        table.add_column("Project", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Items", style="blue")
        table.add_column("Duration", style="white")

        for execution in executions:
            status_style = "green" if execution["status"] == "completed" else "red"
            duration = (
                f"{execution['execution_duration_seconds']:.1f}s"
                if execution["execution_duration_seconds"]
                else "N/A"
            )

            table.add_row(
                str(execution["id"]),
                execution["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                execution["project"],
                f"[{status_style}]{execution['status']}[/{status_style}]",
                f"{execution['work_items_count']} ({execution['completed_items_count']} completed)",
                duration,
            )

        self.console.print(table)

        if detailed and executions:
            self.console.print("\n[bold]Most Recent Execution Details:[/bold]")
            latest = executions[0]
            self.console.print(f"Organization: {latest['organization']}")
            self.console.print(f"Project: {latest['project']}")
            self.console.print(f"Status: {latest['status']}")
            self.console.print(f"Work Items: {latest['work_items_count']}")
            self.console.print(f"Completed: {latest['completed_items_count']}")
            if latest["error_message"]:
                self.console.print(f"[red]Error: {latest['error_message']}[/red]")
    
    def display_validation_summary(self, validation_errors: List[str], warnings: List[str]) -> None:
        """Display validation summary with errors and warnings."""
        self.console.print("\n" + "=" * 50)
        self.console.print("[bold]Validation Summary[/bold]")
        self.console.print("=" * 50)

        if warnings:
            self.console.print(
                f"\n[yellow]{self.symbols['warning']} Warnings ({len(warnings)}):[/yellow]"
            )
            for warning in warnings:
                self.console.print(f"  • {warning}")

        if validation_errors:
            self.console.print(
                f"\n[red]{self.symbols['error']} Errors ({len(validation_errors)}):[/red]"
            )
            for error in validation_errors:
                self.console.print(f"  • {error}")

            self.console.print("\n[yellow]Recommended actions:[/yellow]")
            self.console.print("1. Fix configuration errors above")
            self.console.print("2. Ensure AZURE_DEVOPS_PAT is set correctly")
            self.console.print("3. Check network connectivity to Azure DevOps")
            self.console.print("\n[cyan]For immediate testing, use mock data:[/cyan]")
            self.console.print("  python -m src.cli data fresh --use-mock")
            return False
        else:
            self.print_success("All validation checks passed!")
            self.console.print("\n[green]You can now fetch real data:[/green]")
            self.console.print("  python -m src.cli data fresh --days-back 7")
            self.console.print("  python -m src.cli serve --open-browser")
            return True
    
    def display_wiql_query(self, query: str) -> None:
        """Display a WIQL query with formatting."""
        self.console.print(f"\n[bold]WIQL Query:[/bold]")
        self.console.print(f"[dim]{query}[/dim]")
    
    def display_config(self, config_dict: Dict[str, Any]) -> None:
        """Display configuration using Rich printing."""
        rprint(config_dict)
    
    def save_report_json(self, report: Dict[str, Any], output_path: Path) -> None:
        """Save report to JSON file."""
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        self.print_success(f"Report saved to {output_path}")
    
    def save_dashboard_data(self, report: Dict[str, Any], dashboard_path: Path) -> None:
        """Save dashboard-compatible data."""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "source": "cli_calculation",
            "data": report,
        }
        with open(dashboard_path, "w") as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        self.print_success(f"Dashboard data updated: {dashboard_path}")
    
    def save_work_items(self, items: List[Dict[str, Any]], output_path: Path) -> None:
        """Save work items to JSON file."""
        with open(output_path, "w") as f:
            json.dump(items, f, indent=2, default=str)
        self.print_success(f"Saved {len(items)} work items to {output_path}")
    
    def display_validation_item_summary(self, validation_stats: Dict[str, int]) -> None:
        """Display validation summary for work items."""
        total_skipped = (
            validation_stats["missing_fields"]
            + validation_stats["empty_fields"]
            + validation_stats["invalid_dates"]
        )
        
        if total_skipped > 0:
            self.console.print(f"[cyan]Validation Summary:[/cyan]")
            self.console.print(f"  Total items processed: {validation_stats['total_processed']}")
            self.console.print(f"  Skipped items: {total_skipped}")
            if validation_stats["missing_fields"] > 0:
                self.console.print(f"    - Missing fields: {validation_stats['missing_fields']}")
            if validation_stats["empty_fields"] > 0:
                self.console.print(f"    - Empty fields: {validation_stats['empty_fields']}")
            if validation_stats["invalid_dates"] > 0:
                self.console.print(f"    - Invalid dates: {validation_stats['invalid_dates']}")
    
    def log_server_info(self, message: str) -> None:
        """Log server information with proper formatting."""
        self.print_info(f"HTTP: {message}")
    
    def log_server_error(self, path: str, error: str) -> None:
        """Log server error with proper formatting."""
        self.print_error(f"Server error for {path}: {error}")