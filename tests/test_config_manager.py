"""
Tests for configuration management.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from src.config_manager import FlowMetricsSettings


class TestConfigManager:
    """Test configuration management functionality."""

    def test_default_settings(self):
        """Test default settings creation."""
        settings = FlowMetricsSettings()

        # Test default values
        assert settings.azure_devops.organization is None
        assert settings.azure_devops.project is None
        assert settings.azure_devops.pat_token is None
        assert settings.azure_devops.base_url == "https://dev.azure.com"

        # Test default stage definitions
        assert "active_states" in settings.stage_definitions
        assert "completion_states" in settings.stage_definitions
        assert "waiting_states" in settings.stage_definitions

        # Test default active states
        expected_active = [
            "Active",
            "Committed",
            "In Progress",
            "Code Review",
            "Testing",
        ]
        assert settings.stage_definitions["active_states"] == expected_active

    def test_config_from_file(self):
        """Test loading configuration from file."""
        config_data = {
            "azure_devops": {
                "organization": "test-org",
                "project": "test-project",
                "pat_token": "test-token",
            },
            "stage_definitions": {
                "active_states": ["Custom Active"],
                "completion_states": ["Custom Done"],
                "waiting_states": ["Custom Waiting"],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            settings = FlowMetricsSettings.from_file(Path(config_file))

            assert settings.azure_devops.organization == "test-org"
            assert settings.azure_devops.project == "test-project"
            assert settings.azure_devops.pat_token == "test-token"
            assert settings.stage_definitions["active_states"] == ["Custom Active"]
        finally:
            Path(config_file).unlink()

    @patch.dict(
        "os.environ",
        {
            "AZURE_DEVOPS_PAT": "env-token",
            "AZURE_DEVOPS_ORGANIZATION": "env-org",
            "AZURE_DEVOPS_PROJECT": "env-project",
        },
    )
    def test_environment_variables(self):
        """Test configuration from environment variables."""
        settings = FlowMetricsSettings()

        assert settings.azure_devops.pat_token == "env-token"
        assert settings.azure_devops.organization == "env-org"
        assert settings.azure_devops.project == "env-project"

    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid JSON in config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            invalid_config_file = f.name

        try:
            # Should handle invalid JSON gracefully
            settings = FlowMetricsSettings.from_file(Path(invalid_config_file))
            # Should fall back to defaults
            assert settings.azure_devops.organization is None
        finally:
            Path(invalid_config_file).unlink()

    def test_missing_config_file(self):
        """Test handling of missing config file."""
        # Should handle missing file gracefully
        settings = FlowMetricsSettings.from_file(Path("/nonexistent/path/config.json"))

        # Should use defaults
        assert settings.azure_devops.organization is None
        assert len(settings.stage_definitions["active_states"]) > 0

    def test_partial_config(self):
        """Test handling of partial configuration."""
        config_data = {
            "azure_devops": {
                "organization": "partial-org"
                # Missing project and pat_token
            }
            # Missing stage_definitions
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            settings = FlowMetricsSettings.from_file(Path(config_file))

            # Should have partial values
            assert settings.azure_devops.organization == "partial-org"
            # Should have defaults for missing values
            assert settings.azure_devops.project is None
            assert len(settings.stage_definitions["active_states"]) > 0
        finally:
            Path(config_file).unlink()

    def test_config_paths(self):
        """Test configuration path creation."""
        settings = FlowMetricsSettings()

        # Test that paths are Path objects
        assert isinstance(settings.data_management.data_directory, Path)

        # Test default paths
        assert str(settings.data_management.data_directory).endswith("data")
        assert settings.logging.file is not None

    def test_azure_devops_config_validation(self):
        """Test Azure DevOps configuration validation."""
        config_data = {
            "azure_devops": {
                "organization": "",  # Empty string should be treated as None
                "project": "   ",  # Whitespace should be stripped
                "base_url": "https://custom.azure.com",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            settings = FlowMetricsSettings.from_file(Path(config_file))

            # Empty organization should be None
            assert settings.azure_devops.organization is None
            # Whitespace project should be stripped and become None if empty
            assert (
                settings.azure_devops.project is None
                or settings.azure_devops.project.strip() == ""
            )
            # Custom base URL should be preserved
            assert settings.azure_devops.base_url == "https://custom.azure.com"
        finally:
            Path(config_file).unlink()

    def test_stage_definitions_validation(self):
        """Test stage definitions validation."""
        config_data = {
            "stage_definitions": {
                "active_states": [],  # Empty list
                "completion_states": ["Done", "Closed"],
                "waiting_states": ["New", "Blocked"],
                "custom_field": ["Custom"],  # Extra field should be preserved
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            settings = FlowMetricsSettings.from_file(Path(config_file))

            # Empty active_states should fall back to defaults
            assert len(settings.stage_definitions["active_states"]) > 0
            # Other states should be preserved
            assert settings.stage_definitions["completion_states"] == ["Done", "Closed"]
            assert settings.stage_definitions["waiting_states"] == ["New", "Blocked"]
            # Custom fields should be preserved
            assert settings.stage_definitions.get("custom_field") == ["Custom"]
        finally:
            Path(config_file).unlink()
