"""
Tests for flow metrics data models.
"""
import pytest
from datetime import datetime, timezone, timedelta
from src.models import WorkItem, StateTransition, FlowMetrics
from pydantic import ValidationError


class TestWorkItem:
    """Test WorkItem model validation and functionality."""
    
    def test_work_item_creation(self):
        """Test basic work item creation."""
        item = WorkItem(
            id=12345,
            title="Test Work Item",
            type="User Story",
            state="Active",
            assigned_to="John Doe",
            created_date=datetime.now(timezone.utc),
            transitions=[]
        )
        assert item.id == 12345
        assert item.title == "Test Work Item"
        assert item.type == "User Story"
        assert item.state == "Active"
        assert item.assigned_to == "John Doe"
    
    def test_work_item_with_transitions(self):
        """Test work item with state transitions."""
        transitions = [
            StateTransition(
                from_state="New",
                to_state="Active",
                transition_date=datetime.now(timezone.utc),
                changed_by="Jane Smith"
            )
        ]
        
        item = WorkItem(
            id=12346,
            title="Test with Transitions",
            type="Bug",
            state="Active",
            assigned_to="Jane Smith",
            created_date=datetime.now(timezone.utc),
            transitions=transitions
        )
        
        assert len(item.transitions) == 1
        assert item.transitions[0].from_state == "New"
        assert item.transitions[0].to_state == "Active"
    
    def test_work_item_validation_error(self):
        """Test work item validation with invalid data."""
        with pytest.raises(ValidationError):
            WorkItem(
                id="invalid_id",  # Should be int
                title="Test",
                type="User Story",
                state="Active",
                assigned_to="John Doe",
                created_date=datetime.now(timezone.utc),
                transitions=[]
            )


class TestStateTransition:
    """Test StateTransition model validation and functionality."""
    
    def test_state_transition_creation(self):
        """Test basic state transition creation."""
        transition = StateTransition(
            from_state="New",
            to_state="Active",
            transition_date=datetime.now(timezone.utc),
            changed_by="John Doe"
        )
        
        assert transition.from_state == "New"
        assert transition.to_state == "Active"
        assert transition.changed_by == "John Doe"
        assert isinstance(transition.transition_date, datetime)
    
    def test_state_transition_optional_fields(self):
        """Test state transition with optional fields."""
        transition = StateTransition(
            from_state=None,  # Initial state
            to_state="New",
            transition_date=datetime.now(timezone.utc),
            changed_by="System"
        )
        
        assert transition.from_state is None
        assert transition.to_state == "New"
        assert transition.changed_by == "System"


class TestFlowMetrics:
    """Test FlowMetrics model validation and functionality."""
    
    def test_flow_metrics_creation(self):
        """Test basic flow metrics creation."""
        now = datetime.now(timezone.utc)
        metrics = FlowMetrics(
            period_start=now - timedelta(days=30),
            period_end=now,
            total_items=100,
            completed_items=80,
            average_lead_time=10.5,
            median_lead_time=9.0,
            average_cycle_time=7.5,
            median_cycle_time=7.0,
            throughput_per_day=2.5,
            throughput_per_week=17.5,
            throughput_per_month=75.0,
            current_wip=25,
            flow_efficiency=75.0
        )
        
        assert metrics.average_lead_time == 10.5
        assert metrics.median_lead_time == 9.0
        assert metrics.average_cycle_time == 7.5
        assert metrics.median_cycle_time == 7.0
        assert metrics.throughput_per_month == 75.0
        assert metrics.current_wip == 25
        assert metrics.flow_efficiency == 75.0
        assert metrics.total_items == 100
        assert metrics.completed_items == 80
    
    def test_flow_metrics_computed_properties(self):
        """Test computed properties of flow metrics."""
        now = datetime.now(timezone.utc)
        metrics = FlowMetrics(
            period_start=now - timedelta(days=30),
            period_end=now,
            total_items=100,
            completed_items=85,
            average_lead_time=10.0,
            median_lead_time=9.0,
            average_cycle_time=7.0,
            median_cycle_time=6.0,
            throughput_per_day=2.8,
            throughput_per_week=20.0,
            throughput_per_month=85.0,
            current_wip=30,
            flow_efficiency=70.0
        )
        
        # Test completion rate calculation
        completion_rate = metrics.completed_items / metrics.total_items
        assert completion_rate == 0.85
        
        # Test Little's Law validation (WIP = Throughput * Lead Time)
        expected_wip = metrics.throughput_per_day * metrics.average_lead_time
        assert abs(metrics.current_wip - expected_wip) < 10  # Allow some variance
    
    def test_flow_metrics_validation_error(self):
        """Test flow metrics validation with invalid data."""
        now = datetime.now(timezone.utc)
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            FlowMetrics(
                period_start=now - timedelta(days=30),
                period_end=now,
                # Missing required fields: total_items, completed_items, etc.
            )