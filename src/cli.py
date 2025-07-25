"""Command-line interface for Flow Metrics."""

import json
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import click
from rich import print as rprint
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .azure_devops_client import AzureDevOpsClient
from .calculator import FlowMetricsCalculator
from .config_manager import get_settings
from .data_storage import FlowMetricsDatabase
from .mock_data import generate_mock_azure_devops_data as generate_mock_data
from .models import FlowMetricsReport


# Windows-compatible console setup
def create_console():
    """Create a Rich console with Windows compatibility"""
    try:
        if os.name == 'nt':  # Windows
            try:
                # Try to enable UTF-8 support
                import subprocess
                subprocess.run("chcp 65001", shell=True, capture_output=True)
                return Console(legacy_windows=False, force_terminal=True)
            except:
                # Fallback to safe mode for Windows
                return Console(legacy_windows=True, no_color=True, force_terminal=True)
        else:
            return Console()
    except:
        # Ultimate fallback
        return Console(no_color=True, force_terminal=True)


console = create_console()

# Define cross-platform symbols
if os.name == 'nt':  # Windows
    SYMBOLS = {
        'check': 'OK',
        'error': 'ERROR', 
        'info': 'INFO',
        'warning': 'WARN',
        'arrow': '->',
        'bullet': '*'
    }
else:  # Unix/Linux/Mac
    SYMBOLS = {
        'check': '✓',
        'error': '✗',
        'info': 'ℹ',
        'warning': '⚠',
        'arrow': '→',
        'bullet': '•'
    }


