#!/usr/bin/env python3
"""
Debug Configuration Loading
Shows which config file is being loaded and its contents
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config_manager import get_settings
    
    print("Flow Metrics - Configuration Debug")
    print("=" * 40)
    
    print("\nChecking config file locations...")
    
    # Check all possible config paths
    search_paths = [
        Path(__file__).parent / "powershell" / "config.json",
        Path("config/config.json"),
        Path("../config/config.json"),
        Path.home() / ".flow_metrics" / "config.json",
    ]
    
    for i, path in enumerate(search_paths, 1):
        exists = path.exists()
        print(f"{i}. {path} - {'EXISTS' if exists else 'NOT FOUND'}")
        if exists:
            print(f"   Size: {path.stat().st_size} bytes")
    
    print("\nLoading configuration...")
    settings = get_settings()
    
    print(f"✓ Configuration loaded successfully")
    print(f"Organization: {settings.azure_devops.org_url}")
    print(f"Project: {settings.azure_devops.default_project}")
    
    # Check if it's loading the right values
    if settings.azure_devops.default_project == "Your-Project-Name":
        print("\n❌ ERROR: Loading sample config instead of real config!")
        print("This explains the 'your-project-name' error")
    elif settings.azure_devops.default_project == "Axos-Universal-Core":
        print("\n✓ Loading correct config file")
    else:
        print(f"\n? Unknown project name: {settings.azure_devops.default_project}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()