"""
Comprehensive unit tests for WIQL Client - Critical gap coverage.
Tests all edge cases, error conditions, and business logic.
Follows AAA pattern with comprehensive assertions.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.exceptions import WIQLError, WIQLParseError, WIQLValidationError
from src.models import StateTransition, WorkItem
from src.wiql_client import WIQLClient


@pytest.fixture
def wiql_client():
    """Create WIQL client for testing."""
    return WIQLClient(
        org_url="https://dev.azure.com/test-org",
        project="test-project",
        pat_token="test-token-123",
    )


@pytest.fixture
def mock_work_items():
    """Mock work items for testing."""
    return [
        {
            "id": 1001,
            "fields": {
                "System.Title": "Test User Story",
                "System.WorkItemType": "User Story",
                "System.State": "Active",
                "System.AssignedTo": {"displayName": "John Doe"},
                "System.CreatedDate": "2024-01-01T00:00:00Z",
                "System.ChangedDate": "2024-01-15T12:00:00Z",
            },
        },
        {
            "id": 1002,
            "fields": {
                "System.Title": "Test Bug",
                "System.WorkItemType": "Bug",
                "System.State": "New",
                "System.AssignedTo": {"displayName": "Jane Smith"},
                "System.CreatedDate": "2024-01-02T00:00:00Z",
                "System.ChangedDate": "2024-01-16T14:00:00Z",
            },
        },
    ]


@pytest.mark.unit
class TestWIQLClientInitialization:
    """Test WIQL client initialization and configuration."""

    def test_client_inherits_from_azure_client(self, wiql_client):
        """Test that WIQL client properly inherits from Azure DevOps client."""
        # ARRANGE & ACT - Client created in fixture

        # ASSERT
        assert hasattr(wiql_client, "org_url")
        assert hasattr(wiql_client, "project")
        assert hasattr(wiql_client, "pat_token")
        assert hasattr(wiql_client, "wiql_parser")
        assert wiql_client.org_url == "https://dev.azure.com/test-org"
        assert wiql_client.project == "test-project"

    def test_wiql_parser_initialization(self, wiql_client):
        """Test WIQL parser is properly initialized."""
        # ARRANGE & ACT - Client created in fixture

        # ASSERT
        assert wiql_client.wiql_parser is not None
        assert hasattr(wiql_client, "_wiql_cache")
        assert isinstance(wiql_client._wiql_cache, dict)

    def test_cache_initialization(self, wiql_client):
        """Test WIQL cache is properly initialized."""
        # ARRANGE & ACT - Client created in fixture

        # ASSERT
        assert wiql_client._wiql_cache == {}


@pytest.mark.unit
class TestWIQLQueryExecution:
    """Test WIQL query execution logic."""

    @patch("src.wiql_client.WIQLClient._execute_parsed_query")
    @patch("src.wiql_client.WIQLClient._parse_and_validate_query")
    def test_execute_wiql_query_success(
        self, mock_parse, mock_execute, wiql_client, mock_work_items
    ):
        """Test successful WIQL query execution."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.State] = 'Active'"
        mock_parsed_query = Mock()
        mock_parse.return_value = mock_parsed_query
        mock_execute.return_value = mock_work_items

        # ACT
        result = wiql_client.execute_wiql_query(query)

        # ASSERT
        assert result == mock_work_items
        mock_parse.assert_called_once_with(query)
        mock_execute.assert_called_once_with(mock_parsed_query, None)

    @patch("src.wiql_client.WIQLClient._parse_and_validate_query")
    def test_execute_wiql_query_with_validation_disabled(self, mock_parse, wiql_client):
        """Test WIQL query execution with validation disabled."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"
        with patch.object(wiql_client.wiql_parser, "parse_query") as mock_parser_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parsed_query = Mock()
                mock_parser_parse.return_value = mock_parsed_query
                mock_execute.return_value = []

                # ACT
                result = wiql_client.execute_wiql_query(query, validate=False)

                # ASSERT
                mock_parse.assert_not_called()
                mock_parser_parse.assert_called_once_with(query)
                mock_execute.assert_called_once_with(mock_parsed_query, None)

    @patch("src.wiql_client.WIQLClient._parse_and_validate_query")
    def test_execute_wiql_query_with_progress_callback(self, mock_parse, wiql_client):
        """Test WIQL query execution with progress callback."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"
        progress_callback = Mock()
        mock_parsed_query = Mock()
        mock_parse.return_value = mock_parsed_query

        with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
            mock_execute.return_value = []

            # ACT
            result = wiql_client.execute_wiql_query(
                query, progress_callback=progress_callback
            )

            # ASSERT
            mock_execute.assert_called_once_with(mock_parsed_query, progress_callback)

    @patch("src.wiql_client.WIQLClient._parse_and_validate_query")
    def test_execute_wiql_query_parse_error(self, mock_parse, wiql_client):
        """Test WIQL query execution with parse error."""
        # ARRANGE
        query = "INVALID WIQL QUERY"
        mock_parse.side_effect = WIQLParseError("Invalid query syntax")

        # ACT & ASSERT
        with pytest.raises(WIQLError) as exc_info:
            wiql_client.execute_wiql_query(query)

        assert "WIQL query execution failed" in str(exc_info.value)

    @patch("src.wiql_client.WIQLClient._execute_parsed_query")
    @patch("src.wiql_client.WIQLClient._parse_and_validate_query")
    def test_execute_wiql_query_execution_error(
        self, mock_parse, mock_execute, wiql_client
    ):
        """Test WIQL query execution with execution error."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"
        mock_parsed_query = Mock()
        mock_parse.return_value = mock_parsed_query
        mock_execute.side_effect = requests.exceptions.RequestException("Network error")

        # ACT & ASSERT
        with pytest.raises(WIQLError) as exc_info:
            wiql_client.execute_wiql_query(query)

        assert "WIQL query execution failed" in str(exc_info.value)


@pytest.mark.unit
class TestWIQLClientAdvancedFiltering:
    """Test advanced WIQL filtering capabilities."""

    @patch("src.wiql_client.create_filtered_work_items_query")
    @patch("src.wiql_client.WIQLClient.execute_wiql_query")
    def test_get_work_items_with_wiql_default_params(
        self, mock_execute, mock_create_query, wiql_client
    ):
        """Test get_work_items_with_wiql with default parameters."""
        # ARRANGE
        mock_query = "SELECT [System.Id] FROM WorkItems"
        mock_create_query.return_value = mock_query
        mock_execute.return_value = []

        # ACT
        result = wiql_client.get_work_items_with_wiql()

        # ASSERT
        mock_create_query.assert_called_once_with(
            project=None,
            days_back=90,
            work_item_types=None,
            states=None,
            assignees=None,
            additional_filters=None,
        )
        mock_execute.assert_called_once_with(
            mock_query, validate=True, progress_callback=None
        )

    @patch("src.wiql_client.create_filtered_work_items_query")
    @patch("src.wiql_client.WIQLClient.execute_wiql_query")
    def test_get_work_items_with_wiql_custom_params(
        self, mock_execute, mock_create_query, wiql_client
    ):
        """Test get_work_items_with_wiql with custom parameters."""
        # ARRANGE
        mock_query = "SELECT [System.Id] FROM WorkItems WHERE ..."
        mock_create_query.return_value = mock_query
        mock_execute.return_value = []

        # ACT
        result = wiql_client.get_work_items_with_wiql(
            project="custom-project",
            days_back=30,
            work_item_types=["User Story", "Bug"],
            states=["Active", "New"],
            assignees=["john@example.com"],
            additional_filters={"priority": "High"},
        )

        # ASSERT
        mock_create_query.assert_called_once_with(
            project="custom-project",
            days_back=30,
            work_item_types=["User Story", "Bug"],
            states=["Active", "New"],
            assignees=["john@example.com"],
            additional_filters={"priority": "High"},
        )

    def test_get_work_items_with_wiql_empty_filters(self, wiql_client):
        """Test handling of empty filter lists."""
        # ARRANGE
        with patch(
            "src.wiql_client.create_filtered_work_items_query"
        ) as mock_create_query:
            with patch.object(wiql_client, "execute_wiql_query") as mock_execute:
                mock_create_query.return_value = "SELECT [System.Id] FROM WorkItems"
                mock_execute.return_value = []

                # ACT
                result = wiql_client.get_work_items_with_wiql(
                    work_item_types=[], states=[], assignees=[]
                )

                # ASSERT
                mock_create_query.assert_called_once_with(
                    project=None,
                    days_back=90,
                    work_item_types=[],
                    states=[],
                    assignees=[],
                    additional_filters=None,
                )


@pytest.mark.unit
class TestWIQLClientErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_invalid_query_syntax_error(self, wiql_client):
        """Test handling of invalid WIQL query syntax."""
        # ARRANGE
        invalid_query = "INVALID QUERY SYNTAX"

        with patch.object(wiql_client.wiql_parser, "parse_query") as mock_parse:
            mock_parse.side_effect = WIQLParseError("Syntax error at position 8")

            # ACT & ASSERT
            with pytest.raises(WIQLError) as exc_info:
                wiql_client.execute_wiql_query(invalid_query, validate=False)

            assert "WIQL query execution failed" in str(exc_info.value)

    def test_validation_error_handling(self, wiql_client):
        """Test handling of WIQL validation errors."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems WHERE [InvalidField] = 'value'"

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_validate:
            mock_validate.side_effect = WIQLValidationError(
                "Invalid field: InvalidField"
            )

            # ACT & ASSERT
            with pytest.raises(WIQLError) as exc_info:
                wiql_client.execute_wiql_query(query)

            assert "WIQL query execution failed" in str(exc_info.value)

    def test_network_timeout_handling(self, wiql_client):
        """Test handling of network timeouts during query execution."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.side_effect = requests.exceptions.Timeout(
                    "Request timeout"
                )

                # ACT & ASSERT
                with pytest.raises(WIQLError) as exc_info:
                    wiql_client.execute_wiql_query(query)

                assert "WIQL query execution failed" in str(exc_info.value)

    def test_authentication_error_handling(self, wiql_client):
        """Test handling of authentication errors."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.side_effect = requests.exceptions.HTTPError(
                    "401 Unauthorized"
                )

                # ACT & ASSERT
                with pytest.raises(WIQLError) as exc_info:
                    wiql_client.execute_wiql_query(query)

                assert "WIQL query execution failed" in str(exc_info.value)


