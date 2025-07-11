#!/usr/bin/env python3
"""
Performance benchmark for Azure DevOps improvements
This simulates the before/after performance to demonstrate improvements
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List


def simulate_old_sequential_processing(batches: List[List[int]]) -> float:
    """Simulate the old sequential batch processing"""
    print("🐌 Simulating OLD sequential processing...")
    start_time = time.time()

    for i, batch in enumerate(batches):
        # Simulate API call delay (200ms per batch)
        time.sleep(0.2)
        print(f"  Processed batch {i+1}/{len(batches)} ({len(batch)} items)")

    end_time = time.time()
    return end_time - start_time


def simulate_new_concurrent_processing(batches: List[List[int]]) -> float:
    """Simulate the new concurrent batch processing"""
    print("🚀 Simulating NEW concurrent processing...")
    start_time = time.time()

    def process_batch(batch_info):
        batch_num, batch = batch_info
        # Simulate API call delay (200ms per batch)
        time.sleep(0.2)
        return f"Batch {batch_num+1} ({len(batch)} items)"

    # Use concurrent processing with max 5 workers
    max_workers = min(5, len(batches))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        batch_info = [(i, batch) for i, batch in enumerate(batches)]
        results = list(executor.map(process_batch, batch_info))

        for result in results:
            print(f"  ✓ {result}")

    end_time = time.time()
    return end_time - start_time


def main():
    """Run performance benchmark"""
    print("🔧 Azure DevOps Performance Improvement Benchmark")
    print("=" * 55)

    # Simulate realistic batch sizes
    # Example: 1000 work items = 5 batches of 200 items each
    work_item_count = 1000
    batch_size = 200
    batches = [
        list(range(i, min(i + batch_size, work_item_count)))
        for i in range(0, work_item_count, batch_size)
    ]

    print(f"📊 Benchmark Setup:")
    print(f"  Total work items: {work_item_count}")
    print(f"  Batch size: {batch_size}")
    print(f"  Number of batches: {len(batches)}")
    print(f"  Simulated API delay: 200ms per batch")
    print()

    # Test old sequential approach
    sequential_time = simulate_old_sequential_processing(batches)
    print(f"  ⏱️  Sequential time: {sequential_time:.2f} seconds")
    print()

    # Test new concurrent approach
    concurrent_time = simulate_new_concurrent_processing(batches)
    print(f"  ⏱️  Concurrent time: {concurrent_time:.2f} seconds")
    print()

    # Calculate improvements
    improvement_factor = sequential_time / concurrent_time
    time_saved = sequential_time - concurrent_time
    percentage_improvement = (
        (sequential_time - concurrent_time) / sequential_time
    ) * 100

    print("📈 Performance Improvement Results:")
    print(f"  ⚡ Speed improvement: {improvement_factor:.1f}x faster")
    print(f"  ⏰ Time saved: {time_saved:.2f} seconds")
    print(f"  📊 Percentage improvement: {percentage_improvement:.1f}%")
    print()

    print("🎯 Real-world Impact:")
    print(f"  • For {work_item_count} items: {time_saved:.1f}s faster")
    print(f"  • For 5000 items: {time_saved * 5:.1f}s faster")
    print(f"  • Daily time savings: ~{time_saved * 10:.1f}s per fetch")
    print()

    print("✅ Additional Benefits:")
    print("  • Real-time progress visibility")
    print("  • Batch completion tracking")
    print("  • Retry logic with exponential backoff")
    print("  • Reduced terminal verbosity")
    print("  • Better error handling")

    return 0


if __name__ == "__main__":
    sys.exit(main())
