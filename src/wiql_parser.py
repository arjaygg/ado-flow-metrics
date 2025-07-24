"""WIQL (Work Item Query Language) parser and validator for Azure DevOps."""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .exceptions import DataValidationError

logger = logging.getLogger(__name__)


class WIQLOperator(Enum):
    """Supported WIQL operators."""

    EQUALS = "="
    NOT_EQUALS = "<>"
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    CONTAINS = "CONTAINS"
    UNDER = "UNDER"
    EVER = "EVER"
    NOT_EVER = "NOT EVER"
    WAS_EVER = "WAS EVER"
    CHANGED_DATE = "CHANGED DATE"
    CHANGED_BY = "CHANGED BY"


class WIQLFieldType(Enum):
    """WIQL field types for validation."""

    STRING = "string"
    INTEGER = "integer"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    REFERENCE = "reference"
    IDENTITY = "identity"
    GUID = "guid"
    PLAINTEXT = "plaintext"
    HTML = "html"
    HISTORY = "history"
    DOUBLE = "double"
    TREEPATH = "treepath"


@dataclass
class WIQLField:
    """WIQL field definition."""

    name: str
    reference_name: str
    field_type: WIQLFieldType
    is_sortable: bool = True
    is_queryable: bool = True
    supported_operators: List[WIQLOperator] = field(default_factory=list)

    def __post_init__(self):
        """Set default supported operators based on field type."""
        if not self.supported_operators:
            if self.field_type == WIQLFieldType.STRING:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                    WIQLOperator.LIKE,
                    WIQLOperator.IN,
                    WIQLOperator.NOT_IN,
                    WIQLOperator.CONTAINS,
                ]
            elif self.field_type == WIQLFieldType.INTEGER:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                    WIQLOperator.GREATER_THAN,
                    WIQLOperator.GREATER_THAN_OR_EQUAL,
                    WIQLOperator.LESS_THAN,
                    WIQLOperator.LESS_THAN_OR_EQUAL,
                    WIQLOperator.IN,
                    WIQLOperator.NOT_IN,
                ]
            elif self.field_type == WIQLFieldType.DATETIME:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                    WIQLOperator.GREATER_THAN,
                    WIQLOperator.GREATER_THAN_OR_EQUAL,
                    WIQLOperator.LESS_THAN,
                    WIQLOperator.LESS_THAN_OR_EQUAL,
                    WIQLOperator.EVER,
                    WIQLOperator.NOT_EVER,
                    WIQLOperator.WAS_EVER,
                    WIQLOperator.CHANGED_DATE,
                ]
            elif self.field_type == WIQLFieldType.BOOLEAN:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                ]
            elif self.field_type == WIQLFieldType.TREEPATH:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                    WIQLOperator.UNDER,
                    WIQLOperator.IN,
                    WIQLOperator.NOT_IN,
                ]
            else:
                self.supported_operators = [
                    WIQLOperator.EQUALS,
                    WIQLOperator.NOT_EQUALS,
                ]


@dataclass
class WIQLCondition:
    """Represents a WIQL WHERE condition."""

    field: str
    operator: WIQLOperator
    value: Union[str, int, float, bool, List[str]]
    logical_operator: Optional[str] = None  # AND, OR


