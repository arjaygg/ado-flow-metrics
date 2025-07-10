"""Command-line interface for Flow Metrics."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .azure_devops_client import AzureDevOpsClient
from .calculator import FlowMetricsCalculator
from .config_manager import get_settings, ConfigManager
from .mock_data import generate_mock_data
from .models import FlowMetricsReport

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="flow-metrics")
def cli():
    """Flow Metrics - Calculate and analyze software development metrics."""
    pass


@cli.command()
@click.option('--days-back', default=30, help='Number of days to fetch data for')
@click.option('--project', help='Azure DevOps project (overrides config)')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--incremental', is_flag=True, help='Fetch only changed items since last run')
@click.option('--save-last-run', is_flag=True, help='Save execution timestamp')
def fetch(days_back: int, project: Optional[str], output: Optional[str], 
          incremental: bool, save_last_run: bool):
    """Fetch work items from Azure DevOps."""
    try:
        settings = get_settings()
        
        # Override project if specified
        if project:
            settings.azure_devops.default_project = project
        
        if not settings.azure_devops.pat_token:
            console.print("[red]Error: AZURE_DEVOPS_PAT environment variable not set[/red]")
            sys.exit(1)
        
        client = AzureDevOpsClient(
            settings.azure_devops.org_url,
            settings.azure_devops.default_project,
            settings.azure_devops.pat_token
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching work items...", total=None)
            
            if incremental:
                # TODO: Implement incremental sync
                console.print("[yellow]Incremental sync not yet implemented[/yellow]")
            
            items = client.get_work_items(days_back=days_back)
            progress.update(task, completed=True)
        
        # Save to file
        output_path = Path(output) if output else settings.data_management.data_directory / "work_items.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(items, f, indent=2, default=str)
        
        console.print(f"[green]✓ Fetched {len(items)} work items[/green]")
        console.print(f"[green]✓ Saved to {output_path}[/green]")
        
        if save_last_run:
            # TODO: Implement last run tracking
            console.print("[yellow]Last run tracking not yet implemented[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--input', 'input_file', type=click.Path(exists=True), help='Input JSON file')
@click.option('--output', type=click.Path(), help='Output file path')
@click.option('--format', 'output_format', type=click.Choice(['json', 'csv', 'html']), 
              default='json', help='Output format')
@click.option('--from-date', type=click.DateTime(), help='Start date for analysis')
@click.option('--to-date', type=click.DateTime(), help='End date for analysis')
@click.option('--use-mock-data', is_flag=True, help='Use mock data for testing')
def calculate(input_file: Optional[str], output: Optional[str], output_format: str,
              from_date: Optional[datetime], to_date: Optional[datetime], use_mock_data: bool):
    """Calculate flow metrics from work items."""
    try:
        settings = get_settings()
        
        # Load work items
        if use_mock_data:
            console.print("[yellow]Using mock data...[/yellow]")
            work_items = generate_mock_data()
        else:
            input_path = Path(input_file) if input_file else settings.data_management.data_directory / "work_items.json"
            if not input_path.exists():
                console.print(f"[red]Error: Input file not found: {input_path}[/red]")
                console.print("[yellow]Tip: Run 'flow-metrics fetch' first or use --use-mock-data[/yellow]")
                sys.exit(1)
            
            with open(input_path, 'r') as f:
                work_items = json.load(f)
        
        # Calculate metrics
        calculator = FlowMetricsCalculator()
        
        with console.status("Calculating metrics..."):
            report = calculator.calculate_all_metrics(
                work_items,
                analysis_period_days=settings.flow_metrics.default_days_back
            )
        
        # Display summary
        _display_metrics_summary(report)
        
        # Save output
        if output_format == 'json':
            output_path = Path(output) if output else settings.data_management.data_directory / "flow_metrics_report.json"
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            console.print(f"[green]✓ Report saved to {output_path}[/green]")
        else:
            console.print(f"[yellow]{output_format} format not yet implemented[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--auto-increment', is_flag=True, help='Use last execution time')
@click.option('--save-last-run', is_flag=True, help='Save execution timestamp')
def sync(auto_increment: bool, save_last_run: bool):
    """Synchronize work items and calculate metrics."""
    try:
        # This combines fetch and calculate
        ctx = click.get_current_context()
        
        # Fetch data
        fetch_args = ['--save-last-run'] if save_last_run else []
        if auto_increment:
            fetch_args.append('--incremental')
        ctx.invoke(fetch, *fetch_args)
        
        # Calculate metrics
        ctx.invoke(calculate)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--items', default=200, help='Number of mock items to generate')
@click.option('--output', type=click.Path(), help='Output file path')
def mock(items: int, output: Optional[str]):
    """Generate mock work items for testing."""
    try:
        settings = get_settings()
        
        with console.status(f"Generating {items} mock work items..."):
            mock_items = generate_mock_data(num_items=items)
        
        output_path = Path(output) if output else settings.data_management.data_directory / "mock_work_items.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(mock_items, f, indent=2, default=str)
        
        console.print(f"[green]✓ Generated {len(mock_items)} mock work items[/green]")
        console.print(f"[green]✓ Saved to {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--port', default=8050, help='Dashboard port')
@click.option('--host', default='0.0.0.0', help='Dashboard host')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--data-source', default='mock', help='Data source: mock, api, or file path')
def dashboard(port: int, host: str, debug: bool, data_source: str):
    """Launch interactive web dashboard."""
    try:
        from .web_server import create_web_server
        
        console.print(f"[green]Starting Flow Metrics Dashboard...[/green]")
        console.print(f"[cyan]Host: {host}[/cyan]")
        console.print(f"[cyan]Port: {port}[/cyan]")
        console.print(f"[cyan]Data source: {data_source}[/cyan]")
        console.print(f"[yellow]Dashboard will be available at: http://{host}:{port}[/yellow]")
        
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


@config.command('show')
def config_show():
    """Show current configuration."""
    try:
        settings = get_settings()
        
        # Pretty print configuration
        config_dict = settings.model_dump(exclude={'azure_devops': {'pat_token'}})
        rprint(config_dict)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key: str, value: str):
    """Set a configuration value."""
    console.print(f"[yellow]Configuration updates not yet implemented[/yellow]")
    console.print(f"Would set {key} = {value}")


@config.command('init')
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
        console.print("[yellow]Remember to set AZURE_DEVOPS_PAT environment variable[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _display_metrics_summary(report: dict):
    """Display metrics summary in a nice table."""
    metrics = report.get('metrics', {})
    
    # Create summary table
    table = Table(title="Flow Metrics Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    # Add rows
    table.add_row("Total Items", str(metrics.get('total_items', 0)))
    table.add_row("Completed Items", str(metrics.get('completed_items', 0)))
    table.add_row("Current WIP", str(metrics.get('wip', {}).get('total', 0)))
    
    if metrics.get('lead_time'):
        table.add_row("Avg Lead Time", f"{metrics['lead_time'].get('average', 0):.1f} days")
        table.add_row("Median Lead Time", f"{metrics['lead_time'].get('median', 0):.1f} days")
    
    if metrics.get('cycle_time'):
        table.add_row("Avg Cycle Time", f"{metrics['cycle_time'].get('average', 0):.1f} days")
        table.add_row("Median Cycle Time", f"{metrics['cycle_time'].get('median', 0):.1f} days")
    
    if metrics.get('throughput'):
        table.add_row("Throughput", f"{metrics['throughput'].get('per_30_days', 0):.1f} items/30 days")
    
    if metrics.get('flow_efficiency'):
        table.add_row("Flow Efficiency", f"{metrics['flow_efficiency']:.1f}%")
    
    console.print(table)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()