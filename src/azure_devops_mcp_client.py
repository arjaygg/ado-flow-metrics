"""Azure DevOps client using MCP server integration."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# Note: This would require MCP client library
# from mcp_client import MCPClient, MCPError


class AzureDevOpsMCPClient:
    """Azure DevOps client using MCP server for data access."""

    def __init__(self, mcp_server_name: str = "azure-devops-mcp"):
        self.mcp_server_name = mcp_server_name
        # self.mcp_client = MCPClient(mcp_server_name)

    def get_work_items(
        self, days_back: int = 90, project: Optional[str] = None
    ) -> List[Dict]:
        """Fetch work items via MCP server."""
        try:
            # MCP tool call - this would be the actual implementation
            # result = self.mcp_client.call_tool("get_work_items", {
            #     "days_back": days_back,
            #     "project": project
            # })

            # For now, return placeholder showing intended structure
            return self._mock_mcp_response(days_back, project)

        except Exception as e:
            print(f"Error fetching work items via MCP: {e}")
            return []

    def get_work_item_history(self, work_item_id: int) -> List[Dict]:
        """Get work item state transition history via MCP."""
        try:
            # result = self.mcp_client.call_tool("get_work_item_history", {
            #     "work_item_id": work_item_id
            # })

            return self._mock_history_response(work_item_id)

        except Exception as e:
            print(f"Error fetching work item history via MCP: {e}")
            return []

    def _mock_mcp_response(self, days_back: int, project: Optional[str]) -> List[Dict]:
        """Mock MCP response for development."""
        return [
            {
                "id": 12345,
                "title": "Example work item from MCP",
                "type": "User Story",
                "state": "Active",
                "assigned_to": "developer@company.com",
                "created_date": "2024-01-01T00:00:00Z",
                "project": project or "Default-Project",
                "mcp_source": True,
            }
        ]

    def _mock_history_response(self, work_item_id: int) -> List[Dict]:
        """Mock work item history from MCP."""
        return [
            {
                "work_item_id": work_item_id,
                "from_state": "New",
                "to_state": "Active",
                "changed_date": "2024-01-01T00:00:00Z",
                "changed_by": "developer@company.com",
            },
            {
                "work_item_id": work_item_id,
                "from_state": "Active",
                "to_state": "Resolved",
                "changed_date": "2024-01-05T00:00:00Z",
                "changed_by": "developer@company.com",
            },
        ]


# Factory function to choose client type
def create_azure_devops_client(use_mcp: bool = False, **kwargs) -> object:
    """Create appropriate Azure DevOps client."""
    if use_mcp:
        return AzureDevOpsMCPClient(kwargs.get("mcp_server_name", "azure-devops-mcp"))
    else:
        from .azure_devops_client import AzureDevOpsClient

        return AzureDevOpsClient(
            kwargs["org_url"], kwargs["project"], kwargs["pat_token"]
        )
