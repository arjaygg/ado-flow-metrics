"""
State Mapper - Workflow State Configuration and Mapping Utilities

This module provides utilities for working with workflow states based on 
external configuration, enabling flexible adaptation to different team processes.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class StateMapper:
    """Manages workflow state mappings and categorization based on external configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize StateMapper with configuration.
        
        Args:
            config_path: Path to workflow_states.json config file
        """
        if config_path is None:
            # Default to config/workflow_states.json in project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "workflow_states.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._build_lookup_maps()
    
    def _load_config(self) -> Dict:
        """Load workflow states configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Workflow states config not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in workflow states config: {e}")
    
    def _build_lookup_maps(self):
        """Build reverse lookup maps for efficient state categorization."""
        self.state_to_category = {}
        self.state_to_properties = {}
        
        for category_name, category_config in self.config["stateCategories"].items():
            for state in category_config["states"]:
                self.state_to_category[state] = category_name
                self.state_to_properties[state] = {
                    "category": category_name,
                    "isActive": category_config.get("isActive", True),
                    "flowPosition": category_config.get("flowPosition", 0),
                    "color": category_config.get("color", "#f5f5f5"),
                    "cycleTimetWeight": category_config.get("cycleTimetWeight", 0.1),
                    "isBlockedState": category_config.get("isBlockedState", False),
                    "isCompletedState": category_config.get("isCompletedState", False),
                    "isFinalState": category_config.get("isFinalState", False)
                }
    
    def get_state_category(self, state: str) -> Optional[str]:
        """
        Get the category for a given state.
        
        Args:
            state: The workflow state name
            
        Returns:
            Category name or None if state not found
        """
        return self.state_to_category.get(state)
    
    def get_state_properties(self, state: str) -> Dict:
        """
        Get all properties for a given state.
        
        Args:
            state: The workflow state name
            
        Returns:
            Dictionary of state properties
        """
        return self.state_to_properties.get(state, {})
    
    def is_active_state(self, state: str) -> bool:
        """Check if a state represents active work."""
        props = self.get_state_properties(state)
        return props.get("isActive", False)
    
    def is_blocked_state(self, state: str) -> bool:
        """Check if a state represents blocked work."""
        props = self.get_state_properties(state)
        return props.get("isBlockedState", False)
    
    def is_completed_state(self, state: str) -> bool:
        """Check if a state represents completed work."""
        props = self.get_state_properties(state)
        return props.get("isCompletedState", False)
    
    def is_final_state(self, state: str) -> bool:
        """Check if a state represents final/cancelled work."""
        props = self.get_state_properties(state)
        return props.get("isFinalState", False)
    
    def normalize_state(self, state: str) -> str:
        """
        Normalize a state name to canonical form.
        
        Args:
            state: Raw state name from data
            
        Returns:
            Normalized state name
        """
        # Apply data quality fixes
        fixes = self.config.get("stateValidation", {}).get("dataQualityFixes", {})
        if state in fixes:
            return fixes[state]
        
        # Apply state normalization
        normalization = self.config.get("stateValidation", {}).get("stateNormalization", {})
        return normalization.get(state, state)
    
    def get_flow_position(self, state: str) -> int:
        """Get the flow position for cycle time calculations."""
        props = self.get_state_properties(state)
        return props.get("flowPosition", 0)
    
    def get_cycle_time_weight(self, state: str) -> float:
        """Get the cycle time weight for this state."""
        props = self.get_state_properties(state)
        return props.get("cycleTimetWeight", 0.1)
    
    def get_states_by_category(self, category: str) -> List[str]:
        """Get all states in a given category."""
        category_config = self.config["stateCategories"].get(category, {})
        return category_config.get("states", [])
    
    def get_states_by_mapping(self, mapping_type: str, mapping_name: str) -> List[str]:
        """
        Get states by predefined mapping.
        
        Args:
            mapping_type: "normalized" or "flowCalculations" 
            mapping_name: Name of the specific mapping
            
        Returns:
            List of states in the mapping
        """
        mappings = self.config.get("stateMappings", {})
        mapping_group = mappings.get(mapping_type, {})
        return mapping_group.get(mapping_name, [])
    
    def is_todo_state(self, state: str) -> bool:
        """Check if state is a TODO/initial state."""
        todo_states = self.get_states_by_mapping("normalized", "todo_states")
        return state in todo_states
    
    def is_in_progress_state(self, state: str) -> bool:
        """Check if state is an in-progress state."""
        progress_states = self.get_states_by_mapping("normalized", "in_progress_states")
        return state in progress_states
    
    def is_done_state(self, state: str) -> bool:
        """Check if state is a done state."""
        done_states = self.get_states_by_mapping("normalized", "done_states")
        return state in done_states
    
    def is_cancelled_state(self, state: str) -> bool:
        """Check if state is a cancelled state."""
        cancelled_states = self.get_states_by_mapping("normalized", "cancelled_states")
        return state in cancelled_states
    
    def get_lead_time_bounds(self) -> Tuple[List[str], List[str]]:
        """Get start and end states for lead time calculation."""
        start_states = self.get_states_by_mapping("flowCalculations", "startStates")
        end_states = self.get_states_by_mapping("flowCalculations", "endStates")
        return start_states, end_states
    
    def get_cycle_time_bounds(self) -> Tuple[List[str], List[str]]:
        """Get start and end states for cycle time calculation."""
        start_states = self.get_states_by_mapping("flowCalculations", "activeStates")
        end_states = self.get_states_by_mapping("flowCalculations", "endStates")
        return start_states, end_states
    
    def get_blocked_time_states(self) -> List[str]:
        """Get states that count as blocked time."""
        return self.config.get("metrics", {}).get("blockedTimeStates", [])
    
    def get_wait_time_states(self) -> List[str]:
        """Get states that count as waiting time."""
        return self.config.get("metrics", {}).get("waitTimeStates", [])
    
    def get_all_categories(self) -> Dict[str, Dict]:
        """Get all category configurations."""
        return self.config["stateCategories"]
    
    def get_category_info(self, category: str) -> Dict:
        """Get detailed information about a category."""
        return self.config["stateCategories"].get(category, {})
    
    def validate_state_transition(self, from_state: str, to_state: str) -> bool:
        """
        Validate if a state transition is allowed.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is allowed
        """
        allowed_transitions = self.config.get("stateValidation", {}).get("allowedTransitions", {})
        allowed_next_states = allowed_transitions.get(from_state, [])
        return to_state in allowed_next_states
    
    def get_state_color(self, state: str) -> str:
        """Get the color code for a state based on its category."""
        props = self.get_state_properties(state)
        return props.get("color", "#f5f5f5")
    
    def export_state_summary(self) -> Dict:
        """Export a summary of all states and their properties."""
        summary = {
            "totalStates": len(self.state_to_category),
            "totalCategories": len(self.config["stateCategories"]),
            "statesByCategory": {},
            "stateProperties": self.state_to_properties
        }
        
        for category, config in self.config["stateCategories"].items():
            summary["statesByCategory"][category] = {
                "count": len(config["states"]),
                "states": config["states"],
                "isActive": config.get("isActive", True),
                "flowPosition": config.get("flowPosition", 0)
            }
        
        return summary