@dataclass
class WIQLQuery:
    """Parsed WIQL query structure."""

    select_fields: List[str]
    from_clause: str = "WorkItems"
    where_conditions: List[WIQLCondition] = field(default_factory=list)
    order_by: List[Dict[str, str]] = field(
        default_factory=list
    )  # [{"field": "System.Id", "direction": "ASC"}]
    project_filter: Optional[str] = None
    top_count: Optional[int] = None

    def to_wiql_string(self) -> str:
        """Convert parsed query back to WIQL string."""
        query_parts = []

        # SELECT clause
        if self.select_fields:
            query_parts.append(f"SELECT {', '.join(self.select_fields)}")
        else:
            query_parts.append("SELECT [System.Id]")

        # FROM clause
        query_parts.append(f"FROM {self.from_clause}")

        # WHERE clause
        if self.where_conditions:
            where_parts = []
            for condition in self.where_conditions:
                if condition.logical_operator and where_parts:
                    where_parts.append(condition.logical_operator)

                if isinstance(condition.value, list):
                    if condition.operator in [WIQLOperator.IN, WIQLOperator.NOT_IN]:
                        quoted_values = [f"'{self._escape_wiql_string(str(v))}'" for v in condition.value]
                        value_str = f"({', '.join(quoted_values)})"
                    else:
                        value_str = f"'{condition.value[0]}'"
                elif isinstance(condition.value, str):
                    value_str = f"'{self._escape_wiql_string(condition.value)}'"
                else:
                    value_str = str(condition.value)

                where_parts.append(
                    f"[{condition.field}] {condition.operator.value} {value_str}"
                )

            query_parts.append(f"WHERE {' '.join(where_parts)}")

        # ORDER BY clause
        if self.order_by:
            order_parts = []
            for order in self.order_by:
                direction = order.get("direction", "ASC")
                order_parts.append(f"[{order['field']}] {direction}")
            query_parts.append(f"ORDER BY {', '.join(order_parts)}")

        return "\n".join(query_parts)

    def _escape_wiql_string(self, value: str) -> str:
        """Escape WIQL string values to prevent injection attacks."""
        if not isinstance(value, str):
            return str(value)
        
        # Escape single quotes by doubling them (WIQL standard)
        escaped = value.replace("'", "''")
        
        # Remove or escape potentially dangerous characters
        # Block common SQL injection patterns
        dangerous_patterns = [
            '--', '/*', '*/', ';', 'UNION', 'SELECT', 'INSERT', 
            'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER'
        ]
        
        for pattern in dangerous_patterns:
            if pattern.upper() in escaped.upper():
                # Log potential injection attempt
                logger.warning(f"Potential WIQL injection attempt blocked: {pattern} in '{value}'")
                # Replace with safe alternative or remove
                escaped = escaped.replace(pattern, '').replace(pattern.upper(), '').replace(pattern.lower(), '')
        
        return escaped


