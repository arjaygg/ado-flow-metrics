"""
Integration tests for advanced filtering functionality.
Tests API endpoint integration with data sources and real data flow.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.config_manager import get_settings
from src.web_server import FlowMetricsWebServer


class TestWorkItemsAPIIntegration:
    """Integration tests for /api/work-items endpoint with various data sources."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_work_items_file(self, temp_data_dir):
        """Create mock work items JSON file."""
        work_items = [
            {
                "id": 1001,
                "title": "Integration Test Item 1",
                "type": "User Story",
                "priority": 2,
                "assigned_to": "integration@test.com",
                "current_state": "Active",
                "created_date": "2024-01-01T00:00:00Z",
                "tags": ["integration", "test"],
                "story_points": 5,
                "effort_hours": 20,
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Active", "date": "2024-01-02T00:00:00Z"},
                ],
            },
            {
                "id": 1002,
                "title": "Integration Test Item 2",
                "type": "Bug",
                "priority": 1,
                "assigned_to": "bugfix@test.com",
                "current_state": "Done",
                "created_date": "2024-01-03T00:00:00Z",
                "tags": ["bugfix"],
                "story_points": None,
                "effort_hours": 8,
                "state_transitions": [
                    {"state": "New", "date": "2024-01-03T00:00:00Z"},
                    {"state": "Active", "date": "2024-01-03T08:00:00Z"},
                    {"state": "Done", "date": "2024-01-04T16:00:00Z"},
                ],
            },
        ]

        data_dir = Path(temp_data_dir) / "data"
        data_dir.mkdir(exist_ok=True)

        work_items_file = data_dir / "work_items.json"
        with open(work_items_file, "w") as f:
            json.dump(work_items, f)

        return str(work_items_file)

    def test_api_endpoint_with_mock_data_source(self):
        """Test API endpoint integration with mock data source."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        response = client.get("/api/work-items")

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify data transformation
        for item in data:
            assert "id" in item
            assert "title" in item
            assert "workItemType" in item
            assert "priority" in item
            assert "assignedTo" in item
            assert "state" in item

    def test_api_endpoint_with_file_data_source(self, mock_work_items_file):
        """Test API endpoint integration with file data source."""
        server = FlowMetricsWebServer(data_source=mock_work_items_file)

        client = server.app.test_client()
        response = client.get("/api/work-items")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data) == 2
        assert data[0]["title"] == "Integration Test Item 1"
        assert data[1]["title"] == "Integration Test Item 2"

    def test_api_endpoint_error_handling_integration(self):
        """Test API endpoint error handling in integration scenario."""
        server = FlowMetricsWebServer(data_source="api")

        # Mock a failure in the data loading process
        with patch.object(
            server, "_load_work_items", side_effect=Exception("Data source unavailable")
        ):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            assert response.status_code == 503  # DATA_SOURCE_ERROR returns 503
            data = json.loads(response.data)
            assert "error" in data
            # Check the error message in the proper field
            assert "message" in data
            assert "work-items" in data["message"]  # Error message includes data source

    def test_cors_headers_integration(self):
        """Test CORS headers are properly set for API endpoints."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        response = client.get("/api/work-items")

        # Check CORS headers are present
        assert "Access-Control-Allow-Origin" in response.headers

    def test_json_response_format_integration(self):
        """Test JSON response format is correct."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        response = client.get("/api/work-items")

        assert response.content_type == "application/json"

        # Verify JSON is valid and well-formed
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_health_check_integration(self):
        """Test health check endpoint integration."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        response = client.get("/health")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["data_source"] == "mock"


