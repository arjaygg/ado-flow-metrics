import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .configuration_manager import ConfigurationManager, get_config_manager
from .metrics import CycleTimeCalculator, LeadTimeCalculator, ThroughputCalculator
from .workstream_manager import WorkstreamManager

logger = logging.getLogger(__name__)


class FlowMetricsCalculator:
    def __init__(
        self,
        work_items_data: List[Dict],
        config: Union[Dict, object] = None,
        config_manager: Optional[ConfigurationManager] = None,
    ):
        logger.info(f"Initializing calculator with {len(work_items_data)} work items.")
        self.work_items = work_items_data
        self.config = self._normalize_config(config)

        # Initialize configuration manager
        self.config_manager = (
            config_manager if config_manager is not None else get_config_manager()
        )

        # Extract state configuration using ConfigurationManager with fallbacks
        self.active_states = set()
        self.done_states = set()
        self.blocked_states = set()

        try:
            # Get workflow states from configuration manager
            workflow_config = self.config_manager.get_workflow_states()

            if workflow_config:
                # Use the new configuration structure
                self.active_states = self._extract_active_states_from_config(
                    workflow_config
                )
                self.done_states = self._extract_completion_states_from_config(
                    workflow_config
                )
                self.blocked_states = self._extract_blocked_states_from_config(
                    workflow_config
                )

                logger.info("Using ConfigurationManager for workflow states")
            else:
                logger.warning(
                    "ConfigurationManager workflow states not available, falling back to legacy config"
                )
                self._configure_states_from_legacy_config()

        except Exception as e:
            logger.error(
                f"Error loading workflow states from ConfigurationManager: {e}"
            )
            logger.warning("Falling back to legacy configuration approach")
            self._configure_states_from_legacy_config()

        # Load calculation parameters
        try:
            self.calc_params = self.config_manager.get_calculation_parameters()
            logger.info("Loaded calculation parameters from ConfigurationManager")
        except Exception as e:
            logger.warning(
                f"Could not load calculation parameters: {e}. Using defaults."
            )
            self.calc_params = {}

        logger.info(
            f"Configured with {len(self.active_states)} active states, "
            f"{len(self.done_states)} done states, and {len(self.blocked_states)} blocked states."
        )
        logger.debug(f"Active states: {self.active_states}")
        logger.debug(f"Done states: {self.done_states}")
        logger.debug(f"Blocked states: {self.blocked_states}")

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
        calculator = LeadTimeCalculator(self.parsed_items, self.done_states)
        return calculator.calculate_lead_time()

    def calculate_cycle_time(self) -> Dict:
        """Calculate cycle time (active to closed)"""
        calculator = CycleTimeCalculator(
            self.parsed_items, self.active_states, self.done_states
        )
        return calculator.calculate_cycle_time()

    def calculate_throughput(self, period_days: Optional[int] = None) -> Dict:
        """Calculate throughput (items completed per period)"""
        calculator = ThroughputCalculator(
            self.parsed_items, self.done_states, self.config_manager
        )
        return calculator.calculate_throughput(period_days)

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

            # Calculate average lead time for closed items with type-aware processing
            if closed_items:
                lead_times = []
                velocity_items = []
                for item in closed_items:
                    # Look for any completion date field
                    completion_date = None
                    for state in self.done_states:
                        state_key = (
                            f"{state.lower().replace(' ', '_').replace('-', '_')}_date"
                        )
                        if state_key in item:
                            completion_date = item[state_key]
                            break

                    if completion_date:
                        lead_time = (completion_date - item["created_date"]).days
                        item_type = item.get("type", "")

                        # Apply complexity multiplier for weighted calculations
                        complexity_multiplier = self._get_complexity_multiplier(
                            item_type
                        )
                        weighted_lead_time = lead_time * complexity_multiplier

                        lead_times.append(lead_time)

                        # Track velocity-contributing items
                        if self._should_include_in_velocity(item_type):
                            velocity_items.append(item)

                avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
            else:
                avg_lead_time = 0
                velocity_items = []

            team_metrics[member] = {
                "total_items": len(items),
                "completed_items": len(closed_items),
                "active_items": len(active_items),
                "velocity_items": len(velocity_items),
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

        # Build report in exact PowerShell format with configuration enhancements
        report = {
            "summary": {
                "total_work_items": len(self.parsed_items),
                "completed_items": completed_count,
                "completion_rate": (
                    round(completed_count / len(self.parsed_items) * 100, 1)
                    if self.parsed_items
                    else 0
                ),
                "configuration_summary": self._get_configuration_summary(),
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

        # Add historical data for dashboard charts
        logger.info("Preparing historical data for dashboard charts...")
        report["historical_data"] = self._prepare_historical_data()

        logger.info("Flow metrics report generation completed.")

        return report

    def _prepare_historical_data(self) -> List[Dict]:
        """Prepare historical data for dashboard charts"""
        historical_data = []

        for item in self.parsed_items:
            # Only include completed items with resolution dates
            if item["current_state"] in self.done_states:
                # Find the resolution date
                resolved_date = None
                for state in self.done_states:
                    state_key = f"{state.lower().replace(' ', '_')}_date"
                    if state_key in item:
                        resolved_date = (
                            item[state_key].isoformat()
                            if hasattr(item[state_key], "isoformat")
                            else str(item[state_key])
                        )
                        break

                if resolved_date:
                    # Calculate lead time and cycle time for this item
                    lead_time = self._calculate_item_lead_time(item)
                    cycle_time = self._calculate_item_cycle_time(item)

                    historical_data.append(
                        {
                            "id": item.get("id", ""),
                            "title": item.get("title", ""),
                            "type": item.get("type", ""),
                            "assignee": item.get("assignee", ""),
                            "resolvedDate": resolved_date,
                            "leadTime": lead_time,
                            "cycleTime": cycle_time,
                            "state": item.get("current_state", ""),
                        }
                    )

        return historical_data

    def _calculate_item_lead_time(self, item: Dict) -> float:
        """Calculate lead time for a single item"""
        created_date = item.get("created_date")
        if not created_date:
            return 0

        # Find completion date
        completion_date = None
        for state in self.done_states:
            state_key = f"{state.lower().replace(' ', '_')}_date"
            if state_key in item:
                completion_date = item[state_key]
                break

        if completion_date and created_date:
            delta = completion_date - created_date
            return round(delta.days + delta.seconds / 86400, 2)

        return 0

    def _calculate_item_cycle_time(self, item: Dict) -> float:
        """Calculate cycle time for a single item"""
        # Find first active state date
        start_date = None
        for state in self.active_states:
            state_key = f"{state.lower().replace(' ', '_')}_date"
            if state_key in item:
                start_date = item[state_key]
                break

        # If no active state date, use created date
        if not start_date:
            start_date = item.get("created_date")

        # Find completion date
        completion_date = None
        for state in self.done_states:
            state_key = f"{state.lower().replace(' ', '_')}_date"
            if state_key in item:
                completion_date = item[state_key]
                break

        if completion_date and start_date:
            delta = completion_date - start_date
            return round(delta.days + delta.seconds / 86400, 2)

        return 0

    def _extract_active_states_from_config(self, workflow_config: Dict) -> set:
        """Extract active states from workflow configuration."""
        active_states = set()

        # Check for stateMappings.flowCalculations.activeStates first
        flow_calc = workflow_config.get("stateMappings", {}).get("flowCalculations", {})
        if "activeStates" in flow_calc:
            active_states.update(flow_calc["activeStates"])

        # Also include states from categories marked as active
        state_categories = workflow_config.get("stateCategories", {})
        for category_name, category_data in state_categories.items():
            if category_data.get("isActive", False) and not category_data.get(
                "isCompletedState", False
            ):
                states = category_data.get("states", [])
                active_states.update(states)

        # Fallback: if no active states found, try to get from specific active categories
        if not active_states:
            # Extract from categories that represent work in progress
            active_category_names = [
                "development_ready",
                "development_active",
                "testing",
                "testing_approved",
                "release_ready",
                "requirements",
            ]
            for category_name in active_category_names:
                if category_name in state_categories:
                    category_data = state_categories[category_name]
                    if category_data.get(
                        "isActive", True
                    ):  # Default to True for these categories
                        states = category_data.get("states", [])
                        active_states.update(states)

        return active_states

    def _extract_completion_states_from_config(self, workflow_config: Dict) -> set:
        """Extract completion states from workflow configuration."""
        completion_states = set()

        # Check for stateMappings.normalized.done_states first
        normalized = workflow_config.get("stateMappings", {}).get("normalized", {})
        if "done_states" in normalized:
            completion_states.update(normalized["done_states"])

        # Also include states from categories marked as completed
        state_categories = workflow_config.get("stateCategories", {})
        for category_name, category_data in state_categories.items():
            if category_data.get("isCompletedState", False):
                states = category_data.get("states", [])
                completion_states.update(states)

        return completion_states

    def _extract_blocked_states_from_config(self, workflow_config: Dict) -> set:
        """Extract blocked states from workflow configuration."""
        blocked_states = set()

        # Check for stateMappings.normalized.blocked_states first
        normalized = workflow_config.get("stateMappings", {}).get("normalized", {})
        if "blocked_states" in normalized:
            blocked_states.update(normalized["blocked_states"])

        # Also include states from categories marked as blocked
        state_categories = workflow_config.get("stateCategories", {})
        for category_name, category_data in state_categories.items():
            if category_data.get("isBlockedState", False):
                states = category_data.get("states", [])
                blocked_states.update(states)

        return blocked_states

    def _configure_states_from_legacy_config(self):
        """Configure states using legacy configuration approach."""
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

    def _should_include_in_throughput(self, work_item_type: str) -> bool:
        """Check if work item type should be included in throughput calculations."""
        try:
            return self.config_manager.should_include_in_throughput(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not check throughput inclusion for {work_item_type}: {e}"
            )
            return True  # Default to include if configuration is unavailable

    def _should_include_in_velocity(self, work_item_type: str) -> bool:
        """Check if work item type should be included in velocity calculations."""
        try:
            return self.config_manager.should_include_in_velocity(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not check velocity inclusion for {work_item_type}: {e}"
            )
            return True  # Default to include if configuration is unavailable

    def _get_complexity_multiplier(self, work_item_type: str) -> float:
        """Get complexity multiplier for work item type."""
        try:
            return self.config_manager.get_type_complexity_multiplier(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not get complexity multiplier for {work_item_type}: {e}"
            )
            return 1.0  # Default multiplier

    def _get_lead_time_thresholds(self, work_item_type: str) -> Dict[str, int]:
        """Get lead time thresholds for work item type."""
        try:
            return self.config_manager.get_lead_time_threshold(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not get lead time thresholds for {work_item_type}: {e}"
            )
            return {"target_days": 14, "warning_days": 21, "critical_days": 30}

    def _get_cycle_time_thresholds(self, work_item_type: str) -> Dict[str, int]:
        """Get cycle time thresholds for work item type."""
        try:
            return self.config_manager.get_cycle_time_threshold(work_item_type)
        except Exception as e:
            logger.debug(
                f"Could not get cycle time thresholds for {work_item_type}: {e}"
            )
            return {"target_days": 7, "warning_days": 14, "critical_days": 21}

    def _get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration for reporting."""
        try:
            config_summary = self.config_manager.get_configuration_summary()
            config_summary["states_configured"] = {
                "active_states_count": len(self.active_states),
                "done_states_count": len(self.done_states),
                "blocked_states_count": len(self.blocked_states),
            }
            return config_summary
        except Exception as e:
            logger.debug(f"Could not get configuration summary: {e}")
            return {
                "states_configured": {
                    "active_states_count": len(self.active_states),
                    "done_states_count": len(self.done_states),
                    "blocked_states_count": len(self.blocked_states),
                },
                "configuration_manager_available": False,
            }


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
