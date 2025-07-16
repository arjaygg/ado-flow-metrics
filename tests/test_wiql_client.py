"""Tests for WIQL client functionality."""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.exceptions import WIQLError, WIQLParseError, WIQLValidationError
from src.wiql_client import WIQLClient, create_wiql_client_from_config
from src.wiql_parser import WIQLCondition, WIQLOperator, WIQLQuery


class TestWIQLClient:
    """Test cases for WIQL client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = WIQLClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_execute_wiql_query_success(self, mock_get, mock_post):
        """Test successful WIQL query execution."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "workItems": [
                {
                    "id": 1,
                    "url": "https://dev.azure.com/test-org/_apis/wit/workItems/1",
                },
                {
                    "id": 2,
                    "url": "https://dev.azure.com/test-org/_apis/wit/workItems/2",
                },
            ]
        }

        # Mock work items details response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Test Item 1",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "System.Title": "Test Item 2",
                        "System.WorkItemType": "Bug",
                        "System.State": "Resolved",
                        "System.CreatedDate": "2023-01-02T11:00:00Z",
                    },
                },
            ]
        }

        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'test-project'
        """

        result = self.client.execute_wiql_query(query)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert mock_post.called
        assert mock_get.called

    @patch("src.wiql_client.requests.post")
    def test_execute_wiql_query_validation_error(self, mock_post):
        """Test WIQL query execution with validation error."""
        query = "SELECT [Unknown.Field] FROM WorkItems"

        with pytest.raises(WIQLValidationError):
            self.client.execute_wiql_query(query, validate=True)

    @patch("src.wiql_client.requests.post")
    def test_execute_wiql_query_api_error(self, mock_post):
        """Test WIQL query execution with API error."""
        mock_post.return_value.status_code = 400
        mock_post.return_value.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("Bad Request")
        )

        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'test-project'
        """

        with pytest.raises(WIQLError):
            self.client.execute_wiql_query(query)

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_get_work_items_with_wiql_default_query(self, mock_get, mock_post):
        """Test getting work items with default WIQL query."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "workItems": [{"id": 1, "url": "test-url"}]
        }

        # Mock work items details response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Test Item",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                    },
                }
            ]
        }

        result = self.client.get_work_items_with_wiql(
            days_back=30, work_item_types=["User Story"], states=["Active"]
        )

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert mock_post.called

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_get_work_items_with_wiql_custom_query(self, mock_get, mock_post):
        """Test getting work items with custom WIQL query."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "workItems": [{"id": 1, "url": "test-url"}]
        }

        # Mock work items details response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Test Item",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                    },
                }
            ]
        }

        custom_query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.Title] LIKE 'Test%'
        """

        result = self.client.get_work_items_with_wiql(custom_wiql=custom_query)

        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_validate_wiql_query_valid(self):
        """Test validating valid WIQL query."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'test-project'
        """

        result = self.client.validate_wiql_query(query)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["parsed_query"] is not None

    def test_validate_wiql_query_invalid(self):
        """Test validating invalid WIQL query."""
        query = "INVALID QUERY"

        result = self.client.validate_wiql_query(query)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["parsed_query"] is None

    def test_get_wiql_query_preview(self):
        """Test getting WIQL query preview."""
        preview = self.client.get_wiql_query_preview(
            days_back=30, work_item_types=["User Story", "Bug"], states=["Active"]
        )

        assert "SELECT [System.Id]" in preview
        assert "FROM WorkItems" in preview
        assert "WHERE [System.TeamProject] = 'test-project'" in preview
        assert "AND [System.WorkItemType] IN ('User Story', 'Bug')" in preview
        assert "AND [System.State] IN ('Active')" in preview

    def test_get_supported_fields(self):
        """Test getting supported fields."""
        fields = self.client.get_supported_fields()

        assert "System.Id" in fields
        assert "System.Title" in fields
        assert "System.WorkItemType" in fields

        # Check field structure
        title_field = fields["System.Title"]
        assert title_field["name"] == "Title"
        assert title_field["reference_name"] == "System.Title"
        assert title_field["type"] == "string"
        assert title_field["is_sortable"] is True
        assert title_field["is_queryable"] is True
        assert len(title_field["supported_operators"]) > 0

    def test_register_custom_field(self):
        """Test registering custom field."""
        self.client.register_custom_field(
            "Custom.Field", "string", display_name="Custom Field", is_sortable=True
        )

        fields = self.client.get_supported_fields()
        assert "Custom.Field" in fields
        assert fields["Custom.Field"]["name"] == "Custom Field"
        assert fields["Custom.Field"]["type"] == "string"

    def test_register_custom_field_invalid_type(self):
        """Test registering custom field with invalid type."""
        with pytest.raises(WIQLError):
            self.client.register_custom_field("Custom.Field", "invalid_type")

    def test_create_filtered_query(self):
        """Test creating filtered query."""
        query = self.client.create_filtered_query(
            work_item_types=["User Story", "Bug"],
            states=["Active", "Resolved"],
            days_back=30,
        )

        assert "SELECT [System.Id]" in query
        assert "FROM WorkItems" in query
        assert "WHERE [System.TeamProject] = 'test-project'" in query
        assert "AND [System.WorkItemType] IN ('User Story', 'Bug')" in query
        assert "AND [System.State] IN ('Active', 'Resolved')" in query

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_test_wiql_connection_success(self, mock_get, mock_post):
        """Test WIQL connection test success."""
        # Mock verify_connection
        with patch.object(self.client, "verify_connection", return_value=True):
            # Mock WIQL query response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "workItems": [{"id": 1, "url": "test-url"}]
            }

            # Mock work items details response
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "value": [
                    {
                        "id": 1,
                        "fields": {
                            "System.Title": "Test Item",
                            "System.WorkItemType": "User Story",
                            "System.State": "Active",
                            "System.CreatedDate": "2023-01-01T10:00:00Z",
                        },
                    }
                ]
            }

            result = self.client.test_wiql_connection()

            assert result["connection_ok"] is True
            assert result["wiql_ok"] is True
            assert result["validation_ok"] is True
            assert result["work_items_found"] == 1
            assert "successful" in result["message"]

    @patch("src.wiql_client.requests.post")
    def test_test_wiql_connection_validation_error(self, mock_post):
        """Test WIQL connection test with validation error."""
        with patch.object(self.client, "verify_connection", return_value=True):
            # Mock the parser to return validation errors
            with patch.object(
                self.client.wiql_parser, "validate_query", return_value=["Test error"]
            ):
                result = self.client.test_wiql_connection()

                assert result["connection_ok"] is True
                assert result["wiql_ok"] is False
                assert result["validation_ok"] is False
                assert "validation_errors" in result
                assert "validation failed" in result["message"]

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_get_work_item_statistics(self, mock_get, mock_post):
        """Test getting work item statistics."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "workItems": [{"id": 1, "url": "test-url"}, {"id": 2, "url": "test-url"}]
        }

        # Mock work items details response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Test Item 1",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                        "System.AssignedTo": {"displayName": "John Doe"},
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "System.Title": "Test Item 2",
                        "System.WorkItemType": "Bug",
                        "System.State": "Resolved",
                        "System.CreatedDate": "2023-01-02T11:00:00Z",
                        "System.AssignedTo": {"displayName": "Jane Smith"},
                    },
                },
            ]
        }

        result = self.client.get_work_item_statistics()

        assert result["total_items"] == 2
        assert result["by_type"]["User Story"] == 1
        assert result["by_type"]["Bug"] == 1
        assert result["by_state"]["Active"] == 1
        assert result["by_state"]["Resolved"] == 1
        assert result["by_assignee"]["John Doe"] == 1
        assert result["by_assignee"]["Jane Smith"] == 1
        assert result["date_range"]["earliest"] is not None
        assert result["date_range"]["latest"] is not None

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_get_work_item_statistics_empty(self, mock_get, mock_post):
        """Test getting work item statistics with no items."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"workItems": []}

        result = self.client.get_work_item_statistics()

        assert result["total_items"] == 0
        assert "No work items found" in result["message"]

    def test_wiql_cache(self):
        """Test WIQL query caching."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'test-project'
        """

        # Parse query twice
        parsed1 = self.client._parse_and_validate_query(query)
        parsed2 = self.client._parse_and_validate_query(query)

        # Should be the same object (cached)
        assert parsed1 is parsed2

        # Check cache contains the query
        cache_key = hash(query)
        assert cache_key in self.client._wiql_cache

    def test_progress_callback(self):
        """Test progress callback functionality."""
        callback_calls = []

        def progress_callback(phase, message):
            callback_calls.append((phase, message))

        with patch("src.wiql_client.requests.post") as mock_post:
            with patch("src.wiql_client.requests.get") as mock_get:
                # Mock responses
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {"workItems": []}

                try:
                    self.client.get_work_items_with_wiql(
                        days_back=30, progress_callback=progress_callback
                    )
                except:
                    pass  # Ignore errors, we just want to test callbacks

                # Check that callbacks were called
                assert len(callback_calls) > 0
                assert any(
                    "Building WIQL query" in str(call) for call in callback_calls
                )


class TestWIQLClientFactory:
    """Test cases for WIQL client factory functions."""

    def test_create_wiql_client_from_config(self):
        """Test creating WIQL client from configuration."""
        config = {
            "azure_devops": {
                "org_url": "https://dev.azure.com/test-org",
                "default_project": "test-project",
                "pat_token": "test-token",
            }
        }

        client = create_wiql_client_from_config(config)

        assert isinstance(client, WIQLClient)
        assert client.org_url == "https://dev.azure.com/test-org"
        assert client.project == "test-project"
        assert client.pat_token == "test-token"

    def test_create_wiql_client_from_config_missing_fields(self):
        """Test creating WIQL client with missing configuration fields."""
        config = {
            "azure_devops": {
                "org_url": "https://dev.azure.com/test-org"
                # Missing project and pat_token
            }
        }

        with pytest.raises(WIQLError):
            create_wiql_client_from_config(config)

    def test_create_wiql_client_from_config_alternative_field_names(self):
        """Test creating WIQL client with alternative field names."""
        config = {
            "azure_devops": {
                "organization": "https://dev.azure.com/test-org",
                "project": "test-project",
                "pat_token": "test-token",
            }
        }

        client = create_wiql_client_from_config(config)

        assert isinstance(client, WIQLClient)
        assert client.org_url == "https://dev.azure.com/test-org"
        assert client.project == "test-project"


if __name__ == "__main__":
    pytest.main([__file__])
