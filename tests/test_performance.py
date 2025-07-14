"""
Performance and load testing suite for ADO Flow Hive.

These tests verify:
- Response times under various loads
- Memory usage patterns
- Database performance with large datasets
- Web server throughput and latency
- Concurrent operation handling
- System resource utilization
"""

import pytest
import time
import threading
import concurrent.futures
import statistics
import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
import psutil
import os

from src.azure_devops_client import AzureDevOpsClient
from src.data_storage import FlowMetricsDatabase
from src.calculator import FlowMetricsCalculator
from src.web_server import FlowMetricsWebServer
from src.config_manager import FlowMetricsSettings
from src.models import WorkItem, StateTransition


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.fixture
    def perf_db(self):
        """Create temporary database for performance testing."""
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        yield db_file.name
        Path(db_file.name).unlink(missing_ok=True)

    @pytest.fixture
    def large_dataset(self):
        """Generate large dataset for performance testing."""
        now = datetime.now(timezone.utc)
        work_items = []
        
        for i in range(1000):  # 1000 work items
            # Create realistic state transitions
            transitions = []
            for j in range(3):  # 3 transitions per item
                transition = StateTransition(
                    from_state="New" if j == 0 else f"State{j}",
                    to_state=f"State{j+1}",
                    changed_date=now - timedelta(days=30-j*5),
                    changed_by=f"User{i % 10}"
                )
                transitions.append(transition)
            
            work_item = WorkItem(
                id=i + 100000,
                title=f"Performance Test Item {i:04d}",
                work_item_type="User Story" if i % 3 == 0 else "Task",
                state="Done" if i % 5 == 0 else "Active",
                assigned_to=f"User{i % 20}",
                created_date=now - timedelta(days=i % 90),
                changed_date=now - timedelta(days=i % 30),
                state_transitions=transitions
            )
            work_items.append(work_item)
        
        return work_items

    def test_bulk_insert_performance(self, perf_db, large_dataset):
        """Test bulk insert performance with large dataset."""
        storage = DataStorage(perf_db)
        
        # Measure insertion time
        start_time = time.time()
        storage.store_work_items(large_dataset)
        insert_time = time.time() - start_time
        
        # Performance assertions
        assert insert_time < 30.0  # Should complete within 30 seconds
        
        # Verify data was inserted
        count = storage._get_work_item_count()
        assert count == len(large_dataset)
        
        print(f"Bulk insert performance: {len(large_dataset)} items in {insert_time:.2f}s")
        print(f"Rate: {len(large_dataset)/insert_time:.0f} items/second")

    def test_query_performance_with_large_dataset(self, perf_db, large_dataset):
        """Test query performance with large dataset."""
        storage = DataStorage(perf_db)
        storage.store_work_items(large_dataset)
        
        # Test various query operations
        query_times = {}
        
        # 1. Get all work items
        start_time = time.time()
        all_items = storage.get_work_items()
        query_times['get_all'] = time.time() - start_time
        
        # 2. Get work items by date range
        start_time = time.time()
        recent_items = storage.get_work_items_by_date_range(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )
        query_times['date_range'] = time.time() - start_time
        
        # 3. Get specific work item
        start_time = time.time()
        specific_item = storage.get_work_item(100001)
        query_times['specific'] = time.time() - start_time
        
        # Performance assertions
        assert query_times['get_all'] < 5.0      # All items within 5 seconds
        assert query_times['date_range'] < 2.0   # Date range within 2 seconds
        assert query_times['specific'] < 0.1     # Specific item within 100ms
        
        # Verify results
        assert len(all_items) == len(large_dataset)
        assert len(recent_items) > 0
        assert specific_item is not None
        
        for operation, time_taken in query_times.items():
            print(f"Query performance - {operation}: {time_taken:.3f}s")

    def test_concurrent_database_operations(self, perf_db):
        """Test database performance under concurrent operations."""
        def concurrent_operation(thread_id, num_items=100):
            """Simulate concurrent database operation."""
            storage = DataStorage(perf_db)
            now = datetime.now(timezone.utc)
            
            # Create thread-specific work items
            work_items = []
            for i in range(num_items):
                work_item = WorkItem(
                    id=thread_id * 10000 + i,
                    title=f"Concurrent Item T{thread_id}-{i}",
                    work_item_type="Task",
                    state="Active",
                    assigned_to=f"User{thread_id}",
                    created_date=now,
                    changed_date=now,
                    state_transitions=[]
                )
                work_items.append(work_item)
            
            start_time = time.time()
            storage.store_work_items(work_items)
            operation_time = time.time() - start_time
            
            return {
                'thread_id': thread_id,
                'items_count': len(work_items),
                'time_taken': operation_time
            }
        
        # Run concurrent operations
        num_threads = 5
        items_per_thread = 200
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(concurrent_operation, i, items_per_thread) 
                for i in range(num_threads)
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all operations completed successfully
        assert len(results) == num_threads
        total_items = sum(result['items_count'] for result in results)
        
        # Verify data consistency
        storage = DataStorage(perf_db)
        stored_items = storage.get_work_items()
        assert len(stored_items) >= total_items
        
        print(f"Concurrent operations: {num_threads} threads, {total_items} items in {total_time:.2f}s")
        for result in results:
            print(f"Thread {result['thread_id']}: {result['items_count']} items in {result['time_taken']:.2f}s")

    def test_database_memory_usage(self, perf_db, large_dataset):
        """Test database memory usage patterns."""
        storage = DataStorage(perf_db)
        
        # Measure memory before operation
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operation
        storage.store_work_items(large_dataset)
        all_items = storage.get_work_items()
        
        # Measure memory after operation
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Memory usage assertions (adjust thresholds based on system)
        assert memory_increase < 500  # Memory increase should be reasonable (< 500MB)
        assert len(all_items) == len(large_dataset)
        
        print(f"Memory usage: {memory_before:.1f}MB → {memory_after:.1f}MB (+{memory_increase:.1f}MB)")