def safe_print(message, style=None):
    """Print with Windows-safe encoding"""
    try:
        if style:
            console.print(message, style=style)
        else:
            console.print(message)
    except UnicodeEncodeError:
        # Fallback to plain print for Windows encoding issues
        plain_message = message
        if hasattr(message, 'plain'):
            plain_message = message.plain
        print(str(plain_message).encode('ascii', 'replace').decode('ascii'))


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
@click.option(
    "--history-limit",
    default=None,
    type=int,
    help="Limit number of state history entries per work item for faster testing",
)
def fetch(
    days_back: int,
    project: Optional[str],
    output: Optional[str],
    incremental: bool,
    save_last_run: bool,
    history_limit: Optional[int],
):
    """Fetch work items from Azure DevOps.
    
    Note: If you encounter authentication or conditional access policy errors,
    use 'python -m src.cli data fresh --use-mock' to generate test data instead.
    """

    # Set up signal handler for graceful cancellation
    def signal_handler(signum, frame):
        safe_print(f"\n[yellow]{SYMBOLS['warning']} Operation cancelled by user. Exiting...[/yellow]")
        sys.exit(130)  # Standard exit code for Ctrl+C

    signal.signal(signal.SIGINT, signal_handler)

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
            org_url=settings.azure_devops.org_url,
            project=settings.azure_devops.default_project,
            pat_token=settings.azure_devops.pat_token,
        )

        # Setup enhanced progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            # Create task for overall progress
            main_task = progress.add_task("Initializing...", total=None)
            batch_task = None

            def progress_callback(event_type: str, *args):
                """Handle progress updates from Azure DevOps client"""
                nonlocal batch_task

                if event_type == "phase":
                    phase_description = args[0]
                    progress.update(main_task, description=phase_description)

                elif event_type == "count":
                    item_count = args[0]
                    progress.update(
                        main_task, description=f"Found {item_count} work items"
                    )

                elif event_type == "items":
                    # Handle state history progress updates
                    items_description = args[0]
                    progress.update(main_task, description=items_description)

                elif event_type == "batch":
                    completed_batches, total_batches = args[0], args[1]
                    if batch_task is None:
                        batch_task = progress.add_task(
                            "Fetching batches...", total=total_batches
                        )
                    progress.update(
                        batch_task,
                        completed=completed_batches,
                        description=f"Batch {completed_batches}/{total_batches}",
                    )

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

            # Fetch with enhanced progress tracking
            items = client.get_work_items(
                days_back=days_back,
                progress_callback=progress_callback,
                history_limit=history_limit,
            )

            # Mark completion
            progress.update(
                main_task, description="✓ Fetch complete!", completed=1, total=1
            )
            if batch_task is not None:
                progress.remove_task(batch_task)

        # Save to file
        output_path = (
            Path(output)
            if output
            else settings.data_management.data_directory / "work_items.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(items, f, indent=2, default=str)

        safe_print(f"[green]{SYMBOLS['check']} Fetched {len(items)} work items[/green]")
        safe_print(f"[green]{SYMBOLS['check']} Saved to {output_path}[/green]")

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

        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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
            safe_print(f"[green]{SYMBOLS['check']} Validated {len(work_items)} work items[/green]")
        except ValueError as e:
            safe_print(f"[red]{SYMBOLS['error']} Validation Error: {e}[/red]")
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
            safe_print(f"[green]{SYMBOLS['check']} Report saved to {output_path}[/green]")

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
            safe_print(f"[green]{SYMBOLS['check']} Dashboard data updated: {dashboard_path}[/green]")
        else:
            console.print(
                f"[yellow]{output_format} format not yet implemented[/yellow]"
            )

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--auto-increment", is_flag=True, help="Use last execution time")
@click.option("--save-last-run", is_flag=True, help="Save execution timestamp")
@click.option("--days-back", default=30, help="Number of days to fetch data for")
@click.option("--project", help="Azure DevOps project (overrides config)")
@click.option(
    "--history-limit",
    default=None,
    type=int,
    help="Limit number of state history entries per work item for faster testing",
)
def sync(
    auto_increment: bool,
    save_last_run: bool,
    days_back: int,
    project: Optional[str],
    history_limit: Optional[int],
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
            "history_limit": history_limit,
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
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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

        safe_print(f"[green]{SYMBOLS['check']} Generated {len(mock_items)} mock work items[/green]")
        safe_print(f"[green]{SYMBOLS['check']} Saved to {output_path}[/green]")

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8050, help="Dashboard port")
@click.option(
    "--host", default="127.0.0.1", help="Dashboard host (default: localhost only)"
)
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
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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

        safe_print(f"[green]{SYMBOLS['check']} Created config.json from sample[/green]")
        console.print(
            "[yellow]Remember to set AZURE_DEVOPS_PAT environment variable[/yellow]"
        )

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Port to serve dashboard on")
@click.option("--open-browser", is_flag=True, help="Open browser automatically")
@click.option("--use-mock-data", is_flag=True, help="Use mock data for demo")
@click.option(
    "--executive", is_flag=True, help="Launch executive dashboard instead of standard dashboard"
)
def demo(port: int, open_browser: bool, use_mock_data: bool, executive: bool):
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
            serve, port=port, open_browser=open_browser, auto_generate=not use_mock_data, executive=executive
        )

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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
        safe_print(f"[green]{SYMBOLS['check']} Kept data from last {days_to_keep} days[/green]")

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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

        safe_print(f"[green]{SYMBOLS['check']} Data reset complete - ready for fresh start[/green]")

        if keep_config:
            console.print("[yellow]Configuration preserved[/yellow]")
        else:
            console.print(
                "[yellow]Run 'python3 -m src.cli config init' to setup configuration[/yellow]"
            )

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
        sys.exit(1)


