"""Configuration management for Flow Metrics using Pydantic."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class StageMetadata(BaseModel):
    """Workflow stage configuration."""

    stage_name: str = Field(
        ..., description="Name of the stage as it appears in Azure DevOps"
    )
    stage_group: str = Field(..., description="Logical grouping of stages")
    is_active: bool = Field(
        False, description="Whether this stage represents active work"
    )
    is_done: bool = Field(
        False, description="Whether this stage represents completed work"
    )


class AzureDevOpsConfig(BaseModel):
    """Azure DevOps connection configuration."""

    org_url: str = Field(
        "https://dev.azure.com", description="Azure DevOps organization URL"
    )
    organization: Optional[str] = Field(None, description="Organization name")
    project: Optional[str] = Field(None, description="Project name")
    default_project: str = Field("", description="Default project name")
    base_url: str = Field(
        "https://dev.azure.com", description="Base URL for Azure DevOps"
    )
    api_version: str = Field("7.0", description="Azure DevOps API version")
    pat_token: Optional[str] = Field(
        None, description="Personal Access Token (from env var)"
    )

    def __init__(self, **data):
        # Always prioritize environment variables over config file
        import os

        # Always use environment variables if available, regardless of config values
        env_pat = os.getenv("AZURE_DEVOPS_PAT")
        if env_pat:
            data["pat_token"] = env_pat
        elif "pat_token" not in data or data["pat_token"] is None:
            data["pat_token"] = None

        env_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
        if env_org:
            data["organization"] = env_org
        elif (
            "organization" not in data
            or data["organization"] is None
            or (
                isinstance(data.get("organization"), str)
                and data["organization"].strip() == ""
            )
        ):
            data["organization"] = None

        env_project = os.getenv("AZURE_DEVOPS_PROJECT")
        if env_project:
            data["project"] = env_project
        elif "project" not in data or data["project"] is None:
            data["project"] = None
        if data.get("project") and data["project"].strip() == "":
            data["project"] = None
        super().__init__(**data)

    @field_validator("org_url")
    @classmethod
    def validate_org_url(cls, v):
        if not v.startswith(("https://", "http://")):
            raise ValueError("Organization URL must start with http:// or https://")
        return v.rstrip("/")


class FlowMetricsConfig(BaseModel):
    """Flow metrics calculation configuration."""

    throughput_period_days: int = Field(
        30, ge=1, description="Period for throughput calculation"
    )
    default_days_back: int = Field(
        30, ge=1, description="Default days to look back for data"
    )
    work_item_types: List[str] = Field(
        default=["User Story", "Bug", "Task", "Feature"],
        description="Work item types to include",
    )
    excluded_states: List[str] = Field(
        default=["Removed", "Cancelled"], description="States to exclude from metrics"
    )
    active_states: List[str] = Field(
        default=["In Progress", "Active", "Development", "Testing"],
        description="States considered as active work",
    )
    done_states: List[str] = Field(
        default=["Done", "Closed", "Completed", "Released"],
        description="States considered as completed work",
    )


class DataManagementConfig(BaseModel):
    """Data storage and caching configuration."""

    data_directory: Path = Field(Path("./data"), description="Directory for data files")
    cache_enabled: bool = Field(True, description="Enable caching")
    cache_ttl_hours: int = Field(24, ge=0, description="Cache time-to-live in hours")
    batch_size: int = Field(
        200, ge=1, le=1000, description="Batch size for API requests"
    )
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(5, ge=1, description="Delay between retries")

    @field_validator("data_directory")
    @classmethod
    def ensure_data_directory(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


class DashboardConfig(BaseModel):
    """Dashboard configuration."""

    port: int = Field(8050, ge=1, le=65535, description="Dashboard port")
    host: str = Field(
        "127.0.0.1", description="Dashboard host (localhost only for security)"
    )
    debug: bool = Field(False, description="Enable debug mode")
    auto_reload: bool = Field(True, description="Auto-reload on code changes")
    theme: str = Field("light", description="Dashboard theme")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    file: Optional[str] = Field("flow_metrics.log", description="Log file path")
    max_size_mb: int = Field(10, ge=1, description="Maximum log file size in MB")
    backup_count: int = Field(5, ge=0, description="Number of backup files to keep")


class FlowMetricsSettings(BaseSettings):
    """Main configuration class with environment variable support."""

    # Sub-configurations
    azure_devops: Optional[AzureDevOpsConfig] = Field(default_factory=AzureDevOpsConfig)
    flow_metrics: FlowMetricsConfig = FlowMetricsConfig()
    data_management: DataManagementConfig = DataManagementConfig()
    stage_metadata: List[StageMetadata] = []
    dashboard: DashboardConfig = DashboardConfig()
    logging: LoggingConfig = LoggingConfig()

    # Legacy stage definitions for backward compatibility
    stage_definitions: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "active_states": [
                "Active",
                "Committed",
                "In Progress",
                "Code Review",
                "Testing",
            ],
            "completion_states": ["Done", "Closed", "Completed", "Released"],
            "waiting_states": ["New", "Proposed", "Blocked", "Ready for Review"],
        }
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",  # Allow extra fields for backward compatibility
    )

    @classmethod
    def from_file(cls, config_path: Path) -> "FlowMetricsSettings":
        """Load configuration from a JSON file."""
        try:
            if not config_path.exists():
                # Return default settings if file doesn't exist
                return cls()

            with open(config_path, "r") as f:
                config_data = json.load(f)

            # Handle PAT token from environment (only if not specified in file)
            if "azure_devops" in config_data:
                if (
                    "pat_token" not in config_data["azure_devops"]
                    or config_data["azure_devops"]["pat_token"] is None
                ):
                    config_data["azure_devops"]["pat_token"] = os.getenv(
                        "AZURE_DEVOPS_PAT"
                    )

            # Validate stage definitions - ensure empty lists fall back to defaults
            if "stage_definitions" in config_data:
                stage_def = config_data["stage_definitions"]
                defaults = {
                    "active_states": [
                        "Active",
                        "Committed",
                        "In Progress",
                        "Code Review",
                        "Testing",
                    ],
                    "completion_states": ["Done", "Closed", "Completed", "Released"],
                    "waiting_states": [
                        "New",
                        "Proposed",
                        "Blocked",
                        "Ready for Review",
                    ],
                }
                for key, default_value in defaults.items():
                    if key in stage_def and not stage_def[key]:  # If empty list
                        stage_def[key] = default_value

            return cls(**config_data)
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            # Return default settings if file can't be read or parsed
            return cls()

    @classmethod
    def from_config_file(cls, config_file: str) -> "FlowMetricsSettings":
        """Alternative constructor for loading from file path string."""
        return cls.from_file(Path(config_file))

    def get_active_stages(self) -> List[str]:
        """Get list of active stage names."""
        return [stage.stage_name for stage in self.stage_metadata if stage.is_active]

    def get_done_stages(self) -> List[str]:
        """Get list of done stage names."""
        return [stage.stage_name for stage in self.stage_metadata if stage.is_done]

    def is_stage_active(self, stage_name: str) -> bool:
        """Check if a stage is considered active."""
        for stage in self.stage_metadata:
            if stage.stage_name == stage_name:
                return stage.is_active
        # Fallback to configured active states
        return stage_name in self.flow_metrics.active_states

    def is_stage_done(self, stage_name: str) -> bool:
        """Check if a stage is considered done."""
        for stage in self.stage_metadata:
            if stage.stage_name == stage_name:
                return stage.is_done
        # Fallback to configured done states
        return stage_name in self.flow_metrics.done_states

    def save_to_file(self, config_path: Path) -> None:
        """Save current configuration to a JSON file."""
        config_dict = self.model_dump(exclude={"azure_devops": {"pat_token"}})
        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=2, default=str)


class ConfigManager:
    """Configuration manager singleton."""

    _instance: Optional["ConfigManager"] = None
    _settings: Optional[FlowMetricsSettings] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: Optional[Path] = None) -> FlowMetricsSettings:
        """Load configuration from file or use defaults."""
        if config_path is None:
            # Try to find config.json in standard locations
            search_paths = [
                # Centralized config for PowerShell and Python
                Path(__file__).parent.parent.parent / "powershell" / "config.json",
                # Standard Python-specific config paths
                Path("config/config.json"),
                Path("../config/config.json"),
                Path.home() / ".flow_metrics" / "config.json",
            ]

            for path in search_paths:
                if path.exists():
                    config_path = path
                    break

        if config_path and config_path.exists():
            self._settings = FlowMetricsSettings.from_file(config_path)
        else:
            # Load from environment variables or use defaults
            # This requires proper environment setup
            raise ValueError(
                "No configuration file found. Please create config/config.json "
                "from config.sample.json or set environment variables."
            )

        return self._settings

    @property
    def settings(self) -> FlowMetricsSettings:
        """Get current settings, loading if necessary."""
        if self._settings is None:
            self.load()
        return self._settings

    def reload(self) -> FlowMetricsSettings:
        """Reload configuration from file."""
        self._settings = None
        return self.load()


# Global config manager instance
config_manager = ConfigManager()


def get_settings() -> FlowMetricsSettings:
    """Get current configuration settings."""
    return config_manager.settings
