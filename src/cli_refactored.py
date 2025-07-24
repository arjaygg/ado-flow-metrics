"""Refactored command-line interface for Flow Metrics."""

import sys
from typing import Optional

import click

from .cli_parser import CLIParser
from .command_executor import CommandExecutor
from .output_formatter import OutputFormatter


def main():
    """Main entry point for the refactored CLI."""
    # Initialize components
    formatter = OutputFormatter()
    parser = CLIParser()
    executor = CommandExecutor(formatter)
    
    # Create CLI group
    cli = parser.create_cli_group()
    
    # Add fetch command
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
    @click.option("--wiql-query", help="Custom WIQL query string")
    @click.option(
        "--wiql-file",
        type=click.Path(exists=True),
        help="Path to file containing WIQL query",
    )
    def fetch(
        days_back: int,
        project: Optional[str],
        output: Optional[str],
        incremental: bool,
        save_last_run: bool,
        history_limit: Optional[int],
        wiql_query: Optional[str],
        wiql_file: Optional[str],
    ):
        """Fetch work items from Azure DevOps.

        Note: If you encounter authentication or conditional access policy errors,
        use 'python -m src.cli data fresh --use-mock' to generate test data instead.

        NEW: Support for WIQL filtering:
        --wiql-query "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
        --wiql-file path/to/query.wiql
        """
        try:
            # Validate options
            options = parser.validate_fetch_options(
                days_back=days_back,
                project=project,
                output=output,
                incremental=incremental,
                save_last_run=save_last_run,
                history_limit=history_limit,
                wiql_query=wiql_query,
                wiql_file=wiql_file,
            )
            
            # Execute command
            executor.execute_fetch_command(**options)
            
        except Exception as e:
            formatter.print_error(f"Validation error: {e}")
            sys.exit(1)
    
    # Add calculate command
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
        from_date: Optional[click.DateTime],
        to_date: Optional[click.DateTime],
        use_mock_data: bool,
    ):
        """Calculate flow metrics from work items."""
        try:
            # Validate options
            options = parser.validate_calculate_options(
                input_file=input_file,
                output=output,
                output_format=output_format,
                from_date=from_date,
                to_date=to_date,
                use_mock_data=use_mock_data,
            )
            
            # Execute command
            executor.execute_calculate_command(**options)
            
        except Exception as e:
            formatter.print_error(f"Validation error: {e}")
            sys.exit(1)
    
    # Add dashboard command
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
            # Validate options
            options = parser.validate_dashboard_options(
                port=port,
                host=host,
                debug=debug,
                data_source=data_source,
            )
            
            # Execute command
            executor.execute_dashboard_command(**options)
            
        except Exception as e:
            formatter.print_error(f"Validation error: {e}")
            sys.exit(1)
    
    # Add serve command
    @cli.command()
    @click.option("--port", default=8000, help="Port to serve dashboard on")
    @click.option("--open-browser", is_flag=True, help="Open browser automatically")
    @click.option(
        "--auto-generate", is_flag=True, help="Auto-generate fresh data before serving"
    )
    @click.option(
        "--executive",
        is_flag=True,
        help="Launch executive dashboard instead of standard dashboard",
    )
    def serve(port: int, open_browser: bool, auto_generate: bool, executive: bool):
        """Launch the Flow Metrics dashboard with HTTP server."""
        try:
            # Validate options
            options = parser.validate_serve_options(
                port=port,
                open_browser=open_browser,
                auto_generate=auto_generate,
                executive=executive,
            )
            
            # Execute command
            executor.execute_serve_command(**options)
            
        except Exception as e:
            formatter.print_error(f"Validation error: {e}")
            sys.exit(1)
    
    # Add config group
    @cli.group()
    def config():
        """Manage configuration settings."""
        pass
    
    @config.command("show")
    def config_show():
        """Show current configuration."""
        executor.execute_config_show_command()
    
    @config.command("init")
    def config_init():
        """Initialize configuration from sample."""
        executor.execute_config_init_command()
    
    # Add history command
    @cli.command()
    @click.option("--limit", default=10, help="Number of recent executions to show")
    @click.option("--detailed", is_flag=True, help="Show detailed execution information")
    def history(limit: int, detailed: bool):
        """Show execution history."""
        executor.execute_history_command(limit, detailed)
    
    # Add data group (simplified for this example)
    @cli.group()
    def data():
        """Data management commands."""
        pass
    
    @data.command("validate")
    def data_validate():
        """Validate Azure DevOps configuration and connection."""
        executor.execute_data_validate_command()
    
    # Run the CLI
    cli()


if __name__ == "__main__":
    main()