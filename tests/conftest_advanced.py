"""
Advanced pytest configuration for comprehensive testing.

This module provides:
- Advanced fixtures for complex test scenarios
- Performance testing utilities
- Quality gates and thresholds
- Test data factories
- Test environment management
"""

import pytest
import tempfile
import json
import sqlite3
import time
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass

from src.models import WorkItem, StateTransition
from src.config_manager import FlowMetricsSettings
from src.data_storage import DataStorage


@dataclass
class TestMetrics:
    """Test execution metrics."""
    test_name: str
    execution_time: float
    memory_usage: float
    assertions_count: int
    passed: bool


class TestEnvironmentManager:
    """Manage test environments and cleanup."""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_temp_file(self, suffix=".tmp", content=None):
        """Create temporary file with automatic cleanup."""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        if content:
            if isinstance(content, str):
                temp_file.write(content.encode())
            else:
                temp_file.write(content)
        temp_file.close()
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_temp_dir(self):
        """Create temporary directory with automatic cleanup."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary files and directories."""
        for file_path in self.temp_files:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass
        
        for dir_path in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()


class WorkItemFactory:
    """Factory for creating test work items with various scenarios."""
    
    @staticmethod
    def create_basic_work_item(
        id: int = 1000,
        title: str = "Test Work Item",
        work_item_type: str = "Task",
        state: str = "Active",
        assigned_to: str = "Test User",
        days_old: int = 5
    ) -> WorkItem:
        """Create a basic work item for testing."""
        now = datetime.now(timezone.utc)
        return WorkItem(
            id=id,
            title=title,
            work_item_type=work_item_type,
            state=state,
            assigned_to=assigned_to,
            created_date=now - timedelta(days=days_old),
            changed_date=now - timedelta(days=days_old//2),
            state_transitions=[]
        )
    
    @staticmethod
    def create_work_item_with_transitions(
        id: int = 2000,
        num_transitions: int = 3
    ) -> WorkItem:
        """Create work item with state transitions."""
        now = datetime.now(timezone.utc)
        
        states = ["New", "Active", "In Progress", "Code Review", "Done"]
        transitions = []
        
        for i in range(num_transitions):
            from_state = states[i] if i > 0 else None
            to_state = states[min(i + 1, len(states) - 1)]
            
            transition = StateTransition(
                from_state=from_state,
                to_state=to_state,
                changed_date=now - timedelta(days=num_transitions-i),
                changed_by=f"User{i+1}"
            )
            transitions.append(transition)
        
        return WorkItem(
            id=id,
            title=f"Work Item with {num_transitions} Transitions",
            work_item_type="User Story",
            state=states[min(num_transitions, len(states) - 1)],
            assigned_to="Test User",
            created_date=now - timedelta(days=num_transitions + 1),
            changed_date=now,
            state_transitions=transitions
        )
    
    @staticmethod
    def create_bulk_work_items(
        count: int = 100,
        variety: bool = True
    ) -> List[WorkItem]:
        """Create bulk work items for performance testing."""
        work_items = []
        now = datetime.now(timezone.utc)
        
        types = ["User Story", "Bug", "Task", "Feature"] if variety else ["Task"]
        states = ["New", "Active", "In Progress", "Done", "Blocked"] if variety else ["Active"]
        users = ["Alice", "Bob", "Charlie", "Diana", "Eve"] if variety else ["TestUser"]
        
        for i in range(count):
            work_item = WorkItem(
                id=10000 + i,
                title=f"Bulk Test Item {i:04d}",
                work_item_type=types[i % len(types)],
                state=states[i % len(states)],
                assigned_to=users[i % len(users)],
                created_date=now - timedelta(days=i % 90),
                changed_date=now - timedelta(days=i % 30),
                state_transitions=[]
            )
            work_items.append(work_item)
        
        return work_items
    
    @staticmethod
    def create_edge_case_work_items() -> List[WorkItem]:
        """Create work items for edge case testing."""
        now = datetime.now(timezone.utc)
        
        return [
            # Very old work item
            WorkItem(
                id=99991,
                title="Ancient Work Item",
                work_item_type="Epic",
                state="Done",
                assigned_to="Historical User",
                created_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
                changed_date=datetime(2020, 12, 31, tzinfo=timezone.utc),
                state_transitions=[]
            ),
            
            # Future work item
            WorkItem(
                id=99992,
                title="Future Work Item",
                work_item_type="Task",
                state="New",
                assigned_to="Future User",
                created_date=now + timedelta(days=30),
                changed_date=now + timedelta(days=30),
                state_transitions=[]
            ),
            
            # Work item with extreme title length
            WorkItem(
                id=99993,
                title="X" * 1000,  # Very long title
                work_item_type="Bug",
                state="Active",
                assigned_to="Test User",
                created_date=now,
                changed_date=now,
                state_transitions=[]
            ),
            
            # Work item with None assigned_to
            WorkItem(
                id=99994,
                title="Unassigned Work Item",
                work_item_type="Task",
                state="New",
                assigned_to=None,
                created_date=now,
                changed_date=now,
                state_transitions=[]
            )
        ]


class MockAzureDevOpsAPI:
    """Mock Azure DevOps API for testing."""
    
    def __init__(self, scenario: str = "default"):
        self.scenario = scenario
        self.call_count = 0
        self.response_delay = 0.0
    
    def set_response_delay(self, delay: float):
        """Set artificial delay for responses."""
        self.response_delay = delay
    
    def get_work_items_response(self):
        """Get mock work items response based on scenario."""
        self.call_count += 1
        
        if self.response_delay:
            time.sleep(self.response_delay)
        
        if self.scenario == "empty":
            return {"workItems": []}
        elif self.scenario == "large":
            return {
                "workItems": [
                    {"id": i, "url": f"https://dev.azure.com/_apis/wit/workItems/{i}"}
                    for i in range(1000, 1500)
                ]
            }
        elif self.scenario == "error":
            raise Exception("API Error")
        elif self.scenario == "timeout":
            import requests
            raise requests.exceptions.Timeout("Request timed out")
        else:  # default
            return {
                "workItems": [
                    {"id": 1001, "url": "https://dev.azure.com/_apis/wit/workItems/1001"},
                    {"id": 1002, "url": "https://dev.azure.com/_apis/wit/workItems/1002"},
                    {"id": 1003, "url": "https://dev.azure.com/_apis/wit/workItems/1003"}
                ]
            }
    
    def get_work_item_details_response(self, work_item_id: int):
        """Get mock work item details response."""
        if self.response_delay:
            time.sleep(self.response_delay)
        
        return {
            "value": [{
                "id": work_item_id,
                "fields": {
                    "System.Title": f"Mock Work Item {work_item_id}",
                    "System.WorkItemType": "Task",
                    "System.State": "Active",
                    "System.AssignedTo": {"displayName": "Mock User"},
                    "System.CreatedDate": "2024-01-01T00:00:00Z",
                    "System.ChangedDate": "2024-01-02T00:00:00Z"
                }
            }]
        }


# Advanced fixtures
@pytest.fixture(scope="session")
def test_env_manager():
    """Session-scoped test environment manager."""
    manager = TestEnvironmentManager()
    yield manager
    manager.cleanup()


@pytest.fixture
def work_item_factory():
    """Provide WorkItemFactory for test data creation."""
    return WorkItemFactory()


@pytest.fixture
def mock_ado_api():
    """Provide MockAzureDevOpsAPI for testing."""
    return MockAzureDevOpsAPI()


@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "max_execution_time": 5.0,  # seconds
        "max_memory_increase": 100,  # MB
        "min_throughput": 10,  # operations per second
        "max_response_time": 2.0,  # seconds
        "concurrency_levels": [1, 5, 10, 20]
    }


