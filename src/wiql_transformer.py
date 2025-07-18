"""Data transformation utilities for WIQL query results."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .exceptions import DataValidationError
from .models import StateTransition, WorkItem

logger = logging.getLogger(__name__)


@dataclass
class TransformationConfig:
    """Configuration for data transformation."""

    include_custom_fields: bool = True
    include_relations: bool = False
    include_attachments: bool = False
    date_format: str = "%Y-%m-%dT%H:%M:%S.%fZ"
    timezone_aware: bool = True
    validate_data: bool = True
    fill_missing_values: bool = True

    # Field mappings for different Azure DevOps templates
    field_mappings: Dict[str, str] = None

    def __post_init__(self):
        if self.field_mappings is None:
            self.field_mappings = {}


class WIQLTransformer:
    """Transform WIQL query results into structured data models."""

    def __init__(self, config: Optional[TransformationConfig] = None):
        self.config = config or TransformationConfig()
        self.field_cache = {}  # Cache for field lookups

    def transform_work_items(self, raw_work_items: List[Dict]) -> List[WorkItem]:
        """Transform raw Azure DevOps work items into WorkItem models."""
        transformed_items = []

        for raw_item in raw_work_items:
            try:
                work_item = self._transform_single_work_item(raw_item)
                if work_item:
                    transformed_items.append(work_item)
            except Exception as e:
                logger.warning(
                    f"Failed to transform work item {raw_item.get('id', 'unknown')}: {e}"
                )
                if self.config.validate_data:
                    raise DataValidationError(f"Work item transformation failed: {e}")

        return transformed_items

    def _transform_single_work_item(self, raw_item: Dict) -> Optional[WorkItem]:
        """Transform a single raw work item into a WorkItem model."""
        try:
            fields = raw_item.get("fields", {})

            # Extract basic fields
            work_item_id = raw_item.get("id")
            if not work_item_id:
                logger.warning("Work item missing ID, skipping")
                return None

            title = self._get_field_value(fields, "System.Title", "")
            work_item_type = self._get_field_value(fields, "System.WorkItemType", "")
            state = self._get_field_value(fields, "System.State", "New")

            # Extract dates
            created_date = self._parse_date_field(fields, "System.CreatedDate")
            closed_date = self._parse_date_field(fields, "System.ClosedDate")
            activated_date = self._parse_date_field(fields, "System.ActivatedDate")

            if not created_date:
                logger.warning(
                    f"Work item {work_item_id} missing created date, skipping"
                )
                return None

            # Extract assignee
            assigned_to = self._extract_identity_field(fields, "System.AssignedTo")

            # Extract priority
            priority = self._extract_priority_field(fields)

            # Extract effort/estimation fields
            effort = self._extract_effort_field(fields)

            # Extract tags
            tags = self._extract_tags_field(fields)

            # Extract path information
            area_path = self._get_field_value(fields, "System.AreaPath")
            iteration_path = self._get_field_value(fields, "System.IterationPath")

            # Extract sprint information
            sprint_info = self._extract_sprint_info(fields)

            # Extract parent information
            parent_id = self._extract_parent_id(raw_item)

            # Extract state transitions (if available)
            transitions = self._extract_state_transitions(raw_item)

            # Extract custom fields
            custom_fields = (
                self._extract_custom_fields(fields)
                if self.config.include_custom_fields
                else {}
            )

            # Create WorkItem model
            work_item = WorkItem(
                id=work_item_id,
                title=title,
                type=work_item_type,
                state=state,
                assigned_to=assigned_to,
                created_date=created_date,
                closed_date=closed_date,
                activated_date=activated_date,
                priority=priority,
                effort=effort,
                tags=tags,
                area_path=area_path,
                iteration_path=iteration_path,
                sprint_name=sprint_info.get("name"),
                sprint_path=sprint_info.get("path"),
                transitions=transitions,
                parent_id=parent_id,
                custom_fields=custom_fields,
            )

            return work_item

        except Exception as e:
            logger.error(
                f"Failed to transform work item {raw_item.get('id', 'unknown')}: {e}"
            )
            if self.config.validate_data:
                raise
            return None

    def _get_field_value(
        self, fields: Dict, field_name: str, default: Any = None
    ) -> Any:
        """Get field value with optional mapping and default."""
        # Check for field mapping
        mapped_field = self.config.field_mappings.get(field_name, field_name)

        value = fields.get(mapped_field, default)

        # Handle empty strings
        if value == "" and default is not None:
            return default

        return value

    def _parse_date_field(self, fields: Dict, field_name: str) -> Optional[datetime]:
        """Parse a date field from Azure DevOps format."""
        date_value = self._get_field_value(fields, field_name)

        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            try:
                # Handle various Azure DevOps date formats
                if "T" in date_value:
                    # ISO format: 2023-12-01T10:30:00.000Z
                    date_str = date_value.replace("Z", "+00:00")
                    return datetime.fromisoformat(date_str)
                else:
                    # Try parsing as date only
                    return datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError as e:
                logger.warning(
                    f"Failed to parse date field {field_name}: {date_value} - {e}"
                )
                return None

        return None

    def _extract_identity_field(self, fields: Dict, field_name: str) -> Optional[str]:
        """Extract identity field (user) from Azure DevOps format."""
        identity_value = self._get_field_value(fields, field_name)

        if not identity_value:
            return None

        if isinstance(identity_value, dict):
            return identity_value.get("displayName") or identity_value.get("uniqueName")

        return str(identity_value)

    def _extract_priority_field(self, fields: Dict) -> Optional[int]:
        """Extract priority field with fallback to different priority fields."""
        priority_fields = [
            "Microsoft.VSTS.Common.Priority",
            "System.Priority",
            "Microsoft.VSTS.Common.Severity",
        ]

        for field_name in priority_fields:
            priority_value = self._get_field_value(fields, field_name)
            if priority_value is not None:
                try:
                    return int(priority_value)
                except (ValueError, TypeError):
                    continue

        return None

    def _extract_effort_field(self, fields: Dict) -> Optional[float]:
        """Extract effort/estimation field."""
        effort_fields = [
            "Microsoft.VSTS.Scheduling.StoryPoints",
            "Microsoft.VSTS.Scheduling.OriginalEstimate",
            "Microsoft.VSTS.Scheduling.Effort",
            "Microsoft.VSTS.Scheduling.Size",
        ]

        for field_name in effort_fields:
            effort_value = self._get_field_value(fields, field_name)
            if effort_value is not None:
                try:
                    return float(effort_value)
                except (ValueError, TypeError):
                    continue

        return None

    def _extract_tags_field(self, fields: Dict) -> List[str]:
        """Extract tags field."""
        tags_value = self._get_field_value(fields, "System.Tags")

        if not tags_value:
            return []

        if isinstance(tags_value, str):
            # Tags are semicolon-separated
            return [tag.strip() for tag in tags_value.split(";") if tag.strip()]

        if isinstance(tags_value, list):
            return [str(tag) for tag in tags_value]

        return []

    def _extract_sprint_info(self, fields: Dict) -> Dict[str, Optional[str]]:
        """Extract sprint information from iteration path."""
        iteration_path = self._get_field_value(fields, "System.IterationPath")

        if not iteration_path:
            return {"name": None, "path": None}

        # Extract sprint name from iteration path
        # Format: ProjectName\Sprint 1\Sprint 2 or ProjectName\Release 1\Sprint 1
        path_parts = iteration_path.split("\\")

        sprint_name = None
        if len(path_parts) > 1:
            sprint_name = path_parts[-1]  # Last part is usually the sprint name

        return {"name": sprint_name, "path": iteration_path}

    def _extract_parent_id(self, raw_item: Dict) -> Optional[int]:
        """Extract parent work item ID from relations."""
        if not self.config.include_relations:
            return None

        relations = raw_item.get("relations", [])
        if not relations:
            return None

        for relation in relations:
            if relation.get("rel") == "System.LinkTypes.Hierarchy-Reverse":
                # This is a parent link
                parent_url = relation.get("url", "")
                # Extract ID from URL: .../_apis/wit/workItems/12345
                if "workItems/" in parent_url:
                    try:
                        parent_id = int(parent_url.split("workItems/")[-1])
                        return parent_id
                    except (ValueError, IndexError):
                        continue

        return None

    def _extract_state_transitions(self, raw_item: Dict) -> List[StateTransition]:
        """Extract state transitions if available in the work item data."""
        # This would typically come from a separate API call to get work item updates
        # For now, we'll return an empty list as this data isn't typically in the main work item query
        return []

    def _extract_custom_fields(self, fields: Dict) -> Dict[str, Any]:
        """Extract custom fields (non-system fields)."""
        custom_fields = {}

        # System field prefixes to exclude
        system_prefixes = ["System.", "Microsoft.VSTS.", "Microsoft.TeamFoundation."]

        for field_name, field_value in fields.items():
            # Skip system fields
            if any(field_name.startswith(prefix) for prefix in system_prefixes):
                continue

            # Include custom fields
            custom_fields[field_name] = field_value

        return custom_fields

    def transform_to_metrics_format(
        self, work_items: List[WorkItem]
    ) -> List[Dict[str, Any]]:
        """Transform WorkItem models to metrics calculation format."""
        metrics_items = []

        for work_item in work_items:
            metrics_item = {
                "id": work_item.id,
                "title": work_item.title,
                "type": work_item.type,
                "current_state": work_item.state,
                "priority": work_item.priority,
                "created_date": work_item.created_date.isoformat()
                if work_item.created_date
                else None,
                "closed_date": work_item.closed_date.isoformat()
                if work_item.closed_date
                else None,
                "activated_date": work_item.activated_date.isoformat()
                if work_item.activated_date
                else None,
                "assigned_to": work_item.assigned_to,
                "created_by": work_item.custom_fields.get("System.CreatedBy"),
                "story_points": work_item.effort,
                "effort_hours": work_item.effort,
                "tags": work_item.tags,
                "area_path": work_item.area_path,
                "iteration_path": work_item.iteration_path,
                "sprint_name": work_item.sprint_name,
                "sprint_path": work_item.sprint_path,
                "parent_id": work_item.parent_id,
                "state_transitions": [
                    {
                        "state": transition.to_state,
                        "date": transition.transition_date.isoformat()
                        if transition.transition_date
                        else None,
                        "changed_by": transition.changed_by,
                    }
                    for transition in work_item.transitions
                ],
                "custom_fields": work_item.custom_fields,
            }

            metrics_items.append(metrics_item)

        return metrics_items

    def validate_transformed_data(self, work_items: List[WorkItem]) -> List[str]:
        """Validate transformed work items and return validation errors."""
        errors = []

        for work_item in work_items:
            # Check required fields
            if not work_item.id:
                errors.append("Work item missing ID")

            if not work_item.title:
                errors.append(f"Work item {work_item.id} missing title")

            if not work_item.type:
                errors.append(f"Work item {work_item.id} missing type")

            if not work_item.created_date:
                errors.append(f"Work item {work_item.id} missing created date")

            # Validate date consistency
            if work_item.closed_date and work_item.created_date:
                if work_item.closed_date < work_item.created_date:
                    errors.append(
                        f"Work item {work_item.id} closed date before created date"
                    )

            if work_item.activated_date and work_item.created_date:
                if work_item.activated_date < work_item.created_date:
                    errors.append(
                        f"Work item {work_item.id} activated date before created date"
                    )

            # Validate priority range
            if work_item.priority is not None:
                if work_item.priority < 1 or work_item.priority > 4:
                    errors.append(
                        f"Work item {work_item.id} priority out of range (1-4)"
                    )

            # Validate effort
            if work_item.effort is not None and work_item.effort < 0:
                errors.append(f"Work item {work_item.id} effort cannot be negative")

        return errors

    def get_transformation_summary(self, work_items: List[WorkItem]) -> Dict[str, Any]:
        """Get a summary of the transformation results."""
        if not work_items:
            return {"total_items": 0}

        summary = {
            "total_items": len(work_items),
            "by_type": {},
            "by_state": {},
            "with_effort": 0,
            "with_assignee": 0,
            "completed_items": 0,
            "date_range": {"earliest_created": None, "latest_created": None},
        }

        for work_item in work_items:
            # Count by type
            summary["by_type"][work_item.type] = (
                summary["by_type"].get(work_item.type, 0) + 1
            )

            # Count by state
            summary["by_state"][work_item.state] = (
                summary["by_state"].get(work_item.state, 0) + 1
            )

            # Count items with effort
            if work_item.effort is not None:
                summary["with_effort"] += 1

            # Count items with assignee
            if work_item.assigned_to:
                summary["with_assignee"] += 1

            # Count completed items
            if work_item.closed_date:
                summary["completed_items"] += 1

            # Track date range
            if work_item.created_date:
                if (
                    not summary["date_range"]["earliest_created"]
                    or work_item.created_date
                    < summary["date_range"]["earliest_created"]
                ):
                    summary["date_range"]["earliest_created"] = work_item.created_date
                if (
                    not summary["date_range"]["latest_created"]
                    or work_item.created_date > summary["date_range"]["latest_created"]
                ):
                    summary["date_range"]["latest_created"] = work_item.created_date

        return summary


# Utility functions for common transformations
def create_transformer_for_scrum() -> WIQLTransformer:
    """Create a transformer configured for Scrum process template."""
    config = TransformationConfig(
        field_mappings={
            "Microsoft.VSTS.Common.Priority": "System.Priority",
            "Microsoft.VSTS.Scheduling.StoryPoints": "System.StoryPoints",
        }
    )
    return WIQLTransformer(config)


def create_transformer_for_agile() -> WIQLTransformer:
    """Create a transformer configured for Agile process template."""
    config = TransformationConfig(
        field_mappings={
            "Microsoft.VSTS.Common.Priority": "System.Priority",
            "Microsoft.VSTS.Scheduling.StoryPoints": "System.StoryPoints",
        }
    )
    return WIQLTransformer(config)


def create_transformer_for_cmmi() -> WIQLTransformer:
    """Create a transformer configured for CMMI process template."""
    config = TransformationConfig(
        field_mappings={
            "Microsoft.VSTS.Common.Priority": "System.Priority",
            "Microsoft.VSTS.Scheduling.Size": "System.Size",
        }
    )
    return WIQLTransformer(config)
