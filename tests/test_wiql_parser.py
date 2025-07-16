"""Tests for WIQL parser functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.exceptions import WIQLParseError, WIQLValidationError
from src.wiql_parser import (
    WIQLCondition,
    WIQLField,
    WIQLFieldType,
    WIQLOperator,
    WIQLParser,
    WIQLQuery,
    create_basic_work_items_query,
    create_filtered_work_items_query,
    validate_wiql_query,
)


class TestWIQLParser:
    """Test cases for WIQL parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = WIQLParser()

    def test_parse_simple_query(self):
        """Test parsing a simple WIQL query."""
        query = """
        SELECT [System.Id], [System.Title]
        FROM WorkItems
        WHERE [System.TeamProject] = 'MyProject'
        ORDER BY [System.Id] DESC
        """

        result = self.parser.parse_query(query)

        assert result.select_fields == ["System.Id", "System.Title"]
        assert result.from_clause == "WorkItems"
        assert len(result.where_conditions) == 1
        assert result.where_conditions[0].field == "System.TeamProject"
        assert result.where_conditions[0].operator == WIQLOperator.EQUALS
        assert result.where_conditions[0].value == "MyProject"
        assert len(result.order_by) == 1
        assert result.order_by[0]["field"] == "System.Id"
        assert result.order_by[0]["direction"] == "DESC"

    def test_parse_complex_query(self):
        """Test parsing a complex WIQL query with multiple conditions."""
        query = """
        SELECT [System.Id], [System.Title], [System.State]
        FROM WorkItems
        WHERE [System.TeamProject] = 'MyProject'
        AND [System.WorkItemType] IN ('User Story', 'Bug')
        AND [System.State] <> 'Closed'
        AND [System.CreatedDate] >= '2023-01-01'
        ORDER BY [System.CreatedDate] DESC, [System.Id] ASC
        """

        result = self.parser.parse_query(query)

        assert len(result.select_fields) == 3
        assert len(result.where_conditions) == 4
        assert len(result.order_by) == 2

        # Check specific conditions
        type_condition = next(
            c for c in result.where_conditions if c.field == "System.WorkItemType"
        )
        assert type_condition.operator == WIQLOperator.IN
        assert type_condition.value == ["User Story", "Bug"]

        state_condition = next(
            c for c in result.where_conditions if c.field == "System.State"
        )
        assert state_condition.operator == WIQLOperator.NOT_EQUALS
        assert state_condition.value == "Closed"

    def test_parse_query_with_comments(self):
        """Test parsing query with comments."""
        query = """
        -- This is a comment
        SELECT [System.Id] -- Another comment
        FROM WorkItems
        /* Multi-line
           comment */
        WHERE [System.TeamProject] = 'MyProject'
        """

        result = self.parser.parse_query(query)

        assert result.select_fields == ["System.Id"]
        assert len(result.where_conditions) == 1

    def test_parse_query_with_top_clause(self):
        """Test parsing query with TOP clause."""
        query = """
        SELECT TOP 10 [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'MyProject'
        """

        result = self.parser.parse_query(query)

        assert result.top_count == 10
        assert result.select_fields == ["System.Id"]

    def test_parse_query_with_like_operator(self):
        """Test parsing query with LIKE operator."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.Title] LIKE 'Bug%'
        """

        result = self.parser.parse_query(query)

        assert len(result.where_conditions) == 1
        assert result.where_conditions[0].operator == WIQLOperator.LIKE
        assert result.where_conditions[0].value == "Bug%"

    def test_parse_query_with_contains_operator(self):
        """Test parsing query with CONTAINS operator."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.Tags] CONTAINS 'urgent'
        """

        result = self.parser.parse_query(query)

        assert len(result.where_conditions) == 1
        assert result.where_conditions[0].operator == WIQLOperator.CONTAINS
        assert result.where_conditions[0].value == "urgent"

    def test_parse_query_with_under_operator(self):
        """Test parsing query with UNDER operator."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.AreaPath] UNDER 'MyProject\\Area1'
        """

        result = self.parser.parse_query(query)

        assert len(result.where_conditions) == 1
        assert result.where_conditions[0].operator == WIQLOperator.UNDER
        assert result.where_conditions[0].value == "MyProject\\Area1"

    def test_parse_query_with_date_operators(self):
        """Test parsing query with date-specific operators."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.State] EVER 'Active'
        AND [System.AssignedTo] WAS EVER 'John Doe'
        AND [System.CreatedDate] CHANGED DATE >= '2023-01-01'
        """

        result = self.parser.parse_query(query)

        assert len(result.where_conditions) == 3

        ever_condition = next(
            c for c in result.where_conditions if c.operator == WIQLOperator.EVER
        )
        assert ever_condition.field == "System.State"
        assert ever_condition.value == "Active"

        was_ever_condition = next(
            c for c in result.where_conditions if c.operator == WIQLOperator.WAS_EVER
        )
        assert was_ever_condition.field == "System.AssignedTo"
        assert was_ever_condition.value == "John Doe"

        changed_date_condition = next(
            c
            for c in result.where_conditions
            if c.operator == WIQLOperator.CHANGED_DATE
        )
        assert changed_date_condition.field == "System.CreatedDate"

    def test_parse_malformed_query(self):
        """Test parsing malformed query raises exception."""
        query = "INVALID WIQL QUERY"

        with pytest.raises(Exception):
            self.parser.parse_query(query)

    def test_validate_valid_query(self):
        """Test validation of valid query."""
        query = WIQLQuery(
            select_fields=["System.Id", "System.Title"],
            where_conditions=[
                WIQLCondition(
                    field="System.TeamProject",
                    operator=WIQLOperator.EQUALS,
                    value="MyProject",
                )
            ],
            order_by=[{"field": "System.Id", "direction": "ASC"}],
        )

        errors = self.parser.validate_query(query)

        assert len(errors) == 0

    def test_validate_unknown_field(self):
        """Test validation fails for unknown field."""
        query = WIQLQuery(
            select_fields=["Unknown.Field"],
            where_conditions=[
                WIQLCondition(
                    field="Unknown.Field", operator=WIQLOperator.EQUALS, value="test"
                )
            ],
        )

        errors = self.parser.validate_query(query)

        assert len(errors) == 2  # One for SELECT, one for WHERE
        assert "Unknown field" in errors[0]
        assert "Unknown field" in errors[1]

    def test_validate_unsupported_operator(self):
        """Test validation fails for unsupported operator."""
        query = WIQLQuery(
            select_fields=["System.Id"],
            where_conditions=[
                WIQLCondition(
                    field="System.Id",
                    operator=WIQLOperator.LIKE,  # LIKE not supported for integer fields
                    value="test",
                )
            ],
        )

        errors = self.parser.validate_query(query)

        assert len(errors) > 0
        assert "not supported" in errors[0]

    def test_validate_invalid_value_type(self):
        """Test validation fails for invalid value type."""
        query = WIQLQuery(
            select_fields=["System.Id"],
            where_conditions=[
                WIQLCondition(
                    field="System.Id",
                    operator=WIQLOperator.EQUALS,
                    value="not_an_integer",
                )
            ],
        )

        errors = self.parser.validate_query(query)

        assert len(errors) > 0
        assert "Invalid value" in errors[0]

    def test_build_query_for_work_items(self):
        """Test building query for work items."""
        query = self.parser.build_query_for_work_items(
            project="MyProject",
            days_back=30,
            work_item_types=["User Story", "Bug"],
            states=["Active", "Resolved"],
        )

        assert query.project_filter == "MyProject"
        assert len(query.where_conditions) >= 3  # Project, date, types, states

        # Check project condition
        project_condition = next(
            c for c in query.where_conditions if c.field == "System.TeamProject"
        )
        assert project_condition.value == "MyProject"

        # Check types condition
        types_condition = next(
            c for c in query.where_conditions if c.field == "System.WorkItemType"
        )
        assert types_condition.value == ["User Story", "Bug"]

        # Check states condition
        states_condition = next(
            c for c in query.where_conditions if c.field == "System.State"
        )
        assert states_condition.value == ["Active", "Resolved"]

    def test_build_query_with_additional_filters(self):
        """Test building query with additional filters."""
        additional_filters = {"System.Priority": ["1", "2"], "System.Tags": "urgent"}

        query = self.parser.build_query_for_work_items(
            project="MyProject", additional_filters=additional_filters
        )

        # Check additional filters are applied
        priority_condition = next(
            c for c in query.where_conditions if c.field == "System.Priority"
        )
        assert priority_condition.value == ["1", "2"]

        tags_condition = next(
            c for c in query.where_conditions if c.field == "System.Tags"
        )
        assert tags_condition.value == "urgent"

    def test_register_custom_field(self):
        """Test registering custom field."""
        custom_field = WIQLField(
            name="Custom Field",
            reference_name="Custom.Field",
            field_type=WIQLFieldType.STRING,
        )

        self.parser.register_custom_field(custom_field)

        assert "Custom.Field" in self.parser.custom_fields
        assert self.parser.custom_fields["Custom.Field"] == custom_field

    def test_query_to_wiql_string(self):
        """Test converting query back to WIQL string."""
        query = WIQLQuery(
            select_fields=["System.Id", "System.Title"],
            where_conditions=[
                WIQLCondition(
                    field="System.TeamProject",
                    operator=WIQLOperator.EQUALS,
                    value="MyProject",
                ),
                WIQLCondition(
                    field="System.WorkItemType",
                    operator=WIQLOperator.IN,
                    value=["User Story", "Bug"],
                    logical_operator="AND",
                ),
            ],
            order_by=[{"field": "System.Id", "direction": "DESC"}],
        )

        wiql_string = query.to_wiql_string()

        assert "SELECT [System.Id], [System.Title]" in wiql_string
        assert "FROM WorkItems" in wiql_string
        assert "WHERE [System.TeamProject] = 'MyProject'" in wiql_string
        assert "AND [System.WorkItemType] IN ('User Story', 'Bug')" in wiql_string
        assert "ORDER BY [System.Id] DESC" in wiql_string


