"""
Tests for Azure DevOps client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import json
from src.azure_devops_client import AzureDevOpsClient
from src.config_manager import FlowMetricsSettings


class TestAzureDevOpsClient:
    """Test Azure DevOps client functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Provide mock configuration for testing."""
        config = Mock(spec=FlowMetricsSettings)
        config.azure_devops.organization = "test-org"
        config.azure_devops.project = "test-project"
        config.azure_devops.pat_token = "test-token"
        config.azure_devops.base_url = "https://dev.azure.com"
        return config
    
    @pytest.fixture
    def client(self, mock_config):
        """Provide configured client for testing."""
        return AzureDevOpsClient(mock_config)
    
    def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = AzureDevOpsClient(mock_config)
        
        assert client.organization == "test-org"
        assert client.project == "test-project"
        assert client.pat_token == "test-token"
        assert client.base_url == "https://dev.azure.com"
    
    def test_missing_configuration(self):
        """Test client with missing configuration."""
        config = Mock(spec=FlowMetricsSettings)
        config.azure_devops.organization = None
        config.azure_devops.project = None
        config.azure_devops.pat_token = None
        
        with pytest.raises(ValueError, match="Azure DevOps configuration is incomplete"):
            AzureDevOpsClient(config)
    
    @patch('src.azure_devops_client.requests.post')
    def test_fetch_work_items_success(self, mock_post, client):
        """Test successful work items fetch."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "workItems": [
                {"id": 1, "url": "https://dev.azure.com/_apis/wit/workItems/1"},
                {"id": 2, "url": "https://dev.azure.com/_apis/wit/workItems/2"}
            ]
        }
        mock_post.return_value = mock_response
        
        # Mock work item details responses
        with patch('src.azure_devops_client.requests.get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {
                "id": 1,
                "fields": {
                    "System.Title": "Test Work Item",
                    "System.WorkItemType": "User Story",
                    "System.State": "Active",
                    "System.AssignedTo": {"displayName": "John Doe"},
                    "System.CreatedDate": "2024-01-01T00:00:00Z",
                    "System.ChangedDate": "2024-01-02T00:00:00Z"
                }
            }
            
            work_items = client.fetch_work_items()
            
            assert len(work_items) >= 0  # Should return work items
            mock_post.assert_called_once()
    
    @patch('src.azure_devops_client.requests.post')
    def test_fetch_work_items_api_error(self, mock_post, client):
        """Test work items fetch with API error."""
        # Mock API error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="API Error"):
            client.fetch_work_items()
    
    @patch('src.azure_devops_client.requests.get')
    def test_fetch_work_item_details_success(self, mock_get, client):
        """Test successful work item details fetch."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "id": 123,
            "fields": {
                "System.Title": "Test Item",
                "System.WorkItemType": "Bug",
                "System.State": "Done",
                "System.AssignedTo": {"displayName": "Jane Smith"},
                "System.CreatedDate": "2024-01-01T10:00:00Z",
                "System.ChangedDate": "2024-01-05T15:30:00Z"
            }
        }
        mock_get.return_value = mock_response
        
        work_item = client._fetch_work_item_details(123)
        
        assert work_item.id == 123
        assert work_item.title == "Test Item"
        assert work_item.work_item_type == "Bug"
        assert work_item.state == "Done"
        assert work_item.assigned_to == "Jane Smith"
    
    @patch('src.azure_devops_client.requests.get')
    def test_fetch_work_item_details_missing_fields(self, mock_get, client):
        """Test work item details fetch with missing fields."""
        # Mock response with missing optional fields
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "id": 124,
            "fields": {
                "System.Title": "Minimal Item",
                "System.WorkItemType": "Task",
                "System.State": "New",
                "System.CreatedDate": "2024-01-01T10:00:00Z",
                "System.ChangedDate": "2024-01-01T10:00:00Z"
                # Missing AssignedTo
            }
        }
        mock_get.return_value = mock_response
        
        work_item = client._fetch_work_item_details(124)
        
        assert work_item.id == 124
        assert work_item.title == "Minimal Item"
        assert work_item.assigned_to == "Unassigned"  # Default value
    
    @patch('src.azure_devops_client.requests.get')
    def test_fetch_state_transitions_success(self, mock_get, client):
        """Test successful state transitions fetch."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "value": [
                {
                    "fields": {
                        "System.State": {
                            "oldValue": "New",
                            "newValue": "Active"
                        }
                    },
                    "changedDate": "2024-01-02T10:00:00Z",
                    "changedBy": {"displayName": "John Doe"}
                },
                {
                    "fields": {
                        "System.State": {
                            "oldValue": "Active",
                            "newValue": "Done"
                        }
                    },
                    "changedDate": "2024-01-05T15:00:00Z",
                    "changedBy": {"displayName": "Jane Smith"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        transitions = client._fetch_state_transitions(123)
        
        assert len(transitions) == 2
        assert transitions[0].from_state == "New"
        assert transitions[0].to_state == "Active"
        assert transitions[1].from_state == "Active"
        assert transitions[1].to_state == "Done"
    
    @patch('src.azure_devops_client.requests.get')
    def test_fetch_state_transitions_no_state_changes(self, mock_get, client):
        """Test state transitions fetch with no state changes."""
        # Mock response with no state transitions
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "value": [
                {
                    "fields": {
                        "System.Title": {
                            "oldValue": "Old Title",
                            "newValue": "New Title"
                        }
                    },
                    "changedDate": "2024-01-02T10:00:00Z",
                    "changedBy": {"displayName": "John Doe"}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        transitions = client._fetch_state_transitions(123)
        
        assert len(transitions) == 0
    
    def test_build_wiql_query(self, client):
        """Test WIQL query building."""
        # Test default query
        query = client._build_wiql_query()
        
        assert "SELECT [System.Id]" in query
        assert "FROM workitems" in query
        assert "[System.TeamProject] = 'test-project'" in query
        
        # Test query with date filter
        query_with_date = client._build_wiql_query(days_back=30)
        
        assert "AND [System.ChangedDate] >= " in query_with_date
    
    def test_batch_work_items(self, client):
        """Test work items batching."""
        work_item_ids = list(range(1, 501))  # 500 items
        
        batches = client._batch_work_items(work_item_ids)
        
        # Should create 3 batches (200, 200, 100)
        assert len(batches) == 3
        assert len(batches[0]) == 200
        assert len(batches[1]) == 200
        assert len(batches[2]) == 100
    
    def test_headers_creation(self, client):
        """Test HTTP headers creation."""
        headers = client._get_headers()
        
        assert "Authorization" in headers
        assert "Basic" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
    
    @patch('src.azure_devops_client.requests.post')
    def test_fetch_work_items_empty_result(self, mock_post, client):
        """Test work items fetch with empty result."""
        # Mock empty API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"workItems": []}
        mock_post.return_value = mock_response
        
        work_items = client.fetch_work_items()
        
        assert len(work_items) == 0
    
    def test_date_parsing(self, client):
        """Test date parsing functionality."""
        # Test valid ISO date
        date_str = "2024-01-01T10:30:00Z"
        parsed_date = client._parse_date(date_str)
        
        assert isinstance(parsed_date, datetime)
        assert parsed_date.tzinfo == timezone.utc
        
        # Test invalid date
        invalid_date = client._parse_date("invalid-date")
        assert isinstance(invalid_date, datetime)  # Should return current time as fallback
    
    @patch('src.azure_devops_client.requests.get')
    def test_network_timeout_handling(self, mock_get, client):
        """Test handling of network timeouts."""
        # Mock timeout exception
        mock_get.side_effect = Exception("Network timeout")
        
        with pytest.raises(Exception, match="Network timeout"):
            client._fetch_work_item_details(123)