@data.command("validate")
def data_validate():
    """Validate Azure DevOps configuration and connection."""
    try:
        console.print("[bold cyan]Flow Metrics - Azure DevOps Validation[/bold cyan]")
        console.print("=" * 50)
        
        from .config_manager import get_settings
        from .azure_devops_client import AzureDevOpsClient
        import os
        
        validation_errors = []
        warnings = []
        
        # Step 1: Validate configuration file
        console.print("\n[cyan]1. Checking configuration file...[/cyan]")
        try:
            settings = get_settings()
            safe_print(f"[green]{SYMBOLS['check']} Configuration loaded successfully[/green]")
            
            # Validate Azure DevOps config
            if not hasattr(settings, 'azure_devops'):
                validation_errors.append("Missing 'azure_devops' section in config")
            else:
                if not settings.azure_devops.org_url:
                    validation_errors.append("Missing 'org_url' in azure_devops config")
                elif not settings.azure_devops.org_url.startswith('https://dev.azure.com/'):
                    warnings.append(f"Unusual org_url format: {settings.azure_devops.org_url}")
                else:
                    safe_print(f"[green]{SYMBOLS['check']} Organization URL: {settings.azure_devops.org_url}[/green]")
                
                if not settings.azure_devops.default_project:
                    validation_errors.append("Missing 'default_project' in azure_devops config")
                else:
                    safe_print(f"[green]{SYMBOLS['check']} Project: {settings.azure_devops.default_project}[/green]")
                    
        except Exception as config_error:
            validation_errors.append(f"Configuration error: {config_error}")
            
        # Step 2: Validate PAT token
        console.print("\n[cyan]2. Checking PAT token...[/cyan]")
        pat_token = os.getenv("AZURE_DEVOPS_PAT")
        
        if not pat_token:
            validation_errors.append("AZURE_DEVOPS_PAT environment variable not set")
            console.print("[yellow]To set PAT token:[/yellow]")
            console.print("  Windows: set AZURE_DEVOPS_PAT=your_token_here")
            console.print("  Unix/Mac: export AZURE_DEVOPS_PAT=your_token_here")
        else:
            if len(pat_token) < 20:
                warnings.append(f"PAT token seems short (length: {len(pat_token)})")
            safe_print(f"[green]{SYMBOLS['check']} PAT Token: {'*' * (len(pat_token) - 4)}{pat_token[-4:]} (length: {len(pat_token)})[/green]")
        
        # Step 3: Check data directory
        console.print("\n[cyan]3. Checking data directory...[/cyan]")
        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir()
            safe_print(f"[green]{SYMBOLS['check']} Created data directory[/green]")
        else:
            safe_print(f"[green]{SYMBOLS['check']} Data directory exists[/green]")
        
        # Step 4: Test Azure DevOps connection (only if config and token are valid)
        if not validation_errors:
            console.print("\n[cyan]4. Testing Azure DevOps connection...[/cyan]")
            
            client = AzureDevOpsClient(
                org_url=settings.azure_devops.org_url,
                project=settings.azure_devops.default_project,
                pat_token=pat_token
            )
            
            if client.verify_connection():
                safe_print(f"[green]{SYMBOLS['check']} Azure DevOps connection successful![/green]")
            else:
                validation_errors.append("Azure DevOps connection verification failed")
        
        # Display results
        console.print("\n" + "=" * 50)
        console.print("[bold]Validation Summary[/bold]")
        console.print("=" * 50)
        
        if warnings:
            console.print(f"\n[yellow]{SYMBOLS['warning']} Warnings ({len(warnings)}):[/yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        if validation_errors:
            console.print(f"\n[red]{SYMBOLS['error']} Errors ({len(validation_errors)}):[/red]")
            for error in validation_errors:
                console.print(f"  • {error}")
            
            console.print("\n[yellow]Recommended actions:[/yellow]")
            console.print("1. Fix configuration errors above")
            console.print("2. Ensure AZURE_DEVOPS_PAT is set correctly")
            console.print("3. Check network connectivity to Azure DevOps")
            console.print("\n[cyan]For immediate testing, use mock data:[/cyan]")
            console.print("  python -m src.cli data fresh --use-mock")
            sys.exit(1)
        else:
            safe_print(f"\n[green]{SYMBOLS['check']} All validation checks passed![/green]")
            console.print("\n[green]You can now fetch real data:[/green]")
            console.print("  python -m src.cli data fresh --days-back 7")
            console.print("  python -m src.cli serve --open-browser")
            
    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Validation failed: {e}[/red]")
        console.print("\n[cyan]For immediate testing, use mock data:[/cyan]")
        console.print("  python -m src.cli data fresh --use-mock")
        sys.exit(1)


@data.command("fresh")
@click.option("--days-back", default=30, help="Number of days to fetch")
@click.option("--use-mock", is_flag=True, help="Use mock data instead of Azure DevOps")
@click.option(
    "--history-limit",
    default=None,
    type=int,
    help="Limit number of state history entries per work item for faster testing",
)
@click.option(
    "--force-mock",
    is_flag=True,
    help="Skip Azure DevOps validation and use mock data directly",
)
def data_fresh(days_back: int, use_mock: bool, history_limit: Optional[int], force_mock: bool):
    """Start fresh: reset data and fetch new."""
    try:
        safe_print(f"[cyan]{SYMBOLS['arrow']} Starting fresh data load...[/cyan]")

        # Reset data (but keep config)
        ctx = click.get_current_context()
        ctx.invoke(data_reset, keep_config=True)

        # Generate fresh data
        if use_mock or force_mock:
            console.print("[yellow]Generating fresh mock data...[/yellow]")
            ctx.invoke(calculate, use_mock_data=True)
        else:
            console.print(
                f"[yellow]Fetching fresh data for last {days_back} days...[/yellow]"
            )
            
            # Pre-validate Azure DevOps connection
            console.print("[cyan]Validating Azure DevOps connection...[/cyan]")
            try:
                from .config_manager import get_settings
                from .azure_devops_client import AzureDevOpsClient
                import os
                
                settings = get_settings()
                pat_token = os.getenv("AZURE_DEVOPS_PAT")
                
                # Debug: Print what config is being loaded
                console.print(f"[dim]Debug: Organization: {settings.azure_devops.org_url}[/dim]")
                console.print(f"[dim]Debug: Project: {settings.azure_devops.default_project}[/dim]")
                
                if not pat_token:
                    safe_print(f"[yellow]{SYMBOLS['warning']} AZURE_DEVOPS_PAT environment variable not set[/yellow]")
                    safe_print(f"[cyan]{SYMBOLS['info']} Falling back to mock data for testing...[/cyan]")
                    ctx.invoke(calculate, use_mock_data=True)
                    return
                
                client = AzureDevOpsClient(
                    org_url=settings.azure_devops.org_url,
                    project=settings.azure_devops.default_project,
                    pat_token=pat_token
                )
                
                if not client.verify_connection():
                    safe_print(f"[yellow]{SYMBOLS['warning']} Azure DevOps connection verification failed[/yellow]")
                    safe_print(f"[cyan]{SYMBOLS['info']} This may be due to conditional access policies or authentication issues[/cyan]")
                    safe_print(f"[cyan]{SYMBOLS['info']} Falling back to mock data for testing...[/cyan]")
                    ctx.invoke(calculate, use_mock_data=True)
                    return
                
                safe_print(f"[green]{SYMBOLS['check']} Azure DevOps connection verified[/green]")
                
            except Exception as conn_error:
                error_msg = str(conn_error)
                safe_print(f"[yellow]{SYMBOLS['warning']} Connection validation failed: {conn_error}[/yellow]")
                
                # Provide specific guidance for common errors
                if "not found" in error_msg and "project" in error_msg.lower():
                    console.print("[yellow]This usually means:[/yellow]")
                    console.print("• Project name is incorrect in config/config.json")
                    console.print("• You don't have access to this project")
                    console.print("• The project has been renamed or moved")
                    console.print(f"[cyan]Check that '{settings.azure_devops.default_project}' is the correct project name[/cyan]")
                
                safe_print(f"[cyan]{SYMBOLS['info']} Falling back to mock data for testing...[/cyan]")
                ctx.invoke(calculate, use_mock_data=True)
                return
            
            # Connection is valid, proceed with fetch
            try:
                ctx.invoke(fetch, days_back=days_back, save_last_run=True, history_limit=history_limit)
                
                # Check if fetch was successful by looking at the work items file
                data_dir = Path("data")
                work_items_file = data_dir / "work_items.json"
                
                if work_items_file.exists():
                    with open(work_items_file) as f:
                        work_items_data = json.load(f)
                    
                    if not work_items_data or len(work_items_data) == 0:
                        # Fetch completed but got no data - likely auth/policy issue
                        safe_print(f"[yellow]{SYMBOLS['warning']} Azure DevOps fetch completed but returned no work items[/yellow]")
                        safe_print(f"[cyan]{SYMBOLS['info']} This may be due to conditional access policies or insufficient permissions[/cyan]")
                        safe_print(f"[cyan]{SYMBOLS['info']} Falling back to mock data for testing...[/cyan]")
                        ctx.invoke(calculate, use_mock_data=True)
                    else:
                        # Success - proceed with normal calculation
                        ctx.invoke(calculate)
                else:
                    # No file created - fetch failed
                    safe_print(f"[yellow]{SYMBOLS['warning']} No work items file created - falling back to mock data[/yellow]")
                    ctx.invoke(calculate, use_mock_data=True)
                    
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['json', 'conditional access', 'authentication', 'invalid', 'no work items']):
                    safe_print(f"[red]{SYMBOLS['error']} Azure DevOps connection failed: {e}[/red]")
                    safe_print(f"[yellow]{SYMBOLS['warning']} This is likely due to conditional access policies or authentication issues[/yellow]")
                    safe_print(f"[cyan]{SYMBOLS['info']} Falling back to mock data for testing...[/cyan]")
                    # Fallback to mock data
                    ctx.invoke(calculate, use_mock_data=True)
                else:
                    # Re-raise other errors
                    raise

        safe_print(f"[green]{SYMBOLS['check']} Fresh data load complete![/green]")
        safe_print(
            f"[cyan]{SYMBOLS['info']} Run 'python3 -m src.cli serve --open-browser' to view dashboard[/cyan]"
        )
        safe_print(
            f"[cyan]{SYMBOLS['info']} Run 'python3 -m src.cli serve --open-browser --executive' to view executive dashboard[/cyan]"
        )

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Port to serve dashboard on")
@click.option("--open-browser", is_flag=True, help="Open browser automatically")
@click.option(
    "--auto-generate", is_flag=True, help="Auto-generate fresh data before serving"
)
@click.option(
    "--executive", is_flag=True, help="Launch executive dashboard instead of standard dashboard"
)
def serve(port: int, open_browser: bool, auto_generate: bool, executive: bool):
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
        dashboard_filename = "executive-dashboard.html" if executive else "dashboard.html"
        dashboard_file = Path(__file__).parent.parent / dashboard_filename
        if not dashboard_file.exists():
            console.print(
                f"[red]Error: Dashboard file not found: {dashboard_file}[/red]"
            )
            sys.exit(1)

        # Create a robust HTTP server to serve the dashboard
        class DashboardHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(dashboard_file.parent), **kwargs)
            
            def log_message(self, format, *args):
                """Enhanced logging for debugging"""
                safe_print(f"[cyan]{SYMBOLS['info']} HTTP: {format % args}[/cyan]")
            
            def do_GET(self):
                """Enhanced GET handler with better error handling"""
                safe_print(f"[cyan]{SYMBOLS['info']} GET request for: {self.path}[/cyan]")
                try:
                    return super().do_GET()
                except Exception as e:
                    safe_print(f"[red]{SYMBOLS['error']} Server error for {self.path}: {e}[/red]")
                    self.send_error(500, f"Server error: {e}")
            
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.send_header('Cache-Control', 'no-cache')
                super().end_headers()
            
            def guess_type(self, path):
                """Enhanced MIME type detection"""
                try:
                    result = super().guess_type(path)
                    if isinstance(result, tuple) and len(result) >= 2:
                        mimetype, encoding = result[0], result[1]
                    else:
                        mimetype, encoding = result, None
                except Exception:
                    mimetype, encoding = None, None
                
                # Override with our specific types
                if path.endswith('.js'):
                    return 'application/javascript', encoding
                elif path.endswith('.json'):
                    return 'application/json', encoding
                elif path.endswith('.html'):
                    return 'text/html', encoding
                elif path.endswith('.css'):
                    return 'text/css', encoding
                elif path.endswith('.woff') or path.endswith('.woff2'):
                    return 'font/woff', encoding
                elif path.endswith('.ico'):
                    return 'image/x-icon', encoding
                
                return mimetype or 'application/octet-stream', encoding

        # Start server in background thread
        def start_server():
            try:
                with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
                    httpd.allow_reuse_address = True
                    console.print(
                        f"[green]✓ Dashboard server started on http://localhost:{port}[/green]"
                    )
                    console.print(f"[cyan]Serving files from: {dashboard_file.parent}[/cyan]")
                    console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        console.print("[yellow]Dashboard server stopped[/yellow]")
            except OSError as e:
                console.print(f"[red]Server error: {e}[/red]")
                console.print(f"[yellow]Try a different port: --port {port + 1}[/yellow]")

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Wait a moment for server to start
        import time

        time.sleep(1)

        dashboard_url = f"http://localhost:{port}/{dashboard_filename}"
        dashboard_type = "Executive Dashboard" if executive else "Dashboard"
        console.print(f"[green]{dashboard_type} available at: {dashboard_url}[/green]")
        safe_print(
            f"[cyan]{SYMBOLS['info']} Select 'CLI Data' in the dashboard to load generated metrics[/cyan]"
        )
        safe_print(
            f"[cyan]{SYMBOLS['info']} Enable 'Auto-refresh' to automatically update when data changes[/cyan]"
        )

        if open_browser:
            webbrowser.open(dashboard_url)
            safe_print(f"[green]{SYMBOLS['check']} Opened dashboard in browser[/green]")

        # Keep the main thread alive
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]Dashboard stopped[/yellow]")

    except Exception as e:
        safe_print(f"[red]{SYMBOLS['error']} Error: {e}[/red]")
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
