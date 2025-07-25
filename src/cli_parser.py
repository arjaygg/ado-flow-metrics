"""CLI argument parsing and validation for Flow Metrics."""

from pathlib import Path
from typing import Any, Dict, Optional

import click

from .exceptions import ConfigurationError


class CLIParser:
    """Handles CLI argument parsing and validation."""

    def __init__(self):
        self.version = "0.1.0"
        self.prog_name = "flow-metrics"

    def create_cli_group(self) -> click.Group:
        """Create the main CLI group."""

        @click.group()
        @click.version_option(version=self.version, prog_name=self.prog_name)
        def cli():
            """Flow Metrics - Calculate and analyze software development metrics."""
            pass

        return cli

    def validate_fetch_options(self, **kwargs) -> Dict[str, Any]:
        """Validate fetch command options."""
        validated = {}

        # Validate days_back
        days_back = kwargs.get("days_back", 30)
        if days_back <= 0:
            raise ConfigurationError("days_back must be a positive integer")
        validated["days_back"] = days_back

        # Validate project name
        project = kwargs.get("project")
        if project and not self._is_valid_project_name(project):
            raise ConfigurationError(f"Invalid project name: {project}")
        validated["project"] = project

        # Validate output path
        output = kwargs.get("output")
        if output:
            output_path = Path(output)
            if not output_path.parent.exists():
                raise ConfigurationError(
                    f"Output directory does not exist: {output_path.parent}"
                )
        validated["output"] = output

        # Validate history limit
        history_limit = kwargs.get("history_limit")
        if history_limit is not None and history_limit <= 0:
            raise ConfigurationError("history_limit must be a positive integer")
        validated["history_limit"] = history_limit

        # Validate WIQL options
        wiql_query = kwargs.get("wiql_query")
        wiql_file = kwargs.get("wiql_file")

        if wiql_query and wiql_file:
            raise ConfigurationError("Cannot specify both --wiql-query and --wiql-file")

        if wiql_file:
            wiql_path = Path(wiql_file)
            if not wiql_path.exists():
                raise ConfigurationError(f"WIQL file does not exist: {wiql_file}")
            if not wiql_path.is_file():
                raise ConfigurationError(f"WIQL path is not a file: {wiql_file}")

        validated["wiql_query"] = wiql_query
        validated["wiql_file"] = wiql_file
        validated["incremental"] = kwargs.get("incremental", False)
        validated["save_last_run"] = kwargs.get("save_last_run", False)

        return validated

    def validate_calculate_options(self, **kwargs) -> Dict[str, Any]:
        """Validate calculate command options."""
        validated = {}

        # Validate input file
        input_file = kwargs.get("input_file")
        if input_file:
            input_path = Path(input_file)
            if not input_path.exists():
                raise ConfigurationError(f"Input file does not exist: {input_file}")
            if not input_path.is_file():
                raise ConfigurationError(f"Input path is not a file: {input_file}")
        validated["input_file"] = input_file

        # Validate output path
        output = kwargs.get("output")
        if output:
            output_path = Path(output)
            if not output_path.parent.exists():
                raise ConfigurationError(
                    f"Output directory does not exist: {output_path.parent}"
                )
        validated["output"] = output

        # Validate output format
        output_format = kwargs.get("output_format", "json")
        valid_formats = ["json", "csv", "html"]
        if output_format not in valid_formats:
            raise ConfigurationError(
                f"Invalid output format: {output_format}. Must be one of: {', '.join(valid_formats)}"
            )
        validated["output_format"] = output_format

        # Validate dates
        from_date = kwargs.get("from_date")
        to_date = kwargs.get("to_date")

        if from_date and to_date and from_date >= to_date:
            raise ConfigurationError("from_date must be before to_date")

        validated["from_date"] = from_date
        validated["to_date"] = to_date
        validated["use_mock_data"] = kwargs.get("use_mock_data", False)

        return validated

    def validate_dashboard_options(self, **kwargs) -> Dict[str, Any]:
        """Validate dashboard command options."""
        validated = {}

        # Validate port
        port = kwargs.get("port", 8050)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigurationError("Port must be an integer between 1 and 65535")
        validated["port"] = port

        # Validate host
        host = kwargs.get("host", "127.0.0.1")
        if not self._is_valid_host(host):
            raise ConfigurationError(f"Invalid host format: {host}")
        validated["host"] = host

        validated["debug"] = kwargs.get("debug", False)
        validated["data_source"] = kwargs.get("data_source", "mock")

        return validated

    def validate_serve_options(self, **kwargs) -> Dict[str, Any]:
        """Validate serve command options."""
        validated = {}

        # Validate port
        port = kwargs.get("port", 8000)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigurationError("Port must be an integer between 1 and 65535")
        validated["port"] = port

        validated["open_browser"] = kwargs.get("open_browser", False)
        validated["auto_generate"] = kwargs.get("auto_generate", False)
        validated["executive"] = kwargs.get("executive", False)

        return validated

    def validate_data_options(self, **kwargs) -> Dict[str, Any]:
        """Validate data management command options."""
        validated = {}

        # Validate days_to_keep for cleanup
        days_to_keep = kwargs.get("days_to_keep")
        if days_to_keep is not None:
            if not isinstance(days_to_keep, int) or days_to_keep <= 0:
                raise ConfigurationError("days_to_keep must be a positive integer")
        validated["days_to_keep"] = days_to_keep

        # Validate days_back for fresh
        days_back = kwargs.get("days_back")
        if days_back is not None:
            if not isinstance(days_back, int) or days_back <= 0:
                raise ConfigurationError("days_back must be a positive integer")
        validated["days_back"] = days_back

        # Validate history_limit for fresh
        history_limit = kwargs.get("history_limit")
        if history_limit is not None:
            if not isinstance(history_limit, int) or history_limit <= 0:
                raise ConfigurationError("history_limit must be a positive integer")
        validated["history_limit"] = history_limit

        validated["dry_run"] = kwargs.get("dry_run", False)
        validated["keep_config"] = kwargs.get("keep_config", False)
        validated["use_mock"] = kwargs.get("use_mock", False)
        validated["force_mock"] = kwargs.get("force_mock", False)

        return validated

    def validate_mock_options(self, **kwargs) -> Dict[str, Any]:
        """Validate mock command options."""
        validated = {}

        # Validate items count
        items = kwargs.get("items", 200)
        if not isinstance(items, int) or items <= 0:
            raise ConfigurationError("items must be a positive integer")
        validated["items"] = items

        # Validate output path
        output = kwargs.get("output")
        if output:
            output_path = Path(output)
            if not output_path.parent.exists():
                raise ConfigurationError(
                    f"Output directory does not exist: {output_path.parent}"
                )
        validated["output"] = output

        return validated

    def _is_valid_project_name(self, project: str) -> bool:
        """Check if project name is valid."""
        if not project:
            return False

        # Basic sanitization check - allow alphanumeric, hyphens, underscores, and spaces
        import re

        return bool(re.match(r"^[a-zA-Z0-9\s_-]+$", project))

    def _is_valid_host(self, host: str) -> bool:
        """Check if host format is valid."""
        if not host:
            return False

        # Basic validation for IPv4 or hostname
        import re

        # IPv4 pattern
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.match(ipv4_pattern, host):
            return True

        # Hostname pattern (basic)
        hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        if re.match(hostname_pattern, host):
            return True

        # Special cases
        return host in ["localhost", "0.0.0.0"]
