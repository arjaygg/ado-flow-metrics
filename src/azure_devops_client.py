import base64
import json
import logging
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

import requests

from .exceptions import (
    ADOFlowException,
    AuthenticationError,
    AuthorizationError,
    APIError,
    NetworkError,
    ConfigurationError,
    WorkItemError
)

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

        except requests.exceptions.Timeout as e:
            logger.error(f"Connection timeout: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection verification: {e}")
            return False

    def get_work_items(
        self,
        days_back: int = 90,
        progress_callback: Optional[Callable] = None,
        history_limit: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch work items from Azure DevOps with enhanced progress tracking"""
        try:
            if progress_callback:
                progress_callback("phase", "Initializing Azure DevOps connection...")

            logger.debug(
                f"Fetching work items from the last {days_back} days for project '{self.project}'."
            )

            # Verify connection first to provide better error diagnostics
            if not self._validate_connection_and_project():
                return []

            # Get work item IDs using WIQL query
            work_item_ids = self._query_work_item_ids(days_back, progress_callback)
            if not work_item_ids:
                return []

            # Fetch detailed work item information
            work_items = self._fetch_work_item_details(work_item_ids, progress_callback)
            if not work_items:
                return []

            # Transform and enrich with state history
            return self._transform_and_enrich_work_items(work_items, progress_callback, history_limit)

        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout while fetching work items: {e}")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while fetching work items: {e}")
            return []
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception while fetching work items: {e}")
            return []
        except ADOFlowException as e:
            logger.error(f"ADO Flow error: {e.message}")
            return []
        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while fetching work items: {e}"
            )
            return []

    def _validate_connection_and_project(self) -> bool:
        """Validate Azure DevOps connection and project configuration."""
        if not self.verify_connection():
            logger.error(
                "Connection verification failed. Cannot proceed with work item fetch."
            )
            return False

        # Validate project name to prevent injection (basic sanitization)
        if not self.project.replace("-", "").replace("_", "").isalnum():
            raise ConfigurationError(f"Invalid project name: {self.project}")

        return True

    def _query_work_item_ids(self, days_back: int, progress_callback: Optional[Callable] = None) -> List[int]:
        """Query work item IDs using WIQL with proper project scoping."""
        if progress_callback:
            progress_callback("phase", "Querying work item IDs...")

        # Build WIQL query with validated inputs and project scope
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        wiql_query = {
            "query": f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.project}'
            AND [System.ChangedDate] >= '{cutoff_date}'
            ORDER BY [System.ChangedDate] DESC
            """
        }

        response = self._execute_wiql_query(wiql_query)
        work_item_refs = self._parse_wiql_response(response)
        
        if progress_callback:
            progress_callback("count", len(work_item_refs))

        if not work_item_refs:
            logger.warning("No work items found in the specified period.")
            return []

        return [item["id"] for item in work_item_refs]

    def _execute_wiql_query(self, wiql_query: Dict) -> requests.Response:
        """Execute WIQL query with proper error handling."""
        wiql_url = f"{self.org_url}/{self.project}/_apis/wit/wiql?api-version=7.0"
        logger.debug(f"Making WIQL request to: {wiql_url}")
        
        response = requests.post(
            wiql_url, json=wiql_query, headers=self.headers, timeout=30
        )

        if response.status_code == 405:
            logger.error(f"HTTP 405 Method Not Allowed. URL: {wiql_url}")
            # Create safe headers for logging (redact PAT token)
            safe_headers = {
                k: ("Basic [REDACTED]" if k == "Authorization" else v)
                for k, v in self.headers.items()
            }
            logger.error(f"Request headers: {safe_headers}")
            logger.error(f"Request body: {wiql_query}")
            raise APIError(
                "Azure DevOps API returned 405 Method Not Allowed. This usually indicates an incorrect API endpoint or authentication issue.",
                status_code=405
            )

        response.raise_for_status()
        return response

    def _parse_wiql_response(self, response: requests.Response) -> List[Dict]:
        """Parse WIQL response with comprehensive error handling."""
        try:
            response_data = response.json()
            return response_data.get("workItems", [])
        except ValueError as json_error:
            # Log the actual response for debugging
            logger.error(f"Invalid JSON response from Azure DevOps API")
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response headers: {dict(response.headers)}")
            logger.error(f"Response content (first 500 chars): {response.text[:500]}")
            
            # Check if it's an HTML error page (common with auth issues)
            if response.text.strip().startswith('<'):
                logger.error("Response appears to be HTML, likely an authentication or access error")
                if "conditional access" in response.text.lower():
                    logger.error("Conditional Access Policy detected - use --use-mock flag for testing")
                elif "sign in" in response.text.lower() or "login" in response.text.lower():
                    logger.error("Authentication required - check your PAT token")
            
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed - check your PAT token"
                )
            elif response.status_code == 403:
                raise AuthorizationError(
                    "Access forbidden - check project permissions or conditional access policies"
                )
            else:
                raise APIError(
                    f"Azure DevOps API returned invalid JSON. Response status: {response.status_code}. Use --use-mock flag to generate test data instead.",
                    status_code=response.status_code,
                    response_text=response.text[:500]
                ) from json_error

    def _fetch_work_item_details(self, work_item_ids: List[int], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Fetch detailed work item information in batches."""
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
        
        return work_items

    def _transform_and_enrich_work_items(
        self, 
        work_items: List[Dict], 
        progress_callback: Optional[Callable] = None, 
        history_limit: Optional[int] = None
    ) -> List[Dict]:
        """Transform work items to our format and enrich with state history."""
        if progress_callback:
            progress_callback("phase", "Processing work items and state history...")

        # First, prepare all work items without state history
        work_items_to_process = self._transform_work_items(work_items)
        
        # Then enrich with state history concurrently
        return self._enrich_with_state_history(work_items_to_process, progress_callback, history_limit)

    def _transform_work_items(self, work_items: List[Dict]) -> List[Dict]:
        """Transform raw work items to our standardized format."""
        work_items_to_process = []
        
        for item in work_items:
            fields = item.get("fields", {})

            # Generate proper web link for Azure DevOps
            # Convert from: https://dev.azure.com/ORG/PROJECT_GUID/_apis/wit/workItems/ID
            # To: https://ORG.visualstudio.com/PROJECT/_workitems/edit/ID
            web_link = None
            if self.org_url and self.project and item["id"]:
                # Extract org name from the org URL
                org_name = self.org_url.replace("https://dev.azure.com/", "").replace("https://", "").replace(".visualstudio.com", "").rstrip("/")
                # Use the actual project name from configuration
                web_link = f"https://{org_name}.visualstudio.com/{self.project}/_workitems/edit/{item['id']}"
            
            # Build transformed item without state history (will be fetched concurrently)
            transformed_item = {
                "id": item["id"],  # Use real Azure DevOps numeric ID directly
                "raw_id": item["id"],  # Keep raw ID for state history fetching
                "title": fields.get("System.Title") or "[No Title]",
                "type": fields.get("System.WorkItemType") or "Unknown",
                "priority": fields.get("Microsoft.VSTS.Common.Priority") or "Medium",
                "created_date": fields.get("System.CreatedDate") or "",
                "created_by": self._extract_display_name(fields.get("System.CreatedBy")) or "Unknown",
                "assigned_to": self._extract_display_name(fields.get("System.AssignedTo")) or "Unassigned",
                "current_state": fields.get("System.State") or "New",
                "state_transitions": [],  # Will be populated concurrently
                "story_points": fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
                "effort_hours": fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate"),
                "tags": self._parse_tags(fields.get("System.Tags")),
                # Preserve Azure DevOps API fields
                "url": item.get("url"),  # Direct API endpoint
                "_links": item.get("_links", {}),  # Navigation links
                "rev": item.get("rev"),  # Revision number
                "link": web_link,  # Proper web UI link
            }

            # Skip items with critical missing data
            if not transformed_item["created_date"]:
                logger.warning(
                    f"Skipping work item {item['id']} - missing creation date"
                )
                continue

            work_items_to_process.append(transformed_item)
            
        return work_items_to_process

    def _extract_display_name(self, field_value) -> str:
        """Extract display name from Azure DevOps user field."""
        if isinstance(field_value, dict):
            return field_value.get("displayName", "")
        return str(field_value) if field_value else ""

    def _parse_tags(self, tags_value) -> List[str]:
        """Parse tags from Azure DevOps tags field."""
        if not tags_value:
            return []
        return tags_value.split(";")

    def _enrich_with_state_history(
        self, 
        work_items_to_process: List[Dict], 
        progress_callback: Optional[Callable] = None, 
        history_limit: Optional[int] = None
    ) -> List[Dict]:
        """Enrich work items with state history using concurrent processing."""
        if progress_callback:
            progress_callback(
                "items",
                f"Fetching state history for {len(work_items_to_process)} items...",
            )

        # Use ThreadPoolExecutor for concurrent state history fetching
        max_workers = min(5, len(work_items_to_process))  # Limit concurrent requests
        
        if not work_items_to_process or max_workers <= 0:
            return work_items_to_process

        transformed_items = []
        
        # Thread-safe counter for progress tracking
        progress_lock = threading.Lock()
        completed = 0
        total = len(work_items_to_process)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all state history requests
            future_to_item = {
                executor.submit(
                    self._get_state_history, item["raw_id"], history_limit
                ): item
                for item in work_items_to_process
            }

            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    state_transitions = future.result(timeout=30)  # Add timeout
                    item["state_transitions"] = state_transitions
                except KeyboardInterrupt:
                    logger.info("Cancelling remaining state history requests...")
                    # Thread-safe cancellation
                    remaining_futures = list(future_to_item.keys())
                    for f in remaining_futures:
                        f.cancel()
                    raise
                except Exception as e:
                    logger.warning(
                        f"Failed to get state history for {item['id']}: {e}"
                    )
                    item["state_transitions"] = []

                # Thread-safe progress update
                with progress_lock:
                    completed += 1
                    if progress_callback and completed % 10 == 0:
                        progress_callback(
                            "items", f"Processed state history: {completed}/{total}"
                        )

            # Remove raw_id field as it's no longer needed
            for item in work_items_to_process:
                item.pop("raw_id", None)
                transformed_items.append(item)
                
        return transformed_items

    def _fetch_work_items_concurrent(
        self, batches: List[List[int]], progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Fetch work item batches concurrently for improved performance"""
        work_items = []
        work_items_lock = threading.Lock()
        completed_batches = 0
        progress_lock = threading.Lock()
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

                    # Thread-safe progress update
                    nonlocal completed_batches
                    with progress_lock:
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

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all batch requests
                future_to_batch = {
                    executor.submit(fetch_batch_with_retry, batch, idx): idx
                    for idx, batch in enumerate(batches)
                }

                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    try:
                        batch_items = future.result(timeout=30)  # Add timeout
                        # Thread-safe list extension
                        with work_items_lock:
                            work_items.extend(batch_items)
                    except KeyboardInterrupt:
                        logger.info("Cancelling remaining batch requests...")
                        # Thread-safe cancellation
                        remaining_futures = list(future_to_batch.keys())
                        for f in remaining_futures:
                            f.cancel()
                        raise
                    except Exception as e:
                        logger.warning(f"Batch request failed: {e}")
                        continue
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            raise

        return work_items

    def _get_state_history(
        self, work_item_id: int, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get state transition history for a work item with optional limit for performance"""
        try:
            # Add limit parameter for performance optimization during testing
            limit_param = f"&$top={limit}" if limit else ""
            updates_url = f"{self.org_url}/{self.project}/_apis/wit/workitems/{work_item_id}/updates?api-version=7.0{limit_param}"
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
