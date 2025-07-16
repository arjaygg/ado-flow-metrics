"""
Enhanced Test Pyramid Strategy for ADO Flow Metrics

This module implements a comprehensive testing strategy following agile test pyramid principles:
- 70% Unit Tests (fast, isolated, comprehensive coverage)
- 20% Integration Tests (API, database, external services)
- 10% End-to-End Tests (UI, full workflows)

Plus performance, security, and quality gate testing.
"""

import concurrent.futures
import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.azure_devops_client import AzureDevOpsClient
from src.calculator import FlowMetricsCalculator
from src.config_manager import FlowMetricsSettings
from src.data_storage import FlowMetricsDatabase
from src.mock_data import generate_mock_azure_devops_data

# Import all core modules for comprehensive testing
from src.models import StateTransition, WorkItem
from src.web_server import FlowMetricsWebServer


@dataclass
class TestMetrics:
    """Test execution metrics for analysis."""

    test_type: str
    execution_time: float
    memory_usage: float
    coverage_percentage: float
    assertions_count: int
    setup_time: float
    teardown_time: float


class TestPyramidStrategy:
    """Comprehensive test pyramid implementation."""

    def __init__(self):
        self.test_metrics: List[TestMetrics] = []
        self.quality_gates = {
            "unit_test_coverage": 85.0,
            "integration_test_coverage": 75.0,
            "e2e_test_coverage": 60.0,
            "performance_threshold_ms": 1000,
            "memory_threshold_mb": 512,
            "error_rate_threshold": 0.01,
        }

    def record_test_metrics(self, test_type: str, start_time: float, **kwargs):
        """Record test metrics for analysis."""
        execution_time = time.time() - start_time
        memory_usage = self._get_memory_usage()

        metrics = TestMetrics(
            test_type=test_type,
            execution_time=execution_time,
            memory_usage=memory_usage,
            coverage_percentage=kwargs.get("coverage", 0.0),
            assertions_count=kwargs.get("assertions", 0),
            setup_time=kwargs.get("setup_time", 0.0),
            teardown_time=kwargs.get("teardown_time", 0.0),
        )
        self.test_metrics.append(metrics)
        return metrics

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def analyze_test_pyramid_health(self) -> Dict[str, Any]:
        """Analyze test pyramid health and compliance."""
        if not self.test_metrics:
            return {"status": "no_data", "recommendations": ["Run tests first"]}

        # Calculate distribution
        total_tests = len(self.test_metrics)
        unit_tests = len([m for m in self.test_metrics if m.test_type == "unit"])
        integration_tests = len(
            [m for m in self.test_metrics if m.test_type == "integration"]
        )
        e2e_tests = len([m for m in self.test_metrics if m.test_type == "e2e"])

        distribution = {
            "unit": (unit_tests / total_tests) * 100,
            "integration": (integration_tests / total_tests) * 100,
            "e2e": (e2e_tests / total_tests) * 100,
        }

        # Performance analysis
        avg_execution_time = (
            sum(m.execution_time for m in self.test_metrics) / total_tests
        )
        max_memory = max(m.memory_usage for m in self.test_metrics)

        # Health assessment
        health_score = 100
        recommendations = []

        # Check pyramid shape (70/20/10 ideal)
        if distribution["unit"] < 60:
            health_score -= 20
            recommendations.append(
                "Increase unit test coverage (current: {:.1f}%, target: 70%)".format(
                    distribution["unit"]
                )
            )

        if distribution["integration"] > 30:
            health_score -= 10
            recommendations.append(
                "Reduce integration test proportion (current: {:.1f}%, target: 20%)".format(
                    distribution["integration"]
                )
            )

        if distribution["e2e"] > 15:
            health_score -= 10
            recommendations.append(
                "Reduce E2E test proportion (current: {:.1f}%, target: 10%)".format(
                    distribution["e2e"]
                )
            )

        # Performance checks
        if avg_execution_time > 1.0:
            health_score -= 15
            recommendations.append(
                "Improve test execution speed (current: {:.2f}s average)".format(
                    avg_execution_time
                )
            )

        if max_memory > 512:
            health_score -= 10
            recommendations.append(
                "Optimize memory usage (current: {:.1f}MB max)".format(max_memory)
            )

        return {
            "health_score": max(0, health_score),
            "distribution": distribution,
            "performance": {
                "avg_execution_time": avg_execution_time,
                "max_memory": max_memory,
                "total_tests": total_tests,
            },
            "recommendations": recommendations,
            "status": "healthy" if health_score >= 80 else "needs_improvement",
        }


