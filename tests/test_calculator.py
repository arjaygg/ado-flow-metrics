"""
Tests for flow metrics calculator.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from src.calculator import FlowMetricsCalculator
from src.models import WorkItem, StateTransition
from src.config_manager import Settings


class TestFlowMetricsCalculator:
    """Test FlowMetricsCalculator functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Provide sample configuration for testing."""
        return {
            "stage_definitions": {
                "active_states": ["Active", "In Progress", "Code Review"],
                "completion_states": ["Done", "Closed", "Resolved"],
                "waiting_states": ["New", "Blocked", "Waiting"]
            }
        }
    
    @pytest.fixture
    def sample_work_items(self):
        """Provide sample work items for testing."""
        now = datetime.now(timezone.utc)
        
        # Work item 1: Complete lifecycle
        item1 = WorkItem(
            id=1,
            title="Complete Item",
            work_item_type="User Story",
            state="Done",
            assigned_to="John Doe",
            created_date=now - timedelta(days=10),
            changed_date=now - timedelta(days=1),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=10),
                    changed_by="System"
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=8),
                    changed_by="John Doe"
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Code Review",
                    changed_date=now - timedelta(days=3),
                    changed_by="John Doe"
                ),
                StateTransition(
                    from_state="Code Review",
                    to_state="Done",
                    changed_date=now - timedelta(days=1),
                    changed_by="Jane Smith"
                )
            ]
        )
        
        # Work item 2: In progress
        item2 = WorkItem(
            id=2,
            title="In Progress Item",
            work_item_type="Bug",
            state="Active",
            assigned_to="Jane Smith",
            created_date=now - timedelta(days=5),
            changed_date=now - timedelta(days=2),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=5),
                    changed_by="System"
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=2),
                    changed_by="Jane Smith"
                )
            ]
        )
        
        return [item1, item2]
    
    def test_calculator_initialization(self, sample_work_items, sample_config):
        """Test calculator initialization."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        assert calculator.work_items == sample_work_items
        assert calculator.config == sample_config
    
    def test_calculate_lead_time(self, sample_work_items, sample_config):
        """Test lead time calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        lead_times = calculator._calculate_lead_times()
        
        # Should have one completed item with lead time
        assert len(lead_times) == 1
        assert lead_times[0] == 9.0  # 10 days from creation to completion (minus 1)
    
    def test_calculate_cycle_time(self, sample_work_items, sample_config):
        """Test cycle time calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        cycle_times = calculator._calculate_cycle_times()
        
        # Should have one completed item with cycle time
        assert len(cycle_times) == 1
        assert cycle_times[0] == 7.0  # 8 days from Active to Done (minus 1)
    
    def test_calculate_wip(self, sample_work_items, sample_config):
        """Test WIP calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        wip = calculator._calculate_wip()
        
        # Should have one item in progress
        assert wip == 1
    
    def test_calculate_throughput(self, sample_work_items, sample_config):
        """Test throughput calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        throughput = calculator._calculate_throughput()
        
        # Should have 1 completed item in the last 30 days
        assert throughput == 1.0
    
    def test_calculate_flow_efficiency(self, sample_work_items, sample_config):
        """Test flow efficiency calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        flow_efficiency = calculator._calculate_flow_efficiency()
        
        # Should calculate based on active vs total time
        assert 0.0 <= flow_efficiency <= 1.0
    
    def test_calculate_metrics_integration(self, sample_work_items, sample_config):
        """Test full metrics calculation integration."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        metrics = calculator.calculate_metrics()
        
        # Verify all metrics are calculated
        assert metrics.lead_time_avg > 0
        assert metrics.lead_time_median > 0
        assert metrics.cycle_time_avg > 0
        assert metrics.cycle_time_median > 0
        assert metrics.throughput >= 0
        assert metrics.wip >= 0
        assert 0.0 <= metrics.flow_efficiency <= 1.0
        assert metrics.total_items == 2
        assert metrics.completed_items == 1
    
    def test_empty_work_items(self, sample_config):
        """Test calculator with empty work items."""
        calculator = FlowMetricsCalculator([], sample_config)
        metrics = calculator.calculate_metrics()
        
        # Should handle empty data gracefully
        assert metrics.lead_time_avg == 0.0
        assert metrics.cycle_time_avg == 0.0
        assert metrics.throughput == 0.0
        assert metrics.wip == 0
        assert metrics.flow_efficiency == 0.0
        assert metrics.total_items == 0
        assert metrics.completed_items == 0
    
    def test_calculate_team_metrics(self, sample_work_items, sample_config):
        """Test team metrics calculation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        team_metrics = calculator.calculate_team_metrics()
        
        # Should have metrics for both team members
        assert "John Doe" in team_metrics
        assert "Jane Smith" in team_metrics
        
        # John Doe should have 1 completed item
        john_metrics = team_metrics["John Doe"]
        assert john_metrics["completed_items"] == 1
        assert john_metrics["lead_time_avg"] > 0
        
        # Jane Smith should have 0 completed items (in progress)
        jane_metrics = team_metrics["Jane Smith"]
        assert jane_metrics["completed_items"] == 0
        assert jane_metrics["wip"] == 1
    
    def test_validate_littles_law(self, sample_work_items, sample_config):
        """Test Little's Law validation."""
        calculator = FlowMetricsCalculator(sample_work_items, sample_config)
        is_valid, ratio = calculator.validate_littles_law()
        
        # Should return validation status and ratio
        assert isinstance(is_valid, bool)
        assert isinstance(ratio, float)
        assert ratio > 0
    
    def test_edge_cases(self, sample_config):
        """Test various edge cases."""
        now = datetime.now(timezone.utc)
        
        # Work item with no state transitions
        item_no_transitions = WorkItem(
            id=999,
            title="No Transitions",
            work_item_type="Task",
            state="New",
            assigned_to="Test User",
            created_date=now - timedelta(days=1),
            changed_date=now - timedelta(days=1),
            state_transitions=[]
        )
        
        calculator = FlowMetricsCalculator([item_no_transitions], sample_config)
        metrics = calculator.calculate_metrics()
        
        # Should handle gracefully
        assert metrics.total_items == 1
        assert metrics.completed_items == 0
        assert metrics.wip == 1  # Item in active state counts as WIP