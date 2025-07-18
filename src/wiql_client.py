"""Enhanced Azure DevOps client with WIQL filtering capabilities."""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .azure_devops_client import AzureDevOpsClient
from .exceptions import WIQLError, WIQLParseError, WIQLValidationError
from .wiql_parser import WIQLParser, WIQLQuery, create_filtered_work_items_query

logger = logging.getLogger(__name__)


class WIQLClient(AzureDevOpsClient):
    """Enhanced Azure DevOps client with WIQL query support."""

    def __init__(self, org_url: str, project: str, pat_token: str):
        super().__init__(org_url, project, pat_token)
        self.wiql_parser = WIQLParser()
        self._wiql_cache = {}  # Simple cache for parsed queries

    def execute_wiql_query(
        self,
        wiql_query: str,
        validate: bool = True,
        progress_callback: Optional[Callable] = None,
    ) -> List[Dict]:
        """Execute a WIQL query and return work items."""
        try:
            # Parse and validate query
            if validate:
                parsed_query = self._parse_and_validate_query(wiql_query)
            else:
                parsed_query = self.wiql_parser.parse_query(wiql_query)

            # Execute query
            return self._execute_parsed_query(parsed_query, progress_callback)

        except Exception as e:
            logger.error(f"Failed to execute WIQL query: {e}")
            raise WIQLError(f"WIQL query execution failed: {e}")

    def get_work_items_with_wiql(
        self,
        project: Optional[str] = None,
        days_back: int = 90,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
        custom_wiql: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        history_limit: Optional[int] = None,
    ) -> List[Dict]:
        """Get work items using WIQL with flexible filtering options."""

        # Use project from parameter or default
        target_project = project or self.project

        if progress_callback:
            progress_callback("phase", "Building WIQL query...")

        try:
            # Use custom WIQL if provided, otherwise build query
            if custom_wiql:
                wiql_query = custom_wiql
            else:
                parsed_query = self.wiql_parser.build_query_for_work_items(
                    project=target_project,
                    days_back=days_back,
                    work_item_types=work_item_types,
                    states=states,
                    assignees=assignees,
                    additional_filters=additional_filters,
                )
                wiql_query = parsed_query.to_wiql_string()

            logger.info(f"Executing WIQL query: {wiql_query}")

            # Execute the query
            return self.execute_wiql_query(
                wiql_query, validate=True, progress_callback=progress_callback
            )

        except Exception as e:
            logger.error(f"Failed to get work items with WIQL: {e}")
            raise WIQLError(f"Failed to get work items with WIQL: {e}")

    def _parse_and_validate_query(self, wiql_query: str) -> WIQLQuery:
        """Parse and validate a WIQL query."""
        # Check cache first
        cache_key = hash(wiql_query)
        if cache_key in self._wiql_cache:
            return self._wiql_cache[cache_key]

        try:
            # Parse query
            parsed_query = self.wiql_parser.parse_query(wiql_query)

            # Validate query
            validation_errors = self.wiql_parser.validate_query(parsed_query)
            if validation_errors:
                raise WIQLValidationError(
                    f"WIQL validation failed: {'; '.join(validation_errors)}"
                )

            # Cache the parsed query
            self._wiql_cache[cache_key] = parsed_query

            return parsed_query

        except WIQLValidationError:
            raise
        except Exception as e:
            raise WIQLParseError(f"Failed to parse WIQL query: {e}")

    def _execute_parsed_query(
        self, parsed_query: WIQLQuery, progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Execute a parsed WIQL query."""

        if progress_callback:
            progress_callback("phase", "Executing WIQL query...")

        # Convert back to WIQL string for API call
        wiql_string = parsed_query.to_wiql_string()

        # Build the request
        wiql_request = {"query": wiql_string}

        # Execute WIQL query to get work item IDs
        response = self._execute_wiql_query(wiql_request)
        work_item_refs = self._parse_wiql_response(response)

        if not work_item_refs:
            logger.warning("No work items found for the WIQL query")
            return []

        work_item_ids = [item["id"] for item in work_item_refs]

        if progress_callback:
            progress_callback("count", len(work_item_ids))
            progress_callback("phase", "Fetching work item details...")

        # Fetch detailed work item information
        work_items = self._fetch_work_item_details(work_item_ids, progress_callback)

        if not work_items:
            return []

        # Transform and enrich with state history
        return self._transform_and_enrich_work_items(work_items, progress_callback)

    def validate_wiql_query(self, wiql_query: str) -> Dict[str, Any]:
        """Validate a WIQL query and return validation results."""
        try:
            parsed_query = self.wiql_parser.parse_query(wiql_query)
            validation_errors = self.wiql_parser.validate_query(parsed_query)

            return {
                "valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "parsed_query": {
                    "select_fields": parsed_query.select_fields,
                    "from_clause": parsed_query.from_clause,
                    "conditions_count": len(parsed_query.where_conditions),
                    "order_by_fields": [
                        order["field"] for order in parsed_query.order_by
                    ],
                    "project_filter": parsed_query.project_filter,
                    "top_count": parsed_query.top_count,
                },
            }

        except Exception as e:
            return {"valid": False, "errors": [str(e)], "parsed_query": None}

    def get_wiql_query_preview(
        self,
        project: Optional[str] = None,
        days_back: int = 90,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get a preview of the WIQL query that would be generated."""

        target_project = project or self.project

        parsed_query = self.wiql_parser.build_query_for_work_items(
            project=target_project,
            days_back=days_back,
            work_item_types=work_item_types,
            states=states,
            assignees=assignees,
            additional_filters=additional_filters,
        )

        return parsed_query.to_wiql_string()

    def get_supported_fields(self) -> Dict[str, Dict[str, Any]]:
        """Get information about supported WIQL fields."""
        all_fields = {
            **self.wiql_parser.system_fields,
            **self.wiql_parser.custom_fields,
        }

        field_info = {}
        for ref_name, field in all_fields.items():
            field_info[ref_name] = {
                "name": field.name,
                "reference_name": field.reference_name,
                "type": field.field_type.value,
                "is_sortable": field.is_sortable,
                "is_queryable": field.is_queryable,
                "supported_operators": [op.value for op in field.supported_operators],
            }

        return field_info

    def register_custom_field(self, field_name: str, field_type: str, **kwargs) -> None:
        """Register a custom field for WIQL queries."""
        from .wiql_parser import WIQLField, WIQLFieldType

        try:
            field_type_enum = WIQLFieldType(field_type)
        except ValueError:
            raise WIQLError(f"Unsupported field type: {field_type}")

        custom_field = WIQLField(
            name=kwargs.get("display_name", field_name),
            reference_name=field_name,
            field_type=field_type_enum,
            is_sortable=kwargs.get("is_sortable", True),
            is_queryable=kwargs.get("is_queryable", True),
        )

        self.wiql_parser.register_custom_field(custom_field)
        logger.info(f"Registered custom field: {field_name} ({field_type})")

    def create_filtered_query(
        self,
        work_item_types: List[str],
        states: Optional[List[str]] = None,
        days_back: int = 30,
        project: Optional[str] = None,
    ) -> str:
        """Create a filtered WIQL query for specific work item types and states."""
        target_project = project or self.project
        return create_filtered_work_items_query(
            project=target_project,
            work_item_types=work_item_types,
            states=states,
            days_back=days_back,
        )

    def test_wiql_connection(self) -> Dict[str, Any]:
        """Test WIQL functionality with a simple query."""
        try:
            # Simple test query
            test_query = f"""
            SELECT TOP 5 [System.Id], [System.Title]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project}'
            ORDER BY [System.Id] DESC
            """

            validation_result = self.validate_wiql_query(test_query)

            if validation_result["valid"]:
                # Try to execute the query
                try:
                    work_items = self.execute_wiql_query(test_query, validate=False)
                    return {
                        "connection_ok": True,
                        "wiql_ok": True,
                        "validation_ok": True,
                        "test_query": test_query,
                        "work_items_found": len(work_items),
                        "message": "WIQL connection test successful",
                    }
                except Exception as e:
                    return {
                        "connection_ok": self.verify_connection(),
                        "wiql_ok": False,
                        "validation_ok": True,
                        "test_query": test_query,
                        "error": str(e),
                        "message": "WIQL execution failed",
                    }
            else:
                return {
                    "connection_ok": self.verify_connection(),
                    "wiql_ok": False,
                    "validation_ok": False,
                    "test_query": test_query,
                    "validation_errors": validation_result["errors"],
                    "message": "WIQL validation failed",
                }

        except Exception as e:
            return {
                "connection_ok": False,
                "wiql_ok": False,
                "validation_ok": False,
                "error": str(e),
                "message": "WIQL connection test failed",
            }

    def get_work_item_statistics(
        self, custom_wiql: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about work items using WIQL."""
        try:
            # Default statistics query
            if not custom_wiql:
                stats_query = f"""
                SELECT [System.Id], [System.WorkItemType], [System.State], [System.CreatedDate]
                FROM WorkItems
                WHERE [System.TeamProject] = '{self.project}'
                AND [System.CreatedDate] >= '{(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')}'
                """
            else:
                stats_query = custom_wiql

            work_items = self.execute_wiql_query(stats_query, validate=True)

            if not work_items:
                return {"total_items": 0, "message": "No work items found"}

            # Calculate statistics
            stats = {
                "total_items": len(work_items),
                "by_type": {},
                "by_state": {},
                "by_assignee": {},
                "date_range": {"earliest": None, "latest": None},
            }

            for item in work_items:
                fields = item.get("fields", {})

                # Count by type
                item_type = fields.get("System.WorkItemType", "Unknown")
                stats["by_type"][item_type] = stats["by_type"].get(item_type, 0) + 1

                # Count by state
                state = fields.get("System.State", "Unknown")
                stats["by_state"][state] = stats["by_state"].get(state, 0) + 1

                # Count by assignee
                assignee_field = fields.get("System.AssignedTo")
                if isinstance(assignee_field, dict):
                    assignee = assignee_field.get("displayName", "Unassigned")
                else:
                    assignee = str(assignee_field) if assignee_field else "Unassigned"
                stats["by_assignee"][assignee] = (
                    stats["by_assignee"].get(assignee, 0) + 1
                )

                # Track date range
                created_date = fields.get("System.CreatedDate")
                if created_date:
                    if (
                        not stats["date_range"]["earliest"]
                        or created_date < stats["date_range"]["earliest"]
                    ):
                        stats["date_range"]["earliest"] = created_date
                    if (
                        not stats["date_range"]["latest"]
                        or created_date > stats["date_range"]["latest"]
                    ):
                        stats["date_range"]["latest"] = created_date

            return stats

        except Exception as e:
            logger.error(f"Failed to get work item statistics: {e}")
            raise WIQLError(f"Failed to get work item statistics: {e}")


# Factory function to create WIQL client from configuration
def create_wiql_client_from_config(config_dict: Dict[str, Any]) -> WIQLClient:
    """Create a WIQL client from configuration dictionary."""
    azure_config = config_dict.get("azure_devops", {})

    org_url = azure_config.get("org_url") or azure_config.get("organization")
    project = azure_config.get("default_project") or azure_config.get("project")
    pat_token = azure_config.get("pat_token")

    if not org_url or not project or not pat_token:
        raise WIQLError("Missing required Azure DevOps configuration for WIQL client")

    return WIQLClient(org_url, project, pat_token)
