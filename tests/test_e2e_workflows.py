"""
End-to-End (E2E) tests for complete ADO Flow Hive workflows.

These tests verify complete user journeys:
- CLI command execution from start to finish
- Dashboard loading and interaction workflows
- Data fetch → calculation → display pipeline
- Configuration → setup → operation workflows
- Error scenarios and recovery workflows
"""

import pytest
import json
import tempfile
import subprocess
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.cli import main as cli_main
from src.web_server import FlowMetricsWebServer
from src.config_manager import FlowMetricsSettings
from src.data_storage import FlowMetricsDatabase
from src.models import WorkItem, StateTransition


@pytest.mark.e2e
class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows."""

    @pytest.fixture
    def e2e_environment(self):
        """Setup complete test environment for E2E tests."""
        # Create temporary files
        config_data = {
            "azure_devops": {
                "org_url": "https://dev.azure.com/e2e-test-org",
                "default_project": "e2e-test-project",
                "pat_token": "e2e-test-token-123456",
                "api_version": "7.0"
            },
            "flow_metrics": {
                "throughput_period_days": 30,
                "lead_time_percentiles": [50, 75, 85, 95],
                "cycle_time_percentiles": [50, 75, 85, 95],
                "wip_age_threshold_days": 14,
                "blocked_threshold_days": 3,
                "default_days_back": 90
            },
            "stage_definitions": {
                "active_states": ["Active", "In Progress", "Code Review", "Testing"],
                "completion_states": ["Done", "Closed", "Resolved", "Completed"],
                "waiting_states": ["New", "Blocked", "Waiting", "On Hold"]
            },
            "data_management": {
                "data_directory": "e2e_test_data",
                "backup_enabled": True,
                "backup_frequency_hours": 24
            },
            "dashboard": {
                "host": "127.0.0.1",
                "port": 5555,
                "debug": False
            }
        }
        
        # Create config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        # Create database file
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        # Create data directory
        data_dir = Path(tempfile.mkdtemp())
        
        yield {
            "config_file": config_file,
            "db_file": db_file.name,
            "data_dir": data_dir,
            "config_data": config_data
        }
        
        # Cleanup
        Path(config_file).unlink(missing_ok=True)
        Path(db_file.name).unlink(missing_ok=True)
        import shutil
        shutil.rmtree(data_dir, ignore_errors=True)

    @pytest.fixture
    def mock_ado_api_full(self):
        """Comprehensive Azure DevOps API mock for E2E tests."""
        return {
            "project_response": {
                "id": "test-project-id",
                "name": "e2e-test-project",
                "state": "wellFormed"
            },
            "wiql_response": {
                "workItems": [
                    {"id": 5001, "url": "https://dev.azure.com/_apis/wit/workItems/5001"},
                    {"id": 5002, "url": "https://dev.azure.com/_apis/wit/workItems/5002"},
                    {"id": 5003, "url": "https://dev.azure.com/_apis/wit/workItems/5003"},
                    {"id": 5004, "url": "https://dev.azure.com/_apis/wit/workItems/5004"},
                    {"id": 5005, "url": "https://dev.azure.com/_apis/wit/workItems/5005"}
                ]
            },
            "work_items_batch": {
                "value": [
                    {
                        "id": 5001,
                        "fields": {
                            "System.Title": "E2E User Authentication Feature",
                            "System.WorkItemType": "User Story",
                            "System.State": "Done",
                            "System.AssignedTo": {"displayName": "Alice Johnson"},
                            "System.CreatedDate": "2024-01-01T08:00:00Z",
                            "System.ChangedDate": "2024-01-20T16:30:00Z",
                            "System.Tags": "backend;security;e2e"
                        }
                    },
                    {
                        "id": 5002,
                        "fields": {
                            "System.Title": "E2E Dashboard Implementation",
                            "System.WorkItemType": "Feature",
                            "System.State": "In Progress",
                            "System.AssignedTo": {"displayName": "Bob Smith"},
                            "System.CreatedDate": "2024-01-05T09:00:00Z",
                            "System.ChangedDate": "2024-01-25T14:20:00Z",
                            "System.Tags": "frontend;dashboard;e2e"
                        }
                    },
                    {
                        "id": 5003,
                        "fields": {
                            "System.Title": "E2E Performance Optimization",
                            "System.WorkItemType": "Task",
                            "State": "Active",
                            "System.AssignedTo": {"displayName": "Charlie Brown"},
                            "System.CreatedDate": "2024-01-10T10:30:00Z",
                            "System.ChangedDate": "2024-01-22T11:45:00Z",
                            "System.Tags": "performance;optimization;e2e"
                        }
                    },
                    {
                        "id": 5004,
                        "fields": {
                            "System.Title": "E2E API Integration Bug",
                            "System.WorkItemType": "Bug",
                            "System.State": "Blocked",
                            "System.AssignedTo": {"displayName": "Diana Prince"},
                            "System.CreatedDate": "2024-01-12T11:00:00Z",
                            "System.ChangedDate": "2024-01-18T15:30:00Z",
                            "System.Tags": "api;integration;bug;e2e"
                        }
                    },
                    {
                        "id": 5005,
                        "fields": {
                            "System.Title": "E2E Documentation Update",
                            "System.WorkItemType": "Task",
                            "System.State": "New",
                            "System.AssignedTo": {"displayName": "Eve Adams"},
                            "System.CreatedDate": "2024-01-15T13:00:00Z",
                            "System.ChangedDate": "2024-01-15T13:00:00Z",
                            "System.Tags": "documentation;e2e"
                        }
                    }
                ]
            },
            "teams_response": {
                "value": [
                    {"id": "e2e-dev-team", "name": "E2E Development Team"},
                    {"id": "e2e-qa-team", "name": "E2E QA Team"}
                ]
            },
            "team_members_response": {
                "value": [
                    {"identity": {"displayName": "Alice Johnson"}},
                    {"identity": {"displayName": "Bob Smith"}},
                    {"identity": {"displayName": "Charlie Brown"}},
                    {"identity": {"displayName": "Diana Prince"}},
                    {"identity": {"displayName": "Eve Adams"}}
                ]
            }
        }

    @patch('src.azure_devops_client.requests.get')
    @patch('src.azure_devops_client.requests.post')
    def test_complete_cli_fetch_workflow(self, mock_post, mock_get, e2e_environment, mock_ado_api_full):
        """Test complete CLI workflow: configure → fetch → calculate → display."""
        
        # Setup API mocks
        mock_post_response = Mock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = mock_ado_api_full["wiql_response"]
        mock_post.return_value = mock_post_response
        
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = mock_ado_api_full["work_items_batch"]
        mock_get.return_value = mock_get_response
        
        config_file = e2e_environment["config_file"]
        
        # Test CLI fetch command
        with patch('src.config_manager.get_settings'):
            with patch('sys.argv', ['flow_cli.py', 'fetch']):
                try:
                    result = cli_main()
                    # CLI should execute without errors
                    assert result is None or result == 0
                except SystemExit as e:
                    # CLI might exit with 0 on success
                    assert e.code == 0 or e.code is None

    @patch('src.azure_devops_client.requests.get')
    @patch('src.azure_devops_client.requests.post')
    def test_complete_dashboard_workflow(self, mock_post, mock_get, e2e_environment, mock_ado_api_full):
        """Test complete dashboard workflow: start server → load data → display dashboard."""
        
        # Setup API mocks
        mock_post_response = Mock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = mock_ado_api_full["wiql_response"]
        mock_post.return_value = mock_post_response
        
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = mock_ado_api_full["work_items_batch"]
        mock_get.return_value = mock_get_response
        
        # Setup data storage with test data
        from src.config_manager import FlowMetricsSettings
        config_settings = FlowMetricsSettings(_config_file=e2e_environment["config_file"])
        storage = FlowMetricsDatabase(config_settings)
        test_work_items = self._create_test_work_items()
        execution_id = storage.start_execution("test-org", "test-project")
        storage.store_work_items(execution_id, test_work_items)
        
        # Test web server endpoints
        app.config['TESTING'] = True
        with patch('src.web_server.storage', storage):
            with app.test_client() as client:
                # Test dashboard page loads
                response = client.get('/')
                assert response.status_code == 200
                
                # Test API endpoints work
                api_response = client.get('/api/flow-data')
                assert api_response.status_code == 200
                
                data = json.loads(api_response.data)
                assert 'metrics' in data
                assert 'workItems' in data
                assert len(data['workItems']) == len(test_work_items)

    def test_configuration_to_operation_workflow(self, e2e_environment):
        """Test workflow from configuration setup to operation."""
        config_file = e2e_environment["config_file"]
        
        # Load and validate configuration
        settings = FlowMetricsSettings(_config_file=config_file)
        
        # Verify configuration loaded correctly
        assert settings.azure_devops.org_url == "https://dev.azure.com/e2e-test-org"
        assert settings.azure_devops.default_project == "e2e-test-project"
        assert len(settings.stage_definitions["active_states"]) == 4
        
        # Test storage initialization
        storage = FlowMetricsDatabase(settings)
        
        # Verify database schema created
        conn = sqlite3.connect(str(settings.data_management.data_directory / "flow_metrics.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = ["work_items", "state_transitions", "flow_metrics"]
        for table in expected_tables:
            assert table in tables

    @patch('src.azure_devops_client.requests.get')
    @patch('src.azure_devops_client.requests.post')
    def test_data_pipeline_end_to_end(self, mock_post, mock_get, e2e_environment, mock_ado_api_full):
        """Test complete data pipeline: fetch → transform → store → calculate → serve."""
        
        # Setup mocks
        mock_post_response = Mock()
        mock_post_response.raise_for_status.return_value = None
        mock_post_response.json.return_value = mock_ado_api_full["wiql_response"]
        mock_post.return_value = mock_post_response
        
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = mock_ado_api_full["work_items_batch"]
        mock_get.return_value = mock_get_response
        
        config_file = e2e_environment["config_file"]
        db_file = e2e_environment["db_file"]
        
        # 1. Load configuration
        settings = FlowMetricsSettings.from_file(Path(config_file))
        
        # 2. Initialize components
        from src.azure_devops_client import AzureDevOpsClient
        from src.calculator import FlowMetricsCalculator
        
        storage = FlowMetricsDatabase(db_file)
        client = AzureDevOpsClient(
            org_url=f"{settings.azure_devops.base_url}/{settings.azure_devops.organization}",
            project=settings.azure_devops.project,
            pat_token=settings.azure_devops.pat_token
        )
        calculator = FlowMetricsCalculator(settings, storage)
        
        # 3. Fetch data from Azure DevOps
        work_items_data = client.get_work_items()
        assert len(work_items_data) == 5
        
        # 4. Transform and store data
        work_items = []
        for item in work_items_data:
            work_item = WorkItem(
                id=int(item["id"].replace("WI-", "")),
                title=item["title"],
                work_item_type=item["type"],
                state=item["state"],
                assigned_to=item["assignedTo"],
                created_date=datetime.fromisoformat(item["createdDate"].replace("Z", "+00:00")),
                changed_date=datetime.fromisoformat(item["changedDate"].replace("Z", "+00:00")),
                state_transitions=[]
            )
            work_items.append(work_item)
        
        storage.store_work_items(work_items)
        
        # 5. Calculate metrics
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        metrics = calculator.calculate_flow_metrics(start_date, end_date)
        
        # 6. Verify metrics calculated
        assert "throughput" in metrics
        assert "cycle_time" in metrics
        assert "work_in_progress" in metrics
        
        # 7. Test web serving
        app.config['TESTING'] = True
        with patch('src.web_server.storage', storage):
            with app.test_client() as client:
                response = client.get('/api/flow-data')
                assert response.status_code == 200
                
                data = json.loads(response.data)
                assert len(data['workItems']) == 5

    def test_error_recovery_workflow(self, e2e_environment):
        """Test error scenarios and recovery workflows."""
        config_file = e2e_environment["config_file"]
        
        # Test invalid configuration handling
        invalid_config_data = {
            "azure_devops": {
                "organization": "",  # Invalid empty organization
                "project": "",       # Invalid empty project
                "pat_token": "",     # Invalid empty token
                "base_url": "invalid-url"  # Invalid URL
            }
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_config_data, f)
            invalid_config_file = f.name
        
        try:
            # Should handle invalid configuration gracefully
            with pytest.raises((ValueError, AttributeError, Exception)):
                FlowMetricsSettings.from_file(Path(invalid_config_file))
        finally:
            Path(invalid_config_file).unlink(missing_ok=True)

    def test_concurrent_operations_workflow(self, e2e_environment, mock_ado_api_full):
        """Test concurrent operations in E2E workflow."""
        import concurrent.futures
        import threading
        
        config_file = e2e_environment["config_file"]
        db_file = e2e_environment["db_file"]
        
        def concurrent_operation(thread_id):
            """Simulate concurrent user operation."""
            storage = FlowMetricsDatabase(db_file)
            
            # Create thread-specific work items
            work_items = []
            for i in range(3):
                work_item = WorkItem(
                    id=thread_id * 1000 + i,
                    title=f"Thread {thread_id} Item {i}",
                    work_item_type="Task",
                    state="Active",
                    assigned_to=f"User{thread_id}",
                    created_date=datetime.now(timezone.utc),
                    changed_date=datetime.now(timezone.utc),
                    state_transitions=[]
                )
                work_items.append(work_item)
            
            storage.store_work_items(work_items)
            return len(work_items)
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all operations completed successfully
        assert all(result == 3 for result in results)
        
        # Verify data consistency
        storage = FlowMetricsDatabase(db_file)
        all_items = storage.get_work_items()
        assert len(all_items) >= 9  # 3 threads * 3 items each

    def test_performance_under_load_workflow(self, e2e_environment):
        """Test system performance under load in E2E scenario."""
        config_file = e2e_environment["config_file"]
        db_file = e2e_environment["db_file"]
        
        storage = FlowMetricsDatabase(db_file)
        
        # Create large dataset
        large_dataset = []
        for i in range(500):  # 500 work items
            work_item = WorkItem(
                id=i + 10000,
                title=f"Performance Test Item {i}",
                work_item_type="Task",
                state="Active" if i % 3 == 0 else "Done",
                assigned_to=f"User{i % 10}",
                created_date=datetime.now(timezone.utc) - timedelta(days=i % 90),
                changed_date=datetime.now(timezone.utc) - timedelta(days=i % 30),
                state_transitions=[]
            )
            large_dataset.append(work_item)
        
        # Measure storage performance
        start_time = time.time()
        storage.store_work_items(large_dataset)
        storage_time = time.time() - start_time
        
        # Measure retrieval performance
        start_time = time.time()
        retrieved_items = storage.get_work_items()
        retrieval_time = time.time() - start_time
        
        # Measure web serving performance
        app.config['TESTING'] = True
        with patch('src.web_server.storage', storage):
            with app.test_client() as client:
                start_time = time.time()
                response = client.get('/api/flow-data')
                web_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert storage_time < 10.0    # Storage should complete within 10 seconds
        assert retrieval_time < 5.0   # Retrieval should complete within 5 seconds
        assert web_time < 5.0         # Web response should complete within 5 seconds
        assert response.status_code == 200
        assert len(retrieved_items) >= 500

    def _create_test_work_items(self):
        """Create test work items for E2E testing."""
        now = datetime.now(timezone.utc)
        work_items = []
        
        for i in range(10):
            work_item = WorkItem(
                id=i + 6000,
                title=f"E2E Test Work Item {i}",
                work_item_type="User Story" if i % 3 == 0 else "Task",
                state="Done" if i % 4 == 0 else "Active",
                assigned_to=f"TestUser{i % 3}",
                created_date=now - timedelta(days=i * 2),
                changed_date=now - timedelta(days=i),
                state_transitions=[]
            )
            work_items.append(work_item)
        
        return work_items


@pytest.mark.e2e
@pytest.mark.slow
class TestComplexScenarios:
    """E2E tests for complex real-world scenarios."""

    def test_multi_day_operation_scenario(self, e2e_environment):
        """Test scenario simulating multi-day operation with data accumulation."""
        config_file = e2e_environment["config_file"]
        db_file = e2e_environment["db_file"]
        
        storage = FlowMetricsDatabase(db_file)
        now = datetime.now(timezone.utc)
        
        # Simulate 7 days of work item updates
        for day in range(7):
            day_items = []
            for i in range(5):  # 5 items per day
                work_item = WorkItem(
                    id=day * 100 + i,
                    title=f"Day {day} Item {i}",
                    work_item_type="Task",
                    state="Active",
                    assigned_to=f"User{i}",
                    created_date=now - timedelta(days=7-day),
                    changed_date=now - timedelta(days=7-day),
                    state_transitions=[]
                )
                day_items.append(work_item)
            
            storage.store_work_items(day_items)
            
            # Simulate some items being completed
            if day > 2:  # After day 2, start completing items
                completed_items = storage.get_work_items()[-3:]  # Get last 3 items
                for item in completed_items:
                    item.state = "Done"
                    item.changed_date = now - timedelta(days=7-day-1)
                storage.store_work_items(completed_items)
        
        # Verify accumulated data
        all_items = storage.get_work_items()
        assert len(all_items) >= 35  # 7 days * 5 items
        
        # Verify some items are completed
        completed_items = [item for item in all_items if item.state == "Done"]
        assert len(completed_items) > 0

    def test_data_migration_scenario(self, e2e_environment):
        """Test data migration and upgrade scenarios."""
        config_file = e2e_environment["config_file"]
        db_file = e2e_environment["db_file"]
        
        # Create initial data storage
        storage_v1 = FlowMetricsDatabase(db_file)
        initial_items = self._create_test_work_items()
        storage_v1.store_work_items(initial_items)
        
        # Simulate database upgrade by creating new storage instance
        storage_v2 = FlowMetricsDatabase(db_file)
        migrated_items = storage_v2.get_work_items()
        
        # Verify data survived migration
        assert len(migrated_items) == len(initial_items)
        original_ids = {item.id for item in initial_items}
        migrated_ids = {item.id for item in migrated_items}
        assert original_ids == migrated_ids

    def _create_test_work_items(self):
        """Create test work items for complex scenarios."""
        now = datetime.now(timezone.utc)
        work_items = []
        
        states = ["New", "Active", "In Progress", "Code Review", "Done", "Blocked"]
        types = ["User Story", "Bug", "Task", "Feature"]
        users = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        
        for i in range(15):
            work_item = WorkItem(
                id=i + 7000,
                title=f"Complex Scenario Item {i}",
                work_item_type=types[i % len(types)],
                state=states[i % len(states)],
                assigned_to=users[i % len(users)],
                created_date=now - timedelta(days=i * 3),
                changed_date=now - timedelta(days=i),
                state_transitions=[]
            )
            work_items.append(work_item)
        
        return work_items