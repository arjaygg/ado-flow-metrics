"""Comprehensive tests for flow metrics calculator."""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from src.calculator import FlowMetricsCalculator
from src.exceptions import CalculationError


class TestFlowMetricsCalculator:
    """Comprehensive test suite for flow metrics calculator."""

    @pytest.fixture
    def calculator(self):
        """Provide a metrics calculator instance."""
        return FlowMetricsCalculator()

    @pytest.fixture
    def sample_work_items_with_history(self):
        """Provide sample work items with detailed state history."""
        base_date = datetime(2024, 1, 1)
        return [
            {
                "id": 1,
                "title": "Feature A",
                "type": "User Story",
                "created_date": (base_date).isoformat(),
                "current_state": "Done",
                "story_points": 8,
                "state_transitions": [
                    {
                        "state": "New",
                        "date": base_date.isoformat(),
                        "assigned_to": "John Doe",
                    },
                    {
                        "state": "Active",
                        "date": (base_date + timedelta(days=2)).isoformat(),
                        "assigned_to": "Jane Doe",
                    },
                    {
                        "state": "Review",
                        "date": (base_date + timedelta(days=7)).isoformat(),
                        "assigned_to": "Jane Doe",
                    },
                    {
                        "state": "Done",
                        "date": (base_date + timedelta(days=10)).isoformat(),
                        "assigned_to": "Jane Doe",
                    },
                ],
            },
            {
                "id": 2,
                "title": "Bug Fix B",
                "type": "Bug",
                "created_date": (base_date + timedelta(days=1)).isoformat(),
                "current_state": "Active",
                "story_points": 3,
                "state_transitions": [
                    {
                        "state": "New",
                        "date": (base_date + timedelta(days=1)).isoformat(),
                        "assigned_to": "Bob Smith",
                    },
                    {
                        "state": "Active",
                        "date": (base_date + timedelta(days=3)).isoformat(),
                        "assigned_to": "Alice Johnson",
                    },
                ],
            },
            {
                "id": 3,
                "title": "Feature C",
                "type": "User Story",
                "created_date": (base_date + timedelta(days=5)).isoformat(),
                "current_state": "Done",
                "story_points": 5,
                "state_transitions": [
                    {
                        "state": "New",
                        "date": (base_date + timedelta(days=5)).isoformat(),
                        "assigned_to": "Charlie Brown",
                    },
                    {
                        "state": "Active",
                        "date": (base_date + timedelta(days=6)).isoformat(),
                        "assigned_to": "Diana Prince",
                    },
                    {
                        "state": "Done",
                        "date": (base_date + timedelta(days=12)).isoformat(),
                        "assigned_to": "Diana Prince",
                    },
                ],
            },
        ]

    def test_calculate_lead_time_single_item(self, calculator):
        """Test lead time calculation for a single work item."""
        work_item = {
            "id": 1,
            "created_date": "2024-01-01T00:00:00Z",
            "current_state": "Done",
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Done", "date": "2024-01-10T00:00:00Z"},
            ],
        }

        lead_time = calculator.calculate_lead_time([work_item])

        assert lead_time == 9.0  # 9 days from creation to completion

    def test_calculate_lead_time_multiple_items(
        self, calculator, sample_work_items_with_history
    ):
        """Test lead time calculation for multiple work items."""
        lead_time = calculator.calculate_lead_time(sample_work_items_with_history)

        # Only completed items (id 1 and 3): (10 + 7) / 2 = 8.5 days
        assert lead_time == 8.5

    def test_calculate_lead_time_no_completed_items(self, calculator):
        """Test lead time calculation with no completed items."""
        work_items = [
            {
                "id": 1,
                "created_date": "2024-01-01T00:00:00Z",
                "current_state": "Active",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Active", "date": "2024-01-05T00:00:00Z"},
                ],
            }
        ]

        lead_time = calculator.calculate_lead_time(work_items)

        assert lead_time == 0.0

    def test_calculate_cycle_time_single_item(self, calculator):
        """Test cycle time calculation for a single work item."""
        work_item = {
            "id": 1,
            "current_state": "Done",
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {"state": "Active", "date": "2024-01-03T00:00:00Z"},
                {"state": "Done", "date": "2024-01-08T00:00:00Z"},
            ],
        }

        cycle_time = calculator.calculate_cycle_time([work_item])

        assert cycle_time == 5.0  # 5 days from Active to Done

    def test_calculate_cycle_time_with_work_states(self, calculator):
        """Test cycle time calculation with custom work states."""
        work_item = {
            "id": 1,
            "current_state": "Done",
            "state_transitions": [
                {"state": "Backlog", "date": "2024-01-01T00:00:00Z"},
                {"state": "In Progress", "date": "2024-01-05T00:00:00Z"},
                {"state": "Testing", "date": "2024-01-10T00:00:00Z"},
                {"state": "Done", "date": "2024-01-15T00:00:00Z"},
            ],
        }

        work_states = ["In Progress", "Testing"]
        cycle_time = calculator.calculate_cycle_time(
            [work_item], work_states=work_states
        )

        assert cycle_time == 10.0  # 10 days from first work state to completion

    def test_calculate_throughput_weekly(
        self, calculator, sample_work_items_with_history
    ):
        """Test throughput calculation on weekly basis."""
        throughput = calculator.calculate_throughput(
            sample_work_items_with_history, period_days=7
        )

        # 2 completed items in roughly 2 weeks = 1 item per week
        assert throughput == 1.0

    def test_calculate_throughput_by_story_points(
        self, calculator, sample_work_items_with_history
    ):
        """Test throughput calculation by story points."""
        throughput = calculator.calculate_throughput(
            sample_work_items_with_history, period_days=7, by_story_points=True
        )

        # Completed items: 8 + 5 = 13 story points in ~2 weeks = 6.5 points per week
        assert throughput == 6.5

    def test_calculate_work_in_progress(
        self, calculator, sample_work_items_with_history
    ):
        """Test work in progress calculation."""
        wip = calculator.calculate_work_in_progress(sample_work_items_with_history)

        # Only item with id=2 is still in progress (Active state)
        assert wip == 1

    def test_calculate_work_in_progress_by_state(self, calculator):
        """Test work in progress calculation grouped by state."""
        work_items = [
            {"id": 1, "current_state": "Active"},
            {"id": 2, "current_state": "Active"},
            {"id": 3, "current_state": "Review"},
            {"id": 4, "current_state": "Done"},
        ]

        wip_by_state = calculator.calculate_work_in_progress(
            work_items, group_by_state=True
        )

        expected = {
            "Active": 2,
            "Review": 1,
            "Done": 0,  # Completed items don't count as WIP
        }
        assert wip_by_state == expected

    def test_calculate_flow_efficiency(self, calculator):
        """Test flow efficiency calculation."""
        work_item = {
            "id": 1,
            "current_state": "Done",
            "state_transitions": [
                {"state": "New", "date": "2024-01-01T00:00:00Z"},
                {
                    "state": "Active",
                    "date": "2024-01-05T00:00:00Z",
                },  # Work time: 5 days
                {
                    "state": "Blocked",
                    "date": "2024-01-10T00:00:00Z",
                },  # Wait time: 3 days
                {
                    "state": "Active",
                    "date": "2024-01-13T00:00:00Z",
                },  # Work time: 2 days
                {"state": "Done", "date": "2024-01-15T00:00:00Z"},
            ],
        }

        work_states = ["Active"]
        wait_states = ["New", "Blocked"]

        efficiency = calculator.calculate_flow_efficiency(
            [work_item], work_states=work_states, wait_states=wait_states
        )

        # Work time: 5 + 2 = 7 days, Wait time: 4 + 3 = 7 days
        # Efficiency: 7 / (7 + 7) = 0.5 = 50%
        assert efficiency == 0.5

    def test_get_velocity_trends(self, calculator):
        """Test velocity trends calculation."""
        work_items = []
        base_date = datetime(2024, 1, 1)

        # Create work items across multiple sprints
        for week in range(4):
            for item_id in range(3):  # 3 items per week
                work_items.append(
                    {
                        "id": week * 3 + item_id + 1,
                        "current_state": "Done",
                        "story_points": 5,
                        "state_transitions": [
                            {
                                "state": "New",
                                "date": (base_date + timedelta(weeks=week)).isoformat(),
                            },
                            {
                                "state": "Done",
                                "date": (
                                    base_date + timedelta(weeks=week, days=5)
                                ).isoformat(),
                            },
                        ],
                    }
                )

        trends = calculator.get_velocity_trends(work_items, sprint_length_days=7)

        assert len(trends) == 4  # 4 sprints
        for trend in trends:
            assert trend["completed_points"] == 15  # 3 items * 5 points
            assert trend["completed_items"] == 3

    def test_get_bottleneck_analysis(self, calculator):
        """Test bottleneck analysis."""
        work_items = [
            {
                "id": 1,
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Development", "date": "2024-01-02T00:00:00Z"},  # 1 day
                    {"state": "Testing", "date": "2024-01-05T00:00:00Z"},  # 3 days
                    {
                        "state": "Review",
                        "date": "2024-01-10T00:00:00Z",
                    },  # 5 days (bottleneck)
                    {"state": "Done", "date": "2024-01-12T00:00:00Z"},  # 2 days
                ],
            },
            {
                "id": 2,
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Development", "date": "2024-01-03T00:00:00Z"},  # 2 days
                    {"state": "Testing", "date": "2024-01-06T00:00:00Z"},  # 3 days
                    {
                        "state": "Review",
                        "date": "2024-01-12T00:00:00Z",
                    },  # 6 days (bottleneck)
                    {"state": "Done", "date": "2024-01-14T00:00:00Z"},  # 2 days
                ],
            },
        ]

        analysis = calculator.get_bottleneck_analysis(work_items)

        # Review should be identified as the bottleneck with average 5.5 days
        assert "Review" in analysis
        assert analysis["Review"]["avg_time_days"] == 5.5
        assert analysis["Review"]["item_count"] == 2

    def test_calculate_predictability_metrics(self, calculator):
        """Test predictability metrics calculation."""
        work_items = [
            {
                "id": 1,
                "story_points": 5,
                "created_date": "2024-01-01T00:00:00Z",
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-06T00:00:00Z"},  # 5 days
                ],
            },
            {
                "id": 2,
                "story_points": 5,
                "created_date": "2024-01-01T00:00:00Z",
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-11T00:00:00Z"},  # 10 days
                ],
            },
            {
                "id": 3,
                "story_points": 5,
                "created_date": "2024-01-01T00:00:00Z",
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-08T00:00:00Z"},  # 7 days
                ],
            },
        ]

        metrics = calculator.calculate_predictability_metrics(work_items)

        assert "lead_time_percentiles" in metrics
        assert "cycle_time_percentiles" in metrics
        assert "lead_time_std_dev" in metrics
        assert "cycle_time_std_dev" in metrics

        # Check percentile calculations
        percentiles = metrics["lead_time_percentiles"]
        assert percentiles["p50"] == 7.0  # Median
        assert percentiles["p85"] >= percentiles["p50"]
        assert percentiles["p95"] >= percentiles["p85"]

    def test_calculate_team_performance_metrics(self, calculator):
        """Test team performance metrics calculation."""
        work_items = [
            {
                "id": 1,
                "assigned_to": "Alice",
                "current_state": "Done",
                "story_points": 8,
                "created_date": "2024-01-01T00:00:00Z",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-05T00:00:00Z"},
                ],
            },
            {
                "id": 2,
                "assigned_to": "Bob",
                "current_state": "Done",
                "story_points": 5,
                "created_date": "2024-01-01T00:00:00Z",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-08T00:00:00Z"},
                ],
            },
            {
                "id": 3,
                "assigned_to": "Alice",
                "current_state": "Done",
                "story_points": 3,
                "created_date": "2024-01-01T00:00:00Z",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01T00:00:00Z"},
                    {"state": "Done", "date": "2024-01-06T00:00:00Z"},
                ],
            },
        ]

        metrics = calculator.calculate_team_performance_metrics(work_items)

        assert "Alice" in metrics
        assert "Bob" in metrics

        alice_metrics = metrics["Alice"]
        assert alice_metrics["completed_items"] == 2
        assert alice_metrics["total_story_points"] == 11  # 8 + 3
        assert alice_metrics["avg_lead_time"] == 5.0  # (4 + 5) / 2

        bob_metrics = metrics["Bob"]
        assert bob_metrics["completed_items"] == 1
        assert bob_metrics["total_story_points"] == 5
        assert bob_metrics["avg_lead_time"] == 7.0

    def test_calculate_quality_metrics(self, calculator):
        """Test quality metrics calculation."""
        work_items = [
            {"id": 1, "type": "User Story", "current_state": "Done"},
            {"id": 2, "type": "Bug", "current_state": "Done"},
            {"id": 3, "type": "User Story", "current_state": "Done"},
            {"id": 4, "type": "Bug", "current_state": "Active"},
            {"id": 5, "type": "Defect", "current_state": "Done"},
        ]

        metrics = calculator.calculate_quality_metrics(work_items)

        assert metrics["total_items"] == 5
        assert metrics["bug_count"] == 2  # Bug + Defect
        assert metrics["defect_rate"] == 0.4  # 2 defects / 5 total items
        assert metrics["completed_bugs"] == 2  # Both bugs are done
        assert metrics["bug_resolution_rate"] == 1.0  # All bugs resolved

    def test_calculate_flow_metrics_with_custom_states(self, calculator):
        """Test flow metrics with custom state definitions."""
        work_items = [
            {
                "id": 1,
                "current_state": "Released",
                "created_date": "2024-01-01T00:00:00Z",
                "state_transitions": [
                    {"state": "Backlog", "date": "2024-01-01T00:00:00Z"},
                    {"state": "In Development", "date": "2024-01-05T00:00:00Z"},
                    {"state": "Code Review", "date": "2024-01-10T00:00:00Z"},
                    {"state": "Testing", "date": "2024-01-12T00:00:00Z"},
                    {"state": "Released", "date": "2024-01-15T00:00:00Z"},
                ],
            }
        ]

        custom_states = {
            "backlog_states": ["Backlog"],
            "work_states": ["In Development", "Code Review", "Testing"],
            "done_states": ["Released"],
            "wait_states": ["Backlog"],
        }

        # Test lead time with custom done states
        lead_time = calculator.calculate_lead_time(
            work_items, done_states=custom_states["done_states"]
        )
        assert lead_time == 14.0  # From creation to Released

        # Test cycle time with custom work states
        cycle_time = calculator.calculate_cycle_time(
            work_items,
            work_states=custom_states["work_states"],
            done_states=custom_states["done_states"],
        )
        assert cycle_time == 10.0  # From first work state to Released

    def test_error_handling_invalid_data(self, calculator):
        """Test error handling with invalid data."""
        # Test with None input
        assert calculator.calculate_lead_time(None) == 0.0
        assert calculator.calculate_cycle_time([]) == 0.0

        # Test with malformed work items
        invalid_items = [
            {"id": 1},  # Missing required fields
            {"id": 2, "created_date": "invalid-date"},  # Invalid date format
        ]

        # Should handle gracefully without crashing
        result = calculator.calculate_lead_time(invalid_items)
        assert result == 0.0

    def test_date_parsing_edge_cases(self, calculator):
        """Test date parsing with various formats."""
        work_items = [
            {
                "id": 1,
                "created_date": "2024-01-01T00:00:00.000Z",  # With milliseconds
                "current_state": "Done",
                "state_transitions": [
                    {"state": "New", "date": "2024-01-01"},  # Date only
                    {"state": "Done", "date": "2024-01-05T23:59:59Z"},  # End of day
                ],
            }
        ]

        lead_time = calculator.calculate_lead_time(work_items)
        assert lead_time > 0  # Should parse successfully

    def test_memory_efficiency_large_dataset(self, calculator):
        """Test memory efficiency with large dataset."""
        # Create a large number of work items
        large_dataset = []
        base_date = datetime(2024, 1, 1)

        for i in range(1000):  # 1000 work items
            large_dataset.append(
                {
                    "id": i + 1,
                    "created_date": base_date.isoformat(),
                    "current_state": "Done" if i % 2 == 0 else "Active",
                    "story_points": (i % 8) + 1,
                    "state_transitions": [
                        {"state": "New", "date": base_date.isoformat()},
                        {
                            "state": "Active",
                            "date": (base_date + timedelta(days=1)).isoformat(),
                        },
                        {
                            "state": "Done",
                            "date": (base_date + timedelta(days=5)).isoformat(),
                        },
                    ]
                    if i % 2 == 0
                    else [
                        {"state": "New", "date": base_date.isoformat()},
                        {
                            "state": "Active",
                            "date": (base_date + timedelta(days=1)).isoformat(),
                        },
                    ],
                }
            )

        # Should handle large dataset without memory issues
        lead_time = calculator.calculate_lead_time(large_dataset)
        throughput = calculator.calculate_throughput(large_dataset)
        wip = calculator.calculate_work_in_progress(large_dataset)

        assert lead_time >= 0
        assert throughput >= 0
        assert wip >= 0

    @pytest.mark.parametrize(
        "state_config",
        [
            {"done_states": ["Complete", "Closed", "Released"]},
            {"work_states": ["In Progress", "Development", "Testing"]},
            {"wait_states": ["Backlog", "Blocked", "On Hold"]},
        ],
    )
    def test_parameterized_state_configurations(self, calculator, state_config):
        """Test various state configurations."""
        work_item = {
            "id": 1,
            "created_date": "2024-01-01T00:00:00Z",
            "current_state": "Complete",
            "state_transitions": [
                {"state": "Backlog", "date": "2024-01-01T00:00:00Z"},
                {"state": "In Progress", "date": "2024-01-05T00:00:00Z"},
                {"state": "Complete", "date": "2024-01-10T00:00:00Z"},
            ],
        }

        # Test that custom state configurations don't break calculations
        if "done_states" in state_config:
            result = calculator.calculate_lead_time([work_item], **state_config)
            assert result >= 0

        if "work_states" in state_config:
            result = calculator.calculate_cycle_time([work_item], **state_config)
            assert result >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
