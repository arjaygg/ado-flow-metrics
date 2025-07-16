"""
Advanced API and WIQL Performance Tests

This module tests the performance of Azure DevOps API interactions and WIQL queries
specifically for flow metrics calculations. Tests follow performance testing best practices.
"""

import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests.exceptions import RequestException, Timeout

from src.azure_devops_client import AzureDevOpsClient
from src.calculator import FlowMetricsCalculator
from src.mock_data import generate_mock_azure_devops_data
from src.models import StateTransition, WorkItem


@pytest.mark.performance
class TestWIQLQueryPerformance:
    """Test WIQL query performance and optimization."""

    def test_basic_wiql_query_performance(self):
        """Test basic WIQL query performance."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock response for basic query
        mock_response = {
            "workItems": [
                {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                for i in range(1, 101)
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            # Test basic query performance
            start_time = time.time()

            query = "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'User Story'"
            work_item_ids = client.get_work_items_by_query(query)

            query_time = time.time() - start_time

            # Query should complete within 1 second
            assert (
                query_time < 1.0
            ), f"WIQL query took {query_time:.2f}s, should be < 1s"
            assert len(work_item_ids) == 100

            # Verify correct API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "wiql" in call_args[0][0]
            assert call_args[1]["json"]["query"] == query

    def test_complex_wiql_query_performance(self):
        """Test complex WIQL query performance."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock response for complex query
        mock_response = {
            "workItems": [
                {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                for i in range(1, 501)
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            # Test complex query with multiple conditions
            start_time = time.time()

            complex_query = """
            SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
            FROM WorkItems
            WHERE [System.WorkItemType] IN ('User Story', 'Bug', 'Task')
            AND [System.State] NOT IN ('Removed', 'Deleted')
            AND [System.CreatedDate] >= @Today - 30
            AND [System.TeamProject] = @project
            ORDER BY [System.CreatedDate] DESC
            """

            work_item_ids = client.get_work_items_by_query(complex_query)

            query_time = time.time() - start_time

            # Complex query should complete within 2 seconds
            assert (
                query_time < 2.0
            ), f"Complex WIQL query took {query_time:.2f}s, should be < 2s"
            assert len(work_item_ids) == 500

    def test_wiql_query_with_date_filters_performance(self):
        """Test WIQL query performance with date filters."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock response for date-filtered query
        mock_response = {
            "workItems": [
                {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                for i in range(1, 201)
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            # Test date filter query
            start_time = time.time()

            date_query = """
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.WorkItemType] = 'User Story'
            AND [System.CreatedDate] >= '2024-01-01'
            AND [System.ChangedDate] <= '2024-12-31'
            AND [System.State] IN ('Active', 'Resolved', 'Closed')
            """

            work_item_ids = client.get_work_items_by_query(date_query)

            query_time = time.time() - start_time

            # Date query should complete within 1.5 seconds
            assert (
                query_time < 1.5
            ), f"Date-filtered WIQL query took {query_time:.2f}s, should be < 1.5s"
            assert len(work_item_ids) == 200

    def test_wiql_query_batch_performance(self):
        """Test performance of batch WIQL queries."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock responses for batch queries
        mock_responses = [
            {
                "workItems": [
                    {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                    for i in range(batch * 50 + 1, (batch + 1) * 50 + 1)
                ]
            }
            for batch in range(5)
        ]

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.side_effect = mock_responses

            # Test batch query performance
            start_time = time.time()

            queries = [
                f"SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'User Story' AND [System.Id] > {i * 50}"
                for i in range(5)
            ]

            all_work_item_ids = []
            for query in queries:
                work_item_ids = client.get_work_items_by_query(query)
                all_work_item_ids.extend(work_item_ids)

            batch_query_time = time.time() - start_time

            # Batch queries should complete within 3 seconds
            assert (
                batch_query_time < 3.0
            ), f"Batch WIQL queries took {batch_query_time:.2f}s, should be < 3s"
            assert len(all_work_item_ids) == 250  # 5 batches * 50 items each

            # Verify all queries were called
            assert mock_post.call_count == 5


@pytest.mark.performance
class TestAPIResponsePerformance:
    """Test API response handling and performance."""

    def test_work_item_details_fetch_performance(self):
        """Test performance of fetching work item details."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock work item details response
        mock_details = {
            "id": 1001,
            "fields": {
                "System.Title": "Test Work Item",
                "System.WorkItemType": "User Story",
                "System.State": "Active",
                "System.AssignedTo": {"displayName": "John Doe"},
                "System.CreatedDate": "2024-01-01T00:00:00Z",
                "System.ChangedDate": "2024-01-02T00:00:00Z",
                "System.Description": "A test work item description",
                "System.Tags": "test; performance; api",
            },
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_details

            # Test single work item fetch
            start_time = time.time()

            work_item = client.get_work_item_details(1001)

            fetch_time = time.time() - start_time

            # Single fetch should complete within 0.5 seconds
            assert (
                fetch_time < 0.5
            ), f"Work item fetch took {fetch_time:.2f}s, should be < 0.5s"
            assert work_item.id == 1001
            assert work_item.title == "Test Work Item"
            assert work_item.work_item_type == "User Story"
            assert work_item.state == "Active"
            assert work_item.assigned_to == "John Doe"

    def test_batch_work_item_details_fetch_performance(self):
        """Test performance of batch fetching work item details."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock batch response
        work_item_ids = list(range(1001, 1101))  # 100 work items
        mock_batch_response = {
            "value": [
                {
                    "id": work_id,
                    "fields": {
                        "System.Title": f"Test Work Item {work_id}",
                        "System.WorkItemType": "User Story",
                        "System.State": "Active",
                        "System.AssignedTo": {"displayName": "John Doe"},
                        "System.CreatedDate": "2024-01-01T00:00:00Z",
                        "System.ChangedDate": "2024-01-02T00:00:00Z",
                    },
                }
                for work_id in work_item_ids
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_batch_response

            # Test batch fetch performance
            start_time = time.time()

            work_items = client.get_work_items_details(work_item_ids)

            batch_fetch_time = time.time() - start_time

            # Batch fetch should complete within 2 seconds
            assert (
                batch_fetch_time < 2.0
            ), f"Batch fetch took {batch_fetch_time:.2f}s, should be < 2s"
            assert len(work_items) == 100

            # Verify all work items were fetched correctly
            for i, work_item in enumerate(work_items):
                assert work_item.id == work_item_ids[i]
                assert work_item.title == f"Test Work Item {work_item_ids[i]}"

    def test_concurrent_api_requests_performance(self):
        """Test performance of concurrent API requests."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock response for concurrent requests
        mock_response = {
            "workItems": [
                {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                for i in range(1, 51)
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response

            # Test concurrent requests
            start_time = time.time()

            def make_query(query_id):
                query = f"SELECT [System.Id] FROM WorkItems WHERE [System.Id] > {query_id * 50}"
                return client.get_work_items_by_query(query)

            # Run 10 concurrent queries
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_query, i) for i in range(10)]
                results = [future.result() for future in as_completed(futures)]

            concurrent_time = time.time() - start_time

            # Concurrent requests should complete within 3 seconds
            assert (
                concurrent_time < 3.0
            ), f"Concurrent requests took {concurrent_time:.2f}s, should be < 3s"
            assert len(results) == 10

            # Each result should have 50 items
            for result in results:
                assert len(result) == 50

    def test_api_error_handling_performance(self):
        """Test performance of API error handling."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Test timeout handling
        with patch("requests.post") as mock_post:
            mock_post.side_effect = Timeout("Request timed out")

            start_time = time.time()

            try:
                client.get_work_items_by_query("SELECT [System.Id] FROM WorkItems")
            except Exception:
                pass  # Expected to fail

            error_handling_time = time.time() - start_time

            # Error handling should be fast
            assert (
                error_handling_time < 1.0
            ), f"Error handling took {error_handling_time:.2f}s, should be < 1s"

        # Test 404 error handling
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.text = "Not Found"

            start_time = time.time()

            try:
                client.get_work_items_by_query("SELECT [System.Id] FROM WorkItems")
            except Exception:
                pass  # Expected to fail

            error_handling_time = time.time() - start_time

            # Error handling should be fast
            assert (
                error_handling_time < 1.0
            ), f"404 error handling took {error_handling_time:.2f}s, should be < 1s"

    def test_large_response_handling_performance(self):
        """Test performance with large API responses."""
        client = AzureDevOpsClient(
            org_url="https://dev.azure.com/test-org",
            project="test-project",
            pat_token="test-token",
        )

        # Mock large response (5000 work items)
        large_response = {
            "workItems": [
                {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                for i in range(1, 5001)
            ]
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = large_response

            # Test large response handling
            start_time = time.time()

            work_item_ids = client.get_work_items_by_query(
                "SELECT [System.Id] FROM WorkItems"
            )

            large_response_time = time.time() - start_time

            # Large response should be handled within 5 seconds
            assert (
                large_response_time < 5.0
            ), f"Large response took {large_response_time:.2f}s, should be < 5s"
            assert len(work_item_ids) == 5000


@pytest.mark.performance
class TestFlowMetricsCalculationPerformance:
    """Test flow metrics calculation performance."""

    def test_cycle_time_calculation_performance(self):
        """Test cycle time calculation performance."""
        calculator = FlowMetricsCalculator()

        # Generate large dataset
        large_dataset = generate_mock_azure_devops_data(count=1000)

        # Test cycle time calculation
        start_time = time.time()

        cycle_times = []
        for work_item in large_dataset:
            cycle_time = calculator.calculate_cycle_time(work_item)
            cycle_times.append(cycle_time)

        calc_time = time.time() - start_time

        # Calculation should complete within 2 seconds
        assert (
            calc_time < 2.0
        ), f"Cycle time calculation took {calc_time:.2f}s, should be < 2s"
        assert len(cycle_times) == 1000

        # Verify calculations are reasonable
        valid_cycle_times = [ct for ct in cycle_times if ct > 0]
        assert len(valid_cycle_times) > 0

    def test_lead_time_calculation_performance(self):
        """Test lead time calculation performance."""
        calculator = FlowMetricsCalculator()

        # Generate large dataset
        large_dataset = generate_mock_azure_devops_data(count=1000)

        # Test lead time calculation
        start_time = time.time()

        lead_times = []
        for work_item in large_dataset:
            lead_time = calculator.calculate_lead_time(work_item)
            lead_times.append(lead_time)

        calc_time = time.time() - start_time

        # Calculation should complete within 2 seconds
        assert (
            calc_time < 2.0
        ), f"Lead time calculation took {calc_time:.2f}s, should be < 2s"
        assert len(lead_times) == 1000

        # Verify calculations are reasonable
        valid_lead_times = [lt for lt in lead_times if lt > 0]
        assert len(valid_lead_times) > 0

    def test_throughput_calculation_performance(self):
        """Test throughput calculation performance."""
        calculator = FlowMetricsCalculator()

        # Generate large dataset with time-based data
        large_dataset = generate_mock_azure_devops_data(count=2000)

        # Test throughput calculation
        start_time = time.time()

        # Calculate throughput for different time windows
        daily_throughput = calculator.calculate_throughput(
            large_dataset, time_window="daily"
        )
        weekly_throughput = calculator.calculate_throughput(
            large_dataset, time_window="weekly"
        )
        monthly_throughput = calculator.calculate_throughput(
            large_dataset, time_window="monthly"
        )

        calc_time = time.time() - start_time

        # Calculation should complete within 3 seconds
        assert (
            calc_time < 3.0
        ), f"Throughput calculation took {calc_time:.2f}s, should be < 3s"

        # Verify calculations are reasonable
        assert daily_throughput >= 0
        assert weekly_throughput >= 0
        assert monthly_throughput >= 0

    def test_comprehensive_metrics_calculation_performance(self):
        """Test comprehensive metrics calculation performance."""
        calculator = FlowMetricsCalculator()

        # Generate very large dataset
        very_large_dataset = generate_mock_azure_devops_data(count=5000)

        # Test comprehensive metrics calculation
        start_time = time.time()

        metrics = calculator.calculate_metrics(very_large_dataset)

        calc_time = time.time() - start_time

        # Comprehensive calculation should complete within 10 seconds
        assert (
            calc_time < 10.0
        ), f"Comprehensive metrics calculation took {calc_time:.2f}s, should be < 10s"

        # Verify all metrics are calculated
        assert "total_work_items" in metrics
        assert "cycle_time_avg" in metrics
        assert "lead_time_avg" in metrics
        assert "throughput" in metrics
        assert "wip" in metrics
        assert "flow_efficiency" in metrics

        # Verify metrics are reasonable
        assert metrics["total_work_items"] == 5000
        assert metrics["cycle_time_avg"] >= 0
        assert metrics["lead_time_avg"] >= 0
        assert metrics["throughput"] >= 0

    def test_memory_efficient_calculation_performance(self):
        """Test memory-efficient calculation performance."""
        calculator = FlowMetricsCalculator()

        # Test streaming/batch processing of large datasets
        import gc

        # Monitor memory usage
        initial_memory = self._get_memory_usage()

        # Process data in batches
        batch_size = 1000
        total_items = 10000

        start_time = time.time()

        aggregated_metrics = {
            "total_work_items": 0,
            "cycle_time_sum": 0,
            "lead_time_sum": 0,
            "throughput_sum": 0,
        }

        for batch_start in range(0, total_items, batch_size):
            batch_end = min(batch_start + batch_size, total_items)
            batch_data = generate_mock_azure_devops_data(count=batch_end - batch_start)

            batch_metrics = calculator.calculate_metrics(batch_data)

            # Aggregate metrics
            aggregated_metrics["total_work_items"] += batch_metrics["total_work_items"]
            aggregated_metrics["cycle_time_sum"] += (
                batch_metrics["cycle_time_avg"] * batch_metrics["total_work_items"]
            )
            aggregated_metrics["lead_time_sum"] += (
                batch_metrics["lead_time_avg"] * batch_metrics["total_work_items"]
            )
            aggregated_metrics["throughput_sum"] += batch_metrics["throughput"]

            # Clean up batch data
            del batch_data
            gc.collect()

        calc_time = time.time() - start_time
        peak_memory = self._get_memory_usage()

        # Memory-efficient calculation should complete within 20 seconds
        assert (
            calc_time < 20.0
        ), f"Memory-efficient calculation took {calc_time:.2f}s, should be < 20s"

        # Memory usage should not increase dramatically
        memory_increase = peak_memory - initial_memory
        assert (
            memory_increase < 512
        ), f"Memory increased by {memory_increase:.1f}MB, should be < 512MB"

        # Verify aggregated metrics
        assert aggregated_metrics["total_work_items"] == total_items

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil

            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


@pytest.mark.performance
class TestPerformanceRegression:
    """Test performance regression detection."""

    def test_performance_baseline_establishment(self):
        """Establish performance baselines for regression testing."""
        # Define performance baselines
        baselines = {
            "wiql_query_time": 1.0,  # seconds
            "work_item_fetch_time": 0.5,  # seconds
            "cycle_time_calc_time": 2.0,  # seconds for 1000 items
            "lead_time_calc_time": 2.0,  # seconds for 1000 items
            "throughput_calc_time": 3.0,  # seconds for 2000 items
            "comprehensive_metrics_time": 10.0,  # seconds for 5000 items
            "memory_usage_threshold": 512,  # MB
            "concurrent_requests_time": 3.0,  # seconds for 10 requests
        }

        # Save baselines to file for future regression testing
        baseline_file = Path("performance_baselines.json")
        with open(baseline_file, "w") as f:
            json.dump(baselines, f, indent=2)

        assert baseline_file.exists()

        # Load and verify baselines
        with open(baseline_file, "r") as f:
            loaded_baselines = json.load(f)

        assert loaded_baselines == baselines

    def test_performance_regression_detection(self):
        """Test performance regression detection mechanism."""
        # Load performance baselines
        baseline_file = Path("performance_baselines.json")

        if baseline_file.exists():
            with open(baseline_file, "r") as f:
                baselines = json.load(f)
        else:
            # Use default baselines if file doesn't exist
            baselines = {
                "wiql_query_time": 1.0,
                "work_item_fetch_time": 0.5,
                "cycle_time_calc_time": 2.0,
                "lead_time_calc_time": 2.0,
                "throughput_calc_time": 3.0,
                "comprehensive_metrics_time": 10.0,
                "memory_usage_threshold": 512,
                "concurrent_requests_time": 3.0,
            }

        # Test regression detection thresholds
        regression_threshold = 1.2  # 20% performance degradation

        # Simulate performance measurements
        current_performance = {
            "wiql_query_time": 0.8,  # Better than baseline
            "work_item_fetch_time": 0.4,  # Better than baseline
            "cycle_time_calc_time": 1.8,  # Better than baseline
            "lead_time_calc_time": 2.5,  # Regression (25% slower)
            "throughput_calc_time": 2.8,  # Better than baseline
            "comprehensive_metrics_time": 12.0,  # Regression (20% slower)
            "memory_usage_threshold": 400,  # Better than baseline
            "concurrent_requests_time": 2.5,  # Better than baseline
        }

        # Check for regressions
        regressions = []
        for metric, current_value in current_performance.items():
            baseline_value = baselines.get(metric, 0)
            if current_value > baseline_value * regression_threshold:
                regression_pct = (
                    (current_value - baseline_value) / baseline_value
                ) * 100
                regressions.append(
                    {
                        "metric": metric,
                        "baseline": baseline_value,
                        "current": current_value,
                        "regression_pct": regression_pct,
                    }
                )

        # Report regressions
        if regressions:
            print("\nPerformance Regressions Detected:")
            for regression in regressions:
                print(
                    f"  {regression['metric']}: {regression['baseline']:.2f} -> {regression['current']:.2f} "
                    f"({regression['regression_pct']:.1f}% slower)"
                )

        # For testing purposes, we expect some regressions in our simulated data
        assert (
            len(regressions) == 2
        )  # lead_time_calc_time and comprehensive_metrics_time
        assert any(r["metric"] == "lead_time_calc_time" for r in regressions)
        assert any(r["metric"] == "comprehensive_metrics_time" for r in regressions)


def create_performance_test_suite():
    """Create a comprehensive performance test suite."""
    test_suite = {
        "wiql_performance": TestWIQLQueryPerformance,
        "api_performance": TestAPIResponsePerformance,
        "calculation_performance": TestFlowMetricsCalculationPerformance,
        "regression_testing": TestPerformanceRegression,
    }

    return test_suite


if __name__ == "__main__":
    # Run performance tests if script is executed directly
    pytest.main([__file__, "-v", "-m", "performance"])
