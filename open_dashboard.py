#!/usr/bin/env python3
"""
Simple dashboard launcher for Flow Metrics
Opens the browser-based dashboard that requires no server.
"""
import webbrowser
import os
from pathlib import Path


def open_dashboard():
    """Open the Flow Metrics dashboard in the default browser."""
    script_dir = Path(__file__).parent
    dashboard_path = script_dir / "dashboard.html"
    
    print(f"🔍 Looking for dashboard at: {dashboard_path}")
    print(f"📁 Script directory: {script_dir}")
    print(f"📋 Files in directory: {list(script_dir.glob('*.html'))}")
    
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found at: {dashboard_path}")
        print("Make sure dashboard.html exists in the same directory as this script.")
        
        # Try alternative locations
        alt_paths = [
            script_dir.parent / "dashboard.html",  # Parent directory
            script_dir.parent / "dashboard" / "index.html",  # Shared dashboard
        ]
        
        for alt_path in alt_paths:
            if alt_path.exists():
                print(f"✅ Found dashboard at alternative location: {alt_path}")
                dashboard_path = alt_path
                break
        else:
            return False
    
    # Convert to file:// URL for browser (Windows-compatible)
    dashboard_url = dashboard_path.absolute().as_uri()
    
    print(f"🚀 Opening Flow Metrics Dashboard...")
    print(f"📊 URL: {dashboard_url}")
    
    try:
        webbrowser.open(dashboard_url)
        print("✅ Dashboard opened in your default browser")
        print("\n📝 Dashboard Features:")
        print("  • Mock data (default) - generates sample flow metrics")
        print("  • JSON file upload - load your own metrics data")
        print("  • IndexedDB - persists data between sessions")
        print("\n💡 To load real data:")
        print("  1. Run the flow metrics calculator to generate JSON")
        print("  2. Use 'Load JSON' button in the dashboard")
        print("  3. Select your generated metrics file")
        return True
    except Exception as e:
        print(f"❌ Error opening dashboard: {e}")
        print(f"💡 Manually open: {dashboard_url}")
        return False


if __name__ == "__main__":
    open_dashboard()