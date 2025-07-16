"""Cycle Time calculation for Flow Metrics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CycleTimeCalculator:
    """Calculate cycle time metrics for work items."""

    def __init__(self, work_items: List[Dict], active_states: set, done_states: set):
        self.work_items = work_items
        self.active_states = active_states
        self.done_states = done_states

    def calculate_cycle_time(self) -> Dict:
        """Calculate cycle time (active to closed)"""
        closed_items = self._get_closed_items_with_active_dates()

        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}

        cycle_times = self._calculate_cycle_times(closed_items)

        if not cycle_times:
            return {"average_days": 0, "median_days": 0, "count": 0}

        return self._generate_cycle_time_metrics(cycle_times)

    def _get_closed_items_with_active_dates(self) -> List[Dict]:
        """Get items that are closed and have active dates."""
        closed_items = []

        for item in self.work_items:
            if item["current_state"] in self.done_states:
                active_date = self._find_active_date(item)
                completion_date = self._find_completion_date(item)

                if completion_date and active_date:
                    item["_completion_date"] = completion_date
                    item["_active_date"] = active_date
                    closed_items.append(item)

        return closed_items

    def _find_active_date(self, item: Dict) -> Optional[datetime]:
        """Find the active start date for an item using multiple strategies."""
        # Strategy 1: Look for exact state name matches
        for state in self.active_states:
            state_key = f"{state.lower().replace(' ', '_').replace('-', '_')}_date"
            if state_key in item:
                return item[state_key]

        # Strategy 2: Look for common active date field patterns
        active_patterns = [
            "active_date",
            "in_progress_date",
            "started_date",
            "development_date",
            "2_2___in_progress_date",
            "2_1___ready_for_development_date",
        ]

        for pattern in active_patterns:
            if pattern in item:
                return item[pattern]

        # Strategy 3: Look for any date field that contains active state keywords
        for field_name, field_value in item.items():
            if field_name.endswith("_date") and isinstance(field_value, datetime):
                for state in self.active_states:
                    state_clean = state.lower().replace(" ", "_").replace("-", "_")
                    if state_clean in field_name.lower():
                        return field_value

        # Strategy 4: If no active date found, fall back to created date + 1 day
        if "created_date" in item:
            return item["created_date"] + timedelta(days=1)

        return None

    def _find_completion_date(self, item: Dict) -> Optional[datetime]:
        """Find the completion date for an item."""
        # Strategy 1: Look for exact state name matches
        for state in self.done_states:
            state_key = f"{state.lower().replace(' ', '_').replace('-', '_')}_date"
            if state_key in item:
                return item[state_key]

        # Strategy 2: Look for common done date field patterns
        done_patterns = [
            "done_date",
            "closed_date",
            "completed_date",
            "resolved_date",
            "released_date",
            "finished_date",
        ]

        for pattern in done_patterns:
            if pattern in item:
                return item[pattern]

        return None

    def _calculate_cycle_times(self, closed_items: List[Dict]) -> List[float]:
        """Calculate cycle times for closed items."""
        cycle_times = []

        for item in closed_items:
            if "_completion_date" in item and "_active_date" in item:
                cycle_time = (item["_completion_date"] - item["_active_date"]).days
                if cycle_time >= 0:  # Sanity check
                    cycle_times.append(cycle_time)

        return cycle_times

    def _generate_cycle_time_metrics(self, cycle_times: List[float]) -> Dict:
        """Generate comprehensive cycle time metrics."""
        cycle_times.sort()

        return {
            "average_days": round(sum(cycle_times) / len(cycle_times), 2),
            "median_days": cycle_times[len(cycle_times) // 2],
            "min_days": min(cycle_times),
            "max_days": max(cycle_times),
            "count": len(cycle_times),
            "percentile_85": cycle_times[int(len(cycle_times) * 0.85)]
            if cycle_times
            else 0,
            "percentile_95": cycle_times[int(len(cycle_times) * 0.95)]
            if cycle_times
            else 0,
        }
