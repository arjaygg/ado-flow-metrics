"""Test configuration environment variable behavior."""

import os
import pytest
from unittest.mock import patch
from src.config_manager import AzureDevOpsConfig, FlowMetricsSettings


class TestConfigEnvironmentVariables:
    """Test environment variable priority in configuration."""
    
    def test_env_vars_override_config_values(self):
        """Test that environment variables take precedence over config file values."""
        # Arrange: Mock environment variables
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_PAT': 'env-pat-token',
            'AZURE_DEVOPS_ORGANIZATION': 'env-org',
            'AZURE_DEVOPS_PROJECT': 'env-project'
        }):
            # Config data with placeholder values (like config.json)
            config_data = {
                'pat_token': '${AZURE_DEVOPS_PAT}',
                'organization': 'placeholder-org',
                'default_project': 'your-project-name'
            }
            
            # Act: Create config with environment variables set
            config = AzureDevOpsConfig(**config_data)
            
            # Assert: Environment variables should override config values
            assert config.pat_token == 'env-pat-token'
            assert config.organization == 'env-org'
            assert config.default_project == 'env-project'
    
    def test_config_fallback_when_no_env_vars(self):
        """Test that config values are used when environment variables are not set."""
        # Arrange: Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            config_data = {
                'pat_token': 'config-pat-token',
                'organization': 'config-org',
                'default_project': 'config-project'
            }
            
            # Act: Create config without environment variables
            config = AzureDevOpsConfig(**config_data)
            
            # Assert: Config values should be used
            assert config.pat_token == 'config-pat-token'
            assert config.organization == 'config-org'
            assert config.default_project == 'config-project'
    
    def test_partial_env_var_override(self):
        """Test behavior when only some environment variables are set."""
        # Arrange: Set only PAT and project env vars
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_PAT': 'env-pat-token',
            'AZURE_DEVOPS_PROJECT': 'env-project'
        }, clear=True):
            config_data = {
                'pat_token': 'config-pat-token',
                'organization': 'config-org',
                'default_project': 'config-project'
            }
            
            # Act: Create config with partial environment variables
            config = AzureDevOpsConfig(**config_data)
            
            # Assert: Environment variables should override, config used for missing
            assert config.pat_token == 'env-pat-token'  # From env
            assert config.organization == 'config-org'  # From config (no env var)
            assert config.default_project == 'env-project'  # From env
    
    def test_empty_env_vars_use_config(self):
        """Test that empty environment variables fall back to config values."""
        # Arrange: Set empty environment variables
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_PAT': '',
            'AZURE_DEVOPS_ORGANIZATION': '',
            'AZURE_DEVOPS_PROJECT': ''
        }):
            config_data = {
                'pat_token': 'config-pat-token',
                'organization': 'config-org',
                'default_project': 'config-project'
            }
            
            # Act: Create config with empty environment variables
            config = AzureDevOpsConfig(**config_data)
            
            # Assert: Config values should be used for empty env vars
            assert config.pat_token == 'config-pat-token'
            assert config.organization == 'config-org'
            assert config.default_project == 'config-project'
    
    def test_placeholder_values_overridden_by_env(self):
        """Test the exact scenario from the bug - placeholder config values."""
        # Arrange: Environment variable with real value, config with placeholder
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_PROJECT': 'Axos-Universal-Core'
        }, clear=True):
            # This is exactly what's in the config.json file
            config_data = {
                'org_url': 'https://dev.azure.com/your-org',
                'default_project': 'your-project-name',  # Placeholder value
                'pat_token': '${AZURE_DEVOPS_PAT}'
            }
            
            # Act: Create config (this was failing before)
            config = AzureDevOpsConfig(**config_data)
            
            # Assert: Environment variable should override placeholder
            assert config.default_project == 'Axos-Universal-Core'
            assert config.org_url == 'https://dev.azure.com/your-org'  # Config value used
            assert config.pat_token is None  # No env var set, placeholder ignored
    
    def test_flow_metrics_settings_integration(self):
        """Test environment variables work through FlowMetricsSettings."""
        # Arrange: Set environment variables
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_PAT': 'integration-pat',
            'AZURE_DEVOPS_ORGANIZATION': 'integration-org',
            'AZURE_DEVOPS_PROJECT': 'integration-project'
        }):
            # Act: Create settings (simulates loading from config file)
            settings = FlowMetricsSettings(azure_devops={
                'org_url': 'https://dev.azure.com/placeholder',
                'default_project': 'placeholder-project'
            })
            
            # Assert: Environment variables should be used
            assert settings.azure_devops.pat_token == 'integration-pat'
            assert settings.azure_devops.organization == 'integration-org'
            assert settings.azure_devops.default_project == 'integration-project'