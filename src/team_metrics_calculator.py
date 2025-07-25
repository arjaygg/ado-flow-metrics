"""Team metrics calculation logic extracted from FlowMetricsCalculator."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

from .workstream_manager import WorkstreamManager

logger = logging.getLogger(__name__)


class TeamMetricsCalculator:
    """Handles team-specific metrics calculations."""

    def __init__(
        self,
        parsed_items: List[Dict],
        done_states: Set[str],
        active_states: Set[str],
        config_manager=None,
    ):
        self.parsed_items = parsed_items
        self.done_states = done_states
        self.active_states = active_states
        self.config_manager = config_manager

    def calculate_team_metrics(
        self,
        selected_members: Optional[List[str]] = None,
        workstreams: Optional[List[str]] = None,
    ) -> Dict:
        """Calculate metrics by team member with optional filtering by members or workstreams"""
        logger.info("Starting team metrics calculation...")

        # Apply filtering
        selected_members = self._apply_workstream_filtering(
            workstreams, selected_members
        )

        # Group items by assignee
        assignee_items = self._group_items_by_assignee(selected_members)
        logger.info(f"Found {len(assignee_items)} team members with work assignments")

        # Calculate metrics for each team member
        return self._calculate_member_metrics(assignee_items)

    def _apply_workstream_filtering(
        self, workstreams: Optional[List[str]], selected_members: Optional[List[str]]
    ) -> Optional[List[str]]:
        """Apply workstream filtering to determine selected members."""
        if workstreams:
            logger.info(f"Filtering for workstreams: {workstreams}")
            workstream_manager = WorkstreamManager()

            # Get all members for specified workstreams
            workstream_members = set()
            for item in self.parsed_items:
                assigned_to = item.get("assigned_to", "")
                item_workstream = workstream_manager.get_workstream_for_member(
                    assigned_to
                )
                if item_workstream in workstreams:
                    workstream_members.add(assigned_to)

            selected_members = list(workstream_members)
            logger.info(
                f"Workstream filtering resulted in {len(selected_members)} members: {selected_members}"
            )
        elif selected_members:
            logger.info(
                f"Filtering for {len(selected_members)} selected team members: {selected_members}"
            )

        return selected_members

    def _group_items_by_assignee(
        self, selected_members: Optional[List[str]]
    ) -> Dict[str, List[Dict]]:
        """Group work items by assignee with optional filtering."""
        assignee_items = defaultdict(list)

        for item in self.parsed_items:
            assignee = item["assigned_to"]
            # Apply team member filter if specified
            if selected_members is None or assignee in selected_members:
                assignee_items[assignee].append(item)

        return assignee_items

    def _calculate_member_metrics(self, assignee_items: Dict[str, List[Dict]]) -> Dict:
        """Calculate metrics for each team member."""
        team_metrics = {}

        for idx, (member, items) in enumerate(assignee_items.items()):
            if idx % 10 == 0:  # Log progress every 10 members
                logger.info(
                    f"Processing team member {idx + 1}/{len(assignee_items)}: {member}"
                )

            # Categorize items
            closed_items = self._get_closed_items(items)
            active_items = self._get_active_items(items)

            # Calculate metrics for this member
            member_metrics = self._calculate_individual_member_metrics(
                member, items, closed_items, active_items
            )

            team_metrics[member] = member_metrics

        logger.info(
            f"Team metrics calculation completed for {len(team_metrics)} members"
        )

        return team_metrics

    def _get_closed_items(self, items: List[Dict]) -> List[Dict]:
        """Get items that are in done states."""
        return [item for item in items if item["current_state"] in self.done_states]

    def _get_active_items(self, items: List[Dict]) -> List[Dict]:
        """Get items that are in active states."""
        return [item for item in items if item["current_state"] in self.active_states]

    def _calculate_individual_member_metrics(
        self,
        member: str,
        items: List[Dict],
        closed_items: List[Dict],
        active_items: List[Dict],
    ) -> Dict:
        """Calculate metrics for an individual team member."""
        # Calculate average lead time for closed items with type-aware processing
        avg_lead_time, velocity_items = self._calculate_lead_time_and_velocity(
            closed_items
        )

        return {
            "total_items": len(items),
            "completed_items": len(closed_items),
            "active_items": len(active_items),
            "velocity_items": len(velocity_items),
            "average_lead_time": round(avg_lead_time, 2),
            "completion_rate": (
                round(len(closed_items) / len(items) * 100, 1) if items else 0
            ),
        }

    def _calculate_lead_time_and_velocity(
        self, closed_items: List[Dict]
    ) -> tuple[float, List[Dict]]:
        """Calculate average lead time and identify velocity items."""
        if not closed_items:
            return 0.0, []

        lead_times = []
        velocity_items = []

        for item in closed_items:
            # Look for any completion date field
            completion_date = self._find_completion_date(item)

            if completion_date:
                lead_time = (completion_date - item["created_date"]).days
                item_type = item.get("type", "")

                # Apply complexity multiplier for weighted calculations
                complexity_multiplier = self._get_complexity_multiplier(item_type)
                weighted_lead_time = lead_time * complexity_multiplier

                lead_times.append(lead_time)

                # Track velocity-contributing items
                if self._should_include_in_velocity(item_type):
                    velocity_items.append(item)

        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
        return avg_lead_time, velocity_items

    def _find_completion_date(self, item: Dict) -> Optional[datetime]:
        """Find the completion date for an item."""
        for state in self.done_states:
            state_key = f"{state.lower().replace(' ', '_').replace('-', '_')}_date"
            if state_key in item:
                return item[state_key]
        return None

    def _should_include_in_velocity(self, work_item_type: str) -> bool:
        """Check if work item type should be included in velocity calculations."""
        if not self.config_manager:
            return True  # Default to include if configuration is unavailable

        try:
            return self.config_manager.should_include_in_velocity(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not check velocity inclusion for {work_item_type}: {e}"
            )
            return True  # Default to include if configuration is unavailable

    def _get_complexity_multiplier(self, work_item_type: str) -> float:
        """Get complexity multiplier for work item type."""
        if not self.config_manager:
            return 1.0  # Default multiplier

        try:
            return self.config_manager.get_type_complexity_multiplier(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not get complexity multiplier for {work_item_type}: {e}"
            )
            return 1.0  # Default multiplier
