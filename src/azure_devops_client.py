import base64
import json
import logging
from typing import Dict, List

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

    def get_work_items(self, days_back: int = 90) -> List[Dict]:
        """Fetch work items from Azure DevOps"""
        logger.info(
            f"Fetching work items from the last {days_back} days for project '{self.project}'."
        )
        try:
            # First, get work item IDs using WIQL
            wiql_query = {
                "query": f"""
                SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType],
                       [System.CreatedDate], [System.AssignedTo], [Microsoft.VSTS.Common.Priority]
                FROM WorkItems
                WHERE [System.TeamProject] = '{self.project}'
                  AND [System.CreatedDate] >= @today - {days_back}
                ORDER BY [System.CreatedDate] DESC
                """
            }

            wiql_url = f"{self.org_url}/{self.project}/_apis/wit/wiql?api-version=6.0"
            response = requests.post(wiql_url, json=wiql_query, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes

            work_item_refs = response.json().get("workItems", [])
            logger.info(f"Found {len(work_item_refs)} work item references.")

            if not work_item_refs:
                logger.warning("No work items found in the specified period.")
                return []

            work_item_ids = [item["id"] for item in work_item_refs]

            # Get detailed work item information in batches to avoid URL length limits
            work_items = []
            batch_size = 200  # Azure DevOps API limit
            for i in range(0, len(work_item_ids), batch_size):
                batch_ids = work_item_ids[i : i + batch_size]
                ids_string = ",".join(map(str, batch_ids))
                details_url = f"{self.org_url}/{self.project}/_apis/wit/workitems?ids={ids_string}&$expand=relations&api-version=6.0"

                logger.info(
                    f"Fetching details for batch {i//batch_size + 1}/{len(work_item_ids)//batch_size + 1} ({len(batch_ids)} items)."
                )
                details_response = requests.get(details_url, headers=self.headers)
                details_response.raise_for_status()

                batch_work_items = details_response.json().get("value", [])
                work_items.extend(batch_work_items)

            logger.info(
                f"Successfully fetched details for {len(work_items)} work items in total."
            )

            # Transform to our format
            transformed_items = []
            for item in work_items:
                fields = item.get("fields", {})

                # Get state history
                state_transitions = self._get_state_history(item["id"])

                # Build transformed item with better default handling
                transformed_item = {
                    "id": f"WI-{item['id']}",
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
                    "state_transitions": state_transitions,
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

                transformed_items.append(transformed_item)

            return transformed_items

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {response.text}")
            return []
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred while fetching work items: {e}"
            )
            return []

    def _get_state_history(self, work_item_id: int) -> List[Dict]:
        """Get state transition history for a work item"""
        try:
            updates_url = f"{self.org_url}/{self.project}/_apis/wit/workitems/{work_item_id}/updates?api-version=6.0"
            response = requests.get(updates_url, headers=self.headers)

            if response.status_code != 200:
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
            response = requests.get(teams_url, headers=self.headers)

            if response.status_code != 200:
                return []

            teams = response.json().get("value", [])
            if not teams:
                return []

            # Get members of the first team (or you can specify a specific team)
            team_id = teams[0]["id"]
            members_url = f"{self.org_url}/_apis/projects/{self.project}/teams/{team_id}/members?api-version=6.0"

            members_response = requests.get(members_url, headers=self.headers)

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
