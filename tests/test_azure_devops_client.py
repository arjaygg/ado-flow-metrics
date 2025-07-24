"""
Comprehensive tests for Azure DevOps client functionality.
"""

import pytest
import json
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from src.azure_devops_client import AzureDevOpsClient
from src.config_manager import FlowMetricsSettings
from src.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    WIQLError,
    WIQLValidationError,
)


class TestAzureDevOpsClient:
    """Test Azure DevOps client functionality."""

    @pytest.fixture
    def mock_config(self):
        """Provide mock configuration for testing."""
        config = Mock(spec=FlowMetricsSettings)
        azure_devops_mock = Mock()
        azure_devops_mock.organization = "test-org"
        azure_devops_mock.project = "test-project"
        azure_devops_mock.pat_token = "test-token"
        azure_devops_mock.base_url = "https://dev.azure.com"
        config.azure_devops = azure_devops_mock
        return config

    @pytest.fixture
    def client(self, mock_config):
        """Provide configured client for testing."""
        return AzureDevOpsClient(
            org_url=mock_config.azure_devops.base_url
            + "/"
            + mock_config.azure_devops.organization,
            project=mock_config.azure_devops.project,
            pat_token=mock_config.azure_devops.pat_token,
        )

    def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = AzureDevOpsClient(
            org_url=mock_config.azure_devops.base_url
            + "/"
            + mock_config.azure_devops.organization,
            project=mock_config.azure_devops.project,
            pat_token=mock_config.azure_devops.pat_token,
        )

        assert client.org_url == "https://dev.azure.com/test-org"
        assert client.project == "test-project"
        assert client.pat_token == "test-token"
        assert "Authorization" in client.headers
        assert "Content-Type" in client.headers

    def test_missing_configuration(self):
        """Test client with missing configuration."""
        with pytest.raises(AttributeError):
            AzureDevOpsClient(org_url=None, project=None, pat_token=None)

    @patch("src.azure_devops_client.requests.post")
    @patch("src.azure_devops_client.requests.get")
    def test_get_work_items_success(self, mock_get, mock_post, client):
        """Test successful work items fetch."""
        # Mock WIQL query response
        mock_post_response = Mock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = {
            "workItems": [
                {"id": 1, "url": "https://dev.azure.com/_apis/wit/workItems/1"},
                {"id": 2, "url": "https://dev.azure.com/_apis/wit/workItems/2"},
            ]
        }
        mock_post.return_value = mock_post_response

        # Mock work item details responses
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Test Work Item 1",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.AssignedTo": {"displayName": "John Doe"},
                        "System.CreatedDate": "2024-01-01T00:00:00Z",
                        "System.ChangedDate": "2024-01-02T00:00:00Z",
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "System.Title": "Test Work Item 2",
                        "System.WorkItemType": "Bug",
                        "System.State": "New",
                        "System.AssignedTo": {"displayName": "Jane Doe"},
                        "System.CreatedDate": "2024-01-03T00:00:00Z",
                        "System.ChangedDate": "2024-01-04T00:00:00Z",
                    },
                },
            ]
        }
        mock_get.return_value = mock_get_response

        work_items = client.get_work_items()

        assert len(work_items) == 2
        assert work_items[0]["id"] == 1  # Work item ID as returned by API
        assert work_items[0]["title"] == "Test Work Item 1"
        assert work_items[1]["id"] == "WI-2"
        assert work_items[1]["title"] == "Test Work Item 2"

    @patch("src.azure_devops_client.requests.post")
    def test_get_work_items_api_error(self, mock_post, client):
        """Test work items fetch with API error."""
        mock_post.side_effect = Exception("API Error")

        work_items = client.get_work_items()
        assert work_items == []

    @patch("src.azure_devops_client.requests.post")
    def test_get_work_items_empty_result(self, mock_post, client):
        """Test work items fetch with empty result."""
        # Mock empty API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"workItems": []}
        mock_post.return_value = mock_response

        work_items = client.get_work_items()
        assert work_items == []

    @patch("src.azure_devops_client.requests.get")
    def test_get_state_history_success(self, mock_get, client):
        """Test successful state history fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [
                {
                    "fields": {
                        "System.State": {"newValue": "Active"},
                        "System.ChangedDate": {"newValue": "2024-01-01T00:00:00Z"},
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        history = client._get_state_history(123)
        assert len(history) == 1
        assert history[0]["state"] == "Active"

    @patch("src.azure_devops_client.requests.get")
    def test_get_state_history_error(self, mock_get, client):
        """Test state history fetch with error."""
        mock_get.side_effect = Exception("Network error")

        history = client._get_state_history(123)
        assert history == []

    @patch("src.azure_devops_client.requests.get")
    def test_get_team_members_success(self, mock_get, client):
        """Test successful team members fetch."""
        # Mock teams response first
        mock_teams_response = Mock()
        mock_teams_response.status_code = 200
        mock_teams_response.json.return_value = {
            "value": [{"id": "team1", "name": "Test Team"}]
        }

        # Mock team members response
        mock_members_response = Mock()
        mock_members_response.status_code = 200
        mock_members_response.json.return_value = {
            "value": [
                {"identity": {"displayName": "John Doe"}},
                {"identity": {"displayName": "Jane Doe"}},
            ]
        }

        mock_get.side_effect = [mock_teams_response, mock_members_response]

        members = client.get_team_members()
        assert len(members) == 2
        assert "John Doe" in members
        assert "Jane Doe" in members

    @patch("src.azure_devops_client.requests.get")
    def test_get_team_members_error(self, mock_get, client):
        """Test team members fetch with error."""
        mock_get.side_effect = Exception("Network error")

        members = client.get_team_members()
        assert members == []
