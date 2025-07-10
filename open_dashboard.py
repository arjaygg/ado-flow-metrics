#!/usr/bin/env python3
"""
Simple script to open the executive dashboard and show available data files
"""

import os
import subprocess
import sys
from pathlib import Path

def open_dashboard():
    """Open the executive dashboard and show available data files."""
    
    print("🎯 Opening Executive Dashboard")
    print("=" * 40)
    
    # Check dashboard file
    dashboard_file = Path("../dashboard/executive-index.html")
    if not dashboard_file.exists():
        print("❌ Dashboard file not found!")
        return False
    
    # List available data files
    dashboard_dir = Path("../dashboard")
    json_files = list(dashboard_dir.glob("*.json"))
    json_files = [f for f in json_files if f.name != "package.json"]
    
    print("📊 Available Data Files:")
    for json_file in sorted(json_files):
        size_kb = json_file.stat().st_size / 1024
        print(f"   • {json_file.name} ({size_kb:.1f} KB)")
    
    print(f"\n📁 Dashboard Location: {dashboard_file.absolute()}")
    
    # Convert Windows path for opening in browser
    windows_path = str(dashboard_file.absolute()).replace("/mnt/c/", "C:/").replace("/", "\\")
    
    print(f"🌐 Opening in browser...")
    print(f"   Windows Path: {windows_path}")
    
    try:
        # Try to open with default browser (works on Windows)
        if os.name == 'nt':
            os.startfile(windows_path)
        else:
            # For WSL, try to use Windows explorer to open
            subprocess.run(["explorer.exe", windows_path], check=True)
        
        print("✅ Dashboard opened successfully!")
        
    except Exception as e:
        print(f"⚠️  Could not auto-open dashboard: {e}")
        print(f"🔧 Manual Steps:")
        print(f"   1. Open file explorer to: C:\\dev\\PerfMngmt\\flow_metrics\\dashboard\\")
        print(f"   2. Double-click: executive-index.html")
        print(f"   3. Or paste this in browser: file:///{windows_path}")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Click 'Upload Report' button in dashboard")
    print(f"   2. Select one of these data files:")
    for json_file in sorted(json_files):
        if "ado_integration" in json_file.name or "live_demo" in json_file.name:
            print(f"      → {json_file.name} (recommended)")
        else:
            print(f"      • {json_file.name}")
    print(f"   3. View executive metrics and insights")
    
    return True

if __name__ == "__main__":
    success = open_dashboard()
    if success:
        input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)