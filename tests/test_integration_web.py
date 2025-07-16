"""
Integration tests for web server and API endpoints.

These tests verify the integration between:
- Flask web server with routing and error handling
- Data storage and retrieval through web endpoints
- Dashboard functionality and data rendering
- Static file serving and web assets
"""

import pytest
import json
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from src.web_server import FlowMetricsWebServer
from src.data_storage import FlowMetricsDatabase
from src.config_manager import FlowMetricsSettings
from src.models import WorkItem, StateTransition


@pytest.mark.integration
class TestWebServerIntegration:
    """Integration tests for web server functionality."""

    @pytest.fixture
    def client(self):
        """Create test client for Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def temp_config_and_db(self):
        """Create temporary config and database files."""
        config_data = {
            "azure_devops": {
                "organization": "test-org",
                "project": "test-project",
                "pat_token": "test-token",
                "base_url": "https://dev.azure.com"
            },
            "stage_definitions": {
                "active_states": ["Active", "In Progress"],
                "completion_states": ["Done", "Closed"],
                "waiting_states": ["New", "Blocked"]
            },
            "data_dir": "test_data",
            "log_dir": "test_logs"
        }
        
        # Create config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        # Create database file
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        yield config_file, db_file.name
        
        # Cleanup
        Path(config_file).unlink(missing_ok=True)
        Path(db_file.name).unlink(missing_ok=True)

    @pytest.fixture
    def web_storage_with_data(self, temp_config_and_db, sample_work_items):
        """Create data storage with sample data for web tests."""
        config_file, db_file = temp_config_and_db
        storage = DataStorage(db_file)
        storage.store_work_items(sample_work_items)
        
        # Patch the storage in web_server module
        with patch('src.web_server.storage', storage):
            yield storage

    def test_dashboard_endpoint_integration(self, client):
        """Test dashboard page serves correctly."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'ADO Flow Hive Dashboard' in response.data or b'dashboard' in response.data.lower()

    def test_api_flow_data_endpoint(self, client, web_storage_with_data):
        """Test flow data API endpoint integration."""
        response = client.get('/api/flow-data')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'metrics' in data
        assert 'workItems' in data
        assert 'teams' in data
        assert isinstance(data['workItems'], list)

    def test_api_work_items_endpoint(self, client, web_storage_with_data, sample_work_items):
        """Test work items API endpoint integration."""
        response = client.get('/api/work-items')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == len(sample_work_items)
        
        # Verify work item structure
        if data:
            work_item = data[0]
            expected_fields = ['id', 'title', 'work_item_type', 'state', 'assigned_to']
            for field in expected_fields:
                assert field in work_item

    def test_api_metrics_endpoint(self, client, web_storage_with_data):
        """Test metrics API endpoint integration."""
        response = client.get('/api/metrics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'throughput' in data
        assert 'cycle_time' in data
        assert 'work_in_progress' in data

    def test_static_files_serving(self, client):
        """Test static files are served correctly."""
        # Test common static file requests
        static_files = [
            '/favicon.ico',
            '/manifest.json'
        ]
        
        for file_path in static_files:
            response = client.get(file_path)
            # Should either return file (200) or not found (404), not server error
            assert response.status_code in [200, 404]

    def test_error_handling_integration(self, client):
        """Test web server error handling."""
        # Test 404 for non-existent endpoint
        response = client.get('/api/non-existent-endpoint')
        assert response.status_code == 404

    def test_concurrent_api_requests(self, client, web_storage_with_data):
        """Test handling concurrent API requests."""
        import concurrent.futures
        
        def make_request():
            response = client.get('/api/work-items')
            return response.status_code
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(status == 200 for status in results)

    @patch('src.web_server.storage')
    def test_database_error_handling(self, mock_storage, client):
        """Test web server handling of database errors."""
        # Mock database error
        mock_storage.get_work_items.side_effect = Exception("Database connection failed")
        
        response = client.get('/api/work-items')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_cors_headers(self, client):
        """Test CORS headers are present for API endpoints."""
        response = client.get('/api/flow-data')
        assert 'Access-Control-Allow-Origin' in response.headers

    def test_content_type_headers(self, client, web_storage_with_data):
        """Test correct content type headers."""
        # Test JSON API endpoints
        response = client.get('/api/work-items')
        assert response.content_type == 'application/json'
        
        # Test HTML dashboard
        response = client.get('/')
        assert 'text/html' in response.content_type


@pytest.mark.integration
class TestDashboardDataIntegration:
    """Integration tests for dashboard data processing."""

    @pytest.fixture
    def dashboard_data_setup(self, temp_config_and_db, sample_work_items):
        """Setup dashboard with real data."""
        config_file, db_file = temp_config_and_db
        settings = FlowMetricsSettings(_config_file=config_file)
        storage = DataStorage(db_file)
        storage.store_work_items(sample_work_items)
        
        return settings, storage

    def test_flow_data_generation_integration(self, dashboard_data_setup, sample_work_items):
        """Test complete flow data generation for dashboard."""
        settings, storage = dashboard_data_setup
        
        # Test get_flow_data function
        with patch('src.web_server.storage', storage):
            flow_data = get_flow_data()
        
        # Verify data structure
        assert 'metrics' in flow_data
        assert 'workItems' in flow_data
        assert 'teams' in flow_data
        assert 'lastUpdated' in flow_data
        
        # Verify metrics calculation
        metrics = flow_data['metrics']
        assert 'throughput' in metrics
        assert 'cycle_time' in metrics
        assert 'work_in_progress' in metrics
        
        # Verify work items data
        work_items = flow_data['workItems']
        assert len(work_items) == len(sample_work_items)

    def test_dashboard_performance_with_large_dataset(self, dashboard_data_setup):
        """Test dashboard performance with larger dataset."""
        settings, storage = dashboard_data_setup
        
        # Create larger dataset
        now = datetime.now(timezone.utc)
        large_dataset = []
        
        for i in range(100):  # Create 100 work items
            work_item = WorkItem(
                id=i + 2000,
                title=f"Performance Test Item {i}",
                work_item_type="Task",
                state="Active" if i % 2 == 0 else "Done",
                assigned_to=f"User{i % 5}",
                created_date=now - timedelta(days=i % 30),
                changed_date=now - timedelta(days=i % 10),
                state_transitions=[]
            )
            large_dataset.append(work_item)
        
        storage.store_work_items(large_dataset)
        
        # Measure performance
        start_time = time.time()
        with patch('src.web_server.storage', storage):
            flow_data = get_flow_data()
        end_time = time.time()
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert end_time - start_time < 5.0  # 5 seconds max
        assert len(flow_data['workItems']) >= 100

    def test_data_consistency_across_endpoints(self, dashboard_data_setup):
        """Test data consistency across different API endpoints."""
        settings, storage = dashboard_data_setup
        
        with patch('src.web_server.storage', storage):
            # Get data from different endpoints
            flow_data = get_flow_data()
            
            app.config['TESTING'] = True
            with app.test_client() as client:
                work_items_response = client.get('/api/work-items')
                metrics_response = client.get('/api/metrics')
        
        # Parse responses
        work_items_data = json.loads(work_items_response.data)
        metrics_data = json.loads(metrics_response.data)
        
        # Verify consistency
        assert len(flow_data['workItems']) == len(work_items_data)
        assert flow_data['metrics']['throughput'] == metrics_data['throughput']

    def test_real_time_data_updates(self, dashboard_data_setup, sample_work_items):
        """Test dashboard reflects data updates."""
        settings, storage = dashboard_data_setup
        
        with patch('src.web_server.storage', storage):
            # Get initial data
            initial_data = get_flow_data()
            initial_count = len(initial_data['workItems'])
            
            # Add new work item
            new_work_item = WorkItem(
                id=9999,
                title="Real-time test item",
                work_item_type="Task",
                state="New",
                assigned_to="Test User",
                created_date=datetime.now(timezone.utc),
                changed_date=datetime.now(timezone.utc),
                state_transitions=[]
            )
            
            storage.store_work_items([new_work_item])
            
            # Get updated data
            updated_data = get_flow_data()
            updated_count = len(updated_data['workItems'])
        
        # Verify update reflected
        assert updated_count == initial_count + 1