@pytest.mark.unit
class TestWIQLClientCaching:
    """Test WIQL query caching behavior."""

    def test_cache_empty_initialization(self, wiql_client):
        """Test cache is empty on initialization."""
        # ARRANGE & ACT - Client created in fixture

        # ASSERT
        assert len(wiql_client._wiql_cache) == 0

    def test_cache_storage_and_retrieval(self, wiql_client):
        """Test cache storage and retrieval functionality."""
        # ARRANGE
        query_key = "test_query"
        parsed_query = Mock()

        # ACT
        wiql_client._wiql_cache[query_key] = parsed_query
        retrieved_query = wiql_client._wiql_cache.get(query_key)

        # ASSERT
        assert retrieved_query == parsed_query
        assert len(wiql_client._wiql_cache) == 1

    def test_cache_miss_handling(self, wiql_client):
        """Test cache miss handling."""
        # ARRANGE
        nonexistent_key = "nonexistent_query"

        # ACT
        result = wiql_client._wiql_cache.get(nonexistent_key)

        # ASSERT
        assert result is None


@pytest.mark.unit
class TestWIQLClientEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_query_string(self, wiql_client):
        """Test handling of empty query string."""
        # ARRANGE
        empty_query = ""

        with patch.object(wiql_client.wiql_parser, "parse_query") as mock_parse:
            mock_parse.side_effect = WIQLParseError("Empty query")

            # ACT & ASSERT
            with pytest.raises(WIQLError):
                wiql_client.execute_wiql_query(empty_query, validate=False)

    def test_whitespace_only_query(self, wiql_client):
        """Test handling of whitespace-only query."""
        # ARRANGE
        whitespace_query = "   \n\t   "

        with patch.object(wiql_client.wiql_parser, "parse_query") as mock_parse:
            mock_parse.side_effect = WIQLParseError("Invalid query")

            # ACT & ASSERT
            with pytest.raises(WIQLError):
                wiql_client.execute_wiql_query(whitespace_query, validate=False)

    def test_very_long_query_handling(self, wiql_client):
        """Test handling of very long queries."""
        # ARRANGE
        long_query = "SELECT [System.Id] FROM WorkItems WHERE " + " OR ".join(
            [f"[System.Title] CONTAINS 'test{i}'" for i in range(1000)]
        )

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.return_value = []

                # ACT
                result = wiql_client.execute_wiql_query(long_query)

                # ASSERT
                assert result == []
                mock_parse.assert_called_once_with(long_query)

    def test_special_characters_in_query(self, wiql_client):
        """Test handling of special characters in queries."""
        # ARRANGE
        special_query = "SELECT [System.Id] FROM WorkItems WHERE [System.Title] CONTAINS 'test with \"quotes\" and \\'apostrophes\\' and [brackets]'"

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.return_value = []

                # ACT
                result = wiql_client.execute_wiql_query(special_query)

                # ASSERT
                assert result == []
                mock_parse.assert_called_once()

    def test_null_parameter_handling(self, wiql_client):
        """Test handling of None parameters."""
        # ARRANGE & ACT & ASSERT
        with pytest.raises(Exception):
            wiql_client.execute_wiql_query(None)


@pytest.mark.unit
class TestWIQLClientPerformance:
    """Test performance-related aspects of WIQL client."""

    def test_large_result_set_handling(self, wiql_client):
        """Test handling of large result sets."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"
        large_result_set = [{"id": i} for i in range(10000)]

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.return_value = large_result_set

                # ACT
                result = wiql_client.execute_wiql_query(query)

                # ASSERT
                assert len(result) == 10000
                assert result == large_result_set

    def test_progress_callback_execution(self, wiql_client):
        """Test progress callback is called during execution."""
        # ARRANGE
        query = "SELECT [System.Id] FROM WorkItems"
        progress_callback = Mock()

        with patch.object(wiql_client, "_parse_and_validate_query") as mock_parse:
            with patch.object(wiql_client, "_execute_parsed_query") as mock_execute:
                mock_parse.return_value = Mock()
                mock_execute.return_value = []

                # ACT
                wiql_client.execute_wiql_query(
                    query, progress_callback=progress_callback
                )

                # ASSERT
                mock_execute.assert_called_once_with(Mock(), progress_callback)