class TestWIQLUtilityFunctions:
    """Test cases for WIQL utility functions."""

    def test_create_basic_work_items_query(self):
        """Test creating basic work items query."""
        query = create_basic_work_items_query("MyProject", 30)

        assert "SELECT [System.Id]" in query
        assert "FROM WorkItems" in query
        assert "WHERE [System.TeamProject] = 'MyProject'" in query
        assert "ORDER BY [System.ChangedDate] DESC" in query

    def test_create_filtered_work_items_query(self):
        """Test creating filtered work items query."""
        query = create_filtered_work_items_query(
            "MyProject", ["User Story", "Bug"], ["Active", "Resolved"], 30
        )

        assert "SELECT [System.Id]" in query
        assert "FROM WorkItems" in query
        assert "WHERE [System.TeamProject] = 'MyProject'" in query
        assert "AND [System.WorkItemType] IN ('User Story', 'Bug')" in query
        assert "AND [System.State] IN ('Active', 'Resolved')" in query

    def test_validate_wiql_query_valid(self):
        """Test validating valid WIQL query."""
        query = """
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = 'MyProject'
        """

        errors = validate_wiql_query(query)

        assert len(errors) == 0

    def test_validate_wiql_query_invalid(self):
        """Test validating invalid WIQL query."""
        query = "INVALID QUERY"

        errors = validate_wiql_query(query)

        assert len(errors) > 0


