"""
Unit tests for web server endpoint functionality.
Tests the new /api/work-items endpoint and supporting methods.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from flask import Flask

from src.web_server import FlowMetricsWebServer


class TestWorkItemsEndpoint:
    """Test suite for the /api/work-items endpoint."""

    @pytest.fixture
    def web_server(self):
        """Create web server instance for testing."""
        return FlowMetricsWebServer(data_source="mock")

    @pytest.fixture
    def client(self, web_server):
        """Create test client."""
        web_server.app.config['TESTING'] = True
        return web_server.app.test_client()

    @pytest.fixture
    def mock_work_items(self):
        """Mock work items data."""
        return [
            {
                "id": 1001,
                "title": "Test User Story",
                "type": "User Story",
                "priority": 2,
                "assigned_to": "alice@test.com",
                "current_state": "Active",
                "created_date": "2024-01-01T00:00:00Z",
                "tags": ["feature", "ui"],
                "story_points": 5,
                "effort_hours": 16,
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Active", "date": "2024-01-02T00:00:00Z"}
                ]
            },
            {
                "id": 1002,
                "title": "Critical Bug Fix",
                "type": "Bug",
                "priority": 1,
                "assigned_to": "bob@test.com",
                "current_state": "Done",
                "created_date": "2024-01-05T00:00:00Z",
                "tags": ["bugfix", "urgent"],
                "story_points": None,
                "effort_hours": 8,
                "state_transitions": [
                    {"state": "New", "date": "2024-01-05T00:00:00Z"},
                    {"state": "Active", "date": "2024-01-05T08:00:00Z"},
                    {"state": "Done", "date": "2024-01-06T16:00:00Z"}
                ]
            },
            {
                "id": 1003,
                "title": "Feature Enhancement",
                "type": "Feature",
                "priority": None,
                "assigned_to": None,
                "current_state": "New",
                "created_date": "2024-01-10T00:00:00Z",
                "tags": [],
                "story_points": 3,
                "effort_hours": None,
                "state_transitions": [
                    {"state": "New", "date": "2024-01-10T00:00:00Z"}
                ]
            }
        ]

    def test_work_items_endpoint_success(self, client, web_server, mock_work_items):
        """Test successful work items endpoint response."""
        with patch.object(web_server, '_load_work_items', return_value=mock_work_items):
            response = client.get('/api/work-items')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert len(data) == 3
            assert isinstance(data, list)

    def test_work_items_endpoint_data_transformation(self, client, web_server, mock_work_items):
        """Test data transformation in work items endpoint."""
        with patch.object(web_server, '_load_work_items', return_value=mock_work_items):
            response = client.get('/api/work-items')
            data = json.loads(response.data)
            
            # Test first item transformation
            item1 = data[0]
            assert item1['id'] == 1001
            assert item1['title'] == "Test User Story"
            assert item1['workItemType'] == "User Story"
            assert item1['priority'] == "High"  # priority 2 -> "High"
            assert item1['assignedTo'] == "alice@test.com"
            assert item1['state'] == "Active"
            assert item1['tags'] == ["feature", "ui"]
            assert item1['storyPoints'] == 5
            assert item1['effortHours'] == 16

    def test_work_items_endpoint_handles_null_values(self, client, web_server, mock_work_items):
        """Test endpoint handles null values correctly."""
        with patch.object(web_server, '_load_work_items', return_value=mock_work_items):
            response = client.get('/api/work-items')
            data = json.loads(response.data)
            
            # Test item with null values
            item3 = data[2]
            assert item3['priority'] == "Low"  # None -> "Low"
            assert item3['assignedTo'] is None
            assert item3['tags'] == []
            assert item3['effortHours'] is None

    def test_work_items_endpoint_error_handling(self, client, web_server):
        """Test error handling in work items endpoint."""
        with patch.object(web_server, '_load_work_items', side_effect=Exception("Test error")):
            response = client.get('/api/work-items')
            
            # The actual implementation returns 503 for data source errors
            assert response.status_code == 503
            data = json.loads(response.data)
            assert 'error' in data

    def test_work_items_endpoint_empty_list(self, client, web_server):
        """Test endpoint with empty work items list."""
        with patch.object(web_server, '_load_work_items', return_value=[]):
            response = client.get('/api/work-items')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data == []


class TestDataTransformationMethods:
    """Test suite for data transformation helper methods."""

    @pytest.fixture
    def web_server(self):
        """Create web server instance for testing."""
        return FlowMetricsWebServer(data_source="mock")

    def test_map_priority_numeric_values(self, web_server):
        """Test priority mapping for numeric values."""
        assert web_server._map_priority(1) == "Critical"
        assert web_server._map_priority(2) == "High"
        assert web_server._map_priority(3) == "Medium"
        assert web_server._map_priority(4) == "Low"

    def test_map_priority_float_values(self, web_server):
        """Test priority mapping for float values."""
        assert web_server._map_priority(1.0) == "Critical"
        assert web_server._map_priority(2.5) == "High"
        assert web_server._map_priority(3.7) == "Medium"

    def test_map_priority_edge_cases(self, web_server):
        """Test priority mapping edge cases."""
        assert web_server._map_priority(None) == "Low"
        assert web_server._map_priority(0) == "Low"
        assert web_server._map_priority(5) == "Low"
        assert web_server._map_priority(-1) == "Low"

    def test_map_priority_string_values(self, web_server):
        """Test priority mapping for string values."""
        assert web_server._map_priority("1") == "1"  # String returned as-is
        assert web_server._map_priority("high") == "high"  # Non-numeric string returned as-is
        assert web_server._map_priority("") == ""  # Empty string returned as-is

    def test_get_resolved_date_with_transitions(self, web_server):
        """Test resolved date extraction from state transitions."""
        item = {
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Active", "date": "2024-01-02T00:00:00Z"},
                {"state": "Done", "date": "2024-01-03T00:00:00Z"}
            ]
        }
        
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date == "2024-01-03T00:00:00Z"

    def test_get_resolved_date_multiple_resolved_states(self, web_server):
        """Test resolved date with multiple resolved states."""
        item = {
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Closed", "date": "2024-01-02T00:00:00Z"},
                {"state": "Active", "date": "2024-01-03T00:00:00Z"},  # Reopened
                {"state": "Done", "date": "2024-01-04T00:00:00Z"}
            ]
        }
        
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date == "2024-01-04T00:00:00Z"  # Most recent resolved state

    def test_get_resolved_date_no_resolved_state(self, web_server):
        """Test resolved date when no resolved state exists."""
        item = {
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Active", "date": "2024-01-02T00:00:00Z"}
            ]
        }
        
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date is None

    def test_get_resolved_date_empty_transitions(self, web_server):
        """Test resolved date with empty state transitions."""
        item = {"state_transitions": []}
        
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date is None

    def test_get_resolved_date_no_transitions_key(self, web_server):
        """Test resolved date when state_transitions key doesn't exist."""
        item = {"id": 1001}
        
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date is None

    def test_get_completed_date_delegates_to_resolved(self, web_server):
        """Test that completed date delegates to resolved date."""
        item = {
            "state_transitions": [
                {"state": "Done", "date": "2024-01-03T00:00:00Z"}
            ]
        }
        
        completed_date = web_server._get_completed_date(item)
        resolved_date = web_server._get_resolved_date(item)
        assert completed_date == resolved_date

    def test_get_last_updated_date_from_transitions(self, web_server):
        """Test last updated date from state transitions."""
        item = {
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Active", "date": "2024-01-02T00:00:00Z"},
                {"state": "Done", "date": "2024-01-03T00:00:00Z"}
            ],
            "created_date": "2023-12-31T00:00:00Z"
        }
        
        last_updated = web_server._get_last_updated_date(item)
        assert last_updated == "2024-01-03T00:00:00Z"

    def test_get_last_updated_date_fallback_to_created(self, web_server):
        """Test last updated date fallback to created date."""
        item = {
            "state_transitions": [],
            "created_date": "2024-01-01T00:00:00Z"
        }
        
        last_updated = web_server._get_last_updated_date(item)
        assert last_updated == "2024-01-01T00:00:00Z"

    def test_get_last_updated_date_no_transitions_no_created(self, web_server):
        """Test last updated date with no transitions or created date."""
        item = {"state_transitions": []}
        
        last_updated = web_server._get_last_updated_date(item)
        assert last_updated is None


