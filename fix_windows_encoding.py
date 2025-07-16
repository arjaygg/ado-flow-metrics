#!/usr/bin/env python3
"""
Windows Encoding Fix for Flow Metrics CLI
Ensures proper Unicode support in Windows Command Prompt
"""

import os
import sys
import subprocess


def fix_windows_encoding():
    """Fix Windows console encoding issues"""
    if os.name != 'nt':
        print("This script is only needed on Windows systems.")
        return
    
    print("Flow Metrics - Windows Encoding Fix")
    print("=" * 40)
    
    try:
        # Set console code page to UTF-8
        print("Setting console to UTF-8 encoding...")
        result = subprocess.run("chcp 65001", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Console encoding set to UTF-8")
        else:
            print("! Warning: Could not set UTF-8 encoding")
        
        # Set environment variables for Python
        print("Setting Python environment variables...")
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        print("✓ Python environment configured for UTF-8")
        
        # Test the CLI
        print("\nTesting CLI with mock data...")
        test_result = subprocess.run([
            sys.executable, "-m", "src.cli", "data", "mock", "--count", "10"
        ], capture_output=True, text=True)
        
        if test_result.returncode == 0:
            print("✓ CLI test successful!")
            print("\nTo run the dashboard:")
            print("  python -m src.cli serve --open-browser")
        else:
            print("! CLI test failed:")
            print(test_result.stderr)
            
            # Fallback suggestion
            print("\nTry running with environment variables:")
            print("  set PYTHONIOENCODING=utf-8")
            print("  set PYTHONUTF8=1")
            print("  python -m src.cli data mock --count 10")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nManual fix instructions:")
        print("1. Run: chcp 65001")
        print("2. Set: set PYTHONIOENCODING=utf-8")
        print("3. Set: set PYTHONUTF8=1")
        print("4. Test: python -m src.cli data mock --count 10")


if __name__ == "__main__":
    fix_windows_encoding()