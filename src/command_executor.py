"""Command execution logic for Flow Metrics CLI."""

import http.server
import json
import os
import shutil
import signal
import socketserver
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from .azure_devops_client import AzureDevOpsClient
from .calculator import FlowMetricsCalculator
from .config_manager import get_settings
from .data_storage import FlowMetricsDatabase
from .exceptions import ConfigurationError
from .mock_data import generate_mock_azure_devops_data as generate_mock_data
from .output_formatter import OutputFormatter


class CommandExecutor:
    """Handles execution of CLI commands."""

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter

    def execute_fetch_command(self, **options) -> None:
        """Execute the fetch command."""

        # Set up signal handler for graceful cancellation
        def signal_handler(signum, frame):
            self.formatter.print_warning("Operation cancelled by user. Exiting...")
            sys.exit(130)  # Standard exit code for Ctrl+C

        signal.signal(signal.SIGINT, signal_handler)

        execution_start_time = datetime.now()
        execution_id = None

        try:
            settings = get_settings()

            # Override project if specified
            project = options.get("project")
            if project:
                settings.azure_devops.default_project = project

            if not settings.azure_devops.pat_token:
                self.formatter.print_error(
                    "AZURE_DEVOPS_PAT environment variable not set"
                )
                sys.exit(1)

            # Handle WIQL query input
            custom_wiql_query = self._handle_wiql_input(options)

            # Initialize database for tracking
            db = FlowMetricsDatabase(settings)

            # Start execution tracking
            if options.get("save_last_run"):
                execution_id = db.start_execution(
                    settings.azure_devops.org_url, settings.azure_devops.default_project
                )

            client = AzureDevOpsClient(
                org_url=settings.azure_devops.org_url,
                project=settings.azure_devops.default_project,
                pat_token=settings.azure_devops.pat_token,
            )

            # Execute fetch with progress tracking
            items = self._execute_fetch_with_progress(
                client, options, custom_wiql_query
            )

            # Save results
            self._save_fetch_results(
                items, options, settings, db, execution_id, execution_start_time
            )

        except Exception as e:
            # Record failed execution
            if options.get("save_last_run") and execution_id:
                execution_duration = (
                    datetime.now() - execution_start_time
                ).total_seconds()
                db.complete_execution(execution_id, 0, 0, execution_duration, str(e))

            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_calculate_command(self, **options) -> None:
        """Execute the calculate command."""
        try:
            settings = get_settings()

            # Load work items
            work_items = self._load_work_items(options, settings)

            # Validate work items
            work_items = self._validate_work_items(work_items)
            self.formatter.print_success(f"Validated {len(work_items)} work items")

            # Calculate metrics
            calculator = FlowMetricsCalculator(work_items, settings)

            with self.formatter.console.status("Calculating metrics..."):
                report = calculator.generate_flow_metrics_report()

            # Display summary
            self.formatter.display_metrics_summary(report)

            # Save output
            self._save_calculate_results(report, options, settings)

        except Exception as e:
            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_dashboard_command(self, **options) -> None:
        """Execute the dashboard command."""
        try:
            from .web_server import create_web_server

            host = options["host"]
            port = options["port"]
            data_source = options["data_source"]
            debug = options["debug"]

            self.formatter.console.print(
                f"[green]Starting Flow Metrics Dashboard...[/green]"
            )
            self.formatter.console.print(f"[cyan]Host: {host}[/cyan]")
            self.formatter.console.print(f"[cyan]Port: {port}[/cyan]")
            self.formatter.console.print(f"[cyan]Data source: {data_source}[/cyan]")
            self.formatter.console.print(
                f"[yellow]Dashboard will be available at: http://{host}:{port}[/yellow]"
            )

            # Create and run web server
            server = create_web_server(data_source=data_source)
            server.run(host=host, port=port, debug=debug)

        except ImportError:
            self.formatter.print_error("Missing dependencies for dashboard")
            self.formatter.console.print(
                f"[yellow]Please install: pip install flask flask-cors[/yellow]"
            )
            sys.exit(1)
        except Exception as e:
            self.formatter.console.print(f"[red]Error starting dashboard: {e}[/red]")
            sys.exit(1)

    def execute_serve_command(self, **options) -> None:
        """Execute the serve command."""
        try:
            port = options["port"]
            open_browser = options["open_browser"]
            auto_generate = options["auto_generate"]
            executive = options["executive"]

            # Auto-generate fresh data if requested
            if auto_generate:
                self.formatter.console.print(
                    "[cyan]Auto-generating fresh data...[/cyan]"
                )
                ctx = click.get_current_context()
                ctx.invoke(self.execute_calculate_command, use_mock_data=True)

            # Check if dashboard file exists
            dashboard_filename = (
                "executive-dashboard.html" if executive else "dashboard.html"
            )
            dashboard_file = Path(__file__).parent.parent / dashboard_filename
            if not dashboard_file.exists():
                self.formatter.print_error(
                    f"Dashboard file not found: {dashboard_file}"
                )
                sys.exit(1)

            # Start server
            self._start_dashboard_server(dashboard_file, port, open_browser, executive)

        except Exception as e:
            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_config_show_command(self) -> None:
        """Execute the config show command."""
        try:
            settings = get_settings()

            # Pretty print configuration
            config_dict = settings.model_dump(exclude={"azure_devops": {"pat_token"}})
            self.formatter.display_config(config_dict)

        except Exception as e:
            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_config_init_command(self) -> None:
        """Execute the config init command."""
        try:
            sample_path = Path("config/config.sample.json")
            config_path = Path("config/config.json")

            if config_path.exists():
                if not click.confirm("config.json already exists. Overwrite?"):
                    return

            if not sample_path.exists():
                self.formatter.print_error("config.sample.json not found")
                sys.exit(1)

            # Copy sample to config
            shutil.copy(sample_path, config_path)

            self.formatter.print_success("Created config.json from sample")
            self.formatter.console.print(
                "[yellow]Remember to set AZURE_DEVOPS_PAT environment variable[/yellow]"
            )

        except Exception as e:
            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_history_command(self, limit: int, detailed: bool) -> None:
        """Execute the history command."""
        try:
            settings = get_settings()
            db = FlowMetricsDatabase(settings)

            executions = db.get_recent_executions(limit=limit)
            self.formatter.display_execution_history(executions, detailed)

        except Exception as e:
            self.formatter.print_error(f"Error: {e}")
            sys.exit(1)

    def execute_data_validate_command(self) -> None:
        """Execute the data validate command."""
        try:
            self.formatter.console.print(
                "[bold cyan]Flow Metrics - Azure DevOps Validation[/bold cyan]"
            )
            self.formatter.console.print("=" * 50)

            validation_errors = []
            warnings = []

            # Step 1: Validate configuration file
            self._validate_configuration(validation_errors, warnings)

            # Step 2: Validate PAT token
            self._validate_pat_token(validation_errors, warnings)

            # Step 3: Check data directory
            self._validate_data_directory()

            # Step 4: Test Azure DevOps connection (only if config and token are valid)
            if not validation_errors:
                self._test_azure_devops_connection(validation_errors)

            # Display results
            success = self.formatter.display_validation_summary(
                validation_errors, warnings
            )
            if not success:
                sys.exit(1)

        except Exception as e:
            self.formatter.print_error(f"Validation failed: {e}")
            self.formatter.console.print(
                "\n[cyan]For immediate testing, use mock data:[/cyan]"
            )
            self.formatter.console.print("  python -m src.cli data fresh --use-mock")
            sys.exit(1)

    def _handle_wiql_input(self, options: Dict[str, Any]) -> Optional[str]:
        """Handle WIQL query input from options."""
        wiql_file = options.get("wiql_file")
        wiql_query = options.get("wiql_query")

        custom_wiql_query = None
        if wiql_file:
            with open(wiql_file, "r") as f:
                custom_wiql_query = f.read().strip()
            self.formatter.print_info(f"Loaded WIQL query from: {wiql_file}")
        elif wiql_query:
            custom_wiql_query = wiql_query
            self.formatter.print_info("Using custom WIQL query")

        # Validate WIQL query if provided
        if custom_wiql_query:
            self._validate_wiql_query(custom_wiql_query)

        return custom_wiql_query

    def _validate_wiql_query(self, query: str) -> None:
        """Validate WIQL query."""
        try:
            from .wiql_parser import validate_wiql_query

            validation_errors = validate_wiql_query(query)
            if validation_errors:
                self.formatter.print_error("WIQL validation errors:")
                for error in validation_errors:
                    self.formatter.console.print(f"  • {error}")
                sys.exit(1)
            self.formatter.print_success("WIQL query validation passed")
        except ImportError:
            self.formatter.print_warning(
                "WIQL validation not available, proceeding without validation"
            )

    def _execute_fetch_with_progress(
        self,
        client: AzureDevOpsClient,
        options: Dict[str, Any],
        custom_wiql_query: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Execute fetch with progress tracking."""
        # Setup enhanced progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.formatter.console,
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

            # Handle incremental sync
            days_back = self._handle_incremental_sync(options, progress_callback)

            # Fetch with enhanced progress tracking
            if custom_wiql_query:
                # Use custom WIQL query
                try:
                    progress.update(main_task, description="Executing WIQL query...")
                    items = client.execute_custom_wiql(custom_wiql_query)
                    progress.update(
                        main_task, description=f"WIQL query returned {len(items)} items"
                    )
                except Exception as e:
                    progress.update(
                        main_task, description=f"WIQL query failed: {str(e)}"
                    )
                    raise
            else:
                # Use standard fetch method
                items = client.get_work_items(
                    days_back=days_back,
                    progress_callback=progress_callback,
                    history_limit=options.get("history_limit"),
                )

            # Mark completion
            progress.update(
                main_task, description="✓ Fetch complete!", completed=1, total=1
            )
            if batch_task is not None:
                progress.remove_task(batch_task)

        return items

    def _handle_incremental_sync(
        self, options: Dict[str, Any], progress_callback: Callable
    ) -> int:
        """Handle incremental sync logic."""
        days_back = options.get("days_back", 30)
        incremental = options.get("incremental", False)

        if incremental:
            from .config_manager import get_settings
            from .data_storage import FlowMetricsDatabase

            settings = get_settings()
            db = FlowMetricsDatabase(settings)

            # Get last successful execution timestamp
            recent_executions = db.get_recent_executions(limit=1)
            if recent_executions:
                last_run = recent_executions[0]["timestamp"]
                # Calculate days since last run
                days_since_last = (datetime.now() - last_run).days
                if days_since_last < days_back:
                    days_back = max(1, days_since_last)
                    self.formatter.console.print(
                        f"[cyan]Using incremental sync: fetching last {days_back} days[/cyan]"
                    )
                else:
                    self.formatter.console.print(
                        f"[yellow]Last run was {days_since_last} days ago, using full sync[/yellow]"
                    )
            else:
                self.formatter.console.print(
                    "[yellow]No previous runs found, using full sync[/yellow]"
                )

        return days_back

    def _save_fetch_results(
        self,
        items: List[Dict[str, Any]],
        options: Dict[str, Any],
        settings: Any,
        db: FlowMetricsDatabase,
        execution_id: Optional[str],
        execution_start_time: datetime,
    ) -> None:
        """Save fetch results."""
        # Save to file
        output = options.get("output")
        output_path = (
            Path(output)
            if output
            else settings.data_management.data_directory / "work_items.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.formatter.save_work_items(items, output_path)

        # Complete execution tracking
        if options.get("save_last_run") and execution_id:
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
            self.formatter.console.print(
                f"[green]✓ Execution tracking saved (ID: {execution_id})[/green]"
            )

    def _load_work_items(
        self, options: Dict[str, Any], settings: Any
    ) -> List[Dict[str, Any]]:
        """Load work items from file or generate mock data."""
        use_mock_data = options.get("use_mock_data", False)
        input_file = options.get("input_file")

        if use_mock_data:
            self.formatter.console.print("[yellow]Using mock data...[/yellow]")
            return generate_mock_data()
        else:
            input_path = (
                Path(input_file)
                if input_file
                else settings.data_management.data_directory / "work_items.json"
            )
            if not input_path.exists():
                self.formatter.print_error(f"Input file not found: {input_path}")
                self.formatter.console.print(
                    "[yellow]Tip: Run 'flow-metrics fetch' first or use --use-mock-data[/yellow]"
                )
                sys.exit(1)

            with open(input_path, "r") as f:
                return json.load(f)

    def _validate_work_items(
        self, work_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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

                self.formatter.console.print(
                    f"[yellow]Warning: Skipping item {item.get('id', 'unknown')} - {'; '.join(issue_details)}[/yellow]"
                )
                continue

            # Validate date format
            try:
                if isinstance(item["created_date"], str):
                    datetime.fromisoformat(item["created_date"])
            except ValueError:
                validation_stats["invalid_dates"] += 1
                self.formatter.console.print(
                    f"[yellow]Warning: Skipping item {item['id']} - invalid created_date format[/yellow]"
                )
                continue

            valid_items.append(item)

        if not valid_items:
            raise ValueError("No valid work items found after validation")

        # Display validation summary if there were any issues
        self.formatter.display_validation_item_summary(validation_stats)

        return valid_items

    def _save_calculate_results(
        self, report: Dict[str, Any], options: Dict[str, Any], settings: Any
    ) -> None:
        """Save calculation results."""
        output_format = options.get("output_format", "json")
        output = options.get("output")

        if output_format == "json":
            output_path = (
                Path(output)
                if output
                else settings.data_management.data_directory
                / "flow_metrics_report.json"
            )
            self.formatter.save_report_json(report, output_path)

            # Also save dashboard-compatible format for browser integration
            dashboard_path = (
                settings.data_management.data_directory / "dashboard_data.json"
            )
            self.formatter.save_dashboard_data(report, dashboard_path)
        else:
            self.formatter.console.print(
                f"[yellow]{output_format} format not yet implemented[/yellow]"
            )

    def _start_dashboard_server(
        self, dashboard_file: Path, port: int, open_browser: bool, executive: bool
    ) -> None:
        """Start the dashboard HTTP server."""

        # Create a robust HTTP server to serve the dashboard
        class DashboardHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, formatter=None, **kwargs):
                self.formatter = formatter
                super().__init__(*args, directory=str(dashboard_file.parent), **kwargs)

            def log_message(self, format, *args):
                """Enhanced logging for debugging"""
                if self.formatter:
                    self.formatter.log_server_info(format % args)

            def do_GET(self):
                """Enhanced GET handler with better error handling"""
                try:
                    return super().do_GET()
                except Exception as e:
                    if self.formatter:
                        self.formatter.log_server_error(self.path, str(e))
                    self.send_error(500, f"Server error: {e}")

            def end_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Cache-Control", "no-cache")
                super().end_headers()

        # Start server in background thread
        def start_server():
            try:
                handler = lambda *args, **kwargs: DashboardHandler(
                    *args, formatter=self.formatter, **kwargs
                )
                with socketserver.TCPServer(("", port), handler) as httpd:
                    httpd.allow_reuse_address = True
                    self.formatter.console.print(
                        f"[green]✓ Dashboard server started on http://localhost:{port}[/green]"
                    )
                    self.formatter.console.print(
                        f"[cyan]Serving files from: {dashboard_file.parent}[/cyan]"
                    )
                    self.formatter.console.print(
                        "[yellow]Press Ctrl+C to stop the server[/yellow]"
                    )
                    try:
                        httpd.serve_forever()
                    except KeyboardInterrupt:
                        self.formatter.console.print(
                            "[yellow]Dashboard server stopped[/yellow]"
                        )
            except OSError as e:
                self.formatter.console.print(f"[red]Server error: {e}[/red]")
                self.formatter.console.print(
                    f"[yellow]Try a different port: --port {port + 1}[/yellow]"
                )

        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # Wait a moment for server to start
        time.sleep(1)

        dashboard_filename = (
            "executive-dashboard.html" if executive else "dashboard.html"
        )
        dashboard_url = f"http://localhost:{port}/{dashboard_filename}"
        dashboard_type = "Executive Dashboard" if executive else "Dashboard"
        self.formatter.console.print(
            f"[green]{dashboard_type} available at: {dashboard_url}[/green]"
        )
        self.formatter.print_info(
            "Select 'CLI Data' in the dashboard to load generated metrics"
        )
        self.formatter.print_info(
            "Enable 'Auto-refresh' to automatically update when data changes"
        )

        if open_browser:
            webbrowser.open(dashboard_url)
            self.formatter.print_success("Opened dashboard in browser")

        # Keep the main thread alive
        try:
            while server_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            self.formatter.console.print("[yellow]Dashboard stopped[/yellow]")

    def _validate_configuration(
        self, validation_errors: List[str], warnings: List[str]
    ) -> None:
        """Validate configuration file."""
        self.formatter.console.print("\n[cyan]1. Checking configuration file...[/cyan]")
        try:
            settings = get_settings()
            self.formatter.print_success("Configuration loaded successfully")

            # Validate Azure DevOps config
            if not hasattr(settings, "azure_devops"):
                validation_errors.append("Missing 'azure_devops' section in config")
            else:
                if not settings.azure_devops.org_url:
                    validation_errors.append("Missing 'org_url' in azure_devops config")
                elif not settings.azure_devops.org_url.startswith(
                    "https://dev.azure.com/"
                ):
                    warnings.append(
                        f"Unusual org_url format: {settings.azure_devops.org_url}"
                    )
                else:
                    self.formatter.print_success(
                        f"Organization URL: {settings.azure_devops.org_url}"
                    )

                if not settings.azure_devops.default_project:
                    validation_errors.append(
                        "Missing 'default_project' in azure_devops config"
                    )
                else:
                    self.formatter.print_success(
                        f"Project: {settings.azure_devops.default_project}"
                    )

        except Exception as config_error:
            validation_errors.append(f"Configuration error: {config_error}")

    def _validate_pat_token(
        self, validation_errors: List[str], warnings: List[str]
    ) -> None:
        """Validate PAT token."""
        self.formatter.console.print("\n[cyan]2. Checking PAT token...[/cyan]")
        pat_token = os.getenv("AZURE_DEVOPS_PAT")

        if not pat_token:
            validation_errors.append("AZURE_DEVOPS_PAT environment variable not set")
            self.formatter.console.print("[yellow]To set PAT token:[/yellow]")
            self.formatter.console.print(
                "  Windows: set AZURE_DEVOPS_PAT=your_token_here"
            )
            self.formatter.console.print(
                "  Unix/Mac: export AZURE_DEVOPS_PAT=your_token_here"
            )
        else:
            if len(pat_token) < 20:
                warnings.append(f"PAT token seems short (length: {len(pat_token)})")
            self.formatter.print_success(
                f"PAT Token: {'*' * (len(pat_token) - 4)}{pat_token[-4:]} (length: {len(pat_token)})"
            )

    def _validate_data_directory(self) -> None:
        """Validate data directory."""
        self.formatter.console.print("\n[cyan]3. Checking data directory...[/cyan]")
        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir()
            self.formatter.print_success("Created data directory")
        else:
            self.formatter.print_success("Data directory exists")

    def _test_azure_devops_connection(self, validation_errors: List[str]) -> None:
        """Test Azure DevOps connection."""
        self.formatter.console.print(
            "\n[cyan]4. Testing Azure DevOps connection...[/cyan]"
        )

        settings = get_settings()
        pat_token = os.getenv("AZURE_DEVOPS_PAT")

        client = AzureDevOpsClient(
            org_url=settings.azure_devops.org_url,
            project=settings.azure_devops.default_project,
            pat_token=pat_token,
        )

        if client.verify_connection():
            self.formatter.print_success("Azure DevOps connection successful!")
        else:
            validation_errors.append("Azure DevOps connection verification failed")
