"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from src.models import WorkItem, StateTransition
from src.config_manager import FlowMetricsSettings


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = {
        "azure_devops": {
            "organization": "test-org",
            "project": "test-project",
            "pat_token": "test-token",
            "base_url": "https://dev.azure.com",
        },
        "stage_definitions": {
            "active_states": ["Active", "In Progress", "Code Review"],
            "completion_states": ["Done", "Closed", "Resolved"],
            "waiting_states": ["New", "Blocked", "Waiting"],
        },
        "data_dir": "test_data",
        "log_dir": "test_logs",
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name

    yield config_file

    # Cleanup
    Path(config_file).unlink(missing_ok=True)


@pytest.fixture
def sample_settings(temp_config_file):
    """Provide sample settings for testing."""
    return FlowMetricsSettings(_config_file=temp_config_file)


@pytest.fixture
def sample_work_items():
    """Provide comprehensive sample work items for testing."""
    now = datetime.now(timezone.utc)

    work_items = []

    # Work item 1: Complete User Story
    work_items.append(
        WorkItem(
            id=1001,
            title="User Login Feature",
            work_item_type="User Story",
            state="Done",
            assigned_to="Alice Johnson",
            created_date=now - timedelta(days=15),
            changed_date=now - timedelta(days=2),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=15),
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=12),
                    changed_by="Alice Johnson",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Code Review",
                    changed_date=now - timedelta(days=5),
                    changed_by="Alice Johnson",
                ),
                StateTransition(
                    from_state="Code Review",
                    to_state="Done",
                    changed_date=now - timedelta(days=2),
                    changed_by="Bob Smith",
                ),
            ],
        )
    )

    # Work item 2: Bug in progress
    work_items.append(
        WorkItem(
            id=1002,
            title="Fix login validation",
            work_item_type="Bug",
            state="In Progress",
            assigned_to="Bob Smith",
            created_date=now - timedelta(days=7),
            changed_date=now - timedelta(days=1),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=7),
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="In Progress",
                    changed_date=now - timedelta(days=1),
                    changed_by="Bob Smith",
                ),
            ],
        )
    )

    # Work item 3: Blocked task
    work_items.append(
        WorkItem(
            id=1003,
            title="Database migration",
            work_item_type="Task",
            state="Blocked",
            assigned_to="Charlie Brown",
            created_date=now - timedelta(days=10),
            changed_date=now - timedelta(days=3),
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
                    changed_by="Charlie Brown",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Blocked",
                    changed_date=now - timedelta(days=3),
                    changed_by="Charlie Brown",
                ),
            ],
        )
    )

    # Work item 4: Recently completed
    work_items.append(
        WorkItem(
            id=1004,
            title="API documentation",
            work_item_type="Task",
            state="Closed",
            assigned_to="Diana Prince",
            created_date=now - timedelta(days=5),
            changed_date=now - timedelta(hours=6),
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
                    changed_date=now - timedelta(days=3),
                    changed_by="Diana Prince",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Closed",
                    changed_date=now - timedelta(hours=6),
                    changed_by="Diana Prince",
                ),
            ],
        )
    )

    # Work item 5: Old completed item
    work_items.append(
        WorkItem(
            id=1005,
            title="Legacy feature removal",
            work_item_type="User Story",
            state="Resolved",
            assigned_to="Eve Adams",
            created_date=now - timedelta(days=45),
            changed_date=now - timedelta(days=35),
            state_transitions=[
                StateTransition(
                    from_state=None,
                    to_state="New",
                    changed_date=now - timedelta(days=45),
                    changed_by="System",
                ),
                StateTransition(
                    from_state="New",
                    to_state="Active",
                    changed_date=now - timedelta(days=40),
                    changed_by="Eve Adams",
                ),
                StateTransition(
                    from_state="Active",
                    to_state="Resolved",
                    changed_date=now - timedelta(days=35),
                    changed_by="Eve Adams",
                ),
            ],
        )
    )

    return work_items


@pytest.fixture
def empty_work_items():
    """Provide empty work items list for testing edge cases."""
    return []


@pytest.fixture
def mock_azure_devops_response():
    """Provide mock Azure DevOps API response data."""
    return {
        "workItems": [
            {"id": 1001, "url": "https://dev.azure.com/_apis/wit/workItems/1001"},
            {"id": 1002, "url": "https://dev.azure.com/_apis/wit/workItems/1002"},
        ]
    }


@pytest.fixture
def mock_work_item_details():
    """Provide mock work item details response."""
    return {
        "id": 1001,
        "fields": {
            "System.Title": "Test Work Item",
            "System.WorkItemType": "User Story",
            "System.State": "Active",
            "System.AssignedTo": {"displayName": "Test User"},
            "System.CreatedDate": "2024-01-01T00:00:00Z",
            "System.ChangedDate": "2024-01-02T00:00:00Z",
        },
    }


@pytest.fixture
def mock_state_transitions():
    """Provide mock state transitions response."""
    return {
        "value": [
            {
                "fields": {"System.State": {"oldValue": "New", "newValue": "Active"}},
                "changedDate": "2024-01-02T10:00:00Z",
                "changedBy": {"displayName": "Test User"},
            }
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Mark all tests in test_azure_devops_client as integration tests
        if "test_azure_devops_client" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark tests that use network calls as slow
        if any(keyword in item.name for keyword in ["fetch", "network", "api"]):
            item.add_marker(pytest.mark.slow)
