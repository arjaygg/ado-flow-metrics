"""
Integration tests for Azure DevOps API functionality.

These tests verify the actual integration between components:
- Azure DevOps API client with real-like responses
- Configuration manager with different settings
- Data storage with database interactions
- Error handling across component boundaries
"""

import pytest
import json
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.azure_devops_client import AzureDevOpsClient
from src.config_manager import FlowMetricsSettings
from src.data_storage import FlowMetricsDatabase
from src.calculator import FlowMetricsCalculator
from src.models import WorkItem, StateTransition


@pytest.mark.integration
class TestAzureDevOpsIntegration:
    """Integration tests for Azure DevOps API integration."""

    @pytest.fixture
    def integration_config(self):
        """Create realistic integration configuration."""
        config_data = {
            "azure_devops": {
                "organization": "test-integration-org",
                "project": "test-integration-project", 
                "pat_token": "integration-test-token-123",
                "base_url": "https://dev.azure.com",
                "api_version": "7.0"
            },
            "stage_definitions": {
                "active_states": ["Active", "In Progress", "Code Review", "Testing"],
                "completion_states": ["Done", "Closed", "Resolved", "Completed"],
                "waiting_states": ["New", "Blocked", "Waiting", "On Hold"]
            },
            "data_dir": "integration_test_data",
            "log_dir": "integration_test_logs",
            "cache_duration_hours": 1
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        yield config_file
        Path(config_file).unlink(missing_ok=True)

    @pytest.fixture
    def mock_ado_responses(self):
        """Create realistic Azure DevOps API response data."""
        return {
            "wiql_response": {
                "workItems": [
                    {"id": 1001, "url": "https://dev.azure.com/_apis/wit/workItems/1001"},
                    {"id": 1002, "url": "https://dev.azure.com/_apis/wit/workItems/1002"},
                    {"id": 1003, "url": "https://dev.azure.com/_apis/wit/workItems/1003"}
                ]
            },
            "work_items_batch_response": {
                "value": [
                    {
                        "id": 1001,
                        "fields": {
                            "System.Title": "Implement user authentication",
                            "System.WorkItemType": "User Story",
                            "System.State": "Done",
                            "System.AssignedTo": {"displayName": "Alice Johnson"},
                            "System.CreatedDate": "2024-01-01T08:00:00Z",
                            "System.ChangedDate": "2024-01-15T16:30:00Z",
                            "System.Tags": "backend;security;critical"
                        }
                    },
                    {
                        "id": 1002,
                        "fields": {
                            "System.Title": "Fix login validation bug",
                            "System.WorkItemType": "Bug",
                            "System.State": "In Progress", 
                            "System.AssignedTo": {"displayName": "Bob Smith"},
                            "System.CreatedDate": "2024-01-05T09:15:00Z",
                            "System.ChangedDate": "2024-01-10T14:20:00Z",
                            "System.Tags": "frontend;urgent"
                        }
                    },
                    {
                        "id": 1003,
                        "fields": {
                            "System.Title": "Database optimization task",
                            "System.WorkItemType": "Task",
                            "System.State": "Blocked",
                            "System.AssignedTo": {"displayName": "Charlie Brown"},
                            "System.CreatedDate": "2024-01-03T10:30:00Z",
                            "System.ChangedDate": "2024-01-08T11:45:00Z",
                            "System.Tags": "database;performance"
                        }
                    }
                ]
            },
            "state_history_1001": {
                "value": [
                    {
                        "fields": {
                            "System.State": {"oldValue": None, "newValue": "New"},
                            "System.ChangedDate": {"newValue": "2024-01-01T08:00:00Z"}
                        },
                        "changedBy": {"displayName": "System"}
                    },
                    {
                        "fields": {
                            "System.State": {"oldValue": "New", "newValue": "Active"},
                            "System.ChangedDate": {"newValue": "2024-01-02T09:00:00Z"}
                        },
                        "changedBy": {"displayName": "Alice Johnson"}
                    },
                    {
                        "fields": {
                            "System.State": {"oldValue": "Active", "newValue": "Code Review"},
                            "System.ChangedDate": {"newValue": "2024-01-12T15:30:00Z"}
                        },
                        "changedBy": {"displayName": "Alice Johnson"}
                    },
                    {
                        "fields": {
                            "System.State": {"oldValue": "Code Review", "newValue": "Done"},
                            "System.ChangedDate": {"newValue": "2024-01-15T16:30:00Z"}
                        },
                        "changedBy": {"displayName": "Bob Smith"}
                    }
                ]
            },
            "teams_response": {
                "value": [
                    {"id": "team1", "name": "Development Team"},
                    {"id": "team2", "name": "QA Team"}
                ]
            },
            "team_members_response": {
                "value": [
                    {"identity": {"displayName": "Alice Johnson"}},
                    {"identity": {"displayName": "Bob Smith"}},
                    {"identity": {"displayName": "Charlie Brown"}},
                    {"identity": {"displayName": "Diana Prince"}}
                ]
            }
        }

    @patch('src.azure_devops_client.requests.post')
    @patch('src.azure_devops_client.requests.get')
    def test_full_workflow_integration(self, mock_get, mock_post, integration_config, mock_ado_responses):
        """Test complete workflow from configuration to data retrieval."""
        # Setup mock responses
        mock_post_response = Mock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = mock_ado_responses["wiql_response"]
        mock_post.return_value = mock_post_response
        
        # Setup sequential GET responses for work items batch and state history
        mock_get_responses = [
            Mock(),  # Work items batch
            Mock(),  # State history for 1001
            Mock(),  # State history for 1002  
            Mock(),  # State history for 1003
            Mock(),  # Teams
            Mock(),  # Team members
        ]
        
        # Configure work items batch response
        mock_get_responses[0].raise_for_status.return_value = None
        mock_get_responses[0].json.return_value = mock_ado_responses["work_items_batch_response"]
        
        # Configure state history responses
        mock_get_responses[1].status_code = 200
        mock_get_responses[1].json.return_value = mock_ado_responses["state_history_1001"]
        mock_get_responses[2].status_code = 200
        mock_get_responses[2].json.return_value = {"value": []}  # Empty history for 1002
        mock_get_responses[3].status_code = 200
        mock_get_responses[3].json.return_value = {"value": []}  # Empty history for 1003
        
        # Configure teams and members responses
        mock_get_responses[4].status_code = 200
        mock_get_responses[4].json.return_value = mock_ado_responses["teams_response"]
        mock_get_responses[5].status_code = 200
        mock_get_responses[5].json.return_value = mock_ado_responses["team_members_response"]
        
        mock_get.side_effect = mock_get_responses
        
        # Load configuration
        settings = FlowMetricsSettings.from_file(Path(integration_config))
        
        # Initialize client
        client = AzureDevOpsClient(
            org_url=f"{settings.azure_devops.base_url}/{settings.azure_devops.organization}",
            project=settings.azure_devops.project,
            pat_token=settings.azure_devops.pat_token
        )
        
        # Test work items retrieval
        work_items = client.get_work_items()
        
        # Verify integration results
        assert len(work_items) == 3
        assert work_items[0]["id"] == "WI-1001"
        assert work_items[0]["title"] == "Implement user authentication"
        assert work_items[0]["type"] == "User Story"
        assert work_items[0]["state"] == "Done"
        assert work_items[0]["assignedTo"] == "Alice Johnson"
        
        # Test team members retrieval
        team_members = client.get_team_members()
        assert len(team_members) == 4
        assert "Alice Johnson" in team_members
        assert "Bob Smith" in team_members
        
        # Verify API calls were made correctly
        assert mock_post.called
        assert mock_get.call_count >= 2  # At least work items batch + some additional calls

    def test_configuration_validation_integration(self, integration_config):
        """Test configuration validation across components."""
        # Test valid configuration
        settings = FlowMetricsSettings.from_file(Path(integration_config))
        assert settings.azure_devops.organization == "test-integration-org"
        assert settings.azure_devops.project == "test-integration-project"
        assert len(settings.stage_definitions.active_states) == 4
        
        # Test configuration with Azure DevOps client
        client = AzureDevOpsClient(
            org_url=f"{settings.azure_devops.base_url}/{settings.azure_devops.organization}",
            project=settings.azure_devops.project,
            pat_token=settings.azure_devops.pat_token
        )
        
        assert client.org_url == "https://dev.azure.com/test-integration-org"
        assert client.project == "test-integration-project"
        assert "Authorization" in client.headers

    @patch('src.azure_devops_client.requests.post')
    def test_error_handling_integration(self, mock_post, integration_config):
        """Test error handling across component integration."""
        settings = FlowMetricsSettings.from_file(Path(integration_config))
        
        client = AzureDevOpsClient(
            org_url=f"{settings.azure_devops.base_url}/{settings.azure_devops.organization}",
            project=settings.azure_devops.project,
            pat_token=settings.azure_devops.pat_token
        )
        
        # Test network error handling
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        work_items = client.get_work_items()
        assert work_items == []
        
        # Test API error handling
        mock_post.side_effect = requests.exceptions.HTTPError("HTTP 500 error")
        work_items = client.get_work_items()
        assert work_items == []

    def test_data_transformation_integration(self, integration_config, mock_ado_responses):
        """Test data transformation through the integration pipeline."""
        with patch('src.azure_devops_client.requests.post') as mock_post, \
             patch('src.azure_devops_client.requests.get') as mock_get:
            
            # Setup mocks
            mock_post_response = Mock()
            mock_post_response.raise_for_status.return_value = None
            mock_post_response.json.return_value = mock_ado_responses["wiql_response"]
            mock_post.return_value = mock_post_response
            
            mock_get_response = Mock()
            mock_get_response.raise_for_status.return_value = None
            mock_get_response.json.return_value = mock_ado_responses["work_items_batch_response"]
            mock_get.return_value = mock_get_response
            
            settings = FlowMetricsSettings.from_file(Path(integration_config))
            client = AzureDevOpsClient(
                org_url=f"{settings.azure_devops.base_url}/{settings.azure_devops.organization}",
                project=settings.azure_devops.project,
                pat_token=settings.azure_devops.pat_token
            )
            
            work_items = client.get_work_items()
            
            # Verify transformation from ADO format to internal format
            assert all(item["id"].startswith("WI-") for item in work_items)
            assert all("title" in item for item in work_items)
            assert all("type" in item for item in work_items)
            assert all("state" in item for item in work_items)
            assert all("assignedTo" in item for item in work_items)
            assert all("createdDate" in item for item in work_items)
            assert all("changedDate" in item for item in work_items)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        yield db_file.name
        Path(db_file.name).unlink(missing_ok=True)

    @pytest.fixture
    def storage_with_data(self, temp_db, sample_work_items):
        """Create data storage with sample data."""
        storage = DataStorage(temp_db)
        storage.store_work_items(sample_work_items)
        return storage

    def test_database_schema_creation(self, temp_db):
        """Test database schema creation and validation."""
        storage = DataStorage(temp_db)
        
        # Verify tables exist
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ["work_items", "state_transitions", "flow_metrics"]
        for table in expected_tables:
            assert table in tables
        
        conn.close()

    def test_work_items_storage_and_retrieval(self, storage_with_data, sample_work_items):
        """Test storing and retrieving work items."""
        # Test retrieval
        retrieved_items = storage_with_data.get_work_items()
        assert len(retrieved_items) == len(sample_work_items)
        
        # Verify data integrity
        original_ids = {item.id for item in sample_work_items}
        retrieved_ids = {item.id for item in retrieved_items}
        assert original_ids == retrieved_ids

    def test_state_transitions_storage(self, storage_with_data, sample_work_items):
        """Test state transitions storage and retrieval."""
        # Get work item with transitions
        work_item_with_transitions = next(
            item for item in sample_work_items 
            if item.state_transitions
        )
        
        retrieved_item = storage_with_data.get_work_item(work_item_with_transitions.id)
        assert retrieved_item is not None
        assert len(retrieved_item.state_transitions) == len(work_item_with_transitions.state_transitions)

    def test_concurrent_database_access(self, temp_db, sample_work_items):
        """Test concurrent database operations."""
        import threading
        import concurrent.futures
        
        def store_items(thread_id):
            storage = DataStorage(temp_db)
            # Modify items to have unique IDs per thread
            thread_items = []
            for item in sample_work_items[:2]:  # Use subset for speed
                new_item = WorkItem(
                    id=item.id + thread_id * 1000,
                    title=f"{item.title} - Thread {thread_id}",
                    work_item_type=item.work_item_type,
                    state=item.state,
                    assigned_to=item.assigned_to,
                    created_date=item.created_date,
                    changed_date=item.changed_date,
                    state_transitions=item.state_transitions
                )
                thread_items.append(new_item)
            
            storage.store_work_items(thread_items)
            return len(thread_items)
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(store_items, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all operations completed
        assert all(result == 2 for result in results)
        
        # Verify total stored items
        storage = DataStorage(temp_db)
        all_items = storage.get_work_items()
        assert len(all_items) >= 6  # 3 threads * 2 items each


@pytest.mark.integration
class TestCalculatorIntegration:
    """Integration tests for flow metrics calculator with data storage."""

    @pytest.fixture
    def calculator_with_storage(self, temp_config_file):
        """Create calculator with temporary storage."""
        settings = FlowMetricsSettings.from_file(Path(temp_config_file))
        
        # Create temporary database
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        storage = DataStorage(db_file.name)
        calculator = FlowMetricsCalculator(settings, storage)
        
        yield calculator
        
        Path(db_file.name).unlink(missing_ok=True)

    def test_calculator_storage_integration(self, calculator_with_storage, sample_work_items):
        """Test calculator integration with data storage."""
        # Store work items
        calculator_with_storage.storage.store_work_items(sample_work_items)
        
        # Calculate metrics
        metrics = calculator_with_storage.calculate_flow_metrics(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )
        
        # Verify metrics calculation
        assert "throughput" in metrics
        assert "cycle_time" in metrics
        assert "work_in_progress" in metrics
        assert isinstance(metrics["throughput"], (int, float))

    def test_metrics_persistence(self, calculator_with_storage, sample_work_items):
        """Test metrics persistence and retrieval."""
        calculator_with_storage.storage.store_work_items(sample_work_items)
        
        # Calculate and store metrics
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        metrics = calculator_with_storage.calculate_flow_metrics(start_date, end_date)
        calculator_with_storage.storage.store_flow_metrics(metrics, start_date, end_date)
        
        # Retrieve stored metrics
        stored_metrics = calculator_with_storage.storage.get_flow_metrics(start_date, end_date)
        
        assert stored_metrics is not None
        assert stored_metrics["throughput"] == metrics["throughput"]