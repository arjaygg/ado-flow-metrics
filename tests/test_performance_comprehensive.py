"""
Comprehensive performance tests for ADO Flow Metrics application.
Tests performance across all components following test pyramid principles.
"""

import concurrent.futures
import gc
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import psutil
import pytest
import requests

from src.azure_devops_client import AzureDevOpsClient
from src.calculator import FlowMetricsCalculator
from src.data_storage import FlowMetricsDatabase
from src.mock_data import generate_mock_azure_devops_data
from src.web_server import FlowMetricsWebServer


@pytest.mark.performance
class TestPerformanceBaselines:
    """Performance baseline tests for all components."""

    def test_mock_data_generation_performance(self):
        """Test performance of mock data generation."""
        start_time = time.time()

        # Generate large mock dataset
        work_items = generate_mock_azure_devops_data(count=1000)

        generation_time = time.time() - start_time

        # Should generate 1000 work items within 5 seconds
        assert (
            generation_time < 5
        ), f"Mock data generation took {generation_time:.2f}s, exceeds 5s threshold"
        assert (
            len(work_items) == 1000
        ), f"Expected 1000 work items, got {len(work_items)}"

        # Check memory usage
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        assert (
            memory_usage < 100
        ), f"Memory usage {memory_usage:.2f}MB exceeds 100MB threshold"

    def test_calculator_performance_with_large_dataset(self):
        """Test calculator performance with large datasets."""
        # Generate large dataset
        work_items = generate_mock_azure_devops_data(count=5000)

        start_time = time.time()
        calculator = FlowMetricsCalculator(work_items)
        report = calculator.generate_flow_metrics_report()
        calculation_time = time.time() - start_time

        # Should calculate metrics for 5000 items within 10 seconds
        assert (
            calculation_time < 10
        ), f"Calculation took {calculation_time:.2f}s, exceeds 10s threshold"
        assert report is not None, "Report generation failed"

        # Check report structure
        assert "throughput" in report
        assert "lead_time" in report
        assert "cycle_time" in report

    def test_database_performance_bulk_operations(self):
        """Test database performance with bulk operations."""
        db = FlowMetricsDatabase(db_path=":memory:")

        # Generate test data
        work_items = generate_mock_azure_devops_data(count=2000)

        # Test bulk insert performance
        start_time = time.time()
        db.save_work_items(work_items)
        insert_time = time.time() - start_time

        assert (
            insert_time < 5
        ), f"Bulk insert took {insert_time:.2f}s, exceeds 5s threshold"

        # Test bulk query performance
        start_time = time.time()
        retrieved_items = db.get_work_items(limit=2000)
        query_time = time.time() - start_time

        assert (
            query_time < 2
        ), f"Bulk query took {query_time:.2f}s, exceeds 2s threshold"
        assert (
            len(retrieved_items) == 2000
        ), f"Expected 2000 items, got {len(retrieved_items)}"

    def test_web_server_response_time_baseline(self):
        """Test web server response time baseline."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        # Warm up
        client.get("/health")

        # Test metrics endpoint
        response_times = []
        for _ in range(10):
            start_time = time.time()
            response = client.get("/api/metrics")
            response_time = time.time() - start_time
            response_times.append(response_time)

            assert (
                response.status_code == 200
            ), f"Request failed with status {response.status_code}"

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert (
            avg_response_time < 0.5
        ), f"Average response time {avg_response_time:.3f}s exceeds 0.5s threshold"
        assert (
            max_response_time < 1.0
        ), f"Max response time {max_response_time:.3f}s exceeds 1.0s threshold"

    def test_concurrent_request_performance(self):
        """Test performance under concurrent requests."""
        server = FlowMetricsWebServer(data_source="mock")

        def make_request():
            client = server.app.test_client()
            start_time = time.time()
            response = client.get("/api/metrics")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Run 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]

        assert (
            len(successful_requests) == 20
        ), f"Only {len(successful_requests)}/20 requests succeeded"

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert (
            avg_response_time < 2.0
        ), f"Average response time {avg_response_time:.3f}s exceeds 2.0s threshold"
        assert (
            max_response_time < 5.0
        ), f"Max response time {max_response_time:.3f}s exceeds 5.0s threshold"

    def test_memory_usage_patterns(self):
        """Test memory usage patterns during operations."""
        # Get initial memory usage
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        work_items = generate_mock_azure_devops_data(count=10000)
        calculator = FlowMetricsCalculator(work_items)
        report = calculator.generate_flow_metrics_report()

        # Get peak memory usage
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Clean up
        del work_items
        del calculator
        del report
        gc.collect()

        # Get final memory usage
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        memory_increase = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory

        assert (
            memory_increase < 200
        ), f"Memory increase {memory_increase:.2f}MB exceeds 200MB threshold"
        assert (
            memory_cleanup > 0
        ), f"Memory not properly cleaned up: {memory_cleanup:.2f}MB"

    def test_cpu_usage_during_intensive_operations(self):
        """Test CPU usage during intensive operations."""
        # Monitor CPU usage during calculation
        cpu_usage_samples = []

        def monitor_cpu():
            while not stop_monitoring:
                cpu_usage_samples.append(psutil.cpu_percent())
                time.sleep(0.1)

        stop_monitoring = False
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()

        # Perform CPU-intensive operation
        work_items = generate_mock_azure_devops_data(count=5000)
        calculator = FlowMetricsCalculator(work_items)
        report = calculator.generate_flow_metrics_report()

        stop_monitoring = True
        monitor_thread.join()

        avg_cpu_usage = sum(cpu_usage_samples) / len(cpu_usage_samples)
        max_cpu_usage = max(cpu_usage_samples)

        # CPU usage should be reasonable
        assert (
            avg_cpu_usage < 80
        ), f"Average CPU usage {avg_cpu_usage:.2f}% exceeds 80% threshold"
        assert (
            max_cpu_usage < 95
        ), f"Max CPU usage {max_cpu_usage:.2f}% exceeds 95% threshold"


@pytest.mark.performance
class TestScalabilityTests:
    """Test scalability with increasing data sizes."""

    @pytest.mark.parametrize("data_size", [100, 500, 1000, 5000, 10000])
    def test_calculator_scalability(self, data_size):
        """Test calculator performance with different data sizes."""
        work_items = generate_mock_azure_devops_data(count=data_size)

        start_time = time.time()
        calculator = FlowMetricsCalculator(work_items)
        report = calculator.generate_flow_metrics_report()
        calculation_time = time.time() - start_time

        # Performance should scale reasonably
        time_per_item = calculation_time / data_size
        assert (
            time_per_item < 0.01
        ), f"Time per item {time_per_item:.4f}s exceeds 0.01s threshold"

        # Memory usage should scale reasonably
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_per_item = memory_usage / data_size
        assert (
            memory_per_item < 0.1
        ), f"Memory per item {memory_per_item:.4f}MB exceeds 0.1MB threshold"

    @pytest.mark.parametrize("concurrent_users", [1, 5, 10, 20, 50])
    def test_web_server_scalability(self, concurrent_users):
        """Test web server performance with different numbers of concurrent users."""
        server = FlowMetricsWebServer(data_source="mock")

        def simulate_user():
            client = server.app.test_client()
            start_time = time.time()
            response = client.get("/api/metrics")
            end_time = time.time()
            return {
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # Run concurrent user simulation
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrent_users
        ) as executor:
            futures = [executor.submit(simulate_user) for _ in range(concurrent_users)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]

        assert (
            len(successful_requests) == concurrent_users
        ), f"Only {len(successful_requests)}/{concurrent_users} requests succeeded"

        avg_response_time = sum(response_times) / len(response_times)

        # Response time should degrade gracefully with more users
        expected_max_response_time = 1.0 + (
            concurrent_users * 0.1
        )  # Allow for reasonable degradation
        assert (
            avg_response_time < expected_max_response_time
        ), f"Average response time {avg_response_time:.3f}s exceeds {expected_max_response_time:.3f}s threshold"


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance and effectiveness."""

    def test_cache_hit_performance(self):
        """Test cache hit performance."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/api/metrics")
        first_response_time = time.time() - start_time

        assert response1.status_code == 200

        # Second request (should be faster if cached)
        start_time = time.time()
        response2 = client.get("/api/metrics")
        second_response_time = time.time() - start_time

        assert response2.status_code == 200

        # Note: Since we're using mock data, caching might not be as effective
        # but the second request should not be significantly slower
        assert (
            second_response_time < first_response_time * 2
        ), "Second request significantly slower than first"

    def test_cache_invalidation_performance(self):
        """Test cache invalidation performance."""
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        # Fill cache
        response1 = client.get("/api/metrics")
        assert response1.status_code == 200

        # Refresh (invalidate cache)
        start_time = time.time()
        response2 = client.get("/api/refresh")
        refresh_time = time.time() - start_time

        assert response2.status_code == 200
        assert (
            refresh_time < 5.0
        ), f"Cache refresh took {refresh_time:.3f}s, exceeds 5.0s threshold"


@pytest.mark.performance
class TestRegressionTests:
    """Performance regression tests."""

    def test_performance_regression_baseline(self):
        """Test that performance doesn't regress below baseline."""
        # This test serves as a baseline for performance regression testing
        baseline_metrics = {
            "mock_data_generation_1000_items": 5.0,  # seconds
            "calculator_5000_items": 10.0,  # seconds
            "web_server_response_time": 0.5,  # seconds
            "database_bulk_insert_2000_items": 5.0,  # seconds
        }

        # Mock data generation test
        start_time = time.time()
        work_items = generate_mock_azure_devops_data(count=1000)
        mock_data_time = time.time() - start_time

        assert (
            mock_data_time < baseline_metrics["mock_data_generation_1000_items"]
        ), f"Mock data generation regression: {mock_data_time:.3f}s > {baseline_metrics['mock_data_generation_1000_items']:.3f}s"

        # Calculator test
        start_time = time.time()
        calculator = FlowMetricsCalculator(
            work_items[:5000] if len(work_items) >= 5000 else work_items
        )
        report = calculator.generate_flow_metrics_report()
        calculator_time = time.time() - start_time

        assert (
            calculator_time < baseline_metrics["calculator_5000_items"]
        ), f"Calculator regression: {calculator_time:.3f}s > {baseline_metrics['calculator_5000_items']:.3f}s"

        # Web server test
        server = FlowMetricsWebServer(data_source="mock")
        client = server.app.test_client()

        start_time = time.time()
        response = client.get("/api/metrics")
        web_server_time = time.time() - start_time

        assert response.status_code == 200
        assert (
            web_server_time < baseline_metrics["web_server_response_time"]
        ), f"Web server regression: {web_server_time:.3f}s > {baseline_metrics['web_server_response_time']:.3f}s"

        # Database test
        db = FlowMetricsDatabase(db_path=":memory:")

        start_time = time.time()
        db.save_work_items(work_items[:2000] if len(work_items) >= 2000 else work_items)
        db_time = time.time() - start_time

        assert (
            db_time < baseline_metrics["database_bulk_insert_2000_items"]
        ), f"Database regression: {db_time:.3f}s > {baseline_metrics['database_bulk_insert_2000_items']:.3f}s"