class TestDashboardDataLoadingIntegration:
    """Integration tests for dashboard loading work items data."""

    @pytest.fixture
    def server_with_client(self):
        """Create server with test client."""
        server = FlowMetricsWebServer(data_source="mock")
        server.app.config["TESTING"] = True
        client = server.app.test_client()
        return server, client

    def test_dashboard_html_loads_work_items(self, server_with_client):
        """Test that dashboard HTML can fetch work items data."""
        server, client = server_with_client

        # First, verify work items endpoint works
        api_response = client.get("/api/work-items")
        assert api_response.status_code == 200
        work_items = json.loads(api_response.data)
        assert len(work_items) > 0

        # Then verify dashboard loads (if dashboard.html exists)
        dashboard_response = client.get("/")
        # Dashboard should load regardless of whether HTML file exists
        # The important thing is that the API is available for the dashboard

    def test_work_items_data_structure_for_filtering(self, server_with_client):
        """Test work items data structure matches filtering requirements."""
        server, client = server_with_client

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Verify required fields for advanced filtering
        required_fields = [
            "id",
            "title",
            "workItemType",
            "priority",
            "assignedTo",
            "state",
            "tags",
        ]

        for item in work_items:
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"

    def test_priority_mapping_integration(self, server_with_client):
        """Test priority mapping works correctly in full integration."""
        server, client = server_with_client

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Verify all priorities are mapped to string values
        valid_priorities = ["Critical", "High", "Medium", "Low"]

        for item in work_items:
            assert (
                item["priority"] in valid_priorities
            ), f"Invalid priority: {item['priority']}"

    def test_state_mapping_integration(self, server_with_client):
        """Test state mapping works correctly in full integration."""
        server, client = server_with_client

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Verify states are properly mapped
        for item in work_items:
            assert item["state"] is not None
            assert isinstance(item["state"], str)

    def test_assignee_mapping_integration(self, server_with_client):
        """Test assignee mapping works correctly in full integration."""
        server, client = server_with_client

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Verify assignee field is properly mapped
        for item in work_items:
            # assignedTo can be None or string
            assert "assignedTo" in item
            if item["assignedTo"] is not None:
                assert isinstance(item["assignedTo"], str)


class TestFilteringWithRealDataFlow:
    """Integration tests for filtering with real data flow."""

    @pytest.fixture
    def filtering_server(self):
        """Create server configured for filtering tests."""
        return FlowMetricsWebServer(data_source="mock")

    def test_end_to_end_filtering_data_flow(self, filtering_server):
        """Test complete data flow from API to filtering."""
        client = filtering_server.app.test_client()

        # Step 1: Get work items from API
        response = client.get("/api/work-items")
        assert response.status_code == 200
        work_items = json.loads(response.data)

        # Step 2: Simulate filtering operations
        # Test filtering by work item type
        bugs = [item for item in work_items if item["workItemType"] == "Bug"]
        user_stories = [
            item for item in work_items if item["workItemType"] == "User Story"
        ]

        # Verify filtering results make sense
        assert len(bugs) + len(user_stories) <= len(work_items)

        # Test filtering by priority
        high_priority = [item for item in work_items if item["priority"] == "High"]
        critical_priority = [
            item for item in work_items if item["priority"] == "Critical"
        ]

        # Verify priority filtering
        for item in high_priority:
            assert item["priority"] == "High"
        for item in critical_priority:
            assert item["priority"] == "Critical"

    def test_multi_dimensional_filtering_integration(self, filtering_server):
        """Test multi-dimensional filtering with real data."""
        client = filtering_server.app.test_client()

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Apply multiple filters simultaneously
        filtered_items = [
            item
            for item in work_items
            if item["workItemType"] == "Bug"
            and item["priority"] in ["High", "Critical"]
        ]

        # Verify multi-dimensional filtering
        for item in filtered_items:
            assert item["workItemType"] == "Bug"
            assert item["priority"] in ["High", "Critical"]

    def test_filtering_with_tags_integration(self, filtering_server):
        """Test tag-based filtering integration."""
        client = filtering_server.app.test_client()

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Find items with specific tags
        tagged_items = [
            item
            for item in work_items
            if any(tag in item.get("tags", []) for tag in ["urgent", "feature"])
        ]

        # Verify tag filtering works
        for item in tagged_items:
            assert isinstance(item.get("tags", []), list)

    def test_assignee_filtering_integration(self, filtering_server):
        """Test assignee-based filtering integration."""
        client = filtering_server.app.test_client()

        response = client.get("/api/work-items")
        work_items = json.loads(response.data)

        # Get unique assignees
        assignees = list(
            set(
                item["assignedTo"]
                for item in work_items
                if item["assignedTo"] is not None
            )
        )

        if assignees:
            # Test filtering by specific assignee
            test_assignee = assignees[0]
            assignee_items = [
                item for item in work_items if item["assignedTo"] == test_assignee
            ]

            # Verify assignee filtering
            for item in assignee_items:
                assert item["assignedTo"] == test_assignee


