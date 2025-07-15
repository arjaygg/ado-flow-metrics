"""Configuration management for Flow Metrics using Pydantic."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# --- Pydantic Models for nested configuration in config.json ---

class AzureDevOpsConfig(BaseSettings):
    """Maps to the 'azure_devops' object in config.json."""
    org_url: Optional[str] = Field(alias="organization", default=None)
    default_project: Optional[str] = Field(alias="project", default=None)
    pat_token: Optional[str] = None
    api_version: str = "7.0"
    base_url: str = "https://dev.azure.com"
    
    model_config = {"env_prefix": "AZURE_DEVOPS_", "populate_by_name": True}
    
    # Support both field names for backward compatibility
    @property
    def organization(self) -> Optional[str]:
        # Check environment variable first
        env_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
        if env_org:
            return env_org
        
        if self.org_url:
            return self.org_url.replace("https://dev.azure.com/", "") if self.org_url.startswith("https://dev.azure.com/") else self.org_url
        return None
    
    @property
    def project(self) -> Optional[str]:
        # Check environment variable first
        env_project = os.getenv("AZURE_DEVOPS_PROJECT") 
        if env_project:
            return env_project
        return self.default_project
    
    def model_post_init(self, __context) -> None:
        """Override with environment variables after initialization."""
        # Check for environment variables and override
        env_pat = os.getenv("AZURE_DEVOPS_PAT")
        if env_pat:
            self.pat_token = env_pat
        elif self.pat_token and self.pat_token.startswith("${") and self.pat_token.endswith("}"):
            # Handle placeholder values - if no env var is set, treat placeholder as None
            self.pat_token = None
            
        env_org = os.getenv("AZURE_DEVOPS_ORGANIZATION")
        if env_org:
            self.org_url = f"https://dev.azure.com/{env_org}" if not env_org.startswith("http") else env_org
            
        env_project = os.getenv("AZURE_DEVOPS_PROJECT")
        if env_project:
            self.default_project = env_project

class FlowMetricsConfig(BaseModel):
    """Maps to the 'flow_metrics' object in config.json."""
    throughput_period_days: int = 30
    default_days_back: int = 30
    work_item_types: List[str] = ["User Story", "Bug", "Task", "Feature"]
    excluded_states: List[str] = ["Removed", "Cancelled"]
    active_states: List[str] = ["Active", "Committed", "In Progress", "Code Review", "Testing"]
    done_states: List[str] = ["Done", "Closed", "Completed", "Released"]

class StageMetadata(BaseModel):
    """Metadata for workflow stages."""
    stage_name: str
    stage_group: str
    is_active: bool
    is_done: bool

class DataManagementConfig(BaseModel):
    """Maps to the 'data_management' object in config.json."""
    data_directory: Path = Path("./data")
    auto_backup: bool = True
    export_directory: Path = Path("./exports")
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    batch_size: int = 200
    max_retries: int = 3
    retry_delay_seconds: int = 5

class DashboardConfig(BaseModel):
    """Maps to the 'dashboard' object in config.json."""
    port: int = 8050
    host: str = Field(default="127.0.0.1", description="Host to bind to - use localhost only for security")
    debug: bool = False
    auto_reload: bool = True
    theme: str = "light"

class ServerConfig(BaseModel):
    """Maps to the 'server' object in config.json."""
    default_port: int = 8080
    host: str = "0.0.0.0"
    auto_open_browser: bool = False

class LoggingConfig(BaseModel):
    """Maps to the 'logging' object in config.json."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "flow_metrics.log"
    max_size_mb: int = 10
    backup_count: int = 5

class FlowMetricsSettings(BaseSettings):
    """Main settings class that loads from JSON and overrides with environment variables."""
    azure_devops: AzureDevOpsConfig = Field(default_factory=AzureDevOpsConfig)
    flow_metrics: FlowMetricsConfig = Field(default_factory=FlowMetricsConfig)
    data_management: DataManagementConfig = Field(default_factory=DataManagementConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    stage_metadata: List[StageMetadata] = Field(default_factory=list)
    stage_definitions: Dict[str, List[str]] = Field(default_factory=lambda: {
        "active_states": ["Active", "Committed", "In Progress", "Code Review", "Testing"],
        "completion_states": ["Done", "Closed", "Completed", "Released"],
        "waiting_states": ["Removed", "Cancelled"]
    })
    
    model_config = {"env_prefix": "AZURE_DEVOPS_"}
    
    @classmethod
    def from_file(cls, config_path: Path) -> "FlowMetricsSettings":
        """Load settings from a JSON file."""
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            
            # Handle stage_definitions validation - empty lists should fall back to defaults
            if "stage_definitions" in config_data:
                stage_defs = config_data["stage_definitions"]
                default_defs = {
                    "active_states": ["Active", "Committed", "In Progress", "Code Review", "Testing"],
                    "completion_states": ["Done", "Closed", "Completed", "Released"],
                    "waiting_states": ["Removed", "Cancelled"]
                }
                
                # Replace empty lists with defaults
                for key, default_value in default_defs.items():
                    if key in stage_defs and not stage_defs[key]:
                        stage_defs[key] = default_value
                
                config_data["stage_definitions"] = stage_defs
            
            return cls.model_validate(config_data)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default settings if file doesn't exist or is invalid
            return cls()

# For backward compatibility
ConfigManager = FlowMetricsSettings

# --- Public Accessor Function ---

@lru_cache()
def get_settings() -> FlowMetricsSettings:
    """Loads settings and caches the result.
    
    First loads from config.json, then explicitly overrides with environment variables.
    """
    try:
        # Load from config.json if it exists
        if os.path.exists("config/config.json"):
            with open("config/config.json", "r") as f:
                config_data = json.load(f)
            
            # Create the settings object from config file
            settings = FlowMetricsSettings.model_validate(config_data)
        else:
            # Use default settings if no config file
            settings = FlowMetricsSettings()
    except Exception:
        # Fallback to default settings if config loading fails
        settings = FlowMetricsSettings()
    
    # Override with environment variables if they exist
    if hasattr(settings, 'azure_devops') and settings.azure_devops:
        ado_config = settings.azure_devops.model_dump()
        
        if org_url := os.getenv("AZURE_DEVOPS_ORGANIZATION"):
            ado_config["org_url"] = org_url
        if project := os.getenv("AZURE_DEVOPS_PROJECT"):
            ado_config["default_project"] = project
        if pat := os.getenv("AZURE_DEVOPS_PAT"):
            ado_config["pat_token"] = pat
        
        # Update the settings with the overridden values
        settings.azure_devops = AzureDevOpsConfig.model_validate(ado_config)
    
    return settings
