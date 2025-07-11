#!/usr/bin/env python3
"""
Test script to verify Azure DevOps connection and diagnose HTTP 405 errors.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from azure_devops_client import AzureDevOpsClient  # noqa: E402
from config_manager import get_settings  # noqa: E402

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_azure_connection():
    """Test Azure DevOps connection with detailed diagnostics."""
    try:
        # Load settings
        settings = get_settings()

        if not settings.azure_devops.pat_token:
            print("❌ Error: AZURE_DEVOPS_PAT environment variable not set")
            return False

        print(f"🔧 Organization URL: {settings.azure_devops.org_url}")
        print(f"🔧 Project: {settings.azure_devops.default_project}")
        token_display = (
            "***" + settings.azure_devops.pat_token[-4:]
            if len(settings.azure_devops.pat_token) > 4
            else "Set"
        )
        print(f"🔧 PAT Token: {token_display}")

        # Create client
        client = AzureDevOpsClient(
            settings.azure_devops.org_url,
            settings.azure_devops.default_project,
            settings.azure_devops.pat_token,
        )

        print("\n🧪 Testing Azure DevOps connection...")

        # Test connection
        if client.verify_connection():
            print("✅ Connection verification successful!")

            print("\n🧪 Testing work items fetch (1 day)...")
            work_items = client.get_work_items(days_back=1)

            if work_items:
                print(f"✅ Successfully fetched {len(work_items)} work items")

                # Show sample work item structure
                if work_items:
                    sample = work_items[0]
                    print("\n📄 Sample work item structure:")
                    print(f"   ID: {sample.get('id', 'N/A')}")
                    title = sample.get('title', 'N/A')
                    print(f"   Title: {title[:50]}...")
                    print(f"   Type: {sample.get('type', 'N/A')}")
                    print(f"   State: {sample.get('current_state', 'N/A')}")
                    print(f"   Created: {sample.get('created_date', 'N/A')}")

                return True
            else:
                print(
                    "⚠️  No work items found "
                    "(this might be normal for a short time period)"
                )
                return True
        else:
            print("❌ Connection verification failed")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logging.exception("Detailed error information:")
        return False


if __name__ == "__main__":
    print("🚀 Azure DevOps Connection Test")
    print("=" * 50)

    success = test_azure_connection()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Azure DevOps integration is working.")
    else:
        print("💥 Tests failed. Check the error messages above.")
        sys.exit(1)
