import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from .workstream_manager import WorkstreamManager

logger = logging.getLogger(__name__)


class FlowMetricsCalculator:
    def __init__(self, work_items_data: List[Dict], config: Union[Dict, object] = None):
        logger.info(f"Initializing calculator with {len(work_items_data)} work items.")
        self.work_items = work_items_data
        self.config = self._normalize_config(config)

        # Extract state configuration in order of preference:
        # 1. flow_metrics.active_states and flow_metrics.done_states (simple approach)
        # 2. stage_metadata (complex approach)
        # 3. hardcoded defaults

        self.active_states = set()
        self.done_states = set()

        # Try simple flow_metrics configuration first
        flow_metrics_config = self.config.get("flow_metrics", {})
        if isinstance(flow_metrics_config, dict):
            if "active_states" in flow_metrics_config:
                self.active_states = set(flow_metrics_config["active_states"])
            if "done_states" in flow_metrics_config:
                self.done_states = set(flow_metrics_config["done_states"])

        # If not found, try stage_metadata approach
        if not self.active_states or not self.done_states:
            stage_config = self.config.get("stage_metadata", [])
            if stage_config:
                if not self.active_states:
                    self.active_states = {
                        s.get("stage_name") for s in stage_config if s.get("is_active")
                    }
                if not self.done_states:
                    self.done_states = {
                        s.get("stage_name") for s in stage_config if s.get("is_done")
                    }

        # Final fallback to reasonable defaults
        if not self.active_states:
            self.active_states = {"In Progress", "Active", "Development", "Testing"}
            logger.warning(
                "No active states configured. Using defaults: %s", self.active_states
            )

        if not self.done_states:
            self.done_states = {"Done", "Closed", "Completed", "Released"}
            logger.warning(
                "No done states configured. Using defaults: %s", self.done_states
            )

        logger.info(
            f"Configured with {len(self.active_states)} active states and "
            f"{len(self.done_states)} done states."
        )
        logger.debug(f"Active states: {self.active_states}")
        logger.debug(f"Done states: {self.done_states}")

        self.parsed_items = self._parse_work_items()

    def _normalize_config(self, config: Union[Dict, object]) -> Dict:
        """Convert config to dictionary format, handling Pydantic models."""
        if config is None:
            return {}

        # If it's already a dictionary, return as-is
        if isinstance(config, dict):
            return config

        # If it's a Pydantic model, use model_dump()
        if hasattr(config, "model_dump"):
            try:
                return config.model_dump()
            except Exception as e:
                logger.warning(f"Failed to convert Pydantic model to dict: {e}")
                return {}

        # If it has a dict() method (older Pydantic versions)
        if hasattr(config, "dict"):
            try:
                return config.dict()
            except Exception as e:
                logger.warning(f"Failed to convert config to dict: {e}")
                return {}

        # Try to convert to dict using vars()
        try:
            return vars(config)
        except Exception as e:
            logger.warning(f"Could not convert config object to dict: {e}")
            return {}

    def _parse_work_items(self) -> List[Dict]:
        """Parse work items and add calculated fields"""
        logger.debug("Starting work item parsing.")
        parsed_items = []
        total_items = len(self.work_items)

        for idx, item in enumerate(self.work_items):
            if idx % 50 == 0:  # Log progress every 50 items
                logger.info(f"Processing work item {idx + 1}/{total_items}")

            try:
                parsed_item = {
                    "id": item["id"],
                    "title": item["title"],
                    "type": item["type"],
                    "priority": item["priority"],
                    "created_date": datetime.fromisoformat(item["created_date"]),
                    "created_by": item["created_by"],
                    "assigned_to": item["assigned_to"],
                    "current_state": item["current_state"],
                    "story_points": item.get("story_points"),
                    "effort_hours": item.get("effort_hours"),
                    "tags": item.get("tags", []),
                }

                # Add state transition dates
                transitions = item.get("state_transitions", [])
                for trans in transitions:
                    try:
                        # Handle both 'to_state' (new format) and 'state' (legacy)
                        state = trans.get("to_state") or trans.get("state")
                        # Handle both 'transition_date' (new) and 'date' (legacy)
                        date_str = trans.get("transition_date") or trans.get("date")

                        if state and date_str:
                            # Clean state name for use as field key
                            state_clean = (
                                state.lower()
                                .replace(" ", "_")
                                .replace("-", "_")
                                .replace(".", "_")
                            )
                            # Remove multiple underscores and strip
                            state_clean = "_".join(
                                [part for part in state_clean.split("_") if part]
                            )
                            state_key = f"{state_clean}_date"
                            parsed_item[state_key] = datetime.fromisoformat(date_str)
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse transition date for "
                            f"item {item['id']}: {e}"
                        )
                        continue

                parsed_items.append(parsed_item)

            except Exception as e:
                logger.error(
                    f"Failed to parse work item {item.get('id', 'unknown')}: {e}"
                )
                continue

        logger.debug(
            f"Finished parsing. {len(parsed_items)} items are usable for calculations."
        )
        return parsed_items

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
                # Check if this field corresponds to a done state
                for state in self.done_states:
                    state_clean = state.lower().replace(" ", "_").replace("-", "_")
                    if state_clean in field_name.lower():
                        return field_value

        return None

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
                # Check if this field corresponds to an active state
                for state in self.active_states:
                    state_clean = state.lower().replace(" ", "_").replace("-", "_")
                    if state_clean in field_name.lower():
                        return field_value

        # Strategy 4: If no active date found, fall back to created date + 1 day
        # This provides a reasonable estimate for cycle time calculation
        if "created_date" in item:
            return item["created_date"] + timedelta(days=1)

        return None

    def calculate_lead_time(self) -> Dict:
        """Calculate lead time (created to closed)"""
        # Find completed items with any done state date field
        closed_items = []
        for item in self.parsed_items:
            if item["current_state"] in self.done_states:
                # Look for any done state date field using multiple strategies
                completion_date = self._find_completion_date(item)
                if completion_date:
                    item["_completion_date"] = completion_date
                    closed_items.append(item)

        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}

        lead_times = []
        for item in closed_items:
            if "_completion_date" in item:
                lead_time = (item["_completion_date"] - item["created_date"]).days
                lead_times.append(lead_time)

        if not lead_times:
            return {"average_days": 0, "median_days": 0, "count": 0}

        lead_times.sort()
        return {
            "average_days": round(sum(lead_times) / len(lead_times), 2),
            "median_days": lead_times[len(lead_times) // 2],
            "min_days": min(lead_times),
            "max_days": max(lead_times),
            "count": len(lead_times),
        }

    def calculate_cycle_time(self) -> Dict:
        """Calculate cycle time (active to closed)"""
        # Find completed items with active date and any done state date field
        closed_items = []
        for item in self.parsed_items:
            if item["current_state"] in self.done_states:
                # Look for active start date using multiple strategies
                active_date = self._find_active_date(item)
                # Look for completion date
                completion_date = self._find_completion_date(item)

                if completion_date and active_date:
                    item["_completion_date"] = completion_date
                    item["_active_date"] = active_date
                    closed_items.append(item)

        if not closed_items:
            return {"average_days": 0, "median_days": 0, "count": 0}

        cycle_times = []
        for item in closed_items:
            if "_completion_date" in item and "_active_date" in item:
                cycle_time = (item["_completion_date"] - item["_active_date"]).days
                cycle_times.append(cycle_time)

        if not cycle_times:
            return {"average_days": 0, "median_days": 0, "count": 0}

        cycle_times.sort()
        return {
            "average_days": round(sum(cycle_times) / len(cycle_times), 2),
            "median_days": cycle_times[len(cycle_times) // 2],
            "min_days": min(cycle_times),
            "max_days": max(cycle_times),
            "count": len(cycle_times),
        }

    def calculate_throughput(self, period_days: int = 30) -> Dict:
        """Calculate throughput (items completed per period)"""
        # Find completed items with any done state date field
        closed_items = []
        for item in self.parsed_items:
            if item["current_state"] in self.done_states:
                # Look for any done state date field
                done_date_field = None
                for state in self.done_states:
                    state_key = f"{state.lower().replace(' ', '_')}_date"
                    if state_key in item:
                        done_date_field = state_key
                        break
                if done_date_field:
                    item["_completion_date"] = item[done_date_field]
                    closed_items.append(item)

        if not closed_items:
            return {"items_per_period": 0, "period_days": period_days}

        # Get date range
        closed_dates = [item["_completion_date"] for item in closed_items]
        start_date = min(closed_dates)
        end_date = max(closed_dates)
        total_days = (end_date - start_date).days

        if total_days == 0:
            return {"items_per_period": len(closed_items), "period_days": period_days}

        # Calculate throughput
        items_per_day = len(closed_items) / total_days
        items_per_period = items_per_day * period_days

        return {
            "items_per_period": round(items_per_period, 2),
            "period_days": period_days,
            "total_completed": len(closed_items),
            "analysis_period_days": total_days,
        }

    def calculate_wip(self) -> Dict:
        """Calculate current Work in Progress"""
        wip_items = [
            item
            for item in self.parsed_items
            if item["current_state"] in self.active_states
        ]

        wip_by_state = defaultdict(int)
        wip_by_assignee = defaultdict(int)

        for item in wip_items:
            wip_by_state[item["current_state"]] += 1
            wip_by_assignee[item["assigned_to"]] += 1

        return {
            "total_wip": len(wip_items),
            "wip_by_state": dict(wip_by_state),
            "wip_by_assignee": dict(wip_by_assignee),
        }

    def calculate_flow_efficiency(self) -> Dict:
        """Calculate flow efficiency (active time / total lead time)"""
        closed_items = []
        for item in self.parsed_items:
            if item["current_state"] in self.done_states:
                active_date = self._find_active_date(item)
                completion_date = self._find_completion_date(item)
                if active_date and completion_date:
                    item["_active_date"] = active_date
                    item["_completion_date"] = completion_date
                    closed_items.append(item)

        if not closed_items:
            return {"average_efficiency": 0, "count": 0}

        efficiencies = []
        for item in closed_items:
            # For flow efficiency, we need to calculate active time vs total time
            # Active time: time spent in active states
            # Total time: lead time (created to completed)
            active_time = (item["_completion_date"] - item["_active_date"]).days
            total_lead_time = (item["_completion_date"] - item["created_date"]).days

            if total_lead_time > 0 and active_time >= 0:
                efficiency = active_time / total_lead_time
                efficiencies.append(efficiency)

        if not efficiencies:
            return {"average_efficiency": 0, "count": 0}

        efficiencies.sort()
        return {
            "average_efficiency": round(sum(efficiencies) / len(efficiencies), 3),
            "median_efficiency": round(efficiencies[len(efficiencies) // 2], 3),
            "count": len(efficiencies),
        }

    def calculate_team_metrics(
        self,
        selected_members: Optional[List[str]] = None,
        workstreams: Optional[List[str]] = None,
    ) -> Dict:
        """Calculate metrics by team member with optional filtering by members or workstreams"""
        logger.info("Starting team metrics calculation...")

        # Handle workstream filtering
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
        team_metrics = {}

        # Group items by assignee with optional filtering
        assignee_items = defaultdict(list)
        for item in self.parsed_items:
            assignee = item["assigned_to"]
            # Apply team member filter if specified
            if selected_members is None or assignee in selected_members:
                assignee_items[assignee].append(item)

        logger.info(f"Found {len(assignee_items)} team members with work assignments")

        for idx, (member, items) in enumerate(assignee_items.items()):
            if idx % 10 == 0:  # Log progress every 10 members
                logger.info(
                    f"Processing team member {idx + 1}/{len(assignee_items)}: {member}"
                )

            closed_items = [
                item for item in items if item["current_state"] in self.done_states
            ]
            active_items = [
                item for item in items if item["current_state"] in self.active_states
            ]

            # Calculate average lead time for closed items
            if closed_items:
                lead_times = []
                for item in closed_items:
                    # Look for any completion date field
                    completion_date = None
                    for state in self.done_states:
                        state_key = f"{state.lower().replace(' ', '_')}_date"
                        if state_key in item:
                            completion_date = item[state_key]
                            break

                    if completion_date:
                        lead_time = (completion_date - item["created_date"]).days
                        lead_times.append(lead_time)

                avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            else:
                avg_lead_time = 0

            team_metrics[member] = {
                "total_items": len(items),
                "completed_items": len(closed_items),
                "active_items": len(active_items),
                "average_lead_time": round(avg_lead_time, 2),
                "completion_rate": (
                    round(len(closed_items) / len(items) * 100, 1) if items else 0
                ),
            }

        logger.info(
            f"Team metrics calculation completed for {len(team_metrics)} members"
        )

        return team_metrics

    def calculate_littles_law_validation(self) -> Dict:
        """Calculate Little's Law validation metrics"""
        wip_metrics = self.calculate_wip()
        throughput_metrics = self.calculate_throughput()
        cycle_time_metrics = self.calculate_cycle_time()

        if wip_metrics["total_wip"] > 0 and throughput_metrics["items_per_period"] > 0:
            throughput_rate = (
                throughput_metrics["items_per_period"]
                / throughput_metrics["period_days"]
            )
            calculated_cycle_time = (
                wip_metrics["total_wip"] / throughput_rate if throughput_rate > 0 else 0
            )

            variance_percentage = 0
            if cycle_time_metrics["average_days"] > 0:
                variance_percentage = (
                    (calculated_cycle_time - cycle_time_metrics["average_days"])
                    / cycle_time_metrics["average_days"]
                ) * 100

            # Determine interpretation
            if abs(calculated_cycle_time - cycle_time_metrics["average_days"]) <= (
                cycle_time_metrics["average_days"] * 0.2
            ):
                interpretation = "Good alignment - system in steady state"
            elif calculated_cycle_time > cycle_time_metrics["average_days"]:
                interpretation = "Higher than measured - possible WIP accumulation"
            else:
                interpretation = (
                    "Lower than measured - possible batch processing or delays"
                )

            return {
                "theoretical_cycle_time": round(calculated_cycle_time, 2),
                "measured_cycle_time": cycle_time_metrics["average_days"],
                "variance_percentage": round(variance_percentage, 1),
                "throughput_rate_per_day": round(throughput_rate, 2),
                "interpretation": interpretation,
            }

        logger.info("No Little's Law validation calculated.")
        return {}

    def generate_flow_metrics_report(self) -> Dict:
        """Generate comprehensive flow metrics report compatible with dashboard"""
        logger.info("Generating full flow metrics report.")
        logger.info(f"Working with {len(self.parsed_items)} parsed items")
        completed_count = len(
            [
                item
                for item in self.parsed_items
                if item["current_state"] in self.done_states
            ]
        )
        logger.info(f"Found {completed_count} completed items")

        # Build report in exact PowerShell format
        report = {
            "summary": {
                "total_work_items": len(self.parsed_items),
                "completed_items": completed_count,
                "completion_rate": (
                    round(completed_count / len(self.parsed_items) * 100, 1)
                    if self.parsed_items
                    else 0
                ),
            }
        }

        logger.info("Calculating lead time...")
        report["lead_time"] = self.calculate_lead_time()

        logger.info("Calculating cycle time...")
        report["cycle_time"] = self.calculate_cycle_time()

        logger.info("Calculating throughput...")
        report["throughput"] = self.calculate_throughput()

        logger.info("Calculating work in progress...")
        report["work_in_progress"] = self.calculate_wip()

        logger.info("Calculating flow efficiency...")
        report["flow_efficiency"] = self.calculate_flow_efficiency()

        logger.info("Calculating Little's Law validation...")
        report["littles_law_validation"] = self.calculate_littles_law_validation()

        logger.info("Calculating team metrics...")
        report["team_metrics"] = self.calculate_team_metrics()

        # Add remaining static sections
        report["trend_analysis"] = {}
        report["bottlenecks"] = {"state_transitions": {}}
        report["cycle_time_distribution"] = {}

        logger.info("Flow metrics report generation completed.")

        return report


def main():
    # Load mock data
    with open("mock_azure_devops_workitems.json", "r") as f:
        work_items = json.load(f)

    # Calculate metrics
    calculator = FlowMetricsCalculator(work_items)
    metrics = calculator.generate_flow_metrics_report()

    # Save metrics report
    with open("flow_metrics_report.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("Flow Metrics Report Generated")
    print(f"Total Work Items: {metrics['summary']['total_work_items']}")
    print(f"Completed Items: {metrics['summary']['completed_items']}")
    print(f"Completion Rate: {metrics['summary']['completion_rate']}%")
    print(f"Average Lead Time: {metrics['lead_time']['average_days']} days")
    print(f"Average Cycle Time: {metrics['cycle_time']['average_days']} days")
    print(f"Current WIP: {metrics['work_in_progress']['total_wip']} items")
    print(f"Flow Efficiency: {metrics['flow_efficiency']['average_efficiency']:.1%}")


if __name__ == "__main__":
    main()
