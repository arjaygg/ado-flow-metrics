"""
Workstream Manager - Configuration-based team grouping system
Implements Power BI-like SWITCH logic for team member categorization
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WorkstreamManager:
    """Manages workstream configuration and team member grouping"""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with workstream configuration"""
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent / "config" / "workstream_config.json"
            )

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.workstreams = self.config.get("workstreams", {})
        self.default_workstream = self.config.get("default_workstream", "Others")
        self.matching_options = self.config.get("matching_options", {})

        logger.info(
            f"Loaded {len(self.workstreams)} workstreams from {self.config_path}"
        )
        logger.debug(f"Workstreams: {list(self.workstreams.keys())}")

    def _load_config(self) -> Dict:
        """Load workstream configuration from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            logger.info(
                f"Successfully loaded workstream config from {self.config_path}"
            )
            return config
        except FileNotFoundError:
            logger.warning(
                f"Workstream config not found at {self.config_path}, using empty config"
            )
            return {"workstreams": {}, "default_workstream": "Others"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workstream config: {e}")
            return {"workstreams": {}, "default_workstream": "Others"}

    def get_workstream_for_member(self, assigned_to: str) -> str:
        """
        Get workstream for a team member using CONTAINSSTRING logic
        Implements Power BI SWITCH(TRUE(), CONTAINSSTRING(...)) pattern
        """
        if not assigned_to or assigned_to.strip() == "":
            return self.default_workstream

        # Get matching options
        case_sensitive = self.matching_options.get("case_sensitive", False)
        partial_match = self.matching_options.get("partial_match", True)

        # Normalize name for comparison
        search_name = assigned_to if case_sensitive else assigned_to.lower()

        # Check each workstream (like SWITCH conditions)
        for workstream_name, workstream_config in self.workstreams.items():
            patterns = workstream_config.get("name_patterns", [])

            for pattern in patterns:
                # Normalize pattern for comparison
                search_pattern = pattern if case_sensitive else pattern.lower()

                # Implement CONTAINSSTRING logic
                if partial_match:
                    if search_pattern in search_name:
                        logger.debug(
                            f"Matched '{assigned_to}' to '{workstream_name}' via pattern '{pattern}'"
                        )
                        return workstream_name
                else:
                    if search_pattern == search_name:
                        logger.debug(
                            f"Matched '{assigned_to}' to '{workstream_name}' via exact pattern '{pattern}'"
                        )
                        return workstream_name

        # No match found - return default (like "Others" in Power BI)
        logger.debug(
            f"No workstream match for '{assigned_to}', using default: {self.default_workstream}"
        )
        return self.default_workstream

    def get_members_by_workstream(self, work_items: List[Dict]) -> Dict[str, List[str]]:
        """Group team members by workstream"""
        workstream_members = {}

        for item in work_items:
            assigned_to = item.get("assigned_to", "")
            workstream = self.get_workstream_for_member(assigned_to)

            if workstream not in workstream_members:
                workstream_members[workstream] = []

            if assigned_to not in workstream_members[workstream]:
                workstream_members[workstream].append(assigned_to)

        return workstream_members

    def get_workstream_members(self, workstream_name: str) -> List[str]:
        """Get all potential members for a workstream based on patterns"""
        if workstream_name not in self.workstreams:
            return []

        return self.workstreams[workstream_name].get("name_patterns", [])

    def get_available_workstreams(self) -> List[str]:
        """Get list of all configured workstreams"""
        return list(self.workstreams.keys()) + [self.default_workstream]

    def filter_work_items_by_workstream(
        self, work_items: List[Dict], workstream_names: List[str]
    ) -> List[Dict]:
        """Filter work items to only include specified workstreams"""
        if not workstream_names:
            return work_items

        filtered_items = []
        for item in work_items:
            assigned_to = item.get("assigned_to", "")
            item_workstream = self.get_workstream_for_member(assigned_to)

            if item_workstream in workstream_names:
                filtered_items.append(item)

        return filtered_items

    def get_workstream_summary(self, work_items: List[Dict]) -> Dict:
        """Generate summary of workstream distribution"""
        workstream_counts = {}
        total_items = len(work_items)

        for item in work_items:
            assigned_to = item.get("assigned_to", "")
            workstream = self.get_workstream_for_member(assigned_to)
            workstream_counts[workstream] = workstream_counts.get(workstream, 0) + 1

        # Calculate percentages
        summary = {}
        for workstream, count in workstream_counts.items():
            percentage = (count / total_items * 100) if total_items > 0 else 0
            summary[workstream] = {
                "count": count,
                "percentage": round(percentage, 1),
                "description": self.workstreams.get(workstream, {}).get(
                    "description", ""
                ),
            }

        return summary

    def validate_config(self) -> Dict[str, List[str]]:
        """Validate workstream configuration and return any issues"""
        issues = {"errors": [], "warnings": [], "info": []}

        if not self.workstreams:
            issues["warnings"].append("No workstreams configured")
            return issues

        # Check for duplicate patterns across workstreams
        all_patterns = {}
        for workstream_name, config in self.workstreams.items():
            patterns = config.get("name_patterns", [])

            if not patterns:
                issues["warnings"].append(
                    f"Workstream '{workstream_name}' has no name patterns"
                )
                continue

            for pattern in patterns:
                if pattern in all_patterns:
                    issues["errors"].append(
                        f"Pattern '{pattern}' is duplicated in workstreams: "
                        f"'{all_patterns[pattern]}' and '{workstream_name}'"
                    )
                else:
                    all_patterns[pattern] = workstream_name

        # Info about configuration
        issues["info"].append(f"Configured {len(self.workstreams)} workstreams")
        issues["info"].append(f"Total patterns: {len(all_patterns)}")
        issues["info"].append(f"Default workstream: {self.default_workstream}")

        return issues


def main():
    """Test workstream manager functionality"""
    manager = WorkstreamManager()

    # Test team member assignments
    test_members = [
        "Nenissa Malibago",
        "Christopher Jan Riños",
        "Glizzel Ann Artates",
        "Sharon Smith",
        "Unknown Person",
        "Apollo Bodiongan",
    ]

    print("=== Workstream Assignment Test ===")
    for member in test_members:
        workstream = manager.get_workstream_for_member(member)
        print(f"{member:25} -> {workstream}")

    print(f"\n=== Available Workstreams ===")
    for ws in manager.get_available_workstreams():
        print(f"- {ws}")

    print(f"\n=== Configuration Validation ===")
    validation = manager.validate_config()
    for level, messages in validation.items():
        if messages:
            print(f"{level.upper()}:")
            for msg in messages:
                print(f"  - {msg}")


if __name__ == "__main__":
    main()
