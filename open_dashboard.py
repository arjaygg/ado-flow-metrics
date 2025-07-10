#!/usr/bin/env python3
"""
Dashboard launcher for Flow Metrics
Opens browser-based dashboards that require no server.
Supports both standard and executive dashboards.
"""
import webbrowser
import os
import sys
from pathlib import Path


def open_dashboard(dashboard_type="standard"):
    """Open the Flow Metrics dashboard in the default browser."""
    script_dir = Path(__file__).parent

    # Determine which dashboard to open
    if dashboard_type.lower() in ["executive", "exec", "e"]:
        dashboard_file = "executive-dashboard.html"
        dashboard_name = "Executive Dashboard"
    else:
        dashboard_file = "dashboard.html"
        dashboard_name = "Standard Dashboard"

    dashboard_path = script_dir / dashboard_file

    print(f"🔍 Looking for {dashboard_name} at: {dashboard_path}")
    print(f"📁 Script directory: {script_dir}")
    print(f"📋 Available dashboards: {list(script_dir.glob('*dashboard*.html'))}")

    if not dashboard_path.exists():
        print(f"❌ {dashboard_name} not found at: {dashboard_path}")

        # Try alternative locations
        alt_paths = [
            script_dir.parent / dashboard_file,  # Parent directory
            (
                script_dir.parent / "dashboard" / "index.html"
                if dashboard_type == "standard"
                else script_dir.parent / "dashboard" / "executive-index.html"
            ),
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                print(f"✅ Found {dashboard_name} at alternative location: {alt_path}")
                dashboard_path = alt_path
                break
        else:
            print(f"💡 Available dashboard options:")
            available = list(script_dir.glob("*dashboard*.html"))
            for dash in available:
                print(f"   • {dash.name}")
            return False

    # Convert to file:// URL for browser (Windows-compatible)
    dashboard_url = dashboard_path.absolute().as_uri()

    print(f"🚀 Opening {dashboard_name}...")
    print(f"📊 URL: {dashboard_url}")

    try:
        webbrowser.open(dashboard_url)
        print(f"✅ {dashboard_name} opened in your default browser")

        if dashboard_type.lower() in ["executive", "exec", "e"]:
            print("\n📊 Executive Dashboard Features:")
            print("  • High-level KPIs and executive summary")
            print("  • DORA metrics visualization")
            print("  • Team performance overview")
            print("  • Trend analysis and forecasting")
        else:
            print("\n📝 Standard Dashboard Features:")
            print("  • Detailed flow metrics and charts")
            print("  • Mock data (default) - generates sample flow metrics")
            print("  • JSON file upload - load your own metrics data")
            print("  • IndexedDB - persists data between sessions")

        print("\n💡 To load real data:")
        print("  1. Run the flow metrics calculator to generate JSON")
        print("  2. Use 'Load JSON' button in the dashboard")
        print("  3. Select your generated metrics file")
        return True
    except Exception as e:
        print(f"❌ Error opening {dashboard_name}: {e}")
        print(f"💡 Manually open: {dashboard_url}")
        return False


def main():
    """Main function to handle command line arguments."""
    dashboard_type = "standard"

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["executive", "exec", "e", "--executive", "-e"]:
            dashboard_type = "executive"
        elif arg in ["standard", "std", "s", "--standard", "-s"]:
            dashboard_type = "standard"
        elif arg in ["help", "--help", "-h"]:
            print("Flow Metrics Dashboard Launcher")
            print("\nUsage:")
            print("  python open_dashboard.py [dashboard_type]")
            print("\nDashboard Types:")
            print("  standard (default) - Detailed flow metrics dashboard")
            print("  executive          - High-level executive summary dashboard")
            print("\nExamples:")
            print("  python open_dashboard.py")
            print("  python open_dashboard.py executive")
            print("  python open_dashboard.py standard")
            return
        else:
            print(f"Unknown dashboard type: {arg}")
            print("Use 'python open_dashboard.py help' for usage information")
            return

    open_dashboard(dashboard_type)


if __name__ == "__main__":
    main()
