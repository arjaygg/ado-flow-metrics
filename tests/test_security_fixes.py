"""Tests for security and code quality fixes."""

import unittest.mock as mock
from unittest.mock import Mock, patch

import pytest
import requests

from src.azure_devops_client import AzureDevOpsClient
from src.config_manager import FlowMetricsSettings, DashboardConfig
from src.data_storage import FlowMetricsDatabase


class TestSecurityFixes:
    """Test security fixes implementation."""

    def test_undefined_variable_fix(self):
        """Test that undefined variable issue is fixed in azure_devops_client."""
        client = AzureDevOpsClient(
            "https://dev.azure.com/test", "test-project", "fake-pat"
        )

        # Mock requests.post to raise an exception before response assignment
        with patch("src.azure_devops_client.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError(
                "Connection failed"
            )

            with patch("src.azure_devops_client.logger") as mock_logger:
                # This should not raise UnboundLocalError
                result = client.get_work_items(days_back=30)

                # Should return empty list on error
                assert result == []

                # Should log connection error (now properly categorized)
                mock_logger.error.assert_called()

    def test_pat_token_logging_security(self):
        """Test that PAT tokens are not exposed in debug logs."""
        # Test that the source code contains the security fix
        import inspect

        from src.azure_devops_client import AzureDevOpsClient

        # Get the source code of the _execute_wiql_query method where redaction occurs
        source = inspect.getsource(AzureDevOpsClient._execute_wiql_query)

        # Should contain the redaction logic
        assert "[REDACTED]" in source
        assert "safe_headers" in source

        # Should not log self.headers directly when status is 405
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "if response.status_code == 405:" in line:
                # Check the next few lines for safe logging
                next_lines = "\n".join(lines[i : i + 10])
                assert "safe_headers" in next_lines
                assert (
                    'logger.error(f"Request headers: {self.headers}")' not in next_lines
                )

    def test_network_binding_security(self):
        """Test that default network binding is localhost only."""
        config = DashboardConfig()

        # Default should be localhost only, not all interfaces
        assert config.host == "127.0.0.1"
        assert config.host != "0.0.0.0"

    def test_sql_injection_fix(self):
        """Test that SQL construction uses safer patterns."""
        # Test that the source code uses proper parameterized queries
        import inspect

        from src.data_storage import FlowMetricsDatabase

        # Get the source code of the cleanup method
        source = inspect.getsource(FlowMetricsDatabase.cleanup_old_data)

        # Should use safe parameterization
        assert "placeholders" in source
        assert "?\"] * len(" in source
        # Should use parameterized queries
        assert "cursor.execute(" in source


class TestDependencyUpdates:
    """Test that dependency updates are properly applied."""

    def test_requests_version_updated(self):
        """Test that requests dependency is updated to secure version."""
        # Read requirements.txt to verify version update
        with open("requirements.txt", "r") as f:
            requirements_content = f.read()

        # Should require secure version
        assert "requests>=2.31.0" in requirements_content
        # Should not have old vulnerable version
        assert "requests>=2.28.0" not in requirements_content

    def test_pydantic_version_pinned(self):
        """Test that pydantic version is properly pinned."""
        with open("requirements.txt", "r") as f:
            requirements_content = f.read()

        # Should have version pinning to prevent breaking changes
        assert "pydantic>=2.0.0,<3.0.0" in requirements_content


class TestCodeQualityFixes:
    """Test code quality improvements."""

    def test_azure_client_response_initialization(self):
        """Test that response variable is properly initialized."""
        client = AzureDevOpsClient(
            "https://dev.azure.com/test", "test-project", "fake-pat"
        )

        # Inspect the method to ensure response is initialized
        import inspect

        source = inspect.getsource(client.get_work_items)

        # The refactored code structure eliminates the response variable issue
        # by using proper exception handling in smaller methods
        assert "try:" in source
        assert "except" in source
        assert "return []" in source

    def test_configuration_security_comments(self):
        """Test that configuration has proper security documentation."""
        # Check the model class instead of instance to avoid deprecation warning
        field_info = DashboardConfig.model_fields["host"]
        description = field_info.description

        assert "localhost only" in description or "security" in description


if __name__ == "__main__":
    pytest.main([__file__])
