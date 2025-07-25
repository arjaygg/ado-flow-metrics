"""State history service for Azure DevOps work items."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StateHistoryService:
    """Handles state history enrichment for work items."""

    def __init__(self, api_client):
        self.api_client = api_client
        self.max_concurrent_requests = 5

    def enrich_with_state_history(
        self,
        work_items_to_process: List[Dict],
        progress_callback: Optional[Callable] = None,
        history_limit: Optional[int] = None,
    ) -> List[Dict]:
        """Enrich work items with state history using concurrent processing."""
        if not work_items_to_process:
            return work_items_to_process

        self._report_progress_start(progress_callback, len(work_items_to_process))

        # Use ThreadPoolExecutor for concurrent state history fetching
        max_workers = min(self.max_concurrent_requests, len(work_items_to_process))

        if max_workers <= 0:
            return work_items_to_process

        return self._process_items_concurrently(
            work_items_to_process, max_workers, history_limit, progress_callback
        )

    def _report_progress_start(
        self, progress_callback: Optional[Callable], total_items: int
    ) -> None:
        """Report the start of state history processing."""
        if progress_callback:
            progress_callback(
                "items",
                f"Fetching state history for {total_items} items...",
            )

    def _process_items_concurrently(
        self,
        work_items_to_process: List[Dict],
        max_workers: int,
        history_limit: Optional[int],
        progress_callback: Optional[Callable],
    ) -> List[Dict]:
        """Process items concurrently with thread pool."""
        transformed_items = []
        progress_tracker = ProgressTracker(len(work_items_to_process))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all state history requests
            future_to_item = self._submit_history_requests(
                executor, work_items_to_process, history_limit
            )

            # Collect results as they complete
            self._collect_results(
                future_to_item, progress_tracker, progress_callback, transformed_items
            )

        # Clean up temporary fields
        self._cleanup_temporary_fields(transformed_items)

        return transformed_items

    def _submit_history_requests(
        self,
        executor: ThreadPoolExecutor,
        work_items_to_process: List[Dict],
        history_limit: Optional[int],
    ) -> Dict:
        """Submit all state history requests to the thread pool."""
        return {
            executor.submit(
                self.api_client._get_state_history, item["raw_id"], history_limit
            ): item
            for item in work_items_to_process
        }

    def _collect_results(
        self,
        future_to_item: Dict,
        progress_tracker: "ProgressTracker",
        progress_callback: Optional[Callable],
        transformed_items: List[Dict],
    ) -> None:
        """Collect results from completed futures."""
        for future in as_completed(future_to_item):
            item = future_to_item[future]

            try:
                state_transitions = future.result(timeout=30)  # Add timeout
                item["state_transitions"] = state_transitions
            except KeyboardInterrupt:
                logger.info("Cancelling remaining state history requests...")
                self._cancel_remaining_futures(future_to_item)
                raise
            except Exception as e:
                logger.warning(f"Failed to get state history for {item['id']}: {e}")
                item["state_transitions"] = []

            # Update progress
            progress_tracker.increment()
            if progress_callback and progress_tracker.should_report_progress():
                progress_callback(
                    "items",
                    f"Processed state history: {progress_tracker.completed}/{progress_tracker.total}",
                )

            transformed_items.append(item)

    def _cancel_remaining_futures(self, future_to_item: Dict) -> None:
        """Cancel remaining futures in case of interruption."""
        remaining_futures = list(future_to_item.keys())
        for f in remaining_futures:
            f.cancel()

    def _cleanup_temporary_fields(self, transformed_items: List[Dict]) -> None:
        """Remove temporary fields that are no longer needed."""
        for item in transformed_items:
            item.pop("raw_id", None)


class ProgressTracker:
    """Thread-safe progress tracker for concurrent operations."""

    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.lock = threading.Lock()
        self.report_interval = 10  # Report every 10 items

    def increment(self) -> None:
        """Increment the completed counter in a thread-safe manner."""
        with self.lock:
            self.completed += 1

    def should_report_progress(self) -> bool:
        """Check if progress should be reported."""
        with self.lock:
            return self.completed % self.report_interval == 0