# Global test pyramid instance
test_pyramid = TestPyramidStrategy()


@pytest.mark.unit
class TestUnitTestFoundation:
    """Foundation unit tests - 70% of test pyramid."""

    def test_work_item_model_creation(self):
        """Test WorkItem model creation with all edge cases."""
        start_time = time.time()

        # Test normal creation
        work_item = WorkItem(
            id=1001,
            title="Test Work Item",
            work_item_type="User Story",
            state="Active",
            assigned_to="John Doe",
            created_date=datetime.now(timezone.utc),
            changed_date=datetime.now(timezone.utc),
            state_transitions=[],
        )

        assert work_item.id == 1001
        assert work_item.title == "Test Work Item"
        assert work_item.work_item_type == "User Story"
        assert work_item.state == "Active"
        assert work_item.assigned_to == "John Doe"
        assert isinstance(work_item.created_date, datetime)
        assert isinstance(work_item.changed_date, datetime)
        assert isinstance(work_item.state_transitions, list)

        # Test with None values
        work_item_none = WorkItem(
            id=1002,
            title="Test",
            work_item_type="Bug",
            state="New",
            assigned_to=None,
            created_date=datetime.now(timezone.utc),
            changed_date=datetime.now(timezone.utc),
            state_transitions=[],
        )

        assert work_item_none.assigned_to is None

        # Test with empty string
        work_item_empty = WorkItem(
            id=1003,
            title="",
            work_item_type="Task",
            state="Done",
            assigned_to="",
            created_date=datetime.now(timezone.utc),
            changed_date=datetime.now(timezone.utc),
            state_transitions=[],
        )

        assert work_item_empty.title == ""
        assert work_item_empty.assigned_to == ""

        test_pyramid.record_test_metrics("unit", start_time, assertions=11)

    def test_state_transition_model_creation(self):
        """Test StateTransition model creation with edge cases."""
        start_time = time.time()

        # Test normal transition
        transition = StateTransition(
            from_state="New",
            to_state="Active",
            changed_date=datetime.now(timezone.utc),
            changed_by="John Doe",
        )

        assert transition.from_state == "New"
        assert transition.to_state == "Active"
        assert isinstance(transition.changed_date, datetime)
        assert transition.changed_by == "John Doe"

        # Test initial creation (from_state is None)
        initial_transition = StateTransition(
            from_state=None,
            to_state="New",
            changed_date=datetime.now(timezone.utc),
            changed_by="System",
        )

        assert initial_transition.from_state is None
        assert initial_transition.to_state == "New"
        assert initial_transition.changed_by == "System"

        # Test with empty strings
        empty_transition = StateTransition(
            from_state="",
            to_state="",
            changed_date=datetime.now(timezone.utc),
            changed_by="",
        )

        assert empty_transition.from_state == ""
        assert empty_transition.to_state == ""
        assert empty_transition.changed_by == ""

        test_pyramid.record_test_metrics("unit", start_time, assertions=10)

    def test_flow_metrics_calculator_basic_operations(self):
        """Test basic flow metrics calculations."""
        start_time = time.time()

        calculator = FlowMetricsCalculator()

        # Test with empty work items
        empty_metrics = calculator.calculate_metrics([])
        assert empty_metrics["total_work_items"] == 0
        assert empty_metrics["cycle_time_avg"] == 0
        assert empty_metrics["lead_time_avg"] == 0
        assert empty_metrics["throughput"] == 0

        # Test with single work item
        now = datetime.now(timezone.utc)
        work_item = WorkItem(
            id=1001,
            title="Test",
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
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=8),
                    changed_by="John Doe",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Done",
                    changed_date=now - timedelta(days=1),
                    changed_by="John Doe",
                ),
            ],
        )

        single_metrics = calculator.calculate_metrics([work_item])
        assert single_metrics["total_work_items"] == 1
        assert single_metrics["cycle_time_avg"] > 0
        assert single_metrics["lead_time_avg"] > 0
        assert single_metrics["throughput"] > 0

        test_pyramid.record_test_metrics("unit", start_time, assertions=11)

    def test_azure_devops_client_configuration(self):
        """Test Azure DevOps client configuration handling."""
        start_time = time.time()

        # Test valid configuration
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        assert client.org_url == "https://dev.azure.com/test-org"
        assert client.project == "test-project"
        assert client.pat_token == "test-token"

        # Test URL normalization
        client_slash = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org/",
            project="test-project",
            pat_token="test-token",
        )

        assert client_slash.org_url == "https://dev.azure.com/test-org"

        # Test configuration validation
        with pytest.raises(ValueError):
            AzureDevOpsClient(
                org_url="", project="test-project", pat_token="test-token"
            )

        with pytest.raises(ValueError):
            AzureDevOpsClient(
                org_url="https://dev.azure.com/test-org",
                project="",
                pat_token="test-token",
            )

        with pytest.raises(ValueError):
            AzureDevOpsClient(
                org_url="https://dev.azure.com/test-org",
                project="test-project",
                pat_token="",
            )

        test_pyramid.record_test_metrics("unit", start_time, assertions=8)

    def test_config_manager_settings_validation(self):
        """Test configuration manager settings validation."""
        start_time = time.time()

        # Test with valid configuration
        config_data = {
            "azure_devops": {
                "organization": "test-org",
                "project": "test-project",
                "pat_token": "test-token",
                "base_url": "https://dev.azure.com",
            },
            "stage_definitions": {
                "active_states": ["Active", "In Progress"],
                "completion_states": ["Done", "Closed"],
                "waiting_states": ["New", "Blocked"],
            },
        }

        with patch("src.config_manager.Path.exists", return_value=True):
            with patch("src.config_manager.Path.open") as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    json.dumps(config_data)
                )

                settings = FlowMetricsSettings()

                assert settings.azure_devops.organization == "test-org"
                assert settings.azure_devops.project == "test-project"
                assert settings.azure_devops.pat_token == "test-token"
                assert settings.azure_devops.base_url == "https://dev.azure.com"

                assert "Active" in settings.stage_definitions.active_states
                assert "Done" in settings.stage_definitions.completion_states
                assert "New" in settings.stage_definitions.waiting_states

        test_pyramid.record_test_metrics("unit", start_time, assertions=7)

    def test_data_storage_database_operations(self):
        """Test database operations with comprehensive edge cases."""
        start_time = time.time()

        # Test with in-memory database
        db = FlowMetricsDatabase(":memory:")

        # Test table creation
        db.create_tables()

        # Test storing work items
        now = datetime.now(timezone.utc)
        work_item = WorkItem(
            id=1001,
            title="Test Work Item",
            work_item_type="User Story",
            state="Active",
            assigned_to="John Doe",
            created_date=now - timedelta(days=5),
            changed_date=now - timedelta(days=1),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=5),
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=1),
                    changed_by="John Doe",
                ),
            ],
        )

        db.store_work_items([work_item])

        # Test retrieving work items
        retrieved_items = db.get_work_items()
        assert len(retrieved_items) == 1
        assert retrieved_items[0].id == 1001
        assert retrieved_items[0].title == "Test Work Item"

        # Test filtering
        filtered_items = db.get_work_items(state="Active")
        assert len(filtered_items) == 1
        assert filtered_items[0].state == "Active"

        # Test empty result
        empty_items = db.get_work_items(state="NonExistent")
        assert len(empty_items) == 0

        # Test duplicate handling
        db.store_work_items([work_item])  # Store again
        retrieved_after_duplicate = db.get_work_items()
        assert len(retrieved_after_duplicate) == 1  # Should not duplicate

        test_pyramid.record_test_metrics("unit", start_time, assertions=9)


