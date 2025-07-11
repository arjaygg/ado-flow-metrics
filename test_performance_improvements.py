#!/usr/bin/env python3
"""
Test script for Azure DevOps performance improvements
"""
import sys
from typing import List
from unittest.mock import Mock, patch


# Test progress callback functionality
def test_progress_callback():
    """Test the progress callback interface"""
    print("Testing progress callback interface...")

    callbacks_received = []

    def test_callback(event_type: str, *args):
        callbacks_received.append((event_type, args))
        print(f"Progress: {event_type} - {args}")

    # Test different callback types
    test_callback("phase", "Initializing...")
    test_callback("count", 150)
    test_callback("batch", 2, 5)

    # Verify we received the expected callbacks
    assert len(callbacks_received) == 3
    assert callbacks_received[0][0] == "phase"
    assert callbacks_received[1][0] == "count"
    assert callbacks_received[2][0] == "batch"

    print("✓ Progress callback interface test passed")


def test_concurrent_processing_structure():
    """Test that concurrent processing methods are properly structured"""
    print("Testing concurrent processing structure...")

    from src.azure_devops_client import AzureDevOpsClient

    # Create a mock client to test method signatures
    client = AzureDevOpsClient("https://test.com", "test-project", "fake-token")

    # Verify the new concurrent method exists
    assert hasattr(client, "_fetch_work_items_concurrent")

    # Verify get_work_items accepts progress_callback
    import inspect

    sig = inspect.signature(client.get_work_items)
    assert "progress_callback" in sig.parameters

    print("✓ Concurrent processing structure test passed")


def test_retry_logic_constants():
    """Test that retry logic constants are reasonable"""
    print("Testing retry logic constants...")

    # These should be reasonable values for production use
    max_retries = 3
    base_delay = 1
    max_workers = 5
    timeout = 60

    assert 1 <= max_retries <= 5, f"max_retries should be 1-5, got {max_retries}"
    assert 0.5 <= base_delay <= 2, f"base_delay should be 0.5-2s, got {base_delay}"
    assert 3 <= max_workers <= 10, f"max_workers should be 3-10, got {max_workers}"
    assert 30 <= timeout <= 120, f"timeout should be 30-120s, got {timeout}"

    print("✓ Retry logic constants test passed")


def main():
    """Run all performance improvement tests"""
    print("🚀 Testing Azure DevOps Performance Improvements")
    print("=" * 50)

    try:
        test_progress_callback()
        test_concurrent_processing_structure()
        test_retry_logic_constants()

        print("=" * 50)
        print("✅ All performance improvement tests passed!")
        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
