"""Integration tests for WIQL components."""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.exceptions import WIQLError, WIQLValidationError
from src.wiql_client import WIQLClient
from src.wiql_parser import WIQLParser
from src.wiql_transformer import TransformationConfig, WIQLTransformer


class TestWIQLIntegration:
    """Integration tests for WIQL components working together."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = WIQLClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )
        self.parser = WIQLParser()
        self.transformer = WIQLTransformer()

    def test_end_to_end_wiql_flow(self):
        """Test complete WIQL flow from query to transformed data."""
        # Build query using parser
        query = self.parser.build_query_for_work_items(
            project="test-project",
            days_back=30,
            work_item_types=["User Story", "Bug"],
            states=["Active", "Resolved"],
        )

        # Convert to WIQL string
        wiql_string = query.to_wiql_string()

        # Validate the query
        validation_errors = self.parser.validate_query(query)
        assert len(validation_errors) == 0

        # Parse back the WIQL string
        parsed_query = self.parser.parse_query(wiql_string)

        # Verify round-trip consistency
        assert parsed_query.project_filter == query.project_filter
        assert len(parsed_query.where_conditions) == len(query.where_conditions)
        assert parsed_query.select_fields == query.select_fields

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_wiql_client_with_transformer(self, mock_get, mock_post):
        """Test WIQL client with data transformer."""
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
                        "System.Title": "Test User Story",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                        "System.AssignedTo": {"displayName": "John Doe"},
                        "Microsoft.VSTS.Common.Priority": 2,
                        "Microsoft.VSTS.Scheduling.StoryPoints": 3.0,
                        "System.Tags": "frontend;critical",
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "System.Title": "Test Bug",
                        "System.WorkItemType": "Bug",
                        "System.State": "Resolved",
                        "System.CreatedDate": "2023-01-02T11:00:00Z",
                        "System.ClosedDate": "2023-01-03T12:00:00Z",
                        "System.AssignedTo": {"displayName": "Jane Smith"},
                        "Microsoft.VSTS.Common.Priority": 1,
                        "System.Tags": "backend;bug",
                    },
                },
            ]
        }

        # Execute query
        raw_work_items = self.client.execute_wiql_query(
            "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'test-project'"
        )

        # Transform data
        work_items = self.transformer.transform_work_items(raw_work_items)

        assert len(work_items) == 2

        # Check first item (User Story)
        user_story = work_items[0]
        assert user_story.id == 1
        assert user_story.title == "Test User Story"
        assert user_story.type == "User Story"
        assert user_story.state == "Active"
        assert user_story.assigned_to == "John Doe"
        assert user_story.priority == 2
        assert user_story.effort == 3.0
        assert user_story.tags == ["frontend", "critical"]
        assert user_story.closed_date is None

        # Check second item (Bug)
        bug = work_items[1]
        assert bug.id == 2
        assert bug.title == "Test Bug"
        assert bug.type == "Bug"
        assert bug.state == "Resolved"
        assert bug.assigned_to == "Jane Smith"
        assert bug.priority == 1
        assert bug.tags == ["backend", "bug"]
        assert bug.closed_date is not None

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_wiql_filtering_with_custom_fields(self, mock_get, mock_post):
        """Test WIQL filtering with custom fields."""
        # Register custom field
        self.client.register_custom_field(
            "Custom.BusinessValue", "integer", display_name="Business Value"
        )

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
                        "System.Title": "High Value Story",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                        "Custom.BusinessValue": 100,
                    },
                }
            ]
        }

        # Use custom field in query
        custom_query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'test-project'
        AND [Custom.BusinessValue] >= 50
        """

        # Validate query includes custom field
        validation_result = self.client.validate_wiql_query(custom_query)
        assert validation_result["valid"] is True

        # Execute query
        work_items = self.client.execute_wiql_query(custom_query)

        assert len(work_items) == 1
        assert work_items[0]["id"] == 1

    def test_wiql_parser_validation_integration(self):
        """Test WIQL parser validation with various scenarios."""
        test_cases = [
            # Valid queries
            {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'test'",
                "should_be_valid": True,
            },
            {
                "query": "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] IN ('Active', 'Resolved')",
                "should_be_valid": True,
            },
            {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.CreatedDate] >= '2023-01-01'",
                "should_be_valid": True,
            },
            # Invalid queries
            {
                "query": "SELECT [Unknown.Field] FROM WorkItems",
                "should_be_valid": False,
            },
            {
                "query": "SELECT [System.Id] FROM WorkItems WHERE [System.Id] LIKE 'test'",
                "should_be_valid": False,  # LIKE not supported for integer fields
            },
        ]

        for test_case in test_cases:
            try:
                parsed_query = self.parser.parse_query(test_case["query"])
                validation_errors = self.parser.validate_query(parsed_query)
                is_valid = len(validation_errors) == 0

                if test_case["should_be_valid"]:
                    assert (
                        is_valid
                    ), f"Query should be valid: {test_case['query']}, Errors: {validation_errors}"
                else:
                    assert (
                        not is_valid
                    ), f"Query should be invalid: {test_case['query']}"
            except Exception as e:
                if test_case["should_be_valid"]:
                    pytest.fail(
                        f"Query parsing failed unexpectedly: {test_case['query']}, Error: {e}"
                    )

    def test_wiql_transformer_different_configurations(self):
        """Test WIQL transformer with different configurations."""
        # Test data
        raw_work_item = {
            "id": 1,
            "fields": {
                "System.Title": "Test Story",
                "System.WorkItemType": "User Story",
                "System.State": "Active",
                "System.CreatedDate": "2023-01-01T10:00:00Z",
                "Microsoft.VSTS.Common.Priority": 2,
                "Microsoft.VSTS.Scheduling.StoryPoints": 5.0,
                "Custom.BusinessValue": 100,
                "System.Tags": "frontend;critical",
            },
        }

        # Test with custom fields included
        config_with_custom = TransformationConfig(include_custom_fields=True)
        transformer_with_custom = WIQLTransformer(config_with_custom)

        work_items_with_custom = transformer_with_custom.transform_work_items(
            [raw_work_item]
        )
        assert len(work_items_with_custom) == 1
        assert "Custom.BusinessValue" in work_items_with_custom[0].custom_fields

        # Test with custom fields excluded
        config_without_custom = TransformationConfig(include_custom_fields=False)
        transformer_without_custom = WIQLTransformer(config_without_custom)

        work_items_without_custom = transformer_without_custom.transform_work_items(
            [raw_work_item]
        )
        assert len(work_items_without_custom) == 1
        assert len(work_items_without_custom[0].custom_fields) == 0

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_wiql_error_handling_integration(self, mock_get, mock_post):
        """Test error handling across WIQL components."""
        # Test malformed WIQL query
        with pytest.raises(WIQLError):
            self.client.execute_wiql_query("INVALID WIQL QUERY")

        # Test API error
        mock_post.return_value.status_code = 400
        mock_post.return_value.raise_for_status.side_effect = Exception("API Error")

        with pytest.raises(WIQLError):
            self.client.execute_wiql_query(
                "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'test'"
            )

        # Test validation error
        with pytest.raises(WIQLValidationError):
            self.client.execute_wiql_query(
                "SELECT [Unknown.Field] FROM WorkItems", validate=True
            )

    def test_wiql_caching_behavior(self):
        """Test WIQL query caching behavior."""
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'test'"

        # First parse
        parsed1 = self.client._parse_and_validate_query(query)

        # Second parse (should be cached)
        parsed2 = self.client._parse_and_validate_query(query)

        # Should be the same object
        assert parsed1 is parsed2

        # Cache should contain the query
        cache_key = hash(query)
        assert cache_key in self.client._wiql_cache

        # Different query should not be cached
        different_query = (
            "SELECT [System.Title] FROM WorkItems WHERE [System.TeamProject] = 'test'"
        )
        parsed3 = self.client._parse_and_validate_query(different_query)

        assert parsed3 is not parsed1

    def test_wiql_performance_optimizations(self):
        """Test WIQL performance optimizations."""
        # Test query building with different parameters
        test_scenarios = [
            {
                "days_back": 7,
                "work_item_types": ["User Story"],
                "states": ["Active"],
                "expected_conditions": 3,  # Project, date, types, states
            },
            {
                "days_back": 30,
                "work_item_types": ["User Story", "Bug", "Task"],
                "states": ["Active", "Resolved", "Closed"],
                "assignees": ["John Doe", "Jane Smith"],
                "expected_conditions": 4,  # Project, date, types, states, assignees
            },
        ]

        for scenario in test_scenarios:
            query = self.parser.build_query_for_work_items(
                project="test-project",
                days_back=scenario["days_back"],
                work_item_types=scenario["work_item_types"],
                states=scenario["states"],
                assignees=scenario.get("assignees"),
            )

            # Verify query structure
            assert len(query.where_conditions) >= scenario["expected_conditions"]
            assert query.project_filter == "test-project"

            # Verify query can be converted to string
            wiql_string = query.to_wiql_string()
            assert "SELECT [System.Id]" in wiql_string
            assert "FROM WorkItems" in wiql_string
            assert "WHERE [System.TeamProject] = 'test-project'" in wiql_string

    def test_wiql_field_type_handling(self):
        """Test WIQL field type handling across components."""
        # Test different field types
        test_fields = [
            {
                "name": "System.Id",
                "type": "integer",
                "test_value": 123,
                "valid_operators": ["=", "<>", ">", ">=", "<", "<=", "IN", "NOT IN"],
            },
            {
                "name": "System.Title",
                "type": "string",
                "test_value": "Test Title",
                "valid_operators": ["=", "<>", "LIKE", "IN", "NOT IN", "CONTAINS"],
            },
            {
                "name": "System.CreatedDate",
                "type": "datetime",
                "test_value": "2023-01-01T10:00:00Z",
                "valid_operators": [
                    "=",
                    "<>",
                    ">",
                    ">=",
                    "<",
                    "<=",
                    "EVER",
                    "NOT EVER",
                    "WAS EVER",
                    "CHANGED DATE",
                ],
            },
        ]

        for field_info in test_fields:
            field_name = field_info["name"]

            # Check field is in supported fields
            supported_fields = self.client.get_supported_fields()
            assert field_name in supported_fields

            # Check field type
            field_def = supported_fields[field_name]
            assert field_def["type"] == field_info["type"]

            # Check operators
            for operator in field_info["valid_operators"]:
                assert operator in field_def["supported_operators"]

    @patch("src.wiql_client.requests.post")
    @patch("src.wiql_client.requests.get")
    def test_wiql_statistics_integration(self, mock_get, mock_post):
        """Test WIQL statistics integration."""
        # Mock WIQL query response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "workItems": [
                {"id": 1, "url": "test-url"},
                {"id": 2, "url": "test-url"},
                {"id": 3, "url": "test-url"},
            ]
        }

        # Mock work items details response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "value": [
                {
                    "id": 1,
                    "fields": {
                        "System.Title": "Story 1",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-01T10:00:00Z",
                        "System.AssignedTo": {"displayName": "John Doe"},
                    },
                },
                {
                    "id": 2,
                    "fields": {
                        "System.Title": "Bug 1",
                        "System.WorkItemType": "Bug",
                        "System.State": "Resolved",
                        "System.CreatedDate": "2023-01-02T11:00:00Z",
                        "System.AssignedTo": {"displayName": "Jane Smith"},
                    },
                },
                {
                    "id": 3,
                    "fields": {
                        "System.Title": "Story 2",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.CreatedDate": "2023-01-03T12:00:00Z",
                        "System.AssignedTo": {"displayName": "John Doe"},
                    },
                },
            ]
        }

        # Get statistics
        stats = self.client.get_work_item_statistics()

        # Verify statistics
        assert stats["total_items"] == 3
        assert stats["by_type"]["User Story"] == 2
        assert stats["by_type"]["Bug"] == 1
        assert stats["by_state"]["Active"] == 2
        assert stats["by_state"]["Resolved"] == 1
        assert stats["by_assignee"]["John Doe"] == 2
        assert stats["by_assignee"]["Jane Smith"] == 1

        # Verify date range
        assert stats["date_range"]["earliest"] is not None
        assert stats["date_range"]["latest"] is not None


if __name__ == "__main__":
    pytest.main([__file__])