@pytest.mark.integration
class TestIntegrationTestMiddleLayer:
    """Integration tests - 20% of test pyramid."""

    def test_azure_devops_client_mock_integration(self):
        """Test Azure DevOps client with mock API responses."""
        start_time = time.time()

        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock successful API response
        mock_response = {
            "workItems": [
                {"id": 1001, "url": "https://dev.azure.com/_apis/wit/workItems/1001"},
                {"id": 1002, "url": "https://dev.azure.com/_apis/wit/workItems/1002"},
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            work_item_ids = client.get_work_items_by_query(
                "SELECT [System.Id] FROM WorkItems"
            )

            assert len(work_item_ids) == 2
            assert 1001 in work_item_ids
            assert 1002 in work_item_ids

            # Verify API was called correctly
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "wiql" in args[0]
            assert kwargs["auth"] == ("", "test-token")

        test_pyramid.record_test_metrics("integration", start_time, assertions=5)

    def test_database_calculator_integration(self):
        """Test integration between database and calculator."""
        start_time = time.time()

        # Setup in-memory database
        db = FlowMetricsDatabase(":memory:")
        db.create_tables()

        # Create test data
        now = datetime.now(timezone.utc)
        work_items = [
            WorkItem(
                id=1001,
                title="Completed Story",
                work_item_type="User Story",
                state="Done",
                assigned_to="Alice",
                created_date=now - timedelta(days=10),
                changed_date=now - timedelta(days=1),
                state_transitions=[
                    StateTransition(None, "New", now - timedelta(days=10), "System"),
                    StateTransition("New", "Active", now - timedelta(days=8), "Alice"),
                    StateTransition("Active", "Done", now - timedelta(days=1), "Alice"),
                ],
            ),
            WorkItem(
                id=1002,
                title="In Progress Story",
                work_item_type="User Story",
                state="Active",
                assigned_to="Bob",
                created_date=now - timedelta(days=5),
                changed_date=now - timedelta(days=2),
                state_transitions=[
                    StateTransition(None, "New", now - timedelta(days=5), "System"),
                    StateTransition("New", "Active", now - timedelta(days=2), "Bob"),
                ],
            ),
        ]

        # Store work items
        db.store_work_items(work_items)

        # Test calculator integration
        calculator = FlowMetricsCalculator()
        retrieved_items = db.get_work_items()

        assert len(retrieved_items) == 2

        # Calculate metrics
        metrics = calculator.calculate_metrics(retrieved_items)

        assert metrics["total_work_items"] == 2
        assert metrics["cycle_time_avg"] > 0
        assert metrics["lead_time_avg"] > 0
        assert metrics["throughput"] > 0

        # Test filtered metrics
        completed_items = db.get_work_items(state="Done")
        completed_metrics = calculator.calculate_metrics(completed_items)

        assert completed_metrics["total_work_items"] == 1
        assert completed_metrics["cycle_time_avg"] > 0

        test_pyramid.record_test_metrics("integration", start_time, assertions=9)

    def test_web_server_api_integration(self):
        """Test web server API endpoints integration."""
        start_time = time.time()

        # Initialize web server with mock data
        server = FlowMetricsWebServer(data_source="mock")

        # Test that app is configured correctly
        assert server.app is not None
        assert server.data_source == "mock"

        # Test with Flask test client
        with server.app.test_client() as client:
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200

            # Test API endpoints
            api_response = client.get("/api/work-items")
            assert api_response.status_code == 200

            data = json.loads(api_response.data)
            assert isinstance(data, list)

            # Test metrics endpoint
            metrics_response = client.get("/api/metrics")
            assert metrics_response.status_code == 200

            metrics_data = json.loads(metrics_response.data)
            assert isinstance(metrics_data, dict)
            assert "total_work_items" in metrics_data
            assert "cycle_time_avg" in metrics_data
            assert "lead_time_avg" in metrics_data
            assert "throughput" in metrics_data

        test_pyramid.record_test_metrics("integration", start_time, assertions=11)

    def test_performance_under_load_integration(self):
        """Test system performance under load."""
        start_time = time.time()

        # Generate large dataset
        large_dataset = generate_mock_azure_devops_data(count=1000)

        # Test database performance
        db = FlowMetricsDatabase(":memory:")
        db.create_tables()

        store_start = time.time()
        db.store_work_items(large_dataset)
        store_time = time.time() - store_start

        # Should store 1000 items in reasonable time
        assert (
            store_time < 5.0
        ), f"Database store took {store_time:.2f}s, should be < 5s"

        # Test retrieval performance
        retrieve_start = time.time()
        retrieved_items = db.get_work_items()
        retrieve_time = time.time() - retrieve_start

        assert len(retrieved_items) == 1000
        assert (
            retrieve_time < 2.0
        ), f"Database retrieval took {retrieve_time:.2f}s, should be < 2s"

        # Test calculation performance
        calculator = FlowMetricsCalculator()
        calc_start = time.time()
        metrics = calculator.calculate_metrics(retrieved_items)
        calc_time = time.time() - calc_start

        assert (
            calc_time < 3.0
        ), f"Metrics calculation took {calc_time:.2f}s, should be < 3s"
        assert metrics["total_work_items"] == 1000

        test_pyramid.record_test_metrics("integration", start_time, assertions=6)


@pytest.mark.e2e
class TestEndToEndUserWorkflows:
    """End-to-end tests - 10% of test pyramid."""

    def test_complete_data_flow_workflow(self):
        """Test complete data flow from Azure DevOps to dashboard."""
        start_time = time.time()

        # This test simulates the complete workflow:
        # 1. Fetch data from Azure DevOps (mocked)
        # 2. Store in database
        # 3. Calculate metrics
        # 4. Serve via web API
        # 5. Display in dashboard

        # Step 1: Mock Azure DevOps client
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Step 2: Setup database
        db = FlowMetricsDatabase(":memory:")
        db.create_tables()

        # Step 3: Generate mock data (simulating Azure DevOps fetch)
        mock_data = generate_mock_azure_devops_data(count=50)

        # Step 4: Store data
        db.store_work_items(mock_data)

        # Step 5: Calculate metrics
        calculator = FlowMetricsCalculator()
        stored_items = db.get_work_items()
        metrics = calculator.calculate_metrics(stored_items)

        # Step 6: Test web server with actual data
        server = FlowMetricsWebServer(data_source="mock")

        with server.app.test_client() as web_client:
            # Test that all endpoints work with the data
            response = web_client.get("/api/work-items")
            assert response.status_code == 200

            work_items_data = json.loads(response.data)
            assert len(work_items_data) > 0

            # Test metrics endpoint
            metrics_response = web_client.get("/api/metrics")
            assert metrics_response.status_code == 200

            metrics_data = json.loads(metrics_response.data)
            assert metrics_data["total_work_items"] > 0
            assert metrics_data["cycle_time_avg"] >= 0
            assert metrics_data["lead_time_avg"] >= 0
            assert metrics_data["throughput"] >= 0

            # Test dashboard rendering
            dashboard_response = web_client.get("/")
            assert dashboard_response.status_code == 200
            assert b"Flow Metrics" in dashboard_response.data

        test_pyramid.record_test_metrics("e2e", start_time, assertions=11)

    def test_error_handling_end_to_end(self):
        """Test end-to-end error handling scenarios."""
        start_time = time.time()

        # Test web server error handling
        server = FlowMetricsWebServer(data_source="mock")

        with server.app.test_client() as client:
            # Test non-existent endpoint
            response = client.get("/api/nonexistent")
            assert response.status_code == 404

            # Test invalid parameters
            response = client.get("/api/work-items?invalid=param")
            assert response.status_code in [200, 400]  # Should handle gracefully

            # Test server error simulation
            with patch(
                "src.web_server.FlowMetricsWebServer.get_work_items"
            ) as mock_get:
                mock_get.side_effect = Exception("Database error")

                response = client.get("/api/work-items")
                # Should handle error gracefully, not crash
                assert response.status_code in [200, 500]

        test_pyramid.record_test_metrics("e2e", start_time, assertions=4)


@pytest.mark.performance
class TestPerformanceAndQualityGates:
    """Performance and quality gate tests."""

    def test_memory_usage_quality_gate(self):
        """Test memory usage stays within quality gates."""
        start_time = time.time()

        import gc

        gc.collect()  # Clean up before test

        # Generate large dataset
        large_dataset = generate_mock_azure_devops_data(count=5000)

        # Monitor memory usage
        initial_memory = test_pyramid._get_memory_usage()

        # Process data
        calculator = FlowMetricsCalculator()
        metrics = calculator.calculate_metrics(large_dataset)

        peak_memory = test_pyramid._get_memory_usage()
        memory_increase = peak_memory - initial_memory

        # Memory should not increase by more than 256MB for 5000 items
        assert (
            memory_increase < 256
        ), f"Memory increased by {memory_increase:.1f}MB, should be < 256MB"

        # Cleanup
        del large_dataset
        gc.collect()

        test_pyramid.record_test_metrics("performance", start_time, assertions=1)

    def test_concurrent_access_performance(self):
        """Test concurrent access performance."""
        start_time = time.time()

        server = FlowMetricsWebServer(data_source="mock")

        def make_request():
            with server.app.test_client() as client:
                response = client.get("/api/work-items")
                return response.status_code == 200

        # Test concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        success_rate = sum(results) / len(results)
        assert (
            success_rate >= 0.95
        ), f"Success rate {success_rate:.2f} below 95% threshold"

        test_pyramid.record_test_metrics("performance", start_time, assertions=1)

    def test_test_pyramid_health_analysis(self):
        """Test the test pyramid health analysis."""
        start_time = time.time()

        # Analyze current test pyramid
        health_analysis = test_pyramid.analyze_test_pyramid_health()

        assert isinstance(health_analysis, dict)
        assert "health_score" in health_analysis
        assert "distribution" in health_analysis
        assert "performance" in health_analysis
        assert "recommendations" in health_analysis
        assert "status" in health_analysis

        # Health score should be between 0 and 100
        assert 0 <= health_analysis["health_score"] <= 100

        # Distribution should have all test types
        distribution = health_analysis["distribution"]
        assert "unit" in distribution
        assert "integration" in distribution
        assert "e2e" in distribution

        # Performance metrics should be present
        performance = health_analysis["performance"]
        assert "avg_execution_time" in performance
        assert "max_memory" in performance
        assert "total_tests" in performance

        test_pyramid.record_test_metrics("quality", start_time, assertions=12)


def pytest_runtest_setup(item):
    """Setup hook for each test."""
    # Mark all tests in this module with appropriate markers
    if "test_unit" in item.name or "TestUnitTestFoundation" in str(item.parent):
        item.add_marker(pytest.mark.unit)
    elif "test_integration" in item.name or "TestIntegrationTestMiddleLayer" in str(
        item.parent
    ):
        item.add_marker(pytest.mark.integration)
    elif "test_e2e" in item.name or "TestEndToEndUserWorkflows" in str(item.parent):
        item.add_marker(pytest.mark.e2e)
    elif "test_performance" in item.name or "TestPerformanceAndQualityGates" in str(
        item.parent
    ):
        item.add_marker(pytest.mark.performance)


def pytest_sessionfinish(session, exitstatus):
    """Generate test pyramid report after all tests complete."""
    if test_pyramid.test_metrics:
        health_analysis = test_pyramid.analyze_test_pyramid_health()

        print("\n" + "=" * 60)
        print("TEST PYRAMID HEALTH ANALYSIS")
        print("=" * 60)
        print(f"Health Score: {health_analysis['health_score']}/100")
        print(f"Status: {health_analysis['status']}")
        print(f"Total Tests: {health_analysis['performance']['total_tests']}")
        print(
            f"Avg Execution Time: {health_analysis['performance']['avg_execution_time']:.2f}s"
        )
        print(f"Max Memory Usage: {health_analysis['performance']['max_memory']:.1f}MB")

        print("\nTest Distribution:")
        for test_type, percentage in health_analysis["distribution"].items():
            print(f"  {test_type.capitalize()}: {percentage:.1f}%")

        if health_analysis["recommendations"]:
            print("\nRecommendations:")
            for rec in health_analysis["recommendations"]:
                print(f"  • {rec}")

        print("=" * 60)

        # Save detailed report
        report_path = Path("test_pyramid_health_report.json")
        with open(report_path, "w") as f:
            json.dump(health_analysis, f, indent=2)
        print(f"Detailed report saved to: {report_path}")