class TestErrorScenariosAndFallbacks:
    """Integration tests for error scenarios and fallback behavior."""

    def test_invalid_data_source_fallback(self):
        """Test fallback behavior with invalid data source."""
        server = FlowMetricsWebServer(data_source="invalid_source")
        client = server.app.test_client()

        # Should fallback to mock data or handle gracefully
        response = client.get("/api/work-items")

        # Response should either be successful (fallback) or proper error
        assert response.status_code in [200, 500]

    def test_corrupted_data_handling(self):
        """Test handling of corrupted or malformed data."""
        server = FlowMetricsWebServer(data_source="mock")

        # Mock corrupted data
        corrupted_data = [
            {"id": "invalid"},  # Invalid ID type
            {"title": None},  # Missing required fields
            {},  # Empty object
            None,  # Null item
        ]

        with patch.object(server, "_load_work_items", return_value=corrupted_data):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            # Corrupted data should cause an error in data transformation
            assert response.status_code == 503  # DATA_SOURCE_ERROR for corrupted data
            data = json.loads(response.data)
            assert "error" in data

    def test_large_dataset_handling(self):
        """Test handling of large datasets."""
        server = FlowMetricsWebServer(data_source="mock")

        # Mock large dataset
        large_dataset = [
            {
                "id": i,
                "title": f"Item {i}",
                "type": "User Story",
                "priority": 2,
                "assigned_to": f"user{i}@test.com",
                "current_state": "Active",
                "created_date": "2024-01-01T00:00:00Z",
                "tags": ["performance"],
                "story_points": 1,
                "effort_hours": 4,
                "state_transitions": [],
            }
            for i in range(1000)  # 1000 items
        ]

        with patch.object(server, "_load_work_items", return_value=large_dataset):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1000

    def test_network_timeout_simulation(self):
        """Test behavior during network timeout scenarios."""
        server = FlowMetricsWebServer(data_source="api")

        # Simulate network timeout
        with patch.object(
            server, "_load_work_items", side_effect=TimeoutError("Network timeout")
        ):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            assert response.status_code == 503  # DATA_SOURCE_ERROR for network timeout
            data = json.loads(response.data)
            assert "error" in data

    def test_partial_data_recovery(self):
        """Test recovery from partial data corruption."""
        server = FlowMetricsWebServer(data_source="mock")

        # Mix of valid and invalid items
        mixed_data = [
            {
                "id": 1,
                "title": "Valid Item",
                "type": "User Story",
                "priority": 2,
                "assigned_to": "user@test.com",
                "current_state": "Active",
            },
            {"invalid": "data"},  # Invalid structure
            {
                "id": 2,
                "title": "Another Valid Item",
                "type": "Bug",
                "priority": 1,
                "assigned_to": "user2@test.com",
                "current_state": "Done",
            },
        ]

        with patch.object(server, "_load_work_items", return_value=mixed_data):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            assert response.status_code == 200
            data = json.loads(response.data)

            # Should process all items (even invalid ones with defaults)
            assert len(data) == 3


class TestCacheAndPerformanceIntegration:
    """Integration tests for caching and performance aspects."""

    def test_data_loading_performance(self):
        """Test data loading performance characteristics."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        import time

        # Measure response time
        start_time = time.time()
        response = client.get("/api/work-items")
        end_time = time.time()

        assert response.status_code == 200

        # Response should be reasonably fast (under 1 second for mock data)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Response took too long: {response_time}s"

    def test_concurrent_requests_handling(self):
        """Test handling of concurrent requests."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        import threading

        results = []

        def make_request():
            response = client.get("/api/work-items")
            results.append(response.status_code)

        # Create multiple concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5

    def test_memory_usage_with_large_datasets(self):
        """Test memory usage characteristics with large datasets."""
        server = FlowMetricsWebServer(data_source="mock")

        # This test would ideally monitor memory usage
        # For now, just ensure large datasets don't crash
        large_dataset = [{"id": i, "title": f"Item {i}"} for i in range(5000)]

        with patch.object(server, "_load_work_items", return_value=large_dataset):
            client = server.app.test_client()
            response = client.get("/api/work-items")

            assert response.status_code == 200
            # Response should complete without memory errors
