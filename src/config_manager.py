"""Configuration management for Flow Metrics using Pydantic."""

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

# --- Pydantic Models for nested configuration in config.json ---

class AzureDevOpsConfig(BaseModel):
    """Maps to the 'azure_devops' object in config.json."""
    org_url: str
    default_project: str
    pat_token: Optional[str] = None

class FlowMetricsConfig(BaseModel):
    """Maps to the 'flow_metrics' object in config.json."""
    throughput_period_days: int
    default_days_back: int

class DataManagementConfig(BaseModel):
    """Maps to the 'data_management' object in config.json."""
    data_directory: Path
    auto_backup: bool
    export_directory: Path

class ServerConfig(BaseModel):
    """Maps to the 'server' object in config.json."""
    default_port: int
    host: str
    auto_open_browser: bool

class FlowMetricsSettings(BaseModel):
    """Main settings class that loads from JSON and overrides with environment variables."""
    azure_devops: AzureDevOpsConfig
    flow_metrics: FlowMetricsConfig
    data_management: DataManagementConfig
    server: ServerConfig

# --- Public Accessor Function ---

@lru_cache()
def get_settings() -> FlowMetricsSettings:
    """Loads settings and caches the result.
    
    First loads from config.json, then explicitly overrides with environment variables.
    """
    # Load from config.json
    with open("config/config.json", "r") as f:
        config_data = json.load(f)
    
    # Create the settings object
    settings = FlowMetricsSettings.model_validate(config_data)
    
    # Override with environment variables if they exist
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
