"""
Tests for historical data storage functionality.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from src.data_storage import FlowMetricsDatabase
from src.models import WorkItem, StateTransition, FlowMetrics
from src.config_manager import FlowMetricsSettings


class TestFlowMetricsDatabase:
    """Test FlowMetricsDatabase functionality."""

    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Mock(spec=FlowMetricsSettings)
            # Create the data_management mock with the expected structure
            data_management = Mock()
            data_management.data_directory = Path(temp_dir)
            config.data_management = data_management
            yield config

    @pytest.fixture
    def database(self, temp_db_config):
        """Create database instance for testing."""
        return FlowMetricsDatabase(temp_db_config)

    @pytest.fixture
    def sample_work_item(self):
        """Create sample work item for testing."""
        now = datetime.now(timezone.utc)
        return WorkItem(
            id=1001,
            title="Test Work Item",
            type="User Story",
            state="Done",
            assigned_to="Test User",
            created_date=now - timedelta(days=10),
            closed_date=now - timedelta(days=2),
            activated_date=now - timedelta(days=8),
            transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    transition_date=now - timedelta(days=10),
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    transition_date=now - timedelta(days=8),
                    changed_by="Test User",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Done",
                    transition_date=now - timedelta(days=2),
                    changed_by="Test User",
                ),
            ],
        )

    @pytest.fixture
    def sample_flow_metrics(self):
        """Create sample flow metrics for testing."""
        now = datetime.now(timezone.utc)
        return FlowMetrics(
            period_start=now - timedelta(days=30),
            period_end=now,
            total_items=100,
            completed_items=85,
            average_lead_time=10.5,
            median_lead_time=9.0,
            average_cycle_time=7.5,
            median_cycle_time=6.0,
            throughput_per_day=2.8,
            throughput_per_week=20.0,
            throughput_per_month=85.0,
            current_wip=25,
            flow_efficiency=75.0,
        )

    def test_database_initialization(self, database):
        """Test database initialization creates tables."""
        assert database.db_path.exists()

        # Check that tables were created
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                "executions",
                "work_items",
                "state_transitions",
                "flow_metrics",
            ]
            for table in expected_tables:
                assert table in tables

    def test_start_and_complete_execution(self, database):
        """Test execution tracking functionality."""
        # Start execution
        execution_id = database.start_execution("test-org", "test-project")
        assert isinstance(execution_id, int)
        assert execution_id > 0

        # Complete execution
        database.complete_execution(execution_id, 50, 40, 120.5)

        # Verify execution was stored correctly
        execution = database.get_execution_by_id(execution_id)
        assert execution is not None
        assert execution["organization"] == "test-org"
        assert execution["project"] == "test-project"
        assert execution["work_items_count"] == 50
        assert execution["completed_items_count"] == 40
        assert execution["execution_duration_seconds"] == 120.5
        assert execution["status"] == "completed"

    def test_execution_with_error(self, database):
        """Test execution tracking with error."""
        execution_id = database.start_execution("test-org", "test-project")
        database.complete_execution(execution_id, 0, 0, 30.0, "Connection timeout")

        execution = database.get_execution_by_id(execution_id)
        assert execution["status"] == "failed"
        assert execution["error_message"] == "Connection timeout"

    def test_store_work_items(self, database, sample_work_item):
        """Test storing work items."""
        execution_id = database.start_execution("test-org", "test-project")
        database.store_work_items(execution_id, [sample_work_item])

        # Verify work item was stored
        work_items = database.get_work_items_for_execution(execution_id)
        assert len(work_items) == 1

        stored_item = work_items[0]
        assert stored_item["id"] == sample_work_item.id
        assert stored_item["title"] == sample_work_item.title
        assert stored_item["type"] == sample_work_item.type
        assert stored_item["state"] == sample_work_item.state
        assert stored_item["assigned_to"] == sample_work_item.assigned_to

    def test_store_state_transitions(self, database, sample_work_item):
        """Test storing state transitions."""
        execution_id = database.start_execution("test-org", "test-project")
        database.store_work_items(execution_id, [sample_work_item])

        # Verify state transitions were stored
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM state_transitions 
                WHERE work_item_id = ? AND execution_id = ?
                ORDER BY transition_date
            """,
                (sample_work_item.id, execution_id),
            )

            transitions = cursor.fetchall()
            assert len(transitions) == 3  # Should match the sample work item

            # Check first transition
            assert transitions[0]["from_state"] is None
            assert transitions[0]["to_state"] == "New"
            assert transitions[0]["changed_by"] == "System"

    def test_store_flow_metrics(self, database, sample_flow_metrics):
        """Test storing flow metrics."""
        execution_id = database.start_execution("test-org", "test-project")
        database.store_flow_metrics(execution_id, sample_flow_metrics)

        # Verify flow metrics were stored
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM flow_metrics WHERE execution_id = ?", (execution_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row["total_items"] == sample_flow_metrics.total_items
            assert row["completed_items"] == sample_flow_metrics.completed_items
            assert row["average_lead_time"] == sample_flow_metrics.average_lead_time
            assert row["throughput_per_day"] == sample_flow_metrics.throughput_per_day

    def test_get_recent_executions(self, database):
        """Test retrieving recent executions."""
        # Create multiple executions
        execution_ids = []
        for i in range(5):
            execution_id = database.start_execution(f"org-{i}", f"project-{i}")
            database.complete_execution(execution_id, i * 10, i * 8, 60.0)
            execution_ids.append(execution_id)

        # Get recent executions
        recent = database.get_recent_executions(limit=3)
        assert len(recent) == 3

        # Should be ordered by timestamp descending
        assert recent[0]["id"] == execution_ids[-1]  # Most recent
        assert recent[1]["id"] == execution_ids[-2]
        assert recent[2]["id"] == execution_ids[-3]

    def test_get_historical_metrics(self, database, sample_flow_metrics):
        """Test retrieving historical metrics."""
        # Create executions with metrics
        for i in range(3):
            execution_id = database.start_execution("test-org", "test-project")
            database.complete_execution(execution_id, 100, 80, 120.0)
            database.store_flow_metrics(execution_id, sample_flow_metrics)

        # Get historical metrics
        historical = database.get_historical_metrics(days_back=7)
        assert len(historical) == 3

        # Verify data structure
        for metrics in historical:
            assert "execution_timestamp" in metrics
            assert "organization" in metrics
            assert "project" in metrics
            assert "total_items" in metrics

    def test_get_throughput_trend(self, database, sample_flow_metrics):
        """Test retrieving throughput trend data."""
        # Create executions over time
        for i in range(5):
            execution_id = database.start_execution("test-org", "test-project")
            database.complete_execution(execution_id, 100, 80, 120.0)
            database.store_flow_metrics(execution_id, sample_flow_metrics)

        # Get throughput trend
        trend = database.get_throughput_trend(days_back=30)
        assert len(trend) == 5

        # Verify trend data structure
        for point in trend:
            assert "date" in point
            assert "throughput_per_day" in point
            assert "current_wip" in point
            assert "average_lead_time" in point

    def test_cleanup_old_data(self, database):
        """Test cleaning up old execution data."""
        # Create old and new executions
        old_execution_id = database.start_execution("old-org", "old-project")

        # Mock old timestamp
        with database._get_connection() as conn:
            cursor = conn.cursor()
            old_date = datetime.now(timezone.utc) - timedelta(days=400)
            cursor.execute(
                "UPDATE executions SET timestamp = ? WHERE id = ?",
                (old_date, old_execution_id),
            )
            conn.commit()

        new_execution_id = database.start_execution("new-org", "new-project")

        # Cleanup old data (keep 365 days)
        deleted_count = database.cleanup_old_data(days_to_keep=365)
        assert deleted_count == 1

        # Verify old execution is gone, new one remains
        assert database.get_execution_by_id(old_execution_id) is None
        assert database.get_execution_by_id(new_execution_id) is not None

    def test_export_data(self, database, sample_work_item, sample_flow_metrics):
        """Test exporting data to JSON."""
        # Create test data
        execution_id = database.start_execution("test-org", "test-project")
        database.store_work_items(execution_id, [sample_work_item])
        database.store_flow_metrics(execution_id, sample_flow_metrics)
        database.complete_execution(execution_id, 1, 1, 60.0)

        # Export data
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            database.export_data(export_path, [execution_id])

            # Verify export file was created and contains data
            assert export_path.exists()

            import json

            with open(export_path) as f:
                export_data = json.load(f)

            assert "exported_at" in export_data
            assert "executions" in export_data
            assert len(export_data["executions"]) == 1

            execution_data = export_data["executions"][0]
            assert execution_data["organization"] == "test-org"
            assert execution_data["project"] == "test-project"
        finally:
            export_path.unlink(missing_ok=True)

    def test_database_error_handling(self, database):
        """Test database error handling."""
        # Test with invalid execution ID
        assert database.get_execution_by_id(99999) is None

        # Test get work items for non-existent execution
        work_items = database.get_work_items_for_execution(99999)
        assert len(work_items) == 0

    def test_json_field_serialization(self, database):
        """Test JSON field serialization and deserialization."""
        now = datetime.now(timezone.utc)
        work_item = WorkItem(
            id=1002,
            title="JSON Test Item",
            type="Bug",
            state="New",
            created_date=now,
            tags=["urgent", "customer-facing"],
            custom_fields={"priority_score": 85, "customer_id": "CUST-123"},
        )

        execution_id = database.start_execution("test-org", "test-project")
        database.store_work_items(execution_id, [work_item])

        # Retrieve and verify JSON fields were properly serialized/deserialized
        stored_items = database.get_work_items_for_execution(execution_id)
        stored_item = stored_items[0]

        assert stored_item["tags"] == ["urgent", "customer-facing"]
        assert stored_item["custom_fields"] == {
            "priority_score": 85,
            "customer_id": "CUST-123",
        }