class TestErrorHandling:
    """Test suite for error handling in web server methods."""

    @pytest.fixture
    def web_server(self):
        """Create web server instance for testing."""
        return FlowMetricsWebServer(data_source="mock")

    @pytest.fixture
    def client(self, web_server):
        """Create test client."""
        web_server.app.config['TESTING'] = True
        return web_server.app.test_client()

    def test_load_work_items_mock_source_error(self, web_server):
        """Test error handling in load work items with mock source."""
        with patch('src.web_server.generate_mock_azure_devops_data', side_effect=Exception("Mock error")):
            with pytest.raises(Exception, match="Mock error"):
                web_server._load_work_items()

    def test_load_work_items_api_source_error(self, web_server):
        """Test error handling in load work items with API source."""
        web_server.data_source = "api"
        
        with patch('src.web_server.get_settings', side_effect=Exception("Settings error")):
            # The error handler catches exceptions and returns empty list
            result = web_server._load_work_items()
            assert isinstance(result, list)  # Should return empty list or fallback data

    def test_priority_mapping_with_invalid_data(self, web_server):
        """Test priority mapping with various invalid data types."""
        # Test with complex objects that are converted to strings
        assert web_server._map_priority([1, 2, 3]) == "[1, 2, 3]"
        assert web_server._map_priority({"priority": 1}) == "{'priority': 1}"
        # Lambda functions are converted to string representation
        lambda_result = web_server._map_priority(lambda x: x)
        assert "function" in lambda_result or "lambda" in lambda_result

    def test_date_extraction_with_malformed_transitions(self, web_server):
        """Test date extraction with malformed state transitions."""
        item = {
            "state_transitions": [
                {"state": "New"},  # Missing date
                {"date": "2024-01-02T00:00:00Z"},  # Missing state
                None,  # Null transition
                {"state": "Done", "date": "2024-01-03T00:00:00Z"}
            ]
        }
        
        # Should handle malformed data gracefully
        resolved_date = web_server._get_resolved_date(item)
        assert resolved_date == "2024-01-03T00:00:00Z"

    def test_work_items_transformation_with_missing_fields(self, client, web_server):
        """Test work items transformation with missing required fields."""
        malformed_items = [
            {},  # Completely empty item
            {"id": 1001},  # Only ID
            {"title": "Test"},  # Missing ID
        ]
        
        with patch.object(web_server, '_load_work_items', return_value=malformed_items):
            response = client.get('/api/work-items')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 3
            
            # Verify graceful handling of missing fields
            for item in data:
                assert 'id' in item
                assert 'title' in item
                assert 'priority' in item