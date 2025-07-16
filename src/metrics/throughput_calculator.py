"""Throughput calculation for Flow Metrics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ThroughputCalculator:
    """Calculate throughput metrics for work items."""

    def __init__(self, work_items: List[Dict], done_states: set, config_manager=None):
        self.work_items = work_items
        self.done_states = done_states
        self.config_manager = config_manager

    def calculate_throughput(self, period_days: Optional[int] = None) -> Dict:
        """Calculate throughput (items completed per period)"""
        if period_days is None:
            period_days = self._get_default_period_days()

        closed_items = self._get_closed_items_with_dates()

        if not closed_items:
            return {"items_per_period": 0, "period_days": period_days}

        return self._calculate_throughput_metrics(closed_items, period_days)

    def _get_default_period_days(self) -> int:
        """Get default period days from configuration."""
        if self.config_manager:
            try:
                throughput_config = self.config_manager.get_throughput_config()
                return throughput_config.get("default_period_days", 30)
            except Exception as e:
                logger.debug(f"Could not get throughput config: {e}")

        return 30  # Default fallback

    def _get_closed_items_with_dates(self) -> List[Dict]:
        """Get completed items with completion dates."""
        closed_items = []

        for item in self.work_items:
            if item["current_state"] in self.done_states:
                # Apply work item type filtering if configured
                if self._should_include_in_throughput(item.get("type", "")):
                    completion_date = self._find_completion_date(item)
                    if completion_date:
                        item["_completion_date"] = completion_date
                        closed_items.append(item)

        return closed_items

    def _should_include_in_throughput(self, work_item_type: str) -> bool:
        """Check if work item type should be included in throughput calculations."""
        if self.config_manager:
            try:
                return self.config_manager.should_include_in_throughput(work_item_type)
            except Exception as e:
                logger.debug(
                    f"Could not check throughput inclusion for {work_item_type}: {e}"
                )

        return True  # Default to include if configuration is unavailable

    def _find_completion_date(self, item: Dict) -> Optional[datetime]:
        """Find completion date for an item."""
        # Look for exact state name matches
        for state in self.done_states:
            state_key = f"{state.lower().replace(' ', '_').replace('-', '_')}_date"
            if state_key in item:
                return item[state_key]

        # Look for common done date field patterns
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

    def _calculate_throughput_metrics(
        self, closed_items: List[Dict], period_days: int
    ) -> Dict:
        """Calculate throughput metrics from closed items."""
        closed_dates = [item["_completion_date"] for item in closed_items]
        start_date = min(closed_dates)
        end_date = max(closed_dates)
        total_days = (end_date - start_date).days

        if total_days == 0:
            return {
                "items_per_period": len(closed_items),
                "period_days": period_days,
                "total_completed": len(closed_items),
                "analysis_period_days": total_days,
            }

        # Calculate throughput
        items_per_day = len(closed_items) / total_days
        items_per_period = items_per_day * period_days

        return {
            "items_per_period": round(items_per_period, 2),
            "period_days": period_days,
            "total_completed": len(closed_items),
            "analysis_period_days": total_days,
            "items_per_day": round(items_per_day, 3),
            "items_per_week": round(items_per_day * 7, 2),
            "items_per_month": round(items_per_day * 30, 2),
        }
