"""Pydantic models for Flow Metrics data structures."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class WorkItemType(str, Enum):
    """Supported work item types."""
    USER_STORY = "User Story"
    BUG = "Bug"
    TASK = "Task"
    FEATURE = "Feature"
    EPIC = "Epic"
    ISSUE = "Issue"
    TEST_CASE = "Test Case"


class Priority(int, Enum):
    """Work item priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class StateTransition(BaseModel):
    """Represents a state transition in a work item's lifecycle."""
    from_state: Optional[str] = Field(None, description="Previous state")
    to_state: str = Field(..., description="New state")
    transition_date: datetime = Field(..., description="When the transition occurred")
    changed_by: Optional[str] = Field(None, description="Who made the change")
    
    @property
    def is_to_active(self) -> bool:
        """Check if this transition is to an active state."""
        # This would be determined by configuration
        active_keywords = ["In Progress", "Active", "Development", "Testing", "Review"]
        return any(keyword in self.to_state for keyword in active_keywords)
    
    @property
    def is_to_done(self) -> bool:
        """Check if this transition is to a done state."""
        done_keywords = ["Done", "Closed", "Completed", "Released", "Approved"]
        return any(keyword in self.to_state for keyword in done_keywords)


class WorkItem(BaseModel):
    """Represents a work item from Azure DevOps."""
    id: int = Field(..., description="Work item ID")
    title: str = Field(..., description="Work item title")
    type: str = Field(..., description="Work item type")
    state: str = Field(..., description="Current state")
    assigned_to: Optional[str] = Field(None, description="Assigned team member")
    created_date: datetime = Field(..., description="Creation date")
    closed_date: Optional[datetime] = Field(None, description="Closure date")
    activated_date: Optional[datetime] = Field(None, description="First activation date")
    priority: Optional[int] = Field(None, ge=1, le=4, description="Priority level")
    effort: Optional[float] = Field(None, ge=0, description="Estimated effort")
    tags: List[str] = Field(default_factory=list, description="Tags")
    area_path: Optional[str] = Field(None, description="Area path")
    iteration_path: Optional[str] = Field(None, description="Iteration path")
    transitions: List[StateTransition] = Field(
        default_factory=list, 
        description="State transition history"
    )
    parent_id: Optional[int] = Field(None, description="Parent work item ID")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom fields"
    )
    
    @field_validator('closed_date')
    @classmethod
    def validate_closed_date(cls, v, info):
        if v and info.data.get('created_date') and v < info.data['created_date']:
            raise ValueError('Closed date cannot be before created date')
        return v
    
    @property
    def lead_time_days(self) -> Optional[float]:
        """Calculate lead time in days (created to closed)."""
        if self.closed_date:
            return (self.closed_date - self.created_date).total_seconds() / 86400
        return None
    
    @property
    def cycle_time_days(self) -> Optional[float]:
        """Calculate cycle time in days (activated to closed)."""
        if self.closed_date and self.activated_date:
            return (self.closed_date - self.activated_date).total_seconds() / 86400
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if work item is completed."""
        return self.closed_date is not None
    
    @property
    def age_days(self) -> float:
        """Calculate age in days since creation."""
        return (datetime.now() - self.created_date).total_seconds() / 86400
    
    def get_time_in_state(self, state_name: str) -> Optional[float]:
        """Get time spent in a specific state in hours."""
        time_in_state = 0.0
        entered_state = None
        
        for i, transition in enumerate(self.transitions):
            if transition.to_state == state_name:
                entered_state = transition.transition_date
            elif entered_state and transition.from_state == state_name:
                time_in_state += (transition.transition_date - entered_state).total_seconds() / 3600
                entered_state = None
        
        # If still in the state
        if entered_state and self.state == state_name:
            time_in_state += (datetime.now() - entered_state).total_seconds() / 3600
        
        return time_in_state if time_in_state > 0 else None


class FlowMetrics(BaseModel):
    """Calculated flow metrics for a set of work items."""
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")
    total_items: int = Field(..., description="Total items analyzed")
    completed_items: int = Field(..., description="Items completed in period")
    
    # Lead time metrics
    average_lead_time: Optional[float] = Field(None, description="Average lead time in days")
    median_lead_time: Optional[float] = Field(None, description="Median lead time in days")
    lead_time_percentiles: Dict[str, float] = Field(
        default_factory=dict,
        description="Lead time percentiles"
    )
    
    # Cycle time metrics
    average_cycle_time: Optional[float] = Field(None, description="Average cycle time in days")
    median_cycle_time: Optional[float] = Field(None, description="Median cycle time in days")
    cycle_time_percentiles: Dict[str, float] = Field(
        default_factory=dict,
        description="Cycle time percentiles"
    )
    
    # Throughput
    throughput_per_day: float = Field(..., description="Items completed per day")
    throughput_per_week: float = Field(..., description="Items completed per week")
    throughput_per_month: float = Field(..., description="Items completed per 30 days")
    
    # Work in Progress
    current_wip: int = Field(..., description="Current work in progress")
    wip_by_state: Dict[str, int] = Field(
        default_factory=dict,
        description="WIP breakdown by state"
    )
    wip_by_assignee: Dict[str, int] = Field(
        default_factory=dict,
        description="WIP breakdown by assignee"
    )
    
    # Flow efficiency
    flow_efficiency: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Flow efficiency percentage"
    )
    
    # Little's Law
    littles_law_cycle_time: Optional[float] = Field(
        None,
        description="Theoretical cycle time from Little's Law"
    )
    littles_law_variance: Optional[float] = Field(
        None,
        description="Variance from Little's Law prediction"
    )
    
    # Additional metrics
    blocked_items: int = Field(0, description="Number of blocked items")
    items_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Items breakdown by type"
    )
    items_by_priority: Dict[int, int] = Field(
        default_factory=dict,
        description="Items breakdown by priority"
    )


class TeamMemberMetrics(BaseModel):
    """Metrics for an individual team member."""
    name: str = Field(..., description="Team member name")
    completed_items: int = Field(0, description="Items completed")
    active_items: int = Field(0, description="Currently active items")
    average_lead_time: Optional[float] = Field(None, description="Average lead time")
    average_cycle_time: Optional[float] = Field(None, description="Average cycle time")
    throughput_per_week: float = Field(0, description="Items completed per week")


class FlowMetricsReport(BaseModel):
    """Complete flow metrics report."""
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")
    metrics: FlowMetrics = Field(..., description="Overall metrics")
    team_metrics: List[TeamMemberMetrics] = Field(
        default_factory=list,
        description="Per-member metrics"
    )
    analysis_period_days: int = Field(..., description="Analysis period in days")
    data_source: str = Field(..., description="Data source identifier")
    
    # Optional advanced analytics
    trends: Optional[Dict[str, Any]] = Field(None, description="Trend analysis")
    bottlenecks: Optional[List[Dict[str, Any]]] = Field(None, description="Identified bottlenecks")
    predictions: Optional[Dict[str, Any]] = Field(None, description="Predictive analytics")
    
    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return self.model_dump_json(indent=indent, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return self.model_dump(mode='json', default=str)