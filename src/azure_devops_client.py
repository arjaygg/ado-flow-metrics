import base64
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    def __init__(self, org_url: str, project: str, pat_token: str):
        self.org_url = org_url.rstrip("/")
        self.project = project
        self.pat_token = pat_token
        self.headers = {
            "Authorization": f'Basic {base64.b64encode(f":{pat_token}".encode()).decode()}',
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def verify_connection(self) -> bool:
        """Verify connection to Azure DevOps and permissions"""
        try:
            # Test basic project access
            project_url = (
                f"{self.org_url}/_apis/projects/{self.project}?api-version=7.0"
            )
            logger.info(f"Testing connection to: {project_url}")
            response = requests.get(project_url, headers=self.headers, timeout=30)

            if response.status_code == 401:
                logger.error("Authentication failed - check your PAT token")
                return False
            elif response.status_code == 403:
                logger.error("Access forbidden - check project permissions")
                return False
            elif response.status_code == 404:
                logger.error(f"Project '{self.project}' not found")
                return False
            elif response.status_code == 405:
                logger.error("Method not allowed - possible API endpoint issue")
                return False

            response.raise_for_status()
            logger.info("Connection to Azure DevOps verified successfully")
            return True

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    def get_work_items(
        self, days_back: int = 90, progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Fetch work items from Azure DevOps with enhanced progress tracking"""
        if progress_callback:
            progress_callback("phase", "Initializing Azure DevOps connection...")

        logger.debug(
            f"Fetching work items from the last {days_back} days for project '{self.project}'."
        )

        # Verify connection first to provide better error diagnostics
        if not self.verify_connection():
            logger.error(
                "Connection verification failed. Cannot proceed with work item fetch."
            )
            return []

        try:
            # Validate project name to prevent injection (basic sanitization)
            if not self.project.replace("-", "").replace("_", "").isalnum():
                logger.error(f"Invalid project name: {self.project}")
                return []

            if progress_callback:
                progress_callback("phase", "Querying work item IDs...")

            # First, get work item IDs using WIQL
            # Note: Azure DevOps WIQL doesn't support full parameterization,
            # but we validate inputs above
            wiql_query = {
                "query": f"""
                SELECT [System.Id]
                FROM WorkItems
                WHERE [System.ChangedDate] >= '{(datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")}'
                ORDER BY [System.ChangedDate] DESC
                """
            }

            wiql_url = f"{self.org_url}/{self.project}/_apis/wit/wiql?api-version=7.0"
            logger.debug(f"Making WIQL request to: {wiql_url}")
            response = requests.post(
                wiql_url, json=wiql_query, headers=self.headers, timeout=30
            )

            if response.status_code == 405:
                logger.error(f"HTTP 405 Method Not Allowed. URL: {wiql_url}")
                logger.error(f"Request headers: {self.headers}")
                logger.error(f"Request body: {wiql_query}")
                raise requests.exceptions.HTTPError(
                    f"Azure DevOps API returned 405 Method Not Allowed. This usually indicates an incorrect API endpoint or authentication issue."
                )

            response.raise_for_status()  # Raise an exception for bad status codes

            work_item_refs = response.json().get("workItems", [])
            logger.debug(f"Found {len(work_item_refs)} work item references.")

            if progress_callback:
                progress_callback("count", len(work_item_refs))

            if not work_item_refs:
                logger.warning("No work items found in the specified period.")
                return []

            work_item_ids = [item["id"] for item in work_item_refs]

            # Get detailed work item information in batches using concurrent processing
            work_items = []
            batch_size = 200  # Azure DevOps API limit
            batches = [
                work_item_ids[i : i + batch_size]
                for i in range(0, len(work_item_ids), batch_size)
            ]

            if progress_callback:
                progress_callback(
                    "phase", f"Fetching {len(batches)} batches concurrently..."
                )

            # Use concurrent processing for better performance
            work_items = self._fetch_work_items_concurrent(batches, progress_callback)

            logger.debug(
                f"Successfully fetched details for {len(work_items)} work items in total."
            )

            if progress_callback:
                progress_callback("phase", "Processing work items and state history...")

            # Transform to our format with concurrent state history fetching
            transformed_items = []

            # First, prepare all work items without state history
            work_items_to_process = []
            for item in work_items:
                fields = item.get("fields", {})

                # Build transformed item without state history
                transformed_item = {
                    "id": f"WI-{item['id']}",
                    "raw_id": item["id"],  # Keep raw ID for state history fetching
                    "title": fields.get("System.Title") or "[No Title]",
                    "type": fields.get("System.WorkItemType") or "Unknown",
                    "priority": fields.get("Microsoft.VSTS.Common.Priority")
                    or "Medium",
                    "created_date": fields.get("System.CreatedDate") or "",
                    "created_by": (
                        fields.get("System.CreatedBy", {}).get("displayName")
                        if isinstance(fields.get("System.CreatedBy"), dict)
                        else str(fields.get("System.CreatedBy", ""))
                    )
                    or "Unknown",
                    "assigned_to": (
                        fields.get("System.AssignedTo", {}).get("displayName")
                        if isinstance(fields.get("System.AssignedTo"), dict)
                        else str(fields.get("System.AssignedTo", ""))
                    )
                    or "Unassigned",
                    "current_state": fields.get("System.State") or "New",
                    "state_transitions": [],  # Will be populated concurrently
                    "story_points": fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
                    "effort_hours": fields.get(
                        "Microsoft.VSTS.Scheduling.OriginalEstimate"
                    ),
                    "tags": (
                        fields.get("System.Tags", "").split(";")
                        if fields.get("System.Tags")
                        else []
                    ),
                }

                # Skip items with critical missing data
                if not transformed_item["created_date"]:
                    logger.warning(
                        f"Skipping work item {item['id']} - missing creation date"
                    )
                    continue

                work_items_to_process.append(transformed_item)

            # Now fetch state histories concurrently
            if progress_callback:
                progress_callback(
                    "items",
                    f"Fetching state history for {len(work_items_to_process)} items...",
                )

            # Use ThreadPoolExecutor for concurrent state history fetching
            max_workers = min(
                5, len(work_items_to_process)
            )  # Limit concurrent requests
            if work_items_to_process and max_workers > 0:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all state history requests
                    future_to_item = {
                        executor.submit(self._get_state_history, item["raw_id"]): item
                        for item in work_items_to_process
                    }

                    # Update progress as histories are fetched
                    completed = 0
                    total = len(work_items_to_process)

                    # Collect results as they complete
                    for future in as_completed(future_to_item):
                        item = future_to_item[future]
                        try:
                            state_transitions = future.result()
                            item["state_transitions"] = state_transitions
                        except Exception as e:
                            logger.warning(
                                f"Failed to get state history for {item['id']}: {e}"
                            )
                            item["state_transitions"] = []

                        completed += 1
                        if progress_callback and completed % 10 == 0:
                            progress_callback(
                                "items", f"Processed state history: {completed}/{total}"
                            )

                    # Remove raw_id field as it's no longer needed
                    for item in work_items_to_process:
                        item.pop("raw_id", None)
                        transformed_items.append(item)
            else:
                transformed_items = work_items_to_process

            return transformed_items

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.text}")
            return []
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred while fetching work items: {e}"
            )
            return []

    def _fetch_work_items_concurrent(
        self, batches: List[List[int]], progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Fetch work item batches concurrently for improved performance"""
        work_items = []
        completed_batches = 0
        total_batches = len(batches)

        def fetch_batch_with_retry(batch_ids: List[int], batch_num: int) -> List[Dict]:
            """Fetch a single batch with retry logic"""
            max_retries = 3
            base_delay = 1  # seconds

            for attempt in range(max_retries):
                try:
                    ids_string = ",".join(map(str, batch_ids))
                    details_url = f"{self.org_url}/{self.project}/_apis/wit/workitems?ids={ids_string}&$expand=relations&api-version=7.0"

                    logger.debug(
                        f"Fetching batch {batch_num + 1}/{total_batches} (attempt {attempt + 1})"
                    )

                    response = requests.get(
                        details_url, headers=self.headers, timeout=60
                    )

                    if response.status_code == 429:  # Rate limited
                        retry_after = int(
                            response.headers.get(
                                "Retry-After", base_delay * (2**attempt)
                            )
                        )
                        logger.debug(f"Rate limited, waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue

                    if response.status_code == 405:
                        logger.error(
                            f"HTTP 405 Method Not Allowed for batch {batch_num + 1}"
                        )
                        raise requests.exceptions.HTTPError(
                            f"Azure DevOps API returned 405 Method Not Allowed for work items details."
                        )

                    response.raise_for_status()
                    batch_work_items = response.json().get("value", [])

                    # Update progress
                    nonlocal completed_batches
                    completed_batches += 1
                    if progress_callback:
                        progress_callback("batch", completed_batches, total_batches)

                    return batch_work_items

                except requests.RequestException as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(
                            f"Failed to fetch batch {batch_num + 1} after {max_retries} attempts: {e}"
                        )
                        return []
                    else:
                        delay = base_delay * (2**attempt)
                        logger.debug(
                            f"Batch {batch_num + 1} failed (attempt {attempt + 1}), retrying in {delay}s..."
                        )
                        time.sleep(delay)

            return []

        # Use ThreadPoolExecutor for concurrent requests
        # Limit to 5 concurrent requests to respect API rate limits
        max_workers = min(5, len(batches))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batch requests
            future_to_batch = {
                executor.submit(fetch_batch_with_retry, batch, idx): idx
                for idx, batch in enumerate(batches)
            }

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_items = future.result()
                work_items.extend(batch_items)

        return work_items

    def _get_state_history(self, work_item_id: int) -> List[Dict]:
        """Get state transition history for a work item"""
        try:
            updates_url = f"{self.org_url}/{self.project}/_apis/wit/workitems/{work_item_id}/updates?api-version=7.0"
            response = requests.get(updates_url, headers=self.headers, timeout=30)

            if response.status_code == 405:
                logger.warning(
                    f"HTTP 405 for state history of work item {work_item_id}. Skipping state history."
                )
                return []

            if response.status_code != 200:
                logger.warning(
                    f"Failed to get state history for work item {work_item_id}: HTTP {response.status_code}"
                )
                return []

            updates = response.json().get("value", [])
            state_transitions = []

            for update in updates:
                fields = update.get("fields", {})
                if "System.State" in fields:
                    state_info = fields["System.State"]
                    if "newValue" in state_info:
                        transition = {
                            "state": state_info["newValue"],
                            "date": update.get("fields", {})
                            .get("System.ChangedDate", {})
                            .get("newValue", ""),
                            "assigned_to": update.get("fields", {})
                            .get("System.AssignedTo", {})
                            .get("newValue", {})
                            .get("displayName", ""),
                        }
                        state_transitions.append(transition)

            return state_transitions

        except Exception as e:
            print(
                f"Error fetching state history for work item {work_item_id}: {str(e)}"
            )
            return []

    def get_team_members(self) -> List[str]:
        """Get team members from Azure DevOps"""
        try:
            teams_url = (
                f"{self.org_url}/_apis/projects/{self.project}/teams?api-version=6.0"
            )
            response = requests.get(teams_url, headers=self.headers, timeout=30)

            if response.status_code != 200:
                return []

            teams = response.json().get("value", [])
            if not teams:
                return []

            # Get members of the first team (or you can specify a specific team)
            team_id = teams[0]["id"]
            members_url = f"{self.org_url}/_apis/projects/{self.project}/teams/{team_id}/members?api-version=6.0"

            members_response = requests.get(
                members_url, headers=self.headers, timeout=30
            )

            if members_response.status_code != 200:
                return []

            members = members_response.json().get("value", [])
            return [
                member.get("identity", {}).get("displayName", "") for member in members
            ]

        except Exception as e:
            print(f"Error fetching team members: {str(e)}")
            return []


def load_azure_devops_data():
    """Load real Azure DevOps data using the configured client"""
    try:
        import os

        with open("azure_devops_config.json", "r") as f:
            config = json.load(f)

        # Try environment variable first, then config file
        pat_token = os.getenv("AZURE_DEVOPS_PAT") or config.get("AZURE_DEVOPS_PAT")
        if not pat_token or pat_token == "YOUR_PAT_TOKEN_HERE":
            print("Please set your Azure DevOps PAT token:")
            print(
                "Option 1: Set environment variable: export AZURE_DEVOPS_PAT=your_token_here"
            )
            print("Option 2: Update azure_devops_config.json with your token")
            return None

        client = AzureDevOpsClient(
            org_url=config["AZURE_DEVOPS_ORG_URL"],
            project=config["AZURE_DEVOPS_DEFAULT_PROJECT"],
            pat_token=pat_token,
        )

        print("Fetching work items from Azure DevOps...")
        work_items = client.get_work_items()

        if work_items:
            print(f"Successfully fetched {len(work_items)} work items")

            # Save to file
            with open("azure_devops_workitems.json", "w") as f:
                json.dump(work_items, f, indent=2)

            return work_items
        else:
            print("No work items found or error occurred")
            return None

    except Exception as e:
        print(f"Error loading Azure DevOps data: {str(e)}")
        return None


if __name__ == "__main__":
    work_items = load_azure_devops_data()
    if work_items:
        print("Azure DevOps data loaded successfully!")
    else:
        print(
            "Failed to load Azure DevOps data. Check your configuration and PAT token."
        )
