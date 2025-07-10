"""Command-line interface for Flow Metrics."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import click
from rich import print as rprint
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .azure_devops_client import AzureDevOpsClient
from .calculator import FlowMetricsCalculator
from .config_manager import ConfigManager, get_settings
from .data_storage import FlowMetricsDatabase
from .mock_data import generate_mock_azure_devops_data as generate_mock_data
from .models import FlowMetricsReport

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="flow-metrics")
def cli():
    """Flow Metrics - Calculate and analyze software development metrics."""
    pass


@cli.command()
@click.option("--days-back", default=30, help="Number of days to fetch data for")
@click.option("--project", help="Azure DevOps project (overrides config)")
@click.option("--output", type=click.Path(), help="Output file path")
@click.option(
    "--incremental", is_flag=True, help="Fetch only changed items since last run"
)
@click.option("--save-last-run", is_flag=True, help="Save execution timestamp")
def fetch(
    days_back: int,
    project: Optional[str],
    output: Optional[str],
    incremental: bool,
    save_last_run: bool,
):
    """Fetch work items from Azure DevOps."""
    execution_start_time = datetime.now()
    execution_id = None

    try:
        settings = get_settings()

        # Override project if specified
        if project:
            settings.azure_devops.default_project = project

        if not settings.azure_devops.pat_token:
            console.print(
                "[red]Error: AZURE_DEVOPS_PAT environment variable not set[/red]"
            )
            sys.exit(1)

        # Initialize database for tracking
        db = FlowMetricsDatabase(settings)

        # Start execution tracking
        if save_last_run:
            execution_id = db.start_execution(
                settings.azure_devops.org_url, settings.azure_devops.default_project
            )

        client = AzureDevOpsClient(
            settings.azure_devops.org_url,
            settings.azure_devops.default_project,
            settings.azure_devops.pat_token,
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching work items...", total=None)

            if incremental:
                # Get last successful execution timestamp
                recent_executions = db.get_recent_executions(limit=1)
                if recent_executions:
                    last_run = recent_executions[0]["timestamp"]
                    # Calculate days since last run
                    days_since_last = (datetime.now() - last_run).days
                    if days_since_last < days_back:
                        days_back = max(1, days_since_last)
                        console.print(
                            f"[cyan]Using incremental sync: fetching last {days_back} days[/cyan]"
                        )
                    else:
                        console.print(
                            f"[yellow]Last run was {days_since_last} days ago, using full sync[/yellow]"
                        )
                else:
                    console.print(
                        "[yellow]No previous runs found, using full sync[/yellow]"
                    )

            items = client.get_work_items(days_back=days_back)
            progress.update(task, completed=True)

        # Save to file
        output_path = (
            Path(output)
            if output
            else settings.data_management.data_directory / "work_items.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(items, f, indent=2, default=str)

        console.print(f"[green]✓ Fetched {len(items)} work items[/green]")
        console.print(f"[green]✓ Saved to {output_path}[/green]")

        # Complete execution tracking
        if save_last_run and execution_id:
            execution_duration = (datetime.now() - execution_start_time).total_seconds()
            completed_items = len(
                [
                    item
                    for item in items
                    if item.get("current_state") in ["Done", "Closed", "Completed"]
                ]
            )

            db.complete_execution(
                execution_id, len(items), completed_items, execution_duration
            )
            console.print(
                f"[green]✓ Execution tracking saved (ID: {execution_id})[/green]"
            )

    except Exception as e:
        # Record failed execution
        if save_last_run and execution_id:
            execution_duration = (datetime.now() - execution_start_time).total_seconds()
            db.complete_execution(execution_id, 0, 0, execution_duration, str(e))

        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--input", "input_file", type=click.Path(exists=True), help="Input JSON file"
)
@click.option("--output", type=click.Path(), help="Output file path")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "html"]),
    default="json",
    help="Output format",
)
@click.option("--from-date", type=click.DateTime(), help="Start date for analysis")
@click.option("--to-date", type=click.DateTime(), help="End date for analysis")
@click.option("--use-mock-data", is_flag=True, help="Use mock data for testing")
def calculate(
    input_file: Optional[str],
    output: Optional[str],
    output_format: str,
    from_date: Optional[datetime],
    to_date: Optional[datetime],
    use_mock_data: bool,
):
    """Calculate flow metrics from work items."""
    try:
        settings = get_settings()

        # Load work items
        if use_mock_data:
            console.print("[yellow]Using mock data...[/yellow]")
            work_items = generate_mock_data()
        else:
            input_path = (
                Path(input_file)
                if input_file
                else settings.data_management.data_directory / "work_items.json"
            )
            if not input_path.exists():
                console.print(f"[red]Error: Input file not found: {input_path}[/red]")
                console.print(
                    "[yellow]Tip: Run 'flow-metrics fetch' first or use --use-mock-data[/yellow]"
                )
                sys.exit(1)

            with open(input_path, "r") as f:
                work_items = json.load(f)

        # Validate work items
        try:
            work_items = _validate_work_items(work_items)
            console.print(f"[green]✓ Validated {len(work_items)} work items[/green]")
        except ValueError as e:
            console.print(f"[red]Validation Error: {e}[/red]")
            sys.exit(1)

        # Calculate metrics
        calculator = FlowMetricsCalculator(work_items, settings)

        with console.status("Calculating metrics..."):
            report = calculator.generate_flow_metrics_report()

        # Display summary
        _display_metrics_summary(report)

        # Save output
        if output_format == "json":
            output_path = (
                Path(output)
                if output
                else settings.data_management.data_directory
                / "flow_metrics_report.json"
            )
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]✓ Report saved to {output_path}[/green]")

            # Also save dashboard-compatible format for browser integration
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "cli_calculation",
                "data": report,
            }
            dashboard_path = (
                settings.data_management.data_directory / "dashboard_data.json"
            )
            with open(dashboard_path, "w") as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            console.print(f"[green]✓ Dashboard data updated: {dashboard_path}[/green]")
        else:
            console.print(
                f"[yellow]{output_format} format not yet implemented[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--auto-increment", is_flag=True, help="Use last execution time")
@click.option("--save-last-run", is_flag=True, help="Save execution timestamp")
@click.option("--days-back", default=30, help="Number of days to fetch data for")
@click.option("--project", help="Azure DevOps project (overrides config)")
def sync(
    auto_increment: bool, save_last_run: bool, days_back: int, project: Optional[str]
):
    """Synchronize work items and calculate metrics."""
    try:
        # This combines fetch and calculate
        ctx = click.get_current_context()

        # Prepare fetch arguments
        fetch_kwargs = {
            "days_back": days_back,
            "project": project,
            "output": None,
            "incremental": auto_increment,
            "save_last_run": save_last_run,
        }

        # Fetch data
        ctx.invoke(fetch, **fetch_kwargs)

        # Calculate metrics
        ctx.invoke(
            calculate,
            input_file=None,
            output=None,
            output_format="json",
            from_date=None,
            to_date=None,
            use_mock_data=False,
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--items", default=200, help="Number of mock items to generate")
@click.option("--output", type=click.Path(), help="Output file path")
def mock(items: int, output: Optional[str]):
    """Generate mock work items for testing."""
    try:
        settings = get_settings()

        with console.status(f"Generating {items} mock work items..."):
            # Note: generate_mock_data() currently generates a fixed number (200)
            # Future enhancement: modify mock_data.py to accept num_items parameter
            mock_items = generate_mock_data()
            if len(mock_items) > items:
                mock_items = mock_items[:items]

        output_path = (
            Path(output)
            if output
            else settings.data_management.data_directory / "mock_work_items.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(mock_items, f, indent=2, default=str)

        console.print(f"[green]✓ Generated {len(mock_items)} mock work items[/green]")
        console.print(f"[green]✓ Saved to {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8050, help="Dashboard port")
@click.option("--host", default="0.0.0.0", help="Dashboard host")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--data-source", default="mock", help="Data source: mock, api, or file path"
)
def dashboard(port: int, host: str, debug: bool, data_source: str):
    """Launch interactive web dashboard."""
    try:
        from .web_server import create_web_server

        console.print(f"[green]Starting Flow Metrics Dashboard...[/green]")
        console.print(f"[cyan]Host: {host}[/cyan]")
        console.print(f"[cyan]Port: {port}[/cyan]")
        console.print(f"[cyan]Data source: {data_source}[/cyan]")
        console.print(
            f"[yellow]Dashboard will be available at: http://{host}:{port}[/yellow]"
        )

        # Create and run web server
        server = create_web_server(data_source=data_source)
        server.run(host=host, port=port, debug=debug)

    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for dashboard[/red]")
        console.print(f"[yellow]Please install: pip install flask flask-cors[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error starting dashboard: {e}[/red]")
        sys.exit(1)


@cli.group()
def config():
    """Manage configuration settings."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    try:
        settings = get_settings()

        # Pretty print configuration
        config_dict = settings.model_dump(exclude={"azure_devops": {"pat_token"}})
        rprint(config_dict)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value."""
    console.print(f"[yellow]Configuration updates not yet implemented[/yellow]")
    console.print(f"Would set {key} = {value}")


@config.command("init")
def config_init():
    """Initialize configuration from sample."""
    try:
        sample_path = Path("config/config.sample.json")
        config_path = Path("config/config.json")

        if config_path.exists():
            if not click.confirm("config.json already exists. Overwrite?"):
                return

        if not sample_path.exists():
            console.print("[red]Error: config.sample.json not found[/red]")
            sys.exit(1)

        # Copy sample to config
        import shutil

        shutil.copy(sample_path, config_path)

        console.print("[green]✓ Created config.json from sample[/green]")
        console.print(
            "[yellow]Remember to set AZURE_DEVOPS_PAT environment variable[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--limit", default=10, help="Number of recent executions to show")
@click.option("--detailed", is_flag=True, help="Show detailed execution information")
def history(limit: int, detailed: bool):
    """Show execution history."""
    try:
        settings = get_settings()
        db = FlowMetricsDatabase(settings)

        executions = db.get_recent_executions(limit=limit)

        if not executions:
            console.print("[yellow]No execution history found[/yellow]")
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

        console.print(table)

        if detailed and executions:
            console.print("\n[bold]Most Recent Execution Details:[/bold]")
            latest = executions[0]
            console.print(f"Organization: {latest['organization']}")
            console.print(f"Project: {latest['project']}")
            console.print(f"Status: {latest['status']}")
            console.print(f"Work Items: {latest['work_items_count']}")
            console.print(f"Completed: {latest['completed_items_count']}")
            if latest["error_message"]:
                console.print(f"[red]Error: {latest['error_message']}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Port to serve dashboard on")
@click.option("--open-browser", is_flag=True, help="Open browser automatically")
@click.option("--use-mock-data", is_flag=True, help="Use mock data for demo")
def demo(port: int, open_browser: bool, use_mock_data: bool):
    """Quick demo: generate data and launch dashboard."""
    try:
        console.print("[cyan]🚀 Starting Flow Metrics Demo...[/cyan]")

        # Generate fresh data
        if use_mock_data:
            console.print("[yellow]Generating mock data...[/yellow]")
            ctx = click.get_current_context()
            ctx.invoke(calculate, use_mock_data=True)
        else:
            console.print(
                "[yellow]Note: Using existing data or mock data if none exists[/yellow]"
            )

        # Launch dashboard
        ctx = click.get_current_context()
        ctx.invoke(
            serve, port=port, open_browser=open_browser, auto_generate=not use_mock_data
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.group()
def data():
    """Data management commands."""
    pass


@data.command("cleanup")
@click.option("--days-to-keep", default=365, help="Number of days of data to keep")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.confirmation_option(prompt="Are you sure you want to delete old data?")
def data_cleanup(days_to_keep: int, dry_run: bool):
    """Clean up old execution data from database."""
    try:
        settings = get_settings()
        db = FlowMetricsDatabase(settings)

        if dry_run:
            console.print(
                f"[yellow]DRY RUN: Would delete executions older than {days_to_keep} days[/yellow]"
            )
            # TODO: Add preview functionality to show what would be deleted
            console.print(
                "[yellow]Add --no-dry-run to actually delete the data[/yellow]"
            )
            return

        deleted_count = db.cleanup_old_data(days_to_keep=days_to_keep)
        console.print(
            f"[green]✓ Cleaned up {deleted_count} old execution records[/green]"
        )
        console.print(f"[green]✓ Kept data from last {days_to_keep} days[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@data.command("reset")
@click.option("--keep-config", is_flag=True, help="Keep configuration files")
@click.confirmation_option(
    prompt="Are you sure you want to reset all data? This cannot be undone!"
)
def data_reset(keep_config: bool):
    """Reset all data for fresh start."""
    try:
        settings = get_settings()
        data_dir = settings.data_management.data_directory

        console.print("[yellow]Resetting all data...[/yellow]")

        # Remove data directory contents
        import shutil

        if data_dir.exists():
            for item in data_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    console.print(f"[cyan]Removed: {item.name}[/cyan]")
                elif item.is_dir():
                    shutil.rmtree(item)
                    console.print(f"[cyan]Removed directory: {item.name}[/cyan]")

        # Remove config if requested
        if not keep_config:
            config_file = Path("config/config.json")
            if config_file.exists():
                config_file.unlink()
                console.print("[cyan]Removed: config.json[/cyan]")

        console.print("[green]✓ Data reset complete - ready for fresh start[/green]")

        if keep_config:
            console.print("[yellow]Configuration preserved[/yellow]")
        else:
            console.print(
                "[yellow]Run 'python3 -m src.cli config init' to setup configuration[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@data.command("fresh")
@click.option("--days-back", default=30, help="Number of days to fetch")
@click.option("--use-mock", is_flag=True, help="Use mock data instead of Azure DevOps")
def data_fresh(days_back: int, use_mock: bool):
    """Start fresh: reset data and fetch new."""
    try:
        console.print("[cyan]🔄 Starting fresh data load...[/cyan]")

        # Reset data (but keep config)
        ctx = click.get_current_context()
        ctx.invoke(data_reset, keep_config=True)

        # Generate fresh data
        if use_mock:
            console.print("[yellow]Generating fresh mock data...[/yellow]")
            ctx.invoke(calculate, use_mock_data=True)
        else:
            console.print(
                f"[yellow]Fetching fresh data for last {days_back} days...[/yellow]"
            )
            ctx.invoke(fetch, days_back=days_back, save_last_run=True)
            ctx.invoke(calculate)

        console.print("[green]✓ Fresh data load complete![/green]")
        console.print(
            "[cyan]💡 Run 'python3 -m src.cli serve --open-browser' to view dashboard[/cyan]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Port to serve dashboard on")
@click.option("--open-browser", is_flag=True, help="Open browser automatically")
@click.option(
    "--auto-generate", is_flag=True, help="Auto-generate fresh data before serving"
)
def serve(port: int, open_browser: bool, auto_generate: bool):
    """Launch the Flow Metrics dashboard with HTTP server."""
    import http.server
    import socketserver
    import threading
    import webbrowser

    try:
        settings = get_settings()

        # Auto-generate fresh data if requested
        if auto_generate:
            console.print("[cyan]Auto-generating fresh data...[/cyan]")
            ctx = click.get_current_context()
            ctx.invoke(calculate, use_mock_data=True)

        # Check if dashboard file exists
        dashboard_file = Path(__file__).parent.parent / "dashboard.html"
        if not dashboard_file.exists():
            console.print(
                f"[red]Error: Dashboard file not found: {dashboard_file}[/red]"
            )
            sys.exit(1)

        # Create a simple HTTP server to serve the dashboard
        class DashboardHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(dashboard_file.parent), **kwargs)

        # Start server in background thread
        def start_server():
            with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
                console.print(
                    f"[green]✓ Dashboard server started on http://localhost:{port}[/green]"
                )
                console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    console.print("[yellow]Dashboard server stopped[/yellow]")

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Wait a moment for server to start
        import time

        time.sleep(1)

        dashboard_url = f"http://localhost:{port}/dashboard.html"
        console.print(f"[green]Dashboard available at: {dashboard_url}[/green]")
        console.print(
            "[cyan]💡 Select 'CLI Data' in the dashboard to load generated metrics[/cyan]"
        )
        console.print(
            "[cyan]💡 Enable 'Auto-refresh' to automatically update when data changes[/cyan]"
        )

        if open_browser:
            webbrowser.open(dashboard_url)
            console.print("[green]✓ Opened dashboard in browser[/green]")

        # Keep the main thread alive
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]Dashboard stopped[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _validate_work_items(work_items: List[dict]) -> List[dict]:
    """Validate and clean work items data."""
    if not work_items:
        raise ValueError("No work items provided")

    valid_items = []
    validation_stats = {
        "missing_fields": 0,
        "empty_fields": 0,
        "invalid_dates": 0,
        "total_processed": len(work_items),
    }

    for item in work_items:
        # Check required fields with detailed validation
        required_fields = ["id", "title", "type", "current_state", "created_date"]
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in item:
                missing_fields.append(field)
            elif not item[field] or (
                isinstance(item[field], str) and item[field].strip() == ""
            ):
                empty_fields.append(field)

        if missing_fields or empty_fields:
            issue_details = []
            if missing_fields:
                issue_details.append(f"missing: {', '.join(missing_fields)}")
                validation_stats["missing_fields"] += 1
            if empty_fields:
                issue_details.append(f"empty: {', '.join(empty_fields)}")
                validation_stats["empty_fields"] += 1

            console.print(
                f"[yellow]Warning: Skipping item {item.get('id', 'unknown')} - {'; '.join(issue_details)}[/yellow]"
            )
            continue

        # Validate date format
        try:
            if isinstance(item["created_date"], str):
                datetime.fromisoformat(item["created_date"])
        except ValueError:
            validation_stats["invalid_dates"] += 1
            console.print(
                f"[yellow]Warning: Skipping item {item['id']} - invalid created_date format[/yellow]"
            )
            continue

        valid_items.append(item)

    if not valid_items:
        raise ValueError("No valid work items found after validation")

    # Display validation summary if there were any issues
    total_skipped = (
        validation_stats["missing_fields"]
        + validation_stats["empty_fields"]
        + validation_stats["invalid_dates"]
    )
    if total_skipped > 0:
        console.print(f"[cyan]Validation Summary:[/cyan]")
        console.print(f"  Total items processed: {validation_stats['total_processed']}")
        console.print(f"  Valid items: {len(valid_items)}")
        console.print(f"  Skipped items: {total_skipped}")
        if validation_stats["missing_fields"] > 0:
            console.print(f"    - Missing fields: {validation_stats['missing_fields']}")
        if validation_stats["empty_fields"] > 0:
            console.print(f"    - Empty fields: {validation_stats['empty_fields']}")
        if validation_stats["invalid_dates"] > 0:
            console.print(f"    - Invalid dates: {validation_stats['invalid_dates']}")

    return valid_items


def _display_metrics_summary(report: dict):
    """Display metrics summary in a nice table."""
    # Create summary table
    table = Table(title="Flow Metrics Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    # Handle the new report format from FlowMetricsCalculator
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

    console.print(table)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
