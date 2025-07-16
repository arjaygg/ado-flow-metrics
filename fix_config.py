#!/usr/bin/env python3
"""
Fix configuration issues with Azure DevOps setup
Helps users resolve the 'Project Not Found Error' caused by placeholder org names
"""

import json
import os
import sys
from pathlib import Path


def check_current_config():
    """Check the current configuration for placeholder values."""
    print("🔍 Checking current configuration...")
    
    config_path = Path("config/config.json")
    sample_path = Path("config/config.sample.json")
    
    issues = []
    
    # Check if config file exists
    if not config_path.exists():
        if sample_path.exists():
            issues.append("❌ config.json missing - only config.sample.json exists")
        else:
            issues.append("❌ No configuration files found")
    else:
        # Check config.json content
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            azure_config = config.get('azure_devops', {})
            org_url = azure_config.get('org_url', '')
            project = azure_config.get('default_project', '')
            
            if 'your-org' in org_url or 'your-organization' in org_url:
                issues.append(f"❌ Placeholder org URL in config: {org_url}")
            
            if 'your-project' in project.lower() or not project:
                issues.append(f"❌ Placeholder project name in config: {project}")
                
        except Exception as e:
            issues.append(f"❌ Error reading config.json: {e}")
    
    # Check environment variables
    pat_token = os.getenv("AZURE_DEVOPS_PAT")
    org_env = os.getenv("AZURE_DEVOPS_ORG")
    project_env = os.getenv("AZURE_DEVOPS_PROJECT")
    
    print("\n📋 Environment Variables:")
    print(f"   AZURE_DEVOPS_PAT: {'✅ Set' if pat_token else '❌ Not set'}")
    print(f"   AZURE_DEVOPS_ORG: {org_env if org_env else '❌ Not set'}")
    print(f"   AZURE_DEVOPS_PROJECT: {project_env if project_env else '❌ Not set'}")
    
    if org_env and ('your-org' in org_env or 'YOUR_ORG_HERE' in org_env):
        issues.append(f"❌ Placeholder org URL in environment: {org_env}")
    
    return issues


def fix_config_interactively():
    """Interactive configuration fix."""
    print("\n🔧 Interactive Configuration Fix")
    print("=" * 40)
    
    org_name = input("Enter your Azure DevOps organization name (without https://dev.azure.com/): ").strip()
    if not org_name:
        print("❌ Organization name is required")
        return False
    
    project_name = input("Enter your Azure DevOps project name: ").strip()
    if not project_name:
        print("❌ Project name is required")
        return False
    
    # Create or update config.json
    config_path = Path("config/config.json")
    sample_path = Path("config/config.sample.json")
    
    # Load base config from sample or create new
    if sample_path.exists():
        with open(sample_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "azure_devops": {
                "org_url": "",
                "default_project": "",
                "api_version": "7.0"
            }
        }
    
    # Update with actual values
    config["azure_devops"]["org_url"] = f"https://dev.azure.com/{org_name}"
    config["azure_devops"]["default_project"] = project_name
    
    # Ensure config directory exists
    config_path.parent.mkdir(exist_ok=True)
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration updated in {config_path}")
    print(f"   Organization: https://dev.azure.com/{org_name}")
    print(f"   Project: {project_name}")
    
    print("\n💡 Don't forget to set your PAT token:")
    print(f"   export AZURE_DEVOPS_PAT='your-personal-access-token'")
    
    return True


def show_fix_instructions():
    """Show manual fix instructions."""
    print("\n📋 Manual Fix Instructions")
    print("=" * 30)
    
    print("\n1️⃣ Option 1: Set Environment Variables")
    print("   export AZURE_DEVOPS_PAT='your-pat-token'")
    print("   export AZURE_DEVOPS_ORG='https://dev.azure.com/YOUR_ORG_NAME'")
    print("   export AZURE_DEVOPS_PROJECT='YourProjectName'")
    
    print("\n2️⃣ Option 2: Update config.json")
    print("   • Copy config/config.sample.json to config/config.json")
    print("   • Replace 'your-organization' with your actual org name")
    print("   • Replace 'Your-Project-Name' with your actual project name")
    
    print("\n3️⃣ Test the fix:")
    print("   python3 -m src.cli data fresh --use-mock")
    
    print("\n🔗 Common Azure DevOps URLs:")
    print("   Format: https://dev.azure.com/{organization}")
    print("   Example: https://dev.azure.com/contoso")


def main():
    """Main function to diagnose and fix configuration issues."""
    print("🚑 Azure DevOps Configuration Doctor")
    print("=" * 40)
    print("This tool helps fix 'Project Not Found Error' issues")
    print("caused by placeholder organization names like 'your-org'\n")
    
    # Check current config
    issues = check_current_config()
    
    if not issues:
        print("\n✅ Configuration looks good!")
        print("If you're still getting 'Project Not Found Error', check:")
        print("   • PAT token has correct permissions")
        print("   • Organization and project names are spelled correctly")
        print("   • You have access to the specified project")
        return
    
    print("\n🚨 Issues Found:")
    for issue in issues:
        print(f"   {issue}")
    
    print("\nChoose an option:")
    print("1. Interactive fix (recommended)")
    print("2. Show manual fix instructions")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            if fix_config_interactively():
                print("\n🎉 Configuration fixed! Try running your command again.")
            else:
                print("\n❌ Configuration fix failed")
        elif choice == "2":
            show_fix_instructions()
        elif choice == "3":
            print("Exiting...")
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    main()