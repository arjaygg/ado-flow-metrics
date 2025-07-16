#!/usr/bin/env python3
"""
Quick Start Script for Flow Metrics Dashboard
Automatically handles Azure DevOps connection issues and starts the dashboard
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{description}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Success!")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"✗ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("Flow Metrics Dashboard - Quick Start")
    print("=" * 40)
    print("This script will:")
    print("1. Try to fetch real Azure DevOps data")
    print("2. Automatically fall back to mock data if needed")
    print("3. Start the dashboard server")
    print("4. Open the dashboard in your browser")
    
    # Check if we're in the right directory
    if not Path("src/cli.py").exists():
        print("\n❌ Error: Please run this script from the project root directory")
        print("   (where src/cli.py is located)")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    
    # Step 1: Generate data (with automatic fallback)
    print("\n📊 STEP 1: Generating Flow Metrics Data")
    success = run_command([
        sys.executable, "-m", "src.cli", "data", "fresh", 
        "--days-back", "7", "--history-limit", "5"
    ], "Attempting to fetch fresh data from Azure DevOps")
    
    if not success:
        print("\n🔄 Trying with mock data explicitly...")
        success = run_command([
            sys.executable, "-m", "src.cli", "data", "fresh", "--use-mock"
        ], "Generating mock data")
        
        if not success:
            print("\n❌ Failed to generate data. Please check your Python environment.")
            print("\nTry running manually:")
            print("   python -m src.cli data fresh --use-mock")
            sys.exit(1)
    
    # Step 2: Start dashboard server
    print("\n🌐 STEP 2: Starting Dashboard Server")
    print("The dashboard will open in your default browser...")
    print("Press Ctrl+C to stop the server when done.\n")
    
    try:
        # Start server with auto-open browser
        subprocess.run([
            sys.executable, "-m", "src.cli", "serve", 
            "--port", "8080", "--open-browser"
        ])
    except KeyboardInterrupt:
        print("\n\n✓ Dashboard server stopped.")
        print("\nTo restart the dashboard:")
        print("   python -m src.cli serve --open-browser")
        print("\nTo generate fresh data:")
        print("   python -m src.cli data fresh --use-mock")


if __name__ == "__main__":
    main()