# Convenience functions for direct usage
def get_default_state_mapper() -> StateMapper:
    """Get StateMapper instance with default configuration."""
    return StateMapper()


def categorize_state(state: str) -> Optional[str]:
    """Quick function to categorize a single state."""
    mapper = get_default_state_mapper()
    return mapper.get_state_category(state)


def is_active_work(state: str) -> bool:
    """Quick function to check if state represents active work."""
    mapper = get_default_state_mapper()
    return mapper.is_active_state(state)


def is_blocked_work(state: str) -> bool:
    """Quick function to check if state represents blocked work."""
    mapper = get_default_state_mapper()
    return mapper.is_blocked_state(state)


if __name__ == "__main__":
    # Example usage and testing
    mapper = StateMapper()
    
    # Test some states
    test_states = [
        "0 - New",
        "2.2 - In Progress", 
        "3.4 - QA Approved",
        "5 - Done",
        "2.6 - Dev Blocked"
    ]
    
    print("State Mapping Test Results:")
    print("=" * 50)
    
    for state in test_states:
        category = mapper.get_state_category(state)
        properties = mapper.get_state_properties(state)
        
        print(f"State: {state}")
        print(f"  Category: {category}")
        print(f"  Active: {properties.get('isActive', False)}")
        print(f"  Blocked: {properties.get('isBlockedState', False)}")
        print(f"  Flow Position: {properties.get('flowPosition', 0)}")
        print(f"  Color: {properties.get('color', 'N/A')}")
        print()
    
    # Export summary
    summary = mapper.export_state_summary()
    print(f"Total States: {summary['totalStates']}")
    print(f"Total Categories: {summary['totalCategories']}")