class WIQLParser:
    """Parser for WIQL queries with validation."""

    def __init__(self):
        self.system_fields = self._initialize_system_fields()
        self.custom_fields: Dict[str, WIQLField] = {}

    def _initialize_system_fields(self) -> Dict[str, WIQLField]:
        """Initialize common Azure DevOps system fields."""
        return {
            "System.Id": WIQLField("ID", "System.Id", WIQLFieldType.INTEGER),
            "System.Title": WIQLField("Title", "System.Title", WIQLFieldType.STRING),
            "System.WorkItemType": WIQLField(
                "Work Item Type", "System.WorkItemType", WIQLFieldType.STRING
            ),
            "System.State": WIQLField("State", "System.State", WIQLFieldType.STRING),
            "System.AssignedTo": WIQLField(
                "Assigned To", "System.AssignedTo", WIQLFieldType.IDENTITY
            ),
            "System.CreatedDate": WIQLField(
                "Created Date", "System.CreatedDate", WIQLFieldType.DATETIME
            ),
            "System.ChangedDate": WIQLField(
                "Changed Date", "System.ChangedDate", WIQLFieldType.DATETIME
            ),
            "System.ClosedDate": WIQLField(
                "Closed Date", "System.ClosedDate", WIQLFieldType.DATETIME
            ),
            "System.TeamProject": WIQLField(
                "Team Project", "System.TeamProject", WIQLFieldType.STRING
            ),
            "System.AreaPath": WIQLField(
                "Area Path", "System.AreaPath", WIQLFieldType.TREEPATH
            ),
            "System.IterationPath": WIQLField(
                "Iteration Path", "System.IterationPath", WIQLFieldType.TREEPATH
            ),
            "System.Tags": WIQLField("Tags", "System.Tags", WIQLFieldType.STRING),
            "System.Priority": WIQLField(
                "Priority", "System.Priority", WIQLFieldType.INTEGER
            ),
            "Microsoft.VSTS.Common.Priority": WIQLField(
                "Priority", "Microsoft.VSTS.Common.Priority", WIQLFieldType.INTEGER
            ),
            "Microsoft.VSTS.Scheduling.StoryPoints": WIQLField(
                "Story Points",
                "Microsoft.VSTS.Scheduling.StoryPoints",
                WIQLFieldType.DOUBLE,
            ),
            "Microsoft.VSTS.Scheduling.OriginalEstimate": WIQLField(
                "Original Estimate",
                "Microsoft.VSTS.Scheduling.OriginalEstimate",
                WIQLFieldType.DOUBLE,
            ),
            "Microsoft.VSTS.Scheduling.RemainingWork": WIQLField(
                "Remaining Work",
                "Microsoft.VSTS.Scheduling.RemainingWork",
                WIQLFieldType.DOUBLE,
            ),
            "Microsoft.VSTS.Scheduling.CompletedWork": WIQLField(
                "Completed Work",
                "Microsoft.VSTS.Scheduling.CompletedWork",
                WIQLFieldType.DOUBLE,
            ),
        }

    def register_custom_field(self, field: WIQLField) -> None:
        """Register a custom field for validation."""
        self.custom_fields[field.reference_name] = field

    def parse_query(self, wiql_query: str) -> WIQLQuery:
        """Parse a WIQL query string into a structured query object."""
        try:
            # Normalize whitespace and remove comments
            query = self._normalize_query(wiql_query)

            # Parse SELECT clause
            select_fields = self._parse_select_clause(query)

            # Parse FROM clause
            from_clause = self._parse_from_clause(query)

            # Parse WHERE clause
            where_conditions = self._parse_where_clause(query)

            # Parse ORDER BY clause
            order_by = self._parse_order_by_clause(query)

            # Parse TOP clause
            top_count = self._parse_top_clause(query)

            # Extract project filter from WHERE conditions
            project_filter = self._extract_project_filter(where_conditions)

            return WIQLQuery(
                select_fields=select_fields,
                from_clause=from_clause,
                where_conditions=where_conditions,
                order_by=order_by,
                project_filter=project_filter,
                top_count=top_count,
            )

        except Exception as e:
            raise DataValidationError(f"Failed to parse WIQL query: {str(e)}")

    def _normalize_query(self, query: str) -> str:
        """Normalize query by removing comments and extra whitespace."""
        # Remove single line comments
        query = re.sub(r"--.*$", "", query, flags=re.MULTILINE)

        # Remove multi-line comments
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

        # Normalize whitespace
        query = re.sub(r"\s+", " ", query).strip()

        return query

    def _parse_select_clause(self, query: str) -> List[str]:
        """Parse SELECT clause to extract field names."""
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", query, re.IGNORECASE)
        if not select_match:
            return ["System.Id"]  # Default selection

        select_part = select_match.group(1)

        # Handle special cases
        if select_part.strip() == "*":
            return ["*"]

        # Parse field names, handling brackets
        fields = []
        field_pattern = r"\[([^\]]+)\]|(\w+(?:\.\w+)*)"

        for match in re.finditer(field_pattern, select_part):
            field_name = match.group(1) or match.group(2)
            if field_name:
                fields.append(field_name)

        return fields if fields else ["System.Id"]

    def _parse_from_clause(self, query: str) -> str:
        """Parse FROM clause."""
        from_match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
        return from_match.group(1) if from_match else "WorkItems"

    def _parse_where_clause(self, query: str) -> List[WIQLCondition]:
        """Parse WHERE clause into conditions."""
        where_match = re.search(
            r"WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s*$)", query, re.IGNORECASE | re.DOTALL
        )
        if not where_match:
            return []

        where_part = where_match.group(1)
        conditions = []

        # Split by logical operators while preserving them
        condition_parts = re.split(r"\s+(AND|OR)\s+", where_part, flags=re.IGNORECASE)

        logical_op = None
        for i, part in enumerate(condition_parts):
            if part.upper() in ["AND", "OR"]:
                logical_op = part.upper()
            else:
                condition = self._parse_condition(part.strip(), logical_op)
                if condition:
                    conditions.append(condition)
                logical_op = None

        return conditions

    def _parse_condition(
        self, condition_str: str, logical_op: Optional[str]
    ) -> Optional[WIQLCondition]:
        """Parse a single WHERE condition."""
        # Pattern to match field operator value
        pattern = (
            r"\[([^\]]+)\]\s*(=|<>|>=|<=|>|<|LIKE|IN|NOT\s+IN|CONTAINS|"
            r"UNDER|EVER|NOT\s+EVER|WAS\s+EVER|CHANGED\s+DATE|CHANGED\s+BY)\s*(.+)"
        )

        match = re.match(pattern, condition_str, re.IGNORECASE)
        if not match:
            return None

        field_name = match.group(1)
        operator_str = match.group(2).upper()
        value_str = match.group(3).strip()

        # Parse operator
        try:
            operator = WIQLOperator(operator_str)
        except ValueError:
            # Handle multi-word operators
            operator_map = {
                "NOT IN": WIQLOperator.NOT_IN,
                "NOT EVER": WIQLOperator.NOT_EVER,
                "WAS EVER": WIQLOperator.WAS_EVER,
                "CHANGED DATE": WIQLOperator.CHANGED_DATE,
                "CHANGED BY": WIQLOperator.CHANGED_BY,
            }
            operator = operator_map.get(operator_str, WIQLOperator.EQUALS)

        # Parse value
        value = self._parse_value(value_str, operator)

        return WIQLCondition(
            field=field_name,
            operator=operator,
            value=value,
            logical_operator=logical_op,
        )

    def _parse_value(
        self, value_str: str, operator: WIQLOperator
    ) -> Union[str, int, float, bool, List[str]]:
        """Parse value based on operator and format."""
        value_str = value_str.strip()

        # Handle IN/NOT IN operators with lists
        if operator in [WIQLOperator.IN, WIQLOperator.NOT_IN]:
            if value_str.startswith("(") and value_str.endswith(")"):
                value_str = value_str[1:-1]
                return [v.strip().strip("'\"") for v in value_str.split(",")]

        # Handle quoted strings
        if (value_str.startswith("'") and value_str.endswith("'")) or (
            value_str.startswith('"') and value_str.endswith('"')
        ):
            return value_str[1:-1]

        # Handle boolean values
        if value_str.lower() in ["true", "false"]:
            return value_str.lower() == "true"

        # Handle numeric values
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Handle special values
        if value_str.upper() in ["NULL", "@TODAY", "@ME"]:
            return value_str.upper()

        # Default to string
        return value_str

    def _parse_order_by_clause(self, query: str) -> List[Dict[str, str]]:
        """Parse ORDER BY clause."""
        order_match = re.search(
            r"ORDER\s+BY\s+(.*?)(?:\s*$)", query, re.IGNORECASE | re.DOTALL
        )
        if not order_match:
            return []

        order_part = order_match.group(1)
        order_items = []

        # Split by comma
        for item in order_part.split(","):
            item = item.strip()

            # Parse field and direction
            field_match = re.match(
                r"\[([^\]]+)\](?:\s+(ASC|DESC))?", item, re.IGNORECASE
            )
            if field_match:
                field_name = field_match.group(1)
                direction = (
                    field_match.group(2).upper() if field_match.group(2) else "ASC"
                )
                order_items.append({"field": field_name, "direction": direction})

        return order_items

    def _parse_top_clause(self, query: str) -> Optional[int]:
        """Parse TOP clause."""
        top_match = re.search(r"SELECT\s+TOP\s+(\d+)", query, re.IGNORECASE)
        if top_match:
            return int(top_match.group(1))
        return None

    def _extract_project_filter(self, conditions: List[WIQLCondition]) -> Optional[str]:
        """Extract project filter from WHERE conditions."""
        for condition in conditions:
            if (
                condition.field == "System.TeamProject"
                and condition.operator == WIQLOperator.EQUALS
            ):
                return str(condition.value)
        return None

    def validate_query(self, query: WIQLQuery) -> List[str]:
        """Validate a parsed WIQL query and return list of validation errors."""
        errors = []

        # Validate fields
        all_fields = {**self.system_fields, **self.custom_fields}

        for field_name in query.select_fields:
            if field_name != "*" and field_name not in all_fields:
                errors.append(f"Unknown field in SELECT clause: {field_name}")

        # Validate WHERE conditions
        for condition in query.where_conditions:
            if condition.field not in all_fields:
                errors.append(f"Unknown field in WHERE clause: {condition.field}")
                continue

            field_def = all_fields[condition.field]

            # Check if operator is supported for this field
            if condition.operator not in field_def.supported_operators:
                errors.append(
                    f"Operator {condition.operator.value} not supported for field {condition.field}"
                )

            # Validate value type
            validation_error = self._validate_value_type(
                condition.value, field_def.field_type, condition.operator
            )
            if validation_error:
                errors.append(
                    f"Invalid value for field {condition.field}: {validation_error}"
                )

        # Validate ORDER BY fields
        for order in query.order_by:
            if order["field"] not in all_fields:
                errors.append(f"Unknown field in ORDER BY clause: {order['field']}")
            elif not all_fields[order["field"]].is_sortable:
                errors.append(f"Field {order['field']} is not sortable")

        return errors

    def _validate_value_type(
        self, value: Any, field_type: WIQLFieldType, operator: WIQLOperator
    ) -> Optional[str]:
        """Validate value type against field type."""
        if operator in [WIQLOperator.IN, WIQLOperator.NOT_IN]:
            if not isinstance(value, list):
                return "IN/NOT IN operators require list values"
            # Validate each item in the list
            for item in value:
                error = self._validate_single_value_type(item, field_type)
                if error:
                    return error
        else:
            return self._validate_single_value_type(value, field_type)

        return None

    def _validate_single_value_type(
        self, value: Any, field_type: WIQLFieldType
    ) -> Optional[str]:
        """Validate a single value against field type."""
        if value in ["NULL", "@TODAY", "@ME"]:
            return None  # Special values are generally allowed

        if field_type == WIQLFieldType.INTEGER:
            if not isinstance(value, int):
                return "Expected integer value"
        elif field_type == WIQLFieldType.DOUBLE:
            if not isinstance(value, (int, float)):
                return "Expected numeric value"
        elif field_type == WIQLFieldType.BOOLEAN:
            if not isinstance(value, bool):
                return "Expected boolean value"
        elif field_type == WIQLFieldType.DATETIME:
            if isinstance(value, str):
                # Try to parse as datetime
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return "Expected valid datetime format"
            elif not isinstance(value, datetime):
                return "Expected datetime value"
        elif field_type in [
            WIQLFieldType.STRING,
            WIQLFieldType.PLAINTEXT,
            WIQLFieldType.HTML,
        ]:
            if not isinstance(value, str):
                return "Expected string value"

        return None

    def build_query_for_work_items(
        self,
        project: str,
        days_back: int = 30,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> WIQLQuery:
        """Build a standard WIQL query for work items with common filters."""

        # Base conditions
        conditions = [
            WIQLCondition(
                field="System.TeamProject", operator=WIQLOperator.EQUALS, value=project
            )
        ]

        # Date filter
        if days_back > 0:
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime(
                "%Y-%m-%d"
            )
            conditions.append(
                WIQLCondition(
                    field="System.ChangedDate",
                    operator=WIQLOperator.GREATER_THAN_OR_EQUAL,
                    value=cutoff_date,
                    logical_operator="AND",
                )
            )

        # Work item types filter
        if work_item_types:
            conditions.append(
                WIQLCondition(
                    field="System.WorkItemType",
                    operator=WIQLOperator.IN,
                    value=work_item_types,
                    logical_operator="AND",
                )
            )

        # States filter
        if states:
            conditions.append(
                WIQLCondition(
                    field="System.State",
                    operator=WIQLOperator.IN,
                    value=states,
                    logical_operator="AND",
                )
            )

        # Assignees filter
        if assignees:
            conditions.append(
                WIQLCondition(
                    field="System.AssignedTo",
                    operator=WIQLOperator.IN,
                    value=assignees,
                    logical_operator="AND",
                )
            )

        # Additional filters
        if additional_filters:
            for field, filter_value in additional_filters.items():
                if isinstance(filter_value, list):
                    conditions.append(
                        WIQLCondition(
                            field=field,
                            operator=WIQLOperator.IN,
                            value=filter_value,
                            logical_operator="AND",
                        )
                    )
                else:
                    conditions.append(
                        WIQLCondition(
                            field=field,
                            operator=WIQLOperator.EQUALS,
                            value=filter_value,
                            logical_operator="AND",
                        )
                    )

        return WIQLQuery(
            select_fields=["System.Id"],
            from_clause="WorkItems",
            where_conditions=conditions,
            order_by=[{"field": "System.ChangedDate", "direction": "DESC"}],
            project_filter=project,
        )


# Convenience functions for common queries
def create_basic_work_items_query(project: str, days_back: int = 30) -> str:
    """Create a basic WIQL query for work items."""
    parser = WIQLParser()
    query = parser.build_query_for_work_items(project, days_back)
    return query.to_wiql_string()


def create_filtered_work_items_query(
    project: str,
    work_item_types: List[str],
    states: Optional[List[str]] = None,
    days_back: int = 30,
) -> str:
    """Create a filtered WIQL query for specific work item types and states."""
    parser = WIQLParser()
    query = parser.build_query_for_work_items(
        project=project,
        days_back=days_back,
        work_item_types=work_item_types,
        states=states,
    )
    return query.to_wiql_string()


def validate_wiql_query(wiql_query: str) -> List[str]:
    """Validate a WIQL query string and return any errors."""
    parser = WIQLParser()
    try:
        query = parser.parse_query(wiql_query)
        return parser.validate_query(query)
    except Exception as e:
        return [str(e)]