@pytest.mark.performance
class TestWebServerPerformance:
    """Performance tests for web server operations."""

    @pytest.fixture
    def perf_app_setup(self, large_dataset):
        """Setup app with performance test data."""
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        storage = DataStorage(db_file.name)
        storage.store_work_items(large_dataset)
        
        app.config['TESTING'] = True
        
        yield storage, app.test_client()
        
        Path(db_file.name).unlink(missing_ok=True)

    def test_api_endpoint_response_times(self, perf_app_setup):
        """Test API endpoint response times under load."""
        storage, client = perf_app_setup
        
        with patch('src.web_server.storage', storage):
            endpoints = [
                '/api/flow-data',
                '/api/work-items',
                '/api/metrics'
            ]
            
            response_times = {}
            
            for endpoint in endpoints:
                # Measure multiple requests for average
                times = []
                for _ in range(10):
                    start_time = time.time()
                    response = client.get(endpoint)
                    response_time = time.time() - start_time
                    times.append(response_time)
                    
                    assert response.status_code == 200
                
                response_times[endpoint] = {
                    'avg': statistics.mean(times),
                    'min': min(times),
                    'max': max(times),
                    'p95': statistics.quantiles(times, n=20)[18]  # 95th percentile
                }
            
            # Performance assertions
            for endpoint, times in response_times.items():
                assert times['avg'] < 2.0    # Average response < 2 seconds
                assert times['p95'] < 5.0    # 95th percentile < 5 seconds
                
                print(f"Endpoint {endpoint}:")
                print(f"  Avg: {times['avg']:.3f}s, Min: {times['min']:.3f}s, Max: {times['max']:.3f}s, P95: {times['p95']:.3f}s")

    def test_concurrent_web_requests(self, perf_app_setup):
        """Test web server performance under concurrent requests."""
        storage, client = perf_app_setup
        
        def make_request(request_id):
            """Make concurrent web request."""
            with patch('src.web_server.storage', storage):
                start_time = time.time()
                response = client.get('/api/flow-data')
                response_time = time.time() - start_time
                
                return {
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'data_size': len(response.data)
                }
        
        # Run concurrent requests
        num_requests = 20
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        assert len(results) == num_requests
        assert all(result['status_code'] == 200 for result in results)
        
        # Calculate performance metrics
        response_times = [result['response_time'] for result in results]
        avg_response_time = statistics.mean(response_times)
        requests_per_second = num_requests / total_time
        
        # Performance assertions
        assert avg_response_time < 3.0        # Average response time < 3 seconds
        assert requests_per_second > 2.0      # At least 2 requests per second
        
        print(f"Concurrent requests: {num_requests} requests in {total_time:.2f}s")
        print(f"Requests per second: {requests_per_second:.2f}")
        print(f"Average response time: {avg_response_time:.3f}s")

    def test_memory_usage_under_load(self, perf_app_setup):
        """Test web server memory usage under load."""
        storage, client = perf_app_setup
        
        process = psutil.Process(os.getpid())
        
        with patch('src.web_server.storage', storage):
            # Measure initial memory
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Make many requests to stress test memory
            for i in range(50):
                response = client.get('/api/flow-data')
                assert response.status_code == 200
            
            # Measure memory after load
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_increase = memory_after - memory_before
        
        # Memory should not increase excessively
        assert memory_increase < 100  # Less than 100MB increase
        
        print(f"Memory under load: {memory_before:.1f}MB → {memory_after:.1f}MB (+{memory_increase:.1f}MB)")