@pytest.fixture
def large_dataset(work_item_factory):
    """Large dataset for performance testing."""
    return work_item_factory.create_bulk_work_items(count=1000, variety=True)


@pytest.fixture
def edge_case_dataset(work_item_factory):
    """Edge case dataset for boundary testing."""
    return work_item_factory.create_edge_case_work_items()


@pytest.fixture
def temp_database(test_env_manager):
    """Temporary database for testing."""
    db_file = test_env_manager.create_temp_file(suffix=".db")
    storage = DataStorage(db_file)
    yield storage
    # Cleanup handled by test_env_manager


@pytest.fixture
def temp_config_advanced(test_env_manager):
    """Advanced temporary configuration for testing."""
    config_data = {
        "azure_devops": {
            "organization": "advanced-test-org",
            "project": "advanced-test-project",
            "pat_token": "advanced-test-token-456",
            "base_url": "https://dev.azure.com",
            "api_version": "7.0",
            "timeout": 30,
            "retry_attempts": 3
        },
        "stage_definitions": {
            "active_states": ["Active", "In Progress", "Code Review", "Testing", "Ready for Deploy"],
            "completion_states": ["Done", "Closed", "Resolved", "Completed", "Deployed"],
            "waiting_states": ["New", "Blocked", "Waiting", "On Hold", "Backlog"]
        },
        "performance": {
            "batch_size": 200,
            "cache_duration_hours": 4,
            "max_concurrent_requests": 10
        },
        "quality_gates": {
            "min_test_coverage": 80.0,
            "max_response_time_ms": 2000,
            "max_memory_usage_mb": 512
        },
        "data_dir": "advanced_test_data",
        "log_dir": "advanced_test_logs",
        "backup_retention_days": 30
    }
    
    config_file = test_env_manager.create_temp_file(
        suffix=".json",
        content=json.dumps(config_data, indent=2)
    )
    
    return config_file