class TestWIQLFieldDefinitions:
    """Test cases for WIQL field definitions."""

    def test_wiql_field_creation(self):
        """Test creating WIQL field."""
        field = WIQLField(
            name="Test Field",
            reference_name="Test.Field",
            field_type=WIQLFieldType.STRING,
        )

        assert field.name == "Test Field"
        assert field.reference_name == "Test.Field"
        assert field.field_type == WIQLFieldType.STRING
        assert field.is_sortable is True
        assert field.is_queryable is True
        assert len(field.supported_operators) > 0

    def test_wiql_field_default_operators(self):
        """Test default operators for different field types."""
        string_field = WIQLField("String", "Test.String", WIQLFieldType.STRING)
        assert WIQLOperator.EQUALS in string_field.supported_operators
        assert WIQLOperator.LIKE in string_field.supported_operators
        assert WIQLOperator.CONTAINS in string_field.supported_operators

        int_field = WIQLField("Integer", "Test.Integer", WIQLFieldType.INTEGER)
        assert WIQLOperator.EQUALS in int_field.supported_operators
        assert WIQLOperator.GREATER_THAN in int_field.supported_operators
        assert WIQLOperator.LESS_THAN in int_field.supported_operators

        date_field = WIQLField("Date", "Test.Date", WIQLFieldType.DATETIME)
        assert WIQLOperator.EQUALS in date_field.supported_operators
        assert WIQLOperator.GREATER_THAN in date_field.supported_operators
        assert WIQLOperator.EVER in date_field.supported_operators

        bool_field = WIQLField("Boolean", "Test.Boolean", WIQLFieldType.BOOLEAN)
        assert WIQLOperator.EQUALS in bool_field.supported_operators
        assert WIQLOperator.NOT_EQUALS in bool_field.supported_operators
        assert len(bool_field.supported_operators) == 2

    def test_wiql_condition_creation(self):
        """Test creating WIQL condition."""
        condition = WIQLCondition(
            field="System.Title",
            operator=WIQLOperator.EQUALS,
            value="Test Title",
            logical_operator="AND",
        )

        assert condition.field == "System.Title"
        assert condition.operator == WIQLOperator.EQUALS
        assert condition.value == "Test Title"
        assert condition.logical_operator == "AND"


if __name__ == "__main__":
    pytest.main([__file__])
