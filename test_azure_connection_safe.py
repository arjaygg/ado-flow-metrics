#!/usr/bin/env python3
"""
Safe Azure DevOps Connection Test
Tests connection with better error handling and fallback suggestions
"""

import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config_manager import get_settings
    from azure_devops_client import AzureDevOpsClient
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_azure_connection():
    """Test Azure DevOps connection with safe error handling"""
    print("Flow Metrics - Azure DevOps Connection Test")
    print("=" * 50)
    
    try:
        # Load configuration
        print("Loading configuration...")
        settings = get_settings()
        
        # Check if PAT token is configured
        pat_token = os.getenv("AZURE_DEVOPS_PAT")
        if not pat_token:
            print("❌ AZURE_DEVOPS_PAT environment variable not set")
            print("\nTo fix this:")
            print("1. Get a PAT token from Azure DevOps:")
            print("   https://dev.azure.com/[your-org]/_usersettings/tokens")
            print("2. Set environment variable:")
            print("   set AZURE_DEVOPS_PAT=your_token_here")
            print("\nOr use mock data:")
            print("   python -m src.cli data fresh --use-mock")
            return False
        
        print(f"✓ PAT token configured (length: {len(pat_token)})")
        print(f"✓ Organization: {settings.azure_devops.org_url}")
        print(f"✓ Project: {settings.azure_devops.default_project}")
        
        # Test connection
        print("\nTesting Azure DevOps connection...")
        client = AzureDevOpsClient(
            org_url=settings.azure_devops.org_url,
            project=settings.azure_devops.default_project,
            pat_token=pat_token
        )
        
        # Simple connection test
        if client.verify_connection():
            print("✓ Connection successful!")
            
            # Try a minimal work item query
            print("\nTesting work item query...")
            try:
                work_items = client.get_work_items(days_back=1, history_limit=1)
                print(f"✓ Query successful! Found {len(work_items)} work items")
                
                if len(work_items) == 0:
                    print("ℹ No work items found in the last day")
                    print("Try increasing days_back or use mock data:")
                    print("   python -m src.cli data fresh --use-mock")
                
                return True
                
            except Exception as query_error:
                error_msg = str(query_error).lower()
                print(f"❌ Work item query failed: {query_error}")
                
                if "json" in error_msg or "invalid" in error_msg:
                    print("\n🔍 Diagnosis: Azure DevOps returned invalid JSON")
                    print("This usually indicates:")
                    print("• Conditional Access Policy blocking API access")
                    print("• Authentication/authorization issues")
                    print("• Corporate firewall/proxy interference")
                    
                elif "403" in error_msg or "forbidden" in error_msg:
                    print("\n🔍 Diagnosis: Access forbidden")
                    print("• Check PAT token permissions")
                    print("• Ensure token has 'Work Items' read access")
                    
                elif "404" in error_msg:
                    print("\n🔍 Diagnosis: Project not found")
                    print("• Verify project name is correct")
                    print("• Check if you have access to the project")
                
                print("\n💡 Recommended solution:")
                print("   python -m src.cli data fresh --use-mock")
                return False
        else:
            print("❌ Connection failed!")
            print("\n💡 Try using mock data instead:")
            print("   python -m src.cli data fresh --use-mock")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n💡 Use mock data for testing:")
        print("   python -m src.cli data fresh --use-mock")
        return False


def main():
    success = test_azure_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Azure DevOps connection working!")
        print("\nYou can now run:")
        print("   python -m src.cli data fresh --days-back 7")
        print("   python -m src.cli serve --open-browser")
    else:
        print("⚠️  Azure DevOps connection issues detected")
        print("\nFor immediate testing, use:")
        print("   python -m src.cli data fresh --use-mock")
        print("   python -m src.cli serve --open-browser")
        print("\nThis will generate realistic test data for the dashboard.")
    
    print("\nPress Enter to continue...")
    input()


if __name__ == "__main__":
    main()