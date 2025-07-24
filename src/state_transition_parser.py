"""State transition parsing utilities to eliminate code duplication."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class StateTransitionParser:
    """Utility class for parsing and working with state transitions."""
    
    @staticmethod
    def normalize_state_name(state_name: str) -> str:
        """Normalize state name for use as field key."""
        if not state_name:
            return ""
        
        # Clean state name for use as field key
        state_clean = (
            state_name.lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace(".", "_")
        )
        # Remove multiple underscores and strip
        return "_".join([part for part in state_clean.split("_") if part])
    
    @staticmethod
    def get_state_date_field_name(state_name: str) -> str:
        """Get the field name for a state's date."""
        normalized_name = StateTransitionParser.normalize_state_name(state_name)
        return f"{normalized_name}_date"
    
    @staticmethod
    def parse_state_transitions(transitions: List[Dict]) -> Dict[str, datetime]:
        """Parse state transitions into a dictionary of state dates."""
        state_dates = {}
        
        for trans in transitions:
            try:
                # Handle both 'to_state' (new format) and 'state' (legacy)
                state = trans.get("to_state") or trans.get("state")
                # Handle both 'transition_date' (new) and 'date' (legacy)
                date_str = trans.get("transition_date") or trans.get("date")

                if state and date_str:
                    state_key = StateTransitionParser.get_state_date_field_name(state)
                    state_dates[state_key] = datetime.fromisoformat(date_str)
                    
            except Exception as e:
                logger.warning(f"Failed to parse transition: {e}")
                continue
        
        return state_dates
    
    @staticmethod
    def find_completion_date(item: Dict, done_states: Set[str]) -> Optional[datetime]:
        """Find the completion date for an item using multiple strategies."""
        # Strategy 1: Look for exact state name matches
        for state in done_states:
            state_key = StateTransitionParser.get_state_date_field_name(state)
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
                for state in done_states:
                    state_clean = StateTransitionParser.normalize_state_name(state)
                    if state_clean in field_name.lower():
                        return field_value

        return None
    
    @staticmethod
    def find_active_date(item: Dict, active_states: Set[str]) -> Optional[datetime]:
        """Find the active start date for an item using multiple strategies."""
        # Strategy 1: Look for exact state name matches
        for state in active_states:
            state_key = StateTransitionParser.get_state_date_field_name(state)
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
                for state in active_states:
                    state_clean = StateTransitionParser.normalize_state_name(state)
                    if state_clean in field_name.lower():
                        return field_value

        # Strategy 4: If no active date found, fall back to created date + 1 day
        # This provides a reasonable estimate for cycle time calculation
        if "created_date" in item:
            from datetime import timedelta
            return item["created_date"] + timedelta(days=1)

        return None
    
    @staticmethod
    def get_all_state_transitions_for_item(item: Dict) -> List[Dict]:
        """Get all state transitions for an item in a standardized format."""
        transitions = item.get("state_transitions", [])
        standardized_transitions = []
        
        for trans in transitions:
            # Standardize the transition format
            standardized_trans = {
                "state": trans.get("to_state") or trans.get("state", ""),
                "date": trans.get("transition_date") or trans.get("date", ""),
                "assigned_to": trans.get("assigned_to", ""),
            }
            
            # Only add if we have the essential information
            if standardized_trans["state"] and standardized_trans["date"]:
                standardized_transitions.append(standardized_trans)
        
        return standardized_transitions
    
    @staticmethod
    def calculate_time_in_state(
        item: Dict, 
        from_states: Set[str], 
        to_states: Set[str]
    ) -> Optional[float]:
        """Calculate time spent between two sets of states."""
        from_date = None
        to_date = None
        
        # Find the earliest date in from_states
        for state in from_states:
            state_key = StateTransitionParser.get_state_date_field_name(state)
            if state_key in item:
                if from_date is None or item[state_key] < from_date:
                    from_date = item[state_key]
        
        # Find the earliest date in to_states (after from_date)
        for state in to_states:
            state_key = StateTransitionParser.get_state_date_field_name(state)
            if state_key in item:
                state_date = item[state_key]
                if from_date and state_date > from_date:
                    if to_date is None or state_date < to_date:
                        to_date = state_date
        
        if from_date and to_date:
            delta = to_date - from_date
            return delta.days + delta.seconds / 86400
        
        return None
    
    @staticmethod
    def extract_transitions_from_work_item(work_item: Dict) -> Dict[str, datetime]:
        """Extract state transitions from a work item and add them as date fields."""
        transitions = work_item.get("state_transitions", [])
        extracted_dates = {}
        
        for trans in transitions:
            try:
                # Handle both 'to_state' (new format) and 'state' (legacy)
                state = trans.get("to_state") or trans.get("state")
                # Handle both 'transition_date' (new) and 'date' (legacy)  
                date_str = trans.get("transition_date") or trans.get("date")

                if state and date_str:
                    state_key = StateTransitionParser.get_state_date_field_name(state)
                    extracted_dates[state_key] = datetime.fromisoformat(date_str)
                    
            except Exception as e:
                logger.warning(
                    f"Failed to parse transition date for "
                    f"item {work_item.get('id', 'unknown')}: {e}"
                )
                continue
        
        return extracted_dates