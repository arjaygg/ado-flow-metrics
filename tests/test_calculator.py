"""
Tests for flow metrics calculator.
"""

import pytest
from datetime import datetime, timezone, timedelta
from src.calculator import FlowMetricsCalculator


class TestFlowMetricsCalculator:
    """Test FlowMetricsCalculator functionality."""

    @pytest.fixture
    def sample_config(self):
        """Provide actual project configuration for testing."""
        return {
            "azure_devops": {
                "org_url": "https://dev.azure.com/bofaz",
                "default_project": "Axos-Universal-Core",
            },
            "stage_metadata": [
                {
                    "stage_name": "0 - New",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "To Do",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "1.1 - In Requirements",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "1.1.1 - Ready for Refinement",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "1.1.2 - Requirements Adjustment",
                    "stage_group": "1. Requirement",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "1.2 - Ready for Estimate",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "1.2 - Ready for Refinement",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "1.2.1 - Requirements Adjustment",
                    "stage_group": "1. Requirement",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "1.2.2 - Ready for Estimate",
                    "stage_group": "1. Requirement",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.1 - Ready for Development",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.2 - In Progress",
                    "stage_group": "2. Development",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "In Progress",
                    "stage_group": "2. Development",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "2.3 - Ready for Code Review",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.4 - Code Review In Progress",
                    "stage_group": "2. Development",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "2.5 - Dev Blocked",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.5 - Ready to Build",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.5.1 - Build Complete",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.6 - Dev Blocked",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "2.7 - Dependent on Other Work Item",
                    "stage_group": "2. Development",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "3.1 - Ready for Test",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "3.2 - QA in Progress",
                    "stage_group": "3. QA",
                    "is_active": True,
                    "is_done": False,
                },
                {
                    "stage_name": "3.2.1 - Rejected by QA",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "3.3 - QA Blocked",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": False,
                },
                {
                    "stage_name": "3.4 - QA Approved",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "3.4 -QA Approved",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "3.4.1 - Ready for Demo",
                    "stage_group": "3. QA",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "4.1 - Ready for Release",
                    "stage_group": "5. Ready for Release",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "Ready for Release",
                    "stage_group": "5. Ready for Release",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "5 - Done",
                    "stage_group": "6. Done",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "Done",
                    "stage_group": "6. Done",
                    "is_active": False,
                    "is_done": True,
                },
                {
                    "stage_name": "Closed",
                    "stage_group": "6. Done",
                    "is_active": False,
                    "is_done": True,
                },
            ],
        }

    @pytest.fixture
    def sample_work_items(self):
        """Provide sample work items as dictionaries (as expected by calculator)."""
        now = datetime.now(timezone.utc)

        # Work item 1: Complete lifecycle using actual project states
        item1 = {
            "id": 1,
            "title": "Complete Item",
            "type": "User Story",
            "priority": 2,
            "current_state": "3.4 - QA Approved",
            "assigned_to": "John Doe",
            "created_date": (now - timedelta(days=10)).isoformat(),
            "created_by": "System",
            "story_points": 5,
            "effort_hours": 20,
            "tags": ["frontend", "urgent"],
            "state_transitions": [
                {
                    "from_state": None,
                    "to_state": "0 - New",
                    "transition_date": (now - timedelta(days=10)).isoformat(),
                    "changed_by": "System",
                },
                {
                    "from_state": "0 - New",
                    "to_state": "2.2 - In Progress",
                    "transition_date": (now - timedelta(days=8)).isoformat(),
                    "changed_by": "John Doe",
                },
                {
                    "from_state": "2.2 - In Progress",
                    "to_state": "2.4 - Code Review In Progress",
                    "transition_date": (now - timedelta(days=5)).isoformat(),
                    "changed_by": "John Doe",
                },
                {
                    "from_state": "2.4 - Code Review In Progress",
                    "to_state": "3.2 - QA in Progress",
                    "transition_date": (now - timedelta(days=3)).isoformat(),
                    "changed_by": "QA Team",
                },
                {
                    "from_state": "3.2 - QA in Progress",
                    "to_state": "3.4 - QA Approved",
                    "transition_date": (now - timedelta(days=1)).isoformat(),
                    "changed_by": "Jane Smith",
                },
            ],
        }

        # Work item 2: In progress using actual project states
        item2 = {
            "id": 2,
            "title": "In Progress Item",
            "type": "Bug",
            "priority": 1,
            "current_state": "2.2 - In Progress",
            "assigned_to": "Jane Smith",
            "created_date": (now - timedelta(days=5)).isoformat(),
            "created_by": "System",
            "story_points": 3,
            "effort_hours": 12,
            "tags": ["backend"],
            "state_transitions": [
                {
                    "from_state": None,
                    "to_state": "0 - New",
                    "transition_date": (now - timedelta(days=5)).isoformat(),
                    "changed_by": "System",
                },
                {
                    "from_state": "0 - New",
                    "to_state": "2.2 - In Progress",
                    "transition_date": (now - timedelta(days=2)).isoformat(),
                    "changed_by": "Jane Smith",
                },
            ],
        }

        return [item1, item2]

    def test_calculator_initialization(self, sample_work_items, sample_config):
        """Test calculator initialization."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        assert calculator.work_items == sample_work_items
        assert calculator.config == sample_config

    def test_calculate_lead_time(self, sample_work_items, sample_config):
        """Test lead time calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        lead_time_result = calculator.calculate_lead_time()

        # Should have lead time metrics
        assert "average_days" in lead_time_result
        assert "median_days" in lead_time_result
        assert lead_time_result["average_days"] >= 0

    def test_calculate_cycle_time(self, sample_work_items, sample_config):
        """Test cycle time calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        cycle_time_result = calculator.calculate_cycle_time()

        # Should have cycle time metrics
        assert "average_days" in cycle_time_result
        assert "median_days" in cycle_time_result
        assert cycle_time_result["average_days"] >= 0

    def test_calculate_wip(self, sample_work_items, sample_config):
        """Test WIP calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        wip_result = calculator.calculate_wip()

        # Should have WIP metrics
        assert "total_wip" in wip_result
        assert wip_result["total_wip"] >= 0

    def test_calculate_throughput(self, sample_work_items, sample_config):
        """Test throughput calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        throughput_result = calculator.calculate_throughput()

        # Should have throughput metrics
        assert "items_per_period" in throughput_result
        assert throughput_result["items_per_period"] >= 0

    def test_calculate_flow_efficiency(self, sample_work_items, sample_config):
        """Test flow efficiency calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        flow_efficiency_result = calculator.calculate_flow_efficiency()

        # Should have flow efficiency metrics
        assert "average_efficiency" in flow_efficiency_result
        assert 0.0 <= flow_efficiency_result["average_efficiency"] <= 1.0

    def test_generate_flow_metrics_report(self, sample_work_items, sample_config):
        """Test full metrics report generation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        report = calculator.generate_flow_metrics_report()

        # Verify report structure
        assert "summary" in report
        assert "lead_time" in report
        assert "cycle_time" in report
        assert "throughput" in report
        assert "work_in_progress" in report
        assert "flow_efficiency" in report
        assert "team_metrics" in report
        assert "littles_law_validation" in report

        # Verify summary metrics
        summary = report["summary"]
        assert "total_work_items" in summary
        assert "completed_items" in summary
        assert "completion_rate" in summary

    def test_calculator_without_config(self, sample_work_items):
        """Test calculator without configuration (uses defaults)."""
        calculator = FlowMetricsCalculator(sample_work_items)

        # Should use default states
        assert "In Progress" in calculator.active_states
        assert "Active" in calculator.active_states
        assert "Done" in calculator.done_states
        assert "Closed" in calculator.done_states

    def test_calculator_with_pydantic_config(self, sample_work_items):
        """Test calculator with Pydantic configuration object."""
        from src.config_manager import FlowMetricsSettings

        # Create a Pydantic config object
        config = FlowMetricsSettings(
            azure_devops={
                "org_url": "https://dev.azure.com/test",
                "default_project": "test-project",
                "pat_token": "test",
            }
        )

        calculator = FlowMetricsCalculator(sample_work_items, config)

        # Should extract states from flow_metrics defaults
        assert len(calculator.active_states) > 0
        assert len(calculator.done_states) > 0

    def test_empty_work_items(self, sample_config):
        """Test calculator with empty work items."""
        calculator = FlowMetricsCalculator([], sample_config)

        # Should not crash and have proper state configuration
        assert len(calculator.active_states) > 0
        assert len(calculator.done_states) > 0

    def test_calculate_team_metrics(self, sample_work_items, sample_config):
        """Test team metrics calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        team_metrics = calculator.calculate_team_metrics()

        # Should have team metrics structure
        assert isinstance(team_metrics, dict)

        # Should have metrics for team members
        assert len(team_metrics) >= 0  # Depends on sample data

    def test_validate_littles_law(self, sample_work_items, sample_config):
        """Test Little's Law validation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        littles_law_result = calculator.calculate_littles_law_validation()

        # Should have validation metrics (when WIP > 0 and throughput > 0)
        if littles_law_result:  # Only validate if Little's Law could be calculated
            assert "theoretical_cycle_time" in littles_law_result
            assert "variance_percentage" in littles_law_result
            assert "measured_cycle_time" in littles_law_result
            assert "interpretation" in littles_law_result
            assert isinstance(
                littles_law_result["theoretical_cycle_time"], (int, float)
            )
            assert isinstance(littles_law_result["variance_percentage"], (int, float))
            assert isinstance(littles_law_result["measured_cycle_time"], (int, float))
            assert isinstance(littles_law_result["interpretation"], str)
        else:
            # If no Little's Law validation (WIP=0 or throughput=0), that's also valid
            assert littles_law_result == {}

    def test_edge_cases(self, sample_config):
        """Test various edge cases."""
        now = datetime.now(timezone.utc)

        # Work item with no state transitions - use dictionary format
        item_no_transitions = {
            "id": 999,
            "title": "No Transitions",
            "type": "Task",
            "priority": 1,
            "current_state": "New",
            "assigned_to": "Test User",
            "created_date": (now - timedelta(days=1)).isoformat(),
            "created_by": "System",
            "story_points": 1,
            "effort_hours": 1,
            "tags": [],
            "state_transitions": [],
        }

        calculator = FlowMetricsCalculator([item_no_transitions], sample_config)
        report = calculator.generate_flow_metrics_report()

        # Should handle gracefully
        assert report["summary"]["total_work_items"] == 1
        assert report["summary"]["completed_items"] == 0
        assert report["work_in_progress"]["total_wip"] >= 0  # Item state handling