@pytest.mark.performance
@pytest.mark.slow
class TestCalculationPerformance:
    """Performance tests for flow metrics calculations."""

    @pytest.fixture
    def calc_perf_setup(self, large_dataset):
        """Setup calculator with large dataset for performance testing."""
        # Create temporary config
        config_data = {
            "azure_devops": {
                "organization": "perf-test-org",
                "project": "perf-test-project",
                "pat_token": "perf-test-token",
                "base_url": "https://dev.azure.com"
            },
            "stage_definitions": {
                "active_states": ["Active", "In Progress", "Code Review"],
                "completion_states": ["Done", "Closed", "Resolved"],
                "waiting_states": ["New", "Blocked", "Waiting"]
            },
            "data_dir": "perf_test_data",
            "log_dir": "perf_test_logs"
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        # Create database and storage
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        settings = FlowMetricsSettings(_config_file=config_file)
        storage = DataStorage(db_file.name)
        storage.store_work_items(large_dataset)
        
        calculator = FlowMetricsCalculator(settings, storage)
        
        yield calculator, len(large_dataset)
        
        # Cleanup
        Path(config_file).unlink(missing_ok=True)
        Path(db_file.name).unlink(missing_ok=True)

    def test_metrics_calculation_performance(self, calc_perf_setup):
        """Test flow metrics calculation performance with large dataset."""
        calculator, dataset_size = calc_perf_setup
        
        # Test different date ranges
        end_date = datetime.now(timezone.utc)
        date_ranges = [
            (end_date - timedelta(days=7), end_date),    # 1 week
            (end_date - timedelta(days=30), end_date),   # 1 month
            (end_date - timedelta(days=90), end_date),   # 3 months
        ]
        
        calculation_times = {}
        
        for start_date, end_date in date_ranges:
            range_name = f"{(end_date - start_date).days}d"
            
            start_time = time.time()
            metrics = calculator.calculate_flow_metrics(start_date, end_date)
            calculation_time = time.time() - start_time
            
            calculation_times[range_name] = calculation_time
            
            # Verify metrics were calculated
            assert "throughput" in metrics
            assert "cycle_time" in metrics
            assert "work_in_progress" in metrics
            
            # Performance assertion
            assert calculation_time < 10.0  # Should complete within 10 seconds
        
        for range_name, time_taken in calculation_times.items():
            print(f"Metrics calculation ({range_name}): {time_taken:.3f}s for {dataset_size} items")

    def test_calculation_memory_efficiency(self, calc_perf_setup):
        """Test memory efficiency of metrics calculations."""
        calculator, dataset_size = calc_perf_setup
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # Perform calculation
        start_date = datetime.now(timezone.utc) - timedelta(days=90)
        end_date = datetime.now(timezone.utc)
        
        metrics = calculator.calculate_flow_metrics(start_date, end_date)
        
        memory_after = process.memory_info().rss / 1024 / 1024
        memory_increase = memory_after - memory_before
        
        # Memory efficiency assertions
        assert memory_increase < 200  # Less than 200MB increase
        assert "throughput" in metrics
        
        print(f"Calculation memory usage: +{memory_increase:.1f}MB for {dataset_size} items")


@pytest.mark.performance
class TestSystemResourceUsage:
    """Tests for overall system resource usage."""

    def test_cpu_usage_under_load(self, large_dataset):
        """Test CPU usage patterns under load."""
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        storage = DataStorage(db_file.name)
        
        # Monitor CPU during intensive operation
        cpu_percentages = []
        
        def monitor_cpu():
            """Monitor CPU usage."""
            for _ in range(10):  # Monitor for 10 seconds
                cpu_percentages.append(psutil.cpu_percent(interval=1))
        
        # Start CPU monitoring in background
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Perform intensive operations
        storage.store_work_items(large_dataset)
        retrieved_items = storage.get_work_items()
        
        monitor_thread.join()
        
        # Analyze CPU usage
        avg_cpu = statistics.mean(cpu_percentages)
        max_cpu = max(cpu_percentages)
        
        # CPU usage should be reasonable
        assert avg_cpu < 80.0  # Average CPU < 80%
        assert max_cpu < 95.0  # Peak CPU < 95%
        assert len(retrieved_items) == len(large_dataset)
        
        print(f"CPU usage - Average: {avg_cpu:.1f}%, Peak: {max_cpu:.1f}%")
        
        Path(db_file.name).unlink(missing_ok=True)

    def test_disk_io_performance(self, large_dataset):
        """Test disk I/O performance patterns."""
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_file.close()
        
        storage = DataStorage(db_file.name)
        
        # Measure disk I/O during operations
        process = psutil.Process(os.getpid())
        io_before = process.io_counters()
        
        # Perform I/O intensive operations
        storage.store_work_items(large_dataset)
        retrieved_items = storage.get_work_items()
        
        io_after = process.io_counters()
        
        # Calculate I/O metrics
        bytes_read = io_after.read_bytes - io_before.read_bytes
        bytes_written = io_after.write_bytes - io_before.write_bytes
        
        # Verify operations completed successfully
        assert len(retrieved_items) == len(large_dataset)
        
        print(f"Disk I/O - Read: {bytes_read/1024/1024:.1f}MB, Write: {bytes_written/1024/1024:.1f}MB")
        
        Path(db_file.name).unlink(missing_ok=True)