@pytest.fixture
def comprehensive_test_data(work_item_factory):
    """Comprehensive test data covering various scenarios."""
    data = {
        "basic_items": [
            work_item_factory.create_basic_work_item(id=i, days_old=i*2)
            for i in range(1, 11)
        ],
        "items_with_transitions": [
            work_item_factory.create_work_item_with_transitions(id=2000+i, num_transitions=i+1)
            for i in range(5)
        ],
        "edge_cases": work_item_factory.create_edge_case_work_items(),
        "bulk_data": work_item_factory.create_bulk_work_items(count=50)
    }
    
    return data


# Performance testing utilities
class PerformanceMonitor:
    """Monitor test performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = []
    
    def start_monitoring(self, test_name: str):
        """Start monitoring performance for a test."""
        self.start_time = time.time()
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            self.start_memory = 0
    
    def stop_monitoring(self, test_name: str, passed: bool = True):
        """Stop monitoring and record metrics."""
        if self.start_time is None:
            return
        
        execution_time = time.time() - self.start_time
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = end_memory - self.start_memory
        except ImportError:
            memory_usage = 0
        
        metric = TestMetrics(
            test_name=test_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            assertions_count=0,  # Could be enhanced to count assertions
            passed=passed
        )
        
        self.metrics.append(metric)
        return metric


@pytest.fixture
def performance_monitor():
    """Provide performance monitor for tests."""
    return PerformanceMonitor()


# Quality gates
class QualityGates:
    """Quality gates for test validation."""
    
    THRESHOLDS = {
        "max_test_execution_time": 10.0,  # seconds
        "max_memory_usage": 200.0,  # MB
        "min_coverage_percentage": 75.0,
        "max_database_operation_time": 5.0,  # seconds
        "max_api_response_time": 3.0,  # seconds
    }
    
    @classmethod
    def check_performance_threshold(cls, metric: TestMetrics):
        """Check if test meets performance thresholds."""
        issues = []
        
        if metric.execution_time > cls.THRESHOLDS["max_test_execution_time"]:
            issues.append(
                f"Execution time {metric.execution_time:.2f}s exceeds threshold "
                f"{cls.THRESHOLDS['max_test_execution_time']}s"
            )
        
        if metric.memory_usage > cls.THRESHOLDS["max_memory_usage"]:
            issues.append(
                f"Memory usage {metric.memory_usage:.2f}MB exceeds threshold "
                f"{cls.THRESHOLDS['max_memory_usage']}MB"
            )
        
        return issues
    
    @classmethod
    def validate_test_result(cls, metric: TestMetrics, strict: bool = False):
        """Validate test result against quality gates."""
        if not metric.passed:
            return False
        
        issues = cls.check_performance_threshold(metric)
        
        if strict and issues:
            pytest.fail(f"Quality gate violations for {metric.test_name}:\n" + 
                       "\n".join(f"- {issue}" for issue in issues))
        
        return len(issues) == 0


@pytest.fixture
def quality_gates():
    """Provide quality gates validator."""
    return QualityGates()


# Test markers configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "critical: Critical functionality tests")
    config.addinivalue_line("markers", "edge_case: Edge case and boundary tests")
    config.addinivalue_line("markers", "security: Security-related tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers."""
    for item in items:
        # Auto-mark performance tests
        if "performance" in item.name.lower() or "perf" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark integration tests
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Auto-mark e2e tests
        if "e2e" in item.nodeid or "test_e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark edge case tests
        if "edge" in item.name.lower() or "boundary" in item.name.lower():
            item.add_marker(pytest.mark.edge_case)


# Hooks for test monitoring
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Hook called before each test runs."""
    if hasattr(item, 'cls') and hasattr(item.cls, 'performance_monitor'):
        item.cls.performance_monitor.start_monitoring(item.name)


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    """Hook called after each test runs."""
    if hasattr(item, 'cls') and hasattr(item.cls, 'performance_monitor'):
        passed = item.get_closest_marker("passed") is not None
        item.cls.performance_monitor.stop_monitoring(item.name, passed)


# Custom assertion helpers
def assert_performance_within_threshold(execution_time: float, max_time: float):
    """Assert that execution time is within performance threshold."""
    assert execution_time <= max_time, (
        f"Execution time {execution_time:.3f}s exceeded threshold {max_time}s"
    )


def assert_memory_usage_reasonable(memory_increase: float, max_increase: float = 100.0):
    """Assert that memory usage increase is reasonable."""
    assert memory_increase <= max_increase, (
        f"Memory increase {memory_increase:.1f}MB exceeded threshold {max_increase}MB"
    )