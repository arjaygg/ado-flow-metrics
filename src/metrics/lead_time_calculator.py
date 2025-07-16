"""Lead Time calculation for Flow Metrics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LeadTimeCalculator:
    """Calculate lead time metrics for work items."""

    def __init__(self, work_items: List[Dict], done_states: set):
        self.work_items = work_items
        self.done_states = done_states

    def calculate_lead_time(self) -> Dict:
        """Calculate lead time (created to closed)"""
        closed_items = self._get_closed_items()

        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}

        lead_times = self._calculate_lead_times(closed_items)

        if not lead_times:
            return {"average_days": 0, "median_days": 0, "count": 0}

        return self._generate_lead_time_metrics(lead_times)

    def _get_closed_items(self) -> List[Dict]:
        """Get items that are in done states with completion dates."""
        closed_items = []

        for item in self.work_items:
            if item["current_state"] in self.done_states:
                completion_date = self._find_completion_date(item)
                if completion_date:
                    item["_completion_date"] = completion_date
                    closed_items.append(item)

        return closed_items

    def _find_completion_date(self, item: Dict) -> Optional[datetime]:
        """Find the completion date for an item using multiple strategies."""
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
            "5___done_date",
            "qa_approved_date",
        ]

        for pattern in done_patterns:
            if pattern in item:
                return item[pattern]

        # Strategy 3: Look for any date field that contains done state keywords
        for field_name, field_value in item.items():
            if field_name.endswith("_date") and isinstance(field_value, datetime):
                for state in self.done_states:
                    state_clean = state.lower().replace(" ", "_").replace("-", "_")
                    if state_clean in field_name.lower():
                        return field_value

        return None

    def _calculate_lead_times(self, closed_items: List[Dict]) -> List[float]:
        """Calculate lead times for closed items."""
        lead_times = []

        for item in closed_items:
            if "_completion_date" in item:
                lead_time = (item["_completion_date"] - item["created_date"]).days
                if lead_time >= 0:  # Sanity check
                    lead_times.append(lead_time)

        return lead_times

    def _generate_lead_time_metrics(self, lead_times: List[float]) -> Dict:
        """Generate comprehensive lead time metrics."""
        lead_times.sort()

        return {
            "average_days": round(sum(lead_times) / len(lead_times), 2),
            "median_days": lead_times[len(lead_times) // 2],
            "min_days": min(lead_times),
            "max_days": max(lead_times),
            "count": len(lead_times),
            "percentile_85": lead_times[int(len(lead_times) * 0.85)]
            if lead_times
            else 0,
            "percentile_95": lead_times[int(len(lead_times) * 0.95)]
            if lead_times
            else 0,
        }
